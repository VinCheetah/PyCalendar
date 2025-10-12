"""Validation module for solution checking."""

from .solution_validator import SolutionValidator, ViolationDetail, afficher_rapport_validation

__all__ = [
    'SolutionValidator',
    'ViolationDetail',
    'afficher_rapport_validation',
]
