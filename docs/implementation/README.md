# 📚 Documentation d'Implémentation PyCalendar V2

## Structure de la Documentation

Cette documentation détaille l'implémentation complète de PyCalendar V2, organisée en phases progressives.

### 📁 Organisation

```
docs/
├── ARCHITECTURE.md              # Architecture globale (voir racine projet)
├── PLAN_IMPLEMENTATION.md       # Plan général (voir racine projet)
│
└── implementation/
    ├── README.md                # Ce fichier - Index
    │
    ├── phase1/                  # Phase 1 : Backend Foundation
    │   ├── 01_setup_fastapi.md
    │   ├── 02_database_models.md
    │   ├── 03_api_routes.md
    │   ├── 04_sync_service.md
    │   └── 05_tests.md
    │
    ├── phase2/                  # Phase 2 : Frontend Foundation
    │   ├── 01_setup_react.md
    │   ├── 02_api_client.md
    │   ├── 03_components.md
    │   ├── 04_calendar.md
    │   └── 05_routing.md
    │
    ├── phase3/                  # Phase 3 : Édition Interactive
    │   ├── 01_drag_drop.md
    │   ├── 02_validation.md
    │   ├── 03_undo_redo.md
    │   └── 04_match_operations.md
    │
    ├── phase4/                  # Phase 4 : Solver Integration
    │   ├── 01_solver_api.md
    │   ├── 02_async_tasks.md
    │   └── 03_progress_tracking.md
    │
    ├── phase5/                  # Phase 5 : Features Avancées
    │   ├── 01_scores_classements.md
    │   ├── 02_analytics.md
    │   ├── 03_multi_projets.md
    │   └── 04_exports.md
    │
    └── phase6/                  # Phase 6 : Déploiement
        ├── 01_docker.md
        ├── 02_ci_cd.md
        └── 03_production.md
```

---

## 🚀 Comment Utiliser cette Documentation

### Pour Développeurs Humains

1. **Commencer par** :
   - Lire `../../ARCHITECTURE.md` pour comprendre la vision globale
   - Lire `../../PLAN_IMPLEMENTATION.md` pour le planning

2. **Phase par phase** :
   - Suivre les guides dans l'ordre numérique
   - Valider chaque étape avant de passer à la suivante
   - Exécuter les tests à chaque fin de guide

3. **Référence** :
   - Utiliser les guides comme référence pendant le développement
   - Copier-coller les exemples de code
   - Adapter selon besoins spécifiques

### Pour Agents IA

**Format de requête optimal** :
```
Agent, implémente la Phase 1, Étape 1 selon le guide 
docs/implementation/phase1/01_setup_fastapi.md
```

**Bonnes pratiques** :
- Une session = un guide complet
- Valider après chaque guide
- Commiter avec message clair
- Tester avant de passer au suivant

---

## 📅 Planning de Lecture Recommandé

### Semaine 1 : Backend Foundation (Phase 1)
- **Jour 1-2** : `phase1/01_setup_fastapi.md` + `phase1/02_database_models.md`
- **Jour 3** : `phase1/03_api_routes.md`
- **Jour 4** : `phase1/04_sync_service.md`
- **Jour 5** : `phase1/05_tests.md` + Validation complète

### Semaine 2 : Backend Foundation (Suite)
- **Jour 1-2** : Finalisation Phase 1, correction bugs
- **Jour 3-5** : Documentation code, refactoring, optimisations

### Semaine 3 : Frontend Foundation (Phase 2)
- **Jour 1** : `phase2/01_setup_react.md`
- **Jour 2** : `phase2/02_api_client.md`
- **Jour 3** : `phase2/03_components.md`
- **Jour 4** : `phase2/04_calendar.md`
- **Jour 5** : `phase2/05_routing.md` + Validation

### Semaine 4 : Frontend Foundation (Suite)
- **Jour 1-3** : Finalisation composants, styling
- **Jour 4-5** : Tests, responsive, accessibilité

### Semaine 5-6 : Édition Interactive (Phase 3)
- À détailler dans les guides Phase 3

### Semaine 7-8 : Solver Integration (Phase 4)
- À détailler dans les guides Phase 4

### Semaine 9-10 : Features Avancées (Phase 5)
- À détailler dans les guides Phase 5

### Semaine 11-12 : Déploiement (Phase 6)
- À détailler dans les guides Phase 6

---

## 🎯 Objectifs par Phase

### Phase 1 : Backend Foundation ✅
**Objectif** : API REST complète et fonctionnelle

