"""Team-related constraints."""

from typing import Dict, Tuple
from pycalendar.core.models import Match, Creneau
from .base import Constraint


class TeamAvailabilityConstraint(Constraint):
    """Ensures both teams are available for the match at the specified time slot."""
    
    def __init__(self, weight: float = 1000.0):
        super().__init__(weight=weight, hard=True)
    
    def validate(self, match: Match, creneau: Creneau, solution_state: Dict) -> Tuple[bool, float]:
        # Vérifier la disponibilité avec l'horaire spécifique ET le gymnase
        # Le gymnase est important pour les disponibilités anticipées spécifiques
        if not match.equipe1.est_disponible(creneau.semaine, creneau.horaire, creneau.gymnase):
            return False, self.weight
        
        if not match.equipe2.est_disponible(creneau.semaine, creneau.horaire, creneau.gymnase):
            return False, self.weight
        
        return True, 0.0
    
    def get_name(self) -> str:
        return "TeamAvailability"


class MaxMatchesPerWeekConstraint(Constraint):
    """Ensures teams don't play too many matches per week.
    
    IMPORTANT: Utilise id_unique pour distinguer équipes de même nom mais genre différent.
    """
    
    def __init__(self, max_matches: int = 1, weight: float = 500.0):
        super().__init__(weight=weight, hard=True)
        self.max_matches = max_matches
    
    def validate(self, match: Match, creneau: Creneau, solution_state: Dict) -> Tuple[bool, float]:
        matchs_equipe1 = solution_state.get('equipes_semaines', {}).get(
            (match.equipe1.id_unique, creneau.semaine), 0
        )
        matchs_equipe2 = solution_state.get('equipes_semaines', {}).get(
            (match.equipe2.id_unique, creneau.semaine), 0
        )
        
        if matchs_equipe1 >= self.max_matches or matchs_equipe2 >= self.max_matches:
            return False, self.weight
        
        return True, 0.0
    
    def get_name(self) -> str:
        return "MaxMatchesPerWeek"


class TeamNotPlayingSimultaneouslyConstraint(Constraint):
    """Ensures a team doesn't play multiple matches at the same time.
    
    IMPORTANT: Utilise id_unique pour distinguer équipes de même nom mais genre différent.
    """
    
    def __init__(self, weight: float = 1000.0):
        super().__init__(weight=weight, hard=True)
    
    def validate(self, match: Match, creneau: Creneau, solution_state: Dict) -> Tuple[bool, float]:
        key = (creneau.semaine, creneau.horaire)
        equipes_au_creneau = solution_state.get('equipes_creneaux', {}).get(key, set())
        
        if match.equipe1.id_unique in equipes_au_creneau or match.equipe2.id_unique in equipes_au_creneau:
            return False, self.weight
        
        return True, 0.0
    
    def get_name(self) -> str:
        return "TeamNotPlayingSimultaneously"
