#!/usr/bin/env python3
"""
Test des corrections du DataFormatter.

Ce script charge une solution existante et la re-formate
avec les corrections pour voir si les problèmes sont résolus.
"""

import json
from pathlib import Path
from core.solution_store import SolutionStore
from interface.core.validator import SolutionValidator, Severity

def test_corrections():
    """Test les corrections du formatter."""
    
    print("="*80)
    print("TEST DES CORRECTIONS DU DATA FORMATTER")
    print("="*80)
    
    # 1. Charger une solution v1.0 existante
    store = SolutionStore(solution_name="volley")
    
    print("\n📂 Chargement de la solution...")
    solution_data = store.load_latest()
    
    if not solution_data:
        print("❌ Aucune solution trouvée")
        return False
    
    print(f"✓ Solution chargée: {solution_data.get('metadata', {}).get('solution_name', 'unknown')}")
    
    # 2. Reconstruire la solution avec le formatter actuel
    print("\n🔄 Reconstruction avec formatter corrigé...")
    
    # Charger les objets depuis le store
    from core.models import Solution, Match, Equipe, Creneau
    
    # Extraire équipes
    equipes_data = solution_data.get("entities", {}).get("equipes", [])
    equipes = []
    for eq_data in equipes_data:
        equipe = Equipe(
            nom=eq_data["nom"],
            nom_complet=eq_data.get("nom_complet", eq_data["nom"]),
            institution=eq_data.get("institution", ""),
            numero_equipe=eq_data.get("numero_equipe", 1),
            genre=eq_data.get("genre", ""),
            poule=eq_data.get("poule", "")
        )
        equipe.id_unique = eq_data["id"]
        equipe.horaires_preferes = eq_data.get("horaires_preferes", [])
        equipes.append(equipe)
    
    print(f"  ✓ {len(equipes)} équipes extraites")
    
    # Reconstruire avec le nouveau formatter
    from interface.core.data_formatter import DataFormatter
    
    # Créer une solution minimale pour le test
    solution = Solution()
    solution.score = solution_data.get("metadata", {}).get("score", 0)
    solution.metadata = solution_data.get("metadata", {})
    
    # Reconstruire les matchs
    for match_data in solution_data.get("matches", {}).get("scheduled", []):
        # Trouver les équipes
        eq1 = next((e for e in equipes if e.id_unique == match_data["equipe1_id"]), None)
        eq2 = next((e for e in equipes if e.id_unique == match_data["equipe2_id"]), None)
        
        if eq1 and eq2:
            match = Match(eq1, eq2, match_data.get("poule", ""))
            
            if "semaine" in match_data:
                creneau = Creneau(
                    semaine=match_data["semaine"],
                    horaire=match_data["horaire"],
                    gymnase=match_data["gymnase"]
                )
                match.creneau = creneau
                match.metadata["is_fixed"] = match_data.get("is_fixed", False)
            
            solution.matchs_planifies.append(match)
    
    print(f"  ✓ {len(solution.matchs_planifies)} matchs reconstruits")
    
    # 3. Reformater avec le nouveau code
    print("\n🔨 Reformatage avec corrections...")
    new_data = DataFormatter.format_solution(
        solution=solution,
        equipes=equipes,
        gymnases=None,
        creneaux_disponibles=None
    )
    
    print(f"  ✓ Données reformatées")
    
    # 4. Valider
    print("\n🔍 Validation des données corrigées...")
    validator = SolutionValidator()
    is_valid, issues = validator.validate_full(new_data)
    
    # Statistiques
    errors = [i for i in issues if i.severity == Severity.ERROR]
    warnings = [i for i in issues if i.severity == Severity.WARNING]
    infos = [i for i in issues if i.severity == Severity.INFO]
    
    print(f"\n📊 RÉSULTATS")
    print("-" * 80)
    print(f"❌ Erreurs:         {len(errors):>5}")
    print(f"⚠️  Avertissements:  {len(warnings):>5}")
    print(f"ℹ️  Informations:    {len(infos):>5}")
    print("-" * 80)
    print(f"   TOTAL:          {len(issues):>5}")
    
    # Vérifier amélioration
    print("\n🎯 VÉRIFICATION DES CORRECTIONS")
    print("-" * 80)
    
    # 1. Genres
    genre_errors = [e for e in errors if "genre" in e.category.lower()]
    print(f"✓ Erreurs de genre:        {len(genre_errors):>5} (avant: ~52)")
    
    # 2. Slots
    slot_errors = [e for e in errors if "slot" in e.category.lower() or "slot_id" in e.message or "status" in e.message]
    print(f"✓ Erreurs de slots:        {len(slot_errors):>5} (avant: ~1365)")
    
    # 3. Total
    improvement = 1498 - len(errors)
    improvement_pct = (improvement / 1498) * 100 if 1498 > 0 else 0
    print(f"\n💡 Amélioration: -{improvement} erreurs ({improvement_pct:.1f}%)")
    
    # Sauvegarder pour inspection
    output_file = Path("test_output/corrected_solution_v2.json")
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Solution corrigée sauvegardée: {output_file}")
    
    if is_valid:
        print("\n✅ SUCCÈS - Solution valide !")
    else:
        print(f"\n⚠️  {len(errors)} erreur(s) restante(s)")
        
        # Afficher les premières erreurs
        if errors:
            print("\nPremières erreurs:")
            for issue in errors[:5]:
                print(f"  • {issue.category}: {issue.message[:60]}")
    
    return is_valid


if __name__ == "__main__":
    test_corrections()
