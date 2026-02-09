#!/usr/bin/env python3
"""
Export des classements de poules en images pour présentation.

Ce script génère des images des classements à partir d'une solution JSON.
Les classements peuvent être regroupés sur des feuilles paysage pour présentation.

Fonctionnalités:
- Calcul des classements avec règles spécifiques par sport (volleyball: tie-break)
- Export en PNG haute résolution ou PDF multi-pages
- Regroupement flexible des poules par genre, niveau, ou personnalisé
- Séparation par genre sur la même feuille (filles en haut, garçons en bas)
- Adaptation automatique du nombre de colonnes selon le nombre de poules
- Mise en page compacte avec espaces verticaux réduits
- Options pour masquer le titre et/ou la légende du barème
- Format paysage optimisé pour présentation avec esthétique améliorée

Usage:
    python scripts/export_standings.py                                    # Auto-détection
    python scripts/export_standings.py --solution solutions/latest_volley.json
    python scripts/export_standings.py --group-by genre                   # Grouper par genre (M/F)
    python scripts/export_standings.py --group-by level                   # Grouper par niveau (A1-A4)
    python scripts/export_standings.py --pools-per-row 5                  # Max 5 poules par ligne
    python scripts/export_standings.py --genre-split                      # Filles et garçons sur même feuille
    python scripts/export_standings.py --genre-split --group-by level     # Combinaison: niveau + genre
    python scripts/export_standings.py --no-title                         # Sans titre global
    python scripts/export_standings.py --show-legend                      # Avec légende du barème
    python scripts/export_standings.py --output exports/classements.png   # Fichier de sortie

Exemples:
    # Exporter tous les classements du volleyball
    python scripts/export_standings.py --sport volley

    # Exporter avec 4 poules par ligne, groupées par genre
    python scripts/export_standings.py --pools-per-row 4 --group-by genre
    
    # Exporter par niveau avec séparation homme/femme, sans titre (COMPACT)
    python scripts/export_standings.py --group-by level --genre-split --pools-per-row 5 --no-title
    
    # Exporter avec légende du barème de points
    python scripts/export_standings.py --genre-split --show-legend
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from collections import defaultdict
import argparse

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from scripts.script_base import (
    ScriptContext,
    create_base_parser,
    print_header,
    print_success,
    print_error,
    print_info,
    print_warning,
)

# Type hints pour matplotlib (importé conditionnellement)
plt = None  # type: ignore
PdfPages = None  # type: ignore

try:
    import matplotlib.pyplot as plt  # type: ignore
    import matplotlib.patches as mpatches  # type: ignore
    from matplotlib.backends.backend_pdf import PdfPages  # type: ignore
    import numpy as np  # type: ignore
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    plt = None
    PdfPages = None
    print_warning("matplotlib non installé. Installez avec: pip install matplotlib")


@dataclass
class TeamStats:
    """Statistiques d'une équipe dans une poule."""
    id: str
    nom: str
    nom_complet: str
    played: int = 0           # Matchs joués (avec score)
    no_score: int = 0         # Matchs sans score
    won: int = 0              # Total victoires
    won_classic: int = 0      # Victoires classiques (3-0, 3-1) - volley
    won_tiebreak: int = 0     # Victoires tie-break (3-2) - volley
    drawn: int = 0            # Match nul (autres sports)
    lost: int = 0             # Total défaites
    lost_tiebreak: int = 0    # Défaites tie-break (2-3) - volley
    lost_classic: int = 0     # Défaites classiques (0-3, 1-3) - volley
    points: int = 0
    sets_for: int = 0         # Sets gagnés (volley) / Buts marqués (autres)
    sets_against: int = 0     # Sets perdus (volley) / Buts encaissés (autres)


@dataclass
class PoolStandings:
    """Classement complet d'une poule."""
    pool_id: str
    pool_name: str
    genre: str
    level: str
    teams: List[TeamStats] = field(default_factory=list)


