"""
Tests pour la gestion des matchs fixes dans les solveurs.

Ce module teste que les solveurs CPSATSolver et GreedySolver respectent correctement:
1. Les matchs avec est_fixe=True (verrouillés via UI)
2. Les matchs avec semaine < semaine_minimum (déjà joués/planifiés)
3. Pas de conflits d'équipes (une équipe ne peut pas jouer 2x la même semaine)
4. Non-régression: tout fonctionne normalement sans matchs fixes
"""

import pytest
import yaml
from pathlib import Path
from typing import List, Dict

from core.models import Match, Equipe, Creneau, Gymnase, Solution
from core.config import Config
from solvers.cpsat_solver import CPSATSolver
from solvers.greedy_solver import GreedySolver


@pytest.fixture
def config_base() -> Config:
    """Configuration de base pour les tests."""
    # Charger une config par défaut
    config_path = Path("configs/default.yaml")
    if not config_path.exists():
        pytest.skip("Config file not found")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config_dict = yaml.safe_load(f)
    
    # Forcer quelques paramètres pour les tests
    config_dict['semaine_minimum'] = 5
    config_dict['respecter_matchs_fixes'] = True
    config_dict['afficher_progression'] = False
    config_dict['niveau_log'] = 0
    config_dict['nb_essais'] = 3
    
    # Créer l'objet Config à partir du dict
    config = Config(**config_dict)
    
    return config


@pytest.fixture
def equipes_test() -> List[Equipe]:
    """Créer des équipes de test."""
    equipes = []
    for i in range(6):
        equipe = Equipe(
            nom=f"Équipe{i+1}",
            poule="PouleA",
            institution=f"Institution{(i//2)+1}",
            numero_equipe=str(i+1),
            genre="M"
        )
        equipes.append(equipe)
    
    return equipes


@pytest.fixture
def creneaux_test() -> List[Creneau]:
    """Créer des créneaux de test (semaines 1-10, 2 créneaux/semaine)."""
    creneaux = []
    for semaine in range(1, 11):
        for horaire in ["18:00", "20:00"]:
            creneau = Creneau(
                semaine=semaine,
                horaire=horaire,
                gymnase="Gymnase1"
            )
            creneaux.append(creneau)
    return creneaux


@pytest.fixture
def gymnases_test() -> Dict[str, Gymnase]:
    """Créer des gymnases de test."""
    return {
        "Gymnase1": Gymnase(
            nom="Gymnase1",
            capacite=2,
            horaires_disponibles=["18:00", "20:00"]
        )
    }


def test_cpsat_respect_matchs_fixes(config_base: Config, equipes_test: List[Equipe], 
                                     creneaux_test: List[Creneau], gymnases_test: Dict[str, Gymnase]):
    """
    Test CPSATSolver: Les matchs avec est_fixe=True doivent rester inchangés.
    """
    # Créer 4 matchs: 2 fixes, 2 à planifier
    match_fixe_1 = Match(
        equipe1=equipes_test[0],
        equipe2=equipes_test[1],
        poule="PouleA",
        creneau=Creneau(semaine=3, horaire="18:00", gymnase="Gymnase1"),
        est_fixe=True,
        statut="fixe"
    )
    
    match_fixe_2 = Match(
        equipe1=equipes_test[2],
        equipe2=equipes_test[3],
        poule="PouleA",
        creneau=Creneau(semaine=4, horaire="20:00", gymnase="Gymnase1"),
        est_fixe=True,
        statut="fixe"
    )
    
    match_a_planifier_1 = Match(
        equipe1=equipes_test[4],
        equipe2=equipes_test[5],
        poule="PouleA",
        est_fixe=False,
        statut="a_planifier"
    )
    
    match_a_planifier_2 = Match(
        equipe1=equipes_test[0],
        equipe2=equipes_test[2],
        poule="PouleA",
        est_fixe=False,
        statut="a_planifier"
    )
    
    matchs = [match_fixe_1, match_fixe_2, match_a_planifier_1, match_a_planifier_2]
    
    # Résoudre
    solver = CPSATSolver(config_base)
    solution = solver.solve(matchs, creneaux_test, gymnases_test)
    
    # Vérifications
    assert solution is not None
    
    # Les matchs fixes doivent être dans la solution et inchangés
    matchs_fixes_solution = [m for m in solution.matchs_planifies if m.est_fixe]
    assert len(matchs_fixes_solution) == 2
    
    # Vérifier que les créneaux des matchs fixes n'ont pas changé
    for match in solution.matchs_planifies:
        if match.est_fixe:
            if match == match_fixe_1:
                assert match.creneau is not None
                assert match.creneau.semaine == 3
                assert match.creneau.horaire == "18:00"
            elif match == match_fixe_2:
                assert match.creneau is not None
                assert match.creneau.semaine == 4
                assert match.creneau.horaire == "20:00"
    
    # Les matchs modifiables doivent être planifiés
    matchs_modifiables_solution = [m for m in solution.matchs_planifies if not m.est_fixe]
    assert len(matchs_modifiables_solution) >= 1  # Au moins 1 planifié


