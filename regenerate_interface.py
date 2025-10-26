#!/usr/bin/env python3
"""
regenerate_interface.py - Wrapper pour regénérer l'interface HTML

Ce script génère l'interface HTML à partir d'une solution PyCalendar.

Usage:
    python regenerate_interface.py --solution SOLUTION --output OUTPUT
    
Exemples:
    # Depuis une solution existante
    python regenerate_interface.py --solution latest_volley.json --output calendrier.html
    
    # Sans arguments (utilise latest_volley.json)
    python regenerate_interface.py
"""

import argparse
import json
import sys
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description='Génère l\'interface HTML PyCalendar',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  # Génération depuis latest_volley.json
  %(prog)s --solution latest_volley.json --output calendrier.html
  
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
    solution_path = None
    
    # 1. Chercher d'abord dans solutions/
    candidate = Path('solutions') / args.solution
    if candidate.exists():
        solution_path = candidate
    
    # 2. Chemin direct
    if not solution_path or not solution_path.exists():
        candidate = Path(args.solution)
        if candidate.exists():
            solution_path = candidate
    
    if not solution_path or not solution_path.exists():
        print(f"❌ Solution introuvable: {args.solution}")
        print(f"   Cherché dans:")
        print(f"   - solutions/{args.solution}")
        print(f"   - {args.solution}")
        return 1
    
    print(f"📂 Solution: {solution_path}")
    
    output_path = Path(args.output)
    
    # Générer l'interface directement
    print(f"\n✅ Génération de l'interface\n")
    cmd = [
        sys.executable, 'scripts/regenerate_interface.py',
        str(solution_path),
        '-o', str(output_path)
    ]
    
    try:
        result = subprocess.run(cmd, check=True)
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
