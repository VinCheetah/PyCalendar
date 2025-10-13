# 🗄️ Phase 1.2 : Database Models

## 🎯 Objectif
Créer les modèles de base de données SQLAlchemy et la couche de persistance.

**Durée estimée** : 3 heures  
**Prérequis** : Phase 1.1 complétée

---

## 📋 Ce que nous allons créer

```
backend/
├── database/
│   ├── __init__.py
│   ├── engine.py          # Configuration DB
│   ├── models.py          # Modèles SQLAlchemy
│   └── repositories.py    # Couche d'accès données
│
scripts/
└── init_db.py             # Script d'initialisation DB
```

---

## 🔧 Étape 1 : Créer la Structure Database

### 1.1 Créer les dossiers

```bash
mkdir -p backend/database
mkdir -p scripts
mkdir -p database  # Pour stocker le fichier SQLite
```

### 1.2 Créer les fichiers

```bash
touch backend/database/__init__.py
touch backend/database/engine.py
touch backend/database/models.py
touch backend/database/repositories.py
touch scripts/init_db.py
```

---

## 📝 Étape 2 : Configuration Database Engine

### 2.1 Créer `backend/database/engine.py`

```python
"""
Configuration de la connexion à la base de données.
Gère la création de l'engine SQLAlchemy et des sessions.
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from pathlib import Path
from typing import Generator

# ============================================================================
# Configuration Paths
# ============================================================================

# Dossier racine du projet
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Dossier pour la base de données
DB_DIR = PROJECT_ROOT / "database"
DB_DIR.mkdir(parents=True, exist_ok=True)

# Chemin vers le fichier SQLite
DB_PATH = DB_DIR / "pycalendar.db"

# ============================================================================
# Database URL
# ============================================================================

# SQLite URL (pour dev)
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Pour PostgreSQL (production future) :
# DATABASE_URL = "postgresql://user:password@localhost:5432/pycalendar"

# ============================================================================
# Engine Configuration
# ============================================================================

# Configuration engine
engine_kwargs = {
    "echo": False,  # True pour voir les requêtes SQL en console
}

# Config spécifique SQLite
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs.update({
        "connect_args": {"check_same_thread": False},
        # StaticPool pour tests (optionnel)
        # "poolclass": StaticPool,
    })

# Créer l'engine
engine = create_engine(DATABASE_URL, **engine_kwargs)


# ============================================================================
# Enable SQLite Foreign Keys
# ============================================================================

def _set_sqlite_pragma(dbapi_conn, connection_record):
    """
    Active les foreign keys pour SQLite.
    SQLite désactive les FK par défaut, on les active ici.
    """
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# Activer FKs si SQLite
if DATABASE_URL.startswith("sqlite"):
    event.listen(engine, "connect", _set_sqlite_pragma)


# ============================================================================
# Session Factory
# ============================================================================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ============================================================================
# Dependency pour FastAPI
# ============================================================================

def get_db() -> Generator[Session, None, None]:
    """
    Dependency pour obtenir une session DB dans FastAPI.
    
    Usage dans une route:
        @app.get("/items/")
        def read_items(db: Session = Depends(get_db)):
            items = db.query(Item).all()
            return items
    
    La session est automatiquement fermée après la requête.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# Fonctions Utilitaires
# ============================================================================

def init_db():
    """
    Initialise la base de données (crée les tables).
    
    À appeler depuis scripts/init_db.py ou au démarrage de l'app.
    """
    from .models import Base
    
    # Créer toutes les tables définies dans models.py
    Base.metadata.create_all(bind=engine)
    
    print(f"✅ Base de données initialisée : {DB_PATH}")
    print(f"   Tables créées : {', '.join(Base.metadata.tables.keys())}")


def drop_db():
    """
    Supprime toutes les tables de la base de données.
    ⚠️ ATTENTION: Perte de toutes les données !
    
    Utile pour tests ou réinitialisation complète.
    """
    from .models import Base
    
    Base.metadata.drop_all(bind=engine)
    print(f"⚠️  Toutes les tables supprimées de {DB_PATH}")


def reset_db():
    """
    Réinitialise complètement la base de données.
    Supprime puis recrée toutes les tables.
    """
    print("⚠️  Réinitialisation de la base de données...")
    drop_db()
    init_db()
    print("✅ Base de données réinitialisée")


# ============================================================================
# Info Database
# ============================================================================

def get_db_info():
    """
    Retourne des informations sur la base de données.
    """
    from .models import Base
    
    return {
        "url": str(DATABASE_URL).replace(str(PROJECT_ROOT), "..."),
        "path": str(DB_PATH),
        "engine": str(engine),
        "tables": list(Base.metadata.tables.keys()),
        "exists": DB_PATH.exists(),
        "size_mb": DB_PATH.stat().st_size / (1024 * 1024) if DB_PATH.exists() else 0,
    }


# ============================================================================
# Test Connection
# ============================================================================

def test_connection():
    """
    Teste la connexion à la base de données.
    """
    try:
        with engine.connect() as conn:
            result = conn.execute("SELECT 1").fetchone()
            print(f"✅ Connexion DB OK : {DATABASE_URL}")
            return True
    except Exception as e:
        print(f"❌ Erreur connexion DB : {e}")
        return False


if __name__ == "__main__":
    # Test de connexion
    test_connection()
    
    # Afficher infos
    import json
    print(json.dumps(get_db_info(), indent=2))
```

