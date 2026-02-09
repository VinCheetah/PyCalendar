"""
Match duplicate detection for Excel configuration.

Detects and reports duplicate matches in Matchs_Fixes sheet:
- Same teams playing multiple times in non-Aller-Retour pools
- Handles team order (A vs B == B vs A)
- Respects "compte double" / "double comptage" annotations
- Identifies missing return matches in Aller-Retour pools
"""

import re
import pandas as pd
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any
from collections import defaultdict

from .reports import Severity, CellIssue


# Patterns indicating a match should be counted double (not a real duplicate)
COMPTE_DOUBLE_PATTERNS = [
    r'compte\s*double',
    r'double\s*comptage',
    r'comptabilisé\s*double',
    r'match\s*double',
    r'doublon\s*volontaire',
    r'double\s*count',
    r'forfait\s*double',  # Sometimes forfaits are counted as double
]

# Compiled regex for efficiency
COMPTE_DOUBLE_REGEX = re.compile(
    '|'.join(COMPTE_DOUBLE_PATTERNS), 
    re.IGNORECASE
)


@dataclass
class MatchInfo:
    """Information about a match for duplicate detection."""
    row_index: int  # Excel row (1-indexed, including header)
    equipe_1: str
    equipe_2: str
    genre: str
    poule: str
    semaine: Optional[int]
    remarques: Optional[str] = None
    
    @property
    def match_key(self) -> Tuple[str, str, str]:
        """
        Returns a normalized key for match comparison.
        Teams are sorted alphabetically so A-vs-B == B-vs-A.
        """
        teams = tuple(sorted([self.equipe_1.strip().upper(), self.equipe_2.strip().upper()]))
        return (teams[0], teams[1], self.genre.strip().upper() if self.genre else '')
    
    @property
    def is_compte_double(self) -> bool:
        """Check if this match is marked as 'compte double'."""
        if not self.remarques:
            return False
        return bool(COMPTE_DOUBLE_REGEX.search(self.remarques))
    
    def format_display(self) -> str:
        """Format match for display in error messages."""
        return f"{self.equipe_1} vs {self.equipe_2} [{self.genre}]"


@dataclass
class DuplicateGroup:
    """A group of duplicate matches."""
    matches: List[MatchInfo] = field(default_factory=list)
    poule: str = ""
    is_aller_retour: bool = False
    
    @property
    def count(self) -> int:
        return len(self.matches)
    
    @property
    def real_duplicates(self) -> List[MatchInfo]:
        """Matches that are real duplicates (not marked compte double)."""
        return [m for m in self.matches if not m.is_compte_double]
    
    @property
    def compte_double_matches(self) -> List[MatchInfo]:
        """Matches marked as compte double."""
        return [m for m in self.matches if m.is_compte_double]
    
    @property
    def expected_count(self) -> int:
        """Expected number of matches between two teams."""
        return 2 if self.is_aller_retour else 1
    
    @property
    def is_valid(self) -> bool:
        """Check if the number of matches is valid."""
        real_count = len(self.real_duplicates)
        return real_count <= self.expected_count


