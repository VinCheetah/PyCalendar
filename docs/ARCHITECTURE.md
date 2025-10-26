# 🏗️ Architecture PyCalendar v2.0

## 📋 Vue d'ensemble

PyCalendar suit maintenant une **architecture moderne et standardisée** conforme aux meilleures pratiques Python (PEP 8, packaging standard).

## 📂 Structure du projet

```
PyCalendar/
├── 📁 src/pycalendar/                  # 🆕 Code source principal (package Python)
│   ├── __init__.py                     # Exports publics du package
│   ├── __main__.py                     # Point d'entrée: python -m pycalendar
│   │
│   ├── 📁 core/                        # Cœur métier
│   │   ├── models.py                   # Modèles: Equipe, Gymnase, Match, Solution
│   │   ├── config.py                   # Configuration système
│   │   ├── config_manager.py           # Gestionnaire de configuration
│   │   ├── calendar_manager.py         # Gestion calendrier et dates
│   │   ├── solution_store.py           # Stockage et versioning solutions
│   │   ├── statistics.py               # 🆕 Statistiques de solutions
│   │   └── utils.py                    # Fonctions utilitaires
│   │
│   ├── 📁 data/                        # Chargement et transformation données
│   │   ├── data_loader.py              # Lecture fichiers Excel
│   │   ├── data_source.py              # Interface source de données
│   │   ├── transformers.py             # Transformations de données
│   │   └── validators.py               # Validation données d'entrée
│   │
│   ├── 📁 constraints/                 # Système de contraintes
│   │   ├── base.py                     # Contraintes de base
│   │   ├── team_constraints.py         # Contraintes équipes
│   │   ├── venue_constraints.py        # Contraintes gymnases
│   │   ├── schedule_constraints.py     # Contraintes horaires
│   │   └── institution_constraints.py  # Contraintes institutionnelles
│   │
│   ├── 📁 generators/                  # Génération de matchs
│   │   ├── match_generator.py          # Générateur de matchs basique
│   │   └── multi_pool_generator.py     # Générateur multi-poules
│   │
│   ├── 📁 solvers/                     # Algorithmes d'optimisation
│   │   ├── base_solver.py              # Interface solver abstrait
│   │   ├── greedy_solver.py            # Algorithme glouton (rapide)
│   │   └── cpsat_solver.py             # Google CP-SAT (optimal)
│   │
│   ├── 📁 orchestrator/                # Pipeline principal
│   │   └── pipeline.py                 # Orchestration complète du workflow
│   │
│   ├── 📁 exporters/                   # Export vers formats externes
│   │   └── excel_exporter.py           # Export Excel avec formatage
│   │
│   ├── 📁 validation/                  # Validation de solutions
│   │   └── solution_validator.py       # Validateur de contraintes
│   │
│   ├── 📁 interface/                   # Interface web HTML
│   │   ├── README.md                   # Documentation interface
│   │   ├── 📁 core/                    # Backend Python
│   │   │   ├── data_formatter.py       # Format Solution → JSON v2.0
│   │   │   ├── generator.py            # Génération HTML autonome
│   │   │   └── validator.py            # Validation solutions v2.0
│   │   ├── 📁 assets/                  # Ressources statiques (CSS)
│   │   ├── 📁 scripts/                 # JavaScript modulaire
│   │   ├── 📁 templates/               # Templates HTML
│   │   └── 📁 data/                    # Schémas JSON
│   │
│   └── 📁 cli/                         # 🆕 Outils ligne de commande
│       ├── config_tools.py             # Validation/actualisation config
│       ├── pool_extractor.py           # Extraction poules depuis Excel
│       ├── match_sheet_generator.py    # Génération feuilles de matchs
│       ├── external_importer.py        # Import matchs externes
│       ├── solution_validator.py       # Validation solutions
│       ├── quality_checker.py          # Vérification qualité
│       └── interface_regenerator.py    # Régénération interface HTML
│
├── 📁 examples/                        # 🆕 Exemples et données test
│   ├── volleyball/                     # Exemple volleyball (ex data_volley/)
│   ├── handball/                       # Exemple handball (ex data_hand/)
│   └── basic/                          # Exemple basique (ex exemple/)
│
├── 📁 configs/                         # Fichiers configuration YAML
│   ├── default.yaml                    # Configuration par défaut
│   ├── config_volley.yaml              # Configuration volleyball
│   └── config_hand.yaml                # Configuration handball
│
├── 📁 solutions/                       # Solutions générées (JSON v2.0)
│   └── latest_volley.json
│
├── 📁 docs/                            # Documentation
│   ├── ARCHITECTURE.md                 # 🆕 Ce fichier
│   ├── FORMAT_V2_GUIDE.md              # Guide format v2.0
│   ├── IMPORTATEUR_MATCHS_EXTERNES.md  # Guide importation
│   └── MIGRATION_V2_ANALYSIS.md        # Analyse migration v2
│
├── 📁 scripts/                         # Scripts de maintenance
│   ├── apply_modifications.py          # Application modifications JSON
│   ├── convert_solution_to_v2.py       # Conversion format v1 → v2
│   └── validate_modifications.py       # Validation modifications
│
├── 📁 tests/                           # 🆕 Tests unitaires (à créer)
│   └── (à venir)
│
├── main.py                             # 🎯 Point d'entrée principal
├── setup.py                            # 🆕 Configuration installation
├── pyproject.toml                      # 🆕 Configuration moderne Python
├── requirements.txt                    # Dépendances production
├── requirements-dev.txt                # 🆕 Dépendances développement
├── README.md                           # Documentation principale
├── LICENSE                             # Licence MIT
└── .gitignore                          # Fichiers ignorés par git
```

## 🎯 Points d'entrée

### 1. Interface utilisateur (recommandé)

