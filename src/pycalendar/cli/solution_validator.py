#!/usr/bin/env python3
"""
Script de validation de solutions PyCalendar.

Usage:
    python validate_solution.py <solution_file.json>
    python validate_solution.py solutions/latest_volley.json
    python validate_solution.py --all  # Valider tous les fichiers dans solutions/
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from pycalendar.interface.core.validator import SolutionValidator, Severity


def validate_file(file_path: Path, verbose: bool = False) -> bool:
    """
    Validate a single solution file.
    
    Args:
        file_path: Path to solution JSON file
        verbose: Show detailed report
        
    Returns:
        True if valid (no errors), False otherwise
    """
    print(f"\n{'='*80}")
    print(f"Validation de: {file_path}")
    print(f"{'='*80}")
    
    # Check file exists
    if not file_path.exists():
        print(f"❌ Fichier introuvable: {file_path}")
        return False
    
    # Load JSON
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Erreur de parsing JSON: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur de lecture: {e}")
        return False
    
    # Validate
    try:
        validator = SolutionValidator()
        is_valid, issues = validator.validate_full(data)
        
        # Generate report
        if verbose or not is_valid:
            report = validator.generate_report(issues)
            print(report)
        else:
            # Quick summary
            errors = sum(1 for i in issues if i.severity == Severity.ERROR)
            warnings = sum(1 for i in issues if i.severity == Severity.WARNING)
            infos = sum(1 for i in issues if i.severity == Severity.INFO)
            
            if errors == 0 and warnings == 0 and infos == 0:
                print("✅ Solution valide - aucun problème détecté")
            else:
                print(f"📊 Résumé: {errors} erreur(s), {warnings} avertissement(s), {infos} info(s)")
                if errors > 0:
                    print("\n⚠️  Utiliser --verbose pour voir les détails")
        
        return is_valid
        
    except Exception as e:
        print(f"❌ Erreur de validation: {e}")
        import traceback
        traceback.print_exc()
        return False


def validate_directory(dir_path: Path, verbose: bool = False) -> tuple:
    """
    Validate all JSON files in a directory.
    
    Args:
        dir_path: Directory containing solution files
        verbose: Show detailed reports
        
    Returns:
        Tuple (total_files, valid_files, invalid_files)
    """
    json_files = list(dir_path.glob("*.json"))
    
    if not json_files:
        print(f"❌ Aucun fichier JSON trouvé dans: {dir_path}")
        return 0, 0, 0
    
    print(f"\n{'='*80}")
    print(f"Validation de {len(json_files)} fichier(s) dans: {dir_path}")
    print(f"{'='*80}")
    
    valid = []
    invalid = []
    
    for json_file in sorted(json_files):
        is_valid = validate_file(json_file, verbose=verbose)
        
        if is_valid:
            valid.append(json_file)
        else:
            invalid.append(json_file)
    
    # Summary
    print(f"\n{'='*80}")
    print(f"BILAN GLOBAL")
    print(f"{'='*80}")
    print(f"Total: {len(json_files)} fichier(s)")
    print(f"✅ Valides: {len(valid)}")
    print(f"❌ Invalides: {len(invalid)}")
    
    if invalid:
        print(f"\nFichiers invalides:")
        for f in invalid:
            print(f"  - {f.name}")
    
    return len(json_files), len(valid), len(invalid)


def main():
    parser = argparse.ArgumentParser(
        description="Valider des solutions PyCalendar",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python validate_solution.py solutions/latest_volley.json
  python validate_solution.py solutions/latest_volley.json --verbose
  python validate_solution.py --all
  python validate_solution.py --all --verbose
        """
    )
    
    parser.add_argument(
        "solution_file",
        nargs="?",
        help="Fichier JSON de solution à valider"
    )
    
    parser.add_argument(
        "--all",
        action="store_true",
        help="Valider tous les fichiers dans solutions/"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Afficher le rapport détaillé"
    )
    
    parser.add_argument(
        "--dir",
        type=Path,
        default=Path("solutions"),
        help="Répertoire à valider avec --all (défaut: solutions/)"
    )
    
    args = parser.parse_args()
    
    # Check arguments
    if not args.all and not args.solution_file:
        parser.print_help()
        print("\n❌ Erreur: Spécifier un fichier ou --all")
        sys.exit(1)
    
    # Validate
    if args.all:
        total, valid, invalid = validate_directory(args.dir, verbose=args.verbose)
        sys.exit(0 if invalid == 0 else 1)
    else:
        file_path = Path(args.solution_file)
        is_valid = validate_file(file_path, verbose=args.verbose)
        sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
