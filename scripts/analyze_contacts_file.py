#!/usr/bin/env python3
"""
Analyse le fichier CONTACTS RESPO EQUIPES BB_HB_VB.xlsx pour comprendre
la structure et extraire les correspondances équipes-contacts.

Format du fichier:
- Chaque ligne = une institution avec ses coordonnées de contact
- Colonnes CODE/NOM/EMAIL/TEL contiennent les infos de contact
- Colonnes sport (VOLLEYBALL MASCULIN [Equipe X], etc.) contiennent 
  le nom de l'institution si elle a cette équipe
"""

import pandas as pd
import json
import re
from pathlib import Path


def analyze_contacts_structure(excel_file):
    """Analyse la structure du fichier de contacts."""
    df = pd.read_excel(excel_file, sheet_name='Feuil1')
    
    print("=" * 80)
    print("📊 ANALYSE DU FICHIER DE CONTACTS")
    print("=" * 80)
    print()
    
    # Informations générales
    print(f"📄 Fichier: {excel_file}")
    print(f"📋 Nombre d'institutions: {len(df)}")
    print()
    
    # Colonnes principales
    contact_cols = ['CODE / ASSOCIATION SPORTIVE', 'NOM/PRÉNOM du responsable', 
                   'Adresse e-mail', 'TELEPHONE du responsable']
    
    # Colonnes sport
    sport_columns = {}
    for col in df.columns:
        if 'VOLLEYBALL MASCULIN' in col:
            # Extraire le numéro d'équipe
            match = re.search(r'\[Equipe (\d+)\s*\]', col)
            if match:
                team_num = int(match.group(1))
                sport_columns[col] = ('VOLLEYBALL', 'M', team_num)
        elif 'VOLLEYBALL FÉMININ' in col or 'VOLLEYBALL FEMININ' in col:
            match = re.search(r'\[Equipe (\d+)\s*\]', col)
            if match:
                team_num = int(match.group(1))
                sport_columns[col] = ('VOLLEYBALL', 'F', team_num)
    
    print(f"🏐 Colonnes VOLLEYBALL MASCULIN trouvées: {sum(1 for s in sport_columns.values() if s[0] == 'VOLLEYBALL' and s[1] == 'M')}")
    print(f"🏐 Colonnes VOLLEYBALL FÉMININ trouvées: {sum(1 for s in sport_columns.values() if s[0] == 'VOLLEYBALL' and s[1] == 'F')}")
    print()
    
    return df, contact_cols, sport_columns


def extract_team_contacts(df, contact_cols, sport_columns):
    """Extrait les correspondances équipe -> contact."""
    
    print("=" * 80)
    print("🔍 EXTRACTION DES CORRESPONDANCES ÉQUIPE-CONTACT")
    print("=" * 80)
    print()
    
    team_contacts = {}
    stats = {
        'total_teams': 0,
        'teams_with_contact': 0,
        'teams_without_contact': 0,
        'institutions': set()
    }
    
    # Pour chaque colonne sport
    for col_name, (sport, genre, team_num) in sorted(sport_columns.items(), key=lambda x: (x[1][0], x[1][1], x[1][2])):
        # Trouver toutes les institutions qui ont cette équipe
        teams_found = []
        
        for idx, row in df.iterrows():
            institution_in_col = row[col_name]
            
            # Si la cellule contient le nom d'une institution
            if pd.notna(institution_in_col) and str(institution_in_col).strip():
                # Récupérer les infos de contact de cette ligne
                institution_code = row[contact_cols[0]]
                responsable = row[contact_cols[1]]
                email = row[contact_cols[2]]
                telephone = row[contact_cols[3]]
                
                # Nettoyer les valeurs
                institution_code = str(institution_code).strip() if pd.notna(institution_code) else None
                responsable = str(responsable).strip() if pd.notna(responsable) else None
                email = str(email).strip() if pd.notna(email) else None
                telephone = str(telephone).strip() if pd.notna(telephone) else None
                
                team_key = f"{sport}_{genre}_{team_num}"
                
                contact_info = {
                    'sport': sport,
                    'genre': genre,
                    'numero': team_num,
                    'institution_code': institution_code,
                    'institution_in_column': str(institution_in_col).strip(),
                    'responsable': responsable,
                    'email': email,
                    'telephone': telephone
                }
                
                team_contacts[team_key] = contact_info
                stats['total_teams'] += 1
                
                if responsable and responsable != 'nan' and email and email != 'nan':
                    stats['teams_with_contact'] += 1
                else:
                    stats['teams_without_contact'] += 1
                
                if institution_code and institution_code != 'nan':
                    stats['institutions'].add(institution_code)
                
                teams_found.append((institution_in_col, responsable, email))
        
        # Afficher les équipes trouvées pour cette colonne
        if teams_found:
            print(f"✅ {sport} {genre} Équipe {team_num}:")
            for inst, resp, email_val in teams_found:
                resp_str = f" - {resp}" if resp and resp != 'nan' else ""
                email_str = f" ({email_val})" if email_val and email_val != 'nan' else ""
                print(f"   {inst}{resp_str}{email_str}")
    
    print()
    print("=" * 80)
    print("📈 STATISTIQUES")
    print("=" * 80)
    print(f"Total d'équipes trouvées: {stats['total_teams']}")
    print(f"Équipes avec contact complet: {stats['teams_with_contact']}")
    print(f"Équipes sans contact complet: {stats['teams_without_contact']}")
    print(f"Institutions différentes: {len(stats['institutions'])}")
    print()
    
    return team_contacts, stats


