# 🚀 Phase 1.1 : Setup FastAPI

## 🎯 Objectif
Créer la structure backend FastAPI de base avec configuration, routes, et middleware.

**Durée estimée** : 2 heures  
**Prérequis** : Python 3.9+, pip, venv

---

## 📋 Ce que nous allons créer

```
backend/
├── __init__.py
├── api/
│   ├── __init__.py
│   ├── main.py              # ← Point d'entrée FastAPI
│   ├── dependencies.py      # ← Dépendances injectables
│   └── routes/
│       └── __init__.py
```

---

## 🔧 Étape 1 : Installer les Dépendances

### 1.1 Activer l'environnement virtuel

```bash
cd /home/vincheetah/Documents/Travail/FFSU/PyCalendar
source .venv/bin/activate
```

### 1.2 Installer FastAPI et dépendances

```bash
pip install fastapi uvicorn[standard] python-multipart
pip install sqlalchemy pydantic-settings
```

### 1.3 Mettre à jour requirements.txt

```bash
pip freeze > requirements.txt
```

**Vérification** :
```bash
pip list | grep fastapi
# Devrait afficher : fastapi 0.104.x ou plus
```

---

## 🏗️ Étape 2 : Créer la Structure Backend

### 2.1 Créer les dossiers

```bash
mkdir -p backend/api/routes
```

### 2.2 Créer les fichiers `__init__.py`

```bash
touch backend/__init__.py
touch backend/api/__init__.py
touch backend/api/routes/__init__.py
```

---

## 📝 Étape 3 : Créer le Point d'Entrée FastAPI

### 3.1 Créer `backend/api/main.py`

**Objectif** : Configurer FastAPI avec CORS, routes, et endpoints de base

```python
"""
PyCalendar API - Point d'entrée principal
Gère la configuration FastAPI, CORS, et routing.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Version de l'API
API_VERSION = "2.0.0"
API_TITLE = "PyCalendar API"
API_DESCRIPTION = """
API REST pour la gestion de calendriers sportifs.

## Features

* **Projets** : Gestion de projets multi-sports
* **Matchs** : CRUD matchs avec planification
* **Équipes** : Gestion des équipes et institutions
* **Gymnases** : Gestion des lieux et créneaux
* **Solver** : Exécution des algorithmes de planification
* **Export** : Export Excel, iCal, PDF
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestion du cycle de vie de l'application.
    Exécuté au démarrage et à l'arrêt.
    """
    # Startup
    print("🚀 PyCalendar API démarrage...")
    print(f"📚 Documentation: http://localhost:8000/docs")
    print(f"🔄 Redoc: http://localhost:8000/redoc")
    
    yield
    
    # Shutdown
    print("👋 PyCalendar API arrêt...")


# Création de l'application FastAPI
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


# ============================================================================
# CORS Configuration
# ============================================================================

# Origins autorisées (à ajuster selon environnement)
origins = [
    "http://localhost:5173",  # Vite dev server
    "http://localhost:3000",  # React dev server alternatif
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Permet GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],  # Permet tous les headers
)


# ============================================================================
# Routes de Base
# ============================================================================

@app.get("/", tags=["Root"])
async def root():
    """
    Endpoint racine - Informations sur l'API.
    """
    return {
        "name": API_TITLE,
        "version": API_VERSION,
        "status": "running",
        "documentation": "/docs",
        "endpoints": {
            "projects": "/api/projects",
            "matches": "/api/matches",
            "teams": "/api/teams",
            "venues": "/api/venues",
        }
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Endpoint de santé pour monitoring.
    Utile pour les health checks Docker/Kubernetes.
    """
    return {
        "status": "healthy",
        "version": API_VERSION,
    }


@app.get("/api", tags=["API"])
async def api_info():
    """
    Informations sur l'API.
    """
    return {
        "version": API_VERSION,
        "title": API_TITLE,
        "description": "API REST pour gestion de calendriers sportifs",
    }


# ============================================================================
# Routes Modules (à ajouter progressivement)
# ============================================================================

# from .routes import projects, matches, teams, venues

# app.include_router(
#     projects.router,
#     prefix="/api/projects",
#     tags=["Projects"]
# )
# app.include_router(
#     matches.router,
#     prefix="/api/matches",
#     tags=["Matches"]
# )
# app.include_router(
#     teams.router,
#     prefix="/api/teams",
#     tags=["Teams"]
# )
# app.include_router(
#     venues.router,
#     prefix="/api/venues",
#     tags=["Venues"]
# )


# ============================================================================
# Exception Handlers (optionnel)
# ============================================================================

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handler personnalisé pour les erreurs de validation Pydantic.
    Retourne un message d'erreur plus clair.
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Erreur de validation",
            "errors": exc.errors(),
        },
    )


# ============================================================================
# Run (pour développement uniquement)
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "backend.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload en dev
        log_level="info",
    )
```

