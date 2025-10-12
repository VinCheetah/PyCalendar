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
            
            df_stats = ExcelExporter._create_stats_dataframe(solution)
            df_stats.to_excel(writer, sheet_name='Statistiques', index=False)
        
        print(f"✓ Calendrier exporté: {filepath}")
    
    @staticmethod
    def _create_dataframe_matchs(matchs: List[Match]) -> pd.DataFrame:
        """Create DataFrame from match list."""
        data = []
        
        for match in matchs:
            row = {
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
