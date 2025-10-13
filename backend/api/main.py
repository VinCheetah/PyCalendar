"""
Application FastAPI principale pour PyCalendar V2.

Cette API expose les endpoints REST pour gérer les projets de calendriers sportifs,
incluant la gestion des équipes, gymnases et matchs avec fonctionnalités avancées
(drag & drop, fixation de matchs, statistiques).
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Créer l'application FastAPI
app = FastAPI(
    title="PyCalendar API",
    version="2.0.0",
    description="API REST pour la gestion de calendriers sportifs",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuration CORS pour le frontend React (dev)
# ⚠️ En production : remplacer par le domaine réel et restreindre les méthodes/headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend Vite dev server
    allow_credentials=True,
    allow_methods=["*"],  # GET, POST, PUT, DELETE, PATCH, OPTIONS
    allow_headers=["*"],  # Authorization, Content-Type, etc.
)


# Routes basiques
@app.get("/")
def root():
    """Page d'accueil de l'API avec informations de base."""
    return {
        "title": "PyCalendar API",
        "version": "2.0.0",
        "description": "API REST pour la gestion de calendriers sportifs",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
def health_check():
    """Health check endpoint pour monitoring."""
    return {"status": "ok"}


# Import et inclusion des routers
from backend.api.routes import matches, projects, teams, venues, solver

app.include_router(matches.router, prefix="/matches", tags=["Matches"])
app.include_router(projects.router, prefix="/projects", tags=["Projects"])
app.include_router(teams.router, prefix="/teams", tags=["Teams"])
app.include_router(venues.router, prefix="/venues", tags=["Venues"])
app.include_router(solver.router, prefix="/projects", tags=["Solver"])
