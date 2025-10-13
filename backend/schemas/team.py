"""
Pydantic Schemas for Team Entity

These schemas handle validation and serialization for Team-related API operations.
Team data is sourced from Excel sheets (Equipes, Preferences_Gymnases).
"""

from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime


class TeamBase(BaseModel):
    """
    Base schema with common fields for Team.
    
    Data sources:
    - nom, poule: From Excel sheet "Equipes"
    - institution, numero_equipe, genre: Extracted from team name
    - horaires_preferes: From Excel column "Horaire_Prefere"
    - lieux_preferes: From Excel sheet "Preferences_Gymnases" (by institution)
    """
    # Informations équipe (depuis feuille Excel "Equipes")
    nom: str
    institution: Optional[str] = None
    numero_equipe: Optional[str] = None
    genre: Optional[str] = None
    poule: Optional[str] = None
    
    # Préférences (depuis Excel ou calculées)
    horaires_preferes: Optional[List[Optional[str]]] = None  # Depuis "Horaire_Prefere"
    lieux_preferes: Optional[List[Optional[str]]] = None     # Depuis feuille "Preferences_Gymnases"


class TeamCreate(TeamBase):
    """
    Schema for creating a new team.
    
    Adds project_id to link team to a project.
    """
    project_id: int


class TeamUpdate(BaseModel):
    """
    Schema for partial team updates (PATCH).
    
    All fields are optional to support partial updates.
    """
    # Tous champs optionnels
    nom: Optional[str] = None
    institution: Optional[str] = None
    numero_equipe: Optional[str] = None
    genre: Optional[str] = None
    poule: Optional[str] = None
    horaires_preferes: Optional[List[Optional[str]]] = None
    lieux_preferes: Optional[List[Optional[str]]] = None


class TeamResponse(BaseModel):
    """
    Schema for team API responses.
    
    Includes all fields plus id, project_id, and timestamp.
    Uses from_attributes=True for automatic ORM → Pydantic conversion.
    
    Note: All fields redefined to ensure proper ORM conversion.
    """
    id: int
    project_id: int
    
    # Informations équipe
    nom: str
    institution: Optional[str] = None
    numero_equipe: Optional[str] = None
    genre: Optional[str] = None
    poule: Optional[str] = None
    
    # Préférences
    horaires_preferes: Optional[List[Optional[str]]] = None
    lieux_preferes: Optional[List[Optional[str]]] = None
    
    # Timestamp
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
