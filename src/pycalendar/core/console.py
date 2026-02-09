"""
Système unifié d'affichage console pour PyCalendar.

Ce module centralise toute la logique d'affichage pour garantir
une présentation cohérente et professionnelle des messages.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime


class LogLevel(Enum):
    """Niveaux de verbosité."""
    QUIET = 0      # Erreurs uniquement
    NORMAL = 1     # Messages importants
    VERBOSE = 2    # Détails supplémentaires
    DEBUG = 3      # Tout afficher


class MessageType(Enum):
    """Types de messages pour le formatage."""
    HEADER = "header"
    SECTION = "section"
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    PROGRESS = "progress"
    DETAIL = "detail"


@dataclass
class ConsoleConfig:
    """Configuration de l'affichage console."""
    level: LogLevel = LogLevel.NORMAL
    use_colors: bool = True
    use_emojis: bool = True
    line_width: int = 70
    indent: str = "  "


# Configuration globale (peut être modifiée via set_config)
_config = ConsoleConfig()


def set_config(config: ConsoleConfig):
    """Définit la configuration globale."""
    global _config
    _config = config


def get_config() -> ConsoleConfig:
    """Récupère la configuration globale."""
    return _config


# === COULEURS ANSI ===
class Colors:
    """Codes couleurs ANSI."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    
    # Couleurs
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    GRAY = "\033[90m"


def _color(text: str, color: str) -> str:
    """Applique une couleur si activé."""
    if _config.use_colors:
        return f"{color}{text}{Colors.RESET}"
    return text


def _emoji(emoji: str, fallback: str = "") -> str:
    """Retourne l'emoji si activé, sinon le fallback."""
    if _config.use_emojis:
        return emoji
    return fallback


# === FONCTIONS D'AFFICHAGE ===

def print_banner(sport_name: str = "Sports", sport_emoji: str = "🏐"):
    """Affiche la bannière principale du programme."""
    width = _config.line_width
    print()
    print("=" * width)
    title = f"PYCALENDAR - {sport_name} Scheduling System"
    if _config.use_emojis:
        title = f"{sport_emoji} {title} {sport_emoji}"
    # Centrage simplifié (les emojis complexifient le calcul de largeur)
    print(_color(title.center(width), Colors.BOLD + Colors.CYAN))
    print("=" * width)


def print_header(title: str, char: str = "="):
    """Affiche un en-tête de section majeure."""
    width = _config.line_width
    print()
    print(char * width)
    print(_color(title.upper(), Colors.BOLD))
    print(char * width)


def print_section(title: str, emoji: str = "📋"):
    """Affiche un titre de sous-section."""
    prefix = _emoji(emoji + " ", "")
    print(f"\n{prefix}{_color(title, Colors.BOLD)}")


def print_subsection(title: str):
    """Affiche un titre de sous-sous-section."""
    print(f"\n{_config.indent}{_color(title, Colors.BOLD)}")


def print_success(message: str, emoji: str = "✓"):
    """Affiche un message de succès."""
    prefix = _emoji(emoji + " ", "[OK] ")
    print(_color(f"{prefix}{message}", Colors.GREEN))


def print_error(message: str, emoji: str = "✗"):
    """Affiche un message d'erreur."""
    prefix = _emoji(emoji + " ", "[ERROR] ")
    print(_color(f"{prefix}{message}", Colors.RED))


def print_warning(message: str, emoji: str = "⚠"):
    """Affiche un message d'avertissement."""
    prefix = _emoji(emoji + "  ", "[WARN] ")
    print(_color(f"{prefix}{message}", Colors.YELLOW))


def print_info(message: str, emoji: str = "ℹ"):
    """Affiche un message informatif."""
    prefix = _emoji(emoji + "  ", "[INFO] ")
    print(_color(f"{prefix}{message}", Colors.BLUE))


def print_detail(message: str, indent_level: int = 1):
    """Affiche un détail indenté."""
    indent = _config.indent * indent_level
    print(f"{indent}• {message}")


def print_progress(step: str, current: Optional[int] = None, total: Optional[int] = None):
    """Affiche une étape de progression."""
    if current is not None and total is not None:
        pct = (current / total) * 100 if total > 0 else 0
        bar_width = 20
        filled = int(bar_width * current / total) if total > 0 else 0
        bar = "█" * filled + "░" * (bar_width - filled)
        print(f"\r{step} [{bar}] {pct:.0f}%", end="", flush=True)
        if current >= total:
            print()  # Nouvelle ligne à la fin
    else:
        print(f"{_emoji('⏳ ', '')}  {step}...")


def print_table(headers: List[str], rows: List[List[Any]], alignments: Optional[List[str]] = None):
    """
    Affiche un tableau formaté.
    
    Args:
        headers: Liste des en-têtes
        rows: Liste des lignes (chaque ligne est une liste de valeurs)
        alignments: Liste d'alignements ('l', 'c', 'r') pour chaque colonne
    """
    if not rows:
        return
    
    # Calculer les largeurs de colonnes
    col_widths = [len(str(h)) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], len(str(cell)))
    
    # Alignements par défaut
    if alignments is None:
        alignments = ['l'] * len(headers)
    
    def format_cell(value, width, align):
        s = str(value)
        if align == 'r':
            return s.rjust(width)
        elif align == 'c':
            return s.center(width)
        return s.ljust(width)
    
    # En-têtes
    header_line = " │ ".join(format_cell(h, col_widths[i], alignments[i]) 
                             for i, h in enumerate(headers))
    print(_color(header_line, Colors.BOLD))
    print("─" * len(header_line.replace("│", "─")))
    
    # Lignes
    for row in rows:
        line = " │ ".join(format_cell(row[i] if i < len(row) else "", 
                                       col_widths[i], alignments[i])
                          for i in range(len(headers)))
        print(line)


