"""
PyCalendar - Système de planification sportive automatique.

Package principal pour la génération de calendriers de compétitions sportives
avec contraintes multiples et algorithmes d'optimisation.
"""

__version__ = "2.0.0"
__author__ = "VinCheetah"

# Imports publics principaux
from .core.models import Equipe, Gymnase, Match, Solution, Creneau
from .core.config import Config
from .orchestrator.pipeline import SchedulingPipeline

__all__ = [
    "Equipe",
    "Gymnase", 
    "Match",
    "Solution",
    "Creneau",
    "Config",
    "SchedulingPipeline",
]
