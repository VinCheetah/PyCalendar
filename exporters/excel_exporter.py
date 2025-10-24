"""Excel exporter for scheduling solutions."""

import pandas as pd
from typing import List
from pathlib import Path
from core.models import Solution, Match


class ExcelExporter:
    """Exports scheduling solutions to Excel format."""
    
    @staticmethod
    def export(solution: Solution, filepath: str):
        """Export solution to Excel file."""
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            if solution.matchs_planifies:
                df_planifies = ExcelExporter._create_dataframe_matchs(solution.matchs_planifies)
                df_planifies.to_excel(writer, sheet_name='Calendrier', index=False)
            
            if solution.matchs_non_planifies:
                df_non_planifies = ExcelExporter._create_dataframe_matchs(solution.matchs_non_planifies)
                df_non_planifies.to_excel(writer, sheet_name='Non_Planifies', index=False)
            
            # Nouvelle feuille: Tous les matchs au format Matchs_Fixes (compatible copier-coller)
            if solution.matchs_planifies:
                df_tous_matchs = ExcelExporter._create_dataframe_matchs_fixes_format(solution.matchs_planifies)
                df_tous_matchs.to_excel(writer, sheet_name='Tous_Matchs', index=False)
            
            df_stats = ExcelExporter._create_stats_dataframe(solution)
            df_stats.to_excel(writer, sheet_name='Statistiques', index=False)
        
        print(f"✓ Calendrier exporté: {filepath}")
    
    @staticmethod
    def _create_dataframe_matchs(matchs: List[Match]) -> pd.DataFrame:
        """Create DataFrame from match list."""
        data = []
        
        for match in matchs:
            # Generate unique Match_ID for tracking modifications
            match_id = f"{match.equipe1.id_unique}__{match.equipe2.id_unique}__{match.poule}"
            
            row = {
                'Match_ID': match_id,
                'Poule': match.poule,
                'Institution_1': match.equipe1.institution,
                'Num_1': match.equipe1.numero_equipe,
                'Genre_1': match.equipe1.genre,
                'Equipe_1': match.equipe1.nom_complet,
                'Institution_2': match.equipe2.institution,
                'Num_2': match.equipe2.numero_equipe,
                'Genre_2': match.equipe2.genre,
                'Equipe_2': match.equipe2.nom_complet,
            }
            
            if match.creneau:
                row['Semaine'] = match.creneau.semaine
                row['Horaire'] = match.creneau.horaire
                row['Gymnase'] = match.creneau.gymnase
            else:
                row['Semaine'] = ''
                row['Horaire'] = ''
                row['Gymnase'] = ''
            
            data.append(row)
        
        df = pd.DataFrame(data)
        
        if 'Semaine' in df.columns:
            df = df.sort_values(['Semaine', 'Horaire', 'Gymnase', 'Poule'])
        
        return df
    
    @staticmethod
    def _create_stats_dataframe(solution: Solution) -> pd.DataFrame:
        """Create statistics DataFrame."""
        stats = [
            {'Metrique': 'Matchs planifiés', 'Valeur': len(solution.matchs_planifies)},
            {'Metrique': 'Matchs non planifiés', 'Valeur': len(solution.matchs_non_planifies)},
            {'Metrique': 'Taux planification (%)', 'Valeur': f"{solution.taux_planification():.2f}"},
            {'Metrique': 'Score solution', 'Valeur': f"{solution.score:.2f}"},
        ]
        
        matchs_par_semaine = solution.get_matchs_par_semaine()
        if matchs_par_semaine:
            stats.append({
                'Metrique': 'Semaines utilisées', 
                'Valeur': len(matchs_par_semaine)
            })
            stats.append({
                'Metrique': 'Matchs/semaine (moy)', 
                'Valeur': f"{len(solution.matchs_planifies) / len(matchs_par_semaine):.1f}"
            })
        
        if 'solver' in solution.metadata:
            stats.append({'Metrique': 'Solver utilisé', 'Valeur': solution.metadata['solver']})
        
        return pd.DataFrame(stats)
    
    @staticmethod
    def _create_dataframe_matchs_fixes_format(matchs: List[Match]) -> pd.DataFrame:
        """
        Create DataFrame with Matchs_Fixes format for easy copy-paste.
        Format: Equipe_1, Equipe_2, Genre, Poule, Semaine, Horaire, Gymnase, Score, Type_Competition, Remarques
        Tri: Semaine → Genre (F puis M) → Catégorie (A1, A2, A3, A4)
        """
        data = []
        
        for match in matchs:
            # Extraire le genre (F ou M) depuis le nom de la poule
            # Format poule: VB + genre (F/M) + catégorie (A1-A4) + poule (PA, PB, etc.)
            # Exemples: VBFA1PA (Volley Féminin A1 Poule A), VBMA2PB (Volley Masculin A2 Poule B)
            genre = 'M'  # Par défaut Hommes
            if match.poule and len(match.poule) >= 4:
                if match.poule[2] == 'F':  # 3ème caractère = F ou M
                    genre = 'F'
                elif match.poule[2] == 'M':
                    genre = 'M'
            
            # Extraire la catégorie (A1, A2, A3, A4) depuis le nom de la poule
            categorie = 'A1'  # Par défaut
            if match.poule and len(match.poule) >= 6:
                # Format: VB + F/M + A + chiffre (1-4)
                if 'A1' in match.poule:
                    categorie = 'A1'
                elif 'A2' in match.poule:
                    categorie = 'A2'
                elif 'A3' in match.poule:
                    categorie = 'A3'
                elif 'A4' in match.poule:
                    categorie = 'A4'
            
            # Enlever le [F] ou [M] des noms d'équipes (institution + numéro seulement)
            eq1_nom = match.equipe1.nom_complet.replace(' [F]', '').replace(' [M]', '').strip()
            eq2_nom = match.equipe2.nom_complet.replace(' [F]', '').replace(' [M]', '').strip()
            
            row = {
                'Equipe_1': eq1_nom,
                'Equipe_2': eq2_nom,
                'Genre': genre,
                'Poule': match.poule,
                'Semaine': match.creneau.semaine if match.creneau else '',
                'Horaire': match.creneau.horaire if match.creneau else '',
                'Gymnase': match.creneau.gymnase if match.creneau else '',
                'Score': '',  # Vide car match à jouer
                'Type_Competition': 'Acad',  # Par défaut
                'Remarques': '',
                # Colonnes de tri (seront supprimées après)
                '_categorie': categorie,
                '_ordre_genre': 0 if genre == 'F' else 1,  # F avant M
            }
            
            data.append(row)
        
        df = pd.DataFrame(data)
        
        # Tri: Semaine → Genre (F puis M) → Catégorie (A1, A2, A3, A4) → Horaire → Equipe_1
        if not df.empty:
            df = df.sort_values(
                by=['Semaine', '_ordre_genre', '_categorie', 'Horaire', 'Equipe_1'],
                na_position='last'
            )
            
            # Supprimer les colonnes de tri auxiliaires
            df = df.drop(columns=['_categorie', '_ordre_genre'])
        
        return df
    
    @staticmethod
    def export_par_poule(solution: Solution, output_dir: str):
        """Export separate file for each pool."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        poules = {}
        for match in solution.matchs_planifies:
            if match.poule not in poules:
                poules[match.poule] = []
            poules[match.poule].append(match)
        
        for nom_poule, matchs in poules.items():
            filename = output_path / f"calendrier_poule_{nom_poule}.xlsx"
            df = ExcelExporter._create_dataframe_matchs(matchs)
            df.to_excel(filename, index=False)
        
        print(f"✓ {len(poules)} calendriers de poule exportés dans {output_dir}")
