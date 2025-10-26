# 🏐 PyCalendar - Guide d'Utilisation

## 🚀 Démarrage Rapide

### 1. Générer un Planning Complet

```bash
# Volleyball (configuration par défaut)
python main.py configs/config_volley.yaml

# Handball
python main.py configs/config_hand.yaml

# Configuration personnalisée
python main.py configs/ma_config.yaml
```

### 2. Fichiers Générés

Après l'exécution, PyCalendar génère automatiquement :

- **Solution JSON** : `solutions/latest_volley.json`
  - Format enrichi avec toutes les données
  - Validation automatique intégrée
  - Réutilisable pour warm-start CP-SAT

- **Fichier Excel** : `data_volley/calendrier_volley.xlsx`
  - Feuille de matchs planifiés
  - Prêt pour impression/distribution

- **Interface HTML** : `data_volley/calendrier_volley.html`
  - Interface interactive moderne
  - Filtres par poule/équipe/gymnase
  - Vue agenda et vue grille
  - Double-clic pour modifier les matchs

### 3. Valider une Solution

```bash
# Validation simple
python validate_solution.py solutions/latest_volley.json

# Validation détaillée
python validate_solution.py solutions/latest_volley.json --verbose

# Avec rapport silencieux (seulement erreurs)
python validate_solution.py solutions/latest_volley.json --quiet
```

### 4. Régénérer uniquement l'Interface

Si vous avez modifié la solution manuellement :

```bash
python regenerate_interface.py --solution latest_volley.json --output calendrier.html

# Ou simplement
python regenerate_interface.py
```

## 📁 Structure des Fichiers

```
PyCalendar/
├── main.py                      # Point d'entrée principal
├── configs/                     # Configurations
│   ├── default.yaml            # Configuration par défaut
│   ├── config_volley.yaml      # Volleyball
│   └── config_hand.yaml        # Handball
├── data_volley/                # Données volleyball
│   ├── config_volley.xlsx      # Données d'entrée
│   └── calendrier_volley.html  # Interface générée
├── solutions/                  # Solutions JSON
│   ├── latest_volley.json      # Dernière solution
│   └── solution_volley_*.json  # Historique
└── interface/                  # Code de l'interface
    └── core/
        ├── data_formatter.py   # Formatage JSON
        └── validator.py        # Validation
```

## ⚙️ Configuration

### Fichier de Configuration (YAML)

Les paramètres principaux :

```yaml
fichiers:
  donnees: "data_volley/config_volley.xlsx"
  sortie: "data_volley/calendrier_volley.xlsx"

planification:
  nb_semaines: 14
  semaine_min: 3
  strategie: "cpsat"  # ou "greedy"

cpsat:
  temps_limite: 300  # 5 minutes
  warm_start: true   # Réutiliser solution précédente
```

### Fichier Excel de Données

Feuilles requises :
- **Equipes** : Liste des équipes avec genre, poule, institution
- **Gymnases** : Liste des gymnases avec capacité et créneaux
- **Poules** : Configuration des poules (optionnel)
- **MatchsFixes** : Matchs déjà planifiés (optionnel)

## 🔍 Résolution de Problèmes

### Planification Partielle

**Symptôme** : Certains matchs ne sont pas planifiés

**Solutions** :
1. Augmentez `cpsat.temps_limite` dans la config
2. Vérifiez le nombre de créneaux disponibles
3. Réduisez les contraintes trop restrictives
4. Activez `cpsat.warm_start` pour réutiliser la solution précédente

### Erreurs de Validation

**Symptôme** : Validation échoue avec erreurs de schéma

**Solutions** :
1. Régénérez la solution avec `python main.py`
2. Les anciennes solutions peuvent manquer des champs requis
3. Vérifiez que le DataFormatter est à jour

### Interface ne se Charge Pas

**Symptôme** : L'interface HTML affiche une erreur

**Solutions** :
1. Validez d'abord le JSON : `python validate_solution.py solutions/latest_volley.json`
2. Régénérez l'interface : `python regenerate_interface.py`
3. Vérifiez la console du navigateur (F12)

## 📊 Workflow Complet

### Première Génération

```bash
# 1. Préparer les données Excel
nano data_volley/config_volley.xlsx

# 2. Configurer les paramètres
nano configs/config_volley.yaml

# 3. Générer le planning
python main.py configs/config_volley.yaml

# 4. Valider le résultat
python validate_solution.py solutions/latest_volley.json

# 5. Ouvrir l'interface
firefox data_volley/calendrier_volley.html
```

### Modifications Manuelles

```bash
# 1. Modifier la solution JSON
nano solutions/latest_volley.json

# 2. Valider les modifications
python validate_solution.py solutions/latest_volley.json

# 3. Régénérer l'interface
python regenerate_interface.py

# 4. Vérifier le résultat
firefox data_volley/calendrier_volley.html
```

## 🎯 Conseils d'Optimisation

### Pour CP-SAT

1. **Warm Start** : Activez `cpsat.warm_start: true` pour réutiliser les solutions précédentes
2. **Temps Limite** : Commencez avec 300s, augmentez si nécessaire
3. **Contraintes** : Désactivez les contraintes non critiques pour une première passe

### Pour Greedy

1. **Essais Multiples** : Augmentez `greedy.nb_essais` (10-20)
2. **Fallback** : Activez `planification.fallback_greedy` pour basculer automatiquement

### Performance

- **Réutilisation** : Les solutions sont automatiquement sauvegardées pour warm-start
- **Cache** : Les signatures de configuration détectent les changements
- **Validation** : Intégrée automatiquement, désactivable si besoin

## 📚 Documentation Technique

- **Format de Données** : `docs/FORMAT_V2_GUIDE.md`
- **Validation** : `VALIDATION_GUIDE.md`
- **Migration** : `MIGRATION_COMPLETE.md`
- **Architecture** : `README.md`

## 💡 Astuces

### Commandes Utiles

```bash
# Lister toutes les solutions
ls -lh solutions/*.json

# Comparer deux solutions
diff solutions/solution_volley_2025-01-24_120000.json \
     solutions/solution_volley_2025-01-24_130000.json

# Valider toutes les solutions
for f in solutions/*.json; do
    echo "Validation: $f"
    python validate_solution.py "$f" --quiet
done
```

### Variables d'Environnement

```bash
# Verbose mode (plus de logs)
export PYCALENDAR_VERBOSE=1
python main.py configs/config_volley.yaml

# Désactiver validation automatique
export PYCALENDAR_NO_VALIDATION=1
python main.py configs/config_volley.yaml
```

## 🆘 Support

En cas de problème :

1. Vérifiez les logs dans le terminal
2. Validez votre solution JSON
3. Consultez `VALIDATION_GUIDE.md`
4. Vérifiez la structure de vos données Excel

---

**Version** : 2.0 (Format Unique)  
**Dernière mise à jour** : 26 Janvier 2025
