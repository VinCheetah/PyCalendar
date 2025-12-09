#!/usr/bin/env python3
"""
Script pour générer une feuille de matchs formatée à partir de la solution JSON.

Usage:
    python scripts/generer_feuille_matchs.py --semaine 1 --date-depart "16/10/25"
    python scripts/generer_feuille_matchs.py -s 2 -d "23/10/25"
    python scripts/generer_feuille_matchs.py -s 3 --solution solutions/solution_volley_2025-11-24.json
"""

import json
import pandas as pd
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

from pycalendar.core.constants import (
    DATE_USER_FORMAT_LABEL,
    format_user_date,
    parse_user_date,
)


# Dictionnaire de mapping des gymnases
GYMNASES_SIUAPS = {
    "DESCARTES": "ENS DESCARTES",
    "ECL": "CENTRALE",
    "ESA": "GYMNASE ESA",
    "LYON 2 HC": "HALLE LYON 2",
    "LAENNEC": "HALLE - 3D",
    "BESSON": "HALLE - C.BESSON",
    "L. J. HAUT": "COMPET C (HAUT) - LEON JOUHAUX",
    "ENTPE": "ENTPE",
    "GRENOBLE": "GRENOBLE"
}


def extraire_genre_niveau(code_poule):
    """
    Extrait le genre et le niveau depuis le code de poule.
    Format: VB + (F/M) + (A1/A2/A3/A4) + P + (A/B/C/...)
    
    Exemples:
        VBFA1PA -> (F, A1)
        VBMA3PB -> (M, A3)
    """
    # Gérer les cas où code_poule est NaN ou None
    if pd.isna(code_poule) or not isinstance(code_poule, str):
        return 'M', 'A1'  # Valeurs par défaut
    
    # Vérifier que le code fait au moins 5 caractères
    if len(code_poule) < 5:
        return 'M', 'A1'  # Valeurs par défaut
    
    # Le genre est en position 2 (après VB)
    genre = code_poule[2] if len(code_poule) > 2 else 'M'  # 'F' ou 'M'
    
    # Le niveau est en position 3-4 (A + chiffre)
    niveau = code_poule[3:5] if len(code_poule) > 4 else 'A1'  # 'A1', 'A2', 'A3', ou 'A4'
    
    return genre, niveau


def mapper_gymnase(gymnase_code):
    """Convertit le code gymnase en nom complet selon le dictionnaire."""
    return GYMNASES_SIUAPS.get(gymnase_code, gymnase_code)


def calculer_date_semaine(date_depart, numero_semaine):
    """
    Calcule la date correspondant à une semaine donnée.
    
    Args:
        date_depart: Date de départ (semaine 1) au format "DD/MM/YY"
        numero_semaine: Numéro de la semaine (1, 2, 3, ...)
    
    Returns:
        Date au format "DD/MM/YY"
    """
    date_obj = parse_user_date(date_depart)
    if not date_obj:
        raise ValueError(f"Date de départ invalide '{date_depart}', attendu: {DATE_USER_FORMAT_LABEL}")
    # Ajouter (numero_semaine - 1) semaines
    date_cible = date_obj + timedelta(weeks=(numero_semaine - 1))
    return format_user_date(date_cible)


def charger_solution_json(fichier_json):
    """
    Charge le fichier JSON de solution.
    
    Args:
        fichier_json: Chemin vers le fichier JSON
    
    Returns:
        Dictionnaire contenant la solution
    """
    with open(fichier_json, 'r', encoding='utf-8') as f:
        return json.load(f)


def compter_equipes_par_institution(solution):
    """
    Compte le nombre d'équipes par institution et genre.
    
    Args:
        solution: Dictionnaire de solution
        
    Returns:
        Dict[institution][genre] -> nombre d'équipes
    """
    from collections import defaultdict
    equipes = solution['entities']['equipes']
    counts = defaultdict(lambda: defaultdict(int))
    for e in equipes:
        counts[e['institution']][e['genre']] += 1
    return counts


def simplifier_nom_equipe(nom_complet, institution, genre, counts):
    """
    Simplifie le nom d'une équipe si c'est la seule de l'institution/genre.
    
    Args:
        nom_complet: Nom complet de l'équipe (ex: "ECL (1)")
        institution: Institution de l'équipe
        genre: Genre de l'équipe
        counts: Dictionnaire de comptage institution/genre
        
    Returns:
        Nom simplifié si une seule équipe, sinon nom complet
    """
    if counts[institution][genre] == 1:
        # Une seule équipe -> retourner juste l'institution
        return institution
    else:
        # Plusieurs équipes -> garder le nom complet
        return nom_complet


