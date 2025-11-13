"""Base solver interface."""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from pycalendar.core.models import Match, Creneau, Gymnase, Solution
from pycalendar.core.config import Config


class BaseSolver(ABC):
    """Abstract base class for all scheduling solvers."""
    
    def __init__(self, config: Config):
        self.config = config
    
    @abstractmethod
    def solve(self, matchs: List[Match], creneaux: List[Creneau], 
             gymnases: Dict[str, Gymnase]) -> Solution:
        """
        Solve the scheduling problem.
        Returns a Solution object.
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get solver name."""
        pass
    
    def _create_solution_state(self, matchs_fixes: Optional[List[Match]] = None) -> Dict:
        """Create initial solution state for constraint validation.
        
        Args:
            matchs_fixes: Liste optionnelle des matchs déjà fixés/planifiés.
                         Ces matchs seront intégrés dans le state initial pour que
                         les contraintes (espacement, max par semaine, etc.) en tiennent compte.
        
        Returns:
            Dictionnaire représentant l'état de la solution
        """
        state = {
            'creneaux_usage': {},
            'equipes_semaines': {},
            'equipes_creneaux': {},
            'derniers_matchs': {},
            'matchs_par_semaine': {},
            'matchs_par_gymnase': {},
            'avg_matchs_semaine': 0,
            'avg_matchs_gymnase': 0,
        }
        
        # Intégrer les matchs fixes dans l'état initial
        if matchs_fixes:
            for match in matchs_fixes:
                # Les matchs fixes doivent avoir leurs métadonnées avec semaine/horaire/gymnase
                if match.metadata and 'semaine' in match.metadata:
                    from pycalendar.core.models import Creneau
                    creneau = Creneau(
                        semaine=match.metadata['semaine'],
                        horaire=match.metadata['horaire'],
                        gymnase=match.metadata['gymnase']
                    )
                    self._update_solution_state(state, match, creneau)
        
        return state
    
    def _update_solution_state(self, state: Dict, match: Match, creneau: Creneau):
        """Update solution state after assigning a match.
        
        IMPORTANT: Utilise id_unique pour distinguer équipes de même nom mais genre différent.
        """
        key_creneau = (creneau.semaine, creneau.gymnase, creneau.horaire)
        state['creneaux_usage'][key_creneau] = state['creneaux_usage'].get(key_creneau, 0) + 1
        
        # Utiliser id_unique au lieu de nom
        key_equipe1 = (match.equipe1.id_unique, creneau.semaine)
        key_equipe2 = (match.equipe2.id_unique, creneau.semaine)
        state['equipes_semaines'][key_equipe1] = state['equipes_semaines'].get(key_equipe1, 0) + 1
        state['equipes_semaines'][key_equipe2] = state['equipes_semaines'].get(key_equipe2, 0) + 1
        
        key_horaire = (creneau.semaine, creneau.horaire)
        if key_horaire not in state['equipes_creneaux']:
            state['equipes_creneaux'][key_horaire] = set()
        state['equipes_creneaux'][key_horaire].add(match.equipe1.id_unique)
        state['equipes_creneaux'][key_horaire].add(match.equipe2.id_unique)
        
        if match.equipe1.id_unique not in state['derniers_matchs']:
            state['derniers_matchs'][match.equipe1.id_unique] = []
        state['derniers_matchs'][match.equipe1.id_unique].append(creneau.semaine)
        
        if match.equipe2.id_unique not in state['derniers_matchs']:
            state['derniers_matchs'][match.equipe2.id_unique] = []
        state['derniers_matchs'][match.equipe2.id_unique].append(creneau.semaine)
        
        state['matchs_par_semaine'][creneau.semaine] = state['matchs_par_semaine'].get(creneau.semaine, 0) + 1
        state['matchs_par_gymnase'][creneau.gymnase] = state['matchs_par_gymnase'].get(creneau.gymnase, 0) + 1
