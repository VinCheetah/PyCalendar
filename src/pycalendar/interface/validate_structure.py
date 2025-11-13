#!/usr/bin/env python3
"""
Validation de la structure de l'interface PyCalendar
Vérifie que tous les fichiers essentiels sont présents
"""

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
        '00-variables.css',
        '01-reset.css',
        '02-base.css',
        '03-layout.css',
    ],
    'assets/styles/components': [
        'match-card.css',
        'filters.css',
        'modals.css',
        'loading.css',
        'tabs.css',
        'views.css',
    ],
    'assets/styles/themes': [
        'default-light.css',
    ],
    'scripts/core': [
        '__init__.py',
        'data-manager.js',
    ],
    'scripts/data': [
        '__init__.py',
        'modification-manager.js',
    ],
    'scripts/utils': [
        '__init__.py',
        'formatters.js',
        'validators.js',
    ],
    'scripts/views': [
        '__init__.py',
        'agenda-view.js',
        'pools-view.js',
        'teams-view.js',
        'cards-view.js',
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
    
    return present, missing

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
