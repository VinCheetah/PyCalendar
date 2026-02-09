"""
Display utilities for validation reports.

Provides formatted console output for validation results.
"""

from typing import Dict, List, Optional
from .reports import RapportFeuille, RapportGlobal, Severity, CellIssue


class Colors:
    """ANSI color codes for terminal output."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"


def print_header(title: str, emoji: str = "🔄"):
    """Affiche un en-tête stylisé."""
    width = 65
    print()
    print(f"┏{'━' * width}┓")
    print(f"┃{emoji}  {title.center(width - 4)}┃")
    print(f"┗{'━' * width}┛")
    print()


def print_section(title: str, icon: str = ""):
    """Affiche un titre de section."""
    if icon:
        print(f"\n  {icon} {title}")
    else:
        print(f"\n  {title}")
    print(f"  {'─' * 60}")


def print_step(step_num: int, total: int, description: str, status: str = ""):
    """Affiche une étape du processus."""
    if status:
        print(f"  [{step_num}/{total}] {description}... {status}")
    else:
        print(f"  [{step_num}/{total}] {description}...", end='', flush=True)


def print_step_result(result: str, count: Optional[int] = None):
    """Affiche le résultat d'une étape."""
    if count is not None:
        print(f" {result} ({count})")
    else:
        print(f" {result}")


def print_success(message: str):
    """Affiche un message de succès."""
    print(f"  {Colors.GREEN}✓{Colors.RESET} {message}")


def print_error(message: str):
    """Affiche un message d'erreur."""
    print(f"  {Colors.RED}✗{Colors.RESET} {message}")


def print_warning(message: str):
    """Affiche un message d'avertissement."""
    print(f"  {Colors.YELLOW}⚠{Colors.RESET} {message}")


def print_info(message: str):
    """Affiche un message d'information."""
    print(f"  {Colors.BLUE}ℹ{Colors.RESET} {message}")


def format_issue(issue: CellIssue, show_suggestion: bool = True) -> str:
    """Formate un problème pour l'affichage."""
    prefix = f"L{issue.ligne}, '{issue.colonne}'"
    msg = f"{prefix}: {issue.message}"
    
    if show_suggestion and issue.valeur_suggeree is not None:
        msg += f" → suggestion: '{issue.valeur_suggeree}'"
    
    return msg


def print_issues_grouped(issues: List[CellIssue], max_display: int = 20):
    """Affiche les problèmes groupés par sévérité."""
    if not issues:
        return
    
    # Group by severity
    by_severity: Dict[Severity, List[CellIssue]] = {}
    for issue in issues:
        if issue.severite not in by_severity:
            by_severity[issue.severite] = []
        by_severity[issue.severite].append(issue)
    
    # Display in order: CRITICAL, ERROR, WARNING, INFO
    for severity in [Severity.CRITICAL, Severity.ERROR, Severity.WARNING, Severity.INFO]:
        if severity not in by_severity:
            continue
        
        severity_issues = by_severity[severity]
        count = len(severity_issues)
        
        color = {
            Severity.CRITICAL: Colors.MAGENTA,
            Severity.ERROR: Colors.RED,
            Severity.WARNING: Colors.YELLOW,
            Severity.INFO: Colors.BLUE,
        }.get(severity, Colors.RESET)
        
        print(f"\n     {color}{severity.emoji} {count} {severity.value}(s):{Colors.RESET}")
        
        displayed = 0
        for issue in severity_issues[:max_display]:
            auto_tag = " [auto]" if issue.auto_correctable else ""
            print(f"        • {format_issue(issue)}{auto_tag}")
            displayed += 1
        
        if count > max_display:
            print(f"        ... et {count - max_display} autre(s)")


