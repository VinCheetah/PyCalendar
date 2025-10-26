# 🎉 PyCalendar - Système Unifié et Prêt à l'Emploi

## ✅ État Actuel du Système

### Migration Complétée

Le système PyCalendar a été **entièrement migré vers un format unique** :

- ❌ **AVANT** : Formats v1.0 (legacy) et v2.0 (enrichi) coexistaient
- ✅ **MAINTENANT** : Un seul format enrichi, validation automatique

### Structure Simplifiée

```
solutions/                          ← Un seul dossier (plus de v1.0/v2.0/)
├── latest_volley.json             ← Dernière solution
├── latest_volley_backup.json      ← Sauvegarde
└── solution_volley_*.json         ← Historique avec timestamps
```

## 🚀 Utilisation - Commandes Principales

### 1. Générer un Planning Complet

```bash
# Volleyball (recommandé)
python main.py configs/config_volley.yaml

# Handball
python main.py configs/config_hand.yaml

# Configuration par défaut
python main.py
```

**Résultat** : Génère automatiquement
- ✅ Solution JSON validée (`solutions/latest_volley.json`)
- ✅ Fichier Excel (`data_volley/calendrier_volley.xlsx`)
- ✅ Interface HTML interactive (`data_volley/calendrier_volley.html`)

### 2. Valider une Solution

```bash
# Validation complète
python validate_solution.py solutions/latest_volley.json

# Mode verbose (détails complets)
python validate_solution.py solutions/latest_volley.json --verbose

# Mode silencieux (erreurs uniquement)
python validate_solution.py solutions/latest_volley.json --quiet
```

### 3. Régénérer l'Interface Seule

```bash
# Défaut (latest_volley.json)
python regenerate_interface.py

# Solution spécifique
python regenerate_interface.py --solution mon_fichier.json --output calendrier.html
```

## 📋 Workflow Recommandé

### Première Utilisation

```bash
# 1. Vérifier la configuration
cat configs/config_volley.yaml

# 2. Générer le planning
python main.py configs/config_volley.yaml

# 3. Vérifier la validation (automatique)
# → Le système valide automatiquement à la génération

# 4. Ouvrir l'interface
firefox data_volley/calendrier_volley.html
# ou
google-chrome data_volley/calendrier_volley.html
```

### Après Modifications Manuelles

```bash
# 1. Éditer la solution JSON
nano solutions/latest_volley.json

# 2. Valider les changements
python validate_solution.py solutions/latest_volley.json

# 3. Régénérer l'interface
python regenerate_interface.py

# 4. Vérifier le résultat
firefox data_volley/calendrier_volley.html
```

## 🎯 Fonctionnalités Clés

### ✨ Format de Données Enrichi

Le format JSON inclut maintenant :

```json
{
  "version": "2.0",
  "metadata": {...},           // Informations générales
  "entities": {                // Données de référence
    "equipes": [...],
    "gymnases": [...],
    "poules": [...]
  },
  "matches": {                 // Matchs planifiés et non planifiés
    "scheduled": [...],
    "unscheduled": [...]
  },
  "slots": {                   // Créneaux disponibles et occupés
    "available": [...],
    "occupied": [...]
  },
  "statistics": {...},         // Statistiques complètes
  "config_signature": {...}    // Signature pour détection changements
}
```

### 🔍 Validation Automatique

**7 catégories de validation** :
1. ✅ **Schema** : Conformité JSON Schema Draft 7
2. ✅ **Genre** : Cohérence F/M dans poules et matchs
3. ✅ **Poule** : Vérification des poules et équipes
4. ✅ **Match** : Détection doublons et conflits
5. ✅ **Slot** : Vérification occupation et capacités
6. ✅ **Statistics** : Cohérence des statistiques
7. ✅ **Institution** : Contraintes métier

**3 niveaux de sévérité** : 🔴 ERROR, ⚠️ WARNING, ℹ️ INFO

### 🌐 Interface HTML Interactive

**4 vues différentes** :
- 📅 **Agenda** : Vue par semaine/horaire
- 📊 **Timeline** : Vue chronologique
- 🏢 **Gymnases** : Organisation par lieu
- 🎯 **Poules** : Répartition par groupe

**Fonctionnalités** :
- Filtres dynamiques (poule/équipe/gymnase/semaine)
- Double-clic pour modifier les matchs
- Export PDF/impression
- Statistiques en temps réel