class StandingsCalculator:
    """Calcule les classements selon les règles du sport."""
    
    def __init__(self, solution_data: Dict[str, Any]):
        self.data = solution_data
        self.sport_type = solution_data.get('sport', {}).get('type', 'volleyball')
        self.is_volleyball = self.sport_type == 'volleyball'
        
        # Indexer les données
        self.teams_by_id = {t['id']: t for t in self.data.get('entities', {}).get('equipes', [])}
        
        # Les matchs sont dans data['matches']['scheduled'] et data['matches']['unscheduled']
        matches_data = self.data.get('matches', {})
        scheduled = matches_data.get('scheduled', []) if isinstance(matches_data, dict) else []
        unscheduled = matches_data.get('unscheduled', []) if isinstance(matches_data, dict) else []
        self.matches = scheduled + unscheduled
        
        self.pools = self._extract_pools()
    
    def _extract_pools(self) -> Dict[str, Dict]:
        """Extrait les informations des poules à partir des équipes."""
        pools = {}
        for team in self.teams_by_id.values():
            pool_id = team.get('poule', '')
            if pool_id and pool_id not in pools:
                # Extraire genre et niveau
                genre = self._extract_genre(pool_id, team)
                level = self._extract_level(pool_id)
                pools[pool_id] = {
                    'id': pool_id,
                    'name': pool_id,
                    'genre': genre,
                    'level': level,
                    'teams': []
                }
            if pool_id:
                pools[pool_id]['teams'].append(team['id'])
        return pools
    
    def _extract_genre(self, pool_id: str, team: Dict) -> str:
        """Extrait le genre d'une poule."""
        # Essayer depuis l'équipe
        if team.get('genre'):
            return team['genre']
        # Essayer depuis le code de poule (VBF... = F, VBM... = M)
        if len(pool_id) >= 3:
            if pool_id[2].upper() == 'F':
                return 'F'
            elif pool_id[2].upper() == 'M':
                return 'M'
        return 'M'  # Par défaut
    
    def _extract_level(self, pool_id: str) -> str:
        """Extrait le niveau d'une poule (A1, A2, A3, A4)."""
        import re
        match = re.search(r'A([1-4])', pool_id, re.IGNORECASE)
        if match:
            return f'A{match.group(1)}'
        return ''
    
    def _has_valid_score(self, match: Dict) -> bool:
        """Vérifie si un match a un score valide."""
        score = match.get('score', {})
        return (
            score.get('has_score', False) and
            score.get('equipe1') is not None and
            score.get('equipe2') is not None
        )
    
    def calculate_pool_standings(self, pool_id: str) -> PoolStandings:
        """Calcule le classement d'une poule."""
        pool_info = self.pools.get(pool_id, {})
        team_ids = pool_info.get('teams', [])
        
        # Initialiser les stats
        stats: Dict[str, TeamStats] = {}
        for team_id in team_ids:
            team = self.teams_by_id.get(team_id, {})
            stats[team_id] = TeamStats(
                id=team_id,
                nom=team.get('nom', team_id),
                nom_complet=team.get('nom_complet', team.get('nom', team_id))
            )
        
        # Compter les matchs sans score pour chaque équipe
        for match in self.matches:
            if match.get('poule') != pool_id:
                continue
            
            if not self._has_valid_score(match) and match.get('semaine'):
                # Match planifié mais sans score
                t1_id = match.get('equipe1_id')
                t2_id = match.get('equipe2_id')
                if t1_id in stats:
                    stats[t1_id].no_score += 1
                if t2_id in stats:
                    stats[t2_id].no_score += 1
        
        # Analyser les matchs avec scores
        for match in self.matches:
            if match.get('poule') != pool_id:
                continue
            
            if not self._has_valid_score(match):
                continue
            
            team1_id = match.get('equipe1_id')
            team2_id = match.get('equipe2_id')
            score1 = match['score']['equipe1']
            score2 = match['score']['equipe2']
            
            if team1_id not in stats or team2_id not in stats:
                continue
            
            # Incrémenter matchs joués
            stats[team1_id].played += 1
            stats[team2_id].played += 1
            
            # Enregistrer sets/buts
            stats[team1_id].sets_for += score1
            stats[team1_id].sets_against += score2
            stats[team2_id].sets_for += score2
            stats[team2_id].sets_against += score1
            
            # Appliquer les points selon le sport
            if self.is_volleyball:
                self._apply_volleyball_points(stats, team1_id, team2_id, score1, score2)
            else:
                self._apply_classic_points(stats, team1_id, team2_id, score1, score2)
        
        # Trier le classement
        sorted_teams = sorted(
            stats.values(),
            key=lambda t: (
                -t.points,
                -(t.sets_for - t.sets_against),
                -t.sets_for,
                -t.won,
                t.nom
            )
        )
        
        return PoolStandings(
            pool_id=pool_id,
            pool_name=pool_info.get('name', pool_id),
            genre=pool_info.get('genre', ''),
            level=pool_info.get('level', ''),
            teams=sorted_teams
        )
    
    def _apply_volleyball_points(
        self, 
        stats: Dict[str, TeamStats], 
        team1_id: str, 
        team2_id: str, 
        score1: int, 
        score2: int
    ):
        """Applique les points volleyball avec tie-break."""
        max_score = max(score1, score2)
        min_score = min(score1, score2)
        is_tiebreak = (max_score == 3 and min_score == 2)
        
        if score1 > score2:
            # Victoire équipe 1
            stats[team1_id].won += 1
            stats[team2_id].lost += 1
            
            if is_tiebreak:
                stats[team1_id].won_tiebreak += 1
                stats[team1_id].points += 2
                stats[team2_id].lost_tiebreak += 1
                stats[team2_id].points += 1
            else:
                stats[team1_id].won_classic += 1
                stats[team1_id].points += 3
                stats[team2_id].lost_classic += 1
        
        elif score2 > score1:
            # Victoire équipe 2
            stats[team2_id].won += 1
            stats[team1_id].lost += 1
            
            if is_tiebreak:
                stats[team2_id].won_tiebreak += 1
                stats[team2_id].points += 2
                stats[team1_id].lost_tiebreak += 1
                stats[team1_id].points += 1
            else:
                stats[team2_id].won_classic += 1
                stats[team2_id].points += 3
                stats[team1_id].lost_classic += 1
    
    def _apply_classic_points(
        self, 
        stats: Dict[str, TeamStats], 
        team1_id: str, 
        team2_id: str, 
        score1: int, 
        score2: int
    ):
        """Applique les points classiques (football, handball, etc.)."""
        if score1 > score2:
            stats[team1_id].won += 1
            stats[team1_id].won_classic += 1
            stats[team1_id].points += 3
            stats[team2_id].lost += 1
            stats[team2_id].lost_classic += 1
        elif score2 > score1:
            stats[team2_id].won += 1
            stats[team2_id].won_classic += 1
            stats[team2_id].points += 3
            stats[team1_id].lost += 1
            stats[team1_id].lost_classic += 1
        else:
            stats[team1_id].drawn += 1
            stats[team1_id].points += 1
            stats[team2_id].drawn += 1
            stats[team2_id].points += 1
    
    def get_all_standings(self) -> List[PoolStandings]:
        """Retourne tous les classements."""
        standings = []
        for pool_id in sorted(self.pools.keys()):
            standings.append(self.calculate_pool_standings(pool_id))
        return standings


