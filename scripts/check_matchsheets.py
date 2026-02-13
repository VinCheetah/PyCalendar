#!/usr/bin/env python3
"""
Vérification des feuilles de match MySportU.

Ce script permet de :
- Se connecter à l'API MySportU (via le module pycalendar.mysportu)
- Récupérer les matchs d'une date spécifique
- Analyser l'état de complétion des feuilles de match
- Afficher un rapport détaillé (Rich) sur la préparation des matchs
- Exporter en CSV ou PDF

L'analyse inclut pour chaque match :
- Nombre de joueurs inscrits par équipe
- Validation des effectifs (joueurs et staffs)
- Présence d'arbitre(s)
- Statut global "prêt à jouer"

Par défaut, les matchs reportés, forfaits et terminés sont exclus.

Usage:
    # Matchs du jour
    python check_matchsheets.py

    # Date spécifique
    python check_matchsheets.py --date 05/02/2026

    # Filtrer par sport
    python check_matchsheets.py --date 05/02/2026 --sport volley

    # Filtrer par compétition (recherche partielle)
    python check_matchsheets.py --competition "LYON VBF PH2"

    # Détails des matchs non prêts
    python check_matchsheets.py --verbose

    # Vue par institution
    python check_matchsheets.py --by-team

    # Liens vers les feuilles de match
    python check_matchsheets.py --links

    # Inclure reportés/forfaits/terminés
    python check_matchsheets.py --include-cancelled

    # Exporter en CSV / PDF
    python check_matchsheets.py --export rapport.csv
    python check_matchsheets.py --pdf rapport.pdf --by-team
"""

from __future__ import annotations

import sys
import argparse
import re
from datetime import datetime
from dataclasses import dataclass, field
from collections import defaultdict

# Rich — dépendance du projet
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.rule import Rule

# Module MySportU (pycalendar.mysportu)
from pycalendar.mysportu import (
    MySportU,
    MatchInfo,
    MatchDetail,
    MatchState,
)

# Optionnel : pandas (CSV), reportlab (PDF)
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate, Table as PDFTable, TableStyle,
        Paragraph, Spacer,
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False


console = Console()

# ═══════════════════════════════════════════════════════════════════════════
# CONSTANTES
# ═══════════════════════════════════════════════════════════════════════════

BASE_URL = "https://gestion.mysportu.com"
MATCHSHEET_URL = f"{BASE_URL}/feuille-de-match/rencontre"

SPORT_KEYWORDS: dict[str, list[str]] = {
    "volley": ["VB", "VOLLEY"],
    "hand":   ["HB", "HAND"],
    "basket": ["BB", "BASKET"],
    "foot":   ["FB", "FOOT"],
    "rugby":  ["RG", "RUGBY"],
}


# ═══════════════════════════════════════════════════════════════════════════
# UTILITAIRES
# ═══════════════════════════════════════════════════════════════════════════

def extraire_institution(nom_equipe: str) -> str:
    """Extrait l'institution du nom de l'équipe.

    Exemples :
        'LYON 1 (4)'       → 'LYON 1'
        'LYON 2 (IEP) (4)' → 'LYON 2 (IEP)'
        'ENTPE (1)'         → 'ENTPE'
    """
    m = re.match(r"^(.+?)\s*\(\d+\)$", nom_equipe)
    return m.group(1).strip() if m else nom_equipe


def extract_genre_from_competition(competition: str) -> str:
    """Extrait le genre (M/F) depuis le nom de la compétition."""
    upper = competition.upper()
    if re.search(r"VBF|HBF|BBF|FBF|DAMES|FEM|FÉMININ|FEMININE", upper):
        return "F"
    if re.search(r"VBM|HBM|BBM|FBM|MESSIEURS|MASC|MASCULIN", upper):
        return "M"
    return "?"


# ═══════════════════════════════════════════════════════════════════════════
# MODÈLES LOCAUX (wrappers autour des modèles du module)
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class TeamStatus:
    """État d'une équipe pour un match."""
    id: int
    nom: str
    institution: str = ""
    joueurs_inscrits: int = 0
    joueurs_min: int = 6
    joueurs_valide: bool = False
    staffs_inscrits: int = 0
    staffs_valide: bool = False

    def __post_init__(self) -> None:
        if not self.institution:
            self.institution = extraire_institution(self.nom)

    @property
    def joueurs_ok(self) -> bool:
        return self.joueurs_inscrits >= self.joueurs_min

    @property
    def pret(self) -> bool:
        return self.joueurs_ok and self.joueurs_valide

    def status_str(self) -> str:
        j = f"J:{self.joueurs_inscrits}/{self.joueurs_min}"
        j += "✓" if self.joueurs_valide else "✗"
        s = f" S:{self.staffs_inscrits}"
        s += "✓" if self.staffs_valide else "✗"
        return j + s


