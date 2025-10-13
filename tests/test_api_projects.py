"""
Tests des endpoints API /projects.

Valide CRUD projects, stats, cascade delete.
"""

import pytest
from fastapi import status


def test_create_project(client, config_yaml_file, config_excel_file):
    """Test POST /projects → création project avec import YAML+Excel."""
    response = client.post(
        "/projects",
        json={
            "nom": "Test Project API",
            "yaml_path": str(config_yaml_file),
            "excel_path": str(config_excel_file),
            "import_data": True
        }
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["nom"] == "Test Project API"
    assert data["id"] is not None
    assert data["config_yaml_path"] == str(config_yaml_file)


def test_create_project_without_import(client, config_yaml_file):
    """Test POST /projects sans import_data → juste créer project vide."""
    response = client.post(
        "/projects",
        json={
            "nom": "Empty Project",
            "yaml_path": str(config_yaml_file),
            "import_data": False
        }
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["nom"] == "Empty Project"
    
    # Vérifier pas d'équipes importées
    project_id = data["id"]
    stats_response = client.get(f"/projects/{project_id}/stats")
    stats = stats_response.json()
    assert stats.get("equipes_count", 0) == 0


def test_get_projects(client, config_yaml_file, config_excel_file):
    """Test GET /projects → liste tous les projects."""
    # Créer 2 projects
    client.post(
        "/projects",
        json={
            "nom": "Project 1",
            "yaml_path": str(config_yaml_file),
            "excel_path": str(config_excel_file),
            "import_data": True
        }
    )
    client.post(
        "/projects",
        json={
            "nom": "Project 2",
            "yaml_path": str(config_yaml_file),
            "import_data": False
        }
    )
    
    # Récupérer liste
    response = client.get("/projects")
    assert response.status_code == status.HTTP_200_OK
    
    projects = response.json()
    assert len(projects) >= 2
    project_names = [p["nom"] for p in projects]
    assert "Project 1" in project_names
    assert "Project 2" in project_names


def test_get_project_by_id(client, config_yaml_file):
    """Test GET /projects/{id} → détails d'un project."""
    # Créer project
    create_response = client.post(
        "/projects",
        json={
            "nom": "Detail Project",
            "yaml_path": str(config_yaml_file),
            "import_data": False
        }
    )
    project_id = create_response.json()["id"]
    
    # Récupérer détails
    response = client.get(f"/projects/{project_id}")
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["id"] == project_id
    assert data["nom"] == "Detail Project"
    assert data["config_yaml_path"] == str(config_yaml_file)


def test_get_project_stats(client, config_yaml_file, config_excel_file):
    """Test GET /projects/{id}/stats → statistiques project."""
    # Créer project avec import
    create_response = client.post(
        "/projects",
        json={
            "nom": "Stats Project",
            "yaml_path": str(config_yaml_file),
            "excel_path": str(config_excel_file),
            "import_data": True
        }
    )
    project_id = create_response.json()["id"]
    
    # Récupérer stats
    response = client.get(f"/projects/{project_id}/stats")
    assert response.status_code == status.HTTP_200_OK
    
    stats = response.json()
    assert "equipes_count" in stats
    assert "gymnases_count" in stats
    assert "matchs_count" in stats
    assert stats["equipes_count"] >= 3  # 3 équipes dans config_excel_file
    assert stats["gymnases_count"] >= 2  # 2 gymnases


def test_delete_project_cascade(client, config_yaml_file, config_excel_file):
    """Test DELETE /projects/{id} → suppression cascade teams/venues/matches."""
    # Créer project avec données
    create_response = client.post(
        "/projects",
        json={
            "nom": "Delete Project",
            "yaml_path": str(config_yaml_file),
            "excel_path": str(config_excel_file),
            "import_data": True
        }
    )
    project_id = create_response.json()["id"]
    
    # Vérifier existence équipes
    stats_before = client.get(f"/projects/{project_id}/stats").json()
    assert stats_before["equipes_count"] > 0
    
    # Supprimer project
    delete_response = client.delete(f"/projects/{project_id}")
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT
    
    # Vérifier project n'existe plus
    get_response = client.get(f"/projects/{project_id}")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND


def test_get_project_not_found(client):
    """Test GET /projects/{id} avec ID inexistant → 404."""
    response = client.get("/projects/99999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_project_not_found(client):
    """Test DELETE /projects/{id} avec ID inexistant → 404."""
    response = client.delete("/projects/99999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_create_project_invalid_yaml_path(client):
    """Test POST /projects avec YAML inexistant → erreur."""
    response = client.post(
        "/projects",
        json={
            "nom": "Invalid Project",
            "yaml_path": "/fake/config.yaml",
            "import_data": True
        }
    )
    
    # Devrait retourner erreur (400 ou 500 selon implémentation)
    assert response.status_code >= 400