def filtrer_matchs_par_semaine(solution, numero_semaine, date_str):
    """
    Filtre les matchs planifiés pour une semaine donnée et les formate.
    
    Args:
        solution: Dictionnaire de solution chargé depuis JSON
        numero_semaine: Numéro de la semaine à extraire
        date_str: Date au format "DD/MM/YY" pour affichage
    
    Returns:
        DataFrame avec les matchs filtrés et formatés
    """
    matchs_planifies = solution['matches']['scheduled']
    
    # Filtrer par semaine (exclure les matchs en entente qui n'ont pas de semaine)
    matchs_semaine = [m for m in matchs_planifies if m.get('semaine') == numero_semaine]
    
    if not matchs_semaine:
        print(f"⚠️  Aucun match trouvé pour la semaine {numero_semaine}")
        return None
    
    # Compter les équipes par institution/genre pour simplification des noms
    counts = compter_equipes_par_institution(solution)
    
    # Convertir en DataFrame
    data = []
    for match in matchs_semaine:
        poule = match.get('poule', 'HORS_CHAMPIONNAT')
        championship_type = match.get('championship_type', 'Acad')
        
        # Déterminer si c'est un match CFE/CFU
        # Méthode 1: avec championship_type (nouvelles solutions)
        # Méthode 2: poule vide + match fixe (anciennes solutions)
        is_cfe_cfu = (
            championship_type in ['CFE', 'CFU'] or 
            (poule == '' and match.get('is_fixed', False))
        )
        
        # Si pas de championship_type mais poule vide + fixed, deviner CFE/CFU
        if championship_type == 'Acad' and poule == '' and match.get('is_fixed', False):
            # Pour les anciennes solutions: on suppose CFE par défaut
            # (CFE est plus courant que CFU dans les données)
            championship_type = 'CFE'
        
        # Déterminer le genre
        genre = match.get('genre', match.get('equipe1_genre', 'M'))
        
        # Déterminer le niveau depuis la poule (pour tri uniquement)
        if poule and poule != 'HORS_CHAMPIONNAT' and not is_cfe_cfu:
            _, niveau = extraire_genre_niveau(poule)
        else:
            niveau = 'EXT'
        
        # Simplifier les noms d'équipes pour CFE/CFU si une seule équipe
        # Pour les équipes externes, utiliser 'nom' au lieu de 'nom_complet'
        # Détecter si équipe externe: nom_complet == "EXTERNE"
        equipe1_is_externe = match['equipe1_nom_complet'] == 'EXTERNE'
        equipe2_is_externe = match['equipe2_nom_complet'] == 'EXTERNE'
        
        equipe1_nom = match['equipe1_nom'] if equipe1_is_externe else match['equipe1_nom_complet']
        equipe2_nom = match['equipe2_nom'] if equipe2_is_externe else match['equipe2_nom_complet']
        
        if is_cfe_cfu and not (equipe1_is_externe or equipe2_is_externe):
            # Pour CFE/CFU (hors externes), simplifier le nom si une seule équipe institution/genre
            equipe1_nom = simplifier_nom_equipe(
                match['equipe1_nom_complet'], 
                match['equipe1_institution'], 
                match['equipe1_genre'],
                counts
            )
            equipe2_nom = simplifier_nom_equipe(
                match['equipe2_nom_complet'],
                match['equipe2_institution'],
                match['equipe2_genre'],
                counts
            )
            # Pour CFE/CFU, afficher le type de compétition dans la colonne Poule
            poule_affichee = championship_type
        elif is_cfe_cfu:
            # CFE/CFU avec équipe externe: juste afficher le type de compétition
            poule_affichee = championship_type
        else:
            poule_affichee = poule if poule else 'HORS_CHAMPIONNAT'
        
        data.append({
            'Date': date_str,
            'Sport': 'VB',
            'Sexe': genre,
            'Poule': poule_affichee,
            'Equipe 1': equipe1_nom,
            'Equipe 2': equipe2_nom,
            'Hre Déb': match['horaire'],
            'Lieu': mapper_gymnase(match['gymnase']),
            '_niveau': niveau,
            '_is_cfe_cfu': is_cfe_cfu,
            '_priorite': 0 if is_cfe_cfu else 1  # CFE/CFU en priorité (0 = en haut)
        })
    
    df = pd.DataFrame(data)
    
    # Définir l'ordre de tri pour le genre (F avant M)
    genre_order = {'F': 0, 'M': 1}
    df['_genre_order'] = df['Sexe'].map(genre_order).fillna(2)
    
    # Définir l'ordre de tri pour le niveau (A1 < A2 < A3 < A4 < EXT)
    niveau_order = {'A1': 0, 'A2': 1, 'A3': 2, 'A4': 3, 'EXT': 4}
    df['_niveau_order'] = df['_niveau'].map(niveau_order).fillna(5)
    
    # Trier par priorité (CFE/CFU d'abord), puis genre, niveau, puis horaire
    df = df.sort_values(
        by=['_genre_order', '_priorite', '_niveau_order', 'Hre Déb'],
        ascending=[True, True, True, True]
    )
    
    # Supprimer les colonnes temporaires de tri (garder _is_cfe_cfu pour la mise en forme)
    df = df.drop(columns=['_genre_order', '_niveau_order', '_niveau', '_priorite'])
    
    # Réinitialiser l'index
    df = df.reset_index(drop=True)
    
    return df


