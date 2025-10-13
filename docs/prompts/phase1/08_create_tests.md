# PROMPT 1.8 : Tests Unitaires Backend

## Contexte Projet

**PyCalendar V2** : Tests backend pour valider database models et API routes.

## État Actuel

- ✅ Backend complet (DB, API, Scripts)
- ⏳ Phase 1 finale : Tests unitaires

## Objectif

Créer tests avec pytest :
- **Fixtures** : DB in-memory, sample data
- **Tests models** : CRUD, properties, cascade
- **Tests API** : Endpoints HTTP

**Durée** : 1h

## Instructions

### 1. Structure

```bash
mkdir -p tests/unit
touch tests/__init__.py
touch tests/conftest.py
touch tests/unit/__init__.py
touch tests/unit/test_models.py
touch tests/unit/test_api_matches.py
```

### 2. Fixtures pytest

**Fichier** : `tests/conftest.py`

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from backend.database.models import Base
from backend.database import models
from backend.api.main import app
from backend.api.dependencies import get_db

# Engine in-memory pour tests
@pytest.fixture(scope="function")
def db_engine():
    """Engine SQLite in-memory."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(db_engine):
    """Session DB pour tests."""
    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()
    yield session
    session.close()

@pytest.fixture(scope="function")
def sample_project(db_session):
    """Projet de test."""
    project = models.Project(
        nom="Test Project",
        sport="volleyball",
        nb_semaines=10,
        semaine_min=1
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project

@pytest.fixture(scope="function")
def sample_match(db_session, sample_project):
    """Match de test."""
    match = models.Match(
        project_id=sample_project.id,
        equipe1_nom="Équipe A",
        equipe2_nom="Équipe B",
        poule="P1"
    )
    db_session.add(match)
    db_session.commit()
    db_session.refresh(match)
    return match

@pytest.fixture(scope="function")
def client(db_session):
    """TestClient FastAPI avec DB override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
```

### 3. Tests Models

**Fichier** : `tests/unit/test_models.py`

```python
from backend.database import models

def test_create_project(db_session):
    """Test création projet."""
    project = models.Project(
        nom="Test",
        sport="volley",
        nb_semaines=26
    )
    db_session.add(project)
    db_session.commit()
    
    assert project.id is not None
    assert project.nom == "Test"
    assert project.semaine_min == 1  # Default

def test_create_match(db_session, sample_project):
    """Test création match."""
    match = models.Match(
        project_id=sample_project.id,
        equipe1_nom="A",
        equipe2_nom="B",
        poule="P1"
    )
    db_session.add(match)
    db_session.commit()
    
    assert match.id is not None
    assert match.project_id == sample_project.id

def test_match_properties(db_session, sample_match):
    """Test properties Match."""
    # Non planifié par défaut
    assert sample_match.est_planifie == False
    assert sample_match.est_modifiable == True
    
    # Planifier
    sample_match.semaine = 5
    sample_match.horaire = "14:00"
    sample_match.gymnase = "Gymnase A"
    db_session.commit()
    
    assert sample_match.est_planifie == True
    assert sample_match.est_modifiable == True
    
    # Fixer
    sample_match.est_fixe = True
    sample_match.statut = "fixe"
    db_session.commit()
    
    assert sample_match.est_modifiable == False

def test_cascade_delete(db_session, sample_project):
    """Test suppression cascade."""
    # Créer match lié
    match = models.Match(
        project_id=sample_project.id,
        equipe1_nom="A",
        equipe2_nom="B",
        poule="P1"
    )
    db_session.add(match)
    db_session.commit()
    match_id = match.id
    
    # Supprimer projet
    db_session.delete(sample_project)
    db_session.commit()
    
    # Vérifier match supprimé
    match = db_session.query(models.Match).filter(models.Match.id == match_id).first()
    assert match is None

