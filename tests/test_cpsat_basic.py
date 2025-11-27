"""
Tests de base du solveur CP-SAT.

Ces tests vérifient le comportement fondamental du solveur sur des cas simples
où la solution optimale est évidente et connue à l'avance.
"""

import pytest
from pycalendar.solvers.cpsat_solver import CPSATSolver
from .conftest import assert_match_assigned_to, assert_match_not_assigned


class TestBasicAssignment:
    """Tests d'affectation de base (sans pénalités)."""
    
    def test_single_match_single_slot(self, minimal_config, match_builder, 
                                      creneau_builder, gymnase_builder):
        """
        CAS LE PLUS SIMPLE : 1 match, 1 créneau
        
        Solution optimale attendue : Match planifié au créneau unique.
        """
        # Setup
        match = match_builder.create()
        creneau = creneau_builder.create()
        gymnases = gymnase_builder.create_dict([creneau.gymnase])
        
        # Résolution
        solver = CPSATSolver(minimal_config)
        solution = solver.solve([match], [creneau], gymnases)
        
        # Vérification
        assert solution.est_complete(), "La solution devrait être complète"
        assert_match_assigned_to(match, creneau)
    
    def test_one_match_two_slots_identical(self, minimal_config, match_builder,
                                           creneau_builder, gymnase_builder):
        """
        1 match, 2 créneaux identiques (même coût)
        
        Solution optimale : N'importe lequel des 2 créneaux (les deux sont optimaux).
        """
        # Setup
        match = match_builder.create()
        creneau1 = creneau_builder.create(semaine=1, horaire="18:00", gymnase="Gym1")
        creneau2 = creneau_builder.create(semaine=2, horaire="18:00", gymnase="Gym1")
        gymnases = gymnase_builder.create_dict(["Gym1"])
        
        # Résolution
        solver = CPSATSolver(minimal_config)
        solution = solver.solve([match], [creneau1, creneau2], gymnases)
        
        # Vérification : match doit être planifié (peu importe où)
        assert solution.est_complete()
        assert match.est_planifie()
    
    def test_two_matches_one_slot_capacity_one(self, minimal_config, match_builder,
                                                creneau_builder, gymnase_builder):
        """
        2 matchs, 1 créneau avec capacité=1
        
        Solution optimale : Exactement 1 match planifié (contrainte dure de capacité).
        """
        # Setup
        match1 = match_builder.create()
        match2 = match_builder.create()
        creneau = creneau_builder.create(gymnase="Gym1")
        gymnases = gymnase_builder.create_dict(["Gym1"], capacite=1)
        
        # Résolution
        solver = CPSATSolver(minimal_config)
        solution = solver.solve([match1, match2], [creneau], gymnases)
        
        # Vérification : exactement 1 match planifié
        matchs_planifies = [m for m in [match1, match2] if m.est_planifie()]
        assert len(matchs_planifies) == 1, \
            f"Capacité=1 → exactement 1 match, mais {len(matchs_planifies)} planifiés"
    
    def test_two_matches_one_slot_capacity_two(self, minimal_config, match_builder,
                                                creneau_builder, gymnase_builder):
        """
        2 matchs, 1 créneau avec capacité=2
        
        Solution optimale : Les 2 matchs planifiés au même créneau.
        """
        # Setup
        match1 = match_builder.create()
        match2 = match_builder.create()
        creneau = creneau_builder.create(gymnase="Gym1")
        gymnases = gymnase_builder.create_dict(["Gym1"], capacite=2)
        
        # Résolution
        solver = CPSATSolver(minimal_config)
        solution = solver.solve([match1, match2], [creneau], gymnases)
        
        # Vérification : les 2 matchs planifiés
        assert solution.est_complete()
        assert match1.est_planifie()
        assert match2.est_planifie()
        assert match1.creneau == creneau
        assert match2.creneau == creneau
    
    def test_three_matches_two_slots(self, minimal_config, match_builder,
                                     creneau_builder, gymnase_builder):
        """
        3 matchs, 2 créneaux (capacité=1 chacun)
        
        Solution optimale : 2 matchs planifiés, 1 non planifié.
        """
        # Setup
        matches = [match_builder.create() for _ in range(3)]
        creneau1 = creneau_builder.create(semaine=1, gymnase="Gym1")
        creneau2 = creneau_builder.create(semaine=2, gymnase="Gym2")
        gymnases = gymnase_builder.create_dict(["Gym1", "Gym2"], capacite=1)
        
        # Résolution
        solver = CPSATSolver(minimal_config)
        solution = solver.solve(matches, [creneau1, creneau2], gymnases)
        
        # Vérification
        matchs_planifies = [m for m in matches if m.est_planifie()]
        matchs_non_planifies = [m for m in matches if not m.est_planifie()]
        
        assert len(matchs_planifies) == 2, \
            f"2 créneaux → 2 matchs planifiés, mais {len(matchs_planifies)} obtenus"
        assert len(matchs_non_planifies) == 1


