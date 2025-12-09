"""Shared penalty helper functions used by both solver and analyzers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

from ..config import Config
from ..models import Creneau, Match


@dataclass
class TimePenaltyContext:
    """Detailed information returned with the time preference penalty."""

    penalty: float
    equipes_avant: int = 0
    equipes_apres: int = 0


def horaire_to_minutes(horaire: Optional[str]) -> int:
    """Convert an hour string ("14:00", "14H30", "14") to minutes since midnight."""
    if not horaire:
        return 0
    cleaned = horaire.strip().upper().replace("H", ":")
    if ":" not in cleaned:
        cleaned = f"{cleaned}:00"
    parts = cleaned.split(":")
    try:
        heures = int(parts[0])
        minutes = int(parts[1]) if len(parts) > 1 and parts[1] else 0
    except (ValueError, IndexError):
        return 0
    return heures * 60 + minutes


def is_retour_match(match: Match) -> bool:
    """Return True when the match order corresponds to the retour leg."""
    id1 = getattr(match.equipe1, "id_unique", None) or match.equipe1.nom or match.equipe1.institution or ""
    id2 = getattr(match.equipe2, "id_unique", None) or match.equipe2.nom or match.equipe2.institution or ""
    ordered = tuple(sorted([id1 or "", id2 or ""]))
    return (id1 or "", id2 or "") != ordered


def compute_time_preference_penalty(match: Match, creneau: Creneau, config: Config) -> TimePenaltyContext:
    """Return penalty and counts for schedule vs preferred hours using solver formula."""
    penalty_total = 0.0
    if not creneau:
        return TimePenaltyContext(0.0, 0, 0)

    horaire_match_min = horaire_to_minutes(creneau.horaire)
    tolerance = getattr(config, "penalite_horaire_tolerance", 0) or 0
    diviseur = getattr(config, "penalite_horaire_diviseur", 60) or 60

    equipes_avant_distances: List[int] = []
    equipes_apres_distances: List[int] = []

    for equipe in (match.equipe1, match.equipe2):
        prefs = getattr(equipe, "horaires_preferes", None) or []
        if not prefs:
            continue
        pref_minutes = horaire_to_minutes(prefs[0])
        distance = abs(horaire_match_min - pref_minutes)
        if distance <= tolerance:
            continue
        if horaire_match_min < pref_minutes:
            equipes_avant_distances.append(distance)
        else:
            equipes_apres_distances.append(distance)

    if equipes_avant_distances:
        if len(equipes_avant_distances) >= 2:
            multiplicateur_avant = getattr(config, "penalite_avant_horaire_min_deux", 0.0)
        else:
            multiplicateur_avant = getattr(config, "penalite_avant_horaire_min", 0.0)
        for distance in equipes_avant_distances:
            penalty_total += multiplicateur_avant * ((distance / diviseur) ** 2)

    if equipes_apres_distances:
        multiplicateur_apres = getattr(config, "penalite_apres_horaire_min", 0.0)
        for distance in equipes_apres_distances:
            penalty_total += multiplicateur_apres * ((distance / diviseur) ** 2)

    return TimePenaltyContext(
        penalty=penalty_total,
        equipes_avant=len(equipes_avant_distances),
        equipes_apres=len(equipes_apres_distances),
    )


def compute_gym_preference_penalty(match: Match, creneau: Creneau, config: Config) -> float:
    """Apply the shared gym preference penalty formula (bonus-based)."""
    bonuses = getattr(config, "bonus_preferences_gymnases", None)
    if not bonuses:
        return 0.0

    base_penalty = 2 * max(bonuses)
    penalty_total = 0.0

    for equipe in (match.equipe1, match.equipe2):
        equipe_penalty = base_penalty
        prefs = [pref for pref in (getattr(equipe, "lieux_preferes", None) or []) if pref]
        for rang, gymnase_pref in enumerate(prefs):
            if gymnase_pref == creneau.gymnase and rang < len(bonuses):
                equipe_penalty -= bonuses[rang]
                break
        penalty_total += equipe_penalty

    return penalty_total


def _extract_match_level(match: Match) -> Optional[int]:
    poule = (getattr(match, "poule", "") or "").strip()
    if not poule:
        return None
    digits = re.search(r"(\d+)", poule)
    if not digits:
        return None
    level_idx = int(digits.group(1)) - 1
    return level_idx if level_idx >= 0 else None


def _normalize_gym_level_label(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    normalized = str(value).strip().lower()
    if 'haut' in normalized:
        return 'haut'
    if 'bas' in normalized:
        return 'bas'
    return normalized or None


def compute_gym_level_penalty(
    match: Match,
    creneau: Creneau,
    config: Config,
    niveaux_gymnases: Optional[Dict[str, str]] = None,
) -> float:
    """Penalty or bonus when gym level mismatches match level."""
    if not creneau:
        return 0.0

    niveau_match = _extract_match_level(match)
    if niveau_match is None:
        return 0.0

    niveaux = niveaux_gymnases or {}
    niveau_gym = _normalize_gym_level_label(niveaux.get(creneau.gymnase))
    if not niveau_gym:
        return 0.0

    poids_haut = getattr(config, "poids_niveaux_gymnases_haut", None) or []
    poids_bas = getattr(config, "poids_niveaux_gymnases_bas", None) or []

    table = poids_haut if niveau_gym == "haut" else poids_bas
    if niveau_match >= len(table):
        return 0.0
    return float(table[niveau_match])


def _infer_match_genre(match: Match) -> Optional[str]:
    for equipe in (match.equipe1, match.equipe2):
        genre = getattr(equipe, 'genre', None)
        if genre:
            genre_clean = str(genre).strip().upper()
            if genre_clean in {'M', 'F'}:
                return genre_clean
    metadata_genre = (match.metadata or {}).get('genre') if hasattr(match, 'metadata') else None
    if metadata_genre:
        genre_clean = str(metadata_genre).strip().upper()
        if genre_clean in {'M', 'F'}:
            return genre_clean
    return None


def compute_gym_gender_priority_penalty(
    match: Match,
    creneau: Creneau,
    config: Config,
    priorites_genre: Optional[Dict[str, str]] = None,
) -> float:
    """Penalize matches scheduled in a venue with opposite gender priority."""
    if not creneau or not priorites_genre:
        return 0.0

    penalty_value = getattr(config, 'penalite_gymnase_priorite_genre', 0.0) or 0.0
    if penalty_value <= 0:
        return 0.0

    priorite = priorites_genre.get(creneau.gymnase)
    if not priorite:
        return 0.0
    priorite_clean = str(priorite).strip().upper()
    if priorite_clean not in {'M', 'F'}:
        return 0.0

    match_genre = _infer_match_genre(match)
    if not match_genre:
        return 0.0

    if match_genre != priorite_clean:
        return float(penalty_value)
    return 0.0


def compaction_penalty_for_week(config: Config, semaine: int) -> float:
    penalites = getattr(config, "compaction_penalites_par_semaine", None) or []
    if not penalites or semaine <= 0:
        return 0.0
    if semaine <= len(penalites):
        return float(penalites[semaine - 1])
    return 0.0


def spacing_penalty_for_gap(config: Config, weeks_rest: int) -> float:
    penalites = getattr(config, "penalites_espacement_repos", None) or []
    if weeks_rest < 0 or weeks_rest >= len(penalites):
        return 0.0
    return float(penalites[weeks_rest])


def aller_retour_gap_penalty(config: Config, weeks_gap: int) -> float:
    penalites = getattr(config, "aller_retour_penalites_par_ecart", None) or []
    if weeks_gap < 0:
        return 0.0
    if weeks_gap >= len(penalites):
        return 0.0
    return float(penalites[weeks_gap])
