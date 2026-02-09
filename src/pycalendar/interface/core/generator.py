"""
Interface Generator - Assembles complete HTML interface with all components.

This module generates a single, self-contained HTML file with embedded:
- CSS styles (from modular files)
- JavaScript code (from modular files)
- Solution data (as JSON)
- Template structure
"""

from pathlib import Path
from typing import Optional, List, Union, Dict
import json

from pycalendar.core.models import Solution
from pycalendar.core.config import Config
from .data_formatter import DataFormatter


class InterfaceGenerator:
    """Generates complete HTML interface from solution data."""
    
    def __init__(self):
        self.interface_dir = Path(__file__).parent.parent
        self.assets_dir = self.interface_dir / 'assets'
        self.scripts_dir = self.interface_dir / 'scripts'
        self.templates_dir = self.interface_dir / 'templates'
    
    def generate(
        self,
        solution: Union[Solution, Path, str, Dict],
        output_path: str,
        config: Optional[Config] = None,
        solution_name: str = "solution",
        types_poules: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Generate complete HTML interface.
        
        Args:
            solution: Solution object, Path to JSON file, or dict with solution data (v2.0 format)
            output_path: Path where to save HTML file
            config: Configuration object (optional)
            solution_name: Name of the solution (for modifications tracking)
            types_poules: Dictionary {poule_name: type} where type is 'Classique' or 'Aller-Retour' (optional)
            
        Returns:
            Absolute path to generated HTML file
        """
        print("\n🎨 Generating PyCalendar Interface...")
        
        # Step 1: Format solution data
        print("  📊 Formatting solution data...")
        
        solution_data = {} # Default to empty dict
        
        # Handle different input types
        if isinstance(solution, (Path, str)):
            # Load JSON file (v2.0 format)
            solution_path = Path(solution)
            with open(solution_path, 'r', encoding='utf-8') as f:
                solution_data = json.load(f)
            
            # Validate it's v2.0 format
            if solution_data.get('version') != '2.0':
                raise ValueError(f"Solution file must be in v2.0 format (found: {solution_data.get('version')})")
            
            print(f"     Loaded v2.0 solution from: {solution_path.name}")
            
            # Enrich penalties with per-team breakdown if config available
            if config:
                solution_data = self._enrich_penalties(solution_data, config)
            
        elif isinstance(solution, dict):
            # Direct dict (already v2.0 format)
            if solution.get('version') != '2.0':
                raise ValueError(f"Solution dict must be in v2.0 format (found: {solution.get('version')})")
            solution_data = solution
            
            # Enrich penalties with per-team breakdown if config available
            if config:
                solution_data = self._enrich_penalties(solution_data, config)
            
        elif isinstance(solution, Solution):
            # Legacy Solution object - format it
            solution_data = DataFormatter.format_solution(solution, config, types_poules=types_poules)
            
        else:
            raise TypeError(f"Invalid solution type: {type(solution)}")

        # Validate that we have data before proceeding
        if not solution_data:
            print("  ⚠️  Warning: Solution data is empty. Proceeding with an empty dataset.")
            solution_data = {}
        
        # Enrich solution data with calendar config if available and missing
        if config and 'config' in solution_data:
            if 'calendrier' not in solution_data['config']:
                solution_data['config']['calendrier'] = {
                    'date_debut': getattr(config, 'calendrier_date_debut', '2025-10-13'),
                    'jour_match': getattr(config, 'calendrier_jour_match', 'jeudi'),
                    'semaines_banalisees': getattr(config, 'calendrier_semaines_banalisees', []),
                }
                print(f"     Enriched solution with calendar config: date_debut={solution_data['config']['calendrier']['date_debut']}")
        
        # Step 2: Load HTML template
        print("  📄 Loading HTML template...")
        template = self._load_template()
        
        # Step 3: Load and combine CSS
        print("  🎨 Loading CSS modules...")
        css_content = self._load_all_css()
        
        # Step 4: Load and combine JavaScript
        print("  📜 Loading JavaScript modules...")
        js_content = self._load_all_js()
        
        # Step 5: Inject everything into template
        print("  🔧 Assembling final HTML...")
        html = self._assemble_html(template, css_content, js_content, solution_data, solution_name)
        
        # Step 6: Write output file
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"  ✅ Interface generated: {output_file.absolute()}")
        print(f"  📦 File size: {len(html) / 1024:.1f} KB")
        
        return str(output_file.absolute())
    
    def _enrich_penalties(self, solution_data: Dict, config: Config) -> Dict:
        """
        Enrich penalty data with per-team breakdown.
        
        When loading a v2.0 JSON solution, the penalties may not include
        per-team breakdown (equipe1/equipe2 keys). This method recalculates
        penalties with the detailed breakdown.
        
        Args:
            solution_data: The solution data dict (v2.0 format)
            config: Configuration object for penalty calculation
            
        Returns:
            Updated solution_data with enriched penalties
        """
        from pycalendar.core.penalty_calculator import PenaltyCalculator
        from pycalendar.core.models import Match, Equipe, Creneau
        
        # Check if enrichment is needed (first match doesn't have equipe1/equipe2 in penalties)
        # Note: v2.0 format uses 'matches' key (English) not 'matchs' (French)
        scheduled = solution_data.get('matches', {}).get('scheduled', [])
        if not scheduled:
            # Fallback to 'matchs' for compatibility
            scheduled = solution_data.get('matchs', {}).get('scheduled', [])
        if not scheduled:
            return solution_data
            
        first_penalties = scheduled[0].get('penalties', {})
        if 'equipe1' in first_penalties and 'equipe2' in first_penalties:
            # Already enriched
            return solution_data
            
        print("     Enriching penalties with per-team breakdown...")
        
        # Get metadata for niveaux_gymnases
        metadata = solution_data.get('metadata', {})
        niveaux_gymnases = metadata.get('niveaux_gymnases', {})
        priorites_genre = metadata.get('priorites_genre_gymnases', {})
        
        # Build list of matches for context
        all_match_data = scheduled  # Use raw match data
        
        # Process each scheduled match
        for i, match_data in enumerate(scheduled):
            if 'penalties' not in match_data:
                continue
                
            # Create mock Match object for penalty calculation
            try:
                equipe1 = Equipe(
                    nom=match_data.get('equipe1_nom', 'Unknown'),
                    institution=match_data.get('equipe1_institution', ''),
                    poule=match_data.get('poule', ''),
                    genre=match_data.get('equipe1_genre', ''),
                    horaires_preferes=match_data.get('equipe1_horaires_preferes', []),
                    lieux_preferes=match_data.get('equipe1_lieux_preferes', []),
                )
                
                equipe2 = Equipe(
                    nom=match_data.get('equipe2_nom', 'Unknown'),
                    institution=match_data.get('equipe2_institution', ''),
                    poule=match_data.get('poule', ''),
                    genre=match_data.get('equipe2_genre', ''),
                    horaires_preferes=match_data.get('equipe2_horaires_preferes', []),
                    lieux_preferes=match_data.get('equipe2_lieux_preferes', []),
                )
                
                creneau = Creneau(
                    semaine=match_data.get('semaine', 1),
                    horaire=match_data.get('horaire', '14:00'),
                    gymnase=match_data.get('gymnase', ''),
                )
                
                mock_match = Match(
                    equipe1=equipe1,
                    equipe2=equipe2,
                    poule=match_data.get('poule', ''),
                    creneau=creneau,
                )
                
                # Create calculator with single match (simplified)
                calculator = PenaltyCalculator(
                    config,
                    [mock_match],
                    niveaux_gymnases=niveaux_gymnases,
                    priorites_genre_gymnases=priorites_genre,
                )
                
                # Get detailed penalties
                detailed = calculator.calculate_match_penalties_detailed(mock_match)
                
                # Update penalties with per-team breakdown
                if 'equipe1' in detailed:
                    match_data['penalties']['equipe1'] = detailed['equipe1']
                if 'equipe2' in detailed:
                    match_data['penalties']['equipe2'] = detailed['equipe2']
                    
            except Exception as e:
                # Skip this match if there's an error
                print(f"     ⚠️  Could not enrich penalties for match {i}: {e}")
                continue
        
        return solution_data
    
    def _load_template(self) -> str:
        """Load main HTML template."""
        template_path = self.templates_dir / 'index.html'
        
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _load_all_css(self) -> str:
        """Load and combine all CSS modules in correct order."""
        manifest_path = self.assets_dir / 'styles' / 'manifest.json'
        if not manifest_path.exists():
            raise FileNotFoundError("CSS manifest missing. Create 'assets/styles/manifest.json' to declare styles order.")

        css_files = self._load_css_from_manifest(manifest_path)
        if not css_files:
            raise ValueError("CSS manifest produced no CSS files. Ensure sections declare at least one file.")

        combined_css = []
        
        for css_file in css_files:
            css_path = self.assets_dir / css_file
            
            if css_path.exists():
                with open(css_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    combined_css.append(f"/* {css_file} */\n{content}\n")
            else:
                print(f"  ⚠️  CSS file not found: {css_file}")
        
        return '\n'.join(combined_css)

    def _load_css_from_manifest(self, manifest_path: Path) -> List[str]:
        """Resolve CSS file order from manifest.json (supports glob patterns)."""
        with open(manifest_path, 'r', encoding='utf-8') as manifest_file:
            manifest = json.load(manifest_file)

        if not isinstance(manifest, list):
            raise ValueError("CSS manifest must be a list of sections")

        styles_root = self.assets_dir / 'styles'
        seen = set()
        ordered_files: List[str] = []

        for section in manifest:
            files = section.get('files', []) if isinstance(section, dict) else []
            for entry in files:
                for rel_path in self._resolve_manifest_entry(entry, styles_root):
                    if rel_path not in seen:
                        seen.add(rel_path)
                        ordered_files.append(rel_path)

        return ordered_files

    def _resolve_manifest_entry(self, entry: str, styles_root: Path) -> List[str]:
        """Return resolved asset-relative paths for a manifest entry (supports globs)."""
        if not entry or not isinstance(entry, str):
            return []

        entry = entry.strip()
        has_glob = any(char in entry for char in ['*', '?', '['])

        if has_glob:
            matches = sorted(styles_root.glob(entry))
            return [match.relative_to(self.assets_dir).as_posix() for match in matches if match.is_file()]
        
        return [(Path('styles') / entry).as_posix()]

    
    def _load_all_js(self) -> str:
        """Load and combine all JavaScript modules in correct order."""
        js_files = [
            # Utilities (loaded first, no dependencies)
            'utils/sport-utils.js',  # Utilitaires sport (doit être chargé en premier)
            'utils/formatters.js',
            'utils/validators.js',
            'utils/slot-manager.js',
            'utils/scroll-sync.js',
            'utils/match-card-renderer.js',
            'utils/agenda-view-manager.js',  # Gestionnaire des vues (gymnase/semaine)
            'utils/available-slots-manager.js',  # Gestion des créneaux disponibles
            
            # Managers
            'managers/view-options-manager.js',
            
            # Features
            'features/drag-drop-manager.js',  # Drag & drop des matchs
            'features/enhanced-filter-system.js',  # Système de filtres amélioré
            'features/horaire-timeline.js',  # Extension timeline horaire interactive
            
            # Core modules (order matters!)
            'core/data-manager.js',
            
            # Data layer
            'data/modification-manager.js',
            
            # Components (depend on core & utils)
            'components/ui/match-card.js',
            'components/edit/edit-modal.js',
            'app/modals.js',
            'app/ui-controls.js',
            
            # Views (depend on everything else)
            'views/agenda-grid.js',
            'views/agenda/agenda-view.js',
            'views/pools-view.js',
            'views/teams-view.js',
            'views/matches-view.js',
            'views/penalties-view.js',
            
            # Application initialization (loaded last)
            'app.js',
        ]
        
        combined_js = []
        
        for js_file in js_files:
            js_path = self.scripts_dir / js_file
            
            if js_path.exists():
                with open(js_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    combined_js.append(f"// {js_file}\n{content}\n")
            else:
                print(f"  ⚠️  JavaScript file not found: {js_file}")
        
        return '\n'.join(combined_js)
    
    def _sanitize_json_data(self, data):
        """
        Nettoie les données pour assurer un JSON valide.
        Remplace inf, -inf et NaN par des valeurs JSON valides.
        """
        import math
        
        if isinstance(data, dict):
            return {k: self._sanitize_json_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_json_data(item) for item in data]
        elif isinstance(data, float):
            if math.isinf(data):
                return 999999999 if data > 0 else -999999999  # Grande valeur au lieu de inf
            elif math.isnan(data):
                return None
        return data
    
    def _assemble_html(
        self,
        template: str,
        css: str,
        js: str,
        solution_data: dict,
        solution_name: str
    ) -> str:
        """Assemble final HTML with all components."""
        
        # Inject CSS
        css_block = f'<style>\n{css}\n</style>'
        html = template.replace('<!-- CSS_PLACEHOLDER -->', css_block)
        
        # Sanitize data to ensure valid JSON (replace inf, nan, etc.)
        solution_data = self._sanitize_json_data(solution_data)
        
        # Inject solution data as JSON
        solution_json = json.dumps(solution_data, ensure_ascii=False, indent=2)
        data_script = f'''
<script id="solution-data" type="application/json">
{solution_json}
</script>
'''
        html = html.replace('<!-- DATA_PLACEHOLDER -->', data_script)
        
        # Inject JavaScript
        js_block = f'''
<script>
// Solution name for modification tracking
const SOLUTION_NAME = "{solution_name}";

{js}
</script>
'''
        html = html.replace('<!-- JS_PLACEHOLDER -->', js_block)
        
        return html


def generate_interface(
    solution: Solution,
    output_path: str,
    config: Optional[Config] = None,
    solution_name: str = "solution"
) -> str:
    """
    Convenience function to generate interface.
    
    Args:
        solution: Solution to visualize
        output_path: Where to save HTML
        config: Optional configuration
        solution_name: Name for modification tracking
        
    Returns:
        Path to generated HTML file
    """
    generator = InterfaceGenerator()
    return generator.generate(solution, output_path, config, solution_name)