def appliquer_mise_en_forme(workbook, worksheet, df):
    """
    Applique la mise en forme au fichier Excel pour correspondre à l'exemple.
    
    Args:
        workbook: Objet Workbook d'openpyxl
        worksheet: Feuille de calcul active
        df: DataFrame contenant les données
    """
    # Définir les styles
    header_font = Font(bold=True, size=11)
    header_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center")
    
    # Surlignage jaune pour CFE/CFU
    yellow_fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
    
    cell_alignment = Alignment(horizontal="left", vertical="center")
    center_alignment = Alignment(horizontal="center", vertical="center")
    
    border_style = Side(style="thin", color="000000")
    border = Border(left=border_style, right=border_style, top=border_style, bottom=border_style)
    
    # Appliquer le style aux en-têtes (ligne 1)
    for col_num, column_title in enumerate(df.columns, 1):
        # Ignorer la colonne _is_cfe_cfu (colonne cachée)
        if column_title == '_is_cfe_cfu':
            continue
        cell = worksheet.cell(row=1, column=col_num)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = border
    
    # Appliquer les bordures et alignement aux cellules de données
    for row_num in range(2, len(df) + 2):
        is_cfe_cfu = df.iloc[row_num - 2]['_is_cfe_cfu'] if '_is_cfe_cfu' in df.columns else False
        
        for col_num in range(1, len(df.columns) + 1):
            col_name = df.columns[col_num - 1]
            
            # Ignorer la colonne _is_cfe_cfu dans l'affichage
            if col_name == '_is_cfe_cfu':
                continue
                
            cell = worksheet.cell(row=row_num, column=col_num)
            cell.border = border
            
            # Surligner en jaune si CFE/CFU
            if is_cfe_cfu:
                cell.fill = yellow_fill
            
            # Alignement centré pour Date, Sport, Sexe, Hre Déb
            if col_num in [1, 2, 3, 7]:  # Date, Sport, Sexe, Hre Déb
                cell.alignment = center_alignment
            else:
                cell.alignment = cell_alignment
    
    # Ajuster la largeur des colonnes
    column_widths = {
        'A': 12,   # Date
        'B': 8,    # Sport
        'C': 6,    # Sexe
        'D': 12,   # Poule
        'E': 15,   # Equipe 1
        'F': 15,   # Equipe 2
        'G': 10,   # Hre Déb
        'H': 35    # Lieu
    }
    
    for col, width in column_widths.items():
        worksheet.column_dimensions[col].width = width


def generer_feuille_excel(df, fichier_sortie):
    """
    Génère un fichier Excel avec mise en forme à partir du DataFrame.
    
    Args:
        df: DataFrame contenant les matchs
        fichier_sortie: Chemin du fichier Excel de sortie
    """
    # Créer une copie du DataFrame sans la colonne _is_cfe_cfu pour l'export
    df_export = df.drop(columns=['_is_cfe_cfu'], errors='ignore')
    
    # Créer un workbook avec openpyxl
    wb = Workbook()
    ws = wb.active
    ws.title = "Matchs"
    
    # Écrire les en-têtes (sans _is_cfe_cfu)
    for col_num, column_title in enumerate(df_export.columns, 1):
        ws.cell(row=1, column=col_num, value=column_title)
    
    # Écrire les données (sans _is_cfe_cfu)
    for row_num, row_data in enumerate(df_export.itertuples(index=False), 2):
        for col_num, value in enumerate(row_data, 1):
            ws.cell(row=row_num, column=col_num, value=value)
    
    # Appliquer la mise en forme (en passant le df original avec _is_cfe_cfu)
    appliquer_mise_en_forme(wb, ws, df)
    
    # Sauvegarder le fichier
    wb.save(fichier_sortie)
    print(f"✅ Fichier généré : {fichier_sortie}")
    print(f"   Nombre de matchs : {len(df)}")


