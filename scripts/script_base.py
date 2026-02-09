#!/usr/bin/env python3
"""
Module de base pour tous les scripts PyCalendar.

Ce module fournit:
- ScriptContext: Contexte d'exécution intelligent avec auto-détection
- Gestion automatique des configurations, solutions, et sports
- Arguments CLI standardisés
- Logging unifié

Usage:
    from scripts.script_base import ScriptContext, create_base_parser

    parser = create_base_parser("Description du script")
    parser.add_argument("--custom", help="Argument spécifique")
    args = parser.parse_args()

    with ScriptContext.from_args(args) as ctx:
        print(f"Sport: {ctx.sport.name} {ctx.sport.emoji}")
        print(f"Solution: {ctx.solution_path}")
        print(f"Config: {ctx.config_path}")
"""

import sys
import json
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
from contextlib import contextmanager


# ============================================================================
# CONFIGURATION DES PATHS
# ============================================================================

SCRIPTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPTS_DIR.parent
SRC_DIR = PROJECT_ROOT / "src"
SOLUTIONS_DIR = PROJECT_ROOT / "solutions"
CONFIGS_DIR = PROJECT_ROOT / "configs"
DATA_DIR = PROJECT_ROOT / "data"

# Ajouter les paths nécessaires
for _path in [str(PROJECT_ROOT), str(SRC_DIR)]:
    if _path not in sys.path:
        sys.path.insert(0, _path)


# ============================================================================
# MAPPINGS SPORTS (SINGLE SOURCE OF TRUTH)
# ============================================================================

SPORT_MAPPINGS = {
    # code -> (type, pattern, name, name_short, emoji, duree, score_format)
    'VB': ('volleyball', 'volley', 'Volleyball', 'Volley', '🏐', 120, 'sets'),
    'HB': ('handball', 'hand', 'Handball', 'Hand', '🤾', 90, 'points'),
    'BB': ('basketball', 'basket', 'Basketball', 'Basket', '🏀', 90, 'points'),
    'FB': ('football', 'foot', 'Football', 'Foot', '⚽', 90, 'points'),
    'FU': ('futsal', 'futsal', 'Futsal', 'Futsal', '🥅', 60, 'points'),
    'RU': ('rugby', 'rugby', 'Rugby', 'Rugby', '🏉', 80, 'points'),
    'TE': ('tennis', 'tennis', 'Tennis', 'Tennis', '🎾', 90, 'sets'),
    'BA': ('badminton', 'badminton', 'Badminton', 'Bad', '🏸', 60, 'sets'),
    'AT': ('athletisme', 'athle', 'Athlétisme', 'Athlé', '🏃', 120, 'points'),
}

# Mappings dérivés
CODE_TO_TYPE = {k: v[0] for k, v in SPORT_MAPPINGS.items()}
TYPE_TO_CODE = {v[0]: k for k, v in SPORT_MAPPINGS.items()}
PATTERN_TO_CODE = {v[1]: k for k, v in SPORT_MAPPINGS.items()}
CODE_TO_PATTERN = {k: v[1] for k, v in SPORT_MAPPINGS.items()}

# Alias pour les noms de sports
SPORT_ALIASES = {
    'volley': 'volleyball', 'volleyball': 'volleyball',
    'hand': 'handball', 'handball': 'handball',
    'basket': 'basketball', 'basketball': 'basketball',
    'foot': 'football', 'football': 'football',
    'futsal': 'futsal',
    'rugby': 'rugby',
    'tennis': 'tennis',
    'bad': 'badminton', 'badminton': 'badminton',
    'athle': 'athletisme', 'athletisme': 'athletisme',
}


# ============================================================================
# CLASSE SPORT
# ============================================================================

