"""Multi-pool match generation."""

from typing import List, Dict, Union
from pycalendar.core.models import Equipe, Match
from .match_generator import MatchGenerator


class MultiPoolGenerator:
    """Generates matches for multiple pools simultaneously."""
    
    def __init__(self, types_poules: Union[bool, Dict[str, str]] = False):
        """
        Initialize generator with pool types.
        
        Args:
            types_poules: Either:
                - bool: False (all Classique) or True (all Aller-Retour) - legacy mode
                - Dict[str, str]: {poule_name: type} where type is 'Classique' or 'Aller-Retour'
        """
        if isinstance(types_poules, bool):
            # Legacy mode: all pools same type
            self.types_poules = None
            self.aller_retour_global = types_poules
        else:
            # New mode: per-pool types
            self.types_poules = types_poules
            self.aller_retour_global = None
        
        self.generator = MatchGenerator()
    
    def generer_tous_matchs(self, poules: Dict[str, List[Equipe]]) -> List[Match]:
        """Generate matches for all pools according to their types."""
        tous_matchs = []
        stats = {}
        
        for nom_poule, equipes in poules.items():
            # Determine if this pool is aller-retour
            if self.types_poules is not None:
                # Per-pool type mode
                type_poule = self.types_poules.get(nom_poule, 'Classique')
                est_aller_retour = (type_poule == 'Aller-Retour')
            else:
                # Legacy global mode
                est_aller_retour = self.aller_retour_global
            
            # Generate matches
            if est_aller_retour:
                matchs = self.generator.generer_matchs_aller_retour(equipes, nom_poule)
            else:
                matchs = self.generator.generer_round_robin(equipes, nom_poule)
            
            tous_matchs.extend(matchs)
            stats[nom_poule] = {
                'nb_equipes': len(equipes),
                'nb_matchs': len(matchs),
                'type': 'Aller-Retour' if est_aller_retour else 'Classique'
            }
        
        return tous_matchs
    
    def get_stats(self, poules: Dict[str, List[Equipe]]) -> Dict:
        """Get generation statistics."""
        total_equipes = sum(len(equipes) for equipes in poules.values())
        
        # Calculate total matches considering per-pool types
        total_matchs = 0
        for nom_poule, equipes in poules.items():
            if self.types_poules is not None:
                type_poule = self.types_poules.get(nom_poule, 'Classique')
                est_aller_retour = (type_poule == 'Aller-Retour')
            else:
                est_aller_retour = bool(self.aller_retour_global)  # Convert None to False
            
            total_matchs += self.generator.calculer_nombre_matchs(len(equipes), est_aller_retour)
        
        return {
            'nb_poules': len(poules),
            'nb_equipes_total': total_equipes,
            'nb_matchs_total': total_matchs,
            'tailles_poules': {nom: len(equipes) for nom, equipes in poules.items()}
        }
