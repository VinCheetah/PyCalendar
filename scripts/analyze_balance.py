#!/usr/bin/env python3
"""Analyse l'équilibrage des matchs par équipe dans une solution."""

import json
import sys
from collections import defaultdict
from pathlib import Path


def analyze_balance(solution_file: str):
    """Analyse l'équilibrage des matchs."""
    
    with open(solution_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Compter les matchs par équipe et par poule
    matchs_par_equipe = defaultdict(lambda: {'planifies': 0, 'totaux': 0})
    matchs_par_poule = defaultdict(lambda: {'planifies': 0, 'totaux': 0})
    equipes_par_poule = defaultdict(set)
    
    # Traiter tous les matchs (supporter V1 et V2)
    # IMPORTANT: Exclure les matchs d'entente car ils ne doivent pas être comptés
    # dans l'équilibrage (les ententes sont censées ne PAS être planifiées)
    if 'matches' in data:  # V2
        scheduled = data['matches'].get('scheduled', [])
        unscheduled = data['matches'].get('unscheduled', [])
        all_matchs = scheduled + unscheduled
        
        for match in all_matchs:
            # Vérifier si c'est une entente
            is_entente = match.get('is_entente', False)
            
            # Exclure les ententes de l'analyse d'équilibrage
            if not is_entente:
                eq1 = match['equipe1_nom_complet']
                eq2 = match['equipe2_nom_complet']
                poule = match['poule']
                is_planifie = 'semaine' in match and match['semaine'] is not None
            
                # Compter totaux
                matchs_par_equipe[eq1]['totaux'] += 1
                matchs_par_equipe[eq2]['totaux'] += 1
                matchs_par_poule[poule]['totaux'] += 1
                
                # Compter planifiés
                if is_planifie:
                    matchs_par_equipe[eq1]['planifies'] += 1
                    matchs_par_equipe[eq2]['planifies'] += 1
                    matchs_par_poule[poule]['planifies'] += 1
                
                # Grouper équipes par poule
                equipes_par_poule[poule].add(eq1)
                equipes_par_poule[poule].add(eq2)
    else:  # V1
        all_matchs = data.get('matchs_planifies', []) + data.get('matchs_non_planifies', [])
        
        for match in all_matchs:
            # Vérifier si c'est une entente
            is_entente = match.get('metadata', {}).get('is_entente', False)
            
            # Exclure les ententes de l'analyse d'équilibrage
            if not is_entente:
                eq1 = match['equipe1']['nom_complet']
                eq2 = match['equipe2']['nom_complet']
                poule = match['poule']
                is_planifie = 'creneau' in match and match['creneau'] is not None
                
                # Compter totaux
                matchs_par_equipe[eq1]['totaux'] += 1
                matchs_par_equipe[eq2]['totaux'] += 1
                matchs_par_poule[poule]['totaux'] += 1
                
                # Compter planifiés
                if is_planifie:
                    matchs_par_equipe[eq1]['planifies'] += 1
                    matchs_par_equipe[eq2]['planifies'] += 1
                    matchs_par_poule[poule]['planifies'] += 1
                
                # Grouper équipes par poule
                equipes_par_poule[poule].add(eq1)
                equipes_par_poule[poule].add(eq2)
    
    print("=" * 80)
    print("ANALYSE D'ÉQUILIBRAGE DES MATCHS PAR ÉQUIPE")
    print("=" * 80)
    print()
    
    # === NIVEAU 1: PETITES POULES ===
    print("📊 NIVEAU 1 - PRIORITÉ AUX PETITES POULES (≤10 matchs)")
    print("-" * 80)
    
    petites_poules = {p: stats for p, stats in matchs_par_poule.items() 
                      if stats['totaux'] <= 10}
    
    if petites_poules:
        for poule, stats in sorted(petites_poules.items()):
            taux = (stats['planifies'] / stats['totaux'] * 100) if stats['totaux'] > 0 else 0
            status = "✓" if taux >= 90 else "⚠️"
            print(f"{status} {poule}: {stats['planifies']}/{stats['totaux']} matchs ({taux:.1f}%)")
        
        # Stats globales
        total_planif = sum(s['planifies'] for s in petites_poules.values())
        total_poss = sum(s['totaux'] for s in petites_poules.values())
        taux_global = (total_planif / total_poss * 100) if total_poss > 0 else 0
        print(f"\n📈 Global petites poules: {total_planif}/{total_poss} ({taux_global:.1f}%)")
    else:
        print("  Aucune petite poule (≤10 matchs)")
    
    print()
    
    # === NIVEAU 2: ÉQUITÉ INTRA-POULE ===
    print("⚖️  NIVEAU 2 - ÉQUITÉ INTRA-POULE (tolérance ±1 match)")
    print("-" * 80)
    
    for poule in sorted(equipes_par_poule.keys()):
        equipes = sorted(equipes_par_poule[poule])
        if len(equipes) <= 1:
            continue
        
        # Calculer taux de planification de chaque équipe
        taux_equipes = []
        for eq in equipes:
            stats = matchs_par_equipe[eq]
            taux = (stats['planifies'] / stats['totaux']) if stats['totaux'] > 0 else 0
            taux_equipes.append((eq, stats['planifies'], stats['totaux'], taux))
        
        # Trier par taux
        taux_equipes.sort(key=lambda x: x[3])
        
        # Calculer écart max
        min_taux = taux_equipes[0][3]
        max_taux = taux_equipes[-1][3]
        ecart_taux = max_taux - min_taux
        
        # Calculer écart absolu max
        min_planif = min(t[1] for t in taux_equipes)
        max_planif = max(t[1] for t in taux_equipes)
        ecart_abs = max_planif - min_planif
        
        # Status
        status = "✓" if ecart_abs <= 1 else "⚠️"
        
        print(f"\n{status} {poule} ({len(equipes)} équipes, {matchs_par_poule[poule]['totaux']} matchs):")
        print(f"   Écart: {ecart_abs} matchs, {ecart_taux*100:.1f}% taux")
        
        # Afficher détails si déséquilibre
        if ecart_abs > 1:
            for eq, planif, total, taux in taux_equipes:
                print(f"     • {eq}: {planif}/{total} ({taux*100:.1f}%)")
    
    print()
    
    # === NIVEAU 3: ÉQUILIBRAGE GLOBAL ===
    print("🌍 NIVEAU 3 - ÉQUILIBRAGE GLOBAL")
    print("-" * 80)
    
    # Calculer stats globales
    taux_globaux = []
    for eq, stats in matchs_par_equipe.items():
        taux = (stats['planifies'] / stats['totaux']) if stats['totaux'] > 0 else 0
        taux_globaux.append(taux)
    
    if taux_globaux:
        import statistics
        
        mean_taux = statistics.mean(taux_globaux)
        stdev_taux = statistics.stdev(taux_globaux) if len(taux_globaux) > 1 else 0
        min_taux = min(taux_globaux)
        max_taux = max(taux_globaux)
        
        print(f"Taux de planification moyen: {mean_taux*100:.1f}%")
        print(f"Écart-type: {stdev_taux*100:.2f}%")
        print(f"Min: {min_taux*100:.1f}% / Max: {max_taux*100:.1f}%")
        print(f"Amplitude: {(max_taux - min_taux)*100:.1f}%")
        
        # Top 5 équipes avec moins de matchs
        equipes_sorted = sorted(matchs_par_equipe.items(), 
                               key=lambda x: x[1]['planifies'] / x[1]['totaux'] if x[1]['totaux'] > 0 else 0)
        
        print("\n🔻 Top 5 équipes avec le moins de matchs planifiés (taux):")
        for eq, stats in equipes_sorted[:5]:
            taux = (stats['planifies'] / stats['totaux'] * 100) if stats['totaux'] > 0 else 0
            print(f"   • {eq}: {stats['planifies']}/{stats['totaux']} ({taux:.1f}%)")
        
        print("\n🔺 Top 5 équipes avec le plus de matchs planifiés (taux):")
        for eq, stats in reversed(equipes_sorted[-5:]):
            taux = (stats['planifies'] / stats['totaux'] * 100) if stats['totaux'] > 0 else 0
            print(f"   • {eq}: {stats['planifies']}/{stats['totaux']} ({taux:.1f}%)")
    
    print()
    print("=" * 80)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_balance.py <solution.json>")
        sys.exit(1)
    
    solution_file = sys.argv[1]
    if not Path(solution_file).exists():
        print(f"Erreur: Fichier {solution_file} introuvable")
        sys.exit(1)
    
    analyze_balance(solution_file)
