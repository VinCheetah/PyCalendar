"""
Pydantic Schemas for Match Entity

These schemas handle validation and serialization for Match-related API operations.
Pattern: Base (common fields) → Create/Update (operation-specific) → Response (ORM conversion)
"""

from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class MatchBase(BaseModel):
    """
    Base schema with common fields for Match.
    
    Fields match SQLAlchemy model exactly, with same default values.
    Team data is denormalized (no FK to Team) for query simplification.
    """
    # Équipes (dénormalisées - depuis modèle DB)
    equipe1_nom: str
    equipe1_institution: Optional[str] = None
    equipe1_genre: Optional[str] = None
    
    equipe2_nom: str
    equipe2_institution: Optional[str] = None
    equipe2_genre: Optional[str] = None
    
    # Poule
    poule: Optional[str] = None
    
    # Créneau (optionnel si non planifié)
    semaine: Optional[int] = None
    horaire: Optional[str] = None
    gymnase: Optional[str] = None
    
    # État (valeurs par défaut identiques au model DB)
    est_fixe: bool = False
    statut: str = "a_planifier"
    priorite: int = 0


class MatchCreate(MatchBase):
    """
    Schema for creating a new match.
    
    Adds project_id to link match to a project.
    """
    project_id: int  # Référence au projet


class MatchUpdate(BaseModel):
    """
    Schema for partial match updates (PATCH).
    
    All fields are optional to support partial updates.
    Use model_dump(exclude_unset=True) to get only changed fields.
    """
    # Tous champs optionnels pour updates partiels
    semaine: Optional[int] = None
    horaire: Optional[str] = None
    gymnase: Optional[str] = None
    est_fixe: Optional[bool] = None
    statut: Optional[str] = None
    priorite: Optional[int] = None
    score_equipe1: Optional[int] = None
    score_equipe2: Optional[int] = None
    notes: Optional[str] = None


class MatchResponse(BaseModel):
    """
    Schema for match API responses.
    
    Includes all fields plus id, project_id, scores, notes, and timestamps.
    Uses from_attributes=True for automatic ORM → Pydantic conversion.
    
    Note: All fields from MatchBase are redefined here to allow proper ORM conversion
    when database defaults may not be set yet.
    """
    id: int
    project_id: int
    
    # Équipes (dénormalisées)
    equipe1_nom: str
    equipe1_institution: Optional[str] = None
    equipe1_genre: Optional[str] = None
    equipe2_nom: str
    equipe2_institution: Optional[str] = None
    equipe2_genre: Optional[str] = None
    
    # Poule
    poule: Optional[str] = None
    
    # Créneau
    semaine: Optional[int] = None
    horaire: Optional[str] = None
    gymnase: Optional[str] = None
    
    # État (with defaults for ORM conversion)
    est_fixe: bool = False
    statut: str = "a_planifier"
    priorite: int = 0
    
    # Scores et notes (ajoutés Tâche 1.1)
    score_equipe1: Optional[int] = None
    score_equipe2: Optional[int] = None
    notes: Optional[str] = None
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)  # Pour conversion ORM → Pydantic


class MatchMove(BaseModel):
    """
    Schema for drag & drop match rescheduling.
    
    Used by frontend calendar to move matches to new slots.
    All fields are required for a complete move operation.
    """
    semaine: int
    horaire: str
    gymnase: str
