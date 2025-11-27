#!/usr/bin/env python3
"""
Analyse approfondie du système d'équilibrage des matchs.

Ce script vérifie:
1. Distribution des matchs par équipe
2. Efficacité du système de bonus progressif
3. Équipes sous-servies et raisons possibles
4. Impact des contraintes sur l'équilibrage
"""

import json
from collections import defaultdict, Counter
from pathlib import Path
from typing import Dict, List, Tuple

def load_solution(filepath: str = "solutions/latest_volley.json") -> dict:
    """Charge la solution JSON."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def analyze_match_distribution(data: dict) -> Dict:
    """Analyse la distribution des matchs par équipe."""
    
    # Compter matchs par équipe
    matchs_par_equipe = defaultdict(lambda: {
        'scheduled': 0,
        'unscheduled': 0,
        'total': 0,
        'ententes': 0,
        'normaux': 0,
        'pool': None,
        'nom': None
    })
    
    # Récupérer les infos équipes
    equipes_data = {eq['id']: eq for eq in data['entities']['equipes']}
    
    # Analyser matchs planifiés
    for match in data['matches']['scheduled']:
        eq1_id = match['equipe1_id']
        eq2_id = match['equipe2_id']
        est_entente = match.get('est_entente', False)
        
        for eq_id in [eq1_id, eq2_id]:
            matchs_par_equipe[eq_id]['scheduled'] += 1
            matchs_par_equipe[eq_id]['total'] += 1
            if est_entente:
                matchs_par_equipe[eq_id]['ententes'] += 1
            else:
                matchs_par_equipe[eq_id]['normaux'] += 1
            
            if matchs_par_equipe[eq_id]['pool'] is None:
                eq_data = equipes_data.get(eq_id, {})
                matchs_par_equipe[eq_id]['pool'] = eq_data.get('poule', 'Unknown')
                matchs_par_equipe[eq_id]['nom'] = eq_data.get('nom', eq_id)
    
    # Analyser matchs non planifiés
    for match in data['matches']['unscheduled']:
        eq1_id = match['equipe1_id']
        eq2_id = match['equipe2_id']
        est_entente = match.get('est_entente', False)
        
        for eq_id in [eq1_id, eq2_id]:
            matchs_par_equipe[eq_id]['unscheduled'] += 1
            matchs_par_equipe[eq_id]['total'] += 1
            
            if matchs_par_equipe[eq_id]['pool'] is None:
                eq_data = equipes_data.get(eq_id, {})
                matchs_par_equipe[eq_id]['pool'] = eq_data.get('poule', 'Unknown')
                matchs_par_equipe[eq_id]['nom'] = eq_data.get('nom', eq_id)
    
    return matchs_par_equipe

def analyze_by_pool(matchs_par_equipe: Dict, data: dict) -> None:
    """Analyse par poule."""
    
    print("\n" + "=" * 100)
    print("📊 ANALYSE PAR POULE")
    print("=" * 100)
    
    # Grouper par poule
    equipes_par_poule = defaultdict(list)
    for eq_id, stats in matchs_par_equipe.items():
        equipes_par_poule[stats['pool']].append((eq_id, stats))
    
    # Types de poules
    types_poules = data.get('entities', {}).get('pools', {})
    
    for poule in sorted(equipes_par_poule.keys()):
        equipes = equipes_par_poule[poule]
        type_poule = types_poules.get(poule, {}).get('type', 'Unknown')
        
        print(f"\n🏐 Poule: {poule} ({type_poule})")
        print("-" * 100)
        
        # Statistiques de la poule
        scheduled_counts = [stats['scheduled'] for _, stats in equipes]
        total_counts = [stats['total'] for _, stats in equipes]
        
        min_scheduled = min(scheduled_counts)
        max_scheduled = max(scheduled_counts)
        avg_scheduled = sum(scheduled_counts) / len(scheduled_counts)
        
        print(f"   Équipes: {len(equipes)}")
        print(f"   Matchs planifiés: min={min_scheduled}, max={max_scheduled}, avg={avg_scheduled:.1f}")
        print(f"   Écart: {max_scheduled - min_scheduled} matchs")
        
        # Distribution
        distribution = Counter(scheduled_counts)
        print(f"   Distribution: {dict(distribution)}")
        
        # Afficher équipes sous-servies (< moyenne)
        equipes_sous_servies = [(eq_id, stats) for eq_id, stats in equipes 
                                if stats['scheduled'] < avg_scheduled]
        
        if equipes_sous_servies:
            print(f"\n   ⚠️  Équipes SOUS-SERVIES ({len(equipes_sous_servies)}):")
            for eq_id, stats in sorted(equipes_sous_servies, key=lambda x: x[1]['scheduled']):
                print(f"      • {stats['nom']}: {stats['scheduled']}/{stats['total']} matchs planifiés "
                      f"({stats['unscheduled']} non planifiés)")

def calculate_theoretical_bonus(n: int, config: dict) -> float:
    """Calcule le bonus théorique pour le n-ième match."""
    bonus_base = config.get('equilibrage_bonus_base', 100000.0)
    facteur = config.get('equilibrage_facteur_decroissance', 0.3)
    bonus_min = config.get('equilibrage_bonus_minimum', 50.0)
    
    bonus = bonus_base * (facteur ** n)
    return max(bonus, bonus_min)

def analyze_bonus_effectiveness(matchs_par_equipe: Dict, data: dict) -> None:
    """Analyse l'efficacité du système de bonus."""
    
    print("\n" + "=" * 100)
    print("💰 ANALYSE DU SYSTÈME DE BONUS PROGRESSIF")
    print("=" * 100)
    
    config = data.get('config', {})
    
    bonus_base = config.get('equilibrage_bonus_base')
    facteur = config.get('equilibrage_facteur_decroissance')
    bonus_min = config.get('equilibrage_bonus_minimum')
    entente_facteur = config.get('entente_facteur_reduction')
    
    print(f"\n📋 Configuration:")
    print(f"   • bonus_base: {bonus_base:,.0f}" if bonus_base else "   • bonus_base: N/A")
    print(f"   • facteur_decroissance: {facteur}" if facteur else "   • facteur_decroissance: N/A")
    print(f"   • bonus_minimum: {bonus_min:,.0f}" if bonus_min else "   • bonus_minimum: N/A")
    print(f"   • entente_facteur_reduction: {entente_facteur}" if entente_facteur else "   • entente_facteur_reduction: N/A")
    
    print(f"\n📈 Bonus théoriques (matchs normaux):")
    for i in range(6):
        bonus = calculate_theoretical_bonus(i, config)
        print(f"   Match #{i+1}: {bonus:>12,.0f}")
    
    # Vérifier si le système est actif
    scheduled_counts = [stats['scheduled'] for stats in matchs_par_equipe.values()]
    min_matches = min(scheduled_counts)
    max_matches = max(scheduled_counts)
    
    print(f"\n🎯 Résultat observé:")
    print(f"   • Min matchs planifiés: {min_matches}")
    print(f"   • Max matchs planifiés: {max_matches}")
    print(f"   • Écart: {max_matches - min_matches}")
    
    # Calculer le ratio bonus 1er vs 2ème match
    bonus_1 = calculate_theoretical_bonus(0, config)
    bonus_2 = calculate_theoretical_bonus(1, config)
    ratio = bonus_1 / bonus_2 if bonus_2 > 0 else float('inf')
    
    print(f"\n🔍 Ratio bonus 1er/2ème match: {ratio:.2f}x")
    
    if ratio < 2:
        print("   ⚠️  ATTENTION: Le ratio est faible (<2). Le système peut ne pas être assez incitatif.")
        print("      Suggestion: Diminuer facteur_decroissance (actuellement {:.2f})".format(
            config.get('equilibrage_facteur_decroissance', 0.3)))

