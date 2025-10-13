"""
Validateur de solution de calendrier.

Vérifie que la solution respecte toutes les contraintes critiques :
- Matchs fixes non modifiés
- Semaine >= semaine_minimum  
- Pas de conflits équipes (une équipe ne joue qu'une fois par semaine)
- Pas de conflits gymnases (capacité respectée)
"""

import logging
from typing import List, Tuple, Dict, Set, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MatchSnapshot:
    """Snapshot d'un match pour validation (valeurs Python pures)."""
    id: int
    equipe1_nom: str
    equipe1_institution: Optional[str]
    equipe2_nom: str
    equipe2_institution: Optional[str]
    semaine: Optional[int]
    horaire: Optional[str]
    gymnase: Optional[str]
    est_fixe: bool


class SolutionValidator:
    """Validateur de solution de planification."""
    
    def __init__(
        self, 
        semaine_minimum: int,
        nb_semaines: int,
        matchs_before: List,  # List[models.Match]
        matchs_after: List,  # List[models.Match]
        gymnases_capacite: Dict[str, int]
    ):
        """
        Initialise le validateur.
        
        Args:
            semaine_minimum: Semaine minimum pour planification
            nb_semaines: Nombre total de semaines
            matchs_before: Matchs avant résolution
            matchs_after: Matchs après résolution
            gymnases_capacite: Dict {nom_gymnase: capacite}
        """
        self.semaine_minimum = semaine_minimum
        self.nb_semaines = nb_semaines
        self.gymnases_capacite = gymnases_capacite
        
        # Convertir en snapshots (valeurs Python pures)
        self.matchs_before = {
            m.id: self._to_snapshot(m) for m in matchs_before
        }
        self.matchs_after = {
            m.id: self._to_snapshot(m) for m in matchs_after
        }
    
    @staticmethod
    def _to_snapshot(match) -> MatchSnapshot:
        """Convertit un modèle Match en snapshot avec valeurs Python."""
        return MatchSnapshot(
            id=int(match.id),
            equipe1_nom=str(match.equipe1_nom),
            equipe1_institution=str(match.equipe1_institution) if match.equipe1_institution else None,
            equipe2_nom=str(match.equipe2_nom),
            equipe2_institution=str(match.equipe2_institution) if match.equipe2_institution else None,
            semaine=int(match.semaine) if match.semaine is not None else None,
            horaire=str(match.horaire) if match.horaire else None,
            gymnase=str(match.gymnase) if match.gymnase else None,
            est_fixe=bool(match.est_fixe)
        )
    
    def validate(self) -> Tuple[bool, List[str]]:
        """
        Valide la solution.
        
        Returns:
            (bool, List[str]): (est_valide, liste_erreurs)
        """
        errors = []
        
        # 1. Vérifier matchs fixes non modifiés
        errors.extend(self._validate_matchs_fixes())
        
        # 2. Vérifier semaine >= semaine_minimum (pour matchs non fixes)
        errors.extend(self._validate_semaine_minimum())
        
        # 3. Vérifier pas de conflits équipes (même semaine)
        errors.extend(self._validate_conflits_equipes())
        
        # 4. Vérifier capacité gymnases respectée
        errors.extend(self._validate_capacite_gymnases())
        
        is_valid = len(errors) == 0
        
        if is_valid:
            logger.info("[SolutionValidator] Solution validée avec succès")
        else:
            logger.warning(f"[SolutionValidator] Solution invalide: {len(errors)} erreurs")
            for error in errors[:5]:  # Log premiers 5 erreurs
                logger.warning(f"  - {error}")
        
        return is_valid, errors
    
    def _validate_matchs_fixes(self) -> List[str]:
        """Vérifie que les matchs fixes n'ont pas été modifiés."""
        errors = []
        
        for match_id, match_before in self.matchs_before.items():
            if not match_before.est_fixe:
                continue
            
            match_after = self.matchs_after.get(match_id)
            
            if not match_after:
                errors.append(f"Match fixe {match_id} manquant dans solution")
                continue
            
            # Vérifier semaine non modifiée
            if match_before.semaine != match_after.semaine:
                errors.append(
                    f"Match fixe {match_id}: semaine modifiée "
                    f"({match_before.semaine} → {match_after.semaine})"
                )
            
            # Vérifier horaire non modifié
            if match_before.horaire != match_after.horaire:
                errors.append(
                    f"Match fixe {match_id}: horaire modifié "
                    f"({match_before.horaire} → {match_after.horaire})"
                )
            
            # Vérifier gymnase non modifié
            if match_before.gymnase != match_after.gymnase:
                errors.append(
                    f"Match fixe {match_id}: gymnase modifié "
                    f"({match_before.gymnase} → {match_after.gymnase})"
                )
        
        return errors
    
    def _validate_semaine_minimum(self) -> List[str]:
        """Vérifie que les matchs non fixes respectent semaine_minimum."""
        errors = []
        
        for match_after in self.matchs_after.values():
            # Skip si match fixe (autorisé à être avant semaine_minimum)
            if match_after.est_fixe:
                continue
            
            # Skip si non planifié
            if match_after.semaine is None:
                continue
            
            # Vérifier semaine >= semaine_minimum
            if match_after.semaine < self.semaine_minimum:
                errors.append(
                    f"Match {match_after.id}: semaine {match_after.semaine} < "
                    f"semaine_minimum {self.semaine_minimum}"
                )
        
        return errors
    
    def _validate_conflits_equipes(self) -> List[str]:
        """Vérifie qu'une équipe ne joue qu'une fois par semaine."""
        errors = []
        
        for semaine in range(1, self.nb_semaines + 1):
            # Matchs planifiés cette semaine
            matchs_semaine = [
                m for m in self.matchs_after.values() 
                if m.semaine == semaine
            ]
            
            # Tracker équipes déjà vues
            equipes_jouees: Set[str] = set()
            
            for match in matchs_semaine:
                equipe1_key = self._equipe_key(match.equipe1_nom, match.equipe1_institution)
                equipe2_key = self._equipe_key(match.equipe2_nom, match.equipe2_institution)
                
                # Vérifier équipe 1
                if equipe1_key in equipes_jouees:
                    errors.append(
                        f"Équipe {match.equipe1_nom} joue 2 fois semaine {semaine} "
                        f"(match {match.id})"
                    )
                
                # Vérifier équipe 2
                if equipe2_key in equipes_jouees:
                    errors.append(
                        f"Équipe {match.equipe2_nom} joue 2 fois semaine {semaine} "
                        f"(match {match.id})"
                    )
                
                equipes_jouees.add(equipe1_key)
                equipes_jouees.add(equipe2_key)
        
        return errors
    
    def _validate_capacite_gymnases(self) -> List[str]:
        """Vérifie que la capacité des gymnases est respectée."""
        errors = []
        
        for semaine in range(1, self.nb_semaines + 1):
            # Grouper matchs par (semaine, horaire, gymnase)
            matchs_par_creneau: Dict[Tuple[int, str, str], List[MatchSnapshot]] = {}
            
            for match in self.matchs_after.values():
                if match.semaine != semaine or not match.horaire or not match.gymnase:
                    continue
                
                # Type narrowing: on sait que semaine, horaire, gymnase sont non-None
                assert match.semaine is not None
                assert match.horaire is not None
                assert match.gymnase is not None
                
                key = (match.semaine, match.horaire, match.gymnase)
                if key not in matchs_par_creneau:
                    matchs_par_creneau[key] = []
                matchs_par_creneau[key].append(match)
            
            # Vérifier capacité pour chaque créneau
            for (sem, horaire, gymnase), matchs in matchs_par_creneau.items():
                capacite = self.gymnases_capacite.get(gymnase, 1)
                nb_matchs = len(matchs)
                
                if nb_matchs > capacite:
                    errors.append(
                        f"Gymnase {gymnase} dépassé semaine {sem} {horaire}: "
                        f"{nb_matchs} matchs > capacité {capacite} "
                        f"(matchs: {[m.id for m in matchs]})"
                    )
        
        return errors
    
    @staticmethod
    def _equipe_key(nom: str, institution: Optional[str]) -> str:
        """Génère une clé unique pour une équipe."""
        return f"{institution or ''}|{nom}"


class ValidationError(Exception):
    """Exception levée quand la validation échoue."""
    
    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__(f"Validation échouée: {len(errors)} erreurs")
