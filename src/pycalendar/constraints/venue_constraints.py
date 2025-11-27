"""Venue-related constraints."""

from typing import Dict, Tuple
from pycalendar.core.models import Match, Creneau, Gymnase
from pycalendar.core.config import Config
from .base import Constraint


class VenueCapacityConstraint(Constraint):
    """Ensures venue capacity is not exceeded.
    
    IMPORTANT: Cette contrainte prend en compte la durée réelle des matchs (configurable).
    Un match à 15h occupe un terrain de 15h à 16h30 (handball) ou 17h (volley), donc il 
    réduit la capacité disponible des créneaux adjacents.
    """
    
    def __init__(self, gymnases: Dict[str, Gymnase], config: Config, weight: float = 500.0):
        super().__init__(weight=weight, hard=True)
        self.gymnases = gymnases
        self.match_duration_minutes = config.duree_match_minutes
    
    @staticmethod
    def _horaire_to_minutes(horaire: str) -> int:
        """Convertit '14h00' en 840 (14*60)"""
        if not horaire or 'h' not in horaire:
            return 0
        parts = horaire.lower().split('h')
        heures = int(parts[0])
        minutes = int(parts[1]) if len(parts) > 1 and parts[1] else 0
        return heures * 60 + minutes
    
    def _creneaux_se_chevauchent(self, horaire1: str, horaire2: str) -> bool:
        """
        Vérifie si deux créneaux se chevauchent.
        Un match à horaire1 (durée configurable) chevauche le créneau horaire2 (durée 2h).
        """
        match_start = self._horaire_to_minutes(horaire1)
        match_end = match_start + self.match_duration_minutes
        
        creneau_start = self._horaire_to_minutes(horaire2)
        creneau_end = creneau_start + 120  # Créneaux de 2h (120 minutes)
        
        # Chevauchement si: début_match < fin_créneau ET fin_match > début_créneau
        return match_start < creneau_end and match_end > creneau_start
    
    def validate(self, match: Match, creneau: Creneau, solution_state: Dict) -> Tuple[bool, float]:
        gymnase = self.gymnases.get(creneau.gymnase)
        if not gymnase:
            return False, self.weight
        
        # Utiliser la capacité disponible (qui peut être réduite par des indisponibilités partielles)
        capacite_disponible = gymnase.get_capacite_disponible(creneau.semaine, creneau.horaire)
        
        # Compter le nombre de matchs qui chevauchent ce créneau
        # On doit parcourir tous les créneaux pour vérifier les chevauchements
        nb_matchs_chevauchants = 0
        creneaux_usage = solution_state.get('creneaux_usage', {})
        
        for (semaine, gymnase_nom, horaire), count in creneaux_usage.items():
            # Vérifier si c'est le même gymnase et la même semaine
            if gymnase_nom == creneau.gymnase and semaine == creneau.semaine:
                # Vérifier si les horaires se chevauchent
                if self._creneaux_se_chevauchent(horaire, creneau.horaire):
                    nb_matchs_chevauchants += count
        
        # Vérifier s'il reste de la place pour le nouveau match
        # nb_matchs_chevauchants inclut déjà les matchs fixés et planifiés
        # On veut ajouter 1 match, donc: nb_matchs_chevauchants + 1 <= capacite_disponible
        if nb_matchs_chevauchants + 1 > capacite_disponible:
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