class MatchDuplicateDetector:
    """
    Detects duplicate matches in Matchs_Fixes.
    
    Features:
    - Detects same match played multiple times
    - Handles team order (A vs B == B vs A)
    - Respects pool type (Aller-Retour allows 2 matches)
    - Recognizes "compte double" annotations
    - Reports missing return matches in Aller-Retour pools
    """
    
    def __init__(self, poules_aller_retour: Optional[Set[str]] = None):
        """
        Initialize detector.
        
        Args:
            poules_aller_retour: Set of pool names that are Aller-Retour type
        """
        self.poules_aller_retour = poules_aller_retour or set()
        self.matches: List[MatchInfo] = []
        self.duplicates: Dict[Tuple, DuplicateGroup] = {}
        
    def load_matches(self, df: pd.DataFrame) -> None:
        """
        Load matches from Matchs_Fixes DataFrame.
        
        Expected columns: Equipe_1, Equipe_2, Genre, Poule, Semaine, Remarques
        """
        self.matches = []
        
        required_cols = ['Equipe_1', 'Equipe_2']
        for col in required_cols:
            if col not in df.columns:
                return  # Missing columns, can't analyze
        
        for idx, row in df.iterrows():
            equipe_1 = str(row.get('Equipe_1', '')).strip()
            equipe_2 = str(row.get('Equipe_2', '')).strip()
            
            # Skip empty rows
            if not equipe_1 or not equipe_2 or pd.isna(row.get('Equipe_1')) or pd.isna(row.get('Equipe_2')):
                continue
            
            # Parse semaine (handle "N (dd/mm)" format)
            semaine_raw = row.get('Semaine')
            semaine = None
            if semaine_raw is not None and not pd.isna(semaine_raw):
                semaine_str = str(semaine_raw).strip()
                match = re.match(r'^(\d+)', semaine_str)
                if match:
                    semaine = int(match.group(1))
            
            match_info = MatchInfo(
                row_index=idx + 2,  # +2 for header row and 0-indexing
                equipe_1=equipe_1,
                equipe_2=equipe_2,
                genre=str(row.get('Genre', '')).strip() if not pd.isna(row.get('Genre')) else '',
                poule=str(row.get('Poule', '')).strip() if not pd.isna(row.get('Poule')) else '',
                semaine=semaine,
                remarques=str(row.get('Remarques', '')) if not pd.isna(row.get('Remarques')) else None
            )
            self.matches.append(match_info)
    
    def detect_duplicates(self) -> List[CellIssue]:
        """
        Detect duplicate matches and return issues.
        
        Returns:
            List of CellIssue for each duplicate detected
        """
        issues = []
        
        # Group matches by their normalized key (teams + genre)
        match_groups: Dict[Tuple, DuplicateGroup] = defaultdict(lambda: DuplicateGroup())
        
        for match in self.matches:
            key = match.match_key
            group = match_groups[key]
            group.matches.append(match)
            group.poule = match.poule
            group.is_aller_retour = match.poule.upper() in {p.upper() for p in self.poules_aller_retour}
        
        # Analyze each group
        for key, group in match_groups.items():
            if group.count < 2:
                continue  # No duplicates possible
            
            real_matches = group.real_duplicates
            compte_double = group.compte_double_matches
            
            # Helper to format all concerned rows
            def format_all_rows(matches: List[MatchInfo]) -> str:
                rows = [str(m.row_index) for m in matches]
                return ', '.join(rows)
            
            # For Aller-Retour pools: 2 matches are expected
            if group.is_aller_retour:
                if len(real_matches) > 2:
                    # More than 2 real matches - this is a problem
                    # Flag ALL excess matches (all of them, not just from 3rd)
                    all_rows = format_all_rows(real_matches)
                    for match in real_matches:
                        issues.append(CellIssue(
                            ligne=match.row_index,
                            colonne='Equipe_1',
                            message=f"Match en excès : {match.format_display()} apparaît {len(real_matches)} fois (max 2 en Aller-Retour). Lignes concernées : {all_rows}",
                            severite=Severity.ERROR,
                            valeur_actuelle=match.equipe_1,
                        ))
                        # Also highlight Equipe_2 column
                        issues.append(CellIssue(
                            ligne=match.row_index,
                            colonne='Equipe_2',
                            message=f"Match en excès : {match.format_display()} apparaît {len(real_matches)} fois (max 2 en Aller-Retour). Lignes concernées : {all_rows}",
                            severite=Severity.ERROR,
                            valeur_actuelle=match.equipe_2,
                        ))
            else:
                # For Classique pools: only 1 match is expected
                if len(real_matches) > 1:
                    # Duplicates found - flag ALL matches, not just extras
                    has_compte_double = len(compte_double) > 0
                    all_rows = format_all_rows(real_matches)
                    
                    for match in real_matches:
                        if has_compte_double:
                            # Some match is marked compte double, just warn
                            issues.append(CellIssue(
                                ligne=match.row_index,
                                colonne='Equipe_1',
                                message=f"Match en doublon (un autre est marqué 'compte double') : {match.format_display()}. Lignes concernées : {all_rows}",
                                severite=Severity.WARNING,
                                valeur_actuelle=match.equipe_1,
                            ))
                            issues.append(CellIssue(
                                ligne=match.row_index,
                                colonne='Equipe_2',
                                message=f"Match en doublon (un autre est marqué 'compte double') : {match.format_display()}. Lignes concernées : {all_rows}",
                                severite=Severity.WARNING,
                                valeur_actuelle=match.equipe_2,
                            ))
                        else:
                            # Real duplicate with no justification
                            issues.append(CellIssue(
                                ligne=match.row_index,
                                colonne='Equipe_1',
                                message=f"Match en doublon : {match.format_display()} (poule {group.poule} non Aller-Retour). Lignes concernées : {all_rows}",
                                severite=Severity.ERROR,
                                valeur_actuelle=match.equipe_1,
                            ))
                            issues.append(CellIssue(
                                ligne=match.row_index,
                                colonne='Equipe_2',
                                message=f"Match en doublon : {match.format_display()} (poule {group.poule} non Aller-Retour). Lignes concernées : {all_rows}",
                                severite=Severity.ERROR,
                                valeur_actuelle=match.equipe_2,
                            ))
        
        return issues
    
    def check_missing_return_matches(self) -> List[CellIssue]:
        """
        Check for missing return matches in Aller-Retour pools.
        
        Returns:
            List of warnings for matches missing their return leg
        """
        issues = []
        
        # Group matches by key
        match_groups: Dict[Tuple, List[MatchInfo]] = defaultdict(list)
        
        for match in self.matches:
            if match.poule.upper() in {p.upper() for p in self.poules_aller_retour}:
                key = match.match_key
                match_groups[key].append(match)
        
        # Check each Aller-Retour match pair
        for key, matches in match_groups.items():
            real_matches = [m for m in matches if not m.is_compte_double]
            
            if len(real_matches) == 1:
                match = real_matches[0]
                # Only one match found in Aller-Retour pool - might be missing return
                # This is just an info, not an error (could be planned later)
                issues.append(CellIssue(
                    ligne=match.row_index,
                    colonne='Equipe_2',
                    message=f"Match retour manquant ? {match.format_display()} (poule Aller-Retour, un seul match trouvé)",
                    severite=Severity.INFO,
                    valeur_actuelle=match.equipe_2,
                ))
        
        return issues
    
    def detect_same_team_match(self) -> List[CellIssue]:
        """
        Detect matches where a team plays against itself.
        
        Returns:
            List of errors for self-matches
        """
        issues = []
        
        for match in self.matches:
            if match.equipe_1.strip().upper() == match.equipe_2.strip().upper():
                issues.append(CellIssue(
                    ligne=match.row_index,
                    colonne='Equipe_2',
                    message=f"Match impossible : une équipe ne peut pas jouer contre elle-même ({match.equipe_1})",
                    severite=Severity.ERROR,
                    valeur_actuelle=match.equipe_2,
                ))
        
        return issues
    
    def run_all_checks(self) -> List[CellIssue]:
        """
        Run all duplicate and consistency checks.
        
        Returns:
            Combined list of all issues found
        """
        issues = []
        
        # Check for self-matches first
        issues.extend(self.detect_same_team_match())
        
        # Check for duplicates
        issues.extend(self.detect_duplicates())
        
        # Note: Missing return matches are informational only
        # Uncomment if you want to include them:
        # issues.extend(self.check_missing_return_matches())
        
        return issues


def detect_match_duplicates(
    df_matchs_fixes: pd.DataFrame,
    df_types_poules: Optional[pd.DataFrame] = None
) -> List[CellIssue]:
    """
    Convenience function to detect match duplicates.
    
    Args:
        df_matchs_fixes: DataFrame from Matchs_Fixes sheet
        df_types_poules: Optional DataFrame from Types_Poules sheet
        
    Returns:
        List of issues found
    """
    # Build set of Aller-Retour pools
    poules_ar = set()
    if df_types_poules is not None and 'Poule' in df_types_poules.columns and 'Type' in df_types_poules.columns:
        for _, row in df_types_poules.iterrows():
            poule = str(row.get('Poule', '')).strip()
            type_poule = str(row.get('Type', '')).strip()
            if 'retour' in type_poule.lower():
                poules_ar.add(poule)
    
    detector = MatchDuplicateDetector(poules_aller_retour=poules_ar)
    detector.load_matches(df_matchs_fixes)
    
    return detector.run_all_checks()
