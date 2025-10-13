# PyCalendar V2 - Guide Complet des Prompts# README – Organisation des prompts PyCalendar V2



## Vue d'ensemble du projet## Vue d'ensemble



PyCalendar V2 est un système de planification sportive avec **double configuration** (YAML + Excel) et **architecture web moderne** (FastAPI + React).Ce dossier contient l'ensemble des prompts techniques pour l'implémentation complète de PyCalendar V2, une application web d'optimisation de calendriers sportifs.



**Architecture complète** :**Objectif global** : Transformer PyCalendar d'une application CLI/Excel en solution web full-stack avec API REST et interface interactive, tout en préservant l'intégralité du code existant.

- **Backend** : FastAPI + SQLAlchemy + SQLite + OR-Tools/CP-SAT

- **Frontend** : React 18 + TypeScript + Vite + FullCalendar + React Query**Stack technique** :

- **Configuration** : YAML (hyperparamètres) + Excel (données métier)- **Backend** : FastAPI, SQLAlchemy, SQLite

- **Solveurs** : Optimal (CP-SAT), Heuristique, Hybride- **Frontend** : React, TypeScript, Vite, FullCalendar, React Query

- **Solveurs** : CP-SAT (Google OR-Tools), Greedy

**Workflow utilisateur** :

1. **Import** : Charger config YAML + Excel → créer projet en DB## Architecture des prompts

2. **Visualiser** : Voir calendrier dans interface React

3. **Fixer** : Marquer matchs importants comme "fixes" (immobiles)Les prompts sont organisés en 3 phases correspondant aux étapes d'implémentation :

4. **Optimiser** : Lancer solveur pour planifier matchs restants

5. **Exporter** : Télécharger calendrier final en Excel```

prompts/

---├── README.txt                          # Ce fichier

├── phase1/                             # Backend (8 prompts)

## Double configuration (RAPPEL CRITIQUE)│   ├── 01_modele_match_extension.txt

│   ├── 02_contrainte_semaine_min.txt

**⚠️ PRINCIPE FONDAMENTAL - À RÉPÉTER DANS CHAQUE PROMPT ⚠️**│   ├── 03_creation_base_donnees.txt

│   ├── 04_schemas_pydantic_api.txt

PyCalendar V2 utilise **2 sources de configuration complémentaires** :│   ├── 05_routes_api_backend.txt

│   ├── 06_service_synchronisation_excel.txt

### 1. Configuration YAML (Hyperparamètres)│   ├── 07_scripts_cli_init_import.txt

│   └── 08_tests_unitaires_backend.txt

**📁 Fichiers** : `configs/default.yaml`, `configs/config_volley.yaml`├── phase2/                             # Frontend (6 prompts)

│   ├── 01_initialisation_react.txt

**Contenu** :│   ├── 02_typescript_types.txt

- **Sport et semaines** : sport, nb_semaines, semaine_minimum, date_debut│   ├── 03_client_api_axios.txt

- **Fichiers Excel** : `fichiers.donnees` (chemin vers Excel)│   ├── 04_hooks_react_query.txt

- **Stratégie solveur** : `solver.strategie` (optimal/heuristique/hybride), temps_max_secondes│   ├── 05_composant_calendrier_fullcalendar.txt

- **Poids contraintes** : respect_repos, equilibre_domicile_exterieur, respect_indisponibilites, etc.│   └── 06_page_principale_integration.txt

└── phase3/                             # Solver (4 prompts)

**Exemple** :    ├── 01_modification_solveurs_matchs_fixes.txt

```yaml    ├── 02_service_solveur_orchestration.txt

sport: "Volleyball"    ├── 03_endpoint_api_resolution.txt

nb_semaines: 14    └── 04_integration_frontend_resolution.txt

semaine_minimum: 3  # Première semaine modifiable (1-2 sont fixes)```

date_debut: "2025-10-16"

## Structure de chaque prompt

fichiers:

  donnees: "data_volley/POULES_VB_OPTIMISEES.xlsx"Chaque prompt est **auto-suffisant** et contient :



solver:1. **Contexte global** : Description du projet PyCalendar V2

  strategie: "hybride"  # optimal, heuristique, ou hybride2. **Contexte technique** : Détails spécifiques de la tâche

  temps_max_secondes: 3003. **Résumé du travail précédent** : Ce qui a été fait avant

4. **Objectifs** : Buts précis de la tâche

contraintes:5. **Détails techniques** : 

  poids:   - Fichiers à créer/modifier (chemins exacts)

    respect_repos: 100   - Architecture et organisation

    equilibre_domicile_exterieur: 80   - Algorithmes et instructions précises

    respect_indisponibilites: 100   - Consignes sur qualité, extensibilité, maintenabilité

    # ...6. **Impact et liens** : Relations avec autres modules

