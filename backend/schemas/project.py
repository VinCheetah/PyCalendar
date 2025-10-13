"""
Pydantic Schemas for Project Entity

These schemas handle validation and serialization for Project-related API operations.
Projects store both YAML configuration (hyperparameters) and reference to Excel data.
"""

from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime


class ProjectBase(BaseModel):
    """
    Base schema with common fields for Project.
    
    Stores paths to configuration files (YAML/Excel) and key planning parameters.
    semaine_min maps to 'semaine_minimum' from YAML config (Tâche 1.2).
    """
    nom: str
    sport: str
    
    # Chemins des fichiers de configuration (optionnels)
    config_yaml_path: Optional[str] = None
    
    # Paramètres planification (depuis YAML)
    nb_semaines: int = 26
    semaine_min: int = 1  # De "semaine_minimum" dans YAML (Tâche 1.2)


class ProjectCreate(ProjectBase):
    """
    Schema for creating a new project.
    
    Optionally stores complete configuration data as JSON.
    This allows preserving full YAML config for traceability.
    """
    # Données complètes optionnelles (JSON)
    config_data: Optional[Dict[str, Any]] = None  # Stockage config YAML complète en JSON


class ProjectUpdate(BaseModel):
    """
    Schema for partial project updates (PATCH).
    
    All fields are optional to support partial updates.
    """
    # Tous champs optionnels pour updates partiels
    nom: Optional[str] = None
    sport: Optional[str] = None
    config_yaml_path: Optional[str] = None
    config_data: Optional[Dict[str, Any]] = None
    nb_semaines: Optional[int] = None
    semaine_min: Optional[int] = None


class ProjectResponse(BaseModel):
    """
    Schema for project API responses.
    
    Includes all fields plus id, config_data, and timestamps.
    Uses from_attributes=True for automatic ORM → Pydantic conversion.
    
    Note: All fields redefined to ensure proper ORM conversion with defaults.
    """
    id: int
    nom: str
    sport: str
    
    # Configuration
    config_yaml_path: Optional[str] = None
    config_data: Optional[Dict[str, Any]] = None
    
    # Paramètres planification
    nb_semaines: int = 26
    semaine_min: int = 1
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ProjectStats(BaseModel):
    """
    Schema for project statistics.
    
    Used by dashboard/overview endpoints to display project status.
    Calculated from related matches, teams, and venues.
    """
    nb_matchs_total: int
    nb_matchs_planifies: int
    nb_matchs_fixes: int
    nb_matchs_a_planifier: int
    nb_equipes: int
    nb_gymnases: int
