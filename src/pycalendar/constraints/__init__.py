"""
Constraint system for sports scheduling.

NOTE: Ce module définit une architecture de contraintes orientée objet
mais n'est PAS actuellement utilisé par le solver CP-SAT (cpsat_solver.py).
Les contraintes sont implémentées directement dans le solver.

Ce module est conservé pour une future refactorisation vers une architecture
plus modulaire et testable.
"""

from .base import Constraint, ConstraintValidator
from .venue_constraints import VenueCapacityConstraint, VenueAvailabilityConstraint
from .team_constraints import TeamAvailabilityConstraint, MaxMatchesPerWeekConstraint
from .schedule_constraints import MinSpacingConstraint, LoadBalancingConstraint

__all__ = [
    'Constraint', 'ConstraintValidator',
    'VenueCapacityConstraint', 'VenueAvailabilityConstraint',
    'TeamAvailabilityConstraint', 'MaxMatchesPerWeekConstraint',
    'MinSpacingConstraint', 'LoadBalancingConstraint'
]
