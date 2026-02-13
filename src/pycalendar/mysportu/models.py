"""
Modèles de données pour l'API MySportU.

Tous les modèles sont des dataclasses immuables (frozen) qui peuvent être
sérialisées en JSON pour le cache et désérialisées depuis les réponses API.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


# ─────────────────────────────────────────────────────────────────────────────
# Énumérations
# ─────────────────────────────────────────────────────────────────────────────

class MatchState(str, Enum):
    """État d'un match MySportU."""
    NON_JOUE = "non_joue"
    TERMINE = "termine"
    REPORTE = "reporte"
    ANNULE = "annule"
    FORFAIT = "forfait"

    @classmethod
    def from_api(cls, etat: str | None, forfait: Any | None = None) -> "MatchState":
        """Convertit les champs API en état."""
        if forfait is not None:
            return cls.FORFAIT
        mapping = {"T": cls.TERMINE, "R": cls.REPORTE, "N": cls.ANNULE}
        return mapping.get(etat, cls.NON_JOUE)  # type: ignore[arg-type]

    @property
    def label(self) -> str:
        labels = {
            "non_joue": "Non joué",
            "termine": "Terminé",
            "reporte": "Reporté",
            "annule": "Annulé",
            "forfait": "Forfait",
        }
        return labels.get(self.value, self.value)

    @property
    def is_cancelled(self) -> bool:
        return self in (MatchState.REPORTE, MatchState.ANNULE, MatchState.FORFAIT)

    @property
    def icon(self) -> str:
        icons = {
            "non_joue": "⏳",
            "termine": "✅",
            "reporte": "🔄",
            "annule": "❌",
            "forfait": "🚫",
        }
        return icons.get(self.value, "❓")


class Genre(str, Enum):
    MASCULIN = "M"
    FEMININ = "F"


# ─────────────────────────────────────────────────────────────────────────────
# Modèles de données
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Competition:
    """Compétition MySportU."""
    id: int
    libelle: str
    sport: str = ""          # Déduit du libellé (VB, HB, BB, FB, ...)
    genre: str = ""          # M ou F, déduit du libellé
    championship: str = ""   # PH1, PH2, CFU, CFE, ...

    @classmethod
    def from_api(cls, data: dict) -> "Competition":
        libelle = data.get("libelle", "")
        sport = _detect_sport(libelle)
        genre = _detect_genre(libelle)
        championship = _detect_championship(libelle)
        return cls(
            id=data.get("id", 0),
            libelle=libelle,
            sport=sport,
            genre=genre,
            championship=championship,
        )

    def to_dict(self) -> dict:
        return {"id": self.id, "libelle": self.libelle, "sport": self.sport,
                "genre": self.genre, "championship": self.championship}

    @classmethod
    def from_dict(cls, d: dict) -> "Competition":
        return cls(**d)


@dataclass(frozen=True)
class LieuPratique:
    """Lieu de pratique (gymnase / salle)."""
    libelle: str
    id: int | None = None
    adresse: str = ""
    ville: str = ""

    @classmethod
    def from_api(cls, data: dict | str | None) -> Optional["LieuPratique"]:
        if data is None:
            return None
        if isinstance(data, str):
            return cls(libelle=data)
        return cls(
            id=data.get("id"),
            libelle=data.get("libelle", "Inconnu"),
            adresse=data.get("adresse", ""),
            ville=data.get("ville", ""),
        )

    def to_dict(self) -> dict:
        return {"id": self.id, "libelle": self.libelle,
                "adresse": self.adresse, "ville": self.ville}

    @classmethod
    def from_dict(cls, d: dict) -> "LieuPratique":
        return cls(**d)


@dataclass(frozen=True)
class Equipe:
    """Équipe dans un match MySportU."""
    id: int
    libelle: str
    libelle_court: str
    club_code: str = ""
    club_nom: str = ""

    @classmethod
    def from_api(cls, data: dict) -> "Equipe":
        club = data.get("club", {}) or {}
        return cls(
            id=data.get("id", 0),
            libelle=data.get("libelle", ""),
            libelle_court=data.get("libelle_court", ""),
            club_code=club.get("code", ""),
            club_nom=club.get("nom", ""),
        )

    def to_dict(self) -> dict:
        return {"id": self.id, "libelle": self.libelle,
                "libelle_court": self.libelle_court,
                "club_code": self.club_code, "club_nom": self.club_nom}

    @classmethod
    def from_dict(cls, d: dict) -> "Equipe":
        return cls(**d)


