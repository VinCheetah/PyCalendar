"""
Tests d'optimisation CP-SAT avec objectifs mesurables.

Ces tests vérifient que l'optimisation produit les résultats attendus
avec des métriques précises et des vérifications quantitatives.
"""

import pytest
from pycalendar.solvers.cpsat_solver import CPSATSolver
from pycalendar.core.penalties import (
    compute_time_preference_penalty,
    compute_gym_preference_penalty,
    compute_gym_level_penalty,
    spacing_penalty_for_gap,
    compaction_penalty_for_week,
    aller_retour_gap_penalty,
)
from .conftest import assert_match_assigned_to, assert_match_not_assigned


class TestOptimizationMetrics:
    """Tests avec métriques quantitatives pour valider l'optimisation."""
    
    def test_optimization_minimizes_total_time_penalty(self, minimal_config, match_builder,
                                                        creneau_builder, gymnase_builder, equipe_builder):
        """
        OBJECTIF: La solution doit minimiser la somme des pénalités horaires.
        
        Scénario:
        - 3 matchs avec préférences horaires différentes
        - 3 créneaux à horaires différents
        - Calcul de la pénalité totale attendue
        
        MÉTRIQUE: Pénalité totale < seuil calculé.
        """
        minimal_config.penalite_apres_horaire_min = 10.0
        minimal_config.penalite_avant_horaire_min = 50.0
        minimal_config.penalite_horaire_tolerance = 0
        minimal_config.penalite_horaire_diviseur = 60
        
        # Équipes avec horaires préférés différents
        equipe_a = equipe_builder.create(horaires_preferes=["18:00"])
        equipe_b = equipe_builder.create(horaires_preferes=["18:00"])
        equipe_c = equipe_builder.create(horaires_preferes=["19:00"])
        equipe_d = equipe_builder.create(horaires_preferes=["19:00"])
        equipe_e = equipe_builder.create(horaires_preferes=["20:00"])
        equipe_f = equipe_builder.create(horaires_preferes=["20:00"])
        
        match1 = match_builder.create(equipe1=equipe_a, equipe2=equipe_b)  # Préfère 18:00
        match2 = match_builder.create(equipe1=equipe_c, equipe2=equipe_d)  # Préfère 19:00
        match3 = match_builder.create(equipe1=equipe_e, equipe2=equipe_f)  # Préfère 20:00
        
        # 3 créneaux aux horaires correspondants
        creneau_18 = creneau_builder.create(semaine=1, horaire="18:00", gymnase="Gym1")
        creneau_19 = creneau_builder.create(semaine=1, horaire="19:00", gymnase="Gym1")
        creneau_20 = creneau_builder.create(semaine=1, horaire="20:00", gymnase="Gym1")
        
        gymnases = gymnase_builder.create_dict(["Gym1"], capacite=1)
        
        solver = CPSATSolver(minimal_config)
        solution = solver.solve([match1, match2, match3], [creneau_18, creneau_19, creneau_20], gymnases)
        
        # VÉRIFICATION: Solution optimale = chaque match à son horaire préféré = pénalité 0
        assert solution.est_complete()
        
        total_penalty = 0.0
        for match in solution.matchs_planifies:
            penalty = compute_time_preference_penalty(match, match.creneau, minimal_config)
            total_penalty += penalty.penalty
        
        # La solution optimale doit avoir pénalité = 0 (chaque match à son horaire)
        assert total_penalty == 0.0, f"Pénalité totale devrait être 0, obtenu {total_penalty}"
    
    def test_optimization_respects_gym_level_hierarchy(self, minimal_config, match_builder,
                                                        creneau_builder, gymnase_builder, equipe_builder):
        """
        OBJECTIF: Matchs haut niveau sur gymnases haut niveau, bas niveau sur gymnases bas niveau.
        
        MÉTRIQUE: Bonus/pénalités de niveau gymnase doivent être minimisées.
        """
        minimal_config.poids_niveaux_gymnases_haut = [-100, -50, 0, 50]  # Bonus pour haut niveau
        minimal_config.poids_niveaux_gymnases_bas = [200, 100, 0, -20]   # Pénalité pour haut niveau
        
        # Matchs de différents niveaux
        equipe_a1 = equipe_builder.create(poule="A1")  # Haut niveau
        equipe_b1 = equipe_builder.create(poule="A1")
        equipe_a4 = equipe_builder.create(poule="A4")  # Bas niveau
        equipe_b4 = equipe_builder.create(poule="A4")
        
        match_haut = match_builder.create(equipe1=equipe_a1, equipe2=equipe_b1, poule="A1")
        match_bas = match_builder.create(equipe1=equipe_a4, equipe2=equipe_b4, poule="A4")
        
        creneau_gym_haut = creneau_builder.create(semaine=1, horaire="18:00", gymnase="Gym_Haut")
        creneau_gym_bas = creneau_builder.create(semaine=1, horaire="18:00", gymnase="Gym_Bas")
        
        gymnases = gymnase_builder.create_dict(["Gym_Haut", "Gym_Bas"])
        niveaux_gymnases = {"Gym_Haut": "haut", "Gym_Bas": "bas"}
        
        solver = CPSATSolver(minimal_config, niveaux_gymnases=niveaux_gymnases)
        solution = solver.solve([match_haut, match_bas], [creneau_gym_haut, creneau_gym_bas], gymnases)
        
        # VÉRIFICATION: Match A1 sur gym haut, match A4 sur gym bas
        assert solution.est_complete()
        assert_match_assigned_to(match_haut, creneau_gym_haut)
        assert_match_assigned_to(match_bas, creneau_gym_bas)
    
    def test_optimization_balances_matches_fairly(self, minimal_config, match_builder,
                                                   creneau_builder, gymnase_builder, equipe_builder):
        """
        OBJECTIF: Équilibrage max-min = maximiser le minimum de matchs par équipe.
        
        Scénario:
        - Équipe A: 3 matchs possibles
        - Équipe B: 1 match possible
        - Équipe C: 1 match possible
        - 2 créneaux disponibles
        
        MÉTRIQUE: Chaque équipe doit avoir au moins 1 match (si possible).
        """
        minimal_config.equilibrage_actif = True
        minimal_config.equilibrage_bonus_base = 1000000
        minimal_config.equilibrage_facteur_decroissance = 0.1  # Très forte décroissance
        minimal_config.equilibrage_bonus_minimum = 1
        
        equipe_a = equipe_builder.create(nom="A")
        equipe_b = equipe_builder.create(nom="B")
        equipe_c = equipe_builder.create(nom="C")
        equipe_d = equipe_builder.create(nom="D")
        
        # A joue beaucoup, B et C jouent peu
        match_a1 = match_builder.create(equipe1=equipe_a, equipe2=equipe_d)
        match_a2 = match_builder.create(equipe1=equipe_a, equipe2=equipe_c)
        match_b1 = match_builder.create(equipe1=equipe_b, equipe2=equipe_d)
        
        creneaux = [
            creneau_builder.create(semaine=1, horaire="18:00", gymnase="Gym1"),
            creneau_builder.create(semaine=2, horaire="18:00", gymnase="Gym1"),
        ]
        gymnases = gymnase_builder.create_dict(["Gym1"])
        
        solver = CPSATSolver(minimal_config)
        solution = solver.solve([match_a1, match_a2, match_b1], creneaux, gymnases)
        
        # VÉRIFICATION: B doit avoir son match (il n'en a qu'un seul)
        assert match_b1.est_planifie(), "Équipe B avec 1 seul match doit être priorisée"
        
        # Et 1 match de A aussi (2 créneaux disponibles)
        matchs_a_planifies = [m for m in [match_a1, match_a2] if m.est_planifie()]
        assert len(matchs_a_planifies) == 1, "1 match de A doit être planifié"


