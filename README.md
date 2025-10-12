# PyCalendar - Système de planification sportive

Système modulaire et évolutif pour générer automatiquement des calendriers de compétitions sportives avec **configuration centrale unifiée**.

## 🎯 Fonctionnalités

- **Configuration centrale** : Un seul fichier Excel contient équipes, gymnases et **toutes les contraintes**
- **Contraintes institutionnelles** ## 🎓 Exemples

Voir le dossier `exemple/` pour un exemple complet de configuration avec :ppliquez des contraintes à toutes les équipes d'une institution
- **Obligations de présence** : Garantissez qu'une institution utilise son propre gymnase
- **Génération de matchs** : Round-robin automatique pour poules multiples
- **Contraintes modulaires** : Système flexible de contraintes dures et souples
- **Multiples algorithmes** : Greedy (rapide) ou CP-SAT (optimal)
- **Export Excel** : Calendriers formatés avec statistiques
- **Visualisation interactive** : Interface web HTML avec 4 vues différentes
  - 📅 Vue calendrier par semaine
  - 📊 Timeline chronologique
  - 🏢 Organisation par gymnase
  - 🎯 Répartition par poule
- **Filtres dynamiques** : Par poule, gymnase, semaine
- **Vérification automatique** : Validation des contraintes respectées

## 🚀 Installation

```bash
# Créer un environnement virtuel
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt
```

## 📋 Démarrage rapide

### 1. Préparez votre configuration

Créez ou utilisez un fichier de configuration centrale Excel avec 7 feuilles :

**Feuilles manuelles** (à remplir) :
- `Equipes` : Liste des équipes
- `Gymnases` : Liste des gymnases avec leurs créneaux

**Feuilles auto-générées** (optionnelles) :
- `Indispos_Gymnases` : Indisponibilités des gymnases
- `Indispos_Equipes` : Indisponibilités des équipes spécifiques
- `Indispos_Institutions` : Indisponibilités s'appliquant à toute une institution
- `Preferences_Gymnases` : Préférences de gymnases par institution
- `Obligation_Presence` : Gymnases nécessitant la présence d'une institution

