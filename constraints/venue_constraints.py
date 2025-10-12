"""Venue-related constraints."""

from typing import Dict, Tuple
from core.models import Match, Creneau, Gymnase
from .base import Constraint


class VenueCapacityConstraint(Constraint):
    """Ensures venue capacity is not exceeded."""
    
    def __init__(self, gymnases: Dict[str, Gymnase], weight: float = 500.0):
        super().__init__(weight=weight, hard=True)
        self.gymnases = gymnases
    
    def validate(self, match: Match, creneau: Creneau, solution_state: Dict) -> Tuple[bool, float]:
        key = (creneau.semaine, creneau.gymnase, creneau.horaire)
        matchs_au_creneau = solution_state.get('creneaux_usage', {}).get(key, 0)
        
        gymnase = self.gymnases.get(creneau.gymnase)
        if not gymnase:
            return False, self.weight
        
        # Utiliser la capacité disponible (qui peut être réduite par des indisponibilités partielles)
        capacite_disponible = gymnase.get_capacite_disponible(creneau.semaine, creneau.horaire)
        
        if matchs_au_creneau >= capacite_disponible:
            return False, self.weight
        
        return True, 0.0
    
    def get_name(self) -> str:
        return "VenueCapacity"


class VenueAvailabilityConstraint(Constraint):
    """Ensures venue is available at the time slot."""
    
    def __init__(self, gymnases: Dict[str, Gymnase], weight: float = 1000.0):
        super().__init__(weight=weight, hard=True)
        self.gymnases = gymnases
    
    def validate(self, match: Match, creneau: Creneau, solution_state: Dict) -> Tuple[bool, float]:
        gymnase = self.gymnases.get(creneau.gymnase)
        if not gymnase:
            return False, self.weight
        
        if not gymnase.est_disponible(creneau.semaine, creneau.horaire):
            return False, self.weight
        
        return True, 0.0
    
    def get_name(self) -> str:
        return "VenueAvailability"


class VenuePresenceObligationConstraint(Constraint):
    """Ensures venue presence obligations are respected.
    
    If a venue has a presence obligation for an institution, then at least
    one of the teams in the match must be from that institution.
    """
    
    def __init__(self, obligations: Dict[str, str], weight: float = 1000.0):
        """
        Initialize constraint.
        
        Args:
            obligations: Dict mapping venue name to required institution
            weight: Penalty weight for violations
        """
        super().__init__(weight=weight, hard=True)
        self.obligations = obligations  # {gymnase: institution_requise}
    
    def validate(self, match: Match, creneau: Creneau, solution_state: Dict) -> Tuple[bool, float]:
        # Vérifier si ce gymnase a une obligation
        institution_requise = self.obligations.get(creneau.gymnase)
        
        if not institution_requise:
            # Pas d'obligation pour ce gymnase
            return True, 0.0
        
        # Vérifier si au moins une équipe est de l'institution requise
        inst1 = match.equipe1.institution
        inst2 = match.equipe2.institution
        
        if institution_requise in [inst1, inst2]:
            return True, 0.0
        
        # Aucune équipe de l'institution requise
        return False, self.weight
    
    def get_name(self) -> str:
        return "VenuePresenceObligation"
