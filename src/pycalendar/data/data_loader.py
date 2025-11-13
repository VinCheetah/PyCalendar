"""
Data loader for the Excel configuration file.

This loader reads all data from the Excel file and automatically applies
institutional constraints to all teams.
"""

import pandas as pd
from typing import List, Dict, Set, Tuple, Optional
from pathlib import Path
from pycalendar.core.models import Equipe, Gymnase, ContrainteTemporelle, Match
from pycalendar.core.utils import extraire_genre_depuis_poule, parser_nom_avec_genre, formater_nom_avec_genre
from pycalendar.core.config_manager import ConfigManager
import logging
import re

logger = logging.getLogger(__name__)


class DataLoader:
    """Loads teams, venues, and constraints data from Excel configuration file."""
    
    def __init__(self, fichier_config: str):
        """
        Initialise le loader avec le fichier de configuration.
        
        Args:
            fichier_config: Chemin vers le fichier de configuration central
        """
        self.config = ConfigManager(fichier_config)
        
        if not self.config.fichier_existe():
            raise FileNotFoundError(f"Fichier de configuration non trouvé : {fichier_config}")
        
        # Valider la structure
        valide, erreurs = self.config.valider_fichier_complet()
        if not valide:
            logger.warning("Le fichier de configuration contient des erreurs :")
            for feuille, errs in erreurs.items():
                for err in errs:
                    logger.warning(f"  {feuille}: {err}")
    
    @staticmethod
    def _normaliser_horaire(horaire_brut: str) -> str:
        """
        Normalise un horaire au format HH:MM.
        
        Gère les formats: "14h00", "14h", "14:00", "9:00", etc.
        Retourne toujours au format "HH:MM" (ex: "09:00", "14:00")
        
        Args:
            horaire_brut: Horaire brut depuis Excel
            
        Returns:
            Horaire normalisé au format HH:MM
        """
        horaire = horaire_brut.replace('h', ':')
        if ':' not in horaire:
            horaire = horaire + ':00'
        elif horaire.endswith(':'):
            horaire += '00'
        # Ajouter le zéro devant si nécessaire (9:00 → 09:00)
        if len(horaire) == 4:  # Format "9:00"
            horaire = '0' + horaire
        return horaire
    
    def _obtenir_horaires_systeme(self) -> List[str]:
        """
        Obtient la liste de tous les horaires disponibles dans le système.
        
        IMPORTANT: Retourne les horaires au format "HH:MM" (ex: "14:00", "16:00")
        pour être cohérent avec le reste du système (gymnases, créneaux).
        
        Returns:
            Liste triée des horaires disponibles au format "HH:MM" (ex: ['14:00', '16:00', ...])
        """
        df_gymnases = self.config.lire_feuille('Gymnases')
        if df_gymnases is None or df_gymnases.empty:
            logger.warning("Aucun gymnase trouvé pour extraire les horaires")
            return []
        
        # Récupérer tous les horaires depuis les colonnes HORAIRES ou Creneaux
        horaires = set()
        for _, row in df_gymnases.iterrows():
            # Essayer les deux noms possibles de colonne
            horaires_str = row.get('HORAIRES') or row.get('Creneaux', '')
            if pd.notna(horaires_str):
                # Format: "14:00, 16:00, ..." ou "14h00;16h00;..."
                if isinstance(horaires_str, str):
                    # Diviser par ; ou ,
                    horaires_list = re.split(r'[;,]', horaires_str)
                    for h in horaires_list:
                        h_clean = h.strip()
                        if h_clean:
                            # Normaliser au format HH:MM
                            # Convertir "14h00" ou "14h" → "14:00"
                            h_normalized = h_clean.replace('h', ':')
                            # Si pas de minutes, ajouter ":00"
                            if ':' not in h_normalized:
                                h_normalized = h_clean + ':00'
                            elif h_normalized.endswith(':'):
                                h_normalized += '00'
                            horaires.add(h_normalized)
        
        return sorted(list(horaires))
    
    def charger_equipes(self) -> List[Equipe]:
        """
        Charge toutes les équipes avec leurs contraintes.
        
        Returns:
            Liste des équipes avec contraintes institutionnelles appliquées
        """
        # Charger les équipes de base
        df_equipes = self.config.lire_feuille('Equipes')
        if df_equipes is None or df_equipes.empty:
            logger.warning("Aucune équipe trouvée dans le fichier")
            return []
        
        # Obtenir les horaires disponibles du système (depuis les gymnases)
        horaires_systeme = self._obtenir_horaires_systeme()
        
        # Charger les contraintes institutionnelles
        contraintes_institutions = self._charger_contraintes_institutions(horaires_systeme)
        preferences_institutions = self._charger_preferences_institutions()
        indispos_equipes = self._charger_indispos_equipes(horaires_systeme)
        dispos_gymnases_equipes = self._charger_dispos_gymnases_equipes()
        
        equipes = []
        
        for _, row in df_equipes.iterrows():
            nom_brut = str(row.get('Equipe', '')).strip()
            if not nom_brut or pd.isna(nom_brut):
                continue
            
            poule = str(row.get('Poule', 'Default')).strip()
            
            # NORMALISATION: Extraire le nom SANS genre et le genre depuis le nom brut
            # Le nom dans la feuille Equipes peut contenir [M] ou [F], on les retire systématiquement
            # pour garantir que Equipe.nom soit TOUJOURS sans genre
            nom_sans_genre, genre_depuis_nom = parser_nom_avec_genre(nom_brut)
            
            # Extraire le genre : priorité au genre dans le nom, sinon colonne Genre, sinon poule
            genre = genre_depuis_nom
            if not genre and 'Genre' in df_equipes.columns:
                genre_explicite = row.get('Genre')
                if pd.notna(genre_explicite) and str(genre_explicite).strip() in ['M', 'F']:
                    genre = str(genre_explicite).strip()
            
            if not genre:
                # Extraire le genre depuis le code de la poule en dernier recours
                genre = extraire_genre_depuis_poule(poule)
            
            # Parser le nom SANS GENRE pour extraire institution et numéro
            match = re.match(r'^(.+?)\s*\((\d+)\)\s*$', nom_sans_genre)
            
            if match:
                institution = match.group(1).strip()
                numero_equipe = match.group(2).strip()
            else:
                institution = nom_sans_genre
                numero_equipe = ""
            
            # Horaire préféré de l'équipe (format nouveau: une seule colonne)
            horaires = []
            horaire_pref = row.get('Horaire_Prefere')
            if pd.notna(horaire_pref):
                horaire_str = str(horaire_pref).strip()
                if horaire_str:
                    horaires.append(horaire_str)
            
            # Lieux préférés de l'équipe (format nouveau: colonne unique avec virgules ou multiple colonnes)
            lieux = []
            # Essayer d'abord la colonne unique Lieu_Prefere
            lieu_pref = row.get('Lieu_Prefere')
            if pd.notna(lieu_pref):
                lieu_str = str(lieu_pref).strip()
                if lieu_str and lieu_str.lower() != 'nan':
                    # Si plusieurs lieux séparés par virgule
                    if ',' in lieu_str:
                        lieux.extend([l.strip() for l in lieu_str.split(',') if l.strip()])
                    else:
                        lieux.append(lieu_str)
            
            # Sinon essayer l'ancien format avec Lieu_1, Lieu_2, etc.
            if not lieux:
                for i in range(1, 10):
                    l = row.get(f'Lieu_{i}')
                    if pd.notna(l):
                        lieux.append(str(l).strip())
            
            # Indisponibilités spécifiques à l'équipe (ancien format depuis colonnes Indispo_1, Indispo_2, ...)
            # Ces colonnes contiennent juste des numéros de semaines -> toute la journée est indisponible
            indispos: Dict[int, Set[str]] = {}
            for i in range(1, 20):
                ind = row.get(f'Indispo_{i}')
                if pd.notna(ind):
                    try:
                        semaine = int(ind)
                        if semaine not in indispos:
                            indispos[semaine] = set()
                        indispos[semaine].update(horaires_systeme)  # Toute la journée
                    except (ValueError, TypeError):
                        pass
            
            # === APPLIQUER LES CONTRAINTES INSTITUTIONNELLES ===
            
            # 1. Ajouter les indisponibilités de l'institution
            # Les indisponibilités institutionnelles s'appliquent à TOUTES les équipes de l'institution
            if institution in contraintes_institutions:
                indispos_inst = contraintes_institutions[institution]
                # indispos_inst est maintenant un Dict[int, Set[str]]
                for semaine, horaires_indispo in indispos_inst.items():
                    if semaine not in indispos:
                        indispos[semaine] = set()
                    indispos[semaine].update(horaires_indispo)
                logger.debug(f"Équipe {nom_sans_genre} [{genre}]: indisponibilités institutionnelles ajoutées pour {len(indispos_inst)} semaines")
            
            # 2. Ajouter les préférences de lieux de l'institution
            if institution in preferences_institutions:
                # gymnases_preferes_institution est une liste avec potentiellement des None
                # On garde la structure complète pour préserver les rangs
                lieux = preferences_institutions[institution].copy()
                
                nb_prefs = sum(1 for g in lieux if g is not None)
                logger.debug(f"Équipe {nom_sans_genre} [{genre}]: {nb_prefs} gymnases préférés institutionnels (avec rangs préservés)")
            
            # 3. Ajouter les indisponibilités spécifiques de l'équipe (depuis Indispos_Equipes)
            # IMPORTANT: Les indispos_equipes peuvent être stockées de deux façons:
            # - Avec genre (format "LYON 1 (1)|F") → s'applique uniquement à ce genre
            # - Sans genre (format "LYON 1 (1)") → s'applique à tous les genres
            logger.debug(f"Recherche indispos pour nom_sans_genre='{nom_sans_genre}', genre='{genre}'")
            
            # Chercher d'abord les indispos spécifiques au genre
            cle_avec_genre = f"{nom_sans_genre}|{genre}"
            if cle_avec_genre in indispos_equipes:
                indispo_equipe = indispos_equipes[cle_avec_genre]
                for semaine, horaires_indispo in indispo_equipe.items():
                    if semaine not in indispos:
                        indispos[semaine] = set()
                    indispos[semaine].update(horaires_indispo)
                logger.info(f"✅ Équipe {nom_sans_genre} [{genre}]: {len(indispo_equipe)} semaines d'indispos (spécifique genre)")
            
            # Chercher ensuite les indispos globales (sans genre, s'appliquent à M et F)
            if nom_sans_genre in indispos_equipes:
                indispo_globale = indispos_equipes[nom_sans_genre]
                for semaine, horaires_indispo in indispo_globale.items():
                    if semaine not in indispos:
                        indispos[semaine] = set()
                    indispos[semaine].update(horaires_indispo)
                logger.info(f"✅ Équipe {nom_sans_genre} [{genre}]: {len(indispo_globale)} semaines d'indispos (globale tous genres)")
            
            # Si aucune indispo trouvée
            if cle_avec_genre not in indispos_equipes and nom_sans_genre not in indispos_equipes:
                if indispos_equipes:
                    logger.debug(f"❌ Équipe {nom_sans_genre} [{genre}]: PAS d'indispo trouvée")
            
            # 4. Ajouter les disponibilités anticipées sur gymnases spécifiques
            # IMPORTANT: Les dispos_gymnases_equipes utilisent le nom SANS genre (format: "LYON 1 (1)")
            # car c'est le format de la colonne Equipe dans la feuille Dispos_Gymnases_Equipes
            dispos_gymnases = {}
            cle_equipe = f"{nom_sans_genre}|{genre}"
            if cle_equipe in dispos_gymnases_equipes:
                dispos_gymnases = dispos_gymnases_equipes[cle_equipe].copy()
                logger.debug(f"Équipe {nom_sans_genre} [{genre}]: {len(dispos_gymnases)} disponibilités anticipées sur gymnases")
            
            # Créer l'équipe avec toutes les contraintes appliquées
            # IMPORTANT: Equipe.nom doit TOUJOURS être SANS genre pour garantir la cohérence
            # Le genre est stocké dans Equipe.genre, et id_unique combine les deux
            equipe = Equipe(
                nom=nom_sans_genre,
                poule=poule,
                institution=institution,
                numero_equipe=numero_equipe,
                genre=genre,
                horaires_preferes=horaires,
                lieux_preferes=lieux,
                semaines_indisponibles=indispos,
                dispos_gymnases_specifiques=dispos_gymnases
            )
            equipes.append(equipe)
        
        logger.info(f"{len(equipes)} équipes chargées avec contraintes institutionnelles")
        
        return equipes
    
    def _charger_contraintes_institutions(self, horaires_systeme: List[str]) -> Dict[str, Dict[int, Set[str]]]:
        """
        Charge les contraintes (indisponibilités) par institution.
        
        Structure de la feuille Indispos_Institutions:
        - Institution: Nom de l'institution
        - Semaine: Numéro de la semaine (obligatoire)
        - Horaire_Debut: Heure de début (optionnel)
        - Horaire_Fin: Heure de fin (optionnel)
        - Remarques: Commentaires (optionnel)
        
        IMPORTANT - Gestion des horaires:
        - Si Horaire_Debut OU Horaire_Fin est vide (cellule vide, NaN, ou ""),
          l'indisponibilité s'applique à TOUTE LA JOURNÉE (tous les horaires système)
        - Si les deux horaires sont renseignés, l'indisponibilité s'applique à la plage
          [Horaire_Debut, Horaire_Fin[ (l'horaire de fin est EXCLU)
        - Les horaires sont normalisés (gère "14h00", "14h", "9:00" → "14:00", "09:00")
        - Ces indisponibilités s'appliquent à TOUTES les équipes de l'institution
        
        Args:
            horaires_systeme: Liste de tous les horaires disponibles dans le système
        
        Returns:
            Dictionnaire {institution: {semaine: set(horaires_indisponibles)}}
        """
        df = self.config.lire_feuille('Indispos_Institutions')
        if df is None or df.empty:
            return {}
        
        contraintes = {}
        
        for _, row in df.iterrows():
            institution = str(row.get('Institution', '')).strip()
            if not institution or pd.isna(institution):
                continue
            
            # Récupérer la semaine
            semaine = row.get('Semaine')
            if pd.isna(semaine):
                logger.warning(f"Indisponibilité institution '{institution}': semaine manquante, ligne ignorée")
                continue
            
            try:
                semaine = int(semaine)
            except (ValueError, TypeError):
                logger.warning(f"Indisponibilité institution '{institution}': semaine invalide '{semaine}', ligne ignorée")
                continue
            
            # Vérifier si des horaires spécifiques sont définis
            horaire_debut = row.get('Horaire_Debut')
            horaire_fin = row.get('Horaire_Fin')
            
            # Vérifier si l'horaire est vide (None, NaN, ou chaîne vide)
            horaire_debut_vide = pd.isna(horaire_debut) or str(horaire_debut).strip() == ''
            horaire_fin_vide = pd.isna(horaire_fin) or str(horaire_fin).strip() == ''
            
            # Déterminer les horaires concernés
            if horaire_debut_vide or horaire_fin_vide:
                # Toute la semaine est indisponible si l'un des deux horaires est vide
                horaires_concernes = set(horaires_systeme)
            else:
                # Normaliser les horaires au format HH:MM pour comparaison
                horaire_debut_str = self._normaliser_horaire(str(horaire_debut).strip())
                horaire_fin_str = self._normaliser_horaire(str(horaire_fin).strip())
                
                # Filtrer les horaires dans la plage [debut, fin[
                # L'horaire de fin est EXCLU pour permettre un match commençant à cet horaire
                horaires_concernes = set(h for h in horaires_systeme 
                                        if horaire_debut_str <= h < horaire_fin_str)
            
            # Ajouter l'indisponibilité
            if institution not in contraintes:
                contraintes[institution] = {}
            if semaine not in contraintes[institution]:
                contraintes[institution][semaine] = set()
            contraintes[institution][semaine].update(horaires_concernes)
        
        logger.info(f"Contraintes institutionnelles chargées pour {len(contraintes)} institutions")
        return contraintes
    
    def _charger_preferences_institutions(self) -> Dict[str, List[Optional[str]]]:
        """
        Charge les préférences de gymnases par institution.
        
        Nouvelle structure : Institution | Gymnase_Pref_1 | Gymnase_Pref_2 | ... | Gymnase_Pref_N
        
        Returns:
            Dictionnaire {institution: [liste_avec_trous]}
            où liste_avec_trous contient des gymnases ou None, préservant l'index = rang
            Ex: Si Gymnase_Pref_1 = vide, Gymnase_Pref_2 = vide, Gymnase_Pref_3 = "PARC"
                alors preferences["Institution"] = [None, None, "PARC"]
            L'index dans la liste correspond au rang de préférence (0-based)
        """
        df = self.config.lire_feuille('Preferences_Gymnases')
        if df is None or df.empty:
            return {}
        
        preferences = {}
        
        for _, row in df.iterrows():
            institution = str(row.get('Institution', '')).strip()
            if not institution or pd.isna(institution):
                continue
            
            # Extraire les gymnases préférés depuis les colonnes Gymnase_Pref_1, Gymnase_Pref_2, etc.
            # Important : Préserver le rang même si certaines colonnes sont vides
            # Ex: si Gymnase_Pref_3 est renseigné mais pas Pref_1 et Pref_2, 
            # on veut que ce gymnase ait le bonus correspondant au rang 3
            
            # Trier les colonnes par numéro de préférence
            colonnes_pref = sorted(
                [col for col in df.columns if col.startswith('Gymnase_Pref_')],
                key=lambda x: int(x.split('_')[-1])
            )
            
            # Collecter les gymnases en gardant les "trous" (None pour les colonnes vides)
            # Index de la liste = rang de préférence
            gymnases_preferes = []
            
            for col in colonnes_pref:
                gymnase = row.get(col)
                if gymnase and not pd.isna(gymnase):
                    gymnase_str = str(gymnase).strip()
                    if gymnase_str:
                        gymnases_preferes.append(gymnase_str)
                    else:
                        gymnases_preferes.append(None)
                else:
                    gymnases_preferes.append(None)
            
            # Stocker uniquement si au moins un gymnase est renseigné
            if any(g is not None for g in gymnases_preferes):
                preferences[institution] = gymnases_preferes
        
        logger.info(f"Préférences de gymnases chargées pour {len(preferences)} institutions")
        return preferences
    
    def _charger_indispos_equipes(self, horaires_systeme: List[str]) -> Dict[str, Dict[int, Set[str]]]:
        """
        Charge les indisponibilités spécifiques par équipe.
        
        Structure attendue:
        - Equipe: Nom de l'équipe (SANS genre, ex: "LYON 1 (1)")
        - Semaine: Numéro de semaine (obligatoire)
        - Horaire_Debut: Heure de début (optionnel)
        - Horaire_Fin: Heure de fin (optionnel)
        
        IMPORTANT - Gestion des horaires:
        - Si Horaire_Debut OU Horaire_Fin est vide (cellule vide, NaN, ou ""), 
          l'indisponibilité s'applique à TOUTE LA JOURNÉE (tous les horaires système)
        - Si les deux horaires sont renseignés, l'indisponibilité s'applique à la plage
          [Horaire_Debut, Horaire_Fin[ (l'horaire de fin est EXCLU)
        - Les horaires sont normalisés (gère "14h00", "14h", "9:00" → "14:00", "09:00")
        
        Args:
            horaires_systeme: Liste de tous les horaires disponibles dans le système
        
        Returns:
            Dictionnaire {nom_equipe: {semaine: set(horaires_indisponibles)}}
        """
        df = self.config.lire_feuille('Indispos_Equipes')
        if df is None or df.empty:
            print("⚠️  INDISPOS: Feuille Indispos_Equipes vide ou inexistante")
            return {}
        
        print(f"📋 INDISPOS: Chargement de {len(df)} lignes depuis Indispos_Equipes")
        
        # Structure: {nom_equipe: {semaine: set(horaires)}} ou {nom_equipe|genre: {semaine: set(horaires)}}
        # Si le nom contient [F] ou [M], on stocke avec le genre pour appliquer uniquement à ce genre
        # Sinon, on stocke sans genre pour appliquer à tous les genres
        indispos = {}
        
        # Import pour parser les noms avec genre
        from pycalendar.core.utils import parser_nom_avec_genre
        
        for _, row in df.iterrows():
            equipe_brut = str(row.get('Equipe', '')).strip()
            if not equipe_brut or pd.isna(equipe_brut):
                continue
            
            # Parser le nom pour retirer [M] ou [F] si présent
            # IMPORTANT: Indispos_Equipes peut contenir:
            # - "LYON 1 (1) [F]" → indispo s'applique uniquement à l'équipe féminine
            # - "LYON 1 (1)" → indispo s'applique aux équipes M ET F
            equipe_nom, genre_depuis_nom = parser_nom_avec_genre(equipe_brut)
            
            # Déterminer la clé de stockage
            if genre_depuis_nom:
                # Genre spécifié → indispo spécifique à ce genre
                cle_indispo = f"{equipe_nom}|{genre_depuis_nom}"
            else:
                # Pas de genre → indispo pour tous les genres
                cle_indispo = equipe_nom
            
            # Récupérer la semaine
            semaine = row.get('Semaine')
            if pd.isna(semaine):
                logger.warning(f"Indisponibilité équipe '{cle_indispo}': semaine manquante, ligne ignorée")
                continue
            
            try:
                semaine = int(semaine)
            except (ValueError, TypeError):
                logger.warning(f"Indisponibilité équipe '{cle_indispo}': semaine invalide '{semaine}', ligne ignorée")
                continue
            
            # Vérifier si des horaires spécifiques sont définis
            horaire_debut = row.get('Horaire_Debut')
            horaire_fin = row.get('Horaire_Fin')
            
            # Vérifier si l'horaire est vide (None, NaN, ou chaîne vide)
            horaire_debut_vide = pd.isna(horaire_debut) or str(horaire_debut).strip() == ''
            horaire_fin_vide = pd.isna(horaire_fin) or str(horaire_fin).strip() == ''
            
            # Déterminer les horaires concernés
            if horaire_debut_vide or horaire_fin_vide:
                # Toute la journée est indisponible si l'un des deux horaires est vide
                horaires_concernes = set(horaires_systeme)
                logger.debug(f"Indispo {cle_indispo} S{semaine}: TOUTE LA JOURNÉE ({len(horaires_concernes)} horaires)")
            else:
                # Normaliser les horaires au format HH:MM pour comparaison
                horaire_debut_str = self._normaliser_horaire(str(horaire_debut).strip())
                horaire_fin_str = self._normaliser_horaire(str(horaire_fin).strip())
                
                # Filtrer les horaires dans la plage [debut, fin[
                # L'horaire de fin est EXCLU pour permettre un match commençant à cet horaire
                horaires_concernes = set(h for h in horaires_systeme 
                                        if horaire_debut_str <= h < horaire_fin_str)
                logger.debug(f"Indispo {cle_indispo} S{semaine}: {horaire_debut_str} - {horaire_fin_str} → {len(horaires_concernes)} horaires")
            
            # Ajouter l'indisponibilité
            if cle_indispo not in indispos:
                indispos[cle_indispo] = {}
            if semaine not in indispos[cle_indispo]:
                indispos[cle_indispo][semaine] = set()
            indispos[cle_indispo][semaine].update(horaires_concernes)
            
            logger.debug(f"Indispo chargée: clé='{cle_indispo}', semaine={semaine}, horaires={len(horaires_concernes)}")
        
        logger.info(f"Indisponibilités spécifiques chargées pour {len(indispos)} équipes")
        if indispos:
            logger.debug(f"Équipes avec indispos: {list(indispos.keys())}")
        return indispos
    
    def _charger_dispos_gymnases_equipes(self) -> Dict[str, Dict[str, str]]:
        """
        Charge les disponibilités anticipées d'équipes sur des gymnases spécifiques.
        
        Structure de la feuille Dispos_Gymnases_Equipes:
        - Equipe: Nom de l'équipe (sans genre)
        - Genre: M ou F
        - Horaire_Dispo: Horaire de disponibilité anticipée (avant l'horaire général)
        - Gymnase_1 à Gymnase_5: Gymnases où la disponibilité s'applique
        - Remarques: Commentaires (optionnel)
        
        Returns:
            Dictionnaire {equipe_avec_genre: {gymnase: horaire_dispo}}
            Format: {"LYON 1 (1)|M": {"PARC": "18:00", "INSA C": "18:00"}}
        """
        df = self.config.lire_feuille('Dispos_Gymnases_Equipes')
        if df is None or df.empty:
            return {}
        
        dispos_gymnases = {}
        lignes_traitees = 0
        
        for _, row in df.iterrows():
            equipe = str(row.get('Equipe', '')).strip()
            if not equipe or pd.isna(equipe):
                continue
            
            # Récupérer le genre
            genre = row.get('Genre')
            if pd.isna(genre):
                logger.warning(f"Dispo gymnases '{equipe}': genre manquant, ligne ignorée")
                continue
            
            genre_str = str(genre).strip().upper()
            if genre_str not in ['M', 'F']:
                logger.warning(f"Dispo gymnases '{equipe}': genre invalide '{genre}', ligne ignorée")
                continue
            
            # Récupérer l'horaire de disponibilité
            horaire_dispo = row.get('Horaire_Dispo')
            if pd.isna(horaire_dispo):
                logger.warning(f"Dispo gymnases '{equipe}' {genre_str}: horaire manquant, ligne ignorée")
                continue
            
            horaire_dispo_str = str(horaire_dispo).strip()
            if not horaire_dispo_str:
                continue
            
            # Normaliser l'horaire au format HH:MM
            horaire_normalise = horaire_dispo_str.replace('h', ':')
            if ':' not in horaire_normalise:
                horaire_normalise = horaire_normalise + ':00'
            elif horaire_normalise.endswith(':'):
                horaire_normalise += '00'
            
            # Récupérer les gymnases (colonnes Gymnase_1 à Gymnase_5)
            gymnases = []
            for i in range(1, 6):
                col_gymnase = f'Gymnase_{i}'
                if col_gymnase in df.columns:
                    gymnase = row.get(col_gymnase)
                    if pd.notna(gymnase):
                        gymnase_str = str(gymnase).strip()
                        if gymnase_str:
                            gymnases.append(gymnase_str)
            
            if not gymnases:
                logger.warning(f"Dispo gymnases '{equipe}' {genre_str}: aucun gymnase spécifié, ligne ignorée")
                continue
            
            # Créer la clé avec équipe|genre
            cle = f"{equipe}|{genre_str}"
            lignes_traitees += 1
            
            # Initialiser le dictionnaire pour cette équipe
            if cle not in dispos_gymnases:
                dispos_gymnases[cle] = {}
            
            # Ajouter chaque gymnase avec son horaire
            for gymnase in gymnases:
                dispos_gymnases[cle][gymnase] = horaire_normalise
        
        logger.info(f"Disponibilités gymnases spécifiques chargées pour {len(dispos_gymnases)} équipes")
        return dispos_gymnases
    
    def charger_gymnases(self) -> List[Gymnase]:
        """
        Charge tous les gymnases avec leurs créneaux disponibles.
        
        Returns:
            Liste des gymnases
        """
        df = self.config.lire_feuille('Gymnases')
        if df is None or df.empty:
            logger.warning("Aucun gymnase trouvé dans le fichier")
            return []
        
        gymnases_dict = {}
        
        for _, row in df.iterrows():
            nom = str(row.get('Gymnase', '')).strip()
            if not nom or pd.isna(nom):
                continue
            
            if nom not in gymnases_dict:
                adresse = str(row.get('Adresse', '')).strip()
                capacite = row.get('Capacite', 0)
                
                try:
                    capacite = int(capacite)
                except (ValueError, TypeError):
                    capacite = 0
                
                gymnases_dict[nom] = Gymnase(
                    nom=nom,
                    capacite=capacite,
                    horaires_disponibles=[],
                    semaines_indisponibles={}
                )
            
            # Ajouter le créneau si disponible
            disponible = str(row.get('Disponible', 'Oui')).strip().lower()
            if disponible in ['oui', 'yes', 'true', '1']:
                jour = str(row.get('Jour', '')).strip()
                heure_debut = row.get('Heure_Debut')
                heure_fin = row.get('Heure_Fin')
                
                if jour and pd.notna(heure_debut) and pd.notna(heure_fin):
                    # TODO: Convertir en format de créneau approprié
                    # Pour l'instant on stocke juste le gymnase
                    pass
        
        gymnases = list(gymnases_dict.values())
        logger.info(f"{len(gymnases)} gymnases chargés")
        
        return gymnases
    
    def charger_contraintes_specifiques(self) -> Dict[str, List[Dict]]:
        """
        Charge les contraintes spécifiques (anti-collisions, etc.).
        
        Returns:
            Dictionnaire {type_contrainte: [contraintes]}
        """
        df = self.config.lire_feuille('Contraintes_Specifiques')
        if df is None or df.empty:
            return {}
        
        contraintes = {}
        
        for _, row in df.iterrows():
            type_contrainte = str(row.get('Type_Contrainte', '')).strip()
            if not type_contrainte or pd.isna(type_contrainte):
                continue
            
            if type_contrainte not in contraintes:
                contraintes[type_contrainte] = []
            
            contrainte = {
                'Equipe_1': row.get('Equipe_1'),
                'Equipe_2': row.get('Equipe_2'),
                'Poule_1': row.get('Poule_1'),
                'Poule_2': row.get('Poule_2'),
                'Institution_1': row.get('Institution_1'),
                'Institution_2': row.get('Institution_2'),
                'Condition': row.get('Condition'),
                'Priorite': row.get('Priorite', 'Moyenne'),
                'Remarques': row.get('Remarques', '')
            }
            
            contraintes[type_contrainte].append(contrainte)
        
        logger.info(f"Contraintes spécifiques chargées: {len(contraintes)} types")
        return contraintes
    
    def charger_ententes(self) -> Dict[Tuple[str, str], float]:
        """
        Charge les ententes (paires d'institutions avec pénalité réduite si non planifiées).
        
        Une entente désigne un match entre 2 institutions spécifiques qui est moins prioritaire.
        Si ce match n'est pas planifié, la pénalité appliquée est RÉDUITE (au lieu de la pénalité
        standard élevée).
        
        Structure de la feuille Ententes (optionnelle):
        - Institution_1: Première institution de la paire
        - Institution_2: Seconde institution de la paire  
        - Penalite_Non_Planif: Pénalité si match non planifié (optionnel, utilise défaut YAML sinon)
        - Remarques: Commentaires (optionnel)
        
        Returns:
            Dictionnaire {(inst1, inst2): pénalité_non_planif}
            La clé est un tuple trié alphabétiquement pour détection bidirectionnelle
        """
        df = self.config.lire_feuille('Ententes')
        if df is None or df.empty:
            logger.debug("Pas de feuille Ententes")
            return {}
        
        ententes = {}
        
        for idx, row in df.iterrows():
            inst1 = str(row.get('Institution_1', '')).strip()
            inst2 = str(row.get('Institution_2', '')).strip()
            
            if not inst1 or pd.isna(row.get('Institution_1')):
                logger.warning(f"Ligne {idx+2}: Institution_1 manquante, ligne ignorée")
                continue
            if not inst2 or pd.isna(row.get('Institution_2')):
                logger.warning(f"Ligne {idx+2}: Institution_2 manquante, ligne ignorée")
                continue
            
            # Créer clé triée pour détection bidirectionnelle (LYON 1, LYON 2) = (LYON 2, LYON 1)
            cle = tuple(sorted([inst1, inst2]))
            
            # Pénalité optionnelle
            penalite_col = row.get('Penalite_Non_Planif')
            if pd.isna(penalite_col) or penalite_col == '':
                # Pas de pénalité spécifiée, on utilisera le défaut du YAML
                penalite = None
            else:
                try:
                    penalite = float(penalite_col)
                    if penalite < 0:
                        logger.warning(f"Ligne {idx+2}: Pénalité négative ({penalite}), utilisation défaut")
                        penalite = None
                except (ValueError, TypeError):
                    logger.warning(f"Ligne {idx+2}: Pénalité invalide '{penalite_col}', utilisation défaut")
                    penalite = None
            
            ententes[cle] = penalite
        
        logger.info(f"Ententes chargées: {len(ententes)} paires d'institutions")
        return ententes
    
    def charger_niveaux_gymnases(self) -> Dict[str, str]:
        """
        Charge les niveaux des gymnases (haut/bas niveau).
        
        Structure de la feuille Niveaux_Gymnases:
        - Gymnase: Nom du gymnase (doit exister dans la feuille Gymnases)
        - Niveau: "Haut niveau" ou "Bas niveau"
        - Remarque: Commentaire optionnel
        
        Returns:
            Dictionnaire {nom_gymnase: niveau}
        """
        df = self.config.lire_feuille('Niveaux_Gymnases')
        if df is None or df.empty:
            logger.debug("Pas de feuille Niveaux_Gymnases")
            return {}
        
        niveaux = {}
        
        for idx, row in df.iterrows():
            gymnase = str(row.get('Gymnase', '')).strip()
            niveau = str(row.get('Niveau', '')).strip()
            
            if not gymnase or pd.isna(row.get('Gymnase')):
                logger.warning(f"Ligne {idx+2}: Gymnase manquant, ligne ignorée")
                continue
            
            if not niveau or pd.isna(row.get('Niveau')):
                logger.warning(f"Ligne {idx+2}: Niveau manquant pour gymnase '{gymnase}', ligne ignorée")
                continue
            
            # Validation du niveau
            if niveau not in ['Haut niveau', 'Bas niveau']:
                logger.warning(f"Ligne {idx+2}: Niveau invalide '{niveau}' pour gymnase '{gymnase}', doit être 'Haut niveau' ou 'Bas niveau'")
                continue
            
            niveaux[gymnase] = niveau
        
        logger.info(f"Niveaux de gymnases chargés: {len(niveaux)} gymnases classés")
        return niveaux
    
    def charger_contraintes_temporelles(self) -> Dict[Tuple[str, str], 'ContrainteTemporelle']:
        """
        Charge les contraintes temporelles sur matchs spécifiques.
        
        Une contrainte temporelle impose qu'un match entre deux équipes soit planifié
        avant ou après une semaine donnée (ex: matchs CFE après semaine 8).
        
        Structure de la feuille Contraintes_Temporelles (optionnelle):
        - Equipe_1: Première équipe de la paire (format: "NOM (X)" sans [F]/[M])
        - Equipe_2: Seconde équipe de la paire (format: "NOM (X)" sans [F]/[M])
        - Genre: Genre commun aux deux équipes (M ou F)
        - Type_Contrainte: "Avant" ou "Apres"
        - Semaine: Numéro de semaine limite (1-52)
        - Horaires_Possibles: Liste d'horaires préférés séparés par virgule (optionnel)
        - Remarques: Commentaires (optionnel)
        
        Format des noms d'équipes:
        - Noms sans genre: "LYON 1 (1)" - le genre est spécifié dans la colonne Genre
        
        Returns:
            Dictionnaire {(equipe1_id, equipe2_id): ContrainteTemporelle}
            Clé = (nom|genre, nom|genre) ex: ("LYON 1 (1)|M", "LYON 2 (1)|M")
            La clé est un tuple trié alphabétiquement pour détection bidirectionnelle
        """
        from pycalendar.core.models import ContrainteTemporelle
        
        df = self.config.lire_feuille('Contraintes_Temporelles')
        if df is None or df.empty:
            logger.debug("Pas de feuille Contraintes_Temporelles")
            return {}
        
        contraintes = {}
        
        for idx, row in df.iterrows():
            ligne_num = int(idx) + 2  # Numéro de ligne Excel (en-tête en ligne 1)
            
            eq1_str = str(row.get('Equipe_1', '')).strip()
            eq2_str = str(row.get('Equipe_2', '')).strip()
            genre_str = str(row.get('Genre', '')).strip().upper()
            type_contrainte = str(row.get('Type_Contrainte', '')).strip()
            semaine = row.get('Semaine')
            
            # Validation des champs obligatoires
            if not eq1_str or pd.isna(row.get('Equipe_1')):
                logger.warning(f"Ligne {ligne_num}: Equipe_1 manquante, ligne ignorée")
                continue
            if not eq2_str or pd.isna(row.get('Equipe_2')):
                logger.warning(f"Ligne {ligne_num}: Equipe_2 manquante, ligne ignorée")
                continue
            if not genre_str or pd.isna(row.get('Genre')):
                logger.warning(f"Ligne {ligne_num}: Genre manquant, ligne ignorée")
                continue
            if not type_contrainte or pd.isna(row.get('Type_Contrainte')):
                logger.warning(f"Ligne {ligne_num}: Type_Contrainte manquant, ligne ignorée")
                continue
            if pd.isna(semaine):
                logger.warning(f"Ligne {ligne_num}: Semaine manquante, ligne ignorée")
                continue
            
            # Valider le genre
            if genre_str not in ['M', 'F']:
                logger.warning(f"Ligne {ligne_num}: Genre invalide '{genre_str}', doit être 'M' ou 'F', ligne ignorée")
                continue
            
            # Valider le type
            if type_contrainte not in ['Avant', 'Apres']:
                logger.warning(f"Ligne {ligne_num}: Type_Contrainte invalide '{type_contrainte}', ligne ignorée")
                continue
            
            # Valider la semaine
            try:
                semaine_int = int(semaine)
                if semaine_int < 1 or semaine_int > 52:
                    logger.warning(f"Ligne {ligne_num}: Semaine invalide ({semaine_int}), doit être entre 1 et 52")
                    continue
            except (ValueError, TypeError):
                logger.warning(f"Ligne {ligne_num}: Semaine invalide '{semaine}', doit être un nombre")
                continue
            
            # Parser les horaires possibles (optionnel)
            horaires_possibles = None
            horaires_col = row.get('Horaires_Possibles')
            if pd.notna(horaires_col) and str(horaires_col).strip():
                horaires_str = str(horaires_col).strip()
                # Séparer par virgule ou point-virgule
                horaires_possibles = [h.strip() for h in horaires_str.replace(';', ',').split(',') if h.strip()]
            
            # Créer les identifiants pour la clé
            # Format: "NOM|GENRE" - les noms sont déjà sans genre, le genre vient de la colonne Genre
            eq1_id = f"{eq1_str}|{genre_str}"
            eq2_id = f"{eq2_str}|{genre_str}"
            
            # Créer clé triée pour détection bidirectionnelle
            cle = tuple(sorted([eq1_id, eq2_id]))
            
            # Créer la contrainte
            contrainte = ContrainteTemporelle(
                type_contrainte=type_contrainte,
                semaine_limite=semaine_int,
                horaires_possibles=horaires_possibles
            )
            
            # Si une contrainte existe déjà pour cette paire, logger un warning
            if cle in contraintes:
                logger.warning(
                    f"Ligne {ligne_num}: Contrainte en doublon pour {eq1_str} ↔ {eq2_str}, "
                    f"la nouvelle contrainte écrase l'ancienne"
                )
            
            contraintes[cle] = contrainte
        
        logger.info(f"Contraintes temporelles chargées: {len(contraintes)} paires d'équipes")
        return contraintes
    
    def charger_types_poules(self) -> Dict[str, str]:
        """
        Charge les types de poules depuis la feuille Types_Poules.
        
        Returns:
            Dictionnaire {nom_poule: type} où type est "Classique" ou "Aller-Retour"
            Par défaut, toutes les poules non spécifiées sont "Classique"
        """
        df = self.config.lire_feuille('Types_Poules')
        
        if df is None or df.empty:
            logger.info("Aucun type de poule défini, toutes les poules seront 'Classique'")
            return {}
        
        types = {}
        for _, row in df.iterrows():
            poule = str(row.get('Poule', '')).strip()
            type_poule = str(row.get('Type', 'Classique')).strip()
            
            # Validation
            if not poule:
                continue
            
            # Normalisation du type
            if type_poule.lower() in ['aller-retour', 'aller retour', 'allerretour', 'ar']:
                type_poule = 'Aller-Retour'
            else:
                type_poule = 'Classique'
            
            types[poule] = type_poule
        
        logger.info(f"Types de poules chargés: {len(types)} poules configurées")
        if types:
            nb_aller_retour = sum(1 for t in types.values() if t == 'Aller-Retour')
            nb_classique = len(types) - nb_aller_retour
            logger.info(f"  - {nb_classique} poule(s) Classique")
            logger.info(f"  - {nb_aller_retour} poule(s) Aller-Retour")
        
        return types
    
    def charger_groupes_non_simultaneite(self) -> Dict[str, List[str]]:
        """
        Charge les groupes d'équipes/institutions à ne pas faire jouer simultanément.
        
        Returns:
            Dictionnaire {nom_groupe: [liste_entites]} où entites sont les équipes/institutions
            du groupe qui ne doivent pas jouer simultanément
        """
        df = self.config.lire_feuille('Groupes_Non_Simultaneite')
        
        if df is None or df.empty:
            logger.info("Aucun groupe de non-simultanéité défini")
            return {}
        
        groupes = {}
        for _, row in df.iterrows():
            nom_groupe = str(row.get('Nom_Groupe', '')).strip()
            entites_str = str(row.get('Entites', '')).strip()
            
            if not nom_groupe or not entites_str:
                continue
            
            # Parser les entités (séparées par des virgules)
            entites = [entite.strip() for entite in entites_str.split(',') if entite.strip()]
            
            if entites:
                groupes[nom_groupe] = entites
        
        logger.info(f"Groupes de non-simultanéité chargés: {len(groupes)} groupe(s)")
        for nom_groupe, entites in groupes.items():
            logger.info(f"  - {nom_groupe}: {len(entites)} entité(s)")
        
        return groupes
    
    def charger_matchs_fixes(self) -> List[Match]:
        """
        Charge les matchs déjà joués ou planifiés depuis la feuille Matchs_Fixes.
        
        Ces matchs seront intégrés directement dans la solution finale et
        ne seront pas inclus dans la génération automatique.
        
        Structure attendue:
        - Equipe_1: Nom de la première équipe
        - Equipe_2: Nom de la deuxième équipe
        - Genre: Genre du match (F ou M)
        - Poule: Code de la poule
        - Semaine: Numéro de semaine
        - Horaire: Heure du match (HH:MM)
        - Gymnase: Nom du gymnase
        - Score: Score du match si joué (optionnel)
        - Type_Competition: CFE, CFU, Acad, ou Autre
        - Remarques: Informations complémentaires (optionnel)
        
        Returns:
            Liste des matchs fixes avec leurs informations complètes
        """
        df = self.config.lire_feuille('Matchs_Fixes')
        if df is None or df.empty:
            logger.info("Aucun match fixe trouvé")
            return []
        
        matchs_fixes = []
        
        # Charger les équipes pour pouvoir créer les objets Match complets
        equipes = self.charger_equipes()
        # Utiliser id_unique comme clé pour éviter les collisions entre équipes de même nom mais genre différent
        # Format: "NOM|GENRE" (ex: "LYON 1 (1)|M", "LYON 1 (1)|F")
        equipes_dict = {eq.id_unique: eq for eq in equipes}
        # Créer aussi un index par nom seul (pour les matchs sans genre spécifié)
        # ATTENTION: Si plusieurs équipes ont le même nom, on garde la dernière (comportement de fallback)
        equipes_dict_by_nom = {eq.nom: eq for eq in equipes}
        
        for ligne_idx, (idx, row) in enumerate(df.iterrows()):
            ligne_num = ligne_idx + 2  # Numéro de ligne dans Excel (header + 1-based)
            equipe1_nom = str(row.get('Equipe_1', '')).strip()
            equipe2_nom = str(row.get('Equipe_2', '')).strip()
            genre = str(row.get('Genre', '')).strip().upper()
            poule = str(row.get('Poule', '')).strip()
            
            # Nettoyer les données d'entrée
            if pd.isna(equipe1_nom) or equipe1_nom.lower() == 'nan':
                equipe1_nom = ''
            if pd.isna(equipe2_nom) or equipe2_nom.lower() == 'nan':
                equipe2_nom = ''
            if pd.isna(genre) or genre.lower() == 'nan':
                genre = ''
            if pd.isna(poule) or poule.lower() == 'nan':
                poule = ''
            
            if not equipe1_nom or not equipe2_nom:
                logger.warning(f"Ligne {ligne_num}: équipes manquantes, ligne ignorée")
                continue
            
            # Recherche des équipes avec priorité au genre
            # Priorité 1: Utiliser le genre du match fixé pour construire l'id_unique
            # Priorité 2: Recherche par nom seul (fallback si pas de genre ou équipe introuvable)
            equipe1 = None
            equipe2 = None
            
            if genre in ['F', 'M']:
                # Si le genre est spécifié, chercher avec id_unique (nom|genre)
                equipe1_id = f"{equipe1_nom}|{genre}"
                equipe2_id = f"{equipe2_nom}|{genre}"
                equipe1 = equipes_dict.get(equipe1_id)
                equipe2 = equipes_dict.get(equipe2_id)
            
            # Fallback: chercher par nom seul si pas trouvé avec le genre
            if not equipe1:
                equipe1 = equipes_dict_by_nom.get(equipe1_nom)
            if not equipe2:
                equipe2 = equipes_dict_by_nom.get(equipe2_nom)
            
            # Vérifier que les équipes existent, sinon créer des équipes temporaires pour les externes
            if not equipe1:
                # Déterminer le genre pour l'équipe externe
                genre_equipe = genre if genre in ['F', 'M'] else extraire_genre_depuis_poule(poule)
                
                # Créer une équipe temporaire pour les équipes hors championnat
                equipe1 = Equipe(
                    nom=equipe1_nom,
                    poule=poule,
                    institution="EXTERNE",  # Marquer comme équipe externe
                    genre=genre_equipe,  # Utiliser le genre déterminé en majuscules
                    numero_equipe=""
                )
                logger.info(f"Ligne {ligne_num}: équipe externe '{equipe1_nom}' créée pour match fixe (genre: {genre_equipe or 'non défini'})")
            
            if not equipe2:
                # Déterminer le genre pour l'équipe externe
                genre_equipe = genre if genre in ['F', 'M'] else extraire_genre_depuis_poule(poule)
                
                # Créer une équipe temporaire pour les équipes hors championnat
                equipe2 = Equipe(
                    nom=equipe2_nom,
                    poule=poule,
                    institution="EXTERNE",  # Marquer comme équipe externe
                    genre=genre_equipe,  # Utiliser le genre déterminé en majuscules
                    numero_equipe=""
                )
                logger.info(f"Ligne {ligne_num}: équipe externe '{equipe2_nom}' créée pour match fixe (genre: {genre_equipe or 'non défini'})")
            
            semaine = row.get('Semaine')
            if pd.isna(semaine):
                logger.warning(f"Ligne {ligne_num}: semaine manquante pour {equipe1_nom} vs {equipe2_nom}, ligne ignorée")
                continue
            try:
                semaine = int(semaine)
            except (ValueError, TypeError):
                logger.warning(f"Ligne {ligne_num}: semaine invalide '{semaine}' pour {equipe1_nom} vs {equipe2_nom}, ligne ignorée")
                continue
            
            horaire = str(row.get('Horaire', '')).strip()
            if not horaire or pd.isna(horaire):
                logger.warning(f"Ligne {ligne_num}: horaire manquant pour {equipe1_nom} vs {equipe2_nom}, ligne ignorée")
                continue
            
            gymnase = str(row.get('Gymnase', '')).strip()
            if not gymnase or pd.isna(gymnase):
                logger.warning(f"Ligne {ligne_num}: gymnase manquant pour {equipe1_nom} vs {equipe2_nom}, ligne ignorée")
                continue
            
            # Informations optionnelles
            score = row.get('Score')
            score_str = str(score).strip() if pd.notna(score) and str(score).strip() else None
            
            type_competition = row.get('Type_Competition')
            type_competition_str = str(type_competition).strip() if pd.notna(type_competition) else 'Acad'
            
            remarques = row.get('Remarques')
            remarques_str = str(remarques).strip() if pd.notna(remarques) and str(remarques).strip() else ''
            
            # Créer le match (on utilise un créneau fictif pour l'instant)
            # Le créneau sera créé/trouvé lors de l'intégration dans le pipeline
            match = Match(
                equipe1=equipe1,
                equipe2=equipe2,
                poule=poule,
                creneau=None,  # Sera assigné plus tard dans le pipeline
                metadata={
                    'fixe': True,
                    'semaine': semaine,
                    'horaire': horaire,
                    'gymnase': gymnase,
                    'score': score_str,
                    'type_competition': type_competition_str,
                    'remarques': remarques_str,
                    'genre_fixe': genre if genre in ['F', 'M'] else None  # Préserver le genre du match fixé
                }
            )
            
            matchs_fixes.append(match)
        
        logger.info(f"{len(matchs_fixes)} matchs fixes chargés depuis la feuille Matchs_Fixes")
        return matchs_fixes
    
    def get_poules_dict(self, equipes: List[Equipe]) -> Dict[str, List[Equipe]]:
        """Group teams by pool."""
        poules = {}
        for equipe in equipes:
            if equipe.poule not in poules:
                poules[equipe.poule] = []
            poules[equipe.poule].append(equipe)
        return poules


if __name__ == "__main__":
    # Configuration du logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test du loader
    print("\n" + "="*80)
    print("🧪 TEST DU LOADER DE CONFIGURATION CENTRAL")
    print("="*80 + "\n")
    
    try:
        loader = DataLoader("exemple/config_exemple.xlsx")
        
        print("📊 Chargement des équipes...")
        equipes = loader.charger_equipes()
        print(f"✅ {len(equipes)} équipes chargées\n")
        
        # Afficher quelques exemples
        print("📝 Exemples d'équipes avec contraintes :")
        for i, equipe in enumerate(equipes[:5]):
            print(f"\n{i+1}. {equipe.nom_complet}")
            print(f"   Institution: {equipe.institution}")
            print(f"   Genre: {equipe.genre}")
            print(f"   Poule: {equipe.poule}")
            print(f"   Horaires préférés: {equipe.horaires_preferes}")
            print(f"   Lieux préférés: {equipe.lieux_preferes}")
            print(f"   Indisponibilités: {len(equipe.semaines_indisponibles)} semaines")
        
        print("\n" + "="*80)
        print("✅ Test réussi !")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"❌ Erreur : {e}")
        import traceback
        traceback.print_exc()
