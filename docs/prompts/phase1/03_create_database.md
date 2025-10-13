# PROMPT 1.3 : Créer Database Backend avec SQLAlchemy

## Contexte Projet

**PyCalendar V2** : Application web pour gestion calendriers sportifs. Phase Backend : créer couche persistance pour stocker projets, équipes, gymnases, matchs en base de données.

## État Actuel

- ✅ Modèle `Match` enrichi (matchs fixes, scores)
- ✅ Config avec `semaine_min`
- ⏳ Phase 1.3 : Créer database models SQLAlchemy

## Objectif de cette Tâche

Créer la couche persistance avec :
1. **Engine SQLAlchemy** (SQLite dev)
2. **4 Models** : Project, Team, Venue, Match
3. **Relations** entre tables
4. **Indexes** pour performance

**Durée estimée** : 1h30

## Instructions Techniques

### 1. Créer Structure Dossiers

```bash
mkdir -p backend/database
touch backend/__init__.py
touch backend/database/__init__.py
touch backend/database/engine.py
touch backend/database/models.py
```

### 2. Créer Engine SQLAlchemy

**Fichier** : `backend/database/engine.py`

```python
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from pathlib import Path

# Chemin base de données
DB_PATH = Path(__file__).parent.parent.parent / "database" / "pycalendar.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Engine SQLite
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False  # True pour debug SQL
)

# Activer foreign keys SQLite (CRITIQUE)
def _set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

event.listen(engine, "connect", _set_sqlite_pragma)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency pour FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Fonctions utilitaires
def init_db():
    """Créer toutes les tables."""
    from .models import Base
    Base.metadata.create_all(bind=engine)

def drop_db():
    """Supprimer toutes les tables."""
    from .models import Base
    Base.metadata.drop_all(bind=engine)

def reset_db():
    """Réinitialiser la base."""
    drop_db()
    init_db()
```

**Points critiques** :
- `PRAGMA foreign_keys=ON` **obligatoire** pour SQLite
- `check_same_thread=False` pour FastAPI async
- `get_db()` est un generator pour dependency injection

### 3. Créer Models SQLAlchemy

**Fichier** : `backend/database/models.py`

```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON, Index
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

class Project(Base):
    """Projet de calendrier (ex: Volley 2025, Handball Printemps)."""
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(200), nullable=False)
    sport = Column(String(50), nullable=False)  # volleyball, handball, basket, etc.
    config_yaml_path = Column(String(500), nullable=True)
    config_data = Column(JSON, nullable=True)  # Config complète en JSON
    nb_semaines = Column(Integer, default=26)
    semaine_min = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations (cascade delete)
    matches = relationship("Match", back_populates="project", cascade="all, delete-orphan")
    teams = relationship("Team", back_populates="project", cascade="all, delete-orphan")
    venues = relationship("Venue", back_populates="project", cascade="all, delete-orphan")


class Team(Base):
    """Équipe participante."""
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    
    nom = Column(String(200), nullable=False)
    institution = Column(String(200), nullable=True)
    numero_equipe = Column(String(50), nullable=True)
    genre = Column(String(10), nullable=True)  # M, F, Mixte
    poule = Column(String(100), nullable=False, index=True)
    
    horaires_preferes = Column(JSON, nullable=True)  # ["14:00", "16:00"]
    lieux_preferes = Column(JSON, nullable=True)     # ["Gymnase A", "Gymnase B"]
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relation
    project = relationship("Project", back_populates="teams")


class Venue(Base):
    """Gymnase/lieu de jeu."""
    __tablename__ = "venues"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    
    nom = Column(String(200), nullable=False)
    capacite = Column(Integer, default=1)  # Nombre matchs simultanés
    horaires_disponibles = Column(JSON, nullable=True)  # ["14:00", "16:00", "18:00"]
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relation
    project = relationship("Project", back_populates="venues")


class Match(Base):
    """Match entre deux équipes."""
    __tablename__ = "matches"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    
    # Équipe 1
    equipe1_nom = Column(String(200), nullable=False)
    equipe1_institution = Column(String(200), nullable=True)
    equipe1_genre = Column(String(10), nullable=True)
    
    # Équipe 2
    equipe2_nom = Column(String(200), nullable=False)
    equipe2_institution = Column(String(200), nullable=True)
    equipe2_genre = Column(String(10), nullable=True)
    
    poule = Column(String(100), nullable=False, index=True)
    
    # Créneau (nullable si non planifié)
    semaine = Column(Integer, nullable=True, index=True)
    horaire = Column(String(20), nullable=True)
    gymnase = Column(String(200), nullable=True)
    
    # État du match
    est_fixe = Column(Boolean, default=False, index=True)
    statut = Column(String(50), default="a_planifier", index=True)  # a_planifier|planifie|fixe|termine|annule
    priorite = Column(Integer, default=0)
    
    # Scores (si terminé)
    score_equipe1 = Column(Integer, nullable=True)
    score_equipe2 = Column(Integer, nullable=True)
    notes = Column(Text, default="")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relation
    project = relationship("Project", back_populates="matches")
    
    # Properties (comme core.Match)
    @property
    def est_planifie(self) -> bool:
        return self.semaine is not None
    
    @property
    def est_modifiable(self) -> bool:
        return not self.est_fixe and self.statut not in ["fixe", "termine", "annule"]


# Indexes composites pour performance
Index('idx_match_project_semaine', Match.project_id, Match.semaine)
Index('idx_match_project_poule', Match.project_id, Match.poule)
Index('idx_match_project_statut', Match.project_id, Match.statut)
```

