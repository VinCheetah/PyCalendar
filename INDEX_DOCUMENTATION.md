# 📚 PyCalendar - Index de Documentation

Bienvenue dans la documentation complète de PyCalendar !

## 🚀 Démarrage

| Document | Description | Pour qui ? |
|----------|-------------|------------|
| **[DEMARRAGE_RAPIDE.md](DEMARRAGE_RAPIDE.md)** | 🎯 **Commencez ici !** Guide essentiel | Tous |
| **[GUIDE_UTILISATION.md](GUIDE_UTILISATION.md)** | 📖 Guide complet d'utilisation | Utilisateurs |
| **[README.md](README.md)** | 📚 Documentation technique | Développeurs |

## 🔄 Migration et Nouveautés

| Document | Description | Statut |
|----------|-------------|--------|
| **[MIGRATION_COMPLETE.md](MIGRATION_COMPLETE.md)** | ✅ Migration v2.0 complétée | ✅ Fait |
| **[VALIDATION_IMPLEMENTATION.md](VALIDATION_IMPLEMENTATION.md)** | ⚙️ Système de validation | ✅ Actif |

## 📊 Format de Données

| Document | Description | Version |
|----------|-------------|---------|
| **[docs/FORMAT_V2_GUIDE.md](docs/FORMAT_V2_GUIDE.md)** | 📋 Format JSON enrichi | v2.0 |
| **[FORMAT_SOLUTION.md](FORMAT_SOLUTION.md)** | 📄 Structure des solutions | v2.0 |
| **[STRUCTURE_SOLUTIONS.md](STRUCTURE_SOLUTIONS.md)** | 🗂️ Organisation fichiers | v2.0 |

## 🔍 Validation

| Document | Description | Détails |
|----------|-------------|---------|
| **[VALIDATION_GUIDE.md](VALIDATION_GUIDE.md)** | 🔍 Guide de validation | 7 catégories |
| **[VALIDATION_IMPLEMENTATION.md](VALIDATION_IMPLEMENTATION.md)** | ⚙️ Implémentation | Technique |

## ⚙️ Configuration

| Document | Description | Niveau |
|----------|-------------|--------|
| **[GUIDE_CONFIGURATION_CENTRALE.md](GUIDE_CONFIGURATION_CENTRALE.md)** | 🎛️ Config Excel complète | Avancé |
| **[GUIDE_GENERATION.md](GUIDE_GENERATION.md)** | 🔧 Génération de matchs | Technique |

## 📝 Données

| Document | Description | Usage |
|----------|-------------|-------|
| **[RECAPITULATIF_DONNEES.md](RECAPITULATIF_DONNEES.md)** | 📊 Structure données Excel | Référence |

## 🎯 Guides par Cas d'Usage

### Je veux générer un planning

1. **[DEMARRAGE_RAPIDE.md](DEMARRAGE_RAPIDE.md)** → Section "Générer un Planning Complet"
2. Commande : `python main.py configs/config_volley.yaml`
3. Résultat : JSON + Excel + HTML générés automatiquement

### Je veux valider ma solution

1. **[VALIDATION_GUIDE.md](VALIDATION_GUIDE.md)** → Utilisation
2. Commande : `python validate_solution.py solutions/latest_volley.json`
3. Rapport détaillé avec erreurs/warnings/infos

### Je veux configurer les contraintes

1. **[GUIDE_CONFIGURATION_CENTRALE.md](GUIDE_CONFIGURATION_CENTRALE.md)** → Feuilles Excel
2. **[README.md](README.md)** → Section Contraintes
3. Modifier `data_volley/config_volley.xlsx`

### Je veux comprendre le format JSON

1. **[docs/FORMAT_V2_GUIDE.md](docs/FORMAT_V2_GUIDE.md)** → Structure complète
2. **[FORMAT_SOLUTION.md](FORMAT_SOLUTION.md)** → Exemples
3. Voir `solutions/latest_volley.json`

### Je veux modifier l'interface HTML

1. **[interface/README.md](interface/README.md)** → Architecture
2. **[docs/AGENDA_SIDE_BY_SIDE.md](docs/AGENDA_SIDE_BY_SIDE.md)** → Vues
3. Code dans `interface/`

## 🗺️ Navigation Rapide

### Par Rôle

