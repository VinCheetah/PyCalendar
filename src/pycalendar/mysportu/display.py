"""
Affichage Rich pour les données MySportU.

Fournit des fonctions et une classe Display pour afficher proprement
les matchs, compétitions, équipes et statistiques du cache.
"""

from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.columns import Columns
from rich.tree import Tree

from .models import (
    Competition,
    MatchInfo,
    MatchDetail,
    MatchState,
)


# ─────────────────────────────────────────────────────────────────────────────
# Styles et couleurs
# ─────────────────────────────────────────────────────────────────────────────

STYLE_HEADER = "bold cyan"
STYLE_SUCCESS = "bold green"
STYLE_ERROR = "bold red"
STYLE_WARNING = "bold yellow"
STYLE_INFO = "bold blue"
STYLE_DIM = "dim"
STYLE_HIGHLIGHT = "bold white"

STATE_STYLES: dict[MatchState, str] = {
    MatchState.NON_JOUE: "dim white",
    MatchState.TERMINE: "green",
    MatchState.REPORTE: "yellow",
    MatchState.ANNULE: "red",
    MatchState.FORFAIT: "red dim",
}

SPORT_EMOJI: dict[str, str] = {
    "VB": "🏐",
    "HB": "🤾",
    "BB": "🏀",
    "FB": "⚽",
    "RG": "🏉",
    "BD": "🏸",
    "TT": "🏓",
}