def print_key_value(key: str, value: Any, indent_level: int = 1):
    """Affiche une paire clé-valeur."""
    indent = _config.indent * indent_level
    print(f"{indent}{key}: {_color(str(value), Colors.CYAN)}")


def print_separator(char: str = "─"):
    """Affiche un séparateur."""
    print(char * _config.line_width)


def print_blank():
    """Affiche une ligne vide."""
    print()


# === CLASSES POUR RAPPORTS STRUCTURÉS ===

@dataclass
class LoadingResult:
    """Résultat du chargement d'une ressource."""
    name: str
    count: int
    success: bool = True
    details: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class LoadingReport:
    """Collecte et affiche les résultats de chargement."""
    
    def __init__(self):
        self.results: List[LoadingResult] = []
        self.start_time: datetime = datetime.now()
    
    def add(self, result: LoadingResult):
        """Ajoute un résultat."""
        self.results.append(result)
    
    def display_summary(self):
        """Affiche un résumé compact."""
        print_section("Données chargées", "📦")
        
        for r in self.results:
            if r.success:
                if r.count > 0:
                    msg = f"{r.name}: {r.count}"
                    if r.details:
                        msg += f" ({', '.join(r.details[:2])})"
                    print_detail(msg)
                else:
                    print_detail(f"{r.name}: aucun", 1)
            else:
                print_warning(f"{r.name}: échec du chargement")
        
        # Avertissements groupés
        all_warnings = []
        for r in self.results:
            all_warnings.extend(r.warnings)
        
        if all_warnings:
            print()
            for w in all_warnings[:5]:
                print_warning(w)
            if len(all_warnings) > 5:
                print_info(f"... et {len(all_warnings) - 5} autres avertissements")


@dataclass
class ValidationResult:
    """Résultat de validation d'une contrainte."""
    category: str
    is_hard: bool
    is_valid: bool
    message: str
    details: Dict[str, Any] = field(default_factory=dict)


class ValidationReport:
    """Collecte et affiche les résultats de validation."""
    
    def __init__(self):
        self.results: List[ValidationResult] = []
        self.stats: Dict[str, Any] = {}
    
    def add(self, result: ValidationResult):
        """Ajoute un résultat."""
        self.results.append(result)
    
    def is_valid(self) -> bool:
        """Retourne True si aucune contrainte dure n'est violée."""
        return all(r.is_valid for r in self.results if r.is_hard)
    
    def count_violations(self, hard_only: bool = False) -> int:
        """Compte les violations."""
        if hard_only:
            return sum(1 for r in self.results if r.is_hard and not r.is_valid)
        return sum(1 for r in self.results if not r.is_valid)
    
    def display(self, verbose: bool = False):
        """Affiche le rapport de validation."""
        hard_violations = [r for r in self.results if r.is_hard and not r.is_valid]
        soft_violations = [r for r in self.results if not r.is_hard and not r.is_valid]
        
        # Résumé
        if self.is_valid():
            if not soft_violations:
                print_success("Solution valide - toutes les contraintes respectées")
            else:
                print_success(f"Solution valide ({len(soft_violations)} contraintes souples non optimales)")
        else:
            print_error(f"Solution invalide - {len(hard_violations)} contrainte(s) dure(s) violée(s)")
        
        # Détails des violations dures
        if hard_violations:
            print_subsection("Contraintes dures violées")
            by_category = {}
            for v in hard_violations:
                by_category.setdefault(v.category, []).append(v)
            
            for cat, violations in by_category.items():
                print_detail(f"{cat}: {len(violations)} violation(s)", 1)
                if verbose:
                    for v in violations[:3]:
                        print_detail(v.message, 2)
                    if len(violations) > 3:
                        print_detail(f"... et {len(violations) - 3} autres", 2)
        
        # Résumé des violations souples (sans détails sauf verbose)
        if soft_violations and verbose:
            print_subsection("Contraintes souples non optimales")
            by_category = {}
            for v in soft_violations:
                by_category.setdefault(v.category, []).append(v)
            
            for cat, violations in by_category.items():
                print_detail(f"{cat}: {len(violations)}", 1)


# === FONCTION POUR FORMATER LES STATISTIQUES FINALES ===

def format_solution_summary(
    scheduled: int,
    unscheduled: int,
    score: Optional[float] = None,
    slots_used: Optional[int] = None,
    slots_available: Optional[int] = None
) -> None:
    """Affiche un résumé de la solution."""
    total = scheduled + unscheduled
    rate = (scheduled / total * 100) if total > 0 else 0
    
    print_header("RÉSULTAT", "═")
    
    # Statut principal
    if unscheduled == 0:
        print_success(f"PLANIFICATION COMPLÈTE - {scheduled} matchs planifiés")
    elif scheduled == 0:
        print_error(f"ÉCHEC - Aucun match planifié sur {total}")
    else:
        print_warning(f"PLANIFICATION PARTIELLE - {scheduled}/{total} matchs ({rate:.0f}%)")
    
    # Détails
    print()
    print_key_value("Matchs planifiés", f"{scheduled}/{total} ({rate:.1f}%)")
    if unscheduled > 0:
        print_key_value("Matchs non planifiés", unscheduled)
    
    if slots_used is not None and slots_available is not None:
        usage = (slots_used / slots_available * 100) if slots_available > 0 else 0
        print_key_value("Créneaux utilisés", f"{slots_used}/{slots_available} ({usage:.0f}%)")
    
    if score is not None and score != float('inf'):
        print_key_value("Score d'optimisation", f"{score:,.0f}")
    
    print()
