#!/usr/bin/env python3
"""
Script de vérification de la qualité des solutions générées.

Vérifie que:
- Les poules sont correctement renseignées (pas de M_Pool_*, F_Pool_*)
- Les noms d'équipes sont complets
- Les données essentielles sont présentes
"""

import json
import sys
from pathlib import Path
from collections import Counter


def check_solution_quality(solution_path: Path) -> dict:
    """
    Vérifie la qualité d'une solution.
    
    Returns:
        dict avec les statistiques et problèmes détectés
    """
    with open(solution_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    version = data.get('version', '1.0')
    results = {
        'version': version,
        'path': str(solution_path),
        'issues': [],
        'warnings': [],
        'stats': {}
    }
    
    if version == '2.0':
        # Vérification format v2.0
        entities = data.get('entities', {})
        matches = data.get('matches', {}).get('scheduled', [])
        
        # Stats
        results['stats'] = {
            'equipes': len(entities.get('equipes', [])),
            'gymnases': len(entities.get('gymnases', [])),
            'poules': len(entities.get('poules', [])),
            'matchs': len(matches)
        }
        
        # Vérifier les poules
        poules = entities.get('poules', [])
        poule_names = [p['nom'] for p in poules]
        
        invented_pools = [p for p in poule_names if p.startswith('M_Pool_') or p.startswith('F_Pool_')]
        if invented_pools:
            results['issues'].append({
                'type': 'POULES_INVENTÉES',
                'message': f"{len(invented_pools)} poules inventées détectées (clustering)",
                'details': invented_pools[:5]  # Premiers 5 exemples
            })
        else:
            results['stats']['poules_reelles'] = len(poule_names)
        
        # Vérifier les noms d'équipes
        equipes = entities.get('equipes', [])
        equipes_sans_nom = [e for e in equipes if not e.get('nom') or e.get('nom') == '']
        if equipes_sans_nom:
            results['issues'].append({
                'type': 'ÉQUIPES_SANS_NOM',
                'message': f"{len(equipes_sans_nom)} équipes sans nom",
                'details': [e.get('id') for e in equipes_sans_nom[:5]]
            })
        
        # Vérifier les matchs
        matchs_sans_poule = [m for m in matches if not m.get('poule')]
        if matchs_sans_poule:
            results['warnings'].append({
                'type': 'MATCHS_SANS_POULE',
                'message': f"{len(matchs_sans_poule)} matchs sans poule",
                'count': len(matchs_sans_poule)
            })
        
    else:
        # Vérification format v1.0
        assignments = data.get('assignments', [])
        metadata = data.get('metadata', {})
        
        results['stats'] = {
            'assignments': len(assignments),
            'matchs_planifies': metadata.get('matchs_planifies', 0),
            'matchs_non_planifies': metadata.get('matchs_non_planifies', 0)
        }
        
        # Vérifier les poules
        poules = [a.get('poule') for a in assignments]
        poules_uniques = list(set([p for p in poules if p]))
        
        if not poules_uniques:
            results['issues'].append({
                'type': 'POULES_MANQUANTES',
                'message': 'Aucune poule renseignée dans les assignments',
                'details': 'Le champ "poule" est manquant ou vide'
            })
        else:
            results['stats']['poules_uniques'] = len(poules_uniques)
            
            # Compter les assignments sans poule
            sans_poule = sum(1 for p in poules if not p)
            if sans_poule > 0:
                results['warnings'].append({
                    'type': 'ASSIGNMENTS_SANS_POULE',
                    'message': f"{sans_poule} assignments sans poule",
                    'count': sans_poule
                })
    
    return results


def print_results(results: dict):
    """Affiche les résultats de vérification."""
    print("=" * 70)
    print(f"🔍 VÉRIFICATION DE QUALITÉ - Format v{results['version']}")
    print("=" * 70)
    print(f"📂 Fichier: {results['path']}")
    print()
    
    # Stats
    print("📊 Statistiques:")
    for key, value in results['stats'].items():
        key_label = key.replace('_', ' ').title()
        print(f"   • {key_label}: {value}")
    print()
    
    # Issues (problèmes critiques)
    if results['issues']:
        print("❌ PROBLÈMES CRITIQUES:")
        for issue in results['issues']:
            print(f"   • {issue['type']}: {issue['message']}")
            if 'details' in issue:
                details = issue['details']
                if isinstance(details, list):
                    for d in details[:3]:
                        print(f"     - {d}")
                    if len(details) > 3:
                        print(f"     ... et {len(details) - 3} autres")
                else:
                    print(f"     {details}")
        print()
    
    # Warnings (avertissements)
    if results['warnings']:
        print("⚠️  AVERTISSEMENTS:")
        for warning in results['warnings']:
            print(f"   • {warning['type']}: {warning['message']}")
        print()
    
    # Verdict
    if not results['issues'] and not results['warnings']:
        print("✅ TOUT EST OK ! Aucun problème détecté.")
    elif not results['issues']:
        print("⚠️  QUALITÉ ACCEPTABLE (avertissements mineurs)")
    else:
        print("❌ PROBLÈMES DÉTECTÉS - Veuillez vérifier les erreurs ci-dessus")
    
    print("=" * 70)
    
    return 0 if not results['issues'] else 1


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Vérifie la qualité des solutions générées',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        'solution',
        nargs='?',
        default='latest_volley.json',
        help='Fichier de solution à vérifier (défaut: latest_volley.json)'
    )
    
    parser.add_argument(
        '--format',
        choices=['v1', 'v2', 'auto'],
        default='auto',
        help='Format de la solution (auto: détecte automatiquement)'
    )
    
    args = parser.parse_args()
    
    # Trouver le fichier
    solution_path = None
    
    if args.format == 'auto':
        # Chercher dans v2.0, puis v1.0, puis racine
        for folder in ['v2.0', 'v1.0', '']:
            candidate = Path('solutions') / folder / args.solution if folder else Path('solutions') / args.solution
            if candidate.exists():
                solution_path = candidate
                break
    elif args.format == 'v2':
        solution_path = Path('solutions') / 'v2.0' / args.solution
    else:
        solution_path = Path('solutions') / 'v1.0' / args.solution
    
    if not solution_path or not solution_path.exists():
        # Essayer chemin direct
        solution_path = Path(args.solution)
        if not solution_path.exists():
            print(f"❌ Solution introuvable: {args.solution}")
            print("\n💡 Fichiers disponibles:")
            for folder in ['v2.0', 'v1.0']:
                folder_path = Path('solutions') / folder
                if folder_path.exists():
                    print(f"\n   {folder}/:")
                    for f in folder_path.glob('*.json'):
                        print(f"     - {f.name}")
            return 1
    
    # Vérifier la solution
    try:
        results = check_solution_quality(solution_path)
        return print_results(results)
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
