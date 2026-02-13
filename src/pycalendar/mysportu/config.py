"""
Configuration du module MySportU.

Centralise les paramètres de connexion, cache et comportement.
Les valeurs peuvent être surchargées via un fichier YAML ou des variables d'environnement.

Chaîne de priorité (du plus faible au plus fort):
    1. Valeurs par défaut
    2. configs/default.yaml (auto-découvert depuis la racine projet)
    3. Fichier YAML passé en paramètre (section ``mysportu:``)
    4. Variables d'environnement (MYSPORTU_USERNAME, MYSPORTU_PASSWORD, …)
    5. Overrides passés en argument (username=, password=, …)
"""

from __future__ import annotations

import os
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Utilitaires
# ─────────────────────────────────────────────────────────────────────────────

def _find_project_root(start: Path | None = None) -> Path | None:
    """Remonte l'arborescence pour trouver la racine du projet."""
    current = start or Path.cwd()
    for parent in [current] + list(current.parents):
        if (parent / "pyproject.toml").exists() or (parent / ".git").exists():
            return parent
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Dataclasses de configuration
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class AuthConfig:
    """Paramètres d'authentification MySportU."""
    username: str = ""
    password: str = ""
    base_url: str = "https://gestion.mysportu.com"
    login_path: str = "/auth/login"

    @property
    def login_url(self) -> str:
        return f"{self.base_url}{self.login_path}"

    @property
    def has_credentials(self) -> bool:
        """Vérifie que les identifiants sont renseignés."""
        return bool(self.username and self.password)


@dataclass
class CacheConfig:
    """Paramètres du cache."""
    enabled: bool = True
    directory: str = ".cache/mysportu"
    # TTL par type de ressource (en secondes)
    ttl_matches: int = 300          # 5 minutes
    ttl_competitions: int = 3600    # 1 heure
    ttl_match_detail: int = 120     # 2 minutes
    ttl_participants: int = 120     # 2 minutes

    @property
    def dir_path(self) -> Path:
        return Path(self.directory)


@dataclass
class RequestConfig:
    """Paramètres des requêtes HTTP."""
    delay_between_requests: float = 0.05   # secondes
    timeout: int = 30                       # secondes
    max_retries: int = 3
    retry_delay: float = 1.0               # secondes entre retries


@dataclass
class MySportUConfig:
    """Configuration complète du module MySportU."""
    auth: AuthConfig = field(default_factory=AuthConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    requests: RequestConfig = field(default_factory=RequestConfig)
    verbose: bool = False

    @property
    def has_credentials(self) -> bool:
        """Vérifie que les identifiants sont renseignés."""
        return self.auth.has_credentials

    @classmethod
    def load(cls, path: str | Path | None = None, **overrides: Any) -> "MySportUConfig":
        """
        Charge la configuration en suivant la chaîne de priorité.

        1. Valeurs par défaut
        2. ``configs/default.yaml`` (auto-découvert)
        3. Fichier YAML passé en *path* (section ``mysportu:``)
        4. Variables d'environnement
        5. *overrides* en argument
        """
        config = cls()

        # ── 1. Auto-découverte de configs/default.yaml ──
        project_root = _find_project_root(Path(path).parent if path else None)
        if project_root:
            default_yaml = project_root / "configs" / "default.yaml"
            if default_yaml.exists():
                _load_yaml_into(config, default_yaml)

        # ── 2. Fichier YAML passé en paramètre ──
        if path:
            yaml_path = Path(path)
            if yaml_path.exists():
                _load_yaml_into(config, yaml_path)

        # ── 3. Variables d'environnement ──
        env_username = os.environ.get("MYSPORTU_USERNAME")
        env_password = os.environ.get("MYSPORTU_PASSWORD")
        env_base_url = os.environ.get("MYSPORTU_BASE_URL")
        if env_username:
            config.auth.username = env_username
        if env_password:
            config.auth.password = env_password
        if env_base_url:
            config.auth.base_url = env_base_url

        # ── 4. Overrides ──
        for key, value in overrides.items():
            if value is None:
                continue
            if key == "username":
                config.auth.username = value
            elif key == "password":
                config.auth.password = value
            elif key == "base_url":
                config.auth.base_url = value
            elif key == "cache_dir":
                config.cache.directory = value
            elif key == "cache_enabled":
                config.cache.enabled = value
            elif key == "verbose":
                config.verbose = value

        # ── Diagnostic ──
        if config.verbose:
            logger.debug(
                "Config MySportU: user=%s, base_url=%s, cache=%s",
                config.auth.username or "(vide)",
                config.auth.base_url,
                "on" if config.cache.enabled else "off",
            )

        return config


# ─────────────────────────────────────────────────────────────────────────────
# Chargement YAML
# ─────────────────────────────────────────────────────────────────────────────

def _load_yaml_into(config: MySportUConfig, yaml_path: Path) -> None:
    """Charge la section ``mysportu:`` d'un YAML dans *config* (in-place)."""
    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except (yaml.YAMLError, OSError) as e:
        logger.warning("Impossible de lire %s: %s", yaml_path, e)
        return

    msu_data = data.get("mysportu", {})
    if not msu_data:
        return

    _apply_yaml(config, msu_data)
    logger.debug("Config chargée depuis %s", yaml_path)


def _apply_yaml(config: MySportUConfig, data: dict) -> MySportUConfig:
    """Applique les valeurs d'un dict YAML à la config."""
    auth = data.get("auth", {})
    if auth:
        for k in ("username", "password", "base_url", "login_path"):
            v = auth.get(k)
            # Ne jamais écraser avec une chaîne vide
            if v:
                setattr(config.auth, k, v)

    cache = data.get("cache", {})
    if cache:
        for k in ("enabled", "directory", "ttl_matches", "ttl_competitions",
                   "ttl_match_detail", "ttl_participants"):
            if k in cache:
                setattr(config.cache, k, cache[k])

    req = data.get("requests", {})
    if req:
        for k in ("delay_between_requests", "timeout", "max_retries",
                   "retry_delay"):
            if k in req:
                setattr(config.requests, k, req[k])

    if "verbose" in data:
        config.verbose = data["verbose"]

    return config
