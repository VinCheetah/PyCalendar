"""Base constraint classes."""

from abc import ABC, abstractmethod
from typing import List, Dict, Tuple
from core.models import Match, Creneau


class Constraint(ABC):
    """Abstract base class for all constraints."""
    
    def __init__(self, weight: float = 1.0, hard: bool = True):
        self.weight = weight
        self.hard = hard
    
    @abstractmethod
    def validate(self, match: Match, creneau: Creneau, solution_state: Dict) -> Tuple[bool, float]:
        """
        Validate if assigning match to creneau respects constraint.
        Returns: (is_valid, penalty_score)
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get constraint name."""
        pass


class ConstraintValidator:
    """Validates a match assignment against multiple constraints."""
    
    def __init__(self):
        self.constraints: List[Constraint] = []
    
    def add_constraint(self, constraint: Constraint):
        """Add a constraint to the validator."""
        self.constraints.append(constraint)
    
    def validate_assignment(self, match: Match, creneau: Creneau, 
                          solution_state: Dict) -> Tuple[bool, float]:
        """
        Validate match assignment against all constraints.
        Returns: (is_valid, total_penalty)
        """
        total_penalty = 0.0
        is_valid = True
        
        for constraint in self.constraints:
            valid, penalty = constraint.validate(match, creneau, solution_state)
            
            if constraint.hard and not valid:
                return False, float('inf')
            
            if not valid:
                is_valid = False
            
            total_penalty += penalty * constraint.weight
        
        return is_valid, total_penalty
    
    def get_constraint_violations(self, match: Match, creneau: Creneau, 
                                 solution_state: Dict) -> List[str]:
        """Get list of violated constraints."""
        violations = []
        
        for constraint in self.constraints:
            valid, _ = constraint.validate(match, creneau, solution_state)
            if not valid:
                violations.append(constraint.get_name())
        
        return violations
