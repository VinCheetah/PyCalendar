"""Statistics and metrics for scheduling solutions."""

from typing import Dict, List, Optional
from collections import defaultdict
from core.models import Solution, Match, Creneau


class Statistics:
    """Calculate and display statistics for scheduling solutions."""
    
    @staticmethod
    def afficher_stats(solution: Solution, creneaux_disponibles: Optional[List[Creneau]] = None):
        """Display solution statistics."""
        print("\n" + "="*60)
        print("STATISTIQUES DE LA SOLUTION")
        print("="*60)
        
        total = len(solution.matchs_planifies) + len(solution.matchs_non_planifies)
        print(f"Matchs planifiés:      {len(solution.matchs_planifies)}/{total} ({solution.taux_planification():.1f}%)")
        print(f"Matchs non planifiés:  {len(solution.matchs_non_planifies)}")
        print(f"Score de la solution:  {solution.score:.2f}")
        
        if solution.matchs_planifies:
            Statistics._afficher_stats_detaillees(solution)
        
        # Afficher les matchs non planifiés
        if solution.matchs_non_planifies:
            Statistics._afficher_matchs_non_planifies(solution.matchs_non_planifies)
        
        # Afficher les créneaux disponibles restants
        if creneaux_disponibles:
            Statistics._afficher_creneaux_disponibles(creneaux_disponibles)
        
        print("="*60 + "\n")
    
    @staticmethod
    def _afficher_stats_detaillees(solution: Solution):
        """Display detailed statistics."""
        matchs_par_semaine = solution.get_matchs_par_semaine()
        
        if matchs_par_semaine:
            print(f"\nRépartition par semaine:")
            for semaine in sorted(matchs_par_semaine.keys()):
                nb_matchs = len(matchs_par_semaine[semaine])
                print(f"  Semaine {semaine:2d}: {nb_matchs:3d} matchs")
        
        poules_stats = Statistics._calculer_stats_poules(solution.matchs_planifies)
        if poules_stats:
            print(f"\nRépartition par poule:")
            for poule, nb_matchs in sorted(poules_stats.items()):
                print(f"  Poule {poule}: {nb_matchs} matchs")
        
        gymnases_stats = Statistics._calculer_stats_gymnases(solution.matchs_planifies)
        if gymnases_stats:
            print(f"\nUtilisation des gymnases:")
            for gymnase, nb_matchs in sorted(gymnases_stats.items(), key=lambda x: x[1], reverse=True):
                print(f"  {gymnase}: {nb_matchs} matchs")
    
    @staticmethod
    def _calculer_stats_poules(matchs: List[Match]) -> Dict[str, int]:
        """Calculate statistics per pool."""
        stats = defaultdict(int)
        for match in matchs:
            stats[match.poule] += 1
        return dict(stats)
    
    @staticmethod
    def _calculer_stats_gymnases(matchs: List[Match]) -> Dict[str, int]:
        """Calculate statistics per venue."""
        stats = defaultdict(int)
        for match in matchs:
            if match.creneau:
                stats[match.creneau.gymnase] += 1
        return dict(stats)
    
    @staticmethod
    def _afficher_matchs_non_planifies(matchs: List[Match]):
        """Display unscheduled matches."""
        print(f"\n⚠️  MATCHS NON PLANIFIÉS ({len(matchs)}):")
        print("-" * 60)
        
        # Grouper par poule
        par_poule = defaultdict(list)
        for match in matchs:
            par_poule[match.poule].append(match)
        
        for poule in sorted(par_poule.keys()):
            matchs_poule = par_poule[poule]
            print(f"\n  Poule {poule} ({len(matchs_poule)} matchs):")
            for match in matchs_poule:
                print(f"    • {match.equipe1.nom_complet} vs {match.equipe2.nom_complet}")
    
    @staticmethod
    def _afficher_creneaux_disponibles(creneaux: List[Creneau]):
        """Display available time slots."""
        print(f"\n📅 CRÉNEAUX DISPONIBLES RESTANTS ({len(creneaux)}):")
        print("-" * 60)
        
        # Grouper par gymnase
        par_gymnase = defaultdict(list)
        for creneau in creneaux:
            par_gymnase[creneau.gymnase].append(creneau)
        
        for gymnase in sorted(par_gymnase.keys()):
            creneaux_gym = par_gymnase[gymnase]
            print(f"\n  {gymnase} ({len(creneaux_gym)} créneaux):")
            
            # Grouper par semaine
            par_semaine = defaultdict(list)
            for c in creneaux_gym:
                par_semaine[c.semaine].append(c.horaire)
            
            for semaine in sorted(par_semaine.keys())[:5]:  # Afficher max 5 semaines
                horaires = sorted(set(par_semaine[semaine]))
                print(f"    Semaine {semaine:2d}: {', '.join(horaires)}")
            
            if len(par_semaine) > 5:
                print(f"    ... et {len(par_semaine) - 5} autres semaines")
    
    @staticmethod
    def generer_rapport(solution: Solution) -> Dict:
        """Generate comprehensive report."""
        matchs_par_semaine = solution.get_matchs_par_semaine()
        
        return {
            'total_matchs': len(solution.matchs_planifies) + len(solution.matchs_non_planifies),
            'matchs_planifies': len(solution.matchs_planifies),
            'matchs_non_planifies': len(solution.matchs_non_planifies),
            'taux_planification': solution.taux_planification(),
            'score': solution.score,
            'nb_semaines_utilisees': len(matchs_par_semaine),
            'stats_poules': Statistics._calculer_stats_poules(solution.matchs_planifies),
            'stats_gymnases': Statistics._calculer_stats_gymnases(solution.matchs_planifies),
            'matchs_par_semaine': {k: len(v) for k, v in matchs_par_semaine.items()},
        }
