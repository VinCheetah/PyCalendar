#!/usr/bin/env python3
"""
Script de vérification des feuilles de match MySportU.

Ce script permet de :
- Se connecter à l'API MySportU
- Récupérer les matchs d'une date spécifique
- Analyser l'état de complétion des feuilles de match
- Afficher un rapport détaillé sur la préparation des matchs

L'analyse inclut pour chaque match :
- Nombre de joueurs inscrits par équipe
- Validation des effectifs (joueurs et staffs)
- Présence d'arbitre(s)
- Statut global "prêt à jouer"

Par défaut, les matchs reportés, forfaits et terminés sont exclus.

Usage:
    # Vérifier les matchs du jour
    python check_matchsheets.py
    
    # Vérifier les matchs d'une date spécifique
    python check_matchsheets.py --date 05/02/2026
    
    # Filtrer par sport
    python check_matchsheets.py --date 05/02/2026 --sport volley
    
    # Filtrer par compétition (recherche partielle)
    python check_matchsheets.py --date 05/02/2026 --competition "LYON VBF PH2"
    
    # Afficher les détails de chaque match
    python check_matchsheets.py --date 05/02/2026 --verbose
    
    # Affichage par institution (statistiques par équipe)
    python check_matchsheets.py --date 05/02/2026 --by-team
    
    # Inclure les liens vers les feuilles de match
    python check_matchsheets.py --date 05/02/2026 --links
    
    # Inclure les matchs reportés/forfaits/terminés
    python check_matchsheets.py --date 05/02/2026 --include-cancelled
    
    # Exporter en CSV
    python check_matchsheets.py --date 05/02/2026 --export rapport.csv

Auteur: PyCalendar Team
"""

import sys
import argparse
import json
import time
import re
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any, Tuple
from collections import defaultdict
from enum import Enum

import requests
from bs4 import BeautifulSoup

# Configuration des chemins
SCRIPTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPTS_DIR.parent

# Essayer d'importer pandas/rich pour un meilleur affichage
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

# Essayer d'importer reportlab pour l'export PDF
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm, cm
    from reportlab.platypus import SimpleDocTemplate, Table as PDFTable, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich import print as rprint
    HAS_RICH = True
    console = Console()
except ImportError:
    HAS_RICH = False
    console = None


# =============================================================================
# CONSTANTES ET CONFIGURATION
# =============================================================================

BASE_URL = "https://gestion.mysportu.com"
LOGIN_URL = f"{BASE_URL}/auth/login"
MATCHSHEET_URL = f"{BASE_URL}/feuille-de-match/rencontre"

# Identifiants par défaut (peuvent être surchargés par env vars ou arguments)
DEFAULT_USERNAME = "0838827"
DEFAULT_PASSWORD = "CheeGliFFSU2!"

# Mapping des sports pour le filtrage
SPORT_KEYWORDS = {
    'volley': ['VB', 'VOLLEY', 'volleyball'],
    'hand': ['HB', 'HAND', 'handball'],
    'basket': ['BB', 'BASKET', 'basketball'],
    'foot': ['FB', 'FOOT', 'football'],
    'rugby': ['RG', 'RUGBY'],
}

# Emojis pour l'affichage
EMOJI = {
    'volley': '🏐',
    'hand': '🤾',
    'basket': '🏀',
    'foot': '⚽',
    'rugby': '🏉',
    'ok': '✅',
    'ko': '❌',
    'warning': '⚠️',
    'check': '✓',
    'cross': '✗',
    'reporte': '📅',
    'forfait': '🚫',
    'link': '🔗',
}


# =============================================================================
# UTILITAIRES
# =============================================================================

def extraire_institution(nom_equipe: str) -> str:
    """Extrait l'institution du nom de l'équipe.
    
    Ex: 'LYON 1 (4)' -> 'LYON 1'
        'LYON 2 (IEP) (4)' -> 'LYON 2 (IEP)'
        'ENTPE (1)' -> 'ENTPE'
    """
    match = re.match(r'^(.+?)\s*\(\d+\)$', nom_equipe)
    if match:
        return match.group(1).strip()
    return nom_equipe


def get_matchsheet_url(match_id: int) -> str:
    """Retourne l'URL de la feuille de match."""
    return f"{MATCHSHEET_URL}/{match_id}"


# =============================================================================
# CLASSES DE DONNÉES
# =============================================================================

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
    
    def __post_init__(self):
        if not self.institution:
            self.institution = extraire_institution(self.nom)
    
    @property
    def joueurs_ok(self) -> bool:
        """Vérifie si le nombre de joueurs est suffisant."""
        return self.joueurs_inscrits >= self.joueurs_min
    
    @property
    def pret(self) -> bool:
        """Vérifie si l'équipe est prête (joueurs OK et validés)."""
        return self.joueurs_ok and self.joueurs_valide
    
    def status_str(self) -> str:
        """Retourne une chaîne de statut formatée."""
        j_status = f"J:{self.joueurs_inscrits}/{self.joueurs_min}"
        j_status += EMOJI['check'] if self.joueurs_valide else EMOJI['cross']
        s_status = f" S:{self.staffs_inscrits}"
        s_status += EMOJI['check'] if self.staffs_valide else EMOJI['cross']
        return j_status + s_status


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
    arbitres: List[str] = field(default_factory=list)
    officiels_valide: bool = False
    etat: Optional[str] = None  # None, 'T', 'R', 'N'
    forfait: bool = False
    clos: bool = False
    
    @property
    def is_cancelled(self) -> bool:
        """Vérifie si le match est annulé/reporté/forfait."""
        return self.etat in ('R', 'N', 'T') or self.forfait
    
    @property
    def pret(self) -> bool:
        """Vérifie si le match est prêt à être joué."""
        if self.is_cancelled:
            return False
        return (
            self.receveur.pret and 
            self.visiteur.pret and 
            len(self.arbitres) > 0
        )
    
    @property
    def statut_emoji(self) -> str:
        """Retourne l'emoji de statut."""
        if self.etat == 'R':
            return EMOJI['reporte']
        if self.forfait or self.etat == 'N':
            return EMOJI['forfait']
        if self.etat == 'T':
            return EMOJI['ok']  # Terminé
        return EMOJI['ok'] if self.pret else EMOJI['ko']
    
    @property
    def url(self) -> str:
        """Retourne l'URL de la feuille de match."""
        return get_matchsheet_url(self.id)


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
        """Pourcentage de matchs prêts."""
        if self.matchs_total == 0:
            return 0.0
        return (self.matchs_prets / self.matchs_total) * 100


# =============================================================================
# CLIENT API MYSPORTU
# =============================================================================

