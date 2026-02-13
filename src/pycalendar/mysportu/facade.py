"""
Facade MySportU — Point d'entrée unique pour les scripts.

Combine client, cache, API et display dans une interface simple et cohérente.

Usage:
    >>> from pycalendar.mysportu import MySportU
    >>>
    >>> # Création simple (identifiants par défaut ou env vars)
    >>> msu = MySportU(username="...", password="...")
    >>>
    >>> # Récupérer les matchs de volley PH2
    >>> matches = msu.get_matches(sport="VB", championship="PH2")
    >>>
    >>> # Afficher les matchs
    >>> msu.display_matches(matches)
    >>>
    >>> # Récupérer les détails d'un match
    >>> detail = msu.get_match_detail(12345)
    >>> msu.display_match_detail(detail)
    >>>
    >>> # Forcer le rafraîchissement du cache
    >>> matches = msu.get_matches(sport="VB", force_refresh=True)
    >>>
    >>> # Gérer le cache
    >>> msu.show_cache_stats()
    >>> msu.clear_cache()
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from rich.console import Console

from .api import MySportUAPI
from .cache import CacheManager
from .client import MySportUClient
from .config import MySportUConfig
from .display import Display
from .models import (
    Competition,
    MatchDetail,
    MatchInfo,
    MatchState,
)

logger = logging.getLogger(__name__)


class MySportU:
    """
    Interface principale pour l'intégration MySportU.

    Combine authentification, appels API, cache intelligent et affichage Rich
    dans une interface simple pour les scripts du projet.
    """

    def __init__(
        self,
        *,
        username: str | None = None,
        password: str | None = None,
        config_path: str | Path | None = None,
        cache_dir: str | None = None,
        cache_enabled: bool = True,
        verbose: bool = False,
        console: Console | None = None,
    ):
        """
        Initialise la facade MySportU.

        Args:
            username: Identifiant MySportU (sinon: env MYSPORTU_USERNAME ou config YAML)
            password: Mot de passe MySportU (sinon: env MYSPORTU_PASSWORD ou config YAML)
            config_path: Chemin vers un fichier de config YAML
            cache_dir: Répertoire de cache (.cache/mysportu par défaut)
            cache_enabled: Activer/désactiver le cache
            verbose: Mode verbeux
            console: Console Rich (créée automatiquement sinon)
        """
        # Configuration
        overrides: dict[str, Any] = {"verbose": verbose, "cache_enabled": cache_enabled}
        if username:
            overrides["username"] = username
        if password:
            overrides["password"] = password
        if cache_dir:
            overrides["cache_dir"] = cache_dir

        self._config = MySportUConfig.load(config_path, **overrides)

        # Composants
        self._client = MySportUClient(self._config)
        self._cache = CacheManager(self._config.cache)
        self._api = MySportUAPI(self._client, self._cache, self._config)
        self._display = Display(console)
        self._connected = False

    # ── Propriétés ──────────────────────────────────────────────────────

    @property
    def config(self) -> MySportUConfig:
        """Accès à la configuration (utile pour les scripts)."""
        return self._config

    @property
    def base_url(self) -> str:
        return self._config.auth.base_url

    # ── Connexion ───────────────────────────────────────────────────────

    def connect(self) -> "MySportU":
        """Établit la connexion à MySportU."""
        if self._connected:
            return self

        with self._display.progress() as progress:
            task = progress.add_task("Connexion à MySportU...", total=1)
            self._client.login()
            progress.advance(task)

        self._display.success("Connecté à MySportU")
        self._connected = True
        return self

    def disconnect(self) -> None:
        """Ferme la session."""
        self._client.logout()
        self._connected = False

    def _ensure_connected(self) -> None:
        if not self._connected:
            self.connect()

    @property
    def is_connected(self) -> bool:
        return self._connected

    # ── Matchs ──────────────────────────────────────────────────────────

    def get_all_matches(self, *, force_refresh: bool = False) -> list[MatchInfo]:
        """
        Récupère tous les matchs (toutes compétitions).

        Args:
            force_refresh: Ignorer le cache et re-télécharger

        Returns:
            Liste complète des MatchInfo
        """
        self._ensure_connected()

        with self._display.progress() as progress:
            task = progress.add_task("Récupération des matchs...", total=100)

            def on_progress(page: int, total: int, count: int) -> None:
                progress.update(task, completed=int(page / max(total, 1) * 100),
                                total=100,
                                description=f"Matchs: {count} (page {page}/{total})")

            matches = self._api.get_all_matches(
                force_refresh=force_refresh,
                on_progress=on_progress,
            )
            progress.update(task, completed=100)

        self._display.success(f"{len(matches)} matchs récupérés")
        return matches

    def get_matches(
        self,
        *,
        sport: str | None = None,
        championship: str | None = None,
        genre: str | None = None,
        date: str | None = None,
        state: str | None = None,
        force_refresh: bool = False,
    ) -> list[MatchInfo]:
        """
        Récupère les matchs avec filtres.

        Args:
            sport: Code sport (VB, HB, BB, ...)
            championship: Code championnat (PH1, PH2, CFU, ...)
            genre: Genre (M, F)
            date: Date (dd/mm/yyyy)
            state: État (non_joue, termine, reporte, annule, forfait)
            force_refresh: Ignorer le cache

        Returns:
            Liste de MatchInfo filtrés
        """
        self._ensure_connected()

        with self._display.progress() as progress:
            task = progress.add_task("Récupération des matchs...", total=100)

            def on_progress(page: int, total: int, count: int) -> None:
                progress.update(task, completed=int(page / max(total, 1) * 100),
                                description=f"Matchs: {count} (page {page}/{total})")

            matches = self._api.get_matches(
                sport=sport, championship=championship, genre=genre,
                date=date, state=state, force_refresh=force_refresh,
                on_progress=on_progress,
            )
            progress.update(task, completed=100)

        # Résumé des filtres
        filters = []
        if sport:
            filters.append(f"sport={sport}")
        if championship:
            filters.append(f"champ={championship}")
        if genre:
            filters.append(f"genre={genre}")
        if date:
            filters.append(f"date={date}")
        if state:
            filters.append(f"état={state}")

        filter_str = f" ({', '.join(filters)})" if filters else ""
        self._display.success(f"{len(matches)} matchs{filter_str}")

        return matches

    def get_match_detail(self, match_id: int, *,
                          force_refresh: bool = False) -> MatchDetail:
        """
        Récupère les détails d'un match (joueurs, staff, arbitres).

        Args:
            match_id: ID du match
            force_refresh: Ignorer le cache

        Returns:
            MatchDetail complet
        """
        self._ensure_connected()
        self._display.status(f"Chargement du match #{match_id}...")
        return self._api.get_match_detail(match_id, force_refresh=force_refresh)

    def get_matches_details(
        self,
        match_ids: list[int],
        *,
        force_refresh: bool = False,
    ) -> list[MatchDetail]:
        """
        Récupère les détails de plusieurs matchs avec barre de progression.

        Args:
            match_ids: Liste d'IDs de matchs
            force_refresh: Ignorer le cache

        Returns:
            Liste de MatchDetail
        """
        self._ensure_connected()
        details = []

        with self._display.progress() as progress:
            task = progress.add_task("Chargement des détails...", total=len(match_ids))
            for mid in match_ids:
                try:
                    detail = self._api.get_match_detail(mid, force_refresh=force_refresh)
                    details.append(detail)
                except Exception as e:
                    self._display.warning(f"Match #{mid}: {e}")
                progress.advance(task)

        self._display.success(f"{len(details)}/{len(match_ids)} détails chargés")
        return details

    # ── Compétitions ────────────────────────────────────────────────────

    def get_competitions(self, *, force_refresh: bool = False) -> list[Competition]:
        """Récupère la liste des compétitions."""
        self._ensure_connected()
        comps = self._api.get_competitions(force_refresh=force_refresh)
        self._display.success(f"{len(comps)} compétitions")
        return comps

    # ── Équipes & Lieux ─────────────────────────────────────────────────

    def get_equipes(self, *, sport: str | None = None,
                     championship: str | None = None,
                     force_refresh: bool = False) -> list[dict[str, Any]]:
        """Extrait les équipes uniques depuis les matchs."""
        self._ensure_connected()
        return self._api.get_equipes(sport=sport, championship=championship,
                                      force_refresh=force_refresh)

    def get_lieux(self, *, force_refresh: bool = False) -> list[dict[str, Any]]:
        """Extrait les lieux de pratique depuis les matchs."""
        self._ensure_connected()
        return self._api.get_lieux(force_refresh=force_refresh)

    # ── Affichage ───────────────────────────────────────────────────────

    def display_matches(self, matches: list[MatchInfo], *,
                         title: str = "Matchs MySportU",
                         show_competition: bool = False,
                         compact: bool = False) -> None:
        """Affiche les matchs dans un tableau Rich."""
        self._display.matches_table(matches, title=title,
                                     show_competition=show_competition,
                                     compact=compact)

    def display_match_detail(self, detail: MatchDetail,
                              match_info: MatchInfo | None = None) -> None:
        """Affiche les détails d'un match."""
        self._display.match_detail(detail, match_info)

    def display_competitions(self, competitions: list[Competition], *,
                              title: str = "Compétitions MySportU") -> None:
        """Affiche les compétitions."""
        self._display.competitions_table(competitions, title=title)

    def display_equipes(self, equipes: list[dict[str, Any]], *,
                         title: str = "Équipes MySportU") -> None:
        """Affiche les équipes."""
        self._display.equipes_table(equipes, title=title)

    def display_lieux(self, lieux: list[dict[str, Any]], *,
                       title: str = "Lieux de pratique") -> None:
        """Affiche les lieux."""
        self._display.lieux_table(lieux, title=title)

    def display_stats(self, matches: list[MatchInfo], *,
                       title: str = "Statistiques") -> None:
        """Affiche des statistiques sur les matchs."""
        self._display.stats_panel(matches, title=title)

    # ── Cache ───────────────────────────────────────────────────────────

    def show_cache_stats(self) -> None:
        """Affiche les statistiques du cache."""
        stats = self._api.cache_stats()
        self._display.cache_stats(stats)

    def clear_cache(self, resource_type: str | None = None) -> int:
        """
        Vide le cache.

        Args:
            resource_type: Si fourni, ne vide que ce type (matches, competitions, ...)
                           Sinon, vide tout.

        Returns:
            Nombre d'entrées supprimées
        """
        count = self._api.invalidate_cache(resource_type)
        label = resource_type or "tout"
        self._display.success(f"Cache vidé ({label}): {count} entrée(s)")
        return count

    def cleanup_cache(self) -> int:
        """Supprime les entrées expirées du cache."""
        count = self._cache.cleanup()
        self._display.success(f"Cache nettoyé: {count} entrée(s) expirée(s) supprimée(s)")
        return count

    # ── Context manager ─────────────────────────────────────────────────

    def __enter__(self) -> "MySportU":
        self.connect()
        return self

    def __exit__(self, *_: Any) -> None:
        self.disconnect()

    def __repr__(self) -> str:
        status = "connecté" if self._connected else "déconnecté"
        return f"<MySportU ({status})>"
