"""Exceptions spécifiques au module MySportU."""

from __future__ import annotations


class MySportUError(Exception):
    """Erreur de base pour le module MySportU."""


class AuthenticationError(MySportUError):
    """Erreur d'authentification (login échoué, session expirée)."""


class APIError(MySportUError):
    """Erreur lors d'un appel à l'API MySportU."""

    def __init__(self, message: str, status_code: int | None = None, url: str | None = None):
        self.status_code = status_code
        self.url = url
        detail = f" [HTTP {status_code}]" if status_code else ""
        detail += f" ({url})" if url else ""
        super().__init__(f"{message}{detail}")


class CacheError(MySportUError):
    """Erreur liée au cache (lecture/écriture/corruption)."""


class RateLimitError(APIError):
    """Trop de requêtes envoyées à l'API."""
