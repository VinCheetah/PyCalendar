#!/usr/bin/env python3
"""
Script pour générer l'interface HTML à partir d'une solution v2.0.

Usage:
    python scripts/regenerate_interface.py solutions/latest_volley_v2.json
    python scripts/regenerate_interface.py solutions/latest_volley_v2.json -o calendar.html
"""

import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from interface.core.generator import InterfaceGenerator


def main():
    """Point d'entrée du script."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Génère l\'interface HTML à partir d\'une solution v2.0',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  # Générer depuis latest_volley_v2.json
  python scripts/regenerate_interface.py solutions/latest_volley_v2.json
  
  # Spécifier fichier de sortie
  python scripts/regenerate_interface.py solutions/latest_volley_v2.json -o custom.html
        """
    )
    
    parser.add_argument('solution', type=Path, help='Fichier JSON de solution v2.0')
    parser.add_argument('-o', '--output', type=Path, help='Fichier HTML de sortie (défaut: calendar.html)')
    
    args = parser.parse_args()
    
    # Vérifier que le fichier de solution existe
    if not args.solution.exists():
        print(f"❌ Erreur: fichier introuvable: {args.solution}")
        sys.exit(1)
    
    # Déterminer le fichier de sortie
    output_file = args.output or Path('calendar.html')
    
    # Générer l'interface
    print(f"🚀 Génération de l'interface HTML...")
    print(f"   Source: {args.solution}")
    print(f"   Sortie: {output_file}")
    
    try:
        generator = InterfaceGenerator()
        generator.generate(args.solution, str(output_file))
        
        print(f"\n✅ Interface générée avec succès!")
        print(f"   Fichier: {output_file}")
        print(f"   Taille: {output_file.stat().st_size / 1024:.1f} KB")
        print(f"\n💡 Ouvrez {output_file} dans votre navigateur pour visualiser le calendrier.")
        
    except Exception as e:
        print(f"\n❌ Erreur lors de la génération: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