class MySportUClient:
    """Client pour l'API MySportU."""
    
    def __init__(self, username: str = DEFAULT_USERNAME, password: str = DEFAULT_PASSWORD):
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.logged_in = False
        self._competitions_cache: Optional[List[Dict]] = None
    
    def login(self) -> bool:
        """Connexion à MySportU."""
        try:
            # Récupérer le token CSRF
            resp = self.session.get(LOGIN_URL)
            if resp.status_code != 200:
                return False
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            csrf_input = soup.find('input', {'name': '_token'})
            if not csrf_input:
                return False
            
            csrf_token = csrf_input.get('value')
            
            # Se connecter
            login_data = {
                '_token': csrf_token,
                'username': self.username,
                'password': self.password
            }
            resp = self.session.post(LOGIN_URL, data=login_data, allow_redirects=True)
            
            # Vérifier la connexion
            self.logged_in = 'ffsu_session' in self.session.cookies
            return self.logged_in
            
        except Exception as e:
            print(f"Erreur de connexion: {e}")
            return False
    
    def _api_get(self, url: str) -> Optional[Dict]:
        """Effectue une requête GET à l'API."""
        if not self.logged_in:
            return None
        
        try:
            resp = self.session.get(url, headers={
                'Accept': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            })
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        return None
    
    def get_competitions(self) -> List[Dict]:
        """Récupère la liste des compétitions."""
        if self._competitions_cache is None:
            url = f"{BASE_URL}/feuille-de-match/ajax/competitions"
            data = self._api_get(url)
            self._competitions_cache = data if data else []
        return self._competitions_cache
    
    def get_all_matches(self, show_progress: bool = True) -> List[Dict]:
        """Récupère tous les matchs (paginés)."""
        all_matches = []
        page = 1
        last_page = None
        
        if show_progress and HAS_RICH:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Récupération des matchs...", total=None)
                
                while True:
                    url = f"{BASE_URL}/feuille-de-match/rencontres?page={page}"
                    data = self._api_get(url)
                    
                    if not data or 'data' not in data:
                        break
                    
                    matches = data['data']
                    if not matches:
                        break
                    
                    # Extraire la pagination de 'meta'
                    meta = data.get('meta', {})
                    if last_page is None:
                        last_page = meta.get('last_page', 1)
                    
                    all_matches.extend(matches)
                    progress.update(task, description=f"Récupération des matchs... ({len(all_matches)} trouvés, page {page}/{last_page})")
                    
                    if page >= last_page:
                        break
                    
                    page += 1
                    time.sleep(0.05)
        else:
            while True:
                url = f"{BASE_URL}/feuille-de-match/rencontres?page={page}"
                data = self._api_get(url)
                
                if not data or 'data' not in data:
                    break
                
                matches = data['data']
                if not matches:
                    break
                
                # Extraire la pagination de 'meta'
                meta = data.get('meta', {})
                if last_page is None:
                    last_page = meta.get('last_page', 1)
                
                all_matches.extend(matches)
                
                if page >= last_page:
                    break
                
                page += 1
                time.sleep(0.05)
        
        return all_matches
    
    def get_match_details(self, match_id: int) -> Optional[Dict]:
        """Récupère les détails d'un match."""
        url = f"{BASE_URL}/feuille-de-match/rencontre/{match_id}"
        return self._api_get(url)
    
    def get_match_participants(self, match_id: int) -> Optional[Dict]:
        """Récupère les participants d'un match (joueurs et staffs)."""
        url = f"{BASE_URL}/feuille-de-match/rencontre/{match_id}/participants"
        return self._api_get(url)
    
    def analyze_match(self, match_id: int, match_data: Optional[Dict] = None) -> Optional[MatchStatus]:
        """Analyse complète d'un match."""
        # Récupérer les détails du match
        details = self.get_match_details(match_id)
        if not details:
            return None
        
        rencontre = details.get('rencontre', {})
        
        # Récupérer les participants
        participants = self.get_match_participants(match_id)
        joueurs_list = participants.get('joueurs', []) if participants else []
        staffs_list = participants.get('staffs', []) if participants else []
        
        # Infos de base
        infos = rencontre.get('infosRencontre', {})
        date_str = infos.get('date_rencontre', 'N/A')
        date_parts = date_str.split(' ') if date_str != 'N/A' else ['N/A', 'N/A']
        date = date_parts[0] if len(date_parts) > 0 else 'N/A'
        heure = date_parts[1] if len(date_parts) > 1 else 'N/A'
        
        # Règles
        regles = rencontre.get('regles', {})
        joueurs_min = int(regles.get('nombre_joueurs_min', 6) or 6)
        
        # Équipes
        receveur_info = rencontre.get('receveur', {})
        visiteur_info = rencontre.get('visiteur', {})
        
        receveur_id = receveur_info.get('id')
        visiteur_id = visiteur_info.get('id')
        
        # Compter les participants par équipe
        joueurs_by_team = defaultdict(list)
        staffs_by_team = defaultdict(list)
        
        for j in joueurs_list:
            joueurs_by_team[j.get('equipe_id')].append(j)
        for s in staffs_list:
            staffs_by_team[s.get('equipe_id')].append(s)
        
        # Validations
        validations = {v.get('equipe_id'): v for v in rencontre.get('validations', [])}
        
        val_receveur = validations.get(receveur_id, {})
        val_visiteur = validations.get(visiteur_id, {})
        
        # Créer les statuts d'équipe
        receveur = TeamStatus(
            id=receveur_id or 0,
            nom=receveur_info.get('libelle_court', receveur_info.get('libelle', 'N/A')),
            joueurs_inscrits=len(joueurs_by_team.get(receveur_id, [])),
            joueurs_min=joueurs_min,
            joueurs_valide=val_receveur.get('joueurs_valide', False),
            staffs_inscrits=len(staffs_by_team.get(receveur_id, [])),
            staffs_valide=val_receveur.get('staffs_valide', False),
        )
        
        visiteur = TeamStatus(
            id=visiteur_id or 0,
            nom=visiteur_info.get('libelle_court', visiteur_info.get('libelle', 'N/A')),
            joueurs_inscrits=len(joueurs_by_team.get(visiteur_id, [])),
            joueurs_min=joueurs_min,
            joueurs_valide=val_visiteur.get('joueurs_valide', False),
            staffs_inscrits=len(staffs_by_team.get(visiteur_id, [])),
            staffs_valide=val_visiteur.get('staffs_valide', False),
        )
        
        # Officiels
        officiels = rencontre.get('officiels', [])
        arbitres = [o.get('nom_complet', o.get('nom', 'N/A')) for o in officiels]
        
        # Validation globale des officiels
        val_globale = validations.get(None, {})
        
        # État du match (depuis match_data si disponible)
        etat = None
        forfait = False
        clos = False
        if match_data:
            etat = match_data.get('etat')
            forfait = match_data.get('forfait') is not None
            clos = match_data.get('clos', False)
        
        return MatchStatus(
            id=match_id,
            date=date,
            heure=heure,
            competition=infos.get('competition_libelle', 'N/A'),
            lieu=infos.get('lieu', 'N/A'),
            receveur=receveur,
            visiteur=visiteur,
            arbitres=arbitres,
            officiels_valide=val_globale.get('officiels_valide', False),
            etat=etat,
            forfait=forfait,
            clos=clos,
        )