**Voir les guides** :
- [Guide de configuration](GUIDE_CONFIGURATION_CENTRALE.md) - Configuration complète
- [Guide d'intégration des contraintes](GUIDE_INTEGRATION_CONTRAINTES.md) - Comment les contraintes fonctionnent
- [Guide d'actualisation](GUIDE_ACTUALISATION.md) - Valider et corriger automatiquement

### 2. Créez votre fichier de configuration YAML

**💡 Configuration en cascade** : Toutes les valeurs par défaut sont dans `configs/default.yaml`.  
Vous ne spécifiez que ce que vous voulez **modifier**. Configuration ultra-simple !

**Exemple minimal** `exemple/config.yaml` :

```yaml
fichiers:
  donnees: "exemple/config_exemple.xlsx"
  sortie: "exemple/calendrier_exemple.xlsx"

planification:
  strategie: "cpsat"  # Le reste vient de default.yaml
```

**Exemple complet** avec surcharge de paramètres :

```yaml
fichiers:
  donnees: "exemple/config_exemple.xlsx"
  sortie: "exemple/calendrier_exemple.xlsx"

planification:
  nb_semaines: 26
  strategie: "greedy"

contraintes:
  penalite_apres_horaire_min: 40.0  # Surcharge la valeur par défaut (10.0)

# Voir configs/default.yaml pour tous les paramètres disponibles
```

### 3. Lancez la planification

```bash
python main.py exemple/config.yaml
```

### 4. Résultats

Le système génère :
- `calendrier_handball.xlsx` : Calendrier Excel avec 3 feuilles
  - `Calendrier` : Tous les matchs planifiés
  - `Non_Planifies` : Matchs non planifiés (si applicable)
  - `Statistiques` : Métriques et résumé
- `calendrier_handball.html` : Visualisation interactive

## 🎯 Outils d'Analyse des Pénalités (Nouveau !)

### 🎲 Simulateur de Pénalités (Pédagogique)

**Objectif** : Comprendre la formule de pénalité sans la complexité des données réelles

```bash
# Lancer le simulateur
streamlit run app_penalty_simulator.py
# Ou
./run_simulator.sh
```

**Fonctionnalités** :
- 📊 **Visualiser la courbe** de pénalité autour d'un horaire
- 🎯 **Simuler des matchs** avec différents horaires
- 📈 **Comparer les 3 scénarios** (APRÈS, AVANT 1, AVANT 2)
- 📚 **Documentation intégrée** de la formule

**Idéal pour** :
- 🎓 Découvrir comment fonctionne la formule
- ⚙️ Tester différentes configurations de paramètres
- 🔍 Comprendre l'impact de chaque paramètre
- 📐 Trouver les bonnes valeurs avant d'utiliser les vraies données

➡️ **Consultez le [guide du simulateur](GUIDE_SIMULATEUR_PENALITES.md)**

---

### 📊 Analyseur de Pénalités (Avancé)

**Objectif** : Ajuster les paramètres avec vos données réelles

```bash
# Lancer l'analyseur
streamlit run app_penalty_analyzer.py
# Ou
./run_analyzer.sh
```

**Fonctionnalités** :
- 🔍 **Trouver les meilleurs créneaux** pour chaque match réel
- � **Analyser la sensibilité** de chaque paramètre
- 📈 **Comparer les alternatives** (top 10 des créneaux)
- ⚙️ **Ajuster en temps réel** avec vos équipes et gymnases

**Idéal pour** :
- 🎯 Valider vos paramètres avec des cas concrets
- 📋 Identifier les matchs problématiques
- 🔧 Affiner la configuration pour votre situation
- ✅ Vérifier l'impact avant la planification complète

➡️ **Consultez le [guide de l'analyseur](GUIDE_ANALYSEUR_PENALITES.md)**

---

**💡 Workflow recommandé** :
1. **Simulateur** → Comprendre la formule et trouver de bons paramètres théoriques
2. **Analyseur** → Valider et affiner avec vos données réelles
3. **Planification** → Lancer la génération complète du calendrier

## 📊 Format de configuration centrale

### Feuille "Equipes" (OBLIGATOIRE)

| Equipe      | Poule    | Horaire_Prefere |
|-------------|----------|-----------------|
| LYON 1 (1)  | HBFA1PA  | 18:00           |
| INSA (2)    | HBMA2PA  | 14:00           |

**Format des noms** : `"Institution (numéro)"` (ex: `"LYON 1 (1)"`, `"ECL (1)"`)
- Le genre est extrait automatiquement du code de poule
- Affichage sans genre pour éviter doublons visuels
- Genre utilisé en interne pour différencier les équipes

### Feuille "Gymnases" (OBLIGATOIRE)

| Gymnase    | Adresse              | Capacite | Creneaux                    |
|------------|----------------------|----------|-----------------------------|
| SCIENCES C | Campus Doua          | 1        | 09:00, 12:00, 14:00, 18:00  |
| ECL        | 36 avenue Guy        | 1        | 14:00, 18:00                |

**Creneaux** : Liste séparée par des virgules

### Feuille "Indispos_Institutions" (AUTO-GÉNÉRÉE)

Permet de définir des indisponibilités qui s'appliquent à **toutes les équipes** d'une institution.

| Institution | Semaine | Horaire_Debut | Horaire_Fin | Remarques           |
|-------------|---------|---------------|-------------|---------------------|
| LYON 1      | 10      |               |             | Semaine intensive   |
| LYON 1      | 11      |               |             | Semaine intensive   |
| INSA        | 5       | 08:00         | 12:00       | Réunion matinale    |
| ENS         | 15      | 18:30         | 21:00       | Événement étudiant  |

**Colonnes** :
- `Institution` : Nom exact de l'institution (obligatoire)
- `Semaine` : Numéro de la semaine concernée (obligatoire)
- `Horaire_Debut` : Heure de début de l'indisponibilité (format HH:MM, optionnel)
- `Horaire_Fin` : Heure de fin de l'indisponibilité (format HH:MM, optionnel)
- `Remarques` : Informations complémentaires (optionnel)

**Notes importantes** :
- Si `Horaire_Debut` et `Horaire_Fin` ne sont pas renseignés → indisponibilité sur **toute la semaine**
- ⚠️ **Actuellement, seules les indisponibilités par semaine complète sont supportées** (les horaires spécifiques seront implémentés dans une version future)
- L'indisponibilité s'applique automatiquement à toutes les équipes de l'institution

### Feuille "Obligation_Presence" (AUTO-GÉNÉRÉE)

| Gymnase | Institution_Obligatoire | Raison                        |
|---------|-------------------------|-------------------------------|
| ECL     | ECL                     | Gymnase propriété de l'école  |
| EML     | EML                     | Gymnase propriété de l'école  |

**Garantit** : Chaque match dans ce gymnase inclut au moins une équipe de l'institution

## 🔧 Outils de gestion

### Actualiser une configuration

Valide et complète automatiquement un fichier de configuration :

```bash
python actualiser_config.py exemple/config_exemple.xlsx
```

**Actions automatiques** :
1. ✅ Valide la structure des feuilles manuelles
2. 🧹 Nettoie les marqueurs `[M]`/`[F]` des noms d'équipes
3. 🗑️ Supprime les lignes d'exemple
4. 📝 Extrait les références (équipes, gymnases, institutions)
5. ➕ Génère les feuilles manquantes
6. 🔍 Vérifie la cohérence des références
7. 📋 Met à jour les listes déroulantes de validation

## 📁 Structure du projet

```
PyCalendar/
├── core/                       # Modèles et configuration
│   ├── models.py              # Equipe, Gymnase, Match, Solution
│   ├── config.py              # Gestion configuration YAML
│   └── config_manager.py      # Gestion Excel central
├── data/                       # Chargement de données
│   ├── data_loader.py  # Charge config avec contraintes
│   ├── data_source.py      # Adapte pour le pipeline
│   └── validators.py          # Validation des données
├── constraints/                # Système de contraintes
│   ├── base.py                # Constraint base class
│   ├── team_constraints.py    # Contraintes équipes
│   ├── venue_constraints.py   # Contraintes gymnases + obligations
│   └── schedule_constraints.py # Contraintes planification
├── solvers/                    # Algorithmes
│   ├── greedy_solver.py       # Algorithme glouton (rapide)
│   └── cpsat_solver.py        # Programmation par contraintes (optimal)
├── orchestrator/               # Pipeline principal
│   └── pipeline.py            # Orchestration complète
├── exporters/                  # Export résultats
│   └── excel_exporter.py
├── visualization/              # Visualisation
│   ├── html_visualizer.py
│   └── statistics.py
├── configs/                    # Configurations YAML
│   └── default.yaml
├── exemple/                    # Fichiers d'exemple
│   └── config_exemple.xlsx    # Configuration centrale d'exemple
├── main.py                     # Point d'entrée principal
└── actualiser_config.py        # Outil de validation/correction
```

## 🎮 Utilisation avancée

### Personnaliser la planification

Modifiez le fichier de configuration YAML pour ajuster les paramètres :

```yaml
planification:
  nb_semaines: 20           # Nombre de semaines
  strategie: "cpsat"        # Algorithme: "greedy" (rapide) ou "cpsat" (optimal)

contraintes:
  penalite_apres_horaire_min: 10.0    # Pénalité si match après horaire préféré
  penalite_avant_horaire_min: 100.0   # Pénalité si match avant horaire (1 équipe)
  penalites_espacement_repos: [100.0, 50.0, 10.0]  # Pénalités par semaines de repos
  # ... voir configs/default.yaml pour tous les paramètres
```

**Résultat** :
- ✅ Vérification automatique des contraintes
- 📊 Statistiques détaillées
- ⚠️ Violations de contraintes (si présentes)

### Contraintes supportées

**Contraintes DURES** (toujours respectées) :
- ✅ Indisponibilités des équipes
- ✅ Indisponibilités institutionnelles (toutes équipes d'une institution)
- ✅ Indisponibilités des gymnases
- ✅ **Obligations de présence** (gymnase → institution)
- ✅ Capacité des gymnases
- ✅ Une équipe joue maximum 1 match par semaine

**Contraintes SOUPLES** (optimisées) :
- 📊 Préférences d'horaires
- 📊 Préférences de gymnases
- 📊 Espacement entre matchs (avec pénalités progressives)
- 📊 Équilibrage de la charge

## 🐛 Dépannage

### Erreur "Duplicate team"

Le genre fait partie de l'identité de l'équipe. `LYON 1 (1)` masculin ≠ `LYON 1 (1)` féminin.
Le genre est extrait du code de poule automatiquement.

### Planification incomplète

Si tous les matchs ne sont pas planifiés :
1. Vérifiez les indisponibilités (peut-être trop restrictives)
2. Augmentez le nombre de créneaux (plus de gymnases ou horaires)
3. Réduisez les contraintes DURES si approprié

### Configuration invalide

```bash
# Valider et corriger automatiquement
python actualiser_config.py exemple/config_exemple.xlsx
```

## 📚 Documentation complète

- **[GUIDE_CONFIGURATION_CENTRALE.md](GUIDE_CONFIGURATION_CENTRALE.md)** - Guide complet de configuration
- **[GUIDE_INTEGRATION_CONTRAINTES.md](GUIDE_INTEGRATION_CONTRAINTES.md)** - Comment les contraintes fonctionnent
- **[GUIDE_ACTUALISATION.md](GUIDE_ACTUALISATION.md)** - Utilisation de l'outil d'actualisation
- **[GUIDE_SIMULATEUR_PENALITES.md](GUIDE_SIMULATEUR_PENALITES.md)** - 🆕 Simulateur pédagogique pour comprendre la formule
- **[GUIDE_ANALYSEUR_PENALITES.md](GUIDE_ANALYSEUR_PENALITES.md)** - 🆕 Analyseur avancé avec données réelles
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Architecture technique du système

## 🆕 Fonctionnalités

- ✅ **Configuration centrale unifiée** : Un seul fichier Excel
- ✅ **Contraintes institutionnelles** : S'appliquent à toutes les équipes
- ✅ **Obligations de présence** : Garanties gymnase→institution
- ✅ **Actualisation automatique** : Validation et correction
- ✅ **Vérification des contraintes** : Rapport automatique après génération
- ✅ **Visualisation HTML interactive** : Calendriers avec 4 vues différentes
- ✅ **Multiples algorithmes** : Greedy (rapide) ou CP-SAT (optimal)

## 📄 Licence

Ce projet est développé pour la FFSU (Fédération Française du Sport Universitaire).

## 👥 Contribution

Pour ajouter de nouvelles contraintes ou fonctionnalités, consultez [GUIDE_INTEGRATION_CONTRAINTES.md](GUIDE_INTEGRATION_CONTRAINTES.md).

## 🎯 Exemples

Voir le dossier `data_hand/` pour un exemple complet de configuration handball avec :
- 46 équipes réparties en 10 poules
- 8 gymnases
- 4 obligations de présence
- 6 préférences de gymnases
- Configuration sur 26 semaines
