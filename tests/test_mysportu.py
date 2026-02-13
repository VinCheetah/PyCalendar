"""Tests pour le module pycalendar.mysportu."""

from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pycalendar.mysportu.models import (
    Competition,
    Equipe,
    LieuPratique,
    MatchDetail,
    MatchInfo,
    MatchState,
    Officiel,
    Participant,
    Regles,
    Score,
    ValidationEquipe,
)
from pycalendar.mysportu.cache import CacheManager
from pycalendar.mysportu.config import AuthConfig, CacheConfig, MySportUConfig, RequestConfig
from pycalendar.mysportu.exceptions import (
    APIError,
    AuthenticationError,
    CacheError,
    MySportUError,
)


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_match_api() -> dict:
    """Données brutes API pour un match."""
    return {
        "id": 42,
        "etat": "T",
        "forfait": None,
        "clos": True,
        "tour": 3,
        "poule": {"libelle": "VBM-A1-PA"},
        "score": [
            {"equipe_id": 100, "score": 3},
            {"equipe_id": 200, "score": 1},
        ],
        "receveur": {
            "id": 100,
            "libelle": "069069025 - AS INSA LYON",
            "libelle_court": "INSA (1)",
            "club": {"code": "069069025", "nom": "AS INSA LYON"},
        },
        "visiteur": {
            "id": 200,
            "libelle": "069069016 - AS ECL",
            "libelle_court": "ECL (2)",
            "club": {"code": "069069016", "nom": "AS ECL"},
        },
        "infosRencontre": {
            "competition_libelle": "ACAD LYON VBM PH2",
            "date_rencontre": "05/02/2026 20:00",
            "lieu_pratique": {"id": 1, "libelle": "HALLE - C.BESSON"},
        },
    }


@pytest.fixture
def sample_rencontre_detail() -> dict:
    """Données API pour le détail d'une rencontre."""
    return {
        "id": 42,
        "etat": "T",
        "forfait": None,
        "score": [
            {"equipe_id": 100, "score": 3},
            {"equipe_id": 200, "score": 1},
        ],
        "receveur": {
            "id": 100,
            "libelle": "INSA (1)",
            "libelle_court": "INSA (1)",
            "club": {"code": "069069025", "nom": "AS INSA LYON"},
        },
        "visiteur": {
            "id": 200,
            "libelle": "ECL (2)",
            "libelle_court": "ECL (2)",
            "club": {"code": "069069016", "nom": "AS ECL"},
        },
        "regles": {
            "nombre_joueurs_min": 6,
            "nombre_joueurs_max": 14,
            "nombre_titulaires": 6,
            "nombre_staffs_min": 0,
        },
        "validations": [
            {"equipe_id": 100, "joueurs_valide": True, "staffs_valide": True,
             "nb_joueurs": 8, "nb_staffs": 1},
            {"equipe_id": 200, "joueurs_valide": True, "staffs_valide": False,
             "nb_joueurs": 6, "nb_staffs": 0},
        ],
        "officiels": [
            {"id": 1, "nom": "Dupont", "prenom": "Jean", "est_present": True},
        ],
    }


@pytest.fixture
def sample_participants() -> dict:
    """Données API pour les participants d'un match."""
    return {
        "joueurs": [
            {"id": 1, "nom": "Martin", "prenom": "Alice", "equipe_id": 100,
             "numero": 7, "titulaire": True, "selectionne": True},
            {"id": 2, "nom": "Bernard", "prenom": "Bob", "equipe_id": 200,
             "numero": 3, "titulaire": True, "selectionne": True},
        ],
        "staffs": [
            {"id": 10, "nom": "Coach", "prenom": "Marc", "equipe_id": 100,
             "fonction": "Entraîneur", "selectionne": True},
        ],
    }


@pytest.fixture
def cache_dir(tmp_path: Path) -> Path:
    d = tmp_path / "cache_test"
    d.mkdir()
    return d


@pytest.fixture
def cache_config(cache_dir: Path) -> CacheConfig:
    return CacheConfig(
        enabled=True,
        directory=str(cache_dir),
        ttl_matches=60,
        ttl_competitions=120,
        ttl_match_detail=30,
        ttl_participants=30,
    )


@pytest.fixture
def cache_mgr(cache_config: CacheConfig) -> CacheManager:
    return CacheManager(cache_config)


# ─────────────────────────────────────────────────────────────────────────────
# Tests: MatchState
# ─────────────────────────────────────────────────────────────────────────────

