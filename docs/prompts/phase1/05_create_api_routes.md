# PROMPT 1.5 : Créer Routes FastAPI pour CRUD + Opérations Spéciales

## Contexte Projet

**PyCalendar V2** : API REST FastAPI pour gestion calendriers. Routes = endpoints HTTP (GET, POST, PUT, DELETE).

## État Actuel

- ✅ Database models + Schemas Pydantic
- ⏳ Créer application FastAPI avec routes CRUD

## Objectif

Créer API REST avec :
- **App FastAPI** avec CORS
- **Routes Matches** : CRUD + move/fix/unfix
- **Routes Projects, Teams, Venues** : CRUD standard

**Durée** : 2h

## Instructions

### 1. Structure

```bash
mkdir -p backend/api backend/api/routes
touch backend/api/__init__.py
touch backend/api/main.py
touch backend/api/dependencies.py
touch backend/api/routes/__init__.py
touch backend/api/routes/matches.py
touch backend/api/routes/projects.py
touch backend/api/routes/teams.py
touch backend/api/routes/venues.py
```

### 2. Application FastAPI

**Fichier** : `backend/api/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="PyCalendar API",
    version="2.0.0",
    description="API REST pour gestion calendriers sportifs"
)

# CORS pour dev (frontend localhost:5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"name": "PyCalendar API", "version": "2.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

# Import routes
from .routes import matches, projects, teams, venues

app.include_router(matches.router, prefix="/api/matches", tags=["Matches"])
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(teams.router, prefix="/api/teams", tags=["Teams"])
app.include_router(venues.router, prefix="/api/venues", tags=["Venues"])
```

### 3. Dependencies

**Fichier** : `backend/api/dependencies.py`

```python
from backend.database.engine import get_db

# Réexporter pour simplicité
__all__ = ["get_db"]
```

### 4. Routes Matches (COMPLET)

**Fichier** : `backend/api/routes/matches.py`

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.database import models
from backend.schemas import match as schemas
from backend.api.dependencies import get_db

router = APIRouter()

@router.get("/", response_model=List[schemas.MatchResponse])
def list_matches(
    project_id: Optional[int] = Query(None),
    poule: Optional[str] = Query(None),
    statut: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Lister matchs avec filtres optionnels."""
    query = db.query(models.Match)
    
    if project_id:
        query = query.filter(models.Match.project_id == project_id)
    if poule:
        query = query.filter(models.Match.poule == poule)
    if statut:
        query = query.filter(models.Match.statut == statut)
    
    return query.all()

@router.get("/{match_id}", response_model=schemas.MatchResponse)
def get_match(match_id: int, db: Session = Depends(get_db)):
    """Récupérer un match par ID."""
    match = db.query(models.Match).filter(models.Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match non trouvé")
    return match

@router.post("/", response_model=schemas.MatchResponse, status_code=201)
def create_match(match: schemas.MatchCreate, db: Session = Depends(get_db)):
    """Créer un nouveau match."""
    db_match = models.Match(**match.dict())
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
    """Mettre à jour un match (partiel)."""
    db_match = db.query(models.Match).filter(models.Match.id == match_id).first()
    if not db_match:
        raise HTTPException(status_code=404, detail="Match non trouvé")
    
    # Update uniquement champs fournis
    update_data = match_update.dict(exclude_unset=True)
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
    """Déplacer un match vers nouveau créneau (drag & drop)."""
    db_match = db.query(models.Match).filter(models.Match.id == match_id).first()
    if not db_match:
        raise HTTPException(status_code=404, detail="Match non trouvé")
    
    # Vérifier modifiable
    if not db_match.est_modifiable:
        raise HTTPException(status_code=400, detail="Match fixé, non modifiable")
    
    # Update créneau
    db_match.semaine = move_data.semaine
    db_match.horaire = move_data.horaire
    db_match.gymnase = move_data.gymnase
    db_match.statut = "planifie"
    
    db.commit()
    db.refresh(db_match)
    return db_match

@router.post("/{match_id}/fix")
def fix_match(match_id: int, db: Session = Depends(get_db)):
    """Fixer un match (verrouiller)."""
    db_match = db.query(models.Match).filter(models.Match.id == match_id).first()
    if not db_match:
        raise HTTPException(status_code=404, detail="Match non trouvé")
    
    db_match.est_fixe = True
    db_match.statut = "fixe"
    
    db.commit()
    return {"message": "Match fixé", "match_id": match_id}

@router.post("/{match_id}/unfix")
def unfix_match(match_id: int, db: Session = Depends(get_db)):
    """Déverrouiller un match fixé."""
    db_match = db.query(models.Match).filter(models.Match.id == match_id).first()
    if not db_match:
        raise HTTPException(status_code=404, detail="Match non trouvé")
    
    db_match.est_fixe = False
    # Restaurer statut selon créneau
    if db_match.est_planifie:
        db_match.statut = "planifie"
    else:
        db_match.statut = "a_planifier"
    
    db.commit()
    return {"message": "Match déverrouillé", "match_id": match_id}

@router.delete("/{match_id}", status_code=204)
def delete_match(match_id: int, db: Session = Depends(get_db)):
    """Supprimer un match."""
    db_match = db.query(models.Match).filter(models.Match.id == match_id).first()
    if not db_match:
        raise HTTPException(status_code=404, detail="Match non trouvé")
    
    db.delete(db_match)
    db.commit()
```

### 5. Routes Projects (Pattern CRUD simple)

**Fichier** : `backend/api/routes/projects.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.database import models
from backend.schemas import project as schemas
from backend.api.dependencies import get_db

router = APIRouter()

@router.get("/", response_model=List[schemas.ProjectResponse])
def list_projects(db: Session = Depends(get_db)):
    return db.query(models.Project).all()

@router.get("/{project_id}", response_model=schemas.ProjectResponse)
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    return project

@router.post("/", response_model=schemas.ProjectResponse, status_code=201)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    db_project = models.Project(**project.dict())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@router.put("/{project_id}", response_model=schemas.ProjectResponse)
def update_project(project_id: int, project_update: schemas.ProjectUpdate, db: Session = Depends(get_db)):
    db_project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    update_data = project_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_project, key, value)
    
    db.commit()
    db.refresh(db_project)
    return db_project

@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    db_project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    db.delete(db_project)
    db.commit()
```

### 6. Routes Teams et Venues

Dupliquer pattern `projects.py` en remplaçant :
- Model : `models.Team` / `models.Venue`
- Schema : `schemas.Team*` / `schemas.Venue*`
- Messages erreur

## Validation

### 1. Lancer API

```bash
uvicorn backend.api.main:app --reload
```

### 2. Tester Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Swagger UI
# Ouvrir http://localhost:8000/docs

# Créer projet
curl -X POST http://localhost:8000/api/projects/ \
  -H "Content-Type: application/json" \
  -d '{"nom":"Test","sport":"volleyball","nb_semaines":10}'

# Lister projets
curl http://localhost:8000/api/projects/

# Lister matchs
curl http://localhost:8000/api/matches/?project_id=1
```

## Critères de Réussite

- [ ] API démarre sur port 8000
- [ ] Swagger UI accessible à /docs
- [ ] Endpoint /health retourne 200
- [ ] Routes matches : GET list, GET detail, POST, PUT, DELETE, POST move/fix/unfix
- [ ] Routes projects/teams/venues : CRUD complet
- [ ] CORS configuré pour localhost:5173

## Prochaine Étape

➡️ **Prompt 1.6** : Créer service synchronisation Excel → DB
