# Plan d'Implémentation PyCalendar V2 - Guide Technique

## Objectif Global
Transformer PyCalendar d'une application CLI avec export Excel/HTML en application web full-stack avec API REST et interface interactive, tout en préservant l'intégralité du code existant.

## Contraintes Strictes
1. **Préservation totale** : Aucune modification destructive des modules `solvers/`, `constraints/`, `generators/`, `validation/`
2. **Compatibilité CLI** : Le script `main.py` doit continuer à fonctionner identiquement
3. **Import Excel** : Les fichiers Excel existants doivent pouvoir être importés
4. **Matchs fixes** : Support des matchs verrouillés non-replanifiables par le solver
5. **Semaine minimum** : Contrainte de non-planification avant une semaine donnée

---

## Architecture Cible - Structure des Dossiers

**Légende** : 🆕 = Nouveau fichier, ✏️ = Modification requise, ✅ = Préserver tel quel

```
PyCalendar/
├── backend/                    # 🆕 NOUVEAU - Couche API REST
│   ├── api/
│   │   ├── main.py            # Point entrée FastAPI
│   │   ├── dependencies.py    # get_db(), get_config()
│   │   └── routes/
│   │       ├── projects.py    # CRUD projets
│   │       ├── matches.py     # CRUD + move/fix/unfix
│   │       ├── teams.py       # CRUD équipes
│   │       └── venues.py      # CRUD gymnases
│   │
│   ├── database/
│   │   ├── engine.py          # SQLAlchemy engine + SessionLocal
│   │   ├── models.py          # Project, Team, Venue, Match (SQLAlchemy)
│   │   └── repositories.py    # Couche accès données (optionnel)
│   │
│   ├── services/
│   │   ├── sync_service.py    # Excel → DB
│   │   ├── solver_service.py  # Appel solvers existants
│   │   └── match_service.py   # Logique métier matchs
│   │
│   └── schemas/
│       ├── project.py         # Pydantic schemas
│       ├── match.py
│       ├── team.py
│       └── venue.py
│
├── frontend/                   # NOUVEAU - React app
│   ├── src/
│   │   ├── api/
│   │   │   ├── client.ts      # Axios instance
│   │   │   └── endpoints/
│   │   │       └── matches.ts  # API calls
│   │   │
│   │   ├── components/
│   │   │   └── calendar/
│   │   │       └── Calendar.tsx  # FullCalendar
│   │   │
│   │   ├── hooks/
│   │   │   └── useMatches.ts  # React Query hooks
│   │   │
│   │   ├── pages/
│   │   │   └── CalendarPage.tsx
│   │   │
│   │   └── types/
│   │       └── match.ts       # TypeScript types
│   │
│   └── package.json
│
├── core/                       # ✅ EXISTANT - À préserver
│   └── models.py              # ✏️ MODIFIER - Ajouter champs matchs fixes/scores
│
├── constraints/                # ✅ EXISTANT - Ne pas toucher
├── solvers/                    # ✅ EXISTANT - Modification minimale (filtrage)
├── generators/                 # ✅ EXISTANT - Ne pas toucher
├── validation/                 # ✅ EXISTANT - Ne pas toucher
│
├── tests/                      # 🆕 NOUVEAU
│   ├── conftest.py
│   ├── unit/
│   └── integration/
│
└── scripts/                    # 🆕 NOUVEAU
    ├── init_db.py
    └── import_excel.py
```

---

## PHASE 1 : Backend Foundation (Durée : 2 semaines)

### Objectif de Phase
Mettre en place la couche persistance (SQLAlchemy), l'API REST (FastAPI), et le service de synchronisation Excel→DB, sans impacter le fonctionnement CLI existant.

---

### TÂCHE 1.1 : Enrichir le Modèle Match Existant

**📁 Fichier concerné** : `core/models.py`

**🎯 Objectif** : Ajouter les propriétés nécessaires pour gérer les matchs fixes et les scores sans casser le code existant.

**📋 Instructions détaillées** :

1. **Localiser la dataclass `Match`** dans `core/models.py`
2. **Ajouter les champs suivants** en fin de dataclass avec valeurs par défaut pour compatibilité :
   - `est_fixe: bool = False` - Indique si le match est verrouillé (non-replanifiable)
   - `statut: str = "a_planifier"` - États possibles : `a_planifier`, `planifie`, `fixe`, `termine`, `annule`
   - `score_equipe1: Optional[int] = None` - Score équipe 1 si match terminé
   - `score_equipe2: Optional[int] = None` - Score équipe 2 si match terminé
   - `notes: str = ""` - Notes libres sur le match

3. **Ajouter une méthode `est_modifiable()`** qui retourne `False` si :
   - `est_fixe == True` OU
   - `statut` dans `["fixe", "termine", "annule"]`
   
4. **Ajouter une property `est_planifie`** qui retourne `True` si `semaine is not None`

**⚠️ Points d'attention** :
- Utiliser des valeurs par défaut pour tous les nouveaux champs (compatibilité avec code existant)
- Importer `Optional` depuis `typing` si pas déjà fait
- Ne pas modifier les champs existants (equipe1, equipe2, poule, creneau, priorite)
- Vérifier que les générateurs de matchs dans `generators/` continuent de fonctionner

**🧪 Validation** :
- Exécuter `python main.py configs/config_volley.yaml` → doit fonctionner sans erreur
- Les matchs générés doivent avoir `est_fixe=False` et `statut="a_planifier"` par défaut
- La méthode `est_modifiable()` doit retourner `True` pour un match standard

---

### TÂCHE 1.2 : Ajouter Contrainte Semaine Minimum

**📁 Fichier concerné** : `core/config.py`

**🎯 Objectif** : Permettre de spécifier une semaine minimum avant laquelle aucun match ne peut être planifié.

**📋 Instructions détaillées** :
1. **Localiser la dataclass `Config`** dans `core/config.py`
2. **Ajouter le champ** : `semaine_min: int = 1` avec valeur par défaut 1
3. **Modifier le parsing YAML** pour supporter ce nouveau champ optionnel

**⚠️ Points d'attention** :
- Valeur par défaut à 1 (planification dès semaine 1)
- Doit être optionnel dans les fichiers YAML existants
- Si absent du YAML, utiliser valeur par défaut

**🧪 Validation** :
- Charger un config YAML sans `semaine_min` → doit utiliser 1
- Ajouter `semaine_min: 5` dans un YAML test → doit lire correctement

---

### TÂCHE 1.3 : Créer Structure Database Backend

**📁 Dossiers à créer** : `backend/database/`

**🎯 Objectif** : Mettre en place SQLAlchemy avec models mappant les entités du projet vers une base SQLite.

**📋 Instructions détaillées** :

#### Sous-tâche 1.3.1 : Engine et Session Factory

**Créer fichier** : `backend/database/engine.py`

**Contenu requis** :
1. **Import** : SQLAlchemy `create_engine`, `sessionmaker`, `event` de sqlalchemy
2. **Définir chemin DB** : `database/pycalendar.db` à la racine du projet (utiliser `pathlib.Path`)
3. **Créer engine** : SQLite avec `check_same_thread=False`
4. **Activer foreign keys** : Utiliser `event.listen` pour exécuter `PRAGMA foreign_keys=ON` à chaque connexion
5. **SessionLocal** : Factory sessionmaker avec `autocommit=False`, `autoflush=False`
6. **Fonction `get_db()`** : Generator pour dependency injection FastAPI
   - Créer session
   - `yield session`
   - Fermer session dans `finally`
7. **Fonction `init_db()`** : Créer toutes les tables via `Base.metadata.create_all()`

**⚠️ Points d'attention** :
- Le pragma SQLite MUST être exécuté à chaque nouvelle connexion
- Le dossier `database/` sera créé automatiquement si inexistant
- Session doit toujours être fermée (via finally)

#### Sous-tâche 1.3.2 : Models SQLAlchemy

**Créer fichier** : `backend/database/models.py`

**Contenu requis** :

1. **Base declarative** : `Base = declarative_base()`

