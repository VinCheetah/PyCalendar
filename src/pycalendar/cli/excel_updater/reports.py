"""
Validation results and reports for Excel configuration.

Contains data structures for validation results and sheet reports.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum


class Severity(Enum):
    """Severity levels for validation issues."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    
    def __str__(self) -> str:
        return self.value
    
    @property
    def emoji(self) -> str:
        return {
            Severity.INFO: "ℹ️",
            Severity.WARNING: "⚠️",
            Severity.ERROR: "❌",
            Severity.CRITICAL: "🚫",
        }.get(self, "•")
    
    @property
    def color_code(self) -> str:
        """ANSI color code for terminal output."""
        return {
            Severity.INFO: "\033[94m",  # Blue
            Severity.WARNING: "\033[93m",  # Yellow
            Severity.ERROR: "\033[91m",  # Red
            Severity.CRITICAL: "\033[95m",  # Magenta
        }.get(self, "\033[0m")


@dataclass
class ValidationResult:
    """Résultat d'une validation de cellule."""
    valide: bool
    message: Optional[str] = None
    valeur_corrigee: Optional[Any] = None
    severite: Severity = Severity.INFO
    auto_correctable: bool = False  # Peut être corrigé automatiquement
    
    @classmethod
    def ok(cls, valeur_corrigee: Optional[Any] = None) -> 'ValidationResult':
        """Crée un résultat valide."""
        return cls(valide=True, valeur_corrigee=valeur_corrigee)
    
    @classmethod
    def error(cls, message: str, suggestion: Optional[Any] = None, 
              auto_correctable: bool = False) -> 'ValidationResult':
        """Crée un résultat d'erreur."""
        return cls(
            valide=False, 
            message=message, 
            valeur_corrigee=suggestion,
            severite=Severity.ERROR,
            auto_correctable=auto_correctable
        )
    
    @classmethod
    def warning(cls, message: str, suggestion: Optional[Any] = None,
                auto_correctable: bool = False) -> 'ValidationResult':
        """Crée un résultat d'avertissement."""
        return cls(
            valide=True,  # Warnings don't block
            message=message,
            valeur_corrigee=suggestion,
            severite=Severity.WARNING,
            auto_correctable=auto_correctable
        )


@dataclass
class CellIssue:
    """Représente un problème détecté dans une cellule."""
    ligne: int  # Numéro de ligne (1-indexed pour l'affichage)
    colonne: str
    message: str
    severite: Severity
    valeur_actuelle: Any = None
    valeur_suggeree: Optional[Any] = None
    auto_correctable: bool = False
    
    def __str__(self) -> str:
        prefix = f"Ligne {self.ligne}, '{self.colonne}'"
        if self.valeur_suggeree is not None:
            return f"{prefix}: {self.message} (suggestion: '{self.valeur_suggeree}')"
        return f"{prefix}: {self.message}"


@dataclass
class RapportFeuille:
    """Rapport de validation complet pour une feuille."""
    nom: str
    
    # Structure issues
    colonnes_manquantes: List[str] = field(default_factory=list)
    colonnes_ajoutees: List[str] = field(default_factory=list)
    colonnes_renommees: List[Tuple[str, str]] = field(default_factory=list)
    colonnes_extra: List[str] = field(default_factory=list)
    
    # Content issues (grouped by severity)
    issues: List[CellIssue] = field(default_factory=list)
    
    # Legacy compatibility
    erreurs_contenu: List[str] = field(default_factory=list)
    warnings_contenu: List[str] = field(default_factory=list)
    corrections_contenu: List[str] = field(default_factory=list)
    
    # Statistics
    nb_lignes_valides: int = 0
    nb_lignes_total: int = 0
    structure_modifiee: bool = False
    
    # Pending updates
    mises_a_jour_cellules: Dict[Any, Dict[str, Any]] = field(default_factory=dict)
    
    def add_issue(self, ligne: int, colonne: str, message: str, 
                  severite: Severity, valeur_actuelle: Any = None,
                  valeur_suggeree: Any = None, auto_correctable: bool = False):
        """Ajoute un problème détecté."""
        issue = CellIssue(
            ligne=ligne,
            colonne=colonne,
            message=message,
            severite=severite,
            valeur_actuelle=valeur_actuelle,
            valeur_suggeree=valeur_suggeree,
            auto_correctable=auto_correctable
        )
        self.issues.append(issue)
        
        # Legacy compatibility
        full_message = f"Ligne {ligne}, colonne '{colonne}': {message}"
        if severite == Severity.ERROR or severite == Severity.CRITICAL:
            self.erreurs_contenu.append(full_message)
        elif severite == Severity.WARNING:
            self.warnings_contenu.append(full_message)
    
    def add_correction(self, ligne: int, colonne: str, old_value: Any, new_value: Any):
        """Enregistre une correction à appliquer."""
        self.corrections_contenu.append(
            f"Ligne {ligne}, '{colonne}': '{old_value}' → '{new_value}'"
        )
    
    @property
    def nb_erreurs(self) -> int:
        return len([i for i in self.issues if i.severite in (Severity.ERROR, Severity.CRITICAL)])
    
    @property
    def nb_warnings(self) -> int:
        return len([i for i in self.issues if i.severite == Severity.WARNING])
    
    @property
    def nb_auto_correctable(self) -> int:
        return len([i for i in self.issues if i.auto_correctable])
    
    @property
    def has_problems(self) -> bool:
        return bool(self.issues) or self.structure_modifiee
    
    def get_issues_by_severity(self, severity: Severity) -> List[CellIssue]:
        """Retourne les issues filtrées par sévérité."""
        return [i for i in self.issues if i.severite == severity]
    
    def get_issues_by_column(self, column: str) -> List[CellIssue]:
        """Retourne les issues filtrées par colonne."""
        return [i for i in self.issues if i.colonne == column]


@dataclass 
class RapportGlobal:
    """Rapport global de validation pour tout le fichier."""
    fichier: str
    rapports_feuilles: Dict[str, RapportFeuille] = field(default_factory=dict)
    
    # Feuilles en trop/manquantes
    feuilles_extra: List[str] = field(default_factory=list)
    feuilles_manquantes: List[str] = field(default_factory=list)
    
    @property
    def total_erreurs(self) -> int:
        return sum(len(r.erreurs_contenu) for r in self.rapports_feuilles.values())
    
    @property
    def total_warnings(self) -> int:
        return sum(len(r.warnings_contenu) for r in self.rapports_feuilles.values())
    
    @property
    def total_corrections(self) -> int:
        return sum(len(r.corrections_contenu) for r in self.rapports_feuilles.values())
    
    @property
    def total_auto_correctable(self) -> int:
        return sum(r.nb_auto_correctable for r in self.rapports_feuilles.values())
    
    @property
    def est_valide(self) -> bool:
        """Retourne True si aucune erreur de contenu (les feuilles manquantes sont créées auto)."""
        return self.total_erreurs == 0
    
    def feuilles_avec_problemes(self) -> List[Tuple[str, RapportFeuille]]:
        """Retourne les feuilles ayant des problèmes."""
        return [
            (nom, rapport) for nom, rapport in self.rapports_feuilles.items()
            if rapport.has_problems
        ]
