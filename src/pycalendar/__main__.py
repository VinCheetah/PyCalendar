"""
PyCalendar - Main entry point when running as module.

Usage:
    python -m pycalendar [config.yaml]
    python -m pycalendar configs/config_volley.yaml

This module delegates to the main entry point to avoid code duplication.
For direct execution, use: python main.py [config.yaml]
"""

import sys
from pathlib import Path

# Add project root to path for imports when running as module
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def main():
    """Point d'entrée principal (délégué à main.py)."""
    import importlib.util
    
    main_path = project_root / "main.py"
    if main_path.exists():
        spec = importlib.util.spec_from_file_location("main_module", main_path)
        main_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(main_module)
        return main_module.main()
    else:
        print("❌ Fichier main.py introuvable")
        return 1


if __name__ == "__main__":
    sys.exit(main())

