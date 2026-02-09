#!/usr/bin/env python3
"""
Import des matchs fixes depuis les fichiers J[numéro].xlsx du dossier Downloads.

Ce script importe automatiquement les fichiers de matchs CFE/CFU déposés dans
le dossier Downloads. Les fichiers doivent être nommés J1.xlsx, J2.xlsx, etc.

Usage:
    python scripts/import_fixed_matches.py --config configs/config_volley.yaml --week 3
    python scripts/import_fixed_matches.py --up-to-week 6 --dry-run
    python scripts/import_fixed_matches.py -w 5 --force

Exemples:
    # Importer la semaine 3 pour le volleyball
    python scripts/import_fixed_matches.py -w 3

    # Importer toutes les semaines jusqu'à la 6 (simulation)
    python scripts/import_fixed_matches.py --up-to-week 6 --dry-run

    # Forcer la réimportation (ignorer l'historique)
    python scripts/import_fixed_matches.py -w 4 --force
"""

import sys
from pathlib import Path
import argparse
import re
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import pandas as pd

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from scripts.script_base import (
    ScriptContext,
    print_header,
    print_success,
    print_error,
    print_info,
)
from pycalendar.cli.external_importer import ImporteurMatchsExternes


# ==============================================================================
# Configuration
# ==============================================================================

DEFAULT_HISTORY_FILE = PROJECT_ROOT / 'temp_tests' / 'import_fixed_history.json'
DOWNLOADS_DIR = Path.home() / 'Downloads'


# ==============================================================================
# Métadonnées de fichiers
# ==============================================================================

@dataclass
class MatchFileMetadata:
    """Métadonnées extraites d'un fichier de matchs externes."""

    file_path: Path
    total_rows: int
    rows_with_dates: int
    unique_dates: List[datetime]
    unique_weeks: List[int]
    official_day_rows: int

    @property
    def formatted_dates(self) -> List[str]:
        return [dt.strftime('%d/%m/%Y') for dt in self.unique_dates]

    @property
    def iso_dates(self) -> List[str]:
        return [dt.date().isoformat() for dt in self.unique_dates]

    @property
    def missing_dates(self) -> int:
        return max(0, self.total_rows - self.rows_with_dates)

    @property
    def single_week(self) -> Optional[int]:
        return self.unique_weeks[0] if len(self.unique_weeks) == 1 else None


# ==============================================================================
# Fonctions utilitaires
# ==============================================================================

def find_download_files(downloads_dir: Path = None, pattern: str = r'^J(\d+)\.xlsx$') -> List[Tuple[int, Path]]:
    """Trouve les fichiers J[n].xlsx dans le dossier Downloads."""
    downloads_dir = downloads_dir or DOWNLOADS_DIR
    files = []
    
    if not downloads_dir.exists():
        return files
    
    for p in downloads_dir.iterdir():
        if p.is_file():
            m = re.match(pattern, p.name, re.IGNORECASE)
            if m:
                week = int(m.group(1))
                files.append((week, p))
    
    files.sort(key=lambda x: x[0])
    return files


def file_signature(path: Path) -> Dict[str, float]:
    """Génère une signature de fichier (taille, date de modification)."""
    stat = path.stat()
    return {'size': stat.st_size, 'mtime': stat.st_mtime}


def load_history(path: Path) -> Dict[str, Dict]:
    """Charge l'historique des imports."""
    if not path or not path.exists():
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as exc:
        print(f"⚠️  Historique illisible ({path}): {exc}. Réinitialisation.")
        return {}


def save_history(path: Path, history: Dict[str, Dict]):
    """Sauvegarde l'historique des imports."""
    if not path:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=True, indent=2)


def format_history_dates(date_strings: List[str]) -> List[str]:
    """Convertit les dates ISO en format DD/MM/YYYY."""
    formatted = []
    for value in date_strings or []:
        try:
            formatted.append(datetime.fromisoformat(value).strftime('%d/%m/%Y'))
        except (TypeError, ValueError):
            continue
    return formatted


def weekday_index_from_label(label: str) -> Optional[int]:
    """Convertit un jour de la semaine en index (0=lundi)."""
    mapping = {
        'lundi': 0, 'mardi': 1, 'mercredi': 2, 'jeudi': 3,
        'vendredi': 4, 'samedi': 5, 'dimanche': 6,
        'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
        'friday': 4, 'saturday': 5, 'sunday': 6,
    }
    cleaned = (label or '').strip().lower()
    return mapping.get(cleaned) if cleaned else None


