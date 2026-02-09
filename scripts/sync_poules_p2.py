#!/usr/bin/env python3
"""
Script pour synchroniser les données du fichier PoulesP2.xlsx vers la configuration Excel.

Ce script:
1. Parse le fichier PoulesP2.xlsx pour extraire les équipes, poules et types de championnat
2. Compare avec le fichier de configuration existant
3. Crée une copie mise à jour du fichier de configuration tout en préservant les données supplémentaires

Format des poules: [SPORT][Genre][Niveau]P[Lettre]
Exemple: VBFA1PA = Volleyball Féminin A1 Poule A

Usage:
    python scripts/sync_poules_p2.py --poules data/volleyball/PoulesP2.xlsx --config data/volleyball/config_volleyP2.xlsx
    python scripts/sync_poules_p2.py --poules data/volleyball/PoulesP2.xlsx --config data/volleyball/config_volleyP2.xlsx --dry-run
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Set, Tuple
from dataclasses import dataclass, field
import shutil

import pandas as pd

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))


@dataclass
class EquipeInfo:
    """Information sur une équipe extraite du fichier des poules."""
    nom: str
    genre: str  # 'F' ou 'M'
    niveau: str  # 'A1', 'A2', 'A3', 'A4'
    poule: str  # 'VBFA1PA', etc.
    horaire: str  # '14H', '16H', etc.
    
    @property
    def cle_unique(self) -> Tuple[str, str]:
        """Clé unique pour identifier une équipe: (nom, genre)"""
        return (self.nom, self.genre)
    
    @property
    def horaire_prefere(self) -> str:
        """Convertit l'horaire du format '14H' en '14:00'."""
        if self.horaire and self.horaire.endswith('H'):
            h = self.horaire[:-1]
            return f"{h}:00"
        return self.horaire


@dataclass
class PouleInfo:
    """Information sur une poule extraite du fichier des poules."""
    nom: str  # 'VBFA1PA', etc.
    genre: str  # 'F' ou 'M'
    niveau: str  # 'A1', 'A2', 'A3', 'A4'
    lettre: str  # 'A', 'B', 'C', etc.
    type_championnat: str  # 'Classique' ou 'Aller-Retour'
    equipes: List[EquipeInfo] = field(default_factory=list)


