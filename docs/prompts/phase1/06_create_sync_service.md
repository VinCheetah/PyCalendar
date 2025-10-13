# PROMPT 1.6 : Service Synchronisation Excel → Database

## Contexte Projet

**PyCalendar V2** : Import projets depuis fichiers Excel existants vers base de données pour utilisation via API web.

## État Actuel

- ✅ Database + API routes fonctionnelles
- ⏳ Créer service import Excel → DB

## Objectif

Service `SyncService` pour :
1. Charger config YAML + Excel
2. Créer Project en DB
3. Importer Teams, Venues
4. Générer et importer Matches

**Durée** : 1h

## Instructions

### 1. Structure

```bash
mkdir -p backend/services
touch backend/services/__init__.py
touch backend/services/sync_service.py
```

### 2. Service Sync

**Fichier** : `backend/services/sync_service.py`

```python
from sqlalchemy.orm import Session
from pathlib import Path
import json

from core.config import Config
from data.data_source import DataSource
from generators.multi_pool_generator import MultiPoolGenerator
from backend.database import models

class SyncService:
    """Service synchronisation Excel → Database."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def import_from_excel(self, config_path: str, project_name: str) -> models.Project:
        """
        Importer projet depuis Excel.
        
        Args:
            config_path: Chemin vers config YAML
            project_name: Nom projet en DB
            
        Returns:
            Project créé
        """
        # 1. Charger config
        config = Config.from_yaml(config_path)
        
        # 2. Charger données Excel
        source = DataSource(config.fichier_donnees)
        equipes = source.charger_equipes()
        gymnases = source.charger_gymnases()
        
        # 3. Créer projet
        project = models.Project(
            nom=project_name,
            sport=self._detect_sport(config),
            config_yaml_path=config_path,
            nb_semaines=config.nb_semaines,
            semaine_min=getattr(config, 'semaine_min', 1)
        )
        self.db.add(project)
        self.db.flush()  # Obtenir project.id
        
        # 4. Importer équipes
        for equipe in equipes:
            db_team = models.Team(
                project_id=project.id,
                nom=equipe.nom,
                institution=equipe.institution,
                numero_equipe=equipe.numero_equipe,
                genre=equipe.genre,
                poule=equipe.poule,
                horaires_preferes=json.dumps(equipe.horaires_preferes),
                lieux_preferes=json.dumps([l if l else None for l in equipe.lieux_preferes])
            )
            self.db.add(db_team)
        
        # 5. Importer gymnases
        for gymnase in gymnases:
            db_venue = models.Venue(
                project_id=project.id,
                nom=gymnase.nom,
                capacite=gymnase.capacite,
                horaires_disponibles=json.dumps(gymnase.horaires_disponibles)
            )
            self.db.add(db_venue)
        
        # 6. Générer matchs
        poules = source.get_poules_dict(equipes)
        generator = MultiPoolGenerator()
        matchs = generator.generer_matchs(poules)
        
        # 7. Importer matchs (non planifiés)
        for match in matchs:
            db_match = models.Match(
                project_id=project.id,
                equipe1_nom=match.equipe1.nom,
                equipe1_institution=match.equipe1.institution,
                equipe1_genre=match.equipe1.genre,
                equipe2_nom=match.equipe2.nom,
                equipe2_institution=match.equipe2.institution,
                equipe2_genre=match.equipe2.genre,
                poule=match.poule,
                priorite=match.priorite,
                # semaine/horaire/gymnase = None (non planifiés)
            )
            self.db.add(db_match)
        
        # 8. Commit
        self.db.commit()
        self.db.refresh(project)
        
        return project
    
    def _detect_sport(self, config: Config) -> str:
        """Détecter sport depuis nom fichier."""
        fichier_lower = config.fichier_donnees.lower()
        
        if 'volley' in fichier_lower:
            return 'volleyball'
        elif 'hand' in fichier_lower:
            return 'handball'
        elif 'basket' in fichier_lower:
            return 'basketball'
        elif 'foot' in fichier_lower:
            return 'football'
        else:
            return 'autre'
```

## Validation

### Test Import

```python
from backend.database.engine import SessionLocal
from backend.services.sync_service import SyncService

db = SessionLocal()
try:
    service = SyncService(db)
    project = service.import_from_excel(
        "configs/config_volley.yaml",
        "Test Import"
    )
    
    print(f"✅ Projet créé : ID={project.id}, Nom={project.nom}")
    
    # Vérifier données
    nb_teams = db.query(models.Team).filter(models.Team.project_id == project.id).count()
    nb_venues = db.query(models.Venue).filter(models.Venue.project_id == project.id).count()
    nb_matches = db.query(models.Match).filter(models.Match.project_id == project.id).count()
    
    print(f"Teams: {nb_teams}, Venues: {nb_venues}, Matches: {nb_matches}")
    
finally:
    db.close()
```

## Critères de Réussite

- [ ] Service `SyncService` créé
- [ ] Méthode `import_from_excel()` implémentée
- [ ] Project + Teams + Venues + Matches importés
- [ ] Matchs non planifiés (semaine=None)
- [ ] Commit réussi sans erreur

## Prochaine Étape

➡️ **Prompt 1.7** : Créer scripts CLI init_db.py et import_excel.py