**Points clés** :
- ✅ Configuration SQLite avec foreign keys activées
- ✅ Fonction `get_db()` pour injection dans FastAPI
- ✅ Fonctions utilitaires (`init_db`, `drop_db`, `reset_db`)
- ✅ Support futur PostgreSQL (commenté)

---

## 📝 Étape 3 : Modèles SQLAlchemy

### 3.1 Créer `backend/database/models.py`

**Important** : Ces modèles mappent les classes Python (`core/models.py`) vers des tables SQL.

```python
"""
Modèles SQLAlchemy pour la base de données.
Définit la structure des tables et leurs relations.
"""
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, 
    ForeignKey, Text, Float, JSON
)
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
from typing import Optional

# Base pour tous les modèles
Base = declarative_base()


# ============================================================================
# Model: Project
# ============================================================================

class Project(Base):
    """
    Projet sportif (ex: Championnat Volley 2025-2026).
    
    Un projet contient :
    - Des équipes
    - Des gymnases
    - Des matchs
    - Une configuration spécifique
    """
    __tablename__ = "projects"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Informations générales
    nom = Column(String(200), nullable=False, index=True)
    sport = Column(String(50), nullable=False, index=True)
    description = Column(Text, default="")
    
    # Configuration
    config_yaml_path = Column(String(500))  # Chemin vers config YAML
    config_data = Column(JSON)  # Config en JSON pour accès rapide
    
    # Paramètres de planification
    nb_semaines = Column(Integer, default=26)
    semaine_min = Column(Integer, default=1)  # Semaine min pour planification
    semaine_debut = Column(DateTime)  # Date de début du championnat
    
    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations (cascade = suppression en cascade)
    matches = relationship(
        "Match",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    teams = relationship(
        "Team",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    venues = relationship(
        "Venue",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<Project(id={self.id}, nom='{self.nom}', sport='{self.sport}')>"


# ============================================================================
# Model: Team
# ============================================================================

class Team(Base):
    """
    Équipe sportive.
    
    Une équipe appartient à :
    - Un projet
    - Une institution
    - Une poule
    """
    __tablename__ = "teams"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Keys
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    
    # Informations équipe
    nom = Column(String(200), nullable=False, index=True)
    institution = Column(String(200), index=True)
    numero_equipe = Column(String(50))
    genre = Column(String(10), index=True)  # "M", "F", ""
    poule = Column(String(100), nullable=False, index=True)
    
    # Préférences (stockées en JSON)
    horaires_preferes = Column(JSON)  # Liste d'horaires
    lieux_preferes = Column(JSON)     # Liste de gymnases
    
    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    project = relationship("Project", back_populates="teams")
    
    def __repr__(self):
        return f"<Team(id={self.id}, nom='{self.nom}', poule='{self.poule}')>"
    
    @property
    def nom_complet(self) -> str:
        """Nom complet de l'équipe (institution + numéro)."""
        if self.numero_equipe:
            return f"{self.institution} ({self.numero_equipe})"
        return self.institution if self.institution else self.nom


# ============================================================================
# Model: Venue
# ============================================================================

class Venue(Base):
    """
    Gymnase/Lieu de compétition.
    
    Un gymnase a :
    - Une capacité (nombre de matchs simultanés)
    - Des créneaux horaires disponibles
    - Des indisponibilités
    """
    __tablename__ = "venues"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Keys
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    
    # Informations gymnase
    nom = Column(String(200), nullable=False, index=True)
    capacite = Column(Integer, default=1)  # Nombre de matchs simultanés
    
    # Disponibilités (JSON)
    horaires_disponibles = Column(JSON)  # Liste d'horaires
    semaines_indisponibles = Column(JSON)  # Dict {semaine: [horaires]}
    
    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    project = relationship("Project", back_populates="venues")
    
    def __repr__(self):
        return f"<Venue(id={self.id}, nom='{self.nom}', capacite={self.capacite})>"


# ============================================================================
# Model: Match
# ============================================================================

class Match(Base):
    """
    Match entre deux équipes.
    
    Un match a :
    - Deux équipes (domicile/extérieur)
    - Un créneau (semaine + horaire + gymnase) ou None si non planifié
    - Un statut (a_planifier, planifie, fixe, termine, annule)
    - Des scores (si match terminé)
    """
    __tablename__ = "matches"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Keys
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    
    # Équipe 1 (domicile)
    equipe1_nom = Column(String(200), nullable=False, index=True)
    equipe1_institution = Column(String(200))
    equipe1_genre = Column(String(10))
    
    # Équipe 2 (extérieur)
    equipe2_nom = Column(String(200), nullable=False, index=True)
    equipe2_institution = Column(String(200))
    equipe2_genre = Column(String(10))
    
    # Poule
    poule = Column(String(100), nullable=False, index=True)
    
    # Planification
    semaine = Column(Integer, nullable=True, index=True)
    horaire = Column(String(20), nullable=True)
    gymnase = Column(String(200), nullable=True, index=True)
    
    # Statut et contraintes
    est_fixe = Column(Boolean, default=False, index=True)
    statut = Column(
        String(50),
        default="a_planifier",
        nullable=False,
        index=True
    )
    # Statuts possibles :
    # - "a_planifier" : Match généré, pas encore planifié
    # - "planifie" : Match planifié (créneau attribué)
    # - "fixe" : Match fixé, ne peut pas être replanifié par solver
    # - "termine" : Match joué, scores enregistrés
    # - "annule" : Match annulé
    
    priorite = Column(Integer, default=0)  # Priorité de planification
    
    # Scores (si match terminé)
    score_equipe1 = Column(Integer, nullable=True)
    score_equipe2 = Column(Integer, nullable=True)
    
    # Métadonnées
    notes = Column(Text, default="")  # Notes libres
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    project = relationship("Project", back_populates="matches")
    
    def __repr__(self):
        creneau = f"S{self.semaine} {self.horaire}" if self.semaine else "Non planifié"
        return f"<Match(id={self.id}, {self.equipe1_nom} vs {self.equipe2_nom}, [{creneau}])>"
    
    @property
    def est_planifie(self) -> bool:
        """Le match est-il planifié ?"""
        return self.semaine is not None
    
    @property
    def est_modifiable(self) -> bool:
        """Le match peut-il être replanifié par le solver ?"""
        return not self.est_fixe and self.statut not in ["fixe", "termine", "annule"]
    
    @property
    def est_termine(self) -> bool:
        """Le match est-il terminé (avec scores) ?"""
        return self.statut == "termine" and self.score_equipe1 is not None
    
    def get_creneau_str(self) -> str:
        """Retourne le créneau sous forme de string."""
        if not self.est_planifie:
            return "Non planifié"
        return f"S{self.semaine} {self.horaire} - {self.gymnase}"


# ============================================================================
# Index Composés (pour performances)
# ============================================================================

from sqlalchemy import Index

# Index pour recherches fréquentes
Index('idx_match_project_semaine', Match.project_id, Match.semaine)
Index('idx_match_project_poule', Match.project_id, Match.poule)
Index('idx_match_project_statut', Match.project_id, Match.statut)
Index('idx_team_project_poule', Team.project_id, Team.poule)
```

