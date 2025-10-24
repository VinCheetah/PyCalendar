#!/usr/bin/env python3
"""
Apply modifications from JSON to Excel calendar.

This script reads JSON modifications exported from the HTML interface,
validates constraints, applies changes to the Excel calendar, and
optionally regenerates the HTML visualization.

Usage:
    python scripts/apply_modifications.py <excel_file> <modifications_json> <config_yaml> [--no-html]
    
Example:
    python scripts/apply_modifications.py \\
        data_volley/calendrier_volley.xlsx \\
        modifications_2025-01-16.json \\
        configs/config_volley.yaml
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import pandas as pd
from dataclasses import dataclass

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import Config
from core.models import Creneau, Gymnase, Match
from visualization.html_visualizer_v2 import HTMLVisualizerV2
from data.data_source import DataSource


@dataclass
class Modification:
    """Represents a single match modification."""
    match_id: str
    original_week: int
    original_time: str
    original_venue: str
    new_week: int
    new_time: str
    new_venue: str
    teams: str
    timestamp: str
    
    @classmethod
    def from_json(cls, match_id: str, data: dict) -> 'Modification':
        """Create Modification from JSON structure."""
        return cls(
            match_id=match_id,
            original_week=data['original']['week'],
            original_time=data['original']['time'],
            original_venue=data['original']['venue'],
            new_week=data['new']['week'],
            new_time=data['new']['time'],
            new_venue=data['new']['venue'],
            teams=data['teams'],
            timestamp=data['timestamp']
        )


class ModificationApplier:
    """Applies JSON modifications to Excel calendar."""
    
    def __init__(self, excel_file: str, config_file: str):
        """Initialize with Excel and config paths."""
        self.excel_file = Path(excel_file)
        self.config_file = Path(config_file)
        self.config = Config.from_yaml(str(config_file))
        
        # Load Excel data
        self.df_calendar = pd.read_excel(excel_file, sheet_name='Calendrier')
        self.df_non_planifies = pd.read_excel(excel_file, sheet_name='Non_Planifies')
        
        # Load available venues and time slots from config
        self.venues = self._load_venues()
        self.time_slots = self._load_time_slots()
        
        # Track validation results
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.applied: List[str] = []
    
    def _load_venues(self) -> Dict[str, Gymnase]:
        """Load venues from config."""
        venues = {}
        for venue_data in self.config.gymnases:
            venues[venue_data['nom']] = Gymnase(
                nom=venue_data['nom'],
                creneaux=[
                    Creneau(
                        semaine=c['semaine'],
                        horaire=c['horaire'],
                        duree_minutes=c.get('duree_minutes', 120)
                    )
                    for c in venue_data.get('creneaux', [])
                ]
            )
        return venues
    
    def _load_time_slots(self) -> List[str]:
        """Get list of valid time slots from config."""
        slots = set()
        for venue in self.venues.values():
            for creneau in venue.creneaux:
                slots.add(creneau.horaire)
        return sorted(list(slots))
    
    def load_modifications(self, json_file: str) -> List[Modification]:
        """Load modifications from JSON file."""
        json_path = Path(json_file)
        
        if not json_path.exists():
            raise FileNotFoundError(f"Modifications file not found: {json_file}")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        modifications = []
        for match_id, mod_data in data.items():
            modifications.append(Modification.from_json(match_id, mod_data))
        
        print(f"📥 Loaded {len(modifications)} modification(s) from {json_file}")
        return modifications
    
    def validate_modification(self, mod: Modification) -> Tuple[bool, List[str]]:
        """
        Validate a single modification.
        
        Returns:
            (is_valid, error_messages)
        """
        errors = []
        
        # Check if venue exists
        if mod.new_venue not in self.venues:
            errors.append(f"❌ Venue '{mod.new_venue}' not found in config")
            return False, errors
        
        # Check if time slot is valid
        if mod.new_time not in self.time_slots:
            errors.append(f"❌ Time slot '{mod.new_time}' not valid. Available: {', '.join(self.time_slots)}")
            return False, errors
        
        # Check if venue has the time slot at the specified week
        venue = self.venues[mod.new_venue]
        available_slot = None
        for creneau in venue.creneaux:
            if creneau.semaine == mod.new_week and creneau.horaire == mod.new_time:
                available_slot = creneau
                break
        
        if not available_slot:
            errors.append(
                f"❌ Venue '{mod.new_venue}' not available at week {mod.new_week}, {mod.new_time}"
            )
            return False, errors
        
        # Check for conflicts in the Excel calendar
        conflicts = self.df_calendar[
            (self.df_calendar['Semaine'] == mod.new_week) &
            (self.df_calendar['Horaire'] == mod.new_time) &
            (self.df_calendar['Gymnase'] == mod.new_venue) &
            (self.df_calendar['Match_ID'] != mod.match_id)
        ]
        
        if len(conflicts) > 0:
            conflict_match = conflicts.iloc[0]
            errors.append(
                f"⚠️  Conflict: Another match already scheduled at {mod.new_venue}, "
                f"week {mod.new_week}, {mod.new_time} "
                f"({conflict_match['Institution_1']} vs {conflict_match['Institution_2']})"
            )
            # This is a warning, not an error - user might want to swap
        
        # Check for team conflicts (same team playing twice at same time)
        # Extract team IDs from match_id (format: TEAM1_ID__TEAM2_ID__POOL)
        parts = mod.match_id.split('__')
        if len(parts) >= 2:
            team1_id = parts[0]
            team2_id = parts[1]
            
            # Check if either team is already playing at this time
            team_conflicts = self.df_calendar[
                (self.df_calendar['Semaine'] == mod.new_week) &
                (self.df_calendar['Horaire'] == mod.new_time) &
                (self.df_calendar['Match_ID'] != mod.match_id) &
                (
                    self.df_calendar['Match_ID'].str.contains(team1_id, regex=False) |
                    self.df_calendar['Match_ID'].str.contains(team2_id, regex=False)
                )
            ]
            
            if len(team_conflicts) > 0:
                errors.append(
                    f"❌ Team conflict: One of the teams is already playing at week {mod.new_week}, {mod.new_time}"
                )
                return False, errors
        
        return len([e for e in errors if e.startswith('❌')]) == 0, errors
    
    def apply_modification(self, mod: Modification) -> bool:
        """Apply a single modification to the DataFrame."""
        # Find the row with matching Match_ID
        mask = self.df_calendar['Match_ID'] == mod.match_id
        
        if not mask.any():
            self.errors.append(f"❌ Match not found in calendar: {mod.match_id}")
            return False
        
        # Validate first
        is_valid, validation_errors = self.validate_modification(mod)
        
        if not is_valid:
            self.errors.extend(validation_errors)
            return False
        
        # Apply the changes
        self.df_calendar.loc[mask, 'Semaine'] = mod.new_week
        self.df_calendar.loc[mask, 'Horaire'] = mod.new_time
        self.df_calendar.loc[mask, 'Gymnase'] = mod.new_venue
        
        # Add warnings if any
        warnings_only = [e for e in validation_errors if e.startswith('⚠️')]
        self.warnings.extend(warnings_only)
        
        self.applied.append(f"✅ {mod.teams}: Week {mod.original_week}→{mod.new_week}, "
                           f"{mod.original_time}→{mod.new_time}, "
                           f"{mod.original_venue}→{mod.new_venue}")
        return True
    
    def apply_all(self, modifications: List[Modification]) -> bool:
        """Apply all modifications."""
        print(f"\n🔍 Validating and applying {len(modifications)} modification(s)...\n")
        
        success_count = 0
        for i, mod in enumerate(modifications, 1):
            print(f"[{i}/{len(modifications)}] {mod.teams}...")
            if self.apply_modification(mod):
                success_count += 1
        
        print(f"\n📊 Results:")
        print(f"   ✅ Applied: {success_count}/{len(modifications)}")
        print(f"   ❌ Failed: {len(modifications) - success_count}")
        print(f"   ⚠️  Warnings: {len(self.warnings)}")
        
        return success_count > 0
    
    def save_excel(self, output_path: Optional[str] = None) -> str:
        """Save modified calendar to Excel."""
        if output_path is None:
            # Create backup and overwrite original
            backup_path = self.excel_file.parent / f"{self.excel_file.stem}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            self.excel_file.rename(backup_path)
            print(f"💾 Backup created: {backup_path}")
            output_path = str(self.excel_file)
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            self.df_calendar.to_excel(writer, sheet_name='Calendrier', index=False)
            self.df_non_planifies.to_excel(writer, sheet_name='Non_Planifies', index=False)
            
            # Add statistics sheet if it existed
            try:
                df_stats = pd.read_excel(self.excel_file, sheet_name='Statistiques')
                df_stats.to_excel(writer, sheet_name='Statistiques', index=False)
            except:
                pass
        
        print(f"💾 Modified calendar saved: {output_path}")
        return output_path
    
    def regenerate_html(self) -> Optional[str]:
        """Regenerate HTML visualization from modified Excel."""
        try:
            print(f"\n🌐 Regenerating HTML visualization...")
            
            # Load solution from Excel
            ds = DataSource(str(self.config_file))
            solution = ds.create_solution()
            
            html_path = str(self.excel_file).replace('.xlsx', '.html')
            HTMLVisualizerV2.generate(solution, html_path, self.config)
            
            print(f"✅ HTML regenerated: {html_path}")
            return html_path
        except Exception as e:
            print(f"⚠️  HTML regeneration failed: {e}")
            return None
    
    def print_summary(self):
        """Print summary of operations."""
        print("\n" + "="*60)
        print("MODIFICATION SUMMARY")
        print("="*60)
        
        if self.applied:
            print(f"\n✅ Successfully Applied ({len(self.applied)}):")
            for msg in self.applied:
                print(f"   {msg}")
        
        if self.warnings:
            print(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for msg in self.warnings:
                print(f"   {msg}")
        
        if self.errors:
            print(f"\n❌ Errors ({len(self.errors)}):")
            for msg in self.errors:
                print(f"   {msg}")
        
        print("\n" + "="*60)


def main():
    """Main entry point."""
    if len(sys.argv) < 4:
        print(__doc__)
        return 1
    
    excel_file = sys.argv[1]
    json_file = sys.argv[2]
    config_file = sys.argv[3]
    no_html = '--no-html' in sys.argv
    
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
        # Initialize applier
        print(f"📊 Loading calendar from: {excel_file}")
        applier = ModificationApplier(excel_file, config_file)
        
        # Load modifications
        modifications = applier.load_modifications(json_file)
        
        if not modifications:
            print("ℹ️  No modifications to apply")
            return 0
        
        # Apply modifications
        if applier.apply_all(modifications):
            # Save Excel
            applier.save_excel()
            
            # Regenerate HTML (unless disabled)
            if not no_html:
                applier.regenerate_html()
            
            # Print summary
            applier.print_summary()
            
            print("\n✅ Modifications applied successfully!")
            return 0
        else:
            applier.print_summary()
            print("\n❌ No modifications were applied due to errors")
            return 1
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
