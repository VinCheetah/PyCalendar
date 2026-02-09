#!/usr/bin/env python3
"""Calcule et visualise graphiquement les créneaux disponibles.

Le script lit une configuration YAML PyCalendar, charge les gymnases depuis le
fichier Excel, applique les semaines banalisées et les indisponibilités, puis
produit une visualisation graphique claire avec diagnostic détaillé des indispos.

Usage:
    python scripts/compute_available_slots.py --config configs/config_volley.yaml
    python scripts/compute_available_slots.py -c configs/config_hand.yaml -o out.png
    python scripts/compute_available_slots.py -c configs/config_hand.yaml --verbose

Options:
    --output, -o : Fichier PNG (défaut: exports/available_slots_{sport}.png)
    --verbose, -v : Affiche diagnostic des indisponibilités
"""

from __future__ import annotations

import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from scripts.script_base import (
    ScriptContext,
    create_base_parser,
    print_error,
    print_header,
    print_info,
    print_success,
    print_warning,
)
from pycalendar.core.config import Config
from pycalendar.core.calendar_manager import CalendarConfig, CalendarManager
from pycalendar.data.data_source import DataSource
from pycalendar.core.models import Gymnase

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


def _compute_weekly_slots(
    gymnases: List[Gymnase],
    semaines: Iterable[int],
) -> Dict[int, Dict[str, Dict[str, Counter]]]:
    """Calcule les créneaux disponibles pour chaque semaine.
    
    Retourne: {semaine: {horaire: {"total": int, "par_gym": Counter}}}
    """
    weekly: Dict[int, Dict[str, Dict[str, Counter]]] = {}

    for semaine in semaines:
        stats: Dict[str, Dict[str, Counter]] = defaultdict(lambda: {"total": 0, "par_gym": Counter()})

        for gym in gymnases:
            if not gym.horaires_disponibles:
                continue

            for horaire in gym.horaires_disponibles:
                capacite = max(0, gym.get_capacite_disponible(semaine, horaire))
                if capacite <= 0:
                    continue
                stats[horaire]["total"] += capacite
                stats[horaire]["par_gym"][gym.nom] += capacite

        weekly[semaine] = stats

    return weekly


def _aggregate_slots(weekly: Dict[int, Dict[str, Dict[str, Counter]]]) -> Dict[str, Dict[str, Counter]]:
    """Agrège les stats hebdomadaires en total par horaire."""
    aggregated: Dict[str, Dict[str, Counter]] = defaultdict(lambda: {"total": 0, "par_gym": Counter()})

    for stats in weekly.values():
        for horaire, data in stats.items():
            aggregated[horaire]["total"] += data["total"]
            aggregated[horaire]["par_gym"].update(data["par_gym"])

    return aggregated


def _format_banalisees(semaines_banalisees: List[int]) -> str:
    if not semaines_banalisees:
        return "Aucune"
    return ", ".join(str(s) for s in sorted(semaines_banalisees))


def _print_summary(
    stats: Dict[str, Dict[str, Counter]],
    nb_semaines: int,
    semaine_min: int,
    semaines_actives: List[int],
    gymnases: List[Gymnase],
) -> None:
    """Affiche un résumé textuel par horaire."""
    if not stats:
        print_warning("Aucun créneau disponible détecté.")
        return

    total_global = sum(data["total"] for data in stats.values())

    print()
    print_info(f"Semaines actives: {len(semaines_actives)} / {nb_semaines} (à partir de S{semaine_min})")
    print_info(f"Gymnases considérés: {len(gymnases)}")

    header = f"{'Horaire':<8} | {'Créneaux':>14} | Détail par gymnase (capacité × semaines)"
    print(header)
    print("-" * len(header))

    for horaire in sorted(stats.keys()):
        data = stats[horaire]
        detail = ", ".join(f"{nom}={nb}" for nom, nb in data["par_gym"].most_common())
        print(f"{horaire:<8} | {data['total']:>14} | {detail}")

    print()
    print_success(f"Total: {total_global} créneaux disponibles")


def _print_weekly_view(
    weekly: Dict[int, Dict[str, Dict[str, Counter]]],
    calendar_manager: CalendarManager,
) -> None:
    """Affiche une vue hebdomadaire détaillée."""
    if not weekly:
        print_warning("Aucune donnée hebdomadaire.")
        return

    for semaine in sorted(weekly.keys()):
        stats = weekly[semaine]
        if not stats:
            continue

        semaine_label = calendar_manager.formater_semaine(semaine)
        print()
        print_info(semaine_label)

        header = f"{'Horaire':<8} | {'Total':>6} | Gymnases"
        print(header)
        print("-" * len(header))

        for horaire in sorted(stats.keys()):
            data = stats[horaire]
            detail = ", ".join(f"{nom}({nb})" for nom, nb in sorted(data["par_gym"].items()))
            print(f"{horaire:<8} | {data['total']:>6} | {detail}")


