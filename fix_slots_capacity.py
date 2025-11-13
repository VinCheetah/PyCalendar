#!/usr/bin/env python3
"""
Script pour patcher les slots dans latest_volley.json
afin de gérer correctement la capacité des gymnases.
"""

import json
from pathlib import Path
from collections import Counter

def fix_slots_capacity(json_path):
    """Patch les slots en ajoutant des suffixes de capacité."""
    
    # Charger le JSON
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"📂 Chargement de {json_path}")
    print(f"   Version: {data.get('version')}")
    print(f"   Matchs planifiés: {len(data['matches']['scheduled'])}")
    print(f"   Slots disponibles avant: {len(data['slots']['available'])}")
    print(f"   Slots occupés avant: {len(data['slots']['occupied'])}")
    
    # Extraire les capacités des gymnases
    gymnase_capacities = {}
    for gym in data['entities']['gymnases']:
        gymnase_capacities[gym['id']] = gym['capacite']
    
    print(f"\n🏢 Capacités des gymnases:")
    for gym_id, capacite in sorted(gymnase_capacities.items()):
        print(f"   {gym_id}: {capacite}")
    
    # Compter l'occupation des créneaux depuis les matchs planifiés
    slot_occupation = Counter()
    occupied_with_matches = {}
    
    for match in data['matches']['scheduled']:
        if 'gymnase' in match and match['gymnase']:
            gymnase = match['gymnase']
            semaine = match['semaine']
            horaire = match['horaire']
            slot_key = (gymnase, semaine, horaire)
            slot_occupation[slot_key] += 1
            
            # Créer le nouveau slot_id avec suffixe
            slot_id = f"S_{gymnase}_{semaine}_{horaire}_{slot_occupation[slot_key]}"
            occupied_with_matches[slot_id] = {
                "slot_id": slot_id,
                "gymnase": gymnase,
                "semaine": semaine,
                "horaire": horaire,
                "status": "occupé",
                "match_id": match['match_id']
            }
    
    # Reconstruire les slots disponibles avec gestion de la capacité
    available_slots = []
    
    # Grouper les anciens slots disponibles par (gymnase, semaine, horaire)
    slots_by_key = {}
    for slot in data['slots']['available']:
        key = (slot['gymnase'], slot['semaine'], slot['horaire'])
        if key not in slots_by_key:
            slots_by_key[key] = []
        slots_by_key[key].append(slot)
    
    # Pour chaque créneau disponible, calculer combien de slots sont libres
    for slot_key, slots in slots_by_key.items():
        gymnase, semaine, horaire = slot_key
        nb_matchs_occupes = slot_occupation.get(slot_key, 0)
        capacite = gymnase_capacities.get(gymnase, 1)
        
        # Calculer le nombre de slots disponibles
        nb_slots_disponibles = capacite - nb_matchs_occupes
        
        # Générer les slots disponibles avec suffixes
        for i in range(nb_slots_disponibles):
            slot_id = f"S_{gymnase}_{semaine}_{horaire}_{nb_matchs_occupes + i + 1}"
            available_slots.append({
                "slot_id": slot_id,
                "gymnase": gymnase,
                "semaine": semaine,
                "horaire": horaire,
                "status": "libre"
            })
    
    # Mettre à jour le JSON
    data['slots']['available'] = available_slots
    data['slots']['occupied'] = list(occupied_with_matches.values())
    
    print(f"\n✨ Résultat après patch:")
    print(f"   Slots disponibles: {len(data['slots']['available'])}")
    print(f"   Slots occupés: {len(data['slots']['occupied'])}")
    
    # Afficher quelques exemples de créneaux multi-capacité
    print(f"\n📊 Exemples de créneaux:")
    examples = {}
    for slot in available_slots[:50]:  # Les 50 premiers
        key = (slot['gymnase'], slot['semaine'], slot['horaire'])
        if key not in examples:
            examples[key] = []
        examples[key].append(slot['slot_id'])
    
    for (gymnase, semaine, horaire), slot_ids in list(examples.items())[:10]:
        if len(slot_ids) > 1:  # Montrer seulement les multi-capacité
            print(f"   {gymnase} S{semaine} {horaire}: {len(slot_ids)} slots libres")
            for sid in slot_ids:
                print(f"      - {sid}")
    
    # Sauvegarder le JSON patché
    output_path = json_path.parent / f"{json_path.stem}_patched.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 JSON patché sauvegardé: {output_path}")
    print(f"   Taille: {output_path.stat().st_size / 1024:.1f} KB")
    
    return output_path


if __name__ == '__main__':
    json_path = Path('solutions/latest_volley.json')
    if not json_path.exists():
        print(f"❌ Fichier introuvable: {json_path}")
        exit(1)
    
    output_path = fix_slots_capacity(json_path)
    
    print(f"\n✅ Patch terminé!")
    print(f"\n💡 Pour tester:")
    print(f"   1. Copiez {output_path} vers solutions/latest_volley.json")
    print(f"   2. Lancez: python generate_interface.py")
