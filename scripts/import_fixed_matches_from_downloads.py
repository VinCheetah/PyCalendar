#!/usr/bin/env python3
"""
Import fixed matches from local Downloads files named J[number].xlsx

This script reuses the existing ImporteurMatchsExternes class (CLI importer)
to import matchday files placed in the user's `Downloads` folder. It provides
options to import a single week (`--week`) or all files up to a given week
(`--up-to-week`). Files must be named like `J3.xlsx`, `J10.xlsx`, etc.

Usage examples:
  python scripts/import_fixed_matches_from_downloads.py --config configs/config_volley.yaml --week 3
  python scripts/import_fixed_matches_from_downloads.py --config configs/config_volley.yaml --up-to-week 6 --dry-run

Note: this script must be run from the project root so relative config paths
resolve correctly. It will add project root to `sys.path` similarly to other
scripts in `scripts/`.
"""

import sys
from pathlib import Path
import argparse
import re
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional

# Add project root so we can import package modules
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

SRC_ROOT = PROJECT_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

try:
    from pycalendar.cli.external_importer import ImporteurMatchsExternes
except Exception as e:
    print(f"❌ Impossible d'importer ImporteurMatchsExternes: {e}")
    raise

DEFAULT_HISTORY_FILE = PROJECT_ROOT / 'temp_tests' / 'import_fixed_history.json'


def find_download_files(pattern=r'^J(\d+)\.xlsx$', downloads_dir: Path = None):
    downloads_dir = downloads_dir or Path.home() / 'Downloads'
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


def load_history(path: Path) -> Dict[str, Dict]:
    if not path or not path.exists():
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as exc:
        print(f"⚠️  Historique illisible ({path}): {exc}. Réinitialisation.")
        return {}


def save_history(path: Path, history: Dict[str, Dict]):
    if not path:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=True, indent=2)


def file_signature(path: Path) -> Dict[str, float]:
    stat = path.stat()
    return {'size': stat.st_size, 'mtime': stat.st_mtime}


def main():
    parser = argparse.ArgumentParser(
        description="Import fixed matches from Downloads/J[number].xlsx files"
    )
    parser.add_argument('--config', required=True, help='Path to config YAML (e.g. configs/config_volley.yaml)')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--week', type=int, help='Import a single week number (e.g. 3)')
    group.add_argument('--up-to-week', type=int, help='Import all files with week <= this number')
    parser.add_argument('--sport', default='VB', help='Sport code (default VB)')
    parser.add_argument('--dry-run', action='store_true', help='Do not modify files, only simulate')
    parser.add_argument('--ignore-annules', dest='ignore_annules', action='store_true', default=True, help='Ignore matches marked as cancelled (default)')
    parser.add_argument('--garder-annules', dest='ignore_annules', action='store_false', help='Import matches even if marked as cancelled')
    parser.add_argument('--downloads-dir', help='Override Downloads folder path (useful for testing)')
    parser.add_argument('--history-file', help=f'Path to history JSON (default: {DEFAULT_HISTORY_FILE})')
    parser.add_argument('--no-history', action='store_true', help='Disable history tracking/skipping')
    parser.add_argument('--force', action='store_true', help='Re-import files even if unchanged since last run')

    args = parser.parse_args()

    downloads_dir = Path(args.downloads_dir) if args.downloads_dir else Path.home() / 'Downloads'
    files = find_download_files(downloads_dir=downloads_dir)

    if not files:
        print(f"Aucun fichier 'J[number].xlsx' trouvé dans {downloads_dir}")
        return

    # Select files to import
    if args.week is not None:
        sel = [f for (w, f) in files if w == args.week]
        if not sel:
            print(f"Aucun fichier J{args.week}.xlsx trouvé dans {downloads_dir}")
            return
    else:
        sel = [f for (w, f) in files if w <= args.up_to_week]
        if not sel:
            print(f"Aucun fichier J<= {args.up_to_week} trouvé dans {downloads_dir}")
            return

    print(f"🔎 Trouvé {len(sel)} fichier(s) à importer: {[p.name for p in sel]}")

    history_enabled = not args.no_history
    history_path = Path(args.history_file) if args.history_file else DEFAULT_HISTORY_FILE
    history: Dict[str, Dict] = load_history(history_path) if history_enabled else {}
    results: List[Dict[str, Optional[str]]] = []

    for p in sel:
        week_match = re.match(r'^J(\d+)\.xlsx$', p.name, re.IGNORECASE)
        week = int(week_match.group(1)) if week_match else None
        sig = file_signature(p)
        hist_key = str(p.resolve())

        if history_enabled and not args.force:
            past = history.get(hist_key)
            if past and past.get('size') == sig['size'] and abs(past.get('mtime', 0) - sig['mtime']) < 1e-6:
                print(f"\n⏭️  Ignoré {p.name} (inchangé depuis le {past.get('last_imported', 'N/A')}). Utilisez --force pour réimporter.")
                results.append({'file': p.name, 'week': week, 'status': 'skipped'})
                continue

        print(f"\n➡️  Import de {p.name} (J{week})")

        importer = ImporteurMatchsExternes(
            config_path=str(args.config),
            fichier_local=str(p),
            sport=args.sport,
            journee=week,
            dry_run=args.dry_run,
            ignorer_annules=args.ignore_annules
        )

        try:
            importer.executer()
            print(f"✔️  Import {p.name} terminé")
            results.append({'file': p.name, 'week': week, 'status': 'imported'})
            if history_enabled:
                history[hist_key] = {
                    **sig,
                    'week': week,
                    'last_imported': datetime.now(timezone.utc).isoformat(timespec='seconds')
                }
        except Exception as e:
            print(f"❌ Erreur lors de l'import de {p.name}: {e}")
            results.append({'file': p.name, 'week': week, 'status': 'error', 'message': str(e)})

    if history_enabled:
        save_history(history_path, history)

    if results:
        imported = sum(1 for r in results if r['status'] == 'imported')
        skipped = sum(1 for r in results if r['status'] == 'skipped')
        failed = sum(1 for r in results if r['status'] == 'error')
        print("\n📋 Récapitulatif:")
        print(f"   • Imports effectués : {imported}")
        print(f"   • Ignorés (historique): {skipped}")
        print(f"   • Échecs : {failed}")
        if failed:
            for r in results:
                if r['status'] == 'error':
                    print(f"     - {r['file']} (J{r['week']}): {r.get('message', 'Erreur inconnue')}")


if __name__ == '__main__':
    main()