class TestMatchState:
    def test_from_api_termine(self):
        assert MatchState.from_api("T") == MatchState.TERMINE

    def test_from_api_reporte(self):
        assert MatchState.from_api("R") == MatchState.REPORTE

    def test_from_api_annule(self):
        assert MatchState.from_api("N") == MatchState.ANNULE

    def test_from_api_forfait(self):
        assert MatchState.from_api(None, forfait={"type": "F"}) == MatchState.FORFAIT

    def test_from_api_non_joue(self):
        assert MatchState.from_api(None) == MatchState.NON_JOUE

    def test_is_cancelled(self):
        assert MatchState.REPORTE.is_cancelled
        assert MatchState.ANNULE.is_cancelled
        assert MatchState.FORFAIT.is_cancelled
        assert not MatchState.TERMINE.is_cancelled
        assert not MatchState.NON_JOUE.is_cancelled

    def test_label(self):
        assert MatchState.TERMINE.label == "Terminé"
        assert MatchState.NON_JOUE.label == "Non joué"


# ─────────────────────────────────────────────────────────────────────────────
# Tests: Score
# ─────────────────────────────────────────────────────────────────────────────

class TestScore:
    def test_from_api(self):
        scores = [{"equipe_id": 1, "score": 3}, {"equipe_id": 2, "score": 1}]
        score = Score.from_api(scores, receveur_id=1, visiteur_id=2)
        assert score is not None
        assert score.receveur == 3
        assert score.visiteur == 1

    def test_from_api_empty(self):
        assert Score.from_api([], receveur_id=1, visiteur_id=2) is None

    def test_str(self):
        assert str(Score(3, 1)) == "3-1"

    def test_reversed(self):
        r = Score(3, 1).reversed()
        assert r.receveur == 1
        assert r.visiteur == 3

    def test_roundtrip(self):
        s = Score(3, 1)
        assert Score.from_dict(s.to_dict()) == s


# ─────────────────────────────────────────────────────────────────────────────
# Tests: Competition
# ─────────────────────────────────────────────────────────────────────────────

class TestCompetition:
    def test_from_api(self):
        c = Competition.from_api({"id": 10, "libelle": "ACAD LYON VBM PH2"})
        assert c.id == 10
        assert c.sport == "VB"
        assert c.genre == "M"
        assert c.championship == "PH2"

    def test_from_api_feminin(self):
        c = Competition.from_api({"id": 11, "libelle": "ACAD LYON VBF PH2"})
        assert c.genre == "F"

    def test_from_api_basketball(self):
        c = Competition.from_api({"id": 12, "libelle": "ACAD LYON BBM PH1"})
        assert c.sport == "BB"
        assert c.championship == "PH1"

    def test_roundtrip(self):
        c = Competition.from_api({"id": 10, "libelle": "ACAD LYON VBM PH2"})
        assert Competition.from_dict(c.to_dict()) == c


# ─────────────────────────────────────────────────────────────────────────────
# Tests: Equipe
# ─────────────────────────────────────────────────────────────────────────────

class TestEquipe:
    def test_from_api(self):
        eq = Equipe.from_api({
            "id": 100,
            "libelle": "069069025 - AS INSA LYON",
            "libelle_court": "INSA (1)",
            "club": {"code": "069069025", "nom": "AS INSA LYON"},
        })
        assert eq.id == 100
        assert eq.libelle_court == "INSA (1)"
        assert eq.club_code == "069069025"

    def test_roundtrip(self):
        eq = Equipe(id=1, libelle="Test", libelle_court="T (1)",
                    club_code="123", club_nom="Club")
        assert Equipe.from_dict(eq.to_dict()) == eq


# ─────────────────────────────────────────────────────────────────────────────
# Tests: LieuPratique
# ─────────────────────────────────────────────────────────────────────────────

class TestLieuPratique:
    def test_from_api_dict(self):
        lieu = LieuPratique.from_api({"id": 1, "libelle": "BESSON"})
        assert lieu is not None
        assert lieu.libelle == "BESSON"

    def test_from_api_string(self):
        lieu = LieuPratique.from_api("BESSON")
        assert lieu is not None
        assert lieu.libelle == "BESSON"

    def test_from_api_none(self):
        assert LieuPratique.from_api(None) is None


# ─────────────────────────────────────────────────────────────────────────────
# Tests: MatchInfo
# ─────────────────────────────────────────────────────────────────────────────

