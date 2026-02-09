"""
Tests des pénalités et préférences du solveur CP-SAT.

Ces tests vérifient que le solveur choisit correctement les créneaux
en fonction des pénalités et bonus configurés.
"""

import pytest
from pycalendar.solvers.cpsat_solver import CPSATSolver
from .conftest import assert_match_assigned_to


class TestTimePreferencePenalties:
    """Tests des pénalités d'horaires préférés."""
    
    def test_prefers_exact_time_match(self, minimal_config, match_builder,
                                      creneau_builder, gymnase_builder, equipe_builder):
        """
        1 match, 2 créneaux : un à l'horaire préféré, un autre
        
        Solution optimale : Créneau à l'horaire préféré (pénalité = 0).
        """
        # Configuration : activer pénalités horaires
        minimal_config.penalite_apres_horaire_min = 100  # Pénalité si pas l'horaire préféré
        minimal_config.penalite_horaire_tolerance = 0  # Pas de tolérance
        minimal_config.penalite_horaire_diviseur = 60
        
        # Setup : équipes préfèrent 18:00
        equipe1 = equipe_builder.create(horaires_preferes=["18:00"])
        equipe2 = equipe_builder.create(horaires_preferes=["18:00"])
        match = match_builder.create(equipe1=equipe1, equipe2=equipe2)
        
        creneau_prefere = creneau_builder.create(semaine=1, horaire="18:00", gymnase="Gym1")
        creneau_autre = creneau_builder.create(semaine=1, horaire="20:00", gymnase="Gym1")
        
        gymnases = gymnase_builder.create_dict(["Gym1"])
        
        # Résolution
        solver = CPSATSolver(minimal_config)
        solution = solver.solve([match], [creneau_prefere, creneau_autre], gymnases)
        
        # Vérification : DOIT choisir 18:00 (pénalité nulle)
        assert solution.est_complete()
        assert_match_assigned_to(match, creneau_prefere)
    
    def test_within_tolerance_no_penalty(self, minimal_config, match_builder,
                                        creneau_builder, gymnase_builder, equipe_builder):
        """
        Horaire dans la fenêtre de tolérance → pas de pénalité
        
        Solution optimale : Les 2 créneaux sont équivalents (dans tolérance).
        """
        # Configuration
        minimal_config.penalite_apres_horaire_min = 100
        minimal_config.penalite_horaire_tolerance = 60  # Tolérance = 60 minutes
        minimal_config.penalite_horaire_diviseur = 60
        
        # Setup : équipes préfèrent 18:00, créneaux à 18:00 et 18:30 (30 min de diff)
        equipe1 = equipe_builder.create(horaires_preferes=["18:00"])
        equipe2 = equipe_builder.create(horaires_preferes=["18:00"])
        match = match_builder.create(equipe1=equipe1, equipe2=equipe2)
        
        creneau1 = creneau_builder.create(semaine=1, horaire="18:00", gymnase="Gym1")
        creneau2 = creneau_builder.create(semaine=1, horaire="18:30", gymnase="Gym1")
        
        gymnases = gymnase_builder.create_dict(["Gym1"])
        
        # Résolution
        solver = CPSATSolver(minimal_config)
        solution = solver.solve([match], [creneau1, creneau2], gymnases)
        
        # Vérification : match planifié (peu importe lequel, les 2 dans tolérance)
        assert solution.est_complete()
        assert match.est_planifie()
    
    def test_penalty_increases_with_distance(self, minimal_config, match_builder,
                                             creneau_builder, gymnase_builder, equipe_builder):
        """
        Plus l'horaire est éloigné du préféré, plus la pénalité est grande
        
        Solution optimale : Créneau le plus proche de l'horaire préféré.
        """
        # Configuration
        minimal_config.penalite_apres_horaire_min = 10
        minimal_config.penalite_horaire_tolerance = 0
        minimal_config.penalite_horaire_diviseur = 60
        
        # Setup : équipes préfèrent 18:00
        equipe1 = equipe_builder.create(horaires_preferes=["18:00"])
        equipe2 = equipe_builder.create(horaires_preferes=["18:00"])
        match = match_builder.create(equipe1=equipe1, equipe2=equipe2)
        
        creneau_proche = creneau_builder.create(semaine=1, horaire="19:00", gymnase="Gym1")  # +1h
        creneau_loin = creneau_builder.create(semaine=1, horaire="21:00", gymnase="Gym1")    # +3h
        
        gymnases = gymnase_builder.create_dict(["Gym1"])
        
        # Résolution
        solver = CPSATSolver(minimal_config)
        solution = solver.solve([match], [creneau_proche, creneau_loin], gymnases)
        
        # Vérification : DOIT choisir 19:00 (plus proche = moins de pénalité)
        assert solution.est_complete()
        assert_match_assigned_to(match, creneau_proche)
    
    def test_before_preferred_time_higher_penalty(self, minimal_config, match_builder,
                                                  creneau_builder, gymnase_builder, equipe_builder):
        """
        Jouer AVANT l'horaire préféré a une pénalité plus forte qu'APRÈS
        
        Solution optimale : Créneau après (pénalité plus faible).
        """
        # Configuration
        minimal_config.penalite_avant_horaire_min = 100  # Forte pénalité avant
        minimal_config.penalite_apres_horaire_min = 10   # Faible pénalité après
        minimal_config.penalite_horaire_tolerance = 0
        minimal_config.penalite_horaire_diviseur = 60
        
        # Setup : équipes préfèrent 18:00
        equipe1 = equipe_builder.create(horaires_preferes=["18:00"])
        equipe2 = equipe_builder.create(horaires_preferes=["18:00"])
        match = match_builder.create(equipe1=equipe1, equipe2=equipe2)
        
        creneau_avant = creneau_builder.create(semaine=1, horaire="16:00", gymnase="Gym1")  # -2h
        creneau_apres = creneau_builder.create(semaine=1, horaire="20:00", gymnase="Gym1")  # +2h
        
        gymnases = gymnase_builder.create_dict(["Gym1"])
        
        # Résolution
        solver = CPSATSolver(minimal_config)
        solution = solver.solve([match], [creneau_avant, creneau_apres], gymnases)
        
        # Vérification : DOIT choisir 20:00 (après = moins pire)
        assert solution.est_complete()
        assert_match_assigned_to(match, creneau_apres)