```bash
# Via main.py (simple)
python main.py
python main.py configs/config_volley.yaml

# Via module Python (après installation)
python -m pycalendar
python -m pycalendar configs/config_volley.yaml

# Via commande installée (si pip install -e .)
pycalendar
pycalendar configs/config_volley.yaml
```

### 2. Outils CLI

Après installation (`pip install -e .`), tous les outils sont disponibles en ligne de commande :

```bash
# Validation/actualisation configuration
pycalendar-config examples/volleyball/config_volley.xlsx

# Extraction poules
pycalendar-extract input.xlsx -o config.xlsx

# Génération feuilles de matchs
pycalendar-sheet --semaine 1 --date "16/10/2025"

# Import matchs externes
pycalendar-import --config config.yaml --url "https://..."

# Validation solution
pycalendar-validate solutions/latest_volley.json

# Vérification qualité
pycalendar-check solutions/latest_volley.json

# Régénération interface
pycalendar-interface --solution latest_volley.json
```

### 3. API Python

```python
# Import direct du package
from pycalendar import Config, SchedulingPipeline, Equipe, Gymnase

# Créer une configuration
config = Config.from_yaml("configs/config_volley.yaml")

# Exécuter le pipeline
pipeline = SchedulingPipeline(config)
solution = pipeline.run()

# Accéder aux résultats
print(f"Matchs planifiés: {len(solution.matchs_planifies)}")
print(f"Taux: {solution.taux_planification():.1f}%")
```

## 🔄 Flux de données

```
┌──────────────────────┐
│  Fichier Excel       │
│  (config_volley.xlsx)│
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  data_loader.py      │  ← Lecture Excel
│  data_source.py      │  ← Transformation en objets Python
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  match_generator.py  │  ← Génération matchs (round-robin)
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Solver (CP-SAT)     │  ← Optimisation avec contraintes
│  ou Greedy           │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Solution object     │  ← Résultat optimisé
└──────────┬───────────┘
           │
           ├─────────────────┐
           │                 │
           ▼                 ▼
  ┌────────────────┐  ┌──────────────────┐
  │ excel_exporter │  │ interface/       │
  │ .xlsx          │  │ generator        │
  └────────────────┘  │ .html            │
                      └──────────────────┘
```

## 🆕 Changements majeurs v2.0

### Structure
- ✅ **src/pycalendar/** : Code source isolé, imports propres
- ✅ **Package installable** : `pip install -e .`
- ✅ **CLI organisé** : Tous les outils dans `cli/`
- ✅ **Examples/** : Données de test hors du code source

### Imports
**Avant** (v1.x) :
```python
from core.models import Equipe
from orchestrator.pipeline import SchedulingPipeline
```

**Maintenant** (v2.0) :
```python
from pycalendar.core.models import Equipe
from pycalendar.orchestrator.pipeline import SchedulingPipeline
```

### Interface
- ❌ **Supprimé** : Module `visualization` (obsolète)
- ✅ **Nouveau** : Module `interface` (moderne, modulaire)
- ✅ **InterfaceGenerator** : Remplace `HTMLVisualizerV2`
- ✅ **Statistics** : Dans `core/` au lieu de `visualization/`

## 🧪 Tests (À venir)

Structure recommandée :
```
tests/
├── test_core/
│   ├── test_models.py
│   ├── test_config.py
│   └── test_solution_store.py
├── test_solvers/
│   ├── test_greedy.py
│   └── test_cpsat.py
├── test_constraints/
│   └── test_all_constraints.py
└── test_cli/
    └── test_cli_tools.py
```

## 📦 Installation

### Mode développement (recommandé)
```bash
# Cloner le repo
git clone https://github.com/VinCheetah/PyCalendar
cd PyCalendar

# Créer environnement virtuel
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou .venv\Scripts\activate  # Windows

# Installer en mode éditable
pip install -e .

# Installer dépendances dev (optionnel)
pip install -r requirements-dev.txt
```

### Mode production
```bash
pip install git+https://github.com/VinCheetah/PyCalendar
```

## 🛠️ Développement

### Ajouter un nouveau module
1. Créer dans `src/pycalendar/`
2. Utiliser imports absolus : `from pycalendar.core import ...`
3. Ajouter à `__init__.py` si export public souhaité

### Ajouter un outil CLI
1. Créer dans `src/pycalendar/cli/`
2. Ajouter fonction `main()` comme point d'entrée
3. Enregistrer dans `setup.py` section `console_scripts`
4. Documenter l'utilisation

### Code style
```bash
# Formatter le code
black src/

# Vérifier le style
flake8 src/

# Trier les imports
isort src/

# Vérifier les types
mypy src/
```

## 🔗 Dépendances principales

- **pandas** : Manipulation données Excel
- **openpyxl** : Lecture/écriture Excel
- **ortools** : Solveur CP-SAT (Google OR-Tools)
- **pyyaml** : Configuration YAML
- **streamlit** : Interface web (optionnel)
- **jsonschema** : Validation JSON

## 📚 Documentation additionnelle

- `interface/README.md` - Architecture interface web
- `docs/FORMAT_V2_GUIDE.md` - Format Solution v2.0
- `docs/IMPORTATEUR_MATCHS_EXTERNES.md` - Import matchs externes
- `README.md` - Guide utilisateur principal

## 🎉 Avantages de la nouvelle architecture

1. **Standard Python** : Conforme PEP 8, packaging moderne
2. **Maintenable** : Code organisé logiquement
3. **Testable** : Structure adaptée aux tests unitaires
4. **Installable** : `pip install`, commandes CLI
5. **Évolutif** : Facile d'ajouter modules/fonctionnalités
6. **Documenté** : Documentation intégrée
7. **Professionnel** : Structure reconnaissable par tous les développeurs Python
