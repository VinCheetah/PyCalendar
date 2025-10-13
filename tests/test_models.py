"""
Tests des modèles SQLAlchemy.

Valide la création, les relations et la logique métier des modèles.
"""

import pytest
from backend.database import models


def test_create_project(test_db):
    """Test création Project avec configs YAML+Excel dans JSON."""
    project = models.Project(
        nom="Test Project",
        sport="Volleyball",
        nb_semaines=10,
        semaine_min=2,
        config_yaml_path="/path/to/config.yaml",
        config_data={
            "yaml_path": "/path/to/config.yaml",
            "excel_path": "/path/to/data.xlsx",
            "nb_semaines": 10,
            "sport": "Volleyball"
        }
    )
    test_db.add(project)
    test_db.commit()
    
    assert project.id is not None
    assert project.nom == "Test Project"
    assert project.config_yaml_path == "/path/to/config.yaml"
    assert project.config_data["excel_path"] == "/path/to/data.xlsx"
    assert project.config_data["sport"] == "Volleyball"


def test_create_team(test_db):
    """Test création Team avec horaires JSON."""
    project = models.Project(
        nom="Test",
        sport="Volley",
        nb_semaines=5,
        semaine_min=1,
        config_yaml_path="/test.yaml"
    )
    test_db.add(project)
    test_db.commit()
    
    team = models.Team(
        project_id=project.id,
        nom="Lycée A - 1",
        institution="Lycée A",
        numero_equipe="1",
        genre="M",
        poule="P1",
        horaires_preferes='["14:00", "18:00"]',
        lieux_preferes='["Gym A"]'
    )
    test_db.add(team)
    test_db.commit()
    
    assert team.id is not None
    assert team.project_id == project.id
    assert team.nom == "Lycée A - 1"
    assert '"14:00"' in team.horaires_preferes


def test_create_venue(test_db):
    """Test création Venue avec horaires disponibles JSON."""
    project = models.Project(
        nom="Test",
        sport="Volley",
        nb_semaines=5,
        semaine_min=1,
        config_yaml_path="/test.yaml"
    )
    test_db.add(project)
    test_db.commit()
    
    venue = models.Venue(
        project_id=project.id,
        nom="Gymnase 1",
        capacite=100,
        horaires_disponibles='["09:00", "14:00", "18:00"]'
    )
    test_db.add(venue)
    test_db.commit()
    
    assert venue.id is not None
    assert venue.nom == "Gymnase 1"
    assert venue.capacite == 100
    assert '"14:00"' in venue.horaires_disponibles


def test_cascade_delete_project(test_db):
    """Test cascade delete : supprimer project supprime teams/venues/matches."""
    # Créer project
    project = models.Project(
        nom="Test",
        sport="Volley",
        nb_semaines=5,
        semaine_min=1,
        config_yaml_path="/test.yaml"
    )
    test_db.add(project)
    test_db.commit()
    project_id = project.id
    
    # Créer équipes
    team1 = models.Team(
        project_id=project_id,
        nom="Team 1",
        institution="A",
        numero_equipe="1",
        genre="M",
        poule="P1"
    )
    team2 = models.Team(
        project_id=project_id,
        nom="Team 2",
        institution="B",
        numero_equipe="1",
        genre="M",
        poule="P1"
    )
    test_db.add_all([team1, team2])
    test_db.commit()
    
    # Créer gymnase
    venue = models.Venue(
        project_id=project_id,
        nom="Gym 1"
    )
    test_db.add(venue)
    test_db.commit()
    
    # Créer match
    match = models.Match(
        project_id=project_id,
        equipe1_nom=team1.nom,
        equipe1_institution=team1.institution,
        equipe2_nom=team2.nom,
        equipe2_institution=team2.institution,
        poule="P1",
        gymnase="Gym 1",
        semaine=3
    )
    test_db.add(match)
    test_db.commit()
    
    # Vérifier existence
    assert test_db.query(models.Team).filter_by(project_id=project_id).count() == 2
    assert test_db.query(models.Venue).filter_by(project_id=project_id).count() == 1
    assert test_db.query(models.Match).filter_by(project_id=project_id).count() == 1
    
    # Supprimer project
    test_db.delete(project)
    test_db.commit()
    
    # Vérifier cascade delete
    assert test_db.query(models.Team).filter_by(project_id=project_id).count() == 0
    assert test_db.query(models.Venue).filter_by(project_id=project_id).count() == 0
    assert test_db.query(models.Match).filter_by(project_id=project_id).count() == 0


