#!/usr/bin/env python3
"""
PyCalendar Pool Manager - Interface Generator

Génère une interface HTML autonome pour la gestion des poules,
avec les données pré-chargées depuis une solution PyCalendar.

Usage:
    python generate_pool_manager.py [solution_file] [-o output_file]
    
Exemple:
    python generate_pool_manager.py solutions/latest_volley.json -o pool_manager.html
"""

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime


def read_file(path: Path) -> str:
    """Lire le contenu d'un fichier."""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def find_latest_solution(solutions_dir: Path, sport: str = 'volley') -> Path:
    """Trouver la dernière solution pour un sport."""
    latest_file = solutions_dir / f'latest_{sport}.json'
    if latest_file.exists():
        return latest_file
    
    # Chercher par date
    pattern = f'solution_{sport}_*.json'
    files = sorted(solutions_dir.glob(pattern), reverse=True)
    if files:
        return files[0]
    
    return None


def load_solution(solution_path: Path) -> dict:
    """Charger une solution PyCalendar."""
    with open(solution_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_embedded_data(solution_data: dict) -> str:
    """Générer le JavaScript pour les données embarquées."""
    # Minimiser les données pour l'embarquement
    minimal_data = {
        'version': solution_data.get('version', '2.0'),
        'generated_at': solution_data.get('generated_at', datetime.now().isoformat()),
        'metadata': solution_data.get('metadata', {}),
        'sport': solution_data.get('sport', {
            'type': 'volleyball',
            'prefix': 'VB',
            'name': 'Volleyball',
            'emoji': '🏐'
        }),
        'config': solution_data.get('config', {}),
        'entities': solution_data.get('entities', {}),
        'schedule': solution_data.get('schedule', [])
    }
    
    return f"""
// Données pré-chargées depuis la solution PyCalendar
const EMBEDDED_SOLUTION_DATA = {json.dumps(minimal_data, ensure_ascii=False, indent=2)};

// Charger automatiquement les données au démarrage
document.addEventListener('DOMContentLoaded', function() {{
    setTimeout(function() {{
        if (typeof dataManager !== 'undefined') {{
            try {{
                dataManager.loadFromSolution(EMBEDDED_SOLUTION_DATA);
                console.log('✅ Données pré-chargées depuis la solution');
            }} catch (error) {{
                console.error('Erreur lors du chargement des données:', error);
            }}
        }}
    }}, 100);
}});
"""


def assemble_interface(base_dir: Path, solution_data: dict = None) -> str:
    """Assembler l'interface HTML complète."""
    
    # Lire les fichiers de base
    html_template = read_file(base_dir / 'index.html')
    
    # Lire les CSS
    css_files = ['main.css', 'components.css', 'animations.css']
    css_content = '\n'.join([
        f'/* === {f} === */\n' + read_file(base_dir / 'css' / f)
        for f in css_files
    ])
    
    # Lire les JS
    js_files = [
        'utils.js', 'data-manager.js', 'drag-drop.js', 
        'pool-renderer.js', 'team-editor.js', 'pool-editor.js',
        'auto-grouping.js', 'history.js', 'app.js'
    ]
    js_content = '\n'.join([
        f'// === {f} ===\n' + read_file(base_dir / 'js' / f)
        for f in js_files
    ])
    
    # Ajouter les données embarquées si fournies
    if solution_data:
        js_content = generate_embedded_data(solution_data) + '\n\n' + js_content
    
    # Remplacer les liens CSS par du CSS inline
    css_block = f'<style>\n{css_content}\n</style>'
    html_template = html_template.replace(
        '<link rel="stylesheet" href="css/main.css">',
        css_block
    )
    html_template = html_template.replace('<link rel="stylesheet" href="css/components.css">', '')
    html_template = html_template.replace('<link rel="stylesheet" href="css/animations.css">', '')
    
    # Remplacer les scripts par du JS inline
    js_block = f'<script>\n{js_content}\n</script>'
    
    # Retirer les liens scripts existants
    for js_file in js_files:
        html_template = html_template.replace(f'<script src="js/{js_file}"></script>', '')
    
    # Ajouter le JS avant </body>
    html_template = html_template.replace('</body>', f'{js_block}\n</body>')
    
    return html_template


def main():
    parser = argparse.ArgumentParser(
        description='Génère une interface de gestion des poules PyCalendar'
    )
    parser.add_argument(
        'solution',
        nargs='?',
        help='Fichier solution PyCalendar (JSON)'
    )
    parser.add_argument(
        '-o', '--output',
        default='pool_manager.html',
        help='Fichier de sortie (défaut: pool_manager.html)'
    )
    parser.add_argument(
        '--sport',
        default='volley',
        choices=['volley', 'basket', 'hand'],
        help='Sport à utiliser pour trouver la solution (défaut: volley)'
    )
    parser.add_argument(
        '--no-data',
        action='store_true',
        help='Générer l\'interface sans données pré-chargées'
    )
    
    args = parser.parse_args()
    
    # Déterminer les chemins
    script_dir = Path(__file__).parent.resolve()
    project_root = script_dir.parent  # scripts/ -> PyCalendar/
    base_dir = project_root / 'tools' / 'pool_manager'
    solutions_dir = project_root / 'solutions'
    
    # Vérifier que le répertoire de base existe
    if not base_dir.exists():
        print(f'❌ Répertoire interface non trouvé: {base_dir}')
        return 1
    
    # Trouver la solution
    solution_data = None
    if not args.no_data:
        if args.solution:
            solution_path = Path(args.solution)
            if not solution_path.is_absolute():
                solution_path = project_root / solution_path
        else:
            solution_path = find_latest_solution(solutions_dir, args.sport)
        
        if solution_path and solution_path.exists():
            print(f'📂 Chargement de la solution: {solution_path.name}')
            solution_data = load_solution(solution_path)
        else:
            print('⚠️  Aucune solution trouvée, génération sans données')
    
    # Générer l'interface
    print('🔧 Assemblage de l\'interface...')
    html_content = assemble_interface(base_dir, solution_data)
    
    # Déterminer le chemin de sortie
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = project_root / output_path
    
    # Écrire le fichier
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    file_size = output_path.stat().st_size / 1024
    
    print(f'✅ Interface générée: {output_path}')
    print(f'📦 Taille: {file_size:.1f} KB')
    
    if solution_data:
        teams = solution_data.get('entities', {}).get('equipes', [])
        # Count pools from team assignments (more accurate than schedule)
        pools_from_teams = set(t.get('poule') for t in teams if t.get('poule'))
        pools_from_schedule = solution_data.get('schedule', [])
        pool_count = len(pools_from_teams) if pools_from_teams else len(pools_from_schedule)
        print(f'📊 Données: {len(teams)} équipes, {pool_count} poules')
    
    print(f'\n🌐 Ouvrez dans votre navigateur:')
    print(f'   file://{output_path.absolute()}')
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
