"""Statistics display for scheduling solutions."""

from typing import List
from pycalendar.core.models import Solution, Creneau
from pycalendar.core.console import (
    print_section, print_success, print_warning, print_error,
    print_key_value, print_blank, format_solution_summary
)


class Statistics:
    """Utility class for displaying solution statistics."""
    
    @staticmethod
    def afficher_stats(solution: Solution, creneaux_restants: List[Creneau]) -> None:
        """
        Display statistics about the scheduling solution.
        
        Args:
            solution: The scheduling solution
            creneaux_restants: List of remaining unused slots
        """
        # Basic stats
        total_matchs = len(solution.matchs_planifies) + len(solution.matchs_non_planifies)
        scheduled = len(solution.matchs_planifies)
        unscheduled = len(solution.matchs_non_planifies)
        score = getattr(solution, 'score', None)
        
        # Calculate slots
        slots_used = scheduled  # Approximation
        slots_available = slots_used + len(creneaux_restants)
        
        format_solution_summary(
            scheduled=scheduled,
            unscheduled=unscheduled,
            score=score,
            slots_used=slots_used,
            slots_available=slots_available
        )
