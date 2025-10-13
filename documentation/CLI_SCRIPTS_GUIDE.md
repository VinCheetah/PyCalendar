# 📘 Guide Utilisateur - Scripts CLI PyCalendar

## 🎯 Vue d'ensemble

Ce guide explique comment utiliser les scripts CLI de PyCalendar pour initialiser la base de données et importer des projets sportifs depuis des fichiers YAML + Excel.

**Scripts disponibles** :
- `scripts/init_db.py` - Initialise la base de données SQLite
- `scripts/import_excel.py` - Importe un projet depuis YAML + Excel

---

## 🚀 Démarrage rapide (3 commandes)

```bash
# 1. Initialiser la base de données
python scripts/init_db.py

# 2. Importer un projet
python scripts/import_excel.py configs/config_volley.yaml "Championnat Volley 2025"

# 3. Démarrer l'API
python run_api.py
```

📖 **Accéder à la documentation API** : http://localhost:8000/docs

---

## 📦 1. init_db.py - Initialisation de la base de données

### Usage basique

```bash
python scripts/init_db.py
```

### Ce que fait le script

1. ✅ Vérifie si une base de données existe déjà
2. ✅ Demande confirmation avant de la recréer (si existante)
3. ✅ Sauvegarde l'ancienne DB en `.db.bak`
4. ✅ Crée toutes les tables SQLAlchemy (projects, teams, venues, matches)
5. ✅ Affiche la liste des tables créées

### Exemples de sortie

**Première initialisation (DB inexistante)** :

```
============================================================
Initialisation de la base de données PyCalendar
============================================================

📂 Chemin de la base de données :
   /home/.../PyCalendar/database/pycalendar.db

🔧 Création des tables...
✅ Base de données créée : /home/.../database/pycalendar.db
   ✓ Tables créées avec succès

📊 Tables créées (4) :
   - projects
   - teams
   - venues
   - matches

✅ Initialisation terminée avec succès!
```

**DB existante - Avec confirmation** :

```
============================================================
Initialisation de la base de données PyCalendar
============================================================

📂 Chemin de la base de données :
   /home/.../PyCalendar/database/pycalendar.db

⚠️  Base de données existante détectée
Voulez-vous la recréer ? (oui/non) : oui

✓ Sauvegarde créée : .../database/pycalendar.db.bak

🔧 Création des tables...
✅ Base de données créée avec succès
   ✓ Tables créées avec succès

📊 Tables créées (4) :
   - projects
   - teams
   - venues
   - matches

✅ Initialisation terminée avec succès!
```

### Cas d'usage

| Situation | Commande | Résultat |
|-----------|----------|----------|
| Installation initiale | `python scripts/init_db.py` | Crée DB vide |
| Recréer DB (dev/test) | `python scripts/init_db.py` → Répondre "oui" | Backup + nouvelle DB |
| Annuler recréation | `python scripts/init_db.py` → Répondre "non" | Garde DB actuelle |

### ⚠️ Important

- **Sauvegarde automatique** : L'ancienne DB est toujours sauvegardée en `.db.bak`
- **Récupération** : Pour restaurer une sauvegarde :
  ```bash
  mv database/pycalendar.db.bak database/pycalendar.db
  ```

---

## 📥 2. import_excel.py - Import de projets

### Syntaxe

```bash
python scripts/import_excel.py <config_path> [project_name] [options]
```

### Arguments

| Argument | Type | Requis | Description |
|----------|------|--------|-------------|
| `config_path` | Positionnel | ✅ Oui | Chemin vers le fichier YAML de configuration |
| `project_name` | Positionnel | ❌ Non | Nom du projet (défaut: nom du fichier YAML) |

### Options

| Option | Raccourci | Description |
|--------|-----------|-------------|
| `--no-validate` | - | Désactive la validation de structure Excel |
| `--verbose` | `-v` | Affiche des informations détaillées pendant l'import |
| `--help` | `-h` | Affiche l'aide |

### Exemples d'utilisation

#### Exemple 1 : Import basique (nom automatique)

```bash
python scripts/import_excel.py configs/config_volley.yaml
```