2. **Model `Project`** (table `projects`) :
   - PK `id` (Integer, autoincrement)
   - `nom` (String 200, not null)
   - `sport` (String 50, not null)
   - `config_yaml_path` (String 500, nullable)
   - `config_data` (JSON, nullable) - pour stocker config complète
   - `nb_semaines` (Integer, default 26)
   - `semaine_min` (Integer, default 1)
   - `created_at`, `updated_at` (DateTime)
   - **Relationships** : `matches`, `teams`, `venues` avec cascade delete

3. **Model `Team`** (table `teams`) :
   - PK `id`
   - FK `project_id` → projects.id (indexed, not null)
   - `nom`, `institution`, `numero_equipe`, `genre`, `poule`
   - `horaires_preferes` (JSON) - liste d'horaires
   - `lieux_preferes` (JSON) - liste de gymnases
   - `created_at`
   - **Relationship** : `project` back_populates

4. **Model `Venue`** (table `venues`) :
   - PK `id`
   - FK `project_id` (indexed, not null)
   - `nom` (String 200)
   - `capacite` (Integer, default 1)
   - `horaires_disponibles` (JSON) - liste d'horaires
   - `created_at`
   - **Relationship** : `project`

5. **Model `Match`** (table `matches`) :
   - PK `id`
   - FK `project_id` (indexed, not null)
   - **Équipes** : `equipe1_nom`, `equipe1_institution`, `equipe1_genre`, `equipe2_nom`, `equipe2_institution`, `equipe2_genre`
   - `poule` (String 100, indexed)
   - **Créneau** : `semaine` (Integer nullable, indexed), `horaire` (String 20 nullable), `gymnase` (String 200 nullable)
   - **État** : `est_fixe` (Boolean, default False, indexed), `statut` (String 50, default "a_planifier", indexed), `priorite` (Integer, default 0)
   - **Scores** : `score_equipe1`, `score_equipe2` (Integer nullable)
   - `notes` (Text)
   - `created_at`, `updated_at`
   - **Relationship** : `project`
   - **Properties** : `est_planifie` (True si semaine non null), `est_modifiable` (cf logique core.Match)

6. **Indexes composites** (ajouter en fin de fichier) :
   - `idx_match_project_semaine` sur (project_id, semaine)
   - `idx_match_project_poule` sur (project_id, poule)

**⚠️ Points d'attention** :
- Les colonnes JSON nécessitent import `JSON` de sqlalchemy
- Properties `est_planifie` et `est_modifiable` doivent reproduire la logique du `core.Match`
- Cascade delete crucial pour éviter orphelins
- Indexes pour optimiser requêtes API (filtrage par projet/semaine/poule)

**🧪 Validation** :
- Importer `models.py` → pas d'erreur
- Vérifier que `Base.metadata.tables` contient 4 tables

---

### TÂCHE 1.4 : Créer Schemas Pydantic

**📁 Dossier à créer** : `backend/schemas/`

**🎯 Objectif** : Définir les schémas de validation/sérialisation pour l'API REST.

**📋 Instructions détaillées** :

#### Sous-tâche 1.4.1 : Schemas Match

**Créer fichier** : `backend/schemas/match.py`

**Schémas requis** :

1. **`MatchBase`** (BaseModel Pydantic) :
   - Tous les champs d'un match sauf `id`, `project_id`, timestamps
   - Champs équipes, poule, créneau (optionnels), est_fixe, statut
   - Valeurs par défaut identiques au model DB

2. **`MatchCreate`** (hérite MatchBase) :
   - Ajouter : `project_id: int`

3. **`MatchUpdate`** (BaseModel) :
   - Tous champs optionnels : semaine, horaire, gymnase, est_fixe, statut, scores, notes
   - Permet updates partiels

4. **`MatchResponse`** (hérite MatchBase) :
   - Ajouter : `id`, `project_id`, `score_equipe1`, `score_equipe2`, `notes`, `created_at`, `updated_at`
   - Config : `from_attributes = True` (pour conversion depuis ORM)

5. **`MatchMove`** (BaseModel) :
   - Champs : `semaine: int`, `horaire: str`, `gymnase: str`
   - Pour endpoint de déplacement drag & drop

**⚠️ Points d'attention** :
- Utiliser `Optional[T]` pour champs nullables
- Import `datetime` pour typage timestamps
- Config `from_attributes` nécessaire pour réponses ORM

#### Sous-tâche 1.4.2 : Schemas Project/Team/Venue

**Créer fichiers** : `backend/schemas/project.py`, `team.py`, `venue.py`

**Pour chaque** : Créer schémas `Base`, `Create`, `Update`, `Response` selon même pattern que Match

**Structure minimale** :
- **Project** : nom, sport, config_yaml_path, nb_semaines, semaine_min
- **Team** : nom, institution, poule, horaires_preferes (List[str]), lieux_preferes (List[str])
- **Venue** : nom, capacite, horaires_disponibles (List[str])

---

### TÂCHE 1.5 : Implémenter API Routes FastAPI

**📁 Dossier à créer** : `backend/api/`, `backend/api/routes/`

**🎯 Objectif** : Exposer les endpoints REST pour CRUD + opérations spécifiques (fix/unfix/move).

**📋 Instructions détaillées** :

#### Sous-tâche 1.5.1 : Application FastAPI

**Créer fichier** : `backend/api/main.py`

**Contenu requis** :
1. **Créer app** : `FastAPI(title="PyCalendar API", version="2.0.0")`
2. **Middleware CORS** :
   - `allow_origins=["http://localhost:5173"]` (frontend dev)
   - `allow_credentials=True`
   - `allow_methods=["*"]`, `allow_headers=["*"]`
3. **Routes basiques** :
   - `GET /` → info API
   - `GET /health` → status check
4. **Import routers** (commentés initialement, décommenter après création routes)

**⚠️ Points d'attention** :
- CORS essentiel pour dev local
- En production, restreindre origins

#### Sous-tâche 1.5.2 : Routes Matches

**Créer fichier** : `backend/api/routes/matches.py`

**Router** : `APIRouter()`

**Endpoints requis** :

1. **`GET /matches/`** :
   - Query param optionnel : `project_id: int`
   - Filtrer par projet si fourni
   - Response : `List[MatchResponse]`

2. **`GET /matches/{match_id}`** :
   - Récupérer match par ID
   - 404 si non trouvé
   - Response : `MatchResponse`

3. **`POST /matches/`** :
   - Body : `MatchCreate`
   - Créer en DB, commit, refresh
   - Status code 201
   - Response : `MatchResponse`

4. **`PUT /matches/{match_id}`** :
   - Body : `MatchUpdate`
   - Utiliser `.dict(exclude_unset=True)` pour update partiel
   - Itérer et setattr sur model
   - Commit
   - Response : `MatchResponse`

5. **`POST /matches/{match_id}/move`** :
   - Body : `MatchMove`
   - **Vérifier** `est_modifiable` avant update
   - 400 si match fixé
   - Update semaine/horaire/gymnase
   - Changer statut à "planifie"
   - Response : `MatchResponse`

6. **`POST /matches/{match_id}/fix`** :
   - Mettre `est_fixe=True`, `statut="fixe"`
   - Response : `{"message": "Match fixé"}`

7. **`POST /matches/{match_id}/unfix`** :
   - Mettre `est_fixe=False`
   - Restaurer statut : "planifie" si créneau existe, sinon "a_planifier"
   - Response : `{"message": "Match déverrouillé"}`

8. **`DELETE /matches/{match_id}`** :
   - Supprimer de DB
   - Status code 204

**⚠️ Points d'attention** :
- Toujours vérifier existence (404)
- Vérifier `est_modifiable` pour opérations de modification
- Dependency `Depends(get_db)` pour injection session
- Imports : `from backend.database.engine import get_db`, `from backend.database import models`, `from backend.schemas import match as schemas`

#### Sous-tâche 1.5.3 : Routes Projects/Teams/Venues

**Créer fichiers** : `backend/api/routes/projects.py`, `teams.py`, `venues.py`

**Pour chaque** : Implémenter CRUD standard (GET list, GET detail, POST create, PUT update, DELETE)

**Pattern identique** à matches sans opérations spéciales

