#!/usr/bin/env python3
"""
regenerate_interface.py - Wrapper pour regénérer l'interface HTML

Ce script détecte automatiquement le format de solution et génère l'interface.

Usage:
    python regenerate_interface.py --solution SOLUTION --output OUTPUT
    
Exemples:
    # Depuis une solution v1.0 (ancien format)
    python regenerate_interface.py --solution latest_volley.json --output calendrier.html
    
    # Depuis une solution v2.0 (nouveau format)
    python regenerate_interface.py --solution latest_volley_v2.json --output calendrier.html
    
    # Sans arguments (utilise latest_volley.json et convertit automatiquement)
    python regenerate_interface.py
"""

import argparse
import json
import sys
import subprocess
from pathlib import Path


def detect_solution_version(solution_path: Path) -> str:
    """
    Détecte la version d'une solution.
    
    Returns:
        '1.0' ou '2.0'
    """
    try:
        with open(solution_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            version = data.get('version', '1.0')
            return version
    except Exception as e:
        print(f"⚠️  Erreur lecture {solution_path}: {e}")
        return '1.0'  # Assume v1.0 par défaut


def main():
    parser = argparse.ArgumentParser(
        description='Génère l\'interface HTML PyCalendar (détection automatique du format)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  # Génération depuis latest_volley.json (v1.0 → conversion auto → v2.0 → HTML)
  %(prog)s --solution latest_volley.json --output calendrier.html
  
  # Génération depuis latest_volley_v2.json (v2.0 → HTML directement)
  %(prog)s --solution latest_volley_v2.json --output calendrier.html
  
  # Sans arguments (utilise solutions/latest_volley.json)
  %(prog)s
        """
    )
    
    parser.add_argument(
        '--solution', '-s',
        type=str,
        default='latest_volley.json',
        help='Fichier de solution (défaut: latest_volley.json)'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='calendrier.html',
        help='Fichier HTML de sortie (défaut: calendrier.html)'
    )
    
    args = parser.parse_args()
    
    # Résoudre le chemin de la solution
    solution_path = Path('solutions') / args.solution
    if not solution_path.exists():
        solution_path = Path(args.solution)
    
    if not solution_path.exists():
        print(f"❌ Solution introuvable: {args.solution}")
        print(f"   Cherché dans: solutions/{args.solution} et {args.solution}")
        return 1
    
    print(f"📂 Solution: {solution_path}")
    
    # Détecter la version
    version = detect_solution_version(solution_path)
    print(f"📋 Format détecté: v{version}")
    
    output_path = Path(args.output)
    
    if version == '2.0':
        # Solution v2.0 → Générer directement
        print(f"\n✅ Format v2.0 détecté → Génération directe de l'interface\n")
        cmd = [
            'python', 'scripts/regenerate_interface.py',
            str(solution_path),
            '-o', str(output_path)
        ]
    else:
        # Solution v1.0 → Convertir puis générer
        print(f"\n🔄 Format v1.0 détecté → Conversion + Génération automatique\n")
        cmd = [
            'python', 'scripts/auto_generate_interface.py',
            str(solution_path),
            '-o', str(output_path.parent if output_path.name != 'calendrier.html' else 'output')
        ]
    
    try:
        result = subprocess.run(cmd, check=True)
        
        # Si auto_generate_interface, déplacer le fichier
        if version == '1.0':
            expected = Path('output') / f"{solution_path.stem}_calendar.html"
            if expected.exists() and output_path.name != expected.name:
                expected.rename(output_path)
                print(f"\n📄 Fichier renommé: {output_path}")
        
        print(f"\n✅ Succès ! Interface générée: {output_path}")
        return 0
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Erreur lors de la génération")
        return 1
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
