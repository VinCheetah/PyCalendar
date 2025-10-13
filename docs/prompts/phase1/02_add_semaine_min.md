# PROMPT 1.2 : Ajouter Contrainte Semaine Minimum

## Contexte Projet

**PyCalendar V2** : Transformation application CLI → Web avec API REST et interface interactive pour gestion calendriers sportifs.

## État Actuel

- ✅ Prompt 1.1 : Modèle `Match` enrichi (est_fixe, statut, scores, méthodes)
- ⏳ Phase 1 Backend en cours

## Objectif de cette Tâche

Permettre de **bloquer la planification de matchs avant une semaine donnée**. Cas d'usage : début de saison retardé, période de vacances, etc.

**Contrainte** : Solver ne doit pas planifier de matchs avant `semaine_min`.

**Durée estimée** : 10 minutes

## Instructions Techniques

### 1. Localiser la Classe Config

**Fichier** : `core/config.py`

Trouver la dataclass `Config` contenant :
- `fichier_donnees: str`
- `nb_semaines: int`
- `horaires_disponibles: List[str]`
- etc.

### 2. Ajouter Champ semaine_min

Ajouter **à la fin de la dataclass** :

```python
@dataclass
class Config:
    # ... champs existants ...
    
    semaine_min: int = 1  # Semaine minimum pour planification
```

**Points critiques** :
- Valeur par défaut `1` (planification dès semaine 1)
- Optionnel dans fichiers YAML (rétrocompatibilité)

### 3. Vérifier Parsing YAML

Le parsing YAML existant dans `Config.from_yaml()` doit gérer automatiquement les champs optionnels.

**Vérifier** que la méthode `from_yaml()` :
- Utilise `getattr()` ou `dict.get()` pour champs optionnels
- Ou utilise dataclass fields avec defaults (déjà le cas si `= 1` dans dataclass)

**Si nécessaire**, modifier pour :

```python
@classmethod
def from_yaml(cls, yaml_path: str) -> 'Config':
    with open(yaml_path) as f:
        data = yaml.safe_load(f)
    
    # Si semaine_min absent du YAML, utiliser default 1
    semaine_min = data.get('semaine_min', 1)
    
    return cls(
        # ... autres champs ...
        semaine_min=semaine_min
    )
```

### 4. Tester avec Fichier YAML

**Créer fichier test** : `configs/config_test_semaine_min.yaml`

```yaml
# Copier config existant et ajouter
semaine_min: 5
```

Charger et vérifier :

```python
config = Config.from_yaml("configs/config_test_semaine_min.yaml")
assert config.semaine_min == 5
print("✅ semaine_min chargé depuis YAML")
```

## Validation

### Test 1 : Config Sans semaine_min (Rétrocompatibilité)

```bash
python -c "
from core.config import Config
config = Config.from_yaml('configs/config_volley.yaml')
assert config.semaine_min == 1, 'Default doit être 1'
print('✅ Config sans semaine_min utilise default 1')
"
```

### Test 2 : Config Avec semaine_min

Créer `configs/test_semaine_min.yaml` :

```yaml
fichier_donnees: "data/exemple.xlsx"
nb_semaines: 26
semaine_min: 5
# ... autres champs ...
```

```bash
python -c "
from core.config import Config
config = Config.from_yaml('configs/test_semaine_min.yaml')
assert config.semaine_min == 5
print('✅ semaine_min=5 chargé correctement')
"
```

### Test 3 : CLI Fonctionne

```bash
python main.py configs/config_volley.yaml
```

**Attendu** : Aucune erreur, calendrier généré normalement.

## Critères de Réussite

- [ ] Champ `semaine_min: int = 1` ajouté dans `Config`
- [ ] Fichiers YAML sans `semaine_min` utilisent default 1
- [ ] Fichiers YAML avec `semaine_min` chargent valeur correcte
- [ ] CLI fonctionne sans régression

## Prochaine Étape

➡️ **Prompt 1.3** : Créer structure database backend avec SQLAlchemy

## Notes

Cette contrainte sera **utilisée dans Phase 3** lors de l'intégration solver pour filtrer les créneaux disponibles.