## 🔧 Configuration

### Fichier YAML Simplifié

```yaml
fichiers:
  donnees: "data_volley/config_volley.xlsx"
  sortie: "data_volley/calendrier_volley.xlsx"
  # Plus besoin de "solution_format" !

planification:
  nb_semaines: 14
  semaine_min: 3
  strategie: "cpsat"

cpsat:
  temps_limite: 300      # 5 minutes
  warm_start: true       # Réutiliser solution précédente
```

### Fichier Excel de Données

**Feuilles requises** :
- `Equipes` : Équipes avec genre, poule, institution
- `Gymnases` : Gymnases avec capacités et créneaux

**Feuilles optionnelles** :
- `Poules` : Configuration des poules
- `MatchsFixes` : Matchs déjà planifiés
- `Indispos_Gymnases` : Indisponibilités
- `ObligationsPresence` : Contraintes de présence
- etc.

## 📚 Documentation

### Guides Principaux

| Document | Description |
|----------|-------------|
| `GUIDE_UTILISATION.md` | 📖 Guide complet d'utilisation |
| `VALIDATION_GUIDE.md` | 🔍 Système de validation |
| `MIGRATION_COMPLETE.md` | 🔄 Détails de la migration v2.0 |
| `README.md` | 📚 Documentation technique |

### Guides Techniques

| Document | Description |
|----------|-------------|
| `docs/FORMAT_V2_GUIDE.md` | 📊 Format de données JSON |
| `VALIDATION_IMPLEMENTATION.md` | ⚙️ Implémentation validation |
| `GUIDE_CONFIGURATION_CENTRALE.md` | 🎛️ Configuration Excel |

## ⚠️ Notes Importantes

### Anciennes Solutions

Les solutions générées **avant la migration** peuvent avoir des erreurs de validation :
- Champs manquants : `slot_id`, `status` dans les slots
- Genres en minuscules : `f`, `m` au lieu de `F`, `M`

**Solution** : Régénérer avec `python main.py configs/config_volley.yaml`

### Fichiers Obsolètes

Ces fichiers peuvent être supprimés :
- ❌ `scripts/convert_solution_to_v2.py` (conversion plus nécessaire)
- ❌ `MIGRATION_V2_ANALYSIS.md` (document historique)
- ❌ Dossiers `solutions/v1.0/` et `solutions/v2.0/` (déjà supprimés)

### Warm Start CP-SAT

Le système **réutilise automatiquement** les solutions précédentes pour accélérer CP-SAT :
- Solutions sauvegardées dans `solutions/`
- Détection automatique des changements de configuration
- Adaptation intelligente si données modifiées

## 🆘 Résolution de Problèmes

### Erreur : "Module 'interface' not found"

```bash
# Vérifier que le module interface existe
ls -la interface/core/

# Réinstaller si nécessaire
pip install -r requirements.txt
```

### Validation Échoue

```bash
# Voir les détails
python validate_solution.py solutions/latest_volley.json --verbose

# Si erreurs de schéma, régénérer
python main.py configs/config_volley.yaml
```

### Interface ne se Charge Pas

```bash
# 1. Valider le JSON
python validate_solution.py solutions/latest_volley.json

# 2. Régénérer l'interface
python regenerate_interface.py

# 3. Vérifier les erreurs navigateur (F12)
```

## 🎉 En Résumé

### ✅ Avantages du Système Unifié

1. **Simplicité** : Un seul format, une seule commande
2. **Fiabilité** : Validation automatique à chaque génération
3. **Performance** : Warm start CP-SAT automatique
4. **Maintenabilité** : Code plus simple, moins de bugs
5. **Expérience** : Interface moderne générée automatiquement

### 🚀 Commande Magique

```bash
python main.py configs/config_volley.yaml
```

Cette **unique commande** :
- ✅ Charge les données Excel
- ✅ Génère le planning optimal (CP-SAT ou Greedy)
- ✅ Sauvegarde la solution JSON validée
- ✅ Crée le fichier Excel formaté
- ✅ Génère l'interface HTML interactive
- ✅ Affiche les statistiques complètes

---

**Version** : 2.0 (Format Unique)  
**Date** : 26 Janvier 2025  
**Statut** : ✅ Production Ready

**Support** : Consultez `GUIDE_UTILISATION.md` pour plus de détails
