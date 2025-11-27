#!/usr/bin/env python3
"""
Tableau de bord synthétique - Vue d'ensemble rapide des problèmes de config.
"""

def print_box(title: str, lines: list, color: str = ""):
    """Affiche un encadré coloré."""
    width = max(len(line) for line in lines) + 4
    
    print("┌" + "─" * width + "┐")
    print("│ " + title.ljust(width - 2) + " │")
    print("├" + "─" * width + "┤")
    for line in lines:
        print("│ " + line.ljust(width - 2) + " │")
    print("└" + "─" * width + "┘")

def main():
    print()
    print("╔" + "═" * 78 + "╗")
    print("║" + " TABLEAU DE BORD - ANALYSE CONFIGURATION YAML ".center(78) + "║")
    print("╚" + "═" * 78 + "╝")
    print()
    
    # Statistiques globales
    print("📊 STATISTIQUES GLOBALES")
    print("─" * 80)
    print(f"  Total paramètres définis:        56")
    print(f"  Paramètres à supprimer:           7 (ou 11 avec calendrier)")
    print(f"  Paramètres validés OK:            49 (87%)")
    print(f"  Fichiers à modifier:              4")
    print(f"  Lignes de code à supprimer:       ~250")
    print()
    
    # Tableau des problèmes
    print("🔍 PROBLÈMES PAR SÉVÉRITÉ")
    print("─" * 80)
    
    problems = [
        ("🔴", "MAJEUR", "entente_facteur_reduction", "Conflit logique", "4 fichiers"),
        ("🔴", "MAJEUR", "qualite_match (4 params)", "Code mort", "3 fichiers"),
        ("🟡", "MINEUR", "nb_preferences_gymnases", "Redondant", "2 fichiers"),
        ("🟡", "MINEUR", "aller_retour_min_semaines", "Non utilisé", "2 fichiers"),
        ("🔵", "INFO", "calendrier (4 params)", "Décision requise", "2 fichiers"),
    ]
    
    print(f"{'Emoji':<7} {'Sévérité':<10} {'Paramètre':<30} {'Type':<18} {'Impact':<12}")
    print("─" * 80)
    for emoji, severity, param, ptype, impact in problems:
        print(f"{emoji:<7} {severity:<10} {param:<30} {ptype:<18} {impact:<12}")
    print()
    
    # Détail par problème
    print("📋 DÉTAIL DES PROBLÈMES")
    print("─" * 80)
    print()
    
    print_box("🔴 #1: entente_facteur_reduction", [
        "Type: CONFLIT LOGIQUE",
        "Fichiers: config.py, cpsat_solver.py, greedy_solver.py, default.yaml",
        "",
        "Problème:",
        "  Deux systèmes de réduction simultanés:",
        "  • Ancien: multiplication par 0.1 (ligne 132)",
        "  • Nouveau: réduction cumulative 0.90^n (ligne 761)",
        "",
        "Action:",
        "  Supprimer entente_facteur_reduction (4 endroits)",
        "  Garder entente_facteur_reduction_bonus"
    ])
    print()
    
    print_box("🔴 #2: Système qualite_match", [
        "Type: CODE MORT",
        "Fichiers: config.py, cpsat_solver.py, default.yaml",
        "",
        "Problème:",
        "  Système désactivé depuis longtemps",
        "  Commentaire: 'système non fonctionnel'",
        "  4 paramètres + ~200 lignes de code inaccessibles",
        "",
        "Action:",
        "  Supprimer 4 paramètres + code associé"
    ])
    print()
    
    print_box("🟡 #3-4: Paramètres redondants/non utilisés", [
        "Type: NETTOYAGE",
        "Fichiers: config.py, default.yaml",
        "",
        "Problèmes:",
        "  • nb_preferences_gymnases: redondant avec len(liste)",
        "  • aller_retour_min_semaines: jamais utilisé",
        "",
        "Action:",
        "  Supprimer 2 paramètres"
    ])
    print()
    
    print_box("🔵 #5: Paramètres calendrier", [
        "Type: DÉCISION REQUISE",
        "Fichiers: config.py, default.yaml",
        "",
        "Situation:",
        "  4 paramètres définis mais non implémentés",
        "  Usage prévu: conversion semaine→date, vacances",
        "",
        "Options:",
        "  A) GARDER avec TODO (fonctionnalité future)",
        "  B) SUPPRIMER si abandon définitif",
        "",
        "Recommandation: OPTION A"
    ])
    print()
    
    # Plan d'action
    print("✅ PLAN D'ACTION")
    print("─" * 80)
    print()
    print("PHASE 1 - Priorité Haute (1-2h):")
    print("  □ Supprimer qualite_match (4 params, ~200 lignes)")
    print("  □ Supprimer entente_facteur_reduction (1 param, 4 lignes)")
    print()
    print("PHASE 2 - Priorité Moyenne (30min):")
    print("  □ Supprimer nb_preferences_gymnases")
    print("  □ Supprimer aller_retour_min_semaines")
    print()
    print("PHASE 3 - Selon roadmap:")
    print("  □ Décision calendrier (garder/supprimer)")
    print()
    
    # Résultats attendus
    print("🎯 RÉSULTATS ATTENDUS")
    print("─" * 80)
    print("  ✓ Configuration plus claire et cohérente")
    print("  ✓ Suppression code mort (~250 lignes)")
    print("  ✓ Élimination confusion entente_facteur_*")
    print("  ✓ Séparation nette: params actifs/futurs/obsolètes")
    print("  ✓ Maintenance facilitée")
    print()
    
    # Risques
    print("⚠️  RISQUES")
    print("─" * 80)
    print("  Niveau de risque: 🟢 TRÈS FAIBLE")
    print()
    print("  Justification:")
    print("    • Code mort (jamais exécuté)")
    print("    • Paramètres non utilisés")
    print("    • Aucun test ne dépend de ces paramètres")
    print()
    print("  Précautions:")
    print("    • Git commit avant modifications")
    print("    • Tester génération interface après")
    print("    • Vérifier solution volleyball après")
    print()
    
    # Commandes utiles
    print("🛠️  COMMANDES UTILES")
    print("─" * 80)
    print()
    print("Voir analyse automatique:")
    print("  $ python temp_tests/analyze_config_params.py")
    print()
    print("Voir rapport détaillé:")
    print("  $ python temp_tests/analyse_finale_config.py")
    print()
    print("Voir propositions détaillées:")
    print("  $ python temp_tests/propositions_corrections_config.py")
    print()
    print("Voir ce dashboard:")
    print("  $ python temp_tests/dashboard_config.py")
    print()
    
    print("─" * 80)
    print()

if __name__ == '__main__':
    main()
