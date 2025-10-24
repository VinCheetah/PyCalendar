"""Data transformers and utilities."""

from typing import List, Set, Optional
from core.models import Equipe, Gymnase, Creneau
from core.calendar_manager import CalendarManager


class DataTransformer:
    """Transforms and prepares data for scheduling."""
    
    @staticmethod
    def generer_creneaux(gymnases: List[Gymnase], nb_semaines: int, calendar_manager: Optional[CalendarManager] = None) -> List[Creneau]:
        """Generate ALL possible time slots (occupied or not).
        
        Changes from previous version:
        - Generates ALL slots (gymnase × horaire × semaine)
        - Filters out vacation weeks if calendar_manager is provided
        - Doesn't filter by availability yet (done when assigning matches)
        - Each slot is unique: (semaine, horaire, gymnase)
        
        Args:
            gymnases: List of gymnasiums
            nb_semaines: Total number of weeks
            calendar_manager: Optional calendar manager to filter vacation weeks
            
        Returns:
            List of ALL possible time slots (excluding vacation weeks)
        """
        creneaux = []
        
        for semaine in range(1, nb_semaines + 1):
            # Skip vacation weeks if calendar manager is available
            if calendar_manager and calendar_manager.est_semaine_banalisee(semaine):
                continue
                
            for gymnase in gymnases:
                for horaire in gymnase.horaires_disponibles:
                    # Create slot for EVERY combination
                    # Availability check happens during match assignment
                    creneau = Creneau(
                        semaine=semaine,
                        horaire=horaire,
                        gymnase=gymnase.nom
                    )
                    creneaux.append(creneau)
        
        return creneaux
    
    @staticmethod
    def get_horaires_uniques(equipes: List[Equipe]) -> Set[str]:
        """Get all unique preferred time slots from teams."""
        horaires = set()
        for equipe in equipes:
            horaires.update(equipe.horaires_preferes)
        return horaires
    
    @staticmethod
    def get_lieux_uniques(equipes: List[Equipe]) -> Set[str]:
        """Get all unique preferred venues from teams."""
        lieux = set()
        for equipe in equipes:
            lieux.update(equipe.lieux_preferes)
        return lieux
