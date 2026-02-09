#!/usr/bin/env python3
"""
Valide et actualise un fichier de configuration Excel.

Ce script vérifie et met à jour les données du fichier Excel associé à une
configuration YAML.

Usage:
    python scripts/update_config_excel.py                                    # Validation seule
    python scripts/update_config_excel.py --auto                             # Correction automatique
    python scripts/update_config_excel.py --interactive                      # Mode interactif
    python scripts/update_config_excel.py --config configs/config_hand.yaml  # Config spécifique
    python scripts/update_config_excel.py --sport basket                     # Par sport

Modes:
    --validate    : Analyse le fichier sans modification (défaut)
    --auto        : Applique automatiquement toutes les corrections possibles
    --interactive : Demande confirmation pour chaque correction

Options:
    --no-format    : Ne pas appliquer le formatage visuel
    --no-dropdowns : Ne pas ajouter les listes déroulantes
    --no-backup    : Ne pas créer de sauvegarde avant modification
    -v, --verbose  : Mode verbeux (affiche tous les détails)

Exemples:
    # Valider la config volleyball (défaut)
    python scripts/update_config_excel.py

    # Corriger automatiquement la config handball
    python scripts/update_config_excel.py --config configs/config_hand.yaml --auto

    # Mode interactif avec verbosité
    python scripts/update_config_excel.py --interactive -v
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

# Try to import from new modular structure, fallback to old
try:
    from pycalendar.cli.excel_updater import (
        ConfigActualisateurV2,
        actualiser_fichier_v2,
        UpdateMode,
        UpdateOptions,
    )
    USE_NEW_MODULE = True
except ImportError:
    from pycalendar.cli.update_config_excel import actualiser_fichier_v2
    USE_NEW_MODULE = False


def main():
    parser = create_base_parser(
        description="Valide et actualise un fichier de configuration Excel"
    )
    
    # Mode selection
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        '--validate',
        action='store_true',
        default=True,
        help="Validation seule, sans modification (défaut)"
    )
    mode_group.add_argument(
        '--auto', '--auto-correct',
        action='store_true',
        dest='auto_correct',
        help="Applique automatiquement toutes les corrections possibles"
    )
    mode_group.add_argument(
        '--interactive', '-i',
        action='store_true',
        help="Mode interactif: demande confirmation pour chaque correction"
    )
    
    # Options
    parser.add_argument(
        '--no-format',
        action='store_true',
        help="Ne pas appliquer le formatage visuel"
    )
    parser.add_argument(
        '--no-dropdowns',
        action='store_true',
        help="Ne pas ajouter les listes déroulantes"
    )
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help="Ne pas créer de sauvegarde avant modification"
    )
    
    parser.epilog = """
Exemples:
    python scripts/update_config_excel.py
    python scripts/update_config_excel.py --config configs/config_hand.yaml --auto
    python scripts/update_config_excel.py --sport basket --interactive
    python scripts/update_config_excel.py --auto --no-backup -v
    """
    
    args = parser.parse_args()
    
    # Créer le contexte
    try:
        ctx = ScriptContext.from_args(args)
    except FileNotFoundError as e:
        print_error(str(e))
        return 1
    
    # Afficher le header
    print_header(f"Actualisation config {ctx.sport.name}", ctx.sport.emoji)
    ctx.print_status()
    
    # Vérifier qu'on a une config
    if not ctx.config_path or not ctx.config_path.exists():
        print_error("Aucune configuration trouvée")
        print_info("Spécifiez une config avec --config")
        return 1
    
    # Extraire le chemin du fichier Excel depuis la config
    config = ctx.config_data
    if not config:
        print_error("Impossible de lire la configuration")
        return 1
    
    # Trouver le chemin Excel
    excel_path = None
    if 'fichiers' in config and 'donnees' in config['fichiers']:
        excel_path = config['fichiers']['donnees']
    elif 'fichier_excel' in config:
        excel_path = config['fichier_excel']
    
    if not excel_path:
        print_error("Aucun fichier Excel trouvé dans la configuration")
        print_info("Cherché: fichiers.donnees ou fichier_excel")
        return 1
    
    # Résoudre le chemin
    excel_file = Path(excel_path)
    if not excel_file.is_absolute():
        excel_file = PROJECT_ROOT / excel_path
    
    if not excel_file.exists():
        print_error(f"Fichier Excel introuvable: {excel_file}")
        return 1
    
    print()
    print_info(f"Fichier Excel: {excel_file.name}")
    
    # Déterminer le mode
    if args.auto_correct:
        mode_str = "Correction automatique"
    elif args.interactive:
        mode_str = "Mode interactif"
    else:
        mode_str = "Validation seule"
    
    print_info(f"Mode: {mode_str}")
    
    # Actualiser
    try:
        if USE_NEW_MODULE:
            # Utiliser la nouvelle structure modulaire
            if args.auto_correct:
                mode = UpdateMode.AUTO_CORRECT
            elif args.interactive:
                mode = UpdateMode.INTERACTIVE
            else:
                mode = UpdateMode.VALIDATE
            
            options = UpdateOptions(
                mode=mode,
                verbose=args.verbose,
                format_output=not args.no_format,
                add_dropdowns=not args.no_dropdowns,
                backup=not args.no_backup,
                yaml_config_path=str(ctx.config_path) if ctx.config_path else None,
            )
            
            success = actualiser_fichier_v2(str(excel_file), options)
        else:
            # Fallback à l'ancienne version
            if args.auto_correct or args.interactive:
                print_info("Mode avancé non disponible, utilisation du mode standard")
            success = actualiser_fichier_v2(str(excel_file))
        
        if success:
            print()
            print_success("Configuration actualisée avec succès")
            return 0
        else:
            print()
            print_error("Des erreurs ont été détectées")
            if not args.auto_correct:
                print_info("Utilisez --auto pour appliquer les corrections automatiques")
            return 1
            
    except Exception as e:
        print()
        print_error(f"Erreur: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
