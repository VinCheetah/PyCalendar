# Architecture et Interconnexions de PyCalendar

## Vue d'Ensemble

PyCalendar est un système modulaire de planification automatique de calendriers sportifs (volley, handball) utilisant une configuration centrale Excel et des algorithmes d'optimisation. Le système génère des calendriers complets avec contraintes dures et souples, exports Excel/HTML, et validation automatique.

## Architecture Générale

```
PyCalendar/
├── Scripts Utilisateur (Racine)
├── core/                    # Noyau du système
├── data/                    # Chargement des données
├── constraints/             # Système de contraintes
├── solvers/                 # Algorithmes de résolution
├── orchestrator/            # Pipeline principal
├── exporters/               # Exports (Excel, HTML)
├── visualization/           # Interfaces et statistiques
├── interface/               # Code de l'interface web
└── validation/              # Validation des solutions
```

## Scripts Principaux et Leur Rôle

### Points d'Entrée Utilisateur

| Script | Rôle | Dépendances | Sorties |
|--------|------|-------------|---------|
| `main.py` | **Point d'entrée principal** - Orchestre toute la génération | `core.config`, `orchestrator.pipeline` | Solution JSON, Excel, HTML |
| `validate_solution.py` | Valide une solution JSON existante | `interface.core.validator` | Rapport de validation |
| `regenerate_interface.py` | Régénère l'interface HTML depuis une solution | `interface.core.generator` | Fichier HTML |
| `actualiser_config.py` | Valide et corrige automatiquement les fichiers Excel de config | `core.config_manager` | Fichier Excel corrigé |

### Scripts de Génération Spécialisés

| Script | Rôle | Usage |
|--------|------|-------|
| `generate_basic_html.py` | Génère HTML basique (tableau simple) | Alternative légère à l'interface complète |
| `generate_debug_html.py` | HTML de debug avec détails techniques | Diagnostic et développement |
| `generate_simple_html.py` | HTML simplifié pour visualisation rapide | Aperçu rapide |
| `generer_feuille_matchs.py` | Génère feuilles Excel formatées par semaine | Documents pour arbitres/organisateurs |

### Scripts Utilitaires

| Script | Rôle |
|--------|------|
| `importer_matchs_externes.py` | Importe des matchs depuis sources externes |
| `check_solution_quality.py` | Évalue la qualité d'une solution (pénalités, contraintes) |
| `extract_poules.py` | Extrait et analyse les poules depuis les données |
| `fix_gymnase_capacities.py` | Corrige les capacités des gymnases |
| `migrate_to_single_format.py` | Migre les anciennes solutions vers le format v2.0 |
| `refactor_slots.py` | Refactorise les créneaux horaires |

## Workflow Principal (main.py)

```mermaid
graph TD
    A[main.py] --> B[Charger Config YAML]
    B --> C[Créer SchedulingPipeline]
    C --> D[Pipeline.run()]
    D --> E[Charger Données Excel]
    E --> F[Générer Matchs]
    F --> G[Résoudre avec Solver]
    G --> H[Valider Solution]
    H --> I[Sauvegarder JSON]
    I --> J[Exporter Excel]
    J --> K[Générer HTML]
```

### Détail du Pipeline (orchestrator/pipeline.py)

1. **Chargement des Données** (`data/`)
   - Équipes, gymnases depuis Excel
   - Contraintes (indispos, préférences, obligations)
   - Via `DataSource`, `DataLoader`, `DataValidator`

2. **Génération des Matchs** (`generators/`)
   - Round-robin automatique par poule
   - Via `MultiPoolGenerator`

3. **Résolution** (`solvers/`)
   - **Greedy** : Rapide, heuristique
   - **CP-SAT** : Optimal, programmation par contraintes
   - Prend en compte contraintes dures/souples

4. **Validation** (`validation/`)
   - Vérification des contraintes respectées
   - Calcul des pénalités

5. **Exports** (`exporters/`, `visualization/`)
   - **Excel** : Calendrier formaté + statistiques
   - **HTML** : Interface interactive (4 vues)
   - **JSON** : Solution complète pour archivage/warm-start

## Modules Core

### core/