def find_problematic_teams(matchs_par_equipe: Dict, data: dict) -> None:
    """Identifie les équipes problématiques et cherche les raisons."""
    
    print("\n" + "=" * 100)
    print("🔍 ÉQUIPES PROBLÉMATIQUES - ANALYSE APPROFONDIE")
    print("=" * 100)
    
    equipes_data = {eq['id']: eq for eq in data['entities']['equipes']}
    
    # Trouver équipes avec trop peu de matchs
    scheduled_counts = [stats['scheduled'] for stats in matchs_par_equipe.values()]
    avg_scheduled = sum(scheduled_counts) / len(scheduled_counts)
    threshold = avg_scheduled * 0.7  # Moins de 70% de la moyenne
    
    problematic = [(eq_id, stats) for eq_id, stats in matchs_par_equipe.items() 
                   if stats['scheduled'] < threshold and stats['total'] > 0]
    
    if not problematic:
        print("\n✅ Aucune équipe problématique détectée (toutes au-dessus de 70% de la moyenne)")
        return
    
    print(f"\n⚠️  {len(problematic)} équipe(s) problématique(s) détectée(s):")
    print(f"    (Moyenne: {avg_scheduled:.1f}, Seuil: {threshold:.1f})")
    
    for eq_id, stats in sorted(problematic, key=lambda x: x[1]['scheduled']):
        eq_data = equipes_data.get(eq_id, {})
        
        print(f"\n   🚨 {stats['nom']} ({stats['pool']})")
        print(f"      Matchs planifiés: {stats['scheduled']}/{stats['total']} ({stats['scheduled']/stats['total']*100:.1f}%)")
        print(f"      Matchs non planifiés: {stats['unscheduled']}")
        print(f"      Normaux/Ententes: {stats['normaux']}/{stats['ententes']}")
        
        # Analyser les indisponibilités
        indispos = eq_data.get('semaines_indisponibles', {})
        if indispos:
            total_indispos = sum(len(horaires) for horaires in indispos.values())
            print(f"      ⚠️  Indisponibilités: {len(indispos)} semaines, {total_indispos} créneaux")
            # Afficher détails
            for semaine, horaires in sorted(indispos.items(), key=lambda x: int(x[0])):
                print(f"         • S{semaine}: {', '.join(sorted(horaires))}")
        
        # Analyser les préférences horaires
        horaires_pref = eq_data.get('horaires_preferes', [])
        if horaires_pref:
            print(f"      Horaires préférés: {', '.join(horaires_pref)}")