**Points critiques** :
- `cascade="all, delete-orphan"` : supprimer projet = supprimer tous matchs/teams/venues
- Colonnes `JSON` pour listes (horaires, lieux)
- Properties `est_planifie`, `est_modifiable` reproduisent logique `core.Match`
- Indexes sur foreign keys et colonnes souvent queryées

### 4. Créer __init__.py

**Fichier** : `backend/database/__init__.py`

```python
from .engine import engine, SessionLocal, get_db, init_db, drop_db, reset_db
from .models import Base, Project, Team, Venue, Match

__all__ = [
    "engine",
    "SessionLocal",
    "get_db",
    "init_db",
    "drop_db",
    "reset_db",
    "Base",
    "Project",
    "Team",
    "Venue",
    "Match",
]
```

## Validation

### Test 1 : Import Models

```bash
python -c "
from backend.database import models
print('✅ Import models réussi')
print(f'Tables définies: {list(models.Base.metadata.tables.keys())}')
"
```

**Attendu** : `['projects', 'teams', 'venues', 'matches']`

### Test 2 : Créer DB

```bash
python -c "
from backend.database import init_db
init_db()
print('✅ Base de données créée')
"
```

Vérifier fichier créé : `database/pycalendar.db`

### Test 3 : Vérifier Structure

```bash
sqlite3 database/pycalendar.db ".schema"
```

**Attendu** : Tables `projects`, `teams`, `venues`, `matches` avec colonnes correctes.

### Test 4 : Tester Foreign Keys

```bash
python -c "
from backend.database import SessionLocal, models

db = SessionLocal()

# Créer projet
project = models.Project(nom='Test', sport='volley', nb_semaines=10)
db.add(project)
db.commit()
db.refresh(project)

# Créer match lié
match = models.Match(
    project_id=project.id,
    equipe1_nom='Équipe A',
    equipe2_nom='Équipe B',
    poule='P1'
)
db.add(match)
db.commit()

print(f'✅ Projet ID={project.id}, Match ID={match.id}')

# Supprimer projet (doit cascade)
db.delete(project)
db.commit()

# Vérifier match supprimé
count = db.query(models.Match).count()
assert count == 0, 'Match aurait dû être supprimé en cascade'
print('✅ Cascade delete fonctionne')

db.close()
"
```

## Critères de Réussite

- [ ] Dossier `backend/database/` créé
- [ ] Fichier `engine.py` avec SQLAlchemy engine et SessionLocal
- [ ] Fichier `models.py` avec 4 models (Project, Team, Venue, Match)
- [ ] Foreign keys activées (PRAGMA)
- [ ] Cascade delete configuré
- [ ] Properties `est_planifie`, `est_modifiable` sur Match
- [ ] Indexes créés
- [ ] Fichier `database/pycalendar.db` créé par script
- [ ] Tables visibles avec `.schema`

## Prochaine Étape

➡️ **Prompt 1.4** : Créer schemas Pydantic pour validation API