@dataclass
class Sport:
    """Informations complètes sur un sport."""
    
    code: str           # Ex: "VB", "HB"
    type: str           # Ex: "volleyball", "handball"
    pattern: str        # Ex: "volley", "hand" (pour noms de fichiers)
    name: str           # Ex: "Volleyball", "Handball"
    name_short: str     # Ex: "Volley", "Hand"
    emoji: str          # Ex: "🏐", "🤾"
    duree_match: int    # Durée en minutes
    score_format: str   # "points" ou "sets"
    
    # Propriétés calculées depuis la config (optionnelles)
    date_debut: Optional[datetime] = None
    jour_match: Optional[str] = None
    semaines_banalisees: List[int] = field(default_factory=list)
    
    def __str__(self) -> str:
        return f"{self.name} {self.emoji}"
    
    def __repr__(self) -> str:
        return f"Sport({self.name} {self.emoji}, code={self.code})"
    
    @classmethod
    def from_code(cls, code: str) -> 'Sport':
        """Crée un Sport depuis un code (VB, HB, etc.)."""
        code = code.upper()
        if code not in SPORT_MAPPINGS:
            code = 'VB'  # Défaut
        
        sport_type, pattern, name, name_short, emoji, duree, score = SPORT_MAPPINGS[code]
        return cls(
            code=code,
            type=sport_type,
            pattern=pattern,
            name=name,
            name_short=name_short,
            emoji=emoji,
            duree_match=duree,
            score_format=score,
        )
    
    @classmethod
    def from_type(cls, sport_type: str) -> 'Sport':
        """Crée un Sport depuis un type (volleyball, handball, etc.)."""
        sport_type = SPORT_ALIASES.get(sport_type.lower(), sport_type.lower())
        code = TYPE_TO_CODE.get(sport_type, 'VB')
        return cls.from_code(code)
    
    @classmethod
    def from_pattern(cls, pattern: str) -> 'Sport':
        """Crée un Sport depuis un pattern de fichier (volley, hand, etc.)."""
        code = PATTERN_TO_CODE.get(pattern.lower(), 'VB')
        return cls.from_code(code)
    
    @classmethod
    def from_poule_code(cls, poule_code: str) -> 'Sport':
        """Crée un Sport depuis un code de poule (VBFA1PA, HBMA3PB, etc.)."""
        if poule_code and len(poule_code) >= 2:
            return cls.from_code(poule_code[:2])
        return cls.from_code('VB')
    
    @classmethod
    def detect_from_filename(cls, filename: str) -> Optional['Sport']:
        """Détecte le sport depuis un nom de fichier."""
        name_lower = Path(filename).stem.lower()
        for pattern, code in PATTERN_TO_CODE.items():
            if pattern in name_lower:
                return cls.from_code(code)
        return None
    
    @classmethod
    def detect_from_solution(cls, solution_data: Dict[str, Any]) -> Optional['Sport']:
        """Détecte le sport depuis les données d'une solution."""
        # Méthode 1: Section 'sport'
        if 'sport' in solution_data:
            sport_info = solution_data['sport']
            if isinstance(sport_info, dict):
                if 'prefix' in sport_info:
                    return cls.from_code(sport_info['prefix'])
                if 'type' in sport_info:
                    return cls.from_type(sport_info['type'])
        
        # Méthode 2: Depuis les poules
        if 'entities' in solution_data:
            poules = solution_data['entities'].get('poules', [])
            if poules:
                poule_id = poules[0].get('id', '')
                if len(poule_id) >= 2:
                    return cls.from_poule_code(poule_id)
        
        return None


# ============================================================================
# CLASSE SCRIPT CONTEXT
# ============================================================================