def main():
    """Fonction principale."""
    
    print("=" * 100)
    print("🔬 ANALYSE APPROFONDIE DU SYSTÈME D'ÉQUILIBRAGE")
    print("=" * 100)
    
    # Charger la solution
    solution_file = "solutions/latest_volley.json"
    print(f"\n📥 Chargement: {solution_file}")
    
    data = load_solution(solution_file)
    
    print(f"   Version: {data.get('version', 'Unknown')}")
    print(f"   Score: {data.get('metadata', {}).get('score', 'Unknown')}")
    print(f"   Matchs planifiés: {data.get('metadata', {}).get('matchs_planifies', 'Unknown')}")
    
    # Analyser distribution
    matchs_par_equipe = analyze_match_distribution(data)
    
    # Analyses
    analyze_bonus_effectiveness(matchs_par_equipe, data)
    analyze_by_pool(matchs_par_equipe, data)
    find_problematic_teams(matchs_par_equipe, data)
    
    # Résumé final
    print("\n" + "=" * 100)
    print("📝 RÉSUMÉ & RECOMMANDATIONS")
    print("=" * 100)
    
    scheduled_counts = [stats['scheduled'] for stats in matchs_par_equipe.values()]
    min_matches = min(scheduled_counts)
    max_matches = max(scheduled_counts)
    avg_matches = sum(scheduled_counts) / len(scheduled_counts)
    
    print(f"\n   Distribution globale: min={min_matches}, max={max_matches}, avg={avg_matches:.1f}")
    print(f"   Écart: {max_matches - min_matches} matchs")
    
    if max_matches - min_matches > 2:
        print("\n   ❌ PROBLÈME: Écart trop important (>2)")
        print("      Causes possibles:")
        print("      1. Facteur de décroissance trop élevé → bonus insuffisamment différenciés")
        print("      2. Bonus minimum trop élevé → annule la décroissance")
        print("      3. Indisponibilités bloquent certaines équipes")
        print("      4. Contraintes trop strictes limitent les placements possibles")
    else:
        print("\n   ✅ Écart acceptable (≤2)")

if __name__ == "__main__":
    main()