**Points clés** :
- ✅ 4 tables principales : Project, Team, Venue, Match
- ✅ Relations avec cascade delete
- ✅ Index pour performances
- ✅ Properties helper (`est_planifie`, `est_modifiable`, etc.)
- ✅ JSON pour données complexes (horaires, préférences)

---

## 📝 Étape 4 : Script d'Initialisation

### 4.1 Créer `scripts/init_db.py`

```python
"""
Script pour initialiser la base de données.
Crée toutes les tables définies dans backend/database/models.py
"""
import sys
from pathlib import Path

# Ajouter le dossier parent au PYTHONPATH
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.database.engine import init_db, get_db_info, test_connection
import json


def main():
    """Point d'entrée du script."""
    print("="*60)
    print("INITIALISATION DE LA BASE DE DONNÉES")
    print("="*60)
    print()
    
    # Test de connexion
    print("1. Test de connexion...")
    if not test_connection():
        print("❌ Impossible de se connecter à la base de données")
        return 1
    print()
    
    # Initialisation
    print("2. Création des tables...")
    try:
        init_db()
    except Exception as e:
        print(f"❌ Erreur lors de la création des tables : {e}")
        import traceback
        traceback.print_exc()
        return 1
    print()
    
    # Informations
    print("3. Informations sur la base de données :")
    info = get_db_info()
    print(json.dumps(info, indent=2, ensure_ascii=False))
    print()
    
    print("="*60)
    print("✅ INITIALISATION TERMINÉE AVEC SUCCÈS")
    print("="*60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

### 4.2 Rendre le script exécutable

```bash
chmod +x scripts/init_db.py
```

---

## ✅ Étape 5 : Tester la Configuration

### 5.1 Initialiser la base de données

```bash
python scripts/init_db.py
```

**Sortie attendue** :
```
============================================================
INITIALISATION DE LA BASE DE DONNÉES
============================================================