@dataclass
class MatchStatus:
    """État complet d'un match."""
    id: int
    date: str
    heure: str
    competition: str
    lieu: str
    receveur: TeamStatus
    visiteur: TeamStatus
    arbitres: list[str] = field(default_factory=list)
    state: MatchState = MatchState.NON_JOUE
    forfait: bool = False
    clos: bool = False
    genre: str = "?"

    @property
    def is_cancelled(self) -> bool:
        return self.state.is_cancelled

    @property
    def pret(self) -> bool:
        if self.is_cancelled:
            return False
        return self.receveur.pret and self.visiteur.pret and len(self.arbitres) > 0

    @property
    def statut_emoji(self) -> str:
        if self.state == MatchState.REPORTE:
            return "📅"
        if self.state in (MatchState.FORFAIT, MatchState.ANNULE):
            return "🚫"
        if self.state == MatchState.TERMINE:
            return "✅"
        return "✅" if self.pret else "❌"

    @property
    def url(self) -> str:
        return f"{MATCHSHEET_URL}/{self.id}"

    @classmethod
    def from_detail(cls, detail: MatchDetail, info: MatchInfo) -> "MatchStatus":
        """Construit un MatchStatus depuis un MatchDetail + MatchInfo."""
        val_rec = next(
            (v for v in detail.validations if v.equipe_id == detail.receveur.id), None
        )
        val_vis = next(
            (v for v in detail.validations if v.equipe_id == detail.visiteur.id), None
        )

        receveur = TeamStatus(
            id=detail.receveur.id,
            nom=detail.receveur.libelle_court or detail.receveur.libelle,
            joueurs_inscrits=len(detail.joueurs_receveur),
            joueurs_min=detail.regles.nb_joueurs_min,
            joueurs_valide=val_rec.joueurs_valide if val_rec else False,
            staffs_inscrits=len(detail.staffs_receveur),
            staffs_valide=val_rec.staffs_valide if val_rec else False,
        )
        visiteur = TeamStatus(
            id=detail.visiteur.id,
            nom=detail.visiteur.libelle_court or detail.visiteur.libelle,
            joueurs_inscrits=len(detail.joueurs_visiteur),
            joueurs_min=detail.regles.nb_joueurs_min,
            joueurs_valide=val_vis.joueurs_valide if val_vis else False,
            staffs_inscrits=len(detail.staffs_visiteur),
            staffs_valide=val_vis.staffs_valide if val_vis else False,
        )

        return cls(
            id=detail.id,
            date=info.date,
            heure=info.heure,
            competition=info.competition_libelle,
            lieu=info.lieu.libelle if info.lieu else "N/A",
            receveur=receveur,
            visiteur=visiteur,
            arbitres=[o.nom_complet for o in detail.officiels],
            state=detail.state,
            forfait=detail.state == MatchState.FORFAIT,
            clos=info.clos,
            genre=info.genre or extract_genre_from_competition(info.competition_libelle),
        )


@dataclass
class TeamStats:
    """Statistiques agrégées pour une équipe."""
    nom: str
    institution: str
    matchs_total: int = 0
    matchs_prets: int = 0
    joueurs_valides: int = 0
    staffs_valides: int = 0

    @property
    def taux_completion(self) -> float:
        if self.matchs_total == 0:
            return 0.0
        return (self.matchs_prets / self.matchs_total) * 100


@dataclass
class TeamMatchInfo:
    """Information d'un match pour une équipe spécifique (vue par-team)."""
    match_id: int
    heure: str
    equipe: str
    adversaire: str
    is_home: bool
    joueurs: int
    joueurs_min: int
    joueurs_valide: bool
    staffs: int
    staffs_valide: bool
    arbitres: int
    url: str
    genre: str = "?"
    adv_joueurs: int = 0
    adv_joueurs_min: int = 6
    adv_joueurs_valide: bool = False
    adv_staffs: int = 0
    adv_staffs_valide: bool = False

    @property
    def pret(self) -> bool:
        return self.joueurs >= self.joueurs_min and self.joueurs_valide and self.staffs_valide

    @property
    def adv_pret(self) -> bool:
        return (
            self.adv_joueurs >= self.adv_joueurs_min
            and self.adv_joueurs_valide
            and self.adv_staffs_valide
        )