# =============================================================================
# FILTRAGE ET ANALYSE
# =============================================================================

def filter_matches(
    matches: List[Dict],
    date_filter: Optional[str] = None,
    sport_filter: Optional[str] = None,
    competition_filter: Optional[str] = None,
    include_cancelled: bool = False,
) -> List[Dict]:
    """Filtre les matchs selon les critères."""
    filtered = matches
    
    # Filtre par date
    if date_filter:
        filtered = [
            m for m in filtered
            if (m.get('infosRencontre') or {}).get('date_rencontre', '') and
               (m.get('infosRencontre') or {}).get('date_rencontre', '').startswith(date_filter)
        ]
    
    # Filtre par sport
    if sport_filter:
        sport_key = sport_filter.lower()
        if sport_key in SPORT_KEYWORDS:
            keywords = SPORT_KEYWORDS[sport_key]
            filtered = [
                m for m in filtered
                if any(
                    kw.upper() in ((m.get('infosRencontre') or {}).get('competition_libelle') or '').upper()
                    for kw in keywords
                )
            ]
    
    # Filtre par compétition
    if competition_filter:
        pattern = competition_filter.upper()
        filtered = [
            m for m in filtered
            if pattern in ((m.get('infosRencontre') or {}).get('competition_libelle') or '').upper()
        ]
    
    # Exclure les matchs reportés/forfaits/terminés si demandé
    if not include_cancelled:
        filtered = [
            m for m in filtered
            if m.get('etat') not in ('R', 'N', 'T') and m.get('forfait') is None
        ]
    
    return filtered


def analyze_matches(
    client: MySportUClient,
    matches: List[Dict],
    show_progress: bool = True,
) -> List[MatchStatus]:
    """Analyse tous les matchs."""
    results = []
    
    if show_progress and HAS_RICH:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Analyse des matchs...", total=len(matches))
            
            for match in matches:
                match_id = match.get('id')
                status = client.analyze_match(match_id, match_data=match)
                if status:
                    results.append(status)
                progress.advance(task)
                time.sleep(0.05)
    else:
        for i, match in enumerate(matches):
            match_id = match.get('id')
            status = client.analyze_match(match_id, match_data=match)
            if status:
                results.append(status)
            if not HAS_RICH:
                print(f"\rAnalyse: {i+1}/{len(matches)}", end='', flush=True)
            time.sleep(0.05)
        if not HAS_RICH:
            print()
    
    return results


def compute_team_stats(results: List[MatchStatus]) -> Dict[str, Dict[str, TeamStats]]:
    """Calcule les statistiques par équipe, groupées par institution."""
    stats_by_institution = defaultdict(dict)
    
    for r in results:
        if r.is_cancelled:
            continue
            
        for team in [r.receveur, r.visiteur]:
            inst = team.institution
            nom = team.nom
            
            if nom not in stats_by_institution[inst]:
                stats_by_institution[inst][nom] = TeamStats(
                    nom=nom,
                    institution=inst,
                )
            
            stats = stats_by_institution[inst][nom]
            stats.matchs_total += 1
            if team.pret:
                stats.matchs_prets += 1
            if team.joueurs_valide:
                stats.joueurs_valides += 1
            if team.staffs_valide:
                stats.staffs_valides += 1
    
    return dict(stats_by_institution)


@dataclass
class TeamMatchInfo:
    """Information d'un match pour une équipe spécifique."""
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
    genre: str = "?"  # F, M ou ?
    # Infos adversaire pour colorisation
    adv_joueurs: int = 0
    adv_joueurs_min: int = 6
    adv_joueurs_valide: bool = False
    adv_staffs: int = 0
    adv_staffs_valide: bool = False
    
    @property
    def pret(self) -> bool:
        """L'équipe est prête si joueurs OK et staff validé."""
        return self.joueurs >= self.joueurs_min and self.joueurs_valide and self.staffs_valide
    
    @property
    def adv_pret(self) -> bool:
        """L'adversaire est prêt si joueurs OK et staff validé."""
        return self.adv_joueurs >= self.adv_joueurs_min and self.adv_joueurs_valide and self.adv_staffs_valide
    
    def status_str(self) -> str:
        """Retourne le statut formaté."""
        j_ok = self.joueurs >= self.joueurs_min
        return f"J:{self.joueurs}/{self.joueurs_min}{'✓' if self.joueurs_valide else '✗'} S:{self.staffs}{'✓' if self.staffs_valide else '✗'}"


def extract_genre_from_competition(competition: str) -> str:
    """Extrait le genre depuis le nom de la compétition."""
    comp_upper = competition.upper()
    # Patterns pour féminin
    if 'VBF' in comp_upper or 'HBF' in comp_upper or 'BBF' in comp_upper:
        return 'F'
    if 'DAMES' in comp_upper or 'FEM' in comp_upper or 'FEMININE' in comp_upper:
        return 'F'
    # Patterns pour masculin
    if 'VBM' in comp_upper or 'HBM' in comp_upper or 'BBM' in comp_upper:
        return 'M'
    if 'MESSIEURS' in comp_upper or 'MASC' in comp_upper or 'MASCULIN' in comp_upper:
        return 'M'
    return '?'


