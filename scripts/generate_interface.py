#!/usr/bin/env python3
"""
Script simple pour générer l'interface à partir d'une solution existante.
"""

import sys
from pathlib import Path

# Ajouter le répertoire src au chemin Python
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from pycalendar.interface.core.generator import InterfaceGenerator

def main():
    # Chemin de la solution
    solution_path = project_root / 'solutions' / 'latest_volley.json'
    
    if not solution_path.exists():
        print(f"❌ Aucune solution trouvée")
        print(f"   Cherché: {solution_path}")
        return 1
    
    # Chemin de sortie avec design redesigné
    output_path = project_root / 'interface.html'
    
    print(f"📥 Chargement de la solution: {solution_path.name}")
    print(f"📤 Génération de l'interface vers: {output_path.name}")
    
    # Générer l'interface
    generator = InterfaceGenerator()
    
    try:
        result_path = generator.generate(
            solution=solution_path,
            output_path=str(output_path),
            solution_name="volley"
        )
        
        print(f"\n✅ Interface générée avec succès!")
        print(f"📂 Fichier: {result_path}")
        print(f"\n💡 Ouvrez le fichier dans un navigateur pour le visualiser")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Erreur lors de la génération:")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
