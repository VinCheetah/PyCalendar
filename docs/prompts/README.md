# Prompts d'Implémentation PyCalendar V2

## Structure des Prompts

Chaque fichier prompt est autonome et contient :
- **Contexte projet** : Rappel objectif global PyCalendar V2
- **État actuel** : Ce qui a été fait précédemment
- **Objectif tâche** : But précis du prompt
- **Instructions techniques** : Étapes détaillées d'implémentation
- **Validation** : Tests à effectuer

## Organisation

```
docs/prompts/
├── README.md                    # Ce fichier
├── phase1/                      # Backend Foundation
│   ├── 01_enrich_match_model.md
│   ├── 02_add_semaine_min.md
│   ├── 03_create_database.md
│   ├── 04_create_schemas.md
│   ├── 05_create_api_routes.md
│   ├── 06_create_sync_service.md
│   ├── 07_create_scripts.md
│   └── 08_create_tests.md
│
├── phase2/                      # Frontend Foundation
│   ├── 01_setup_react.md
│   ├── 02_define_types.md
│   ├── 03_create_api_client.md
│   ├── 04_create_hooks.md
│   ├── 05_create_calendar.md
│   └── 06_create_pages.md
│
└── phase3/                      # Solver Integration
    ├── 01_modify_solvers.md
    ├── 02_create_solver_service.md
    ├── 03_create_solver_endpoint.md
    └── 04_integrate_frontend_solver.md
```

## Ordre d'Exécution Recommandé

### Phase 1 - Backend (Durée : 2 semaines)
Exécuter prompts 01 à 08 séquentiellement.

**Validation Phase 1** :
```bash
python scripts/init_db.py
python scripts/import_excel.py configs/config_volley.yaml "Test"
uvicorn backend.api.main:app --reload
pytest tests/ -v
```

### Phase 2 - Frontend (Durée : 2 semaines)
Exécuter prompts 01 à 06 séquentiellement.

**Validation Phase 2** :
```bash
cd frontend && npm run dev
# Vérifier calendrier affiche matchs
# Vérifier drag & drop fonctionne
```

### Phase 3 - Solver (Durée : 2 semaines)
Exécuter prompts 01 à 04 séquentiellement.

**Validation Phase 3** :
```bash
# Fixer quelques matchs
# Cliquer bouton "Recalculer"
# Vérifier matchs fixes restent inchangés
```

## Utilisation

1. **Ouvrir prompt** correspondant à la tâche
2. **Lire contexte** et état actuel
3. **Suivre instructions** étape par étape
4. **Exécuter validation** en fin de tâche
5. **Passer au prompt suivant** si validation OK

## Contraintes Globales

- **Ne JAMAIS modifier** : `constraints/`, `generators/`, `validation/`, `main.py`
- **Modifications minimales** : `solvers/` (uniquement filtrage matchs fixes)
- **Préserver CLI** : `python main.py` doit toujours fonctionner
- **Transactions DB** : Toujours `commit()` et gérer `rollback()`
- **Type safety** : Types TypeScript = Schemas Pydantic

## Dépendances

### Backend
```bash
pip install fastapi uvicorn sqlalchemy pydantic
```

### Frontend
```bash
npm install @tanstack/react-query axios @fullcalendar/react react-router-dom
```
