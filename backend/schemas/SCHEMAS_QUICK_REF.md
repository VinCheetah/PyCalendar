# 🚀 Pydantic Schemas - Quick Reference

## 📦 Import

```python
# Import all schemas
from backend.schemas import (
    # Match
    MatchBase, MatchCreate, MatchUpdate, MatchResponse, MatchMove,
    # Project
    ProjectBase, ProjectCreate, ProjectUpdate, ProjectResponse, ProjectStats,
    # Team
    TeamBase, TeamCreate, TeamUpdate, TeamResponse,
    # Venue
    VenueBase, VenueCreate, VenueUpdate, VenueResponse
)
```

## 🎯 Common Patterns

### 1️⃣ Create Resource (POST)
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database.engine import get_db
from backend.database.models import Match
from backend.schemas import MatchCreate, MatchResponse

router = APIRouter()

@router.post("/matches/", response_model=MatchResponse)
def create_match(match: MatchCreate, db: Session = Depends(get_db)):
    db_match = Match(**match.model_dump())
    db.add(db_match)
    db.commit()
    db.refresh(db_match)
    return db_match  # Automatically converted to MatchResponse
```

### 2️⃣ Update Resource (PATCH - partial update)
```python
@router.patch("/matches/{match_id}", response_model=MatchResponse)
def update_match(match_id: int, match: MatchUpdate, db: Session = Depends(get_db)):
    db_match = db.query(Match).filter(Match.id == match_id).first()
    if not db_match:
        raise HTTPException(status_code=404, detail="Match not found")
    
    # Only update provided fields
    update_data = match.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_match, key, value)
    
    db.commit()
    db.refresh(db_match)
    return db_match
```

### 3️⃣ List Resources (GET)
```python
@router.get("/matches/", response_model=List[MatchResponse])
def list_matches(project_id: int, db: Session = Depends(get_db)):
    matches = db.query(Match).filter(Match.project_id == project_id).all()
    return matches  # Auto-converts to List[MatchResponse]
```

### 4️⃣ Get Single Resource (GET)
```python
@router.get("/matches/{match_id}", response_model=MatchResponse)
def get_match(match_id: int, db: Session = Depends(get_db)):
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return match
```

## 📋 Schema Usage by Entity

### Match Schemas
| Schema | Usage | Key Fields |
|--------|-------|-----------|
| `MatchBase` | Common fields | equipe1_nom, equipe2_nom, poule |
| `MatchCreate` | POST /matches/ | All required fields |
| `MatchUpdate` | PATCH /matches/{id} | All optional for partial update |
| `MatchResponse` | Response model | Includes id, timestamps, computed fields |
| `MatchMove` | Drag & drop calendar | semaine, creneau, gymnase_id |

### Project Schemas
| Schema | Usage | Key Fields |
|--------|-------|-----------|
| `ProjectBase` | Common fields | nom, annee_scolaire |
| `ProjectCreate` | POST /projects/ | Includes config_data (JSON) |
| `ProjectUpdate` | PATCH /projects/{id} | All optional |
| `ProjectResponse` | Response model | Includes id, timestamps |
| `ProjectStats` | Dashboard | total_matchs, matchs_planifies, etc. |

### Team Schemas
| Schema | Usage | Key Fields |
|--------|-------|-----------|
| `TeamBase` | Common fields | nom, categorie, niveau |
| `TeamCreate` | POST /teams/ | Includes horaires_preferes (list) |
| `TeamUpdate` | PATCH /teams/{id} | All optional |
| `TeamResponse` | Response model | Full team with preferences |

### Venue Schemas
| Schema | Usage | Key Fields |
|--------|-------|-----------|
| `VenueBase` | Common fields | nom, capacite |
| `VenueCreate` | POST /venues/ | Includes horaires_disponibles (list) |
| `VenueUpdate` | PATCH /venues/{id} | All optional |
| `VenueResponse` | Response model | Full venue with availability |

## ⚙️ Special Use Cases

### 1️⃣ Drag & Drop Calendar Update
```python
@router.patch("/matches/{match_id}/move", response_model=MatchResponse)
def move_match(match_id: int, move: MatchMove, db: Session = Depends(get_db)):
    db_match = db.query(Match).filter(Match.id == match_id).first()
    if not db_match:
        raise HTTPException(status_code=404, detail="Match not found")
    
    # Update only calendar position
    db_match.semaine = move.semaine
    db_match.creneau = move.creneau
    db_match.gymnase_id = move.gymnase_id
    db_match.statut = "planifie"
    
    db.commit()
    db.refresh(db_match)
    return db_match
