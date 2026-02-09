"""
Data source for the scheduling pipeline.

Provides unified access to teams, venues, and constraints data.
"""

from typing import List, Dict, Set, Optional
from pathlib import Path
from pycalendar.core.models import Equipe, Gymnase, Creneau, CoachGroup
from pycalendar.data.data_loader import DataLoader
from pycalendar.core.utils import parser_nom_avec_genre
from pycalendar.core.calendar_manager import CalendarManager
import logging

logger = logging.getLogger(__name__)


class DataSource:
    """Unified data source for the scheduling pipeline."""
    
    def __init__(self, fichier_config: str, calendar_manager: Optional[CalendarManager] = None):
        """
        Initialize the data source.
        
        Args:
            fichier_config: Path to the Excel data file
        """
        self.loader = DataLoader(fichier_config, calendar_manager=calendar_manager)
        self.fichier_config = Path(fichier_config)
        self.calendar_manager = calendar_manager
    
    def charger_equipes(self) -> List[Equipe]:
        """
        Charge les équipes avec toutes les contraintes appliquées.
        
        Returns:
            Liste des équipes avec contraintes institutionnelles
        """
        if not self.fichier_config.exists():
            raise FileNotFoundError(f"Fichier de configuration non trouvé: {self.fichier_config}")
        
        equipes = self.loader.charger_equipes()
        logger.info(f"{len(equipes)} équipes chargées avec contraintes")
        
        return equipes
    
    def charger_gymnases(self) -> List[Gymnase]:
        """
        Charge les gymnases depuis la configuration centrale.
        
        Returns:
            Liste des gymnases
        """
        df_gymnases = self.loader.config.lire_feuille('Gymnases')
        if df_gymnases is None or df_gymnases.empty:
            logger.warning("Aucun gymnase trouvé dans la configuration")
            return []
        
        gymnases = []
        
        for _, row in df_gymnases.iterrows():
            nom = str(row.get('Gymnase', '')).strip()
            if not nom or pd.isna(row.get('Gymnase')):
                continue
            
            # Capacité
            capacite = row.get('Capacite', 1)
            try:
                capacite = int(capacite)
            except (ValueError, TypeError):
                capacite = 1
            
            # Créneaux disponibles
            creneaux_str = str(row.get('Creneaux', '')).strip()
            horaires = []
            if creneaux_str and creneaux_str != 'nan':
                # Format: "09:00, 14:00, 18:00"
                horaires = [h.strip() for h in creneaux_str.split(',') if h.strip()]

            gymnase = Gymnase(
                nom=nom,
                capacite=capacite,
                horaires_disponibles=horaires,
                semaines_indisponibles={},
            )
            
            gymnases.append(gymnase)
        
        # Appliquer les indisponibilités des gymnases
        self._appliquer_indispos_gymnases(gymnases)
        
        logger.info(f"{len(gymnases)} gymnases chargés")
        return gymnases
    
    def _appliquer_indispos_gymnases(self, gymnases: List[Gymnase]):
        """Applique les indisponibilités aux gymnases."""
        import pandas as pd
        
        df_indispos = self.loader.config.lire_feuille('Indispos_Gymnases')
        if df_indispos is None or df_indispos.empty:
            return
        
        # Créer un mapping nom -> gymnase
        gymnases_map = {g.nom: g for g in gymnases}
        
        for _, row in df_indispos.iterrows():
            nom_gymnase = str(row.get('Gymnase', '')).strip()
            if not nom_gymnase or pd.isna(row.get('Gymnase')):
                continue
            
            if nom_gymnase not in gymnases_map:
                logger.warning(f"Gymnase '{nom_gymnase}' dans indispos mais pas dans Gymnases")
                continue
            
            gymnase = gymnases_map[nom_gymnase]
            
            # Semaine - format peut être "6" ou "6 (26/02)"
            semaine = row.get('Semaine')
            if pd.isna(semaine):
                continue
            
            try:
                semaine_str = str(semaine).strip()
                # Extraire le nombre au début (avant la parenthèse si présent)
                semaine = int(semaine_str.split()[0])
            except (ValueError, TypeError, IndexError):
                logger.warning(f"Format de semaine invalide: '{semaine}'")
                continue
            
            # Horaires
            horaire_debut = row.get('Horaire_Debut')
            horaire_fin = row.get('Horaire_Fin')
            
            # Capacité occupée (nouvelle colonne)
            capacite_occupee = row.get('Capacite_Occupee')
            if pd.isna(capacite_occupee):
                # Par défaut, si non spécifié, le gymnase est complètement indisponible
                capacite_occupee = gymnase.capacite
            else:
                try:
                    capacite_occupee = int(capacite_occupee)
                except (ValueError, TypeError):
                    capacite_occupee = gymnase.capacite
            
            # Calculer la capacité restante
            capacite_restante = gymnase.capacite - capacite_occupee
            
            # Si pas d'horaires spécifiés, toute la journée est concernée
            if pd.isna(horaire_debut) or pd.isna(horaire_fin):
                horaires_concernes = gymnase.horaires_disponibles
            else:
                # Trouver les horaires dans la plage [debut, fin[
                # L'horaire de fin est EXCLU pour permettre un match commençant à cet horaire
                horaire_debut_str = str(horaire_debut).strip()
                horaire_fin_str = str(horaire_fin).strip()
                horaires_concernes = [h for h in gymnase.horaires_disponibles 
                                     if horaire_debut_str <= h < horaire_fin_str]
            
            # Appliquer selon la capacité restante
            if capacite_restante <= 0:
                # Complètement indisponible
                if semaine not in gymnase.semaines_indisponibles:
                    gymnase.semaines_indisponibles[semaine] = set()
                gymnase.semaines_indisponibles[semaine].update(horaires_concernes)
            else:
                # Capacité réduite
                if semaine not in gymnase.capacite_reduite:
                    gymnase.capacite_reduite[semaine] = {}
                for horaire in horaires_concernes:
                    # Si déjà une réduction définie, prendre le minimum
                    if horaire in gymnase.capacite_reduite[semaine]:
                        gymnase.capacite_reduite[semaine][horaire] = min(
                            gymnase.capacite_reduite[semaine][horaire],
                            capacite_restante
                        )
                    else:
                        gymnase.capacite_reduite[semaine][horaire] = capacite_restante
        
        logger.debug(f"Indisponibilités appliquées aux gymnases")
    
    def charger_matchs_fixes(self, equipes: Optional[List[Equipe]] = None):
        """
        Charge les matchs déjà joués ou planifiés.
        
        Returns:
            Liste des matchs fixes
        """
        return self.loader.charger_matchs_fixes(equipes)
    
    def charger_contraintes_specifiques(self) -> Dict[str, List[Dict]]:
        """
        Charge les contraintes spécifiques depuis la configuration.
        
        Returns:
            Dictionnaire {type_contrainte: [contraintes]}
        """
        return self.loader.charger_contraintes_specifiques()
    
    def charger_obligations_presence(self) -> Dict[str, str]:
        """
        Charge les obligations de présence par gymnase.
        
        Returns:
            Dictionnaire {gymnase: institution_obligatoire}
        """
        import pandas as pd
        
        df = self.loader.config.lire_feuille('Obligation_Presence')
        if df is None or df.empty:
            return {}
        
        obligations = {}
        
        for _, row in df.iterrows():
            gymnase = str(row.get('Gymnase', '')).strip()
            institution = str(row.get('Institution_Obligatoire', '')).strip()
            
            if gymnase and institution and not pd.isna(row.get('Gymnase')):
                obligations[gymnase] = institution
        
        logger.info(f"{len(obligations)} obligations de présence chargées")
        return obligations
    
    def charger_groupes_non_simultaneite(self) -> Dict[str, Set[str]]:
        """
        Charge les groupes d'équipes/institutions soumis à la contrainte de non-simultanéité.
        
        Returns:
            Dictionnaire {nom_groupe: set(institutions_ou_equipes)}
            
        Exemple:
            {
                'LYON_1_TOUTES': {'LYON 1'},
                'GRANDES_ECOLES': {'ENS', 'CENTRALE', 'MINES'},
                'GROUPE_CUSTOM': {'LYON 1 (1)', 'LYON 1 (2)', 'INSA (3)'}
            }
        """
        import pandas as pd
        
        df = self.loader.config.lire_feuille('Groupes_Non_Simultaneite')
        if df is None or df.empty:
            logger.info("Aucun groupe de non-simultanéité défini")
            return {}
        
        groupes = {}
        ligne_courante = 1  # Compteur pour les groupes sans nom
        
        for _, row in df.iterrows():
            nom_groupe = str(row.get('Nom_Groupe', '')).strip()
            entites_str = str(row.get('Entites', '')).strip()
            
            # Ignorer les lignes complètement vides
            if not entites_str or entites_str == 'nan' or pd.isna(row.get('Entites')):
                continue
            
            # Si pas de nom de groupe, générer un nom automatique
            if not nom_groupe or nom_groupe == 'nan' or pd.isna(row.get('Nom_Groupe')):
                nom_groupe = f"Groupe_{ligne_courante}"
            
            ligne_courante += 1
            
            # Parser les entités (support virgule, point-virgule, retour à la ligne)
            # Remplacer les séparateurs par des virgules
            entites_str = entites_str.replace(';', ',').replace('\n', ',').replace('\r', ',')
            
            # Séparer et nettoyer
            entites_list = [e.strip() for e in entites_str.split(',') if e.strip()]
            
            if not entites_list:
                continue
            
            # Ajouter au dictionnaire
            if nom_groupe not in groupes:
                groupes[nom_groupe] = set()
            
            groupes[nom_groupe].update(entites_list)
        
        logger.info(f"{len(groupes)} groupes de non-simultanéité chargés")
        for nom, membres in groupes.items():
            logger.info(f"  Groupe '{nom}': {', '.join(sorted(membres))}")
        
        return groupes

    def charger_groupes_coachs(self, equipes: List[Equipe]) -> Dict[str, CoachGroup]:
        """Retourne les groupes de coachs avec équipes résolues."""

        groupes = self.loader.charger_groupes_coachs()
        if not groupes:
            return {}

        equipes_par_nom: Dict[str, List[Equipe]] = {}
        for equipe in equipes:
            equipes_par_nom.setdefault(equipe.nom, []).append(equipe)

        for coach_key, group in groupes.items():
            group.team_ids.clear()
            for team_label in group.team_names:
                nom_sans_genre, genre = parser_nom_avec_genre(team_label)
                candidats = equipes_par_nom.get(nom_sans_genre, [])
                if genre:
                    candidats = [eq for eq in candidats if eq.genre == genre]
                if not candidats:
                    logger.warning(
                        "Coach '%s': équipe '%s' introuvable dans la configuration",
                        group.coach_name,
                        team_label
                    )
                    continue
                for eq in candidats:
                    group.add_team_id(eq.id_unique)

        # Filtrer coachs sans équipes résolues
        groupes_valides = {
            group.coach_name: group
            for group in groupes.values()
            if group.team_ids
        }

        coachs_sans_equipes = [g.coach_name for g in groupes.values() if not g.team_ids]
        if coachs_sans_equipes:
            logger.warning("Coach_Groups: %d coach(s) ignoré(s) faute d'équipes correspondantes: %s",
                           len(coachs_sans_equipes), ', '.join(coachs_sans_equipes))

        logger.info("Coach_Groups: %d coach(s) utilisables", len(groupes_valides))
        return groupes_valides
    
    def charger_ententes(self) -> Dict:
        """
        Charge les ententes (paires d'institutions avec pénalité réduite si non planifiées).
        
        Returns:
            Dictionnaire {(inst1, inst2): penalite_non_planif}
        """
        return self.loader.charger_ententes()
    
    def charger_niveaux_gymnases(self) -> Dict[str, str]:
        """
        Charge les niveaux des gymnases (haut/bas niveau).
        
        Returns:
            Dictionnaire {nom_gymnase: niveau}
        """
        return self.loader.charger_niveaux_gymnases()

    def charger_priorites_genre_gymnases(self) -> Dict[str, str]:
        """Charge les genres prioritaires déclarés sur chaque gymnase."""
        return self.loader.charger_priorites_genre_gymnases()

    def charger_contraintes_temporelles(self) -> Dict:
        """
        Charge les contraintes temporelles sur matchs spécifiques.
        
        Returns:
            Dictionnaire {(equipe1, equipe2): ContrainteTemporelle}
        """
        return self.loader.charger_contraintes_temporelles()
    
    def charger_types_poules(self) -> Dict[str, str]:
        """
        Charge les types de poules (Classique ou Aller-Retour).
        
        Returns:
            Dictionnaire {nom_poule: type} où type est 'Classique' ou 'Aller-Retour'
        """
        return self.loader.charger_types_poules()
    
    def get_poules_dict(self, equipes: List[Equipe]) -> Dict[str, List[Equipe]]:
        """Regroupe les équipes par poule."""
        return self.loader.get_poules_dict(equipes)


# Import pandas à la fin pour éviter les problèmes circulaires
import pandas as pd


if __name__ == "__main__":
    # Tests unitaires
    print("🧪 TEST DE LA SOURCE DE DONNÉES")
    print("="*80)
    
    adapter = DataSource("exemple/config_exemple.xlsx")
    
    print("\n📊 Test du DataSource\n")
    
    # Charger équipes
    equipes = adapter.charger_equipes()
    print(f"✅ {len(equipes)} équipes chargées")
    
    # Charger gymnases
    gymnases = adapter.charger_gymnases()
    print(f"✅ {len(gymnases)} gymnases chargés")
    
    # Afficher détails
    print("\n🏟️  Détails gymnases :")
    for g in gymnases[:3]:
        print(f"  - {g.nom} : capacité={g.capacite}, horaires={len(g.horaires_disponibles)}")
        if g.semaines_indisponibles:
            print(f"    Indispos : {len(g.semaines_indisponibles)} semaines")
    
    # Charger obligations
    obligations = adapter.charger_obligations_presence()
    print(f"\n✅ {len(obligations)} obligations de présence")
    for gymnase, institution in obligations.items():
        print(f"  - {gymnase} → {institution}")