class TestHardConstraints:
    """Tests des contraintes dures (indisponibilités, non-simultanéité)."""
    
    def test_unavailability_constraint(self, minimal_config, match_builder,
                                       creneau_builder, gymnase_builder, equipe_builder):
        """
        1 match, 2 créneaux, mais équipe indisponible à 1 créneau
        
        Solution optimale : Match au créneau disponible uniquement.
        """
        # Setup : équipe A indisponible semaine 1 pour tous les horaires
        equipe_a = equipe_builder.create(nom="A")
        equipe_a.semaines_indisponibles = {1: {"18:00", "20:00"}}  # Indispo semaine 1 tous horaires
        equipe_b = equipe_builder.create(nom="B")
        
        match = match_builder.create(equipe1=equipe_a, equipe2=equipe_b)
        
        creneau_indispo = creneau_builder.create(semaine=1, gymnase="Gym1")
        creneau_dispo = creneau_builder.create(semaine=2, gymnase="Gym1")
        gymnases = gymnase_builder.create_dict(["Gym1"])
        
        # Résolution
        solver = CPSATSolver(minimal_config)
        solution = solver.solve([match], [creneau_indispo, creneau_dispo], gymnases)
        
        # Vérification : DOIT être à la semaine 2
        assert solution.est_complete()
        assert_match_assigned_to(match, creneau_dispo)
    
    def test_non_simultaneity_constraint(self, minimal_config, match_builder,
                                        creneau_builder, gymnase_builder, equipe_builder):
        """
        2 matchs avec équipe commune, 1 seul créneau
        
        Solution optimale : 1 seul match planifié (contrainte de non-simultanéité).
        """
        # Setup : équipe A joue 2 matchs
        equipe_a = equipe_builder.create(nom="A")
        equipe_b = equipe_builder.create(nom="B")
        equipe_c = equipe_builder.create(nom="C")
        
        match1 = match_builder.create(equipe1=equipe_a, equipe2=equipe_b)
        match2 = match_builder.create(equipe1=equipe_a, equipe2=equipe_c)
        
        creneau = creneau_builder.create(gymnase="Gym1")
        gymnases = gymnase_builder.create_dict(["Gym1"], capacite=2)  # Capacité suffisante
        
        # Résolution
        solver = CPSATSolver(minimal_config)
        solution = solver.solve([match1, match2], [creneau], gymnases)
        
        # Vérification : 1 seul match (équipe A ne peut pas jouer 2 fois en même temps)
        matchs_planifies = [m for m in [match1, match2] if m.est_planifie()]
        assert len(matchs_planifies) == 1, \
            "Équipe commune → max 1 match au même créneau"


class TestMatchFixing:
    """Tests des matchs fixés (pré-assignés)."""
    
    def test_fixed_match_is_respected(self, minimal_config, match_builder,
                                      creneau_builder, gymnase_builder):
        """
        1 match fixé + 1 match à planifier, 1 créneau libre
        
        Solution optimale : Match fixé inchangé, nouveau match au créneau libre.
        """
        # Setup
        match_fixe = match_builder.create()
        match_a_planifier = match_builder.create()
        
        creneau_fixe = creneau_builder.create(semaine=1, horaire="18:00", gymnase="Gym1")
        creneau_libre = creneau_builder.create(semaine=2, horaire="18:00", gymnase="Gym2")
        
        # Fixer le premier match
        match_fixe.creneau = creneau_fixe
        
        gymnases = gymnase_builder.create_dict(["Gym1", "Gym2"])
        
        # Résolution
        solver = CPSATSolver(minimal_config)
        solution = solver.solve(
            [match_fixe, match_a_planifier],
            [creneau_fixe, creneau_libre],
            gymnases,
            matchs_fixes=[match_fixe]
        )
        
        # Vérification
        assert solution.est_complete()
        assert_match_assigned_to(match_fixe, creneau_fixe)  # Inchangé
        assert_match_assigned_to(match_a_planifier, creneau_libre)
    
    def test_fixed_match_blocks_slot(self, minimal_config, match_builder,
                                     creneau_builder, gymnase_builder):
        """
        1 match fixé occupe un créneau capacité=1, 1 autre match ne peut pas y aller.
        
        Solution optimale : Match non fixé reste non planifié.
        """
        # Setup
        match_fixe = match_builder.create()
        match_concurrent = match_builder.create()
        
        creneau_occupe = creneau_builder.create(semaine=1, horaire="18:00", gymnase="Gym1")
        
        # Fixer le match avec métadonnées (format attendu par CP-SAT)
        match_fixe.creneau = creneau_occupe
        match_fixe.metadata = {
            'semaine': creneau_occupe.semaine,
            'horaire': creneau_occupe.horaire,
            'gymnase': creneau_occupe.gymnase
        }
        
        gymnases = gymnase_builder.create_dict(["Gym1"], capacite=1)
        
        # Résolution
        solver = CPSATSolver(minimal_config)
        solution = solver.solve(
            [match_fixe, match_concurrent],
            [creneau_occupe],
            gymnases,
            matchs_fixes=[match_fixe]
        )
        
        # Vérification
        assert_match_assigned_to(match_fixe, creneau_occupe)
        assert_match_not_assigned(match_concurrent)  # Bloqué par le match fixé
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