**⚠️ Spécificité Projects** :
- Endpoint `GET /projects/{id}/stats` → retourner counts (nb matchs, nb planifiés, nb fixes)

---

### TÂCHE 1.6 : Service de Synchronisation Excel → DB

**📁 Dossier à créer** : `backend/services/`

**🎯 Objectif** : Importer un projet depuis fichiers Excel+YAML existants vers la base de données.

**📋 Instructions détaillées** :

**Créer fichier** : `backend/services/sync_service.py`

**Classe** : `SyncService`

**Constructeur** : Accepter `db: Session`

**Méthode principale** : `import_from_excel(config_path: str, project_name: str) -> models.Project`

**Algorithme** :

1. **Charger config** : `Config.from_yaml(config_path)`
2. **Charger données Excel** : Utiliser `DataSource(config.fichier_donnees)`
   - `equipes = source.charger_equipes()`
   - `gymnases = source.charger_gymnases()`

3. **Créer Project en DB** :
   - nom, sport (détecté via `_detect_sport()`), config_yaml_path
   - `nb_semaines` depuis config
   - `semaine_min` via `getattr(config, 'semaine_min', 1)`
   - `db.add()`, `db.flush()` pour obtenir ID

4. **Importer Teams** :
   - Itérer sur `equipes`
   - Créer `models.Team` pour chaque
   - Sérialiser `horaires_preferes` et `lieux_preferes` en JSON via `json.dumps()`
   - `db.add()` chacun

5. **Importer Venues** :
   - Itérer sur `gymnases`
   - Créer `models.Venue`
   - Sérialiser `horaires_disponibles` en JSON
   - `db.add()` chacun

6. **Générer et importer Matches** :
   - Créer `poules = source.get_poules_dict(equipes)`
   - Instancier `MultiPoolGenerator()`
   - `matchs = generator.generer_matchs(poules)`
   - Itérer sur matchs :
     - Créer `models.Match` avec infos équipes, poule
     - `semaine/horaire/gymnase` à `None` (non planifiés initialement)
     - `db.add()` chacun

7. **Commit final** : `db.commit()`
8. **Retourner** : project

**Méthode auxiliaire** : `_detect_sport(config: Config) -> str`
- Détecter "volleyball" si "volley" dans chemin Excel
- Détecter "handball" si "hand" dans chemin
- Sinon "autre"

**⚠️ Points d'attention** :
- Utiliser `db.flush()` après Project pour obtenir ID avant FK
- Sérialiser listes Python en JSON pour colonnes JSON
- `getattr(config, 'semaine_min', 1)` pour compatibilité anciens configs
- Ne pas oublier commit final
- Gérer exceptions si Excel/YAML invalides

**🧪 Validation** :
- Importer projet test
- Vérifier en DB : 1 project, N teams, M venues, X matches non planifiés

---

### TÂCHE 1.7 : Scripts d'Initialisation

**📁 Dossier à créer** : `scripts/`

**🎯 Objectif** : Fournir scripts CLI pour init DB et import Excel.

**📋 Instructions détaillées** :

#### Script 1 : Init DB

**Créer fichier** : `scripts/init_db.py`

**Contenu** :
1. Ajouter répertoire parent au `sys.path` pour imports PyCalendar
2. Importer `init_db` de `backend.database.engine`
3. Appeler `init_db()`
4. Print confirmation

**Usage** : `python scripts/init_db.py`

#### Script 2 : Import Excel

**Créer fichier** : `scripts/import_excel.py`

**Contenu** :
1. Ajouter répertoire parent au `sys.path`
2. Parser arguments : `<config.yaml>` obligatoire, `[project_name]` optionnel
3. Si pas de nom, utiliser `Path(config_path).stem`
4. Créer session DB via `SessionLocal()`
5. Instancier `SyncService(db)`
6. Appeler `import_from_excel()`
7. Print confirmation avec ID projet
8. Fermer session dans `finally`

**Usage** : `python scripts/import_excel.py configs/config_volley.yaml "Volley 2025"`

**⚠️ Points d'attention** :
- Toujours fermer session
- Afficher message d'usage si args manquants
- Catcher exceptions et afficher erreurs propres

---

### TÂCHE 1.8 : Tests Unitaires Backend

**📁 Dossiers à créer** : `tests/`, `tests/unit/`

**🎯 Objectif** : Tester models DB et endpoints API basiques.

**📋 Instructions détaillées** :

#### Fixtures pytest

**Créer fichier** : `tests/conftest.py`

**Fixtures requis** :

1. **`db_engine`** :
   - Créer engine SQLite en mémoire (`:memory:`)
   - `Base.metadata.create_all()`
   - Yield engine
   - `Base.metadata.drop_all()` cleanup

2. **`db_session`** :
   - Utiliser fixture `db_engine`
   - Créer SessionLocal
   - Yield session
   - Close session

3. **`sample_project`** :
   - Utiliser fixture `db_session`
   - Créer et commit `models.Project` de test
   - Refresh et yield

**⚠️ Points d'attention** :
- SQLite in-memory pour rapidité
- Cleanup via yield/teardown
- Scope par défaut (function) pour isolation

#### Tests Models

**Créer fichier** : `tests/unit/test_models.py`

**Tests requis** :

1. **`test_create_project`** :
   - Créer Project, commit
   - Assert ID non null

2. **`test_create_match`** :
   - Utiliser `sample_project`
   - Créer Match lié au projet
   - Assert ID non null
   - Assert `est_planifie == False`
   - Assert `est_modifiable == True`

3. **`test_fix_match`** :
   - Créer Match avec créneau
   - Fixer : `est_fixe=True`, `statut="fixe"`
   - Assert `est_modifiable == False`

4. **`test_match_properties`** :
   - Match sans créneau → `est_planifie == False`
   - Match avec semaine → `est_planifie == True`

**⚠️ Points d'attention** :
- Tester properties calculées
- Vérifier logique `est_modifiable`

#### Tests API (optionnel Phase 1, recommandé Phase 2)

**Créer fichier** : `tests/unit/test_api_matches.py`

**Utiliser** : `TestClient` de FastAPI avec fixtures

**Tests basiques** :
- GET /matches/ → 200
- POST /matches/ → 201 + vérifier body
- POST /matches/{id}/fix → vérifier changement état

---

### VALIDATION GLOBALE PHASE 1

**🧪 Checklist de validation** :

1. **Structure** :
   - [ ] Dossiers `backend/`, `scripts/`, `tests/` créés
   - [ ] Fichier `database/pycalendar.db` absent (sera créé par script)

2. **Init DB** :
   ```bash
   python scripts/init_db.py
   ```
   - [ ] Pas d'erreur
   - [ ] Fichier `database/pycalendar.db` créé
   - [ ] Tables `projects`, `teams`, `venues`, `matches` présentes (vérifier avec SQLite browser)

3. **Import Excel** :
   ```bash
   python scripts/import_excel.py configs/config_volley.yaml "Test Volley"
   ```
   - [ ] Pas d'erreur
   - [ ] Message confirmation avec ID projet
   - [ ] Vérifier en DB : project créé, teams créées, venues créées, matches créés (non planifiés)

4. **API** :
   ```bash
   uvicorn backend.api.main:app --reload
   ```
   - [ ] Server démarre sur port 8000
   - [ ] Accès à http://localhost:8000/docs → Swagger UI
   - [ ] Endpoint /health → `{"status": "healthy"}`

5. **Tests endpoints** :
   ```bash
   curl http://localhost:8000/api/projects/
   curl http://localhost:8000/api/matches/?project_id=1
   curl http://localhost:8000/api/matches/1
   ```
   - [ ] Réponses JSON valides
   - [ ] Données cohérentes avec import

6. **Tests unitaires** :
   ```bash
   pytest tests/ -v
   ```
   - [ ] Tous les tests passent
   - [ ] Coverage >80% sur models

7. **CLI existant** :
   ```bash
   python main.py configs/config_volley.yaml
   ```
   - [ ] Fonctionne toujours sans erreur
   - [ ] Génère calendrier HTML comme avant

