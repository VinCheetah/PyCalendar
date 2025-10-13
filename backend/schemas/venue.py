"""
Pydantic Schemas for Venue Entity

These schemas handle validation and serialization for Venue-related API operations.
Venue data is sourced from Excel sheet "Gymnases" with dynamic time slot columns.
"""

from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime


class VenueBase(BaseModel):
    """
    Base schema with common fields for Venue.
    
    Data sources:
    - nom, capacite: From Excel sheet "Gymnases"
    - horaires_disponibles: Extracted from dynamic time slot columns in Excel
      (e.g., "Mercredi 14:00", "Vendredi 18:00" columns with 1/0 values)
    
    capacite indicates number of simultaneous matches possible at this venue.
    """
    # Informations gymnase (depuis feuille Excel "Gymnases")
    nom: str
    capacite: int = 1  # Nombre de terrains simultanés
    
    # Disponibilités (depuis colonnes horaires du Excel)
    horaires_disponibles: Optional[List[str]] = None


class VenueCreate(VenueBase):
    """
    Schema for creating a new venue.
    
    Adds project_id to link venue to a project.
    """
    project_id: int


class VenueUpdate(BaseModel):
    """
    Schema for partial venue updates (PATCH).
    
    All fields are optional to support partial updates.
    """
    # Tous champs optionnels
    nom: Optional[str] = None
    capacite: Optional[int] = None
    horaires_disponibles: Optional[List[str]] = None


class VenueResponse(BaseModel):
    """
    Schema for venue API responses.
    
    Includes all fields plus id, project_id, and timestamp.
    Uses from_attributes=True for automatic ORM → Pydantic conversion.
    
    Note: All fields redefined to ensure proper ORM conversion.
    """
    id: int
    project_id: int
    
    # Informations gymnase
    nom: str
    capacite: int = 1
    
    # Disponibilités
    horaires_disponibles: Optional[List[str]] = None
    
    # Timestamp
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
