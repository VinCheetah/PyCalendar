#!/usr/bin/env python3
"""
apply_modifications.py - Applique les modifications JSON à une solution

Ce script charge un fichier de modifications JSON (exporté depuis l'interface)
et applique les changements à une solution existante, créant une nouvelle version.

Usage:
    python apply_modifications.py MODIFICATIONS_FILE [--solution SOLUTION_NAME] [--output OUTPUT_NAME]
    
Exemples:
    python apply_modifications.py modifications_2025-10-24.json
    python apply_modifications.py mods.json --solution latest_volley --output solution_modifiee
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List

from core.config_manager import ConfigManager


def load_modifications(modifications_file: Path) -> Dict:
    """
    Charge et valide un fichier de modifications.
    
    Args:
        modifications_file: Chemin vers le fichier JSON
    
    Returns:
        Données de modifications validées
    """
    if not modifications_file.exists():
        raise FileNotFoundError(f"Fichier de modifications introuvable: {modifications_file}")
    
    print(f"📂 Chargement des modifications: {modifications_file.name}")
    
    with open(modifications_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Validation basique
    required_fields = ['export_version', 'metadata', 'modifications']
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Champ requis manquant: {field}")
    
    print(f"✅ {len(data['modifications'])} modification(s) chargée(s)")
    print(f"📅 Exportées le: {data['metadata']['export_date']}")
    
    return data


def load_solution(solution_name: str = None) -> tuple:
    """
    Charge une solution depuis le store.
    
    Args:
        solution_name: Nom de la solution (sans .json). Si None, charge latest_volley.json
    
    Returns:
        Tuple (solution_data, solution_path, config_signature)
    """
    solutions_dir = Path(__file__).parent / "solutions"
    
    # Déterminer le fichier
    if solution_name:
        solution_file = solutions_dir / f"{solution_name}.json"
        if not solution_file.exists():
            solution_file = solutions_dir / solution_name
    else:
        solution_file = solutions_dir / "latest_volley.json"
    
    if not solution_file.exists():
        raise FileNotFoundError(f"Solution introuvable: {solution_file}")
    
    print(f"📂 Chargement de la solution: {solution_file.name}")
    
    with open(solution_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    config_signature = data.get('config_signature', 'default')
    
    print(f"✅ Solution chargée: {len(data.get('assignments', []))} matchs")
    
    return data, solution_file, config_signature


def apply_modifications_to_solution(solution_data: Dict, modifications_data: Dict) -> Dict:
    """
    Applique les modifications à la solution.
    
    Args:
        solution_data: Données de la solution originale
        modifications_data: Données de modifications
    
    Returns:
        Nouvelle solution avec modifications appliquées
    """
    print(f"\n🔧 Application des modifications...")
    
    # Copier la solution
    new_solution = solution_data.copy()
    assignments = new_solution.get('assignments', [])
    
    # Créer un index des matchs par ID
    matches_by_id = {}
    for i, match in enumerate(assignments):
        match_id = match.get('match_id')
        if match_id:
            matches_by_id[match_id] = i
    
    # Appliquer chaque modification
    applied_count = 0
    skipped_count = 0
    
    for mod in modifications_data['modifications']:
        match_id = mod['match_id']
        new_slot = mod['new']
        
        if match_id not in matches_by_id:
            print(f"⚠️  Match {match_id} introuvable, ignoré")
            skipped_count += 1
            continue
        
        idx = matches_by_id[match_id]
        match = assignments[idx]
        
        # Appliquer les changements
        if 'semaine' in new_slot and new_slot['semaine'] is not None:
            match['semaine'] = new_slot['semaine']
        
        if 'horaire' in new_slot and new_slot['horaire'] is not None:
            match['horaire'] = new_slot['horaire']
        
        if 'gymnase' in new_slot and new_slot['gymnase'] is not None:
            match['gymnase'] = new_slot['gymnase']
        
        applied_count += 1
    
    print(f"✅ {applied_count} modification(s) appliquée(s)")
    if skipped_count > 0:
        print(f"⚠️  {skipped_count} modification(s) ignorée(s)")
    
    # Mettre à jour les métadonnées
    if 'metadata' not in new_solution:
        new_solution['metadata'] = {}
    
    new_solution['metadata']['modified'] = True
    new_solution['metadata']['modification_date'] = datetime.now().isoformat()
    new_solution['metadata']['modifications_source'] = modifications_data['metadata'].get('solution_name', 'unknown')
    new_solution['metadata']['modifications_count'] = applied_count
    
    return new_solution


def save_solution(solution_data: Dict, output_path: Path):
    """
    Sauvegarde la solution modifiée.
    
    Args:
        solution_data: Données de la solution
        output_path: Chemin de sortie
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(solution_data, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Solution sauvegardée: {output_path}")
    print(f"📊 Taille: {output_path.stat().st_size / 1024:.1f} KB")


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(
        description="Applique des modifications JSON à une solution PyCalendar",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  %(prog)s modifications.json
    Applique les modifications à latest_volley.json
  
  %(prog)s mods.json --solution solution_volley_2025-10-13
    Applique à une solution spécifique
  
  %(prog)s mods.json --output ma_solution_modifiee
    Spécifie le nom de sortie
        """
    )
    
    parser.add_argument(
        'modifications',
        type=str,
        help="Fichier JSON de modifications à appliquer"
    )
    
    parser.add_argument(
        '--solution', '-s',
        type=str,
        default=None,
        help="Nom de la solution source (défaut: latest_volley)"
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default=None,
        help="Nom de la solution de sortie (défaut: solution_modified_<timestamp>)"
    )
    
    parser.add_argument(
        '--overwrite',
        action='store_true',
        help="Écrase la solution source au lieu de créer une nouvelle"
    )
    
    args = parser.parse_args()
    
    try:
        # Charger les modifications
        modifications_file = Path(args.modifications)
        modifications_data = load_modifications(modifications_file)
        
        # Charger la solution
        solution_data, solution_path, config_signature = load_solution(args.solution)
        
        # Vérifier la compatibilité (si config_signature disponible)
        mod_config = modifications_data['metadata'].get('config_signature')
        if mod_config and mod_config != config_signature:
            print(f"⚠️  Attention: config différente (solution: {config_signature}, mods: {mod_config})")
            response = input("Continuer quand même ? (o/N): ")
            if response.lower() not in ('o', 'oui', 'y', 'yes'):
                print("Annulé.")
                return 1
        
        # Appliquer les modifications
        new_solution = apply_modifications_to_solution(solution_data, modifications_data)
        
        # Déterminer le chemin de sortie
        if args.overwrite:
            output_path = solution_path
            print(f"\n⚠️  Mode écrasement activé!")
        else:
            if args.output:
                output_name = args.output
                if not output_name.endswith('.json'):
                    output_name += '.json'
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_name = f"solution_modified_{timestamp}.json"
            
            output_path = Path(__file__).parent / "solutions" / output_name
        
        # Sauvegarder
        save_solution(new_solution, output_path)
        
        print(f"\n🎉 Terminé !")
        print(f"📁 Nouvelle solution: {output_path.name}")
        
        # Proposer de régénérer l'interface
        response = input("\nRégénérer l'interface HTML ? (o/N): ")
        if response.lower() in ('o', 'oui', 'y', 'yes'):
            print("\nExécutez:")
            print(f"  python regenerate_interface.py --solution {output_path.stem}")
        
        return 0
        
    except FileNotFoundError as e:
        print(f"❌ Erreur: {e}", file=sys.stderr)
        return 1
    
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
