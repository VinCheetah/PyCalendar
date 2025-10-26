"""Solvers for sports scheduling."""

from .base_solver import BaseSolver
from .greedy_solver import GreedySolver

try:
    from .cpsat_solver import CPSATSolver
    __all__ = ['BaseSolver', 'GreedySolver', 'CPSATSolver']
except ImportError:
    __all__ = ['BaseSolver', 'GreedySolver']
