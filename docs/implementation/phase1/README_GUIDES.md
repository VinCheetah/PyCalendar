# 📚 Phase 1 - Guides Restants (Résumé)

Les guides complets **Phase 1.3 (API Routes)**, **Phase 1.4 (Sync Service)** et **Phase 1.5 (Tests)** sont très volumineux. Voici un résumé de leur contenu avec les fichiers clés à créer.

---

## 📝 Phase 1.3 : API Routes (3-4h)

**Fichiers à créer** :
- `backend/schemas/project.py` - Pydantic schemas pour Project
- `backend/schemas/match.py` - Pydantic schemas pour Match  
- `backend/schemas/team.py` - Pydantic schemas pour Team
- `backend/schemas/venue.py` - Pydantic schemas pour Venue
- `backend/api/routes/projects.py` - CRUD Projects
- `backend/api/routes/matches.py` - CRUD Matches avec opérations spéciales
- `backend/api/routes/teams.py` - CRUD Teams
- `backend/api/routes/venues.py` - CRUD Venues

**Contenu clé** :
Voir `PLAN_IMPLEMENTATION.md` section "1.4 Pydantic Schemas" et "1.5 API Routes - Matches" pour les exemples de code complets.

**Endpoints principaux** :
- `GET /api/projects/` - Liste projets
- `POST /api/projects/` - Créer projet
- `GET /api/matches/?project_id=1` - Liste matchs
- `PUT /api/matches/{id}` - Modifier match
- `POST /api/matches/{id}/move` - Déplacer match (drag & drop)
- `POST /api/matches/{id}/fix` - Fixer match
- Similaire pour teams et venues

---

## 📝 Phase 1.4 : Sync Service (4h)

**Fichiers à créer** :
- `backend/services/sync_service.py` - Import Excel → DB
- `scripts/import_excel.py` - Script CLI pour import

**Contenu clé** :
Voir `PLAN_IMPLEMENTATION.md` section "1.6 Service de Synchronisation Excel → DB" pour le code complet.

**Fonctionnalité** :
```python
# Import d'un projet Excel
service = SyncService(db)
project = service.import_from_excel(
    "configs/config_volley.yaml",
    "Championnat Volley 2025"
)
# → Importe équipes, gymnases, génère matchs
```

---

## 📝 Phase 1.5 : Tests (3h)

**Fichiers à créer** :
- `tests/conftest.py` - Fixtures pytest
- `tests/unit/test_models.py` - Tests modèles DB
- `tests/unit/test_api_routes.py` - Tests API endpoints
- `tests/unit/test_sync_service.py` - Tests import Excel

**Contenu clé** :
Voir `PLAN_IMPLEMENTATION.md` section "1.7 Tests Unitaires" pour les exemples.

**Exemple test** :
```python
def test_create_match(db_session, sample_project):
    match = models.Match(
        project_id=sample_project.id,
        equipe1_nom="A",
        equipe2_nom="B",
        poule="P1"
    )
    db_session.add(match)
    db_session.commit()
    
    assert match.id is not None
    assert not match.est_planifie
    assert match.est_modifiable
```

---

## 🎯 Pour Obtenir les Guides Complets

Les guides détaillés (50-100 lignes chacun) avec tous les exemples de code sont disponibles dans **`PLAN_IMPLEMENTATION.md`** sections correspondantes.

**Option 1** : Extraire depuis PLAN_IMPLEMENTATION.md
- Copier sections 1.4, 1.5, 1.6, 1.7
- Créer fichiers individuels si besoin

**Option 2** : Demander à un agent IA
```
Agent, crée le fichier docs/implementation/phase1/03_api_routes.md
en suivant le format des guides précédents et en utilisant le code 
de PLAN_IMPLEMENTATION.md section 1.4 et 1.5
```

**Option 3** : Les créer au fur et à mesure
- Suivre directement PLAN_IMPLEMENTATION.md pendant l'implémentation
- Les guides phase1/01 et phase1/02 donnent le format à suivre

---

## 📊 Structure Complète Phase 1

```
docs/implementation/phase1/
├── 01_setup_fastapi.md           ✅ Créé (2h)
├── 02_database_models.md          ✅ Créé (3h)
├── 03_api_routes.md               📄 À créer (voir PLAN_IMPLEMENTATION.md)
├── 04_sync_service.md             📄 À créer (voir PLAN_IMPLEMENTATION.md)
└── 05_tests.md                    📄 À créer (voir PLAN_IMPLEMENTATION.md)
```

---

## ✅ Phase 1 Complète = Backend Fonctionnel

Après les 5 guides :
- ✅ FastAPI configuré
- ✅ Base de données SQLite avec 4 tables
- ✅ API REST complète (Projects, Matches, Teams, Venues)
- ✅ Import Excel → DB fonctionnel
- ✅ Tests unitaires >80% coverage

**Validation finale Phase 1** :
```bash
# 1. Init DB
python scripts/init_db.py

# 2. Import projet
python scripts/import_excel.py configs/config_volley.yaml "Volley"

# 3. Lancer API
uvicorn backend.api.main:app --reload

# 4. Tests
pytest tests/ -v --cov=backend

# 5. Vérifier endpoints
curl http://localhost:8000/api/projects/
curl http://localhost:8000/api/matches/?project_id=1
```

---

## 🚀 Prochaine Phase

Une fois Phase 1 terminée → **Phase 2 : Frontend React**

Guides à créer :
- `phase2/01_setup_react.md`
- `phase2/02_api_client.md`
- `phase2/03_components.md`
- `phase2/04_calendar.md`
- `phase2/05_routing.md`
