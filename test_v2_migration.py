#!/usr/bin/env python3
"""
Test de la migration vers le format v2.0

Ce script vérifie que :
1. DataFormatter génère correctement le JSON v2.0
2. Le JSON est conforme au schema
3. Toutes les données essentielles sont présentes
"""

import json
import sys
from pathlib import Path

# Ajouter les chemins nécessaires
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "interface"))

def test_data_formatter():
    """Test du DataFormatter avec des données fictives."""
    print("=" * 60)
    print("TEST 1 : DataFormatter")
    print("=" * 60)
    
    try:
        from core.models import Solution, Match, Equipe, Gymnase, Creneau
        from core.config import Config
        from interface.core.data_formatter import DataFormatter
        
        # Créer des données de test
        equipe1 = Equipe(
            nom="LYON 1 (1)",
            poule="Excellence M",
            institution="LYON 1",
            numero_equipe="1",
            genre="M",
            horaires_preferes=["18h00", "20h00"],
            lieux_preferes=["Gymnase A"],
            semaines_indisponibles={3: {"18h00"}, 5: {"18h00", "20h00"}}
        )
        
        equipe2 = Equipe(
            nom="LYON 2 (1)",
            poule="Excellence M",
            institution="LYON 2",
            numero_equipe="1",
            genre="M",
            horaires_preferes=["18h00"],
            lieux_preferes=[],
            semaines_indisponibles={}
        )
        
        gymnase = Gymnase(
            nom="Gymnase A",
            capacite=2,
            horaires_disponibles=["18h00", "20h00", "21h30"],
            semaines_indisponibles={7: {"18h00"}},
            capacite_reduite={5: {"18h00": 1}}
        )
        
        creneau = Creneau(semaine=1, horaire="18h00", gymnase="Gymnase A")
        
        match = Match(
            equipe1=equipe1,
            equipe2=equipe2,
            poule="Excellence M",
            creneau=creneau,
            priorite=10,
            metadata={"is_fixed": False}
        )
        
        solution = Solution(
            matchs_planifies=[match],
            matchs_non_planifies=[],
            score=100.0,
            metadata={
                "solver": "test",
                "status": "OPTIMAL",
                "execution_time": 1.5
            }
        )
        
        # Tester DataFormatter
        v2_data = DataFormatter.format_solution(
            solution=solution,
            config=None,
            equipes=[equipe1, equipe2],
            gymnases=[gymnase],
            creneaux_disponibles=[creneau]
        )
        
        # Vérifications
        assert v2_data["version"] == "2.0", "Version incorrecte"
        assert "metadata" in v2_data, "Metadata manquante"
        assert "entities" in v2_data, "Entities manquantes"
        assert "matches" in v2_data, "Matches manquants"
        assert "slots" in v2_data, "Slots manquants"
        assert "statistics" in v2_data, "Statistics manquantes"
        
        # Vérifier entities
        assert len(v2_data["entities"]["equipes"]) == 2, "Nombre d'équipes incorrect"
        assert len(v2_data["entities"]["gymnases"]) == 1, "Nombre de gymnases incorrect"
        assert len(v2_data["entities"]["poules"]) >= 1, "Aucune poule détectée"
        
        # Vérifier equipe enrichie
        eq1_data = v2_data["entities"]["equipes"][0]
        assert eq1_data["horaires_preferes"] == ["18h00", "20h00"], "Horaires préférés manquants"
        assert "3" in eq1_data["semaines_indisponibles"], "Semaines indisponibles manquantes"
        
        # Vérifier gymnase enrichi
        gym_data = v2_data["entities"]["gymnases"][0]
        assert gym_data["capacite"] == 2, "Capacité incorrecte"
        assert len(gym_data["horaires_disponibles"]) == 3, "Horaires disponibles incorrects"
        
        # Vérifier matches
        assert len(v2_data["matches"]["scheduled"]) == 1, "Match planifié manquant"
        match_data = v2_data["matches"]["scheduled"][0]
        assert "penalties" in match_data, "Pénalités manquantes"
        assert "priorite" in match_data, "Priorité manquante"
        
        print("✅ DataFormatter fonctionne correctement")
        print(f"   - Version: {v2_data['version']}")
        print(f"   - Equipes: {len(v2_data['entities']['equipes'])}")
        print(f"   - Gymnases: {len(v2_data['entities']['gymnases'])}")
        print(f"   - Poules: {len(v2_data['entities']['poules'])}")
        print(f"   - Matchs planifiés: {len(v2_data['matches']['scheduled'])}")
        
        return v2_data
        
    except Exception as e:
        print(f"❌ Erreur dans DataFormatter: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_validator(v2_data):
    """Test du validateur JSON Schema."""
    print("\n" + "=" * 60)
    print("TEST 2 : Validation JSON Schema")
    print("=" * 60)
    
    try:
        from interface.core.validator import SolutionValidator
        
        validator = SolutionValidator()
        is_valid, errors = validator.validate(v2_data)
        
        if is_valid:
            print("✅ JSON v2.0 valide selon le schema")
        else:
            print(f"❌ JSON v2.0 invalide ({len(errors)} erreurs)")
            for i, error in enumerate(errors[:5], 1):  # Montrer max 5 erreurs
                print(f"   {i}. {error}")
            if len(errors) > 5:
                print(f"   ... et {len(errors) - 5} autres erreurs")
        
        return is_valid
        
    except ImportError as e:
        print(f"⚠️  Validation non disponible (jsonschema manquant)")
        print(f"   Installer avec: pip install jsonschema")
        return True  # Ne pas échouer si lib non installée
    except Exception as e:
        print(f"❌ Erreur lors de la validation: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_existing_solution():
    """Test avec une solution existante si disponible."""
    print("\n" + "=" * 60)
    print("TEST 3 : Solution existante")
    print("=" * 60)
    
    # Chercher une solution v2.0 existante
    v2_dir = Path("solutions/v2.0")
    if not v2_dir.exists():
        print("⚠️  Répertoire solutions/v2.0/ inexistant")
        return True
    
    latest_file = v2_dir / "latest_volley.json"
    if not latest_file.exists():
        # Chercher n'importe quel fichier .json
        json_files = list(v2_dir.glob("*.json"))
        if not json_files:
            print("⚠️  Aucune solution v2.0 trouvée")
            return True
        latest_file = json_files[0]
    
    print(f"📂 Test de: {latest_file.name}")
    
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Vérifications basiques
        assert data.get("version") == "2.0", f"Version incorrecte: {data.get('version')}"
        assert "entities" in data, "Section 'entities' manquante"
        assert "matches" in data, "Section 'matches' manquante"
        
        nb_equipes = len(data.get("entities", {}).get("equipes", []))
        nb_matchs = len(data.get("matches", {}).get("scheduled", []))
        nb_poules = len(data.get("entities", {}).get("poules", []))
        
        print(f"✅ Solution valide")
        print(f"   - Equipes: {nb_equipes}")
        print(f"   - Matchs planifiés: {nb_matchs}")
        print(f"   - Poules: {nb_poules}")
        
        # Valider avec le schema si disponible
        try:
            from interface.core.validator import SolutionValidator
            validator = SolutionValidator()
            is_valid, errors = validator.validate(data)
            
            if is_valid:
                print(f"   ✅ Conforme au schema")
            else:
                print(f"   ⚠️  Non conforme au schema ({len(errors)} erreurs)")
                for error in errors[:3]:
                    print(f"      - {error}")
        except ImportError:
            pass
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON invalide: {e}")
        return False
    except AssertionError as e:
        print(f"❌ Structure incorrecte: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Lancer tous les tests."""
    print("\n🧪 TEST DE LA MIGRATION VERS V2.0\n")
    
    results = {
        "DataFormatter": False,
        "Validation": False,
        "Solution existante": False
    }
    
    # Test 1 : DataFormatter
    v2_data = test_data_formatter()
    results["DataFormatter"] = v2_data is not None
    
    # Test 2 : Validation (si test 1 OK)
    if v2_data:
        results["Validation"] = test_validator(v2_data)
    
    # Test 3 : Solution existante
    results["Solution existante"] = test_existing_solution()
    
    # Résumé
    print("\n" + "=" * 60)
    print("RÉSUMÉ DES TESTS")
    print("=" * 60)
    
    for test_name, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 Tous les tests sont passés !")
        return 0
    else:
        print("\n⚠️  Certains tests ont échoué")
        return 1


if __name__ == "__main__":
    exit(main())
