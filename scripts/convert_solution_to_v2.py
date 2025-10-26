#!/usr/bin/env python3
"""
Script de conversion de solutions PyCalendar vers format v2.0 pour l'interface.

Convertit les fichiers JSON du format actuel (simple liste d'assignments)
vers le format v2.0 enrichi (entities + matches détaillés + penalties).

Usage:
    python scripts/convert_solution_to_v2.py solutions/latest_volley.json
    python scripts/convert_solution_to_v2.py solutions/latest_volley.json -o output.json
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Set, Tuple

# Ajouter le répertoire parent au path pour imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pycalendar.core.config_manager import ConfigManager
from pycalendar.core.models import Equipe
from typing import Optional


class SolutionConverterV2:
    """Convertit les solutions au format v2.0 pour l'interface."""
    
    def __init__(self, solution_path: Path, config_manager: Optional[ConfigManager] = None,
                 equipes_list: Optional[List[Equipe]] = None):
        """
        Initialise le convertisseur.
        
        Args:
            solution_path: Chemin vers le fichier JSON de solution
            config_manager: Instance de ConfigManager (optionnel, pour enrichissement)
            equipes_list: Liste des objets Equipe (optionnel, pour enrichissement complet)
        """
        self.solution_path = solution_path
        self.config_manager = config_manager
        
        # Créer un index des équipes par ID pour accès rapide
        self.equipes_index = {}
        if equipes_list:
            for eq in equipes_list:
                self.equipes_index[eq.id_unique] = eq
        
        # Charger la solution source
        with open(solution_path, 'r', encoding='utf-8') as f:
            self.solution_data = json.load(f)
    
    def _extract_entities(self) -> Dict:
        """
        Extrait les entités (équipes, gymnases, poules) depuis la solution.
        
        Returns:
            Dict avec equipes, gymnases, poules
        """
        equipes_dict = {}
        gymnases_set = set()
        
        # Parcourir les assignments pour extraire les informations
        for assignment in self.solution_data.get('assignments', []):
            # Équipe 1
            eq1_id = assignment['equipe1_id']
            if eq1_id not in equipes_dict:
                # Extraire institution et numéro depuis le nom
                nom = assignment['equipe1_nom']
                institution, numero = self._parse_equipe_nom(nom)
                genre = assignment['equipe1_genre']
                
                # Créer le nom complet avec le genre
                nom_complet = f"{nom} ({genre})"
                
                # Utiliser la poule depuis l'assignment si disponible (format v1.0 amélioré)
                poule_from_assignment = assignment.get('poule', '')
                
                # Récupérer les données enrichies depuis la liste d'équipes si disponible
                horaires_preferes = []
                lieux_preferes = []
                semaines_indisponibles = {}
                
                equipe_obj = self._find_equipe_in_config(eq1_id)
                if equipe_obj:
                    horaires_preferes = equipe_obj.horaires_preferes or []
                    lieux_preferes = [str(lieu) for lieu in (equipe_obj.lieux_preferes or []) if lieu is not None]
                    semaines_indisponibles = {
                        str(k): list(v) for k, v in (equipe_obj.semaines_indisponibles or {}).items()
                    }
                
                equipes_dict[eq1_id] = {
                    'id': eq1_id,
                    'nom': nom,
                    'nom_complet': nom_complet,
                    'institution': institution,
                    'numero_equipe': numero,
                    'genre': genre,
                    'poule': poule_from_assignment,  # Poule depuis assignment si disponible
                    'horaires_preferes': horaires_preferes,
                    'lieux_preferes': lieux_preferes,
                    'semaines_indisponibles': semaines_indisponibles,
                    'adversaires': set()  # Pour détecter les poules si non disponibles
                }
            
            # Équipe 2
            eq2_id = assignment['equipe2_id']
            if eq2_id not in equipes_dict:
                nom = assignment['equipe2_nom']
                institution, numero = self._parse_equipe_nom(nom)
                genre = assignment['equipe2_genre']
                nom_complet = f"{nom} ({genre})"
                poule_from_assignment = assignment.get('poule', '')
                
                # Récupérer les données enrichies
                horaires_preferes = []
                lieux_preferes = []
                semaines_indisponibles = {}
                
                equipe_obj = self._find_equipe_in_config(eq2_id)
                if equipe_obj:
                    horaires_preferes = equipe_obj.horaires_preferes or []
                    lieux_preferes = [str(lieu) for lieu in (equipe_obj.lieux_preferes or []) if lieu is not None]
                    semaines_indisponibles = {
                        str(k): list(v) for k, v in (equipe_obj.semaines_indisponibles or {}).items()
                    }
                
                equipes_dict[eq2_id] = {
                    'id': eq2_id,
                    'nom': nom,
                    'nom_complet': nom_complet,
                    'institution': institution,
                    'numero_equipe': numero,
                    'genre': genre,
                    'poule': poule_from_assignment,
                    'horaires_preferes': horaires_preferes,
                    'lieux_preferes': lieux_preferes,
                    'semaines_indisponibles': semaines_indisponibles,
                    'adversaires': set()
                }
            
            # Enregistrer les adversaires pour détection des poules (si poules non disponibles)
            equipes_dict[eq1_id]['adversaires'].add(eq2_id)
            equipes_dict[eq2_id]['adversaires'].add(eq1_id)
            
            # Gymnases
            gymnases_set.add(assignment['gymnase'])
        
        # Vérifier si les poules sont déjà définies dans les assignments
        has_real_pools = any(eq['poule'] for eq in equipes_dict.values())
        
        if has_real_pools:
            # Les poules sont déjà dans les données (format v1.0 amélioré avec champ poule)
            print("  ✅ Poules trouvées dans les données")
            poules_dict = self._build_pools_from_existing_data(equipes_dict)
        else:
            # Pas de poules dans les données → détecter par clustering (ancien format v1.0)
            print("  ⚠️  Poules manquantes → Détection automatique par clustering")
            poules_dict = self._detect_pools_from_matches(equipes_dict)
        
        # Nettoyer les données temporaires (adversaires) avant conversion
        for eq in equipes_dict.values():
            del eq['adversaires']
        
        # Convertir en listes
        equipes_list = sorted(equipes_dict.values(), key=lambda x: x['id'])
        
        # Charger les capacités réelles depuis le config_manager si disponible
        gymnases_capacites = {}
        if self.config_manager:
            try:
                from pycalendar.data.data_loader import DataLoader
                loader = DataLoader(str(self.config_manager.fichier_path))
                gymnases_obj = loader.charger_gymnases()
                gymnases_capacites = {g.nom: g.capacite for g in gymnases_obj}
                print(f"  ✅ Capacités chargées pour {len(gymnases_capacites)} gymnases depuis la config")
            except Exception as e:
                print(f"  ⚠️  Impossible de charger les capacités: {e}")
        
        gymnases_list = [
            {
                'id': g,
                'nom': g,
                'capacite': gymnases_capacites.get(g, 1),  # Capacité réelle ou 1 par défaut
                'horaires_disponibles': [],
                'semaines_indisponibles': {},
                'capacite_reduite': {}
            }
            for g in sorted(gymnases_set)
        ]
        
        poules_list = [
            {
                'id': poule_id,
                'nom': poule_id,
                'genre': list(data['genres'])[0] if data['genres'] else '',
                'niveau': self._extract_niveau_from_poule(poule_id),
                'nb_equipes': len(data['equipes']),
                'equipes_ids': sorted(list(data['equipes'])),
                'nb_matchs_planifies': data['nb_matchs_planifies'],
                'nb_matchs_non_planifies': data['nb_matchs_non_planifies']
            }
            for poule_id, data in sorted(poules_dict.items())
        ]
        
        return {
            'equipes': equipes_list,
            'gymnases': gymnases_list,
            'poules': poules_list
        }
    
    def _build_pools_from_existing_data(self, equipes_dict: Dict) -> Dict:
        """
        Construit les poules depuis les données existantes des équipes.
        
        Args:
            equipes_dict: Dictionnaire des équipes avec leur poule déjà définie
            
        Returns:
            Dict des poules {poule_id: {equipes: set(), genres: set(), ...}}
        """
        poules = defaultdict(lambda: {
            'equipes': set(),
            'genres': set(),
            'nb_matchs_planifies': 0,
            'nb_matchs_non_planifies': 0
        })
        
        # Regrouper les équipes par poule
        for eq_id, eq_data in equipes_dict.items():
            poule_id = eq_data['poule']
            if poule_id:  # Ne prendre que les équipes avec une poule définie
                poules[poule_id]['equipes'].add(eq_id)
                poules[poule_id]['genres'].add(eq_data['genre'])
        
        # Compter les matchs par poule
        for assignment in self.solution_data.get('assignments', []):
            poule = assignment.get('poule', '')
            if poule:
                poules[poule]['nb_matchs_planifies'] += 1
        
        return dict(poules)
    
    def _detect_pools_from_matches(self, equipes_dict: Dict) -> Dict:
        """
        Détecte les poules en regroupant les équipes qui jouent ensemble.
        
        Utilise un algorithme de clustering : deux équipes sont dans la même poule
        si elles se rencontrent (directement ou indirectement via d'autres équipes).
        
        Args:
            equipes_dict: Dictionnaire des équipes avec leurs adversaires
            
        Returns:
            Dict des poules {poule_id: {equipes: set(), genres: set(), ...}}
        """
        poules = defaultdict(lambda: {
            'equipes': set(),
            'genres': set(),
            'nb_matchs_planifies': 0,
            'nb_matchs_non_planifies': 0
        })
        
        # Union-Find pour regrouper les équipes connectées
        visited = set()
        poule_counter = 1
        
        for eq_id in equipes_dict.keys():
            if eq_id in visited:
                continue
            
            # BFS pour trouver toutes les équipes connectées
            current_pool = set()
            queue = [eq_id]
            visited.add(eq_id)
            current_pool.add(eq_id)
            
            while queue:
                current = queue.pop(0)
                for adversaire in equipes_dict[current]['adversaires']:
                    if adversaire not in visited:
                        visited.add(adversaire)
                        current_pool.add(adversaire)
                        queue.append(adversaire)
            
            # Déterminer le nom de la poule basé sur le genre majoritaire
            genres_in_pool = [equipes_dict[eid]['genre'] for eid in current_pool]
            genre_majoritaire = max(set(genres_in_pool), key=genres_in_pool.count)
            
            # Générer un ID de poule
            pool_size = len(current_pool)
            poule_id = f"{genre_majoritaire}_Pool_{poule_counter}"
            
            # Mettre à jour les équipes avec leur poule
            for eid in current_pool:
                equipes_dict[eid]['poule'] = poule_id
                poules[poule_id]['equipes'].add(eid)
                poules[poule_id]['genres'].add(equipes_dict[eid]['genre'])
            
            poule_counter += 1
        
        # Compter les matchs par poule
        for assignment in self.solution_data.get('assignments', []):
            eq1_poule = equipes_dict[assignment['equipe1_id']]['poule']
            if eq1_poule:
                poules[eq1_poule]['nb_matchs_planifies'] += 1
        
        return dict(poules)
    
    def _find_equipe_in_config(self, equipe_id: str) -> Optional[Equipe]:
        """
        Trouve une équipe dans les données enrichies.
        
        Args:
            equipe_id: ID unique de l'équipe (format: "INSTITUTION (numero)|genre")
            
        Returns:
            Objet Equipe si trouvé, None sinon
        """
        return self.equipes_index.get(equipe_id)
    
    def _parse_equipe_nom(self, nom: str) -> Tuple[str, str]:
        """
        Parse un nom d'équipe pour extraire institution et numéro.
        
        Ex: "LYON 1 (5)" -> ("LYON 1", "5")
        
        Args:
            nom: Nom de l'équipe
            
        Returns:
            Tuple (institution, numero)
        """
        if '(' in nom and ')' in nom:
            parts = nom.split('(')
            institution = parts[0].strip()
            numero = parts[1].rstrip(')').strip()
            return institution, numero
        return nom, "1"
    
    def _extract_niveau_from_poule(self, poule_id: str) -> str:
        """
        Extrait le niveau depuis l'ID de poule.
        
        Args:
            poule_id: ID de la poule
            
        Returns:
            Niveau (ex: "Excellence", "N1", "N2")
        """
        # Logique simplifiée - à adapter selon votre système de nommage
        if 'Excellence' in poule_id or 'EXC' in poule_id:
            return 'Excellence'
        elif 'N1' in poule_id:
            return 'N1'
        elif 'N2' in poule_id:
            return 'N2'
        elif 'N3' in poule_id:
            return 'N3'
        return 'Unknown'
    
    def _enrich_match(self, assignment: Dict, equipes_dict: Dict) -> Dict:
        """
        Enrichit un assignment avec les informations complètes du match.
        
        Args:
            assignment: Assignment depuis la solution source
            equipes_dict: Dictionnaire des équipes par ID
            
        Returns:
            Match enrichi au format v2.0
        """
        eq1_id = assignment['equipe1_id']
        eq2_id = assignment['equipe2_id']
        eq1 = equipes_dict.get(eq1_id, {})
        eq2 = equipes_dict.get(eq2_id, {})
        
        # Déterminer la poule (doit être la même pour les deux équipes)
        poule = eq1.get('poule', '') or eq2.get('poule', '')
        
        # Calculer les pénalités (simplifiées pour l'instant)
        penalties = self._calculate_penalties(assignment, eq1, eq2)
        
        match = {
            'match_id': str(assignment['match_id']),
            'equipe1_id': eq1_id,
            'equipe1_nom': assignment['equipe1_nom'],
            'equipe1_nom_complet': eq1.get('nom_complet', assignment['equipe1_nom']),
            'equipe1_institution': eq1.get('institution', ''),
            'equipe1_genre': assignment['equipe1_genre'],
            'equipe1_horaires_preferes': eq1.get('horaires_preferes', []),
            'equipe2_id': eq2_id,
            'equipe2_nom': assignment['equipe2_nom'],
            'equipe2_nom_complet': eq2.get('nom_complet', assignment['equipe2_nom']),
            'equipe2_institution': eq2.get('institution', ''),
            'equipe2_genre': assignment['equipe2_genre'],
            'equipe2_horaires_preferes': eq2.get('horaires_preferes', []),
            'poule': poule,
            'semaine': assignment['semaine'],
            'horaire': assignment['horaire'],
            'gymnase': assignment['gymnase'],
            'is_fixed': assignment.get('is_fixed', False),
            'is_entente': eq1.get('institution', '') == eq2.get('institution', ''),
            'is_external': False,  # Par défaut
            'score': {
                'equipe1': None,
                'equipe2': None,
                'has_score': False
            },
            'penalties': penalties
        }
        
        return match
    
    def _calculate_penalties(self, assignment: Dict, eq1: Dict, eq2: Dict) -> Dict:
        """
        Calcule les pénalités pour un match (version simplifiée).
        
        Args:
            assignment: Assignment du match
            eq1: Données de l'équipe 1
            eq2: Données de l'équipe 2
            
        Returns:
            Dict des pénalités
        """
        penalties = {
            'total': 0.0,
            'horaire_prefere': 0.0,
            'espacement': 0.0,
            'indisponibilite': 0.0,
            'compaction': 0.0,
            'overlap': 0.0
        }
        
        # Pénalité horaire préféré
        horaire = assignment['horaire']
        horaires_preferes_eq1 = eq1.get('horaires_preferes', [])
        horaires_preferes_eq2 = eq2.get('horaires_preferes', [])
        
        if horaires_preferes_eq1 and horaire not in horaires_preferes_eq1:
            penalties['horaire_prefere'] += 10
        if horaires_preferes_eq2 and horaire not in horaires_preferes_eq2:
            penalties['horaire_prefere'] += 10
        
        # Pénalité indisponibilité
        semaine = assignment['semaine']
        semaines_indispo_eq1 = eq1.get('semaines_indisponibles', {})
        semaines_indispo_eq2 = eq2.get('semaines_indisponibles', {})
        
        if str(semaine) in semaines_indispo_eq1:
            penalties['indisponibilite'] += 100
        if str(semaine) in semaines_indispo_eq2:
            penalties['indisponibilite'] += 100
        
        penalties['total'] = sum(penalties.values())
        
        return penalties
    
    def _build_slots(self) -> Dict[str, List[Dict]]:
        """
        Construit les slots disponibles et occupés.
        
        Returns:
            Dict avec 'available' et 'occupied'
        """
        # Extraire toutes les semaines et horaires
        semaines = set()
        horaires = set()
        gymnases = set()
        
        for assignment in self.solution_data.get('assignments', []):
            semaines.add(assignment['semaine'])
            horaires.add(assignment['horaire'])
            gymnases.add(assignment['gymnase'])
        
        # Créer tous les slots possibles
        all_slots = []
        for semaine in sorted(semaines):
            for horaire in sorted(horaires):
                for gymnase in sorted(gymnases):
                    all_slots.append({
                        'semaine': semaine,
                        'horaire': horaire,
                        'gymnase': gymnase
                    })
        
        # Identifier les slots occupés
        occupied_slots = []
        for assignment in self.solution_data.get('assignments', []):
            occupied_slots.append({
                'semaine': assignment['semaine'],
                'horaire': assignment['horaire'],
                'gymnase': assignment['gymnase'],
                'match_id': str(assignment['match_id'])
            })
        
        # Slots disponibles = tous - occupés
        occupied_keys = {
            (s['semaine'], s['horaire'], s['gymnase'])
            for s in occupied_slots
        }
        
        available_slots = [
            s for s in all_slots
            if (s['semaine'], s['horaire'], s['gymnase']) not in occupied_keys
        ]
        
        return {
            'available': available_slots,
            'occupied': occupied_slots
        }
    
    def _calculate_statistics(self, entities: Dict, matches_scheduled: List[Dict]) -> Dict:
        """
        Calcule les statistiques globales.
        
        Args:
            entities: Entités (équipes, gymnases, poules)
            matches_scheduled: Liste des matchs planifiés
            
        Returns:
            Dict des statistiques
        """
        # Compter par semaine
        matchs_par_semaine = defaultdict(int)
        for match in matches_scheduled:
            matchs_par_semaine[match['semaine']] += 1
        
        # Compter par gymnase
        matchs_par_gymnase = defaultdict(int)
        for match in matches_scheduled:
            matchs_par_gymnase[match['gymnase']] += 1
        
        # Compter par genre
        matchs_par_genre = defaultdict(int)
        for match in matches_scheduled:
            matchs_par_genre[match['equipe1_genre']] += 1
        
        # Pénalités totales
        total_penalties = sum(m['penalties']['total'] for m in matches_scheduled)
        
        return {
            'nb_matchs_planifies': len(matches_scheduled),
            'nb_matchs_non_planifies': 0,  # À calculer si on a l'info
            'nb_equipes': len(entities['equipes']),
            'nb_gymnases': len(entities['gymnases']),
            'nb_poules': len(entities['poules']),
            'nb_semaines': len(matchs_par_semaine),
            'penalties_total': total_penalties,
            'penalties_moyenne': total_penalties / len(matches_scheduled) if matches_scheduled else 0,
            'matchs_par_semaine': dict(matchs_par_semaine),
            'matchs_par_gymnase': dict(matchs_par_gymnase),
            'matchs_par_genre': dict(matchs_par_genre)
        }
    
    def convert(self) -> Dict:
        """
        Convertit la solution au format v2.0.
        
        Returns:
            Solution au format v2.0
        """
        print(f"🔄 Conversion de {self.solution_path.name} vers format v2.0...")
        
        # 1. Extraire les entités
        print("  📦 Extraction des entités...")
        entities = self._extract_entities()
        equipes_dict = {eq['id']: eq for eq in entities['equipes']}
        
        # 2. Enrichir les matchs
        print("  ⚙️  Enrichissement des matchs...")
        matches_scheduled = []
        for assignment in self.solution_data.get('assignments', []):
            enriched_match = self._enrich_match(assignment, equipes_dict)
            matches_scheduled.append(enriched_match)
        
        # 3. Construire les slots
        print("  🎰 Construction des slots...")
        slots = self._build_slots()
        
        # 4. Calculer les statistiques
        print("  📊 Calcul des statistiques...")
        statistics = self._calculate_statistics(entities, matches_scheduled)
        
        # 5. Assembler la solution v2.0
        # Convertir Infinity en None pour compatibilité JSON
        raw_score = self.solution_data['metadata']['score']
        score = None if (isinstance(raw_score, float) and (raw_score == float('inf') or raw_score == float('-inf') or raw_score != raw_score)) else raw_score
        
        solution_v2 = {
            'version': '2.0',
            'generated_at': datetime.now().isoformat(),
            'metadata': {
                'solution_name': self.solution_data['metadata']['solution_name'],
                'solver': self.solution_data['metadata'].get('solver', 'cpsat'),
                'status': self.solution_data['metadata'].get('status', 'FEASIBLE'),
                'score': score,
                'execution_time_seconds': 0  # Non disponible dans l'ancien format
            },
            'config': {
                'hash': self.solution_data['config_signature']['yaml_hash'],
                'nb_semaines': self.solution_data['config_signature']['nb_semaines'],
                'semaine_min': 1,  # Valeur par défaut
                'strategie': 'greedy',  # Valeur par défaut
                'temps_max_secondes': 0,
                'constraints': {}
            },
            'entities': entities,
            'matches': {
                'scheduled': matches_scheduled,
                'unscheduled': []  # Non disponible dans l'ancien format
            },
            'slots': slots,
            'statistics': statistics
        }
        
        print(f"  ✅ Conversion terminée:")
        print(f"     - {len(entities['equipes'])} équipes")
        print(f"     - {len(entities['gymnases'])} gymnases")
        print(f"     - {len(entities['poules'])} poules")
        print(f"     - {len(matches_scheduled)} matchs planifiés")
        print(f"     - {len(slots['available'])} slots disponibles")
        
        return solution_v2
    
    def save(self, output_path: Optional[Path] = None):
        """
        Convertit et sauvegarde la solution v2.0.
        
        Args:
            output_path: Chemin de sortie (défaut: même nom + _v2.json)
        """
        solution_v2 = self.convert()
        
        if output_path is None:
            output_path = self.solution_path.parent / f"{self.solution_path.stem}_v2.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(solution_v2, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Solution v2.0 sauvegardée: {output_path}")
        print(f"   Taille: {output_path.stat().st_size / 1024:.1f} KB")


