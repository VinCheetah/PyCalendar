"""
JSON Schema Validator for PyCalendar Solutions.

This module validates generated solution JSON against the defined schema
to ensure data integrity and compatibility with the web interface.

Includes:
- JSON Schema validation (structure)
- Business logic validation (coherence, constraints)
- Detailed reporting with severity levels
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Set
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from enum import Enum

try:
    import jsonschema
    from jsonschema import ValidationError, Draft7Validator
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    ValidationError = Exception  # Fallback
    Draft7Validator = None


class Severity(Enum):
    """Severity levels for validation issues."""
    ERROR = "ERROR"      # Bloquant, invalide le JSON
    WARNING = "WARNING"  # Problème potentiel
    INFO = "INFO"        # Suggestion d'amélioration


@dataclass
class ValidationIssue:
    """Represents a validation issue."""
    severity: Severity
    category: str
    message: str
    location: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self):
        icon = "❌" if self.severity == Severity.ERROR else "⚠️" if self.severity == Severity.WARNING else "ℹ️"
        loc = f" [{self.location}]" if self.location else ""
        return f"{icon} {self.severity.value}: {self.message}{loc}"


class SolutionValidator:
    """Validates solution JSON against schema and business rules."""
    
    def __init__(self, schema_path: Optional[Path] = None):
        """
        Initialize validator with schema.
        
        Args:
            schema_path: Path to solution_schema.json (auto-detected if None)
        """
        if not JSONSCHEMA_AVAILABLE:
            raise ImportError(
                "jsonschema library is required for validation. "
                "Install with: pip install jsonschema"
            )
        
        # Auto-detect schema path if not provided
        if schema_path is None:
            # Try interface/data/schemas/solution_schema.json
            current_dir = Path(__file__).parent.parent
            schema_path = current_dir / "data" / "schemas" / "solution_schema.json"
            
            if not schema_path.exists():
                # Try from project root
                project_root = Path(__file__).parent.parent.parent
                schema_path = project_root / "interface" / "data" / "schemas" / "solution_schema.json"
        
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
        self.schema_path = schema_path
        
        # Load schema
        with open(schema_path, 'r', encoding='utf-8') as f:
            self.schema = json.load(f)
        
        # Create validator
        self.validator = Draft7Validator(self.schema)
        
        # Store issues found during validation
        self.issues: List[ValidationIssue] = []
    
    def validate_full(self, data: Dict[str, Any]) -> Tuple[bool, List[ValidationIssue]]:
        """
        Perform complete validation (schema + business logic).
        
        Args:
            data: Solution data dictionary
            
        Returns:
            Tuple (is_valid, issues) where:
            - is_valid: True if no ERROR-level issues
            - issues: List of all validation issues (errors, warnings, info)
        """
        self.issues = []
        
        # 1. Schema validation
        self._validate_schema(data)
        
        # 2. Business logic validations
        if "entities" in data and "matches" in data:
            self._validate_genres(data)
            self._validate_poules(data)
            self._validate_matches(data)
            self._validate_slots(data)
            self._validate_statistics(data)
            self._validate_institutions(data)
            self._validate_business_rules(data)
        
        # Check if any ERROR-level issues
        has_errors = any(issue.severity == Severity.ERROR for issue in self.issues)
        
        return not has_errors, self.issues
    
    def _validate_schema(self, data: Dict[str, Any]):
        """Validate against JSON schema."""
        try:
            self.validator.validate(data)
        except ValidationError:
            for error in self.validator.iter_errors(data):
                path = " → ".join(str(p) for p in error.absolute_path) if error.absolute_path else "root"
                self.issues.append(ValidationIssue(
                    severity=Severity.ERROR,
                    category="Schema",
                    message=error.message,
                    location=path
                ))
    
    def _validate_genres(self, data: Dict[str, Any]):
        """Validate genre coherence."""
        equipes = {eq["id"]: eq for eq in data["entities"]["equipes"]}
        poules = {p["id"]: p for p in data["entities"]["poules"]}
        
        # Check each team has valid genre
        for eq_id, eq in equipes.items():
            genre = eq.get("genre", "")
            if genre not in ["M", "F", ""]:
                self.issues.append(ValidationIssue(
                    severity=Severity.ERROR,
                    category="Genre",
                    message=f"Genre invalide: '{genre}'",
                    location=f"equipe {eq_id}"
                ))
        
        # Check poule-genre coherence
        for poule_id, poule in poules.items():
            poule_genre = poule.get("genre", "")
            equipes_ids = poule.get("equipes_ids", [])
            
            genres_in_poule = [equipes[eid]["genre"] for eid in equipes_ids if eid in equipes]
            
            if not genres_in_poule:
                continue
            
            # Check all teams have same genre
            unique_genres = set(genres_in_poule)
            if len(unique_genres) > 1:
                self.issues.append(ValidationIssue(
                    severity=Severity.ERROR,
                    category="Genre",
                    message=f"Poule mixte détectée: genres {unique_genres}",
                    location=f"poule {poule_id}",
                    details={"genres": list(unique_genres)}
                ))
            
            # Check poule genre matches team genres
            if poule_genre and unique_genres:
                team_genre = next(iter(unique_genres))
                if team_genre and poule_genre != team_genre:
                    self.issues.append(ValidationIssue(
                        severity=Severity.WARNING,
                        category="Genre",
                        message=f"Genre poule ({poule_genre}) != genre équipes ({team_genre})",
                        location=f"poule {poule_id}"
                    ))
        
        # Check match genres
        for match in data["matches"]["scheduled"]:
            eq1_genre = match.get("equipe1_genre", "")
            eq2_genre = match.get("equipe2_genre", "")
            
            if eq1_genre and eq2_genre and eq1_genre != eq2_genre:
                self.issues.append(ValidationIssue(
                    severity=Severity.ERROR,
                    category="Genre",
                    message=f"Match entre genres différents: {eq1_genre} vs {eq2_genre}",
                    location=f"match {match.get('match_id', '?')}"
                ))
    
    def _validate_poules(self, data: Dict[str, Any]):
        """Validate pool coherence."""
        equipes = {eq["id"]: eq for eq in data["entities"]["equipes"]}
        poules = {p["id"]: p for p in data["entities"]["poules"]}
        
        # Check each team belongs to exactly one pool
        team_pools = defaultdict(list)
        for poule_id, poule in poules.items():
            for eq_id in poule.get("equipes_ids", []):
                team_pools[eq_id].append(poule_id)
        
        for eq_id, pools in team_pools.items():
            if len(pools) == 0:
                self.issues.append(ValidationIssue(
                    severity=Severity.WARNING,
                    category="Poule",
                    message="Équipe sans poule",
                    location=f"equipe {eq_id}"
                ))
            elif len(pools) > 1:
                self.issues.append(ValidationIssue(
                    severity=Severity.ERROR,
                    category="Poule",
                    message=f"Équipe dans plusieurs poules: {pools}",
                    location=f"equipe {eq_id}"
                ))
        
        # Check pool sizes
        for poule_id, poule in poules.items():
            declared_size = poule.get("nb_equipes", 0)
            actual_size = len(poule.get("equipes_ids", []))
            
            if declared_size != actual_size:
                self.issues.append(ValidationIssue(
                    severity=Severity.WARNING,
                    category="Poule",
                    message=f"Taille déclarée ({declared_size}) != réelle ({actual_size})",
                    location=f"poule {poule_id}"
                ))
            
            if actual_size == 0:
                self.issues.append(ValidationIssue(
                    severity=Severity.WARNING,
                    category="Poule",
                    message="Poule vide",
                    location=f"poule {poule_id}"
                ))
            elif actual_size == 1:
                self.issues.append(ValidationIssue(
                    severity=Severity.INFO,
                    category="Poule",
                    message="Poule avec une seule équipe",
                    location=f"poule {poule_id}"
                ))
        
        # Check matches reference same pool teams
        for match in data["matches"]["scheduled"]:
            eq1_id = match.get("equipe1_id")
            eq2_id = match.get("equipe2_id")
            match_poule = match.get("poule")
            
            if eq1_id in equipes and eq2_id in equipes:
                eq1_poule = equipes[eq1_id].get("poule")
                eq2_poule = equipes[eq2_id].get("poule")
                
                if eq1_poule != eq2_poule:
                    self.issues.append(ValidationIssue(
                        severity=Severity.ERROR,
                        category="Poule",
                        message=f"Match inter-poules: {eq1_poule} vs {eq2_poule}",
                        location=f"match {match.get('match_id', '?')}"
                    ))
                
                if match_poule and eq1_poule and match_poule != eq1_poule:
                    self.issues.append(ValidationIssue(
                        severity=Severity.WARNING,
                        category="Poule",
                        message=f"Poule match ({match_poule}) != poule équipe ({eq1_poule})",
                        location=f"match {match.get('match_id', '?')}"
                    ))
    
    def _validate_matches(self, data: Dict[str, Any]):
        """Validate match coherence."""
        equipes = {eq["id"]: eq for eq in data["entities"]["equipes"]}
        gymnases = {g["id"]: g for g in data["entities"]["gymnases"]}
        poules = {p["id"]: p for p in data["entities"]["poules"]}
        
        # Track match counts per pair per pool: {poule_id: {pair: count}}
        match_counts = defaultdict(lambda: defaultdict(int))
        
        for match in data["matches"]["scheduled"]:
            eq1_id = match.get("equipe1_id")
            eq2_id = match.get("equipe2_id")
            match_id = match.get("match_id", "?")
            poule_id = match.get("poule")
            
            # Check team vs itself
            if eq1_id == eq2_id:
                self.issues.append(ValidationIssue(
                    severity=Severity.ERROR,
                    category="Match",
                    message=f"Match d'une équipe contre elle-même: {eq1_id}",
                    location=f"match {match_id}"
                ))
            
            # Check teams exist
            if eq1_id not in equipes:
                self.issues.append(ValidationIssue(
                    severity=Severity.ERROR,
                    category="Match",
                    message=f"Équipe inexistante: {eq1_id}",
                    location=f"match {match_id}"
                ))
            if eq2_id not in equipes:
                self.issues.append(ValidationIssue(
                    severity=Severity.ERROR,
                    category="Match",
                    message=f"Équipe inexistante: {eq2_id}",
                    location=f"match {match_id}"
                ))
            
            # Check gymnase exists
            gymnase = match.get("gymnase")
            if gymnase and gymnase not in gymnases:
                self.issues.append(ValidationIssue(
                    severity=Severity.ERROR,
                    category="Match",
                    message=f"Gymnase inexistant: {gymnase}",
                    location=f"match {match_id}"
                ))
            
            # Check for duplicate matches based on pool type
            if poule_id and eq1_id and eq2_id:
                pair = tuple(sorted([eq1_id, eq2_id]))
                match_counts[poule_id][pair] += 1
                
                # Get pool type
                poule = poules.get(poule_id, {})
                pool_type = poule.get("type", "Classique")  # Default to Classique
                
                # Check limits based on pool type
                max_matches = 2 if pool_type == "Aller-Retour" else 1
                if match_counts[poule_id][pair] > max_matches:
                    self.issues.append(ValidationIssue(
                        severity=Severity.WARNING,
                        category="Match",
                        message=f"Trop de matchs pour la paire {eq1_id} vs {eq2_id} (poule {pool_type}): {match_counts[poule_id][pair]}/{max_matches}",
                        location=f"match {match_id}"
                    ))
            
            # Check time slot validity
            semaine = match.get("semaine")
            horaire = match.get("horaire")
            
            if semaine and semaine < 1:
                self.issues.append(ValidationIssue(
                    severity=Severity.ERROR,
                    category="Match",
                    message=f"Semaine invalide: {semaine}",
                    location=f"match {match_id}"
                ))
    
    def _validate_slots(self, data: Dict[str, Any]):
        """Validate slot coherence."""
        if "slots" not in data:
            return
        
        gymnases = {g["id"]: g for g in data["entities"]["gymnases"]}
        
        # Build occupied slots from matches and check capacity
        slot_occupancy = {}
        for match in data["matches"]["scheduled"]:
            gymnase = match.get("gymnase")
            semaine = match.get("semaine")
            horaire = match.get("horaire")
            match_id = match.get("match_id")
            
            if gymnase and semaine and horaire:
                key = (gymnase, semaine, horaire)
                if key not in slot_occupancy:
                    slot_occupancy[key] = []
                slot_occupancy[key].append(match_id)
        
        # Check capacity violations
        for (gymnase, semaine, horaire), match_ids in slot_occupancy.items():
            gymnase_info = gymnases.get(gymnase, {})
            capacite = gymnase_info.get("capacite", 1)  # Default to 1 if not specified
            
            if len(match_ids) > capacite:
                self.issues.append(ValidationIssue(
                    severity=Severity.ERROR,
                    category="Slot",
                    message=f"Capacité dépassée: {len(match_ids)}/{capacite} matchs au gymnase {gymnase}",
                    location=f"S{semaine} {horaire} - matchs {', '.join(match_ids)}",
                    details={"gymnase": gymnase, "semaine": semaine, "horaire": horaire, "capacite": capacite, "occupancy": len(match_ids)}
                ))
        
        # Check occupied slots
        declared_occupied = {}
        for slot in data["slots"].get("occupied", []):
            gymnase = slot.get("gymnase")
            semaine = slot.get("semaine")
            horaire = slot.get("horaire")
            match_id = slot.get("match_id")
            
            key = (gymnase, semaine, horaire)
            declared_occupied[key] = match_id
            
            # Check match_id exists
            if not match_id:
                self.issues.append(ValidationIssue(
                    severity=Severity.WARNING,
                    category="Slot",
                    message=f"Slot occupé sans match_id",
                    location=f"{gymnase} S{semaine} {horaire}"
                ))
            
            # Check consistency with matches (using slot_occupancy instead of matches_slots)
            if key not in slot_occupancy:
                self.issues.append(ValidationIssue(
                    severity=Severity.WARNING,
                    category="Slot",
                    message=f"Slot occupé mais pas de match correspondant",
                    location=f"{gymnase} S{semaine} {horaire}",
                    details={"match_id": match_id}
                ))
    
    def _validate_statistics(self, data: Dict[str, Any]):
        """Validate statistics coherence."""
        if "statistics" not in data:
            return
        
        stats = data["statistics"]
        
        # Check global stats
        if "global" in stats:
            global_stats = stats["global"]
            
            nb_scheduled = len(data["matches"]["scheduled"])
            nb_unscheduled = len(data["matches"]["unscheduled"])
            nb_total = nb_scheduled + nb_unscheduled
            
            declared_scheduled = global_stats.get("nb_matchs_planifies", 0)
            declared_unscheduled = global_stats.get("nb_matchs_non_planifies", 0)
            declared_total = global_stats.get("nb_matchs_total", 0)
            
            if declared_scheduled != nb_scheduled:
                self.issues.append(ValidationIssue(
                    severity=Severity.WARNING,
                    category="Statistiques",
                    message=f"Matchs planifiés: déclaré {declared_scheduled} != réel {nb_scheduled}",
                    location="statistics.global"
                ))
            
            if declared_unscheduled != nb_unscheduled:
                self.issues.append(ValidationIssue(
                    severity=Severity.WARNING,
                    category="Statistiques",
                    message=f"Matchs non planifiés: déclaré {declared_unscheduled} != réel {nb_unscheduled}",
                    location="statistics.global"
                ))
            
            if declared_total != nb_total:
                self.issues.append(ValidationIssue(
                    severity=Severity.WARNING,
                    category="Statistiques",
                    message=f"Total matchs: déclaré {declared_total} != réel {nb_total}",
                    location="statistics.global"
                ))
            
            # Check planning rate
            if nb_total > 0:
                real_rate = (nb_scheduled / nb_total) * 100
                declared_rate = global_stats.get("taux_planification", 0)
                
                if abs(real_rate - declared_rate) > 0.1:
                    self.issues.append(ValidationIssue(
                        severity=Severity.INFO,
                        category="Statistiques",
                        message=f"Taux de planification: déclaré {declared_rate:.1f}% != réel {real_rate:.1f}%",
                        location="statistics.global"
                    ))
        
        # Check per-pool stats
        if "par_poule" in stats:
            for poule_id, poule_stats in stats["par_poule"].items():
                # Count real matches for this pool
                real_scheduled = sum(1 for m in data["matches"]["scheduled"] if m.get("poule") == poule_id)
                real_unscheduled = sum(1 for m in data["matches"]["unscheduled"] if m.get("poule") == poule_id)
                
                declared_scheduled = poule_stats.get("nb_matchs_planifies", 0)
                declared_unscheduled = poule_stats.get("nb_matchs_non_planifies", 0)
                
                if declared_scheduled != real_scheduled:
                    self.issues.append(ValidationIssue(
                        severity=Severity.INFO,
                        category="Statistiques",
                        message=f"Matchs planifiés poule: déclaré {declared_scheduled} != réel {real_scheduled}",
                        location=f"poule {poule_id}"
                    ))
    
    def _validate_institutions(self, data: Dict[str, Any]):
        """Validate institution coherence."""
        equipes = data["entities"]["equipes"]
        
        # Check institution format in team names
        for eq in equipes:
            nom = eq.get("nom", "")
            institution = eq.get("institution", "")
            
            # Institution should be in the name
            if institution and institution not in nom:
                self.issues.append(ValidationIssue(
                    severity=Severity.INFO,
                    category="Institution",
                    message=f"Institution '{institution}' absente du nom '{nom}'",
                    location=f"equipe {eq['id']}"
                ))
        
        # Check is_entente flag (removed: same institution matches are not a problem)
        # The validation for same institution matches has been removed as per user requirements
    
    def _validate_business_rules(self, data: Dict[str, Any]):
        """Validate business rules and constraints."""
        equipes = {eq["id"]: eq for eq in data["entities"]["equipes"]}
        
        # Check matches per team per week
        team_week_matches = defaultdict(lambda: defaultdict(int))
        
        for match in data["matches"]["scheduled"]:
            eq1_id = match.get("equipe1_id")
            eq2_id = match.get("equipe2_id")
            semaine = match.get("semaine")
            
            if semaine:
                team_week_matches[eq1_id][semaine] += 1
                team_week_matches[eq2_id][semaine] += 1
        
        for eq_id, weeks in team_week_matches.items():
            for semaine, count in weeks.items():
                if count > 2:
                    self.issues.append(ValidationIssue(
                        severity=Severity.WARNING,
                        category="Règles métier",
                        message=f"{count} matchs en semaine {semaine} (max recommandé: 2)",
                        location=f"equipe {eq_id}"
                    ))
        
        # Check preferred times violations (only if BOTH teams play before their preferred time)
        # REMOVED: Business rules for preferred times are no longer validated
        
        # Check unavailability violations
        for match in data["matches"]["scheduled"]:
            eq1_id = match.get("equipe1_id")
            eq2_id = match.get("equipe2_id")
            semaine = match.get("semaine")
            horaire = match.get("horaire")
            
            if eq1_id in equipes:
                indispo = equipes[eq1_id].get("semaines_indisponibles", {})
                if str(semaine) in indispo and horaire in indispo[str(semaine)]:
                    self.issues.append(ValidationIssue(
                        severity=Severity.ERROR,
                        category="Règles métier",
                        message=f"Équipe 1 indisponible S{semaine} {horaire}",
                        location=f"match {match.get('match_id', '?')}"
                    ))
            
            if eq2_id in equipes:
                indispo = equipes[eq2_id].get("semaines_indisponibles", {})
                if str(semaine) in indispo and horaire in indispo[str(semaine)]:
                    self.issues.append(ValidationIssue(
                        severity=Severity.ERROR,
                        category="Règles métier",
                        message=f"Équipe 2 indisponible S{semaine} {horaire}",
                        location=f"match {match.get('match_id', '?')}"
                    ))
        
        # Check solution quality (high penalties)
        high_penalty_threshold = 100
        for match in data["matches"]["scheduled"]:
            penalties = match.get("penalties", {})
            total = penalties.get("total", 0)
            
            if total > high_penalty_threshold:
                self.issues.append(ValidationIssue(
                    severity=Severity.WARNING,
                    category="Qualité",
                    message=f"Pénalités élevées: {total:.0f}",
                    location=f"match {match.get('match_id', '?')}",
                    details=penalties
                ))
    
    def generate_report(self, issues: List[ValidationIssue]) -> str:
        """
        Generate detailed validation report.
        
        Args:
            issues: List of validation issues
            
        Returns:
            Formatted report string
        """
        if not issues:
            return "✅ Aucun problème détecté"
        
        # Group by severity and category
        by_severity = defaultdict(list)
        by_category = defaultdict(list)
        
        for issue in issues:
            by_severity[issue.severity].append(issue)
            by_category[issue.category].append(issue)
        
        lines = []
        lines.append("=" * 80)
        lines.append("RAPPORT DE VALIDATION")
        lines.append("=" * 80)
        
        # Summary
        lines.append(f"\n📊 RÉSUMÉ")
        lines.append(f"   Total: {len(issues)} problème(s)")
        lines.append(f"   Erreurs: {len(by_severity[Severity.ERROR])}")
        lines.append(f"   Avertissements: {len(by_severity[Severity.WARNING])}")
        lines.append(f"   Informations: {len(by_severity[Severity.INFO])}")
        
        # By category
        lines.append(f"\n📁 PAR CATÉGORIE")
        for category, cat_issues in sorted(by_category.items()):
            lines.append(f"   {category}: {len(cat_issues)}")
        
        # Detailed issues
        for severity in [Severity.ERROR, Severity.WARNING, Severity.INFO]:
            severity_issues = by_severity[severity]
            if not severity_issues:
                continue
            
            icon = "❌" if severity == Severity.ERROR else "⚠️" if severity == Severity.WARNING else "ℹ️"
            lines.append(f"\n{icon} {severity.value}S ({len(severity_issues)})")
            lines.append("-" * 80)
            
            for issue in severity_issues:
                lines.append(f"\n  {issue.category}: {issue.message}")
                if issue.location:
                    lines.append(f"  └─ {issue.location}")
                if issue.details:
                    for key, value in issue.details.items():
                        lines.append(f"     • {key}: {value}")
        
        lines.append("\n" + "=" * 80)
        
        return "\n".join(lines)
    
    def validate(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate solution data against schema (legacy method).
        
        Args:
            data: Solution data dictionary
            
        Returns:
            Tuple (is_valid, errors) where:
            - is_valid: True if data is valid
            - errors: List of validation error messages (empty if valid)
        """
        is_valid, issues = self.validate_full(data)
        
        # Convert to legacy format (only errors)
        errors = [str(issue) for issue in issues if issue.severity == Severity.ERROR]
        
        return is_valid, errors
    
    def validate_and_report(self, data: Dict[str, Any], verbose: bool = True) -> bool:
        """
        Validate and print detailed report.
        
        Args:
            data: Solution data dictionary
            verbose: Whether to print detailed errors
            
        Returns:
            True if valid, False otherwise
        """
        is_valid, errors = self.validate(data)
        
        if is_valid:
            if verbose:
                print("✅ Solution JSON is valid!")
                print(f"   Version: {data.get('version', 'unknown')}")
                print(f"   Matches: {len(data.get('matches', {}).get('scheduled', []))}")
                print(f"   Teams: {len(data.get('entities', {}).get('equipes', []))}")
            return True
        else:
            print(f"❌ Solution JSON validation failed ({len(errors)} errors)")
            if verbose:
                print("\nValidation errors:")
                for i, error in enumerate(errors, 1):
                    print(f"\n{i}. {error}")
            return False
    
    def _format_error(self, error: ValidationError) -> str:
        """
        Format a validation error for display.
        
        Args:
            error: ValidationError from jsonschema
            
        Returns:
            Formatted error message
        """
        # Build path to error location
        path = " → ".join(str(p) for p in error.absolute_path) if error.absolute_path else "root"
        
        # Get error message
        message = error.message
        
        # Add context if available
        if error.validator == 'required':
            missing = error.message.split("'")[1] if "'" in error.message else "field"
            return f"Missing required field '{missing}' at: {path}"
        
        elif error.validator == 'type':
            expected = error.validator_value
            return f"Type error at {path}: {message}"
        
        elif error.validator == 'enum':
            allowed = error.validator_value
            return f"Invalid value at {path}: must be one of {allowed}"
        
        else:
            return f"{path}: {message}"


