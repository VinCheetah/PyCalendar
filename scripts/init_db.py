#!/usr/bin/env python3
"""
Script d'initialisation de la base de données PyCalendar.

Crée toutes les tables nécessaires dans database/pycalendar.db.
"""

import sys
from pathlib import Path

# Ajouter répertoire racine au sys.path pour imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.database.engine import init_db, DATABASE_PATH


def main():
    print("=" * 60)
    print("Initialisation de la base de données PyCalendar")
    print("=" * 60)
    
    # Afficher chemin DB
    print(f"\n📂 Chemin de la base de données :")
    print(f"   {DATABASE_PATH}")
    
    # Vérifier si DB existe déjà
    if DATABASE_PATH.exists():
        print(f"\n⚠️  Base de données existante détectée")
        response = input("   Voulez-vous la recréer ? (oui/non) : ").strip().lower()
        if response not in ['oui', 'o', 'yes', 'y']:
            print("\n❌ Initialisation annulée")
            return
        
        # Sauvegarder ancien fichier
        backup_path = DATABASE_PATH.with_suffix('.db.bak')
        DATABASE_PATH.rename(backup_path)
        print(f"   ✓ Sauvegarde créée : {backup_path}")
    
    # Créer DB
    print(f"\n🔧 Création des tables...")
    try:
        init_db()
        print(f"   ✓ Tables créées avec succès")
    except Exception as e:
        print(f"\n❌ Erreur lors de la création : {e}")
        sys.exit(1)
    
    # Vérifier tables créées
    import sqlite3
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    print(f"\n📊 Tables créées ({len(tables)}) :")
    for table in tables:
        print(f"   - {table}")
    
    print(f"\n✅ Initialisation terminée avec succès!")
    print(f"   Base de données prête à l'emploi : {DATABASE_PATH}")


if __name__ == "__main__":
    main()
