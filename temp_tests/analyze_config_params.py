#!/usr/bin/env python3
"""
Script d'analyse de l'utilisation des paramètres de configuration YAML.
Identifie les paramètres:
- Obsolètes (marqués comme tels mais encore utilisés)
- Non utilisés (définis mais jamais référencés)
- Mal utilisés (confusion entre solvers, valeurs incohérentes)
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, Set, List, Tuple, Any
from collections import defaultdict


def extract_params_from_config_class() -> Set[str]:
    """Extrait tous les paramètres définis dans CalendarConfig."""
    params = set()
    config_file = Path(__file__).parent.parent / 'src' / 'pycalendar' / 'core' / 'config.py'
    
    with open(config_file, 'r', encoding='utf-8') as f:
        content = f.read()
        # Chercher les attributs de dataclass
        for match in re.finditer(r'^\s+(\w+):\s+(?:int|float|bool|str|dict|List)', content, re.MULTILINE):
            params.add(match.group(1))
    
    return params


def search_param_usage(param: str, search_dirs: List[Path]) -> List[Tuple[str, int, str]]:
    """
    Cherche l'utilisation d'un paramètre dans les fichiers Python.
    Retourne: liste de (fichier, ligne, contexte)
    """
    results = []
    
    for search_dir in search_dirs:
        for py_file in search_dir.rglob('*.py'):
            if 'config.py' in str(py_file) or '__pycache__' in str(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        # Chercher self.config.param ou config.param
                        if re.search(rf'\b(?:self\.config|config)\.{param}\b', line):
                            results.append((
                                str(py_file.relative_to(Path(__file__).parent.parent)),
                                line_num,
                                line.strip()
                            ))
            except Exception as e:
                pass
    
    return results


def analyze_obsolete_params() -> Dict[str, Any]:
    """Analyse les paramètres marqués OBSOLÈTE dans le code."""
    config_file = Path(__file__).parent.parent / 'src' / 'pycalendar' / 'core' / 'config.py'
    obsolete = {}
    
    with open(config_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            if 'OBSOLÈTE' in line or 'obsolète' in line.lower():
                # Chercher le nom du paramètre dans les lignes précédentes
                for j in range(max(0, i-3), i+1):
                    match = re.search(r'(\w+):\s+(?:int|float|bool|str)', lines[j])
                    if match:
                        param_name = match.group(1)
                        obsolete[param_name] = {
                            'line': i+1,
                            'comment': line.strip()
                        }
                        break
    
    return obsolete


def analyze_disabled_features() -> Dict[str, Any]:
    """Analyse les fonctionnalités désactivées dans default.yaml."""
    default_yaml = Path(__file__).parent.parent / 'configs' / 'default.yaml'
    disabled = {}
    
    with open(default_yaml, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            if 'non fonctionnel' in line.lower() or 'ne pas activer' in line.lower():
                disabled[i+1] = line.strip()
    
    return disabled


def analyze_solver_specific_params() -> Dict[str, List[str]]:
    """Identifie les paramètres spécifiques à chaque solver."""
    greedy_only = []
    cpsat_only = []
    
    default_yaml = Path(__file__).parent.parent / 'configs' / 'default.yaml'
    
    with open(default_yaml, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            if 'greedy uniquement' in line.lower():
                # Chercher le paramètre dans les lignes précédentes
                for j in range(max(0, i-3), i+1):
                    match = re.search(r'(\w+):', lines[j])
                    if match and not lines[j].strip().startswith('#'):
                        greedy_only.append(match.group(1))
                        break
            elif 'cpsat uniquement' in line.lower() or 'cp-sat uniquement' in line.lower():
                for j in range(max(0, i-3), i+1):
                    match = re.search(r'(\w+):', lines[j])
                    if match and not lines[j].strip().startswith('#'):
                        cpsat_only.append(match.group(1))
                        break
    
    return {'greedy': greedy_only, 'cpsat': cpsat_only}


def main():
    print("=" * 80)
    print("ANALYSE CRITIQUE DES PARAMÈTRES DE CONFIGURATION YAML")
    print("=" * 80)
    print()
    
    # Répertoires à scanner
    src_dir = Path(__file__).parent.parent / 'src' / 'pycalendar'
    search_dirs = [src_dir / 'solvers', src_dir / 'core', src_dir / 'interface']
    
    # 1. Extraire tous les paramètres
    print("1. EXTRACTION DES PARAMÈTRES DÉFINIS")
    print("-" * 80)
    all_params = extract_params_from_config_class()
    print(f"Total de paramètres définis: {len(all_params)}")
    print()
    
    # 2. Analyser les paramètres obsolètes
    print("2. PARAMÈTRES MARQUÉS OBSOLÈTES")
    print("-" * 80)
    obsolete = analyze_obsolete_params()
    if obsolete:
        for param, info in obsolete.items():
            print(f"⚠️  {param}")
            print(f"   Commentaire: {info['comment']}")
            
            # Vérifier s'il est encore utilisé
            usages = search_param_usage(param, search_dirs)
            if usages:
                print(f"   ❌ PROBLÈME: Encore utilisé dans {len(usages)} endroit(s):")
                for file, line, context in usages[:3]:  # Afficher max 3 exemples
                    print(f"      - {file}:{line}")
            else:
                print(f"   ✅ Plus utilisé - PEUT ÊTRE SUPPRIMÉ")
            print()
    else:
        print("Aucun paramètre marqué obsolète trouvé.")
        print()
    
    # 3. Analyser les fonctionnalités désactivées
    print("3. FONCTIONNALITÉS DÉSACTIVÉES")
    print("-" * 80)
    disabled = analyze_disabled_features()
    if disabled:
        for line_num, comment in disabled.items():
            print(f"Ligne {line_num}: {comment}")
        print()
    
    # 4. Analyser les paramètres spécifiques aux solvers
    print("4. PARAMÈTRES SPÉCIFIQUES AUX SOLVERS")
    print("-" * 80)
    solver_params = analyze_solver_specific_params()
    
    print("Greedy uniquement:")
    for param in solver_params['greedy']:
        print(f"  - {param}")
        # Vérifier s'il est utilisé dans cpsat_solver
        cpsat_file = src_dir / 'solvers' / 'cpsat_solver.py'
        if cpsat_file.exists():
            with open(cpsat_file, 'r') as f:
                if param in f.read():
                    print(f"    ❌ PROBLÈME: Trouvé dans cpsat_solver.py !")
    
    print("\nCP-SAT uniquement:")
    for param in solver_params['cpsat']:
        print(f"  - {param}")
        # Vérifier s'il est utilisé dans greedy_solver
        greedy_file = src_dir / 'solvers' / 'greedy_solver.py'
        if greedy_file.exists():
            with open(greedy_file, 'r') as f:
                if param in f.read():
                    print(f"    ❌ PROBLÈME: Trouvé dans greedy_solver.py !")
    print()
    
    # 5. Paramètres jamais utilisés
    print("5. PARAMÈTRES NON UTILISÉS")
    print("-" * 80)
    unused = []
    
    # Paramètres à exclure de l'analyse (utilisés indirectement)
    excluded = {'fichier_donnees', 'fichier_sortie', 'log_level', 'nb_semaines', 
                'semaine_min', 'date_debut', 'jour_match', 'duree_match_minutes'}
    
    for param in sorted(all_params):
        if param in excluded:
            continue
            
        usages = search_param_usage(param, search_dirs)
        if not usages:
            unused.append(param)
    
    if unused:
        for param in unused:
            print(f"⚠️  {param} - jamais utilisé dans le code")
    else:
        print("Tous les paramètres pertinents sont utilisés.")
    print()
    
    # 6. Analyse du système qualite_match
    print("6. SYSTÈME QUALITE_MATCH (DÉSACTIVÉ)")
    print("-" * 80)
    qualite_params = [p for p in all_params if 'qualite_match' in p]
    print(f"Paramètres liés au système: {len(qualite_params)}")
    for param in qualite_params:
        usages = search_param_usage(param, search_dirs)
        print(f"  {param}: {len(usages)} usage(s)")
        if usages and param != 'qualite_match_actif':
            print(f"    ⚠️  Code mort (système désactivé)")
    print()
    
    # 7. Analyse entente_facteur_reduction
    print("7. ANALYSE ENTENTE_FACTEUR_REDUCTION (OBSOLÈTE)")
    print("-" * 80)
    param = 'entente_facteur_reduction'
    usages = search_param_usage(param, search_dirs)
    print(f"Utilisations trouvées: {len(usages)}")
    for file, line, context in usages:
        print(f"  {file}:{line}")
        print(f"    {context}")
    print()
    
    # 8. Résumé des problèmes
    print("=" * 80)
    print("RÉSUMÉ DES PROBLÈMES IDENTIFIÉS")
    print("=" * 80)
    
    problems = []
    
    # Comptage des problèmes
    if obsolete:
        for param, info in obsolete.items():
            usages = search_param_usage(param, search_dirs)
            if usages:
                problems.append(f"OBSOLÈTE mais utilisé: {param} ({len(usages)} usages)")
    
    if unused:
        problems.append(f"Paramètres non utilisés: {len(unused)}")
    
    if len(qualite_params) > 0:
        problems.append(f"Système qualite_match désactivé mais code présent ({len(qualite_params)} params)")
    
    for i, problem in enumerate(problems, 1):
        print(f"{i}. {problem}")
    
    print()
    print(f"Total: {len(problems)} catégories de problèmes identifiés")
    print()


if __name__ == '__main__':
    main()
