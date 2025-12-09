"""Penalty breakdown computation for PyCalendar solutions."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

from ..core.models import Match, Solution
from ..core.penalty_calculator import annotate_solution_with_penalties
from ..core.penalties import aller_retour_gap_penalty, is_retour_match
from ..validation.solution_validator import SolutionValidator


def _safe_float(value: Any, default: float = 0.0) -> float:
    """Convertit en float en tolérant les valeurs None ou non numériques."""
    try:
        if value is None:
            return float(default)
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def calculate_penalty_breakdown(
    solution: Solution,
    config: Any,
    equipes: Optional[List] = None,
    gymnases: Optional[List] = None,
    niveaux_gymnases: Optional[Dict[str, str]] = None,
    priorites_genre_gymnases: Optional[Dict[str, str]] = None,
    ententes: Optional[Dict[Tuple[str, str], float]] = None,
    obligations_presence: Optional[Dict[str, str]] = None,
    groupes_non_simultaneite: Optional[Dict[str, List[str]]] = None,
) -> Dict[str, Any]:
    """Compute the full penalty decomposition for the UI."""

    breakdown = _build_empty_breakdown(solution.score if solution else 0.0)
    if not solution:
        return breakdown

    matchs_planifies = solution.matchs_planifies or []
    matchs_non_planifies = solution.matchs_non_planifies or []

    niveaux_norm = _normalize_levels(niveaux_gymnases or {})
    priorites_norm = _normalize_priorities(priorites_genre_gymnases or {})
    ententes_map = ententes or {}

    if config and matchs_planifies:
        try:
            annotate_solution_with_penalties(
                solution,
                config,
                niveaux_norm,
                priorites_genre_gymnases=priorites_norm,
            )
        except Exception:
            pass  # Annotation is best-effort; do not block export

    rapport_validation = _run_validator(
        solution,
        config,
        gymnases,
        obligations_presence or {},
        groupes_non_simultaneite or {},
    )

    breakdown["contraintes_dures"] = _extract_hard_constraints(rapport_validation)

    if rapport_validation and rapport_validation.get("stats_overlaps"):
        overlaps = rapport_validation["stats_overlaps"]
        breakdown["contraintes_institutionnelles"]["overlaps"]["count"] = int(overlaps.get("nb_overlaps", 0))
        breakdown["contraintes_institutionnelles"]["overlaps"]["penalty"] = _safe_float(overlaps.get("penalite_overlaps", 0.0))

    breakdown["preferences_gymnases"] = _analyze_gym_preferences(matchs_planifies, config)
    breakdown["niveau_gymnases"] = _analyze_niveau_gymnases(matchs_planifies, config, niveaux_norm)
    breakdown["priorite_genre_gymnases"] = _analyze_priorite_genre(matchs_planifies, priorites_norm)
    breakdown["horaires_preferes"] = _analyze_time_preferences(matchs_planifies, config)
    breakdown["espacement_repos"] = _analyze_spacing(matchs_planifies)
    breakdown["compaction_temporelle"] = _analyze_compaction(matchs_planifies, config)

    ententes_stats = _analyze_ententes(matchs_planifies, matchs_non_planifies, ententes_map, config)
    breakdown["contraintes_institutionnelles"]["ententes"].update(ententes_stats)

    breakdown["contraintes_temporelles"] = _analyze_temporal_constraints(matchs_planifies)
    breakdown["aller_retour"] = _analyze_aller_retour(matchs_planifies, config)

    # L'équilibrage est géré directement dans le solveur, difficile à reconstruire ici.
    # On expose néanmoins la contribution totale si elle est stockée dans la solution.
    breakdown["equilibrage_charge"]["penalty"] = _safe_float(
        solution.metadata.get("equilibrage_penalty", 0.0) if solution.metadata else 0.0
    )

    return breakdown


def _build_empty_breakdown(score: float) -> Dict[str, Any]:
    return {
        "score_total": _safe_float(score),
        "contraintes_dures": {
            "indisponibilite": {"violations": 0, "penalty": 0.0},
            "capacite": {"violations": 0, "penalty": 0.0},
        },
        "preferences_gymnases": {
            "matchs_en_gymnases_preferes": 0,
            "bonus_total": 0.0,
            "par_rang": {},
        },
        "niveau_gymnases": {
            "matchs_bien_assignes": 0,
            "matchs_mal_assignes": 0,
            "bonus_total": 0.0,
            "penalty_total": 0.0,
        },
        "priorite_genre_gymnases": {
            "matchs_couverts": 0,
            "matchs_violations": 0,
            "matchs_respect_priorite": 0,
            "penalty_total": 0.0,
        },
        "horaires_preferes": {
            "matchs_ok": 0,
            "matchs_apres": {"count": 0, "penalty": 0.0},
            "matchs_avant_1_equipe": {"count": 0, "penalty": 0.0},
            "matchs_avant_2_equipes": {"count": 0, "penalty": 0.0},
        },
        "espacement_repos": {"violations": 0, "penalty": 0.0},
        "compaction_temporelle": {"penalty_total": 0.0, "par_semaine": {}},
        "contraintes_institutionnelles": {
            "overlaps": {"count": 0, "penalty": 0.0},
            "ententes": {"planifiees": 0, "non_planifiees": 0, "penalty": 0.0},
        },
        "contraintes_temporelles": {"violations": 0, "penalty": 0.0},
        "aller_retour": {
            "par_ecart": {},
            "ordre": {"count": 0, "penalty": 0.0},
            "meme_semaine": {"count": 0, "penalty": 0.0},
            "consecutives": {"count": 0, "penalty": 0.0},
        },
        "equilibrage_charge": {"penalty": 0.0},
    }


def _normalize_levels(levels: Dict[str, str]) -> Dict[str, str]:
    normalized = {}
    for gymnase, niveau in levels.items():
        if not niveau:
            continue
        text = str(niveau).lower()
        if "haut" in text:
            normalized[gymnase] = "haut"
        elif "bas" in text:
            normalized[gymnase] = "bas"
        else:
            normalized[gymnase] = text
    return normalized


def _normalize_priorities(priorities: Dict[str, str]) -> Dict[str, str]:
    normalized = {}
    for gymnase, genre in priorities.items():
        if not genre:
            continue
        genre_clean = str(genre).strip().upper()
        if genre_clean in {"M", "F"}:
            normalized[gymnase] = genre_clean
    return normalized


def _run_validator(
    solution: Solution,
    config: Any,
    gymnases: Optional[List],
    obligations_presence: Dict[str, str],
    groupes_non_simultaneite: Dict[str, List[str]],
) -> Optional[Dict[str, Any]]:
    if not (solution and config and gymnases):
        return None
    gym_dict = {g.nom: g for g in gymnases}
    try:
        validator = SolutionValidator(config, gym_dict, obligations_presence, groupes_non_simultaneite)
        _, rapport = validator.valider_solution(solution)
        rapport["violations_dures"] = rapport.get("violations_dures", [])
        return rapport
    except Exception:
        return None


def _extract_hard_constraints(rapport_validation: Optional[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    stats = {
        "indisponibilite": {"violations": 0, "penalty": 0.0},
        "capacite": {"violations": 0, "penalty": 0.0},
    }
    if not rapport_validation:
        return stats

    for violation in rapport_validation.get("violations_dures", []):
        v_type = violation.type_contrainte if hasattr(violation, "type_contrainte") else ""
        cible = "capacite" if v_type == "Capacité gymnase" else "indisponibilite"
        stats[cible]["violations"] += 1
        stats[cible]["penalty"] += _safe_float(getattr(violation, "penalite", 0.0))
    return stats


def _analyze_gym_preferences(matchs: List[Match], config: Any) -> Dict[str, Any]:
    stats = {
        "matchs_en_gymnases_preferes": 0,
        "bonus_total": 0.0,
        "par_rang": {},
    }
    if not config or not getattr(config, "bonus_preferences_gymnases", None):
        return stats

    bonus_values = list(getattr(config, "bonus_preferences_gymnases", []) or [])

    for match in matchs:
        if not match.creneau:
            continue
        gymnase = match.creneau.gymnase
        match_has_pref = False
        for equipe in (match.equipe1, match.equipe2):
            prefs = [p for p in getattr(equipe, "lieux_preferes", []) if p]
            if not prefs:
                continue
            try:
                rang = prefs.index(gymnase)
            except ValueError:
                continue
            match_has_pref = True
            if rang < len(bonus_values):
                bonus = _safe_float(bonus_values[rang])
                if bonus:
                    stats["bonus_total"] -= bonus
                    stats["par_rang"][str(rang + 1)] = stats["par_rang"].get(str(rang + 1), 0) + 1
            else:
                stats["par_rang"].setdefault(str(rang + 1), 0)
        if match_has_pref:
            stats["matchs_en_gymnases_preferes"] += 1
    return stats


def _analyze_niveau_gymnases(
    matchs: List[Match],
    config: Any,
    niveaux_gymnases: Dict[str, str],
) -> Dict[str, float]:
    stats = {
        "matchs_bien_assignes": 0,
        "matchs_mal_assignes": 0,
        "bonus_total": 0.0,
        "penalty_total": 0.0,
    }
    if not (config and niveaux_gymnases):
        return stats

    penalties_haut = (
        getattr(config, "poids_niveaux_gymnases_haut", None)
        or getattr(config, "penalite_niveau_gymnases_haut", [])
        or []
    )
    penalties_bas = (
        getattr(config, "poids_niveaux_gymnases_bas", None)
        or getattr(config, "penalite_niveau_gymnases_bas", [])
        or []
    )

    for match in matchs:
        if not match.creneau:
            continue
        niveau_match = _extract_match_level(match)
        if niveau_match is None:
            continue
        niveau_gym = niveaux_gymnases.get(match.creneau.gymnase)
        if not niveau_gym:
            continue
        penalty_table = penalties_haut if niveau_gym == "haut" else penalties_bas
        if niveau_match >= len(penalty_table):
            continue
        valeur = _safe_float(penalty_table[niveau_match])
        if valeur <= 0:
            stats["matchs_bien_assignes"] += 1
            stats["bonus_total"] += valeur
        else:
            stats["matchs_mal_assignes"] += 1
            stats["penalty_total"] += valeur
    return stats


def _analyze_priorite_genre(
    matchs: List[Match],
    priorites_genre: Dict[str, str],
) -> Dict[str, float]:
    stats = {
        "matchs_couverts": 0,
        "matchs_violations": 0,
        "matchs_respect_priorite": 0,
        "penalty_total": 0.0,
    }
    if not priorites_genre:
        return stats

    for match in matchs:
        if not match.creneau:
            continue
        priorite = priorites_genre.get(match.creneau.gymnase)
        if not priorite:
            continue
        stats["matchs_couverts"] += 1
        penalties = (match.metadata or {}).get("penalties", {})
        penalty_value = _safe_float(penalties.get("priorite_genre_gymnase", 0.0))
        if penalty_value > 0:
            stats["matchs_violations"] += 1
            stats["penalty_total"] += penalty_value
        else:
            stats["matchs_respect_priorite"] += 1
    return stats


def _extract_match_level(match: Match) -> Optional[int]:
    poule = getattr(match, "poule", "") or ""
    if len(poule) >= 2 and poule[0].upper() == "A" and poule[1].isdigit():
        return int(poule[1]) - 1
    return None



def _analyze_time_preferences(matchs: List[Match], config: Any) -> Dict[str, Any]:
    stats = {
        "matchs_ok": 0,
        "matchs_apres": {"count": 0, "penalty": 0.0},
        "matchs_avant_1_equipe": {"count": 0, "penalty": 0.0},
        "matchs_avant_2_equipes": {"count": 0, "penalty": 0.0},
    }
    if not config:
        stats["matchs_ok"] = sum(1 for m in matchs if m.creneau)
        return stats

    tolerance = getattr(config, "penalite_horaire_tolerance", 0)
    diviseur = getattr(config, "penalite_horaire_diviseur", 60) or 60
    penalite_avant = getattr(config, "penalite_avant_horaire_min", 0.0)
    penalite_avant_deux = getattr(config, "penalite_avant_horaire_min_deux", penalite_avant)
    penalite_apres = getattr(config, "penalite_apres_horaire_min", 0.0)

    for match in matchs:
        if not match.creneau:
            continue
        horaire_match = _parse_horaire_minutes(match.creneau.horaire)
        if horaire_match is None:
            continue

        distances_avant = []
        distances_apres = []

        equipes_consideres = 0
        for equipe in (match.equipe1, match.equipe2):
            prefs = getattr(equipe, "horaires_preferes", []) or []
            if not prefs:
                continue
            equipes_consideres += 1
            pref_minutes = _parse_horaire_minutes(prefs[0])
            if pref_minutes is None:
                continue
            distance = abs(horaire_match - pref_minutes)
            if distance <= tolerance:
                continue
            if horaire_match < pref_minutes:
                distances_avant.append(distance)
            else:
                distances_apres.append(distance)

        if not distances_avant and not distances_apres:
            if equipes_consideres > 0:
                stats["matchs_ok"] += 1
            continue

        if distances_avant:
            if len(distances_avant) >= 2:
                multiplicateur = penalite_avant_deux
                stats["matchs_avant_2_equipes"]["count"] += 1
            else:
                multiplicateur = penalite_avant
                stats["matchs_avant_1_equipe"]["count"] += 1
            for distance in distances_avant:
                penalty = multiplicateur * ((distance / diviseur) ** 2)
                key = "matchs_avant_2_equipes" if len(distances_avant) >= 2 else "matchs_avant_1_equipe"
                stats[key]["penalty"] += penalty

        if distances_apres:
            stats["matchs_apres"]["count"] += len(distances_apres)
            for distance in distances_apres:
                penalty = penalite_apres * ((distance / diviseur) ** 2)
                stats["matchs_apres"]["penalty"] += penalty

    return stats


def _parse_horaire_minutes(value: str) -> Optional[int]:
    if not value:
        return None
    cleaned = value.lower().replace("h", ":")
    try:
        heures, minutes = cleaned.split(":")
        return int(heures) * 60 + int(minutes or 0)
    except ValueError:
        try:
            return int(cleaned) * 60
        except ValueError:
            return None


def _analyze_spacing(matchs: List[Match]) -> Dict[str, float]:
    stats = {"violations": 0, "penalty": 0.0}
    for match in matchs:
        penalties = (match.metadata or {}).get("penalties", {})
        value = _safe_float(penalties.get("espacement", 0.0) or 0.0)
        if value > 0:
            stats["violations"] += 1
            stats["penalty"] += value
    return stats


def _analyze_compaction(matchs: List[Match], config: Any) -> Dict[str, Any]:
    stats = {"penalty_total": 0.0, "par_semaine": {}}
    if not (config and getattr(config, "compaction_temporelle_actif", False)):
        return stats
    penalties = list(getattr(config, "compaction_penalites_par_semaine", []) or [])
    if not penalties:
        return stats

    max_index = len(penalties) - 1
    for match in matchs:
        if not match.creneau:
            continue
        semaine = match.creneau.semaine
        if semaine <= 0:
            continue
        idx = min(semaine - 1, max_index)
        penalty = _safe_float(penalties[idx])
        if penalty <= 0:
            entry = stats["par_semaine"].setdefault(str(semaine), {"nb_matchs": 0, "penalty": 0.0})
            entry["nb_matchs"] += 1
            continue
        stats["penalty_total"] += penalty
        entry = stats["par_semaine"].setdefault(str(semaine), {"nb_matchs": 0, "penalty": 0.0})
        entry["nb_matchs"] += 1
        entry["penalty"] += penalty
    return stats


def _analyze_ententes(
    matchs_planifies: List[Match],
    matchs_non_planifies: List[Match],
    ententes: Dict[Tuple[str, str], float],
    config: Any,
) -> Dict[str, float]:
    stats = {"planifiees": 0, "non_planifiees": 0, "penalty": 0.0}
    fallback_penalty = _safe_float(getattr(config, "entente_penalite_non_planif", 0.0) if config else 0.0)

    for match in matchs_planifies:
        if (match.metadata or {}).get("is_entente"):
            stats["planifiees"] += 1

    for match in matchs_non_planifies:
        if not (match.metadata or {}).get("is_entente"):
            continue
        stats["non_planifiees"] += 1
        cle = tuple(sorted([match.equipe1.institution, match.equipe2.institution]))
        valeur = ententes.get(cle, None)
        stats["penalty"] += _safe_float(valeur, default=fallback_penalty)
    return stats


def _analyze_temporal_constraints(matchs: List[Match]) -> Dict[str, float]:
    stats = {"violations": 0, "penalty": 0.0}
    for match in matchs:
        penalties = (match.metadata or {}).get("penalties", {})
        value = _safe_float(penalties.get("contrainte_temporelle", 0.0) or 0.0)
        if value > 0:
            stats["violations"] += 1
            stats["penalty"] += value
    return stats


def _analyze_aller_retour(matchs: List[Match], config: Any) -> Dict[str, Any]:
    stats = {
        "par_ecart": {},
        "ordre": {"count": 0, "penalty": 0.0},
        "meme_semaine": {"count": 0, "penalty": 0.0},
        "consecutives": {"count": 0, "penalty": 0.0},
    }
    if not config:
        return stats

    ordre_penalite = _safe_float(getattr(config, "aller_retour_penalite_ordre_retour", 0.0))
    paires = defaultdict(list)

    for match in matchs:
        if not match.est_planifie() or not match.creneau:
            continue
        key = (
            getattr(match, "poule", None),
            tuple(sorted([
                getattr(match.equipe1, "id_unique", match.equipe1.nom),
                getattr(match.equipe2, "id_unique", match.equipe2.nom),
            ])),
        )
        paires[key].append(match)

    def _sort_key(m: Match) -> Tuple[int, str]:
        semaine = m.creneau.semaine if (m.creneau and m.creneau.semaine is not None) else 0
        equipe_tags = [
            getattr(m.equipe1, "id_unique", None) or m.equipe1.nom or m.equipe1.nom_complet,
            getattr(m.equipe2, "id_unique", None) or m.equipe2.nom or m.equipe2.nom_complet,
        ]
        ident = "|".join(sorted(equipe_tags))
        return (semaine, ident)

    for matchs_pair in paires.values():
        allers = [m for m in matchs_pair if not is_retour_match(m)]
        retours = [m for m in matchs_pair if is_retour_match(m)]
        if not allers or not retours:
            continue

        allers = sorted(allers, key=_sort_key)
        retours = sorted(retours, key=_sort_key)

        for aller_match, retour_match in zip(allers, retours):
            if not (aller_match.creneau and retour_match.creneau):
                continue
            weeks_gap = abs(aller_match.creneau.semaine - retour_match.creneau.semaine)
            gap_penalty = aller_retour_gap_penalty(config, weeks_gap)
            if gap_penalty > 0:
                bucket = stats["par_ecart"].setdefault(str(weeks_gap), {"count": 0, "penalty": 0.0})
                bucket["count"] += 1
                bucket["penalty"] += gap_penalty

            if ordre_penalite > 0 and retour_match.creneau.semaine <= aller_match.creneau.semaine:
                stats["ordre"]["count"] += 1
                stats["ordre"]["penalty"] += ordre_penalite

    stats["meme_semaine"] = dict(stats["par_ecart"].get("0", {"count": 0, "penalty": 0.0}))
    stats["consecutives"] = dict(stats["par_ecart"].get("1", {"count": 0, "penalty": 0.0}))
    return stats
