"""
Tests pour SolverService et SolutionValidator (Phase 3.2).

Teste l'orchestration complète de résolution :
- Chargement depuis DB
- Exécution solver
- Validation solution
- Sauvegarde résultats
"""

import pytest
from backend.database import models
from backend.services.solver_service import SolverService, SolverError
from backend.services.solution_validator import SolutionValidator, ValidationError, MatchSnapshot
import json


@pytest.fixture
def sample_config():
    """Configuration YAML minimale pour tests."""
    return {
        "fichier_donnees": "test.xlsx",
        "fichier_sortie": "test_out.xlsx",
        "nb_semaines": 10,
        "taille_poule_min": 4,
        "taille_poule_max": 8,
        "semaine_minimum": 2,
        "respecter_matchs_fixes": True,
        "strategie": "greedy",
        "temps_max_secondes": 30,
        "nb_essais": 1,
        "fallback_greedy": False,
        "cpsat_warm_start": False,
        "cpsat_warm_start_file": None,
        "poids_indisponibilite": 100.0,
        "poids_capacite_gymnase": 50.0,
        "poids_equilibrage_charge": 10.0,
        "nb_preferences_gymnases": 3,
        "bonus_preferences_gymnases": [5.0, 3.0, 1.0],
        "penalites_espacement_repos": [20.0, 15.0, 10.0, 5.0],
        "penalite_apres_horaire_min": 8.0,
        "penalite_avant_horaire_min": 15.0,
        "penalite_avant_horaire_min_deux": 25.0,
        "penalite_horaire_diviseur": 2,
        "penalite_horaire_tolerance": 4,
        "compaction_temporelle_actif": False,
        "compaction_penalites_par_semaine": [],
        "overlap_institution_actif": False,
        "overlap_institution_poids": 0.0,
        "entente_penalite_non_planif": 100.0,
        "entente_actif": False,
        "contrainte_temporelle_actif": False,
        "contrainte_temporelle_penalite": 0.0,
        "contrainte_temporelle_dure": False,
        "aller_retour_espacement_actif": False,
        "aller_retour_min_semaines": 3,
        "aller_retour_penalite_meme_semaine": 50.0,
        "aller_retour_penalite_consecutives": 30.0,
        "max_matchs_par_equipe_par_semaine": 1,
        "afficher_progression": False,
        "niveau_log": 0  # 0 = quiet, 1 = normal, 2 = verbose
    }


@pytest.fixture
def simple_project(test_db, sample_config):
    """Crée un projet simple avec matchs, équipes, gymnases."""
    # 1. Créer projet
    project = models.Project(
        nom="Test Project",
        sport="Volleyball",
        nb_semaines=10,
        semaine_min=2,
        config_data=sample_config
    )
    test_db.add(project)
    test_db.commit()
    
    # 2. Créer gymnases
    gym1 = models.Venue(
        project_id=project.id,
        nom="Gymnase A",
        capacite=2,
        horaires_disponibles=json.dumps(["14h00", "16h00", "18h00"])
    )
    gym2 = models.Venue(
        project_id=project.id,
        nom="Gymnase B",
        capacite=1,
        horaires_disponibles=json.dumps(["14h00", "16h00"])
    )
    test_db.add_all([gym1, gym2])
    test_db.commit()
    
    # 3. Créer équipes
    teams = [
        models.Team(
            project_id=project.id,
            nom="Team 1",
            institution="School A",
            genre="M",
            poule="Poule A",
            horaires_preferes=json.dumps(["14h00"]),
            lieux_preferes=json.dumps(["Gymnase A"])
        ),
        models.Team(
            project_id=project.id,
            nom="Team 2",
            institution="School A",
            genre="M",
            poule="Poule A",
            horaires_preferes=json.dumps(["16h00"]),
            lieux_preferes=json.dumps(["Gymnase A"])
        ),
        models.Team(
            project_id=project.id,
            nom="Team 3",
            institution="School B",
            genre="M",
            poule="Poule A",
            horaires_preferes=json.dumps(["14h00"]),
            lieux_preferes=json.dumps(["Gymnase B"])
        ),
        models.Team(
            project_id=project.id,
            nom="Team 4",
            institution="School B",
            genre="M",
            poule="Poule A",
            horaires_preferes=json.dumps(["16h00"]),
            lieux_preferes=json.dumps(["Gymnase B"])
        ),
    ]
    test_db.add_all(teams)
    test_db.commit()
    
    # 4. Créer matchs (non planifiés initialement)
    matches = [
        models.Match(
            project_id=project.id,
            equipe1_nom="Team 1",
            equipe1_institution="School A",
            equipe1_genre="M",
            equipe2_nom="Team 2",
            equipe2_institution="School A",
            equipe2_genre="M",
            poule="Poule A",
            est_fixe=False,
            statut="non_planifie"
        ),
        models.Match(
            project_id=project.id,
            equipe1_nom="Team 3",
            equipe1_institution="School B",
            equipe1_genre="M",
            equipe2_nom="Team 4",
            equipe2_institution="School B",
            equipe2_genre="M",
            poule="Poule A",
            est_fixe=False,
            statut="non_planifie"
        ),
        # Match fixe semaine 1 (avant semaine_min=2)
        models.Match(
            project_id=project.id,
            equipe1_nom="Team 1",
            equipe1_institution="School A",
            equipe1_genre="M",
            equipe2_nom="Team 3",
            equipe2_institution="School B",
            equipe2_genre="M",
            poule="Poule A",
            semaine=1,
            horaire="14h00",
            gymnase="Gymnase A",
            est_fixe=True,
            statut="planifie"
        ),
    ]
    test_db.add_all(matches)
    test_db.commit()
    
    return project


