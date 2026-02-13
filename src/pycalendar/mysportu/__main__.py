"""
CLI MySportU — Point d'entrée en ligne de commande.

Permet d'explorer les données MySportU depuis le terminal avec un affichage Rich.

Usage:
    python -m pycalendar.mysportu                   # Aide
    python -m pycalendar.mysportu matches            # Tous les matchs
    python -m pycalendar.mysportu matches -s VB -c PH2   # Volleyball PH2
    python -m pycalendar.mysportu matches -s VB -c PH2 -g M  # Masculin seulement
    python -m pycalendar.mysportu matches -s VB --date 05/02/2026
    python -m pycalendar.mysportu competitions       # Liste des compétitions
    python -m pycalendar.mysportu equipes -s VB      # Équipes de volley
    python -m pycalendar.mysportu lieux              # Lieux de pratique
    python -m pycalendar.mysportu detail 12345       # Détails d'un match
    python -m pycalendar.mysportu cache              # Stats du cache
    python -m pycalendar.mysportu cache --clear      # Vider le cache
"""

from __future__ import annotations

import argparse
import sys

from rich.console import Console

from .facade import MySportU


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m pycalendar.mysportu",
        description="Explorateur de données MySportU",
    )

    # Options globales
    parser.add_argument("--username", "-u", help="Identifiant MySportU")
    parser.add_argument("--password", "-p", help="Mot de passe MySportU")
    parser.add_argument("--config", help="Fichier de config YAML")
    parser.add_argument("--cache-dir", help="Répertoire de cache")
    parser.add_argument("--no-cache", action="store_true", help="Désactiver le cache")
    parser.add_argument("--force", "-f", action="store_true",
                        help="Forcer le rafraîchissement depuis l'API")
    parser.add_argument("--verbose", "-v", action="store_true", help="Mode verbeux")

    sub = parser.add_subparsers(dest="command", help="Commande")

    # matches
    p_matches = sub.add_parser("matches", aliases=["m"],
                                help="Afficher les matchs")
    p_matches.add_argument("-s", "--sport", help="Code sport (VB, HB, BB, ...)")
    p_matches.add_argument("-c", "--championship", help="Code championnat (PH1, PH2, ...)")
    p_matches.add_argument("-g", "--genre", help="Genre (M, F)")
    p_matches.add_argument("--date", help="Date (dd/mm/yyyy)")
    p_matches.add_argument("--state", help="État (non_joue, termine, reporte, annule)")
    p_matches.add_argument("--stats", action="store_true", help="Afficher les statistiques")
    p_matches.add_argument("--compact", action="store_true", help="Affichage compact")
    p_matches.add_argument("--show-comp", action="store_true",
                            help="Afficher la compétition")

    # competitions
    sub.add_parser("competitions", aliases=["comp", "c"],
                   help="Lister les compétitions")

    # equipes
    p_equipes = sub.add_parser("equipes", aliases=["eq", "e"],
                                help="Lister les équipes")
    p_equipes.add_argument("-s", "--sport", help="Code sport (VB, HB, BB, ...)")
    p_equipes.add_argument("-c", "--championship", help="Code championnat")

    # lieux
    sub.add_parser("lieux", aliases=["l"], help="Lister les lieux de pratique")

    # detail
    p_detail = sub.add_parser("detail", aliases=["d"],
                               help="Détails d'un match")
    p_detail.add_argument("match_id", type=int, help="ID du match")

    # cache
    p_cache = sub.add_parser("cache", help="Gestion du cache")
    p_cache.add_argument("--clear", action="store_true", help="Vider le cache")
    p_cache.add_argument("--cleanup", action="store_true",
                          help="Supprimer les entrées expirées")
    p_cache.add_argument("--type", help="Type de ressource à cibler")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    console = Console()

    try:
        msu = MySportU(
            username=args.username,
            password=args.password,
            config_path=args.config,
            cache_dir=args.cache_dir,
            cache_enabled=not args.no_cache,
            verbose=args.verbose,
            console=console,
        )

        force = args.force

        if args.command in ("matches", "m"):
            matches = msu.get_matches(
                sport=args.sport,
                championship=args.championship,
                genre=args.genre,
                date=args.date,
                state=args.state,
                force_refresh=force,
            )
            msu.display_matches(
                matches,
                show_competition=args.show_comp,
                compact=args.compact,
            )
            if args.stats:
                msu.display_stats(matches)

        elif args.command in ("competitions", "comp", "c"):
            comps = msu.get_competitions(force_refresh=force)
            msu.display_competitions(comps)

        elif args.command in ("equipes", "eq", "e"):
            equipes = msu.get_equipes(
                sport=args.sport,
                championship=args.championship,
                force_refresh=force,
            )
            msu.display_equipes(equipes)

        elif args.command in ("lieux", "l"):
            lieux = msu.get_lieux(force_refresh=force)
            msu.display_lieux(lieux)

        elif args.command in ("detail", "d"):
            detail = msu.get_match_detail(args.match_id, force_refresh=force)
            # Try to find matching MatchInfo for extra context
            try:
                all_matches = msu.get_all_matches()
                match_info = next((m for m in all_matches if m.id == args.match_id), None)
            except Exception:
                match_info = None
            msu.display_match_detail(detail, match_info)

        elif args.command == "cache":
            if args.clear:
                msu.clear_cache(args.type)
            elif args.cleanup:
                msu.cleanup_cache()
            else:
                msu.show_cache_stats()

        msu.disconnect()

    except KeyboardInterrupt:
        console.print("\n[dim]Interrompu.[/]")
        return 130
    except Exception as e:
        console.print(f"[bold red]Erreur:[/] {e}")
        if args.verbose:
            console.print_exception()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