def main():
    """Point d'entrée du script."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Convertit une solution PyCalendar vers le format v2.0',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  # Convertir latest_volley.json
  python scripts/convert_solution_to_v2.py solutions/latest_volley.json
  
  # Spécifier fichier de sortie
  python scripts/convert_solution_to_v2.py solutions/latest_volley.json -o output_v2.json
  
  # Avec enrichissement depuis la config
  python scripts/convert_solution_to_v2.py solutions/latest_volley.json -c examples/volleyball/config_volley.xlsx
        """
    )
    
    parser.add_argument('input', type=Path, help='Fichier JSON de solution à convertir')
    parser.add_argument('-o', '--output', type=Path, help='Fichier JSON de sortie (optionnel)')
    parser.add_argument('-c', '--config', type=Path, help='Fichier de config Excel pour enrichissement (optionnel)')
    
    args = parser.parse_args()
    
    # Vérifier que le fichier d'entrée existe
    if not args.input.exists():
        print(f"❌ Erreur: fichier introuvable: {args.input}")
        sys.exit(1)
    
    # Créer le config_manager si config fournie
    config_manager: Optional[ConfigManager] = None
    if args.config and args.config.exists():
        print(f"📖 Chargement de la config: {args.config}")
        # Note: ConfigManager nécessite adaptation pour cette fonctionnalité
        # config_manager = ConfigManager(str(args.config))
    
    # Convertir
    converter = SolutionConverterV2(args.input, config_manager)
    converter.save(args.output)
    
    print("\n✅ Conversion terminée avec succès!")


if __name__ == '__main__':
    main()