# ═══════════════════════════════════════════════════════════════════════════
# FILTRAGE & ANALYSE
# ═══════════════════════════════════════════════════════════════════════════

def filter_matches(
    matches: list[MatchInfo],
    *,
    date_filter: str | None = None,
    sport_filter: str | None = None,
    competition_filter: str | None = None,
    include_cancelled: bool = False,
) -> list[MatchInfo]:
    """Filtre les MatchInfo selon les critères."""
    filtered = list(matches)

    if date_filter:
        filtered = [m for m in filtered if m.date == date_filter]

    if sport_filter:
        key = sport_filter.lower()
        if key in SPORT_KEYWORDS:
            keywords = [kw.upper() for kw in SPORT_KEYWORDS[key]]
            filtered = [
                m for m in filtered
                if any(kw in m.competition_libelle.upper() for kw in keywords)
            ]

    if competition_filter:
        pattern = competition_filter.upper()
        filtered = [m for m in filtered if pattern in m.competition_libelle.upper()]

    if not include_cancelled:
        filtered = [m for m in filtered if not m.state.is_cancelled]

    return filtered


def analyze_matches(msu: MySportU, matches: list[MatchInfo]) -> list[MatchStatus]:
    """Charge les détails et convertit en MatchStatus."""
    match_ids = [m.id for m in matches]
    details = msu.get_matches_details(match_ids)
    detail_map = {d.id: d for d in details}

    results: list[MatchStatus] = []
    for info in matches:
        detail = detail_map.get(info.id)
        if detail:
            results.append(MatchStatus.from_detail(detail, info))
    return results


def organize_matches_by_team(
    results: list[MatchStatus],
) -> dict[str, dict[str, list[TeamMatchInfo]]]:
    """Organise les matchs par institution puis par équipe."""
    by_institution: dict[str, dict[str, list[TeamMatchInfo]]] = defaultdict(
        lambda: defaultdict(list)
    )

    for r in results:
        if r.is_cancelled:
            continue

        # Receveur
        rec = TeamMatchInfo(
            match_id=r.id, heure=r.heure,
            equipe=r.receveur.nom, adversaire=r.visiteur.nom, is_home=True,
            joueurs=r.receveur.joueurs_inscrits, joueurs_min=r.receveur.joueurs_min,
            joueurs_valide=r.receveur.joueurs_valide,
            staffs=r.receveur.staffs_inscrits, staffs_valide=r.receveur.staffs_valide,
            arbitres=len(r.arbitres), url=r.url, genre=r.genre,
            adv_joueurs=r.visiteur.joueurs_inscrits, adv_joueurs_min=r.visiteur.joueurs_min,
            adv_joueurs_valide=r.visiteur.joueurs_valide,
            adv_staffs=r.visiteur.staffs_inscrits, adv_staffs_valide=r.visiteur.staffs_valide,
        )
        by_institution[r.receveur.institution][r.receveur.nom].append(rec)

        # Visiteur
        vis = TeamMatchInfo(
            match_id=r.id, heure=r.heure,
            equipe=r.visiteur.nom, adversaire=r.receveur.nom, is_home=False,
            joueurs=r.visiteur.joueurs_inscrits, joueurs_min=r.visiteur.joueurs_min,
            joueurs_valide=r.visiteur.joueurs_valide,
            staffs=r.visiteur.staffs_inscrits, staffs_valide=r.visiteur.staffs_valide,
            arbitres=len(r.arbitres), url=r.url, genre=r.genre,
            adv_joueurs=r.receveur.joueurs_inscrits, adv_joueurs_min=r.receveur.joueurs_min,
            adv_joueurs_valide=r.receveur.joueurs_valide,
            adv_staffs=r.receveur.staffs_inscrits, adv_staffs_valide=r.receveur.staffs_valide,
        )
        by_institution[r.visiteur.institution][r.visiteur.nom].append(vis)

    return dict(by_institution)


# ═══════════════════════════════════════════════════════════════════════════
# AFFICHAGE RICH
# ═══════════════════════════════════════════════════════════════════════════

