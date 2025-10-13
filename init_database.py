#!/usr/bin/env python3
"""
Script d'initialisation de la base de données PyCalendar V2

Usage:
    python init_database.py

Ce script:
1. Crée la base de données SQLite avec toutes les tables
2. Active les foreign keys
3. Affiche un résumé de la structure créée
"""

import sys
from pathlib import Path

# Ajouter le répertoire racine au path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend.database.engine import init_db, DATABASE_PATH
from backend.database.models import Base
import sqlite3


def display_structure():
    """Affiche la structure de la base de données créée"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    print("\n" + "=" * 80)
    print("📊 STRUCTURE DE LA BASE DE DONNÉES")
    print("=" * 80)
    
    # Liste des tables
    tables = list(Base.metadata.tables.keys())
    print(f"\n📋 Tables créées ({len(tables)}):")
    for table in tables:
        print(f"   ✅ {table}")
    
    # Liste des indexes
    print("\n📑 Indexes créés:")
    cursor.execute("SELECT name, tbl_name FROM sqlite_master WHERE type='index' AND sql IS NOT NULL ORDER BY tbl_name, name")
    indexes = cursor.fetchall()
    current_table = None
    for idx_name, tbl_name in indexes:
        if tbl_name != current_table:
            print(f"\n   Table '{tbl_name}':")
            current_table = tbl_name
        print(f"      • {idx_name}")
    
    # Vérifier foreign keys
    cursor.execute("PRAGMA foreign_keys")
    fk_enabled = cursor.fetchone()[0]
    print(f"\n🔑 Foreign keys: {'✅ Activées' if fk_enabled else '❌ Désactivées (seront activées à la connexion)'}")
    
    conn.close()


def main():
    print("=" * 80)
    print("🚀 INITIALISATION BASE DE DONNÉES PyCalendar V2")
    print("=" * 80)
    
    # Vérifier si la DB existe déjà
    if DATABASE_PATH.exists():
        response = input(f"\n⚠️  La base de données existe déjà: {DATABASE_PATH}\nVoulez-vous la recréer? (y/N): ")
        if response.lower() != 'y':
            print("❌ Initialisation annulée")
            return
        DATABASE_PATH.unlink()
        print("🗑️  Base de données existante supprimée")
    
    # Créer la base de données
    print("\n📦 Création de la base de données...")
    init_db()
    
    # Afficher la structure
    display_structure()
    
    print("\n" + "=" * 80)
    print("✅ BASE DE DONNÉES INITIALISÉE AVEC SUCCÈS")
    print("=" * 80)
    print(f"\n📍 Emplacement: {DATABASE_PATH}")
    print("📄 Documentation: DATABASE_CREATION_REPORT.md")
    print("\n🚀 Prochaine étape: Tâche 1.4 - Création des schemas Pydantic")


if __name__ == "__main__":
    main()