1. Test de connexion...
✅ Connexion DB OK : sqlite:////home/.../database/pycalendar.db

2. Création des tables...
✅ Base de données initialisée : /home/.../database/pycalendar.db
   Tables créées : projects, teams, venues, matches

3. Informations sur la base de données :
{
  "url": ".../database/pycalendar.db",
  "path": "/home/.../database/pycalendar.db",
  "engine": "Engine(sqlite:///...)",
  "tables": ["projects", "teams", "venues", "matches"],
  "exists": true,
  "size_mb": 0.01
}

============================================================
✅ INITIALISATION TERMINÉE AVEC SUCCÈS
============================================================
```

### 5.2 Vérifier que le fichier DB existe

```bash
ls -lh database/pycalendar.db
# Devrait afficher : -rw-r--r-- ... pycalendar.db
```

### 5.3 Inspecter la structure (optionnel)

```bash
# Installer sqlite3 si pas déjà fait
# sudo apt install sqlite3  # Linux
# brew install sqlite3      # macOS

sqlite3 database/pycalendar.db ".schema"
```

**Sortie attendue** :
```sql
CREATE TABLE projects (
    id INTEGER NOT NULL,
    nom VARCHAR(200) NOT NULL,
    sport VARCHAR(50) NOT NULL,
    ...
    PRIMARY KEY (id)
);

CREATE TABLE teams (
    id INTEGER NOT NULL,
    project_id INTEGER NOT NULL,
    ...
    PRIMARY KEY (id),
    FOREIGN KEY(project_id) REFERENCES projects (id)
);

