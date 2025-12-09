"""
Fixtures pytest partagées pour tous les tests.

Ce fichier contient les fixtures communes (configs, builders d'objets, etc.)
qui peuvent être réutilisées dans tous les tests.
"""

import sys
from pathlib import Path
import pytest

# Ajouter src au path Python
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pycalendar.core.config import Config
from pycalendar.core.models import Match, Creneau, Equipe, Gymnase
from pycalendar.solvers.cpsat_solver import CPSATSolver


@pytest.fixture
def minimal_config():
    """
    Configuration minimale pour tests unitaires.
    
    Désactive la plupart des contraintes pour tester un comportement à la fois.
    """
    # Charger une config de base et la modifier
    config = Config.from_yaml("configs/default.yaml")
    
    # Désactiver tout par défaut
    config.equilibrage_actif = False
    config.contrainte_temporelle_actif = False
    config.compaction_temporelle_actif = False
    config.overlap_institution_actif = False
    config.entente_actif = False
    
    # Pénalités/bonus à zéro par défaut
    config.bonus_preferences_gymnases = []
    config.penalites_espacement_repos = []
    config.poids_niveaux_gymnases_haut = []
    config.poids_niveaux_gymnases_bas = []
    
    # Pénalités horaires désactivées
    config.penalite_avant_horaire_min = 0
    config.penalite_avant_horaire_min_deux = 0
    config.penalite_apres_horaire_min = 0
    config.penalite_horaire_tolerance = 999999  # Tolérance infinie = pas de pénalité
    config.penalite_gymnase_priorite_genre = 0
    
    # Temps de résolution court pour tests rapides
    config.temps_max_secondes = 5
    config.afficher_progression = False
    
    return config


@pytest.fixture
def default_config():
    """Configuration par défaut du projet (depuis default.yaml)."""
    return Config.from_yaml("configs/default.yaml")


@pytest.fixture
def volleyball_config():
    """Configuration volleyball réelle."""
    return Config.from_yaml("configs/config_volley.yaml")


class EquipeBuilder:
    """Builder pour créer des équipes de test facilement."""
    
    def __init__(self):
        self._counter = 0
    
    def create(self, nom=None, poule="A1", institution=None, 
               horaires_preferes=None, lieux_preferes=None):
        """Crée une équipe avec des valeurs par défaut intelligentes."""
        self._counter += 1
        
        if nom is None:
            nom = f"Equipe_{self._counter}"
        
        if institution is None:
            institution = f"Institution_{self._counter}"
        
        return Equipe(
            nom=nom,
            poule=poule,
            institution=institution,
            horaires_preferes=horaires_preferes or [],
            lieux_preferes=lieux_preferes or []
        )


@pytest.fixture
def equipe_builder():
    """Builder pour créer des équipes facilement dans les tests."""
    return EquipeBuilder()


class MatchBuilder:
    """Builder pour créer des matchs de test facilement."""
    
    def __init__(self, equipe_builder: EquipeBuilder):
        self.equipe_builder = equipe_builder
        self._counter = 0
    
    def create(self, equipe1=None, equipe2=None, poule="A1"):
        """Crée un match avec des équipes auto-générées si non fournies."""
        self._counter += 1
        
        if equipe1 is None:
            equipe1 = self.equipe_builder.create(poule=poule)
        
        if equipe2 is None:
            equipe2 = self.equipe_builder.create(poule=poule)
        
        return Match(equipe1=equipe1, equipe2=equipe2, poule=poule)


@pytest.fixture
def match_builder(equipe_builder):
    """Builder pour créer des matchs facilement dans les tests."""
    return MatchBuilder(equipe_builder)


class CreneauBuilder:
    """Builder pour créer des créneaux de test facilement."""
    
    def __init__(self):
        self._counter = 0
    
    def create(self, semaine=1, horaire="18:00", gymnase=None):
        """Crée un créneau avec des valeurs par défaut."""
        self._counter += 1
        
        if gymnase is None:
            gymnase = f"Gymnase_{self._counter}"
        
        return Creneau(semaine=semaine, horaire=horaire, gymnase=gymnase)
    
    def create_batch(self, n, **kwargs):
        """Crée n créneaux avec les mêmes paramètres (gymnases auto-incrémentés)."""
        return [self.create(**kwargs) for _ in range(n)]


@pytest.fixture
def creneau_builder():
    """Builder pour créer des créneaux facilement dans les tests."""
    return CreneauBuilder()


class GymnaseBuilder:
    """Builder pour créer des gymnases de test facilement."""
    
    def __init__(self):
        self._counter = 0
    
    def create(self, nom=None, capacite=1):
        """Crée un gymnase avec des valeurs par défaut."""
        self._counter += 1
        
        if nom is None:
            nom = f"Gymnase_{self._counter}"
        
        return Gymnase(nom=nom, capacite=capacite)
    
    def create_dict(self, names_or_count, capacite=1):
        """
        Crée un dict {nom: Gymnase} pour passer au solver.
        
        Args:
            names_or_count: Liste de noms OU nombre de gymnases à créer
            capacite: Capacité par défaut
        """
        if isinstance(names_or_count, int):
            # Créer N gymnases auto-nommés
            names = [f"Gymnase_{i+1}" for i in range(names_or_count)]
        else:
            # Utiliser les noms fournis
            names = names_or_count
        
        return {
            name: Gymnase(nom=name, capacite=capacite)
            for name in names
        }


@pytest.fixture
def gymnase_builder():
    """Builder pour créer des gymnases facilement dans les tests."""
    return GymnaseBuilder()


def assert_match_assigned_to(match: Match, expected_creneau: Creneau):
    """
    Vérifie qu'un match est planifié au créneau attendu.
    
    Affiche un message d'erreur clair en cas d'échec.
    """
    assert match.est_planifie(), \
        f"Match {match.equipe1.nom} vs {match.equipe2.nom} devrait être planifié"
    
    assert match.creneau.semaine == expected_creneau.semaine, \
        f"Semaine incorrecte: attendu {expected_creneau.semaine}, obtenu {match.creneau.semaine}"
    
    assert match.creneau.horaire == expected_creneau.horaire, \
        f"Horaire incorrect: attendu {expected_creneau.horaire}, obtenu {match.creneau.horaire}"
    
    assert match.creneau.gymnase == expected_creneau.gymnase, \
        f"Gymnase incorrect: attendu {expected_creneau.gymnase}, obtenu {match.creneau.gymnase}"


def assert_match_not_assigned(match: Match):
    """Vérifie qu'un match n'est PAS planifié."""
    assert not match.est_planifie(), \
        f"Match {match.equipe1.nom} vs {match.equipe2.nom} ne devrait PAS être planifié"
