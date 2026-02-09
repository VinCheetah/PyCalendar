#!/usr/bin/env python3
"""
Synchronise la configuration Excel depuis un export JSON du Pool Editor.

Ce script permet de synchroniser un fichier de configuration Excel
avec les données exportées depuis l'éditeur de poules (tools/pool_editor).

Feuilles synchronisées:
- Equipes : données des équipes (Genre, Niveau, Poule, Horaire)
- Types_Poules : types de championnat par poule (Classique/Aller-Retour)
- Dispos_Gymnases_Equipes : équipes avec horaires aménagés

Fonctionnalités:
- Ajoute les nouvelles équipes/poules présentes dans le JSON
- Met à jour les données existantes
- Supprime les éléments absents du JSON (mode 'replace')
- Préserve les données supplémentaires (Responsable_*, etc.)
- Crée une sauvegarde automatique avant modification

Usage:
    # Synchronisation complète (ajoute, modifie, supprime)
    python scripts/update_teams_from_pool_editor.py poules_export.json --config configs/config_volley.yaml

    # Mise à jour uniquement (ajoute, modifie, mais ne supprime pas)
    python scripts/update_teams_from_pool_editor.py poules_export.json --config configs/config_volley.yaml --update

    # Mode interactif avec prévisualisation
    python scripts/update_teams_from_pool_editor.py poules_export.json --config configs/config_volley.yaml --interactive

    # Synchroniser uniquement certaines feuilles
    python scripts/update_teams_from_pool_editor.py export.json --excel data/volley.xlsx --only-equipes

Exemples:
    python scripts/update_teams_from_pool_editor.py poules_2026-01-08.json --config configs/config_volley.yaml
    python scripts/update_teams_from_pool_editor.py export.json --excel data/handball/config_handball.xlsx
"""

import sys
import argparse
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
    print_warning,
)

from pycalendar.cli.pool_editor_sync import (
    synchroniser_depuis_json,
    synchroniser_equipes_depuis_json,
    afficher_rapport,
    PoolEditorSyncError,
    charger_equipes_depuis_json,
    charger_equipes_depuis_excel,
    comparer_equipes,
)


def previsualiser_modifications(json_path: Path, excel_path: Path, mode: str = 'replace'):
    """Affiche un aperçu des modifications qui seront effectuées."""
    print_header("PRÉVISUALISATION DES MODIFICATIONS")
    
    try:
        equipes_json, poules_json = charger_equipes_depuis_json(json_path)
        df_excel = charger_equipes_depuis_excel(excel_path)
        a_ajouter, a_supprimer, a_modifier = comparer_equipes(equipes_json, df_excel)
        
        # Compter les équipes avec horaires aménagés
        equipes_amenagees = [eq for eq in equipes_json if eq.has_amenaged_schedule]
        
        if a_ajouter:
            print_info(f"\n➕ {len(a_ajouter)} équipes seront AJOUTÉES:")
            for equipe in a_ajouter[:10]:
                amenage_str = " ⏰" if equipe.has_amenaged_schedule else ""
                print(f"   • {equipe.nom} [{equipe.genre}] {equipe.niveau} → {equipe.poule or 'Non assignée'}{amenage_str}")
            if len(a_ajouter) > 10:
                print(f"   ... et {len(a_ajouter) - 10} autres")
        
        if a_modifier:
            print_info(f"\n✏️  {len(a_modifier)} équipes seront MODIFIÉES:")
            for nom, equipe in a_modifier[:10]:
                amenage_str = " ⏰" if equipe.has_amenaged_schedule else ""
                print(f"   • {nom} → {equipe.niveau} [{equipe.genre}] {equipe.poule or 'Non assignée'}{amenage_str}")
            if len(a_modifier) > 10:
                print(f"   ... et {len(a_modifier) - 10} autres")
        
        if mode == 'replace' and a_supprimer:
            print_warning(f"\n🗑️  {len(a_supprimer)} équipes seront SUPPRIMÉES:")
            for nom in a_supprimer[:10]:
                print(f"   • {nom}")
            if len(a_supprimer) > 10:
                print(f"   ... et {len(a_supprimer) - 10} autres")
        elif mode == 'update' and a_supprimer:
            print_info(f"\nℹ️  {len(a_supprimer)} équipes absentes du JSON seront CONSERVÉES")
        
        # Afficher les poules
        if poules_json:
            print_info(f"\n🏆 {len(poules_json)} poules seront synchronisées dans Types_Poules:")
            ar_count = sum(1 for p in poules_json if p.type_championnat == 'aller-retour')
            classique_count = len(poules_json) - ar_count
            print(f"   • {classique_count} poules classiques")
            print(f"   • {ar_count} poules aller-retour")
        
        # Afficher les horaires aménagés
        if equipes_amenagees:
            print_info(f"\n⏰ {len(equipes_amenagees)} équipes avec horaires aménagés:")
            for eq in equipes_amenagees[:5]:
                print(f"   • {eq.nom} [{eq.genre}] → {eq.horaire_amenage} sur {', '.join(eq.gymnases_amenages)}")
            if len(equipes_amenagees) > 5:
                print(f"   ... et {len(equipes_amenagees) - 5} autres")
        
        if mode == 'replace':
            total_json = len(equipes_json)
            total_excel = len(df_excel)
            print_info(f"\n📊 Résumé:")
            print(f"   Excel actuel   : {total_excel} équipes")
            print(f"   JSON source    : {total_json} équipes")
            print(f"   → Toutes les équipes du JSON remplaceront celles de l'Excel")
            print(f"   → Les données supplémentaires (contacts) des équipes existantes seront préservées")
            print(f"   → Toutes les équipes du JSON remplaceront celles de l'Excel")
            print(f"   → Les données supplémentaires (contacts) des équipes existantes seront préservées")
        
        if not a_ajouter and not a_modifier and (mode == 'replace' and not a_supprimer):
            print_success("\n✨ Aucune modification nécessaire")
            return False
        
        return True
        
    except PoolEditorSyncError as e:
        print_error(f"Erreur lors de la prévisualisation: {e}")
        return False


