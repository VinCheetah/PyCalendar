#!/usr/bin/env python3
"""
Génère l'interface HTML à partir d'une solution PyCalendar.

Ce script charge une solution JSON et génère une interface HTML interactive
pour visualiser et modifier le calendrier des matchs.

Usage:
    python scripts/generate_interface.py                                    # Auto-détection
    python scripts/generate_interface.py --config configs/config_hand.yaml  # Depuis config
    python scripts/generate_interface.py --solution solutions/latest_volley.json
    python scripts/generate_interface.py --sport basket

Exemples:
    # Générer l'interface pour le volleyball (défaut)
    python scripts/generate_interface.py

    # Générer l'interface pour le handball
    python scripts/generate_interface.py --config configs/config_hand.yaml -o calendrier_hand.html

    # Générer depuis une solution spécifique
    python scripts/generate_interface.py --solution solutions/solution_volley_2025-12-15.json
"""

import sys
from pathlib import Path

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from scripts.script_base import (
    ScriptContext,
    create_base_parser,
    print_header,
    print_success,
    print_error,
    print_info,
)
from pycalendar.interface.core.generator import InterfaceGenerator


def main():
    # Parser avec arguments spécifiques
    parser = create_base_parser(
        description="Génère l'interface HTML à partir d'une solution PyCalendar"
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default=None,
        help='Fichier HTML de sortie (défaut: interface.html ou interface_{sport}.html)'
    )
    
    parser.add_argument(
        '--name',
        type=str,
        default=None,
        help='Nom de la solution (pour le tracking des modifications)'
    )
    
    # Ajouter des exemples en epilog
    parser.epilog = """
Exemples:
    python scripts/generate_interface.py
    python scripts/generate_interface.py --config configs/config_hand.yaml
    python scripts/generate_interface.py --solution solutions/latest_volley.json
    python scripts/generate_interface.py --sport basket -o calendrier_basket.html
    """
    
    args = parser.parse_args()
    
    # Créer le contexte
    try:
        ctx = ScriptContext.from_args(args)
    except FileNotFoundError as e:
        print_error(str(e))
        return 1
    
    # Afficher le header
    print_header(f"Génération de l'interface {ctx.sport.name}", ctx.sport.emoji)
    ctx.print_status()
    
    # Vérifier qu'on a une solution
    if not ctx.solution_path or not ctx.solution_path.exists():
        print_error("Aucune solution trouvée")
        print_info("Spécifiez une solution avec --solution ou --config")
        return 1
    
    # Déterminer le fichier de sortie
    if args.output:
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = PROJECT_ROOT / output_path
    else:
        output_path = PROJECT_ROOT / f'interface_{ctx.sport.pattern}.html'
    
    # Nom de la solution
    solution_name = args.name or ctx.solution_path.stem.replace('latest_', '').replace('solution_', '')
    
    print()
    print_info(f"Génération vers: {output_path.name}")
    
    # Générer l'interface
    generator = InterfaceGenerator()
    
    # Charger la configuration si disponible
    config = None
    if ctx.config_path:
        from pycalendar.core.config import Config
        try:
            config = Config.from_yaml(str(ctx.config_path))
        except Exception as e:
            print_info(f"Configuration non chargée pour enrichissement des pénalités: {e}")
    
    try:
        # Charger la solution et enrichir avec les données du calendrier
        import json
        with open(ctx.solution_path, 'r', encoding='utf-8') as f:
            solution_data = json.load(f)
        
        # Enrichir avec les données du calendrier depuis config_data
        if ctx.config_data and 'config' in solution_data:
            calendrier = ctx.config_data.get('calendrier', {})
            if calendrier and 'calendrier' not in solution_data['config']:
                solution_data['config']['calendrier'] = {
                    'date_debut': calendrier.get('date_debut', '2025-10-13'),
                    'jour_match': calendrier.get('jour_match', 'jeudi'),
                    'semaines_banalisees': calendrier.get('semaines_banalisees', []),
                }
                print_info(f"Enrichissement avec le calendrier: date_debut={calendrier.get('date_debut')}")
        
        result_path = generator.generate(
            solution=solution_data,
            output_path=str(output_path),
            config=config,  # Pass config for penalty enrichment
            solution_name=solution_name
        )
        
        print()
        print_success(f"Interface générée: {result_path}")
        print_info("Ouvrez le fichier dans un navigateur pour le visualiser")
        
        return 0
        
    except Exception as e:
        print()
        print_error(f"Erreur lors de la génération: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