def print_report(
    results: list[MatchStatus],
    verbose: bool = False,
    show_links: bool = False,
) -> None:
    """Affiche le rapport des feuilles de match."""
    active = [r for r in results if not r.is_cancelled]
    cancelled = [r for r in results if r.is_cancelled]

    total = len(active)
    prets = sum(1 for r in active if r.pret)
    non_prets = total - prets

    # Résumé
    summary = (
        f"[bold green]{prets}[/] prêts / [bold red]{non_prets}[/] non prêts "
        f"sur [bold]{total}[/] matchs"
    )
    if cancelled:
        summary += f"\n[dim]({len(cancelled)} matchs reportés/forfaits exclus)[/]"
    console.print(Panel(summary, title="📋 Résumé", border_style="blue"))

    # Tableau
    table = Table(
        title="État des feuilles de match",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("ID", style="dim")
    table.add_column("Heure")
    table.add_column("Receveur")
    table.add_column("Rec. Status")
    table.add_column("Visiteur")
    table.add_column("Vis. Status")
    table.add_column("Arbitre")
    table.add_column("Prêt", justify="center")
    if show_links:
        table.add_column("Lien")

    for r in active:
        rec_style = "green" if r.receveur.pret else "red"
        vis_style = "green" if r.visiteur.pret else "red"
        arb_str = f"{len(r.arbitres)} arb."
        arb_style = "green" if r.arbitres else "red"

        row: list[str | Text] = [
            str(r.id),
            r.heure,
            r.receveur.nom[:15],
            f"[{rec_style}]{r.receveur.status_str()}[/]",
            r.visiteur.nom[:15],
            f"[{vis_style}]{r.visiteur.status_str()}[/]",
            f"[{arb_style}]{arb_str}[/]",
            r.statut_emoji,
        ]
        if show_links:
            row.append(f"[link={r.url}]🔗[/link]")

        table.add_row(*row)

    console.print(table)

    # Détails des matchs non prêts
    if verbose:
        console.print("\n[bold]Détails des matchs non prêts :[/]")
        for r in active:
            if r.pret:
                continue

            console.print(f"\n[bold]{r.id}[/]: {r.receveur.nom} vs {r.visiteur.nom}")
            console.print(f"  Compétition : {r.competition}")
            console.print(f"  Lieu : {r.lieu}")
            if show_links:
                console.print(f"  Lien : {r.url}")

            if not r.receveur.joueurs_ok:
                console.print(
                    f"  ❌ {r.receveur.nom}: {r.receveur.joueurs_inscrits}/"
                    f"{r.receveur.joueurs_min} joueurs"
                )
            if not r.receveur.joueurs_valide:
                console.print(f"  ❌ {r.receveur.nom}: effectif non validé")
            if not r.visiteur.joueurs_ok:
                console.print(
                    f"  ❌ {r.visiteur.nom}: {r.visiteur.joueurs_inscrits}/"
                    f"{r.visiteur.joueurs_min} joueurs"
                )
            if not r.visiteur.joueurs_valide:
                console.print(f"  ❌ {r.visiteur.nom}: effectif non validé")
            if not r.arbitres:
                console.print("  ❌ Pas d'arbitre assigné")


def print_report_by_team(
    results: list[MatchStatus],
    show_links: bool = False,
) -> None:
    """Affiche le rapport par équipe / institution."""
    by_institution = organize_matches_by_team(results)

    # Stats par institution
    inst_stats: dict[str, tuple[int, int]] = {}
    for inst, teams in by_institution.items():
        total = sum(len(ms) for ms in teams.values())
        prets = sum(1 for ms in teams.values() for m in ms if m.pret)
        inst_stats[inst] = (total, prets)

    sorted_insts = sorted(inst_stats)
    total_matchs = sum(s[0] for s in inst_stats.values())
    total_prets = sum(s[1] for s in inst_stats.values())

    # Résumé
    summary = (
        f"[bold]{len(inst_stats)}[/] institutions | "
        f"[bold green]{total_prets}[/] matchs prêts / [bold]{total_matchs}[/] total"
    )
    console.print(Panel(summary, title="📊 État par équipe", border_style="blue"))

    for inst in sorted_insts:
        teams = by_institution[inst]
        inst_total, inst_prets = inst_stats[inst]
        taux = (inst_prets / inst_total * 100) if inst_total > 0 else 0

        color = "green" if taux >= 80 else ("yellow" if taux >= 50 else "red")

        console.print()
        console.print(Rule(
            f"[bold]{inst}[/bold] [dim]—[/dim] [{color}]{taux:.0f}%[/{color}] "
            f"[dim]({inst_prets}/{inst_total})[/dim]",
            style="blue",
        ))

        table = Table(
            show_header=True, header_style="bold cyan",
            border_style="dim", box=None, pad_edge=False, show_edge=False,
        )
        table.add_column("Heure", style="dim", width=6, justify="center")
        table.add_column("Genre", width=3, justify="center")
        table.add_column("Équipe", width=18)
        table.add_column("Adversaire", width=18)
        table.add_column("Joueurs", width=10, justify="center")
        table.add_column("Staff", width=8, justify="center")
        table.add_column("OK", width=3, justify="center")
        if show_links:
            table.add_column("", width=3)

        for team_name in sorted(teams):
            for m in sorted(teams[team_name], key=lambda x: x.heure):
                j_ok = m.joueurs >= m.joueurs_min
                j_color = "green" if j_ok and m.joueurs_valide else ("yellow" if j_ok else "red")
                s_color = "green" if m.staffs_valide else ("yellow" if m.staffs > 0 else "red")
                adv_color = "green" if m.adv_pret else "red"

                joueurs_str = Text()
                joueurs_str.append(f"{m.joueurs}/{m.joueurs_min}", style=j_color)
                joueurs_str.append(" ✓" if m.joueurs_valide else " ✗",
                                   style="green" if m.joueurs_valide else "red")

                staff_str = Text()
                staff_str.append(f"{m.staffs}", style=s_color)
                staff_str.append(" ✓" if m.staffs_valide else " ✗",
                                 style="green" if m.staffs_valide else "red")

                genre_style = "magenta" if m.genre == "F" else (
                    "blue" if m.genre == "M" else "dim"
                )

                row: list[str | Text] = [
                    m.heure,
                    Text(m.genre, style=genre_style),
                    Text(team_name[:17], style="bold"),
                    Text(m.adversaire[:17], style=adv_color),
                    joueurs_str,
                    staff_str,
                    "✅" if m.pret else "❌",
                ]
                if show_links:
                    row.append(f"[link={m.url}]🔗[/link]")

                table.add_row(*row)

        console.print(table)


# ═══════════════════════════════════════════════════════════════════════════
# EXPORT CSV
# ═══════════════════════════════════════════════════════════════════════════

def export_to_csv(
    results: list[MatchStatus],
    filepath: str,
    include_links: bool = False,
) -> None:
    """Exporte les résultats en CSV."""
    if not HAS_PANDAS:
        console.print("[red]pandas requis pour l'export CSV : pip install pandas[/]")
        return

    data = []
    for r in results:
        row: dict = {
            "ID": r.id,
            "Date": r.date,
            "Heure": r.heure,
            "Competition": r.competition,
            "Lieu": r.lieu,
            "Etat": r.state.label,
            "Forfait": r.forfait,
            "Receveur": r.receveur.nom,
            "Rec_Institution": r.receveur.institution,
            "Rec_Joueurs": r.receveur.joueurs_inscrits,
            "Rec_Min": r.receveur.joueurs_min,
            "Rec_Valide": r.receveur.joueurs_valide,
            "Rec_Staffs": r.receveur.staffs_inscrits,
            "Rec_Pret": r.receveur.pret,
            "Visiteur": r.visiteur.nom,
            "Vis_Institution": r.visiteur.institution,
            "Vis_Joueurs": r.visiteur.joueurs_inscrits,
            "Vis_Min": r.visiteur.joueurs_min,
            "Vis_Valide": r.visiteur.joueurs_valide,
            "Vis_Staffs": r.visiteur.staffs_inscrits,
            "Vis_Pret": r.visiteur.pret,
            "Nb_Arbitres": len(r.arbitres),
            "Arbitres": ", ".join(r.arbitres),
            "Pret": r.pret,
        }
        if include_links:
            row["Lien"] = r.url
        data.append(row)

    df = pd.DataFrame(data)
    df.to_csv(filepath, index=False, encoding="utf-8-sig")
    console.print(f"[green]✅ Export CSV : {filepath}[/]")


# ═══════════════════════════════════════════════════════════════════════════
# EXPORT PDF
# ═══════════════════════════════════════════════════════════════════════════

def export_to_pdf(
    results: list[MatchStatus],
    filepath: str,
    date_str: str = "",
    competition_str: str = "",
    by_team: bool = False,
    include_links: bool = False,
) -> None:
    """Exporte les résultats en PDF avec un design professionnel."""
    if not HAS_REPORTLAB:
        console.print("[red]reportlab requis pour l'export PDF : pip install reportlab[/]")
        return

    doc = SimpleDocTemplate(
        filepath,
        pagesize=landscape(A4),
        rightMargin=1 * cm, leftMargin=1 * cm,
        topMargin=1.5 * cm, bottomMargin=1 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle", parent=styles["Heading1"],
        fontSize=18, textColor=colors.HexColor("#1a365d"),
        spaceAfter=20, alignment=TA_CENTER,
    )
    subtitle_style = ParagraphStyle(
        "CustomSubtitle", parent=styles["Normal"],
        fontSize=11, textColor=colors.HexColor("#4a5568"),
        spaceAfter=15, alignment=TA_CENTER,
    )
    inst_header_style = ParagraphStyle(
        "InstHeader", parent=styles["Heading2"],
        fontSize=13, textColor=colors.white,
        spaceBefore=15, spaceAfter=5, alignment=TA_LEFT,
        backColor=colors.HexColor("#2b6cb0"),
        borderPadding=(5, 10, 5, 10),
    )
    footer_style = ParagraphStyle(
        "Footer", parent=styles["Normal"],
        fontSize=8, textColor=colors.HexColor("#718096"),
        alignment=TA_CENTER,
    )

    # Couleurs
    color_ok = colors.HexColor("#48bb78")
    color_warning = colors.HexColor("#ed8936")
    color_error = colors.HexColor("#f56565")
    color_header = colors.HexColor("#2b6cb0")
    color_header_text = colors.white
    color_row_alt = colors.HexColor("#f7fafc")

    elements: list = []

    # Titre
    elements.append(Paragraph("📋 État des Feuilles de Match", title_style))

    subtitle_parts = []
    if date_str:
        subtitle_parts.append(f"Date : {date_str}")
    if competition_str:
        subtitle_parts.append(f"Compétition : {competition_str}")
    if subtitle_parts:
        elements.append(Paragraph(" | ".join(subtitle_parts), subtitle_style))

    # Stats
    active = [r for r in results if not r.is_cancelled]
    total = len(active)
    prets = sum(1 for r in active if r.pret)
    taux = (prets / total * 100) if total > 0 else 0

    stats_style = ParagraphStyle(
        "Stats", parent=styles["Normal"],
        fontSize=11, textColor=colors.HexColor("#2d3748"),
        spaceAfter=20, alignment=TA_CENTER,
    )
    elements.append(Paragraph(
        f"<b>{prets}</b> matchs prêts sur <b>{total}</b> — "
        f"Taux de complétion : <b>{taux:.0f}%</b>",
        stats_style,
    ))
    elements.append(Spacer(1, 10))

    if by_team:
        # ─── Export par équipe ────────────────────────────────
        by_institution = organize_matches_by_team(results)

        for inst in sorted(by_institution):
            teams = by_institution[inst]
            inst_total = sum(len(ms) for ms in teams.values())
            inst_prets = sum(1 for ms in teams.values() for m in ms if m.pret)
            inst_taux = (inst_prets / inst_total * 100) if inst_total > 0 else 0

            elements.append(Paragraph(
                f"<b>{inst}</b> — {inst_taux:.0f}% ({inst_prets}/{inst_total} prêts)",
                inst_header_style,
            ))

            if include_links:
                headers = ["Heure", "Genre", "Équipe", "Adversaire",
                           "Joueurs", "Staff", "", "Lien"]
                col_widths = [1.5*cm, 1.2*cm, 4.5*cm, 4.5*cm,
                              2.5*cm, 2*cm, 1*cm, 6*cm]
            else:
                headers = ["Heure", "Genre", "Équipe", "Adversaire",
                           "Joueurs", "Staff", ""]
                col_widths = [1.5*cm, 1.2*cm, 5*cm, 5*cm,
                              2.5*cm, 2*cm, 1*cm]

            table_data = [headers]
            row_meta: list[dict] = []

            for team_name in sorted(teams):
                for m in sorted(teams[team_name], key=lambda x: x.heure):
                    j_ok = m.joueurs >= m.joueurs_min
                    j_str = f"{m.joueurs}/{m.joueurs_min} {'✓' if m.joueurs_valide else '✗'}"
                    s_str = f"{m.staffs} {'✓' if m.staffs_valide else '✗'}"
                    status = "✓" if m.pret else "✗"

                    row = [m.heure, m.genre, team_name[:20],
                           m.adversaire[:20], j_str, s_str, status]
                    if include_links:
                        url = m.url
                        row.append(url[:40] + "..." if len(url) > 40 else url)

                    table_data.append(row)
                    row_meta.append({
                        "joueurs_valide": m.joueurs_valide,
                        "joueurs_ok": j_ok,
                        "staffs": m.staffs,
                        "staffs_valide": m.staffs_valide,
                        "pret": m.pret,
                        "adv_pret": m.adv_pret,
                    })

            pdf_table = PDFTable(table_data, colWidths=col_widths)
            cmds = _pdf_base_style(color_header, color_header_text, color_row_alt,
                                   len(table_data))
            for i, meta in enumerate(row_meta, start=1):
                _pdf_team_row_colors(cmds, i, meta, color_ok, color_warning, color_error)

            pdf_table.setStyle(TableStyle(cmds))
            elements.append(pdf_table)
            elements.append(Spacer(1, 15))
    else:
        # ─── Export standard ──────────────────────────────────
        if include_links:
            headers = ["ID", "Heure", "Receveur", "Statut Rec.",
                       "Visiteur", "Statut Vis.", "Arb.", "", "Lien"]
            col_widths = [1.2*cm, 1.3*cm, 3.5*cm, 2.8*cm,
                          3.5*cm, 2.8*cm, 1*cm, 0.8*cm, 5*cm]
        else:
            headers = ["ID", "Heure", "Receveur", "Statut Rec.",
                       "Visiteur", "Statut Vis.", "Arb.", ""]
            col_widths = [1.5*cm, 1.5*cm, 4*cm, 3.5*cm,
                          4*cm, 3.5*cm, 1.2*cm, 1*cm]

        table_data = [headers]
        for r in active:
            rec_s = r.receveur.status_str()
            vis_s = r.visiteur.status_str()
            status = "✓" if r.pret else "✗"

            row = [str(r.id), r.heure, r.receveur.nom[:16], rec_s,
                   r.visiteur.nom[:16], vis_s, str(len(r.arbitres)), status]
            if include_links:
                url = r.url
                row.append(url[:35] + "..." if len(url) > 35 else url)
            table_data.append(row)

        pdf_table = PDFTable(table_data, colWidths=col_widths)
        cmds = _pdf_base_style(color_header, color_header_text, color_row_alt,
                               len(table_data))

        for i in range(1, len(table_data)):
            status_col = 7
            if table_data[i][status_col] == "✓":
                cmds.append(("TEXTCOLOR", (status_col, i), (status_col, i), color_ok))
            else:
                cmds.append(("TEXTCOLOR", (status_col, i), (status_col, i), color_error))
            cmds.append(("FONTNAME", (status_col, i), (status_col, i), "Helvetica-Bold"))

        pdf_table.setStyle(TableStyle(cmds))
        elements.append(pdf_table)

    # Pied de page
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(
        f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')} — PyCalendar MySportU",
        footer_style,
    ))

    doc.build(elements)
    console.print(f"[green]✅ Export PDF : {filepath}[/]")