CREATE TABLE venues (...);
CREATE TABLE matches (...);
```

---

## 📝 Étape 6 : Mettre à Jour FastAPI

### 6.1 Mettre à jour `backend/api/dependencies.py`

Décommenter la fonction `get_db()` maintenant qu'elle est implémentée :

```python
"""
Dependencies pour FastAPI.
"""
from typing import Generator
from sqlalchemy.orm import Session
from backend.database.engine import SessionLocal  # ← Ajouter cet import


def get_db() -> Generator[Session, None, None]:
    """
    Dependency pour obtenir une session DB dans FastAPI.
    
    Usage:
        @app.get("/items/")
        def read_items(db: Session = Depends(get_db)):
            items = db.query(Item).all()
            return items
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ... reste du fichier inchangé
```

### 6.2 Ajouter endpoint de test DB dans `backend/api/main.py`

Ajouter cet endpoint à la fin du fichier (avant le `if __name__ == "__main__"`):

```python
# ... code existant ...

# ============================================================================
# Database Test Endpoint
# ============================================================================

from sqlalchemy.orm import Session
from fastapi import Depends
from backend.api.dependencies import get_db
from backend.database import models

@app.get("/api/db/info", tags=["Database"])
async def database_info(db: Session = Depends(get_db)):
    """
    Informations sur la base de données.
    Utile pour vérifier la connexion et le contenu.
    """
    from backend.database.engine import get_db_info
    
    # Infos générales
    info = get_db_info()
    
    # Compter les enregistrements
    info["counts"] = {
        "projects": db.query(models.Project).count(),
        "teams": db.query(models.Team).count(),
        "venues": db.query(models.Venue).count(),
        "matches": db.query(models.Match).count(),
    }
    
    return info


# ... if __name__ == "__main__" ...
```

### 6.3 Tester le endpoint

```bash
# Lancer l'API
uvicorn backend.api.main:app --reload

# Dans un autre terminal
curl http://localhost:8000/api/db/info
```

**Sortie attendue** :
```json
{
  "url": ".../database/pycalendar.db",
  "path": "/home/.../database/pycalendar.db",
  "tables": ["projects", "teams", "venues", "matches"],
  "exists": true,
  "size_mb": 0.01,
  "counts": {
    "projects": 0,
    "teams": 0,
    "venues": 0,
    "matches": 0
  }
}
```

---

## 🐛 Troubleshooting

### Erreur : `no such table: projects`
**Solution** : Relancer `python scripts/init_db.py`

### Erreur : `FOREIGN KEY constraint failed`
**Solution** : Vérifier que les foreign keys sont activées (déjà fait dans `engine.py`)

### Base de données verrouillée
**Solution** :
```bash
# Arrêter tous les processus qui utilisent la DB
pkill -f uvicorn
# Supprimer les locks
rm database/pycalendar.db-wal database/pycalendar.db-shm
```

### Réinitialiser complètement la DB
```bash
rm database/pycalendar.db
python scripts/init_db.py
```

---

## ✅ Critères de Validation

Avant de passer au guide suivant, vérifier que :

- [ ] `python scripts/init_db.py` s'exécute sans erreur
- [ ] Le fichier `database/pycalendar.db` existe
- [ ] `.schema` dans sqlite3 montre les 4 tables
- [ ] L'endpoint `/api/db/info` fonctionne
- [ ] Aucune erreur dans logs FastAPI
- [ ] Foreign keys activées (test avec insertion)

---

## 🎯 Prochaines Étapes

1. **Commit** :
   ```bash
   git add backend/database/ scripts/init_db.py database/
   git commit -m "feat(backend): Add SQLAlchemy models and DB init"
   ```

2. **Passer au guide suivant** :
   ```bash
   cat docs/implementation/phase1/03_api_routes.md
   ```

---

## 📚 Références

- [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/20/orm/)
- [SQLAlchemy Relationships](https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html)
- [SQLite Foreign Keys](https://www.sqlite.org/foreignkeys.html)

---

**Durée réelle** : _____ heures  
**Difficultés rencontrées** : _____  
**Notes** : _____