def test_cpsat_semaine_minimum(config_base: Config, equipes_test: List[Equipe], 
                                creneaux_test: List[Creneau], gymnases_test: Dict[str, Gymnase]):
    """
    Test CPSATSolver: Les matchs avec semaine < semaine_minimum doivent être traités comme fixes.
    """
    # Match planifié avant semaine_minimum (semaine 3 < semaine_minimum=5)
    match_avant_semaine_min = Match(
        equipe1=equipes_test[0],
        equipe2=equipes_test[1],
        poule="PouleA",
        creneau=Creneau(semaine=3, horaire="18:00", gymnase="Gymnase1"),
        est_fixe=False,  # Pas explicitement fixe
        statut="planifie"
    )
    
    # Match à planifier
    match_a_planifier = Match(
        equipe1=equipes_test[2],
        equipe2=equipes_test[3],
        poule="PouleA",
        est_fixe=False,
        statut="a_planifier"
    )
    
    matchs = [match_avant_semaine_min, match_a_planifier]
    
    # Résoudre
    solver = CPSATSolver(config_base)
    solution = solver.solve(matchs, creneaux_test, gymnases_test)
    
    # Vérifications
    assert solution is not None
    
    # Le match avant semaine_minimum doit rester inchangé
    for match in solution.matchs_planifies:
        if match == match_avant_semaine_min:
            assert match.creneau is not None
            assert match.creneau.semaine == 3
            assert match.creneau.horaire == "18:00"
    
    # Le match à planifier doit être planifié à partir de semaine_minimum
    for match in solution.matchs_planifies:
        if match == match_a_planifier:
            assert match.creneau is not None
            assert match.creneau.semaine >= config_base.semaine_minimum


def test_cpsat_eviter_conflits_equipes(config_base: Config, equipes_test: List[Equipe], 
                                        creneaux_test: List[Creneau], gymnases_test: Dict[str, Gymnase]):
    """
    Test CPSATSolver: Une équipe dans un match fixe ne peut pas jouer ailleurs la même semaine.
    """
    # Match fixe avec Équipe 1 et Équipe 2 en semaine 6
    match_fixe = Match(
        equipe1=equipes_test[0],  # Équipe 1
        equipe2=equipes_test[1],  # Équipe 2
        poule="PouleA",
        creneau=Creneau(semaine=6, horaire="18:00", gymnase="Gymnase1"),
        est_fixe=True,
        statut="fixe"
    )
    
    # Match à planifier avec Équipe 1 (doit éviter semaine 6)
    match_avec_equipe_1 = Match(
        equipe1=equipes_test[0],  # Équipe 1 (conflit!)
        equipe2=equipes_test[3],  # Équipe 4
        poule="PouleA",
        est_fixe=False,
        statut="a_planifier"
    )
    
    # Match à planifier avec Équipe 2 (doit éviter semaine 6)
    match_avec_equipe_2 = Match(
        equipe1=equipes_test[4],  # Équipe 5
        equipe2=equipes_test[1],  # Équipe 2 (conflit!)
        poule="PouleA",
        est_fixe=False,
        statut="a_planifier"
    )
    
    matchs = [match_fixe, match_avec_equipe_1, match_avec_equipe_2]
    
    # Résoudre
    solver = CPSATSolver(config_base)
    solution = solver.solve(matchs, creneaux_test, gymnases_test)
    
    # Vérifications
    assert solution is not None
    
    # Vérifier que les équipes du match fixe ne jouent pas ailleurs en semaine 6
    for match in solution.matchs_planifies:
        if match != match_fixe and match.creneau:
            if match.creneau.semaine == 6:
                # Aucune équipe du match fixe ne doit jouer
                assert match.equipe1.id_unique != equipes_test[0].id_unique
                assert match.equipe2.id_unique != equipes_test[0].id_unique
                assert match.equipe1.id_unique != equipes_test[1].id_unique
                assert match.equipe2.id_unique != equipes_test[1].id_unique


