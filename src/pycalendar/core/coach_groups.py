"""Helpers for parsing Coach_Groups slot definitions."""

from dataclasses import dataclass
from typing import Literal, Optional

COACH_GROUP_SLOT_COLUMNS = [f"slot_{i:02d}" for i in range(1, 21)]


class CoachSlotParseError(ValueError):
    """Raised when a slot definition cannot be parsed."""


@dataclass
class CoachSlotSpec:
    """Structured representation of a Coach_Groups slot."""

    kind: Literal["team", "institution"]
    identifier: str
    gender: Optional[str] = None
    raw: str = ""


def parse_coach_slot(raw_value) -> CoachSlotSpec:
    """Parse a raw slot value into a structured spec.

    Accepted forms (case-insensitive keys):
        - "team=LYON 1 (1)" (optional ;gender=F)
        - "institution=LYON" (optional ;gender=M)
        - Plain team value without key (fallback to team)
    """

    text = "" if raw_value is None else str(raw_value).strip()
    if not text:
        raise CoachSlotParseError("slot vide")

    tokens = [token.strip() for token in text.split(';') if token.strip()]
    if not tokens:
        raise CoachSlotParseError("slot vide")

    data = {}
    for token in tokens:
        if '=' not in token:
            if 'team' in data or 'institution' in data:
                raise CoachSlotParseError("multiples cibles détectées dans le même slot")
            data['team'] = token
            continue
        key, value = token.split('=', 1)
        key = key.strip().lower()
        value = value.strip()
        if not key:
            raise CoachSlotParseError(f"clé vide dans '{token}'")
        if key in ('team', 'institution', 'gender', 'genre'):
            if not value:
                raise CoachSlotParseError(f"valeur vide pour '{key}'")
            data[key] = value
        else:
            raise CoachSlotParseError(f"clé '{key}' inconnue")

    if 'team' in data and 'institution' in data:
        raise CoachSlotParseError("un slot ne peut pas cibler à la fois une équipe et une institution")

    gender_raw = data.get('gender') or data.get('genre')
    gender = gender_raw.upper() if gender_raw else None

    if 'team' in data:
        identifier = data['team']
        if not identifier:
            raise CoachSlotParseError("équipe vide")
        return CoachSlotSpec(kind='team', identifier=identifier.strip(), gender=gender, raw=text)

    if 'institution' in data:
        identifier = data['institution']
        if not identifier:
            raise CoachSlotParseError("institution vide")
        return CoachSlotSpec(kind='institution', identifier=identifier.strip(), gender=gender, raw=text)

    # Fallback: treat first token as team name
    identifier = tokens[0]
    return CoachSlotSpec(kind='team', identifier=identifier.strip(), gender=gender, raw=text)