class StandingsExporter:
    """Exporte les classements en images."""
    
    # Couleurs FFSU
    COLORS = {
        'primary': '#0055A4',      # Bleu FFSU
        'secondary': '#EF4135',    # Rouge FFSU
        'gold': '#FFD700',
        'silver': '#C0C0C0',
        'bronze': '#CD7F32',
        'success': '#10B981',
        'warning': '#F59E0B',
        'danger': '#EF4444',
        'text': '#1E293B',
        'text_light': '#64748B',
        'bg_light': '#F8FAFC',
        'border': '#E2E8F0',
    }
    
    def __init__(
        self, 
        standings: List[PoolStandings],
        is_volleyball: bool = True,
        sport_name: str = "Volleyball"
    ):
        self.standings = standings
        self.is_volleyball = is_volleyball
        self.sport_name = sport_name
    
    def export_to_image(
        self,
        output_path: str,
        pools_per_row: int = 2,
        group_by: str = 'none',  # 'none', 'genre', 'level'
        title: Optional[str] = None,
        dpi: int = 150,
        show_legend: bool = False,
        no_title: bool = False
    ) -> List[str]:
        """
        Exporte les classements en image(s).
        
        Args:
            output_path: Chemin de sortie (sans extension = multiple fichiers)
            pools_per_row: Nombre de poules par ligne
            group_by: Comment regrouper les poules ('none', 'genre', 'level')
            title: Titre personnalisé
            dpi: Résolution de l'image
            show_legend: Afficher la légende du barème (défaut: False)
            no_title: Ne pas afficher le titre global (défaut: False)
            
        Returns:
            Liste des fichiers créés
        """
        if not HAS_MATPLOTLIB:
            raise ImportError("matplotlib est requis pour l'export d'images")
        
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        
        # Grouper les poules
        groups = self._group_standings(group_by)
        
        created_files = []
        
        for group_name, group_standings in groups.items():
            # Calculer la disposition (adapter le nombre de colonnes si nécessaire)
            n_pools = len(group_standings)
            actual_cols = min(n_pools, pools_per_row)  # S'adapter au nombre réel de poules
            n_rows = (n_pools + actual_cols - 1) // actual_cols
            
            # Créer la figure en format paysage (taille adaptée au nombre de colonnes)
            fig_width = max(6 * actual_cols, 12)  # Minimum 12 pour lisibilité
            # Réduction de la hauteur: 2.0 au lieu de 2.5, base de 2.5 au lieu de 3
            fig_height = max(2.5 + 2.0 * n_rows, 7)  # Minimum 7 pour lisibilité
            
            fig, axes = plt.subplots(
                n_rows, actual_cols,
                figsize=(fig_width, fig_height),
                squeeze=False
            )
            
            # Titre global (si activé)
            title_height = 0
            if not no_title:
                group_title = title or f"Classements {self.sport_name}"
                if group_by != 'none' and group_name:
                    group_title += f" - {group_name}"
                
                fig.suptitle(
                    group_title,
                    fontsize=15,
                    fontweight='bold',
                    color=self.COLORS['primary'],
                    y=0.97
                )
                title_height = 0.04
            
            # Remplir les tableaux
            for idx, standing in enumerate(group_standings):
                row = idx // actual_cols
                col = idx % actual_cols
                ax = axes[row, col]
                
                self._draw_standings_table(ax, standing)
            
            # Masquer les axes vides
            for idx in range(len(group_standings), n_rows * actual_cols):
                row = idx // actual_cols
                col = idx % actual_cols
                axes[row, col].axis('off')
            
            # Ajouter une légende si volleyball ET si demandé
            legend_height = 0
            if self.is_volleyball and show_legend:
                legend_text = "Système de points: Victoire 3-0/3-1 = 3pts • Victoire 3-2 = 2pts • Défaite 2-3 = 1pt • Défaite 0-3/1-3 = 0pt"
                fig.text(
                    0.5, 0.015,
                    legend_text,
                    ha='center',
                    fontsize=9,
                    color=self.COLORS['text_light'],
                    style='italic',
                    bbox=dict(boxstyle='round,pad=0.4', facecolor=self.COLORS['bg_light'], edgecolor=self.COLORS['border'], linewidth=1)
                )
                legend_height = 0.04
            
            # Ajuster les marges selon la présence du titre et de la légende
            top_margin = 0.98 - title_height
            bottom_margin = legend_height
            plt.tight_layout(rect=[0, bottom_margin, 1, top_margin])
            
            # Sauvegarder
            if group_by == 'none' or len(groups) == 1:
                file_path = output.with_suffix('.png')
            else:
                safe_name = group_name.replace(' ', '_').replace('/', '_')
                file_path = output.parent / f"{output.stem}_{safe_name}.png"
            
            fig.savefig(file_path, dpi=dpi, bbox_inches='tight', facecolor='white')
            plt.close(fig)
            
            created_files.append(str(file_path))
        
        return created_files
    
    def export_to_pdf(
        self,
        output_path: str,
        pools_per_page: int = 4,
        pools_per_row: int = 2,
        group_by: str = 'none',
        title: Optional[str] = None
    ) -> str:
        """Exporte tous les classements dans un PDF multi-pages."""
        if not HAS_MATPLOTLIB:
            raise ImportError("matplotlib est requis pour l'export PDF")
        
        output = Path(output_path).with_suffix('.pdf')
        output.parent.mkdir(parents=True, exist_ok=True)
        
        groups = self._group_standings(group_by)
        
        with PdfPages(output) as pdf:
            for group_name, group_standings in groups.items():
                # Paginer les poules
                for page_start in range(0, len(group_standings), pools_per_page):
                    page_pools = group_standings[page_start:page_start + pools_per_page]
                    n_pools = len(page_pools)
                    n_rows = (n_pools + pools_per_row - 1) // pools_per_row
                    
                    # Figure paysage A4
                    fig, axes = plt.subplots(
                        n_rows, pools_per_row,
                        figsize=(11.69, 8.27),  # A4 paysage
                        squeeze=False
                    )
                    
                    # Titre
                    page_title = title or f"Classements {self.sport_name}"
                    if group_by != 'none' and group_name:
                        page_title += f" - {group_name}"
                    if len(group_standings) > pools_per_page:
                        page_num = page_start // pools_per_page + 1
                        total_pages = (len(group_standings) + pools_per_page - 1) // pools_per_page
                        page_title += f" ({page_num}/{total_pages})"
                    
                    fig.suptitle(
                        page_title,
                        fontsize=14,
                        fontweight='bold',
                        color=self.COLORS['primary']
                    )
                    
                    for idx, standing in enumerate(page_pools):
                        row = idx // pools_per_row
                        col = idx % pools_per_row
                        self._draw_standings_table(axes[row, col], standing)
                    
                    # Masquer axes vides
                    for idx in range(len(page_pools), n_rows * pools_per_row):
                        row = idx // pools_per_row
                        col = idx % pools_per_row
                        axes[row, col].axis('off')
                    
                    if self.is_volleyball:
                        fig.text(
                            0.5, 0.02,
                            "V(3-0/3-1)=3pts | V(3-2)=2pts | D(2-3)=1pt | D=0pt",
                            ha='center',
                            fontsize=8,
                            color=self.COLORS['text_light']
                        )
                    
                    plt.tight_layout(rect=[0, 0.04, 1, 0.94])
                    pdf.savefig(fig, dpi=150)
                    plt.close(fig)
        
        return str(output)
    
    def _group_standings(self, group_by: str) -> Dict[str, List[PoolStandings]]:
        """Groupe les classements selon le critère spécifié."""
        if group_by == 'none':
            return {'': self.standings}
        
        groups = defaultdict(list)
        
        for standing in self.standings:
            if group_by == 'genre':
                key = 'Féminin' if standing.genre == 'F' else 'Masculin'
            elif group_by == 'level':
                key = standing.level or 'Autre'
            else:
                key = ''
            groups[key].append(standing)
        
        # Trier les groupes
        sorted_groups = {}
        for key in sorted(groups.keys()):
            sorted_groups[key] = groups[key]
        
        return sorted_groups
    
    def export_genre_split(
        self,
        output_path: str,
        pools_per_row: int = 2,
        title: Optional[str] = None,
        dpi: int = 150,
        group_by: str = 'none',
        show_legend: bool = False,
        no_title: bool = False
    ) -> List[str]:
        """
        Exporte les classements avec séparation par genre sur la même feuille.
        Filles en haut, garçons en bas.
        
        Args:
            output_path: Chemin de sortie
            pools_per_row: Nombre de poules par ligne par genre
            title: Titre personnalisé
            dpi: Résolution de l'image
            group_by: Regroupement supplémentaire ('none', 'level')
            show_legend: Afficher la légende du barème (défaut: False)
            no_title: Ne pas afficher le titre global (défaut: False)
            
        Returns:
            Liste des chemins de fichiers créés
        """
        if not HAS_MATPLOTLIB:
            raise ImportError("matplotlib est requis pour l'export d'images")
        
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        
        # Grouper d'abord selon le critère (level, etc)
        if group_by != 'none':
            groups = self._group_standings(group_by)
        else:
            groups = {'': self.standings}
        
        created_files = []
        
        for group_name, group_standings in groups.items():
            # Séparer par genre au sein du groupe
            feminine = [s for s in group_standings if s.genre == 'F']
            masculine = [s for s in group_standings if s.genre == 'M']
        
            # Calculer les dimensions (adapter le nombre de colonnes)
            n_fem = len(feminine)
            n_masc = len(masculine)
            
            # Adapter le nombre de colonnes au nombre réel de poules
            actual_cols_fem = min(n_fem, pools_per_row) if n_fem > 0 else pools_per_row
            actual_cols_masc = min(n_masc, pools_per_row) if n_masc > 0 else pools_per_row
            actual_cols = max(actual_cols_fem, actual_cols_masc)
            
            rows_fem = (n_fem + actual_cols - 1) // actual_cols if n_fem > 0 else 0
            rows_masc = (n_masc + actual_cols - 1) // actual_cols if n_masc > 0 else 0
            
            total_rows = rows_fem + rows_masc
            if total_rows == 0:
                total_rows = 1
            
            # Créer la figure (format paysage, taille adaptée)
            fig_width = max(6 * actual_cols, 14)
            # Réduction de la hauteur: 2.2 au lieu de 2.8, base de 3 au lieu de 4
            fig_height = max(3 + 2.2 * total_rows, 8)
            
            fig = plt.figure(figsize=(fig_width, fig_height))
            
            # Titre global (si activé)
            title_y = 0.96
            if not no_title:
                global_title = title or f"Classements {self.sport_name}"
                if group_by != 'none' and group_name:
                    global_title += f" - {group_name}"
                
                fig.suptitle(
                    global_title,
                    fontsize=18,
                    fontweight='bold',
                    color=self.COLORS['primary'],
                    y=0.97
                )
                title_y = 0.94
        
            # Calculer la position verticale (démarrer plus haut si pas de titre)
            current_y = title_y - 0.01
            row_height = (title_y - 0.08) / total_rows if total_rows > 0 else 0.82
            
            # Section Féminine (en haut)
            if feminine:
                # Titre de section avec fond coloré (taille réduite)
                section_y = current_y
                fig.text(
                    0.5, section_y,
                    "♀️ Féminin",
                    fontsize=14,
                    fontweight='bold',
                    ha='center',
                    color='white',
                    bbox=dict(boxstyle='round,pad=0.5', facecolor=self.COLORS['secondary'], edgecolor='none')
                )
                current_y -= 0.025
                
                for idx, standing in enumerate(feminine):
                    row = idx // actual_cols
                    col = idx % actual_cols
                    
                    # Calculer la position de l'axe
                    ax_width = 0.88 / actual_cols
                    ax_height = row_height * 0.85
                    ax_left = 0.06 + col * ax_width
                    ax_bottom = current_y - (row + 1) * row_height
                    
                    ax = fig.add_axes([ax_left, ax_bottom, ax_width * 0.96, ax_height])
                    self._draw_standings_table(ax, standing)
                
                current_y -= rows_fem * row_height + 0.015
        
            # Séparateur visuel (ligne horizontale avec Line2D)
            if feminine and masculine:
                from matplotlib.lines import Line2D
                line = Line2D([0.08, 0.92], [current_y, current_y], 
                             transform=fig.transFigure, 
                             color=self.COLORS['border'], 
                             linewidth=2,
                             linestyle='--',
                             alpha=0.5)
                fig.add_artist(line)
                current_y -= 0.02
            
            # Section Masculine (en bas)
            if masculine:
                # Titre de section avec fond coloré (taille réduite)
                section_y = current_y
                fig.text(
                    0.5, section_y,
                    "♂️ Masculin",
                    fontsize=14,
                    fontweight='bold',
                    ha='center',
                    color='white',
                    bbox=dict(boxstyle='round,pad=0.5', facecolor=self.COLORS['primary'], edgecolor='none')
                )
                current_y -= 0.025
                
                for idx, standing in enumerate(masculine):
                    row = idx // actual_cols
                    col = idx % actual_cols
                    
                    # Calculer la position de l'axe
                    ax_width = 0.88 / actual_cols
                    ax_height = row_height * 0.85
                    ax_left = 0.06 + col * ax_width
                    ax_bottom = current_y - (row + 1) * row_height
                    
                    ax = fig.add_axes([ax_left, ax_bottom, ax_width * 0.96, ax_height])
                    self._draw_standings_table(ax, standing)
        
            # Légende volleyball (si demandée)
            if self.is_volleyball and show_legend:
                fig.text(
                    0.5, 0.015,
                    "Système de points: Victoire 3-0/3-1 = 3pts • Victoire 3-2 = 2pts • Défaite 2-3 = 1pt • Défaite 0-3/1-3 = 0pt",
                    ha='center',
                    fontsize=9,
                    color=self.COLORS['text_light'],
                    style='italic',
                    bbox=dict(boxstyle='round,pad=0.4', facecolor=self.COLORS['bg_light'], edgecolor=self.COLORS['border'], linewidth=1)
                )
            
            # Sauvegarder
            if group_by == 'none' or len(groups) == 1:
                file_path = output.with_suffix('.png')
            else:
                safe_name = group_name.replace(' ', '_').replace('/', '_')
                file_path = output.parent / f"{output.stem}_{safe_name}.png"
            
            fig.savefig(file_path, dpi=dpi, bbox_inches='tight', facecolor='white')
            plt.close(fig)
            
            created_files.append(str(file_path))
        
        return created_files

    def _draw_standings_table(self, ax: Any, standing: PoolStandings):
        """Dessine un tableau de classement sur un axe matplotlib."""
        ax.axis('off')
        
        # Titre de la poule avec fond et meilleur style
        pool_display = standing.pool_name
        genre_emoji = '♀️' if standing.genre == 'F' else '♂️'
        title_color = self.COLORS['secondary'] if standing.genre == 'F' else self.COLORS['primary']
        ax.set_title(
            f"{genre_emoji} {pool_display}",
            fontsize=11,
            fontweight='bold',
            color=title_color,
            pad=8,
            bbox=dict(boxstyle='round,pad=0.3', facecolor=self.COLORS['bg_light'], edgecolor=title_color, linewidth=1.5, alpha=0.3)
        )
        
        if not standing.teams:
            ax.text(
                0.5, 0.5,
                "Aucune équipe",
                ha='center', va='center',
                fontsize=10,
                color=self.COLORS['text_light']
            )
            return
        
        # Préparer les données du tableau
        if self.is_volleyball:
            columns = ['#', 'Équipe', 'J', '?', 'V', 'D', '+/-', 'Pts']
            col_widths = [0.07, 0.38, 0.08, 0.08, 0.08, 0.08, 0.11, 0.12]
        else:
            columns = ['#', 'Équipe', 'J', '?', 'V', 'N', 'D', '+/-', 'Pts']
            col_widths = [0.06, 0.32, 0.08, 0.08, 0.08, 0.08, 0.08, 0.11, 0.11]
        
        rows = []
        cell_colors = []
        
        for idx, team in enumerate(standing.teams):
            diff = team.sets_for - team.sets_against
            diff_str = f"+{diff}" if diff > 0 else str(diff)
            
            if self.is_volleyball:
                row = [
                    str(idx + 1),
                    team.nom[:22],  # Tronquer si trop long
                    str(team.played),
                    str(team.no_score) if team.no_score > 0 else '-',
                    str(team.won),
                    str(team.lost),
                    diff_str,
                    str(team.points)
                ]
            else:
                row = [
                    str(idx + 1),
                    team.nom[:20],
                    str(team.played),
                    str(team.no_score) if team.no_score > 0 else '-',
                    str(team.won),
                    str(team.drawn),
                    str(team.lost),
                    diff_str,
                    str(team.points)
                ]
            rows.append(row)
            
            # Couleurs plus subtiles et harmonieuses pour les 3 premiers
            if idx == 0:
                cell_colors.append(['#FFE97F55'] * len(columns))  # Or doux
            elif idx == 1:
                cell_colors.append(['#E8E8E855'] * len(columns))  # Argent doux
            elif idx == 2:
                cell_colors.append(['#E8C19955'] * len(columns))  # Bronze doux
            else:
                cell_colors.append(['#FAFAFA'] * len(columns))  # Blanc cassé
        
        # Créer le tableau
        table = ax.table(
            cellText=rows,
            colLabels=columns,
            colWidths=col_widths,
            cellColours=cell_colors,
            loc='center',
            cellLoc='center'
        )
        
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 1.6)
        
        # Style des en-têtes et cellules
        for (row, col), cell in table.get_celld().items():
            if row == 0:
                # En-tête avec gradient visuel
                cell.set_text_props(fontweight='bold', color='white', fontsize=9)
                cell.set_facecolor(self.COLORS['primary'])
                cell.set_linewidth(1.5)
            else:
                # Cellules normales
                cell.set_linewidth(0.8)
                # Alignement spécifique pour la colonne Équipe
                if col == 1:
                    cell.set_text_props(ha='left')
                    cell.PAD = 0.05
            
            cell.set_edgecolor(self.COLORS['border'])
            cell.set_alpha(0.95)