def test_greedy_respect_matchs_fixes(config_base: Config, equipes_test: List[Equipe], 
                                      creneaux_test: List[Creneau], gymnases_test: Dict[str, Gymnase]):
    """
    Test GreedySolver: Les matchs avec est_fixe=True doivent rester inchangés.
    """
    # Créer 4 matchs: 2 fixes, 2 à planifier
    match_fixe_1 = Match(
        equipe1=equipes_test[0],
        equipe2=equipes_test[1],
        poule="PouleA",
        creneau=Creneau(semaine=3, horaire="18:00", gymnase="Gymnase1"),
        est_fixe=True,
        statut="fixe"
    )
    
    match_fixe_2 = Match(
        equipe1=equipes_test[2],
        equipe2=equipes_test[3],
        poule="PouleA",
        creneau=Creneau(semaine=4, horaire="20:00", gymnase="Gymnase1"),
        est_fixe=True,
        statut="fixe"
    )
    
    match_a_planifier_1 = Match(
        equipe1=equipes_test[4],
        equipe2=equipes_test[5],
        poule="PouleA",
        est_fixe=False,
        statut="a_planifier"
    )
    
    match_a_planifier_2 = Match(
        equipe1=equipes_test[0],
        equipe2=equipes_test[2],
        poule="PouleA",
        est_fixe=False,
        statut="a_planifier"
    )
    
    matchs = [match_fixe_1, match_fixe_2, match_a_planifier_1, match_a_planifier_2]
    
    # Résoudre
    solver = GreedySolver(config_base)
    solution = solver.solve(matchs, creneaux_test, gymnases_test)
    
    # Vérifications
    assert solution is not None
    
    # Les matchs fixes doivent être dans la solution et inchangés
    matchs_fixes_solution = [m for m in solution.matchs_planifies if m.est_fixe]
    assert len(matchs_fixes_solution) == 2
    
    # Vérifier que les créneaux des matchs fixes n'ont pas changé
    for match in solution.matchs_planifies:
        if match.est_fixe:
            if match == match_fixe_1:
                assert match.creneau is not None
                assert match.creneau.semaine == 3
                assert match.creneau.horaire == "18:00"
            elif match == match_fixe_2:
                assert match.creneau is not None
                assert match.creneau.semaine == 4
                assert match.creneau.horaire == "20:00"


def test_greedy_eviter_conflits_equipes(config_base: Config, equipes_test: List[Equipe], 
                                         creneaux_test: List[Creneau], gymnases_test: Dict[str, Gymnase]):
    """
    Test GreedySolver: Une équipe dans un match fixe ne peut pas jouer ailleurs la même semaine.
    """
    # Match fixe avec Équipe 1 et Équipe 2 en semaine 6
    match_fixe = Match(
        equipe1=equipes_test[0],  # Équipe 1
        equipe2=equipes_test[1],  # Équipe 2
        poule="PouleA",
        creneau=Creneau(semaine=6, horaire="18:00", gymnase="Gymnase1"),
        est_fixe=True,
        statut="fixe"
    )
    
    # Match à planifier avec Équipe 1 (doit éviter semaine 6)
    match_avec_equipe_1 = Match(
        equipe1=equipes_test[0],  # Équipe 1 (conflit!)
        equipe2=equipes_test[3],  # Équipe 4
        poule="PouleA",
        est_fixe=False,
        statut="a_planifier"
    )
    
    # Match à planifier avec Équipe 2 (doit éviter semaine 6)
    match_avec_equipe_2 = Match(
        equipe1=equipes_test[4],  # Équipe 5
        equipe2=equipes_test[1],  # Équipe 2 (conflit!)
        poule="PouleA",
        est_fixe=False,
        statut="a_planifier"
    )
    
    matchs = [match_fixe, match_avec_equipe_1, match_avec_equipe_2]
    
    # Résoudre
    solver = GreedySolver(config_base)
    solution = solver.solve(matchs, creneaux_test, gymnases_test)
    
    # Vérifications
    assert solution is not None
    
    # Vérifier que les équipes du match fixe ne jouent pas ailleurs en semaine 6
    for match in solution.matchs_planifies:
        if match != match_fixe and match.creneau:
            if match.creneau.semaine == 6:
                # Aucune équipe du match fixe ne doit jouer
                assert match.equipe1.id_unique != equipes_test[0].id_unique
                assert match.equipe2.id_unique != equipes_test[0].id_unique
                assert match.equipe1.id_unique != equipes_test[1].id_unique
                assert match.equipe2.id_unique != equipes_test[1].id_unique