```

### 2️⃣ Project Dashboard Stats
```python
@router.get("/projects/{project_id}/stats", response_model=ProjectStats)
def get_project_stats(project_id: int, db: Session = Depends(get_db)):
    total = db.query(Match).filter(Match.project_id == project_id).count()
    planifies = db.query(Match).filter(
        Match.project_id == project_id,
        Match.statut == "planifie"
    ).count()
    
    return ProjectStats(
        total_matchs=total,
        matchs_planifies=planifies,
        matchs_non_planifies=total - planifies,
        taux_planification=(planifies / total * 100) if total > 0 else 0
    )
```

### 3️⃣ JSON Config Storage
```python
# Store YAML config as JSON in database
from core.config import Config

@router.post("/projects/from-yaml/", response_model=ProjectResponse)
def create_project_from_yaml(yaml_path: str, db: Session = Depends(get_db)):
    config = Config.from_yaml(yaml_path)
    
    project_data = ProjectCreate(
        nom=config.nom_championnat,
        annee_scolaire="2025-2026",
        config_data=config.to_dict()  # Dict[str, Any] → JSON
    )
    
    db_project = Project(**project_data.model_dump())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project
```

## 🔄 ORM ↔ Pydantic Conversion

### ORM → Pydantic (Automatic)
```python
# from_attributes=True enables this
match_orm = db.query(Match).first()
match_response = MatchResponse.model_validate(match_orm)
# ✅ Works automatically with Response schemas
```

### Pydantic → ORM (Manual)
```python
# Create from Pydantic
match_create = MatchCreate(...)
match_orm = Match(**match_create.model_dump())

# Update from Pydantic
match_update = MatchUpdate(semaine=10)
for key, value in match_update.model_dump(exclude_unset=True).items():
    setattr(match_orm, key, value)
```

## 🎨 Validation Examples

### Required Fields
```python
# ❌ Missing required fields
match = MatchCreate(equipe1_nom="CENTRALE 1")  # ValidationError

# ✅ All required fields
match = MatchCreate(
    project_id=1,
    equipe1_nom="CENTRALE 1",
    equipe2_nom="MINES 1",
    poule="VBA1",
    semaine=5
)
```

### Optional Fields with Defaults
```python
# ✅ Uses defaults
match = MatchCreate(
    project_id=1,
    equipe1_nom="CENTRALE 1",
    equipe2_nom="MINES 1",
    poule="VBA1",
    semaine=5
    # est_fixe defaults to False
    # statut defaults to "a_planifier"
    # priorite defaults to 0
)
```

### Partial Updates
```python
# ✅ Update only semaine
match_update = MatchUpdate(semaine=10)
# Other fields remain unchanged

# ✅ Update multiple fields
match_update = MatchUpdate(
    semaine=10,
    creneau="14h",
    statut="planifie"
)
```

### List Fields
```python
# ✅ Team with preferences
team = TeamCreate(
    project_id=1,
    nom="CENTRALE 1",
    categorie="VBA",
    niveau=1,
    horaires_preferes=["14h-16h", "16h-18h"],
    lieux_preferes=["Gymnase A", "Gymnase B"]
)

# ✅ Empty lists OK
team = TeamCreate(
    project_id=1,
    nom="CENTRALE 1",
    categorie="VBA",
    niveau=1,
    horaires_preferes=[],  # No preferences
    lieux_preferes=None    # Also OK
)
```

## 📊 Status & Validation

### Match Status Values
- `"a_planifier"` (default): Not yet scheduled
- `"planifie"`: Successfully scheduled
- `"conflit"`: Constraint violation

### Common Validations
```python
# In API route
if match_update.statut and match_update.statut not in ["a_planifier", "planifie", "conflit"]:
    raise HTTPException(status_code=400, detail="Invalid status")

if match_update.semaine and (match_update.semaine < 1 or match_update.semaine > 52):
    raise HTTPException(status_code=400, detail="Invalid week number")
```

## 🚀 Next Steps

After mastering schemas, proceed to:
1. **API Routes (Tâche 1.5)**: Use these schemas in FastAPI routes
2. **Sync Service (Tâche 1.6)**: Import Excel data using Create schemas
3. **Frontend Types (Tâche 2.x)**: Mirror these as TypeScript interfaces

---

**Created**: Tâche 1.4 - Pydantic Schemas  
**Total Schemas**: 18 across 4 entities  
**Pattern**: Base/Create/Update/Response  
**ORM Conversion**: ✅ from_attributes=True