**Livrables** :
- ✅ FastAPI configuré et running
- ✅ Base de données SQLite avec tables
- ✅ Modèles SQLAlchemy + Pydantic schemas
- ✅ API CRUD pour Projects, Matches, Teams, Venues
- ✅ Service synchronisation Excel → DB
- ✅ Tests unitaires (>80% coverage)

**Validation** : API accessible, Swagger UI complet, tests passent

---

### Phase 2 : Frontend Foundation 🎨
**Objectif** : Interface de visualisation interactive

**Livrables** :
- ✅ React + TypeScript + Vite configuré
- ✅ Client API TypeScript
- ✅ Composants UI de base (shadcn/ui)
- ✅ Calendrier FullCalendar intégré
- ✅ Pages et routing
- ✅ Gestion état (TanStack Query + Zustand)

**Validation** : Interface affiche calendrier, filtres fonctionnent

---

### Phase 3 : Édition Interactive ✏️
**Objectif** : Manipulation des matchs en temps réel

**Livrables** :
- ✅ Drag & drop de matchs
- ✅ Validation contraintes temps réel
- ✅ Undo/Redo
- ✅ Swap de matchs
- ✅ Fixation/Dé-fixation matchs
- ✅ Annulation matchs

**Validation** : Drag & drop fluide, contraintes validées, feedback visuel

---

### Phase 4 : Solver Integration 🧠
**Objectif** : Lancer solvers depuis interface

**Livrables** :
- ✅ Endpoint `/api/solve` asynchrone
- ✅ WebSocket pour progression
- ✅ Interface configuration solver
- ✅ Comparaison solutions
- ✅ Suggestions optimisation

**Validation** : Solver lance depuis UI, progression visible

---

### Phase 5 : Features Avancées 📊
**Objectif** : Fonctionnalités métier avancées

**Livrables** :
- ✅ Gestion scores
- ✅ Classements automatiques
- ✅ Dashboard analytics pénalités
- ✅ Support multi-projets
- ✅ Export iCal/PDF

**Validation** : Scores enregistrés, classements calculés, analytics détaillées

---

### Phase 6 : Déploiement 🚀
**Objectif** : Production-ready

**Livrables** :
- ✅ Dockerisation complète
- ✅ CI/CD GitHub Actions
- ✅ Tests E2E
- ✅ Documentation utilisateur
- ✅ Monitoring et logs

**Validation** : Déployé en production, accessible en ligne

---

## 🔗 Liens Rapides