def test_non_regression_sans_matchs_fixes(config_base: Config, equipes_test: List[Equipe], 
                                           creneaux_test: List[Creneau], gymnases_test: Dict[str, Gymnase]):
    """
    Test de non-régression: Les solveurs doivent fonctionner normalement sans matchs fixes.
    """
    # Créer 6 matchs normaux (aucun fixe)
    matchs = []
    for i in range(6):
        match = Match(
            equipe1=equipes_test[i % 6],
            equipe2=equipes_test[(i + 1) % 6],
            poule="PouleA",
            est_fixe=False,
            statut="a_planifier"
        )
        matchs.append(match)
    
    # Test CPSATSolver
    solver_cpsat = CPSATSolver(config_base)
    solution_cpsat = solver_cpsat.solve(matchs.copy(), creneaux_test, gymnases_test)
    
    assert solution_cpsat is not None
    assert len(solution_cpsat.matchs_planifies) >= 4  # Au moins 4 matchs planifiés
    
    # Tous les matchs planifiés doivent avoir un créneau
    for match in solution_cpsat.matchs_planifies:
        assert match.creneau is not None
        assert match.creneau.semaine >= config_base.semaine_minimum
    
    # Test GreedySolver
    solver_greedy = GreedySolver(config_base)
    solution_greedy = solver_greedy.solve(matchs.copy(), creneaux_test, gymnases_test)
    
    assert solution_greedy is not None
    assert len(solution_greedy.matchs_planifies) >= 4  # Au moins 4 matchs planifiés
    
    # Tous les matchs planifiés doivent avoir un créneau
    for match in solution_greedy.matchs_planifies:
        assert match.creneau is not None
        assert match.creneau.semaine >= config_base.semaine_minimum


def test_creneaux_reserves_non_utilises(config_base: Config, equipes_test: List[Equipe], 
                                         creneaux_test: List[Creneau], gymnases_test: Dict[str, Gymnase]):
    """
    Test: Les créneaux réservés par matchs fixes ne doivent pas être réutilisés.
    """
    # Match fixe occupant le créneau (semaine=6, horaire=18:00)
    match_fixe = Match(
        equipe1=equipes_test[0],
        equipe2=equipes_test[1],
        poule="PouleA",
        creneau=Creneau(semaine=6, horaire="18:00", gymnase="Gymnase1"),
        est_fixe=True,
        statut="fixe"
    )
    
    # 3 matchs à planifier (ne doivent pas utiliser semaine=6, horaire=18:00)
    matchs_a_planifier = [
        Match(equipe1=equipes_test[2], equipe2=equipes_test[3], poule="PouleA", est_fixe=False, statut="a_planifier"),
        Match(equipe1=equipes_test[4], equipe2=equipes_test[5], poule="PouleA", est_fixe=False, statut="a_planifier"),
        Match(equipe1=equipes_test[0], equipe2=equipes_test[4], poule="PouleA", est_fixe=False, statut="a_planifier"),
    ]
    
    matchs = [match_fixe] + matchs_a_planifier
    
    # Test CPSATSolver
    solver_cpsat = CPSATSolver(config_base)
    solution_cpsat = solver_cpsat.solve(matchs, creneaux_test, gymnases_test)
    
    # Vérifier qu'aucun match modifiable n'utilise le créneau réservé
    for match in solution_cpsat.matchs_planifies:
        if not match.est_fixe and match.creneau:
            # Ne doit pas être exactement le même créneau (semaine + horaire + gymnase)
            if match.creneau.semaine == 6 and match.creneau.horaire == "18:00":
                # OK si gymnase différent, mais ici on n'a qu'un gymnase
                assert match.creneau.gymnase != "Gymnase1"
    
    # Test GreedySolver
    solver_greedy = GreedySolver(config_base)
    solution_greedy = solver_greedy.solve(matchs, creneaux_test, gymnases_test)
    
    # Vérifier qu'aucun match modifiable n'utilise le créneau réservé
    for match in solution_greedy.matchs_planifies:
        if not match.est_fixe and match.creneau:
            if match.creneau.semaine == 6 and match.creneau.horaire == "18:00":
                assert match.creneau.gymnase != "Gymnase1"