**❌ Critères d'échec** :
- CLI cassé
- Import de modules existants échoue
- Contraintes DB violées
- Tests échouent

---

## PHASE 2 : Frontend React (Durée : 2 semaines)

### Objectif de Phase
Créer l'interface web React avec affichage calendrier, édition drag & drop, et communication API.

---

### TÂCHE 2.1 : Initialiser Projet React avec Vite

**📁 Dossier à créer** : `frontend/` (à la racine du projet)

**🎯 Objectif** : Créer application React TypeScript avec Vite comme bundler.

**📋 Instructions détaillées** :

1. **Créer projet Vite** :
   ```bash
   npm create vite@latest frontend -- --template react-ts
   cd frontend
   ```

2. **Installer dépendances principales** :
   ```bash
   npm install
   ```

3. **Installer librairies requises** :
   ```bash
   # State management et data fetching
   npm install @tanstack/react-query axios zustand
   
   # Calendrier drag & drop
   npm install @fullcalendar/react @fullcalendar/daygrid @fullcalendar/timegrid @fullcalendar/interaction
   
   # Routing
   npm install react-router-dom
   
   # UI (optionnel mais recommandé)
   npm install tailwindcss postcss autoprefixer
   npx tailwindcss init -p
   ```

4. **Configurer Vite pour proxy API** :

**Modifier fichier** : `frontend/vite.config.ts`

**Ajouter** :
- `resolve.alias` : `'@'` pointant vers `./src`
- `server.port` : 5173
- `server.proxy` : `/api` vers `http://localhost:8000` avec `changeOrigin: true`

**⚠️ Points d'attention** :
- Proxy permet d'éviter CORS en dev
- Alias `@` pour imports propres (`@/components/...`)
- Port 5173 correspond au CORS configuré dans backend

**🧪 Validation** :
```bash
npm run dev
```
- [ ] Server démarre sur http://localhost:5173
- [ ] Page React par défaut s'affiche
- [ ] Hot reload fonctionne

---

### TÂCHE 2.2 : Définir Types TypeScript

**📁 Dossier à créer** : `frontend/src/types/`

**🎯 Objectif** : Typer toutes les entités de l'API pour type-safety.

**📋 Instructions détaillées** :

**Créer fichier** : `frontend/src/types/match.ts`

**Types requis** :

1. **Interface `Match`** :
   - Tous les champs de `MatchResponse` backend
   - `id: number`, `project_id: number`
   - Équipes : `equipe1_nom`, `equipe1_institution`, `equipe1_genre` (string)
   - Même pour équipe2
   - `poule: string`
   - Créneau : `semaine: number | null`, `horaire: string | null`, `gymnase: string | null`
   - État : `est_fixe: boolean`, `statut` avec union type littérale
   - Scores : `score_equipe1: number | null`, `score_equipe2: number | null`
   - `notes: string`
   - Timestamps : `created_at: string`, `updated_at: string | null`

2. **Type union `MatchStatus`** :
   ```typescript
   type MatchStatus = 'a_planifier' | 'planifie' | 'fixe' | 'termine' | 'annule'
   ```

3. **Interface `MatchUpdate`** :
   - Tous champs optionnels sauf pour opérations spécifiques
   - `semaine?: number`, etc.

4. **Interface `MatchMove`** :
   - Champs requis : `semaine: number`, `horaire: string`, `gymnase: string`

**Créer de même** : `project.ts`, `team.ts`, `venue.ts`

**⚠️ Points d'attention** :
- Types doivent matcher EXACTEMENT les schemas Pydantic backend
- Utiliser union types pour statuts (autocomplétion IDE)
- `Date` côté Python devient `string` (ISO format) côté TypeScript

---

### TÂCHE 2.3 : Client API Axios

**📁 Dossier à créer** : `frontend/src/api/`

**🎯 Objectif** : Centraliser appels API avec client Axios configuré.

**📋 Instructions détaillées** :

#### Sous-tâche 2.3.1 : Client de base

**Créer fichier** : `frontend/src/api/client.ts`

**Contenu** :
1. Créer instance Axios :
   - `baseURL: '/api'` (proxy Vite redirigera vers backend)
   - Header `Content-Type: application/json`
2. Optionnel : Interceptors pour logging/erreurs

**⚠️ Points d'attention** :
- `baseURL` relatif car proxy Vite gère le mapping
- En production, remplacer par URL absolue backend

#### Sous-tâche 2.3.2 : Endpoints Matches

**Créer fichier** : `frontend/src/api/endpoints/matches.ts`

**Objet export** : `matchesApi`

**Méthodes requises** :

1. **`list(projectId?: number): Promise<Match[]>`** :
   - GET `/matches/`
   - Params : `{ project_id: projectId }` si fourni
   - Retourner `data`

2. **`get(id: number): Promise<Match>`** :
   - GET `/matches/${id}`

3. **`create(match: Partial<Match>): Promise<Match>`** :
   - POST `/matches/`
   - Body : match
   - Status 201

4. **`update(id: number, data: MatchUpdate): Promise<Match>`** :
   - PUT `/matches/${id}`
   - Body : data

5. **`move(id: number, creneau: MatchMove): Promise<Match>`** :
   - POST `/matches/${id}/move`
   - Body : creneau

6. **`fix(id: number): Promise<void>`** :
   - POST `/matches/${id}/fix`

7. **`unfix(id: number): Promise<void>`** :
   - POST `/matches/${id}/unfix`

8. **`delete(id: number): Promise<void>`** :
   - DELETE `/matches/${id}`

**⚠️ Points d'attention** :
- Importer types depuis `@/types/match`
- Destructurer `{ data }` depuis réponse Axios
- Typer retours avec `Promise<T>`

**Créer de même** : `endpoints/projects.ts`, `teams.ts`, `venues.ts`

---

### TÂCHE 2.4 : Hooks React Query

**📁 Dossier à créer** : `frontend/src/hooks/`

**🎯 Objectif** : Wrapper appels API dans hooks React Query pour cache/invalidation automatique.

**📋 Instructions détaillées** :

**Créer fichier** : `frontend/src/hooks/useMatches.ts`

**Hooks requis** :

1. **`useMatches(projectId?: number)`** :
   - Utiliser `useQuery` de TanStack Query
   - `queryKey`: `['matches', projectId]`
   - `queryFn`: appeler `matchesApi.list(projectId)`
   - `enabled`: `!!projectId` (ne query que si projectId fourni)

2. **`useMatch(id: number)`** :
   - `queryKey`: `['matches', id]`
   - `queryFn`: `matchesApi.get(id)`

3. **`useUpdateMatch()`** :
   - Utiliser `useMutation`
   - `mutationFn`: accepter `{ id: number, data: MatchUpdate }`
   - `onSuccess`: invalider query `['matches']`

4. **`useMoveMatch()`** :
   - `mutationFn`: accepter `{ id: number, creneau: MatchMove }`
   - Appeler `matchesApi.move()`
   - `onSuccess`: invalider `['matches']`

5. **`useFixMatch()`** :
   - `mutationFn`: accepter `{ id: number }`
   - Appeler `matchesApi.fix()`
   - `onSuccess`: invalider queries

6. **`useUnfixMatch()`** :
   - Similaire à `useFixMatch` avec `unfix`

7. **`useDeleteMatch()`** :
   - `mutationFn`: accepter `{ id: number }`
   - `onSuccess`: invalider queries

**⚠️ Points d'attention** :
- Utiliser `useQueryClient()` dans mutations pour invalidation
- `invalidateQueries({ queryKey: ['matches'] })` rafraîchit toutes queries matches
- Typer arguments mutations avec interfaces TypeScript
- Considérer optimistic updates (Phase 3)

**Créer de même** : `useProjects.ts`, `useTeams.ts`, `useVenues.ts`

---

### TÂCHE 2.5 : Composant Calendrier FullCalendar

**📁 Dossier à créer** : `frontend/src/components/calendar/`

**🎯 Objectif** : Afficher matchs dans calendrier avec drag & drop.

**📋 Instructions détaillées** :

**Créer fichier** : `frontend/src/components/calendar/Calendar.tsx`