class TestGymPreferenceBonus:
    """Tests des bonus de préférences de gymnase."""
    
    def test_prefers_favorite_gym(self, minimal_config, match_builder,
                                  creneau_builder, gymnase_builder, equipe_builder):
        """
        1 match, 2 créneaux avec gymnases différents, équipes préfèrent Gym1
        
        Solution optimale : Gym1 (bonus > 0).
        """
        # Configuration
        minimal_config.bonus_preferences_gymnases = [100, 50, 10]  # Bonus selon rang
        
        # Setup
        equipe1 = equipe_builder.create(lieux_preferes=["Gym1", "Gym2"])
        equipe2 = equipe_builder.create(lieux_preferes=["Gym1"])
        match = match_builder.create(equipe1=equipe1, equipe2=equipe2)
        
        creneau_prefere = creneau_builder.create(semaine=1, horaire="18:00", gymnase="Gym1")
        creneau_autre = creneau_builder.create(semaine=1, horaire="18:00", gymnase="Gym3")
        
        gymnases = gymnase_builder.create_dict(["Gym1", "Gym3"])
        
        # Résolution
        solver = CPSATSolver(minimal_config)
        solution = solver.solve([match], [creneau_prefere, creneau_autre], gymnases)
        
        # Vérification : DOIT choisir Gym1 (2 équipes le préfèrent)
        assert solution.est_complete()
        assert_match_assigned_to(match, creneau_prefere)
    
    def test_bonus_depends_on_rank(self, minimal_config, match_builder,
                                   creneau_builder, gymnase_builder, equipe_builder):
        """
        Le bonus diminue selon le rang de préférence (1er choix > 2ème choix)
        
        Solution optimale : Gym1 (1er choix) plutôt que Gym2 (2ème choix).
        """
        # Configuration
        minimal_config.bonus_preferences_gymnases = [100, 20]  # 1er >> 2ème
        
        # Setup
        equipe1 = equipe_builder.create(lieux_preferes=["Gym1", "Gym2"])
        equipe2 = equipe_builder.create(lieux_preferes=["Gym1", "Gym2"])
        match = match_builder.create(equipe1=equipe1, equipe2=equipe2)
        
        creneau_choix1 = creneau_builder.create(semaine=1, horaire="18:00", gymnase="Gym1")
        creneau_choix2 = creneau_builder.create(semaine=1, horaire="18:00", gymnase="Gym2")
        
        gymnases = gymnase_builder.create_dict(["Gym1", "Gym2"])
        
        # Résolution
        solver = CPSATSolver(minimal_config)
        solution = solver.solve([match], [creneau_choix1, creneau_choix2], gymnases)
        
        # Vérification : DOIT choisir Gym1 (bonus 100+100 vs 20+20)
        assert solution.est_complete()
        assert_match_assigned_to(match, creneau_choix1)