def organize_matches_by_team(results: List[MatchStatus]) -> Dict[str, Dict[str, List[TeamMatchInfo]]]:
    """Organise les matchs par institution puis par équipe."""
    by_institution = defaultdict(lambda: defaultdict(list))
    
    for r in results:
        if r.is_cancelled:
            continue
        
        # Extraire le genre de la compétition
        genre = extract_genre_from_competition(r.competition)
        
        # Info pour le receveur
        rec_info = TeamMatchInfo(
            match_id=r.id,
            heure=r.heure,
            equipe=r.receveur.nom,
            adversaire=r.visiteur.nom,
            is_home=True,
            joueurs=r.receveur.joueurs_inscrits,
            joueurs_min=r.receveur.joueurs_min,
            joueurs_valide=r.receveur.joueurs_valide,
            staffs=r.receveur.staffs_inscrits,
            staffs_valide=r.receveur.staffs_valide,
            arbitres=len(r.arbitres),
            url=r.url,
            genre=genre,
            adv_joueurs=r.visiteur.joueurs_inscrits,
            adv_joueurs_min=r.visiteur.joueurs_min,
            adv_joueurs_valide=r.visiteur.joueurs_valide,
            adv_staffs=r.visiteur.staffs_inscrits,
            adv_staffs_valide=r.visiteur.staffs_valide,
        )
        by_institution[r.receveur.institution][r.receveur.nom].append(rec_info)
        
        # Info pour le visiteur
        vis_info = TeamMatchInfo(
            match_id=r.id,
            heure=r.heure,
            equipe=r.visiteur.nom,
            adversaire=r.receveur.nom,
            is_home=False,
            joueurs=r.visiteur.joueurs_inscrits,
            joueurs_min=r.visiteur.joueurs_min,
            joueurs_valide=r.visiteur.joueurs_valide,
            staffs=r.visiteur.staffs_inscrits,
            staffs_valide=r.visiteur.staffs_valide,
            arbitres=len(r.arbitres),
            url=r.url,
            genre=genre,
            adv_joueurs=r.receveur.joueurs_inscrits,
            adv_joueurs_min=r.receveur.joueurs_min,
            adv_joueurs_valide=r.receveur.joueurs_valide,
            adv_staffs=r.receveur.staffs_inscrits,
            adv_staffs_valide=r.receveur.staffs_valide,
        )
        by_institution[r.visiteur.institution][r.visiteur.nom].append(vis_info)
    
    return dict(by_institution)


# =============================================================================
# AFFICHAGE
# =============================================================================

