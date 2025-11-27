"""
Tests avancés CP-SAT avec choix forcés et cas complexes.

Ces tests forcent le solver à faire des VRAIS choix difficiles,
contrairement aux tests de base qui ont souvent une seule solution évidente.
"""

import pytest
from pycalendar.solvers.cpsat_solver import CPSATSolver
from pycalendar.core.models import Match


def assert_match_assigned_to(match: Match, expected_creneau) -> None:
    """Vérifie qu'un match est assigné au créneau attendu."""
    assert match.est_planifie(), f"Match {match} devrait être planifié"
    assert match.creneau == expected_creneau, \
        f"Match {match} attendu à {expected_creneau}, trouvé à {match.creneau}"


def assert_match_not_assigned(match: Match) -> None:
    """Vérifie qu'un match n'est PAS assigné."""
    assert not match.est_planifie(), f"Match {match} ne devrait PAS être planifié"


class TestForcedChoices:
    """Tests où CP-SAT doit choisir entre options avec pénalités différentes."""
    
    def test_penalty_forces_choice_between_matches(self, minimal_config, match_builder,
                                                   creneau_builder, gymnase_builder, equipe_builder):
        """
        2 matchs, 1 seul créneau disponible.
        Match1 a une ÉNORME pénalité horaire, Match2 a une petite pénalité.
        
        Solution optimale : CP-SAT doit choisir Match2 (moins de pénalité).
        
        Ce test FORCE un choix réel : CP-SAT ne peut pas planifier les deux.
        """
        # Setup : Équipes avec horaires préférés très différents
        equipe_a = equipe_builder.create(nom="A", horaires_preferes=["18:00"])
        equipe_b = equipe_builder.create(nom="B", horaires_preferes=["18:00"])
        equipe_c = equipe_builder.create(nom="C", horaires_preferes=["20:00"])  # Proche du créneau
        equipe_d = equipe_builder.create(nom="D", horaires_preferes=["20:00"])
        
        match1 = match_builder.create(equipe1=equipe_a, equipe2=equipe_b)  # Horaire loin : 18h vs 21h = -3h
        match2 = match_builder.create(equipe1=equipe_c, equipe2=equipe_d)  # Horaire proche : 20h vs 21h = -1h
        
        creneau = creneau_builder.create(semaine=1, horaire="21:00", gymnase="Gym1")
        gymnases = gymnase_builder.create_dict(["Gym1"], capacite=1)  # UNE SEULE PLACE
        
        # Activer pénalités horaires FORTES
        minimal_config.penalite_avant_horaire_min = 100
        minimal_config.horaire_avant_tolerance = 0
        
        # Résolution
        solver = CPSATSolver(minimal_config)
        solution = solver.solve([match1, match2], [creneau], gymnases)
        
        # Vérification : Match2 DOIT être choisi (moins de pénalité)
        assert_match_not_assigned(match1)  # Match1 exclu (trop de pénalité)
        assert_match_assigned_to(match2, creneau)  # Match2 choisi
    
    def test_gym_preference_forces_choice(self, minimal_config, match_builder,
                                         creneau_builder, gymnase_builder, equipe_builder):
        """
        2 matchs, 2 créneaux (Gym1, Gym2).
        Match1 préfère FORTEMENT Gym1.
        Match2 préfère FORTEMENT Gym2.
        
        Solution optimale : Match1→Gym1, Match2→Gym2 (satisfaction max).
        
        Test de conflit d'intérêts : vérifier que CP-SAT arbitre correctement.
        """
        # Setup : Équipes avec préférences gymnases
        equipe_a = equipe_builder.create(nom="A", lieux_preferes=["Gym1", "Gym2"])
        equipe_b = equipe_builder.create(nom="B", lieux_preferes=["Gym1", "Gym2"])
        equipe_c = equipe_builder.create(nom="C", lieux_preferes=["Gym2", "Gym1"])
        equipe_d = equipe_builder.create(nom="D", lieux_preferes=["Gym2", "Gym1"])
        
        match1 = match_builder.create(equipe1=equipe_a, equipe2=equipe_b)
        match2 = match_builder.create(equipe1=equipe_c, equipe2=equipe_d)
        
        creneau_gym1 = creneau_builder.create(semaine=1, horaire="18:00", gymnase="Gym1")
        creneau_gym2 = creneau_builder.create(semaine=1, horaire="18:00", gymnase="Gym2")
        gymnases = gymnase_builder.create_dict(["Gym1", "Gym2"], capacite=1)
        
        # Activer bonus gymnases préférés
        minimal_config.bonus_preferences_gymnases = [100, 10]  # Rang 1 = +100, Rang 2 = +10
        
        # Résolution
        solver = CPSATSolver(minimal_config)
        solution = solver.solve([match1, match2], [creneau_gym1, creneau_gym2], gymnases)
        
        # Vérification : Match1→Gym1, Match2→Gym2 (meilleur arbitrage)
        assert solution.est_complete()
        assert_match_assigned_to(match1, creneau_gym1)
        assert_match_assigned_to(match2, creneau_gym2)
    
    def test_balancing_forces_fairness(self, minimal_config, match_builder,
                                      creneau_builder, gymnase_builder, equipe_builder):
        """
        3 équipes : A (0 matchs planifiés), B (0 matchs), C (déjà 2 matchs fixés).
        3 matchs à planifier : A-B, B-C, A-C.
        2 créneaux disponibles (capacité totale = 2).
        
        Solution optimale : Planifier A-B et A-C (équipes A et B en priorité).
        Mauvaise solution : Planifier B-C et A-C (équipe C joue encore).
        
        Test d'équilibrage progressif : vérifier priorité aux équipes défavorisées.
        """
        # Setup : Équipes avec historique de matchs différent
        equipe_a = equipe_builder.create(nom="A")
        equipe_b = equipe_builder.create(nom="B")
        equipe_c = equipe_builder.create(nom="C")
        
        # Matchs à planifier
        match_ab = match_builder.create(equipe1=equipe_a, equipe2=equipe_b)
        match_bc = match_builder.create(equipe1=equipe_b, equipe2=equipe_c)
        match_ac = match_builder.create(equipe1=equipe_a, equipe2=equipe_c)
        
        # Matchs déjà planifiés pour C (simuler historique)
        equipe_d = equipe_builder.create(nom="D")
        equipe_e = equipe_builder.create(nom="E")
        match_fixe1 = match_builder.create(equipe1=equipe_c, equipe2=equipe_d)
        match_fixe2 = match_builder.create(equipe1=equipe_c, equipe2=equipe_e)
        
        # Créneaux déjà utilisés par les matchs fixés
        creneau_passe1 = creneau_builder.create(semaine=1, horaire="18:00", gymnase="Gym2")
        creneau_passe2 = creneau_builder.create(semaine=2, horaire="18:00", gymnase="Gym2")
        
        # Fixer les matchs de C (avec métadonnées)
        match_fixe1.creneau = creneau_passe1
        match_fixe1.metadata = {'semaine': 1, 'horaire': '18:00', 'gymnase': 'Gym2'}
        match_fixe2.creneau = creneau_passe2
        match_fixe2.metadata = {'semaine': 2, 'horaire': '18:00', 'gymnase': 'Gym2'}
        
        # Créneaux disponibles pour nouveaux matchs (2 créneaux différents)
        creneau1 = creneau_builder.create(semaine=3, horaire="18:00", gymnase="Gym1")
        creneau2 = creneau_builder.create(semaine=4, horaire="18:00", gymnase="Gym1")
        gymnases = gymnase_builder.create_dict(["Gym1"], capacite=1)
        
        # Activer équilibrage FORT
        minimal_config.equilibrage_actif = True
        minimal_config.equilibrage_coefficient = 2.0  # Bonus exponentiel fort
        
        # Résolution avec matchs fixés pour donner contexte d'historique
        solver = CPSATSolver(minimal_config)
        solution = solver.solve(
            [match_ab, match_bc, match_ac], 
            [creneau1, creneau2], 
            gymnases,
            matchs_fixes=[match_fixe1, match_fixe2]
        )
        
        # Vérification : A-B et A-C planifiés (pas B-C car C a déjà trop de matchs)
        assert len(solution.matchs_planifies) == 2
        assert match_ab.est_planifie()
        assert match_ac.est_planifie()
        assert not match_bc.est_planifie()  # C défavorisé (déjà 2 matchs)


