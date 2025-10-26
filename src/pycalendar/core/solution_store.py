"""
Gestionnaire de stockage et chargement des solutions de planification.

Ce module permet de :
- Sauvegarder les solutions avec metadata
- Charger les solutions précédentes
- Détecter les changements de configuration
- Adapter les solutions aux nouvelles configurations
- Créer des hints pour le solver CP-SAT
"""

from pathlib import Path
import json
import hashlib
from datetime import datetime
from typing import Optional, Dict, List, Tuple, Set
from dataclasses import dataclass, asdict

from pycalendar.core.models import Solution, Match, Creneau, Equipe
from pycalendar.core.config import Config


@dataclass
class ConfigSignature:
    """Signature d'une configuration pour détecter les changements."""
    
    # Hash du fichier YAML
    yaml_hash: str
    
    # Hash du fichier Excel (feuilles Equipes + Gymnases)
    excel_hash: str
    
    # Informations structurelles
    nb_equipes: int
    nb_gymnases: int
    nb_creneaux: int
    nb_semaines: int
    
    # Liste des équipes (pour détecter ajouts/suppressions)
    equipes_ids: List[str]  # Liste des id_unique
    
    # Liste des gymnases
    gymnases: List[str]
    
    def to_dict(self) -> dict:
        """Convertit en dictionnaire."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ConfigSignature':
        """Crée depuis un dictionnaire."""
        return cls(**data)
    
    def compare(self, other: 'ConfigSignature') -> Dict[str, bool]:
        """
        Compare deux signatures et identifie les changements.
        
        Returns:
            Dict avec les types de changements détectés
        """
        changes = {
            'yaml_changed': self.yaml_hash != other.yaml_hash,
            'excel_changed': self.excel_hash != other.excel_hash,
            'equipes_changed': set(self.equipes_ids) != set(other.equipes_ids),
            'gymnases_changed': set(self.gymnases) != set(other.gymnases),
            'structure_changed': (
                self.nb_equipes != other.nb_equipes or
                self.nb_gymnases != other.nb_gymnases or
                self.nb_semaines != other.nb_semaines
            )
        }
        
        changes['any_change'] = any(changes.values())
        changes['critical_change'] = changes['equipes_changed'] or changes['structure_changed']
        
        return changes


class SolutionStore:
    """Gère le stockage et chargement des solutions."""
    
    def __init__(self, solutions_dir: Path = None, solution_name: str = "default"):
        """
        Initialise le gestionnaire de solutions.
        
        Args:
            solutions_dir: Répertoire pour stocker les solutions (défaut: ./solutions)
            solution_name: Nom de la configuration (ex: "volley", "handball", "default")
                          Permet d'avoir des solutions distinctes par configuration
        """
        self.solutions_dir = solutions_dir or Path("solutions")
        self.solutions_dir.mkdir(exist_ok=True)
        
        self.solution_name = solution_name
        self.latest_file = self.solutions_dir / f"latest_{solution_name}.json"
    
    @staticmethod
    def compute_file_hash(file_path: Path) -> str:
        """
        Calcule le hash MD5 d'un fichier.
        
        Args:
            file_path: Chemin du fichier
            
        Returns:
            Hash MD5 en hexadécimal
        """
        if not file_path.exists():
            return "none"
        
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            # Lire par blocs pour les gros fichiers
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    @staticmethod
    def compute_excel_structural_hash(config_manager) -> str:
        """
        Calcule un hash basé sur la structure du fichier Excel.
        
        Ne prend en compte que les feuilles Equipes et Gymnases pour détecter
        les changements structurels (ajout/suppression d'équipes/gymnases).
        
        Args:
            config_manager: Instance de ConfigManager
            
        Returns:
            Hash MD5 de la structure
        """
        hasher = hashlib.md5()
        
        # Hash de la feuille Equipes (uniquement les colonnes structurelles)
        df_equipes = config_manager.lire_feuille('Equipes')
        if df_equipes is not None and 'Equipe' in df_equipes.columns:
            equipes_sorted = sorted(df_equipes['Equipe'].dropna().astype(str).tolist())
            hasher.update(json.dumps(equipes_sorted, sort_keys=True).encode('utf-8'))
        
        # Hash de la feuille Gymnases
        df_gymnases = config_manager.lire_feuille('Gymnases')
        if df_gymnases is not None and 'Gymnase' in df_gymnases.columns:
            gymnases_sorted = sorted(df_gymnases['Gymnase'].dropna().astype(str).tolist())
            hasher.update(json.dumps(gymnases_sorted, sort_keys=True).encode('utf-8'))
        
        return hasher.hexdigest()
    
    def create_signature(self, yaml_path: Path, config_manager, 
                        equipes: List[Equipe], gymnases: List[str],
                        nb_creneaux: int, nb_semaines: int) -> ConfigSignature:
        """
        Crée une signature de la configuration actuelle.
        
        Args:
            yaml_path: Chemin du fichier YAML
            config_manager: Instance de ConfigManager
            equipes: Liste des équipes
            gymnases: Liste des noms de gymnases
            nb_creneaux: Nombre total de créneaux
            nb_semaines: Nombre de semaines
            
        Returns:
            Signature de la configuration
        """
        return ConfigSignature(
            yaml_hash=self.compute_file_hash(yaml_path),
            excel_hash=self.compute_excel_structural_hash(config_manager),
            nb_equipes=len(equipes),
            nb_gymnases=len(gymnases),
            nb_creneaux=nb_creneaux,
            nb_semaines=nb_semaines,
            equipes_ids=[eq.id_unique for eq in equipes],
            gymnases=sorted(gymnases)
        )
    
    def save_solution(self, solution: Solution, signature: ConfigSignature,
                     config: Optional[Config] = None, config_name: str = "unknown", 
                     fixed_matches: Optional[List] = None,
                     equipes: Optional[List] = None, gymnases: Optional[List] = None, 
                     creneaux: Optional[List] = None) -> Path:
        """
        Sauvegarde une solution au format JSON enrichi.
        
        Le format inclut:
        - Entities (equipes, gymnases, poules)
        - Matches enrichis avec toutes les infos
        - Slots (disponibles et occupés)
        - Statistics complètes
        
        Args:
            solution: La solution à sauvegarder
            signature: Signature de la configuration utilisée
            config: Objet Config pour enrichissement
            config_name: Nom de la configuration (pour traçabilité)
            fixed_matches: Liste des matchs fixes originaux
            equipes: Liste des équipes (objets Equipe)
            gymnases: Liste des gymnases (objets Gymnase)
            creneaux: Liste de tous les créneaux (disponibles + occupés)
            
        Returns:
            Path du fichier sauvegardé
        """
        print(f"  💾 Sauvegarde de la solution...")
        
        # Import DataFormatter
        try:
            import sys
            from pathlib import Path as P
            # Ajouter le répertoire racine du projet au sys.path pour que les imports core.* fonctionnent
            project_root = P(__file__).parent.parent
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))
            
            from interface.core.data_formatter import DataFormatter
        except ImportError as e:
            print(f"  ❌ Impossible d'importer DataFormatter: {e}")
            raise ImportError(f"DataFormatter requis pour la sauvegarde: {e}")
        
        # Marquer les matchs fixes dans les metadata
        if fixed_matches:
            fixed_keys = set()
            for fm in fixed_matches:
                key = (fm.equipe1.id_unique, fm.equipe2.id_unique, fm.creneau.semaine if fm.creneau else None)
                fixed_keys.add(key)
            
            for match in solution.matchs_planifies:
                key = (match.equipe1.id_unique, match.equipe2.id_unique, match.creneau.semaine if match.creneau else None)
                if key in fixed_keys:
                    match.metadata["is_fixed"] = True
        
        # Utiliser DataFormatter pour générer le JSON
        data = DataFormatter.format_solution(
            solution=solution,
            config=config,
            equipes=equipes,
            gymnases=gymnases,
            creneaux_disponibles=creneaux
        )
        
        # Ajouter la signature de configuration
        data["config_signature"] = signature.to_dict()
        
        # Sauvegarder
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        filename = self.solutions_dir / f"solution_{self.solution_name}_{timestamp}.json"
        latest = self.latest_file
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        with open(latest, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        file_size = filename.stat().st_size / 1024  # KB
        
        # Validation optionnelle
        try:
            from interface.core.validator import SolutionValidator
            validator = SolutionValidator()
            is_valid, errors = validator.validate(data)
            
            if is_valid:
                print(f"  ✅ Solution sauvegardée et validée: {filename.name}")
            else:
                print(f"  ⚠️  Solution sauvegardée mais validation échouée ({len(errors)} erreurs)")
                if errors:
                    print(f"     Première erreur: {errors[0]}")
        except ImportError:
            print(f"  ✅ Solution sauvegardée (validation non disponible): {filename.name}")
        except Exception as e:
            print(f"  ⚠️  Erreur de validation: {e}")
            print(f"  ✅ Solution sauvegardée: {filename.name}")
        
        print(f"     Taille: {file_size:.1f} KB")
        print(f"     Poules: {len(data.get('entities', {}).get('poules', []))}")
        print(f"     Matchs: {len(data.get('matches', {}).get('scheduled', []))}")
        
        return filename
    
    def load_latest(self) -> Optional[dict]:
        """
        Charge la dernière solution sauvegardée.
        
        Returns:
            Dictionnaire avec la solution, ou None si aucune solution
        """
        if not self.latest_file.exists():
            return None
        
        try:
            with open(self.latest_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"  ⚠️  Erreur lors du chargement de la solution précédente: {e}")
            return None
    
    def validate_and_adapt_solution(self, solution_data: dict, 
                                    current_signature: ConfigSignature,
                                    matchs: List[Match], 
                                    creneaux: List[Creneau]) -> Tuple[Dict, Dict]:
        """
        Valide une solution précédente et l'adapte à la nouvelle configuration.
        
        Cette méthode :
        1. Détecte les changements de configuration
        2. Valide chaque assignment (équipes et créneaux existent toujours ?)
        3. Filtre les assignments invalides
        4. Retourne un hint adapté pour CP-SAT
        
        Args:
            solution_data: Données de la solution précédente
            current_signature: Signature de la configuration actuelle
            matchs: Liste des matchs actuels
            creneaux: Liste des créneaux actuels
            
        Returns:
            Tuple (hint, stats) où :
            - hint: Dict {(match_idx, creneau_idx): 1} pour les assignments valides
            - stats: Dict avec statistiques de validation
        """
        # Extraire la signature de la solution précédente
        old_signature = ConfigSignature.from_dict(solution_data["config_signature"])
        
        # Comparer les signatures
        changes = current_signature.compare(old_signature)
        
        stats = {
            'changes': changes,
            'total_assignments': len(solution_data["assignments"]),
            'valid_assignments': 0,
            'invalid_match': 0,
            'invalid_creneau': 0,
            'adapted': False
        }
        
        # Si aucun changement, on peut utiliser la solution telle quelle
        if not changes['any_change']:
            print("  ✅ Configuration inchangée, réutilisation directe de la solution")
            stats['adapted'] = False
        else:
            print("  🔄 Configuration modifiée, adaptation de la solution...")
            self._print_changes(changes)
            stats['adapted'] = True
        
        # Créer des lookups rapides
        matchs_lookup = self._create_matchs_lookup(matchs)
        creneaux_lookup = self._create_creneaux_lookup(creneaux)
        
        hint = {}
        
        # Valider chaque assignment
        for assignment in solution_data["assignments"]:
            # Trouver le match correspondant dans la nouvelle configuration
            match_idx = self._find_match_index(
                matchs_lookup,
                assignment["equipe1_id"],
                assignment["equipe2_id"]
            )
            
            if match_idx is None:
                stats['invalid_match'] += 1
                continue
            
            # Trouver le créneau correspondant
            creneau_key = (
                assignment["semaine"],
                assignment["horaire"],
                assignment["gymnase"]
            )
            creneau_idx = creneaux_lookup.get(creneau_key)
            
            if creneau_idx is None:
                stats['invalid_creneau'] += 1
                continue
            
            # Assignment valide !
            hint[(match_idx, creneau_idx)] = 1
            stats['valid_assignments'] += 1
        
        # Afficher les statistiques
        self._print_validation_stats(stats)
        
        return hint, stats
    
    def _create_matchs_lookup(self, matchs: List[Match]) -> Dict[Tuple[str, str], int]:
        """
        Crée un dictionnaire de lookup pour les matchs.
        
        Returns:
            Dict {(equipe1_id, equipe2_id): match_idx}
        """
        lookup = {}
        for idx, match in enumerate(matchs):
            # Créer clé bidirectionnelle (peu importe l'ordre des équipes)
            key1 = (match.equipe1.id_unique, match.equipe2.id_unique)
            key2 = (match.equipe2.id_unique, match.equipe1.id_unique)
            lookup[key1] = idx
            lookup[key2] = idx
        return lookup
    
    def _create_creneaux_lookup(self, creneaux: List[Creneau]) -> Dict[Tuple, int]:
        """
        Crée un dictionnaire de lookup pour les créneaux.
        
        Returns:
            Dict {(semaine, horaire, gymnase): creneau_idx}
        """
        return {
            (c.semaine, c.horaire, c.gymnase): idx
            for idx, c in enumerate(creneaux)
        }
    
    def _find_match_index(self, matchs_lookup: Dict, 
                         eq1_id: str, eq2_id: str) -> Optional[int]:
        """
        Trouve l'index d'un match dans le lookup.
        
        Args:
            matchs_lookup: Dictionnaire de lookup des matchs
            eq1_id: ID unique de l'équipe 1
            eq2_id: ID unique de l'équipe 2
            
        Returns:
            Index du match, ou None si non trouvé
        """
        return matchs_lookup.get((eq1_id, eq2_id))
    
    def _print_changes(self, changes: Dict[str, bool]):
        """Affiche les changements détectés."""
        if changes['yaml_changed']:
            print("     • Configuration YAML modifiée")
        if changes['excel_changed']:
            print("     • Fichier Excel modifié")
        if changes['equipes_changed']:
            print("     • Équipes ajoutées/supprimées")
        if changes['gymnases_changed']:
            print("     • Gymnases ajoutés/supprimés")
        if changes['structure_changed']:
            print("     • Structure globale modifiée")
    
    def _print_validation_stats(self, stats: Dict):
        """Affiche les statistiques de validation."""
        total = stats['total_assignments']
        valid = stats['valid_assignments']
        invalid_match = stats['invalid_match']
        invalid_creneau = stats['invalid_creneau']
        
        if valid > 0:
            pourcentage = (valid / total) * 100
            print(f"  📊 Assignments réutilisables: {valid}/{total} ({pourcentage:.1f}%)")
        
        if invalid_match > 0:
            print(f"     ⚠️  {invalid_match} matchs non trouvés (équipes modifiées)")
        
        if invalid_creneau > 0:
            print(f"     ⚠️  {invalid_creneau} créneaux non trouvés (planning modifié)")
        
        if valid == 0:
            print("  ⚠️  Aucun assignment réutilisable, résolution depuis zéro")


def test_solution_store():
    """Fonction de test pour vérifier le bon fonctionnement."""
    print("Test du SolutionStore...")
    
    # Créer un store
    store = SolutionStore(Path("test_solutions"))
    
    # Créer une signature fictive
    sig = ConfigSignature(
        yaml_hash="abc123",
        excel_hash="def456",
        nb_equipes=50,
        nb_gymnases=5,
        nb_creneaux=100,
        nb_semaines=10,
        equipes_ids=["LYON1_M", "LYON2_M"],
        gymnases=["GYM1", "GYM2"]
    )
    
    print(f"✅ Signature créée: {sig}")
    print(f"✅ Hash YAML: {sig.yaml_hash}")
    
    # Tester la comparaison
    sig2 = ConfigSignature(
        yaml_hash="abc123",  # identique
        excel_hash="xxx999",  # différent
        nb_equipes=50,
        nb_gymnases=5,
        nb_creneaux=100,
        nb_semaines=10,
        equipes_ids=["LYON1_M", "LYON2_M"],
        gymnases=["GYM1", "GYM2"]
    )
    
    changes = sig.compare(sig2)
    print(f"✅ Changements détectés: {changes}")
    
    print("\n✅ Tous les tests passés!")


if __name__ == "__main__":
    test_solution_store()
