#!/usr/bin/env python3
"""
Validation automatique des structures de données après chargement.

Ce script peut être appelé pour vérifier la cohérence des données
à n'importe quel moment du pipeline.

Usage:
    python validate_data.py                    # Valide les données du fichier par défaut
    python validate_data.py config.yaml        # Valide avec une config spécifique
    python validate_data.py --solution latest  # Valide une solution sauvegardée
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pycalendar.core.config import Config
from pycalendar.core.data_schema import validate_all, print_validation_report
from pycalendar.data.data_source import DataSource


def validate_from_config(config_path: str):
    """Valide les données chargées depuis un fichier de configuration."""
    print("=" * 80)
    print(f"VALIDATION DES DONNÉES: {config_path}")
    print("=" * 80)
    
    # Charger config
    config = Config.from_yaml(config_path)
    print(f"\n📂 Fichier de données: {config.fichier_donnees}")
    
    # Charger données
    source = DataSource(config.fichier_donnees)
    
    print("\n📊 Chargement des données...")
    equipes = source.charger_equipes()
    print(f"   ✓ {len(equipes)} équipes chargées")
    
    gymnases = source.charger_gymnases()
    print(f"   ✓ {len(gymnases)} gymnases chargés")
    
    # Valider
    print("\n🔍 Validation des structures...")
    results = validate_all(equipes=equipes, gymnases=gymnases)
    
    print()
    print_validation_report(results)
    
    # Retourner code sortie
    total_errors = sum(len(errors) for errors in results.values())
    return 0 if total_errors == 0 else 1


def validate_solution(solution_file: str):
    """Valide une solution sauvegardée."""
    print("=" * 80)
    print(f"VALIDATION DE SOLUTION: {solution_file}")
    print("=" * 80)
    
    import json
    from pycalendar.core.models import Solution, Match, Equipe, Creneau
    
    # Charger solution
    with open(solution_file, 'r') as f:
        data = json.load(f)
    
    # Reconstruire objets (version simplifiée)
    # Dans un vrai cas, utiliser SolutionStore
    print(f"\n📊 Solution chargée: {len(data.get('matchs_planifies', []))} matchs planifiés")
    
    # TODO: Implémenter désérialisation complète et validation
    print("\n⚠️  Validation de solution non encore implémentée")
    print("   (nécessite désérialisation complète)")
    
    return 0


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(description="Valide les structures de données PyCalendar")
    parser.add_argument("config", nargs="?", default="configs/default.yaml",
                       help="Fichier de configuration ou solution à valider")
    parser.add_argument("--solution", action="store_true",
                       help="Valider une solution au lieu des données d'entrée")
    
    args = parser.parse_args()
    
    try:
        if args.solution:
            return validate_solution(args.config)
        else:
            return validate_from_config(args.config)
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