class TestEdgeCases:
    """Tests sur cas limites et situations complexes."""
    
    def test_conflicting_preferences_time_vs_gym(self, minimal_config, match_builder,
                                                 creneau_builder, gymnase_builder, equipe_builder):
        """
        Conflit : Équipe préfère 18h ET Gym1, mais les créneaux sont :
        - (18h, Gym2) : Bon horaire, mauvais gymnase
        - (20h, Gym1) : Mauvais horaire, bon gymnase
        
        Question : CP-SAT privilégie quoi ? Horaire ou gymnase ?
        Réponse : Dépend des poids configurés.
        
        Ce test vérifie que CP-SAT arbitre de façon cohérente.
        """
        # Setup : Équipe avec préférences conflictuelles
        equipe_a = equipe_builder.create(
            nom="A",
            horaires_preferes=["18:00"],
            lieux_preferes=["Gym1"]
        )
        equipe_b = equipe_builder.create(nom="B")
        
        match = match_builder.create(equipe1=equipe_a, equipe2=equipe_b)
        
        creneau_bon_horaire = creneau_builder.create(semaine=1, horaire="18:00", gymnase="Gym2")
        creneau_bon_gym = creneau_builder.create(semaine=1, horaire="20:00", gymnase="Gym1")
        gymnases = gymnase_builder.create_dict(["Gym1", "Gym2"])
        
        # Poids : Gymnase préféré > Horaire préféré
        minimal_config.bonus_preferences_gymnases = [1000]  # Très fort
        minimal_config.penalite_apres_horaire_min = 10  # Faible
        
        # Résolution
        solver = CPSATSolver(minimal_config)
        solution = solver.solve([match], [creneau_bon_horaire, creneau_bon_gym], gymnases)
        
        # Vérification : Gymnase gagne (bonus > pénalité)
        assert solution.est_complete()
        assert_match_assigned_to(match, creneau_bon_gym)
    
    def test_spacing_penalty_influences_choice(self, minimal_config, match_builder,
                                              creneau_builder, gymnase_builder, equipe_builder):
        """
        1 équipe joue 2 matchs.
        Options :
        - S1 et S2 (consécutifs, repos = 0) → Pénalité espacement
        - S1 et S4 (espacés, repos = 2) → Pas de pénalité
        
        Solution optimale : S1 et S4 (meilleur repos).
        
        Test d'espacement : vérifier que CP-SAT évite matchs trop rapprochés.
        """
        # Setup : Une équipe avec 2 matchs
        equipe_a = equipe_builder.create(nom="A")
        equipe_b = equipe_builder.create(nom="B")
        equipe_c = equipe_builder.create(nom="C")
        
        match1 = match_builder.create(equipe1=equipe_a, equipe2=equipe_b)
        match2 = match_builder.create(equipe1=equipe_a, equipe2=equipe_c)
        
        creneau_s1 = creneau_builder.create(semaine=1, horaire="18:00", gymnase="Gym1")
        creneau_s2 = creneau_builder.create(semaine=2, horaire="18:00", gymnase="Gym1")
        creneau_s4 = creneau_builder.create(semaine=4, horaire="18:00", gymnase="Gym1")
        gymnases = gymnase_builder.create_dict(["Gym1"])
        
        # Activer pénalité espacement
        minimal_config.penalites_espacement_repos = [1000, 100, 10, 0]  # [0 sem, 1 sem, 2 sem, 3+ sem]
        
        # Résolution
        solver = CPSATSolver(minimal_config)
        solution = solver.solve([match1, match2], [creneau_s1, creneau_s2, creneau_s4], gymnases)
        
        # Vérification : S1 et S4 choisis (meilleur espacement)
        assert solution.est_complete()
        assert match1.creneau in [creneau_s1, creneau_s4]
        assert match2.creneau in [creneau_s1, creneau_s4]
        assert match1.creneau != match2.creneau
        
        # Vérifier que S2 n'est PAS utilisé (trop proche de S1)
        assert creneau_s2 not in [match1.creneau, match2.creneau]
    
    def test_compaction_prefers_early_weeks(self, minimal_config, match_builder,
                                           creneau_builder, gymnase_builder):
        """
        3 matchs, 3 créneaux : S1, S5, S10.
        Compaction activée : préférer début de saison.
        
        Solution optimale : Tous les matchs en S1 (si capacité permet).
        Mauvaise solution : Répartir S1, S5, S10.
        
        Test de compaction : vérifier que CP-SAT groupe en début.
        """
        # Setup
        match1 = match_builder.create()
        match2 = match_builder.create()
        match3 = match_builder.create()
        
        creneau_s1 = creneau_builder.create(semaine=1, horaire="18:00", gymnase="Gym1")
        creneau_s5 = creneau_builder.create(semaine=5, horaire="18:00", gymnase="Gym1")
        creneau_s10 = creneau_builder.create(semaine=10, horaire="18:00", gymnase="Gym1")
        gymnases = gymnase_builder.create_dict(["Gym1"], capacite=3)  # Peut accueillir les 3
        
        # Activer compaction FORTE
        minimal_config.compaction_temporelle_actif = True
        minimal_config.compaction_penalites_par_semaine = [0, 10, 20, 30, 100, 200, 300, 400, 500, 1000]
        
        # Résolution
        solver = CPSATSolver(minimal_config)
        solution = solver.solve([match1, match2, match3], [creneau_s1, creneau_s5, creneau_s10], gymnases)
        
        # Vérification : Tous en S1 (compaction maximale)
        assert solution.est_complete()
        assert match1.creneau == creneau_s1
        assert match2.creneau == creneau_s1
        assert match3.creneau == creneau_s1