class Display:
    """Couche d'affichage Rich pour MySportU."""

    def __init__(self, console: Console | None = None):
        self.console = console or Console()

    # ── Matchs ──────────────────────────────────────────────────────────

    def matches_table(
        self,
        matches: list[MatchInfo],
        *,
        title: str = "Matchs MySportU",
        show_competition: bool = False,
        compact: bool = False,
    ) -> None:
        """Affiche les matchs dans un tableau Rich."""
        if not matches:
            self.console.print(Panel("[dim]Aucun match trouvé[/]", title=title))
            return

        table = Table(
            title=title,
            show_lines=not compact,
            border_style="blue",
            header_style=STYLE_HEADER,
            title_style="bold white",
            caption=f"{len(matches)} match(s)",
            caption_style=STYLE_DIM,
        )

        table.add_column("#", style="dim", width=4, justify="right")
        table.add_column("Date", style="white", width=12)
        table.add_column("Heure", style="dim", width=6)
        table.add_column("G", width=2, justify="center")
        table.add_column("Receveur", style="white", min_width=16)
        table.add_column("", width=3, justify="center")  # vs
        table.add_column("Visiteur", style="white", min_width=16)
        table.add_column("Score", width=7, justify="center")
        table.add_column("État", width=10)
        table.add_column("Lieu", style="dim", max_width=20)
        if show_competition:
            table.add_column("Compétition", style="dim", max_width=25)

        for i, m in enumerate(matches, 1):
            state_style = STATE_STYLES.get(m.state, "white")
            score_str = str(m.score) if m.score else ""
            genre_style = "magenta" if m.genre == "F" else "blue" if m.genre == "M" else "white"
            lieu_str = m.lieu.libelle[:20] if m.lieu else ""

            row = [
                str(i),
                m.date,
                m.heure,
                Text(m.genre, style=genre_style),
                Text(m.receveur.libelle_court, style="bold"),
                Text("vs", style="dim"),
                Text(m.visiteur.libelle_court, style="bold"),
                Text(score_str, style="bold green" if score_str else ""),
                Text(f"{m.state.icon} {m.state.label}", style=state_style),
                lieu_str,
            ]
            if show_competition:
                row.append(m.competition_libelle[:25])
            table.add_row(*row)

        self.console.print(table)

    def match_detail(self, detail: MatchDetail, match_info: MatchInfo | None = None) -> None:
        """Affiche les détails complets d'un match."""
        # En-tête
        title = (
            f"{detail.receveur.libelle_court} vs {detail.visiteur.libelle_court}"
        )
        subtitle = ""
        if match_info:
            subtitle = f"{match_info.date} {match_info.heure} | {match_info.competition_libelle}"

        header = Text()
        header.append(f"  {detail.receveur.libelle_court}", style="bold cyan")
        header.append("  vs  ", style="dim")
        header.append(f"{detail.visiteur.libelle_court}  ", style="bold yellow")
        if detail.score:
            header.append(f"  {detail.score}  ", style="bold green")
        header.append(f"\n  {detail.state.icon} {detail.state.label}", style=STATE_STYLES.get(detail.state, "white"))

        self.console.print(Panel(header, title=f"Match #{detail.id}", subtitle=subtitle,
                                  border_style="blue"))

        # Joueurs
        for label, joueurs, staffs, equipe in [
            ("Receveur", detail.joueurs_receveur, detail.staffs_receveur, detail.receveur),
            ("Visiteur", detail.joueurs_visiteur, detail.staffs_visiteur, detail.visiteur),
        ]:
            table = Table(title=f"{label}: {equipe.libelle_court}", border_style="dim",
                          show_lines=False, header_style="bold")
            table.add_column("N°", width=4, justify="right")
            table.add_column("Nom", min_width=20)
            table.add_column("Tit.", width=4, justify="center")
            table.add_column("Sél.", width=4, justify="center")

            for j in sorted(joueurs, key=lambda x: x.numero or 99):
                tit = "✓" if j.titulaire else ""
                sel = "✓" if j.selectionne else ""
                table.add_row(
                    str(j.numero) if j.numero else "",
                    j.nom_complet,
                    Text(tit, style="green"),
                    Text(sel, style="blue"),
                )

            if staffs:
                table.add_section()
                for s in staffs:
                    table.add_row("", f"[dim]{s.nom_complet} ({s.fonction})[/]", "", "")

            self.console.print(table)

        # Officiels
        if detail.officiels:
            arb_text = ", ".join(o.nom_complet for o in detail.officiels)
            self.console.print(f"  🏁 Officiels: {arb_text}")

        # Validations
        val_parts = []
        for v in detail.validations:
            icon = "✅" if v.joueurs_valide else "❌"
            val_parts.append(f"Équipe {v.equipe_id}: {icon} {v.nb_joueurs}J/{v.nb_staffs}S")
        if val_parts:
            self.console.print(f"  📋 Validations: {' | '.join(val_parts)}")

        ready_icon = "✅" if detail.is_ready else "❌"
        self.console.print(f"  {ready_icon} Prêt à jouer: {'Oui' if detail.is_ready else 'Non'}")

    # ── Compétitions ────────────────────────────────────────────────────

    def competitions_table(self, competitions: list[Competition], *,
                            title: str = "Compétitions MySportU") -> None:
        """Affiche les compétitions dans un tableau groupé par sport."""
        if not competitions:
            self.console.print(Panel("[dim]Aucune compétition trouvée[/]", title=title))
            return

        # Grouper par sport
        by_sport: dict[str, list[Competition]] = {}
        for c in competitions:
            sport = c.sport or "Autre"
            by_sport.setdefault(sport, []).append(c)

        tree = Tree(f"[bold]{title}[/] ({len(competitions)})")

        for sport in sorted(by_sport.keys()):
            emoji = SPORT_EMOJI.get(sport, "🏅")
            branch = tree.add(f"{emoji} [bold]{sport}[/] ({len(by_sport[sport])})")
            for c in sorted(by_sport[sport], key=lambda x: x.libelle):
                genre_badge = f"[magenta]{c.genre}[/]" if c.genre else "[dim]?[/]"
                champ_badge = f"[cyan]{c.championship}[/]" if c.championship else ""
                branch.add(f"[dim]#{c.id}[/] {c.libelle}  {genre_badge} {champ_badge}")

        self.console.print(tree)

    # ── Équipes ─────────────────────────────────────────────────────────

    def equipes_table(self, equipes: list[dict[str, Any]], *,
                       title: str = "Équipes MySportU") -> None:
        """Affiche les équipes."""
        if not equipes:
            self.console.print(Panel("[dim]Aucune équipe trouvée[/]", title=title))
            return

        table = Table(title=title, border_style="blue", header_style=STYLE_HEADER)
        table.add_column("#", style="dim", width=4, justify="right")
        table.add_column("Équipe", style="bold white", min_width=16)
        table.add_column("G", width=2, justify="center")
        table.add_column("Club", style="dim", max_width=20)
        table.add_column("Code", style="dim", width=12)
        table.add_column("Matchs", width=6, justify="right")

        for i, eq in enumerate(equipes, 1):
            genre_style = "magenta" if eq["genre"] == "F" else "blue"
            table.add_row(
                str(i),
                eq["libelle_court"],
                Text(eq["genre"], style=genre_style),
                eq.get("club_nom", "")[:20],
                eq.get("club_code", ""),
                str(eq.get("count", 0)),
            )

        self.console.print(table)

    # ── Lieux ───────────────────────────────────────────────────────────

    def lieux_table(self, lieux: list[dict[str, Any]], *,
                     title: str = "Lieux de pratique") -> None:
        """Affiche les lieux de pratique."""
        if not lieux:
            self.console.print(Panel("[dim]Aucun lieu trouvé[/]", title=title))
            return

        table = Table(title=title, border_style="blue", header_style=STYLE_HEADER)
        table.add_column("#", style="dim", width=4, justify="right")
        table.add_column("Lieu", style="bold white", min_width=25)
        table.add_column("Matchs", width=8, justify="right")

        for i, lieu in enumerate(lieux, 1):
            table.add_row(str(i), lieu["libelle"], str(lieu["count"]))

        self.console.print(table)

    # ── Statistiques ────────────────────────────────────────────────────

    def stats_panel(self, matches: list[MatchInfo], *,
                     title: str = "Statistiques") -> None:
        """Affiche un panneau de statistiques sur les matchs."""
        if not matches:
            return

        # Compter par état
        by_state: dict[MatchState, int] = {}
        for m in matches:
            by_state[m.state] = by_state.get(m.state, 0) + 1

        # Compter par genre
        by_genre: dict[str, int] = {}
        for m in matches:
            by_genre[m.genre] = by_genre.get(m.genre, 0) + 1

        # Compter par date
        by_date: dict[str, int] = {}
        for m in matches:
            by_date[m.date] = by_date.get(m.date, 0) + 1

        # Construire le panneau
        parts = []

        state_text = Text()
        state_text.append("États:\n", style="bold")
        for state, count in sorted(by_state.items(), key=lambda x: x[1], reverse=True):
            style = STATE_STYLES.get(state, "white")
            state_text.append(f"  {state.icon} {state.label}: ", style=style)
            state_text.append(f"{count}\n", style="bold")
        parts.append(Panel(state_text, border_style="dim"))

        genre_text = Text()
        genre_text.append("Genres:\n", style="bold")
        for g, count in sorted(by_genre.items()):
            style = "magenta" if g == "F" else "blue" if g == "M" else "white"
            genre_text.append(f"  {g}: ", style=style)
            genre_text.append(f"{count}\n", style="bold")
        parts.append(Panel(genre_text, border_style="dim"))

        date_text = Text()
        date_text.append(f"Dates: {len(by_date)} journées\n", style="bold")
        for d in sorted(list(by_date.keys()))[:8]:
            date_text.append(f"  {d}: {by_date[d]}\n")
        if len(by_date) > 8:
            date_text.append(f"  ... +{len(by_date) - 8} autres\n", style="dim")
        parts.append(Panel(date_text, border_style="dim"))

        self.console.print(Panel(
            Columns(parts, equal=True, expand=True),
            title=f"[bold]{title}[/] — {len(matches)} matchs",
            border_style="blue",
        ))

    # ── Cache ───────────────────────────────────────────────────────────

    def cache_stats(self, stats: dict[str, Any]) -> None:
        """Affiche les statistiques du cache."""
        table = Table(title="Cache MySportU", border_style="green", header_style=STYLE_HEADER)
        table.add_column("Type", style="bold")
        table.add_column("Valides", justify="right", style="green")
        table.add_column("Expirées", justify="right", style="red")
        table.add_column("Total", justify="right")

        by_type = stats.get("by_type", {})
        for rtype, info in sorted(by_type.items()):
            table.add_row(
                rtype,
                str(info.get("valid", 0)),
                str(info.get("expired", 0)),
                str(info.get("count", 0)),
            )

        table.add_section()
        table.add_row(
            "[bold]TOTAL[/]",
            "", "",
            f"[bold]{stats.get('total_entries', 0)}[/]  "
            f"({stats.get('total_size_kb', 0)} KB)",
        )

        self.console.print(table)

    # ── Utilitaires ─────────────────────────────────────────────────────

    def status(self, message: str, style: str = STYLE_INFO) -> None:
        """Affiche un message de statut."""
        self.console.print(f"  [{style}]●[/] {message}")

    def success(self, message: str) -> None:
        self.console.print(f"  [green]✓[/] {message}")

    def warning(self, message: str) -> None:
        self.console.print(f"  [yellow]⚠[/] {message}")

    def error(self, message: str) -> None:
        self.console.print(f"  [red]✗[/] {message}")

    def header(self, title: str, subtitle: str = "") -> None:
        """Affiche un en-tête de section."""
        text = Text(title, style="bold white")
        self.console.print(Panel(text, subtitle=subtitle, border_style="blue",
                                  expand=False, padding=(0, 2)))

    def progress(self) -> Progress:
        """Crée une barre de progression Rich."""
        return Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=30),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("•"),
            TextColumn("{task.completed}/{task.total}"),
            TimeElapsedColumn(),
            console=self.console,
        )