class TestGymLevelPenalties:
    """Tests des pénalités de niveau de gymnase."""
    
    def test_high_level_match_avoids_low_level_gym(self, minimal_config, match_builder,
                                                    creneau_builder, gymnase_builder, equipe_builder):
        """
        Match A1 (haut niveau) sur gymnase bas niveau → pénalité
        
        Solution optimale : Gymnase haut niveau.
        """
        # Configuration
        minimal_config.poids_niveaux_gymnases_bas = [1000, 500, 100, 0]  # Pénalité par niveau match
        
        # Setup : match A1 (niveau 0)
        equipe1 = equipe_builder.create(poule="A1")
        equipe2 = equipe_builder.create(poule="A1")
        match = match_builder.create(equipe1=equipe1, equipe2=equipe2, poule="A1")
        
        creneau_haut = creneau_builder.create(semaine=1, horaire="18:00", gymnase="Gym_Haut")
        creneau_bas = creneau_builder.create(semaine=1, horaire="18:00", gymnase="Gym_Bas")
        
        gymnases = gymnase_builder.create_dict(["Gym_Haut", "Gym_Bas"])
        
        # Niveaux de gymnases
        niveaux_gymnases = {
            "Gym_Haut": "haut",
            "Gym_Bas": "bas"
        }
        
        # Résolution
        solver = CPSATSolver(minimal_config, niveaux_gymnases=niveaux_gymnases)
        solution = solver.solve([match], [creneau_haut, creneau_bas], gymnases)
        
        # Vérification : DOIT éviter gymnase bas niveau (pénalité 1000)
        assert solution.est_complete()
        assert_match_assigned_to(match, creneau_haut)


class TestGymGenderPriorityPenalties:
    """Vérifie la prise en compte des priorités de genre des gymnases."""

    def test_respects_gym_gender_priority(self, minimal_config, match_builder,
                                          creneau_builder, gymnase_builder, equipe_builder):
        """Un gymnase prioritaire F doit rester réservé aux matchs féminins si la pénalité est forte."""
        minimal_config.penalite_gymnase_priorite_genre = 1000

        equipe1 = equipe_builder.create()
        equipe2 = equipe_builder.create()
        equipe1.genre = "M"
        equipe2.genre = "M"
        match = match_builder.create(equipe1=equipe1, equipe2=equipe2)

        creneau_masc = creneau_builder.create(semaine=1, horaire="18:00", gymnase="Gym_M")
        creneau_fem = creneau_builder.create(semaine=1, horaire="18:00", gymnase="Gym_F")

        gymnases = gymnase_builder.create_dict(["Gym_M", "Gym_F"])
        priorites = {"Gym_M": "M", "Gym_F": "F"}

        solver = CPSATSolver(minimal_config, priorites_genre_gymnases=priorites)
        solution = solver.solve([match], [creneau_masc, creneau_fem], gymnases)

        assert solution.est_complete()
        assert_match_assigned_to(match, creneau_masc)


