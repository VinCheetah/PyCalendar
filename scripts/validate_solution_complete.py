#!/usr/bin/env python3
"""Validation finale complète de la solution après correction du bug."""

import json
from pathlib import Path
from collections import defaultdict

solution_file = Path("solutions/latest_volley.json")

with open(solution_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

print("=" * 100)
print("✅ VALIDATION COMPLÈTE DE LA SOLUTION")
print("=" * 100)

# Récupérer les poules
pools = {p['id']: p for p in data['entities']['poules']}

# Statistiques globales
total_pools = len(pools)
classique_count = sum(1 for p in pools.values() if p['type'] == 'Classique')
ar_count = sum(1 for p in pools.values() if p['type'] == 'Aller-Retour')

print(f"\n📊 Vue d'ensemble:")
print(f"   • Total de poules: {total_pools}")
print(f"   • Poules Classiques: {classique_count}")
print(f"   • Poules Aller-Retour: {ar_count}")

# Récupérer tous les matchs
all_matches = data['matches']['scheduled'] + data['matches']['unscheduled']

# Analyser chaque poule
print(f"\n🔍 Analyse détaillée par poule:")
print(f"   {'-' * 95}")
print(f"   {'Poule':<12} {'Type':<15} {'Équipes':>7} {'Matchs':>7} {'Attendu':>8} {'Statut':<30}")
print(f"   {'-' * 95}")

errors = []
warnings = []

for pool_id in sorted(pools.keys()):
    pool = pools[pool_id]
    pool_type = pool['type']
    nb_teams = pool['nb_equipes']
    nb_matches = pool['nb_matchs_planifies'] + pool['nb_matchs_non_planifies']
    
    # Calculer le nombre attendu
    if pool_type == 'Aller-Retour':
        expected = nb_teams * (nb_teams - 1)
    else:  # Classique
        expected = nb_teams * (nb_teams - 1) // 2
    
    # Statut
    if nb_matches == expected:
        status = "✅ OK"
        icon = "✅"
    elif nb_matches < expected:
        status = f"❌ MANQUANT ({expected - nb_matches})"
        icon = "❌"
        errors.append((pool_id, f"{nb_matches}/{expected} matchs (manquants: {expected - nb_matches})"))
    else:
        status = f"❌ TROP ({nb_matches - expected})"
        icon = "❌"
        errors.append((pool_id, f"{nb_matches}/{expected} matchs (surplus: {nb_matches - expected})"))
    
    print(f"   {pool_id:<12} {pool_type:<15} {nb_teams:>7} {nb_matches:>7} {expected:>8} {status:<30}")

print(f"   {'-' * 95}")

# Vérifier les doublons dans chaque poule
print(f"\n🔬 Vérification des doublons:")

duplicates_found = 0

for pool_id in sorted(pools.keys()):
    pool = pools[pool_id]
    pool_type = pool['type']
    
    # Récupérer tous les matchs de la poule
    pool_matches = [m for m in all_matches if m.get('poule') == pool_id]
    
    # Compter les occurrences de chaque paire
    pair_counts = defaultdict(int)
    
    for match in pool_matches:
        eq1 = match['equipe1_id']
        eq2 = match['equipe2_id']
        
        if pool_type == 'Classique':
            # Pour Classique, ordre trié (A-B == B-A)
            pair_key = tuple(sorted([eq1, eq2]))
        else:
            # Pour Aller-Retour, ordre exact (A→B ≠ B→A)
            pair_key = (eq1, eq2)
        
        pair_counts[pair_key] += 1
    
    # Vérifier les doublons
    pool_duplicates = []
    
    for pair, count in pair_counts.items():
        if pool_type == 'Classique' and count > 1:
            pool_duplicates.append((pair, count))
        elif pool_type == 'Aller-Retour' and count > 2:
            pool_duplicates.append((pair, count))
    
    if pool_duplicates:
        print(f"   ❌ {pool_id}: {len(pool_duplicates)} doublon(s) détecté(s)")
        for pair, count in pool_duplicates:
            print(f"      → {pair[0]} vs {pair[1]}: {count} fois")
        duplicates_found += len(pool_duplicates)

if duplicates_found == 0:
    print(f"   ✅ Aucun doublon détecté")

# Résumé final
print(f"\n{'=' * 100}")
print(f"📈 RÉSUMÉ FINAL")
print(f"{'=' * 100}")

if errors:
    print(f"\n❌ {len(errors)} poule(s) avec erreurs:")
    for pool_id, msg in errors:
        print(f"   • {pool_id}: {msg}")
else:
    print(f"\n✅ Toutes les poules ont le nombre correct de matchs!")

if duplicates_found > 0:
    print(f"\n❌ {duplicates_found} doublon(s) détecté(s)")
else:
    print(f"✅ Aucun doublon détecté!")

if warnings:
    print(f"\n⚠️  {len(warnings)} avertissement(s):")
    for warning in warnings:
        print(f"   • {warning}")

# Verdict final
print(f"\n{'=' * 100}")
if len(errors) == 0 and duplicates_found == 0:
    print("🎉 VALIDATION RÉUSSIE : La solution est correcte!")
else:
    print("❌ VALIDATION ÉCHOUÉE : Des problèmes ont été détectés")
print(f"{'=' * 100}")

# Statistiques de matchs
print(f"\n📊 Statistiques globales des matchs:")
print(f"   • Matchs planifiés: {len(data['matches']['scheduled'])}")
print(f"   • Matchs non planifiés: {len(data['matches']['unscheduled'])}")
print(f"   • Total: {len(all_matches)}")

# Matchs fixes
nb_fixed = sum(1 for m in all_matches if m.get('is_fixed', False))
nb_entente = sum(1 for m in all_matches if m.get('is_entente', False))

print(f"   • Matchs fixés: {nb_fixed}")
print(f"   • Matchs entente: {nb_entente}")

print(f"\n✅ Script de validation terminé")
