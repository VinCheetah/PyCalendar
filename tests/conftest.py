"""
Configuration pytest pour PyCalendar backend.

Définit les fixtures partagées entre tous les tests.
"""

import pytest
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
import tempfile
import shutil
import pandas as pd

from backend.database.models import Base
from backend.api.main import app
from backend.database.engine import get_db

# Création DB en mémoire pour tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def test_db():
    """
    Fixture pour créer DB de test en mémoire.
    
    Yield:
        Session: Session SQLAlchemy de test
    """
    # Créer engine + tables
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    
    # Créer session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    
    yield db
    
    # Cleanup
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    """
    Fixture pour créer client FastAPI de test.
    
    Override la dépendance get_db pour utiliser test_db.
    
    Yield:
        TestClient: Client FastAPI de test
    """
    def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as c:
        yield c
    
    # Cleanup
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def config_yaml_file():
    """
    Fixture pour créer fichier YAML de test.
    
    Yield:
        Path: Chemin vers YAML temporaire
    """
    # Créer répertoire temporaire
    temp_dir = Path(tempfile.mkdtemp())
    yaml_path = temp_dir / "config_test.yaml"
    
    # Contenu YAML minimal (tous les paramètres sont dedans, pas de défaut .py)
    yaml_content = """sport: "Volleyball"

semaines:
  semaine_minimum: 2
  nb_semaines: 10

contraintes:
  poids:
    respect_repos: 10.0
    equilibre_domicile_exterieur: 8.0
    respect_indisponibilites: 20.0
    respect_preferences: 5.0

solver:
  strategie: "optimal"
  temps_max_secondes: 300

fichiers:
  donnees: "test_data.xlsx"
"""
    
    yaml_path.write_text(yaml_content)
    
    yield yaml_path
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture(scope="function")
def config_excel_file():
    """
    Fixture pour créer fichier Excel de test.
    
    Yield:
        Path: Chemin vers Excel temporaire
    """
    # Créer répertoire temporaire
    temp_dir = Path(tempfile.mkdtemp())
    excel_path = temp_dir / "test_data.xlsx"
    
    # Feuille Equipes
    df_equipes = pd.DataFrame({
        "Institution": ["Lycée A", "Lycée A", "Lycée B"],
        "Numéro équipe": [1, 2, 1],
        "Niveau": ["Minimes", "Minimes", "Minimes"],
        "Catégorie": ["Garçons", "Garçons", "Filles"],
        "Poule": ["P1", "P1", "P1"],
        "Gymnase préféré": ["Gymnase 1", "Gymnase 1", "Gymnase 2"]
    })
    
    # Feuille Gymnases
    df_gymnases = pd.DataFrame({
        "Nom": ["Gymnase 1", "Gymnase 2"],
        "Capacité": [100, 80],
        "Adresse": ["Rue A", "Rue B"]
    })
    
    # Feuille Indispos_Gymnases
    df_indispo_gym = pd.DataFrame({
        "Gymnase": ["Gymnase 1"],
        "Date début": ["2025-01-15"],
        "Date fin": ["2025-01-20"],
        "Raison": ["Travaux"]
    })
    
    # Feuille Indispos_Equipes
    df_indispo_equipes = pd.DataFrame({
        "Institution": ["Lycée A"],
        "Numéro équipe": [1],
        "Niveau": ["Minimes"],
        "Catégorie": ["Garçons"],
        "Date début": ["2025-02-10"],
        "Date fin": ["2025-02-15"],
        "Raison": ["Stage"]
    })
    
    # Feuille Indispos_Institutions
    df_indispo_inst = pd.DataFrame({
        "Institution": ["Lycée B"],
        "Date début": ["2025-03-01"],
        "Date fin": ["2025-03-05"],
        "Raison": ["Vacances"]
    })
    
    # Feuille Preferences_Gymnases
    df_prefs = pd.DataFrame({
        "Institution": ["Lycée A"],
        "Gymnase préféré": ["Gymnase 1"],
        "Priorité": [1]
    })
    
    # Feuille Obligation_Presence
    df_oblig = pd.DataFrame({
        "Institution": ["Lycée A"],
        "Semaine": [3],
        "Raison": ["Événement local"]
    })
    
    # Écrire Excel
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        df_equipes.to_excel(writer, sheet_name='Equipes', index=False)
        df_gymnases.to_excel(writer, sheet_name='Gymnases', index=False)
        df_indispo_gym.to_excel(writer, sheet_name='Indispos_Gymnases', index=False)
        df_indispo_equipes.to_excel(writer, sheet_name='Indispos_Equipes', index=False)
        df_indispo_inst.to_excel(writer, sheet_name='Indispos_Institutions', index=False)
        df_prefs.to_excel(writer, sheet_name='Preferences_Gymnases', index=False)
        df_oblig.to_excel(writer, sheet_name='Obligation_Presence', index=False)
    
    yield excel_path
    
    # Cleanup
    shutil.rmtree(temp_dir)