```7. **À faire/vérifier** : Checklist de validation

8. **Questions** : Invitation à clarifier si besoin

### 2. Configuration Excel (Données métier)9. **Documentation** : Consignes sur la concision



**📁 Fichier** : `data_volley/POULES_VB_OPTIMISEES.xlsx` (référencé dans YAML)## Ordre d'exécution recommandé



**7+ feuilles obligatoires** :### Phase 1 : Backend Foundation (8 prompts, ~2 semaines)

- **Equipes** : Institution, Numéro équipe, Niveau, Catégorie, Poule, Gymnase préféré

- **Gymnases** : Nom, Capacité, Adresse**Objectif** : Mettre en place la couche persistance (SQLAlchemy), l'API REST (FastAPI), et le service de synchronisation Excel→DB.

- **Indispos_Gymnases** : Date, Gymnase (colonnes obligatoires)

- **Indispos_Equipes** : Date, Institution, Numéro équipe1. **01_modele_match_extension.txt**

- **Indispos_Institutions** : Date, Institution (contraintes pour toute l'institution)   - Enrichir le modèle Match (est_fixe, statut, scores)

- **Preferences_Gymnases** : Institution, Gymnase (préférences institution)   - Fichier : `core/models.py`

- **Obligation_Presence** : Institution, Gymnase, Semaine (obligation utiliser son gymnase)   - Validation : CLI fonctionne toujours, nouveaux champs ont valeurs par défaut



**Validation Excel** : `actualiser_config.py`2. **02_contrainte_semaine_min.txt**

- Détecte colonnes manquantes/mal nommées   - Ajouter paramètre semaine_min à la configuration

- Vérifie types de données   - Fichier : `core/config.py`

- Reporte erreurs avec numéros de ligne   - Validation : YAML sans champ utilise défaut, avec champ charge correctement



### 3. Stockage en base de données3. **03_creation_base_donnees.txt**

   - Créer engine SQLAlchemy, session factory, 4 modèles (Project, Team, Venue, Match)

**Modèle Project** :   - Fichiers : `backend/database/engine.py`, `backend/database/models.py`

- `config_yaml_path` : Chemin vers fichier YAML (ex: "configs/config_volley.yaml")   - Validation : Tables créées, foreign keys fonctionnent, cascade delete OK

- `config_excel_path` : Chemin vers fichier Excel (ex: "data_volley/POULES_VB_OPTIMISEES.xlsx")

- `config_yaml_data` : Contenu YAML complet en JSON (permet reconstruction Config sans fichier)4. **04_schemas_pydantic_api.txt**

- `config_excel_data` : Métadonnées Excel en JSON (nb_equipes, nb_gymnases, feuilles_presentes)   - Définir schémas Pydantic pour validation/sérialisation API

   - Fichiers : `backend/schemas/match.py`, `project.py`, `team.py`, `venue.py`

**❌ CE QUI N'EXISTE PAS** :   - Validation : Conversion ORM → Pydantic fonctionne

- PAS de valeurs par défaut dans les fichiers .py (config.py, models.py, etc.)

- PAS de constantes hardcodées dans le code5. **05_routes_api_backend.txt**

- TOUS les défaults sont dans `configs/default.yaml`   - Créer application FastAPI, routes CRUD + move/fix/unfix

   - Fichiers : `backend/api/main.py`, `backend/api/routes/*.py`

---   - Validation : API démarre, Swagger /docs accessible, endpoints testés



## Organisation des prompts6. **06_service_synchronisation_excel.txt**

   - Créer service d'import Excel → DB

Les prompts sont organisés en **3 phases** correspondant aux couches de l'architecture :   - Fichier : `backend/services/sync_service.py`

   - Validation : Projet importé, équipes/gymnases/matchs créés en DB

### Phase 1 : Backend (API FastAPI)

**8 prompts** dans `prompts/phase1/` :7. **07_scripts_cli_init_import.txt**

   - Créer scripts CLI pour init DB et import Excel

1. **01_modele_match_extension.txt** (6,757 bytes)   - Fichiers : `scripts/init_db.py`, `scripts/import_excel.py`

   - Extension modèle Match avec `est_fixe`, `semaine_min`   - Validation : DB créée, import affiche stats

   - Validation : semaine >= semaine_min (YAML)

   - Tests unitaires8. **08_tests_unitaires_backend.txt**

   - Créer tests unitaires (modèles, API)

2. **02_contrainte_semaine_min.txt** (8,152 bytes)   - Fichiers : `tests/conftest.py`, `tests/unit/test_models.py`, `test_api_matches.py`

   - Vérification que semaine_minimum existe déjà (config.py)   - Validation : Tests passent, couverture >80%

   - Tâche de validation uniquement

**Validation globale Phase 1** :

3. **03_creation_base_donnees.txt** (15,384 bytes)- ✅ CLI existant fonctionne toujours

   - Modèles SQLAlchemy : Project, Team, Venue, Match- ✅ API démarrée sur :8000

   - Ajout config_yaml_data, config_excel_data à Project- ✅ Import Excel → DB opérationnel

   - Scripts init_db.py- ✅ Tests unitaires passent



4. **04_schemas_pydantic_api.txt** (12,990 bytes)### Phase 2 : Frontend React (6 prompts, ~2 semaines)

   - Schémas Pydantic : ProjectCreate, ProjectResponse, MatchResponse, etc.

   - Ajout ConfigYamlData, ConfigExcelData**Objectif** : Créer l'interface web React avec affichage calendrier, édition drag & drop, et communication API.

   - Validation config lors création projet

1. **01_initialisation_react.txt**

5. **05_routes_api_backend.txt** (18,154 bytes)   - Initialiser projet React avec Vite, installer dépendances, configurer proxy

   - 8 endpoints matchs : list, get, create, update, move, fix, unfix, delete   - Fichiers : `frontend/vite.config.ts`, `package.json`

   - Endpoints projects : CRUD + stats   - Validation : Frontend démarre sur :5173, hot reload fonctionne

   - Gestion erreurs (404, 400, 500)

2. **02_typescript_types.txt**

6. **06_service_synchronisation_excel.txt** (14,057 bytes)   - Définir interfaces TypeScript pour entités (Match, Project, Team, Venue)

   - SyncService pour synchroniser Excel → DB   - Fichiers : `frontend/src/types/*.ts`

   - Utilise actualiser_config.py pour validation   - Validation : Types correspondent aux schémas Pydantic, autocomplétion IDE

   - Créer/update équipes, gymnases, matchs

3. **03_client_api_axios.txt**

7. **07_scripts_cli_init_import.txt**   - Créer client Axios, endpoints pour toutes les entités

   - init_db.py : Créer tables SQLite   - Fichiers : `frontend/src/api/client.ts`, `frontend/src/api/endpoints/*.ts`

   - import_excel.py : Importer projet depuis YAML + Excel   - Validation : Appels API fonctionnent, proxy Vite opérationnel

   - Option --no-validate pour skip validation

4. **04_hooks_react_query.txt**

8. **08_tests_unitaires_backend.txt**   - Créer hooks React Query pour queries et mutations

   - Fixtures pytest (db, project, matches)   - Fichiers : `frontend/src/hooks/useMatches.ts`, `useProjects.ts`, etc.

   - Tests models, services, API routes   - Validation : Hooks récupèrent données, mutations invalident cache

   - Tests config_yaml_data, config_excel_data

5. **05_composant_calendrier_fullcalendar.txt**

### Phase 2 : Frontend (React + TypeScript)   - Créer composant Calendar avec drag & drop, coloration

**6 prompts** dans `prompts/phase2/` :   - Fichier : `frontend/src/components/calendar/Calendar.tsx`

   - Validation : Calendrier affiche matchs, drag & drop fonctionne, couleurs OK

1. **01_initialisation_react.txt**

   - Vite + React + TypeScript setup6. **06_page_principale_integration.txt**

   - tsconfig.json avec path aliases (@components, @hooks, etc.)   - Créer CalendarPage, configurer App.tsx avec Router et QueryClient

   - vite.config.ts avec proxy /api → http://localhost:8000   - Fichiers : `frontend/src/pages/CalendarPage.tsx`, `frontend/src/App.tsx`

   - React Query config (staleTime: 5min)   - Validation : Interface complète fonctionnelle, états gérés

   - Routing (/, /calendar, /projects, /stats)

**Validation globale Phase 2** :

2. **02_typescript_types.txt**- ✅ Frontend accessible sur :5173

   - ConfigYamlData interface (sport, semaines, contraintes, solver, fichiers)- ✅ Calendrier affiche matchs

   - ConfigExcelData interface (nb_equipes, nb_gymnases, feuilles_presentes)- ✅ Drag & drop opérationnel

   - Project, Team, Venue, Match interfaces- ✅ Matchs fixes non déplaçables

   - MatchExtended avec est_modifiable, titre, couleur- ✅ Build TypeScript sans erreur

   - Helpers : isMatchModifiable(), getPouleColor()

### Phase 3 : Intégration Solver (4 prompts, ~2 semaines)

3. **03_client_api_axios.txt**

   - Axios instance avec interceptors**Objectif** : Permettre l'exécution des solvers depuis l'interface web avec prise en compte des matchs fixes et semaine minimum.

   - projectsApi : CRUD + stats

   - teamsApi, venuesApi : CRUD avec filtres1. **01_modification_solveurs_matchs_fixes.txt**

   - matchesApi : CRUD + move/fix/unfix   - Modifier solvers CP-SAT et Greedy pour filtrer matchs fixes

   - Error helpers : getErrorMessage(), isNotFoundError()   - Fichiers : `solvers/cpsat_solver.py`, `solvers/greedy_solver.py`

   - Validation : Matchs fixes inchangés, autres planifiés, pas de conflits

4. **04_hooks_react_query.txt**

   - useProjects(), useProject(id), useProjectStats(id)2. **02_service_solveur_orchestration.txt**

   - useMatches(projectId), useMatch(id)   - Créer service orchestrant DB → Core → Solver → DB

   - useMoveMatch(), useFixMatch(), useUnfixMatch()   - Fichier : `backend/services/solver_service.py`

   - Query keys hiérarchiques : ['projects', 'list'], ['matches', 'detail', id]   - Validation : Service résout projet, sauvegarde solution, gère erreurs

   - Invalidation cache automatique après mutations

3. **03_endpoint_api_resolution.txt**

5. **05_composant_calendrier_fullcalendar.txt**   - Créer endpoint POST pour lancer résolution

   - Calendar.tsx avec FullCalendar (dayGridPlugin + interactionPlugin)   - Fichier : `backend/api/routes/solver.py`

   - Drag & drop avec useMoveMatch() mutation   - Validation : Endpoint fonctionne, stratégies validées, erreurs gérées

   - EventDetailsModal avec boutons fix/unfix/delete

   - Badge "Fixé" sur matchs fixes4. **04_integration_frontend_resolution.txt**

   - renderEventContent() custom rendering   - Créer bouton résolution dans interface, hook React Query

   - Conversion semaine <-> date   - Fichiers : `frontend/src/api/endpoints/solver.ts`, `frontend/src/hooks/useSolver.ts`

   - Validation : Bouton lance résolution, calendrier rafraîchi, feedback utilisateur

6. **06_page_principale_integration.txt**

   - App.tsx avec ProjectSelector + ProjectStats + Calendar**Validation globale Phase 3** :

   - ProjectSelector (Listbox) montrant config_yaml_path, config_excel_path- ✅ Bouton résolution visible et fonctionnel

   - ProjectStats avec 4 cards (équipes, gymnases, matchs planifiés, fixes)- ✅ Matchs fixes respectés

   - Header.tsx avec branding PyCalendar V2- ✅ Contrainte semaine_min appliquée

   - ErrorBoundary pour React Query errors- ✅ Stratégies CP-SAT et Greedy opérationnelles

- ✅ Calendrier rafraîchi après résolution

### Phase 3 : Solveur (Optimisation)

**4 prompts** dans `prompts/phase3/` :## Principes directeurs



1. **01_modification_solveurs_matchs_fixes.txt** (17,540 bytes)### Qualité du code

   - **Filtrage matchs** : `matchs_fixes = [m for m if m.est_fixe or (m.semaine and m.semaine < semaine_minimum)]`- **Organisation** : Code modulaire, bien structuré, facilement extensible

   - **Modifications solvers/optimal.py** :- **Maintenabilité** : Nommage clair, commentaires si besoin, pas de code dupliqué

     - Séparer matchs_fixes et matchs_modifiables- **Testabilité** : Fonctions pures, injection de dépendances, fixtures pytest

     - Créer variables CP-SAT UNIQUEMENT pour matchs_modifiables- **Extensibilité** : Prévoir l'ajout de nouvelles fonctionnalités sans refactoring majeur

     - Range variables : `range(semaine_minimum, nb_semaines + 1)` au lieu de `range(1, nb_semaines + 1)`

     - Contraintes pour éviter conflits avec matchs fixes (équipes/gymnases)### Documentation

     - Réintégrer matchs fixes dans solution finale sans modification- **Concise** : Pas de blabla inutile, documentation minimale mais utile

   - **Modifications solvers/heuristique.py** : Même principe de filtrage- **Précise** : Termes techniques exacts, instructions claires

   - **Modifications constraints/** : Adapter pour travailler avec matchs filtrés- **Pratique** : Exemples de commandes, checklist de validation

   - **Tests** : test_respect_matchs_fixes(), test_eviter_conflits_equipes()

### Interaction

2. **02_service_solveur_orchestration.txt** (16,092 bytes)- **Questions** : Chaque prompt invite à poser des questions si points obscurs

   - **SolverService class** :- **Validation** : Checklist précise pour vérifier le bon fonctionnement

     - `solve_project(project_id)` : Charge DB → Reconstruit Config → Exécute solveur → Valide → Persiste- **Itération** : Tests recommandés à chaque étape pour détecter problèmes tôt

     - `_build_config_from_project(project)` : Reconstruit Config depuis config_yaml_data (JSON)

     - `_execute_solver(strategie, ...)` : Switch optimal/heuristique/hybride## Commandes utiles

     - `_update_matches_from_solution(solution)` : Persiste solution, skip matchs fixes

   - **Stratégie hybride** : Essaie optimal avec timeout, fallback heuristique si échec### Backend

   - **SolutionValidator class** :```bash

     - `validate()` : Retourne (bool, list[str]) avec erreurs# Initialiser DB

     - Vérifie : matchs fixes inchangés, semaine >= semaine_minimum, pas de conflits équipes/gymnasespython scripts/init_db.py

   - **Gestion erreurs** :

     - SolverError exception pour erreurs métier# Importer projet depuis Excel

     - Validations : nb_matchs_modifiables > 0, nb_equipes >= 2python scripts/import_excel.py configs/config_volley.yaml "Volley 2025"

     - Timeout : signal.alarm() (Linux/Mac) - alternative Windows nécessaire

# Démarrer API

3. **03_endpoint_api_resolution.txt** (22,134 bytes)uvicorn backend.api.main:app --reload

   - **Schémas Pydantic** :

     - SolveRequest : strategie, temps_max_secondes (override optionnel)# Tests

     - SolveResponse : résumé (strategie, nb_matchs_planifies, temps_execution, etc.)pytest tests/ -v

     - SolveStatus : statut async (pending/running/completed/failed)pytest tests/ --cov=backend --cov-report=term-missing

   - **Endpoints** :```

     - POST /projects/{id}/solve : Résolution synchrone

     - GET /projects/{id}/solve/status : Statut async (optionnel)### Frontend

     - DELETE /projects/{id}/solve : Annuler résolution (optionnel)```bash

   - **Résolution async** : BackgroundTasks ou Celery# Installer dépendances

   - **Documentation OpenAPI** : Docstrings complètes avec exemples curlcd frontend

npm install

4. **04_integration_frontend_resolution.txt** (22,456 bytes)

   - **useSolve hook** : Mutation POST /solve avec invalidation cache# Démarrer dev server

   - **SolveButton component** :npm run dev

     - Bouton "Optimiser le calendrier"

     - Désactivé si aucun match modifiable (nbMatchsModifiables = total - fixes)# Build production

     - Spinner pendant résolutionnpm run build

     - Affichage résultat (stratégie, temps, matchs planifiés)

   - **SolveConfigModal (optionnel)** : Override stratégie/temps_max# Preview build

   - **SolveProgress (optionnel)** : Polling statut + barre progressionnpm run preview

   - **Intégration App.tsx** : SolveButton entre ProjectStats et Calendar```

   - **Toasts** : react-hot-toast pour notifications succès/erreur

### Full stack

---```bash

# Terminal 1 : Backend

## Concepts clés à respecteruvicorn backend.api.main:app --reload



### 1. Matchs fixes (est_fixe)# Terminal 2 : Frontend

cd frontend && npm run dev

**Définition** :

Un match est considéré "fixe" (immobile) si :# Accès : http://localhost:5173

- `match.est_fixe == True` (fixé manuellement via interface)```

- OU `match.semaine < semaine_minimum` (YAML config)

## Ressources

**Conséquences** :

- ❌ **Non modifiable** par solveur (semaine, gymnase gelés)### Documentation technique

- ✅ **Préservé** dans solution finale- `docs/IMPLEMENTATION_TECHNIQUE.md` : Guide technique détaillé complet

- ✅ **Pris en compte** dans contraintes (éviter conflits équipes/gymnases)- Chaque prompt : instructions précises et auto-suffisantes



**Implémentation solveur** :### Architecture projet

```python```

# Filtrer matchsPyCalendar/

matchs_fixes = [m for m in matchs if m.est_fixe or (m.semaine and m.semaine < semaine_minimum)]├── backend/              # API REST, DB, services

matchs_modifiables = [m for m in matchs if m not in matchs_fixes]├── frontend/             # React app

├── core/                 # Modèles métier (préservé)

# Créer variables CP-SAT seulement pour matchs modifiables├── solvers/              # Algorithmes optimisation (préservé)

for match in matchs_modifiables:├── constraints/          # Contraintes planification (préservé)

    semaine_var = model.NewIntVar(semaine_minimum, nb_semaines, f"semaine_{match.id}")├── generators/           # Générateurs matchs (préservé)

    # ...├── scripts/              # CLI init/import

├── tests/                # Tests unitaires

# Contraintes : éviter conflits avec matchs fixes└── configs/              # Fichiers configuration YAML

for match_fixe in matchs_fixes:```

    for match_mod in matchs_modifiables:

        if match_fixe.equipe_domicile_id == match_mod.equipe_domicile_id:### Contraintes strictes

            # Contrainte : si même semaine → conflit1. **Préservation totale** : Aucune modification destructive des modules existants

            # ...2. **Compatibilité CLI** : Le script `main.py` doit continuer à fonctionner

3. **Import Excel** : Les fichiers Excel existants doivent pouvoir être importés

# Solution finale : combiner matchs modifiables + matchs fixes4. **Matchs fixes** : Support des matchs verrouillés non-replanifiables

solution = matchs_modifiables_optimises + matchs_fixes5. **Semaine minimum** : Contrainte de non-planification avant une semaine donnée

```

## Contact et support

**Interface frontend** :

- Badge "Fixé" sur matchs fixesPour toute question ou clarification :

- Désactivé drag & drop pour matchs fixes- Se référer au prompt concerné pour détails techniques

- Bouton "Fixer" dans EventDetailsModal- Consulter `docs/IMPLEMENTATION_TECHNIQUE.md` pour vue d'ensemble

- Compteur matchs fixes dans ProjectStats- Poser des questions directement (chaque prompt l'encourage)



### 2. semaine_minimum (YAML) vs semaine_min (API/DB)**Bonne implémentation !** 🚀


**⚠️ ATTENTION NOMENCLATURE** :

- **`semaine_minimum`** (YAML config) : Première semaine modifiable par solveur (ex: 3)
  - Config YAML : `semaine_minimum: 3`
  - Config Python : `config.semaine_minimum`
  - Usage : `range(semaine_minimum, nb_semaines + 1)` pour variables CP-SAT

- **`semaine_min`** (API/DB Match model) : Semaine minimum d'un match spécifique (validation)
  - Match model : `semaine_min: int`
  - Validation : `assert match.semaine >= match.semaine_min`
  - Usage : Empêcher déplacement match avant semaine_min

**Ne PAS confondre** :
- `config.semaine_minimum` = première semaine modifiable globalement (YAML)
- `match.semaine_min` = semaine minimum pour CE match (DB)

### 3. actualiser_config.py (Validation Excel)

**Rôle critique** :
- **Valide structure Excel** AVANT import en DB
- **Détecte erreurs** : colonnes manquantes, types incorrects, valeurs invalides
- **Reporte ligne exacte** de l'erreur dans Excel

**Workflow** :
1. Utilisateur prépare Excel (7+ feuilles)
2. Lance `python actualiser_config.py configs/config_volley.yaml`
3. Script valide Excel et affiche erreurs OU "✅ Validation réussie"
4. Si OK, utilisateur lance import : `python scripts/import_excel.py configs/config_volley.yaml`

**Validation** :
```python
# Exemple validation feuille Gymnases
required_columns = ['Nom', 'Capacité', 'Adresse']
if not all(col in df.columns for col in required_columns):
    raise ValueError(f"Feuille Gymnases : colonnes manquantes. Attendues : {required_columns}")

# Validation types
if not pd.api.types.is_numeric_dtype(df['Capacité']):
    raise ValueError(f"Feuille Gymnases : colonne Capacité doit être numérique")
```

**Option --no-validate** :
- Skip validation pour imports répétés (Excel déjà validé)
- Usage : `python scripts/import_excel.py config.yaml --no-validate`

### 4. Reconstruction Config depuis JSON

**Problème** :
- Projet stocké en DB avec config_yaml_data (JSON)
- Solveur a besoin d'objet Config complet
- Fichier YAML peut avoir été déplacé/supprimé

**Solution** : Reconstruction depuis JSON

```python
def _build_config_from_project(self, project: Project) -> Config:
    """
    Reconstruit Config depuis project.config_yaml_data (JSON).
    
    Permet d'exécuter solveur même si fichier YAML original supprimé.
    """
    yaml_data = project.config_yaml_data  # dict depuis JSON
    
    # Créer Config manuellement
    config = Config(
        sport=yaml_data['sport'],
        nb_semaines=yaml_data['nb_semaines'],
        semaine_minimum=yaml_data.get('semaine_minimum', 1),
        date_debut=datetime.fromisoformat(yaml_data['date_debut']),
        fichiers=Fichiers(
            donnees=project.config_excel_path  # ou yaml_data['fichiers']['donnees']
        ),
        solver=SolverConfig(
            strategie=yaml_data['solver']['strategie'],
            temps_max_secondes=yaml_data['solver']['temps_max_secondes']
        ),
        contraintes=ContraintesConfig(
            poids=Poids(**yaml_data['contraintes']['poids'])
        )
    )
    
    return config
```

**Pourquoi** :
- ✅ Indépendance fichiers : Projet autonome en DB
- ✅ Portabilité : Déplacer DB sans fichiers config
- ✅ Reproductibilité : Config exact utilisé lors import

### 5. Stratégies de résolution

**3 stratégies disponibles** (config YAML : `solver.strategie`) :

1. **"optimal"** : CP-SAT (OR-Tools)
   - ✅ Solution optimale garantie (si existe)
   - ❌ Peut être lent (plusieurs minutes)
   - Usage : Compétitions officielles, calendriers critiques

2. **"heuristique"** : Algorithme glouton
   - ✅ Rapide (quelques secondes)
   - ❌ Non garantie optimale
   - Usage : Tests, prototypes, calendriers simples

3. **"hybride"** : Optimal avec fallback heuristique
   - ✅ Meilleur des 2 mondes
   - Workflow : Essaie optimal → Si échec/timeout → Heuristique
   - Usage : **RECOMMANDÉ** pour production

**Implémentation** :
```python
def _execute_solver(self, strategie: str, config: Config, ...) -> Solution:
    if strategie == "optimal":
        return optimal_solver.solve(config, matchs, equipes, gymnases)
    
    elif strategie == "heuristique":
        return heuristique_solver.solve(config, matchs, equipes, gymnases)
    
    elif strategie == "hybride":
        try:
            # Essayer optimal avec timeout
            return optimal_solver.solve(config, matchs, equipes, gymnases)
        except (TimeoutError, SolverError):
            # Fallback heuristique
            return heuristique_solver.solve(config, matchs, equipes, gymnases)
```

---

## Patterns de code récurrents

### Pattern 1 : Chargement Config depuis YAML

```python
from core.config import load_config

# Charger config YAML
config = load_config("configs/config_volley.yaml")

# Accès
print(config.sport)  # "Volleyball"
print(config.semaine_minimum)  # 3
print(config.solver.strategie)  # "hybride"
print(config.fichiers.donnees)  # "data_volley/POULES_VB_OPTIMISEES.xlsx"
```

### Pattern 2 : Import Excel avec actualiser_config.py

```python
import subprocess

# Validation Excel
result = subprocess.run(
    ["python", "actualiser_config.py", yaml_path],
    capture_output=True,
    text=True
)

if result.returncode != 0:
    raise ValueError(f"Validation Excel échouée : {result.stderr}")

# Si OK, importer
# ...
```

### Pattern 3 : Filtrage matchs fixes

```python
def filtrer_matchs(matchs: list[Match], semaine_minimum: int):
    """
    Sépare matchs fixes et modifiables.
    
    Matchs fixes :
    - est_fixe=True (fixé manuellement)
    - semaine < semaine_minimum (période non modifiable)
    """
    matchs_fixes = [
        m for m in matchs
        if m.est_fixe or (m.semaine and m.semaine < semaine_minimum)
    ]
    
    matchs_modifiables = [
        m for m in matchs
        if m not in matchs_fixes
    ]
    
    return matchs_fixes, matchs_modifiables
```

### Pattern 4 : Invalidation cache React Query

```typescript
// Après mutation (create/update/delete/move/fix)
onSuccess: (data, variables) => {
  // Invalider liste matchs
  queryClient.invalidateQueries({
    queryKey: ['matches', 'list', variables.projectId]
  });
  
  // Invalider stats projet
  queryClient.invalidateQueries({
    queryKey: ['projects', 'stats', variables.projectId]
  });
  
  // Invalider détail match si update
  if (variables.matchId) {
    queryClient.invalidateQueries({
      queryKey: ['matches', 'detail', variables.matchId]
    });
  }
}
```

### Pattern 5 : Conversion semaine <-> date (Frontend)

```typescript
/**
 * Convertit numéro semaine en date (lundi de la semaine).
 */
