"""
Routes API pour la gestion des projets.

Endpoints CRUD + statistiques pour le dashboard.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from backend.database.engine import get_db
from backend.database import models
from backend.schemas import project as schemas

router = APIRouter()


@router.get("/", response_model=List[schemas.ProjectResponse])
def list_projects(db: Session = Depends(get_db)):
    """Lister tous les projets."""
    return db.query(models.Project).all()


@router.get("/{project_id}", response_model=schemas.ProjectResponse)
def get_project(project_id: int, db: Session = Depends(get_db)):
    """Récupérer un projet par ID."""
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Projet {project_id} non trouvé"
        )
    return project


@router.post("/", response_model=schemas.ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    """Créer un nouveau projet."""
    db_project = models.Project(**project.model_dump())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


@router.put("/{project_id}", response_model=schemas.ProjectResponse)
def update_project(
    project_id: int,
    project_update: schemas.ProjectUpdate,
    db: Session = Depends(get_db)
):
    """Mettre à jour un projet."""
    db_project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not db_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Projet {project_id} non trouvé"
        )
    
    update_data = project_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_project, key, value)
    
    db.commit()
    db.refresh(db_project)
    return db_project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    """
    Supprimer un projet.
    
    ⚠️ CASCADE DELETE : Supprime également tous les matchs, équipes et gymnases liés.
    """
    db_project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not db_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Projet {project_id} non trouvé"
        )
    
    db.delete(db_project)
    db.commit()
    return None


@router.get("/{project_id}/stats", response_model=schemas.ProjectStats)
def get_project_stats(project_id: int, db: Session = Depends(get_db)):
    """
    Récupérer les statistiques d'un projet pour le dashboard.
    
    Calcule :
    - Nombre total de matchs
    - Nombre de matchs planifiés (avec créneau)
    - Nombre de matchs fixés (verrouillés)
    - Nombre de matchs à planifier
    - Nombre d'équipes
    - Nombre de gymnases
    """
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Projet {project_id} non trouvé"
        )
    
    # Calculer statistiques
    nb_matchs_total = db.query(models.Match).filter(
        models.Match.project_id == project_id
    ).count()
    
    nb_matchs_planifies = db.query(models.Match).filter(
        models.Match.project_id == project_id,
        models.Match.semaine.isnot(None)
    ).count()
    
    nb_matchs_fixes = db.query(models.Match).filter(
        models.Match.project_id == project_id,
        models.Match.est_fixe == True
    ).count()
    
    nb_matchs_a_planifier = nb_matchs_total - nb_matchs_planifies
    
    nb_equipes = db.query(models.Team).filter(
        models.Team.project_id == project_id
    ).count()
    
    nb_gymnases = db.query(models.Venue).filter(
        models.Venue.project_id == project_id
    ).count()
    
    return schemas.ProjectStats(
        nb_matchs_total=nb_matchs_total,
        nb_matchs_planifies=nb_matchs_planifies,
        nb_matchs_fixes=nb_matchs_fixes,
        nb_matchs_a_planifier=nb_matchs_a_planifier,
        nb_equipes=nb_equipes,
        nb_gymnases=nb_gymnases
    )