# ==========================
# Tests SolverService
# ==========================

def test_solver_service_greedy_resolution(test_db, simple_project):
    """Test résolution basique avec greedy solver."""
    service = SolverService(test_db)
    
    result = service.solve_project(simple_project.id, strategy="greedy")
    
    # Vérifications
    assert result['project_id'] == simple_project.id
    assert result['strategy'] == "greedy"
    assert result['nb_matchs_total'] == 3
    assert result['nb_matchs_fixes'] == 1  # Le match semaine 1
    assert result['nb_matchs_planifies'] >= 1
    assert result['execution_time'] > 0


def test_solver_service_cpsat_resolution(test_db, simple_project):
    """Test résolution avec CP-SAT solver."""
    service = SolverService(test_db)
    
    result = service.solve_project(simple_project.id, strategy="cpsat")
    
    # Vérifications
    assert result['strategy'] == "cpsat"
    assert result['nb_matchs_planifies'] >= 1


def test_solver_service_respects_fixed_matches(test_db, simple_project):
    """Test que les matchs fixes ne sont jamais modifiés."""
    # Récupérer match fixe avant résolution
    match_fixe = test_db.query(models.Match).filter(
        models.Match.project_id == simple_project.id,
        models.Match.est_fixe == True
    ).first()
    
    assert match_fixe is not None
    semaine_before = match_fixe.semaine
    horaire_before = match_fixe.horaire
    gymnase_before = match_fixe.gymnase
    
    # Exécuter résolution
    service = SolverService(test_db)
    service.solve_project(simple_project.id, strategy="greedy")
    
    # Recharger match fixe
    test_db.refresh(match_fixe)
    
    # Vérifier qu'il n'a pas changé
    assert match_fixe.semaine == semaine_before
    assert match_fixe.horaire == horaire_before
    assert match_fixe.gymnase == gymnase_before


def test_solver_service_respects_semaine_minimum(test_db, simple_project):
    """Test que les matchs modifiables respectent semaine_minimum."""
    service = SolverService(test_db)
    service.solve_project(simple_project.id, strategy="greedy")
    
    # Vérifier tous les matchs non fixes
    matchs = test_db.query(models.Match).filter(
        models.Match.project_id == simple_project.id,
        models.Match.est_fixe == False
    ).all()
    
    for match in matchs:
        if match.semaine is not None:
            assert match.semaine >= simple_project.semaine_min, \
                f"Match {match.id} à semaine {match.semaine} < {simple_project.semaine_min}"


def test_solver_service_missing_project(test_db):
    """Test erreur si projet inexistant."""
    service = SolverService(test_db)
    
    with pytest.raises(ValueError, match="introuvable"):
        service.solve_project(project_id=9999)