class PoulesParser:
    """Parser pour le fichier PoulesP2.xlsx."""
    
    # Pattern pour identifier une poule: VB[FM]A[1-4]P[A-Z]
    POULE_PATTERN = re.compile(r'^VB([FM])A([1-4])P([A-Z])$')
    
    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.equipes: List[EquipeInfo] = []
        self.poules: Dict[str, PouleInfo] = {}
    
    def parse(self) -> Tuple[List[EquipeInfo], Dict[str, PouleInfo]]:
        """Parse le fichier Excel et extrait les équipes et poules."""
        # Lire le fichier sans header
        df = pd.read_excel(self.filepath, sheet_name=0, header=None)
        
        current_genre = None
        current_niveau_cols = {}  # {col_index: niveau}
        current_poule_cols = {}   # {col_index: poule_name}
        
        for row_idx, row in df.iterrows():
            # Détecter le genre (VOLLEY FÉMININ ou VOLLEY MASCULIN)
            if pd.notna(row[0]):
                val = str(row[0]).strip().upper()
                if 'FÉMININ' in val or 'FEMININ' in val:
                    current_genre = 'F'
                    current_niveau_cols = {}
                    current_poule_cols = {}
                elif 'MASCULIN' in val:
                    current_genre = 'M'
                    current_niveau_cols = {}
                    current_poule_cols = {}
            
            if current_genre is None:
                continue
            
            # Parcourir chaque colonne
            for col_idx, cell in enumerate(row):
                if pd.isna(cell):
                    continue
                    
                cell_str = str(cell).strip()
                
                # Détecter les niveaux (NIVEAU A1, NIVEAU A2, etc.)
                if cell_str.startswith('NIVEAU A'):
                    niveau = cell_str.replace('NIVEAU ', '')
                    current_niveau_cols[col_idx] = niveau
                    continue
                
                # Détecter les noms de poules (VBFA1PA, VBMA2PB, etc.)
                match = self.POULE_PATTERN.match(cell_str)
                if match:
                    genre, niveau_num, lettre = match.groups()
                    niveau = f"A{niveau_num}"
                    poule_name = cell_str
                    current_poule_cols[col_idx] = poule_name
                    
                    # Initialiser la poule si elle n'existe pas encore
                    if poule_name not in self.poules:
                        self.poules[poule_name] = PouleInfo(
                            nom=poule_name,
                            genre=genre,
                            niveau=niveau,
                            lettre=lettre,
                            type_championnat='Classique'  # Valeur par défaut
                        )
                    continue
                
                # Détecter CHAMPIONNAT -> indique une poule classique
                if cell_str == 'CHAMPIONNAT':
                    # Chercher la poule associée à cette colonne
                    poule_col = col_idx
                    if poule_col in current_poule_cols:
                        poule_name = current_poule_cols[poule_col]
                        if poule_name in self.poules:
                            self.poules[poule_name].type_championnat = 'Classique'
                    continue
                
                # Détecter une équipe (format: NOM (N) où N est un numéro)
                if self._is_team_name(cell_str):
                    # Trouver la poule de cette colonne
                    poule_col = col_idx
                    
                    # Chercher dans la colonne précédente l'horaire
                    horaire = None
                    if col_idx + 1 < len(row) and pd.notna(row[col_idx + 1]):
                        horaire_val = str(row[col_idx + 1]).strip()
                        if horaire_val.endswith('H'):
                            horaire = horaire_val
                    
                    # Trouver la poule correspondante
                    if poule_col in current_poule_cols:
                        poule_name = current_poule_cols[poule_col]
                        if poule_name in self.poules:
                            poule = self.poules[poule_name]
                            equipe = EquipeInfo(
                                nom=cell_str,
                                genre=poule.genre,
                                niveau=poule.niveau,
                                poule=poule_name,
                                horaire=horaire or ''
                            )
                            self.equipes.append(equipe)
                            poule.equipes.append(equipe)
        
        # Déterminer le type de championnat pour chaque poule
        self._determine_pool_types(df)
        
        return self.equipes, self.poules
    
    def _is_team_name(self, text: str) -> bool:
        """Vérifie si le texte ressemble à un nom d'équipe."""
        # Pattern: NOM (N) ou NOM (N) avec des caractères spéciaux
        if not text or text in ('CHAMPIONNAT', 'NaN'):
            return False
        
        # Exclure les patterns de poule
        if self.POULE_PATTERN.match(text):
            return False
        
        # Exclure les niveaux
        if text.startswith('NIVEAU'):
            return False
        
        # Exclure les compteurs d'équipes
        if 'Equipes' in text or 'équipes' in text or 'Total' in text:
            return False
        
        # Pattern pour une équipe: contient généralement des parenthèses avec un numéro
        team_pattern = re.compile(r'^.+\s*\(\d+\)$')
        return bool(team_pattern.match(text))
    
    def _determine_pool_types(self, df: pd.DataFrame):
        """
        Détermine le type de championnat pour chaque poule.
        
        Règle: Si une poule a 4 équipes, c'est un aller-retour (6 matchs = 2 journées par match).
        Si elle a 5 ou 6 équipes, c'est classique (chacun joue une fois contre les autres).
        """
        for poule_name, poule in self.poules.items():
            nb_equipes = len(poule.equipes)
            # Les petites poules (4 équipes) sont généralement en aller-retour
            # Les grandes poules (5-6 équipes) sont classiques
            if nb_equipes <= 4:
                poule.type_championnat = 'Aller-Retour'
            else:
                poule.type_championnat = 'Classique'


