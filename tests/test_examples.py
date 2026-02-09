"""
Guide : Comment écrire un test CP-SAT avec pytest
==================================================

Ce guide vous montre comment créer un nouveau test pour valider
le comportement du solveur CP-SAT sur un cas synthétique simple.
"""

import pytest
from pycalendar.solvers.cpsat_solver import CPSATSolver
from tests.conftest import assert_match_assigned_to, assert_match_not_assigned


# =============================================================================
# EXEMPLE 1 : Test de base (contraintes dures)
# =============================================================================

def test_exemple_contrainte_capacite(minimal_config, match_builder, 
                                     creneau_builder, gymnase_builder):
    """
    SCENARIO : 3 matchs, 1 gymnase capacité=2, 1 créneau
    
    SOLUTION OPTIMALE ATTENDUE :
        - Exactement 2 matchs planifiés (limite de capacité)
        - 1 match non planifié
    
    CE QU'ON TESTE :
        - Contrainte dure de capacité respectée
    """
    # -------------------------------------------------------------------------
    # 1. SETUP : Créer les données du test
    # -------------------------------------------------------------------------
    
    # Créer 3 matchs différents (équipes auto-générées)
    match1 = match_builder.create()
    match2 = match_builder.create()
    match3 = match_builder.create()
    
    # Créer 1 créneau dans un gymnase
    creneau = creneau_builder.create(semaine=1, horaire="18:00", gymnase="Gym1")
    
    # Créer le gymnase avec capacité=2
    gymnases = gymnase_builder.create_dict(["Gym1"], capacite=2)
    
    # -------------------------------------------------------------------------
    # 2. RÉSOLUTION : Lancer CP-SAT
    # -------------------------------------------------------------------------
    
    solver = CPSATSolver(minimal_config)
    solution = solver.solve(
        matchs=[match1, match2, match3],
        creneaux=[creneau],
        gymnases=gymnases
    )
    
    # -------------------------------------------------------------------------
    # 3. VÉRIFICATIONS : Tester la solution
    # -------------------------------------------------------------------------
    
    # Compter combien de matchs planifiés
    matchs_planifies = [m for m in [match1, match2, match3] if m.est_planifie()]
    
    assert len(matchs_planifies) == 2, \
        f"Capacité=2 devrait permettre 2 matchs, mais {len(matchs_planifies)} planifiés"
    
    # Vérifier qu'ils sont bien au bon créneau
    for match in matchs_planifies:
        assert_match_assigned_to(match, creneau)


# =============================================================================
# EXEMPLE 2 : Test de pénalités (optimisation)
# =============================================================================

def test_exemple_penalite_horaire(minimal_config, match_builder, 
                                  creneau_builder, gymnase_builder, equipe_builder):
    """
    SCENARIO : 1 match, 2 créneaux (18h et 20h), équipes préfèrent 18h
    
    SOLUTION OPTIMALE ATTENDUE :
        - Match planifié à 18:00 (horaire préféré = pénalité nulle)
    
    CE QU'ON TESTE :
        - Le solver minimise les pénalités horaires
        - Choix du créneau avec pénalité minimale
    """
    # -------------------------------------------------------------------------
    # 1. CONFIGURATION : Activer les pénalités horaires
    # -------------------------------------------------------------------------
    
    minimal_config.penalite_apres_horaire_min = 100  # Pénalité si après 18h
    minimal_config.penalite_horaire_tolerance = 0
    minimal_config.penalite_horaire_diviseur = 60
    
    # -------------------------------------------------------------------------
    # 2. SETUP : Créer les équipes avec préférences
    # -------------------------------------------------------------------------
    
    # Les 2 équipes préfèrent jouer à 18:00
    equipe1 = equipe_builder.create(
        nom="Équipe A",
        horaires_preferes=["18:00"]
    )
    equipe2 = equipe_builder.create(
        nom="Équipe B", 
        horaires_preferes=["18:00"]
    )
    
    match = match_builder.create(equipe1=equipe1, equipe2=equipe2)
    
    # -------------------------------------------------------------------------
    # 3. SETUP : Créer les créneaux
    # -------------------------------------------------------------------------
    
    # Créneau préféré (pénalité = 0)
    creneau_18h = creneau_builder.create(semaine=1, horaire="18:00", gymnase="Gym1")
    
    # Créneau non préféré (pénalité > 0)
    creneau_20h = creneau_builder.create(semaine=1, horaire="20:00", gymnase="Gym1")
    
    gymnases = gymnase_builder.create_dict(["Gym1"])
    
    # -------------------------------------------------------------------------
    # 4. RÉSOLUTION
    # -------------------------------------------------------------------------
    
    solver = CPSATSolver(minimal_config)
    solution = solver.solve(
        matchs=[match],
        creneaux=[creneau_18h, creneau_20h],
        gymnases=gymnases
    )
    
    # -------------------------------------------------------------------------
    # 5. VÉRIFICATIONS
    # -------------------------------------------------------------------------
    
    assert solution.est_complete(), "Solution devrait être complète"
    
    # DOIT choisir 18:00 (pénalité nulle vs pénalité de 100)
    assert_match_assigned_to(match, creneau_18h)