# ─── Helpers PDF ──────────────────────────────────────────────


def _pdf_base_style(color_header, color_header_text, color_row_alt,
                    num_rows: int) -> list:
    """Style de base commun pour les tableaux PDF."""
    cmds: list = [
        ("BACKGROUND", (0, 0), (-1, 0), color_header),
        ("TEXTCOLOR", (0, 0), (-1, 0), color_header_text),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("ALIGN", (0, 1), (1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
        ("TOPPADDING", (0, 1), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("LINEBELOW", (0, 0), (-1, 0), 1, color_header),
    ]
    for i in range(2, num_rows, 2):
        cmds.append(("BACKGROUND", (0, i), (-1, i), color_row_alt))
    return cmds


def _pdf_team_row_colors(cmds: list, i: int, meta: dict,
                         color_ok, color_warning, color_error) -> None:
    """Ajoute la colorisation par ligne pour le mode par-équipe."""
    # Joueurs (col 4)
    if meta["joueurs_valide"] and meta["joueurs_ok"]:
        cmds.append(("TEXTCOLOR", (4, i), (4, i), color_ok))
    elif meta["joueurs_ok"]:
        cmds.append(("TEXTCOLOR", (4, i), (4, i), color_warning))
    else:
        cmds.append(("TEXTCOLOR", (4, i), (4, i), color_error))

    # Staff (col 5)
    if meta["staffs_valide"]:
        cmds.append(("TEXTCOLOR", (5, i), (5, i), color_ok))
    elif meta["staffs"] > 0:
        cmds.append(("TEXTCOLOR", (5, i), (5, i), color_warning))
    else:
        cmds.append(("TEXTCOLOR", (5, i), (5, i), color_error))

    # Adversaire (col 3)
    c = color_ok if meta["adv_pret"] else color_error
    cmds.append(("TEXTCOLOR", (3, i), (3, i), c))

    # Statut final (col 6)
    c = color_ok if meta["pret"] else color_error
    cmds.append(("TEXTCOLOR", (6, i), (6, i), c))
    cmds.append(("FONTNAME", (6, i), (6, i), "Helvetica-Bold"))


# ═══════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════

def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Vérification des feuilles de match MySportU",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples :
  %(prog)s                                    # Matchs du jour
  %(prog)s --date 05/02/2026                  # Date spécifique
  %(prog)s --date 05/02/2026 --sport volley   # Filtrer par sport
  %(prog)s --competition "LYON VBF PH2"       # Filtrer par compétition
  %(prog)s --verbose                          # Détails des matchs non prêts
  %(prog)s --by-team                          # Vue par institution
  %(prog)s --links                            # Liens feuilles de match
  %(prog)s --include-cancelled                # Inclure reportés/forfaits
  %(prog)s --export rapport.csv               # Exporter en CSV
  %(prog)s --pdf rapport.pdf --by-team        # Exporter en PDF
        """,
    )

    parser.add_argument(
        "--date", "-d", type=str, default=None,
        help="Date des matchs DD/MM/YYYY (défaut : aujourd'hui)",
    )
    parser.add_argument(
        "--sport", "-s", type=str, default=None,
        choices=["volley", "hand", "basket", "foot", "rugby"],
        help="Filtrer par sport",
    )
    parser.add_argument(
        "--competition", "-c", type=str, default=None,
        help="Filtrer par compétition (recherche partielle)",
    )
    parser.add_argument(
        "--username", "-u", type=str, default=None,
        help="Identifiant MySportU (sinon : env ou configs/default.yaml)",
    )
    parser.add_argument(
        "--password", type=str, default=None,
        help="Mot de passe MySportU (sinon : env ou configs/default.yaml)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Détails des matchs non prêts",
    )
    parser.add_argument(
        "--by-team", "-t", action="store_true",
        help="Vue par institution / équipe",
    )
    parser.add_argument(
        "--links", "-l", action="store_true",
        help="Inclure les liens vers les feuilles de match",
    )
    parser.add_argument(
        "--include-cancelled", action="store_true",
        help="Inclure matchs reportés, forfaits, terminés",
    )
    parser.add_argument(
        "--export", "-e", type=str, default=None,
        help="Chemin du fichier CSV à exporter",
    )
    parser.add_argument(
        "--pdf", type=str, default=None,
        help="Chemin du fichier PDF à exporter",
    )
    parser.add_argument(
        "--list-competitions", action="store_true",
        help="Lister les compétitions disponibles et quitter",
    )

    return parser


def main() -> None:
    """Point d'entrée principal."""
    parser = create_parser()
    args = parser.parse_args()

    # Créer le client MySportU
    msu = MySportU(
        username=args.username,
        password=args.password,
        verbose=args.verbose,
    )

    try:
        with msu:
            # ── Lister les compétitions ──
            if args.list_competitions:
                comps = msu.get_competitions()
                msu.display_competitions(comps)
                return

            # ── Récupérer tous les matchs ──
            all_matches = msu.get_all_matches()

            # ── Filtre par date ──
            date_filter = args.date or datetime.now().strftime("%d/%m/%Y")
            console.print(f"\n[bold]📅 Date :[/] {date_filter}")

            if not args.include_cancelled:
                console.print(
                    "[dim](matchs reportés/forfaits exclus — "
                    "utilisez --include-cancelled pour les inclure)[/]"
                )

            # ── Filtrage ──
            filtered = filter_matches(
                all_matches,
                date_filter=date_filter,
                sport_filter=args.sport,
                competition_filter=args.competition,
                include_cancelled=args.include_cancelled,
            )

            if not filtered:
                console.print("[yellow]Aucun match trouvé pour les critères spécifiés[/]")
                return

            console.print(f"[bold]{len(filtered)}[/] matchs correspondent aux critères")

            # ── Analyse (chargement des détails) ──
            results = analyze_matches(msu, filtered)

            # ── Affichage ──
            if args.by_team:
                print_report_by_team(results, args.links)
            else:
                print_report(results, args.verbose, args.links)

            # ── Export CSV ──
            if args.export:
                export_to_csv(results, args.export, include_links=args.links)

            # ── Export PDF ──
            if args.pdf:
                export_to_pdf(
                    results, args.pdf,
                    date_str=date_filter,
                    competition_str=args.competition or "",
                    by_team=args.by_team,
                    include_links=args.links,
                )

    except KeyboardInterrupt:
        console.print("\n[dim]Interrompu.[/]")
        sys.exit(130)
    except Exception as e:
        console.print(f"[red]❌ {e}[/]")
        if args.verbose:
            console.print_exception()
        sys.exit(1)


if __name__ == "__main__":
    main()