class TestAllerRetourPenalties:
    """Vérifie la prise en compte des pénalités aller/retour."""

    def test_high_penalty_discourages_consecutive_weeks(self, minimal_config, match_builder,
                                                         creneau_builder, gymnase_builder):
        minimal_config.aller_retour_espacement_actif = True
        minimal_config.cpsat_enable_aller_retour = True  # Activer la contrainte de performance
        minimal_config.aller_retour_penalites_par_ecart = [0, 1_000_000, 0, 0]
        minimal_config.compaction_temporelle_actif = True
        minimal_config.compaction_penalites_par_semaine = [0, 0, 500, 1000]

        equipe_a = match_builder.equipe_builder.create(nom="VA", poule="A1")
        equipe_b = match_builder.equipe_builder.create(nom="VB", poule="A1")
        aller = match_builder.create(equipe1=equipe_a, equipe2=equipe_b, poule="A1")
        retour = match_builder.create(equipe1=equipe_b, equipe2=equipe_a, poule="A1")

        creneaux = [
            creneau_builder.create(semaine=1, horaire="18:00", gymnase="Gym1"),
            creneau_builder.create(semaine=2, horaire="18:00", gymnase="Gym1"),
            creneau_builder.create(semaine=4, horaire="18:00", gymnase="Gym1"),
        ]
        gymnases = gymnase_builder.create_dict(["Gym1"])

        solver = CPSATSolver(minimal_config)
        solution = solver.solve([aller, retour], creneaux, gymnases)

        assert solution.est_complete()
        semaines = sorted(match.creneau.semaine for match in solution.matchs_planifies)
        assert semaines[1] - semaines[0] >= 2, "La forte pénalité d'écart 1 semaine doit l'emporter sur la compaction"

    def test_fixed_aller_still_penalizes_close_retour(self, minimal_config, match_builder,
                                                      creneau_builder, gymnase_builder):
        minimal_config.aller_retour_espacement_actif = True
        minimal_config.cpsat_enable_aller_retour = True  # Activer la contrainte de performance
        minimal_config.aller_retour_penalites_par_ecart = [0, 1_000_000, 0, 0]
        minimal_config.compaction_temporelle_actif = True
        minimal_config.compaction_penalites_par_semaine = [0, 1_000, 2_000, 3_000, 4_000]

        equipe_a = match_builder.equipe_builder.create(nom="VA", poule="A1")
        equipe_b = match_builder.equipe_builder.create(nom="VB", poule="A1")

        retour = match_builder.create(equipe1=equipe_b, equipe2=equipe_a, poule="A1")
        match_fixe = match_builder.create(equipe1=equipe_a, equipe2=equipe_b, poule="A1")
        match_fixe.metadata = {
            "semaine": 1,
            "horaire": "18:00",
            "gymnase": "Gym1",
        }

        creneaux = [
            creneau_builder.create(semaine=2, horaire="18:00", gymnase="Gym1"),
            creneau_builder.create(semaine=4, horaire="18:00", gymnase="Gym1"),
        ]
        gymnases = gymnase_builder.create_dict(["Gym1"])

        solver = CPSATSolver(minimal_config)
        solution = solver.solve([retour], creneaux, gymnases, matchs_fixes=[match_fixe])

        assert solution.est_complete()
        assert retour.est_planifie()
        assert retour.creneau.semaine == 4, "Le match retour doit éviter la semaine 2 à cause du match aller fixé semaine 1"


class TestProgressiveBalancingBonus:
    """Tests du bonus d'équilibrage progressif."""
    
    def test_balances_matches_between_teams(self, minimal_config, match_builder,
                                            creneau_builder, gymnase_builder, equipe_builder):
        """
        2 équipes : A joue 2 matchs, B joue 1 match. Seulement 2 créneaux disponibles.
        
        Solution optimale : 1 match de A + 1 match de B (équilibrage).
        """
        # Configuration
        minimal_config.equilibrage_actif = True
        minimal_config.equilibrage_bonus_base = 1000000
        minimal_config.equilibrage_facteur_decroissance = 0.3
        minimal_config.equilibrage_bonus_minimum = 1
        
        # Setup
        equipe_a = equipe_builder.create(nom="A")
        equipe_b = equipe_builder.create(nom="B")
        equipe_c = equipe_builder.create(nom="C")
        equipe_d = equipe_builder.create(nom="D")
        
        # A joue 2 matchs
        match_a1 = match_builder.create(equipe1=equipe_a, equipe2=equipe_c)
        match_a2 = match_builder.create(equipe1=equipe_a, equipe2=equipe_d)
        
        # B joue 1 seul match
        match_b1 = match_builder.create(equipe1=equipe_b, equipe2=equipe_c)
        
        # Seulement 2 créneaux
        creneaux = [
            creneau_builder.create(semaine=1, horaire="18:00", gymnase="Gym1"),
            creneau_builder.create(semaine=2, horaire="18:00", gymnase="Gym1")
        ]
        
        gymnases = gymnase_builder.create_dict(["Gym1"])
        
        # Résolution
        solver = CPSATSolver(minimal_config)
        solution = solver.solve([match_a1, match_a2, match_b1], creneaux, gymnases)
        
        # Vérification : B devrait avoir son match (priorité max-min)
        assert match_b1.est_planifie(), \
            "Équipe B n'a qu'1 match, il devrait être priorisé (équilibrage)"
        
        # Au moins 1 des matchs de A devrait aussi être planifié
        matchs_a_planifies = [m for m in [match_a1, match_a2] if m.est_planifie()]
        assert len(matchs_a_planifies) == 1, \
            "1 seul match de A devrait être planifié (2 créneaux - 1 pour B)"


