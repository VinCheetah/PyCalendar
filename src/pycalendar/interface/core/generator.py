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
        solution_name: str = "solution"
    ) -> str:
        """
        Generate complete HTML interface.
        
        Args:
            solution: Solution object, Path to JSON file, or dict with solution data (v2.0 format)
            output_path: Path where to save HTML file
            config: Configuration object (optional)
            solution_name: Name of the solution (for modifications tracking)
            
        Returns:
            Absolute path to generated HTML file
        """
        print("\n🎨 Generating PyCalendar Interface...")
        
        # Step 1: Format solution data
        print("  📊 Formatting solution data...")
        
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
            solution_data = DataFormatter.format_solution(solution, config)
            
        else:
            raise TypeError(f"Invalid solution type: {type(solution)}")
        
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
            
            # Component styles
            'styles/components/match-card.css',
            'styles/components/filters.css',
            'styles/components/modals.css',
            'styles/components/loading.css',
            'styles/components/tabs.css',
            'styles/components/views.css',
            
            # View styles
            'styles/views/agenda-grid.css',
            
            # Theme (last)
            'styles/themes/default-light.css',
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
            
            # Features
            'features/drag-drop-manager.js',  # Drag & drop des matchs
            
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
            'views/pools/pools-view.js',
            'views/cards/cards-view.js',
            
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

// Initialize application when DOM is ready
document.addEventListener('DOMContentLoaded', function() {{
    console.log('🚀 PyCalendar Interface loaded');
    
    // Load solution data
    const solutionDataElement = document.getElementById('solution-data');
    if (!solutionDataElement) {{
        console.error('❌ Solution data not found');
        return;
    }}
    
    let solutionData;
    try {{
        solutionData = JSON.parse(solutionDataElement.textContent);
        console.log('✅ Solution data loaded:', {{
            version: solutionData.version,
            matches: solutionData.matches.scheduled.length
        }});
    }} catch (error) {{
        console.error('❌ Error parsing solution data:', error);
        return;
    }}
    
    // Initialize managers
    try {{
        window.dataManager = new DataManager(solutionData);
        window.modificationManager = new ModificationManager(SOLUTION_NAME);
        
        console.log('✅ Managers initialized');
        
        // Initialize views and populate filters
        if (typeof initializeViews === 'function') {{
            initializeViews();
            console.log('✅ Views initialized');
        }}
        
        if (typeof populateFilters === 'function') {{
            populateFilters();
            console.log('✅ Filters populated');
        }}
        
    }} catch (error) {{
        console.error('❌ Error initializing application:', error);
    }}
}});
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
