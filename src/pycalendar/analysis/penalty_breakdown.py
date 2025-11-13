"""
Module de calcul et décomposition des pénalités pour une solution.
Permet d'analyser en détail le score d'une solution.
"""

from typing import Dict, List, Any, Optional
from ..core.models import Solution


def calculate_penalty_breakdown(
    solution: Solution,
    config: Any,
    equipes: Optional[List] = None,
    gymnases: Optional[List] = None
) -> Dict[str, Any]:
    """
    Calcule la décomposition complète des pénalités pour l'interface web.
    
    Args:
        solution: Solution à analyser
        config: Configuration utilisée
        equipes: Liste des équipes (optionnel)
        gymnases: Liste des gymnases (optionnel)
        
    Returns:
        Dict avec la structure attendue par l'interface penalties-view.js
        
    Note:
        Pour l'instant, retourne une structure vide valide.
        L'implémentation complète nécessite d'analyser chaque match
        et de recalculer toutes les pénalités selon les règles de config.
    """
    
    return {
        "score_total": float(solution.score),
        
        "contraintes_dures": {
            "indisponibilite": {
                "violations": 0,
                "penalty": 0.0
            },
            "capacite": {
                "violations": 0,
                "penalty": 0.0
            }
        },
        
        "preferences_gymnases": {
            "matchs_en_gymnases_preferes": 0,
            "bonus_total": 0.0,
            "par_rang": {}
        },
        
        "niveau_gymnases": {
            "matchs_bien_assignes": 0,
            "matchs_mal_assignes": 0,
            "bonus_total": 0.0,
            "penalty_total": 0.0
        },
        
        "horaires_preferes": {
            "matchs_ok": 0,
            "matchs_apres": {
                "count": 0,
                "penalty": 0.0
            },
            "matchs_avant_1_equipe": {
                "count": 0,
                "penalty": 0.0
            },
            "matchs_avant_2_equipes": {
                "count": 0,
                "penalty": 0.0
            }
        },
        
        "espacement_repos": {
            "violations": 0,
            "penalty": 0.0
        },
        
        "compaction_temporelle": {
            "penalty_total": 0.0,
            "par_semaine": {}
        },
        
        "contraintes_institutionnelles": {
            "overlaps": {
                "count": 0,
                "penalty": 0.0
            },
            "ententes": {
                "planifiees": 0,
                "non_planifiees": 0,
                "penalty": 0.0
            }
        },
        
        "contraintes_temporelles": {
            "violations": 0,
            "penalty": 0.0
        },
        
        "aller_retour": {
            "meme_semaine": {
                "count": 0,
                "penalty": 0.0
            },
            "consecutives": {
                "count": 0,
                "penalty": 0.0
            }
        },
        
        "equilibrage_charge": {
            "penalty": 0.0
        }
    }