class ConfigUpdater:
    """Met à jour le fichier de configuration Excel."""
    
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.sheets: Dict[str, pd.DataFrame] = {}
        self._load_sheets()
    
    def _load_sheets(self):
        """Charge toutes les feuilles du fichier de configuration."""
        xl = pd.ExcelFile(self.config_path)
        for sheet_name in xl.sheet_names:
            self.sheets[sheet_name] = pd.read_excel(self.config_path, sheet_name=sheet_name)
    
    def update_equipes(
        self, 
        equipes: List[EquipeInfo],
        preserve_extra_columns: bool = True
    ) -> Tuple[int, int, int]:
        """
        Met à jour la feuille Equipes.
        
        Returns:
            Tuple (ajoutées, modifiées, supprimées)
        """
        df_equipes = self.sheets['Equipes'].copy()
        
        # Créer un dictionnaire des équipes existantes avec leurs données supplémentaires
        existing_teams: Dict[Tuple[str, str], pd.Series] = {}
        for idx, row in df_equipes.iterrows():
            key = (row['Equipe'], row['Genre_Equipe'])
            existing_teams[key] = row
        
        # Créer les nouvelles lignes
        new_rows = []
        processed_keys: Set[Tuple[str, str]] = set()
        
        ajoutees = 0
        modifiees = 0
        
        for equipe in equipes:
            key = equipe.cle_unique
            processed_keys.add(key)
            
            if key in existing_teams:
                # Équipe existante -> conserver les données supplémentaires
                old_row = existing_teams[key]
                new_row = {
                    'Equipe': equipe.nom,
                    'Niveau_Equipe': equipe.niveau,
                    'Genre_Equipe': equipe.genre,
                    'Poule': equipe.poule,
                    'Horaire_Prefere': equipe.horaire_prefere,
                }
                
                # Préserver les colonnes supplémentaires
                if preserve_extra_columns:
                    for col in df_equipes.columns:
                        if col not in new_row:
                            new_row[col] = old_row[col]
                
                # Vérifier s'il y a eu des modifications
                changed = False
                for col in ['Niveau_Equipe', 'Poule', 'Horaire_Prefere']:
                    old_val = old_row.get(col, '')
                    new_val = new_row.get(col, '')
                    if pd.isna(old_val):
                        old_val = ''
                    if pd.isna(new_val):
                        new_val = ''
                    if str(old_val) != str(new_val):
                        changed = True
                        break
                
                if changed:
                    modifiees += 1
                
                new_rows.append(new_row)
            else:
                # Nouvelle équipe
                new_row = {
                    'Equipe': equipe.nom,
                    'Niveau_Equipe': equipe.niveau,
                    'Genre_Equipe': equipe.genre,
                    'Poule': equipe.poule,
                    'Horaire_Prefere': equipe.horaire_prefere,
                }
                
                # Ajouter des colonnes vides pour les données supplémentaires
                for col in df_equipes.columns:
                    if col not in new_row:
                        new_row[col] = None
                
                new_rows.append(new_row)
                ajoutees += 1
        
        # Compter les équipes supprimées
        supprimees = len(set(existing_teams.keys()) - processed_keys)
        
        # Créer le nouveau DataFrame
        self.sheets['Equipes'] = pd.DataFrame(new_rows, columns=df_equipes.columns)
        
        return ajoutees, modifiees, supprimees
    
    def update_types_poules(
        self, 
        poules: Dict[str, PouleInfo],
        preserve_existing_types: bool = True
    ) -> Tuple[int, int]:
        """
        Met à jour la feuille Types_Poules.
        
        Args:
            poules: Dictionnaire des poules extraites
            preserve_existing_types: Si True, préserve les types existants dans la config
        
        Returns:
            Tuple (ajoutées, modifiées)
        """
        df_types = self.sheets['Types_Poules'].copy()
        
        # Créer un mapping des types existants
        existing_types: Dict[str, str] = {}
        for _, row in df_types.iterrows():
            if pd.notna(row['Poule']):
                existing_types[str(row['Poule'])] = str(row['Type']) if pd.notna(row['Type']) else 'Classique'
        
        new_rows = []
        ajoutees = 0
        modifiees = 0
        
        for poule_name, poule in poules.items():
            if preserve_existing_types and poule_name in existing_types:
                # Préserver le type existant
                type_val = existing_types[poule_name]
            else:
                # Utiliser le type déduit (basé sur le nombre d'équipes)
                type_val = poule.type_championnat
                if poule_name not in existing_types:
                    ajoutees += 1
                elif existing_types[poule_name] != type_val:
                    modifiees += 1
            
            new_rows.append({
                'Poule': poule_name,
                'Type': type_val,
                'Remarques': None
            })
        
        self.sheets['Types_Poules'] = pd.DataFrame(new_rows, columns=['Poule', 'Type', 'Remarques'])
        
        return ajoutees, modifiees
    
    def save(self, output_path: Path):
        """Sauvegarde toutes les feuilles dans un nouveau fichier."""
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            for sheet_name, df in self.sheets.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)