**Utilisateur Final** :
- [DEMARRAGE_RAPIDE.md](DEMARRAGE_RAPIDE.md)
- [GUIDE_UTILISATION.md](GUIDE_UTILISATION.md)
- [VALIDATION_GUIDE.md](VALIDATION_GUIDE.md)

**Administrateur** :
- [GUIDE_CONFIGURATION_CENTRALE.md](GUIDE_CONFIGURATION_CENTRALE.md)
- [RECAPITULATIF_DONNEES.md](RECAPITULATIF_DONNEES.md)
- [README.md](README.md)

**Développeur** :
- [README.md](README.md)
- [VALIDATION_IMPLEMENTATION.md](VALIDATION_IMPLEMENTATION.md)
- [docs/FORMAT_V2_GUIDE.md](docs/FORMAT_V2_GUIDE.md)
- [interface/README.md](interface/README.md)

### Par Tâche

**Génération** :
- Main : [GUIDE_UTILISATION.md](GUIDE_UTILISATION.md)
- Config : [GUIDE_CONFIGURATION_CENTRALE.md](GUIDE_CONFIGURATION_CENTRALE.md)
- Matchs : [GUIDE_GENERATION.md](GUIDE_GENERATION.md)

**Validation** :
- Guide : [VALIDATION_GUIDE.md](VALIDATION_GUIDE.md)
- Implémentation : [VALIDATION_IMPLEMENTATION.md](VALIDATION_IMPLEMENTATION.md)

**Interface** :
- Utilisation : [DEMARRAGE_RAPIDE.md](DEMARRAGE_RAPIDE.md)
- Technique : [interface/README.md](interface/README.md)
- Vues : [docs/AGENDA_SIDE_BY_SIDE.md](docs/AGENDA_SIDE_BY_SIDE.md)

## 🔧 Commandes Essentielles

### Génération

```bash
# Générer planning complet
python main.py configs/config_volley.yaml

# Avec config par défaut
python main.py
```

### Validation

```bash
# Validation complète
python validate_solution.py solutions/latest_volley.json

# Mode verbose
python validate_solution.py solutions/latest_volley.json --verbose

# Mode silencieux
python validate_solution.py solutions/latest_volley.json --quiet
```

### Interface

```bash
# Régénérer interface
python regenerate_interface.py

# Solution spécifique
python regenerate_interface.py --solution mon_fichier.json
```

## 📂 Structure Documentaire

```
PyCalendar/
├── DEMARRAGE_RAPIDE.md          ← 🎯 COMMENCEZ ICI
├── GUIDE_UTILISATION.md         ← Guide complet
├── README.md                    ← Documentation technique
│
├── Format et Validation
│   ├── VALIDATION_GUIDE.md
│   ├── VALIDATION_IMPLEMENTATION.md
│   ├── FORMAT_SOLUTION.md
│   └── STRUCTURE_SOLUTIONS.md
│
├── Configuration
│   ├── GUIDE_CONFIGURATION_CENTRALE.md
│   ├── GUIDE_GENERATION.md
│   └── RECAPITULATIF_DONNEES.md
│
├── Migration
│   └── MIGRATION_COMPLETE.md
│
└── docs/                        ← Documentation détaillée
    ├── FORMAT_V2_GUIDE.md
    ├── AGENDA_SIDE_BY_SIDE.md
    └── IMPORTATEUR_MATCHS_EXTERNES.md
```

## 🆘 Besoin d'Aide ?

1. **Démarrage** : [DEMARRAGE_RAPIDE.md](DEMARRAGE_RAPIDE.md)
2. **Problème spécifique** : Consultez le guide correspondant ci-dessus
3. **Erreur de validation** : [VALIDATION_GUIDE.md](VALIDATION_GUIDE.md)
4. **Configuration Excel** : [GUIDE_CONFIGURATION_CENTRALE.md](GUIDE_CONFIGURATION_CENTRALE.md)

## 📊 Statut de la Documentation

| Document | Statut | Dernière MAJ |
|----------|--------|--------------|
| DEMARRAGE_RAPIDE.md | ✅ À jour | 26/01/2025 |
| GUIDE_UTILISATION.md | ✅ À jour | 26/01/2025 |
| MIGRATION_COMPLETE.md | ✅ À jour | 26/01/2025 |
| VALIDATION_GUIDE.md | ✅ À jour | 24/01/2025 |
| README.md | ✅ À jour | 26/01/2025 |

---

**Version** : 2.0 (Format Unique)  
**Dernière mise à jour** : 26 Janvier 2025
