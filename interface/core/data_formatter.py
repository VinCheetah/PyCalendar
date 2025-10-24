"""
Data Formatter - Transforms Python Solution objects into enriched JSON format.

This module converts internal PyCalendar models into a structured JSON format
optimized for the web interface, with pre-calculated statistics and enriched data.
"""

from typing import Dict, List, Any, Optional, Set
from datetime import datetime
from collections import defaultdict
import hashlib
import json

from core.models import Solution, Match, Equipe, Creneau, Gymnase
from core.config import Config


class DataFormatter:
    """Formats Solution data into enriched JSON structure for web interface."""
    
    VERSION = "2.0"
    
    @staticmethod
    def format_solution(
        solution: Solution,
        config: Optional[Config] = None,
        equipes: Optional[List[Equipe]] = None,
        gymnases: Optional[List[Gymnase]] = None,
        creneaux_disponibles: Optional[List[Creneau]] = None
    ) -> Dict[str, Any]:
        """
        Transform Solution into enriched JSON format.
        
        Args:
            solution: The scheduling solution to format
            config: Configuration object (optional)
            equipes: List of all teams (optional, extracted from matches if not provided)
            gymnases: List of all venues (optional)
            creneaux_disponibles: List of available slots (optional)
            
        Returns:
            Dictionary with complete formatted data
        """
        # Extract entities from matches if not provided
        if equipes is None:
            equipes = DataFormatter._extract_equipes_from_matches(solution)
        if gymnases is None:
            gymnases = DataFormatter._extract_gymnases_from_matches(solution)
        
        # Build JSON structure
        data = {
            "version": DataFormatter.VERSION,
            "generated_at": datetime.now().isoformat(),
            
            "metadata": DataFormatter._format_metadata(solution, config),
            "config": DataFormatter._format_config(config),
            "entities": DataFormatter._format_entities(equipes, gymnases, solution),
            "matches": DataFormatter._format_matches(solution, config),
            "slots": DataFormatter._format_slots(creneaux_disponibles, solution),
            "statistics": DataFormatter._calculate_statistics(solution, equipes, gymnases),
        }
        
        return data
    
    @staticmethod
    def _format_metadata(solution: Solution, config: Optional[Config]) -> Dict[str, Any]:
        """Format solution metadata."""
        metadata = solution.metadata.copy() if solution.metadata else {}
        
        return {
            "solution_name": metadata.get("solution_name", "unknown"),
            "solver": metadata.get("solver", "unknown"),
            "status": metadata.get("status", "UNKNOWN"),
            "score": float(solution.score),
            "execution_time_seconds": metadata.get("execution_time", 0.0),
            "date": metadata.get("date", datetime.now().isoformat()),
        }
    
    @staticmethod
    def _format_config(config: Optional[Config]) -> Dict[str, Any]:
        """Format configuration data."""
        if config is None:
            return {}
        
        # Calculate hash of config for change detection
        config_str = json.dumps({
            "nb_semaines": config.nb_semaines,
            "strategie": config.strategie,
            "poids_indisponibilite": config.poids_indisponibilite,
        }, sort_keys=True)
        config_hash = hashlib.md5(config_str.encode()).hexdigest()
        
        return {
            "hash": config_hash,
            "nb_semaines": config.nb_semaines,
            "semaine_min": config.semaine_min,
            "strategie": config.strategie,
            "temps_max_secondes": config.temps_max_secondes,
            "constraints": {
                "poids_indisponibilite": config.poids_indisponibilite,
                "poids_capacite_gymnase": config.poids_capacite_gymnase,
                "poids_equilibrage_charge": config.poids_equilibrage_charge,
                "penalites_espacement_repos": config.penalites_espacement_repos,
                "penalite_apres_horaire_min": config.penalite_apres_horaire_min,
                "penalite_avant_horaire_min": config.penalite_avant_horaire_min,
                "penalite_avant_horaire_min_deux": config.penalite_avant_horaire_min_deux,
                "penalite_horaire_diviseur": config.penalite_horaire_diviseur,
                "penalite_horaire_tolerance": config.penalite_horaire_tolerance,
            }
        }
    
    @staticmethod
    def _format_entities(
        equipes: List[Equipe],
        gymnases: List[Gymnase],
        solution: Solution
    ) -> Dict[str, Any]:
        """Format all entities (teams, venues, pools)."""
        
        # Format teams
        equipes_data = []
        for equipe in equipes:
            equipes_data.append({
                "id": equipe.id_unique,
                "nom": equipe.nom,
                "nom_complet": equipe.nom_complet,
                "institution": equipe.institution,
                "numero_equipe": equipe.numero_equipe,
                "genre": equipe.genre,
                "poule": equipe.poule,
                "horaires_preferes": equipe.horaires_preferes,
                "lieux_preferes": [lieu for lieu in equipe.lieux_preferes if lieu is not None],
                "semaines_indisponibles": {
                    str(sem): list(horaires) 
                    for sem, horaires in equipe.semaines_indisponibles.items()
                },
            })
        
        # Format venues
        gymnases_data = []
        for gymnase in gymnases:
            gymnases_data.append({
                "id": gymnase.nom,
                "nom": gymnase.nom,
                "capacite": gymnase.capacite,
                "horaires_disponibles": gymnase.horaires_disponibles,
                "semaines_indisponibles": {
                    str(sem): list(horaires)
                    for sem, horaires in gymnase.semaines_indisponibles.items()
                },
                "capacite_reduite": {
                    str(sem): {horaire: cap for horaire, cap in horaires_cap.items()}
                    for sem, horaires_cap in gymnase.capacite_reduite.items()
                },
            })
        
        # Extract pools from matches
        poules_data = DataFormatter._extract_pools_data(solution, equipes)
        
        return {
            "equipes": equipes_data,
            "gymnases": gymnases_data,
            "poules": poules_data,
        }
    
    @staticmethod
    def _extract_pools_data(solution: Solution, equipes: List[Equipe]) -> List[Dict[str, Any]]:
        """Extract pool data from matches and teams."""
        pools: Dict[str, Dict[str, Any]] = {}
        
        # Collect pools from teams
        for equipe in equipes:
            if equipe.poule not in pools:
                # Determine genre and niveau from pool name
                genre = equipe.genre
                # Extract niveau from pool name (e.g., "A1 F" -> "A1")
                niveau = equipe.poule.replace(" F", "").replace(" M", "").strip()
                
                pools[equipe.poule] = {
                    "id": equipe.poule,
                    "nom": equipe.poule,
                    "genre": genre,
                    "niveau": niveau,
                    "equipes_ids": [],
                }
            
            if equipe.id_unique not in pools[equipe.poule]["equipes_ids"]:
                pools[equipe.poule]["equipes_ids"].append(equipe.id_unique)
        
        # Add match count per pool
        for poule_id in pools:
            scheduled_count = sum(1 for m in solution.matchs_planifies if m.poule == poule_id)
            unscheduled_count = sum(1 for m in solution.matchs_non_planifies if m.poule == poule_id)
            
            pools[poule_id]["nb_equipes"] = len(pools[poule_id]["equipes_ids"])
            pools[poule_id]["nb_matchs_planifies"] = scheduled_count
            pools[poule_id]["nb_matchs_non_planifies"] = unscheduled_count
        
        return list(pools.values())
    
    @staticmethod
    def _format_matches(solution: Solution, config: Optional[Config]) -> Dict[str, List[Dict]]:
        """Format all matches (scheduled and unscheduled)."""
        
        scheduled = []
        for idx, match in enumerate(solution.matchs_planifies):
            match_data = DataFormatter._format_single_match(match, idx, True, config)
            scheduled.append(match_data)
        
        unscheduled = []
        for idx, match in enumerate(solution.matchs_non_planifies):
            match_data = DataFormatter._format_single_match(
                match, 
                len(solution.matchs_planifies) + idx, 
                False, 
                config
            )
            unscheduled.append(match_data)
        
        return {
            "scheduled": scheduled,
            "unscheduled": unscheduled,
        }
    
    @staticmethod
    def _format_single_match(
        match: Match, 
        index: int, 
        is_scheduled: bool,
        config: Optional[Config]
    ) -> Dict[str, Any]:
        """Format a single match."""
        
        match_data = {
            "match_id": f"M_{index:04d}",
            "equipe1_id": match.equipe1.id_unique,
            "equipe1_nom": match.equipe1.nom,
            "equipe1_nom_complet": match.equipe1.nom_complet,
            "equipe1_institution": match.equipe1.institution,
            "equipe1_genre": match.equipe1.genre,
            "equipe1_horaires_preferes": match.equipe1.horaires_preferes,
            "equipe2_id": match.equipe2.id_unique,
            "equipe2_nom": match.equipe2.nom,
            "equipe2_nom_complet": match.equipe2.nom_complet,
            "equipe2_institution": match.equipe2.institution,
            "equipe2_genre": match.equipe2.genre,
            "equipe2_horaires_preferes": match.equipe2.horaires_preferes,
            "poule": match.poule,
            "priorite": match.priorite,
        }
        
        if is_scheduled and match.creneau:
            match_data.update({
                "semaine": match.creneau.semaine,
                "horaire": match.creneau.horaire,
                "gymnase": match.creneau.gymnase,
                "is_fixed": match.metadata.get("is_fixed", False),
                "is_entente": match.metadata.get("is_entente", False),
                "is_external": match.metadata.get("is_external", False),
            })
            
            # Add score if available
            score_data = match.metadata.get("score", {})
            match_data["score"] = {
                "equipe1": score_data.get("equipe1"),
                "equipe2": score_data.get("equipe2"),
                "has_score": score_data.get("equipe1") is not None,
            }
            
            # Calculate penalties if config available
            if config:
                penalties = DataFormatter._calculate_match_penalties(match, config)
                match_data["penalties"] = penalties
        else:
            # Unscheduled match
            match_data["reason"] = match.metadata.get("unscheduled_reason", "Aucun créneau disponible")
            match_data["constraints_violated"] = match.metadata.get("constraints_violated", [])
        
        return match_data
    
    @staticmethod
    def _calculate_match_penalties(match: Match, config: Config) -> Dict[str, float]:
        """Calculate penalties for a scheduled match."""
        # TODO: Implement actual penalty calculation based on constraints
        # For now, return placeholder values
        return {
            "total": 0.0,
            "horaire_prefere": 0.0,
            "espacement": 0.0,
            "indisponibilite": 0.0,
            "compaction": 0.0,
            "overlap": 0.0,
        }
    
    @staticmethod
    def _format_slots(
        creneaux_disponibles: Optional[List[Creneau]],
        solution: Solution
    ) -> Dict[str, List[Dict]]:
        """Format slot data (available and occupied)."""
        
        if creneaux_disponibles is None:
            return {"available": [], "occupied": []}
        
        # Build set of occupied slots
        occupied_slots: Dict[str, str] = {}  # slot_id -> match_id
        for idx, match in enumerate(solution.matchs_planifies):
            if match.creneau:
                slot_id = f"S_{match.creneau.gymnase}_{match.creneau.semaine}_{match.creneau.horaire}"
                occupied_slots[slot_id] = f"M_{idx:04d}"
        
        available = []
        occupied = []
        
        for creneau in creneaux_disponibles:
            slot_id = f"S_{creneau.gymnase}_{creneau.semaine}_{creneau.horaire}"
            
            slot_data = {
                "slot_id": slot_id,
                "gymnase": creneau.gymnase,
                "semaine": creneau.semaine,
                "horaire": creneau.horaire,
            }
            
            if slot_id in occupied_slots:
                slot_data["status"] = "occupé"
                slot_data["match_id"] = occupied_slots[slot_id]
                occupied.append(slot_data)
            else:
                slot_data["status"] = "libre"
                available.append(slot_data)
        
        return {
            "available": available,
            "occupied": occupied,
        }
    
    @staticmethod
    def _calculate_statistics(
        solution: Solution,
        equipes: List[Equipe],
        gymnases: List[Gymnase]
    ) -> Dict[str, Any]:
        """Calculate comprehensive statistics."""
        
        total_matchs = len(solution.matchs_planifies) + len(solution.matchs_non_planifies)
        
        # Global statistics
        nb_matchs_fixes = sum(1 for m in solution.matchs_planifies if m.metadata.get("is_fixed", False))
        nb_matchs_auto = len(solution.matchs_planifies) - nb_matchs_fixes
        
        global_stats = {
            "taux_planification": solution.taux_planification(),
            "score_total": float(solution.score),
            "score_moyen_par_match": float(solution.score / total_matchs) if total_matchs > 0 else 0.0,
            "nb_matchs_total": total_matchs,
            "nb_matchs_planifies": len(solution.matchs_planifies),
            "nb_matchs_non_planifies": len(solution.matchs_non_planifies),
            "nb_matchs_fixes": nb_matchs_fixes,
            "nb_matchs_auto": nb_matchs_auto,
        }
        
        # Statistics per week
        par_semaine = DataFormatter._stats_par_semaine(solution)
        
        # Statistics per pool
        par_poule = DataFormatter._stats_par_poule(solution)
        
        # Statistics per venue
        par_gymnase = DataFormatter._stats_par_gymnase(solution, gymnases)
        
        # Statistics per team
        par_equipe = DataFormatter._stats_par_equipe(solution, equipes)
        
        return {
            "global": global_stats,
            "par_semaine": par_semaine,
            "par_poule": par_poule,
            "par_gymnase": par_gymnase,
            "par_equipe": par_equipe,
        }
    
    @staticmethod
    def _stats_par_semaine(solution: Solution) -> Dict[str, Dict[str, Any]]:
        """Calculate statistics per week."""
        matchs_par_semaine = solution.get_matchs_par_semaine()
        
        stats = {}
        for semaine, matchs in matchs_par_semaine.items():
            # Count matches by time slot
            par_horaire = defaultdict(int)
            for match in matchs:
                if match.creneau:
                    par_horaire[match.creneau.horaire] += 1
            
            stats[str(semaine)] = {
                "nb_matchs": len(matchs),
                "par_horaire": dict(par_horaire),
            }
        
        return stats
    
    @staticmethod
    def _stats_par_poule(solution: Solution) -> Dict[str, Dict[str, Any]]:
        """Calculate statistics per pool."""
        stats = defaultdict(lambda: {"nb_matchs_planifies": 0, "nb_matchs_non_planifies": 0})
        
        for match in solution.matchs_planifies:
            stats[match.poule]["nb_matchs_planifies"] += 1
        
        for match in solution.matchs_non_planifies:
            stats[match.poule]["nb_matchs_non_planifies"] += 1
        
        # Calculate completion rate
        for poule in stats:
            total = stats[poule]["nb_matchs_planifies"] + stats[poule]["nb_matchs_non_planifies"]
            stats[poule]["taux_completion"] = (stats[poule]["nb_matchs_planifies"] / total * 100) if total > 0 else 0.0
        
        return dict(stats)
    
    @staticmethod
    def _stats_par_gymnase(solution: Solution, gymnases: List[Gymnase]) -> Dict[str, Dict[str, Any]]:
        """Calculate statistics per venue."""
        stats = defaultdict(lambda: {"nb_matchs": 0, "capacite": 1})
        
        # Initialize with venue data
        for gymnase in gymnases:
            stats[gymnase.nom]["capacite"] = gymnase.capacite
        
        # Count matches
        for match in solution.matchs_planifies:
            if match.creneau:
                stats[match.creneau.gymnase]["nb_matchs"] += 1
        
        # Calculate occupation rate (simplified - would need total available slots)
        for gymnase_nom in stats:
            # This is a placeholder - actual calculation needs total available slots
            stats[gymnase_nom]["taux_occupation"] = 0.0
        
        return dict(stats)
    
    @staticmethod
    def _stats_par_equipe(solution: Solution, equipes: List[Equipe]) -> Dict[str, Dict[str, Any]]:
        """Calculate statistics per team."""
        stats = defaultdict(lambda: {
            "nb_matchs_planifies": 0,
            "nb_matchs_non_planifies": 0,
            "horaires_repartition": defaultdict(int),
        })
        
        # Count scheduled matches
        for match in solution.matchs_planifies:
            for equipe in [match.equipe1, match.equipe2]:
                equipe_id = equipe.id_unique
                stats[equipe_id]["nb_matchs_planifies"] += 1
                if match.creneau:
                    stats[equipe_id]["horaires_repartition"][match.creneau.horaire] += 1
        
        # Count unscheduled matches
        for match in solution.matchs_non_planifies:
            for equipe in [match.equipe1, match.equipe2]:
                equipe_id = equipe.id_unique
                stats[equipe_id]["nb_matchs_non_planifies"] += 1
        
        # Convert defaultdict to dict
        result = {}
        for equipe_id, data in stats.items():
            result[equipe_id] = {
                "nb_matchs_planifies": data["nb_matchs_planifies"],
                "nb_matchs_non_planifies": data["nb_matchs_non_planifies"],
                "horaires_repartition": dict(data["horaires_repartition"]),
            }
        
        return result
    
    @staticmethod
    def _extract_equipes_from_matches(solution: Solution) -> List[Equipe]:
        """Extract unique teams from matches."""
        equipes_dict: Dict[str, Equipe] = {}
        
        for match in solution.matchs_planifies + solution.matchs_non_planifies:
            for equipe in [match.equipe1, match.equipe2]:
                if equipe.id_unique not in equipes_dict:
                    equipes_dict[equipe.id_unique] = equipe
        
        return list(equipes_dict.values())
    
    @staticmethod
    def _extract_gymnases_from_matches(solution: Solution) -> List[Gymnase]:
        """Extract unique venues from matches."""
        gymnases_set: Set[str] = set()
        
        for match in solution.matchs_planifies:
            if match.creneau:
                gymnases_set.add(match.creneau.gymnase)
        
        # Create Gymnase objects with minimal data
        return [Gymnase(nom=nom) for nom in sorted(gymnases_set)]