def trouver_derniere_solution():
    """
    Trouve le fichier de solution le plus récent dans le dossier solutions/.
    
    Returns:
        Path vers le fichier de solution le plus récent
    """
    script_dir = Path(__file__).parent.parent
    solutions_dir = script_dir / 'solutions'
    
    # Chercher latest_volley.json en priorité
    latest_json = solutions_dir / 'latest_volley.json'
    if latest_json.exists():
        return latest_json
    
    # Sinon, chercher tous les fichiers JSON et prendre le plus récent
    json_files = list(solutions_dir.glob('solution_volley_*.json'))
    if not json_files:
        raise FileNotFoundError("Aucun fichier de solution trouvé dans solutions/")
    
    # Trier par date de modification et prendre le plus récent
    json_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return json_files[0]


def main():
    parser = argparse.ArgumentParser(
        description="Génère une feuille de matchs formatée pour une semaine donnée à partir du JSON de solution.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  %(prog)s --semaine 1 --date-depart "16/10/2025"
  %(prog)s -s 2 -d "23/10/2025" -o matchs_semaine_2.xlsx
  %(prog)s -s 3 -d "16/10/2025" --auto-date
  %(prog)s -s 1 --solution solutions/solution_volley_2025-11-24.json
        """
    )
    
    parser.add_argument(
        '-s', '--semaine',
        type=int,
        required=True,
        help='Numéro de la semaine (1, 2, 3, ...)'
    )
    
    parser.add_argument(
        '-d', '--date-depart',
        type=str,
            default="16/10/25",
            help='Date de départ pour la semaine 1 (format: DD/MM/YY). Par défaut: 16/10/25'
    )
    
    parser.add_argument(
        '--auto-date',
        action='store_true',
        help='Calcule automatiquement la date en fonction de la semaine et de la date de départ'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        help='Nom du fichier de sortie (par défaut: Matchs_Semaine_X_DATE.xlsx)'
    )
    
    parser.add_argument(
        '--solution',
        type=str,
        help='Chemin vers le fichier JSON de solution (par défaut: solutions/latest_volley.json)'
    )
    
    args = parser.parse_args()
    
    # Calculer la date si demandé
    if args.auto_date:
        date_str = calculer_date_semaine(args.date_depart, args.semaine)
    else:
        date_str = args.date_depart
    
    # Déterminer le fichier de solution
    script_dir = Path(__file__).parent.parent
    if args.solution:
        fichier_solution = Path(args.solution)
        if not fichier_solution.is_absolute():
            fichier_solution = script_dir / args.solution
    else:
        try:
            fichier_solution = trouver_derniere_solution()
        except FileNotFoundError as e:
            print(f"❌ Erreur : {e}")
            return 1
    
    if not fichier_solution.exists():
        print(f"❌ Erreur : Le fichier {fichier_solution} n'existe pas.")
        return 1
    
    # Charger la solution
    print(f"📅 Génération de la feuille de matchs")
    print(f"   Semaine : {args.semaine}")
    print(f"   Date : {date_str}")
    print(f"   Solution : {fichier_solution}")
    print()
    
    try:
        solution = charger_solution_json(fichier_solution)
    except Exception as e:
        print(f"❌ Erreur lors du chargement de la solution : {e}")
        return 1
    
    # Filtrer les matchs
    df_matchs = filtrer_matchs_par_semaine(solution, args.semaine, date_str)
    
    if df_matchs is None or df_matchs.empty:
        return 1
    
    # Définir le nom du fichier de sortie
    if args.output:
        fichier_sortie = Path(args.output)
        if not fichier_sortie.is_absolute():
            fichier_sortie = script_dir / args.output
    else:
        date_clean = date_str.replace('/', '-')
        fichier_sortie = script_dir / f"Matchs_Semaine_{args.semaine}_{date_clean}.xlsx"
    
    # Créer le dossier de sortie si nécessaire
    fichier_sortie.parent.mkdir(parents=True, exist_ok=True)
    
    # Générer le fichier Excel
    generer_feuille_excel(df_matchs, fichier_sortie)
    
    print()
    print(f"📊 Résumé:")
    print(f"   Matchs féminins : {len(df_matchs[df_matchs['Sexe'] == 'F'])}")
    print(f"   Matchs masculins : {len(df_matchs[df_matchs['Sexe'] == 'M'])}")
    print(f"   Lieux uniques : {df_matchs['Lieu'].nunique()}")
    
    return 0


if __name__ == "__main__":
    exit(main())