**Points clés** :
- ✅ CORS configuré pour frontend local
- ✅ Endpoints de base (`/`, `/health`, `/api`)
- ✅ Documentation auto-générée (`/docs`)
- ✅ Gestion cycle de vie (startup/shutdown)
- ✅ Handler erreurs de validation

---

### 3.2 Créer `backend/api/dependencies.py`

**Objectif** : Fonctions de dépendances réutilisables (DB session, config, etc.)

```python
"""
Dependencies pour FastAPI.
Fonctions injectables dans les routes via Depends().
"""
from typing import Generator
from fastapi import Depends, HTTPException, status


# ============================================================================
# Database Dependencies (sera implémenté dans guide suivant)
# ============================================================================

def get_db():
    """
    Dependency pour obtenir une session de base de données.
    
    Usage:
        @app.get("/items/")
        def read_items(db: Session = Depends(get_db)):
            ...
    
    Note: Implémentation complète dans 02_database_models.md
    """
    # TODO: Implémenter avec SQLAlchemy SessionLocal
    # db = SessionLocal()
    # try:
    #     yield db
    # finally:
    #     db.close()
    pass


# ============================================================================
# Config Dependencies
# ============================================================================

def get_config():
    """
    Dependency pour obtenir la configuration globale.
    
    Usage:
        @app.get("/config/")
        def read_config(config: Config = Depends(get_config)):
            ...
    """
    from core.config import Config
    # Charger config par défaut
    # TODO: Gérer config par projet
    return Config.from_yaml("configs/default.yaml")


# ============================================================================
# Authentication Dependencies (Phase 6)
# ============================================================================

async def get_current_user():
    """
    Dependency pour obtenir l'utilisateur authentifié.
    
    À implémenter dans Phase 6 (Authentification).
    
    Usage:
        @app.get("/me/")
        def read_user_me(current_user: User = Depends(get_current_user)):
            ...
    """
    # TODO: Implémenter avec JWT tokens
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Authentification non implémentée"
    )


# ============================================================================
# Pagination Dependencies
# ============================================================================

def pagination_params(
    skip: int = 0,
    limit: int = 100
):
    """
    Dependency pour paramètres de pagination.
    
    Args:
        skip: Nombre d'éléments à sauter
        limit: Nombre maximum d'éléments à retourner
    
    Returns:
        Dict avec skip et limit
    
    Usage:
        @app.get("/items/")
        def read_items(pagination: dict = Depends(pagination_params)):
            skip = pagination["skip"]
            limit = pagination["limit"]
            ...
    """
    if skip < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="skip doit être >= 0"
        )
    if limit < 1 or limit > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="limit doit être entre 1 et 1000"
        )
    
    return {"skip": skip, "limit": limit}


# ============================================================================
# Validation Dependencies
# ============================================================================

def validate_project_exists(project_id: int, db = Depends(get_db)):
    """
    Dependency pour valider qu'un projet existe.
    
    Args:
        project_id: ID du projet
        db: Session de base de données
    
    Raises:
        HTTPException 404 si projet n'existe pas
    
    Returns:
        Le projet s'il existe
    
    Usage:
        @app.get("/projects/{project_id}/matches/")
        def read_matches(
            project = Depends(validate_project_exists)
        ):
            ...
    """
    # TODO: Implémenter après création models DB
    pass
```