def _create_visualizations(
    weekly: Dict[int, Dict[str, Dict[str, Counter]]],
    aggregated: Dict[str, Dict[str, Counter]],
    output_path: Path,
    sport_name: str,
    sport_emoji: str,
) -> None:
    """Crée des graphiques PNG."""
    if not MATPLOTLIB_AVAILABLE:
        print_warning("matplotlib non installé: graphiques non générés")
        return

    try:
        horaires_sorted = sorted(aggregated.keys())
        semaines_sorted = sorted(weekly.keys())

        # Préparer les données
        horaires_totals = [aggregated[h]["total"] for h in horaires_sorted]
        
        # Heatmap (semaine vs horaire)
        heatmap_data = []
        for sem in semaines_sorted:
            row = [weekly[sem].get(h, {}).get("total", 0) for h in horaires_sorted]
            heatmap_data.append(row)
        heatmap_array = np.array(heatmap_data)

        # Créer figure avec 2 subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        fig.suptitle(f'{sport_emoji} Créneaux disponibles - {sport_name}', fontsize=16, fontweight='bold')

        # --- Graphique 1: Total par horaire (barres)
        colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(horaires_sorted)))
        ax1.bar(horaires_sorted, horaires_totals, color=colors, edgecolor='black', linewidth=1.5)
        ax1.set_xlabel('Horaire', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Créneaux disponibles', fontsize=12, fontweight='bold')
        ax1.set_title('Total par horaire (toutes semaines)', fontsize=13, fontweight='bold')
        ax1.grid(axis='y', alpha=0.3, linestyle='--')
        for i, (h, v) in enumerate(zip(horaires_sorted, horaires_totals)):
            ax1.text(i, v + 2, str(int(v)), ha='center', va='bottom', fontweight='bold')

        # --- Graphique 2: Heatmap (semaine vs horaire)
        im = ax2.imshow(heatmap_array, cmap='YlGn', aspect='auto', origin='lower')
        ax2.set_xlabel('Horaire', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Semaine', fontsize=12, fontweight='bold')
        ax2.set_title('Créneaux par semaine et horaire', fontsize=13, fontweight='bold')
        
        ax2.set_xticks(range(len(horaires_sorted)))
        ax2.set_xticklabels(horaires_sorted, rotation=45, ha='right')
        ax2.set_yticks(range(len(semaines_sorted)))
        ax2.set_yticklabels([f'S{s}' for s in semaines_sorted])
        
        # Ajouter les valeurs dans les cellules
        for i, sem in enumerate(semaines_sorted):
            for j, hor in enumerate(horaires_sorted):
                val = heatmap_array[i, j]
                ax2.text(j, i, str(int(val)), ha='center', va='center', 
                        color='white' if val > heatmap_array.max() / 2 else 'black',
                        fontweight='bold', fontsize=9)
        
        # Colorbar
        cbar = plt.colorbar(im, ax=ax2)
        cbar.set_label('Créneaux', fontsize=11, fontweight='bold')

        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print_success(f"Graphiques générés: {output_path}")

    except Exception as e:
        print_warning(f"Erreur lors de la génération des graphiques: {e}")


def main() -> int:
    parser = create_base_parser(
        description="Calcule et visualise graphiquement les créneaux disponibles",
        with_solution=False,
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default=None,
        help='Fichier PNG de sortie (défaut: exports/available_slots_{sport}.png)'
    )

    parser.epilog = """
Exemples:
  python scripts/compute_available_slots.py --config configs/config_volley.yaml
  python scripts/compute_available_slots.py -c configs/config_hand.yaml -o out.png --verbose
    """

    args = parser.parse_args()

    if not args.config:
        print_error("Veuillez fournir --config / -c")
        return 1

    try:
        ctx = ScriptContext.from_args(args)
    except FileNotFoundError as exc:
        print_error(str(exc))
        return 1

    if not ctx.config_path or not ctx.config_path.exists():
        print_error("Configuration YAML introuvable.")
        return 1

    if not ctx.excel_path:
        print_error("Chemin Excel non trouvé dans fichiers.donnees")
        return 1

    config = Config.from_yaml(str(ctx.config_path))

    calendar_config = CalendarConfig(
        date_debut=config.calendrier_date_debut,
        jour_match=config.calendrier_jour_match,
        semaines_banalisees=config.calendrier_semaines_banalisees,
    )
    calendar_manager = CalendarManager(calendar_config)

    semaines_actives = [
        s for s in range(config.semaine_min, config.nb_semaines + 1)
        if not calendar_manager.est_semaine_banalisee(s)
    ]

    print_header(f"Créneaux disponibles - {ctx.sport.name}", ctx.sport.emoji)
    print_info(f"Config: {ctx.config_path.name}")
    print_info(f"Semaines banalisées: {_format_banalisees(calendar_manager.get_semaines_banalisees())}")

    try:
        datasource = DataSource(str(ctx.excel_path), calendar_manager=calendar_manager)
        gymnases = datasource.charger_gymnases()
    except Exception as exc:
        print_error(f"Erreur chargement données: {exc}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

    weekly_stats = _compute_weekly_slots(gymnases, semaines_actives)
    aggregated = _aggregate_slots(weekly_stats)

    _print_summary(aggregated, config.nb_semaines, config.semaine_min, semaines_actives, gymnases)
    _print_weekly_view(weekly_stats, calendar_manager)

    # Générer graphiques
    if args.output:
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = PROJECT_ROOT / output_path
    else:
        output_path = PROJECT_ROOT / "exports" / f"available_slots_{ctx.sport.pattern}.png"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    _create_visualizations(weekly_stats, aggregated, output_path, ctx.sport.name, ctx.sport.emoji)

    return 0


if __name__ == "__main__":
    sys.exit(main())
