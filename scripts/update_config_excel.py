#!/usr/bin/env python3
"""
Script wrapper pour pycalendar.cli.update_config_excel - Validation et actualisation de configuration.

Usage:
    python scripts/update_config_excel.py --fichier configs/config_volley.yaml
"""

import sys
from pathlib import Path

# Ajouter le répertoire src au chemin Python
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from pycalendar.cli.update_config_excel import actualiser_fichier_v2

def main():
    import argparse
    import yaml
    
    parser = argparse.ArgumentParser(
        description="Actualise et valide un fichier de configuration",
        epilog="""
Exemples:
    python scripts/update_config_excel.py --fichier configs/config_volley.yaml
    python scripts/update_config_excel.py --fichier examples/handball/config_hand.yaml
    python scripts/update_config_excel.py --fichier examples/volleyball/config_volley.xlsx
        """
    )
    
    parser.add_argument(
        '--fichier',
        default='configs/config_volley.yaml',
        help="Fichier de configuration YAML ou Excel à actualiser"
    )
    
    args = parser.parse_args()
    
    fichier_path = project_root / args.fichier
    
    if not fichier_path.exists():
        print(f"❌ Fichier non trouvé: {fichier_path}")
        return 1
    
    print(f"📥 Chargement du fichier: {fichier_path.name}")
    
    # Si c'est un fichier YAML, extraire le chemin de l'Excel
    if fichier_path.suffix in ['.yaml', '.yml']:
        try:
            with open(fichier_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # Extraire le chemin du fichier Excel
            if 'fichiers' in config and 'donnees' in config['fichiers']:
                excel_path = config['fichiers']['donnees']
            elif 'fichier_excel' in config:
                excel_path = config['fichier_excel']
            else:
                print(f"❌ Aucun fichier Excel trouvé dans la configuration YAML")
                print(f"   Cherché: fichiers.donnees ou fichier_excel")
                return 1
            
            # Résoudre le chemin relatif
            excel_file = Path(excel_path)
            if not excel_file.is_absolute():
                # Le chemin est relatif à la racine du projet
                excel_file = project_root / excel_path
            
            if not excel_file.exists():
                print(f"❌ Fichier Excel introuvable: {excel_file}")
                return 1
            
            print(f"📄 Fichier Excel: {excel_file.name}")
            fichier_path = excel_file
            
        except Exception as e:
            print(f"❌ Erreur lors de la lecture du fichier YAML: {e}")
            return 1
    
    success = actualiser_fichier_v2(str(fichier_path))
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())
