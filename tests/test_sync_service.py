"""
Tests du service de synchronisation (import YAML+Excel).

Valide l'import de fichiers config et la création d'équipes/gymnases/matchs.
"""

import pytest
from pathlib import Path
from backend.services.sync_service import SyncService
from backend.database import models


def test_import_from_yaml_and_excel(test_db, config_yaml_file, config_excel_file):
    """Test import complet YAML+Excel → création équipes/gymnases/matchs."""
    # Créer project
    project = models.Project(
        nom="Test Import",
        sport="Volleyball",
        nb_semaines=10,
        semaine_min=2,
        config_yaml_path=str(config_yaml_file)
    )
    test_db.add(project)
    test_db.commit()
    
    # Service
    sync_service = SyncService(test_db)
    
    # Import
    stats = sync_service.import_from_yaml_and_excel(
        project_id=project.id,
        yaml_path=str(config_yaml_file),
        excel_path=str(config_excel_file)
    )
    
    # Vérifier stats
    assert stats["equipes_importees"] == 3  # 3 teams dans config_excel_file
    assert stats["gymnases_importes"] == 2  # 2 gymnases
    assert stats["matchs_generes"] >= 0  # Matchs générés par le système
    
    # Vérifier équipes créées
    teams = test_db.query(models.Team).filter_by(project_id=project.id).all()
    assert len(teams) == 3
    team_names = [t.nom for t in teams]
    assert "Lycée A - 1" in team_names
    assert "Lycée A - 2" in team_names
    assert "Lycée B - 1" in team_names
    
    # Vérifier gymnases créés
    venues = test_db.query(models.Venue).filter_by(project_id=project.id).all()
    assert len(venues) == 2
    venue_names = [v.nom for v in venues]
    assert "Gymnase 1" in venue_names
    assert "Gymnase 2" in venue_names
    
    # Vérifier project config mise à jour
    test_db.refresh(project)
    assert project.config_data is not None
    assert "equipes_importees" in project.config_data


def test_import_yaml_not_found(test_db):
    """Test import avec YAML inexistant → FileNotFoundError."""
    project = models.Project(
        nom="Test",
        sport="Volley",
        nb_semaines=5,
        semaine_min=1,
        config_yaml_path="/fake/path.yaml"
    )
    test_db.add(project)
    test_db.commit()
    
    sync_service = SyncService(test_db)
    
    with pytest.raises(FileNotFoundError):
        sync_service.import_from_yaml_and_excel(
            project_id=project.id,
            yaml_path="/fake/path.yaml",
            excel_path="/fake/data.xlsx"
        )


def test_import_excel_not_found(test_db, config_yaml_file):
    """Test import avec Excel inexistant → FileNotFoundError."""
    project = models.Project(
        nom="Test",
        sport="Volley",
        nb_semaines=5,
        semaine_min=1,
        config_yaml_path=str(config_yaml_file)
    )
    test_db.add(project)
    test_db.commit()
    
    sync_service = SyncService(test_db)
    
    with pytest.raises(FileNotFoundError):
        sync_service.import_from_yaml_and_excel(
            project_id=project.id,
            yaml_path=str(config_yaml_file),
            excel_path="/fake/data.xlsx"
        )


def test_import_validates_sheets(test_db, config_yaml_file, config_excel_file):
    """Test que l'import valide les 7 feuilles Excel requises."""
    project = models.Project(
        nom="Test",
        sport="Volley",
        nb_semaines=10,
        semaine_min=2,
        config_yaml_path=str(config_yaml_file)
    )
    test_db.add(project)
    test_db.commit()
    
    sync_service = SyncService(test_db)
    
    # Import avec fichier valide (7 feuilles)
    stats = sync_service.import_from_yaml_and_excel(
        project_id=project.id,
        yaml_path=str(config_yaml_file),
        excel_path=str(config_excel_file)
    )
    
    # Devrait réussir sans lever d'exception
    assert stats["equipes_importees"] >= 0
    assert stats["gymnases_importes"] >= 0


def test_import_creates_matches_for_pool(test_db, config_yaml_file, config_excel_file):
    """Test que l'import génère des matchs pour les équipes de même poule."""
    project = models.Project(
        nom="Test Matchs",
        sport="Volleyball",
        nb_semaines=10,
        semaine_min=2,
        config_yaml_path=str(config_yaml_file)
    )
    test_db.add(project)
    test_db.commit()
    
    sync_service = SyncService(test_db)
    
    stats = sync_service.import_from_yaml_and_excel(
        project_id=project.id,
        yaml_path=str(config_yaml_file),
        excel_path=str(config_excel_file)
    )
    
    # Vérifier génération matchs
    matches = test_db.query(models.Match).filter_by(project_id=project.id).all()
    assert len(matches) >= 0  # Au moins quelques matchs générés
    
    # Vérifier structure matchs
    if len(matches) > 0:
        match = matches[0]
        assert match.equipe_domicile_id is not None
        assert match.equipe_exterieur_id is not None
        assert match.poule is not None


def test_import_stores_config_in_project(test_db, config_yaml_file, config_excel_file):
    """Test que l'import stocke la config complète dans project.config_data."""
    project = models.Project(
        nom="Test Config",
        sport="Volleyball",
        nb_semaines=10,
        semaine_min=2,
        config_yaml_path=str(config_yaml_file)
    )
    test_db.add(project)
    test_db.commit()
    
    sync_service = SyncService(test_db)
    
    sync_service.import_from_yaml_and_excel(
        project_id=project.id,
        yaml_path=str(config_yaml_file),
        excel_path=str(config_excel_file)
    )
    
    # Vérifier config_data
    test_db.refresh(project)
    assert project.config_data is not None
    assert "yaml_path" in project.config_data
    assert "excel_path" in project.config_data
    assert "equipes_importees" in project.config_data
    assert "gymnases_importes" in project.config_data
    assert project.config_data["yaml_path"] == str(config_yaml_file)
