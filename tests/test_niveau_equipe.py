"""
Tests for the Niveau_Equipe and Genre_Equipe column validation and extraction functionality.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from pycalendar.core.utils import extraire_niveau_depuis_poule, extraire_genre_depuis_poule
from pycalendar.cli.excel_updater.validators import ColumnValidator


class TestExtraireNiveauDepuisPoule:
    """Tests for extracting level from pool code."""
    
    def test_vb_feminine_a1(self):
        """Test extraction from volleyball feminine A1 pool."""
        assert extraire_niveau_depuis_poule('VBFA1PA') == 'A1'
    
    def test_hb_masculine_a2(self):
        """Test extraction from handball masculine A2 pool."""
        assert extraire_niveau_depuis_poule('HBMA2PB') == 'A2'
    
    def test_bb_masculine_a3(self):
        """Test extraction from basketball masculine A3 pool."""
        assert extraire_niveau_depuis_poule('BBMA3PC') == 'A3'
    
    def test_vb_feminine_a4(self):
        """Test extraction from volleyball feminine A4 pool."""
        assert extraire_niveau_depuis_poule('VBFA4PA') == 'A4'
    
    def test_empty_string(self):
        """Test extraction from empty string."""
        assert extraire_niveau_depuis_poule('') == ''
    
    def test_none(self):
        """Test extraction from None."""
        assert extraire_niveau_depuis_poule(None) == ''
    
    def test_invalid_format(self):
        """Test extraction from invalid format."""
        assert extraire_niveau_depuis_poule('INVALID') == ''
    
    def test_lowercase(self):
        """Test extraction from lowercase pool code."""
        assert extraire_niveau_depuis_poule('vbfa1pa') == 'A1'


class TestValiderNiveauEquipe:
    """Tests for team level validation."""
    
    @pytest.fixture
    def validator(self):
        return ColumnValidator()
    
    def test_valid_a1(self, validator):
        """Test valid A1 level."""
        result = validator.valider_niveau_equipe('A1')
        assert result.valide
        assert result.valeur_corrigee == 'A1'
    
    def test_valid_a2(self, validator):
        """Test valid A2 level."""
        result = validator.valider_niveau_equipe('A2')
        assert result.valide
        assert result.valeur_corrigee == 'A2'
    
    def test_valid_a3(self, validator):
        """Test valid A3 level."""
        result = validator.valider_niveau_equipe('A3')
        assert result.valide
    
    def test_valid_a4(self, validator):
        """Test valid A4 level."""
        result = validator.valider_niveau_equipe('A4')
        assert result.valide
    
    def test_lowercase_normalized(self, validator):
        """Test that lowercase is normalized to uppercase."""
        result = validator.valider_niveau_equipe('a1')
        assert result.valide
        assert result.valeur_corrigee == 'A1'
        assert 'normalisé' in result.message.lower()
    
    def test_number_only_converted(self, validator):
        """Test that number only is converted to A-level."""
        result = validator.valider_niveau_equipe('1')
        assert result.valide
        assert result.valeur_corrigee == 'A1'
        assert 'converti' in result.message.lower()
    
    def test_number_2_converted(self, validator):
        """Test that '2' is converted to 'A2'."""
        result = validator.valider_niveau_equipe('2')
        assert result.valide
        assert result.valeur_corrigee == 'A2'
    
    def test_empty_optional(self, validator):
        """Test that empty is valid (optional)."""
        result = validator.valider_niveau_equipe('')
        assert result.valide
    
    def test_none_optional(self, validator):
        """Test that None is valid (optional)."""
        result = validator.valider_niveau_equipe(None)
        assert result.valide
    
    def test_empty_required(self, validator):
        """Test that empty is invalid when required."""
        result = validator.valider_niveau_equipe('', obligatoire=True)
        assert not result.valide
        assert 'obligatoire' in result.message.lower()
    
    def test_invalid_b1(self, validator):
        """Test that B1 is invalid."""
        result = validator.valider_niveau_equipe('B1')
        assert not result.valide
        assert 'invalide' in result.message.lower()
    
    def test_invalid_x(self, validator):
        """Test that X is invalid."""
        result = validator.valider_niveau_equipe('X')
        assert not result.valide
    
    def test_invalid_a5(self, validator):
        """Test that A5 is invalid (only A1-A4 allowed)."""
        result = validator.valider_niveau_equipe('A5')
        assert not result.valide


class TestNiveauCoherence:
    """Tests for level coherence between Niveau_Equipe and Poule."""
    
    def test_coherent_niveau_and_poule(self):
        """Test that matching niveau and poule are detected as coherent."""
        niveau = 'A1'
        poule = 'VBFA1PA'
        niveau_depuis_poule = extraire_niveau_depuis_poule(poule)
        assert niveau == niveau_depuis_poule
    
    def test_incoherent_niveau_and_poule(self):
        """Test that mismatching niveau and poule are detected as incoherent."""
        niveau = 'A2'
        poule = 'VBFA1PA'
        niveau_depuis_poule = extraire_niveau_depuis_poule(poule)
        assert niveau != niveau_depuis_poule
    
    def test_niveau_without_poule(self):
        """Test that niveau can exist without poule."""
        niveau = 'A1'
        poule = ''
        niveau_depuis_poule = extraire_niveau_depuis_poule(poule)
        # When poule is empty, niveau_depuis_poule is empty, so no coherence check
        assert niveau_depuis_poule == ''
        # This is valid: team has niveau but no poule assigned


class TestExtraireGenreDepuisPoule:
    """Tests for extracting gender from pool code."""
    
    def test_vb_feminine(self):
        """Test extraction from volleyball feminine pool."""
        assert extraire_genre_depuis_poule('VBFA1PA') == 'F'
    
    def test_hb_masculine(self):
        """Test extraction from handball masculine pool."""
        assert extraire_genre_depuis_poule('HBMA2PB') == 'M'
    
    def test_bb_mixte(self):
        """Test extraction from basketball mixed pool."""
        assert extraire_genre_depuis_poule('BBXA3PC') == 'X'
    
    def test_empty_string(self):
        """Test extraction from empty string."""
        assert extraire_genre_depuis_poule('') == ''
    
    def test_none(self):
        """Test extraction from None."""
        assert extraire_genre_depuis_poule(None) == ''
    
    def test_invalid_format(self):
        """Test extraction from invalid format."""
        assert extraire_genre_depuis_poule('INVALID') == ''
    
    def test_lowercase(self):
        """Test extraction from lowercase pool code."""
        assert extraire_genre_depuis_poule('vbfa1pa') == 'F'


class TestValiderGenreEquipe:
    """Tests for team gender validation."""
    
    @pytest.fixture
    def validator(self):
        return ColumnValidator()
    
    def test_valid_m(self, validator):
        """Test valid M (Masculin)."""
        result = validator.valider_genre_equipe('M')
        assert result.valide
        assert result.valeur_corrigee == 'M'
    
    def test_valid_f(self, validator):
        """Test valid F (Féminin)."""
        result = validator.valider_genre_equipe('F')
        assert result.valide
        assert result.valeur_corrigee == 'F'
    
    def test_valid_x(self, validator):
        """Test valid X (Mixte)."""
        result = validator.valider_genre_equipe('X')
        assert result.valide
    
    def test_lowercase_normalized(self, validator):
        """Test that lowercase is normalized to uppercase."""
        result = validator.valider_genre_equipe('m')
        assert result.valide
        assert result.valeur_corrigee == 'M'
        assert 'normalisé' in result.message.lower()
    
    def test_h_converted_to_m(self, validator):
        """Test that 'H' (Hommes) is converted to 'M'."""
        result = validator.valider_genre_equipe('H')
        assert result.valide
        assert result.valeur_corrigee == 'M'
        assert 'converti' in result.message.lower()
    
    def test_masculin_converted(self, validator):
        """Test that 'MASCULIN' is converted to 'M'."""
        result = validator.valider_genre_equipe('MASCULIN')
        assert result.valide
        assert result.valeur_corrigee == 'M'
    
    def test_feminin_converted(self, validator):
        """Test that 'FEMININ' is converted to 'F'."""
        result = validator.valider_genre_equipe('FEMININ')
        assert result.valide
        assert result.valeur_corrigee == 'F'
    
    def test_mixte_converted(self, validator):
        """Test that 'MIXTE' is converted to 'X'."""
        result = validator.valider_genre_equipe('MIXTE')
        assert result.valide
        assert result.valeur_corrigee == 'X'
    
    def test_empty_optional(self, validator):
        """Test that empty is valid (optional)."""
        result = validator.valider_genre_equipe('')
        assert result.valide
    
    def test_none_optional(self, validator):
        """Test that None is valid (optional)."""
        result = validator.valider_genre_equipe(None)
        assert result.valide
    
    def test_empty_required(self, validator):
        """Test that empty is invalid when required."""
        result = validator.valider_genre_equipe('', obligatoire=True)
        assert not result.valide
        assert 'obligatoire' in result.message.lower()
    
    def test_invalid_z(self, validator):
        """Test that 'Z' is invalid."""
        result = validator.valider_genre_equipe('Z')
        assert not result.valide
        assert 'invalide' in result.message.lower()


class TestGenreCoherence:
    """Tests for gender coherence between Genre_Equipe and Poule."""
    
    def test_coherent_genre_and_poule(self):
        """Test that matching genre and poule are detected as coherent."""
        genre = 'F'
        poule = 'VBFA1PA'
        genre_depuis_poule = extraire_genre_depuis_poule(poule)
        assert genre == genre_depuis_poule
    
    def test_incoherent_genre_and_poule(self):
        """Test that mismatching genre and poule are detected as incoherent."""
        genre = 'M'
        poule = 'VBFA1PA'
        genre_depuis_poule = extraire_genre_depuis_poule(poule)
        assert genre != genre_depuis_poule
    
    def test_genre_without_poule(self):
        """Test that genre can exist without poule."""
        genre = 'F'
        poule = ''
        genre_depuis_poule = extraire_genre_depuis_poule(poule)
        # When poule is empty, genre_depuis_poule is empty, so no coherence check
        assert genre_depuis_poule == ''
        # This is valid: team has genre but no poule assigned