def match_with_solution(team_contacts, solution_file):
    """Compare avec les équipes de la solution volley."""
    
    print("=" * 80)
    print("🔗 CORRESPONDANCE AVEC LA SOLUTION VOLLEY")
    print("=" * 80)
    print()
    
    # Charger la solution
    with open(solution_file, 'r', encoding='utf-8') as f:
        solution = json.load(f)
    
    equipes = solution.get('equipes', [])
    print(f"📊 Équipes dans la solution: {len(equipes)}")
    print()
    
    # Identifier les équipes
    matched = []
    unmatched = []
    
    for equipe in equipes:
        nom = equipe.get('nom', '')
        institution = equipe.get('institution', '')
        
        # Extraire le genre depuis les poules
        poules = equipe.get('poules', [])
        genre = None
        if poules:
            # Le genre est dans le code poule (ex: VBMA4PA -> M, VBFA3PB -> F)
            first_poule = poules[0]
            if 'VBM' in first_poule or 'HBM' in first_poule or 'BBM' in first_poule:
                genre = 'M'
            elif 'VBF' in first_poule or 'HBF' in first_poule or 'BBF' in first_poule:
                genre = 'F'
        
        # Extraire le numéro
        match = re.search(r'\((\d+)\)', nom)
        numero = int(match.group(1)) if match else None
        
        if genre and numero:
            team_key = f"VOLLEYBALL_{genre}_{numero}"
            
            if team_key in team_contacts:
                contact = team_contacts[team_key]
                matched.append({
                    'equipe': nom,
                    'institution': institution,
                    'genre': genre,
                    'numero': numero,
                    'contact': contact
                })
                print(f"✅ {nom} ({institution}) -> {contact['responsable']} ({contact['email']})")
            else:
                unmatched.append({
                    'equipe': nom,
                    'institution': institution,
                    'genre': genre,
                    'numero': numero
                })
                print(f"❌ {nom} ({institution}) -> PAS DE CONTACT TROUVÉ")
        else:
            print(f"⚠️  {nom} ({institution}) -> Impossible d'extraire genre/numéro")
    
    print()
    print("=" * 80)
    print("📊 RÉSULTATS DU MATCHING")
    print("=" * 80)
    print(f"Équipes matchées: {len(matched)}/{len(equipes)}")
    print(f"Équipes non matchées: {len(unmatched)}/{len(equipes)}")
    print()
    
    if unmatched:
        print("❌ Équipes sans contact:")
        for eq in unmatched[:10]:
            print(f"   {eq['equipe']} ({eq['institution']})")
        if len(unmatched) > 10:
            print(f"   ... et {len(unmatched) - 10} autres")
    
    return matched, unmatched


def main():
    """Fonction principale."""
    base_dir = Path(__file__).parent.parent
    excel_file = base_dir / 'config' / 'CONTACTS RESPO EQUIPES BB_HB_VB.xlsx'
    solution_file = base_dir / 'solutions' / 'latest_volley.json'
    
    # Analyser la structure
    df, contact_cols, sport_columns = analyze_contacts_structure(excel_file)
    
    # Extraire les contacts
    team_contacts, stats = extract_team_contacts(df, contact_cols, sport_columns)
    
    # Sauvegarder les données extraites
    output_file = base_dir / 'config' / 'extracted_contacts.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(team_contacts, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Données extraites sauvegardées dans: {output_file}")
    print()
    
    # Comparer avec la solution
    if solution_file.exists():
        matched, unmatched = match_with_solution(team_contacts, solution_file)
    else:
        print(f"⚠️  Fichier solution non trouvé: {solution_file}")


if __name__ == '__main__':
    main()
