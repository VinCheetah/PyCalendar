"""Service de synchronisation Excel/YAML → Base de données."""

import json
from pathlib import Path
from sqlalchemy.orm import Session
from typing import Optional

from core.config import Config
from data.data_source import DataSource
from generators.multi_pool_generator import MultiPoolGenerator
from backend.database import models


class SyncService:
    """Service de synchronisation YAML + Excel → Base de données."""
    
    def __init__(self, db: Session):
        """
        Initialize sync service.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def import_from_excel(
        self,
        yaml_path: str,
        project_name: Optional[str] = None,
        validate_excel: bool = False  # Validation désactivée par défaut (actualiser_config.py n'a pas --validate-only)
    ) -> models.Project:
        """
        Importe un projet depuis config YAML + Excel.
        
        Args:
            yaml_path: Chemin du fichier YAML (ex: "configs/config_volley.yaml")
            project_name: Nom du projet (optionnel, sinon déduit du sport/Excel)
            validate_excel: Si True, valider Excel avec actualiser_config.py avant import
        
        Returns:
            Project créé en DB avec Teams, Venues, Matches
        
        Raises:
            FileNotFoundError: Si YAML ou Excel introuvable
            ValueError: Si Excel invalide (structure incorrecte)
        """
        # 1. Charger config YAML
        print(f"📄 Chargement config YAML : {yaml_path}")
        config = Config.from_yaml(yaml_path)
        excel_path = config.fichier_donnees
        
        # Vérifier que le fichier Excel existe
        if not Path(excel_path).exists():
            raise FileNotFoundError(f"Fichier Excel introuvable : {excel_path}")
        
        print(f"📊 Fichier Excel détecté : {excel_path}")
        
        # 2. Validation Excel (optionnel)
        if validate_excel:
            print(f"🔍 Validation structure Excel...")
            is_valid = self._validate_excel_structure(excel_path)
            if not is_valid:
                raise ValueError(
                    f"Structure Excel invalide : {excel_path}\n"
                    f"Exécutez 'python actualiser_config.py {excel_path}' pour corriger"
                )
            print(f"✅ Structure Excel validée")
        
        # 3. Charger données Excel via DataSource
        print(f"📋 Chargement données Excel via DataSource...")
        data_source = DataSource(excel_path)
        
        # 4. Charger équipes et gymnases via DataSource
        print(f"🏐 Chargement équipes et gymnases...")
        equipes = data_source.charger_equipes()
        gymnases = data_source.charger_gymnases()
        
        print(f"  → {len(equipes)} équipes chargées")
        print(f"  → {len(gymnases)} gymnases chargés")
        
        # 5. Créer Project en DB
        sport = self._detect_sport(config)
        if not project_name:
            project_name = f"{sport.capitalize()} {config.nb_semaines} semaines"
        
        print(f"🏗️ Création projet : {project_name}")
        
        # Préparer config complète en JSON (inclut chemins YAML et Excel)
        config_data = {
            'yaml_path': str(Path(yaml_path).resolve()),
            'excel_path': str(Path(excel_path).resolve()),
            'nb_semaines': config.nb_semaines,
            'semaine_minimum': getattr(config, 'semaine_minimum', 1),
            'strategie': getattr(config, 'strategie', 'greedy'),
            'temps_max_secondes': getattr(config, 'temps_max_secondes', 60)
        }
        
        project = models.Project(
            nom=project_name,
            sport=sport,
            config_yaml_path=str(Path(yaml_path).resolve()),
            config_data=config_data,  # Config complète en JSON
            nb_semaines=config.nb_semaines,
            semaine_min=getattr(config, 'semaine_minimum', 1)  # YAML utilise "semaine_minimum"
        )
        self.db.add(project)
        self.db.flush()  # Obtenir project.id pour FK
        
        print(f"  → Project ID: {project.id}")
        
        # 6. Importer Teams
        print(f"👥 Import des équipes...")
        teams_created = 0
        
        for equipe in equipes:
            # Convertir horaires_preferes (liste Python) en JSON
            horaires_json = json.dumps(equipe.horaires_preferes) if hasattr(equipe, 'horaires_preferes') else None
            lieux_json = json.dumps(equipe.lieux_preferes) if hasattr(equipe, 'lieux_preferes') else None
            
            team = models.Team(
                project_id=project.id,
                nom=equipe.nom,
                institution=getattr(equipe, 'institution', None),
                numero_equipe=getattr(equipe, 'numero_equipe', None),
                genre=getattr(equipe, 'genre', None),
                poule=equipe.poule,
                horaires_preferes=horaires_json,
                lieux_preferes=lieux_json
            )
            self.db.add(team)
            teams_created += 1
        
        print(f"  → {teams_created} équipes créées")
        
        # 7. Importer Venues (gymnases)
        print(f"🏟️ Import des gymnases...")
        venues_created = 0
        
        for gymnase in gymnases:
            # Convertir horaires_disponibles en JSON
            horaires_json = json.dumps(gymnase.horaires_disponibles) if hasattr(gymnase, 'horaires_disponibles') else None
            
            venue = models.Venue(
                project_id=project.id,
                nom=gymnase.nom,
                capacite=getattr(gymnase, 'capacite', 1),
                horaires_disponibles=horaires_json
            )
            self.db.add(venue)
            venues_created += 1
        
        print(f"  → {venues_created} gymnases créés")
        
        # 8. Générer et importer Matches
        print(f"⚽ Génération des matchs...")
        
        # Grouper équipes par poule
        poules = data_source.get_poules_dict(equipes)  # Dict[str, List[Equipe]]
        
        # Générer matchs (round-robin par défaut, types_poules=False)
        generator = MultiPoolGenerator(types_poules=False)
        matchs_core = generator.generer_tous_matchs(poules)  # Liste[core.models.Match]
        
        print(f"  → {len(matchs_core)} matchs générés")
        
        # Importer matchs en DB
        print(f"💾 Import des matchs...")
        matches_created = 0
        
        for match in matchs_core:
            match_db = models.Match(
                project_id=project.id,
                equipe1_nom=match.equipe1.nom,
                equipe1_institution=getattr(match.equipe1, 'institution', None),
                equipe1_genre=getattr(match.equipe1, 'genre', None),
                equipe2_nom=match.equipe2.nom,
                equipe2_institution=getattr(match.equipe2, 'institution', None),
                equipe2_genre=getattr(match.equipe2, 'genre', None),
                poule=match.poule,
                semaine=None,  # Non planifiés initialement
                horaire=None,
                gymnase=None,
                est_fixe=getattr(match, 'est_fixe', False),
                statut=getattr(match, 'statut', 'a_planifier'),
                priorite=getattr(match, 'priorite', 0)
            )
            self.db.add(match_db)
            matches_created += 1
        
        print(f"  → {matches_created} matchs créés")
        
        # 9. Commit final
        self.db.commit()
        self.db.refresh(project)  # Recharger avec relations
        
        # Afficher résumé
        print(f"\n✅ Import terminé avec succès!")
        print(f"   📊 Projet : {project.nom} (ID: {project.id})")
        print(f"   👥 Équipes : {teams_created}")
        print(f"   🏟️ Gymnases : {venues_created}")
        print(f"   ⚽ Matchs : {matches_created}")
        
        return project
    
    def _detect_sport(self, config: Config) -> str:
        """
        Détecte le sport depuis le chemin Excel ou config YAML.
        
        Args:
            config: Configuration chargée
        
        Returns:
            Nom du sport détecté
        """
        excel_path = config.fichier_donnees.lower()
        
        if "volley" in excel_path or "volleyball" in excel_path:
            return "Volleyball"
        elif "hand" in excel_path or "handball" in excel_path:
            return "Handball"
        elif "basket" in excel_path:
            return "Basketball"
        elif "foot" in excel_path or "football" in excel_path:
            return "Football"
        else:
            return "Autre"
    
    def _validate_excel_structure(self, excel_path: str) -> bool:
        """
        Valide la structure Excel avec actualiser_config.py (optionnel).
        
        Note: actualiser_config.py n'a pas de mode --validate-only pour le moment.
        Cette méthode retourne toujours True sauf en cas d'erreur.
        
        Args:
            excel_path: Chemin du fichier Excel
        
        Returns:
            True si valide, False sinon
        """
        try:
            # OPTION 1 : Appel subprocess (si --validate-only existe)
            # import subprocess
            # result = subprocess.run(
            #     ["python", "actualiser_config.py", excel_path, "--validate-only"],
            #     capture_output=True,
            #     text=True,
            #     timeout=30
            # )
            # return result.returncode == 0
            
            # OPTION 2 : Pour l'instant, vérifier juste que le fichier existe
            if not Path(excel_path).exists():
                return False
            
            # TODO: Implémenter validation via import direct si nécessaire
            # from actualiser_config import valider_structure_excel
            # rapport = valider_structure_excel(excel_path)
            # return rapport.is_valid()
            
            return True  # Validation réussie (basique)
            
        except Exception as e:
            print(f"⚠️ Validation Excel échouée : {e}")
            return False