**Props interface** :
```typescript
interface CalendarProps {
  matches: Match[]
  onMatchDrop?: (matchId: number, newCreneau: MatchMove) => void
  onMatchClick?: (match: Match) => void
}
```

**Contenu composant** :

1. **Transformer matches en events FullCalendar** :
   - Filtrer matches ayant `semaine` et `horaire` non null
   - Mapper vers objets :
     - `id`: `match.id.toString()`
     - `title`: `${equipe1_nom} vs ${equipe2_nom}`
     - `start`: calculer Date depuis semaine + horaire (voir fonction auxiliaire)
     - `backgroundColor`: rouge si `est_fixe`, bleu sinon
     - `editable`: `!est_fixe`
     - `extendedProps`: `{ match }` (stocker objet complet)

2. **Fonction `calculateDate(semaine: number, horaire: string): Date`** :
   - Définir date de référence (ex: 1er janvier 2025)
   - Ajouter `(semaine - 1) * 7` jours
   - Parser horaire (format "HH:MM")
   - Setter heures/minutes sur date

3. **Fonction inverse `getWeekNumber(date: Date): number`** :
   - Calculer différence en jours depuis date référence
   - Diviser par 7, arrondir, +1

4. **Composant FullCalendar** :
   - `plugins`: `[dayGridPlugin, timeGridPlugin, interactionPlugin]`
   - `initialView`: `"timeGridWeek"`
   - `events`: array transformé
   - `editable`: true
   - `eventDrop`: callback :
     - Récupérer `match` depuis `info.event.extendedProps`
     - Calculer nouveau créneau depuis `info.event.start` (via `getWeekNumber` + getHours/Minutes)
     - Appeler `onMatchDrop?.(match.id, newCreneau)`
   - `eventClick`: callback :
     - Appeler `onMatchClick?.(match)`

**⚠️ Points d'attention** :
- Date de référence doit être cohérente (stocker en config ou props)
- Format horaire backend : "HH:MM" (24h)
- `editable` per-event empêche drag si fixé
- Gérer timezone (UTC ou locale selon besoin)
- Import CSS FullCalendar : `import '@fullcalendar/core/main.css'` etc.

**🧪 Validation** :
- Afficher avec matches de test
- Vérifier couleurs (rouge pour fixes)
- Drag & drop fonctionne pour matchs non fixés
- Drag & drop bloqué pour matchs fixés

---

### TÂCHE 2.6 : Page Principale

**📁 Dossier à créer** : `frontend/src/pages/`

**🎯 Objectif** : Assembler composants dans page fonctionnelle.

**📋 Instructions détaillées** :

**Créer fichier** : `frontend/src/pages/CalendarPage.tsx`

**Contenu** :

1. **État local** :
   - `selectedProjectId` (useState, hardcoder 1 pour Phase 2)
   
2. **Hooks data** :
   - `const { data: matches, isLoading } = useMatches(selectedProjectId)`
   - `const moveMatch = useMoveMatch()`

3. **Handler `handleMatchDrop`** :
   - Paramètres : `matchId: number`, `creneau: MatchMove`
   - Try-catch :
     - Appeler `await moveMatch.mutateAsync({ id: matchId, creneau })`
     - Succès : toast/notification optionnelle
     - Erreur : afficher alert "Impossible de déplacer le match"

4. **Render** :
   - Loading state si `isLoading`
   - Si `matches` : `<Calendar matches={matches} onMatchDrop={handleMatchDrop} />`

**⚠️ Points d'attention** :
- Gérer loading/error states proprement
- Notification utilisateur pour feedback (Phase 3 : toast library)
- ID projet hardcodé temporaire (Phase 3 : sélection dynamique)

**Créer fichier** : `frontend/src/App.tsx`

**Contenu** :
1. Wrapper `QueryClientProvider` avec instance `QueryClient`
2. Router (React Router) :
   - Route `/` → `CalendarPage`
   - Routes futures : `/projects`, `/stats`, etc.

**⚠️ Points d'attention** :
- `QueryClient` doit être instancié une seule fois (hors composant)
- Configuration QueryClient :
  - `defaultOptions.queries.refetchOnWindowFocus: false` (optionnel, évite refetch constants)

---

### VALIDATION GLOBALE PHASE 2

**🧪 Checklist de validation** :

1. **Structure** :
   - [ ] Dossier `frontend/` créé avec structure Vite
   - [ ] `node_modules/` et fichiers config présents

2. **Démarrage dev** :
   ```bash
   cd frontend
   npm run dev
   ```
   - [ ] Server démarre sur :5173
   - [ ] Hot reload fonctionne

3. **Affichage calendrier** :
   - [ ] Calendrier FullCalendar s'affiche
   - [ ] Matchs du projet apparaissent aux bons créneaux
   - [ ] Matchs fixes sont rouges, autres bleus
   - [ ] Horaires corrects

4. **Drag & drop** :
   - [ ] Glisser match non fixé → fonctionne
   - [ ] Glisser match fixé → bloqué (pas de mouvement)
   - [ ] Après drop : requête API POST /matches/{id}/move
   - [ ] Calendrier se rafraîchit automatiquement

5. **DevTools** :
   - [ ] Onglet React Query DevTools (si installé) : queries visibles
   - [ ] Network tab : appels API corrects
   - [ ] Console : pas d'erreurs

6. **Types TypeScript** :
   ```bash
   npm run build
   ```
   - [ ] Build réussit sans erreurs TypeScript

**❌ Critères d'échec** :
- Erreurs 404 sur API calls (problème proxy)
- Matchs ne s'affichent pas
- Drag & drop ne trigger pas API
- Erreurs TypeScript

---

## PHASE 3 : Intégration Solver (Durée : 2 semaines)

### Objectif de Phase
Permettre l'exécution des solvers depuis l'interface web avec prise en compte des matchs fixes et semaine minimum.

---

### TÂCHE 3.1 : Modifier Solvers pour Filtrage

**📁 Fichiers concernés** : `solvers/cpsat_solver.py`, `solvers/greedy_solver.py`

**🎯 Objectif** : Filtrer matchs fixes et créneaux réservés AVANT résolution.

**📋 Instructions détaillées** :

**Pour CPSAT Solver** :

**Modifier méthode** : `CPSATSolver.solve()`

**Au début de la méthode, avant création model CP-SAT** :

1. **Séparer matchs** :
   ```python
   matchs_fixes = [m for m in matchs if m.est_fixe or m.statut == "fixe"]
   matchs_modifiables = [m for m in matchs if m.est_modifiable()]
   ```

2. **Identifier créneaux réservés** :
   ```python
   creneaux_reserves = set()
   for m in matchs_fixes:
       if m.creneau:
           creneaux_reserves.add((m.creneau.semaine, m.creneau.horaire, m.creneau.gymnase))
   ```

3. **Filtrer créneaux disponibles** :
   ```python
   creneaux_disponibles = [
       c for c in creneaux 
       if (c.semaine, c.horaire, c.gymnase) not in creneaux_reserves
   ]
   ```

4. **Appliquer contrainte semaine_min** :
   ```python
   if hasattr(self.config, 'semaine_min'):
       creneaux_disponibles = [
           c for c in creneaux_disponibles 
           if c.semaine >= self.config.semaine_min
       ]
   ```

5. **Résoudre avec matchs_modifiables et creneaux_disponibles** :
   - Toute la logique existante du solver
   - Ne créer variables CP-SAT que pour `matchs_modifiables`
   - Ne considérer que `creneaux_disponibles`

6. **Après résolution, reconstruire solution complète** :
   ```python
   # Ajouter matchs fixes à la solution
   for m in matchs_fixes:
       solution.matchs_planifies.append(m)
   ```

**Répéter pour Greedy Solver** : Même logique de filtrage en début de `solve()`

**⚠️ Points d'attention** :
- Ne PAS modifier signature méthode `solve()`
- Préserver logique existante (juste filtrer inputs)
- Vérifier que matchs fixes ont un créneau valide (sinon log warning)
- `est_modifiable()` doit être appelé (utilise méthode ajoutée Phase 1)

