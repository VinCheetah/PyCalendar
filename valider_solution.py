"""
Script autonome pour valider une solution existante.
Usage: python valider_solution.py <config.yaml> <calendrier.xlsx>
"""

import sys
from pathlib import Path
import pandas as pd

from core.config import Config
from core.models import Solution, Match, Creneau, Equipe
from data.data_source import DataSource
from validation.solution_validator import SolutionValidator, afficher_rapport_validation


def charger_solution_depuis_excel(fichier_excel: str, equipes_dict: dict) -> Solution:
    """Charge une solution depuis un fichier Excel."""
    df = pd.read_excel(fichier_excel, sheet_name='Calendrier')
    
    matchs_planifies = []
    for _, row in df.iterrows():
        # Récupérer les équipes
        equipe1 = equipes_dict.get(row['Equipe_1'])
        equipe2 = equipes_dict.get(row['Equipe_2'])
        
        if not equipe1 or not equipe2:
            print(f"⚠️  Équipes non trouvées: {row['Equipe_1']} ou {row['Equipe_2']}")
            continue
        
        # Créer le match
        match = Match(equipe1, equipe2, row['Poule'])
        
        # Créer le créneau
        creneau = Creneau(
            semaine=int(row['Semaine']),
            gymnase=row['Gymnase'],
            horaire=row['Horaire']
        )
        
        match.creneau = creneau
        matchs_planifies.append(match)
    
    # Les matchs non planifiés ne sont pas dans le fichier, on met une liste vide
    return Solution(
        matchs_planifies=matchs_planifies,
        matchs_non_planifies=[],
        score=0.0
    )


def main():
    if len(sys.argv) < 3:
        print("Usage: python valider_solution.py <config.yaml> <calendrier.xlsx>")
        print("\nExemple:")
        print("  python valider_solution.py exemple/config.yaml exemple/calendrier_exemple.xlsx")
        return 1
    
    config_file = sys.argv[1]
    calendrier_file = sys.argv[2]
    
    # Vérifier que les fichiers existent
    if not Path(config_file).exists():
        print(f"❌ Fichier de configuration introuvable: {config_file}")
        return 1
    
    if not Path(calendrier_file).exists():
        print(f"❌ Fichier de calendrier introuvable: {calendrier_file}")
        return 1
    
    print("="*60)
    print("VALIDATION DE SOLUTION EXISTANTE")
    print("="*60)
    print(f"\n📂 Configuration: {config_file}")
    print(f"📂 Calendrier: {calendrier_file}")
    
    # Charger la configuration
    config = Config.from_yaml(config_file)
    
    # Charger les données de base
    source = DataSource(config.fichier_donnees)
    
    print(f"\n📂 Chargement des équipes et gymnases...")
    equipes = source.charger_equipes()
    gymnases = source.charger_gymnases()
    obligations = source.charger_obligations_presence()
    
    equipes_dict = {e.nom: e for e in equipes}
    gymnases_dict = {g.nom: g for g in gymnases}
    
    print(f"✓ {len(equipes)} équipes chargées")
    print(f"✓ {len(gymnases)} gymnases chargés")
    print(f"✓ {len(obligations)} obligations de présence")
    
    # Charger la solution depuis Excel
    print(f"\n📂 Chargement de la solution depuis Excel...")
    solution = charger_solution_depuis_excel(calendrier_file, equipes_dict)
    print(f"✓ {len(solution.matchs_planifies)} matchs chargés")
    
    # Valider la solution
    print(f"\n🔍 Validation de la solution...")
    validator = SolutionValidator(config, gymnases_dict, obligations)
    est_valide, rapport = validator.valider_solution(solution)
    
    # Afficher le rapport
    afficher_rapport_validation(rapport)
    
    # Générer un rapport détaillé dans un fichier
    rapport_file = calendrier_file.replace('.xlsx', '_rapport_validation.txt')
    generer_rapport_fichier(rapport, rapport_file)
    print(f"\n📄 Rapport détaillé sauvegardé: {rapport_file}")
    
    return 0 if est_valide else 1


def generer_rapport_fichier(rapport: dict, fichier: str):
    """Génère un rapport détaillé dans un fichier texte."""
    with open(fichier, 'w', encoding='utf-8') as f:
        f.write("="*60 + "\n")
        f.write("RAPPORT DE VALIDATION DÉTAILLÉ\n")
        f.write("="*60 + "\n\n")
        
        f.write(f"Matchs planifiés: {rapport['nb_matchs_planifies']}\n")
        f.write(f"Matchs non planifiés: {rapport['nb_matchs_non_planifies']}\n")
        f.write(f"Taux de planification: {rapport['taux_planification']:.1f}%\n\n")
        
        f.write(f"Violations DURES: {rapport['nb_violations_dures']}\n")
        f.write(f"Violations SOUPLES: {rapport['nb_violations_souples']}\n\n")
        
        if rapport['est_valide']:
            f.write("✅ SOLUTION VALIDE\n\n")
        else:
            f.write("❌ SOLUTION INVALIDE\n\n")
        
        # Violations dures
        if rapport['violations_dures']:
            f.write("="*60 + "\n")
            f.write("VIOLATIONS DE CONTRAINTES DURES\n")
            f.write("="*60 + "\n\n")
            
            violations_par_type = {}
            for v in rapport['violations_dures']:
                if v.type_contrainte not in violations_par_type:
                    violations_par_type[v.type_contrainte] = []
                violations_par_type[v.type_contrainte].append(v)
            
            for type_contrainte, violations in violations_par_type.items():
                f.write(f"\n{type_contrainte} ({len(violations)} violations):\n")
                f.write("-" * 60 + "\n")
                for i, v in enumerate(violations, 1):
                    f.write(f"\n{i}. {v.description}\n")
                    if v.match_concerne:
                        f.write(f"   Match: {v.match_concerne}\n")
                    if v.creneau_concerne:
                        f.write(f"   Créneau: {v.creneau_concerne}\n")
                    f.write(f"   Pénalité: {v.penalite}\n")
        
        # Violations souples
        if rapport['violations_souples']:
            f.write("\n" + "="*60 + "\n")
            f.write("VIOLATIONS DE CONTRAINTES SOUPLES\n")
            f.write("="*60 + "\n\n")
            
            violations_par_type = {}
            for v in rapport['violations_souples']:
                if v.type_contrainte not in violations_par_type:
                    violations_par_type[v.type_contrainte] = []
                violations_par_type[v.type_contrainte].append(v)
            
            for type_contrainte, violations in violations_par_type.items():
                f.write(f"\n{type_contrainte} ({len(violations)} violations):\n")
                f.write("-" * 60 + "\n")
                penalite_totale = sum(v.penalite for v in violations)
                f.write(f"Pénalité totale: {penalite_totale:.0f}\n")
                
                # Afficher quelques exemples
                for i, v in enumerate(violations[:10], 1):
                    f.write(f"\n{i}. {v.description}\n")
                    if v.match_concerne:
                        f.write(f"   Match: {v.match_concerne}\n")
                
                if len(violations) > 10:
                    f.write(f"\n... et {len(violations) - 10} autres violations\n")


if __name__ == "__main__":
    sys.exit(main())
