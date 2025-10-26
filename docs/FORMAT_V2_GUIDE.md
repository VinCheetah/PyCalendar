# 🔄 Migration vers le format Solution v2.0

## Vue d'ensemble

PyCalendar utilise désormais **exclusivement le format v2.0** pour les solutions, offrant des données enrichies et structurées pour une meilleure compatibilité avec l'interface web.

## Changements principaux

### ✅ Avant (v1.0)
- Format simple avec liste d'assignments
- Données minimales (match_id, équipes, créneau)
- Conversion externe nécessaire pour l'interface
- Pas de validation automatique

### ✨ Maintenant (v2.0)
- **Génération directe** : Plus de conversion intermédiaire
- **Données complètes** : Entities (équipes, gymnases, poules), matches enrichis, slots, statistics
- **Validation automatique** : Vérification contre le schema JSON
- **Pénalités** : Infrastructure prête (calculs à implémenter)
- **Stats avancées** : Taux d'occupation, répartition par poule/gymnase/équipe

## Structure du format v2.0

```json
{
  "version": "2.0",
  "generated_at": "2025-10-26T...",
  
  "metadata": {
    "solution_name": "volley",
    "solver": "cpsat",
    "status": "FEASIBLE",
    "score": 1615395.0,
    "execution_time_seconds": 45.2
  },
  
  "config": { /* Configuration et contraintes */ },
  "entities": { /* Equipes, Gymnases, Poules */ },
  "matches": { /* Scheduled et Unscheduled */ },
  "slots": { /* Available et Occupied */ },
  "statistics": { /* Global, par semaine, poule, gymnase, équipe */ }
}
```

Voir [solution_schema.json](../interface/data/schemas/solution_schema.json) pour le schema complet.

## Utilisation

### Génération d'une solution

```bash
# Le format v2.0 est généré automatiquement
python main.py configs/config_volley.yaml
```

La solution est sauvegardée dans `solutions/v2.0/latest_<config_name>.json`

### Validation d'une solution

```bash
# Valider un fichier JSON
python -m interface.core.validator solutions/v2.0/latest_volley.json

# Validation silencieuse (juste OK/KO)
python -m interface.core.validator solutions/v2.0/latest_volley.json --quiet
```

### Génération de l'interface HTML

```bash
# Génère l'interface depuis le JSON v2.0
python regenerate_interface.py --solution latest_volley.json
```

L'interface utilise directement le format v2.0 sans conversion.

## Nouveautés techniques

### DataFormatter

Module central pour transformer les objets Python en JSON v2.0 :

```python
from interface.core.data_formatter import DataFormatter

v2_data = DataFormatter.format_solution(
    solution=solution,
    config=config,
    equipes=equipes_list,
    gymnases=gymnases_list,
    creneaux_disponibles=all_creneaux
)
```

### Validation automatique

Validation contre le schema JSON lors de la sauvegarde :

```python
from interface.core.validator import SolutionValidator

validator = SolutionValidator()
is_valid, errors = validator.validate(solution_data)

if not is_valid:
    for error in errors:
        print(f"❌ {error}")
```

### Infrastructure pénalités

Structure prête pour les calculs futurs :

```python
# Chaque type de pénalité a sa propre méthode
penalties = {
    "total": 0.0,
    "horaire_prefere": 0.0,      # TODO: À implémenter
    "espacement": 0.0,            # TODO: À implémenter  
    "indisponibilite": 0.0,       # TODO: À implémenter
    "compaction": 0.0,            # TODO: À implémenter
    "overlap": 0.0,               # TODO: À implémenter
}
```

Voir `interface/core/data_formatter.py` pour les TODOs détaillés.

## Migration depuis v1.0

### Solutions existantes

Les anciennes solutions v1.0 peuvent être converties avec :

```bash
python scripts/convert_solution_to_v2.py solutions/old_solution.json
```

### Code personnalisé

Si vous utilisez le format v1.0 dans votre code :

**Avant :**
```python
# Lecture manuelle du JSON v1.0
with open('solution.json') as f:
    data = json.load(f)
    assignments = data['assignments']
```

**Maintenant :**
```python
# Utiliser directement le format v2.0
with open('solutions/v2.0/latest_volley.json') as f:
    data = json.load(f)
    matches = data['matches']['scheduled']
    entities = data['entities']
    stats = data['statistics']
```

## Fichiers modifiés

- ✅ `core/solution_store.py` : Génération directe v2.0 via DataFormatter
- ✅ `orchestrator/pipeline.py` : Appel avec tous les paramètres nécessaires
- ✅ `interface/core/data_formatter.py` : Enrichissement complet des données
- ✅ `interface/core/validator.py` : Validation automatique JSON Schema
- ✅ `requirements.txt` : Ajout de `jsonschema>=4.19.0`

## Avantages

| Aspect | v1.0 | v2.0 |
|--------|------|------|
| **Génération** | 2 étapes (v1.0 → conversion → v2.0) | 1 étape directe |
| **Données** | Minimales | Complètes et enrichies |
| **Validation** | Aucune | Automatique avec schema |
| **Stats** | Calculées côté interface | Pré-calculées |
| **Pénalités** | Absentes | Infrastructure prête |
| **Taille fichier** | ~50 KB | ~200 KB (mais compressible) |
| **Performance** | - | Meilleure (moins de calculs côté client) |

## Prochaines étapes

### TODO : Implémentation des pénalités

Les fonctions suivantes sont prêtes à recevoir les calculs :

1. `_calculate_horaire_prefere_penalty()` : Pénalité horaire non préféré
2. `_calculate_espacement_penalty()` : Pénalité espacement trop court/long
3. `_calculate_indisponibilite_penalty()` : Pénalité indisponibilité équipe
4. `_calculate_compaction_penalty()` : Pénalité répartition semaines
5. `_calculate_overlap_penalty()` : Pénalité chevauchement institutions

Voir les TODOs détaillés dans `interface/core/data_formatter.py`.

### TODO : Stats avancées

- Détection automatique de conflits
- Métriques de qualité globale
- Analyse par institution
- Recommandations d'amélioration

## Support

Pour toute question ou problème :

1. Vérifier [MIGRATION_V2_ANALYSIS.md](MIGRATION_V2_ANALYSIS.md) pour les détails techniques
2. Consulter le schema [solution_schema.json](../interface/data/schemas/solution_schema.json)
3. Valider votre JSON avec `python -m interface.core.validator`

---

**Version** : 2.0  
**Date** : 26 octobre 2025  
**Status** : ✅ Production