class TestPenaltyCalculationConsistency:
    """Tests de cohérence des calculs de pénalités entre solver et helpers."""
    
    def test_time_penalty_formula_consistency(self, minimal_config, equipe_builder):
        """
        OBJECTIF: Vérifier que la formule de pénalité horaire est cohérente.
        
        Formule: penalty = multiplicateur × ((distance / diviseur)²)
        """
        from pycalendar.core.models import Match, Creneau
        
        minimal_config.penalite_apres_horaire_min = 10.0
        minimal_config.penalite_horaire_tolerance = 0
        minimal_config.penalite_horaire_diviseur = 60.0
        
        equipe1 = equipe_builder.create(horaires_preferes=["18:00"])
        equipe2 = equipe_builder.create(horaires_preferes=["18:00"])
        match = Match(equipe1, equipe2, "A1")
        
        # Test avec différentes distances
        test_cases = [
            ("18:00", 0.0),      # Distance = 0
            ("19:00", 10.0),     # Distance = 60min → penalty = 10 × (60/60)² × 2 = 20
            ("20:00", 40.0),     # Distance = 120min → penalty = 10 × (120/60)² × 2 = 80
            ("21:00", 90.0),     # Distance = 180min → penalty = 10 × (180/60)² × 2 = 180
        ]
        
        for horaire, expected_per_team in test_cases:
            creneau = Creneau(semaine=1, horaire=horaire, gymnase="Gym1")
            result = compute_time_preference_penalty(match, creneau, minimal_config)
            
            # Calcul attendu pour 2 équipes avec même préférence
            expected_total = expected_per_team * 2
            
            assert abs(result.penalty - expected_total) < 0.1, \
                f"Horaire {horaire}: attendu {expected_total}, obtenu {result.penalty}"
    
    def test_spacing_penalty_list_indexing(self, minimal_config):
        """
        OBJECTIF: Vérifier que les pénalités d'espacement utilisent le bon index.
        
        Index = semaines de repos (pas d'écart de semaines)
        """
        minimal_config.penalites_espacement_repos = [100.0, 50.0, 25.0, 0.0]
        
        test_cases = [
            (0, 100.0),   # 0 semaines de repos (matchs consécutifs)
            (1, 50.0),    # 1 semaine de repos
            (2, 25.0),    # 2 semaines de repos
            (3, 0.0),     # 3+ semaines de repos
            (5, 0.0),     # Au-delà de la liste
        ]
        
        for weeks_rest, expected in test_cases:
            penalty = spacing_penalty_for_gap(minimal_config, weeks_rest)
            assert penalty == expected, \
                f"Repos {weeks_rest} semaines: attendu {expected}, obtenu {penalty}"
    
    def test_aller_retour_gap_penalty_list(self, minimal_config):
        """
        OBJECTIF: Vérifier que les pénalités aller-retour utilisent le bon index.
        """
        minimal_config.aller_retour_penalites_par_ecart = [1000.0, 500.0, 100.0, 0.0]
        
        test_cases = [
            (0, 1000.0),  # Même semaine
            (1, 500.0),   # 1 semaine d'écart
            (2, 100.0),   # 2 semaines d'écart
            (3, 0.0),     # 3 semaines d'écart
            (10, 0.0),    # Au-delà de la liste
        ]
        
        for weeks_gap, expected in test_cases:
            penalty = aller_retour_gap_penalty(minimal_config, weeks_gap)
            assert penalty == expected, \
                f"Écart {weeks_gap} semaines: attendu {expected}, obtenu {penalty}"
    
    def test_compaction_penalty_week_indexing(self, minimal_config):
        """
        OBJECTIF: Vérifier que les pénalités de compaction sont correctement indexées.
        
        Index = semaine - 1 (semaine 1 → index 0)
        """
        minimal_config.compaction_penalites_par_semaine = [0.0, 10.0, 20.0, 50.0, 100.0]
        
        test_cases = [
            (1, 0.0),     # Semaine 1 → index 0
            (2, 10.0),    # Semaine 2 → index 1
            (3, 20.0),    # Semaine 3 → index 2
            (4, 50.0),    # Semaine 4 → index 3
            (5, 100.0),   # Semaine 5 → index 4
            (6, 0.0),     # Semaine 6 → au-delà de la liste
        ]
        
        for semaine, expected in test_cases:
            penalty = compaction_penalty_for_week(minimal_config, semaine)
            assert penalty == expected, \
                f"Semaine {semaine}: attendu {expected}, obtenu {penalty}"


