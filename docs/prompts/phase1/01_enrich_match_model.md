# PROMPT 1.1 : Enrichir Modèle Match pour Matchs Fixes et Scores

## Contexte Projet

**PyCalendar** est un système d'optimisation de calendriers sportifs utilisant CP-SAT et Greedy solvers. Le projet transforme une application CLI/Excel en application web full-stack avec API REST (FastAPI) et interface React interactive.

**Objectif V2** : Permettre édition interactive des calendriers, gestion matchs fixes (non-replanifiables), et saisie scores.

## État Actuel

- ✅ Branche `feature/web-interface` créée
- ✅ Documentation technique complète (`IMPLEMENTATION_TECHNIQUE.md`)
- ✅ Architecture projet définie (backend API + frontend React)
- ⏳ **Phase 1 en cours** : Backend Foundation

## Objectif de cette Tâche

Ajouter champs et méthodes à `core.Match` pour supporter :
1. **Matchs fixes** : Matchs verrouillés que le solver ne peut replanifier
2. **Statuts** : États du match (à planifier, planifié, fixé, terminé, annulé)
3. **Scores** : Résultats équipe1/équipe2 si match terminé
4. **Notes** : Commentaires libres

**Durée estimée** : 20 minutes

## Instructions Techniques

### 1. Localiser la Classe Match

**Fichier** : `core/models.py`

Trouver la dataclass `Match`. Elle contient actuellement :
- `equipe1: Equipe`
- `equipe2: Equipe`
- `poule: str`
- `creneau: Optional[Creneau]`
- `priorite: int`

### 2. Ajouter Nouveaux Champs

Ajouter **après les champs existants**, **avant toute méthode** :

```python
@dataclass
class Match:
    # ... champs existants (equipe1, equipe2, poule, creneau, priorite) ...
    
    # NOUVEAUX CHAMPS
    est_fixe: bool = False
    statut: str = "a_planifier"  # a_planifier|planifie|fixe|termine|annule
    score_equipe1: Optional[int] = None
    score_equipe2: Optional[int] = None
    notes: str = ""
```

**Points critiques** :
- Tous les champs ont **valeurs par défaut** (compatibilité code existant)
- `Optional[int]` nécessite import : `from typing import Optional` (vérifier présence)
- Statuts valides : `"a_planifier"`, `"planifie"`, `"fixe"`, `"termine"`, `"annule"`

### 3. Ajouter Méthode est_modifiable()

Ajouter **dans la classe Match**, après les champs :

```python
def est_modifiable(self) -> bool:
    """Indique si le match peut être replanifié par le solver."""
    return not self.est_fixe and self.statut not in ["fixe", "termine", "annule"]
```

**Logique** :
- Retourne `False` si `est_fixe == True`
- Retourne `False` si statut dans `["fixe", "termine", "annule"]`
- Sinon retourne `True`

### 4. Ajouter Property est_planifie

Ajouter **dans la classe Match** :

```python
@property
def est_planifie(self) -> bool:
    """Indique si le match a un créneau assigné."""
    return self.creneau is not None
```

**Logique** : Un match est planifié s'il a un créneau (semaine/horaire/gymnase).

### 5. Vérifier Imports

En haut du fichier `core/models.py`, vérifier présence de :

```python
from typing import Optional
from dataclasses import dataclass
```

## Validation

### Test 1 : CLI Fonctionne Toujours

```bash
python main.py configs/config_volley.yaml
```

**Attendu** :
- ✅ Aucune erreur
- ✅ Calendrier généré
- ✅ Export HTML fonctionne

### Test 2 : Matchs Générés Ont Valeurs Par Défaut

Ajouter test temporaire dans `main.py` ou créer script :

```python
from core.config import Config
from data.data_source import DataSource
from generators.multi_pool_generator import MultiPoolGenerator

config = Config.from_yaml("configs/config_volley.yaml")
source = DataSource(config.fichier_donnees)
equipes = source.charger_equipes()
poules = source.get_poules_dict(equipes)
generator = MultiPoolGenerator()
matchs = generator.generer_matchs(poules)

# Vérifier premier match
m = matchs[0]
assert m.est_fixe == False, "est_fixe doit être False par défaut"
assert m.statut == "a_planifier", "statut doit être 'a_planifier'"
assert m.score_equipe1 is None, "score_equipe1 doit être None"
assert m.est_modifiable() == True, "Match par défaut doit être modifiable"

print("✅ Validation réussie : Match a bien les nouveaux champs avec valeurs par défaut")
```

### Test 3 : Méthode est_modifiable()

```python
# Match standard
m = Match(equipe1, equipe2, "P1", creneau=None, priorite=0)
assert m.est_modifiable() == True

# Match fixé
m.est_fixe = True
assert m.est_modifiable() == False

# Match terminé
m2 = Match(equipe1, equipe2, "P1", creneau=None, priorite=0)
m2.statut = "termine"
assert m2.est_modifiable() == False

print("✅ Logique est_modifiable() correcte")
```

## Critères de Réussite

- [ ] Fichier `core/models.py` modifié
- [ ] 5 nouveaux champs ajoutés avec valeurs par défaut
- [ ] Méthode `est_modifiable()` implémentée
- [ ] Property `est_planifie` implémentée
- [ ] `python main.py configs/config_volley.yaml` fonctionne sans erreur
- [ ] Tests valident valeurs par défaut et logique méthodes

## Prochaine Étape

➡️ **Prompt 1.2** : Ajouter contrainte `semaine_min` dans `core/config.py`