def main():
    parser = create_base_parser(
        description="Synchronise la configuration Excel depuis un export JSON du Pool Editor"
    )
    
    # Argument positionnel pour le JSON
    parser.add_argument(
        'json_file',
        type=str,
        help="Chemin vers le fichier JSON exporté depuis le Pool Editor"
    )
    
    # Options de fichier Excel (alternative à --config)
    parser.add_argument(
        '--excel',
        type=str,
        help="Chemin direct vers le fichier Excel (alternative à --config)"
    )
    
    parser.add_argument(
        '--sheet',
        type=str,
        default='Equipes',
        help="Nom de la feuille principale à synchroniser (défaut: Equipes)"
    )
    
    # Mode de synchronisation
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        '--replace',
        action='store_true',
        default=True,
        help="Mode remplacement complet : remplace TOUTES les données du JSON [DÉFAUT]"
    )
    mode_group.add_argument(
        '--update',
        action='store_true',
        help="Mode mise à jour : ajoute et modifie, mais conserve les éléments absents du JSON"
    )
    mode_group.add_argument(
        '--sync',
        action='store_true',
        help="Alias de --replace pour compatibilité"
    )
    
    # Options de feuilles à synchroniser
    sync_group = parser.add_argument_group('Feuilles à synchroniser')
    sync_group.add_argument(
        '--only-equipes',
        action='store_true',
        help="Synchroniser uniquement la feuille Equipes"
    )
    sync_group.add_argument(
        '--only-poules',
        action='store_true',
        help="Synchroniser uniquement la feuille Types_Poules"
    )
    sync_group.add_argument(
        '--no-dispos',
        action='store_true',
        help="Ne pas synchroniser la feuille Dispos_Gymnases_Equipes"
    )
    
    # Options
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help="Ne pas créer de sauvegarde avant modification"
    )
    
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help="Mode interactif avec prévisualisation et confirmation"
    )
    
    parser.epilog = """
Exemples:
    # Synchronisation complète (défaut) - toutes les feuilles
    python scripts/update_teams_from_pool_editor.py poules_export.json --config configs/config_volley.yaml
    
    # Mode mise à jour - conserve les éléments absents du JSON
    python scripts/update_teams_from_pool_editor.py export.json --config configs/config_hand.yaml --update
    
    # Mode interactif avec prévisualisation
    python scripts/update_teams_from_pool_editor.py export.json --excel data/volleyball/config_volley.xlsx -i
    
    # Synchroniser uniquement les équipes
    python scripts/update_teams_from_pool_editor.py export.json --config configs/config_volley.yaml --only-equipes
    """
    
    args = parser.parse_args()
    
    # Vérifier le fichier JSON
    json_path = Path(args.json_file)
    if not json_path.exists():
        print_error(f"Fichier JSON introuvable: {json_path}")
        return 1
    
    # Déterminer le fichier Excel
    excel_path = None
    
    if args.excel:
        excel_path = Path(args.excel)
        if not excel_path.is_absolute():
            excel_path = PROJECT_ROOT / excel_path
    else:
        # Utiliser la config pour trouver le fichier Excel
        try:
            ctx = ScriptContext.from_args(args)
            if not ctx.config_path or not ctx.config_path.exists():
                print_error("Aucune configuration trouvée")
                print_info("Spécifiez --config ou --excel")
                return 1
            
            config = ctx.config_data
            if not config:
                print_error("Impossible de lire la configuration")
                return 1
            
            # Trouver le chemin Excel
            excel_rel_path = None
            if 'fichiers' in config and 'donnees' in config['fichiers']:
                excel_rel_path = config['fichiers']['donnees']
            elif 'fichier_excel' in config:
                excel_rel_path = config['fichier_excel']
            
            if not excel_rel_path:
                print_error("Aucun fichier Excel trouvé dans la configuration")
                print_info("Cherché: fichiers.donnees ou fichier_excel")
                return 1
            
            excel_path = Path(excel_rel_path)
            if not excel_path.is_absolute():
                excel_path = PROJECT_ROOT / excel_rel_path
            
        except FileNotFoundError as e:
            print_error(str(e))
            return 1
    
    if not excel_path.exists():
        print_error(f"Fichier Excel introuvable: {excel_path}")
        return 1
    
    # Afficher le header
    print_header("SYNCHRONISATION POOL EDITOR → EXCEL", "🔄")
    print_info(f"Fichier JSON  : {json_path.name}")
    print_info(f"Fichier Excel : {excel_path.name}")
    
    # Déterminer les feuilles à synchroniser
    sync_equipes = not args.only_poules
    sync_poules = not args.only_equipes
    sync_dispos = not args.no_dispos and not args.only_equipes and not args.only_poules
    
    feuilles = []
    if sync_equipes:
        feuilles.append("Equipes")
    if sync_poules:
        feuilles.append("Types_Poules")
    if sync_dispos:
        feuilles.append("Dispos_Gymnases_Equipes")
    
    print_info(f"Feuilles      : {', '.join(feuilles)}")
    
    # Déterminer le mode
    if args.update:
        mode = 'update'
        mode_label = "MISE À JOUR (conserve les éléments absents du JSON)"
    else:  # replace ou sync
        mode = 'replace'
        mode_label = "REMPLACEMENT COMPLET (toutes les données du JSON)"
    
    print_info(f"Mode          : {mode_label}")
    
    # Mode interactif: prévisualisation
    if args.interactive:
        print()
        a_des_modifications = previsualiser_modifications(json_path, excel_path, mode)
        
        if not a_des_modifications:
            return 0
        
        print()
        reponse = input("❓ Appliquer ces modifications ? [o/N] : ").strip().lower()
        if reponse not in ['o', 'oui', 'y', 'yes']:
            print_warning("Opération annulée")
            return 0
    
    # Effectuer la synchronisation
    print()
    try:
        stats = synchroniser_depuis_json(
            json_path=str(json_path),
            excel_path=str(excel_path),
            backup=not args.no_backup,
            mode=mode,
            sync_equipes=sync_equipes,
            sync_poules=sync_poules,
            sync_dispos=sync_dispos
        )
        
        afficher_rapport(stats)
        print_success("✅ Synchronisation terminée avec succès")
        return 0
        
    except PoolEditorSyncError as e:
        print()
        print_error(f"Erreur: {e}")
        return 1
    except Exception as e:
        print()
        print_error(f"Erreur inattendue: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