class TestSolverScoreReflectsObjective:
    """Tests vérifiant que le score du solver reflète bien la fonction objectif."""
    
    def test_better_solution_has_higher_score(self, minimal_config, match_builder,
                                              creneau_builder, gymnase_builder, equipe_builder):
        """
        OBJECTIF: Plus de matchs planifiés = meilleur score (avec équilibrage).
        
        Scénario: Forcer 2 solutions différentes et comparer les scores.
        """
        minimal_config.equilibrage_actif = True
        minimal_config.equilibrage_bonus_base = 1000
        minimal_config.equilibrage_facteur_decroissance = 0.5
        minimal_config.equilibrage_bonus_minimum = 1
        
        equipe_a = equipe_builder.create()
        equipe_b = equipe_builder.create()
        
        match = match_builder.create(equipe1=equipe_a, equipe2=equipe_b)
        
        # Scénario 1: 1 créneau disponible → 1 match planifié
        creneau = creneau_builder.create(semaine=1, horaire="18:00", gymnase="Gym1")
        gymnases = gymnase_builder.create_dict(["Gym1"])
        
        solver = CPSATSolver(minimal_config)
        solution = solver.solve([match], [creneau], gymnases)
        
        # VÉRIFICATION: Score positif (bonus pour match planifié)
        assert solution.score > 0, f"Score avec match planifié devrait être positif, obtenu {solution.score}"
        
        # Scénario 2: Aucun créneau → score devrait être plus bas
        solution_vide = solver.solve([match], [], gymnases)
        
        # Score avec match planifié > Score sans
        assert solution.score > solution_vide.score, \
            f"Score avec match ({solution.score}) devrait être > score sans ({solution_vide.score})"
    
    def test_penalty_reduces_score(self, minimal_config, match_builder,
                                   creneau_builder, gymnase_builder, equipe_builder):
        """
        OBJECTIF: Une pénalité doit réduire le score final.
        
        Scénario: Comparer score avec/sans pénalité horaire.
        """
        equipe1 = equipe_builder.create(horaires_preferes=["18:00"])
        equipe2 = equipe_builder.create(horaires_preferes=["18:00"])
        match = match_builder.create(equipe1=equipe1, equipe2=equipe2)
        
        gymnases = gymnase_builder.create_dict(["Gym1"])
        
        # Config 1: Pas de pénalité (match à l'horaire exact)
        minimal_config_no_penalty = minimal_config
        minimal_config_no_penalty.penalite_apres_horaire_min = 100
        minimal_config_no_penalty.penalite_horaire_tolerance = 0
        minimal_config_no_penalty.penalite_horaire_diviseur = 60
        
        creneau_exact = creneau_builder.create(semaine=1, horaire="18:00", gymnase="Gym1")
        
        solver1 = CPSATSolver(minimal_config_no_penalty)
        solution_exact = solver1.solve([match], [creneau_exact], gymnases)
        
        # Config 2: Avec pénalité (match éloigné de l'horaire)
        # Réinitialiser le match
        match.creneau = None
        creneau_tard = creneau_builder.create(semaine=1, horaire="21:00", gymnase="Gym1")
        
        solver2 = CPSATSolver(minimal_config_no_penalty)
        solution_tard = solver2.solve([match], [creneau_tard], gymnases)
        
        # Score exact > Score avec pénalité
        assert solution_exact.score > solution_tard.score, \
            f"Score horaire exact ({solution_exact.score}) devrait être > score horaire tardif ({solution_tard.score})"