**Résultat** :
```
🚀 Démarrage de l'import...

🏐 Chargement équipes et gymnases...
   → 126 équipes chargées
   → 7 gymnases chargés

🏗️ Création projet : config_volley
   → Project ID: 1

✅ Import terminé avec succès!
   📊 Projet : config_volley (ID: 1)
   👥 Équipes : 126
   🏟️ Gymnases : 7
   ⚽ Matchs : 216

======================================================================
✅ Import terminé avec succès!
======================================================================

📊 Statistiques du projet :
   ID         : 1
   Nom        : config_volley
   Sport      : Volleyball
   Semaines   : 10
   Semaine min: 1

📈 Données importées :
   Équipes    : 126
   Gymnases   : 7
   Matchs     : 216

🎯 État des matchs :
   Planifiés  : 0
   Fixés      : 0
   À planifier: 216

📁 Fichiers de configuration :
   YAML  : /home/.../configs/config_volley.yaml
   Excel : /home/.../data_volley/config_volley.xlsx

💡 Prochaines étapes :
   1. Démarrer l'API : python run_api.py
   2. Ou : uvicorn backend.api.main:app --reload
   3. Accéder à la documentation : http://localhost:8000/docs
```

#### Exemple 2 : Import avec nom personnalisé

```bash
python scripts/import_excel.py configs/config_volley.yaml "Championnat Volley 2025"
```

**Résultat** :
```
✅ Import terminé avec succès!

📊 Statistiques du projet :
   ID         : 1
   Nom        : Championnat Volley 2025    ← Nom personnalisé appliqué
   Sport      : Volleyball
   Équipes    : 126
   Matchs     : 216
```

#### Exemple 3 : Import verbose (mode debug)

```bash
python scripts/import_excel.py configs/config_volley.yaml "Debug Test" --verbose
```

**Résultat** :
```
🔍 Validation Excel : Activée

🚀 Démarrage de l'import...

🏐 Chargement équipes et gymnases...
   → 126 équipes chargées
   → 7 gymnases chargés

🏗️ Création projet : Debug Test
   → Project ID: 2

📦 Import des équipes...
   → 126 équipes importées

🏟️ Import des gymnases...
   → 7 gymnases importés

⚽ Génération des matchs...
   → 216 matchs générés
   → 216 matchs importés

✅ Import terminé avec succès!
...
```

#### Exemple 4 : Import sans validation (rapide)

```bash
python scripts/import_excel.py configs/config_handball.yaml --no-validate
```

**Avantages** :
- ⚡ Import plus rapide (~30% plus rapide)
- ✅ Utile pour fichiers déjà validés
- ⚠️ Pas de vérification de structure Excel

#### Exemple 5 : Combinaison d'options

```bash
python scripts/import_excel.py configs/config_basket.yaml "Basket 2025" --no-validate -v
```

---

## 🔍 Gestion des erreurs

### Erreur 1 : Base de données manquante

**Commande** :
```bash
python scripts/import_excel.py configs/config_volley.yaml
```

**Erreur** :
```
❌ Base de données non trouvée!
   Exécutez d'abord : python scripts/init_db.py
```

**Solution** :
```bash
python scripts/init_db.py
python scripts/import_excel.py configs/config_volley.yaml
```

### Erreur 2 : Fichier YAML inexistant

**Commande** :
```bash
python scripts/import_excel.py configs/inexistant.yaml
```

**Erreur** :
```
❌ Fichier YAML non trouvé : configs/inexistant.yaml
```

**Solution** :
- Vérifier le chemin du fichier
- Lister les fichiers disponibles :
  ```bash
  ls configs/*.yaml
  ```

### Erreur 3 : Fichier Excel manquant

**Commande** :
```bash
python scripts/import_excel.py configs/config_volley.yaml
```

**Erreur** :
```
❌ Erreur lors de l'import :
   [Errno 2] No such file or directory: '.../data_volley/inexistant.xlsx'
```

**Solution** :
- Vérifier le chemin Excel dans le YAML :
  ```yaml
  fichier_donnees: "data_volley/config_volley.xlsx"  # ← Vérifier ce chemin
  ```
- S'assurer que le fichier Excel existe

### Erreur 4 : Structure Excel invalide

**Commande** :
```bash
python scripts/import_excel.py configs/config_volley.yaml
```

**Erreur** :
```
❌ Erreur lors de l'import :
   Feuille 'Equipes' non trouvée dans le fichier Excel
```

**Solution** :
- Vérifier que l'Excel contient les feuilles requises :
  - `Equipes` (avec colonnes : Nom, Catégorie, Niveau, Gymnase, Jour, Horaire)
  - `Gymnases` (avec colonnes : Nom, Horaires disponibles)
- Utiliser `--no-validate` si la structure est différente mais valide

---

## 📊 Interprétation des statistiques

### Section "📊 Statistiques du projet"

```
📊 Statistiques du projet :
   ID         : 1              ← ID unique en base de données
   Nom        : Volley 2025    ← Nom du projet
   Sport      : Volleyball     ← Détecté automatiquement depuis Excel
   Semaines   : 10             ← Nombre de semaines de compétition
   Semaine min: 1              ← Numéro de première semaine
```

