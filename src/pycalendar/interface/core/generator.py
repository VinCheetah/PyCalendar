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
            
        elif isinstance(solution, dict):
            # Direct dict (already v2.0 format)
            if solution.get('version') != '2.0':
                raise ValueError(f"Solution dict must be in v2.0 format (found: {solution.get('version')})")
            solution_data = solution
            
        elif isinstance(solution, Solution):
            # Legacy Solution object - format it
            solution_data = DataFormatter.format_solution(solution, config, types_poules=types_poules)
            
        else:
            raise TypeError(f"Invalid solution type: {type(solution)}")

        # Validate that we have data before proceeding
        if not solution_data:
            print("  ⚠️  Warning: Solution data is empty. Proceeding with an empty dataset.")
            solution_data = {}
        
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
    
    def _load_template(self) -> str:
        """Load main HTML template."""
        template_path = self.templates_dir / 'index.html'
        
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _load_all_css(self) -> str:
        """Load and combine all CSS modules in correct order."""
        css_files = [
            # Base styles (order matters!)
            'styles/00-variables.css',
            'styles/01-reset.css',
            'styles/02-base.css',
            'styles/03-layout.css',
            'styles/04-enhancements.css',  # Visual enhancements & animations
            'styles/05-backgrounds-france.css',  # Theme decorations
            
            # Component styles
            'styles/components/match-card.css',
            'styles/components/filters.css',
            'styles/components/modals.css',
            'styles/components/loading.css',
            'styles/components/tabs.css',
            'styles/components/views.css',
            'styles/components/view-options.css',
            
            # View styles
            'styles/views/agenda-view.css',
            'styles/views/pools-view.css',
            'styles/views/penalties-view.css',  # Vue Pénalités
            
            # Themes (last)
            'styles/themes/default-light.css',
            'styles/themes/dark.css',
        ]
        
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
    
    def _load_all_js(self) -> str:
        """Load and combine all JavaScript modules in correct order."""
        js_files = [
            # Utilities (loaded first, no dependencies)
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
            
            # Core modules (order matters!)
            'core/data-manager.js',
            
            # Data layer
            'data/modification-manager.js',
            
            # Components (depend on core & utils)
            'components/ui/match-card.js',
            'components/filters/filter-panel.js',
            'components/edit/edit-modal.js',
            
            # Views (depend on everything else)
            'views/agenda-grid.js',
            'views/agenda/agenda-view.js',
            'views/pools-view.js',
            'views/teams-view.js',
            'views/matches-view.js',
            'views/penalties-view.js',  # Vue Pénalités
            
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