**🧪 Validation** :
1. Créer solution avec matchs mixtes (fixes et modifiables)
2. Fixer match sur semaine 3, horaire 14h, gymnase A
3. Lancer solver
4. Vérifier :
   - Match fixé reste à son créneau
   - Aucun autre match assigné à ce créneau
   - Matchs modifiables répartis sur créneaux restants

---

### TÂCHE 3.2 : Service Solver Backend

**📁 Fichier à créer** : `backend/services/solver_service.py`

**🎯 Objectif** : Orchestrer conversion DB → Core models → Solver → DB.

**📋 Instructions détaillées** :

**Classe** : `SolverService`

**Constructeur** : `__init__(self, db: Session)`

**Méthode principale** : `solve_project(project_id: int, strategy: str = "cpsat") -> Solution`

**Algorithme** :

1. **Charger projet depuis DB** :
   ```python
   project = db.query(models.Project).filter(models.Project.id == project_id).first()
   if not project:
       raise ValueError("Projet non trouvé")
   ```

2. **Charger config** :
   ```python
   config = Config.from_yaml(project.config_yaml_path)
   config.semaine_min = project.semaine_min  # Override depuis DB
   ```

3. **Convertir DB models → Core models** :
   - `matchs = self._db_to_core_matches(project_id)`
   - `creneaux = self._generate_creneaux(project_id, config.nb_semaines)`
   - `gymnases = self._db_to_core_gymnases(project_id)`

4. **Instancier solver** :
   ```python
   if strategy == "cpsat":
       solver = CPSATSolver(config)
   elif strategy == "greedy":
       solver = GreedySolver(config)
   else:
       raise ValueError(f"Stratégie inconnue: {strategy}")
   ```

5. **Résoudre** :
   ```python
   solution = solver.solve(matchs, creneaux, gymnases)
   ```

6. **Sauvegarder solution en DB** :
   ```python
   self._save_solution(project_id, solution)
   ```

7. **Retourner solution**

**Méthodes auxiliaires** :

**`_db_to_core_matches(project_id: int) -> List[core.Match]`** :
- Query tous matchs du projet
- Pour chaque match DB :
  - Créer `Equipe` pour equipe1 et equipe2
  - Créer `Creneau` si semaine/horaire/gymnase non null
  - Créer `core.Match` avec tous attributs (est_fixe, statut, priorite)
- Retourner liste

**`_generate_creneaux(project_id: int, nb_semaines: int) -> List[Creneau]`** :
- Query tous venues du projet
- Pour chaque venue :
  - Désérialiser `horaires_disponibles` (JSON → list)
  - Pour chaque semaine (1 à nb_semaines) :
    - Pour chaque horaire dispo :
      - Créer `Creneau(semaine, horaire, venue.nom)`
- Retourner liste complète

**`_db_to_core_gymnases(project_id: int) -> List[Gymnase]`** :
- Query venues
- Mapper vers `core.Gymnase`
- Désérialiser JSON

**`_save_solution(project_id: int, solution: Solution)`** :
- Pour chaque match dans `solution.matchs_planifies` :
  - Trouver match correspondant en DB (par equipe1_nom/equipe2_nom)
  - Si match.est_modifiable (vérifier!) :
    - Update semaine/horaire/gymnase depuis `match.creneau`
    - Changer statut à "planifie"
  - Si match fixé : ne rien changer
- `db.commit()`

**⚠️ Points d'attention** :
- Ne JAMAIS modifier matchs fixes lors de `_save_solution`
- Gérer cas où solver ne trouve pas de solution (solution.matchs_planifies incomplet)
- Logs pour debugging (combien matchs fixes, modifiables, créneaux disponibles)
- Transaction DB : rollback si erreur

**🧪 Validation** :
- Charger projet avec matchs
- Fixer 2-3 matchs
- Appeler `solve_project()`
- Vérifier :
  - Matchs fixes inchangés
  - Autres matchs planifiés
  - Pas de conflits (2 matchs même créneau)

---

### TÂCHE 3.3 : Endpoint API Solver

**📁 Fichier à créer** : `backend/api/routes/solver.py`

**🎯 Objectif** : Exposer endpoint POST pour lancer résolution.

**📋 Instructions détaillées** :

**Router** : `APIRouter()`

**Schema requête** :
```python
class SolveRequest(BaseModel):
    strategy: str = "cpsat"  # "cpsat" ou "greedy"
```

**Endpoint** : `POST /projects/{project_id}/solve`

**Paramètres** :
- Path : `project_id: int`
- Body : `request: SolveRequest`
- Dependencies : `db: Session = Depends(get_db)`

**Implémentation** :

1. **Vérifier projet existe** :
   ```python
   project = db.query(models.Project).filter(models.Project.id == project_id).first()
   if not project:
       raise HTTPException(404, "Projet non trouvé")
   ```

2. **Instancier service** :
   ```python
   service = SolverService(db)
   ```

3. **Option A - Synchrone (simple, Phase 3)** :
   ```python
   solution = service.solve_project(project_id, request.strategy)
   return {"message": "Résolution terminée", "matchs_planifies": len(solution.matchs_planifies)}
   ```

4. **Option B - Asynchrone (recommandé si solver lent)** :
   ```python
   background_tasks.add_task(service.solve_project, project_id, request.strategy)
   return {"message": "Résolution lancée en arrière-plan", "project_id": project_id}
   ```
   - Ajouter param `background_tasks: BackgroundTasks`
   - Phase 4 : ajouter WebSocket pour notifier fin

**Inclure router dans main.py** :
```python
from .routes import solver
app.include_router(solver.router, prefix="/api/projects", tags=["Solver"])
```

**⚠️ Points d'attention** :
- Validation strategy : doit être "cpsat" ou "greedy"
- Timeout possible si solver long (considérer background task)
- Logs pour tracking (début/fin résolution, durée)

**🧪 Validation** :
```bash
curl -X POST http://localhost:8000/api/projects/1/solve \
  -H "Content-Type: application/json" \
  -d '{"strategy": "cpsat"}'
```
- [ ] 200 OK
- [ ] Message confirmation
- [ ] Vérifier en DB : matchs mis à jour

---

### TÂCHE 3.4 : Intégration Frontend Solver

**📁 Fichiers à modifier** : `frontend/src/`

**🎯 Objectif** : Bouton "Recalculer" dans interface pour lancer solver.

**📋 Instructions détaillées** :

#### Sous-tâche 3.4.1 : API Endpoint

**Fichier** : `frontend/src/api/endpoints/solver.ts`

**Fonction** :
```typescript
export const solverApi = {
  solve: async (projectId: number, strategy: 'cpsat' | 'greedy' = 'cpsat') => {
    const { data } = await apiClient.post(`/projects/${projectId}/solve`, { strategy })
    return data
  }
}
```

#### Sous-tâche 3.4.2 : Hook React Query

**Fichier** : `frontend/src/hooks/useSolver.ts`

**Hook** :
```typescript
export function useSolveProject() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ projectId, strategy }: { projectId: number; strategy: 'cpsat' | 'greedy' }) =>
      solverApi.solve(projectId, strategy),
    onSuccess: () => {
      // Invalider matches pour refetch
      queryClient.invalidateQueries({ queryKey: ['matches'] })
    },
  })
}
```

#### Sous-tâche 3.4.3 : UI Button

**Modifier** : `frontend/src/pages/CalendarPage.tsx`

**Ajouter** :
1. Hook : `const solveProject = useSolveProject()`
2. Handler :
   ```typescript
   const handleSolve = async (strategy: 'cpsat' | 'greedy') => {
     try {
       await solveProject.mutateAsync({ projectId: selectedProjectId, strategy })
       // Toast succès
     } catch (error) {
       // Toast erreur
     }
   }
   ```
3. UI :
   ```tsx
   <button onClick={() => handleSolve('cpsat')} disabled={solveProject.isLoading}>
     {solveProject.isLoading ? 'Calcul en cours...' : 'Recalculer (CP-SAT)'}
   </button>
   <button onClick={() => handleSolve('greedy')}>
     Recalculer (Greedy)
   </button>
   ```