def print_sheet_report(nom: str, rapport: RapportFeuille, verbose: bool = False):
    """Affiche le rapport d'une feuille."""
    if not rapport.has_problems and not verbose:
        return
    
    # Header
    status_icon = "❌" if rapport.nb_erreurs > 0 else ("⚠️" if rapport.nb_warnings > 0 else "✓")
    print(f"\n  📄 {nom} {status_icon}")
    
    # Structure changes
    if rapport.structure_modifiee:
        if rapport.colonnes_manquantes:
            print(f"     + {len(rapport.colonnes_manquantes)} colonnes ajoutées: {', '.join(rapport.colonnes_manquantes)}")
        if rapport.colonnes_renommees:
            for old, new in rapport.colonnes_renommees:
                print(f"     ~ Renommée: '{old}' → '{new}'")
        if rapport.colonnes_extra:
            print(f"     ? {len(rapport.colonnes_extra)} colonnes extra: {', '.join(rapport.colonnes_extra)}")
    
    # Content issues
    if rapport.issues:
        print_issues_grouped(rapport.issues, max_display=10 if not verbose else 50)
    
    # Legacy format fallback
    elif rapport.erreurs_contenu or rapport.warnings_contenu:
        if rapport.erreurs_contenu:
            print(f"     {Colors.RED}❌ {len(rapport.erreurs_contenu)} erreur(s):{Colors.RESET}")
            for err in rapport.erreurs_contenu[:10]:
                print(f"        • {err}")
            if len(rapport.erreurs_contenu) > 10:
                print(f"        ... et {len(rapport.erreurs_contenu) - 10} autre(s)")
        
        if rapport.warnings_contenu:
            print(f"     {Colors.YELLOW}⚠️ {len(rapport.warnings_contenu)} avertissement(s):{Colors.RESET}")
            for warn in rapport.warnings_contenu[:10]:
                print(f"        • {warn}")
            if len(rapport.warnings_contenu) > 10:
                print(f"        ... et {len(rapport.warnings_contenu) - 10} autre(s)")
    
    # Corrections
    if rapport.corrections_contenu and verbose:
        print(f"     {Colors.GREEN}🔧 {len(rapport.corrections_contenu)} correction(s) appliquée(s){Colors.RESET}")


def print_global_report(rapport: RapportGlobal, verbose: bool = False):
    """Affiche le rapport global."""
    total_err = rapport.total_erreurs
    total_warn = rapport.total_warnings
    total_auto = rapport.total_auto_correctable
    
    # Summary box
    if total_err == 0 and total_warn == 0:
        print("\n  ╔═══════════════════════════════════════════════════════════╗")
        print("  ║                  ✅ VALIDATION RÉUSSIE                    ║")
        print("  ╚═══════════════════════════════════════════════════════════╝")
        print(f"\n  📊 {len(rapport.rapports_feuilles)} feuille(s) validée(s) • Aucun problème détecté")
        print("  🎉 Le fichier est prêt à l'emploi !\n")
    else:
        print("\n  ╔═══════════════════════════════════════════════════════════╗")
        if total_err > 0:
            print("  ║              ⚠️  VALIDATION AVEC PROBLÈMES                 ║")
        else:
            print("  ║            ℹ️  VALIDATION AVEC AVERTISSEMENTS              ║")
        print("  ╚═══════════════════════════════════════════════════════════╝")
        
        print(f"\n  📊 Résumé : {len(rapport.rapports_feuilles)} feuille(s)")
        print(f"     • {Colors.RED}{total_err} erreur(s){Colors.RESET}")
        print(f"     • {Colors.YELLOW}{total_warn} avertissement(s){Colors.RESET}")
        
        if total_auto > 0:
            print(f"     • {Colors.GREEN}{total_auto} correction(s) automatique(s) possible(s){Colors.RESET}")
        
        # Show extra/missing sheets
        if rapport.feuilles_manquantes:
            print(f"\n  {Colors.RED}📁 Feuilles manquantes:{Colors.RESET}")
            for feuille in rapport.feuilles_manquantes:
                print(f"     • {feuille}")
        
        if rapport.feuilles_extra:
            print(f"\n  {Colors.YELLOW}📁 Feuilles non utilisées/en trop:{Colors.RESET}")
            for feuille in rapport.feuilles_extra:
                print(f"     • {feuille} (peut être supprimée ou ignorée)")
        
        # Detailed reports per sheet
        feuilles_problemes = rapport.feuilles_avec_problemes()
        if feuilles_problemes:
            print("\n  ┌───────────────────────────────────────────────────────────┐")
            print("  │                 DÉTAILS DES PROBLÈMES                     │")
            print("  └───────────────────────────────────────────────────────────┘")
            
            for nom, sheet_rapport in feuilles_problemes:
                print_sheet_report(nom, sheet_rapport, verbose)
        
        # Final message
        print("\n  " + "─" * 60)
        if total_err > 0:
            print("  ⛔ Corrigez les erreurs avant d'utiliser le fichier")
            if total_auto > 0:
                print(f"  💡 Utilisez --auto-correct pour corriger {total_auto} problème(s) automatiquement")
        else:
            print("  ✓ Le fichier est utilisable (vérifiez les avertissements)")
        print()


def print_correction_summary(corrections: List[str], applied: bool = True):
    """Affiche un résumé des corrections."""
    if not corrections:
        return
    
    action = "appliquée(s)" if applied else "proposée(s)"
    print(f"\n  🔧 {len(corrections)} correction(s) {action}:")
    
    for corr in corrections[:20]:
        print(f"     • {corr}")
    
    if len(corrections) > 20:
        print(f"     ... et {len(corrections) - 20} autre(s)")


def print_mode_info(mode_name: str, description: str):
    """Affiche les informations sur le mode actif."""
    print(f"\n  📋 Mode: {Colors.CYAN}{mode_name}{Colors.RESET}")
    print(f"     {description}")
