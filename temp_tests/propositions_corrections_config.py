#!/usr/bin/env python3
"""
Propositions de corrections pour les problèmes de configuration identifiés.
Ce script génère des recommandations concrètes pour chaque problème.
"""

import sys
from pathlib import Path

def print_section(title: str):
    """Affiche un titre de section."""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80 + "\n")

def print_problem(num: int, title: str, severity: str):
    """Affiche un numéro de problème."""
    symbols = {'CRITIQUE': '🔴', 'MAJEUR': '🟠', 'MINEUR': '🟡', 'INFO': '🔵'}
    print(f"\n{symbols.get(severity, '⚪')} PROBLÈME #{num}: {title} [{severity}]")
    print("-" * 80)

def main():
    print_section("RAPPORT D'ANALYSE CRITIQUE - CONFIGURATION YAML")
    
    print("Basé sur l'analyse automatisée, voici les problèmes identifiés et")
    print("les corrections proposées pour chaque paramètre problématique.\n")
    
    # ========================================================================
    # PROBLÈME 1: entente_facteur_reduction (OBSOLÈTE mais utilisé)
    # ========================================================================
    print_problem(1, "entente_facteur_reduction - Paramètre obsolète encore utilisé", "MAJEUR")
    
    print("DIAGNOSTIC:")
    print("  - Marqué 'OBSOLÈTE' dans config.py (ligne 82)")
    print("  - Mais encore utilisé dans:")
    print("    * cpsat_solver.py ligne 132: bonus *= self.config.entente_facteur_reduction")
    print("    * greedy_solver.py ligne 101: bonus *= self.config.entente_facteur_reduction")
    print()
    print("CONTEXTE:")
    print("  Système d'équilibrage max-min fairness avec bonus progressif.")
    print("  Les ententes reçoivent un bonus réduit pour les planifier en dernier.")
    print("  Deux paramètres similaires existent:")
    print("    - entente_facteur_reduction (float, multiplication directe, OBSOLÈTE)")
    print("    - entente_facteur_reduction_bonus (float, réduction cumulative du bonus total)")
    print()
    print("PROPOSITION DE CORRECTION:")
    print("  OPTION A [RECOMMANDÉE]: Supprimer entente_facteur_reduction")
    print("    1. Retirer le paramètre de config.py (ligne 82)")
    print("    2. Retirer du from_yaml() (ligne 251)")
    print("    3. Retirer du to_yaml() (ligne 347)")
    print("    4. Modifier cpsat_solver.py ligne 132:")
    print("       ANCIEN: bonus *= self.config.entente_facteur_reduction")
    print("       NOUVEAU: # Réduction via entente_facteur_reduction_bonus (appliqué globalement)")
    print("    5. Modifier greedy_solver.py ligne 101 (idem)")
    print()
    print("  OPTION B [Alternative]: Clarifier les deux systèmes")
    print("    - Garder les deux paramètres avec documentation claire")
    print("    - entente_facteur_reduction: réduction par match (legacy)")
    print("    - entente_facteur_reduction_bonus: réduction cumulative (nouveau)")
    print()
    print("  RECOMMANDATION: Option A - Le système actuel utilise déjà")
    print("  entente_facteur_reduction_bonus ligne 761 cpsat_solver.py")
    print()
    
    # ========================================================================
    # PROBLÈME 2: Système qualite_match désactivé
    # ========================================================================
    print_problem(2, "Système qualite_match - Code mort (désactivé)", "MAJEUR")
    
    print("DIAGNOSTIC:")
    print("  - qualite_match_actif: false dans default.yaml (ligne 118)")
    print("  - Commentaire: 'Ne pas activer - système non fonctionnel'")
    print("  - 4 paramètres liés:")
    print("    * qualite_match_actif (4 usages)")
    print("    * qualite_match_seuil (4 usages)")
    print("    * qualite_match_guidance_cpsat (2 usages)")
    print("    * qualite_match_log_rejets (2 usages)")
    print("  - Code dans cpsat_solver.py lignes 1071-1079")
    print()
    print("CONTEXTE:")
    print("  Système de filtrage de qualité pour rejeter les matchs de mauvaise qualité.")
    print("  Marqué 'non fonctionnel' mais code toujours présent.")
    print()
    print("PROPOSITION DE CORRECTION:")
    print("  OPTION A [RECOMMANDÉE]: Supprimer entièrement le système")
    print("    1. Retirer les 4 paramètres de config.py")
    print("    2. Retirer du from_yaml() et to_yaml()")
    print("    3. Retirer de default.yaml")
    print("    4. Retirer le code de cpsat_solver.py lignes 1071-1100 (approx)")
    print("    5. Retirer la méthode _ajouter_guidance_qualite() si elle existe")
    print()
    print("  OPTION B [Si système à réparer]: Documenter ce qui ne marche pas")
    print("    - Créer un ticket pour identifier le bug")
    print("    - Ajouter des tests pour le système de qualité")
    print("    - Réparer puis réactiver")
    print()
    print("  RECOMMANDATION: Option A - Système désactivé depuis longtemps,")
    print("  aucun utilisateur ne s'en plaint. Simplifier en supprimant.")
    print()
    
    # ========================================================================
    # PROBLÈME 3: cpsat_warm_start et cpsat_warm_start_file
    # ========================================================================
    print_problem(3, "cpsat_warm_start - Paramètres définis mais non utilisés", "MINEUR")
    
    print("DIAGNOSTIC:")
    print("  - cpsat_warm_start défini dans config.py mais jamais utilisé")
    print("  - cpsat_warm_start_file défini mais jamais utilisé")
    print("  - Méthode solve() de cpsat_solver.py a paramètre use_warm_start")
    print("    mais pas lié à self.config.cpsat_warm_start")
    print("  - config_volley.yaml a warm_start: false (commentaire: 'causes issues')")
    print()
    print("CONTEXTE:")
    print("  Le warm start permet de réutiliser une solution précédente comme")
    print("  point de départ pour accélérer la résolution.")
    print("  Actuellement, warm_start est un paramètre de la méthode solve(),")
    print("  pas un paramètre de configuration.")
    print()
    print("PROPOSITION DE CORRECTION:")
    print("  OPTION A [RECOMMANDÉE]: Supprimer les paramètres inutilisés")
    print("    1. Retirer cpsat_warm_start de config.py")
    print("    2. Retirer cpsat_warm_start_file de config.py")
    print("    3. Retirer de default.yaml")
    print("    4. Laisser use_warm_start comme paramètre de méthode")
    print()
    print("  OPTION B: Connecter les paramètres config au code")
    print("    1. Modifier solve() pour utiliser self.config.cpsat_warm_start")
    print("    2. Utiliser self.config.cpsat_warm_start_file pour le fichier")
    print("    3. Corriger le bug mentionné dans config_volley.yaml")
    print()
    print("  RECOMMANDATION: Option A - Le warm start fonctionne mieux comme")
    print("  paramètre de méthode (contrôle par le code appelant, pas config)")
    print()
    
    # ========================================================================
    # PROBLÈME 4: Paramètres calendrier jamais utilisés
    # ========================================================================
    print_problem(4, "Paramètres calendrier - Définis mais jamais utilisés", "INFO")
    
    print("DIAGNOSTIC:")
    print("  - calendrier_actif défini mais jamais utilisé (sauf validation)")
    print("  - calendrier_date_debut défini mais jamais utilisé")
    print("  - calendrier_jour_match défini mais jamais utilisé")
    print("  - calendrier_semaines_banalisees défini mais jamais utilisé")
    print("  - Code de validation existe (config.py ligne 286)")
    print()
    print("CONTEXTE:")
    print("  Système de gestion de calendrier avec dates réelles.")
    print("  Les paramètres sont chargés depuis le YAML mais jamais utilisés")
    print("  dans les solvers ou l'interface.")
    print()
    print("PROPOSITION DE CORRECTION:")
    print("  OPTION A: Supprimer si fonctionnalité non planifiée")
    print("    1. Retirer les 4 paramètres de config.py")
    print("    2. Retirer de default.yaml")
    print("    3. Retirer la validation ligne 286")
    print()
    print("  OPTION B [RECOMMANDÉE]: Garder si fonctionnalité en développement")
    print("    - Ajouter commentaire: '# TODO: Fonctionnalité à implémenter'")
    print("    - Documenter l'usage prévu:")
    print("      * Conversion semaine → date réelle pour l'affichage")
    print("      * Gestion des semaines banalisées (vacances)")
    print("      * Affichage dates dans interface HTML")
    print()
    print("  RECOMMANDATION: Option B - Fonctionnalité utile pour l'interface,")
    print("  garder en attendant implémentation future.")
    print()
    
    # ========================================================================
    # PROBLÈME 5: aller_retour_min_semaines jamais utilisé
    # ========================================================================
    print_problem(5, "aller_retour_min_semaines - Paramètre non utilisé", "MINEUR")
    
    print("DIAGNOSTIC:")
    print("  - aller_retour_min_semaines défini dans config.py")
    print("  - Chargé depuis YAML (default.yaml: 2)")
    print("  - Jamais utilisé dans le code des solvers")
    print("  - Autres paramètres aller_retour_* semblent utilisés")
    print()
    print("CONTEXTE:")
    print("  Système d'espacement aller-retour pour éviter de planifier")
    print("  les deux matchs d'une paire trop proche.")
    print()
    print("PROPOSITION DE CORRECTION:")
    print("  OPTION A: Implémenter la contrainte manquante")
    print("    - Chercher où aller_retour_espacement_actif est utilisé")
    print("    - Ajouter logique pour respecter aller_retour_min_semaines")
    print("    - Utiliser les pénalités existantes (meme_semaine, consecutives)")
    print()
    print("  OPTION B [RECOMMANDÉE]: Supprimer si déjà géré autrement")
    print("    - Vérifier si aller_retour_penalite_consecutives couvre ce cas")
    print("    - Si oui, supprimer aller_retour_min_semaines (redondant)")
    print()
    print("  RECOMMANDATION: Option B - Les pénalités meme_semaine et consecutives")
    print("  gèrent déjà l'espacement. Paramètre min_semaines semble redondant.")
    print()
    
    # ========================================================================
    # PROBLÈME 6: fallback_greedy jamais utilisé
    # ========================================================================
    print_problem(6, "fallback_greedy - Paramètre stratégie non utilisé", "MINEUR")
    
    print("DIAGNOSTIC:")
    print("  - fallback_greedy défini dans config.py")
    print("  - Chargé depuis YAML (default.yaml: true)")
    print("  - Jamais utilisé dans pipeline.py ou solvers")
    print("  - Paramètre 'strategie' existe et semble gérer le choix du solver")
    print()
    print("CONTEXTE:")
    print("  Le paramètre semble destiné à activer un fallback Greedy si")
    print("  CP-SAT ne trouve pas de solution.")
    print()
    print("PROPOSITION DE CORRECTION:")
    print("  OPTION A [RECOMMANDÉE]: Implémenter le fallback")
    print("    1. Dans pipeline.py, après échec CP-SAT:")
    print("       if not solution and self.config.fallback_greedy:")
    print("           logger.info('CP-SAT failed, trying Greedy fallback...')")
    print("           solution = greedy_solver.solve()")
    print()
    print("  OPTION B: Supprimer si non souhaité")
    print("    - Retirer fallback_greedy de config.py")
    print("    - Retirer de default.yaml")
    print("    - Le paramètre 'strategie' suffit pour choisir le solver")
    print()
    print("  RECOMMANDATION: Option A - Fonctionnalité utile pour robustesse.")
    print("  CP-SAT peut timeout, Greedy donne toujours une solution.")
    print()
    
    # ========================================================================
    # PROBLÈME 7: nb_preferences_gymnases jamais utilisé
    # ========================================================================
    print_problem(7, "nb_preferences_gymnases - Paramètre non utilisé", "MINEUR")
    
    print("DIAGNOSTIC:")
    print("  - nb_preferences_gymnases défini (défaut: 5)")
    print("  - bonus_preferences_gymnases défini (liste de 5 valeurs)")
    print("  - nb_preferences_gymnases jamais utilisé dans le code")
    print("  - Le système utilise directement len(bonus_preferences_gymnases)")
    print()
    print("CONTEXTE:")
    print("  Système de préférences de gymnases avec bonus décroissant")
    print("  par rang (1er choix, 2ème choix, etc.)")
    print()
    print("PROPOSITION DE CORRECTION:")
    print("  OPTION A [RECOMMANDÉE]: Supprimer nb_preferences_gymnases")
    print("    1. Retirer le paramètre de config.py")
    print("    2. Retirer de default.yaml")
    print("    3. Utiliser len(bonus_preferences_gymnases) dans le code")
    print()
    print("  OPTION B: Utiliser pour validation")
    print("    - Valider que len(bonus_preferences_gymnases) == nb_preferences_gymnases")
    print("    - Lever une erreur si incohérence")
    print()
    print("  RECOMMANDATION: Option A - Paramètre redondant, la liste suffit.")
    print()
    
    # ========================================================================
    # RÉSUMÉ DES ACTIONS
    # ========================================================================
    print_section("RÉSUMÉ DES ACTIONS RECOMMANDÉES")
    
    print("ACTIONS PRIORITAIRES (à faire maintenant):")
    print()
    print("1. 🔴 Supprimer entente_facteur_reduction (obsolète mais utilisé)")
    print("   Fichiers: config.py, cpsat_solver.py, greedy_solver.py, default.yaml")
    print()
    print("2. 🔴 Supprimer système qualite_match (désactivé, code mort)")
    print("   Fichiers: config.py, cpsat_solver.py, default.yaml")
    print()
    print("3. 🟠 Supprimer cpsat_warm_start et cpsat_warm_start_file")
    print("   Fichiers: config.py, default.yaml")
    print()
    print("4. 🟡 Supprimer nb_preferences_gymnases (redondant)")
    print("   Fichiers: config.py, default.yaml")
    print()
    print("5. 🟡 Supprimer aller_retour_min_semaines (redondant)")
    print("   Fichiers: config.py, default.yaml")
    print()
    print("ACTIONS SECONDAIRES (à considérer):")
    print()
    print("6. 🔵 Implémenter fallback_greedy dans pipeline.py")
    print("   OU supprimer le paramètre si non souhaité")
    print()
    print("7. 🔵 Documenter paramètres calendrier (TODO futur)")
    print("   OU supprimer si fonctionnalité abandonnée")
    print()
    print("IMPACT ESTIMÉ:")
    print("  - Réduction: ~10 paramètres inutiles supprimés")
    print("  - Lignes de code: ~150 lignes supprimées")
    print("  - Clarté: Séparation claire entre paramètres actifs/futurs/obsolètes")
    print("  - Tests: Aucun impact (code mort)")
    print()
    
    # ========================================================================
    # SCRIPT DE MIGRATION
    # ========================================================================
    print_section("SCRIPTS DE MIGRATION DISPONIBLES")
    
    print("Pour appliquer ces corrections automatiquement:")
    print()
    print("  python temp_tests/apply_config_corrections.py --all")
    print()
    print("Ou par problème:")
    print("  python temp_tests/apply_config_corrections.py --problem 1  # entente_facteur_reduction")
    print("  python temp_tests/apply_config_corrections.py --problem 2  # qualite_match")
    print("  python temp_tests/apply_config_corrections.py --problem 3  # warm_start")
    print()
    print("⚠️  ATTENTION: Sauvegarder votre travail avant d'exécuter ces scripts!")
    print()

if __name__ == '__main__':
    main()