**⚠️ Points d'attention** :
- Désactiver bouton pendant résolution (`isLoading`)
- Feedback visuel (spinner, toast)
- Invalider queries pour refetch automatique

**🧪 Validation** :
1. Fixer 2-3 matchs (via clic → modal Phase 4, ou API directe temporaire)
2. Cliquer "Recalculer"
3. Vérifier :
   - Bouton désactivé pendant calcul
   - Calendrier se rafraîchit après
   - Matchs fixes n'ont pas bougé
   - Autres matchs replanifiés

---

### VALIDATION GLOBALE PHASE 3

**🧪 Checklist de validation** :

1. **Solver avec matchs fixes** :
   - [ ] Fixer match via DB ou API
   - [ ] Lancer solver via API
   - [ ] Vérifier match fixé inchangé
   - [ ] Vérifier autres matchs planifiés sans conflit

2. **Semaine minimum** :
   - [ ] Setter `semaine_min=5` dans projet DB
   - [ ] Lancer solver
   - [ ] Vérifier aucun match avant semaine 5

3. **UI Solver** :
   - [ ] Bouton visible dans page calendrier
   - [ ] Cliquer → requête API POST /projects/{id}/solve
   - [ ] Loading state pendant calcul
   - [ ] Calendrier rafraîchi après

4. **Stratégies** :
   - [ ] Bouton CP-SAT fonctionne
   - [ ] Bouton Greedy fonctionne
   - [ ] Résultats différents selon stratégie

5. **Edge cases** :
   - [ ] Projet sans matchs → erreur propre
   - [ ] Tous matchs fixés → pas de changement
   - [ ] Semaine_min trop haute → matchs non planifiés

**❌ Critères d'échec** :
- Match fixé est replanifié
- Conflit (2 matchs même créneau)
- Solver plante
- Matchs planifiés avant semaine_min

---

## Résumé Commandes

### Backend

**Fichier** : `frontend/vite.config.ts`

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

### 2.2 Types TypeScript

**Fichier** : `frontend/src/types/match.ts`

```typescript
export interface Match {
  id: number
  project_id: number
  equipe1_nom: string
  equipe1_institution: string
  equipe1_genre: string
  equipe2_nom: string
  equipe2_institution: string
  equipe2_genre: string
  poule: string
  semaine: number | null
  horaire: string | null
  gymnase: string | null
  est_fixe: boolean
  statut: 'a_planifier' | 'planifie' | 'fixe' | 'termine' | 'annule'
  score_equipe1: number | null
  score_equipe2: number | null
  notes: string
  created_at: string
  updated_at: string | null
}

export interface MatchUpdate {
  semaine?: number
  horaire?: string
  gymnase?: string
  score_equipe1?: number
  score_equipe2?: number
  notes?: string
}
```

### 2.3 API Client

**Fichier** : `frontend/src/api/client.ts`

```typescript
import axios from 'axios'

export const apiClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})
```

**Fichier** : `frontend/src/api/endpoints/matches.ts`

```typescript
import { apiClient } from '../client'
import type { Match, MatchUpdate } from '@/types/match'

export const matchesApi = {
  list: async (projectId?: number): Promise<Match[]> => {
    const { data } = await apiClient.get('/matches/', {
      params: projectId ? { project_id: projectId } : {}
    })
    return data
  },
  
  get: async (id: number): Promise<Match> => {
    const { data } = await apiClient.get(`/matches/${id}`)
    return data
  },
  
  update: async (id: number, match: MatchUpdate): Promise<Match> => {
    const { data } = await apiClient.put(`/matches/${id}`, match)
    return data
  },
  
  move: async (id: number, creneau: { semaine: number; horaire: string; gymnase: string }): Promise<Match> => {
    const { data } = await apiClient.post(`/matches/${id}/move`, creneau)
    return data
  },
  
  fix: async (id: number): Promise<void> => {
    await apiClient.post(`/matches/${id}/fix`)
  },
  
  unfix: async (id: number): Promise<void> => {
    await apiClient.post(`/matches/${id}/unfix`)
  },
}
```

### 2.4 React Query Hooks

**Fichier** : `frontend/src/hooks/useMatches.ts`

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { matchesApi } from '@/api/endpoints/matches'
import type { MatchUpdate } from '@/types/match'

export function useMatches(projectId?: number) {
  return useQuery({
    queryKey: ['matches', projectId],
    queryFn: () => matchesApi.list(projectId),
    enabled: !!projectId,
  })
}

export function useUpdateMatch() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: MatchUpdate }) =>
      matchesApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['matches'] })
    },
  })
}

export function useMoveMatch() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, creneau }: { id: number; creneau: any }) =>
      matchesApi.move(id, creneau),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['matches'] })
    },
  })
}
```

### 2.5 Composant Calendrier

**Fichier** : `frontend/src/components/Calendar.tsx`

```typescript
import React from 'react'
import FullCalendar from '@fullcalendar/react'
import dayGridPlugin from '@fullcalendar/daygrid'
import timeGridPlugin from '@fullcalendar/timegrid'
import interactionPlugin from '@fullcalendar/interaction'
import type { Match } from '@/types/match'

interface Props {
  matches: Match[]
  onMatchDrop?: (matchId: number, creneau: any) => void
}

export function Calendar({ matches, onMatchDrop }: Props) {
  const events = matches
    .filter(m => m.semaine && m.horaire)
    .map(m => ({
      id: m.id.toString(),
      title: `${m.equipe1_nom} vs ${m.equipe2_nom}`,
      start: calculateDate(m.semaine!, m.horaire!),
      backgroundColor: m.est_fixe ? '#ef4444' : '#3b82f6',
      editable: !m.est_fixe,
      extendedProps: { match: m },
    }))
  
  return (
    <FullCalendar
      plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
      initialView="timeGridWeek"
      events={events}
      editable={true}
      eventDrop={(info) => {
        const match = info.event.extendedProps.match as Match
        const newDate = info.event.start!
        const creneau = {
          semaine: getWeekNumber(newDate),
          horaire: `${newDate.getHours()}:${newDate.getMinutes().toString().padStart(2, '0')}`,
          gymnase: match.gymnase || ''
        }
        onMatchDrop?.(match.id, creneau)
      }}
    />
  )
}

function calculateDate(semaine: number, horaire: string): Date {
  const [h, m] = horaire.split(':').map(Number)
  const date = new Date(2025, 0, 1)
  date.setDate(date.getDate() + (semaine - 1) * 7)
  date.setHours(h, m, 0)
  return date
}

function getWeekNumber(date: Date): number {
  const start = new Date(2025, 0, 1)
  const diff = date.getTime() - start.getTime()
  return Math.floor(diff / (7 * 24 * 60 * 60 * 1000)) + 1
}
```

### 2.6 Page Principale

**Fichier** : `frontend/src/App.tsx`

```typescript
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Calendar } from './components/Calendar'
import { useMatches, useMoveMatch } from './hooks/useMatches'

const queryClient = new QueryClient()

function CalendarPage() {
  const { data: matches } = useMatches(1) // TODO: project ID dynamique
  const moveMatch = useMoveMatch()
  
  const handleMatchDrop = async (matchId: number, creneau: any) => {
    try {
      await moveMatch.mutateAsync({ id: matchId, creneau })
    } catch (error) {
      console.error('Erreur:', error)
      alert('Impossible de déplacer le match')
    }
  }
  
  return (
    <div>
      <h1>Calendrier</h1>
      {matches && <Calendar matches={matches} onMatchDrop={handleMatchDrop} />}
    </div>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <CalendarPage />
    </QueryClientProvider>
  )
}
```

### Validation Phase 2

```bash
cd frontend
npm run dev
# Ouvrir http://localhost:5173
# Vérifier : calendrier s'affiche, drag & drop fonctionne
```

```bash
# Initialiser DB
python scripts/init_db.py

# Importer projet depuis Excel
python scripts/import_excel.py configs/config_volley.yaml "Volley 2025"

# Lancer API (dev mode avec hot reload)
uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000

# Tests unitaires
pytest tests/ -v --cov=backend --cov-report=html

# CLI existant (continue de fonctionner)
python main.py configs/config_volley.yaml
```

### Frontend
```bash
# Installer dépendances
cd frontend && npm install

