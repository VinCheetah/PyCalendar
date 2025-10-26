#!/usr/bin/env python3
"""
Test de démonstration du système de validation v2.0.

Ce script montre comment :
1. Utiliser le validateur programmatiquement
2. Filtrer les issues par sévérité/catégorie
3. Générer des rapports personnalisés
"""

import json
from pathlib import Path
from interface.core.validator import SolutionValidator, Severity

def demo_validation():
    """Démonstration complète du système de validation."""
    
    print("="*80)
    print("DÉMONSTRATION - Système de Validation PyCalendar")
    print("="*80)
    
    # 1. Charger une solution
    solution_file = Path("solutions/latest_volley.json")
    
    if not solution_file.exists():
        solution_file = Path("output/latest_volley.json")
    
    if not solution_file.exists():
        print("❌ Aucun fichier de solution trouvé")
        return
    
    print(f"\n📂 Chargement: {solution_file}")
    
    with open(solution_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 2. Valider
    print(f"\n🔍 Validation en cours...")
    validator = SolutionValidator()
    is_valid, issues = validator.validate_full(data)
    
    # 3. Statistiques par sévérité
    print(f"\n📊 STATISTIQUES PAR SÉVÉRITÉ")
    print("-" * 80)
    
    errors = [i for i in issues if i.severity == Severity.ERROR]
    warnings = [i for i in issues if i.severity == Severity.WARNING]
    infos = [i for i in issues if i.severity == Severity.INFO]
    
    print(f"❌ Erreurs:         {len(errors):>5}")
    print(f"⚠️  Avertissements:  {len(warnings):>5}")
    print(f"ℹ️  Informations:    {len(infos):>5}")
    print(f"{'─'*80}")
    print(f"   TOTAL:          {len(issues):>5}")
    
    # 4. Statistiques par catégorie
    print(f"\n📁 STATISTIQUES PAR CATÉGORIE")
    print("-" * 80)
    
    from collections import defaultdict
    by_category = defaultdict(list)
    for issue in issues:
        by_category[issue.category].append(issue)
    
    for category in sorted(by_category.keys()):
        count = len(by_category[category])
        errors_count = sum(1 for i in by_category[category] if i.severity == Severity.ERROR)
        warnings_count = sum(1 for i in by_category[category] if i.severity == Severity.WARNING)
        infos_count = sum(1 for i in by_category[category] if i.severity == Severity.INFO)
        
        print(f"{category:20} : {count:>4} (❌{errors_count:>3} ⚠️{warnings_count:>3} ℹ️{infos_count:>3})")
    
    # 5. Top 5 des erreurs les plus fréquentes
    print(f"\n🔥 TOP 5 DES ERREURS LES PLUS FRÉQUENTES")
    print("-" * 80)
    
    from collections import Counter
    error_messages = [e.message for e in errors]
    top_errors = Counter(error_messages).most_common(5)
    
    for i, (msg, count) in enumerate(top_errors, 1):
        # Tronquer le message si trop long
        display_msg = msg[:60] + "..." if len(msg) > 60 else msg
        print(f"{i}. {display_msg:65} ({count}×)")
    
    # 6. Exemples d'erreurs critiques
    print(f"\n⚠️  EXEMPLES D'ERREURS CRITIQUES")
    print("-" * 80)
    
    # Double occupation
    double_occ = [e for e in errors if "Double occupation" in e.message]
    if double_occ:
        print(f"\n🚫 Doubles occupations détectées: {len(double_occ)}")
        for issue in double_occ[:3]:
            print(f"   • {issue.message} @ {issue.location}")
    
    # Matchs inter-genres
    inter_genre = [e for e in errors if "genres différents" in e.message]
    if inter_genre:
        print(f"\n⚧️  Matchs inter-genres détectés: {len(inter_genre)}")
        for issue in inter_genre[:3]:
            print(f"   • {issue.location}")
    
    # Violations d'indisponibilités
    indispo = [e for e in errors if "indisponible" in e.message]
    if indispo:
        print(f"\n📅 Violations d'indisponibilités: {len(indispo)}")
        for issue in indispo[:3]:
            print(f"   • {issue.message} @ {issue.location}")
    
    # 7. Résultat final
    print(f"\n{'='*80}")
    if is_valid:
        print("✅ SOLUTION VALIDE - Aucune erreur bloquante")
    else:
        print(f"❌ SOLUTION INVALIDE - {len(errors)} erreur(s) à corriger")
    print(f"{'='*80}")
    
    # 8. Rapport complet (optionnel)
    print(f"\n💡 Pour voir le rapport complet:")
    print(f"   python validate_solution.py {solution_file} --verbose")
    
    return is_valid, issues


if __name__ == "__main__":
    demo_validation()