# ==============================================================================
# Chargement et analyse des fichiers
# ==============================================================================

def detect_header_row(df_raw: pd.DataFrame) -> Optional[int]:
    """Trouve la ligne d'en-tête (Date, Sport, ...)."""
    for idx, row in df_raw.iterrows():
        first_value = row.iloc[0] if len(row) > 0 else None
        second_value = row.iloc[1] if len(row) > 1 else None
        first = str(first_value).strip().lower() if pd.notna(first_value) else ''
        second = str(second_value).strip().lower() if pd.notna(second_value) else ''
        if first == 'date' and second == 'sport':
            return idx
    return None


def compute_metadata(
    df: pd.DataFrame,
    file_path: Path,
    calendar_start: Optional[datetime],
    official_weekday: Optional[int]
) -> MatchFileMetadata:
    """Calcule les métadonnées du fichier (dates, semaines, etc.)."""
    total_rows = len(df)
    rows_with_dates = 0
    unique_dates: List[datetime] = []
    unique_weeks: List[int] = []
    official_rows = 0

    if 'Date' in df.columns:
        date_series = pd.to_datetime(df['Date'], errors='coerce', dayfirst=True)
        rows_with_dates = int(date_series.notna().sum())
        normalized = sorted({pd.Timestamp(ts).normalize() for ts in date_series.dropna()})
        unique_dates = [ts.to_pydatetime() for ts in normalized]
        
        if official_weekday is not None:
            official_mask = date_series.dt.weekday.eq(official_weekday).fillna(False)
            official_rows = int(official_mask.sum())
        else:
            official_rows = rows_with_dates

        if calendar_start and rows_with_dates:
            start_date = calendar_start.date()
            weeks_set = set()
            for ts in date_series.dropna():
                if official_weekday is not None and ts.weekday() != official_weekday:
                    continue
                delta_days = (ts.date() - start_date).days
                if delta_days >= 0:
                    weeks_set.add((delta_days // 7) + 1)
            unique_weeks = sorted(weeks_set)

    return MatchFileMetadata(
        file_path=file_path,
        total_rows=total_rows,
        rows_with_dates=rows_with_dates,
        unique_dates=unique_dates,
        unique_weeks=unique_weeks,
        official_day_rows=official_rows
    )


def load_matches_with_metadata(
    file_path: Path,
    calendar_start: Optional[datetime],
    official_weekday: Optional[int]
) -> Tuple[pd.DataFrame, MatchFileMetadata]:
    """Charge le fichier Excel et calcule ses métadonnées."""
    try:
        df_raw = pd.read_excel(file_path, sheet_name=0, header=None, engine='openpyxl')
    except FileNotFoundError:
        raise
    except Exception as exc:
        raise RuntimeError(f"Impossible d'ouvrir {file_path.name}: {exc}") from exc

    header_row = detect_header_row(df_raw)
    if header_row is None:
        raise RuntimeError(
            f"En-têtes introuvables dans {file_path.name} (colonnes 'Date' et 'Sport' attendues)"
        )

    try:
        df = pd.read_excel(file_path, sheet_name=0, header=header_row, engine='openpyxl')
    except Exception as exc:
        raise RuntimeError(f"Impossible de relire {file_path.name}: {exc}") from exc

    df.columns = df.columns.astype(str).str.strip()
    metadata = compute_metadata(df, file_path, calendar_start, official_weekday)
    return df, metadata


def describe_metadata(
    metadata: MatchFileMetadata,
    expected_week: Optional[int],
    calendar_available: bool,
    restrict_to_official_day: bool,
):
    """Affiche un résumé des dates détectées."""
    if not metadata.unique_dates:
        print(f"   ⚠️  Impossible de détecter une date dans {metadata.file_path.name}")
    else:
        print(f"   📅 Dates détectées: {', '.join(metadata.formatted_dates)}")

    if metadata.missing_dates:
        print(f"   ℹ️  {metadata.missing_dates} ligne(s) sans date sur {metadata.total_rows}")

    if calendar_available:
        if metadata.unique_weeks:
            if metadata.single_week:
                print(f"   🗓️  Semaine estimée: J{metadata.single_week}")
                if expected_week and metadata.single_week != expected_week:
                    print(f"   ⚠️  Écart avec la semaine attendue (J{expected_week})")
            else:
                joined_weeks = ', '.join(f"J{wk}" for wk in metadata.unique_weeks)
                print(f"   ⚠️  Dates couvrant plusieurs semaines: {joined_weeks}")
        elif metadata.rows_with_dates and restrict_to_official_day and metadata.official_day_rows == 0:
            print("   ℹ️  Aucune date sur le jour officiel → semaine non calculée")


def load_calendar_settings(ctx: ScriptContext) -> Tuple[Optional[datetime], Optional[int], Optional[str]]:
    """Extrait les paramètres du calendrier depuis la config."""
    config = ctx.config_data
    if not config:
        return None, None, None
    
    calendrier = config.get('calendrier', {})
    raw_date = calendrier.get('date_debut')
    jour_match = calendrier.get('jour_match', 'jeudi')
    official_day_index = weekday_index_from_label(jour_match)

    if not raw_date:
        return None, official_day_index, jour_match

    cleaned = str(raw_date).strip()
    parsed = None
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d/%m/%y'):
        try:
            parsed = datetime.strptime(cleaned, fmt)
            break
        except ValueError:
            continue
    
    return parsed, official_day_index, jour_match


# ==============================================================================
# Main
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Import des matchs fixes depuis Downloads/J[numéro].xlsx",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    # Arguments de base (config requis pour ce script)
    parser.add_argument(
        '--config', '-c',
        type=str,
        default=None,
        help='Fichier de configuration YAML (ex: configs/config_volley.yaml)'
    )
    
    parser.add_argument(
        '--sport',
        type=str,
        default=None,
        help='Code sport (ex: volley, hand). Auto-détecté depuis config si non fourni.'
    )
    
    # Sélection des semaines
    week_group = parser.add_mutually_exclusive_group(required=True)
    week_group.add_argument(
        '-w', '--week',
        type=int,
        help='Importer une seule semaine (ex: 3)'
    )
    week_group.add_argument(
        '--up-to-week',
        type=int,
        help='Importer toutes les semaines jusqu\'à ce numéro'
    )
    
    # Options d'import
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulation: ne modifie aucun fichier'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Réimporter même si le fichier n\'a pas changé'
    )
    parser.add_argument(
        '--no-history',
        action='store_true',
        help='Désactiver le suivi d\'historique'
    )
    
    # Gestion des annulations et doublons
    parser.add_argument(
        '--garder-annules',
        action='store_true',
        help='Importer aussi les matchs marqués comme annulés'
    )
    parser.add_argument(
        '--duplicate-strategy',
        choices=['ancien', 'nouveau'],
        default='ancien',
        help="Gestion des doublons: 'nouveau' remplace les existants (défaut: 'ancien')"
    )
    
    # Options avancées
    parser.add_argument(
        '--downloads-dir',
        type=str,
        default=None,
        help=f'Dossier des téléchargements (défaut: {DOWNLOADS_DIR})'
    )
    parser.add_argument(
        '--history-file',
        type=str,
        default=None,
        help=f'Fichier d\'historique (défaut: {DEFAULT_HISTORY_FILE})'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Mode verbeux'
    )
    
    parser.epilog = """
Exemples:
    python scripts/import_fixed_matches.py -w 3
    python scripts/import_fixed_matches.py --up-to-week 6 --dry-run
    python scripts/import_fixed_matches.py -w 4 --config configs/config_hand.yaml
    python scripts/import_fixed_matches.py -w 5 --force --garder-annules
    """
    
    args = parser.parse_args()
    
    # Créer le contexte
    # Créer un namespace avec les arguments pour from_args
    class ConfigArgs:
        def __init__(self):
            self.config = args.config
            self.sport = args.sport
            self.solution = None
            self.verbose = args.verbose
    
    try:
        ctx = ScriptContext.from_args(ConfigArgs())
    except FileNotFoundError as e:
        print_error(str(e))
        return 1
    
    # Afficher le header
    print_header(f"Import matchs fixes {ctx.sport.name}", ctx.sport.emoji)
    ctx.print_status()
    
    # Paramètres du calendrier
    calendar_start, official_weekday, jour_label = load_calendar_settings(ctx)
    
    # Trouver les fichiers à importer
    downloads_dir = Path(args.downloads_dir) if args.downloads_dir else DOWNLOADS_DIR
    files = find_download_files(downloads_dir)
    
    if not files:
        print_error(f"Aucun fichier J[n].xlsx trouvé dans {downloads_dir}")
        return 1
    
    # Filtrer selon la sélection
    if args.week is not None:
        sel = [f for (w, f) in files if w == args.week]
        if not sel:
            print_error(f"Fichier J{args.week}.xlsx non trouvé dans {downloads_dir}")
            return 1
    else:
        sel = [f for (w, f) in files if w <= args.up_to_week]
        if not sel:
            print_error(f"Aucun fichier J<= {args.up_to_week} trouvé")
            return 1
    
    print()
    print_info(f"Fichiers à importer: {[p.name for p in sel]}")
    
    if calendar_start:
        jour_info = f" | Jour: {jour_label}" if jour_label else ''
        print_info(f"Date début saison: {calendar_start.strftime('%d/%m/%Y')}{jour_info}")
    else:
        print_info("Date de début introuvable → estimation des semaines impossible")
    
    if args.dry_run:
        print_info("⚠️  Mode simulation: aucun fichier ne sera modifié")
    
    # Historique
    history_enabled = not args.no_history
    history_path = Path(args.history_file) if args.history_file else DEFAULT_HISTORY_FILE
    history = load_history(history_path) if history_enabled else {}
    
    results: List[Dict] = []
    sport_code = ctx.sport.code
    
    for p in sel:
        week_match = re.match(r'^J(\d+)\.xlsx$', p.name, re.IGNORECASE)
        week = int(week_match.group(1)) if week_match else None
        sig = file_signature(p)
        hist_key = str(p.resolve())

        # Vérifier l'historique
        if history_enabled and not args.force:
            past = history.get(hist_key)
            if past and past.get('size') == sig['size'] and abs(past.get('mtime', 0) - sig['mtime']) < 1e-6:
                history_dates = format_history_dates(past.get('dates', []))
                date_suffix = f" | Dates: {', '.join(history_dates)}" if history_dates else ''
                print(f"\n⏭️  Ignoré {p.name} (inchangé){date_suffix}")
                results.append({
                    'file': p.name, 'week': week, 'status': 'skipped',
                    'dates': history_dates, 'detected_week': past.get('detected_week')
                })
                continue

        print(f"\n➡️  Import de {p.name} (J{week})")

        # Charger et analyser
        metadata = None
        df_matches = None
        try:
            df_matches, metadata = load_matches_with_metadata(p, calendar_start, official_weekday)
            describe_metadata(
                metadata, week,
                calendar_available=calendar_start is not None,
                restrict_to_official_day=official_weekday is not None
            )
        except Exception as e:
            print(f"   ⚠️  Analyse impossible: {e}")

        effective_week = metadata.single_week if metadata and metadata.single_week else week

        # Importer
        importer = ImporteurMatchsExternes(
            config_path=str(ctx.config_path),
            fichier_local=str(p),
            sport=sport_code,
            journee=effective_week,
            dry_run=args.dry_run,
            ignorer_annules=not args.garder_annules,
            doublon_priorite=args.duplicate_strategy
        )

        if df_matches is not None:
            importer.df_externe = df_matches

        try:
            importer.executer()
            print_success(f"Import {p.name} terminé")
            results.append({
                'file': p.name, 'week': week, 'status': 'imported',
                'dates': metadata.formatted_dates if metadata else [],
                'detected_week': metadata.single_week if metadata else None
            })
            if history_enabled:
                history[hist_key] = {
                    **sig,
                    'week': week,
                    'detected_week': metadata.single_week if metadata else None,
                    'dates': metadata.iso_dates if metadata else [],
                    'last_imported': datetime.now(timezone.utc).isoformat(timespec='seconds')
                }
        except Exception as e:
            print_error(f"Erreur lors de l'import de {p.name}: {e}")
            results.append({
                'file': p.name, 'week': week, 'status': 'error',
                'message': str(e),
                'dates': metadata.formatted_dates if metadata else [],
                'detected_week': metadata.single_week if metadata else None
            })
            if args.verbose:
                import traceback
                traceback.print_exc()

    # Sauvegarder l'historique
    if history_enabled:
        save_history(history_path, history)

    # Récapitulatif
    if results:
        imported = sum(1 for r in results if r['status'] == 'imported')
        skipped = sum(1 for r in results if r['status'] == 'skipped')
        failed = sum(1 for r in results if r['status'] == 'error')
        
        print("\n📋 Récapitulatif:")
        print(f"   • Imports effectués: {imported}")
        print(f"   • Ignorés (historique): {skipped}")
        print(f"   • Échecs: {failed}")
        
        if failed:
            for r in results:
                if r['status'] == 'error':
                    print(f"     - {r['file']}: {r.get('message', 'Erreur inconnue')}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
