"""
Routes API pour la gestion des matchs.

Endpoints CRUD + actions spécifiques :
- Déplacement (drag & drop sur calendrier)
- Fixation/défixation (verrouillage pour empêcher replanification)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.database.engine import get_db
from backend.database import models
from backend.schemas import match as schemas

router = APIRouter()


@router.get("/", response_model=List[schemas.MatchResponse])
def list_matches(
    project_id: Optional[int] = Query(None, description="Filtrer par projet"),
    db: Session = Depends(get_db)
):
    """Lister tous les matchs, optionnellement filtrés par projet."""
    query = db.query(models.Match)
    
    if project_id is not None:
        query = query.filter(models.Match.project_id == project_id)
    
    matches = query.all()
    return matches


@router.get("/{match_id}", response_model=schemas.MatchResponse)
def get_match(match_id: int, db: Session = Depends(get_db)):
    """Récupérer un match par son ID."""
    match = db.query(models.Match).filter(models.Match.id == match_id).first()
    
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match {match_id} non trouvé"
        )
    
    return match


@router.post("/", response_model=schemas.MatchResponse, status_code=status.HTTP_201_CREATED)
def create_match(match: schemas.MatchCreate, db: Session = Depends(get_db)):
    """Créer un nouveau match."""
    # Vérifier que le projet existe
    project = db.query(models.Project).filter(models.Project.id == match.project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Projet {match.project_id} non trouvé"
        )
    
    # Créer le match
    db_match = models.Match(**match.model_dump())
    db.add(db_match)
    db.commit()
    db.refresh(db_match)
    
    return db_match


@router.put("/{match_id}", response_model=schemas.MatchResponse)
def update_match(
    match_id: int,
    match_update: schemas.MatchUpdate,
    db: Session = Depends(get_db)
):
    """Mettre à jour un match (PATCH partiel)."""
    db_match = db.query(models.Match).filter(models.Match.id == match_id).first()
    
    if not db_match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match {match_id} non trouvé"
        )
    
    # Update partiel (seulement champs fournis)
    update_data = match_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_match, key, value)
    
    db.commit()
    db.refresh(db_match)
    
    return db_match


@router.post("/{match_id}/move", response_model=schemas.MatchResponse)
def move_match(
    match_id: int,
    move_data: schemas.MatchMove,
    db: Session = Depends(get_db)
):
    """
    Déplacer un match vers un nouveau créneau (drag & drop).
    
    Vérifie que le match n'est pas fixé avant de permettre le déplacement.
    """
    db_match = db.query(models.Match).filter(models.Match.id == match_id).first()
    
    if not db_match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match {match_id} non trouvé"
        )
    
    # Vérifier que le match est modifiable (logique métier - Tâche 1.1)
    if not db_match.est_modifiable:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce match est fixé et ne peut pas être déplacé"
        )
    
    # Mettre à jour le créneau
    db_match.semaine = move_data.semaine
    db_match.horaire = move_data.horaire
    db_match.gymnase = move_data.gymnase
    db_match.statut = "planifie"  # Changer statut après déplacement
    
    db.commit()
    db.refresh(db_match)
    
    return db_match


@router.post("/{match_id}/fix")
def fix_match(match_id: int, db: Session = Depends(get_db)):
    """
    Fixer un match (le verrouiller pour empêcher replanification).
    
    Un match fixé ne peut plus être déplacé par le solveur ou en drag & drop,
    sauf s'il est d'abord défixé.
    """
    db_match = db.query(models.Match).filter(models.Match.id == match_id).first()
    
    if not db_match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match {match_id} non trouvé"
        )
    
    # Fixer le match
    db_match.est_fixe = True
    db_match.statut = "fixe"
    
    db.commit()
    db.refresh(db_match)
    
    return {
        "message": "Match fixé avec succès",
        "match": schemas.MatchResponse.model_validate(db_match)
    }


@router.post("/{match_id}/unfix")
def unfix_match(match_id: int, db: Session = Depends(get_db)):
    """
    Défixer un match (le déverrouiller).
    
    Restaure le statut approprié selon l'état du match :
    - "planifie" si le match a déjà un créneau (semaine non null)
    - "a_planifier" sinon
    """
    db_match = db.query(models.Match).filter(models.Match.id == match_id).first()
    
    if not db_match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match {match_id} non trouvé"
        )
    
    # Défixer le match
    db_match.est_fixe = False
    
    # Restaurer statut approprié
    if db_match.semaine is not None:
        db_match.statut = "planifie"  # Match déjà planifié
    else:
        db_match.statut = "a_planifier"  # Match non planifié
    
    db.commit()
    db.refresh(db_match)
    
    return {
        "message": "Match déverrouillé avec succès",
        "match": schemas.MatchResponse.model_validate(db_match)
    }


@router.delete("/{match_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_match(match_id: int, db: Session = Depends(get_db)):
    """Supprimer un match."""
    db_match = db.query(models.Match).filter(models.Match.id == match_id).first()
    
    if not db_match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match {match_id} non trouvé"
        )
    
    db.delete(db_match)
    db.commit()
    
    return None  # 204 No Content
