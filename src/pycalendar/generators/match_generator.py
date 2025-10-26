"""Match generator using round-robin algorithm."""

from typing import List
from itertools import combinations
from pycalendar.core.models import Equipe, Match


class MatchGenerator:
    """Generates matches using round-robin algorithm."""
    
    @staticmethod
    def generer_round_robin(equipes: List[Equipe], poule: str) -> List[Match]:
        """Generate all matches for a pool using round-robin."""
        if len(equipes) < 2:
            return []
        
        matchs = []
        for equipe1, equipe2 in combinations(equipes, 2):
            match = Match(
                equipe1=equipe1,
                equipe2=equipe2,
                poule=poule
            )
            matchs.append(match)
        
        return matchs
    
    @staticmethod
    def generer_matchs_aller_retour(equipes: List[Equipe], poule: str) -> List[Match]:
        """Generate home and away matches for a pool."""
        if len(equipes) < 2:
            return []
        
        matchs = []
        for equipe1, equipe2 in combinations(equipes, 2):
            matchs.append(Match(equipe1=equipe1, equipe2=equipe2, poule=poule))
            matchs.append(Match(equipe1=equipe2, equipe2=equipe1, poule=poule))
        
        return matchs
    
    @staticmethod
    def calculer_nombre_matchs(nb_equipes: int, aller_retour: bool = False) -> int:
        """Calculate number of matches for n teams."""
        matchs_simple = nb_equipes * (nb_equipes - 1) // 2
        return matchs_simple * 2 if aller_retour else matchs_simple