class TestMatchInfo:
    def test_from_api(self, sample_match_api):
        m = MatchInfo.from_api(sample_match_api)
        assert m.id == 42
        assert m.sport == "VB"
        assert m.genre == "M"
        assert m.championship == "PH2"
        assert m.date == "05/02/2026"
        assert m.heure == "20:00"
        assert m.receveur.libelle_court == "INSA (1)"
        assert m.visiteur.libelle_court == "ECL (2)"
        assert m.state == MatchState.TERMINE
        assert m.score is not None
        assert str(m.score) == "3-1"
        assert m.lieu is not None
        assert m.lieu.libelle == "HALLE - C.BESSON"

    def test_from_api_non_joue(self, sample_match_api):
        sample_match_api["etat"] = None
        sample_match_api["score"] = []
        m = MatchInfo.from_api(sample_match_api)
        assert m.state == MatchState.NON_JOUE
        assert m.score is None

    def test_roundtrip(self, sample_match_api):
        m = MatchInfo.from_api(sample_match_api)
        m2 = MatchInfo.from_dict(m.to_dict())
        assert m2.id == m.id
        assert m2.sport == m.sport
        assert m2.state == m.state
        assert str(m2.score) == str(m.score)


# ─────────────────────────────────────────────────────────────────────────────
# Tests: MatchDetail
# ─────────────────────────────────────────────────────────────────────────────

class TestMatchDetail:
    def test_from_api(self, sample_rencontre_detail, sample_participants):
        d = MatchDetail.from_api(sample_rencontre_detail, sample_participants)
        assert d.id == 42
        assert d.receveur.libelle_court == "INSA (1)"
        assert d.state == MatchState.TERMINE
        assert len(d.joueurs) == 2
        assert len(d.staffs) == 1
        assert len(d.officiels) == 1
        assert len(d.validations) == 2
        assert d.regles.nb_joueurs_min == 6

    def test_is_ready(self, sample_rencontre_detail, sample_participants):
        d = MatchDetail.from_api(sample_rencontre_detail, sample_participants)
        assert d.is_ready  # Both validations have joueurs_valide=True + 1 officiel

    def test_joueurs_by_team(self, sample_rencontre_detail, sample_participants):
        d = MatchDetail.from_api(sample_rencontre_detail, sample_participants)
        assert len(d.joueurs_receveur) == 1  # equipe_id=100
        assert len(d.joueurs_visiteur) == 1  # equipe_id=200

    def test_roundtrip(self, sample_rencontre_detail, sample_participants):
        d = MatchDetail.from_api(sample_rencontre_detail, sample_participants)
        d2 = MatchDetail.from_dict(d.to_dict())
        assert d2.id == d.id
        assert len(d2.joueurs) == len(d.joueurs)
        assert len(d2.officiels) == len(d.officiels)


# ─────────────────────────────────────────────────────────────────────────────
# Tests: CacheManager
# ─────────────────────────────────────────────────────────────────────────────

class TestCacheManager:
    def test_put_and_get(self, cache_mgr):
        cache_mgr.put("matches", "test", {"data": [1, 2, 3]})
        entry = cache_mgr.get("matches", "test")
        assert entry is not None
        assert entry.data == {"data": [1, 2, 3]}
        assert entry.resource_type == "matches"

    def test_get_expired(self, cache_dir):
        config = CacheConfig(enabled=True, directory=str(cache_dir), ttl_matches=0)
        mgr = CacheManager(config)
        mgr.put("matches", "test", {"data": "old"})
        time.sleep(0.01)
        assert mgr.get("matches", "test") is None

    def test_get_missing(self, cache_mgr):
        assert cache_mgr.get("matches", "nonexistent") is None

    def test_invalidate_specific(self, cache_mgr):
        cache_mgr.put("matches", "a", {"x": 1})
        cache_mgr.put("matches", "b", {"x": 2})
        count = cache_mgr.invalidate("matches", "a")
        assert count == 1
        assert cache_mgr.get("matches", "a") is None
        # b should still exist
        assert cache_mgr.get("matches", "b") is not None

    def test_invalidate_type(self, cache_mgr):
        cache_mgr.put("matches", "a", {"x": 1})
        cache_mgr.put("competitions", "b", {"x": 2})
        count = cache_mgr.invalidate("matches")
        assert count == 1
        # Competitions should be untouched
        assert cache_mgr.get("competitions", "b") is not None

    def test_invalidate_all(self, cache_mgr):
        cache_mgr.put("matches", "a", {"x": 1})
        cache_mgr.put("competitions", "b", {"x": 2})
        count = cache_mgr.invalidate()
        assert count == 2

    def test_stats(self, cache_mgr):
        cache_mgr.put("matches", "a", [1])
        cache_mgr.put("competitions", "b", [2])
        stats = cache_mgr.stats()
        assert stats["total_entries"] == 2
        assert "matches" in stats["by_type"]
        assert "competitions" in stats["by_type"]

    def test_cleanup(self, cache_dir):
        config = CacheConfig(enabled=True, directory=str(cache_dir),
                             ttl_matches=0, ttl_competitions=9999)
        mgr = CacheManager(config)
        mgr.put("matches", "old", [1])
        time.sleep(0.01)
        mgr.put("competitions", "fresh", [2])
        count = mgr.cleanup()
        assert count == 1  # Only the expired one

    def test_disabled_cache(self, cache_dir):
        config = CacheConfig(enabled=False, directory=str(cache_dir))
        mgr = CacheManager(config)
        mgr.put("matches", "test", [1])
        assert mgr.get("matches", "test") is None

    def test_make_key(self):
        assert CacheManager.make_key(sport="VB", championship="PH2") == "championship=PH2_sport=VB"
        assert CacheManager.make_key() == "default"


