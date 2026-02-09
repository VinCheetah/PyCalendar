"""
Programme d'actualisation et validation automatique du fichier de configuration V2.

Version améliorée avec :
- Validation complète de la structure des colonnes
- Détection et correction automatique des colonnes mal nommées
- Gestion intelligente des colonnes en trop (préfixe EXTRA_)
- Validation du contenu de chaque cellule
- Rapport détaillé et structuré
- Mode auto-correction et mode interactif
- Listes déroulantes avec dates de semaines
- Formatage visuel amélioré

Ce module est un wrapper pour la nouvelle structure modulaire dans excel_updater/
"""

# Re-export everything from the new modular structure
from pycalendar.cli.excel_updater.core import (
    ConfigActualisateurV2,
    actualiser_fichier_v2,
    main,
)
from pycalendar.cli.excel_updater.modes import (
    UpdateMode,
    UpdateOptions,
    prompt_user_correction,
)
from pycalendar.cli.excel_updater.reports import (
    ValidationResult,
    RapportFeuille,
    RapportGlobal,
    Severity,
    CellIssue,
)
from pycalendar.cli.excel_updater.validators import ColumnValidator
from pycalendar.cli.excel_updater.formatters import ExcelFormatter, format_workbook
from pycalendar.cli.excel_updater.dropdowns import DropdownManager, setup_all_dropdowns
from pycalendar.cli.excel_updater.display import (
    print_header,
    print_section,
    print_success,
    print_error,
    print_warning,
    print_info,
    print_global_report,
)

__all__ = [
    # Core
    'ConfigActualisateurV2',
    'actualiser_fichier_v2',
    'main',
    # Modes
    'UpdateMode',
    'UpdateOptions',
    'prompt_user_correction',
    # Reports
    'ValidationResult',
    'RapportFeuille',
    'RapportGlobal',
    'Severity',
    'CellIssue',
    # Validators
    'ColumnValidator',
    # Formatters
    'ExcelFormatter',
    'format_workbook',
    # Dropdowns
    'DropdownManager',
    'setup_all_dropdowns',
    # Display
    'print_header',
    'print_section',
    'print_success',
    'print_error',
    'print_warning',
    'print_info',
    'print_global_report',
]


if __name__ == "__main__":
    import sys
    sys.exit(main())
