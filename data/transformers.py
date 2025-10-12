"""Data transformers and utilities."""

from typing import List, Set
from core.models import Equipe, Gymnase, Creneau


class DataTransformer:
    """Transforms and prepares data for scheduling."""
    
    @staticmethod
    def generer_creneaux(gymnases: List[Gymnase], nb_semaines: int) -> List[Creneau]:
        """Generate all available time slots.
        
        Note: Each time slot is created once. The capacity constraint is handled
        by the solvers, not by duplicating time slots.
        """
        creneaux = []
        
        for semaine in range(1, nb_semaines + 1):
            for gymnase in gymnases:
                for horaire in gymnase.horaires_disponibles:
                    if gymnase.est_disponible(semaine, horaire):
                        # Create only ONE slot per (week, time, venue)
                        # Capacity is enforced by the solver
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