class TestCoachOverlapPenalties:
    """Tests des pénalités de chevauchement des coachs."""
    
    def test_coach_overlap_penalty_applied(self, minimal_config, match_builder,
                                           creneau_builder, gymnase_builder, equipe_builder):
        """
        OBJECTIF: Pénaliser les matchs simultanés du même coach sur gymnases différents.
        """
        minimal_config.coach_overlap_actif = True
        minimal_config.coach_overlap_penalite_simultane_diff_gym = 100000
        minimal_config.coach_overlap_penalite_simultane_meme_gym = 0
        minimal_config.coach_overlap_simultanee_minutes = 60
        minimal_config.coach_overlap_semaine_min = 1
        
        # Équipes du même coach
        equipe_a = equipe_builder.create(nom="COACH1_EQ1")
        equipe_b = equipe_builder.create(nom="Autre1")
        equipe_c = equipe_builder.create(nom="COACH1_EQ2")
        equipe_d = equipe_builder.create(nom="Autre2")
        
        match1 = match_builder.create(equipe1=equipe_a, equipe2=equipe_b)
        match2 = match_builder.create(equipe1=equipe_c, equipe2=equipe_d)
        
        # Créneaux simultanés sur gymnases différents vs créneaux espacés
        creneau_sim1 = creneau_builder.create(semaine=1, horaire="18:00", gymnase="Gym1")
        creneau_sim2 = creneau_builder.create(semaine=1, horaire="18:00", gymnase="Gym2")
        creneau_seq = creneau_builder.create(semaine=2, horaire="18:00", gymnase="Gym1")
        
        gymnases = gymnase_builder.create_dict(["Gym1", "Gym2"])
        
        from pycalendar.core.models import CoachGroup
        coach_group = CoachGroup(coach_name="Coach1")
        coach_group.team_ids = {equipe_a.id_unique, equipe_c.id_unique}
        coach_groups = {"Coach1": coach_group}
        
        solver = CPSATSolver(minimal_config, coach_groups=coach_groups)
        solution = solver.solve([match1, match2], [creneau_sim1, creneau_sim2, creneau_seq], gymnases)
        
        # VÉRIFICATION: Les matchs ne sont pas simultanés sur gyms différents
        if solution.est_complete():
            # Soit les matchs sont à des semaines différentes, soit sur même gym
            if match1.creneau.semaine == match2.creneau.semaine:
                if match1.creneau.horaire == match2.creneau.horaire:
                    assert match1.creneau.gymnase == match2.creneau.gymnase, \
                        "Matchs simultanés du même coach doivent être sur même gymnase"