def test_match_statut_transitions(db_session, sample_match):
    """Test transitions statuts."""
    assert sample_match.statut == "a_planifier"
    
    # Planifier
    sample_match.semaine = 3
    sample_match.statut = "planifie"
    db_session.commit()
    assert sample_match.est_modifiable == True
    
    # Terminer
    sample_match.statut = "termine"
    sample_match.score_equipe1 = 3
    sample_match.score_equipe2 = 1
    db_session.commit()
    assert sample_match.est_modifiable == False
```

### 4. Tests API

**Fichier** : `tests/unit/test_api_matches.py`

```python
def test_health_endpoint(client):
    """Test endpoint santé."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_list_matches_empty(client):
    """Test liste matchs vide."""
    response = client.get("/api/matches/")
    assert response.status_code == 200
    assert response.json() == []

def test_create_match(client, sample_project):
    """Test création match."""
    data = {
        "project_id": sample_project.id,
        "equipe1_nom": "Team A",
        "equipe2_nom": "Team B",
        "poule": "P1"
    }
    response = client.post("/api/matches/", json=data)
    
    assert response.status_code == 201
    match = response.json()
    assert match["equipe1_nom"] == "Team A"
    assert match["id"] is not None

def test_get_match(client, sample_match):
    """Test récupération match."""
    response = client.get(f"/api/matches/{sample_match.id}")
    
    assert response.status_code == 200
    match = response.json()
    assert match["id"] == sample_match.id
    assert match["equipe1_nom"] == "Équipe A"

def test_get_match_not_found(client):
    """Test match inexistant."""
    response = client.get("/api/matches/999")
    assert response.status_code == 404

def test_move_match(client, sample_match):
    """Test déplacement match."""
    # Planifier d'abord
    sample_match.semaine = 1
    sample_match.horaire = "14:00"
    sample_match.gymnase = "Gym A"
    
    # Déplacer
    data = {
        "semaine": 5,
        "horaire": "16:00",
        "gymnase": "Gym B"
    }
    response = client.post(f"/api/matches/{sample_match.id}/move", json=data)
    
    assert response.status_code == 200
    match = response.json()
    assert match["semaine"] == 5
    assert match["horaire"] == "16:00"
    assert match["statut"] == "planifie"

def test_fix_match(client, sample_match):
    """Test fixer match."""
    response = client.post(f"/api/matches/{sample_match.id}/fix")
    
    assert response.status_code == 200
    assert "fixé" in response.json()["message"].lower()
    
    # Vérifier en DB
    response = client.get(f"/api/matches/{sample_match.id}")
    match = response.json()
    assert match["est_fixe"] == True
    assert match["statut"] == "fixe"

def test_cannot_move_fixed_match(client, sample_match):
    """Test impossible déplacer match fixé."""
    # Fixer
    sample_match.est_fixe = True
    sample_match.statut = "fixe"
    
    # Tenter déplacer
    data = {"semaine": 3, "horaire": "14:00", "gymnase": "Gym A"}
    response = client.post(f"/api/matches/{sample_match.id}/move", json=data)
    
    assert response.status_code == 400
    assert "non modifiable" in response.json()["detail"].lower()
```

## Validation

```bash
# Installer pytest
pip install pytest pytest-cov

# Lancer tests
pytest tests/ -v

# Avec coverage
pytest tests/ -v --cov=backend --cov-report=html

# Ouvrir rapport
open htmlcov/index.html
```

**Attendu** : Tous tests passent, coverage >80%

## Critères de Réussite

- [ ] Dossier `tests/` avec structure
- [ ] Fixtures : db_engine, db_session, sample_project, sample_match, client
- [ ] Tests models : création, properties, cascade
- [ ] Tests API : health, CRUD, move, fix/unfix
- [ ] Tous tests passent
- [ ] Coverage >80% sur backend/

## Phase 1 Complète !

✅ Backend Foundation terminé :
- Core models enrichis
- Database SQLAlchemy
- API REST FastAPI
- Service sync Excel
- Scripts CLI
- Tests unitaires

➡️ **Phase 2** : Frontend React