# Dev mode avec hot reload
npm run dev

# Build production
npm run build

# Preview build
npm run preview

# Linting TypeScript
npm run lint

# Tests (si configurés)
npm run test
```

---

## Points Critiques à Surveiller

### 🔴 Critiques (Bloquants si non respectés)

1. **Matchs fixes immuables** :
   - TOUJOURS vérifier `match.est_modifiable()` avant update
   - Filtrer matchs fixes dans solvers AVANT résolution
   - Ne JAMAIS modifier `semaine/horaire/gymnase` si `est_fixe=True`

2. **Compatibilité backward** :
   - Valeurs par défaut obligatoires pour nouveaux champs `Match`
   - `semaine_min` optionnel avec default 1
   - Ne PAS modifier signatures existantes dans core/

3. **Transactions DB** :
   - TOUJOURS `db.commit()` après modifications
   - Utiliser try/except avec `db.rollback()` en cas d'erreur
   - Fermer sessions dans `finally` block

4. **Type safety frontend** :
   - Types TypeScript doivent matcher EXACTEMENT Pydantic schemas
   - Utiliser union types pour statuts (pas de strings libres)

### 🟡 Importants (Dégradent UX si non respectés)

5. **Invalidation cache React Query** :
   - Appeler `invalidateQueries()` après CHAQUE mutation réussie
   - queryKey cohérentes (`['matches', projectId]`)

6. **Gestion erreurs API** :
   - Try/catch autour de `mutateAsync()`
   - Feedback utilisateur (toast/alert) pour succès/échec
   - Status codes HTTP appropriés (404, 400, 201, 204)

7. **Logging** :
   - Logger début/fin résolution solver (avec durée)
   - Logger nombre matchs fixes/modifiables dans solver
   - Logger erreurs import Excel

### 🟢 Nice to have

8. **Performance** :
   - Indexes DB sur colonnes fréquemment queryées
   - Pagination API si >1000 matchs
   - Memoization React pour composants lourds

9. **Tests** :
   - Coverage >80% sur backend
   - Tests E2E Playwright pour flows critiques (Phase 4)

---

## Fichiers à Ne JAMAIS Modifier Directement

### ✅ Préserver tel quel
- `constraints/*.py` - Logique contraintes intacte
- `generators/*.py` - Génération matchs intacte
- `validation/*.py` - Validation solutions intacte
- `exporters/excel_exporter.py` - Export Excel intact
- `visualization/` - Ancien système HTML (peut coexister)
- `data/data_source.py` - Chargement Excel intact
- `orchestrator/pipeline.py` - Pipeline CLI intact

### ⚠️ Modifications minimales autorisées

**`solvers/cpsat_solver.py` et `greedy_solver.py`** :
- UNIQUEMENT ajout filtrage matchs fixes en DÉBUT de `solve()`
- UNIQUEMENT ajout filtrage semaine_min
- Ne PAS modifier logique CP-SAT/Greedy existante
- Ne PAS modifier signature méthodes

**`core/models.py`** :
- UNIQUEMENT ajout champs avec valeurs par défaut
- UNIQUEMENT ajout properties/méthodes
- Ne PAS modifier champs existants
- Ne PAS supprimer attributs

**`core/config.py`** :
- UNIQUEMENT ajout `semaine_min` avec default
- Ne PAS modifier champs existants

**`main.py`** :
- Aucune modification requise
- Doit continuer à fonctionner identiquement

---

## Dépendances à Ajouter

### Backend (`requirements.txt` ou `pyproject.toml`)

```txt
# Existantes (ne pas toucher)
pandas>=2.0.0
openpyxl>=3.1.0
pyyaml>=6.0
ortools>=9.7.0

# NOUVELLES pour Phase 1
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
sqlalchemy>=2.0.0
pydantic>=2.0.0
pydantic-settings>=2.0.0

# Tests
pytest>=7.4.0
pytest-cov>=4.1.0
httpx>=0.25.0  # Pour TestClient FastAPI
```

### Frontend (`package.json`)

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "@tanstack/react-query": "^5.0.0",
    "axios": "^1.6.0",
    "zustand": "^4.4.0",
    "@fullcalendar/react": "^6.1.0",
    "@fullcalendar/daygrid": "^6.1.0",
    "@fullcalendar/timegrid": "^6.1.0",
    "@fullcalendar/interaction": "^6.1.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@vitejs/plugin-react": "^4.2.0",
    "typescript": "^5.3.0",
    "vite": "^5.0.0",
    "tailwindcss": "^3.4.0"
  }
}
```

---

## Vérifications Pre-Commit

Avant chaque commit, vérifier :

### Backend
```bash
# Tests passent
pytest tests/ -v

# CLI fonctionne
python main.py configs/config_volley.yaml

# API démarre
uvicorn backend.api.main:app --reload &
curl http://localhost:8000/health
# Tuer le serveur après
```

### Frontend
```bash
# TypeScript compile
cd frontend && npm run build

# Pas d'erreurs lint
npm run lint
```

### Intégration
```bash
# Workflow complet
python scripts/init_db.py
python scripts/import_excel.py configs/config_volley.yaml "Test"
# Lancer API + Frontend
# Vérifier calendrier affiche matchs
# Drag & drop fonctionne
# Bouton solver fonctionne
```

---

## Checklist Mise en Production (Post Phase 3)

- [ ] Remplacer SQLite par PostgreSQL
- [ ] Variables d'environnement pour secrets (pas de hardcode)
- [ ] CORS origins restreintes (pas `*`)
- [ ] HTTPS obligatoire
- [ ] Rate limiting sur endpoints
- [ ] Logs structurés (JSON)
- [ ] Monitoring (Sentry, DataDog, etc.)
- [ ] Backup DB automatique
- [ ] Tests E2E passent
- [ ] Documentation API à jour (Swagger)
- [ ] README.md avec instructions déploiement

---

## Troubleshooting Courant

### Erreur : "Foreign key constraint failed"
**Cause** : SQLite foreign keys non activées
**Fix** : Vérifier `event.listen` dans `engine.py` exécute `PRAGMA foreign_keys=ON`

### Erreur : "Match fixé a été replanifié"
**Cause** : Solver ne filtre pas matchs fixes
**Fix** : Vérifier logique filtrage en début de `solve()` dans solver

### Erreur : "CORS policy blocking"
**Cause** : Frontend et backend sur origins différents
**Fix** : Vérifier middleware CORS dans `main.py` inclut origin frontend

### Erreur : "React Query ne rafraîchit pas"
**Cause** : Manque `invalidateQueries` après mutation
**Fix** : Ajouter dans `onSuccess` de chaque mutation

### Erreur : "Import Excel échoue"
**Cause** : Chemin fichier Excel incorrect ou format invalide
**Fix** : Vérifier `config.fichier_donnees` pointe vers fichier existant

### Performance : "Solver trop lent"
**Solutions** :
- Réduire `nb_semaines`
- Réduire timeout CP-SAT
- Utiliser Greedy si >100 matchs
- Background task avec WebSocket notification (Phase 4)

---

## Phases Futures (Post Phase 3)

### Phase 4 : Features Avancées (2 semaines)
- Undo/Redo pour opérations UI
- Modal détail match avec édition scores
- Tableau classements auto-calculés
- Export Excel depuis DB
- WebSocket pour notifications solver
- Authentification basique

### Phase 5 : Analytics (2 semaines)
- Dashboard pénalités détaillé
- Graphiques statistiques (Recharts)
- Comparaison solutions (CP-SAT vs Greedy)
- Historique modifications

### Phase 6 : Multi-Sport & Déploiement (2 semaines)
- Sélection projet dynamique
- Support handball/basket/etc.
- Docker compose (backend + frontend + PostgreSQL)
- Déploiement Railway/Render/Fly.io
- CI/CD GitHub Actions

---

## Contact & Support

Pour questions techniques sur l'implémentation :
1. Vérifier cette documentation
2. Consulter Swagger API : `http://localhost:8000/docs`
3. Consulter logs backend/frontend
4. Reproduire en test unitaire isolé
