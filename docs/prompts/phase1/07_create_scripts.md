# PROMPT 1.7 : Scripts CLI pour Init DB et Import Excel

## Contexte Projet

**PyCalendar V2** : Scripts CLI utilitaires pour initialisation base et import données.

## État Actuel

- ✅ Database + API + SyncService
- ⏳ Créer scripts exécutables

## Objectif

2 scripts :
1. `scripts/init_db.py` : Créer toutes tables
2. `scripts/import_excel.py` : Importer projet depuis Excel

**Durée** : 20 min

## Instructions

### 1. Script Init DB

**Fichier** : `scripts/init_db.py`

```python
#!/usr/bin/env python3
"""Script initialisation base de données."""

import sys
from pathlib import Path

# Ajouter racine projet au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database.engine import init_db

def main():
    """Créer toutes les tables."""
    try:
        init_db()
        print("✅ Base de données initialisée avec succès")
        print("📁 Fichier : database/pycalendar.db")
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation : {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### 2. Script Import Excel

**Fichier** : `scripts/import_excel.py`

```python
#!/usr/bin/env python3
"""Script import projet depuis Excel."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database.engine import SessionLocal
from backend.database import models
from backend.services.sync_service import SyncService

def main():
    """Importer projet depuis config YAML + Excel."""
    
    # Parse arguments
    if len(sys.argv) < 2:
        print("Usage: python scripts/import_excel.py <config.yaml> [nom_projet]")
        print("Exemple: python scripts/import_excel.py configs/config_volley.yaml 'Volley 2025'")
        sys.exit(1)
    
    config_path = sys.argv[1]
    project_name = sys.argv[2] if len(sys.argv) > 2 else Path(config_path).stem
    
    # Vérifier fichier existe
    if not Path(config_path).exists():
        print(f"❌ Fichier introuvable : {config_path}")
        sys.exit(1)
    
    # Import
    db = SessionLocal()
    try:
        service = SyncService(db)
        project = service.import_from_excel(config_path, project_name)
        
        # Stats
        nb_teams = db.query(models.Team).filter(models.Team.project_id == project.id).count()
        nb_venues = db.query(models.Venue).filter(models.Venue.project_id == project.id).count()
        nb_matches = db.query(models.Match).filter(models.Match.project_id == project.id).count()
        
        print(f"✅ Projet importé avec succès")
        print(f"   ID: {project.id}")
        print(f"   Nom: {project.nom}")
        print(f"   Sport: {project.sport}")
        print(f"   Teams: {nb_teams}")
        print(f"   Gymnases: {nb_venues}")
        print(f"   Matchs: {nb_matches}")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'import : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()
```

### 3. Rendre Exécutables (Linux/Mac)

```bash
chmod +x scripts/init_db.py
chmod +x scripts/import_excel.py
```

## Validation

### Test Init DB

```bash
# Supprimer DB existante si présente
rm -f database/pycalendar.db

# Init
python scripts/init_db.py

# Vérifier création
ls -lh database/pycalendar.db
sqlite3 database/pycalendar.db ".tables"
```

**Attendu** : Tables `projects teams venues matches`

### Test Import Excel

```bash
python scripts/import_excel.py configs/config_volley.yaml "Volley Test"
```

**Attendu** :
```
✅ Projet importé avec succès
   ID: 1
   Nom: Volley Test
   Sport: volleyball
   Teams: 24
   Gymnases: 5
   Matchs: 276
```

### Test Vérification DB

```bash
python -c "
from backend.database.engine import SessionLocal
from backend.database import models

db = SessionLocal()
projects = db.query(models.Project).all()
print(f'Projets en DB: {len(projects)}')
for p in projects:
    print(f'  - {p.nom} ({p.sport})')
db.close()
"
```

## Critères de Réussite

- [ ] Dossier `scripts/` créé
- [ ] `scripts/init_db.py` crée toutes tables
- [ ] `scripts/import_excel.py` importe projet complet
- [ ] Messages console clairs (✅ succès, ❌ erreur)
- [ ] Gestion erreurs (fichier absent, DB erreur)
- [ ] Stats affichées (nb teams, venues, matches)

## Prochaine Étape

➡️ **Prompt 1.8** : Créer tests unitaires backend
