# 🏗️ Architecture PyCalendar - Vision Complète

## 📋 Table des Matières

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture Actuelle](#architecture-actuelle)
3. [Architecture Cible](#architecture-cible)
4. [Migration Progressive](#migration-progressive)
5. [Structure des Données](#structure-des-données)
6. [Flux de Données](#flux-de-données)
7. [Décisions Techniques](#décisions-techniques)

---

## 🎯 Vue d'ensemble

PyCalendar évolue d'un **système CLI/Excel** vers une **application web full-stack** tout en préservant :
- ✅ Toute la logique métier existante (solvers, contraintes, validations)
- ✅ L'interface HTML actuelle (mode lecture)
- ✅ La compatibilité avec les fichiers Excel existants
- ✅ Les configurations YAML

**Objectif** : Ajouter une interface web interactive pour la gestion et l'édition des calendriers.

---

## 📂 Architecture Actuelle (V1 - CLI)

```
PyCalendar/
├── core/                   # ⚙️ Modèles et configuration
│   ├── models.py          # Equipe, Match, Gymnase, Solution, Creneau
│   ├── config.py          # Gestion config YAML
│   ├── config_manager.py  # Lecture Excel (config centrale)
│   └── solution_store.py  # Sauvegarde solutions (warm start)
│
├── data/                   # 📊 Chargement données
│   ├── data_source.py     # Lecture Excel
│   ├── validators.py      # Validation données
│   └── transformers.py    # Transformation données
│
├── constraints/            # 🔒 Système de contraintes
│   ├── base.py            # Interface Constraint
│   ├── team_constraints.py
│   ├── venue_constraints.py
│   ├── schedule_constraints.py
│   └── institution_constraints.py
│
├── solvers/                # 🧠 Algorithmes de résolution
│   ├── base_solver.py     # Interface BaseSolver
│   ├── cpsat_solver.py    # OR-Tools CP-SAT (optimal)
│   └── greedy_solver.py   # Greedy (rapide)
│
├── generators/             # 🎲 Génération matchs
│   └── multi_pool_generator.py
│
├── validation/             # ✅ Validation solutions
│   └── solution_validator.py
│
├── exporters/              # 📤 Export résultats
│   └── excel_exporter.py
│
├── visualization/          # 🎨 Visualisation HTML (V1)
│   ├── html_visualizer_v2.py
│   ├── templates/
│   └── components/
│
├── orchestrator/           # 🎭 Pipeline principal
│   └── pipeline.py        # SchedulingPipeline
│
├── configs/                # ⚙️ Configurations
│   ├── default.yaml
│   ├── config_volley.yaml
│   └── config_hand.yaml
│
└── main.py                 # 🚀 Point d'entrée CLI
```

### Flux Actuel (CLI)

```
1. main.py
   ↓
2. Config.from_yaml() → Charge config
   ↓
3. SchedulingPipeline.run()
   ↓
4. DataSource.charger_equipes/gymnases() → Lit Excel
   ↓
5. MultiPoolGenerator.generer_matchs() → Crée matchs
   ↓
6. CPSATSolver.solve() → Planifie
   ↓
7. SolutionValidator.validate() → Valide
   ↓
8. ExcelExporter.export() → Excel
   HTMLVisualizerV2.generate() → HTML
```

---

## 🎯 Architecture Cible (V2 - Web)

```
PyCalendar/
├── backend/                    # 🔧 API FastAPI (NOUVEAU)
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py            # Point d'entrée FastAPI
│   │   ├── dependencies.py    # Dépendances (DB session, auth, etc.)
│   │   └── routes/
│   │       ├── projects.py    # CRUD projets
│   │       ├── matches.py     # CRUD matchs (+ drag&drop, swap, etc.)
│   │       ├── teams.py       # CRUD équipes
│   │       ├── venues.py      # CRUD gymnases
│   │       ├── solver.py      # Endpoints pour lancer les solvers
│   │       ├── constraints.py # Analyse contraintes/pénalités
│   │       └── export.py      # Export Excel/iCal
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── engine.py          # Config SQLAlchemy
│   │   ├── models.py          # Modèles SQLAlchemy (DB)
│   │   └── repositories.py    # Couche d'accès données
│   │
│   ├── services/              # Logique métier
│   │   ├── project_service.py
│   │   ├── match_service.py   # Logique édition matchs
│   │   ├── solver_service.py  # Interface avec solvers
│   │   ├── constraint_service.py
│   │   └── sync_service.py    # Sync Excel ↔ DB
│   │
│   └── schemas/               # Pydantic schemas (validation API)
│       ├── project.py
│       ├── match.py
│       ├── team.py
│       └── venue.py
│
├── frontend/                   # 🎨 Interface React (NOUVEAU)
│   ├── public/
│   ├── src/
│   │   ├── api/               # Client API
│   │   │   ├── client.ts
│   │   │   └── endpoints/
│   │   │       ├── matches.ts
│   │   │       ├── projects.ts
│   │   │       └── solver.ts
│   │   │
│   │   ├── components/        # Composants réutilisables
│   │   │   ├── ui/           # shadcn/ui components
│   │   │   ├── calendar/
│   │   │   │   ├── Calendar.tsx
│   │   │   │   ├── MatchCard.tsx
│   │   │   │   └── DragDropMatch.tsx
│   │   │   ├── tables/
│   │   │   │   ├── PoolTable.tsx
│   │   │   │   └── StandingsTable.tsx
│   │   │   └── forms/
│   │   │       ├── MatchForm.tsx
│   │   │       └── ScoreForm.tsx
│   │   │
│   │   ├── pages/             # Pages principales
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Calendar.tsx
│   │   │   ├── Pools.tsx
│   │   │   ├── Penalties.tsx
│   │   │   └── Settings.tsx
│   │   │
│   │   ├── hooks/             # Custom hooks
│   │   │   ├── useMatches.ts
│   │   │   ├── useSolver.ts
│   │   │   └── useConstraints.ts
│   │   │
│   │   ├── store/             # État global (Zustand)
│   │   │   ├── matchStore.ts
│   │   │   ├── filterStore.ts
│   │   │   └── uiStore.ts
│   │   │
│   │   ├── types/             # Types TypeScript
│   │   │   ├── match.ts
│   │   │   ├── team.ts
│   │   │   └── venue.ts
│   │   │
│   │   ├── utils/             # Utilitaires
│   │   │   ├── validation.ts
│   │   │   └── formatting.ts
│   │   │
│   │   ├── App.tsx
│   │   └── main.tsx
│   │
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
│
├── core/                       # ⚙️ Logique métier (CONSERVÉ + AMÉLIORÉ)
│   ├── models.py              # AMÉLIORÉ : Pydantic + méthodes helper
│   ├── config.py
│   ├── config_manager.py
│   └── solution_store.py
│
├── [constraints, solvers, generators, validation]  # CONSERVÉS
│
├── data/                       # 📊 Chargement données (CONSERVÉ)
│   └── [fichiers existants]
│
├── exporters/                  # 📤 Export (CONSERVÉ + AMÉLIORÉ)
│   ├── excel_exporter.py
│   └── ical_exporter.py       # NOUVEAU pour Google Calendar
│
├── visualization/              # 🎨 HTML statique (CONSERVÉ)
│   └── [fichiers existants]  # Mode lecture uniquement
│
├── tests/                      # 🧪 Tests (NOUVEAU)
│   ├── unit/
│   │   ├── test_models.py
│   │   ├── test_constraints.py
│   │   ├── test_solvers.py
│   │   └── test_services.py
│   ├── integration/
│   │   ├── test_api.py
│   │   └── test_solver_integration.py
│   └── conftest.py
│
├── migrations/                 # 🗄️ Migrations DB (NOUVEAU)
│   └── versions/
│
├── docker/                     # 🐳 Déploiement (NOUVEAU)
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── docker-compose.yml
│
├── scripts/                    # 🛠️ Scripts utilitaires (NOUVEAU)
│   ├── init_db.py
│   ├── migrate_excel_to_db.py
│   └── seed_test_data.py
│
├── main.py                     # 🚀 CLI (CONSERVÉ)
└── requirements.txt            # + ajouts (fastapi, sqlalchemy, etc.)
```

---

## 🔄 Migration Progressive

### Phase 1 : Backend Foundation (Semaines 1-2)
**Objectif** : API fonctionnelle qui lit/écrit les données

**Création** :
- `backend/` avec structure complète
- `backend/database/models.py` : Modèles SQLAlchemy
- `backend/api/routes/` : CRUD de base
- `backend/services/sync_service.py` : Import Excel → DB

**Conservation** :
- Tout le code existant fonctionne toujours
- `main.py` continue de fonctionner normalement

**Test** : `pytest tests/unit/test_models.py`

### Phase 2 : Frontend Foundation (Semaines 3-4)
**Objectif** : Interface qui affiche les données

**Création** :
- `frontend/` avec React + Vite
- Composants de visualisation (lecture seule)
- Appels API pour récupérer données

**Conservation** :
- `visualization/` continue de générer HTML statique
- Les deux interfaces coexistent

**Test** : Interface affiche calendrier existant

### Phase 3 : Édition Interactive (Semaines 5-6)
**Objectif** : Drag & drop, édition matchs

**Ajout** :
- Drag & drop dans frontend
- Endpoints API pour modifications
- Validation contraintes en temps réel

**Conservation** :
- Logique de validation reste dans `constraints/`
- Solvers pas touchés

**Test** : Déplacer un match, vérifier contraintes

### Phase 4 : Solver Integration (Semaines 7-8)
**Objectif** : Lancer solvers depuis l'interface

**Ajout** :
- Endpoint `/api/solve`
- Interface de configuration solver
- Affichage progression

**Conservation** :
- `solvers/cpsat_solver.py` et `greedy_solver.py` inchangés
- Juste appelés via API

### Phase 5 : Features Avancées (Semaines 9-10)
**Objectif** : Scores, analytics, multi-sports

**Ajout** :
- Gestion scores et classements
- Dashboard analytics pénalités
- Support multi-projets

---

## 📊 Structure des Données

### Modèles Core (Python - `core/models.py`)

```python
# DÉJÀ EXISTANT (avec améliorations)
@dataclass
class Equipe:
    nom: str
    poule: str
    institution: str
    # ... existant

@dataclass
class Match:
    equipe1: Equipe
    equipe2: Equipe
    creneau: Optional[Creneau]
    est_fixe: bool = False      # ✅ Déjà ajouté
    statut: str = "a_planifier" # ✅ Déjà ajouté
    score_equipe1: Optional[int] = None  # ✅ Déjà ajouté
    score_equipe2: Optional[int] = None  # ✅ Déjà ajouté
    # ... existant
```

### Modèles Database (SQLAlchemy - `backend/database/models.py`)

```python
# NOUVEAU - Mapping vers BDD
class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True)
    nom = Column(String, nullable=False)
    sport = Column(String)
    config_yaml = Column(Text)  # Stocke le YAML
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    matches = relationship("Match", back_populates="project")

class Match(Base):
    __tablename__ = "matches"
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    
    # Données du match
    equipe1_nom = Column(String)
    equipe2_nom = Column(String)
    poule = Column(String)
    
    # Planification
    semaine = Column(Integer, nullable=True)
    horaire = Column(String, nullable=True)
    gymnase = Column(String, nullable=True)
    
    # Statut et contraintes
    est_fixe = Column(Boolean, default=False)
    statut = Column(String, default="a_planifier")
    
    # Scores
    score_equipe1 = Column(Integer, nullable=True)
    score_equipe2 = Column(Integer, nullable=True)
    
    # Métadonnées
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    # Relations
    project = relationship("Project", back_populates="matches")
```

### Schémas API (Pydantic - `backend/schemas/match.py`)

```python
# NOUVEAU - Validation API
class MatchBase(BaseModel):
    equipe1_nom: str
    equipe2_nom: str
    poule: str
    semaine: Optional[int] = None
    horaire: Optional[str] = None
    gymnase: Optional[str] = None
    est_fixe: bool = False
    statut: str = "a_planifier"

class MatchCreate(MatchBase):
    project_id: int

class MatchUpdate(BaseModel):
    semaine: Optional[int] = None
    horaire: Optional[str] = None
    gymnase: Optional[str] = None
    score_equipe1: Optional[int] = None
    score_equipe2: Optional[int] = None
    notes: Optional[str] = None
    statut: Optional[str] = None

class MatchResponse(MatchBase):
    id: int
    project_id: int
    score_equipe1: Optional[int]
    score_equipe2: Optional[int]
    notes: str
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True
```

---

## 🔄 Flux de Données

### Flux 1 : Import Excel → DB → Interface

```
1. Excel (config_exemple.xlsx)
   ↓
2. backend/services/sync_service.py
   - Lit Excel avec data/data_source.py
   - Crée objets core/models.py
   - Sauvegarde dans DB (backend/database/models.py)
   ↓
3. backend/api/routes/matches.py
   - Endpoint GET /api/projects/{id}/matches
   - Retourne JSON
   ↓
4. frontend/api/endpoints/matches.ts
   - Récupère JSON
   ↓
5. frontend/components/calendar/Calendar.tsx
   - Affiche dans FullCalendar
```

### Flux 2 : Édition Match dans Interface → DB → Validation

```
1. frontend/components/calendar/Calendar.tsx
   - User drag & drop un match
   - Capture nouveau créneau
   ↓
2. frontend/api/endpoints/matches.ts
   - PUT /api/matches/{id}
   - Envoie nouveau créneau
   ↓
3. backend/api/routes/matches.py
   - Reçoit requête
   ↓
4. backend/services/match_service.py
   - Valide le déplacement
   - Appelle constraints/ pour vérifier
   ↓
5. constraints/base.py (CODE EXISTANT)
   - Valide contraintes
   - Retourne violations
   ↓
6. backend/services/match_service.py
   - Si OK : Sauvegarde en DB
   - Si KO : Retourne erreur 400
   ↓
7. frontend
   - Si OK : Met à jour affichage
   - Si KO : Affiche erreur, annule déplacement
```

### Flux 3 : Lancer Solver depuis Interface

```
1. frontend/pages/Calendar.tsx
   - Click bouton "Recalculer"
   - Sélectionne stratégie (cpsat/greedy)
   ↓
2. frontend/api/endpoints/solver.ts
   - POST /api/projects/{id}/solve
   - Body: {strategy: "cpsat", nb_semaines: 10}
   ↓
3. backend/api/routes/solver.py
   - Reçoit requête
   - Lance tâche asynchrone (Celery ou background task)
   ↓
4. backend/services/solver_service.py
   - Récupère données du projet (DB)
   - Convertit en core/models.py
   - Appelle solvers/cpsat_solver.py (CODE EXISTANT)
   ↓
5. solvers/cpsat_solver.py (CODE EXISTANT)
   - Résout le problème
   - Retourne Solution
   ↓
6. backend/services/solver_service.py
   - Sauvegarde Solution en DB
   - Envoie notification WebSocket (progression)
   ↓
7. frontend
   - Reçoit notification
   - Recharge matchs
   - Affiche nouveau calendrier
```

---

## 🔧 Décisions Techniques

### Base de Données

**Choix** : SQLite en dev → PostgreSQL en prod

**Raisons** :
- SQLite : Facile setup, pas de serveur, parfait pour dev/test
- PostgreSQL : Production-ready, support JSON, performances

**Migration** : Transparent avec SQLAlchemy, juste changer l'URL

### Backend API

**Choix** : FastAPI

**Raisons** :
- ✅ Python (garde ton code)
- ✅ Async natif (performance)
- ✅ Validation automatique (Pydantic)
- ✅ Doc auto-générée (Swagger UI)
- ✅ WebSockets intégrés (notifications temps réel)

### Frontend

**Choix** : React + TypeScript + Vite

**Raisons** :
- ✅ Écosystème riche (FullCalendar, AG Grid, etc.)
- ✅ TypeScript = typage = moins de bugs
- ✅ Vite = build ultra rapide
- ✅ Composants réutilisables

### Gestion État

**Choix** : TanStack Query + Zustand

**Raisons** :
- **TanStack Query** : Gestion état serveur (cache, revalidation auto)
- **Zustand** : État local simple (filtres UI, sélections)

### Calendrier

**Choix** : FullCalendar

**Raisons** :
- ✅ Drag & drop natif
- ✅ Vues multiples (semaine/mois/timeline)
- ✅ Responsive
- ✅ Événements étendus

### Tests

**Choix** : pytest (backend) + Vitest (frontend)

**Raisons** :
- pytest : Standard Python, fixtures puissantes
- Vitest : Compatible Vite, rapide

---

## 🔒 Gestion des Matchs Fixes

### Concept

**Matchs fixes** = Matchs déjà programmés qui ne doivent PAS être modifiés par le solver

### Implémentation

1. **Marquage** : `match.est_fixe = True` ou `match.statut = "fixe"`

2. **Dans le Solver** (`solvers/cpsat_solver.py`) :
```python
def solve(self, matchs, creneaux, ...):
    # Séparer matchs fixes et modifiables
    matchs_fixes = [m for m in matchs if m.est_fixe or m.statut == "fixe"]
    matchs_modifiables = [m for m in matchs if m.est_modifiable()]
    
    # Réserver les créneaux des matchs fixes
    creneaux_reserves = {m.creneau for m in matchs_fixes if m.creneau}
    creneaux_disponibles = [c for c in creneaux if c not in creneaux_reserves]
    
    # Résoudre uniquement pour matchs_modifiables
    solution = self._solve_internal(matchs_modifiables, creneaux_disponibles)
    
    # Fusionner avec matchs fixes
    solution.matchs_planifies += matchs_fixes
    
    return solution
```

3. **Dans l'Interface** :
- Bouton "🔒 Fixer ce match"
- Matchs fixes affichés avec icône cadenas
- Drag & drop désactivé pour matchs fixes

### Semaine Minimum

**Concept** : Ne pas planifier avant une semaine donnée (ex: semaines 1-2 déjà passées)

**Implémentation** :
```python
# Dans config
planification:
  semaine_min: 3  # Ne planifier qu'à partir de la semaine 3

# Dans solver
creneaux_valides = [c for c in creneaux if c.semaine >= config.semaine_min]
```

---

## 📈 Évolution Future

### Court Terme (Phases 1-3)
- ✅ API + DB
- ✅ Interface lecture
- ✅ Édition matchs

### Moyen Terme (Phases 4-5)
- ✅ Solver intégré
- ✅ Analytics pénalités
- ✅ Multi-projets

### Long Terme
- 🔐 Authentification multi-utilisateurs
- 📱 Application mobile
- 🔔 Notifications équipes
- 📊 Prédictions IA (suggestions optimisation)
- 🌍 Déploiement cloud

---

## 🎯 Compatibilité Ascendante

**Garanties** :
- ✅ `main.py` continue de fonctionner (CLI)
- ✅ Fichiers Excel compatibles
- ✅ Configs YAML compatibles
- ✅ HTML statique toujours généré
- ✅ Solvers pas modifiés (juste appelés différemment)

**Nouvelle Interface** = Couche supplémentaire, pas remplacement
