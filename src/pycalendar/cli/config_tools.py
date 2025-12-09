"""Compatibility shim for the historical ``config_tools`` module.

All of the real logic now lives in :mod:`pycalendar.cli.update_config_excel`. This
module only re-exports the public API so existing imports and entry points keep
working."""

from pycalendar.cli.update_config_excel import (
    ColumnValidator,
    ConfigActualisateurV2,
    RapportFeuille,
    ValidationResult,
    actualiser_fichier_v2,
    main as _update_config_main,
)

__all__ = [
    "ColumnValidator",
    "ConfigActualisateurV2",
    "RapportFeuille",
    "ValidationResult",
    "actualiser_fichier_v2",
    "main",
]


def main() -> int:
    """Entrypoint kept for backward compatibility."""
    return _update_config_main()


def run() -> int:
    """Alias matching the old public API."""
    return main()


if __name__ == "__main__":  # pragma: no cover
    import sys

    sys.exit(main())
