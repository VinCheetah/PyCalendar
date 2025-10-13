# PROMPT 1.4 : Créer Schemas Pydantic pour Validation API

## Contexte Projet

**PyCalendar V2** : Web app avec FastAPI. Schemas Pydantic = validation/sérialisation données API.

## État Actuel

- ✅ Database models SQLAlchemy créés (Project, Team, Venue, Match)
- ⏳ Créer schemas Pydantic pour endpoints API

## Objectif

Créer schemas pour validation entrées/sorties API :
- **MatchBase** : Champs communs
- **MatchCreate** : Création match
- **MatchUpdate** : Update partiel
- **MatchResponse** : Réponse API (avec ID, timestamps)
- **MatchMove** : Déplacement drag & drop
- Idem pour Project, Team, Venue

**Durée** : 45 min

## Instructions

### 1. Structure Dossiers

```bash
mkdir -p backend/schemas
touch backend/schemas/__init__.py
touch backend/schemas/match.py
touch backend/schemas/project.py
touch backend/schemas/team.py
touch backend/schemas/venue.py
```

### 2. Schemas Match

**Fichier** : `backend/schemas/match.py`

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class MatchBase(BaseModel):
    """Champs communs match."""
    equipe1_nom: str
    equipe1_institution: str = ""
    equipe1_genre: str = ""
    equipe2_nom: str
    equipe2_institution: str = ""
    equipe2_genre: str = ""
    poule: str
    semaine: Optional[int] = None
    horaire: Optional[str] = None
    gymnase: Optional[str] = None
    est_fixe: bool = False
    statut: str = "a_planifier"
    priorite: int = 0

class MatchCreate(MatchBase):
    """Création match."""
    project_id: int

class MatchUpdate(BaseModel):
    """Update partiel."""
    semaine: Optional[int] = None
    horaire: Optional[str] = None
    gymnase: Optional[str] = None
    est_fixe: Optional[bool] = None
    statut: Optional[str] = None
    score_equipe1: Optional[int] = None
    score_equipe2: Optional[int] = None
    notes: Optional[str] = None

class MatchResponse(MatchBase):
    """Réponse API."""
    id: int
    project_id: int
    score_equipe1: Optional[int] = None
    score_equipe2: Optional[int] = None
    notes: str = ""
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True  # ORM mode

class MatchMove(BaseModel):
    """Déplacement drag & drop."""
    semaine: int = Field(..., ge=1)
    horaire: str = Field(..., pattern=r'^\d{2}:\d{2}$')
    gymnase: str = Field(..., min_length=1)
```

### 3. Schemas Project

**Fichier** : `backend/schemas/project.py`

```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ProjectBase(BaseModel):
    nom: str
    sport: str
    config_yaml_path: Optional[str] = None
    nb_semaines: int = 26
    semaine_min: int = 1

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    nom: Optional[str] = None
    nb_semaines: Optional[int] = None
    semaine_min: Optional[int] = None

class ProjectResponse(ProjectBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
```

### 4. Schemas Team

**Fichier** : `backend/schemas/team.py`

```python
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class TeamBase(BaseModel):
    nom: str
    institution: Optional[str] = None
    numero_equipe: Optional[str] = None
    genre: Optional[str] = None
    poule: str
    horaires_preferes: Optional[List[str]] = None
    lieux_preferes: Optional[List[str]] = None

class TeamCreate(TeamBase):
    project_id: int

class TeamUpdate(BaseModel):
    nom: Optional[str] = None
    poule: Optional[str] = None
    horaires_preferes: Optional[List[str]] = None
    lieux_preferes: Optional[List[str]] = None

class TeamResponse(TeamBase):
    id: int
    project_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
```

### 5. Schemas Venue

**Fichier** : `backend/schemas/venue.py`

```python
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class VenueBase(BaseModel):
    nom: str
    capacite: int = 1
    horaires_disponibles: Optional[List[str]] = None

class VenueCreate(VenueBase):
    project_id: int

class VenueUpdate(BaseModel):
    nom: Optional[str] = None
    capacite: Optional[int] = None
    horaires_disponibles: Optional[List[str]] = None

class VenueResponse(VenueBase):
    id: int
    project_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
```

### 6. __init__.py

**Fichier** : `backend/schemas/__init__.py`

```python
from .match import MatchBase, MatchCreate, MatchUpdate, MatchResponse, MatchMove
from .project import ProjectBase, ProjectCreate, ProjectUpdate, ProjectResponse
from .team import TeamBase, TeamCreate, TeamUpdate, TeamResponse
from .venue import VenueBase, VenueCreate, VenueUpdate, VenueResponse

__all__ = [
    "MatchBase", "MatchCreate", "MatchUpdate", "MatchResponse", "MatchMove",
    "ProjectBase", "ProjectCreate", "ProjectUpdate", "ProjectResponse",
    "TeamBase", "TeamCreate", "TeamUpdate", "TeamResponse",
    "VenueBase", "VenueCreate", "VenueUpdate", "VenueResponse",
]
```

## Validation

```bash
python -c "
from backend.schemas import match, project, team, venue
from backend.schemas.match import MatchResponse
from backend.database import models

# Test conversion ORM → Pydantic
m = models.Match(
    id=1,
    project_id=1,
    equipe1_nom='A',
    equipe2_nom='B',
    poule='P1'
)
response = MatchResponse.from_orm(m)
print(f'✅ Conversion ORM → Pydantic: {response.equipe1_nom} vs {response.equipe2_nom}')
"
```

## Critères de Réussite

- [ ] Dossier `backend/schemas/` créé
- [ ] 4 fichiers schemas (match, project, team, venue)
- [ ] Chaque entité a : Base, Create, Update, Response
- [ ] Match a schema `MatchMove` en plus
- [ ] Config `from_attributes=True` pour ORM
- [ ] Validation Pydantic (Field, pattern, ge) sur MatchMove

## Prochaine Étape

➡️ **Prompt 1.5** : Créer routes FastAPI pour CRUD