# ─────────────────────────────────────────────────────────────────────────────
# Tests: Config
# ─────────────────────────────────────────────────────────────────────────────

class TestConfig:
    def test_default_config(self):
        config = MySportUConfig()
        assert config.auth.base_url == "https://gestion.mysportu.com"
        assert config.cache.enabled is True
        assert config.cache.ttl_matches == 300

    def test_load_with_overrides(self):
        config = MySportUConfig.load(username="test_user", verbose=True)
        assert config.auth.username == "test_user"
        assert config.verbose is True

    def test_load_yaml(self, tmp_path):
        yaml_file = tmp_path / "test_config.yaml"
        yaml_file.write_text("""
mysportu:
  auth:
    username: yaml_user
    password: yaml_pass
  cache:
    ttl_matches: 999
""")
        config = MySportUConfig.load(yaml_file)
        assert config.auth.username == "yaml_user"
        assert config.cache.ttl_matches == 999

    def test_env_override(self, monkeypatch):
        monkeypatch.setenv("MYSPORTU_USERNAME", "env_user")
        monkeypatch.setenv("MYSPORTU_PASSWORD", "env_pass")
        config = MySportUConfig.load()
        assert config.auth.username == "env_user"
        assert config.auth.password == "env_pass"

    def test_override_priority(self, monkeypatch):
        monkeypatch.setenv("MYSPORTU_USERNAME", "env_user")
        config = MySportUConfig.load(username="override_user")
        assert config.auth.username == "override_user"

    def test_login_url(self):
        auth = AuthConfig(base_url="https://test.com", login_path="/login")
        assert auth.login_url == "https://test.com/login"


# ─────────────────────────────────────────────────────────────────────────────
# Tests: Exceptions
# ─────────────────────────────────────────────────────────────────────────────

class TestExceptions:
    def test_api_error_with_status(self):
        err = APIError("test", status_code=404, url="/test")
        assert "404" in str(err)
        assert "/test" in str(err)

    def test_hierarchy(self):
        assert issubclass(AuthenticationError, MySportUError)
        assert issubclass(APIError, MySportUError)
        assert issubclass(CacheError, MySportUError)


# ─────────────────────────────────────────────────────────────────────────────
# Tests: Participant & Officiel
# ─────────────────────────────────────────────────────────────────────────────

class TestParticipant:
    def test_from_api(self):
        p = Participant.from_api({
            "id": 1, "nom": "Martin", "prenom": "Alice",
            "equipe_id": 100, "numero": 7, "titulaire": True,
        })
        assert p.nom_complet == "Alice Martin"
        assert p.numero == 7
        assert p.titulaire is True

    def test_roundtrip(self):
        p = Participant(id=1, nom="A", prenom="B", equipe_id=1,
                        role="joueur", numero=5)
        assert Participant.from_dict(p.to_dict()) == p


class TestOfficiel:
    def test_from_api(self):
        o = Officiel.from_api({"id": 1, "nom": "Dupont", "prenom": "Jean",
                               "est_present": True})
        assert o.nom_complet == "Jean Dupont"
        assert o.est_present is True

    def test_roundtrip(self):
        o = Officiel(id=1, nom="A", prenom="B", est_present=True)
        assert Officiel.from_dict(o.to_dict()) == o
