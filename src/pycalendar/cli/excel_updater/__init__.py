"""
Excel Configuration Updater Module.

This module provides comprehensive validation, correction, and formatting
for PyCalendar Excel configuration files.

Main components:
- validators: Column and cell validation logic
- formatters: Excel visual formatting and styling
- dropdowns: Data validation and dropdown list management
- reports: Validation reporting and display
- match_duplicates: Match duplicate detection
- core: Main actualization logic
"""

from .core import ConfigActualisateurV2, actualiser_fichier_v2
from .reports import RapportFeuille, ValidationResult, CellIssue, Severity
from .validators import ColumnValidator
from .modes import UpdateMode, UpdateOptions
from .match_duplicates import MatchDuplicateDetector, detect_match_duplicates

__all__ = [
    'ConfigActualisateurV2',
    'actualiser_fichier_v2',
    'ColumnValidator',
    'ValidationResult',
    'RapportFeuille',
    'CellIssue',
    'Severity',
    'UpdateMode',
    'UpdateOptions',
    'MatchDuplicateDetector',
    'detect_match_duplicates',
]
