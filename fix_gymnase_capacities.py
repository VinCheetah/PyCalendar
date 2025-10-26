#!/usr/bin/env python3
"""
Script pour corriger les capacités des gymnases dans le fichier JSON v2.0
en utilisant les valeurs réelles depuis le fichier de configuration Excel.
"""

import json
import sys
from pathlib import Path

# Ajouter le répertoire courant au path pour imports
sys.path.insert(0, str(Path(__file__).parent))

from data.data_loader import DataLoader

def fix_capacities(json_file: Path, config_file: Path):
    """
    Corrige les capacités des gymnases dans le fichier JSON.
    
    Args:
        json_file: Chemin vers le fichier JSON v2.0
        config_file: Chemin vers le fichier de configuration Excel
    """
    print(f"📖 Chargement de {json_file.name}...")
    
    # Charger le JSON
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"📊 Chargement des capacités depuis {config_file.name}...")
    
    # Charger les gymnases depuis la config
    loader = DataLoader(str(config_file))
    gymnases_obj = loader.charger_gymnases()
    capacites = {g.nom: g.capacite for g in gymnases_obj}
    
    print(f"  ✅ {len(capacites)} capacités chargées:")
    for nom, cap in sorted(capacites.items()):
        print(f"     {nom}: {cap} terrain(s)")
    
    # Mettre à jour les capacités dans le JSON
    if 'entities' in data and 'gymnases' in data['entities']:
        updates = 0
        for gymnase in data['entities']['gymnases']:
            nom = gymnase['nom']
            old_capacity = gymnase.get('capacite', 0)
            new_capacity = capacites.get(nom, old_capacity)
            
            if new_capacity != old_capacity:
                gymnase['capacite'] = new_capacity
                updates += 1
                print(f"  🔧 {nom}: {old_capacity} → {new_capacity}")
        
        if updates > 0:
            # Sauvegarder le fichier mis à jour
            backup_file = json_file.parent / f"{json_file.stem}_backup.json"
            print(f"\n💾 Sauvegarde de l'ancien fichier: {backup_file.name}")
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Écriture du fichier corrigé: {json_file.name}")
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"\n✅ {updates} capacités corrigées avec succès!")
        else:
            print(f"\n✅ Toutes les capacités sont déjà correctes!")
    else:
        print(f"\n❌ Structure JSON invalide (pas d'entités/gymnases)")
        return 1
    
    return 0


def main():
    """Point d'entrée du script."""
    # Fichiers par défaut
    json_file = Path("solutions/v2.0/latest_volley.json")
    config_file = Path("data_volley/config_volley.xlsx")
    
    # Vérifier que les fichiers existent
    if not json_file.exists():
        print(f"❌ Fichier JSON introuvable: {json_file}")
        return 1
    
    if not config_file.exists():
        print(f"❌ Fichier de config introuvable: {config_file}")
        return 1
    
    try:
        return fix_capacities(json_file, config_file)
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
