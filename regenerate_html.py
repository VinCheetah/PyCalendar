"""
PyCalendar - HTML Regeneration Script
Regenerate HTML visualization from saved solution
"""

import sys
import json
from pathlib import Path
from core.config import Config
from core.models import Solution, Match, Equipe, Creneau
from data.data_source import DataSource
from data.transformers import DataTransformer
from visualization.html_visualizer_v2 import HTMLVisualizerV2


def main():
    """Regenerate HTML from saved solution."""
    
    print("\n" + "="*70)
    print("HTML CALENDAR REGENERATION".center(70))
    print("="*70 + "\n")
    
    # Parse arguments with defaults
    excel_file = sys.argv[1] if len(sys.argv) > 1 else "data_volley/config_volley.xlsx"
    config_file = sys.argv[2] if len(sys.argv) > 2 else "configs/config_volley.yaml"
    solution_file = sys.argv[3] if len(sys.argv) > 3 else "solutions/latest_volley.json"
    
    # Validate files exist
    for file_path, file_type in [(excel_file, "Excel"), (config_file, "Config"), (solution_file, "Solution")]:
        if not Path(file_path).exists():
            print(f"ERROR: {file_type} file not found: {file_path}")
            return 1
    
    try:
        # Load configuration
        print(f"Loading configuration from {config_file}...")
        config = Config.from_yaml(config_file)
        print("  Config loaded\n")
        
        # Load solution data
        print(f"Loading solution from {solution_file}...")
        with open(solution_file, 'r', encoding='utf-8') as f:
            solution_data = json.load(f)
        
        metadata = solution_data.get('metadata', {})
        print(f"  Solution date: {metadata.get('date', 'Unknown')}")
        print(f"  Solver: {metadata.get('solver', 'Unknown')}")
        print(f"  Score: {metadata.get('score', 0)}")
        print(f"  Scheduled matches: {metadata.get('matchs_planifies', 0)}\n")
        
        # Load teams
        print("Loading teams...")
        data_source = DataSource(excel_file)
        all_equipes = data_source.charger_equipes()
        
        # Build team index for lookup
        equipes_index = {}
        for eq in all_equipes:
            equipes_index[f"{eq.nom_complet}|{eq.genre}"] = eq
            equipes_index[f"{eq.nom}|{eq.genre}"] = eq
            equipes_index[f"{eq.nom_complet}|{eq.genre.lower()}"] = eq
            equipes_index[f"{eq.nom}|{eq.genre.lower()}"] = eq
        
        print(f"  {len(all_equipes)} teams indexed\n")
        
        # Reconstruct matches
        print("Reconstructing matches...")
        matchs_planifies = []
        teams_not_found = set()
        
        for assign in solution_data['assignments']:
            # Find teams in index
            key1 = f"{assign['equipe1_nom']}|{assign['equipe1_genre']}"
            key2 = f"{assign['equipe2_nom']}|{assign['equipe2_genre']}"
            
            eq1 = equipes_index.get(key1)
            eq2 = equipes_index.get(key2)
            
            # Create temporary teams if not found
            if not eq1:
                eq1 = Equipe(
                    nom=assign['equipe1_nom'],
                    poule="UNKNOWN",
                    institution="UNKNOWN",
                    genre=assign['equipe1_genre'].upper()
                )
                teams_not_found.add(key1)
            
            if not eq2:
                eq2 = Equipe(
                    nom=assign['equipe2_nom'],
                    poule="UNKNOWN",
                    institution="UNKNOWN",
                    genre=assign['equipe2_genre'].upper()
                )
                teams_not_found.add(key2)
            
            # Create match
            creneau = Creneau(
                semaine=assign['semaine'],
                horaire=assign['horaire'],
                gymnase=assign['gymnase']
            )
            
            match = Match(
                equipe1=eq1,
                equipe2=eq2,
                poule=eq1.poule if eq1.poule != "UNKNOWN" else eq2.poule,
                creneau=creneau,
                metadata={
                    'match_id': assign['match_id'],
                    'fixe': assign.get('is_fixed', False)
                }
            )
            matchs_planifies.append(match)
        
        if teams_not_found:
            print(f"  Warning: {len(teams_not_found)} team(s) not in current config")
            print(f"  (Normal if solution was generated with different teams)\n")
        
        print(f"  {len(matchs_planifies)} matches reconstructed\n")
        
        # Generate all time slots
        print("Generating time slots...")
        gymnases = data_source.charger_gymnases()
        tous_creneaux = DataTransformer.generer_creneaux(
            gymnases,
            config.nb_semaines,
            config.calendar_manager
        )
        print(f"  {len(tous_creneaux)} slots generated\n")
        
        # Create solution object
        solution = Solution(
            matchs_planifies=matchs_planifies,
            matchs_non_planifies=[],
            score=metadata.get('score', 0.0),
            metadata=metadata
        )
        solution.metadata['creneaux_disponibles'] = tous_creneaux
        
        # Generate HTML
        output_file = excel_file.replace('.xlsx', '.html')
        output_file = output_file.replace('config_', 'calendrier_')
        
        print(f"Generating HTML: {output_file}...")
        HTMLVisualizerV2.generate(solution, output_file, config)
        
        print(f"\n{'='*70}")
        print("SUCCESS".center(70))
        print(f"{'='*70}\n")
        print(f"File: {Path(output_file).absolute()}\n")
        
        return 0
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