def print_summary(equipes: List[EquipeInfo], poules: Dict[str, PouleInfo]):
    """Affiche un récapitulatif des données extraites."""
    print("\n" + "=" * 60)
    print("RÉCAPITULATIF DES DONNÉES EXTRAITES")
    print("=" * 60)
    
    # Statistiques globales
    print(f"\n📊 STATISTIQUES GLOBALES")
    print(f"   Total équipes: {len(equipes)}")
    print(f"   Total poules: {len(poules)}")
    
    # Par genre
    equipes_f = [e for e in equipes if e.genre == 'F']
    equipes_m = [e for e in equipes if e.genre == 'M']
    poules_f = [p for p in poules.values() if p.genre == 'F']
    poules_m = [p for p in poules.values() if p.genre == 'M']
    
    print(f"\n👩 FÉMININ")
    print(f"   Équipes: {len(equipes_f)}")
    print(f"   Poules: {len(poules_f)}")
    
    print(f"\n👨 MASCULIN")
    print(f"   Équipes: {len(equipes_m)}")
    print(f"   Poules: {len(poules_m)}")
    
    # Types de championnat
    classique = sum(1 for p in poules.values() if p.type_championnat == 'Classique')
    aller_retour = sum(1 for p in poules.values() if p.type_championnat == 'Aller-Retour')
    
    print(f"\n🏆 TYPES DE CHAMPIONNAT")
    print(f"   Classique: {classique} poules")
    print(f"   Aller-Retour: {aller_retour} poules")
    
    # Détail par niveau
    print(f"\n📋 DÉTAIL PAR NIVEAU")
    for niveau in ['A1', 'A2', 'A3', 'A4']:
        niveau_equipes = [e for e in equipes if e.niveau == niveau]
        niveau_poules = [p for p in poules.values() if p.niveau == niveau]
        if niveau_equipes:
            print(f"\n   {niveau}:")
            print(f"      Équipes: {len(niveau_equipes)}")
            print(f"      Poules: {len(niveau_poules)}")
            for p in sorted(niveau_poules, key=lambda x: x.nom):
                nb_eq = len(p.equipes)
                print(f"         {p.nom}: {nb_eq} équipes ({p.type_championnat})")
    
    print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Synchronise les données du fichier PoulesP2.xlsx vers la configuration Excel"
    )
    
    parser.add_argument(
        '--poules', '-p',
        type=Path,
        default=PROJECT_ROOT / 'data/volleyball/PoulesP2.xlsx',
        help="Chemin vers le fichier PoulesP2.xlsx"
    )
    
    parser.add_argument(
        '--config', '-c',
        type=Path,
        default=PROJECT_ROOT / 'data/volleyball/config_volleyP2.xlsx',
        help="Chemin vers le fichier de configuration Excel"
    )
    
    parser.add_argument(
        '--output', '-o',
        type=Path,
        default=None,
        help="Chemin de sortie pour le fichier mis à jour (défaut: config_updated_YYYYMMDD_HHMMSS.xlsx)"
    )
    
    parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help="Mode simulation: affiche ce qui serait fait sans créer de fichier"
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help="Mode verbeux: affiche plus de détails"
    )
    
    args = parser.parse_args()
    
    # Vérifier que les fichiers existent
    if not args.poules.exists():
        print(f"❌ Erreur: Le fichier {args.poules} n'existe pas")
        sys.exit(1)
    
    if not args.config.exists():
        print(f"❌ Erreur: Le fichier {args.config} n'existe pas")
        sys.exit(1)
    
    print(f"📂 Fichier des poules: {args.poules}")
    print(f"📂 Fichier de configuration: {args.config}")
    
    # Parser le fichier des poules
    print("\n⏳ Parsing du fichier des poules...")
    poules_parser = PoulesParser(args.poules)
    equipes, poules = poules_parser.parse()
    
    # Afficher le récapitulatif
    print_summary(equipes, poules)
    
    if args.dry_run:
        print("\n🔍 MODE SIMULATION (--dry-run)")
        print("   Aucun fichier ne sera créé.")
        return
    
    # Charger et mettre à jour la configuration
    print("\n⏳ Mise à jour de la configuration...")
    config_updater = ConfigUpdater(args.config)
    
    # Mettre à jour les équipes
    ajoutees, modifiees, supprimees = config_updater.update_equipes(equipes)
    print(f"\n📝 FEUILLE 'Equipes':")
    print(f"   ➕ Ajoutées: {ajoutees}")
    print(f"   ✏️  Modifiées: {modifiees}")
    print(f"   ➖ Supprimées: {supprimees}")
    
    # Mettre à jour les types de poules
    poules_ajoutees, poules_modifiees = config_updater.update_types_poules(poules)
    print(f"\n📝 FEUILLE 'Types_Poules':")
    print(f"   ➕ Ajoutées: {poules_ajoutees}")
    print(f"   ✏️  Modifiées: {poules_modifiees}")
    
    # Déterminer le chemin de sortie
    if args.output:
        output_path = args.output
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = args.config.parent / f"config_volleyP2_updated_{timestamp}.xlsx"
    
    # Sauvegarder
    config_updater.save(output_path)
    print(f"\n✅ Fichier sauvegardé: {output_path}")


if __name__ == '__main__':
    main()