def main():
    parser = create_base_parser(
        description="Exporte les classements de poules en images pour présentation"
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default=None,
        help='Fichier de sortie (PNG ou PDF). Par défaut: exports/classements_{sport}.png'
    )
    
    parser.add_argument(
        '--format', '-f',
        choices=['png', 'pdf'],
        default='png',
        help='Format de sortie (png ou pdf)'
    )
    
    parser.add_argument(
        '--pools-per-row',
        type=int,
        default=2,
        help='Nombre maximum de poules par ligne - s\'adapte automatiquement si moins de poules (défaut: 2)'
    )
    
    parser.add_argument(
        '--pools-per-page',
        type=int,
        default=4,
        help='Nombre de poules par page pour PDF (défaut: 4)'
    )
    
    parser.add_argument(
        '--group-by',
        choices=['none', 'genre', 'level'],
        default='none',
        help='Comment regrouper les poules: none=tout ensemble, genre=séparer M/F, level=séparer A1/A2/A3/A4 (défaut: none)'
    )
    
    parser.add_argument(
        '--genre-split',
        action='store_true',
        help='Afficher les filles en haut et les garçons en bas sur la même feuille (compatible avec --group-by level)'
    )
    
    parser.add_argument(
        '--show-legend',
        action='store_true',
        help='Afficher la légende du barème de points (désactivé par défaut)'
    )
    
    parser.add_argument(
        '--no-title',
        action='store_true',
        help='Ne pas afficher le titre global (désactivé par défaut)'
    )
    
    parser.add_argument(
        '--title',
        type=str,
        default=None,
        help='Titre personnalisé pour les images'
    )
    
    parser.add_argument(
        '--dpi',
        type=int,
        default=150,
        help='Résolution des images PNG (défaut: 150)'
    )
    
    args = parser.parse_args()
    
    if not HAS_MATPLOTLIB:
        print_error("matplotlib est requis. Installez avec: pip install matplotlib")
        return 1
    
    # Créer le contexte
    try:
        ctx = ScriptContext.from_args(args)
    except FileNotFoundError as e:
        print_error(str(e))
        return 1
    
    # Afficher le header
    print_header(f"Export des classements {ctx.sport.name}", ctx.sport.emoji)
    ctx.print_status()
    
    # Vérifier qu'on a une solution
    if not ctx.solution_path or not ctx.solution_path.exists():
        print_error("Aucune solution trouvée")
        print_info("Spécifiez une solution avec --solution ou --config")
        return 1
    
    # Charger la solution
    print()
    print_info(f"Chargement de la solution: {ctx.solution_path.name}")
    
    with open(ctx.solution_path, 'r', encoding='utf-8') as f:
        solution_data = json.load(f)
    
    # Calculer les classements
    print_info("Calcul des classements...")
    calculator = StandingsCalculator(solution_data)
    standings = calculator.get_all_standings()
    
    print_info(f"  {len(standings)} poules trouvées")
    
    # Créer l'exporteur
    exporter = StandingsExporter(
        standings=standings,
        is_volleyball=calculator.is_volleyball,
        sport_name=ctx.sport.name
    )
    
    # Déterminer le fichier de sortie
    if args.output:
        output_path = Path(args.output)
    else:
        exports_dir = PROJECT_ROOT / 'exports'
        output_path = exports_dir / f"classements_{ctx.sport.pattern}"
    
    # Exporter
    print()
    
    try:
        if args.format == 'pdf':
            output_file = exporter.export_to_pdf(
                output_path=str(output_path),
                pools_per_page=args.pools_per_page,
                pools_per_row=args.pools_per_row,
                group_by=args.group_by,
                title=args.title
            )
            print_success(f"PDF exporté: {output_file}")
        elif args.genre_split:
            # Export avec séparation par genre sur la même feuille
            output_files = exporter.export_genre_split(
                output_path=str(output_path),
                pools_per_row=args.pools_per_row,
                title=args.title,
                dpi=args.dpi,
                group_by=args.group_by,
                show_legend=args.show_legend,
                no_title=args.no_title
            )
            for f in output_files:
                print_success(f"Image exportée: {f}")
        else:
            output_files = exporter.export_to_image(
                output_path=str(output_path),
                pools_per_row=args.pools_per_row,
                group_by=args.group_by,
                title=args.title,
                dpi=args.dpi,
                show_legend=args.show_legend,
                no_title=args.no_title
            )
            for f in output_files:
                print_success(f"Image exportée: {f}")
    
    except Exception as e:
        print_error(f"Erreur lors de l'export: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
    
    print()
    print_success("Export terminé!")
    return 0


if __name__ == '__main__':
    sys.exit(main())
