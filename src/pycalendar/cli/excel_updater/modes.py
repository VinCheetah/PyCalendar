"""
Update modes for the Excel configuration updater.

Defines the different modes of operation:
- VALIDATE: Only validate, no modifications
- AUTO_CORRECT: Automatically apply all corrections
- INTERACTIVE: Prompt user for each correction
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional


class UpdateMode(Enum):
    """Mode de fonctionnement de l'actualisateur."""
    VALIDATE = auto()      # Validation seule, pas de modification
    AUTO_CORRECT = auto()  # Correction automatique de toutes les erreurs corrigeables
    INTERACTIVE = auto()   # Demande confirmation pour chaque correction


@dataclass
class UpdateOptions:
    """Options de configuration pour l'actualisation."""
    mode: UpdateMode = UpdateMode.VALIDATE
    verbose: bool = False
    format_output: bool = True  # Appliquer le formatage visuel
    add_dropdowns: bool = True  # Ajouter les listes déroulantes
    show_week_dates: bool = True  # Afficher les dates dans les semaines
    backup: bool = True  # Créer une sauvegarde avant modification
    max_errors_display: int = 50  # Nombre max d'erreurs à afficher
    yaml_config_path: Optional[str] = None  # Chemin explicite vers la config YAML
    
    @classmethod
    def validate_only(cls) -> 'UpdateOptions':
        """Mode validation seule."""
        return cls(mode=UpdateMode.VALIDATE, format_output=False, add_dropdowns=False)
    
    @classmethod
    def auto_correct(cls) -> 'UpdateOptions':
        """Mode correction automatique."""
        return cls(mode=UpdateMode.AUTO_CORRECT)
    
    @classmethod
    def interactive(cls) -> 'UpdateOptions':
        """Mode interactif."""
        return cls(mode=UpdateMode.INTERACTIVE)


def prompt_user_correction(message: str, current_value: str, suggested_value: str) -> Optional[str]:
    """
    Demande à l'utilisateur de confirmer ou modifier une correction.
    
    Args:
        message: Description de la correction
        current_value: Valeur actuelle
        suggested_value: Valeur suggérée
        
    Returns:
        La valeur choisie par l'utilisateur, ou None pour ignorer
    """
    print(f"\n┌─ Correction proposée ─────────────────────────────────────")
    print(f"│ {message}")
    print(f"│ Actuel:   '{current_value}'")
    print(f"│ Proposé:  '{suggested_value}'")
    print(f"└───────────────────────────────────────────────────────────")
    
    while True:
        choice = input("  [O]ui / [N]on / [M]odifier / [T]out accepter / [I]gnorer tout ? ").strip().lower()
        
        if choice in ('o', 'oui', 'y', 'yes', ''):
            return suggested_value
        elif choice in ('n', 'non', 'no'):
            return None
        elif choice in ('m', 'modifier', 'edit'):
            new_value = input("  Nouvelle valeur: ").strip()
            if new_value:
                return new_value
            print("  ⚠️  Valeur vide, réessayez.")
        elif choice in ('t', 'tout', 'all'):
            return '__ACCEPT_ALL__'
        elif choice in ('i', 'ignorer', 'ignore'):
            return '__IGNORE_ALL__'
        else:
            print("  ⚠️  Choix non reconnu. Utilisez O/N/M/T/I")