class TestEntenteReductionBonus:
    """Tests du système de réduction de bonus pour les ententes."""
    
    def test_entente_has_reduced_priority(self, minimal_config, match_builder,
                                          creneau_builder, gymnase_builder, equipe_builder):
        """
        OBJECTIF: Une entente doit avoir un bonus réduit par rapport à un match normal.
        
        Scénario: 1 créneau, 1 match normal, 1 entente → le match normal doit être priorisé.
        """
        minimal_config.equilibrage_actif = True
        minimal_config.equilibrage_bonus_base = 10000
        minimal_config.equilibrage_facteur_decroissance = 0.5
        minimal_config.equilibrage_bonus_minimum = 1
        minimal_config.entente_actif = True
        minimal_config.entente_facteur_reduction_bonus = 0.5  # 50% de réduction
        
        # Match normal
        equipe_a = equipe_builder.create(institution="INST_A")
        equipe_b = equipe_builder.create(institution="INST_B")
        match_normal = match_builder.create(equipe1=equipe_a, equipe2=equipe_b)
        
        # Entente (même institution)
        equipe_c = equipe_builder.create(institution="INST_C")
        equipe_d = equipe_builder.create(institution="INST_C")  # Même institution
        match_entente = match_builder.create(equipe1=equipe_c, equipe2=equipe_d)
        
        creneau = creneau_builder.create(semaine=1, horaire="18:00", gymnase="Gym1")
        gymnases = gymnase_builder.create_dict(["Gym1"], capacite=1)
        
        ententes = {("INST_C", "INST_C"): None}  # Marquer comme entente
        
        solver = CPSATSolver(minimal_config, ententes=ententes)
        solution = solver.solve([match_normal, match_entente], [creneau], gymnases)
        
        # VÉRIFICATION: Match normal priorisé
        assert match_normal.est_planifie(), "Match normal doit être priorisé sur entente"
        assert not match_entente.est_planifie() or match_entente.creneau is None, \
            "Entente ne doit pas être planifiée sur un créneau (ou activée sans créneau)"