@dataclass
class ScriptContext:
    """
    Contexte d'exécution pour les scripts PyCalendar.
    
    Gère automatiquement:
    - La détection du sport
    - La recherche des fichiers de configuration
    - La recherche des fichiers de solution
    - Le chargement des données
    """
    
    # Entrées (une seule suffit pour démarrer)
    config_path: Optional[Path] = None
    solution_path: Optional[Path] = None
    sport_arg: Optional[str] = None
    
    # Données chargées
    sport: Optional[Sport] = None
    config_data: Optional[Dict[str, Any]] = None
    solution_data: Optional[Dict[str, Any]] = None
    
    # Options
    verbose: bool = False
    
    def __post_init__(self):
        """Initialise et résout le contexte."""
        self._resolve()
    
    def _resolve(self):
        """Résout le sport, la config et la solution de manière intelligente."""
        
        # Cas 1: Config fournie -> charger le sport et chercher la solution
        if self.config_path:
            self._load_from_config()
        
        # Cas 2: Solution fournie -> charger et détecter le sport
        elif self.solution_path:
            self._load_from_solution()
        
        # Cas 3: Sport fourni -> chercher config et solution
        elif self.sport_arg:
            self._load_from_sport_arg()
        
        # Cas 4: Rien fourni -> chercher la solution la plus récente
        else:
            self._load_default()
        
        # Vérifier qu'on a au moins un sport
        if not self.sport:
            self.sport = Sport.from_code('VB')
    
    def _load_from_config(self):
        """Charge depuis un fichier de configuration."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration introuvable: {self.config_path}")
        
        # Charger le YAML
        import yaml
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config_data = yaml.safe_load(f)
        
        # Extraire le sport
        sport_config = self.config_data.get('sport', {})
        sport_type = sport_config.get('type', 'volleyball')
        self.sport = Sport.from_type(sport_type)
        
        # Enrichir avec les données du calendrier
        calendrier = self.config_data.get('calendrier', {})
        if calendrier.get('date_debut'):
            self.sport.date_debut = datetime.fromisoformat(calendrier['date_debut'])
        self.sport.jour_match = calendrier.get('jour_match', 'jeudi')
        self.sport.semaines_banalisees = calendrier.get('semaines_banalisees', [])
        
        # Chercher la solution si pas fournie
        if not self.solution_path:
            self.solution_path = self._find_solution(self.sport.pattern)
        
        # Charger la solution si trouvée
        if self.solution_path and self.solution_path.exists():
            self._load_solution_data()
    
    def _load_from_solution(self):
        """Charge depuis un fichier de solution."""
        if not self.solution_path.exists():
            raise FileNotFoundError(f"Solution introuvable: {self.solution_path}")
        
        self._load_solution_data()
        
        # Détecter le sport
        self.sport = Sport.detect_from_solution(self.solution_data)
        if not self.sport:
            self.sport = Sport.detect_from_filename(str(self.solution_path))
        
        # Chercher la config si pas fournie
        if not self.config_path and self.sport:
            self.config_path = self._find_config(self.sport.pattern)
            if self.config_path and self.config_path.exists():
                import yaml
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config_data = yaml.safe_load(f)
    
    def _load_from_sport_arg(self):
        """Charge depuis un argument sport."""
        sport_type = SPORT_ALIASES.get(self.sport_arg.lower(), self.sport_arg.lower())
        self.sport = Sport.from_type(sport_type)
        
        # Chercher config et solution
        self.config_path = self._find_config(self.sport.pattern)
        self.solution_path = self._find_solution(self.sport.pattern)
        
        # Charger les données
        if self.config_path and self.config_path.exists():
            import yaml
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config_data = yaml.safe_load(f)
        
        if self.solution_path and self.solution_path.exists():
            self._load_solution_data()
    
    def _load_default(self):
        """Charge la solution la plus récente."""
        # Chercher toutes les solutions récentes
        latest_files = list(SOLUTIONS_DIR.glob('latest_*.json'))
        solution_files = list(SOLUTIONS_DIR.glob('solution_*.json'))
        
        all_solutions = latest_files + solution_files
        if all_solutions:
            # Trier par date de modification
            all_solutions.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            self.solution_path = all_solutions[0]
            self._load_from_solution()
        else:
            # Aucune solution -> défaut volleyball
            self.sport = Sport.from_code('VB')
    
    def _load_solution_data(self):
        """Charge les données de la solution."""
        with open(self.solution_path, 'r', encoding='utf-8') as f:
            self.solution_data = json.load(f)
    
    def _find_config(self, pattern: str) -> Optional[Path]:
        """Cherche un fichier de configuration pour un sport."""
        candidates = [
            CONFIGS_DIR / f"config_{pattern}.yaml",
            CONFIGS_DIR / f"config_{pattern}.yml",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None
    
    def _find_solution(self, pattern: str) -> Optional[Path]:
        """Cherche le dernier fichier solution pour un sport."""
        # Priorité 1: latest_{pattern}.json
        latest = SOLUTIONS_DIR / f"latest_{pattern}.json"
        if latest.exists():
            return latest
        
        # Priorité 2: solution_{pattern}_*.json le plus récent
        solutions = sorted(
            SOLUTIONS_DIR.glob(f"solution_{pattern}_*.json"),
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )
        return solutions[0] if solutions else None
    
    @classmethod
    def from_args(cls, args: argparse.Namespace) -> 'ScriptContext':
        """Crée un contexte depuis les arguments CLI."""
        config_path = None
        solution_path = None
        sport_arg = None
        
        # Extraire les arguments standard
        if hasattr(args, 'config') and args.config:
            config_path = Path(args.config)
            if not config_path.is_absolute():
                config_path = PROJECT_ROOT / config_path
        
        if hasattr(args, 'solution') and args.solution:
            solution_path = Path(args.solution)
            if not solution_path.is_absolute():
                solution_path = PROJECT_ROOT / solution_path
        
        if hasattr(args, 'sport') and args.sport:
            sport_arg = args.sport
        
        verbose = getattr(args, 'verbose', False)
        
        return cls(
            config_path=config_path,
            solution_path=solution_path,
            sport_arg=sport_arg,
            verbose=verbose,
        )
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def print_status(self):
        """Affiche le statut du contexte."""
        print(f"🎯 Sport: {self.sport}")
        if self.config_path:
            print(f"📋 Config: {self.config_path.name}")
        if self.solution_path:
            print(f"📁 Solution: {self.solution_path.name}")
    
    # ========================================================================
    # PROPRIÉTÉS UTILES
    # ========================================================================
    
    @property
    def data_dir(self) -> Path:
        """Répertoire des données pour ce sport."""
        return DATA_DIR / self.sport.type
    
    @property
    def excel_path(self) -> Optional[Path]:
        """Chemin vers le fichier Excel de configuration."""
        if self.config_data:
            fichiers = self.config_data.get('fichiers', {})
            donnees = fichiers.get('donnees')
            if donnees:
                path = Path(donnees)
                if not path.is_absolute():
                    path = PROJECT_ROOT / donnees
                return path
        return None
    
    @property
    def output_excel_path(self) -> Optional[Path]:
        """Chemin vers le fichier Excel de sortie."""
        if self.config_data:
            fichiers = self.config_data.get('fichiers', {})
            sortie = fichiers.get('sortie')
            if sortie:
                path = Path(sortie)
                if not path.is_absolute():
                    path = PROJECT_ROOT / sortie
                return path
        return None
    
    def get_scheduled_matches(self) -> List[Dict]:
        """Retourne les matchs planifiés."""
        if self.solution_data:
            return self.solution_data.get('matches', {}).get('scheduled', [])
        return []
    
    def get_unscheduled_matches(self) -> List[Dict]:
        """Retourne les matchs non planifiés."""
        if self.solution_data:
            return self.solution_data.get('matches', {}).get('unscheduled', [])
        return []
    
    def get_teams(self) -> List[Dict]:
        """Retourne les équipes."""
        if self.solution_data:
            return self.solution_data.get('entities', {}).get('equipes', [])
        return []
    
    def get_pools(self) -> List[Dict]:
        """Retourne les poules."""
        if self.solution_data:
            return self.solution_data.get('entities', {}).get('poules', [])
        return []
    
    def get_gyms(self) -> List[Dict]:
        """Retourne les gymnases."""
        if self.solution_data:
            return self.solution_data.get('entities', {}).get('gymnases', [])
        return []


# ============================================================================
# FONCTIONS UTILITAIRES CLI
# ============================================================================

def create_base_parser(description: str, with_solution: bool = True, with_sport: bool = True) -> argparse.ArgumentParser:
    """
    Crée un parser d'arguments de base avec les options standard.
    
    Args:
        description: Description du script
        with_solution: Inclure l'argument --solution
        with_sport: Inclure l'argument --sport
    
    Returns:
        ArgumentParser configuré
    """
    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    # Argument principal: --config (prioritaire)
    parser.add_argument(
        '--config', '-c',
        type=str,
        help='Fichier de configuration YAML (ex: configs/config_volley.yaml)'
    )
    
    if with_solution:
        parser.add_argument(
            '--solution', '-s',
            type=str,
            help='Fichier solution JSON (ex: solutions/latest_volley.json)'
        )
    
    if with_sport:
        parser.add_argument(
            '--sport',
            type=str,
            choices=list(SPORT_ALIASES.keys()),
            help='Sport à utiliser (ex: volley, hand, basket)'
        )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Mode verbeux'
    )
    
    return parser


def print_header(title: str, emoji: str = "🚀"):
    """Affiche un en-tête formaté."""
    width = 70
    print()
    print("=" * width)
    print(f"{emoji} {title}")
    print("=" * width)


def print_success(message: str):
    """Affiche un message de succès."""
    print(f"✅ {message}")


def print_error(message: str):
    """Affiche un message d'erreur."""
    print(f"❌ {message}")


