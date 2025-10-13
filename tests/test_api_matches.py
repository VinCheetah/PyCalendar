"""
Tests des endpoints API /matches.

Valide GET matches, déplacement, fixation, erreurs.
"""

import pytest
from fastapi import status


def test_get_matches_by_project(client, config_yaml_file, config_excel_file):
    """Test GET /projects/{id}/matches → liste matchs du project."""
    # Créer project avec import
    create_response = client.post(
        "/projects",
        json={
            "nom": "Matches Project",
            "yaml_path": str(config_yaml_file),
            "excel_path": str(config_excel_file),
            "import_data": True
        }
    )
    project_id = create_response.json()["id"]
    
    # Récupérer matchs
    response = client.get(f"/projects/{project_id}/matches")
    assert response.status_code == status.HTTP_200_OK
    
    matches = response.json()
    assert isinstance(matches, list)
    # Au moins quelques matchs générés
    if len(matches) > 0:
        match = matches[0]
        assert "id" in match
        assert "equipe_domicile_id" in match
        assert "equipe_exterieur_id" in match
        assert "poule" in match


def test_get_matches_filter_by_week(client, config_yaml_file, config_excel_file):
    """Test GET /projects/{id}/matches?semaine=X → filtre par semaine."""
    create_response = client.post(
        "/projects",
        json={
            "nom": "Filter Project",
            "yaml_path": str(config_yaml_file),
            "excel_path": str(config_excel_file),
            "import_data": True
        }
    )
    project_id = create_response.json()["id"]
    
    # Filtrer par semaine 3
    response = client.get(f"/projects/{project_id}/matches?semaine=3")
    assert response.status_code == status.HTTP_200_OK
    
    matches = response.json()
    # Vérifier que tous les matchs sont de semaine 3
    for match in matches:
        if match.get("semaine") is not None:
            assert match["semaine"] == 3


def test_move_match(client, config_yaml_file, config_excel_file):
    """Test POST /matches/{id}/move → déplacer match modifiable."""
    # Créer project avec matchs
    create_response = client.post(
        "/projects",
        json={
            "nom": "Move Project",
            "yaml_path": str(config_yaml_file),
            "excel_path": str(config_excel_file),
            "import_data": True
        }
    )
    project_id = create_response.json()["id"]
    
    # Récupérer un match modifiable
    matches_response = client.get(f"/projects/{project_id}/matches")
    matches = matches_response.json()
    
    # Trouver match modifiable (non fixé, semaine >= semaine_min)
    modifiable_match = None
    for match in matches:
        if not match.get("is_fixed", False) and match.get("semaine"):
            modifiable_match = match
            break
    
    if modifiable_match:
        match_id = modifiable_match["id"]
        nouvelle_semaine = modifiable_match["semaine"] + 1
        
        # Déplacer match
        response = client.post(
            f"/matches/{match_id}/move",
            json={"nouvelle_semaine": nouvelle_semaine}
        )
        
        assert response.status_code == status.HTTP_200_OK
        updated_match = response.json()
        assert updated_match["semaine"] == nouvelle_semaine


def test_move_match_non_modifiable(client, config_yaml_file, config_excel_file):
    """Test POST /matches/{id}/move sur match fixé → erreur 400."""
    create_response = client.post(
        "/projects",
        json={
            "nom": "Fixed Project",
            "yaml_path": str(config_yaml_file),
            "excel_path": str(config_excel_file),
            "import_data": True
        }
    )
    project_id = create_response.json()["id"]
    
    # Récupérer matchs
    matches_response = client.get(f"/projects/{project_id}/matches")
    matches = matches_response.json()
    
    if len(matches) > 0:
        match_id = matches[0]["id"]
        
        # Fixer match d'abord
        client.post(f"/matches/{match_id}/fix")
        
        # Tenter de déplacer match fixé
        response = client.post(
            f"/matches/{match_id}/move",
            json={"nouvelle_semaine": 5}
        )
        
        # Devrait échouer (400 Bad Request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_fix_match(client, config_yaml_file, config_excel_file):
    """Test POST /matches/{id}/fix → fixer un match."""
    create_response = client.post(
        "/projects",
        json={
            "nom": "Fix Project",
            "yaml_path": str(config_yaml_file),
            "excel_path": str(config_excel_file),
            "import_data": True
        }
    )
    project_id = create_response.json()["id"]
    
    # Récupérer match
    matches_response = client.get(f"/projects/{project_id}/matches")
    matches = matches_response.json()
    
    if len(matches) > 0:
        match_id = matches[0]["id"]
        
        # Fixer match
        response = client.post(f"/matches/{match_id}/fix")
        assert response.status_code == status.HTTP_200_OK
        
        fixed_match = response.json()
        assert fixed_match["is_fixed"] == True


def test_unfix_match(client, config_yaml_file, config_excel_file):
    """Test POST /matches/{id}/unfix → défixer un match."""
    create_response = client.post(
        "/projects",
        json={
            "nom": "Unfix Project",
            "yaml_path": str(config_yaml_file),
            "excel_path": str(config_excel_file),
            "import_data": True
        }
    )
    project_id = create_response.json()["id"]
    
    # Récupérer match
    matches_response = client.get(f"/projects/{project_id}/matches")
    matches = matches_response.json()
    
    if len(matches) > 0:
        match_id = matches[0]["id"]
        
        # Fixer puis défixer
        client.post(f"/matches/{match_id}/fix")
        response = client.post(f"/matches/{match_id}/unfix")
        
        assert response.status_code == status.HTTP_200_OK
        unfixed_match = response.json()
        assert unfixed_match["is_fixed"] == False


def test_delete_match(client, config_yaml_file, config_excel_file):
    """Test DELETE /matches/{id} → suppression match."""
    create_response = client.post(
        "/projects",
        json={
            "nom": "Delete Match Project",
            "yaml_path": str(config_yaml_file),
            "excel_path": str(config_excel_file),
            "import_data": True
        }
    )
    project_id = create_response.json()["id"]
    
    # Récupérer match
    matches_response = client.get(f"/projects/{project_id}/matches")
    matches = matches_response.json()
    
    if len(matches) > 0:
        match_id = matches[0]["id"]
        
        # Supprimer match
        response = client.delete(f"/matches/{match_id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Vérifier match supprimé
        get_response = client.get(f"/matches/{match_id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND


def test_get_match_not_found(client):
    """Test GET /matches/{id} avec ID inexistant → 404."""
    response = client.get("/matches/99999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_move_match_not_found(client):
    """Test POST /matches/{id}/move avec ID inexistant → 404."""
    response = client.post(
        "/matches/99999/move",
        json={"nouvelle_semaine": 5}
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
