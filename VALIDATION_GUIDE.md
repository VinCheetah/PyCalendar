# Guide de Validation des Solutions PyCalendar

## 📋 Vue d'ensemble

Le système de validation PyCalendar v2.0 vérifie la conformité des solutions générées selon deux axes :
1. **Validation de schéma** : Conformité au JSON Schema (structure, types)
2. **Validation métier** : Règles de cohérence et contraintes business

## 🎯 Utilisation

### Validation automatique (intégrée)

La validation s'exécute **automatiquement** après chaque génération de solution :

```bash
python main.py
```

À la fin du processus, vous verrez :
```
🔍 Validation du format v2.0...
  ✅ Solution v2.0 valide - aucun problème détecté
```

Ou en cas de problèmes :
```
📊 Résumé validation: 10 erreur(s), 5 avertissement(s), 2 info(s)
```

### Validation manuelle (script standalone)

Pour valider un fichier existant :

```bash
# Validation d'un fichier spécifique
python validate_solution.py solutions/v2.0/latest_volley.json

# Rapport détaillé
python validate_solution.py solutions/v2.0/latest_volley.json --verbose

# Valider tous les fichiers d'un répertoire
python validate_solution.py --all

# Valider un autre répertoire
python validate_solution.py --all --dir output/
```

## 📊 Niveaux de sévérité

### ❌ ERROR (Bloquant)
Problèmes critiques qui invalident la solution :
- Genres invalides (autre que M/F)
- Matchs inter-genres
- Matchs contre soi-même
- Double occupation de créneaux
- Dépassement de capacité gymnase
- Violations d'indisponibilités

### ⚠️ WARNING (Important)
Problèmes significatifs mais non-bloquants :
- Matchs en double
- Équipes dans plusieurs poules
- Incohérences statistiques
- Flag `is_entente` incohérent

### ℹ️ INFO (Informatif)
Observations utiles :
- Trop de matchs par semaine (>2)
- Horaires non préférés
- Poules avec une seule équipe
- Pénalités élevées

## 🔍 Catégories de validation

### 1. Schema
Validation JSON Schema (structure, types, propriétés requises).

**Exemples d'erreurs** :
- Propriété manquante (`slot_id`, `status`)
- Type incorrect (nombre au lieu de chaîne)
- Valeur hors énumération

### 2. Genre
Cohérence des genres (M/F uniquement).

**Validations** :
- ✅ Genres valides (M, F ou vide)
- ✅ Pas de poules mixtes
- ✅ Pas de matchs inter-genres
- ✅ Cohérence poule-équipes

### 3. Poule
Intégrité des poules.

**Validations** :
- ✅ Une équipe = une seule poule
- ✅ Tailles déclarées = réelles
- ✅ Pas de poules vides
- ✅ Matchs intra-poule uniquement

### 4. Match
Cohérence des matchs.

**Validations** :
- ✅ Pas de match contre soi-même
- ✅ Références équipes/gymnases valides
- ✅ Pas de doublons
- ✅ Créneaux valides (semaine ≥ 1)

### 5. Slot (Créneau)
Gestion des créneaux horaires.

**Validations** :
- ✅ Pas de double occupation
- ✅ Respect capacités gymnases
- ✅ Cohérence slots/matchs

### 6. Statistiques
Exactitude des comptages.

**Validations** :
- ✅ Comptages global (déclaré = réel)
- ✅ Comptages par poule
- ✅ Taux de planification

### 7. Institution
Cohérence institutionnelle.

**Validations** :
- ✅ Institution dans nom équipe
- ✅ Flag `is_entente` cohérent

### 8. Règles métier
Contraintes business.

**Validations** :
- ✅ Max 2 matchs par semaine (recommandation)
- ✅ Respect horaires préférés
- ✅ Respect indisponibilités (CRITIQUE)
- ✅ Détection pénalités élevées (>100)

## 📄 Format du rapport

### Rapport résumé (par défaut)

```
================================================================================
Validation de: solutions/v2.0/latest_volley.json
================================================================================
📊 Résumé: 10 erreur(s), 5 avertissement(s), 2 info(s)

⚠️  Utiliser --verbose pour voir les détails
```

