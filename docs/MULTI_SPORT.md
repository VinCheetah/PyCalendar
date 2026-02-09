# Documentation Multi-Sport PyCalendar

Ce document décrit le support multi-sport complet de PyCalendar, incluant le backend, l'interface et tous les scripts utilitaires.

## Sports Supportés

| Code | Sport | Emoji | Durée | Pattern Fichiers |
|------|-------|-------|-------|------------------|
| VB | Volleyball | 🏐 | 120 min | `volley` |
| HB | Handball | 🤾 | 90 min | `hand` |
| BB | Basketball | 🏀 | 90 min | `basket` |
| FB | Football | ⚽ | 90 min | `foot` |
| FU | Futsal | 🥅 | 60 min | `futsal` |
| RU | Rugby | 🏉 | 80 min | `rugby` |
| TE | Tennis | 🎾 | 90 min | `tennis` |
| BA | Badminton | 🏸 | 60 min | `badminton` |
| AT | Athlétisme | 🏃 | 120 min | `athle` |

## Format des Codes de Poule

Les codes de poule suivent le format standardisé :

```
{SPORT}{GENRE}{NIVEAU}P{POULE}
```

**Exemples:**
- `VBFA1PA` = Volleyball, Féminin, A1, Poule A
- `HBMA3PB` = Handball, Masculin, A3, Poule B
- `BBFA2PC` = Basketball, Féminin, A2, Poule C

## Architecture Multi-Sport

### 1. Backend Python

#### Fichier de Configuration: `configs/sports_presets.yaml`

Contient tous les paramètres par défaut pour chaque sport:

```yaml
volleyball:
  prefix: "VB"
  name: "Volleyball"
  name_short: "Volley"
  emoji: "🏐"
  duree_match_minutes: 120
  score_format: "sets"
```

#### Module: `src/pycalendar/core/sport_config.py`

Charge et gère les configurations de sport:

```python
from pycalendar.core.sport_config import get_sport_presets

presets = get_sport_presets()
volleyball = presets.get_sport("volleyball")
print(f"{volleyball.name} {volleyball.emoji}")  # Volleyball 🏐
```

#### Configuration YAML par Sport

Chaque sport a son fichier de configuration:

- `configs/config_volley.yaml` - Volleyball
- `configs/config_hand.yaml` - Handball
- `configs/config_basket.yaml` - Basketball (exemple)

### 2. Module Utilitaire: `scripts/sport_utils.py`

Point d'entrée centralisé pour toutes les opérations liées aux sports dans les scripts.

#### Fonctions Principales

```python
from scripts.sport_utils import (
    load_sport_from_config,    # Charge un sport depuis un YAML
    find_latest_solution,       # Trouve la dernière solution
    resolve_sport_and_solution, # Résout sport + solution depuis arguments
    extraire_sport_code,        # Extrait le code sport d'un code de poule
    extraire_genre_niveau,      # Extrait genre et niveau
    get_sport_info_from_poule,  # Obtient SportInfo depuis un code de poule
)
```

#### Classe SportInfo

```python
@dataclass
class SportInfo:
    type: str           # "volleyball", "handball", etc.
    prefix: str         # "VB", "HB", etc.
    name: str           # "Volleyball", "Handball"
    name_short: str     # "Volley", "Hand"
    emoji: str          # "🏐", "🤾"
    duree_match: int    # 120, 90, etc.
    score_format: str   # "points" ou "sets"
    
    @property
    def pattern(self) -> str:
        """Pattern pour les noms de fichiers: 'volley', 'hand', etc."""
```

### 3. Interface JavaScript

#### Module: `scripts/utils/sport-utils.js`

Équivalent JavaScript du module Python:

```javascript
import { sportUtils } from './utils/sport-utils.js';

// Initialisation (dans app.js)
sportUtils.init(dataManager);

// Utilisation
sportUtils.getEmoji();    // "🏐"
sportUtils.getName();     // "Volleyball"
sportUtils.getPrefix();   // "VB"
sportUtils.extractSportFromPoule("VBFA1PA"); // "VB"
```

## Usage des Scripts

### Méthode Recommandée: `--config`

Tous les scripts supportent l'argument `--config` pour auto-détecter le sport:

```bash
# ✅ Méthode recommandée
python scripts/generer_feuille_matchs.py -s 1 --config configs/config_volley.yaml
python scripts/show_penalties.py --config configs/config_hand.yaml
python scripts/analyze_equilibrage.py --config configs/config_basket.yaml
```

### Méthode Alternative: `--sport`

Pour une compatibilité arrière, les scripts acceptent aussi `--sport`:

```bash
python scripts/show_penalties.py --sport hand
python scripts/analyze_balance.py --sport basket
```

## Liste des Scripts Compatibles

| Script | `--config` | `--sport` | `--solution` |
|--------|-----------|-----------|--------------|
| `validate_solution_complete.py` | ✅ | ✅ | ✅ |
| `generer_feuille_matchs.py` | ✅ | ✅ | ✅ |
| `generate_entente_notifications.py` | ✅ | ✅ | ✅ |
| `show_penalties.py` | ✅ | ✅ | ✅ |
| `analyze_equilibrage.py` | ✅ | ✅ | ✅ |
| `analyze_balance.py` | ✅ | ✅ | ✅ |
| `add_contacts_to_config.py` | ✅ | - | - |
| `import_fixed_matches_from_downloads.py` | ✅ | ✅ | - |

## Création d'un Nouveau Sport

### 1. Ajouter le preset dans `configs/sports_presets.yaml`:

```yaml
esports:
  prefix: "ES"
  name: "Esports"
  name_short: "Esports"
  emoji: "🎮"
  duree_match_minutes: 60
  score_format: "points"
  niveaux: ["A1", "A2"]
  genres: ["M", "F", "X"]
```

### 2. Mettre à jour les mappings dans `sport_utils.py`:

```python
# Ajouter dans les mappings
SPORT_TYPE_TO_PATTERN = {
    # ...existants...
    'esports': 'esport',
}

CODE_TO_SPORT_TYPE = {
    # ...existants...
    'ES': 'esports',
}
```

### 3. Créer le fichier de configuration:

```bash
cp configs/config_volley.yaml configs/config_esport.yaml
# Puis modifier sport_type: esports dans le fichier
```

## Tests

Vérifier le bon fonctionnement:

```bash
# Test du module sport_utils
python scripts/sport_utils.py

# Tests unitaires
python -m pytest tests/ -v
```

## Notes Techniques

### Import Pattern

Tous les scripts suivent le même pattern d'import:

```python
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
for _path in [str(PROJECT_ROOT), str(SRC_DIR)]:
    if _path not in sys.path:
        sys.path.insert(0, _path)

from scripts.sport_utils import load_sport_from_config, find_latest_solution
```

### Gestion des NaN (pandas)

Pour les fonctions appelées avec des DataFrames pandas, utiliser les wrappers:

```python
def extraire_sport_safe(code_poule):
    """Gère les NaN de pandas."""
    if pd.isna(code_poule) or not isinstance(code_poule, str):
        return 'VB'
    return extraire_sport_code(code_poule)
```