def validate_solution_file(file_path: Path, verbose: bool = True) -> bool:
    """
    Validate a solution JSON file.
    
    Args:
        file_path: Path to JSON file
        verbose: Whether to print detailed report
        
    Returns:
        True if valid, False otherwise
    """
    if not JSONSCHEMA_AVAILABLE:
        print("⚠️  jsonschema not installed, skipping validation")
        print("   Install with: pip install jsonschema")
        return True  # Don't fail if library not available
    
    try:
        # Load JSON
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validate
        validator = SolutionValidator()
        return validator.validate_and_report(data, verbose=verbose)
    
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        return False
    
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        return False
    
    except Exception as e:
        print(f"❌ Validation error: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return False


def main():
    """CLI for validating solution files."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Validate PyCalendar solution JSON against schema',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate a solution file
  python -m interface.core.validator output/latest_volley_v2.json
  
  # Validate quietly (only show result)
  python -m interface.core.validator output/latest_volley_v2.json --quiet
        """
    )
    
    parser.add_argument(
        'file',
        type=str,
        help='Path to solution JSON file'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Only show validation result (no details)'
    )
    
    args = parser.parse_args()
    
    file_path = Path(args.file)
    is_valid = validate_solution_file(file_path, verbose=not args.quiet)
    
    # Exit with appropriate code
    exit(0 if is_valid else 1)


if __name__ == '__main__':
    main()