# =============================================================================
# EXEMPLE 3 : Test de bonus (optimisation)
# =============================================================================

def test_exemple_bonus_gymnase(minimal_config, match_builder, 
                               creneau_builder, gymnase_builder, equipe_builder):
    """
    SCENARIO : 1 match, 2 créneaux dans gymnases différents
               Équipes préfèrent GymA
    
    SOLUTION OPTIMALE ATTENDUE :
        - Match dans GymA (bonus maximal)
    
    CE QU'ON TESTE :
        - Le solver maximise les bonus de préférences gymnase
    """
    # -------------------------------------------------------------------------
    # 1. CONFIGURATION : Activer les bonus gymnases
    # -------------------------------------------------------------------------
    
    minimal_config.bonus_preferences_gymnases = [100, 50, 10]  # Rang 1, 2, 3
    
    # -------------------------------------------------------------------------
    # 2. SETUP : Équipes avec préférences gymnase
    # -------------------------------------------------------------------------
    
    equipe1 = equipe_builder.create(
        lieux_preferes=["GymA", "GymB"]  # Préfère GymA en 1er
    )
    equipe2 = equipe_builder.create(
        lieux_preferes=["GymA"]  # Préfère GymA
    )
    
    match = match_builder.create(equipe1=equipe1, equipe2=equipe2)
    
    # -------------------------------------------------------------------------
    # 3. SETUP : Créneaux dans gymnases différents
    # -------------------------------------------------------------------------
    
    creneau_gymA = creneau_builder.create(semaine=1, horaire="18:00", gymnase="GymA")
    creneau_gymB = creneau_builder.create(semaine=1, horaire="18:00", gymnase="GymB")
    
    gymnases = gymnase_builder.create_dict(["GymA", "GymB"])
    
    # -------------------------------------------------------------------------
    # 4. RÉSOLUTION
    # -------------------------------------------------------------------------
    
    solver = CPSATSolver(minimal_config)
    solution = solver.solve(
        matchs=[match],
        creneaux=[creneau_gymA, creneau_gymB],
        gymnases=gymnases
    )
    
    # -------------------------------------------------------------------------
    # 5. VÉRIFICATIONS
    # -------------------------------------------------------------------------
    
    # GymA donne bonus 100+100 = 200
    # GymB donne bonus 50 seulement (2ème choix de equipe1, pas dans liste de equipe2)
    # → DOIT choisir GymA
    assert_match_assigned_to(match, creneau_gymA)


# =============================================================================
# EXEMPLE 4 : Test d'équilibrage (bonus progressif)
# =============================================================================

def test_exemple_equilibrage(minimal_config, match_builder, 
                             creneau_builder, gymnase_builder, equipe_builder):
    """
    SCENARIO : Équipe A joue 2 matchs, équipe B joue 1 match
               Seulement 2 créneaux disponibles
    
    SOLUTION OPTIMALE ATTENDUE :
        - Match de B planifié (priorité max-min)
        - 1 seul match de A planifié
    
    CE QU'ON TESTE :
        - Système d'équilibrage progressif (max-min fairness)
    """
    # -------------------------------------------------------------------------
    # 1. CONFIGURATION : Activer équilibrage
    # -------------------------------------------------------------------------
    
    minimal_config.equilibrage_actif = True
    minimal_config.equilibrage_bonus_base = 1000000
    minimal_config.equilibrage_facteur_decroissance = 0.3
    
    # -------------------------------------------------------------------------
    # 2. SETUP : Matchs avec déséquilibre
    # -------------------------------------------------------------------------
    
    equipe_a = equipe_builder.create(nom="A")
    equipe_b = equipe_builder.create(nom="B")
    equipe_c = equipe_builder.create(nom="C")
    equipe_d = equipe_builder.create(nom="D")
    
    # A joue 2 matchs
    match_a1 = match_builder.create(equipe1=equipe_a, equipe2=equipe_c)
    match_a2 = match_builder.create(equipe1=equipe_a, equipe2=equipe_d)
    
    # B joue 1 seul match
    match_b = match_builder.create(equipe1=equipe_b, equipe2=equipe_c)
    
    # -------------------------------------------------------------------------
    # 3. SETUP : Seulement 2 créneaux (conflit)
    # -------------------------------------------------------------------------
    
    creneaux = [
        creneau_builder.create(semaine=1, horaire="18:00", gymnase="Gym1"),
        creneau_builder.create(semaine=2, horaire="18:00", gymnase="Gym1")
    ]
    
    gymnases = gymnase_builder.create_dict(["Gym1"])
    
    # -------------------------------------------------------------------------
    # 4. RÉSOLUTION
    # -------------------------------------------------------------------------
    
    solver = CPSATSolver(minimal_config)
    solution = solver.solve(
        matchs=[match_a1, match_a2, match_b],
        creneaux=creneaux,
        gymnases=gymnases
    )
    
    # -------------------------------------------------------------------------
    # 5. VÉRIFICATIONS
    # -------------------------------------------------------------------------
    
    # B n'a qu'1 match → priorité maximale (max-min)
    assert match_b.est_planifie(), \
        "Match de B devrait être planifié (équilibrage)"
    
    # A a 2 matchs → 1 seul planifié
    matchs_a = [match_a1, match_a2]
    matchs_a_planifies = [m for m in matchs_a if m.est_planifie()]
    
    assert len(matchs_a_planifies) == 1, \
        f"A devrait avoir 1 match planifié, mais {len(matchs_a_planifies)} obtenus"