### Section "📈 Données importées"

```
📈 Données importées :
   Équipes    : 126    ← Nombre d'équipes importées
   Gymnases   : 7      ← Nombre de gymnases/lieux disponibles
   Matchs     : 216    ← Nombre de matchs générés (round-robin)
```

### Section "🎯 État des matchs"

```
🎯 État des matchs :
   Planifiés  : 0      ← Matchs avec semaine assignée
   Fixés      : 0      ← Matchs avec contrainte "fixe"
   À planifier: 216    ← Matchs sans semaine (= Total - Planifiés)
```

**Note** : Après import initial, tous les matchs sont "À planifier". La planification se fait ensuite via l'API ou l'algorithme d'optimisation.

---

## 🔄 Workflows courants

### Workflow 1 : Installation initiale

```bash
# 1. Cloner le projet
git clone <repo_url>
cd PyCalendar

# 2. Créer environnement virtuel
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate  # Windows

# 3. Installer dépendances
pip install -r requirements.txt

# 4. Initialiser DB
python scripts/init_db.py

# 5. Importer premier projet
python scripts/import_excel.py configs/config_volley.yaml "Volley 2025"

# 6. Démarrer API
python run_api.py
```

### Workflow 2 : Ajouter un nouveau projet

```bash
# 1. Créer fichier YAML de configuration
cp configs/config_volley.yaml configs/config_handball.yaml

# 2. Éditer le nouveau YAML (chemin Excel, paramètres)

# 3. Importer le projet
python scripts/import_excel.py configs/config_handball.yaml "Handball 2025"

# 4. Vérifier via API
curl http://localhost:8000/api/projects
```

### Workflow 3 : Recréer DB pour tests

```bash
# 1. Sauvegarder manuellement (optionnel)
cp database/pycalendar.db database/pycalendar.db.manual_backup

# 2. Recréer DB
python scripts/init_db.py
# Répondre "oui" à la confirmation

# 3. Réimporter projets
python scripts/import_excel.py configs/config_volley.yaml
python scripts/import_excel.py configs/config_handball.yaml

# 4. Relancer API
python run_api.py
```

### Workflow 4 : Mise à jour des données d'un projet

```bash
# 1. Modifier Excel (ajouter équipes, changer gymnases)

# 2. Supprimer ancien projet via API
curl -X DELETE http://localhost:8000/api/projects/1

# 3. Réimporter avec même nom
python scripts/import_excel.py configs/config_volley.yaml "Volley 2025"
```

### Workflow 5 : Import multiple en batch

```bash
# Importer tous les projets disponibles
for config in configs/*.yaml; do
    name=$(basename "$config" .yaml)
    python scripts/import_excel.py "$config" "$name"
done
```

---

## 🎨 Personnalisation

### Modifier le nom de la base de données

**Fichier** : `backend/database/session.py`

```python
# Avant
DATABASE_URL = "sqlite:///./database/pycalendar.db"

# Après (exemple : DB dans /var/lib)
DATABASE_URL = "sqlite:////var/lib/pycalendar/data.db"
```

**Note** : Penser à créer le répertoire avant `init_db.py` :
```bash
mkdir -p /var/lib/pycalendar
python scripts/init_db.py
```

### Ajouter un nouveau sport à la détection automatique

**Fichier** : `backend/services/sync_service.py`

```python
def _detect_sport(self, config: Config) -> str:
    fichier = config.fichier_donnees.lower()
    
    if "volley" in fichier:
        return "Volleyball"
    elif "handball" in fichier or "hand" in fichier:
        return "Handball"
    # Ajouter ici :
    elif "rugby" in fichier:
        return "Rugby"
    elif "badminton" in fichier:
        return "Badminton"
    else:
        return "Autre"
```

### Désactiver la validation Excel par défaut

**Fichier** : `scripts/import_excel.py`

```python
# Ligne ~30
parser.add_argument("--validate", action="store_true",
                    help="Activer la validation Excel (désactivée par défaut)")

# Plus bas, ligne ~50
validate_excel = args.validate  # Au lieu de : not args.no_validate
```

---

## 🐛 Dépannage

### Problème : "ModuleNotFoundError: No module named 'backend'"

**Cause** : Script lancé depuis mauvais répertoire

**Solution** :
```bash
# S'assurer d'être à la racine du projet
cd /path/to/PyCalendar
python scripts/import_excel.py ...
```

### Problème : "sqlite3.OperationalError: table teams already exists"

**Cause** : Tables déjà créées dans la DB

**Solution 1** : Recréer la DB
```bash
python scripts/init_db.py
# Répondre "oui"
```

