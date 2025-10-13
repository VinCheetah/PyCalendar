# 🔧 Backend API - PyCalendar V2

API REST FastAPI pour la gestion de calendriers sportifs.

## 🚀 Démarrage Rapide

```bash
# 1. Initialiser la base de données
python init_database.py

# 2. Lancer l'API
python run_api.py

# 3. Ouvrir la documentation
# → http://localhost:8000/docs
```

## 📋 Prérequis

```bash
# Packages installés
pip install sqlalchemy pydantic fastapi uvicorn[standard]
```

## 🏗️ Architecture

```
backend/
├── database/
│   ├── engine.py           # SQLAlchemy engine + sessions
│   └── models.py           # 4 modèles ORM (Project, Team, Venue, Match)
│
├── schemas/
│   ├── match.py            # Schémas Pydantic Match
│   ├── project.py          # Schémas Pydantic Project
│   ├── team.py             # Schémas Pydantic Team
│   └── venue.py            # Schémas Pydantic Venue
│
└── api/
    ├── main.py             # Application FastAPI
    └── routes/
        ├── matches.py      # 8 endpoints Matches
        ├── projects.py     # 6 endpoints Projects
        ├── teams.py        # 5 endpoints Teams
        └── venues.py       # 5 endpoints Venues
```

## 🎯 Endpoints Principaux

### Matches
- `GET /matches/` - Liste (filtre `?project_id=1`)
- `POST /matches/{id}/move` - Déplacer (drag & drop)
- `POST /matches/{id}/fix` - Fixer (verrouiller)
- `POST /matches/{id}/unfix` - Défixer

### Projects
- `GET /projects/` - Liste tous
- `GET /projects/{id}/stats` - Statistiques dashboard
- `DELETE /projects/{id}` - Supprimer (⚠️ CASCADE)

### Teams / Venues
- `GET /teams/` - Liste équipes
- `GET /venues/` - Liste gymnases

**Total : 29 endpoints**

## 🔧 Utilisation

### Lancer l'API

**Option 1 : Script Python**
```bash
python run_api.py              # Dev (port 8000)
python run_api.py --port 8080  # Dev (port custom)
python run_api.py --prod       # Production
```

**Option 2 : Uvicorn Direct**
```bash
PYTHONPATH=/path/to/PyCalendar \
  uvicorn backend.api.main:app --reload --port 8000
```

### Tests cURL

```bash
# Health check
curl http://localhost:8000/health

# Créer projet
curl -X POST http://localhost:8000/projects/ \
  -H "Content-Type: application/json" \
  -d '{"nom":"Test","sport":"Volley","nb_semaines":26,"semaine_min":1}'

# Créer match
curl -X POST http://localhost:8000/matches/ \
  -H "Content-Type: application/json" \
  -d '{"project_id":1,"equipe1_nom":"A","equipe2_nom":"B","poule":"P1"}'

# Fixer match
curl -X POST http://localhost:8000/matches/1/fix

# Déplacer match
curl -X POST http://localhost:8000/matches/1/move \
  -H "Content-Type: application/json" \
  -d '{"semaine":5,"horaire":"Mer 14h","gymnase":"Gym A"}'
```

## 📊 Documentation

- **Swagger UI** : http://localhost:8000/docs
- **ReDoc** : http://localhost:8000/redoc
- **Guides complets** :
  - `API_ROUTES_REPORT.md` - Architecture détaillée
  - `API_QUICK_START.md` - Guide démarrage rapide
  - `API_COMMANDS.md` - Toutes les commandes

## 🔗 Intégration Frontend

```typescript
// TypeScript/Axios
const api = axios.create({ baseURL: 'http://localhost:8000' });

// Déplacer match
await api.post(`/matches/${matchId}/move`, {
  semaine: 5,
  horaire: "Mercredi 14h",
  gymnase: "Gymnase A"
});
```

## 🐛 Dépannage

### "ModuleNotFoundError: No module named 'backend'"
**Solution** : Utiliser `run_api.py` ou définir PYTHONPATH :
```bash
PYTHONPATH=/path/to/PyCalendar uvicorn ...
```

### Port 8000 déjà utilisé
**Solution** : Changer de port :
```bash
python run_api.py --port 8080
```

### Base de données vide
**Solution** : Initialiser d'abord :
```bash
python init_database.py
```

## ✅ Tests

```bash
# Via Python (recommandé)
python -c "
import requests
r = requests.get('http://localhost:8000/health')
print(r.json())
"
# → {"status":"ok"}
```

## 📚 En Savoir Plus

- **Database** : `DATABASE_QUICK_REF.md`
- **Schemas** : `SCHEMAS_QUICK_REF.md`
- **Récap Backend** : `BACKEND_RECAP.md`
- **Tâche 1.5** : `TASK_1.5_SUMMARY.md`

---

**API Version** : 2.0.0  
**Framework** : FastAPI  
**Database** : SQLite + SQLAlchemy  
**Validation** : Pydantic V2