def print_warning(message: str):
    """Affiche un avertissement."""
    print(f"⚠️  {message}")


def print_info(message: str):
    """Affiche une information."""
    print(f"ℹ️  {message}")


# ============================================================================
# FONCTIONS DE COMPATIBILITÉ (pour sport_utils.py)
# ============================================================================

def extraire_sport_code(code_poule: str) -> str:
    """Extrait le code sport (2 lettres) depuis un code de poule."""
    if not code_poule or not isinstance(code_poule, str) or len(code_poule) < 2:
        return 'VB'
    code = code_poule[:2].upper()
    return code if code in SPORT_MAPPINGS else 'VB'


def extraire_genre_niveau(code_poule: str) -> tuple:
    """Extrait genre et niveau depuis un code de poule (VBFA1PA -> ('F', 'A1'))."""
    if not code_poule or not isinstance(code_poule, str) or len(code_poule) < 5:
        return 'M', 'A1'
    genre = code_poule[2] if code_poule[2] in 'FMX' else 'M'
    niveau = code_poule[3:5]
    return genre, niveau


# ============================================================================
# TEST
# ============================================================================

if __name__ == '__main__':
    print_header("Test du module script_base", "🧪")
    
    # Test 1: Depuis une config
    print("\n📋 Test 1: Chargement depuis config_volley.yaml")
    try:
        ctx = ScriptContext(config_path=CONFIGS_DIR / "config_volley.yaml")
        ctx.print_status()
        print(f"   Matchs planifiés: {len(ctx.get_scheduled_matches())}")
    except Exception as e:
        print(f"   Erreur: {e}")
    
    # Test 2: Depuis une solution
    print("\n📁 Test 2: Chargement depuis latest_volley.json")
    try:
        ctx = ScriptContext(solution_path=SOLUTIONS_DIR / "latest_volley.json")
        ctx.print_status()
    except Exception as e:
        print(f"   Erreur: {e}")
    
    # Test 3: Depuis un sport
    print("\n🏐 Test 3: Chargement depuis sport='hand'")
    try:
        ctx = ScriptContext(sport_arg="hand")
        ctx.print_status()
    except Exception as e:
        print(f"   Erreur: {e}")
    
    # Test 4: Auto-détection
    print("\n🔍 Test 4: Auto-détection")
    try:
        ctx = ScriptContext()
        ctx.print_status()
    except Exception as e:
        print(f"   Erreur: {e}")
    
    print("\n" + "=" * 70)
    print_success("Tests terminés!")
