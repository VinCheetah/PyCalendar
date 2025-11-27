"""Solvers for sports scheduling."""

from .base_solver import BaseSolver

try:
    from .cpsat_solver import CPSATSolver
    __all__ = ['BaseSolver', 'CPSATSolver']
except ImportError:
    __all__ = ['BaseSolver']
