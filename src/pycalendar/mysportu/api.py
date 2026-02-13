"""
Couche API haut-niveau pour MySportU.

Combine le client HTTP, le cache, et les modèles pour fournir
des méthodes propres et typées pour accéder aux données.
"""

from __future__ import annotations

import logging
from typing import Any, Callable

from .cache import CacheManager
from .client import MySportUClient
from .config import MySportUConfig
from .models import (
    Competition,
    MatchDetail,
    MatchInfo,
)

logger = logging.getLogger(__name__)


class MySportUAPI:
    """
    API haut-niveau avec cache intégré.

    Chaque méthode supporte :
    - ``force_refresh=True`` pour ignorer le cache
    - Stockage automatique en cache des résultats
    - Conversion automatique vers les modèles typés
    """

    def __init__(self, client: MySportUClient, cache: CacheManager, config: MySportUConfig):
        self._client = client
        self._cache = cache
        self._config = config

    # ── Matchs (liste paginée) ──────────────────────────────────────────

    def get_all_matches(self, *, force_refresh: bool = False,
                        on_progress: Callable[[int, int, int], None] | None = None,
                        ) -> list[MatchInfo]:
        """
        Récupère TOUS les matchs (paginés).

        Args:
            force_refresh: Ignorer le cache
            on_progress: Callback (page_courante, total_pages, nb_matchs)

        Returns:
            Liste de tous les MatchInfo
        """
        cache_key = "all"

        if not force_refresh:
            entry = self._cache.get("matches", cache_key)
            if entry is not None:
                logger.info("Matchs chargés depuis le cache (%s)", entry.age_display())
                return [MatchInfo.from_dict(m) for m in entry.data]

        # Récupération paginée
        all_raw: list[dict] = []
        page = 1
        last_page: int | None = None

        while True:
            data = self._client.get_json("/feuille-de-match/rencontres", params={"page": page})

            if not data or "data" not in data:
                break

            matches = data["data"]
            if not matches:
                break

            meta = data.get("meta", {})
            if last_page is None:
                last_page = meta.get("last_page", 1)

            all_raw.extend(matches)

            if on_progress:
                on_progress(page, last_page or 1, len(all_raw))

            if page >= (last_page or 1):
                break

            page += 1

        # Sauvegarder en cache (données brutes pour sérialisation)
        typed = [MatchInfo.from_api(m) for m in all_raw]
        self._cache.put("matches", cache_key, [m.to_dict() for m in typed])

        logger.info("%d matchs récupérés depuis l'API", len(typed))
        return typed

    def get_matches(
        self,
        *,
        sport: str | None = None,
        championship: str | None = None,
        genre: str | None = None,
        date: str | None = None,
        state: str | None = None,
        force_refresh: bool = False,
        on_progress: Callable[[int, int, int], None] | None = None,
    ) -> list[MatchInfo]:
        """
        Récupère les matchs avec filtres.

        Les filtres sont appliqués côté client (l'API MySportU ne supporte
        pas le filtrage serveur).

        Args:
            sport: Code sport (VB, HB, BB, ...)
            championship: Code championnat (PH1, PH2, CFU, CFE, ...)
            genre: Genre (M, F)
            date: Date au format dd/mm/yyyy
            state: État (non_joue, termine, reporte, annule, forfait)
            force_refresh: Ignorer le cache
            on_progress: Callback de progression

        Returns:
            Liste de MatchInfo filtrés
        """
        all_matches = self.get_all_matches(
            force_refresh=force_refresh,
            on_progress=on_progress,
        )

        return _filter_matches(all_matches, sport=sport, championship=championship,
                               genre=genre, date=date, state=state)

    # ── Compétitions ────────────────────────────────────────────────────

    def get_competitions(self, *, force_refresh: bool = False) -> list[Competition]:
        """
        Récupère la liste des compétitions.

        Args:
            force_refresh: Ignorer le cache

        Returns:
            Liste de Competition
        """
        cache_key = "all"

        if not force_refresh:
            entry = self._cache.get("competitions", cache_key)
            if entry is not None:
                logger.info("Compétitions chargées depuis le cache (%s)", entry.age_display())
                return [Competition.from_dict(c) for c in entry.data]

        data = self._client.get_json("/feuille-de-match/ajax/competitions")

        typed = [Competition.from_api(c) for c in (data or [])]
        self._cache.put("competitions", cache_key, [c.to_dict() for c in typed])

        logger.info("%d compétitions récupérées depuis l'API", len(typed))
        return typed

    # ── Détail d'un match ───────────────────────────────────────────────

    def get_match_detail(self, match_id: int, *, force_refresh: bool = False,
                         include_participants: bool = True) -> MatchDetail:
        """
        Récupère les détails complets d'un match.

        Args:
            match_id: ID du match MySportU
            force_refresh: Ignorer le cache
            include_participants: Charger aussi les joueurs/staff

        Returns:
            MatchDetail avec joueurs, staff, officiels, validations
        """
        cache_key = str(match_id)

        if not force_refresh:
            entry = self._cache.get("match_detail", cache_key)
            if entry is not None:
                logger.debug("Détail match %d depuis le cache (%s)", match_id,
                             entry.age_display())
                return MatchDetail.from_dict(entry.data)

        # Récupérer le match
        data = self._client.get_json(f"/feuille-de-match/rencontre/{match_id}")
        rencontre = data.get("rencontre", data) if data else {}

        # Récupérer les participants si demandé
        participants = None
        if include_participants:
            try:
                participants = self._client.get_json(
                    f"/feuille-de-match/rencontre/{match_id}/participants"
                )
            except Exception:
                logger.warning("Impossible de charger les participants pour le match %d",
                               match_id)

        detail = MatchDetail.from_api(rencontre, participants)
        self._cache.put("match_detail", cache_key, detail.to_dict())

        return detail

    # ── Lieux de pratique ───────────────────────────────────────────────

    def get_lieux(self, *, force_refresh: bool = False) -> list[dict[str, Any]]:
        """
        Extrait les lieux de pratique uniques depuis les matchs.

        Returns:
            Liste de dicts {libelle, count} triée par fréquence
        """
        matches = self.get_all_matches(force_refresh=force_refresh)
        lieu_counts: dict[str, int] = {}
        for m in matches:
            if m.lieu:
                lieu_counts[m.lieu.libelle] = lieu_counts.get(m.lieu.libelle, 0) + 1

        return sorted(
            [{"libelle": k, "count": v} for k, v in lieu_counts.items()],
            key=lambda x: x["count"],
            reverse=True,
        )

    # ── Équipes uniques ─────────────────────────────────────────────────

    def get_equipes(self, *, sport: str | None = None,
                    championship: str | None = None,
                    force_refresh: bool = False) -> list[dict[str, Any]]:
        """
        Extrait les équipes uniques depuis les matchs.

        Returns:
            Liste de dicts {libelle_court, club_code, genre, count}
        """
        matches = self.get_matches(sport=sport, championship=championship,
                                   force_refresh=force_refresh)
        equipe_map: dict[tuple[str, str], dict[str, Any]] = {}

        for m in matches:
            for eq in (m.receveur, m.visiteur):
                key = (eq.libelle_court, m.genre)
                if key not in equipe_map:
                    equipe_map[key] = {
                        "libelle_court": eq.libelle_court,
                        "club_code": eq.club_code,
                        "club_nom": eq.club_nom,
                        "genre": m.genre,
                        "count": 0,
                    }
                equipe_map[key]["count"] += 1

        return sorted(equipe_map.values(), key=lambda x: (x["genre"], x["libelle_court"]))

    # ── Cache management ────────────────────────────────────────────────

    def invalidate_cache(self, resource_type: str | None = None) -> int:
        """Invalide le cache (tout ou par type)."""
        return self._cache.invalidate(resource_type)

    def cache_stats(self) -> dict[str, Any]:
        """Retourne les statistiques du cache."""
        return self._cache.stats()


# ─────────────────────────────────────────────────────────────────────────────
# Filtrage côté client
# ─────────────────────────────────────────────────────────────────────────────

def _filter_matches(
    matches: list[MatchInfo],
    *,
    sport: str | None = None,
    championship: str | None = None,
    genre: str | None = None,
    date: str | None = None,
    state: str | None = None,
) -> list[MatchInfo]:
    """Filtre une liste de matchs selon les critères."""
    result = matches

    if sport:
        sport_upper = sport.upper()
        result = [m for m in result if sport_upper in m.competition_libelle.upper()]

    if championship:
        champ_upper = championship.upper()
        result = [m for m in result if champ_upper in m.competition_libelle.upper()]

    if genre:
        genre_upper = genre.upper()
        result = [m for m in result if m.genre == genre_upper]

    if date:
        result = [m for m in result if m.date == date]

    if state:
        from .models import MatchState as MS
        try:
            target = MS(state)
        except ValueError:
            target = None
        if target:
            result = [m for m in result if m.state == target]

    return result