function getSemaineDate(semaine: number, dateDebut: string): string {
  const debut = new Date(dateDebut);
  debut.setDate(debut.getDate() + (semaine - 1) * 7);
  return debut.toISOString().split('T')[0];
}

/**
 * Convertit date en numéro de semaine.
 */
function getWeekNumber(date: string, dateDebut: string): number {
  const debut = new Date(dateDebut);
  const current = new Date(date);
  const diffMs = current.getTime() - debut.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  return Math.floor(diffDays / 7) + 1;
}
```

---

## Checklist complète de développement

### Backend (Phase 1)

- ✅ Modèle Match avec `est_fixe`, `semaine_min`
- ✅ Validation semaine >= semaine_min
- ✅ Modèles DB : Project avec config_yaml_data, config_excel_data
- ✅ Schémas Pydantic : ConfigYamlData, ConfigExcelData
- ✅ Endpoints API : 8 matchs + CRUD projects + stats
- ✅ SyncService avec actualiser_config.py
- ✅ Scripts CLI : init_db.py, import_excel.py
- ✅ Tests unitaires : models, services, routes

### Frontend (Phase 2)

- ✅ Init Vite + React + TypeScript
- ✅ tsconfig avec path aliases
- ✅ vite.config avec proxy /api
- ✅ Interfaces TypeScript : ConfigYamlData, Project, Match, etc.
- ✅ Axios client avec interceptors
- ✅ Hooks React Query : useProjects, useMatches, useMoveMatch, etc.
- ✅ Calendar FullCalendar avec drag & drop
- ✅ EventDetailsModal avec fix/unfix
- ✅ ProjectSelector montrant config paths
- ✅ ProjectStats avec 4 cards

### Solveur (Phase 3)

- ✅ Modifications solvers/optimal.py : filtrage matchs, variables, contraintes
- ✅ Modifications solvers/heuristique.py : filtrage matchs
- ✅ Modifications constraints/ : adapter pour matchs filtrés
- ✅ SolverService : solve_project, build_config, execute_solver
- ✅ SolutionValidator : validate matchs fixes, semaine_min, conflits
- ✅ Endpoint POST /projects/{id}/solve
- ✅ Schémas SolveRequest, SolveResponse, SolveStatus
- ✅ useSolve hook + SolveButton component
- ✅ Intégration App.tsx avec toasts

---

## Questions fréquentes (FAQ)

### Q1 : Pourquoi double configuration (YAML + Excel) ?

**Réponse** :
- **YAML** : Hyperparamètres techniques (stratégie, poids contraintes, temps_max) → Pour développeurs/admin
- **Excel** : Données métier (équipes, gymnases, indispos) → Pour utilisateurs finaux (non techniques)
- **Séparation responsabilités** : Admin configure algorithme, utilisateurs gèrent données

### Q2 : Pourquoi actualiser_config.py séparé ?

**Réponse** :
- **Validation pré-import** : Détecte erreurs AVANT import DB (évite corruption)
- **Feedback immédiat** : Utilisateur corrige Excel avant import
- **Réutilisable** : Peut être appelé en CLI, API, GUI

### Q3 : Pourquoi stocker config_yaml_data en JSON ?

**Réponse** :
- **Autonomie** : Projet indépendant des fichiers YAML/Excel (peuvent être déplacés)
- **Reproductibilité** : Config exact utilisé lors import préservé
- **Portabilité** : Partager DB sans fichiers config

### Q4 : Différence semaine_minimum (YAML) vs semaine_min (Match) ?

**Réponse** :
- **`semaine_minimum` (YAML)** : Première semaine modifiable GLOBALEMENT (ex: semaines 1-2 fixes pour TOUS matchs)
- **`semaine_min` (Match)** : Semaine minimum pour CE match SPÉCIFIQUEMENT (validation DB)

### Q5 : Pourquoi stratégie "hybride" recommandée ?

**Réponse** :
- **Robustesse** : Optimal avec fallback heuristique si échec/timeout
- **Performance** : Essaie solution optimale, ne bloque pas si impossible
- **Production ready** : Garantie d'avoir TOUJOURS une solution (même sous-optimale)

### Q6 : Comment gérer timeout solveur cross-platform ?

**Réponse** :
- **Linux/Mac** : `signal.alarm()` fonctionne
- **Windows** : Utiliser `threading.Timer` ou `multiprocessing` avec timeout
- **Alternative** : Résolution asynchrone avec Celery (timeout géré par worker)

### Q7 : Faut-il permettre override config dans API ?

**Réponse** :
- **Si override** : SolveRequest avec strategie/temps_max optionnel → Flexibilité ponctuelle
- **Si pas override** : Forcer config YAML → Plus simple, plus propre
- **Recommandation** : Permettre override pour tests, forcer YAML en production

### Q8 : Résolution synchrone ou asynchrone ?

**Réponse** :
- **Synchrone** : Ok si résolution < 30s (acceptable pour utilisateur)
- **Asynchrone** : Obligatoire si résolution > 1min (BackgroundTasks ou Celery)
- **UX** : Async avec polling/websockets pour progression temps réel

---

## Ordre de lecture recommandé

**Pour développeur backend** :
1. Phase 1 → 03_creation_base_donnees.txt (models)
2. Phase 1 → 04_schemas_pydantic_api.txt (schemas)
3. Phase 1 → 05_routes_api_backend.txt (routes)
4. Phase 3 → 01_modification_solveurs_matchs_fixes.txt (solveurs)
5. Phase 3 → 02_service_solveur_orchestration.txt (orchestration)

**Pour développeur frontend** :
1. Phase 2 → 01_initialisation_react.txt (setup)
2. Phase 2 → 02_typescript_types.txt (types)
3. Phase 2 → 03_client_api_axios.txt (API client)
4. Phase 2 → 04_hooks_react_query.txt (hooks)
5. Phase 2 → 05_composant_calendrier_fullcalendar.txt (calendrier)
6. Phase 3 → 04_integration_frontend_resolution.txt (optimisation)

**Pour architecte/chef de projet** :
1. README.txt (ce fichier)
2. Phase 1 → 03_creation_base_donnees.txt (architecture DB)
3. Phase 2 → 01_initialisation_react.txt (architecture frontend)
4. Phase 3 → 02_service_solveur_orchestration.txt (orchestration)

---

## Commandes utiles

### Backend
```bash
# Créer DB
python scripts/init_db.py