class TestCalculationFunctions:
    """Tests unitaires des fonctions de calcul de pénalités."""
    
    def test_calculate_time_preference_penalty_exact(self, minimal_config, equipe_builder):
        """Test unitaire de _calculate_time_preference_penalty avec horaire exact."""
        minimal_config.penalite_horaire_tolerance = 30
        minimal_config.penalite_apres_horaire_min = 10
        minimal_config.penalite_horaire_diviseur = 60
        
        from pycalendar.core.models import Match, Creneau
        from pycalendar.core.penalties import compute_time_preference_penalty
        
        equipe1 = equipe_builder.create(horaires_preferes=["18:00"])
        equipe2 = equipe_builder.create(horaires_preferes=["18:00"])
        match = Match(equipe1, equipe2, "A1")
        creneau = Creneau(semaine=1, horaire="18:00", gymnase="Gym1")
        
        result = compute_time_preference_penalty(match, creneau, minimal_config)
        
        assert result.penalty == 0.0, "Horaire exact devrait donner pénalité = 0"
    
    def test_calculate_time_preference_penalty_after(self, minimal_config, equipe_builder):
        """Test pénalité après horaire préféré."""
        minimal_config.penalite_horaire_tolerance = 0
        minimal_config.penalite_apres_horaire_min = 10
        minimal_config.penalite_horaire_diviseur = 60
        
        from pycalendar.core.models import Match, Creneau
        from pycalendar.core.penalties import compute_time_preference_penalty
        
        # Préfèrent 18:00, match à 20:00 (+2h = 120 min)
        equipe1 = equipe_builder.create(horaires_preferes=["18:00"])
        equipe2 = equipe_builder.create(horaires_preferes=["18:00"])
        match = Match(equipe1, equipe2, "A1")
        creneau = Creneau(semaine=1, horaire="20:00", gymnase="Gym1")
        
        result = compute_time_preference_penalty(match, creneau, minimal_config)
        
        # Calcul attendu : 10 × ((120/60)²) × 2 équipes = 10 × 4 × 2 = 80
        expected = 10 * ((120 / 60) ** 2) * 2
        
        assert abs(result.penalty - expected) < 0.01, \
            f"Pénalité = {result.penalty}, attendu ≈ {expected}"
    
    def test_progressive_bonus_calculation(self, minimal_config):
        """Test de la formule de bonus progressif."""
        minimal_config.equilibrage_bonus_base = 100000
        minimal_config.equilibrage_facteur_decroissance = 0.3
        minimal_config.equilibrage_bonus_minimum = 1
        
        solver = CPSATSolver(minimal_config)
        
        bonus_0 = solver._calcul_bonus_progressif(0)
        bonus_1 = solver._calcul_bonus_progressif(1)
        bonus_2 = solver._calcul_bonus_progressif(2)
        
        # Vérifications
        assert bonus_0 == 100000, "1er match devrait avoir bonus_base"
        assert bonus_1 == int(100000 * 0.3), "2ème match devrait avoir bonus_base × 0.3"
        assert bonus_2 == int(100000 * 0.3 * 0.3), "3ème match devrait avoir bonus_base × 0.3²"
        
        # Décroissance
        assert bonus_0 > bonus_1 > bonus_2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