def print_report_rich(results: List[MatchStatus], verbose: bool = False, show_links: bool = False):
    """Affiche le rapport avec Rich."""
    if not HAS_RICH:
        print_report_simple(results, verbose, show_links)
        return
    
    # Filtrer les matchs actifs (non annulés) pour les stats
    active_results = [r for r in results if not r.is_cancelled]
    cancelled_results = [r for r in results if r.is_cancelled]
    
    # Statistiques
    total = len(active_results)
    prets = sum(1 for r in active_results if r.pret)
    non_prets = total - prets
    
    # Panel de résumé
    summary = f"[bold green]{prets}[/] prêts / [bold red]{non_prets}[/] non prêts sur [bold]{total}[/] matchs"
    if cancelled_results:
        summary += f"\n[dim]({len(cancelled_results)} matchs reportés/forfaits exclus)[/]"
    console.print(Panel(summary, title="📋 Résumé", border_style="blue"))
    
    # Tableau des matchs
    table = Table(title="État des feuilles de match", show_header=True, header_style="bold magenta")
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
    
    for r in results:
        if r.is_cancelled:
            continue
            
        rec_style = "green" if r.receveur.pret else "red"
        vis_style = "green" if r.visiteur.pret else "red"
        arb_str = f"{len(r.arbitres)} arb."
        arb_style = "green" if len(r.arbitres) > 0 else "red"
        
        row = [
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
            row.append(f"[link={r.url}]{EMOJI['link']}[/link]")
        
        table.add_row(*row)
    
    console.print(table)
    
    # Détails si demandé
    if verbose:
        console.print("\n[bold]Détails des matchs non prêts:[/]")
        for r in results:
            if r.is_cancelled or r.pret:
                continue
                
            console.print(f"\n[bold]{r.id}[/]: {r.receveur.nom} vs {r.visiteur.nom}")
            console.print(f"  Compétition: {r.competition}")
            console.print(f"  Lieu: {r.lieu}")
            if show_links:
                console.print(f"  Lien: {r.url}")
            
            issues = []
            if not r.receveur.joueurs_ok:
                issues.append(f"  ❌ {r.receveur.nom}: {r.receveur.joueurs_inscrits}/{r.receveur.joueurs_min} joueurs")
            if not r.receveur.joueurs_valide:
                issues.append(f"  ❌ {r.receveur.nom}: effectif non validé")
            if not r.visiteur.joueurs_ok:
                issues.append(f"  ❌ {r.visiteur.nom}: {r.visiteur.joueurs_inscrits}/{r.visiteur.joueurs_min} joueurs")
            if not r.visiteur.joueurs_valide:
                issues.append(f"  ❌ {r.visiteur.nom}: effectif non validé")
            if len(r.arbitres) == 0:
                issues.append("  ❌ Pas d'arbitre assigné")
            
            for issue in issues:
                console.print(issue)


def print_report_simple(results: List[MatchStatus], verbose: bool = False, show_links: bool = False):
    """Affiche le rapport sans Rich."""
    active_results = [r for r in results if not r.is_cancelled]
    cancelled_results = [r for r in results if r.is_cancelled]
    
    total = len(active_results)
    prets = sum(1 for r in active_results if r.pret)
    non_prets = total - prets
    
    print("\n" + "=" * 60)
    print(f"RÉSUMÉ: {prets} prêts / {non_prets} non prêts sur {total} matchs")
    if cancelled_results:
        print(f"({len(cancelled_results)} matchs reportés/forfaits exclus)")
    print("=" * 60)
    
    header = f"{'ID':<8} {'Heure':<6} {'Receveur':<15} {'Rec.Status':<12} {'Visiteur':<15} {'Vis.Status':<12} {'Arb.':<6} {'Prêt'}"
    if show_links:
        header += " Lien"
    print(f"\n{header}")
    print("-" * (90 + (50 if show_links else 0)))
    
    for r in results:
        if r.is_cancelled:
            continue
            
        arb_str = f"{len(r.arbitres)} arb."
        line = f"{r.id:<8} {r.heure:<6} {r.receveur.nom[:14]:<15} {r.receveur.status_str():<12} {r.visiteur.nom[:14]:<15} {r.visiteur.status_str():<12} {arb_str:<6} {r.statut_emoji}"
        if show_links:
            line += f" {r.url}"
        print(line)
    
    if verbose:
        print("\n" + "=" * 60)
        print("DÉTAILS DES MATCHS NON PRÊTS")
        print("=" * 60)
        
        for r in results:
            if r.is_cancelled or r.pret:
                continue
                
            print(f"\n{r.id}: {r.receveur.nom} vs {r.visiteur.nom}")
            print(f"  Compétition: {r.competition}")
            if show_links:
                print(f"  Lien: {r.url}")
            
            if not r.receveur.joueurs_ok:
                print(f"  ❌ {r.receveur.nom}: {r.receveur.joueurs_inscrits}/{r.receveur.joueurs_min} joueurs")
            if not r.receveur.joueurs_valide:
                print(f"  ❌ {r.receveur.nom}: effectif non validé")
            if not r.visiteur.joueurs_ok:
                print(f"  ❌ {r.visiteur.nom}: {r.visiteur.joueurs_inscrits}/{r.visiteur.joueurs_min} joueurs")
            if not r.visiteur.joueurs_valide:
                print(f"  ❌ {r.visiteur.nom}: effectif non validé")
            if len(r.arbitres) == 0:
                print("  ❌ Pas d'arbitre assigné")


def print_report_by_team_rich(results: List[MatchStatus], show_links: bool = False):
    """Affiche le rapport par équipe avec Rich - format condensé."""
    if not HAS_RICH:
        print_report_by_team_simple(results, show_links)
        return
    
    from rich.text import Text
    from rich.rule import Rule
    
    by_institution = organize_matches_by_team(results)
    
    # Calculer les totaux par institution
    inst_stats = {}
    for inst, teams in by_institution.items():
        total = sum(len(matches) for matches in teams.values())
        prets = sum(1 for matches in teams.values() for m in matches if m.pret)
        inst_stats[inst] = (total, prets)
    
    # Trier les institutions par nom
    sorted_insts = sorted(inst_stats.keys())
    
    # Panel de résumé
    total_matchs = sum(s[0] for s in inst_stats.values())
    total_prets = sum(s[1] for s in inst_stats.values())
    summary = f"[bold]{len(inst_stats)}[/] institutions | [bold green]{total_prets}[/] matchs prêts / [bold]{total_matchs}[/] total"
    console.print(Panel(summary, title="📊 État par équipe", border_style="blue"))
    
    for inst in sorted_insts:
        teams = by_institution[inst]
        inst_total, inst_prets = inst_stats[inst]
        taux = (inst_prets / inst_total * 100) if inst_total > 0 else 0
        
        # Couleur selon le taux
        if taux >= 80:
            inst_color = "green"
        elif taux >= 50:
            inst_color = "yellow"
        else:
            inst_color = "red"
        
        # En-tête de l'institution
        console.print()
        inst_title = f"[bold]{inst}[/bold] [dim]—[/dim] [{inst_color}]{taux:.0f}%[/{inst_color}] [dim]({inst_prets}/{inst_total})[/dim]"
        console.print(Rule(inst_title, style="blue"))
        
        # Tableau pour cette institution
        table = Table(
            show_header=True,
            header_style="bold cyan",
            border_style="dim",
            box=None,
            pad_edge=False,
            show_edge=False,
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
        
        # Trier les équipes par nom
        sorted_teams = sorted(teams.keys())
        
        for team_name in sorted_teams:
            matches = teams[team_name]
            sorted_matches = sorted(matches, key=lambda m: m.heure)
            
            for m in sorted_matches:
                # Couleurs selon le statut des joueurs
                j_ok = m.joueurs >= m.joueurs_min
                j_color = "green" if j_ok and m.joueurs_valide else ("yellow" if j_ok else "red")
                
                # Couleurs du staff : vert si validé, jaune si présent mais non validé, rouge sinon
                s_color = "green" if m.staffs_valide else ("yellow" if m.staffs > 0 else "red")
                
                # OK = joueurs prêts ET staff validé
                status_emoji = "✅" if m.pret else "❌"
                
                # Couleur de l'adversaire : vert si prêt, rouge sinon
                adv_color = "green" if m.adv_pret else "red"
                
                # Formatage des colonnes
                joueurs_str = Text()
                joueurs_str.append(f"{m.joueurs}/{m.joueurs_min}", style=j_color)
                joueurs_str.append(" ✓" if m.joueurs_valide else " ✗", style="green" if m.joueurs_valide else "red")
                
                staff_str = Text()
                staff_str.append(f"{m.staffs}", style=s_color)
                staff_str.append(" ✓" if m.staffs_valide else " ✗", style="green" if m.staffs_valide else "red")
                
                # Genre avec couleur
                genre_str = Text(m.genre, style="magenta" if m.genre == "F" else ("blue" if m.genre == "M" else "dim"))
                
                # Adversaire avec couleur selon son statut
                adv_str = Text(m.adversaire[:17], style=adv_color)
                
                row = [
                    m.heure,
                    genre_str,
                    Text(f"{team_name[:17]}", style="bold"),
                    adv_str,
                    joueurs_str,
                    staff_str,
                    status_emoji,
                ]
                if show_links:
                    row.append(f"[link={m.url}]🔗[/link]")
                
                table.add_row(*row)
        
        console.print(table)


def print_report_by_team_simple(results: List[MatchStatus], show_links: bool = False):
    """Affiche le rapport par équipe sans Rich - format condensé."""
    by_institution = organize_matches_by_team(results)
    
    # Calculer les totaux
    inst_stats = {}
    for inst, teams in by_institution.items():
        total = sum(len(matches) for matches in teams.values())
        prets = sum(1 for matches in teams.values() for m in matches if m.pret)
        inst_stats[inst] = (total, prets)
    
    sorted_insts = sorted(inst_stats.keys())
    
    total_matchs = sum(s[0] for s in inst_stats.values())
    total_prets = sum(s[1] for s in inst_stats.values())
    
    print("\n" + "=" * 80)
    print(f"ÉTAT PAR ÉQUIPE")
    print(f"{len(inst_stats)} institutions | {total_prets} matchs prêts / {total_matchs} total")
    print("=" * 80)
    
    header = f"{'Heure':<6} {'G':<2} {'Équipe':<18} {'Adversaire':<18} {'Joueurs':<10} {'Staff':<6} {'OK'}"
    if show_links:
        header += " Lien"
    
    for inst in sorted_insts:
        teams = by_institution[inst]
        inst_total, inst_prets = inst_stats[inst]
        taux = (inst_prets / inst_total * 100) if inst_total > 0 else 0
        
        print(f"\n▶ {inst} — {taux:.0f}% ({inst_prets}/{inst_total})")
        print("-" * 80)
        print(header)
        
        sorted_teams = sorted(teams.keys())
        for team_name in sorted_teams:
            matches = teams[team_name]
            sorted_matches = sorted(matches, key=lambda m: m.heure)
            
            for m in sorted_matches:
                j_str = f"{m.joueurs}/{m.joueurs_min}{'✓' if m.joueurs_valide else '✗'}"
                s_str = f"{m.staffs}{'✓' if m.staffs_valide else '✗'}"
                status = "✅" if m.pret else "❌"
                
                line = f"{m.heure:<6} {m.genre:<2} {team_name[:17]:<18} {m.adversaire[:17]:<18} {j_str:<10} {s_str:<6} {status}"
                if show_links:
                    line += f" {m.url}"
                print(line)


def export_to_csv(results: List[MatchStatus], filepath: str, include_links: bool = False):
    """Exporte les résultats en CSV."""
    if not HAS_PANDAS:
        print("pandas requis pour l'export CSV. Installez-le avec: pip install pandas")
        return
    
    data = []
    for r in results:
        row = {
            'ID': r.id,
            'Date': r.date,
            'Heure': r.heure,
            'Competition': r.competition,
            'Lieu': r.lieu,
            'Etat': r.etat or 'A_JOUER',
            'Forfait': r.forfait,
            'Receveur': r.receveur.nom,
            'Rec_Institution': r.receveur.institution,
            'Rec_Joueurs': r.receveur.joueurs_inscrits,
            'Rec_Min': r.receveur.joueurs_min,
            'Rec_Valide': r.receveur.joueurs_valide,
            'Rec_Staffs': r.receveur.staffs_inscrits,
            'Rec_Pret': r.receveur.pret,
            'Visiteur': r.visiteur.nom,
            'Vis_Institution': r.visiteur.institution,
            'Vis_Joueurs': r.visiteur.joueurs_inscrits,
            'Vis_Min': r.visiteur.joueurs_min,
            'Vis_Valide': r.visiteur.joueurs_valide,
            'Vis_Staffs': r.visiteur.staffs_inscrits,
            'Vis_Pret': r.visiteur.pret,
            'Nb_Arbitres': len(r.arbitres),
            'Arbitres': ', '.join(r.arbitres),
            'Pret': r.pret,
        }
        if include_links:
            row['Lien'] = r.url
        data.append(row)
    
    df = pd.DataFrame(data)
    df.to_csv(filepath, index=False, encoding='utf-8-sig')
    print(f"Export CSV: {filepath}")


def export_to_pdf(results: List[MatchStatus], filepath: str, date_str: str = "", 
                  competition_str: str = "", by_team: bool = False, include_links: bool = False):
    """Exporte les résultats en PDF avec un design professionnel."""
    if not HAS_REPORTLAB:
        print("reportlab requis pour l'export PDF. Installez-le avec: pip install reportlab")
        return
    
    # Créer le document
    doc = SimpleDocTemplate(
        filepath,
        pagesize=landscape(A4),
        rightMargin=1*cm,
        leftMargin=1*cm,
        topMargin=1.5*cm,
        bottomMargin=1*cm,
    )
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1a365d'),
        spaceAfter=20,
        alignment=TA_CENTER,
    )
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#4a5568'),
        spaceAfter=15,
        alignment=TA_CENTER,
    )
    inst_header_style = ParagraphStyle(
        'InstHeader',
        parent=styles['Heading2'],
        fontSize=13,
        textColor=colors.white,
        spaceBefore=15,
        spaceAfter=5,
        alignment=TA_LEFT,
        backColor=colors.HexColor('#2b6cb0'),
        borderPadding=(5, 10, 5, 10),
    )
    
    elements = []
    
    # Titre
    title = f"📋 État des Feuilles de Match"
    elements.append(Paragraph(title, title_style))
    
    # Sous-titre avec date et compétition
    subtitle_parts = []
    if date_str:
        subtitle_parts.append(f"Date : {date_str}")
    if competition_str:
        subtitle_parts.append(f"Compétition : {competition_str}")
    if subtitle_parts:
        elements.append(Paragraph(" | ".join(subtitle_parts), subtitle_style))
    
    # Statistiques globales
    active_results = [r for r in results if not r.is_cancelled]
    total = len(active_results)
    prets = sum(1 for r in active_results if r.pret)
    
    stats_text = f"<b>{prets}</b> matchs prêts sur <b>{total}</b> — Taux de complétion : <b>{(prets/total*100) if total > 0 else 0:.0f}%</b>"
    stats_style = ParagraphStyle(
        'Stats',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#2d3748'),
        spaceAfter=20,
        alignment=TA_CENTER,
    )
    elements.append(Paragraph(stats_text, stats_style))
    elements.append(Spacer(1, 10))
    
    # Couleurs pour le statut
    color_ok = colors.HexColor('#48bb78')  # Vert
    color_warning = colors.HexColor('#ed8936')  # Orange
    color_error = colors.HexColor('#f56565')  # Rouge
    color_header = colors.HexColor('#2b6cb0')  # Bleu
    color_header_text = colors.white
    color_row_alt = colors.HexColor('#f7fafc')  # Gris très clair
    color_inst_bg = colors.HexColor('#ebf8ff')  # Bleu très clair
    
    if by_team:
        # Export par équipe
        by_institution = organize_matches_by_team(results)
        sorted_insts = sorted(by_institution.keys())
        
        for inst in sorted_insts:
            teams = by_institution[inst]
            inst_total = sum(len(m) for m in teams.values())
            inst_prets = sum(1 for matches in teams.values() for m in matches if m.pret)
            taux = (inst_prets / inst_total * 100) if inst_total > 0 else 0
            
            # Couleur du taux
            if taux >= 80:
                taux_color = color_ok
            elif taux >= 50:
                taux_color = color_warning
            else:
                taux_color = color_error
            
            # En-tête de l'institution
            inst_para = Paragraph(
                f"<b>{inst}</b> — {taux:.0f}% ({inst_prets}/{inst_total} prêts)",
                inst_header_style
            )
            elements.append(inst_para)
            
            # Données du tableau - colonnes sans location ni arbitre
            if include_links:
                headers = ['Heure', 'Genre', 'Équipe', 'Adversaire', 'Joueurs', 'Staff', '', 'Lien']
                col_widths = [1.5*cm, 1.2*cm, 4.5*cm, 4.5*cm, 2.5*cm, 2*cm, 1*cm, 6*cm]
            else:
                headers = ['Heure', 'Genre', 'Équipe', 'Adversaire', 'Joueurs', 'Staff', '']
                col_widths = [1.5*cm, 1.2*cm, 5*cm, 5*cm, 2.5*cm, 2*cm, 1*cm]
            
            table_data = [headers]
            row_meta = []  # Pour stocker les métadonnées de chaque ligne
            
            sorted_teams = sorted(teams.keys())
            row_idx = 1
            
            for team_name in sorted_teams:
                matches = teams[team_name]
                sorted_matches = sorted(matches, key=lambda m: m.heure)
                
                for m in sorted_matches:
                    j_ok = m.joueurs >= m.joueurs_min
                    j_str = f"{m.joueurs}/{m.joueurs_min} {'✓' if m.joueurs_valide else '✗'}"
                    # Staff avec indicateur
                    s_str = f"{m.staffs} {'✓' if m.staffs_valide else '✗'}"
                    # OK = joueurs prêts ET staff validé
                    status = '✓' if m.pret else '✗'
                    
                    row = [
                        m.heure,
                        m.genre,
                        team_name[:20],
                        m.adversaire[:20],
                        j_str,
                        s_str,
                        status,
                    ]
                    if include_links:
                        row.append(m.url[:40] + '...' if len(m.url) > 40 else m.url)
                    
                    table_data.append(row)
                    # Stocker les métadonnées pour la colorisation
                    row_meta.append({
                        'joueurs_valide': m.joueurs_valide,
                        'joueurs_ok': j_ok,
                        'staffs': m.staffs,
                        'staffs_valide': m.staffs_valide,
                        'pret': m.pret,
                        'adv_pret': m.adv_pret,
                    })
                    row_idx += 1
            
            # Créer le tableau
            table = PDFTable(table_data, colWidths=col_widths)
            
            # Style du tableau
            style_commands = [
                # En-tête
                ('BACKGROUND', (0, 0), (-1, 0), color_header),
                ('TEXTCOLOR', (0, 0), (-1, 0), color_header_text),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('TOPPADDING', (0, 0), (-1, 0), 8),
                
                # Corps
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('ALIGN', (0, 1), (1, -1), 'CENTER'),  # Heure, Genre
                ('ALIGN', (4, 1), (6, -1), 'CENTER'),  # Joueurs, Staff, Status
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
                ('TOPPADDING', (0, 1), (-1, -1), 4),
                
                # Bordures
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                ('LINEBELOW', (0, 0), (-1, 0), 1, color_header),
            ]
            
            # Alternance de couleurs et colorisation selon statuts
            for i in range(1, len(table_data)):
                if i % 2 == 0:
                    style_commands.append(('BACKGROUND', (0, i), (-1, i), color_row_alt))
                
                meta = row_meta[i - 1]
                
                # Couleur des joueurs (colonne 4)
                if meta['joueurs_valide'] and meta['joueurs_ok']:
                    style_commands.append(('TEXTCOLOR', (4, i), (4, i), color_ok))
                elif meta['joueurs_ok']:
                    style_commands.append(('TEXTCOLOR', (4, i), (4, i), color_warning))
                else:
                    style_commands.append(('TEXTCOLOR', (4, i), (4, i), color_error))
                
                # Couleur du staff (colonne 5) : vert si validé, jaune si présent, rouge sinon
                if meta['staffs_valide']:
                    style_commands.append(('TEXTCOLOR', (5, i), (5, i), color_ok))
                elif meta['staffs'] > 0:
                    style_commands.append(('TEXTCOLOR', (5, i), (5, i), color_warning))
                else:
                    style_commands.append(('TEXTCOLOR', (5, i), (5, i), color_error))
                
                # Couleur de l'adversaire (colonne 3) : vert si prêt, rouge sinon
                if meta['adv_pret']:
                    style_commands.append(('TEXTCOLOR', (3, i), (3, i), color_ok))
                else:
                    style_commands.append(('TEXTCOLOR', (3, i), (3, i), color_error))
                
                # Couleur du statut final (colonne 6)
                if meta['pret']:
                    style_commands.append(('TEXTCOLOR', (6, i), (6, i), color_ok))
                    style_commands.append(('FONTNAME', (6, i), (6, i), 'Helvetica-Bold'))
                else:
                    style_commands.append(('TEXTCOLOR', (6, i), (6, i), color_error))
                    style_commands.append(('FONTNAME', (6, i), (6, i), 'Helvetica-Bold'))
            
            table.setStyle(TableStyle(style_commands))
            elements.append(table)
            elements.append(Spacer(1, 15))
    
    else:
        # Export standard (par match)
        if include_links:
            headers = ['ID', 'Heure', 'Receveur', 'Statut Rec.', 'Visiteur', 'Statut Vis.', 'Arb.', '', 'Lien']
            col_widths = [1.2*cm, 1.3*cm, 3.5*cm, 2.8*cm, 3.5*cm, 2.8*cm, 1*cm, 0.8*cm, 5*cm]
        else:
            headers = ['ID', 'Heure', 'Receveur', 'Statut Rec.', 'Visiteur', 'Statut Vis.', 'Arb.', '']
            col_widths = [1.5*cm, 1.5*cm, 4*cm, 3.5*cm, 4*cm, 3.5*cm, 1.2*cm, 1*cm]
        
        table_data = [headers]
        
        for r in active_results:
            rec_status = f"J:{r.receveur.joueurs_inscrits}/{r.receveur.joueurs_min}{'✓' if r.receveur.joueurs_valide else '✗'} S:{r.receveur.staffs_inscrits}{'✓' if r.receveur.staffs_valide else '✗'}"
            vis_status = f"J:{r.visiteur.joueurs_inscrits}/{r.visiteur.joueurs_min}{'✓' if r.visiteur.joueurs_valide else '✗'} S:{r.visiteur.staffs_inscrits}{'✓' if r.visiteur.staffs_valide else '✗'}"
            status = '✓' if r.pret else '✗'
            
            row = [
                str(r.id),
                r.heure,
                r.receveur.nom[:16],
                rec_status,
                r.visiteur.nom[:16],
                vis_status,
                str(len(r.arbitres)),
                status,
            ]
            if include_links:
                row.append(r.url[:35] + '...' if len(r.url) > 35 else r.url)
            
            table_data.append(row)
        
        table = PDFTable(table_data, colWidths=col_widths)
        
        style_commands = [
            # En-tête
            ('BACKGROUND', (0, 0), (-1, 0), color_header),
            ('TEXTCOLOR', (0, 0), (-1, 0), color_header_text),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            
            # Corps
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 1), (1, -1), 'CENTER'),  # ID, Heure
            ('ALIGN', (6, 1), (7, -1), 'CENTER'),  # Arb, Status
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
            ('TOPPADDING', (0, 1), (-1, -1), 5),
            
            # Bordures
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('LINEBELOW', (0, 0), (-1, 0), 1, color_header),
        ]
        
        # Alternance de couleurs et couleurs de statut
        for i in range(1, len(table_data)):
            if i % 2 == 0:
                style_commands.append(('BACKGROUND', (0, i), (-1, i), color_row_alt))
            
            # Couleur du statut final
            row_data = table_data[i]
            if row_data[7] == '✓':
                style_commands.append(('TEXTCOLOR', (7, i), (7, i), color_ok))
                style_commands.append(('FONTNAME', (7, i), (7, i), 'Helvetica-Bold'))
            else:
                style_commands.append(('TEXTCOLOR', (7, i), (7, i), color_error))
                style_commands.append(('FONTNAME', (7, i), (7, i), 'Helvetica-Bold'))
        
        table.setStyle(TableStyle(style_commands))
        elements.append(table)
    
    # Pied de page avec timestamp
    elements.append(Spacer(1, 20))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#718096'),
        alignment=TA_CENTER,
    )
    elements.append(Paragraph(
        f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')} — PyCalendar MySportU",
        footer_style
    ))
    
    # Générer le PDF
    doc.build(elements)
    print(f"Export PDF: {filepath}")