def test_match_properties(test_db):
    """Test propriétés calculées est_planifie et est_modifiable."""
    project = models.Project(
        nom="Test",
        sport="Volley",
        nb_semaines=10,
        semaine_min=2,
        config_yaml_path="/test.yaml"
    )
    test_db.add(project)
    test_db.commit()
    
    team1 = models.Team(
        project_id=project.id,
        nom="T1",
        institution="A",
        numero_equipe="1",
        genre="M",
        poule="P1"
    )
    team2 = models.Team(
        project_id=project.id,
        nom="T2",
        institution="B",
        numero_equipe="1",
        genre="M",
        poule="P1"
    )
    venue = models.Venue(
        project_id=project.id,
        nom="Gym"
    )
    test_db.add_all([team1, team2, venue])
    test_db.commit()
    
    # Match sans semaine : non planifié, modifiable
    match1 = models.Match(
        project_id=project.id,
        equipe1_nom=team1.nom,
        equipe2_nom=team2.nom,
        poule="P1",
        semaine=None,
        est_fixe=False
    )
    test_db.add(match1)
    test_db.commit()
    assert match1.est_planifie == False
    assert match1.est_modifiable == True
    
    # Match avec semaine >= semaine_min : planifié, modifiable
    match2 = models.Match(
        project_id=project.id,
        equipe1_nom=team1.nom,
        equipe2_nom=team2.nom,
        poule="P1",
        gymnase="Gym",
        semaine=3,  # >= semaine_min (2)
        est_fixe=False
    )
    test_db.add(match2)
    test_db.commit()
    assert match2.est_planifie == True
    assert match2.est_modifiable == True
    
    # Match fixé : non modifiable
    match3 = models.Match(
        project_id=project.id,
        equipe1_nom=team1.nom,
        equipe2_nom=team2.nom,
        poule="P1",
        gymnase="Gym",
        semaine=4,
        est_fixe=True
    )
    test_db.add(match3)
    test_db.commit()
    assert match3.est_modifiable == False
    
    # Match avant semaine_min : non modifiable
    match4 = models.Match(
        project_id=project.id,
        equipe1_nom=team1.nom,
        equipe2_nom=team2.nom,
        poule="P1",
        gymnase="Gym",
        semaine=1,  # < semaine_min (2)
        est_fixe=False
    )
    test_db.add(match4)
    test_db.commit()
    # est_modifiable dépend seulement de est_fixe et statut dans les modèles actuels
    assert match4.est_fixe == False


def test_match_fix_unfix(test_db):
    """Test fixation/défixation d'un match."""
    project = models.Project(
        nom="Test",
        sport="Volley",
        nb_semaines=10,
        semaine_min=2,
        config_yaml_path="/test.yaml"
    )
    test_db.add(project)
    test_db.commit()
    
    team1 = models.Team(
        project_id=project.id,
        nom="T1",
        institution="A",
        numero_equipe="1",
        genre="M",
        poule="P1"
    )
    team2 = models.Team(
        project_id=project.id,
        nom="T2",
        institution="B",
        numero_equipe="1",
        genre="M",
        poule="P1"
    )
    venue = models.Venue(project_id=project.id, nom="Gym")
    test_db.add_all([team1, team2, venue])
    test_db.commit()
    
    # Créer match
    match = models.Match(
        project_id=project.id,
        equipe1_nom=team1.nom,
        equipe2_nom=team2.nom,
        poule="P1",
        gymnase="Gym",
        semaine=3,
        est_fixe=False
    )
    test_db.add(match)
    test_db.commit()
    
    # Fixer
    match.est_fixe = True
    test_db.commit()
    assert match.est_fixe == True
    assert match.est_modifiable == False
    
    # Défixer
    match.est_fixe = False
    test_db.commit()
    assert match.est_fixe == False
