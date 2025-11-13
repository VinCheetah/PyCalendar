#!/usr/bin/env python3
"""
Script d'extraction et d'affichage des pénalités depuis une solution JSON.
Utile pour analyser rapidement les pénalités sans interface web.

Usage:
    python scripts/show_penalties.py [chemin_solution.json]
    
Si aucun chemin n'est fourni, utilise solutions/latest_volley.json
"""

import sys
import json
from pathlib import Path


def format_penalty_value(value: float) -> str:
    """Formate une valeur de pénalité avec couleur"""
    if value < 0:
        return f"\033[92m{value:+.2f}\033[0m"  # Vert (bonus)
    elif value == 0:
        return f"{value:.2f}"
    else:
        return f"\033[91m+{value:.2f}\033[0m"  # Rouge (pénalité)


def show_penalties(json_path: str):
    """Affiche la décomposition des pénalités d'une solution"""
    
    # Charger le JSON
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Vérifier présence des pénalités
    if 'penalty_breakdown' not in data.get('metadata', {}):
        print("❌ Aucune décomposition de pénalités trouvée dans cette solution.")
        print("   Relancez la résolution avec la version mise à jour pour générer les pénalités.")
        return 1
    
    breakdown = data['metadata']['penalty_breakdown']
    
    # Header
    print("=" * 80)
    print(" " * 20 + "📊 DÉCOMPOSITION DES PÉNALITÉS")
    print("=" * 80)
    
    # Score total
    score = breakdown['score_total']
    if score < 0:
        quality = "EXCELLENTE"
        color = "\033[92m"  # Vert
    elif score < 100:
        quality = "BONNE"
        color = "\033[93m"  # Jaune
    elif score < 1000:
        quality = "MOYENNE"
        color = "\033[93m"
    else:
        quality = "PROBLÉMATIQUE"
        color = "\033[91m"  # Rouge
    
    print(f"\n🎯 Score Total: {color}{score:.2f}\033[0m ({quality})\n")
    
    # 1. Contraintes Dures
    print("━" * 80)
    print("🚫 CONTRAINTES DURES")
    print("━" * 80)
    
    dures = breakdown['contraintes_dures']
    print(f"  Indisponibilité équipes/institutions")
    print(f"    Violations : {dures['indisponibilite']['violations']}")
    print(f"    Pénalité   : {format_penalty_value(dures['indisponibilite']['penalty'])}")
    print()
    print(f"  Capacité gymnases")
    print(f"    Violations : {dures['capacite']['violations']}")
    print(f"    Pénalité   : {format_penalty_value(dures['capacite']['penalty'])}")
    
    total_dures = dures['indisponibilite']['penalty'] + dures['capacite']['penalty']
    print(f"\n  TOTAL : {format_penalty_value(total_dures)}")
    
    # 2. Préférences Gymnases
    print("\n" + "━" * 80)
    print("🏟️  PRÉFÉRENCES GYMNASES")
    print("━" * 80)
    
    pref = breakdown['preferences_gymnases']
    print(f"  Matchs en gymnases préférés : {pref['matchs_en_gymnases_preferes']}")
    print(f"  Bonus total                 : {format_penalty_value(pref['bonus_total'])}")
    
    # 3. Niveau Gymnases
    print("\n" + "━" * 80)
    print("🏆 NIVEAU GYMNASES")
    print("━" * 80)
    
    niveau = breakdown['niveau_gymnases']
    print(f"  Matchs bien assignés (bonus)")
    print(f"    Count : {niveau['matchs_bien_assignes']}")
    print(f"    Bonus : {format_penalty_value(niveau['bonus_total'])}")
    print()
    print(f"  Matchs mal assignés (pénalité)")
    print(f"    Count    : {niveau['matchs_mal_assignes']}")
    print(f"    Pénalité : {format_penalty_value(niveau['penalty_total'])}")
    
    total_niveau = niveau['bonus_total'] + niveau['penalty_total']
    print(f"\n  TOTAL : {format_penalty_value(total_niveau)}")
    
    # 4. Horaires Préférés
    print("\n" + "━" * 80)
    print("⏰ HORAIRES PRÉFÉRÉS")
    print("━" * 80)
    
    horaires = breakdown['horaires_preferes']
    print(f"  ✅ Matchs OK (dans horaire/tolérance) : {horaires['matchs_ok']}")
    print()
    print(f"  🟡 Matchs après horaire préféré")
    print(f"     Count    : {horaires['matchs_apres']['count']}")
    print(f"     Pénalité : {format_penalty_value(horaires['matchs_apres']['penalty'])}")
    print()
    print(f"  🟠 Matchs avant horaire (1 équipe)")
    print(f"     Count    : {horaires['matchs_avant_1_equipe']['count']}")
    print(f"     Pénalité : {format_penalty_value(horaires['matchs_avant_1_equipe']['penalty'])}")
    print()
    print(f"  🔴 Matchs avant horaire (2 équipes)")
    print(f"     Count    : {horaires['matchs_avant_2_equipes']['count']}")
    print(f"     Pénalité : {format_penalty_value(horaires['matchs_avant_2_equipes']['penalty'])}")
    
    total_horaires = (horaires['matchs_apres']['penalty'] + 
                     horaires['matchs_avant_1_equipe']['penalty'] + 
                     horaires['matchs_avant_2_equipes']['penalty'])
    print(f"\n  TOTAL : {format_penalty_value(total_horaires)}")
    
    # 5. Compaction Temporelle
    print("\n" + "━" * 80)
    print("📅 COMPACTION TEMPORELLE")
    print("━" * 80)
    
    compaction = breakdown['compaction_temporelle']
    print(f"  Répartition par semaine:")
    for week in sorted([int(w) for w in compaction['par_semaine'].keys()]):
        data_week = compaction['par_semaine'][str(week)]
        print(f"    Semaine {week:2d} : {data_week['nb_matchs']:3d} matchs → {format_penalty_value(data_week['penalty'])}")
    
    print(f"\n  TOTAL : {format_penalty_value(compaction['penalty_total'])}")
    
    # 6. Espacement Repos
    print("\n" + "━" * 80)
    print("📊 ESPACEMENT REPOS")
    print("━" * 80)
    
    espacement = breakdown['espacement_repos']
    print(f"  Violations : {espacement['violations']}")
    print(f"  Pénalité   : {format_penalty_value(espacement['penalty'])}")
    
    # 7. Contraintes Institutionnelles
    print("\n" + "━" * 80)
    print("🏫 CONTRAINTES INSTITUTIONNELLES")
    print("━" * 80)
    
    inst = breakdown['contraintes_institutionnelles']
    print(f"  Overlaps (matchs simultanés)")
    print(f"    Count    : {inst['overlaps']['count']}")
    print(f"    Pénalité : {format_penalty_value(inst['overlaps']['penalty'])}")
    print()
    print(f"  Ententes")
    print(f"    Planifiées     : {inst['ententes']['planifiees']}")
    print(f"    Non planifiées : {inst['ententes']['non_planifiees']}")
    print(f"    Pénalité       : {format_penalty_value(inst['ententes']['penalty'])}")
    
    total_inst = inst['overlaps']['penalty'] + inst['ententes']['penalty']
    print(f"\n  TOTAL : {format_penalty_value(total_inst)}")
    
    # 8. Contraintes Temporelles
    temp = breakdown['contraintes_temporelles']
    if temp['violations'] > 0 or temp['penalty'] > 0:
        print("\n" + "━" * 80)
        print("⏱️  CONTRAINTES TEMPORELLES (CFE, etc.)")
        print("━" * 80)
        print(f"  Violations : {temp['violations']}")
        print(f"  Pénalité   : {format_penalty_value(temp['penalty'])}")
    
    # 9. Aller-Retour
    ar = breakdown['aller_retour']
    if ar['meme_semaine']['count'] > 0 or ar['consecutives']['count'] > 0:
        print("\n" + "━" * 80)
        print("🔄 ESPACEMENT ALLER-RETOUR")
        print("━" * 80)
        print(f"  Même semaine")
        print(f"    Count    : {ar['meme_semaine']['count']}")
        print(f"    Pénalité : {format_penalty_value(ar['meme_semaine']['penalty'])}")
        print()
        print(f"  Semaines consécutives")
        print(f"    Count    : {ar['consecutives']['count']}")
        print(f"    Pénalité : {format_penalty_value(ar['consecutives']['penalty'])}")
    
    # 10. Équilibrage Charge
    equilibrage = breakdown['equilibrage_charge']
    if equilibrage['penalty'] > 0:
        print("\n" + "━" * 80)
        print("⚖️  ÉQUILIBRAGE CHARGE")
        print("━" * 80)
        print(f"  Pénalité : {format_penalty_value(equilibrage['penalty'])}")
    
    # Résumé
    print("\n" + "=" * 80)
    print("📈 RÉSUMÉ")
    print("=" * 80)
    
    categories = [
        ("Contraintes Dures", total_dures),
        ("Préférences Gymnases", pref['bonus_total']),
        ("Niveau Gymnases", total_niveau),
        ("Horaires Préférés", total_horaires),
        ("Espacement Repos", espacement['penalty']),
        ("Compaction Temporelle", compaction['penalty_total']),
        ("Institutions", total_inst),
        ("Contraintes Temporelles", temp['penalty']),
        ("Aller-Retour", ar['meme_semaine']['penalty'] + ar['consecutives']['penalty']),
        ("Équilibrage Charge", equilibrage['penalty'])
    ]
    
    total_bonus = sum(val for _, val in categories if val < 0)
    total_penalties = sum(val for _, val in categories if val > 0)
    
    print(f"\n  Total Bonus      : \033[92m{total_bonus:.2f}\033[0m")
    print(f"  Total Pénalités  : \033[91m+{total_penalties:.2f}\033[0m")
    print(f"  {'─' * 40}")
    print(f"  SCORE FINAL      : {format_penalty_value(score)}")
    
    print("\n" + "=" * 80 + "\n")
    
    return 0


def main():
    # Déterminer le chemin du JSON
    if len(sys.argv) > 1:
        json_path = sys.argv[1]
    else:
        json_path = "solutions/latest_volley.json"
    
    json_path = Path(json_path)
    
    if not json_path.exists():
        print(f"❌ Fichier non trouvé : {json_path}")
        print(f"\nUsage: python {sys.argv[0]} [chemin_solution.json]")
        return 1
    
    print(f"\n📂 Analyse de : {json_path}\n")
    return show_penalties(str(json_path))


if __name__ == "__main__":
    sys.exit(main())
