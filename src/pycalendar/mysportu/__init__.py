"""
MySportU — Module d'intégration avec la plateforme MySportU.

Ce module fournit un accès propre, mis en cache et typé à l'API MySportU.
Il est conçu pour être utilisé facilement par les scripts du projet.

Architecture:
    ┌──────────────────────────────────────────┐
    │             MySportU (facade)            │  ← Point d'entrée unique
    ├──────────────────────────────────────────┤
    │  display.py   │  Affichage Rich          │
    ├───────────────┼──────────────────────────┤
    │  api.py       │  Endpoints haut-niveau   │
    ├───────────────┼──────────────────────────┤
    │  cache.py     │  Cache intelligent        │
    ├───────────────┼──────────────────────────┤
    │  client.py    │  Client HTTP + auth       │
    ├───────────────┼──────────────────────────┤
    │  models.py    │  Modèles de données       │
    └───────────────┴──────────────────────────┘

Usage rapide:
    >>> from pycalendar.mysportu import MySportU
    >>> msu = MySportU()
    >>> matches = msu.get_matches(sport="VB", championship="PH2")
    >>> msu.display_matches(matches)
"""

from .facade import MySportU
from .models import (
    Competition,
    Equipe,
    LieuPratique,
    MatchInfo,
    MatchDetail,
    MatchState,
    Participant,
    Score,
)
from .exceptions import (
    MySportUError,
    AuthenticationError,
    APIError,
    CacheError,
)

__all__ = [
    # Facade
    "MySportU",
    # Modèles
    "Competition",
    "Equipe",
    "LieuPratique",
    "MatchInfo",
    "MatchDetail",
    "MatchState",
    "Participant",
    "Score",
    # Exceptions
    "MySportUError",
    "AuthenticationError",
    "APIError",
    "CacheError",
]
