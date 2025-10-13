"""
SQLAlchemy Database Models for PyCalendar V2

This module defines the 4 core database models that persist the scheduling data:
- Project: Top-level container for a scheduling project
- Team: Teams participating in competitions
- Venue: Sports venues/gymnasiums where matches are played
- Match: Individual matches with scheduling metadata

Key design decisions:
- Denormalized team data in Match model for query simplification
- Cascade delete on all relationships to prevent orphan records
- Composite indexes on frequently filtered columns (project_id + semaine/poule)
- Properties to reproduce core.Match business logic (est_planifie, est_modifiable)
"""

from sqlalchemy import Column, Integer, String, Boolean, Text, JSON, DateTime, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Project(Base):
    """
    Top-level project containing all scheduling data.
    
    Stores both YAML configuration (hyperparameters) and Excel data references.
    The DB acts as the source of truth after initial import from Excel/YAML.
    """
    __tablename__ = "projects"
    
    # Clé primaire
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Informations projet
    nom = Column(String(200), nullable=False)
    sport = Column(String(50), nullable=False)
    
    # Configuration - Stockage des fichiers sources et données complètes
    config_yaml_path = Column(String(500), nullable=True)  # Chemin YAML (ex: configs/config_volley.yaml)
    config_data = Column(JSON, nullable=True)  # Config complète en JSON (hyperparamètres, etc.)
    
    # Paramètres planification (extraits de la config pour accès rapide)
    nb_semaines = Column(Integer, default=26, nullable=False)
    semaine_min = Column(Integer, default=1, nullable=False)  # Tâche 1.2 - semaine_minimum constraint
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relations (cascade delete pour supprimer matchs/équipes/gymnases si projet supprimé)
    matches = relationship("Match", back_populates="project", cascade="all, delete-orphan")
    teams = relationship("Team", back_populates="project", cascade="all, delete-orphan")
    venues = relationship("Venue", back_populates="project", cascade="all, delete-orphan")


class Team(Base):
    """
    Team/Équipe participating in the competition.
    
    Source: Excel sheet 'Equipes' with columns like Equipe, Poule, Horaire_Prefere.
    Institution and numero_equipe are extracted from team name (ex: "CENTRALE 1 (1)").
    """
    __tablename__ = "teams"
    
    # Clé primaire
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Informations équipe (depuis feuille Excel "Equipes")
    nom = Column(String(200), nullable=False)  # Colonne "Equipe"
    institution = Column(String(200), nullable=True)  # Extraite du nom (ex: "CENTRALE")
    numero_equipe = Column(String(50), nullable=True)  # Numéro équipe (ex: "1")
    genre = Column(String(20), nullable=True)  # Extrait de la poule (ex: "M" de "HBFA1PK")
    poule = Column(String(100), nullable=True)  # Colonne "Poule"
    
    # Préférences (JSON arrays - depuis Excel ou calculées)
    horaires_preferes = Column(JSON, nullable=True)  # ["Mercredi 14h", "Vendredi 18h"]
    lieux_preferes = Column(JSON, nullable=True)     # ["Gymnase A", "Gymnase B"] (feuille Preferences_Gymnases)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relation
    project = relationship("Project", back_populates="teams")


class Venue(Base):
    """
    Sports venue/gymnasium where matches can be played.
    
    Source: Excel sheet 'Gymnases' with columns Gymnase, Capacite, and dynamic time slot columns.
    Capacite indicates number of simultaneous matches possible.
    """
    __tablename__ = "venues"
    
    # Clé primaire
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Informations gymnase (depuis feuille Excel "Gymnases")
    nom = Column(String(200), nullable=False)  # Colonne "Gymnase"
    capacite = Column(Integer, default=1, nullable=False)  # Nombre de terrains simultanés
    
    # Disponibilités (JSON array - depuis colonnes horaires du Excel)
    horaires_disponibles = Column(JSON, nullable=True)  # ["Mercredi 14h", "Mercredi 16h", ...]
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relation
    project = relationship("Project", back_populates="venues")


class Match(Base):
    """
    Individual match between two teams.
    
    Design notes:
    - Team data is DENORMALIZED (no FK to Team) for query simplification
    - Matches are initially generated by generators/match_generator.py (round-robin)
    - New fields from Tâche 1.1: est_fixe, statut, scores, notes
    - Properties reproduce core.Match business logic
    """
    __tablename__ = "matches"
    
    # Clé primaire
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Équipes (dénormalisé pour simplifier les requêtes - pas de FK vers Team)
    equipe1_nom = Column(String(200), nullable=False)
    equipe1_institution = Column(String(200), nullable=True)
    equipe1_genre = Column(String(20), nullable=True)
    
    equipe2_nom = Column(String(200), nullable=False)
    equipe2_institution = Column(String(200), nullable=True)
    equipe2_genre = Column(String(20), nullable=True)
    
    # Poule
    poule = Column(String(100), nullable=True, index=True)  # Index pour filtrage
    
    # Créneau (nullable si non planifié)
    semaine = Column(Integer, nullable=True, index=True)  # Index pour filtrage par semaine
    horaire = Column(String(20), nullable=True)  # "Mercredi 14h"
    gymnase = Column(String(200), nullable=True)
    
    # État (NOUVEAUX CHAMPS - Tâche 1.1)
    est_fixe = Column(Boolean, default=False, nullable=False, index=True)  # Verrouillé (non replanifiable)
    statut = Column(String(50), default="a_planifier", nullable=False, index=True)  # a_planifier, planifie, fixe, termine, annule
    priorite = Column(Integer, default=0, nullable=False)
    
    # Scores (NOUVEAUX CHAMPS - Tâche 1.1)
    score_equipe1 = Column(Integer, nullable=True)
    score_equipe2 = Column(Integer, nullable=True)
    
    # Notes (NOUVEAU CHAMP - Tâche 1.1)
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relation
    project = relationship("Project", back_populates="matches")
    
    # Properties calculées (reproduire logique core.Match - Tâche 1.1)
    @property
    def est_planifie(self) -> bool:
        """Retourne True si le match a un créneau assigné"""
        return self.semaine is not None
    
    @property
    def est_modifiable(self) -> bool:
        """Retourne True si le match peut être replanifié"""
        if self.est_fixe:
            return False
        if self.statut in ["fixe", "termine", "annule"]:
            return False
        return True


# Indexes composites pour optimiser les requêtes fréquentes
Index('idx_match_project_semaine', Match.project_id, Match.semaine)
Index('idx_match_project_poule', Match.project_id, Match.poule)
