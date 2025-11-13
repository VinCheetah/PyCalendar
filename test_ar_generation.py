#!/usr/bin/env python3
"""Script pour tester la génération des matchs aller-retour."""

import sys
sys.path.insert(0, 'src')

from pycalendar.orchestrator.pipeline import SchedulingPipeline

# Créer le pipeline
pipeline = SchedulingPipeline('examples/volleyball/config_volley.xlsx')

# Charger les types de poules
types_poules = pipeline.source.charger_types_poules()

print("=" * 80)
print("VÉRIFICATION GÉNÉRATION MATCHS ALLER-RETOUR")
print("=" * 80)

print(f"\n📋 Types de poules chargés: {len(types_poules)}")
nb_ar = sum(1 for t in types_poules.values() if t == 'Aller-Retour')
print(f"   Aller-Retour: {nb_ar}")
print(f"   Classique: {len(types_poules) - nb_ar}")

# Charger les équipes et créer les poules
equipes = pipeline.source.charger_equipes()
from collections import defaultdict
poules = defaultdict(list)
for eq in equipes:
    poules[eq.poule].append(eq)

# Générer les matchs
from pycalendar.generators.multi_pool_generator import MultiPoolGenerator
generator = MultiPoolGenerator(types_poules)
matchs = generator.generer_tous_matchs(poules)

print(f"\n⚙️  Matchs générés: {len(matchs)}")

# Analyser chaque poule AR
print("\n🔍 Analyse des poules Aller-Retour:")
print("-" * 80)
print(f"{'Poule':12} {'Type':15} {'Équipes':8} {'Matchs':8} {'Attendu':8}  Statut")
print("-" * 80)

problemes = []
for poule_id in sorted(types_poules.keys()):
    type_poule = types_poules[poule_id]
    if type_poule != 'Aller-Retour':
        continue
    
    nb_eq = len(poules[poule_id])
    matchs_poule = [m for m in matchs if m.poule == poule_id]
    nb_matchs = len(matchs_poule)
    
    # Pour aller-retour: n * (n-1)
    attendu = nb_eq * (nb_eq - 1)
    
    statut = '✅ OK' if nb_matchs == attendu else '❌ ERREUR'
    if nb_matchs != attendu:
        problemes.append((poule_id, nb_eq, nb_matchs, attendu))
    
    print(f"{poule_id:12} {type_poule:15} {nb_eq:8} {nb_matchs:8} {attendu:8}  {statut}")

print("-" * 80)
print(f"\n📊 RÉSUMÉ:")
print(f"   Poules AR analysées: {nb_ar}")
print(f"   Poules avec problème: {len(problemes)}")

if problemes:
    print(f"\n❌ PROBLÈMES DÉTECTÉS:")
    for pid, neq, generated, expected in problemes:
        print(f"   {pid}: {generated} matchs générés au lieu de {expected}")
else:
    print(f"\n✅ Toutes les poules AR ont le bon nombre de matchs !")