# Valider Excel
python actualiser_config.py configs/config_volley.yaml

# Importer projet
python scripts/import_excel.py configs/config_volley.yaml

# Lancer serveur
uvicorn backend.api.main:app --reload --port 8000

# Tests
pytest tests/
```

### Frontend
```bash
# Installer deps
cd frontend
npm install

# Lancer dev
npm run dev

# Build production
npm run build
npm run preview

# Tests
npm run test
```

### Résolution
```bash
# CLI (si existe)
python main.py configs/config_volley.yaml

# API
curl -X POST http://localhost:8000/projects/1/solve

# API avec override
curl -X POST http://localhost:8000/projects/1/solve \
  -H "Content-Type: application/json" \
  -d '{"strategie": "heuristique", "temps_max_secondes": 60}'
```

---

## Contacts et support

**Documentation complète** : Voir dossier `docs/`
- `ARCHITECTURE.md` : Architecture globale
- `CONTRAINTES_README.md` : Détails contraintes
- `GUIDE_MATCHS_FIXES.md` : Guide matchs fixes
- `CONTRIBUTING.md` : Guide contribution

**Structure prompts** :
- `prompts/phase1/` : 8 prompts backend
- `prompts/phase2/` : 6 prompts frontend
- `prompts/phase3/` : 4 prompts solveur
- `prompts/README.txt` : Ce fichier

**Validation** : Tous les prompts intègrent double configuration et respectent les patterns décrits ici.

---

## Récapitulatif final

**✅ Principes à respecter ABSOLUMENT** :

1. **Double configuration** : YAML (hyperparamètres) + Excel (données métier)
2. **Validation Excel** : Toujours utiliser actualiser_config.py AVANT import
3. **Matchs fixes** : est_fixe=True OU semaine < semaine_minimum → Immobiles
4. **Reconstruction Config** : Depuis config_yaml_data (JSON) pour autonomie
5. **NO defaults in .py** : Tous les defaults dans configs/default.yaml
6. **Nomenclature** : semaine_minimum (YAML global) ≠ semaine_min (Match DB)
7. **Stratégie hybride** : Recommandée pour production (optimal + fallback)
8. **Cache invalidation** : Toujours invalider après mutations (React Query)

**❌ À NE JAMAIS FAIRE** :

1. ❌ Hardcoder valeurs par défaut dans .py (utiliser YAML)
2. ❌ Modifier matchs fixes dans solveur (filtrer AVANT)
3. ❌ Importer Excel sans validation (utiliser actualiser_config.py)
4. ❌ Confondre semaine_minimum (YAML) et semaine_min (Match)
5. ❌ Oublier invalidation cache React Query après mutations
6. ❌ Créer variables CP-SAT pour matchs fixes (seulement modifiables)

**🎯 Workflow complet** :

```
1. Préparer Excel (7 feuilles)
   ↓
2. Valider : python actualiser_config.py config.yaml
   ↓
3. Importer : python scripts/import_excel.py config.yaml
   ↓
4. Visualiser calendrier dans React
   ↓
5. Fixer matchs importants (bouton "Fixer")
   ↓
6. Optimiser : Clic "Optimiser le calendrier"
   ↓
7. Exporter : Télécharger Excel final
```

**📚 Total des prompts** : 18 prompts (Phase 1: 8 + Phase 2: 6 + Phase 3: 4)

**🚀 Prêt à implémenter** : Chaque prompt est autonome et détaillé avec :
- Contexte complet
- Code AVANT/APRÈS
- Checklist validation
- Questions critiques
- Documentation

**Bon développement !** 🎉
