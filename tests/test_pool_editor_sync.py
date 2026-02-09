#!/usr/bin/env python3
"""
Tests unitaires pour le module pool_editor_sync.

Usage:
    pytest tests/test_pool_editor_sync.py
    python -m pytest tests/test_pool_editor_sync.py -v
"""

import pytest
import json
import pandas as pd
from pathlib import Path
import tempfile
import shutil

# Import du module à tester
import sys
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from pycalendar.cli.pool_editor_sync import (
    EquipeData,
    PoolEditorSyncError,
    charger_equipes_depuis_json,
    charger_equipes_depuis_excel,
    comparer_equipes,
    synchroniser_equipes_depuis_json,
)


# ==================== FIXTURES ====================

@pytest.fixture
def json_test_simple():
    """Crée un fichier JSON de test simple."""
    data = {
        "teams": [
            {
                "nom": "LYON 1 (1)",
                "genre": "F",
                "niveau": "A1",
                "horaire": "14H",
                "institution": "LYON 1",
                "poule": "VBFA1PA"
            },
            {
                "nom": "PARIS (1)",
                "genre": "M",
                "niveau": "A2",
                "horaire": "16H",
                "institution": "PARIS",
                "poule": None
            }
        ],
        "pools": [],
        "settings": {"sport": "volleyball", "prefix": "VB"}
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump(data, f)
        temp_path = Path(f.name)
    
    yield temp_path
    temp_path.unlink()


@pytest.fixture
def excel_test_simple():
    """Crée un fichier Excel de test simple."""
    data = {
        'Equipe': ['LYON 1 (1)', 'INSA (1)', 'LYON 2 (1)'],
        'Niveau_Equipe': ['A1', 'A1', 'A2'],
        'Genre_Equipe': ['F', 'M', 'F'],
        'Poule': ['VBFA1PA', 'VBMA1PA', 'VBFA2PA'],
        'Horaire_Prefere': ['14:00', '16:00', '18:00'],
        'Responsable_Nom': ['MARTIN', 'DUPONT', 'DURAND'],
        'Responsable_Email': ['martin@test.fr', 'dupont@test.fr', 'durand@test.fr']
    }
    df = pd.DataFrame(data)
    
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        temp_path = Path(f.name)
    
    df.to_excel(temp_path, sheet_name='Equipes', index=False)
    
    yield temp_path
    temp_path.unlink()


# ==================== TESTS EQUIPE DATA ====================

def test_equipe_data_creation():
    """Test la création d'un objet EquipeData."""
    equipe = EquipeData(
        nom="LYON 1 (1)",
        niveau="A1",
        genre="F",
        poule="VBFA1PA",
        horaire="14H",
        institution="LYON 1"
    )
    
    assert equipe.nom == "LYON 1 (1)"
    assert equipe.niveau == "A1"
    assert equipe.genre == "F"
    assert equipe.poule == "VBFA1PA"
    assert equipe.horaire == "14H"
    assert equipe.institution == "LYON 1"


def test_equipe_data_to_dict():
    """Test la conversion d'EquipeData en dictionnaire."""
    equipe = EquipeData(
        nom="LYON 1 (1)",
        niveau="A1",
        genre="F",
        poule="VBFA1PA",
        horaire="14H",
        institution="LYON 1"
    )
    
    result = equipe.to_dict()
    
    assert result['Equipe'] == "LYON 1 (1)"
    assert result['Niveau_Equipe'] == "A1"
    assert result['Genre_Equipe'] == "F"
    assert result['Poule'] == "VBFA1PA"
    assert result['Horaire_Prefere'] == "14:00"  # Conversion 14H → 14:00


def test_equipe_data_horaire_conversion():
    """Test la conversion des formats d'horaire."""
    # Test avec format Pool Editor (14H)
    equipe1 = EquipeData("TEST (1)", "A1", "F", None, "14H", "TEST")
    assert equipe1.to_dict()['Horaire_Prefere'] == "14:00"
    
    equipe2 = EquipeData("TEST (1)", "A1", "F", None, "20H", "TEST")
    assert equipe2.to_dict()['Horaire_Prefere'] == "20:00"
    
    # Test sans horaire
    equipe3 = EquipeData("TEST (1)", "A1", "F", None, None, "TEST")
    assert equipe3.to_dict()['Horaire_Prefere'] == ""


# ==================== TESTS CHARGEMENT JSON ====================

def test_charger_json_valide(json_test_simple):
    """Test le chargement d'un fichier JSON valide."""
    equipes, poules = charger_equipes_depuis_json(json_test_simple)
    
    assert len(equipes) == 2
    assert equipes[0].nom == "LYON 1 (1)"
    assert equipes[0].genre == "F"
    assert equipes[1].nom == "PARIS (1)"
    assert equipes[1].poule is None


def test_charger_json_inexistant():
    """Test le chargement d'un fichier JSON inexistant."""
    with pytest.raises(PoolEditorSyncError):
        charger_equipes_depuis_json(Path("fichier_inexistant.json"))


def test_charger_json_invalide():
    """Test le chargement d'un fichier JSON mal formaté."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("{ invalid json }")
        temp_path = Path(f.name)
    
    try:
        with pytest.raises(PoolEditorSyncError):
            charger_equipes_depuis_json(temp_path)
    finally:
        temp_path.unlink()


def test_charger_json_sans_teams():
    """Test le chargement d'un JSON sans clé 'teams'."""
    data = {"pools": [], "settings": {}}
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump(data, f)
        temp_path = Path(f.name)
    
    try:
        with pytest.raises(PoolEditorSyncError) as exc_info:
            charger_equipes_depuis_json(temp_path)
        assert "teams" in str(exc_info.value)
    finally:
        temp_path.unlink()


# ==================== TESTS CHARGEMENT EXCEL ====================

def test_charger_excel_valide(excel_test_simple):
    """Test le chargement d'un fichier Excel valide."""
    df = charger_equipes_depuis_excel(excel_test_simple)
    
    assert len(df) == 3
    assert 'Equipe' in df.columns
    assert 'Niveau_Equipe' in df.columns
    assert df.iloc[0]['Equipe'] == 'LYON 1 (1)'


def test_charger_excel_inexistant():
    """Test le chargement d'un fichier Excel inexistant."""
    with pytest.raises(PoolEditorSyncError):
        charger_equipes_depuis_excel(Path("fichier_inexistant.xlsx"))


def test_charger_excel_feuille_inexistante(excel_test_simple):
    """Test le chargement avec un nom de feuille incorrect."""
    with pytest.raises(PoolEditorSyncError):
        charger_equipes_depuis_excel(excel_test_simple, sheet_name="FeuilleBidon")


# ==================== TESTS COMPARAISON ====================

def test_comparer_equipes_ajout(json_test_simple, excel_test_simple):
    """Test la détection d'équipes à ajouter."""
    equipes_json, _ = charger_equipes_depuis_json(json_test_simple)
    df_excel = charger_equipes_depuis_excel(excel_test_simple)
    
    a_ajouter, a_supprimer, a_modifier = comparer_equipes(equipes_json, df_excel)
    
    # PARIS (1) est dans le JSON mais pas dans l'Excel
    assert len(a_ajouter) == 1
    assert a_ajouter[0].nom == "PARIS (1)"


def test_comparer_equipes_suppression(json_test_simple, excel_test_simple):
    """Test la détection d'équipes à supprimer."""
    equipes_json, _ = charger_equipes_depuis_json(json_test_simple)
    df_excel = charger_equipes_depuis_excel(excel_test_simple)
    
    a_ajouter, a_supprimer, a_modifier = comparer_equipes(equipes_json, df_excel)
    
    # INSA (1) et LYON 2 (1) sont dans l'Excel mais pas dans le JSON
    assert len(a_supprimer) == 2
    assert "INSA (1)" in a_supprimer
    assert "LYON 2 (1)" in a_supprimer


def test_comparer_equipes_aucune_modification():
    """Test quand aucune modification n'est nécessaire."""
    # Créer des équipes identiques
    equipes_json = [
        EquipeData("LYON 1 (1)", "A1", "F", "VBFA1PA", "14H", "LYON 1")
    ]
    
    df_excel = pd.DataFrame({
        'Equipe': ['LYON 1 (1)'],
        'Niveau_Equipe': ['A1'],
        'Genre_Equipe': ['F'],
        'Poule': ['VBFA1PA'],
        'Horaire_Prefere': ['14:00']
    })
    
    a_ajouter, a_supprimer, a_modifier = comparer_equipes(equipes_json, df_excel)
    
    assert len(a_ajouter) == 0
    assert len(a_supprimer) == 0
    assert len(a_modifier) == 0


# ==================== TESTS SYNCHRONISATION ====================

def test_synchronisation_mode_update(json_test_simple, excel_test_simple):
    """Test la synchronisation en mode update."""
    # Créer une copie temporaire de l'Excel
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        temp_excel = Path(f.name)
    shutil.copy(excel_test_simple, temp_excel)
    
    try:
        stats = synchroniser_equipes_depuis_json(
            json_path=str(json_test_simple),
            excel_path=str(temp_excel),
            mode='update',
            backup=False
        )
        
        # Vérifier les stats
        # Mode update: PARIS (1) est ajouté, LYON 1 (1) est modifié (mise à jour)
        # INSA (1) et LYON 2 (1) sont conservés (pas dans le JSON mais pas supprimés)
        assert stats['ajoutees'] == 1  # PARIS (1)
        assert stats['modifiees'] == 1  # LYON 1 (1) est mis à jour
        assert stats['supprimees'] == 0
        assert stats['conservees'] == 2  # INSA (1) et LYON 2 (1)
        
    finally:
        temp_excel.unlink()


def test_synchronisation_mode_sync(json_test_simple, excel_test_simple):
    """Test la synchronisation en mode sync."""
    # Créer une copie temporaire de l'Excel
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        temp_excel = Path(f.name)
    shutil.copy(excel_test_simple, temp_excel)
    
    try:
        stats = synchroniser_equipes_depuis_json(
            json_path=str(json_test_simple),
            excel_path=str(temp_excel),
            mode='sync',
            backup=False
        )
        
        # Vérifier les stats
        # Mode sync (=replace): remplace tout le contenu
        # LYON 1 (1) existait → modifiée (données supplémentaires préservées)
        # PARIS (1) est nouvelle → ajoutée
        # INSA (1) et LYON 2 (1) → supprimées (pas dans le JSON)
        assert stats['ajoutees'] == 1  # PARIS (1)
        assert stats['modifiees'] == 1  # LYON 1 (1) existait et est préservée avec données supp.
        assert stats['supprimees'] == 2  # INSA (1) et LYON 2 (1)
        assert stats['conservees'] == 0
        
    finally:
        temp_excel.unlink()


def test_synchronisation_avec_backup(json_test_simple, excel_test_simple):
    """Test que la sauvegarde est bien créée."""
    # Créer une copie temporaire de l'Excel
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        temp_excel = Path(f.name)
    shutil.copy(excel_test_simple, temp_excel)
    
    try:
        stats = synchroniser_equipes_depuis_json(
            json_path=str(json_test_simple),
            excel_path=str(temp_excel),
            mode='update',
            backup=True
        )
        
        # Vérifier que le backup existe
        assert stats['backup_path'] is not None
        backup_path = Path(stats['backup_path'])
        assert backup_path.exists()
        
        # Nettoyer le backup
        backup_path.unlink()
        
    finally:
        temp_excel.unlink()


# ==================== TESTS ERREURS ====================

def test_synchronisation_excel_colonnes_manquantes():
    """Test l'erreur quand des colonnes sont manquantes dans l'Excel."""
    # Créer un Excel incomplet
    data = {
        'Equipe': ['LYON 1 (1)'],
        'Niveau_Equipe': ['A1']
        # Manque Genre_Equipe, Poule, Horaire_Prefere
    }
    df = pd.DataFrame(data)
    
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        temp_excel = Path(f.name)
    df.to_excel(temp_excel, sheet_name='Equipes', index=False)
    
    # Créer un JSON simple
    json_data = {
        "teams": [{"nom": "TEST (1)", "genre": "F", "niveau": "A1", 
                   "horaire": "14H", "institution": "TEST", "poule": None}],
        "pools": [], "settings": {}
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump(json_data, f)
        temp_json = Path(f.name)
    
    try:
        with pytest.raises(PoolEditorSyncError) as exc_info:
            synchroniser_equipes_depuis_json(
                json_path=str(temp_json),
                excel_path=str(temp_excel),
                backup=False
            )
        assert "manquantes" in str(exc_info.value).lower()
        
    finally:
        temp_excel.unlink()
        temp_json.unlink()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
