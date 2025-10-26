#!/usr/bin/env python3
"""
quick_interface.py - Script rapide pour régénérer et ouvrir l'interface

Ce script simplifie le workflow : il régénère l'interface depuis la dernière
solution et l'ouvre automatiquement dans le navigateur.

Usage:
    python quick_interface.py              # Utilise latest_volley.json
    python quick_interface.py --format v1  # Force format v1.0
    python quick_interface.py --format v2  # Force format v2.0
    python quick_interface.py --no-open    # Ne pas ouvrir le navigateur
"""

import argparse
import sys
import webbrowser
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(
        description='Régénère rapidement l\'interface et l\'ouvre dans le navigateur',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--format', '-f',
        choices=['v1', 'v2', 'auto'],
        default='auto',
        help='Format de solution à utiliser (auto: cherche v2 puis v1)'
    )
    
    parser.add_argument(
        '--solution', '-s',
        type=str,
        default='latest_volley.json',
        help='Nom du fichier de solution (défaut: latest_volley.json)'
    )
    
    parser.add_argument(
        '--no-open',
        action='store_true',
        help='Ne pas ouvrir automatiquement le navigateur'
    )
    
    args = parser.parse_args()
    
    # Déterminer le chemin de la solution
    if args.format == 'auto':
        # Chercher v2 en priorité, puis v1
        solution_path = Path('solutions') / 'v2.0' / args.solution
        if not solution_path.exists():
            solution_path = Path('solutions') / 'v1.0' / args.solution
        
        if not solution_path.exists():
            print("❌ Aucune solution trouvée !")
            print(f"   Cherché dans:")
            print(f"   - solutions/v2.0/{args.solution}")
            print(f"   - solutions/v1.0/{args.solution}")
            print("\n💡 Lancez d'abord: python main.py configs/config_volley.yaml")
            return 1
            
    elif args.format == 'v2':
        solution_path = Path('solutions') / 'v2.0' / args.solution
    else:
        solution_path = Path('solutions') / 'v1.0' / args.solution
    
    if not solution_path.exists():
        print(f"❌ Solution introuvable: {solution_path}")
        return 1
    
    print("=" * 70)
    print("🚀 RÉGÉNÉRATION RAPIDE DE L'INTERFACE")
    print("=" * 70)
    print(f"📂 Solution: {solution_path}")
    print(f"📄 Sortie: calendrier.html")
    print()
    
    # Régénérer l'interface
    print("🔄 Régénération en cours...\n")
    try:
        result = subprocess.run(
            [sys.executable, 'regenerate_interface.py', 
             '--solution', args.solution, 
             '--output', 'calendrier.html'],
            check=True,
            capture_output=False
        )
    except subprocess.CalledProcessError:
        print("\n❌ Erreur lors de la régénération")
        return 1
    
    print("\n" + "=" * 70)
    print("✅ INTERFACE RÉGÉNÉRÉE AVEC SUCCÈS")
    print("=" * 70)
    
    # Ouvrir dans le navigateur
    if not args.no_open:
        html_path = Path('calendrier.html')
        if html_path.exists():
            absolute_path = html_path.absolute()
            url = f"file://{absolute_path}"
            
            print(f"\n🌐 Ouverture dans le navigateur...")
            print(f"   {url}")
            
            webbrowser.open(url)
            print("\n✅ Calendrier ouvert dans votre navigateur !")
        else:
            print(f"\n⚠️  Fichier calendrier.html introuvable")
    else:
        print(f"\n💡 Pour ouvrir: python3 open_calendar.py calendrier.html")
    
    print()
    return 0


if __name__ == '__main__':
    sys.exit(main())
