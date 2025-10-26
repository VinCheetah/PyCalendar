"""Data validators."""

from typing import List, Dict
from pycalendar.core.models import Equipe, Gymnase


class DataValidator:
    """Validates loaded data."""
    
    @staticmethod
    def validate_equipes(equipes: List[Equipe]) -> Dict[str, List[str]]:
        """Validate teams data and return warnings/errors."""
        issues = {'errors': [], 'warnings': []}
        
        if not equipes:
            issues['errors'].append("No teams loaded")
            return issues
        
        # Utiliser un set d'équipes complètes (inclut le genre via __hash__ et __eq__)
        equipes_uniques = set()
        for equipe in equipes:
            if not equipe.nom:
                issues['errors'].append("Team with empty name")
            elif equipe in equipes_uniques:
                # Vraiment un doublon (même nom, genre, poule)
                issues['errors'].append(f"Duplicate team: {equipe.nom_complet} ({equipe.genre}) in pool {equipe.poule}")
            else:
                equipes_uniques.add(equipe)
            
            if not equipe.poule:
                issues['warnings'].append(f"Team {equipe.nom} has no pool assigned")
        
        return issues
    
    @staticmethod
    def validate_gymnases(gymnases: List[Gymnase]) -> Dict[str, List[str]]:
        """Validate venues data and return warnings/errors."""
        issues = {'errors': [], 'warnings': []}
        
        if not gymnases:
            issues['errors'].append("No venues loaded")
            return issues
        
        for gymnase in gymnases:
            if not gymnase.nom:
                issues['errors'].append("Venue with empty name")
            
            if not gymnase.horaires_disponibles:
                issues['warnings'].append(f"Venue {gymnase.nom} has no available time slots")
            
            if gymnase.capacite < 1:
                issues['errors'].append(f"Venue {gymnase.nom} has invalid capacity: {gymnase.capacite}")
        
        return issues
    
    @staticmethod
    def validate_all(equipes: List[Equipe], gymnases: List[Gymnase]) -> bool:
        """Validate all data. Returns True if no critical errors."""
        issues_equipes = DataValidator.validate_equipes(equipes)
        issues_gymnases = DataValidator.validate_gymnases(gymnases)
        
        all_errors = issues_equipes['errors'] + issues_gymnases['errors']
        all_warnings = issues_equipes['warnings'] + issues_gymnases['warnings']
        
        if all_errors:
            print("❌ Validation errors:")
            for error in all_errors:
                print(f"  - {error}")
            return False
        
        if all_warnings:
            print("⚠️  Validation warnings:")
            for warning in all_warnings:
                print(f"  - {warning}")
        
        return True