**Points clés** :
- ✅ Dépendances réutilisables
- ✅ Pagination standardisée
- ✅ Validation d'existence
- ✅ Placeholder pour auth future

---

## ✅ Étape 4 : Tester le Setup

### 4.1 Lancer le serveur

```bash
cd /home/vincheetah/Documents/Travail/FFSU/PyCalendar
uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000
```

**Sortie attendue** :
```
🚀 PyCalendar API démarrage...
📚 Documentation: http://localhost:8000/docs
🔄 Redoc: http://localhost:8000/redoc
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx] using WatchFiles
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 4.2 Tester les endpoints

**Option 1 : Navigateur**
- Ouvrir http://localhost:8000 → Devrait afficher JSON avec infos API
- Ouvrir http://localhost:8000/docs → Documentation Swagger UI
- Ouvrir http://localhost:8000/health → `{"status": "healthy"}`

**Option 2 : curl**
```bash
# Endpoint racine
curl http://localhost:8000/
# {"name":"PyCalendar API","version":"2.0.0","status":"running"...}

# Health check
curl http://localhost:8000/health
# {"status":"healthy","version":"2.0.0"}

# API info
curl http://localhost:8000/api
# {"version":"2.0.0","title":"PyCalendar API"...}
```

**Option 3 : Swagger UI**
1. Ouvrir http://localhost:8000/docs
2. Cliquer sur `/` GET
3. Cliquer "Try it out"
4. Cliquer "Execute"
5. Vérifier la réponse

---

## 📸 Captures d'Écran Attendues

### Swagger UI
```
┌─────────────────────────────────────────────┐
│ PyCalendar API                         2.0.0│
│                                              │
│ Root                                         │
│ ├─ GET  /        Endpoint racine           │
│ ├─ GET  /health  Health check              │
│ └─ GET  /api     API info                   │
│                                              │
│ [Schemas] [Authorize]                       │
└─────────────────────────────────────────────┘
```

---

## 🐛 Troubleshooting

### Erreur : `ModuleNotFoundError: No module named 'fastapi'`
**Solution** :
```bash
source .venv/bin/activate
pip install fastapi uvicorn[standard]
```

### Erreur : `Address already in use`
**Solution** :
```bash
# Trouver le processus sur port 8000
lsof -i :8000

# Tuer le processus
kill -9 <PID>

# Ou utiliser un autre port
uvicorn backend.api.main:app --reload --port 8001
```

### Erreur CORS dans navigateur
**Solution** : Vérifier que l'origin frontend est dans la liste `origins` de `main.py`

---

## ✅ Critères de Validation

Avant de passer au guide suivant, vérifier que :

- [ ] Le serveur démarre sans erreur
- [ ] http://localhost:8000/ retourne un JSON valide
- [ ] http://localhost:8000/docs affiche Swagger UI
- [ ] http://localhost:8000/health retourne `{"status": "healthy"}`
- [ ] Pas d'erreurs dans la console
- [ ] Hot reload fonctionne (modifier `main.py` → serveur recharge)

---

## 🎯 Prochaines Étapes

Une fois ce guide complété :

1. **Commit** :
   ```bash
   git add backend/
   git commit -m "feat(backend): Setup FastAPI structure"
   ```

2. **Passer au guide suivant** :
   ```bash
   cat docs/implementation/phase1/02_database_models.md
   ```

---

## 📚 Références

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [FastAPI CORS](https://fastapi.tiangolo.com/tutorial/cors/)
- [Uvicorn Settings](https://www.uvicorn.org/settings/)
- [OpenAPI Specification](https://swagger.io/specification/)

---

**Durée réelle** : _____ heures  
**Difficultés rencontrées** : _____  
**Notes** : _____