class TestModuleConsistency:
    """Tests de cohérence entre les différents modules de calcul de pénalités."""
    
    def test_extract_match_level_consistency(self):
        """
        OBJECTIF: Vérifier que _extract_match_level est identique entre helpers.py et penalty_breakdown.py.
        
        C'est critique car une incohérence causerait des pénalités différentes
        entre le solveur et l'analyse post-optimisation.
        """
        from pycalendar.core.penalties.helpers import _extract_match_level as helpers_extract
        from pycalendar.analysis.penalty_breakdown import _extract_match_level as breakdown_extract
        from pycalendar.core.models import Match, Equipe
        
        # Créer des matchs de test avec différentes poules
        test_cases = [
            ("A1", 0),    # Niveau 1 → index 0
            ("A2", 1),    # Niveau 2 → index 1
            ("A3", 2),    # Niveau 3 → index 2
            ("A10", 9),   # Niveau 10 → index 9 (important: tester les nombres à 2 chiffres!)
            ("B1", 0),    # Autre préfixe mais même logique
            ("B2-Féminin", 1),  # Avec suffixe
            ("", None),   # Vide
            ("X", None),  # Pas de chiffre
        ]
        
        for poule, expected in test_cases:
            # Créer un match factice (Equipe nécessite nom et poule)
            equipe = Equipe(nom="Test", poule=poule, institution="Test")
            match = Match(equipe, equipe, poule)
            
            helpers_result = helpers_extract(match)
            breakdown_result = breakdown_extract(match)
            
            assert helpers_result == expected, \
                f"helpers._extract_match_level('{poule}') = {helpers_result}, attendu {expected}"
            assert breakdown_result == expected, \
                f"breakdown._extract_match_level('{poule}') = {breakdown_result}, attendu {expected}"
            assert helpers_result == breakdown_result, \
                f"Incohérence pour poule '{poule}': helpers={helpers_result}, breakdown={breakdown_result}"
    
    def test_horaire_to_minutes_consistency(self):
        """
        OBJECTIF: Vérifier que horaire_to_minutes donne des résultats cohérents.
        """
        from pycalendar.core.penalties import horaire_to_minutes
        
        test_cases = [
            ("18:00", 18 * 60),
            ("18:30", 18 * 60 + 30),
            ("9:00", 9 * 60),
            ("09:00", 9 * 60),
            ("18H00", 18 * 60),
            ("18H30", 18 * 60 + 30),
            ("18", 18 * 60),  # Heures seules
            ("", 0),          # Vide
            (None, 0),        # None
        ]
        
        for horaire, expected in test_cases:
            result = horaire_to_minutes(horaire)
            assert result == expected, f"horaire_to_minutes('{horaire}') = {result}, attendu {expected}"
    
    def test_compaction_penalty_boundary(self, minimal_config):
        """
        OBJECTIF: Vérifier le comportement aux limites de la liste de compaction.
        
        Après le dernier index défini, la pénalité doit être 0 (pas de répétition).
        """
        minimal_config.compaction_penalites_par_semaine = [0.0, 10.0, 20.0, 30.0]  # Index 0-3
        
        test_cases = [
            (1, 0.0),    # Index 0
            (2, 10.0),   # Index 1
            (3, 20.0),   # Index 2
            (4, 30.0),   # Index 3 (dernier défini)
            (5, 0.0),    # Index 4 → au-delà → 0
            (10, 0.0),   # Bien au-delà → 0
        ]
        
        for semaine, expected in test_cases:
            result = compaction_penalty_for_week(minimal_config, semaine)
            assert result == expected, \
                f"compaction_penalty_for_week(semaine={semaine}) = {result}, attendu {expected}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
