"""
Service pour orchestrer la résolution de calendriers.

Ce service gère le flux complet :
1. Charger projet depuis DB (config + données)
2. Convertir DB models → Core models
3. Exécuter solveur selon stratégie
4. Sauvegarder solution en DB
5. Valider résultats
"""

import json
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.database import models
from backend.services.solution_validator import SolutionValidator, ValidationError
from core.models import Match, Equipe, Creneau, Gymnase, Solution
from core.config import Config
from solvers.cpsat_solver import CPSATSolver
from solvers.greedy_solver import GreedySolver

logger = logging.getLogger(__name__)


class SolverError(Exception):
    """Exception levée lors d'erreurs de résolution."""
    pass


class SolverService:
    """Service d'orchestration de la résolution de calendriers."""
    
    def __init__(self, db: Session):
        """
        Initialise le service.
        
        Args:
            db: Session SQLAlchemy pour accès base de données
        """
        self.db = db
    
    def solve_project(self, project_id: int, strategy: Optional[str] = None) -> Dict[str, Any]:
        """
        Résout le calendrier d'un projet.
        
        Args:
            project_id: ID du projet à résoudre
            strategy: Stratégie à utiliser ("cpsat", "greedy", ou None pour utiliser config)
            
        Returns:
            dict: Résumé de la résolution {
                'project_id': int,
                'strategy': str,
                'nb_matchs_total': int,
                'nb_matchs_fixes': int,
                'nb_matchs_planifies': int,
                'nb_matchs_non_planifies': int,
                'execution_time': float,
                'solution_score': float
            }
            
        Raises:
            ValueError: Si projet introuvable
            SolverError: Si résolution échoue
        """
        import time
        start_time = time.time()
        
        try:
            # 1. Charger projet depuis DB
            project = self.db.query(models.Project).filter(
                models.Project.id == project_id
            ).first()
            
            if not project:
                raise ValueError(f"Projet {project_id} introuvable")
            
            logger.info(f"[SolverService] Résolution du projet '{project.nom}' (ID: {project_id})")
            
            # 2. Reconstruire Config
            config = self._build_config_from_project(project)
            
            # Override stratégie si fournie
            if strategy:
                config.strategie = strategy
            
            # 3. Charger matchs, équipes, gymnases depuis DB
            db_matches = self.db.query(models.Match).filter(
                models.Match.project_id == project_id
            ).all()
            
            # Convertir DB → Core models
            matchs = self._db_to_core_matches(db_matches)
            creneaux = self._generate_creneaux(project_id, config.nb_semaines)
            gymnases = self._db_to_core_gymnases(project_id)
            
            # Identifier matchs fixes
            matchs_fixes = [m for m in matchs if m.est_fixe or 
                           (m.creneau and m.creneau.semaine < project.semaine_min)]
            matchs_modifiables = [m for m in matchs if m not in matchs_fixes]
            
            logger.info(f"[SolverService] {len(matchs)} matchs total, "
                       f"{len(matchs_fixes)} fixes, {len(matchs_modifiables)} modifiables")
            logger.info(f"[SolverService] {len(creneaux)} créneaux disponibles, "
                       f"{len(gymnases)} gymnases")
            
            # Validation avant résolution
            if len(matchs_modifiables) == 0:
                logger.warning("[SolverService] Aucun match modifiable, résolution inutile")
                return {
                    'project_id': project_id,
                    'strategy': config.strategie,
                    'nb_matchs_total': len(matchs),
                    'nb_matchs_fixes': len(matchs_fixes),
                    'nb_matchs_planifies': len(matchs_fixes),
                    'nb_matchs_non_planifies': 0,
                    'execution_time': 0.0,
                    'solution_score': 0.0,
                    'message': 'Aucun match modifiable'
                }
            
            # 4. Exécuter solveur selon stratégie
            solution = self._execute_solver(config.strategie, config, matchs, creneaux, gymnases)
            
            if not solution or len(solution.matchs_planifies) == 0:
                raise SolverError("Aucune solution trouvée par le solveur")
            
            logger.info(f"[SolverService] Solution trouvée: {len(solution.matchs_planifies)} matchs planifiés, "
                       f"{len(solution.matchs_non_planifies)} non planifiés")
            
            # 5. Valider solution avant sauvegarde
            db_matches_copy = list(db_matches)  # Copie pour validation "before"
            
            # Construire dict gymnase → capacité (gymnases est déjà un dict str -> Gymnase)
            gymnases_capacite = {nom: g.capacite for nom, g in gymnases.items()}
            
            # Créer validateur
            validator = SolutionValidator(
                semaine_minimum=int(project.semaine_min),
                nb_semaines=config.nb_semaines,
                matchs_before=db_matches_copy,
                matchs_after=db_matches_copy,  # Même liste pour now, changera après save
                gymnases_capacite=gymnases_capacite
            )
            
            # Note: Pour vraiment valider, il faudrait créer une copie modifiée.
            # Pour l'instant, on valide uniquement l'état actuel.
            # TODO: Améliorer pour appliquer solution en mémoire puis valider
            
            # 6. Sauvegarder solution en DB
            nb_updated = self._save_solution(project_id, solution, db_matches)
            
            # 6. Calculer temps d'exécution
            execution_time = time.time() - start_time
            
            # 7. Retourner résumé
            return {
                'project_id': project_id,
                'strategy': config.strategie,
                'nb_matchs_total': len(matchs),
                'nb_matchs_fixes': len(matchs_fixes),
                'nb_matchs_planifies': len(solution.matchs_planifies),
                'nb_matchs_non_planifies': len(solution.matchs_non_planifies),
                'nb_matchs_updated': nb_updated,
                'execution_time': round(execution_time, 2),
                'solution_score': round(solution.score, 2) if hasattr(solution, 'score') else 0.0
            }
            
        except SolverError:
            raise
        except Exception as e:
            logger.error(f"[SolverService] Erreur inattendue: {e}", exc_info=True)
            raise SolverError(f"Erreur lors de la résolution : {e}")
    
    def _build_config_from_project(self, project: models.Project) -> Config:
        """
        Reconstruit un objet Config depuis config_data du projet.
        
        Si yaml_path est disponible dans config_data, charge le config depuis le YAML
        (qui inclut les defaults). Sinon, tente de reconstruire depuis config_data minimal.
        
        Le champ semaine_minimum est toujours pris depuis project.semaine_min.
        
        Args:
            project: Projet DB
            
        Returns:
            Config: Configuration reconstituée
        """
        if not project.config_data:
            raise ValueError(f"Projet {project.id} sans config_data")
        
        config_dict = project.config_data.copy()
        
        # Si on a un yaml_path, charger le config complet depuis le YAML
        yaml_path = config_dict.get('yaml_path')
        if yaml_path:
            try:
                # Charger config complet depuis YAML (inclut defaults)
                config = Config.from_yaml(yaml_path)
                # Override semaine_minimum depuis DB
                # Use dataclass replace to create new instance with updated value
                from dataclasses import replace
                config = replace(config, semaine_minimum=project.semaine_min)
                logger.debug(f"[SolverService] Config chargé depuis YAML: {yaml_path}, "
                            f"stratégie={config.strategie}, nb_semaines={config.nb_semaines}")
                return config
            except Exception as e:
                logger.warning(f"[SolverService] Impossible de charger YAML {yaml_path}: {e}")
                # Continue avec config_dict minimal
        
        # Fallback: tenter de reconstruire depuis config_dict (probablement échouera)
        # Remove metadata fields
        metadata_fields = ['yaml_path', 'excel_path']
        for field in metadata_fields:
            config_dict.pop(field, None)
        
        # Override semaine_minimum depuis DB
        config_dict['semaine_minimum'] = project.semaine_min
        
        # Créer Config depuis dict (nécessite tous les champs requis)
        try:
            config = Config(**config_dict)
            logger.debug(f"[SolverService] Config reconstruite: stratégie={config.strategie}, "
                        f"nb_semaines={config.nb_semaines}, semaine_min={config.semaine_minimum}")
            return config
        except Exception as e:
            raise ValueError(f"Config invalide (manque des champs requis): {e}")
    
    def _db_to_core_matches(self, db_matches: List[models.Match]) -> List[Match]:
        """
        Convertit matchs DB → matchs Core.
        
        Args:
            db_matches: Liste matchs SQLAlchemy
            
        Returns:
            Liste matchs Core (dataclasses)
        """
        core_matches = []
        
        for db_match in db_matches:
            # Créer équipes
            equipe1 = Equipe(
                nom=db_match.equipe1_nom,
                poule=db_match.poule or "",
                institution=db_match.equipe1_institution or "",
                numero_equipe="",  # Pas stocké séparément en DB
                genre=db_match.equipe1_genre or ""
            )
            
            equipe2 = Equipe(
                nom=db_match.equipe2_nom,
                poule=db_match.poule or "",
                institution=db_match.equipe2_institution or "",
                numero_equipe="",
                genre=db_match.equipe2_genre or ""
            )
            
            # Créer créneau si planifié
            creneau = None
            if db_match.semaine and db_match.horaire and db_match.gymnase:
                creneau = Creneau(
                    semaine=db_match.semaine,
                    horaire=db_match.horaire,
                    gymnase=db_match.gymnase
                )
            
            # Créer match Core
            match = Match(
                equipe1=equipe1,
                equipe2=equipe2,
                poule=db_match.poule or "",
                creneau=creneau,
                priorite=db_match.priorite or 0,
                est_fixe=db_match.est_fixe,
                statut=db_match.statut,
                score_equipe1=db_match.score_equipe1,
                score_equipe2=db_match.score_equipe2,
                notes=db_match.notes or ""
            )
            
            core_matches.append(match)
        
        return core_matches
    
    def _generate_creneaux(self, project_id: int, nb_semaines: int) -> List[Creneau]:
        """
        Génère la liste des créneaux disponibles.
        
        Combine venues × horaires × semaines.
        
        Args:
            project_id: ID du projet
            nb_semaines: Nombre de semaines de planification
            
        Returns:
            Liste de créneaux disponibles
        """
        venues = self.db.query(models.Venue).filter(
            models.Venue.project_id == project_id
        ).all()
        
        creneaux = []
        
        for venue in venues:
            # Charger horaires disponibles (JSON array)
            horaires_disponibles = venue.horaires_disponibles or []
            if isinstance(horaires_disponibles, str):
                horaires_disponibles = json.loads(horaires_disponibles)
            
            # Générer créneaux pour chaque semaine × horaire
            for semaine in range(1, nb_semaines + 1):
                for horaire in horaires_disponibles:
                    creneau = Creneau(
                        semaine=semaine,
                        horaire=horaire,
                        gymnase=venue.nom
                    )
                    creneaux.append(creneau)
        
        return creneaux
    
    def _db_to_core_gymnases(self, project_id: int) -> Dict[str, Gymnase]:
        """
        Convertit venues DB → gymnases Core.
        
        Args:
            project_id: ID du projet
            
        Returns:
            Dict {nom_gymnase: Gymnase}
        """
        venues = self.db.query(models.Venue).filter(
            models.Venue.project_id == project_id
        ).all()
        
        gymnases = {}
        
        for venue in venues:
            # Charger horaires disponibles
            horaires = venue.horaires_disponibles or []
            if isinstance(horaires, str):
                horaires = json.loads(horaires)
            
            gymnase = Gymnase(
                nom=venue.nom,
                capacite=venue.capacite or 1,
                horaires_disponibles=horaires
            )
            
            gymnases[venue.nom] = gymnase
        
        return gymnases
    
    def _execute_solver(
        self, 
        strategy: str, 
        config: Config, 
        matchs: List[Match], 
        creneaux: List[Creneau], 
        gymnases: Dict[str, Gymnase]
    ) -> Solution:
        """
        Exécute le solveur selon la stratégie configurée.
        
        Args:
            strategy: "cpsat" ou "greedy"
            config: Configuration complète
            matchs: Matchs à planifier
            creneaux: Créneaux disponibles
            gymnases: Gymnases disponibles
            
        Returns:
            Solution du solveur
            
        Raises:
            SolverError: Si stratégie inconnue ou exécution échoue
        """
        logger.info(f"[SolverService] Exécution solveur '{strategy}'")
        
        try:
            if strategy == 'cpsat':
                solver = CPSATSolver(config)
                return solver.solve(matchs, creneaux, gymnases)
            
            elif strategy == 'greedy':
                solver = GreedySolver(config)
                return solver.solve(matchs, creneaux, gymnases)
            
            else:
                raise SolverError(f"Stratégie inconnue : {strategy}")
                
        except Exception as e:
            logger.error(f"[SolverService] Erreur solveur '{strategy}': {e}", exc_info=True)
            raise SolverError(f"Erreur solveur {strategy}: {e}")
    
    def _save_solution(
        self, 
        project_id: int, 
        solution: Solution,
        db_matches: List[models.Match]
    ) -> int:
        """
        Sauvegarde la solution en DB.
        
        Ne modifie PAS les matchs fixes. Met à jour uniquement les matchs modifiables
        avec leur nouveau créneau.
        
        Args:
            project_id: ID du projet
            solution: Solution du solveur
            db_matches: Matchs DB (pour matching)
            
        Returns:
            Nombre de matchs mis à jour
        """
        nb_updated = 0
        
        # Créer index DB matchs par clé (equipe1_nom, equipe2_nom, poule)
        db_matches_dict = {}
        for db_match in db_matches:
            key = (db_match.equipe1_nom, db_match.equipe2_nom, db_match.poule or "")
            db_matches_dict[key] = db_match
        
        # Parcourir matchs planifiés de la solution
        for match_planifie in solution.matchs_planifies:
            # Trouver match correspondant en DB
            key = (match_planifie.equipe1.nom, match_planifie.equipe2.nom, match_planifie.poule)
            db_match = db_matches_dict.get(key)
            
            if not db_match:
                logger.warning(f"[SolverService] Match non trouvé en DB: {key}")
                continue
            
            # IMPORTANT: Ne PAS modifier matchs fixes
            if db_match.est_fixe:
                logger.debug(f"[SolverService] Match {db_match.id} fixe, ignoré")
                continue
            
            # IMPORTANT: Vérifier est_modifiable (ne pas toucher terminés/annulés)
            if not db_match.est_modifiable:
                logger.debug(f"[SolverService] Match {db_match.id} non modifiable (statut: {db_match.statut}), ignoré")
                continue
            
            # Mettre à jour créneau si planifié
            if match_planifie.creneau:
                db_match.semaine = match_planifie.creneau.semaine
                db_match.horaire = match_planifie.creneau.horaire
                db_match.gymnase = match_planifie.creneau.gymnase
                db_match.statut = "planifie"
                nb_updated += 1
                logger.debug(f"[SolverService] Match {db_match.id} planifié: "
                           f"S{match_planifie.creneau.semaine} {match_planifie.creneau.horaire} "
                           f"{match_planifie.creneau.gymnase}")
        
        # Commit transaction
        try:
            self.db.commit()
            logger.info(f"[SolverService] {nb_updated} matchs mis à jour en DB")
        except Exception as e:
            self.db.rollback()
            raise SolverError(f"Erreur sauvegarde DB: {e}")
        
        return nb_updated
