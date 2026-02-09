#!/usr/bin/env python3
"""
Utilitaires pour la gestion des sports - Interface simplifiée.

Ce module fournit une interface de compatibilité pour les anciens scripts
tout en utilisant le nouveau module script_base.py en interne.

Pour les nouveaux scripts, utilisez directement script_base.py:
    from scripts.script_base import ScriptContext, Sport, create_base_parser

Usage legacy:
    from scripts.sport_utils import load_sport_from_config, find_latest_solution
"""

import sys
from pathlib import Path

# Setup path pour import
_SCRIPTS_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPTS_DIR.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# Réexporter depuis script_base pour compatibilité
from scripts.script_base import (
    # Classes principales
    Sport as SportInfo,
    ScriptContext,
    
    # Constantes
    PROJECT_ROOT,
    SOLUTIONS_DIR,
    CONFIGS_DIR,
    DATA_DIR,
    SPORT_MAPPINGS,
    CODE_TO_TYPE,
    TYPE_TO_CODE,
    PATTERN_TO_CODE,
    CODE_TO_PATTERN,
    SPORT_ALIASES,
    
    # Fonctions utilitaires
    extraire_sport_code,
    extraire_genre_niveau,
    create_base_parser,
    print_header,
    print_success,
    print_error,
    print_warning,
    print_info,
)

from pathlib import Path
from typing import Optional, Dict, Any


# ============================================================================
# FONCTIONS DE COMPATIBILITÉ (LEGACY API)
# ============================================================================

def load_sport_from_config(config_path: str) -> SportInfo:
    """
    Charge les informations de sport depuis un fichier de configuration YAML.
    
    LEGACY: Préférez ScriptContext(config_path=...) pour les nouveaux scripts.
    """
    ctx = ScriptContext(config_path=Path(config_path))
    return SportInfo(
        code=ctx.sport.code,
        type=ctx.sport.type,
        pattern=ctx.sport.pattern,
        name=ctx.sport.name,
        name_short=ctx.sport.name_short,
        emoji=ctx.sport.emoji,
        duree_match=ctx.sport.duree_match,
        score_format=ctx.sport.score_format,
    )


def find_latest_solution(sport_pattern: str, solutions_dir: str = None) -> Optional[Path]:
    """
    Trouve le dernier fichier solution pour un sport donné.
    
    LEGACY: Préférez ScriptContext(sport_arg=...).solution_path pour les nouveaux scripts.
    """
    solutions_path = Path(solutions_dir) if solutions_dir else SOLUTIONS_DIR
    
    if not solutions_path.exists():
        return None
    
    # Priorité 1: latest_{sport}.json
    latest_file = solutions_path / f"latest_{sport_pattern}.json"
    if latest_file.exists():
        return latest_file
    
    # Priorité 2: Dernier solution_{sport}_*.json
    solution_files = sorted(
        solutions_path.glob(f"solution_{sport_pattern}_*.json"),
        key=lambda f: f.stat().st_mtime,
        reverse=True
    )
    
    return solution_files[0] if solution_files else None


def get_sport_code_from_solution(solution_data: Dict[str, Any]) -> str:
    """
    Extrait le code sport depuis les données de solution.
    
    LEGACY: Préférez Sport.detect_from_solution(data).code
    """
    sport = SportInfo.detect_from_solution(solution_data)
    return sport.code if sport else 'VB'


def get_sport_pattern_from_code(code: str) -> str:
    """
    Convertit un code sport en pattern de fichier.
    
    LEGACY: Préférez Sport.from_code(code).pattern
    """
    return CODE_TO_PATTERN.get(code.upper(), 'volley')


def detect_sport_from_filename(filename: str) -> Optional[SportInfo]:
    """
    Détecte le sport depuis un nom de fichier.
    
    LEGACY: Préférez Sport.detect_from_filename(filename)
    """
    return SportInfo.detect_from_filename(filename)


def get_sport_info_from_poule(code_poule: str) -> SportInfo:
    """
    Obtient les informations du sport depuis un code de poule.
    
    LEGACY: Préférez Sport.from_poule_code(code)
    """
    return SportInfo.from_poule_code(code_poule)


def resolve_sport_and_solution(
    config_path: Optional[str] = None,
    sport_arg: Optional[str] = None,
    solution_path: Optional[str] = None,
    default_sport: str = 'volley'
) -> tuple:
    """
    Résout le sport et le fichier solution depuis les arguments.
    
    LEGACY: Préférez ScriptContext.from_args(args)
    """
    ctx = ScriptContext(
        config_path=Path(config_path) if config_path else None,
        solution_path=Path(solution_path) if solution_path else None,
        sport_arg=sport_arg or default_sport,
    )
    
    return ctx.sport, ctx.solution_path


# Alias pour compatibilité avec le code existant
SUPPORTED_SPORT_CODES = list(SPORT_MAPPINGS.keys())
SPORT_TYPE_TO_PATTERN = {v[0]: v[1] for v in SPORT_MAPPINGS.values()}
PATTERN_TO_SPORT_TYPE = {v[1]: v[0] for v in SPORT_MAPPINGS.values()}
CODE_TO_SPORT_TYPE = CODE_TO_TYPE
SPORT_TYPE_TO_CODE = TYPE_TO_CODE


# ============================================================================
# TEST
# ============================================================================

if __name__ == '__main__':
    print("=" * 70)
    print("Test du module sport_utils.py (API de compatibilité)")
    print("=" * 70)
    
    # Test load_sport_from_config
    print("\n📋 Test: load_sport_from_config")
    try:
        sport = load_sport_from_config("configs/config_volley.yaml")
        print(f"   Sport: {sport.name} {sport.emoji}")
        print(f"   Code: {sport.code}, Pattern: {sport.pattern}")
    except Exception as e:
        print(f"   Erreur: {e}")
    
    # Test find_latest_solution
    print("\n📁 Test: find_latest_solution")
    solution = find_latest_solution("volley")
    print(f"   Solution: {solution.name if solution else 'Non trouvée'}")
    
    # Test extraire_sport_code
    print("\n🏐 Test: extraire_sport_code")
    print(f"   VBFA1PA -> {extraire_sport_code('VBFA1PA')}")
    print(f"   HBMA3PB -> {extraire_sport_code('HBMA3PB')}")
    
    # Test extraire_genre_niveau
    print("\n📊 Test: extraire_genre_niveau")
    print(f"   VBFA1PA -> {extraire_genre_niveau('VBFA1PA')}")
    print(f"   HBMA3PB -> {extraire_genre_niveau('HBMA3PB')}")
    
    print("\n" + "=" * 70)
    print("✅ Tests terminés!")
