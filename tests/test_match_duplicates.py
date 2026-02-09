"""
Tests for match duplicate detection.

Tests the MatchDuplicateDetector and related functions.
"""

import pytest
import pandas as pd
from pycalendar.cli.excel_updater.match_duplicates import (
    MatchDuplicateDetector,
    MatchInfo,
    detect_match_duplicates,
    COMPTE_DOUBLE_REGEX,
)
from pycalendar.cli.excel_updater.reports import Severity


class TestMatchInfo:
    """Tests for MatchInfo dataclass."""
    
    def test_match_key_normalizes_order(self):
        """Test that match key is normalized regardless of team order."""
        match1 = MatchInfo(
            row_index=2, equipe_1="LYON 1", equipe_2="LYON 2", 
            genre="M", poule="P1", semaine=1
        )
        match2 = MatchInfo(
            row_index=3, equipe_1="LYON 2", equipe_2="LYON 1", 
            genre="M", poule="P1", semaine=2
        )
        
        assert match1.match_key == match2.match_key
    
    def test_match_key_respects_genre(self):
        """Test that different genres produce different keys."""
        match_m = MatchInfo(
            row_index=2, equipe_1="LYON 1", equipe_2="LYON 2", 
            genre="M", poule="P1", semaine=1
        )
        match_f = MatchInfo(
            row_index=3, equipe_1="LYON 1", equipe_2="LYON 2", 
            genre="F", poule="P1", semaine=2
        )
        
        assert match_m.match_key != match_f.match_key
    
    def test_is_compte_double_detects_patterns(self):
        """Test that 'compte double' patterns are detected."""
        patterns = [
            "Match compte double pour forfait",
            "COMPTE DOUBLE",
            "Double comptage volontaire",
            "Ce match est comptabilisé double",
        ]
        
        for remarque in patterns:
            match = MatchInfo(
                row_index=2, equipe_1="A", equipe_2="B",
                genre="M", poule="P1", semaine=1, remarques=remarque
            )
            assert match.is_compte_double, f"Should detect: {remarque}"
    
    def test_is_compte_double_false_for_normal_remarks(self):
        """Test that normal remarks don't trigger compte double."""
        match = MatchInfo(
            row_index=2, equipe_1="A", equipe_2="B",
            genre="M", poule="P1", semaine=1, 
            remarques="Match reporté semaine prochaine"
        )
        assert not match.is_compte_double