def test_solver_service_all_matches_fixed(test_db, sample_config):
    """Test quand tous les matchs sont fixes."""
    # Créer projet avec tous matchs fixes
    project = models.Project(
        nom="All Fixed",
        sport="Volleyball",
        nb_semaines=5,
        semaine_min=1,
        config_data=sample_config
    )
    test_db.add(project)
    
    match = models.Match(
        project_id=project.id,
        equipe1_nom="Team A",
        equipe2_nom="Team B",
        poule="Poule 1",
        semaine=1,
        horaire="14h00",
        gymnase="Gym A",
        est_fixe=True,
        statut="planifie"
    )
    test_db.add(match)
    test_db.commit()
    
    # Résolution
    service = SolverService(test_db)
    result = service.solve_project(project.id)
    
    # Doit réussir avec message
    assert result['nb_matchs_fixes'] == 1
    assert result['nb_matchs_updated'] == 0
    assert 'message' in result or result['nb_matchs_planifies'] == 1


# ==========================
# Tests SolutionValidator
# ==========================

def test_validator_valid_solution():
    """Test validation d'une solution valide."""
    # Créer des snapshots valides
    match1 = MatchSnapshot(
        id=1,
        equipe1_nom="Team A",
        equipe1_institution="School 1",
        equipe2_nom="Team B",
        equipe2_institution="School 2",
        semaine=2,
        horaire="14h00",
        gymnase="Gym A",
        est_fixe=False
    )
    
    match2 = MatchSnapshot(
        id=2,
        equipe1_nom="Team C",
        equipe1_institution="School 3",
        equipe2_nom="Team D",
        equipe2_institution="School 4",
        semaine=3,
        horaire="14h00",
        gymnase="Gym A",
        est_fixe=False
    )
    
    # Convertir en "pseudo DB models" (utiliser des objets simples)
    class FakeMatch:
        def __init__(self, snapshot):
            self.id = snapshot.id
            self.equipe1_nom = snapshot.equipe1_nom
            self.equipe1_institution = snapshot.equipe1_institution
            self.equipe2_nom = snapshot.equipe2_nom
            self.equipe2_institution = snapshot.equipe2_institution
            self.semaine = snapshot.semaine
            self.horaire = snapshot.horaire
            self.gymnase = snapshot.gymnase
            self.est_fixe = snapshot.est_fixe
    
    fake1 = FakeMatch(match1)
    fake2 = FakeMatch(match2)
    
    validator = SolutionValidator(
        semaine_minimum=2,
        nb_semaines=10,
        matchs_before=[fake1, fake2],
        matchs_after=[fake1, fake2],
        gymnases_capacite={"Gym A": 2}
    )
    
    is_valid, errors = validator.validate()
    
    assert is_valid
    assert len(errors) == 0


def test_validator_detects_fixed_match_modified():
    """Test détection modification match fixe."""
    
    class FakeMatch:
        def __init__(self, id, semaine, horaire, gymnase, est_fixe=False):
            self.id = id
            self.equipe1_nom = "Team A"
            self.equipe1_institution = "School 1"
            self.equipe2_nom = "Team B"
            self.equipe2_institution = "School 2"
            self.semaine = semaine
            self.horaire = horaire
            self.gymnase = gymnase
            self.est_fixe = est_fixe
    
    match_before = FakeMatch(id=1, semaine=1, horaire="14h00", gymnase="Gym A", est_fixe=True)
    match_after = FakeMatch(id=1, semaine=2, horaire="14h00", gymnase="Gym A", est_fixe=True)
    
    validator = SolutionValidator(
        semaine_minimum=1,
        nb_semaines=10,
        matchs_before=[match_before],
        matchs_after=[match_after],
        gymnases_capacite={"Gym A": 1}
    )
    
    is_valid, errors = validator.validate()
    
    assert not is_valid
    assert len(errors) > 0
    assert any("semaine modifiée" in e for e in errors)