**Solution 2** : Supprimer et recréer
```bash
rm database/pycalendar.db
python scripts/init_db.py
```

### Problème : Import lent (> 10 secondes)

**Cause** : Validation Excel activée sur gros fichier

**Solution** : Désactiver la validation
```bash
python scripts/import_excel.py configs/config.yaml --no-validate
```

### Problème : "ValueError: projet avec ce nom existe déjà"

**Cause** : Contrainte unicité sur `Project.nom`

**Solution 1** : Utiliser nom différent
```bash
python scripts/import_excel.py configs/config.yaml "Volley 2025 v2"
```

**Solution 2** : Supprimer ancien projet via API
```bash
curl -X DELETE http://localhost:8000/api/projects/1
python scripts/import_excel.py configs/config.yaml "Volley 2025"
```

---

## 💡 Conseils et bonnes pratiques

### ✅ À faire

- **Initialiser la DB avant tout import**
  ```bash
  python scripts/init_db.py
  ```

- **Utiliser noms de projet descriptifs**
  ```bash
  python scripts/import_excel.py configs/config.yaml "Championnat Volley Académique 2025-2026"
  ```

- **Activer verbose pour debug**
  ```bash
  python scripts/import_excel.py configs/config.yaml -v
  ```

- **Sauvegarder DB avant recréation**
  ```bash
  cp database/pycalendar.db database/backup_$(date +%Y%m%d).db
  python scripts/init_db.py
  ```

### ❌ À éviter

- **Ne pas importer sans vérifier la DB**
  ```bash
  # Mauvais
  python scripts/import_excel.py configs/config.yaml
  # ❌ Erreur : DB non trouvée
  
  # Bon
  python scripts/init_db.py
  python scripts/import_excel.py configs/config.yaml
  ```

- **Ne pas réutiliser le même nom de projet**
  ```bash
  # Mauvais (doublon)
  python scripts/import_excel.py configs/config1.yaml "Volley"
  python scripts/import_excel.py configs/config2.yaml "Volley"
  # ❌ Erreur : nom existe déjà
  
  # Bon
  python scripts/import_excel.py configs/config1.yaml "Volley CMR"
  python scripts/import_excel.py configs/config2.yaml "Volley SPCO"
  ```

- **Ne pas lancer plusieurs imports en parallèle**
  ```bash
  # Mauvais
  python scripts/import_excel.py configs/config1.yaml &
  python scripts/import_excel.py configs/config2.yaml &
  # ⚠️ Risque de corruption DB
  
  # Bon (séquentiel)
  python scripts/import_excel.py configs/config1.yaml
  python scripts/import_excel.py configs/config2.yaml
  ```

---

## 📚 Ressources supplémentaires

### Fichiers de documentation

- **Rapport technique détaillé** : `documentation/TASK_1.7_SCRIPTS_CLI_REPORT.md`
- **Guide SyncService** : `documentation/SYNC_SERVICE_GUIDE.md`
- **Architecture backend** : `documentation/PHASE_1_BACKEND_COMPLETE.md`

### API Documentation

- **Swagger UI** : http://localhost:8000/docs (après `python run_api.py`)
- **ReDoc** : http://localhost:8000/redoc

### Endpoints utiles

```bash
# Lister tous les projets
GET http://localhost:8000/api/projects

# Détails d'un projet
GET http://localhost:8000/api/projects/1

# Équipes d'un projet
GET http://localhost:8000/api/projects/1/teams

# Matchs d'un projet
GET http://localhost:8000/api/projects/1/matches

# Supprimer un projet
DELETE http://localhost:8000/api/projects/1
```

---

## 📞 Support

### Questions fréquentes

**Q : Puis-je importer plusieurs projets dans la même DB ?**  
R : Oui ! Chaque projet a un ID unique. Importez autant de projets que nécessaire.

**Q : Comment supprimer un projet ?**  
R : Via l'API : `curl -X DELETE http://localhost:8000/api/projects/{id}`

**Q : Le script modifie-t-il mes fichiers Excel ?**  
R : Non, les fichiers YAML/Excel sont en lecture seule. Seule la DB est modifiée.

**Q : Puis-je importer le même fichier Excel plusieurs fois ?**  
R : Oui, avec des noms de projet différents à chaque fois.

**Q : Que faire si l'import plante à 50% ?**  
R : Transaction rollback automatique. Rien n'est créé en DB. Corriger l'erreur et relancer.

### Besoin d'aide ?

- **Issues GitHub** : <repo_url>/issues
- **Email** : support@pycalendar.com
- **Documentation complète** : <repo_url>/wiki

---

**Version** : PyCalendar V2 - Phase 1.7  
**Dernière mise à jour** : Janvier 2025