### Rapport détaillé (--verbose)

```
================================================================================
RAPPORT DE VALIDATION
================================================================================

📊 RÉSUMÉ
   Total: 17 problème(s)
   Erreurs: 10
   Avertissements: 5
   Informations: 2

📁 PAR CATÉGORIE
   Genre: 5
   Match: 3
   Slot: 7
   Règles métier: 2

❌ ERRORS (10)
--------------------------------------------------------------------------------

  Genre: Genre invalide: 'f'
  └─ equipe INP (1) [F]|f

  Slot: Double occupation: BESSON S1 16:00
  └─ matchs 2 et 4
     • gymnase: BESSON
     • semaine: 1
     • horaire: 16:00

⚠️ WARNINGS (5)
--------------------------------------------------------------------------------

  Match: Match en double: LYON 3 (6)|M vs SANTE (5)|M
  └─ match 55

ℹ️ INFOS (2)
--------------------------------------------------------------------------------

  Règles métier: 3 matchs en semaine 4 (max recommandé: 2)
  └─ equipe EML (1)|M
```

## 🛠️ Correction des erreurs courantes

### Genres en minuscules
**Problème** : `'f' is not one of ['M', 'F', '']`

**Cause** : Données source avec genres en minuscules

**Solution** : Corriger dans le fichier Excel source ou ajouter normalisation dans `data_loader.py`

### Double occupation
**Problème** : `Double occupation: BESSON S1 16:00`

**Cause** : Solver a assigné plusieurs matchs au même créneau

**Solution** : Bug du solver à corriger (contraintes d'unicité)

### Matchs inter-genres
**Problème** : `Match entre genres différents: M vs F`

**Cause** : Poules mixtes ou erreur d'assignation

**Solution** : Vérifier séparation poules M/F dans config

### Capacité dépassée
**Problème** : `Capacité dépassée: 3 matchs pour capacité 2`

**Cause** : Solver ne respecte pas la capacité gymnase

**Solution** : Bug du solver à corriger (contraintes de capacité)

## 🔧 Intégration dans le code

### Utiliser le validateur dans votre code

```python
from interface.core.validator import SolutionValidator, Severity
import json

# Charger solution
with open('solutions/v2.0/latest_volley.json', 'r') as f:
    data = json.load(f)

# Valider
validator = SolutionValidator()
is_valid, issues = validator.validate_full(data)

# Analyser résultats
errors = [i for i in issues if i.severity == Severity.ERROR]
warnings = [i for i in issues if i.severity == Severity.WARNING]

print(f"Valid: {is_valid}")
print(f"Errors: {len(errors)}")

# Générer rapport
if issues:
    report = validator.generate_report(issues)
    print(report)
```

### Filtrer par catégorie

```python
genre_issues = [i for i in issues if i.category == "Genre"]
slot_issues = [i for i in issues if i.category == "Slot"]
```

### Accéder aux détails

```python
for issue in issues:
    print(f"{issue.severity.value}: {issue.message}")
    print(f"Location: {issue.location}")
    if issue.details:
        print(f"Details: {issue.details}")
```

## 📈 Améliorations futures

- [ ] Export rapport en JSON/HTML
- [ ] Suggestions de correction automatiques
- [ ] Validation incrémentale (modification interface)
- [ ] Calcul effectif des pénalités (actuellement TODOs)
- [ ] Tests unitaires du validateur
- [ ] Benchmarks de performance
- [ ] Validation des contraintes configurables (YAML)

## 🐛 Dépannage

### `ImportError: No module named 'jsonschema'`

```bash
pip install jsonschema>=4.19.0
```

### `FileNotFoundError: Schema file not found`

Le schéma doit être dans `interface/data/schemas/solution_schema.json`.

### Validation lente sur gros fichiers

La validation est O(n) avec n = nombre de matchs. Pour ~1000 matchs, compter 1-2 secondes.

## 📚 Références

- **JSON Schema** : `interface/data/schemas/solution_schema.json`
- **Code validator** : `interface/core/validator.py`
- **Script CLI** : `validate_solution.py`
- **Format v2.0** : `FORMAT_V2_GUIDE.md`
- **Migration** : `MIGRATION_SUMMARY.md`
