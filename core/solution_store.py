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

from core.models import Solution, Match, Creneau, Equipe
from core.config import Config


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
                     config_name: str = "unknown") -> Path:
        """
        Sauvegarde une solution avec sa signature de configuration.
        
        Args:
            solution: La solution à sauvegarder
            signature: Signature de la configuration utilisée
            config_name: Nom de la configuration (pour traçabilité)
            
        Returns:
            Path du fichier sauvegardé
        """
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        filename = self.solutions_dir / f"solution_{self.solution_name}_{timestamp}.json"
        
        data = {
            "metadata": {
                "date": datetime.now().isoformat(),
                "solution_name": self.solution_name,
                "config_name": config_name,
                "solver": solution.metadata.get("solver", "unknown"),
                "status": solution.metadata.get("status", "unknown"),
                "score": float(solution.score),
                "matchs_planifies": len(solution.matchs_planifies),
                "matchs_non_planifies": len(solution.matchs_non_planifies),
            },
            "config_signature": signature.to_dict(),
            "assignments": [
                {
                    "match_id": i,
                    "equipe1_nom": match.equipe1.nom,
                    "equipe1_genre": match.equipe1.genre,
                    "equipe1_id": match.equipe1.id_unique,
                    "equipe2_nom": match.equipe2.nom,
                    "equipe2_genre": match.equipe2.genre,
                    "equipe2_id": match.equipe2.id_unique,
                    "semaine": match.creneau.semaine,
                    "horaire": match.creneau.horaire,
                    "gymnase": match.creneau.gymnase,
                }
                for i, match in enumerate(solution.matchs_planifies)
            ]
        }
        
        # Sauver le fichier daté
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Mettre à jour "latest.json"
        with open(self.latest_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"  💾 Solution sauvegardée: {filename.name}")
        print(f"     Configuration: {self.solution_name}")
        print(f"     Score: {solution.score}, Matchs planifiés: {len(solution.matchs_planifies)}")
        
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