class TestNegativeConstraints:
    """Tests négatifs : vérifier que CP-SAT NE VIOLE JAMAIS les contraintes dures."""
    
    def test_never_exceeds_capacity(self, minimal_config, match_builder,
                                   creneau_builder, gymnase_builder):
        """
        Capacité = 2, 5 matchs veulent le même créneau.
        
        Contrainte dure : MAX 2 matchs sur ce créneau.
        
        Vérification : CP-SAT ne doit JAMAIS planifier plus de 2 matchs.
        """
        # Setup : 5 matchs qui veulent tous le même créneau
        matchs = [match_builder.create() for _ in range(5)]
        
        creneau = creneau_builder.create(semaine=1, horaire="18:00", gymnase="Gym1")
        gymnases = gymnase_builder.create_dict(["Gym1"], capacite=2)  # LIMITE : 2 matchs
        
        # Résolution
        solver = CPSATSolver(minimal_config)
        solution = solver.solve(matchs, [creneau], gymnases)
        
        # Vérification : MAX 2 matchs planifiés (contrainte dure respectée)
        assert len(solution.matchs_planifies) <= 2
        assert len(solution.matchs_non_planifies) >= 3
    
    def test_never_schedules_unavailable_team(self, minimal_config, match_builder,
                                             creneau_builder, gymnase_builder, equipe_builder):
        """
        Équipe A indisponible S1.
        Seul créneau disponible : S1.
        
        Contrainte dure : Équipe A ne peut PAS jouer S1.
        
        Vérification : CP-SAT ne doit JAMAIS planifier le match.
        """
        # Setup : Équipe indisponible
        equipe_a = equipe_builder.create(nom="A")
        equipe_a.semaines_indisponibles = {1: {"18:00", "20:00"}}  # Indispo S1 complète
        equipe_b = equipe_builder.create(nom="B")
        
        match = match_builder.create(equipe1=equipe_a, equipe2=equipe_b)
        
        creneau = creneau_builder.create(semaine=1, horaire="18:00", gymnase="Gym1")
        gymnases = gymnase_builder.create_dict(["Gym1"])
        
        # Résolution
        solver = CPSATSolver(minimal_config)
        solution = solver.solve([match], [creneau], gymnases)
        
        # Vérification : Match NON planifié (contrainte dure respectée)
        assert_match_not_assigned(match)
    
    def test_never_schedules_team_twice_simultaneously(self, minimal_config, match_builder,
                                                      creneau_builder, gymnase_builder, equipe_builder):
        """
        Équipe A joue 2 matchs, 1 seul créneau avec capacité = 2.
        
        Contrainte dure : Équipe A ne peut pas jouer 2 matchs en même temps.
        
        Vérification : CP-SAT ne planifie qu'UN des 2 matchs.
        """
        # Setup : Équipe commune
        equipe_a = equipe_builder.create(nom="A")
        equipe_b = equipe_builder.create(nom="B")
        equipe_c = equipe_builder.create(nom="C")
        
        match1 = match_builder.create(equipe1=equipe_a, equipe2=equipe_b)
        match2 = match_builder.create(equipe1=equipe_a, equipe2=equipe_c)
        
        creneau = creneau_builder.create(semaine=1, horaire="18:00", gymnase="Gym1")
        gymnases = gymnase_builder.create_dict(["Gym1"], capacite=2)  # Capacité OK pour 2
        
        # Résolution
        solver = CPSATSolver(minimal_config)
        solution = solver.solve([match1, match2], [creneau], gymnases)
        
        # Vérification : 1 seul match planifié (non-simultanéité respectée)
        matchs_planifies = solution.matchs_planifies
        assert len(matchs_planifies) == 1
        assert matchs_planifies[0] in [match1, match2]