- **`models.py`** : Classes de données (Equipe, Gymnase, Match, Solution, Creneau)
- **`config.py`** : Gestion configuration YAML (chargement, validation, defaults)
- **`config_manager.py`** : Interface avec fichiers Excel de configuration
- **`solution_store.py`** : Sauvegarde/chargement solutions JSON
- **`utils.py`** : Fonctions utilitaires (parsing noms, genres, horaires)
- **`calendar_manager.py`** : Gestion dates réelles (optionnel)

### data/

- **`data_loader.py`** : Charge données avec contraintes depuis Excel
- **`data_source.py`** : Adapte données pour le pipeline
- **`transformers.py`** : Génère créneaux horaires depuis gymnases
- **`validators.py`** : Validation préliminaire des données

### constraints/

- **`base.py`** : Classe de base pour contraintes
- **`team_constraints.py`** : Contraintes sur équipes (indispos, préférences)
- **`venue_constraints.py`** : Contraintes gymnases + obligations présence
- **`schedule_constraints.py`** : Contraintes de planification (espacement, simultanéité)

### solvers/

- **`greedy_solver.py`** : Algorithme glouton (rapide, sous-optimal)
- **`cpsat_solver.py`** : Programmation par contraintes (optimal, lent)

### orchestrator/

- **`pipeline.py`** : Orchestration complète du workflow

### exporters/

- **`excel_exporter.py`** : Export vers Excel formaté

### visualization/

- **`html_visualizer*.py`** : Génération interfaces HTML (plusieurs versions)
- **`statistics.py`** : Calcul et affichage statistiques

### interface/

- **`core/`** : Logique de génération d'interface web
  - `data_formatter.py` : Formatage données pour JS
  - `validator.py` : Validation côté interface
  - `generator.py` : Génération HTML/JS

### validation/

- **`solution_validator.py`** : Validation complète des solutions

## Flux de Données

### Entrées

- **Configuration YAML** : Paramètres (algorithme, contraintes, fichiers)
- **Fichier Excel Central** : Équipes, gymnases, contraintes (7 feuilles)

### Traitements

1. **Parsing** : YAML → Config object, Excel → DataFrames
2. **Validation** : Cohérence des données, contraintes
3. **Transformation** : Génération matchs/créneaux
4. **Optimisation** : Résolution avec contraintes
5. **Validation** : Vérification solution finale

### Sorties

- **Solution JSON** : Format interne complet (solutions/)
- **Excel** : Calendrier formaté humain (data_*/)
- **HTML** : Interface interactive (data_*/)
- **Rapports** : Statistiques, validations

## Contraintes Supportées

### Dures (Toujours Respectées)

- Indisponibilités équipes/institutions
- Indisponibilités gymnases
- Obligations présence (gymnase ↔ institution)
- Capacité gymnases
- Max 1 match/équipe/semaine

### Souples (Optimisées)

- Préférences horaires (pénalités autour horaire préféré)
- Préférences gymnases (bonus par rang)
- Espacement repos (pénalités progressives)
- Équilibrage charge
- Compaction temporelle
- Chevauchements institutionnels

## Points d'Extension

### Ajouter une Contrainte

1. Créer classe dans `constraints/` héritant de `Constraint`
2. Implémenter méthodes `calculer_penalite()`, `est_violation_dure()`
3. Intégrer dans `DataLoader` et solvers

### Ajouter un Export

1. Créer classe dans `exporters/` ou `visualization/`
2. Implémenter interface commune
3. Ajouter dans `pipeline.py`

### Ajouter un Solver

1. Créer classe dans `solvers/` implémentant interface
2. Retourner objet `Solution`
3. Ajouter dans config et pipeline

## Dépendances Clés

- **pandas/openpyxl** : Manipulation Excel
- **ortools** : CP-SAT solver (optionnel)
- **yaml** : Configuration
- **dataclasses** : Structures de données
- **pathlib** : Gestion chemins

## Scripts de Maintenance/Développement

| Script | Rôle |
|--------|------|
| `test_*.py` | Tests unitaires et validation |
| `demo_*.py` | Démonstrations et exemples |
| `add_features.py` | Ajout de fonctionnalités |
| `scripts/convert_solution_to_v2.py` | Migration format solutions |
| `scripts/apply_modifications.py` | Application modifications solutions |

Ce système modulaire permet une évolution facile tout en maintenant une séparation claire des responsabilités entre chargement des données, résolution, validation et présentation.