class TestMatchDuplicateDetector:
    """Tests for MatchDuplicateDetector class."""
    
    def test_detects_simple_duplicate(self):
        """Test detection of a simple duplicate match."""
        detector = MatchDuplicateDetector()
        
        df = pd.DataFrame({
            'Equipe_1': ['LYON 1', 'LYON 1', 'ENS'],
            'Equipe_2': ['LYON 2', 'LYON 2', 'CATHO'],
            'Genre': ['M', 'M', 'F'],
            'Poule': ['P1', 'P1', 'P2'],
            'Semaine': [1, 2, 1],
            'Remarques': [None, None, None],
        })
        
        detector.load_matches(df)
        issues = detector.detect_duplicates()
        
        # 2 matches en doublon × 2 colonnes (Equipe_1 et Equipe_2) = 4 issues
        assert len(issues) == 4
        # Vérifie que les 2 lignes concernées sont présentes
        lignes = {issue.ligne for issue in issues}
        assert lignes == {2, 3}  # Les deux lignes sont signalées
        assert all(issue.severite == Severity.ERROR for issue in issues)
        # Vérifie que les deux colonnes sont surlignées
        colonnes = {issue.colonne for issue in issues}
        assert colonnes == {'Equipe_1', 'Equipe_2'}
    
    def test_allows_aller_retour_duplicates(self):
        """Test that Aller-Retour pools allow 2 matches."""
        detector = MatchDuplicateDetector(poules_aller_retour={'P1'})
        
        df = pd.DataFrame({
            'Equipe_1': ['LYON 1', 'LYON 2'],
            'Equipe_2': ['LYON 2', 'LYON 1'],
            'Genre': ['M', 'M'],
            'Poule': ['P1', 'P1'],
            'Semaine': [1, 5],
            'Remarques': [None, None],
        })
        
        detector.load_matches(df)
        issues = detector.detect_duplicates()
        
        # No issues: 2 matches allowed in Aller-Retour
        assert len(issues) == 0
    
    def test_detects_triple_in_aller_retour(self):
        """Test that Aller-Retour pools flag > 2 matches."""
        detector = MatchDuplicateDetector(poules_aller_retour={'P1'})
        
        df = pd.DataFrame({
            'Equipe_1': ['LYON 1', 'LYON 2', 'LYON 1'],
            'Equipe_2': ['LYON 2', 'LYON 1', 'LYON 2'],
            'Genre': ['M', 'M', 'M'],
            'Poule': ['P1', 'P1', 'P1'],
            'Semaine': [1, 5, 10],
            'Remarques': [None, None, None],
        })
        
        detector.load_matches(df)
        issues = detector.detect_duplicates()
        
        # 3 matchs en excès × 2 colonnes = 6 issues (tous les 3 sont signalés)
        assert len(issues) == 6
        lignes = {issue.ligne for issue in issues}
        assert lignes == {2, 3, 4}  # Les 3 lignes sont concernées
        colonnes = {issue.colonne for issue in issues}
        assert colonnes == {'Equipe_1', 'Equipe_2'}
    
    def test_respects_compte_double(self):
        """Test that 'compte double' matches are excluded from duplicate detection."""
        detector = MatchDuplicateDetector()
        
        df = pd.DataFrame({
            'Equipe_1': ['LYON 1', 'LYON 1'],
            'Equipe_2': ['LYON 2', 'LYON 2'],
            'Genre': ['M', 'M'],
            'Poule': ['P1', 'P1'],
            'Semaine': [1, 2],
            'Remarques': [None, 'Compte double pour forfait'],
        })
        
        detector.load_matches(df)
        issues = detector.detect_duplicates()
        
        # Should be warning, not error (compte double present)
        assert len(issues) == 0 or issues[0].severite == Severity.WARNING
    
    def test_detects_self_match(self):
        """Test detection of a team playing against itself."""
        detector = MatchDuplicateDetector()
        
        df = pd.DataFrame({
            'Equipe_1': ['LYON 1', 'LYON 2'],
            'Equipe_2': ['LYON 1', 'ENS'],
            'Genre': ['M', 'F'],
            'Poule': ['P1', 'P2'],
            'Semaine': [1, 2],
            'Remarques': [None, None],
        })
        
        detector.load_matches(df)
        issues = detector.detect_same_team_match()
        
        assert len(issues) == 1
        assert issues[0].ligne == 2
        assert "elle-même" in issues[0].message
    
    def test_handles_inverted_team_order(self):
        """Test that A vs B is detected as duplicate of B vs A."""
        detector = MatchDuplicateDetector()
        
        df = pd.DataFrame({
            'Equipe_1': ['LYON 1', 'LYON 2'],
            'Equipe_2': ['LYON 2', 'LYON 1'],
            'Genre': ['M', 'M'],
            'Poule': ['P1', 'P1'],
            'Semaine': [1, 2],
            'Remarques': [None, None],
        })
        
        detector.load_matches(df)
        issues = detector.detect_duplicates()
        
        # 2 matchs × 2 colonnes = 4 issues
        assert len(issues) == 4
        lignes = {issue.ligne for issue in issues}
        assert lignes == {2, 3}  # Les deux lignes sont signalées


class TestDetectMatchDuplicates:
    """Tests for the convenience function."""
    
    def test_loads_aller_retour_from_types_poules(self):
        """Test that Aller-Retour pools are loaded from Types_Poules."""
        df_matchs = pd.DataFrame({
            'Equipe_1': ['LYON 1', 'LYON 2'],
            'Equipe_2': ['LYON 2', 'LYON 1'],
            'Genre': ['M', 'M'],
            'Poule': ['ARPOUL', 'ARPOUL'],
            'Semaine': [1, 5],
            'Remarques': [None, None],
        })
        
        df_types = pd.DataFrame({
            'Poule': ['ARPOUL', 'CLASSIC'],
            'Type': ['Aller-Retour', 'Classique'],
        })
        
        issues = detect_match_duplicates(df_matchs, df_types)
        
        # No issues: ARPOUL is Aller-Retour, 2 matches allowed
        assert len(issues) == 0
    
    def test_handles_missing_types_poules(self):
        """Test that function works without Types_Poules."""
        df_matchs = pd.DataFrame({
            'Equipe_1': ['LYON 1', 'LYON 1'],
            'Equipe_2': ['LYON 2', 'LYON 2'],
            'Genre': ['M', 'M'],
            'Poule': ['P1', 'P1'],
            'Semaine': [1, 2],
            'Remarques': [None, None],
        })
        
        # No Types_Poules provided - all pools treated as Classique
        issues = detect_match_duplicates(df_matchs, None)
        
        # 2 matchs en doublon × 2 colonnes = 4 issues
        assert len(issues) == 4
        lignes = {issue.ligne for issue in issues}
        assert lignes == {2, 3}
