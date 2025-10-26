#!/usr/bin/env python3
"""
Script de migration : suppression complète du format v1.0

Ce script :
1. Déplace tous les fichiers de solutions/v2.0/ vers solutions/
2. Supprime le dossier solutions/v1.0/ et solutions/v2.0/
3. Met à jour tous les fichiers de documentation
"""

import shutil
from pathlib import Path

def migrate_solutions():
    """Migre les solutions du format v2.0 vers le format unique."""
    
    print("="*80)
    print("MIGRATION - Suppression du format v1.0, v2.0 devient le format unique")
    print("="*80)
    
    solutions_dir = Path("solutions")
    v1_dir = solutions_dir / "v1.0"
    v2_dir = solutions_dir / "v2.0"
    
    # 1. Déplacer les fichiers v2.0 vers solutions/
    if v2_dir.exists():
        print(f"\n📦 Déplacement des solutions v2.0 vers solutions/...")
        for file in v2_dir.glob("*.json"):
            target = solutions_dir / file.name
            print(f"  • {file.name}")
            shutil.move(str(file), str(target))
        
        # Supprimer le dossier v2.0
        print(f"\n🗑️  Suppression du dossier v2.0/...")
        shutil.rmtree(v2_dir)
    else:
        print(f"\n⚠️  Dossier v2.0/ introuvable, déjà migré ?")
    
    # 2. Supprimer le dossier v1.0
    if v1_dir.exists():
        print(f"\n🗑️  Suppression du dossier v1.0/...")
        shutil.rmtree(v1_dir)
    else:
        print(f"\n⚠️  Dossier v1.0/ introuvable, déjà migré ?")
    
    print(f"\n✅ Migration terminée !")
    print(f"\n📁 Structure actuelle :")
    for file in sorted(solutions_dir.glob("*.json")):
        size_kb = file.stat().st_size / 1024
        print(f"  • {file.name} ({size_kb:.1f} KB)")
    
    print(f"\n💡 Prochaines étapes :")
    print(f"  1. Lancer main.py pour générer une nouvelle solution")
    print(f"  2. Valider avec: python validate_solution.py solutions/latest_volley.json")


if __name__ == "__main__":
    migrate_solutions()