def test_validator_detects_semaine_below_minimum():
    """Test détection semaine < semaine_minimum."""
    
    class FakeMatch:
        def __init__(self, id, semaine):
            self.id = id
            self.equipe1_nom = "Team A"
            self.equipe1_institution = None
            self.equipe2_nom = "Team B"
            self.equipe2_institution = None
            self.semaine = semaine
            self.horaire = "14h00"
            self.gymnase = "Gym A"
            self.est_fixe = False
    
    match = FakeMatch(id=1, semaine=1)  # Semaine 1 < semaine_minimum 3
    
    validator = SolutionValidator(
        semaine_minimum=3,
        nb_semaines=10,
        matchs_before=[match],
        matchs_after=[match],
        gymnases_capacite={"Gym A": 1}
    )
    
    is_valid, errors = validator.validate()
    
    assert not is_valid
    assert any("semaine_minimum" in e for e in errors)


def test_validator_detects_team_conflict():
    """Test détection équipe joue 2 fois même semaine."""
    
    class FakeMatch:
        def __init__(self, id, equipe1, equipe2, semaine):
            self.id = id
            self.equipe1_nom = equipe1
            self.equipe1_institution = "School 1"
            self.equipe2_nom = equipe2
            self.equipe2_institution = "School 2"
            self.semaine = semaine
            self.horaire = "14h00"
            self.gymnase = "Gym A"
            self.est_fixe = False
    
    # Team A joue 2 fois semaine 2
    match1 = FakeMatch(id=1, equipe1="Team A", equipe2="Team B", semaine=2)
    match2 = FakeMatch(id=2, equipe1="Team A", equipe2="Team C", semaine=2)
    
    validator = SolutionValidator(
        semaine_minimum=1,
        nb_semaines=10,
        matchs_before=[match1, match2],
        matchs_after=[match1, match2],
        gymnases_capacite={"Gym A": 2}
    )
    
    is_valid, errors = validator.validate()
    
    assert not is_valid
    assert any("joue 2 fois" in e for e in errors)


def test_validator_detects_venue_capacity_exceeded():
    """Test détection capacité gymnase dépassée."""
    
    class FakeMatch:
        def __init__(self, id, semaine, horaire, gymnase):
            self.id = id
            self.equipe1_nom = f"Team {id}A"
            self.equipe1_institution = "School 1"
            self.equipe2_nom = f"Team {id}B"
            self.equipe2_institution = "School 2"
            self.semaine = semaine
            self.horaire = horaire
            self.gymnase = gymnase
            self.est_fixe = False
    
    # 3 matchs même créneau, capacité = 2
    match1 = FakeMatch(id=1, semaine=2, horaire="14h00", gymnase="Gym A")
    match2 = FakeMatch(id=2, semaine=2, horaire="14h00", gymnase="Gym A")
    match3 = FakeMatch(id=3, semaine=2, horaire="14h00", gymnase="Gym A")
    
    validator = SolutionValidator(
        semaine_minimum=1,
        nb_semaines=10,
        matchs_before=[match1, match2, match3],
        matchs_after=[match1, match2, match3],
        gymnases_capacite={"Gym A": 2}  # Capacité = 2, mais 3 matchs
    )
    
    is_valid, errors = validator.validate()
    
    assert not is_valid
    assert any("dépassé" in e for e in errors)


def test_validator_allows_fixed_match_before_minimum():
    """Test que matchs fixes peuvent être avant semaine_minimum."""
    
    class FakeMatch:
        def __init__(self, id, semaine, est_fixe):
            self.id = id
            self.equipe1_nom = "Team A"
            self.equipe1_institution = None
            self.equipe2_nom = "Team B"
            self.equipe2_institution = None
            self.semaine = semaine
            self.horaire = "14h00"
            self.gymnase = "Gym A"
            self.est_fixe = est_fixe
    
    # Match fixe semaine 1, semaine_min = 3
    match_fixe = FakeMatch(id=1, semaine=1, est_fixe=True)
    
    validator = SolutionValidator(
        semaine_minimum=3,
        nb_semaines=10,
        matchs_before=[match_fixe],
        matchs_after=[match_fixe],
        gymnases_capacite={"Gym A": 1}
    )
    
    is_valid, errors = validator.validate()
    
    # Doit être valide (match fixe autorisé avant semaine_min)
    assert is_valid
    assert len(errors) == 0
