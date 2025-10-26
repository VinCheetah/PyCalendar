#!/usr/bin/env python3
"""
Validate modifications without applying them.

This script checks if modifications are feasible without making any changes.
Useful for checking constraints before committing to changes.

Usage:
    python scripts/validate_modifications.py <excel_file> <modifications_json> <config_yaml>
    
Example:
    python scripts/validate_modifications.py \\
        examples/volleyball/calendrier_volley.xlsx \\
        modifications_2025-01-16.json \\
        configs/config_volley.yaml
"""

import sys
import json
from pathlib import Path
from typing import Dict, List
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.apply_modifications import ModificationApplier, Modification


class ModificationValidator:
    """Extended validator with detailed constraint analysis."""
    
    def __init__(self, excel_file: str, config_file: str):
        """Initialize validator."""
        self.applier = ModificationApplier(excel_file, config_file)
        self.validation_results: Dict[str, dict] = {}
    
    def validate_all(self, modifications: List[Modification]) -> Dict[str, dict]:
        """
        Validate all modifications and return detailed results.
        
        Returns:
            Dict mapping match_id to validation result:
            {
                'valid': bool,
                'errors': List[str],
                'warnings': List[str],
                'suggestions': List[str]
            }
        """
        print(f"🔍 Validating {len(modifications)} modification(s)...\n")
        
        results = {}
        
        for i, mod in enumerate(modifications, 1):
            print(f"[{i}/{len(modifications)}] Validating: {mod.teams}")
            
            is_valid, messages = self.applier.validate_modification(mod)
            
            errors = [m for m in messages if m.startswith('❌')]
            warnings = [m for m in messages if m.startswith('⚠️')]
            suggestions = self._generate_suggestions(mod, errors)
            
            results[mod.match_id] = {
                'valid': is_valid,
                'errors': errors,
                'warnings': warnings,
                'suggestions': suggestions,
                'modification': mod
            }
            
            # Print status
            if is_valid:
                print(f"   ✅ Valid")
            else:
                print(f"   ❌ Invalid - {len(errors)} error(s)")
                for error in errors[:2]:  # Show first 2 errors
                    print(f"      {error}")
        
        self.validation_results = results
        return results
    
    def _generate_suggestions(self, mod: Modification, errors: List[str]) -> List[str]:
        """Generate alternative suggestions when modification fails."""
        suggestions = []
        
        # If venue not available, suggest alternative venues
        if any('not available' in e for e in errors):
            alt_venues = self._find_alternative_venues(mod.new_week, mod.new_time)
            if alt_venues:
                suggestions.append(
                    f"💡 Alternative venues available at week {mod.new_week}, {mod.new_time}: "
                    f"{', '.join(alt_venues[:3])}"
                )
        
        # If time conflict, suggest alternative times
        if any('conflict' in e.lower() for e in errors):
            alt_times = self._find_alternative_times(mod.new_venue, mod.new_week)
            if alt_times:
                suggestions.append(
                    f"💡 Alternative times at {mod.new_venue}, week {mod.new_week}: "
                    f"{', '.join(alt_times[:3])}"
                )
        
        # If team conflict, suggest alternative weeks
        if any('Team conflict' in e for e in errors):
            alt_weeks = self._find_alternative_weeks(mod.new_venue, mod.new_time)
            if alt_weeks:
                suggestions.append(
                    f"💡 Alternative weeks at {mod.new_venue}, {mod.new_time}: "
                    f"{', '.join(map(str, alt_weeks[:3]))}"
                )
        
        return suggestions
    
    def _find_alternative_venues(self, week: int, time: str) -> List[str]:
        """Find venues available at given week and time."""
        alternatives = []
        for venue_name, venue in self.applier.venues.items():
            for creneau in venue.creneaux:
                if creneau.semaine == week and creneau.horaire == time:
                    # Check if slot is free
                    conflicts = self.applier.df_calendar[
                        (self.applier.df_calendar['Semaine'] == week) &
                        (self.applier.df_calendar['Horaire'] == time) &
                        (self.applier.df_calendar['Gymnase'] == venue_name)
                    ]
                    if len(conflicts) == 0:
                        alternatives.append(venue_name)
        return alternatives
    
    def _find_alternative_times(self, venue: str, week: int) -> List[str]:
        """Find available times at given venue and week."""
        if venue not in self.applier.venues:
            return []
        
        alternatives = []
        venue_obj = self.applier.venues[venue]
        for creneau in venue_obj.creneaux:
            if creneau.semaine == week:
                # Check if slot is free
                conflicts = self.applier.df_calendar[
                    (self.applier.df_calendar['Semaine'] == week) &
                    (self.applier.df_calendar['Horaire'] == creneau.horaire) &
                    (self.applier.df_calendar['Gymnase'] == venue)
                ]
                if len(conflicts) == 0:
                    alternatives.append(creneau.horaire)
        return alternatives
    
    def _find_alternative_weeks(self, venue: str, time: str) -> List[int]:
        """Find available weeks at given venue and time."""
        if venue not in self.applier.venues:
            return []
        
        alternatives = []
        venue_obj = self.applier.venues[venue]
        for creneau in venue_obj.creneaux:
            if creneau.horaire == time:
                # Check if slot is free
                conflicts = self.applier.df_calendar[
                    (self.applier.df_calendar['Semaine'] == creneau.semaine) &
                    (self.applier.df_calendar['Horaire'] == time) &
                    (self.applier.df_calendar['Gymnase'] == venue)
                ]
                if len(conflicts) == 0:
                    alternatives.append(creneau.semaine)
        return sorted(alternatives)
    
    def print_summary(self):
        """Print validation summary."""
        results = self.validation_results
        
        valid_count = sum(1 for r in results.values() if r['valid'])
        invalid_count = len(results) - valid_count
        total_errors = sum(len(r['errors']) for r in results.values())
        total_warnings = sum(len(r['warnings']) for r in results.values())
        
        print("\n" + "="*70)
        print("VALIDATION SUMMARY")
        print("="*70)
        
        print(f"\n📊 Overall Statistics:")
        print(f"   Total modifications: {len(results)}")
        print(f"   ✅ Valid: {valid_count}")
        print(f"   ❌ Invalid: {invalid_count}")
        print(f"   ⚠️  Total warnings: {total_warnings}")
        print(f"   ❌ Total errors: {total_errors}")
        
        if invalid_count > 0:
            print(f"\n❌ Invalid Modifications ({invalid_count}):")
            for match_id, result in results.items():
                if not result['valid']:
                    mod = result['modification']
                    print(f"\n   {mod.teams}")
                    print(f"   {mod.original_venue} W{mod.original_week} {mod.original_time} → "
                          f"{mod.new_venue} W{mod.new_week} {mod.new_time}")
                    
                    for error in result['errors']:
                        print(f"      {error}")
                    
                    for suggestion in result['suggestions']:
                        print(f"      {suggestion}")
        
        if total_warnings > 0:
            print(f"\n⚠️  Warnings ({total_warnings}):")
            for match_id, result in results.items():
                if result['warnings']:
                    mod = result['modification']
                    print(f"\n   {mod.teams}")
                    for warning in result['warnings']:
                        print(f"      {warning}")
        
        if valid_count > 0:
            print(f"\n✅ Valid Modifications ({valid_count}):")
            for match_id, result in results.items():
                if result['valid']:
                    mod = result['modification']
                    print(f"   {mod.teams}: "
                          f"{mod.original_venue} W{mod.original_week} {mod.original_time} → "
                          f"{mod.new_venue} W{mod.new_week} {mod.new_time}")
        
        print("\n" + "="*70)
        
        # Final recommendation
        if invalid_count == 0:
            print("\n✅ All modifications are valid! You can safely apply them.")
            print(f"\n   Run: python scripts/apply_modifications.py \\")
            print(f"            <excel_file> <json_file> <config_file>")
        else:
            print(f"\n⚠️  {invalid_count} modification(s) have errors.")
            print("   Please fix the issues or remove invalid modifications before applying.")
        
        print()


def main():
    """Main entry point."""
    if len(sys.argv) < 4:
        print(__doc__)
        return 1
    
    excel_file = sys.argv[1]
    json_file = sys.argv[2]
    config_file = sys.argv[3]
    
    # Validate files exist
    if not Path(excel_file).exists():
        print(f"❌ Excel file not found: {excel_file}")
        return 1
    
    if not Path(json_file).exists():
        print(f"❌ JSON file not found: {json_file}")
        return 1
    
    if not Path(config_file).exists():
        print(f"❌ Config file not found: {config_file}")
        return 1
    
    try:
        # Initialize validator
        print(f"📊 Loading calendar from: {excel_file}")
        validator = ModificationValidator(excel_file, config_file)
        
        # Load modifications
        print(f"📥 Loading modifications from: {json_file}")
        modifications = validator.applier.load_modifications(json_file)
        
        if not modifications:
            print("ℹ️  No modifications to validate")
            return 0
        
        # Validate
        results = validator.validate_all(modifications)
        
        # Print summary
        validator.print_summary()
        
        # Return appropriate exit code
        invalid_count = sum(1 for r in results.values() if not r['valid'])
        return 0 if invalid_count == 0 else 1
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
