# Analyse Critique de la Configuration YAML

Ce dossier contient les scripts d'analyse de la configuration du projet PyCalendar.

## Scripts disponibles

### 1. Analyse automatisée
```bash
python temp_tests/analyze_config_params.py
```
- Scan automatique de tous les paramètres définis (56 paramètres)
- Détection des paramètres obsolètes, non utilisés, redondants
- Recherche dans le code source (grep intelligent)
- Résumé des problèmes par catégorie

### 2. Rapport détaillé
```bash
python temp_tests/analyse_finale_config.py
```
- Analyse approfondie de chaque problème
- Explications contextuelles et techniques
- Propositions de correction détaillées
- Clarifications sur les faux positifs

### 3. Propositions de corrections
```bash
python temp_tests/propositions_corrections_config.py
```
- Détail des 7 problèmes identifiés
- Solutions recommandées avec justifications
- Impact estimé de chaque correction
- Références précises (fichiers et lignes)

### 4. Récapitulatif
```bash
python temp_tests/recap_config.py
```
- Vue d'ensemble complète
- Plan d'action en 3 phases
- Méthodologie d'analyse
- Impact global

### 5. Dashboard synthétique
```bash
python temp_tests/dashboard_config.py
```
- Tableau de bord visuel
- Statistiques globales
- Résumé par sévérité
- Commandes utiles

## Problèmes identifiés

### 🔴 Priorité Haute

**1. entente_facteur_reduction** - Conflit logique
- Marqué OBSOLÈTE mais encore utilisé
- Conflit avec entente_facteur_reduction_bonus
- Double pénalisation selon le code path
- **Action**: Supprimer + modifier 2 solvers

**2. Système qualite_match** - Code mort
- 4 paramètres définis mais système désactivé
- Commentaire: "système non fonctionnel"
- ~200 lignes de code inaccessibles
- **Action**: Supprimer entièrement

### 🟡 Priorité Moyenne

**3. nb_preferences_gymnases** - Redondant
- Doublon avec len(bonus_preferences_gymnases)
- Jamais utilisé dans le code
- **Action**: Supprimer

**4. aller_retour_min_semaines** - Non utilisé
- Défini mais jamais référencé
- Pénalités existantes suffisent
- **Action**: Supprimer

### 🔵 Décision requise

**5. Paramètres calendrier** - Fonctionnalité future
- 4 paramètres définis mais non implémentés
- Usage prévu: conversion semaine→date, vacances
- **Action**: Garder avec TODO OU supprimer

## Paramètres validés ✅

Les paramètres suivants ont été vérifiés et sont **correctement utilisés**:
- `cpsat_warm_start` (pipeline.py ligne 443)
- `cpsat_warm_start_file` (pipeline.py ligne 468)
- `fallback_greedy` (pipeline.py ligne 451)

## Impact global

- **Paramètres à supprimer**: 7 (ou 11 avec calendrier)
- **Lignes de code**: ~250 lignes supprimées
- **Fichiers modifiés**: 4 (config.py, default.yaml, 2 solvers)
- **Risque**: 🟢 Très faible (code mort/redondant)
- **Bénéfices**: Configuration plus claire et cohérente

## Plan d'action recommandé

**Phase 1** - Priorité Haute (1-2h):
1. Supprimer système qualite_match
2. Supprimer entente_facteur_reduction

**Phase 2** - Priorité Moyenne (30min):
3. Supprimer nb_preferences_gymnases
4. Supprimer aller_retour_min_semaines

**Phase 3** - Selon roadmap:
5. Décision sur paramètres calendrier

## Méthodologie

1. **Extraction**: Tous paramètres de CalendarConfig (56)
2. **Grep automatique**: Recherche dans src/pycalendar/**/*.py
3. **Vérification manuelle**: Élimination faux positifs
4. **Analyse contextuelle**: Compréhension logique métier
5. **Propositions**: Solutions concrètes et justifiées

## Précautions

Avant d'appliquer les corrections:
- ✅ Git commit de l'état actuel
- ✅ Tester génération interface après
- ✅ Vérifier solution volleyball après

## Fichiers générés

- `analyze_config_params.py` - Scan automatique
- `analyse_finale_config.py` - Rapport détaillé
- `propositions_corrections_config.py` - Solutions détaillées
- `recap_config.py` - Récapitulatif complet
- `dashboard_config.py` - Tableau de bord synthétique
- `README_ANALYSE_CONFIG.md` - Ce fichier
