"""Statistics display for scheduling solutions."""

from typing import List
from pycalendar.core.models import Solution, Creneau


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
        print("\n" + "="*60)
        print("📊 STATISTIQUES DE LA SOLUTION")
        print("="*60)
        
        # Basic stats
        total_matchs = len(solution.matchs_planifies) + len(solution.matchs_non_planifies)
        taux = solution.taux_planification()
        
        print(f"\n✅ Matchs planifiés: {len(solution.matchs_planifies)}/{total_matchs} ({taux:.1f}%)")
        
        if solution.matchs_non_planifies:
            print(f"❌ Matchs non planifiés: {len(solution.matchs_non_planifies)}")
        
        # Slot usage
        print(f"\n🏟️  Créneaux restants disponibles: {len(creneaux_restants)}")
        
        # Score if available
        if hasattr(solution, 'score') and solution.score is not None:
            print(f"\n🎯 Score de la solution: {solution.score}")
        
        print("="*60 + "\n")
