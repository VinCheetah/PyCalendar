#!/usr/bin/env python3
"""
Validation de la structure de l'interface PyCalendar
Vérifie que tous les fichiers essentiels sont présents
"""

import json
from pathlib import Path
from typing import List, Tuple

# Définir la structure attendue
EXPECTED_STRUCTURE = {
    'core': [
        '__init__.py',
        'data_formatter.py',
        'generator.py',
    ],
    'assets/styles': [
        'manifest.json',
    ],
    'assets/styles/core': [
        '00-tokens.css',
        '01-reset.css',
        '02-base.css',
        '03-layout.css',
        '04-effects.css',
        '05-decorations.css',
    ],
    'assets/styles/components': [
        'filters.css',
        'loading.css',
        'match-card.css',
        'modals.css',
        'tabs.css',
        'view-options.css',
        'views.css',
    ],
    'assets/styles/views': [
        'agenda-view.css',
        'pools-view.css',
        'penalties-view.css',
    ],
    'assets/styles/themes': [
        'palettes.css',
        'default.css',
        'dark.css',
        'tricolore.css',
    ],
    'scripts/core': [
        '__init__.py',
        'data-manager.js',
    ],
    'scripts/data': [
        '__init__.py',
        'modification-manager.js',
    ],
    'scripts/app': [
        'modals.js',
        'ui-controls.js',
    ],
    'scripts/utils': [
        '__init__.py',
        'formatters.js',
        'validators.js',
    ],
    'scripts/views': [
        '__init__.py',
        'agenda/agenda-view.js',
        'agenda-grid.js',
        'pools-view.js',
        'teams-view.js',
        'matches-view.js',
        'penalties-view.js',
    ],
    'templates': [
        'index.html',
    ],
    'data/schemas': [
        'solution_schema.json',
        'modification_schema.json',
    ],
}

def validate_structure() -> Tuple[List[str], List[str]]:
    """
    Valide que tous les fichiers attendus sont présents.
    
    Returns:
        Tuple (fichiers_présents, fichiers_manquants)
    """
    interface_dir = Path(__file__).parent
    present = []
    missing = []
    
    for directory, files in EXPECTED_STRUCTURE.items():
        dir_path = interface_dir / directory
        
        for file in files:
            file_path = dir_path / file
            
            if file_path.exists():
                present.append(f"{directory}/{file}")
            else:
                missing.append(f"{directory}/{file}")
    
    missing.extend(_validate_css_manifest(interface_dir))
    
    return present, missing


def _validate_css_manifest(interface_dir: Path) -> List[str]:
    """Ensure manifest.json exists and references valid CSS files."""
    missing: List[str] = []
    manifest_path = interface_dir / 'assets' / 'styles' / 'manifest.json'

    if not manifest_path.exists():
        missing.append('assets/styles/manifest.json')
        return missing

    try:
        with open(manifest_path, 'r', encoding='utf-8') as manifest_file:
            manifest = json.load(manifest_file)
    except json.JSONDecodeError:
        missing.append('assets/styles/manifest.json (invalid JSON)')
        return missing

    if not isinstance(manifest, list):
        missing.append('assets/styles/manifest.json (expected list of sections)')
        return missing

    styles_root = manifest_path.parent

    for section in manifest:
        files = section.get('files', []) if isinstance(section, dict) else []
        for entry in files:
            if not isinstance(entry, str) or not entry.strip():
                continue
            entry = entry.strip()
            has_glob = any(char in entry for char in ['*', '?', '['])

            if has_glob:
                matches = list(styles_root.glob(entry))
                if not matches:
                    missing.append(f'styles/{entry} (no match)')
            else:
                css_path = styles_root / entry
                if not css_path.exists():
                    missing.append(str(css_path.relative_to(interface_dir)))

    return missing

def main():
    print("🔍 Validation de la structure de l'interface PyCalendar\n")
    
    present, missing = validate_structure()
    
    print(f"✅ Fichiers présents: {len(present)}")
    print(f"❌ Fichiers manquants: {len(missing)}\n")
    
    if missing:
        print("⚠️  Fichiers manquants:")
        for file in missing:
            print(f"   - {file}")
        print()
        return 1
    
    print("✅ Tous les fichiers essentiels sont présents!")
    
    # Calculer la taille totale
    interface_dir = Path(__file__).parent
    total_size = 0
    file_count = 0
    
    for ext in ['*.py', '*.js', '*.css', '*.html', '*.json']:
        for file in interface_dir.rglob(ext):
            if '__pycache__' not in str(file):
                total_size += file.stat().st_size
                file_count += 1
    
    print(f"\n📊 Statistiques:")
    print(f"   Fichiers: {file_count}")
    print(f"   Taille totale: {total_size / 1024:.1f} KB")
    
    # Compter les lignes de code
    total_lines = 0
    for ext in ['*.py', '*.js', '*.css', '*.html']:
        for file in interface_dir.rglob(ext):
            if '__pycache__' not in str(file):
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        total_lines += len(f.readlines())
                except:
                    pass
    
    print(f"   Lignes de code: ~{total_lines}")
    
    return 0

if __name__ == '__main__':
    exit(main())
