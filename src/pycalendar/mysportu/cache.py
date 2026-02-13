"""
Cache intelligent pour les données MySportU.

Stocke les réponses API en JSON avec un TTL configurable par type de ressource.
Supporte le forçage de rafraîchissement et le nettoyage automatique.
"""

from __future__ import annotations

import json
import hashlib
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import CacheConfig
from .exceptions import CacheError

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Une entrée du cache avec métadonnées."""
    data: Any
    timestamp: float          # epoch seconds
    resource_type: str        # matches, competitions, match_detail, participants
    key: str                  # identifiant unique

    @property
    def age_seconds(self) -> float:
        return time.time() - self.timestamp

    def age_display(self) -> str:
        """Affichage lisible de l'âge."""
        age = self.age_seconds
        if age < 60:
            return f"{age:.0f}s"
        if age < 3600:
            return f"{age / 60:.0f}min"
        if age < 86400:
            return f"{age / 3600:.1f}h"
        return f"{age / 86400:.1f}j"

    def is_expired(self, ttl: int) -> bool:
        return self.age_seconds > ttl


class CacheManager:
    """
    Gestionnaire de cache fichier pour les données MySportU.

    Chaque type de ressource a son propre TTL. Les données sont stockées
    en JSON dans des fichiers individuels sous le répertoire de cache.

    Structure du cache:
        .cache/mysportu/
        ├── matches_<hash>.json
        ├── competitions.json
        ├── match_detail_<id>.json
        └── participants_<id>.json
    """

    def __init__(self, config: CacheConfig):
        self.config = config
        self._ttl_map = {
            "matches": config.ttl_matches,
            "competitions": config.ttl_competitions,
            "match_detail": config.ttl_match_detail,
            "participants": config.ttl_participants,
        }

    @property
    def cache_dir(self) -> Path:
        return self.config.dir_path

    # ── Interface publique ──────────────────────────────────────────────

    def get(self, resource_type: str, key: str = "default") -> CacheEntry | None:
        """
        Récupère une entrée du cache si elle existe et n'est pas expirée.

        Args:
            resource_type: Type de ressource (matches, competitions, ...)
            key: Clé unique (ex: hash des paramètres de filtre)

        Returns:
            CacheEntry si valide, None sinon
        """
        if not self.config.enabled:
            return None

        path = self._path(resource_type, key)
        if not path.exists():
            return None

        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            entry = CacheEntry(
                data=raw["data"],
                timestamp=raw["timestamp"],
                resource_type=resource_type,
                key=key,
            )
        except (json.JSONDecodeError, KeyError, OSError) as e:
            logger.warning("Cache corrompu pour %s/%s: %s", resource_type, key, e)
            path.unlink(missing_ok=True)
            return None

        ttl = self._ttl_map.get(resource_type, 300)
        if entry.is_expired(ttl):
            logger.debug("Cache expiré pour %s/%s (âge: %s)", resource_type, key,
                         entry.age_display())
            return None

        logger.debug("Cache HIT pour %s/%s (âge: %s)", resource_type, key,
                     entry.age_display())
        return entry

    def put(self, resource_type: str, key: str, data: Any) -> CacheEntry:
        """
        Stocke des données dans le cache.

        Args:
            resource_type: Type de ressource
            key: Clé unique
            data: Données à stocker (doit être JSON-sérialisable)

        Returns:
            L'entrée de cache créée
        """
        if not self.config.enabled:
            return CacheEntry(data=data, timestamp=time.time(),
                              resource_type=resource_type, key=key)

        path = self._path(resource_type, key)
        path.parent.mkdir(parents=True, exist_ok=True)

        entry = CacheEntry(
            data=data,
            timestamp=time.time(),
            resource_type=resource_type,
            key=key,
        )

        try:
            payload = {
                "data": data,
                "timestamp": entry.timestamp,
                "resource_type": resource_type,
                "key": key,
            }
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                            encoding="utf-8")
            logger.debug("Cache WRITE pour %s/%s", resource_type, key)
        except OSError as e:
            raise CacheError(f"Impossible d'écrire le cache: {e}") from e

        return entry

    def invalidate(self, resource_type: str | None = None, key: str | None = None) -> int:
        """
        Invalide (supprime) des entrées du cache.

        Args:
            resource_type: Si fourni, ne supprime que ce type.
                           Si None, supprime tout.
            key: Si fourni, ne supprime que cette clé.

        Returns:
            Nombre d'entrées supprimées
        """
        if not self.cache_dir.exists():
            return 0

        count = 0
        if resource_type and key:
            path = self._path(resource_type, key)
            if path.exists():
                path.unlink()
                count = 1
        elif resource_type:
            for path in self.cache_dir.glob(f"{resource_type}_*.json"):
                path.unlink()
                count += 1
        else:
            for path in self.cache_dir.glob("*.json"):
                path.unlink()
                count += 1

        logger.info("Cache invalidé: %d entrée(s) supprimée(s)", count)
        return count

    def stats(self) -> dict[str, Any]:
        """Retourne des statistiques sur le cache."""
        if not self.cache_dir.exists():
            return {"total_entries": 0, "total_size_kb": 0, "by_type": {}}

        entries: dict[str, list[dict]] = {}
        total_size = 0

        for path in self.cache_dir.glob("*.json"):
            size = path.stat().st_size
            total_size += size

            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                rtype = raw.get("resource_type", "unknown")
                ts = raw.get("timestamp", 0)
                age = time.time() - ts
                ttl = self._ttl_map.get(rtype, 300)

                entries.setdefault(rtype, []).append({
                    "key": raw.get("key", ""),
                    "age_s": age,
                    "expired": age > ttl,
                    "size_kb": size / 1024,
                })
            except (json.JSONDecodeError, OSError):
                entries.setdefault("corrupt", []).append({"file": path.name})

        return {
            "total_entries": sum(len(v) for v in entries.values()),
            "total_size_kb": round(total_size / 1024, 1),
            "by_type": {
                rtype: {
                    "count": len(items),
                    "expired": sum(1 for i in items if i.get("expired")),
                    "valid": sum(1 for i in items if not i.get("expired")),
                }
                for rtype, items in entries.items()
            },
        }

    def cleanup(self) -> int:
        """Supprime les entrées expirées. Retourne le nombre supprimé."""
        if not self.cache_dir.exists():
            return 0

        count = 0
        for path in self.cache_dir.glob("*.json"):
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                rtype = raw.get("resource_type", "unknown")
                ts = raw.get("timestamp", 0)
                ttl = self._ttl_map.get(rtype, 300)
                if time.time() - ts > ttl:
                    path.unlink()
                    count += 1
            except (json.JSONDecodeError, OSError):
                path.unlink(missing_ok=True)
                count += 1

        return count

    # ── Helpers privés ──────────────────────────────────────────────────

    def _path(self, resource_type: str, key: str) -> Path:
        safe_key = hashlib.md5(key.encode()).hexdigest()[:12] if len(key) > 30 else key
        safe_key = safe_key.replace("/", "_").replace("\\", "_")
        return self.cache_dir / f"{resource_type}_{safe_key}.json"

    @staticmethod
    def make_key(**kwargs: Any) -> str:
        """Crée une clé de cache à partir de paramètres."""
        parts = sorted(f"{k}={v}" for k, v in kwargs.items() if v is not None)
        return "_".join(parts) if parts else "default"