# =============================================================================
# EXEMPLE 5 : Test de fonction de calcul (unitaire)
# =============================================================================

def test_exemple_fonction_calcul(minimal_config, equipe_builder):
    """
    Test UNITAIRE d'une fonction de calcul de pénalité.
    
    CE QU'ON TESTE :
        - Formule mathématique de calcul de pénalité horaire
        - Sans lancer CP-SAT (test rapide et déterministe)
    """
    from pycalendar.core.models import Match, Creneau
    
    # -------------------------------------------------------------------------
    # 1. CONFIGURATION
    # -------------------------------------------------------------------------
    
    minimal_config.penalite_apres_horaire_min = 10
    minimal_config.penalite_horaire_tolerance = 0
    minimal_config.penalite_horaire_diviseur = 60
    
    # -------------------------------------------------------------------------
    # 2. SETUP : Match avec horaires préférés
    # -------------------------------------------------------------------------
    
    equipe1 = equipe_builder.create(horaires_preferes=["18:00"])
    equipe2 = equipe_builder.create(horaires_preferes=["18:00"])
    
    match = Match(equipe1, equipe2, "A1")
    
    # Créneau 2h APRÈS l'horaire préféré (18:00 → 20:00)
    creneau = Creneau(semaine=1, horaire="20:00", gymnase="Gym1")
    
    # -------------------------------------------------------------------------
    # 3. CALCUL : Appeler directement la fonction helper
    # -------------------------------------------------------------------------
    
    from pycalendar.core.penalties import compute_time_preference_penalty
    result = compute_time_preference_penalty(match, creneau, minimal_config)
    
    # -------------------------------------------------------------------------
    # 4. VÉRIFICATION : Comparer avec formule attendue
    # -------------------------------------------------------------------------
    
    # Formule : multiplicateur × ((distance / diviseur)²) × nb_équipes
    # distance = 120 min (2h)
    # diviseur = 60
    # multiplicateur = 10 (apres_horaire_min)
    # nb_équipes = 2
    
    expected = 10 * ((120 / 60) ** 2) * 2  # = 10 × 4 × 2 = 80
    
    assert abs(result.penalty - expected) < 0.01, \
        f"Pénalité calculée = {result.penalty}, attendue = {expected}"


# =============================================================================
# CONSEILS POUR ÉCRIRE VOS PROPRES TESTS
# =============================================================================

"""
1. UN TEST = UN COMPORTEMENT
   - Testez une seule chose à la fois
   - Désactivez tout sauf ce que vous testez

2. SOLUTION CONNUE À L'AVANCE
   - Créez un cas où la solution optimale est ÉVIDENTE
   - Expliquez pourquoi cette solution est optimale dans la docstring

3. DONNÉES MINIMALES
   - Utilisez le moins de matchs/créneaux possible
   - Gardez le test simple et compréhensible

4. CONFIGURATION MINIMALE
   - Partez de `minimal_config` (tout désactivé)
   - Activez uniquement ce que vous testez

5. DOCSTRING CLAIRE
   - Décrivez le SCENARIO
   - Indiquez la SOLUTION OPTIMALE ATTENDUE
   - Expliquez CE QU'ON TESTE

6. ASSERTIONS EXPLICITES
   - Utilisez des messages d'erreur clairs
   - Expliquez POURQUOI l'assertion devrait passer

7. TESTS RAPIDES
   - `minimal_config.temps_max_secondes = 5` (déjà configuré)
   - Tests simples = résolution quasi-instantanée

8. NOMS DE TESTS DESCRIPTIFS
   - `test_prefers_exact_time_match` ✅
   - `test_penalty_calculation` ❌ (trop vague)
"""

# =============================================================================
# LANCER CES EXEMPLES
# =============================================================================

"""
# Tous les exemples :
pytest tests/test_examples.py -v

# Un seul exemple :
pytest tests/test_examples.py::test_exemple_contrainte_capacite -v

# Avec sortie détaillée :
pytest tests/test_examples.py -v -s
"""