class TestDifficultArbitration:
    """Tests difficiles avec arbitrages complexes et trade-offs."""
    
    def test_complex_tradeoff_three_criteria(self, minimal_config, match_builder,
                                            creneau_builder, gymnase_builder, equipe_builder):
        """
        3 critères en conflit : Horaire, Gymnase, Espacement.
        2 matchs, 2 créneaux.
        
        Créneau1 : Bon horaire, mauvais gymnase, bon espacement.
        Créneau2 : Mauvais horaire, bon gymnase, mauvais espacement.
        
        Question : CP-SAT fait le bon arbitrage selon poids ?
        """
        # Setup complexe
        equipe_a = equipe_builder.create(
            nom="A",
            horaires_preferes=["18:00"],
            lieux_preferes=["Gym2"]
        )
        equipe_b = equipe_builder.create(nom="B")
        
        match1 = match_builder.create(equipe1=equipe_a, equipe2=equipe_b)
        match2 = match_builder.create(equipe1=equipe_a, equipe2=equipe_b)
        
        # Créneau1 : 18h (bon), Gym1 (mauvais), S1 (bon pour espacement)
        creneau1 = creneau_builder.create(semaine=1, horaire="18:00", gymnase="Gym1")
        # Créneau2 : 20h (mauvais), Gym2 (bon), S2 (mauvais pour espacement)
        creneau2 = creneau_builder.create(semaine=2, horaire="20:00", gymnase="Gym2")
        # Créneau3 : S5 (bon espacement avec S1 ou S2)
        creneau3 = creneau_builder.create(semaine=5, horaire="18:00", gymnase="Gym1")
        
        gymnases = gymnase_builder.create_dict(["Gym1", "Gym2"])
        
        # Poids : Gymnase >> Horaire >> Espacement
        minimal_config.bonus_preferences_gymnases = [1000]
        minimal_config.penalite_apres_horaire_min = 100
        minimal_config.penalites_espacement_repos = [500, 50, 0]
        
        # Résolution
        solver = CPSATSolver(minimal_config)
        solution = solver.solve([match1, match2], [creneau1, creneau2, creneau3], gymnases)
        
        # Vérification : Gymnase prioritaire
        # Match devrait préférer Gym2 (créneau2) malgré mauvais horaire
        assert solution.est_complete()
        # Au moins un match sur Gym2
        assert any(m.creneau.gymnase == "Gym2" for m in solution.matchs_planifies)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
