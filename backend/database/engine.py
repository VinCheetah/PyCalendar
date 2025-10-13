"""
SQLAlchemy Engine Configuration for PyCalendar V2

This module sets up the SQLite database connection, session factory, 
and provides utility functions for database initialization and dependency injection.

Key features:
- SQLite database with foreign keys enabled (CRITICAL - disabled by default)
- Session factory for FastAPI dependency injection
- Database initialization function
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from pathlib import Path

# Chemin vers la base de données SQLite
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # Racine du projet
DATABASE_PATH = BASE_DIR / "database" / "pycalendar.db"
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)  # Créer dossier si inexistant

# URL de connexion SQLite
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Créer l'engine SQLAlchemy
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Nécessaire pour FastAPI avec SQLite
    echo=False  # Mettre True pour debug SQL
)

# Activer les foreign keys SQLite (CRUCIAL - désactivées par défaut)
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Dependency injection pour FastAPI
def get_db():
    """Generator pour créer une session DB, l'utiliser, puis la fermer"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Fonction d'initialisation de la DB
def init_db():
    """Créer toutes les tables définies dans models.py"""
    from backend.database.models import Base  # Import ici pour éviter circular import
    Base.metadata.create_all(bind=engine)
    print(f"✅ Base de données créée : {DATABASE_PATH}")
