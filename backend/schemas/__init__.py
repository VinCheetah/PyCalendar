"""
Pydantic Schemas Package

Centralized imports for all API schemas.
Pattern: Base/Create/Update/Response for CRUD operations.
"""

from backend.schemas.match import (
    MatchBase,
    MatchCreate,
    MatchUpdate,
    MatchResponse,
    MatchMove,
)

from backend.schemas.project import (
    ProjectBase,
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectStats,
)

from backend.schemas.team import (
    TeamBase,
    TeamCreate,
    TeamUpdate,
    TeamResponse,
)

from backend.schemas.venue import (
    VenueBase,
    VenueCreate,
    VenueUpdate,
    VenueResponse,
)

__all__ = [
    # Match schemas
    "MatchBase",
    "MatchCreate",
    "MatchUpdate",
    "MatchResponse",
    "MatchMove",
    # Project schemas
    "ProjectBase",
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectResponse",
    "ProjectStats",
    # Team schemas
    "TeamBase",
    "TeamCreate",
    "TeamUpdate",
    "TeamResponse",
    # Venue schemas
    "VenueBase",
    "VenueCreate",
    "VenueUpdate",
    "VenueResponse",
]