# =============================================================================
# CLI
# =============================================================================

def create_parser() -> argparse.ArgumentParser:
    """Crée le parser d'arguments."""
    parser = argparse.ArgumentParser(
        description="Vérification des feuilles de match MySportU",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  %(prog)s                                    # Matchs du jour
  %(prog)s --date 05/02/2026                  # Matchs d'une date spécifique
  %(prog)s --date 05/02/2026 --sport volley   # Filtrer par sport
  %(prog)s --competition "LYON VBF PH2"       # Filtrer par compétition
  %(prog)s --verbose                          # Afficher les détails
  %(prog)s --by-team                          # Affichage par institution
  %(prog)s --links                            # Inclure les liens
  %(prog)s --include-cancelled                # Inclure reportés/forfaits
  %(prog)s --export rapport.csv               # Exporter en CSV
  %(prog)s --pdf rapport.pdf                  # Exporter en PDF
  %(prog)s --pdf rapport.pdf --by-team        # PDF avec vue par équipe
        """
    )
    
    parser.add_argument(
        '--date', '-d',
        type=str,
        default=None,
        help="Date des matchs au format DD/MM/YYYY (défaut: aujourd'hui)"
    )
    
    parser.add_argument(
        '--sport', '-s',
        type=str,
        choices=['volley', 'hand', 'basket', 'foot', 'rugby'],
        default=None,
        help="Filtrer par sport"
    )
    
    parser.add_argument(
        '--competition', '-c',
        type=str,
        default=None,
        help="Filtrer par nom de compétition (recherche partielle)"
    )
    
    parser.add_argument(
        '--username', '-u',
        type=str,
        default=DEFAULT_USERNAME,
        help="Identifiant MySportU"
    )
    
    parser.add_argument(
        '--password', '-p',
        type=str,
        default=DEFAULT_PASSWORD,
        help="Mot de passe MySportU"
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help="Afficher les détails des matchs non prêts"
    )
    
    parser.add_argument(
        '--by-team', '-t',
        action='store_true',
        help="Affichage des statistiques par équipe/institution"
    )
    
    parser.add_argument(
        '--links', '-l',
        action='store_true',
        help="Inclure les liens vers les feuilles de match"
    )
    
    parser.add_argument(
        '--include-cancelled',
        action='store_true',
        help="Inclure les matchs reportés, forfaits et terminés"
    )
    
    parser.add_argument(
        '--export', '-e',
        type=str,
        default=None,
        help="Exporter les résultats en CSV"
    )
    
    parser.add_argument(
        '--pdf',
        type=str,
        default=None,
        help="Exporter les résultats en PDF"
    )
    
    parser.add_argument(
        '--list-competitions',
        action='store_true',
        help="Lister les compétitions disponibles et quitter"
    )
    
    parser.add_argument(
        '--no-progress',
        action='store_true',
        help="Désactiver les barres de progression"
    )
    
    return parser


def main():
    """Point d'entrée principal."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Créer le client
    client = MySportUClient(args.username, args.password)
    
    # Connexion
    if HAS_RICH:
        with console.status("[bold green]Connexion à MySportU..."):
            if not client.login():
                console.print("[bold red]Erreur de connexion à MySportU")
                sys.exit(1)
        console.print("[green]✓ Connecté à MySportU")
    else:
        print("Connexion à MySportU...")
        if not client.login():
            print("Erreur de connexion à MySportU")
            sys.exit(1)
        print("✓ Connecté à MySportU")
    
    # Lister les compétitions si demandé
    if args.list_competitions:
        competitions = client.get_competitions()
        
        # Grouper par sport
        by_sport = defaultdict(list)
        for c in competitions:
            libelle = c.get('libelle', 'N/A')
            sport = 'Autre'
            for sport_key, keywords in SPORT_KEYWORDS.items():
                if any(kw.upper() in libelle.upper() for kw in keywords):
                    sport = sport_key.capitalize()
                    break
            by_sport[sport].append(c)
        
        for sport, comps in sorted(by_sport.items()):
            print(f"\n=== {sport.upper()} ({len(comps)} compétitions) ===")
            for c in comps:
                print(f"  {c.get('id')}: {c.get('libelle')}")
        
        sys.exit(0)
    
    # Déterminer la date
    if args.date:
        date_filter = args.date
    else:
        date_filter = datetime.now().strftime('%d/%m/%Y')
    
    if HAS_RICH:
        console.print(f"[bold]Date sélectionnée:[/] {date_filter}")
        if not args.include_cancelled:
            console.print("[dim](matchs reportés/forfaits exclus par défaut, utilisez --include-cancelled pour les inclure)[/]")
    else:
        print(f"Date sélectionnée: {date_filter}")
        if not args.include_cancelled:
            print("(matchs reportés/forfaits exclus par défaut)")
    
    # Récupérer tous les matchs
    show_progress = not args.no_progress
    all_matches = client.get_all_matches(show_progress=show_progress)
    
    if HAS_RICH:
        console.print(f"[dim]Total: {len(all_matches)} matchs récupérés[/]")
    else:
        print(f"Total: {len(all_matches)} matchs récupérés")
    
    # Filtrer
    filtered = filter_matches(
        all_matches,
        date_filter=date_filter,
        sport_filter=args.sport,
        competition_filter=args.competition,
        include_cancelled=args.include_cancelled,
    )
    
    if not filtered:
        if HAS_RICH:
            console.print("[yellow]Aucun match trouvé pour les critères spécifiés[/]")
        else:
            print("Aucun match trouvé pour les critères spécifiés")
        sys.exit(0)
    
    if HAS_RICH:
        console.print(f"[bold]{len(filtered)} matchs[/] correspondent aux critères")
    else:
        print(f"{len(filtered)} matchs correspondent aux critères")
    
    # Analyser
    results = analyze_matches(client, filtered, show_progress=show_progress)
    
    # Afficher le rapport
    if args.by_team:
        if HAS_RICH:
            print_report_by_team_rich(results, args.links)
        else:
            print_report_by_team_simple(results, args.links)
    else:
        if HAS_RICH:
            print_report_rich(results, args.verbose, args.links)
        else:
            print_report_simple(results, args.verbose, args.links)
    
    # Exporter si demandé
    if args.export:
        export_to_csv(results, args.export, include_links=args.links)
    
    # Exporter en PDF si demandé
    if args.pdf:
        export_to_pdf(
            results, 
            args.pdf, 
            date_str=date_filter,
            competition_str=args.competition or "",
            by_team=args.by_team,
            include_links=args.links
        )


if __name__ == '__main__':
    main()