### Documentation Principale
- [Architecture Globale](../../ARCHITECTURE.md)
- [Plan d'Implémentation](../../PLAN_IMPLEMENTATION.md)
- [README Projet](../../README.md)

### Guides Phase 1 (Backend)
- [1.1 Setup FastAPI](phase1/01_setup_fastapi.md)
- [1.2 Database Models](phase1/02_database_models.md)
- [1.3 API Routes](phase1/03_api_routes.md)
- [1.4 Sync Service](phase1/04_sync_service.md)
- [1.5 Tests](phase1/05_tests.md)

### Guides Phase 2 (Frontend)
- [2.1 Setup React](phase2/01_setup_react.md)
- [2.2 API Client](phase2/02_api_client.md)
- [2.3 Components](phase2/03_components.md)
- [2.4 Calendar](phase2/04_calendar.md)
- [2.5 Routing](phase2/05_routing.md)

### Guides Phase 3 (Édition)
- [3.1 Drag & Drop](phase3/01_drag_drop.md)
- [3.2 Validation](phase3/02_validation.md)
- [3.3 Undo/Redo](phase3/03_undo_redo.md)
- [3.4 Match Operations](phase3/04_match_operations.md)

---

## 📝 Conventions

### Conventions de Code

**Python (Backend)** :
- PEP 8 strict
- Type hints obligatoires
- Docstrings Google style
- Tests unitaires pour chaque fonction publique

**TypeScript (Frontend)** :
- ESLint + Prettier
- Types stricts (no `any`)
- JSDoc pour fonctions complexes
- Composants fonctionnels avec hooks

### Conventions Git

**Commits** :
```
<type>(<scope>): <description>

Types: feat, fix, docs, style, refactor, test, chore
Scopes: backend, frontend, docs, tests, config

Exemples:
feat(backend): Add Match API routes
fix(frontend): Fix calendar drag and drop
docs(phase1): Update setup guide
test(backend): Add Match model tests
```

**Branches** :
```
main                    # Production
develop                 # Développement
feature/phase1-backend  # Features par phase
feature/phase2-frontend
hotfix/fix-api-bug     # Corrections urgentes
```

### Conventions de Nommage

**Fichiers** :
- Python : `snake_case.py`
- TypeScript : `PascalCase.tsx` (composants), `camelCase.ts` (utils)
- Markdown : `kebab-case.md`

**Variables** :
- Python : `snake_case`
- TypeScript : `camelCase`
- Constantes : `UPPER_SNAKE_CASE`

**Classes** :
- Python : `PascalCase`
- TypeScript : `PascalCase`

---

## 🛠️ Commandes Essentielles

### Vérification Rapide

```bash
# Backend
cd /home/vincheetah/Documents/Travail/FFSU/PyCalendar
python -m pytest tests/ -v
uvicorn backend.api.main:app --reload

# Frontend
cd frontend
npm run type-check
npm run lint
npm run dev

# Full Stack
# Terminal 1: Backend
uvicorn backend.api.main:app --reload

# Terminal 2: Frontend
cd frontend && npm run dev
```

### Initialisation Projet

```bash
# Première fois
python scripts/init_db.py
python scripts/import_excel.py configs/config_volley.yaml "Test"

# Frontend
cd frontend
npm install
npm run dev
```

---

## 🆘 Troubleshooting

### Backend ne démarre pas
1. Vérifier `.venv` activé : `source .venv/bin/activate`
2. Vérifier dépendances : `pip install -r requirements.txt`
3. Vérifier DB existe : `ls database/pycalendar.db`

### Frontend ne démarre pas
1. Vérifier Node.js : `node --version` (>= 18.0.0)
2. Réinstaller dépendances : `rm -rf node_modules && npm install`
3. Vérifier port libre : `lsof -i :5173`

### Erreurs CORS
- Vérifier proxy Vite : `vite.config.ts`
- Vérifier CORS FastAPI : `backend/api/main.py`

### Erreurs DB
- Supprimer DB : `rm database/pycalendar.db`
- Recréer : `python scripts/init_db.py`
- Réimporter : `python scripts/import_excel.py ...`

---

## 🎓 Ressources Complémentaires

### Technologies Utilisées

**Backend** :
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
- [Pydantic Docs](https://docs.pydantic.dev/)
- [Pytest Docs](https://docs.pytest.org/)

**Frontend** :
- [React Docs](https://react.dev/)
- [TypeScript Docs](https://www.typescriptlang.org/docs/)
- [FullCalendar Docs](https://fullcalendar.io/docs)
- [TanStack Query Docs](https://tanstack.com/query/latest)
- [Zustand Docs](https://zustand-demo.pmnd.rs/)
- [shadcn/ui Docs](https://ui.shadcn.com/)

### Tutoriels Recommandés

- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)
- [React + TypeScript](https://react-typescript-cheatsheet.netlify.app/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/20/orm/)

---

## 📞 Contact et Support

### Questions sur l'Implémentation
- Consulter les guides détaillés dans `phase*/`
- Vérifier les exemples de code
- Tester avec données de test

### Contributions
- Suivre les conventions de code
- Ajouter tests pour nouvelles features
- Mettre à jour la documentation

---

## 🎯 Prochaines Étapes

### Pour Commencer Immédiatement

1. **Lire l'architecture** :
   ```bash
   cat ../../ARCHITECTURE.md
   ```

2. **Lire le plan global** :
   ```bash
   cat ../../PLAN_IMPLEMENTATION.md
   ```

3. **Commencer Phase 1** :
   ```bash
   cat phase1/01_setup_fastapi.md
   ```

4. **Ou utiliser un agent IA** :
   ```
   Agent, implémente docs/implementation/phase1/01_setup_fastapi.md
   ```

---

## 📊 Progression Globale

```
Phase 1 : Backend Foundation        [ ] 0%   ███████░░░░░░░
Phase 2 : Frontend Foundation       [ ] 0%   ░░░░░░░███████░
Phase 3 : Édition Interactive       [ ] 0%   ░░░░░░░░░░████░
Phase 4 : Solver Integration        [ ] 0%   ░░░░░░░░░░░░███
Phase 5 : Features Avancées         [ ] 0%   ░░░░░░░░░░░░░██
Phase 6 : Déploiement              [ ] 0%   ░░░░░░░░░░░░░██
```

**Durée totale estimée** : 10-12 semaines  
**Effort** : ~40h/semaine  
**Date de début prévue** : À définir  
**Date de fin prévue** : À définir

---

**Bonne chance ! 🚀**
