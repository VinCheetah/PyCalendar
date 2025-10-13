"""
Routes API pour la gestion des gymnases.

Endpoints CRUD avec filtrage optionnel par projet.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.database.engine import get_db
from backend.database import models
from backend.schemas import venue as schemas

router = APIRouter()


@router.get("/", response_model=List[schemas.VenueResponse])
def list_venues(
    project_id: Optional[int] = Query(None, description="Filtrer par projet"),
    db: Session = Depends(get_db)
):
    """Lister tous les gymnases, optionnellement filtrés par projet."""
    query = db.query(models.Venue)
    
    if project_id is not None:
        query = query.filter(models.Venue.project_id == project_id)
    
    return query.all()


@router.get("/{venue_id}", response_model=schemas.VenueResponse)
def get_venue(venue_id: int, db: Session = Depends(get_db)):
    """Récupérer un gymnase par ID."""
    venue = db.query(models.Venue).filter(models.Venue.id == venue_id).first()
    if not venue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gymnase {venue_id} non trouvé"
        )
    return venue


@router.post("/", response_model=schemas.VenueResponse, status_code=status.HTTP_201_CREATED)
def create_venue(venue: schemas.VenueCreate, db: Session = Depends(get_db)):
    """Créer un nouveau gymnase."""
    # Vérifier que le projet existe
    project = db.query(models.Project).filter(models.Project.id == venue.project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Projet {venue.project_id} non trouvé"
        )
    
    db_venue = models.Venue(**venue.model_dump())
    db.add(db_venue)
    db.commit()
    db.refresh(db_venue)
    return db_venue


@router.put("/{venue_id}", response_model=schemas.VenueResponse)
def update_venue(
    venue_id: int,
    venue_update: schemas.VenueUpdate,
    db: Session = Depends(get_db)
):
    """Mettre à jour un gymnase."""
    db_venue = db.query(models.Venue).filter(models.Venue.id == venue_id).first()
    if not db_venue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gymnase {venue_id} non trouvé"
        )
    
    update_data = venue_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_venue, key, value)
    
    db.commit()
    db.refresh(db_venue)
    return db_venue


@router.delete("/{venue_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_venue(venue_id: int, db: Session = Depends(get_db)):
    """Supprimer un gymnase."""
    db_venue = db.query(models.Venue).filter(models.Venue.id == venue_id).first()
    if not db_venue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gymnase {venue_id} non trouvé"
        )
    
    db.delete(db_venue)
    db.commit()
    return None
