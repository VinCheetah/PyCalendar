#!/usr/bin/env python3
"""
Script d'intégration automatique de l'interface.

Ce script est conçu pour être appelé par main.py après la génération d'une solution.
Il convertit automatiquement la solution au format v2.0 et génère l'interface HTML.

Usage depuis main.py:
    from scripts import auto_generate_interface
    auto_generate_interface.process_solution("solutions/latest_volley.json")
    
Usage en ligne de commande:
    python scripts/auto_generate_interface.py solutions/latest_volley.json
"""

import sys
from pathlib import Path
from typing import Optional

# Ajouter le répertoire parent au path pour imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.convert_solution_to_v2 import SolutionConverterV2
from pycalendar.interface.core.generator import InterfaceGenerator


def process_solution(
    solution_path: Path,
    output_dir: Optional[Path] = None,
    verbose: bool = True
) -> tuple[Path, Path]:
    """
    Pipeline complet : conversion v2.0 + génération interface HTML.
    
    Args:
        solution_path: Chemin vers le fichier JSON de solution (ancien format)
        output_dir: Répertoire de sortie (défaut: même que solution_path)
        verbose: Afficher les messages de progression
        
    Returns:
        Tuple (path_v2_json, path_html)
    """
    solution_path = Path(solution_path)
    
    if not solution_path.exists():
        raise FileNotFoundError(f"Solution introuvable: {solution_path}")
    
    # Déterminer les chemins de sortie
    if output_dir is None:
        output_dir = solution_path.parent
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # Chemins de sortie
    v2_path = output_dir / f"{solution_path.stem}_v2.json"
    html_path = output_dir / f"{solution_path.stem}_calendar.html"
    
    if verbose:
        print("\n" + "="*70)
        print("🔄 GÉNÉRATION AUTOMATIQUE DE L'INTERFACE")
        print("="*70)
        print(f"📂 Solution source: {solution_path}")
        print(f"📂 Répertoire sortie: {output_dir}")
        print()
    
    # Étape 1 : Conversion v2.0
    if verbose:
        print("┌─ ÉTAPE 1/2 : Conversion au format v2.0")
        print("│")
    
    try:
        converter = SolutionConverterV2(solution_path)
        converter.save(v2_path)
        
        if verbose:
            print("│")
            print(f"└─ ✅ Conversion réussie: {v2_path.name}")
            print()
    except Exception as e:
        if verbose:
            print(f"└─ ❌ Erreur conversion: {e}")
        raise
    
    # Étape 2 : Génération HTML
    if verbose:
        print("┌─ ÉTAPE 2/2 : Génération de l'interface HTML")
        print("│")
    
    try:
        generator = InterfaceGenerator()
        generator.generate(v2_path, str(html_path))
        
        if verbose:
            print("│")
            print(f"└─ ✅ Interface générée: {html_path.name}")
            print()
    except Exception as e:
        if verbose:
            print(f"└─ ❌ Erreur génération: {e}")
        raise
    
    # Résumé final
    if verbose:
        print("="*70)
        print("✅ GÉNÉRATION TERMINÉE AVEC SUCCÈS")
        print("="*70)
        print(f"📄 Solution v2.0 : {v2_path}")
        print(f"   Taille: {v2_path.stat().st_size / 1024:.1f} KB")
        print()
        print(f"🌐 Interface HTML : {html_path}")
        print(f"   Taille: {html_path.stat().st_size / 1024:.1f} KB")
        print()
        print("💡 Ouvrez l'interface dans votre navigateur:")
        print(f"   firefox {html_path}")
        print("="*70)
        print()
    
    return v2_path, html_path


def main():
    """Point d'entrée en ligne de commande."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Pipeline automatique: conversion v2.0 + génération interface',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  # Traitement complet d'une solution
  python scripts/auto_generate_interface.py solutions/latest_volley.json
  
  # Spécifier répertoire de sortie
  python scripts/auto_generate_interface.py solutions/latest_volley.json -o output/
  
  # Mode silencieux
  python scripts/auto_generate_interface.py solutions/latest_volley.json --quiet

Usage depuis main.py:
  from scripts import auto_generate_interface
  auto_generate_interface.process_solution("solutions/latest_volley.json")
        """
    )
    
    parser.add_argument(
        'solution',
        type=Path,
        help='Fichier JSON de solution à traiter'
    )
    parser.add_argument(
        '-o', '--output',
        type=Path,
        help='Répertoire de sortie (défaut: même que solution)'
    )
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Mode silencieux (pas de messages)'
    )
    
    args = parser.parse_args()
    
    try:
        v2_path, html_path = process_solution(
            args.solution,
            output_dir=args.output,
            verbose=not args.quiet
        )
        sys.exit(0)
        
    except Exception as e:
        print(f"\n❌ ERREUR: {e}", file=sys.stderr)
        if not args.quiet:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