@dataclass(frozen=True)
class Score:
    """Score d'un match."""
    receveur: int
    visiteur: int

    @classmethod
    def from_api(cls, scores: list[dict], receveur_id: int, visiteur_id: int) -> Optional["Score"]:
        if not scores or len(scores) < 2:
            return None
        score_map: dict[int, int] = {}
        for s in scores:
            eid = s.get("equipe_id")
            val = s.get("score")
            if eid is not None and val is not None:
                score_map[eid] = int(val)
        if receveur_id in score_map and visiteur_id in score_map:
            return cls(receveur=score_map[receveur_id], visiteur=score_map[visiteur_id])
        return None

    def __str__(self) -> str:
        return f"{self.receveur}-{self.visiteur}"

    def reversed(self) -> "Score":
        return Score(receveur=self.visiteur, visiteur=self.receveur)

    def to_dict(self) -> dict:
        return {"receveur": self.receveur, "visiteur": self.visiteur}

    @classmethod
    def from_dict(cls, d: dict) -> "Score":
        return cls(**d)


@dataclass(frozen=True)
class MatchInfo:
    """
    Match MySportU (vue liste — données depuis /rencontres).

    Contient les informations principales d'un match sans les détails
    (joueurs, arbitres, validations).
    """
    id: int
    competition_libelle: str
    sport: str
    genre: str
    championship: str
    date_rencontre: str               # "dd/mm/yyyy HH:MM"
    date: str                         # "dd/mm/yyyy"
    heure: str                        # "HH:MM"
    receveur: Equipe
    visiteur: Equipe
    lieu: LieuPratique | None
    poule: str
    tour: int | None
    state: MatchState
    score: Score | None
    clos: bool

    @classmethod
    def from_api(cls, data: dict) -> "MatchInfo":
        infos = data.get("infosRencontre", {})
        rec_data = data.get("receveur", {})
        vis_data = data.get("visiteur", {})
        receveur = Equipe.from_api(rec_data)
        visiteur = Equipe.from_api(vis_data)

        # Date
        date_rencontre = infos.get("date_rencontre", "")
        parts = date_rencontre.split(" ") if date_rencontre else []
        date_str = parts[0] if parts else ""
        heure_str = parts[1] if len(parts) > 1 else ""

        # Lieu
        lieu_raw = infos.get("lieu_pratique") or infos.get("lieu")
        lieu = LieuPratique.from_api(lieu_raw)

        # Poule
        poule_data = data.get("poule", {}) or {}
        poule = poule_data.get("libelle", "") if isinstance(poule_data, dict) else ""

        # Compétition
        comp_libelle = infos.get("competition_libelle", "")
        sport = _detect_sport(comp_libelle)
        genre = _detect_genre(comp_libelle)
        championship = _detect_championship(comp_libelle)

        # État
        state = MatchState.from_api(data.get("etat"), data.get("forfait"))

        # Score
        score = None
        if state == MatchState.TERMINE:
            score = Score.from_api(
                data.get("score", []),
                receveur.id,
                visiteur.id,
            )

        return cls(
            id=data.get("id", 0),
            competition_libelle=comp_libelle,
            sport=sport,
            genre=genre,
            championship=championship,
            date_rencontre=date_rencontre,
            date=date_str,
            heure=heure_str,
            receveur=receveur,
            visiteur=visiteur,
            lieu=lieu,
            poule=poule,
            tour=data.get("tour"),
            state=state,
            score=score,
            clos=bool(data.get("clos")),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "competition_libelle": self.competition_libelle,
            "sport": self.sport, "genre": self.genre,
            "championship": self.championship,
            "date_rencontre": self.date_rencontre,
            "date": self.date, "heure": self.heure,
            "receveur": self.receveur.to_dict(),
            "visiteur": self.visiteur.to_dict(),
            "lieu": self.lieu.to_dict() if self.lieu else None,
            "poule": self.poule,
            "tour": self.tour,
            "state": self.state.value,
            "score": self.score.to_dict() if self.score else None,
            "clos": self.clos,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "MatchInfo":
        return cls(
            id=d["id"],
            competition_libelle=d["competition_libelle"],
            sport=d["sport"], genre=d["genre"],
            championship=d["championship"],
            date_rencontre=d["date_rencontre"],
            date=d["date"], heure=d["heure"],
            receveur=Equipe.from_dict(d["receveur"]),
            visiteur=Equipe.from_dict(d["visiteur"]),
            lieu=LieuPratique.from_dict(d["lieu"]) if d.get("lieu") else None,
            poule=d.get("poule", ""),
            tour=d.get("tour"),
            state=MatchState(d["state"]),
            score=Score.from_dict(d["score"]) if d.get("score") else None,
            clos=d.get("clos", False),
        )


@dataclass(frozen=True)
class Participant:
    """Joueur ou staff inscrit à un match."""
    id: int
    nom: str
    prenom: str
    equipe_id: int
    role: str = "joueur"        # joueur | staff
    numero: int | None = None
    titulaire: bool = False
    selectionne: bool = False
    fonction: str = ""          # Pour les staffs (coach, manager, ...)

    @property
    def nom_complet(self) -> str:
        return f"{self.prenom} {self.nom}".strip()

    @classmethod
    def from_api(cls, data: dict, role: str = "joueur") -> "Participant":
        return cls(
            id=data.get("id", 0),
            nom=data.get("nom", ""),
            prenom=data.get("prenom", ""),
            equipe_id=data.get("equipe_id", 0),
            role=role,
            numero=data.get("numero"),
            titulaire=bool(data.get("titulaire")),
            selectionne=bool(data.get("selectionne")),
            fonction=data.get("fonction", ""),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id, "nom": self.nom, "prenom": self.prenom,
            "equipe_id": self.equipe_id, "role": self.role,
            "numero": self.numero, "titulaire": self.titulaire,
            "selectionne": self.selectionne, "fonction": self.fonction,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Participant":
        return cls(**d)


@dataclass(frozen=True)
class Officiel:
    """Officiel (arbitre) assigné à un match."""
    id: int
    nom: str
    prenom: str
    est_present: bool = False

    @property
    def nom_complet(self) -> str:
        return f"{self.prenom} {self.nom}".strip()

    @classmethod
    def from_api(cls, data: dict) -> "Officiel":
        return cls(
            id=data.get("id", 0),
            nom=data.get("nom", data.get("nom_complet", "")),
            prenom=data.get("prenom", ""),
            est_present=bool(data.get("est_present")),
        )

    def to_dict(self) -> dict:
        return {"id": self.id, "nom": self.nom, "prenom": self.prenom,
                "est_present": self.est_present}

    @classmethod
    def from_dict(cls, d: dict) -> "Officiel":
        return cls(**d)


@dataclass(frozen=True)
class ValidationEquipe:
    """État de validation d'une équipe pour un match."""
    equipe_id: int
    joueurs_valide: bool = False
    staffs_valide: bool = False
    nb_joueurs: int = 0
    nb_staffs: int = 0

    @classmethod
    def from_api(cls, data: dict) -> "ValidationEquipe":
        return cls(
            equipe_id=data.get("equipe_id", 0),
            joueurs_valide=bool(data.get("joueurs_valide")),
            staffs_valide=bool(data.get("staffs_valide")),
            nb_joueurs=data.get("nb_joueurs", 0) or 0,
            nb_staffs=data.get("nb_staffs", 0) or 0,
        )

    def to_dict(self) -> dict:
        return {"equipe_id": self.equipe_id, "joueurs_valide": self.joueurs_valide,
                "staffs_valide": self.staffs_valide,
                "nb_joueurs": self.nb_joueurs, "nb_staffs": self.nb_staffs}

    @classmethod
    def from_dict(cls, d: dict) -> "ValidationEquipe":
        return cls(**d)


@dataclass(frozen=True)
class Regles:
    """Règles d'un match (nombre de joueurs min/max, etc.)."""
    nb_joueurs_min: int = 6
    nb_joueurs_max: int = 14
    nb_titulaires: int = 6
    nb_staffs_min: int = 0

    @classmethod
    def from_api(cls, data: dict) -> "Regles":
        return cls(
            nb_joueurs_min=int(data.get("nombre_joueurs_min", 6) or 6),
            nb_joueurs_max=int(data.get("nombre_joueurs_max", 14) or 14),
            nb_titulaires=int(data.get("nombre_titulaires", 6) or 6),
            nb_staffs_min=int(data.get("nombre_staffs_min", 0) or 0),
        )

    def to_dict(self) -> dict:
        return {"nb_joueurs_min": self.nb_joueurs_min,
                "nb_joueurs_max": self.nb_joueurs_max,
                "nb_titulaires": self.nb_titulaires,
                "nb_staffs_min": self.nb_staffs_min}

    @classmethod
    def from_dict(cls, d: dict) -> "Regles":
        return cls(**d)


@dataclass
class MatchDetail:
    """
    Détails complets d'un match (données depuis /rencontre/{id} + /participants).

    Inclut joueurs, staff, officiels et état de validation.
    """
    id: int
    receveur: Equipe
    visiteur: Equipe
    state: MatchState
    score: Score | None
    regles: Regles
    validations: list[ValidationEquipe] = field(default_factory=list)
    joueurs: list[Participant] = field(default_factory=list)
    staffs: list[Participant] = field(default_factory=list)
    officiels: list[Officiel] = field(default_factory=list)

    @property
    def is_ready(self) -> bool:
        """Vérifie si le match est prêt à être joué."""
        for val in self.validations:
            if not val.joueurs_valide or val.nb_joueurs < self.regles.nb_joueurs_min:
                return False
        return len(self.officiels) > 0

    @property
    def joueurs_receveur(self) -> list[Participant]:
        return [j for j in self.joueurs if j.equipe_id == self.receveur.id]

    @property
    def joueurs_visiteur(self) -> list[Participant]:
        return [j for j in self.joueurs if j.equipe_id == self.visiteur.id]

    @property
    def staffs_receveur(self) -> list[Participant]:
        return [s for s in self.staffs if s.equipe_id == self.receveur.id]

    @property
    def staffs_visiteur(self) -> list[Participant]:
        return [s for s in self.staffs if s.equipe_id == self.visiteur.id]

    @classmethod
    def from_api(cls, rencontre: dict, participants: dict | None = None) -> "MatchDetail":
        rec = Equipe.from_api(rencontre.get("receveur", {}))
        vis = Equipe.from_api(rencontre.get("visiteur", {}))
        state = MatchState.from_api(rencontre.get("etat"), rencontre.get("forfait"))
        score = None
        if state == MatchState.TERMINE:
            score = Score.from_api(rencontre.get("score", []), rec.id, vis.id)

        regles = Regles.from_api(rencontre.get("regles", {}))
        validations = [ValidationEquipe.from_api(v) for v in rencontre.get("validations", [])]

        joueurs: list[Participant] = []
        staffs: list[Participant] = []
        if participants:
            joueurs = [Participant.from_api(j, "joueur") for j in participants.get("joueurs", [])]
            staffs = [Participant.from_api(s, "staff") for s in participants.get("staffs", [])]

        officiels = [Officiel.from_api(o) for o in rencontre.get("officiels", [])]

        return cls(
            id=rencontre.get("id", 0),
            receveur=rec, visiteur=vis,
            state=state, score=score,
            regles=regles, validations=validations,
            joueurs=joueurs, staffs=staffs,
            officiels=officiels,
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "receveur": self.receveur.to_dict(),
            "visiteur": self.visiteur.to_dict(),
            "state": self.state.value,
            "score": self.score.to_dict() if self.score else None,
            "regles": self.regles.to_dict(),
            "validations": [v.to_dict() for v in self.validations],
            "joueurs": [j.to_dict() for j in self.joueurs],
            "staffs": [s.to_dict() for s in self.staffs],
            "officiels": [o.to_dict() for o in self.officiels],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "MatchDetail":
        return cls(
            id=d["id"],
            receveur=Equipe.from_dict(d["receveur"]),
            visiteur=Equipe.from_dict(d["visiteur"]),
            state=MatchState(d["state"]),
            score=Score.from_dict(d["score"]) if d.get("score") else None,
            regles=Regles.from_dict(d.get("regles", {})),
            validations=[ValidationEquipe.from_dict(v) for v in d.get("validations", [])],
            joueurs=[Participant.from_dict(j) for j in d.get("joueurs", [])],
            staffs=[Participant.from_dict(s) for s in d.get("staffs", [])],
            officiels=[Officiel.from_dict(o) for o in d.get("officiels", [])],
        )


# ─────────────────────────────────────────────────────────────────────────────
# Helpers internes
# ─────────────────────────────────────────────────────────────────────────────

_SPORT_PATTERNS: dict[str, list[str]] = {
    "VB": ["VB", "VOLLEY"],
    "HB": ["HB", "HAND"],
    "BB": ["BB", "BASKET"],
    "FB": ["FB", "FOOT"],
    "RG": ["RG", "RUGBY"],
    "BD": ["BD", "BADMINTON"],
    "TT": ["TT", "TENNIS DE TABLE"],
}


def _detect_sport(libelle: str) -> str:
    upper = libelle.upper()
    for code, patterns in _SPORT_PATTERNS.items():
        if any(p in upper for p in patterns):
            return code
    return ""


def _detect_genre(libelle: str) -> str:
    upper = libelle.upper()
    # VBF, HBF, etc. or "FÉMININ" / "MASCULIN"
    if re.search(r"VBF|HBF|BBF|FBF|FEMININ|FÉMININ", upper):
        return "F"
    if re.search(r"VBM|HBM|BBM|FBM|MASCULIN", upper):
        return "M"
    return ""


def _detect_championship(libelle: str) -> str:
    upper = libelle.upper()
    for pattern in ("PH1", "PH2", "PH3", "CFU", "CFE"):
        if pattern in upper:
            return pattern
    return ""
