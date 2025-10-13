"""
Routes API pour la gestion des équipes.

Endpoints CRUD avec filtrage optionnel par projet.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.database.engine import get_db
from backend.database import models
from backend.schemas import team as schemas

router = APIRouter()


@router.get("/", response_model=List[schemas.TeamResponse])
def list_teams(
    project_id: Optional[int] = Query(None, description="Filtrer par projet"),
    db: Session = Depends(get_db)
):
    """Lister toutes les équipes, optionnellement filtrées par projet."""
    query = db.query(models.Team)
    
    if project_id is not None:
        query = query.filter(models.Team.project_id == project_id)
    
    return query.all()


@router.get("/{team_id}", response_model=schemas.TeamResponse)
def get_team(team_id: int, db: Session = Depends(get_db)):
    """Récupérer une équipe par ID."""
    team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Équipe {team_id} non trouvée"
        )
    return team


@router.post("/", response_model=schemas.TeamResponse, status_code=status.HTTP_201_CREATED)
def create_team(team: schemas.TeamCreate, db: Session = Depends(get_db)):
    """Créer une nouvelle équipe."""
    # Vérifier que le projet existe
    project = db.query(models.Project).filter(models.Project.id == team.project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Projet {team.project_id} non trouvé"
        )
    
    db_team = models.Team(**team.model_dump())
    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    return db_team


@router.put("/{team_id}", response_model=schemas.TeamResponse)
def update_team(
    team_id: int,
    team_update: schemas.TeamUpdate,
    db: Session = Depends(get_db)
):
    """Mettre à jour une équipe."""
    db_team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if not db_team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Équipe {team_id} non trouvée"
        )
    
    update_data = team_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_team, key, value)
    
    db.commit()
    db.refresh(db_team)
    return db_team


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_team(team_id: int, db: Session = Depends(get_db)):
    """Supprimer une équipe."""
    db_team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if not db_team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Équipe {team_id} non trouvée"
        )
    
    db.delete(db_team)
    db.commit()
    return None
