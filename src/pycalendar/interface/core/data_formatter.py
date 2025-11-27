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

from pycalendar.core.models import Solution, Match, Equipe, Creneau, Gymnase
from pycalendar.core.config import Config
from pycalendar.core.utils import determiner_genre_match
from pycalendar.core.penalty_calculator import PenaltyCalculator


class DataFormatter:
    """Formats Solution data into enriched JSON structure for web interface."""
    
    VERSION = "2.0"
    
    @staticmethod
    def format_solution(
        solution: Solution,
        config: Optional[Config] = None,
        equipes: Optional[List[Equipe]] = None,
        gymnases: Optional[List[Gymnase]] = None,
        creneaux_disponibles: Optional[List[Creneau]] = None,
        types_poules: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Transform Solution into enriched JSON format.
        
        Args:
            solution: The scheduling solution to format
            config: Configuration object (optional)
            equipes: List of all teams (optional, extracted from matches if not provided)
            gymnases: List of all venues (optional)
            creneaux_disponibles: List of available slots (optional)
            types_poules: Dictionary {poule_name: type} where type is 'Classique' or 'Aller-Retour' (optional)
            
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
            "entities": DataFormatter._format_entities(equipes, gymnases, solution, types_poules),
            "matches": DataFormatter._format_matches(solution, config),
            "slots": DataFormatter._format_slots(creneaux_disponibles, solution, gymnases, config),
            "statistics": DataFormatter._calculate_statistics(solution, equipes, gymnases),
        }
        
        return data
    
    @staticmethod
    def _format_metadata(solution: Solution, config: Optional[Config]) -> Dict[str, Any]:
        """Format solution metadata."""
        metadata = solution.metadata.copy() if solution.metadata else {}
        
        result = {
            "solution_name": metadata.get("solution_name", "unknown"),
            "solver": metadata.get("solver", "unknown"),
            "status": metadata.get("status", "UNKNOWN"),
            "score": float(solution.score),
            "execution_time_seconds": metadata.get("execution_time", 0.0),
            "date": metadata.get("date", datetime.now().isoformat()),
        }
        
        # Ajouter la décomposition des pénalités si disponible
        if "penalty_breakdown" in metadata:
            result["penalty_breakdown"] = metadata["penalty_breakdown"]
        
        return result
    
    @staticmethod
    def _format_config(config: Optional[Config]) -> Dict[str, Any]:
        """Format configuration data."""
        if config is None:
            return {}
        
        # Calculate hash of config for change detection
        config_str = json.dumps({
            "nb_semaines": config.nb_semaines,
        }, sort_keys=True)
        config_hash = hashlib.md5(config_str.encode()).hexdigest()
        
        return {
            "hash": config_hash,
            "nb_semaines": config.nb_semaines,
            "semaine_min": config.semaine_min,
            "temps_max_secondes": config.temps_max_secondes,
            "duree_match_minutes": config.duree_match_minutes,
            "constraints": {
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
        solution: Solution,
        types_poules: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Format all entities (teams, venues, pools)."""
        
        # Format teams with complete data
        equipes_data = []
        for equipe in equipes:
            # Normalize genre to uppercase (M/F) or empty string
            genre = equipe.genre.upper() if equipe.genre else ""
            if genre not in ["M", "F", ""]:
                genre = ""  # Invalid genre -> empty
            
            equipes_data.append({
                "id": equipe.id_unique,
                "nom": equipe.nom,
                "nom_complet": equipe.nom_complet,
                "institution": equipe.institution,
                "numero_equipe": equipe.numero_equipe,
                "genre": genre,
                "poule": equipe.poule,
                "horaires_preferes": equipe.horaires_preferes if equipe.horaires_preferes else [],
                "lieux_preferes": [str(lieu) for lieu in equipe.lieux_preferes if lieu is not None],
                "semaines_indisponibles": {
                    str(sem): sorted(list(horaires)) 
                    for sem, horaires in equipe.semaines_indisponibles.items()
                },
            })
        
        # Format venues with complete data
        gymnases_data = []
        for gymnase in gymnases:
            gymnases_data.append({
                "id": gymnase.nom,
                "nom": gymnase.nom,
                "capacite": gymnase.capacite,
                "horaires_disponibles": gymnase.horaires_disponibles if gymnase.horaires_disponibles else [],
                "semaines_indisponibles": {
                    str(sem): sorted(list(horaires))
                    for sem, horaires in gymnase.semaines_indisponibles.items()
                },
                "capacite_reduite": {
                    str(sem): {horaire: cap for horaire, cap in horaires_cap.items()}
                    for sem, horaires_cap in gymnase.capacite_reduite.items()
                },
            })
        
        # Extract pools from matches
        poules_data = DataFormatter._extract_pools_data(solution, equipes, types_poules)
        
        return {
            "equipes": equipes_data,
            "gymnases": gymnases_data,
            "poules": poules_data,
        }
    
    @staticmethod
    def _extract_pools_data(solution: Solution, equipes: List[Equipe], types_poules: Optional[Dict[str, str]] = None) -> List[Dict]:
        """Extract pool data from matches and teams."""
        pools: Dict[str, Dict[str, Any]] = {}
        
        # Collect pools from teams
        for equipe in equipes:
            if equipe.poule not in pools:
                # Normalize genre to uppercase (M/F) or empty string
                genre = equipe.genre.upper() if equipe.genre else ""
                if genre not in ["M", "F", ""]:
                    genre = ""  # Invalid genre -> empty
                
                # Extract niveau from pool name (e.g., "VBFA1PA" -> "A1", "VBMA2PB" -> "A2")
                import re
                niveau_match = re.search(r'A([1-4])', equipe.poule)
                if niveau_match:
                    niveau = f"A{niveau_match.group(1)}"
                else:
                    # Chercher CFE ou CFU
                    cfe_match = re.search(r'CF[EU]', equipe.poule)
                    niveau = cfe_match.group(0) if cfe_match else equipe.poule
                
                pools[equipe.poule] = {
                    "id": equipe.poule,
                    "nom": equipe.poule,
                    "genre": genre,
                    "niveau": niveau,
                    "equipes_ids": [],
                    "type": types_poules.get(equipe.poule, "Classique") if types_poules else "Classique",
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
        
        # Pre-calculate context for global penalties (espacement, compaction, overlap)
        if config:
            DataFormatter._precalculate_penalty_context(solution, config)
        
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
    def _precalculate_penalty_context(solution: Solution, config: Config):
        """
        Pre-calculate context needed for global penalties (espacement, overlap).
        Stores results in match.metadata for later access.
        
        Note: Compaction penalties are pool-level and not stored per-match.
        """
        # Store all matches for PenaltyCalculator
        all_matches = solution.matchs_planifies
        
        # Build index of matches by team
        matches_by_team: Dict[str, List[Match]] = {}
        for match in solution.matchs_planifies:
            if not match.creneau:
                continue
            
            team1_id = match.equipe1.id_unique
            team2_id = match.equipe2.id_unique
            
            if team1_id not in matches_by_team:
                matches_by_team[team1_id] = []
            if team2_id not in matches_by_team:
                matches_by_team[team2_id] = []
            
            matches_by_team[team1_id].append(match)
            matches_by_team[team2_id].append(match)
        
        # Sort matches by week for each team (for espacement calculation)
        for team_id in matches_by_team:
            matches_by_team[team_id].sort(key=lambda m: m.creneau.semaine if m.creneau else 999)
        
        # Build index of matches by slot (for overlap calculation)
        matches_by_slot: Dict[tuple, List[Match]] = {}  # (semaine, horaire) -> [matches]
        for match in solution.matchs_planifies:
            if not match.creneau:
                continue
            
            slot_key = (match.creneau.semaine, match.creneau.horaire)
            if slot_key not in matches_by_slot:
                matches_by_slot[slot_key] = []
            matches_by_slot[slot_key].append(match)
        
        # Store context in match metadata
        for match in solution.matchs_planifies:
            if not match.creneau:
                continue
            
            if not match.metadata:
                match.metadata = {}
            
            # Store team matches for espacement calculation
            team1_matches = matches_by_team.get(match.equipe1.id_unique, [])
            team2_matches = matches_by_team.get(match.equipe2.id_unique, [])
            
            match.metadata["_penalty_context"] = {
                "all_matches": all_matches,  # Required for PenaltyCalculator
                "team1_matches": team1_matches,
                "team2_matches": team2_matches,
                "slot_matches": matches_by_slot.get(
                    (match.creneau.semaine, match.creneau.horaire), 
                    []
                ),
            }
    
    @staticmethod
    def _format_single_match(
        match: Match, 
        index: int, 
        is_scheduled: bool,
        config: Optional[Config]
    ) -> Dict[str, Any]:
        """Format a single match."""
        
        # Vérifier si le match a un genre fixé explicitement (pour les matchs fixes)
        genre_fixe = match.metadata.get('genre_fixe') if match.metadata else None
        
        # Normalize genres to uppercase
        equipe1_genre = match.equipe1.genre.upper() if match.equipe1.genre else ""
        if equipe1_genre not in ["M", "F", ""]:
            equipe1_genre = ""
        
        equipe2_genre = match.equipe2.genre.upper() if match.equipe2.genre else ""
        if equipe2_genre not in ["M", "F", ""]:
            equipe2_genre = ""
        
        # Déterminer le genre du match
        # Priorité 1: genre_fixe (pour les matchs fixes avec genre explicite)
        # Priorité 2: détermination normale basée sur les équipes et la poule
        if genre_fixe and genre_fixe in ['M', 'F']:
            match_genre = genre_fixe
        else:
            match_genre = determiner_genre_match(equipe1_genre, equipe2_genre, match.poule)
        
        match_data = {
            "match_id": f"M_{index:04d}",
            "equipe1_id": match.equipe1.id_unique,
            "equipe1_nom": match.equipe1.nom,
            "equipe1_nom_complet": match.equipe1.nom_complet,
            "equipe1_institution": match.equipe1.institution,
            "equipe1_genre": equipe1_genre,
            "equipe1_horaires_preferes": match.equipe1.horaires_preferes if match.equipe1.horaires_preferes else [],
            "equipe2_id": match.equipe2.id_unique,
            "equipe2_nom": match.equipe2.nom,
            "equipe2_nom_complet": match.equipe2.nom_complet,
            "equipe2_institution": match.equipe2.institution,
            "equipe2_genre": equipe2_genre,
            "equipe2_horaires_preferes": match.equipe2.horaires_preferes if match.equipe2.horaires_preferes else [],
            "poule": match.poule,
            "priorite": match.priorite,  # Added priority field
            "genre": match_genre,  # Genre du match (M, F, ou X)
            "championship_type": match.championship_type,  # Type de championnat (Acad, CFU, CFE, Autre)
        }
        
        if is_scheduled and match.creneau:
            # IMPORTANT: Un match n'est "entente" QUE s'il n'a PAS de créneau
            # Si le match a un créneau (gymnase + horaire), ce n'est JAMAIS une entente
            # même si les institutions sont dans la liste des ententes
            match_data.update({
                "semaine": match.creneau.semaine,
                "horaire": match.creneau.horaire,
                "gymnase": match.creneau.gymnase,
                "is_fixed": match.metadata.get("is_fixed", False),
                "is_entente": False,  # Match avec créneau = PAS une entente
                "is_external": match.metadata.get("is_external", False),
            })
            
            # Add score if available
            score_data = match.metadata.get("score")
            if isinstance(score_data, dict):
                # Score déjà au format dictionnaire
                match_data["score"] = {
                    "equipe1": score_data.get("equipe1"),
                    "equipe2": score_data.get("equipe2"),
                    "has_score": score_data.get("equipe1") is not None,
                }
            elif isinstance(score_data, str) and score_data.strip():
                # Score au format string (ex: "3-1", "21-19")
                # Parser le score
                parts = score_data.strip().split('-')
                if len(parts) == 2:
                    try:
                        equipe1_score = int(parts[0].strip())
                        equipe2_score = int(parts[1].strip())
                        match_data["score"] = {
                            "equipe1": equipe1_score,
                            "equipe2": equipe2_score,
                            "has_score": True,
                        }
                    except ValueError:
                        # Format invalide, traiter comme pas de score
                        match_data["score"] = {
                            "equipe1": None,
                            "equipe2": None,
                            "has_score": False,
                        }
                else:
                    # Format invalide
                    match_data["score"] = {
                        "equipe1": None,
                        "equipe2": None,
                        "has_score": False,
                    }
            else:
                # Pas de score disponible
                match_data["score"] = {
                    "equipe1": None,
                    "equipe2": None,
                    "has_score": False,
                }
            
            # Calculate penalties if config available
            if config:
                penalties = DataFormatter._calculate_match_penalties(match, config)
                match_data["penalties"] = penalties
            else:
                # Return structure with zeros if no config
                match_data["penalties"] = {
                    "total": 0.0,
                    "horaire_prefere": 0.0,
                    "espacement": 0.0,
                    "indisponibilite": 0.0,
                    "compaction": 0.0,
                    "overlap": 0.0,
                }
        else:
            # Unscheduled match
            # IMPORTANT: Un match "entente" = match sans créneau entre institutions en entente
            # Ces matchs doivent être considérés comme "planifiés" (joués en dehors du calendrier)
            is_entente = match.metadata.get("is_entente", False)
            
            match_data["reason"] = match.metadata.get("unscheduled_reason", "Match en entente" if is_entente else "Aucun créneau disponible")
            match_data["constraints_violated"] = match.metadata.get("constraints_violated", [])
            match_data["is_entente"] = is_entente
        
        return match_data
    
    @staticmethod
    def _calculate_match_penalties(match: Match, config: Config) -> Dict[str, float]:
        """
        Calculate penalties for a scheduled match using PenaltyCalculator.
        
        This ensures consistency between the solver and the interface by using
        the same penalty calculation logic.
        
        Args:
            match: The match to calculate penalties for
            config: Configuration with penalty weights
            
        Returns:
            Dictionary with all 9 penalty types and total
        """
        # Get pre-calculated context (all matches list)
        context = match.metadata.get("_penalty_context") if match.metadata else None
        if not context:
            # Fallback: create minimal context
            all_matches = [match]
        else:
            # Extract all matches from context
            all_matches = context.get("all_matches", [match])
        
        # Use PenaltyCalculator for consistent calculation
        calculator = PenaltyCalculator(config, all_matches)
        penalties_dict = calculator.calculate_match_penalties(match)
        
        # Return the complete penalties dictionary
        # It already contains: horaire_prefere, gymnase_prefere, niveau_gymnase,
        # espacement, compaction, overlap_institution, aller_retour, 
        # contrainte_temporelle, guidance_qualite, and total
        return penalties_dict
    
    @staticmethod
    def _calculate_horaire_prefere_penalty(match: Match, config: Config) -> float:
        """
        Calculate penalty for non-preferred time slots.
        
        Uses the same logic as PreferredTimeSlotConstraint.
        Formula: penalty = multiplier × ((distance_minutes) / divisor)²
        """
        if not match.creneau:
            return 0.0
            
        # Get penalty parameters from config (use exact attribute names)
        weight = getattr(config, 'penalite_apres_horaire_min', 1.0)
        penalty_before_one = getattr(config, 'penalite_avant_horaire_min', 6.0)
        penalty_before_both = getattr(config, 'penalite_avant_horaire_min_deux', 15.0)
        tolerance_minutes = getattr(config, 'penalite_horaire_tolerance', 30.0)
        divisor = getattr(config, 'penalite_horaire_diviseur', 60.0)
        
        def parse_horaire(horaire: str) -> int:
            """Parse HH:MM to minutes since midnight"""
            try:
                parts = horaire.split(':')
                heures = int(parts[0])
                minutes = int(parts[1]) if len(parts) > 1 else 0
                return heures * 60 + minutes
            except (ValueError, IndexError):
                return 14 * 60  # Default 14h
        
        def calculate_for_equipe(equipe) -> tuple:
            """Returns (distance_minutes, is_before)"""
            if not equipe.horaires_preferes:
                return 0.0, False
            
            creneau_horaire = match.creneau.horaire
            if creneau_horaire in equipe.horaires_preferes:
                return 0.0, False
            
            horaire_match = parse_horaire(creneau_horaire)
            horaire_pref = parse_horaire(equipe.horaires_preferes[0])
            
            distance_minutes = abs(horaire_match - horaire_pref)
            
            if distance_minutes <= tolerance_minutes:
                return 0.0, False
            
            is_before = horaire_match < horaire_pref
            return distance_minutes, is_before
        
        # Calculate for both teams
        distance1, is_before1 = calculate_for_equipe(match.equipe1)
        distance2, is_before2 = calculate_for_equipe(match.equipe2)
        
        if distance1 == 0 and distance2 == 0:
            return 0.0
        
        # Count teams playing before their preferred time (outside tolerance)
        nb_equipes_avant = 0
        if distance1 > 0 and is_before1:
            nb_equipes_avant += 1
        if distance2 > 0 and is_before2:
            nb_equipes_avant += 1
        
        # Determine multiplier
        if nb_equipes_avant == 2:
            multiplicateur = penalty_before_both
        elif nb_equipes_avant == 1:
            multiplicateur = penalty_before_one
        else:
            multiplicateur = weight
        
        # Calculate total penalty
        penalty = 0.0
        if distance1 > 0:
            penalty += multiplicateur * ((distance1 / divisor) ** 2)
        if distance2 > 0:
            penalty += multiplicateur * ((distance2 / divisor) ** 2)
        
        return penalty
    
    @staticmethod
    def _calculate_espacement_penalty(match: Match, config: Config) -> float:
        """
        Calculate penalty for poor spacing between matches for same team.
        
        Uses config.penalites_espacement_repos: [penalty_0_weeks, penalty_1_week, penalty_2_weeks, ...]
        If rest >= len(list), penalty = 0 (sufficient spacing).
        
        Returns:
            Penalty value (0.0 = good spacing, higher = worse)
        """
        if not match.creneau:
            return 0.0
        
        # Get penalty list from config
        penalites = getattr(config, 'penalites_espacement_repos', [5.0, 2.0, 1.0])
        if not penalites:
            return 0.0
        
        # Get pre-calculated context
        context = match.metadata.get("_penalty_context") if match.metadata else None
        if not context:
            return 0.0
        
        current_week = match.creneau.semaine
        penalty = 0.0
        
        # Check spacing for team 1
        team1_matches = context.get("team1_matches", [])
        for other_match in team1_matches:
            if other_match is match or not other_match.creneau:
                continue
            
            weeks_gap = abs(current_week - other_match.creneau.semaine)
            
            # Apply penalty if gap is too small
            if weeks_gap < len(penalites):
                penalty += penalites[weeks_gap]
        
        # Check spacing for team 2
        team2_matches = context.get("team2_matches", [])
        for other_match in team2_matches:
            if other_match is match or not other_match.creneau:
                continue
            
            weeks_gap = abs(current_week - other_match.creneau.semaine)
            
            # Apply penalty if gap is too small
            if weeks_gap < len(penalites):
                penalty += penalites[weeks_gap]
        
        # Divide by 2 since we counted each pair twice (once per team)
        return penalty / 2.0
    
    @staticmethod
    def _calculate_indisponibilite_penalty(match: Match, config: Config) -> float:
        """
        Calculate penalty for scheduling during unavailable periods.
        
        semaines_indisponibles is Dict[int, Set[str]] where:
        - key: week number
        - value: set of unavailable time slots (or empty set = whole week unavailable)
        """
        if not match.creneau:
            return 0.0
        
        penalty_weight = 10000  # Hard constraint weight for unavailability
        semaine = match.creneau.semaine
        horaire = match.creneau.horaire
        
        penalty = 0.0
        
        # Check equipe1 unavailability
        if hasattr(match.equipe1, 'semaines_indisponibles'):
            indispo_horaires = match.equipe1.semaines_indisponibles.get(semaine)
            if indispo_horaires is not None:
                # If empty set: whole week unavailable
                # If non-empty: specific time slots unavailable
                if len(indispo_horaires) == 0 or horaire in indispo_horaires:
                    penalty += penalty_weight
        
        # Check equipe2 unavailability
        if hasattr(match.equipe2, 'semaines_indisponibles'):
            indispo_horaires = match.equipe2.semaines_indisponibles.get(semaine)
            if indispo_horaires is not None:
                if len(indispo_horaires) == 0 or horaire in indispo_horaires:
                    penalty += penalty_weight
        
        return penalty
    
    @staticmethod
    def _calculate_compaction_penalty(match: Match, config: Config) -> float:
        """
        Calculate penalty for spreading matches too much or too little across weeks.
        
        Uses config.compaction_penalites_par_semaine: [penalty_week1, penalty_week2, ...]
        The penalty represents how undesirable it is to schedule in that week.
        
        Returns:
            Penalty value (0.0 = good distribution, higher = worse)
        """
        if not match.creneau:
            return 0.0
        
        # Get penalty list from config (indexed by week number - 1)
        penalites = getattr(config, 'compaction_penalites_par_semaine', [])
        if not penalites:
            return 0.0
        
        current_week = match.creneau.semaine
        
        # Week indices are 0-based in the list, but semaine starts at 1 or semaine_min
        semaine_min = getattr(config, 'semaine_min', 1)
        week_index = current_week - semaine_min
        
        # Return penalty for this week if defined
        if 0 <= week_index < len(penalites):
            return float(penalites[week_index])
        
        return 0.0
    
    @staticmethod
    def _calculate_overlap_penalty(match: Match, config: Config) -> float:
        """
        Calculate penalty for institution overlaps (same institution, same time).
        
        Uses config.overlap_institution_poids for penalty weight.
        Checks if multiple teams from same institution play at same time.
        
        Returns:
            Penalty value (0.0 = no overlap, higher = conflicts)
        """
        if not match.creneau:
            return 0.0
        
        # Get penalty weight from config
        poids = getattr(config, 'overlap_institution_poids', 10.0)
        if poids == 0:
            return 0.0
        
        # Get pre-calculated context
        context = match.metadata.get("_penalty_context") if match.metadata else None
        if not context:
            return 0.0
        
        # Get matches at same slot
        slot_matches = context.get("slot_matches", [])
        if len(slot_matches) <= 1:
            return 0.0  # No other matches at this time
        
        # Get institutions of current match teams
        inst1 = match.equipe1.institution
        inst2 = match.equipe2.institution
        
        penalty = 0.0
        
        # Check for overlaps with other matches
        for other_match in slot_matches:
            if other_match is match:
                continue
            
            other_inst1 = other_match.equipe1.institution
            other_inst2 = other_match.equipe2.institution
            
            # Count overlaps (same institution playing in both matches)
            overlaps = 0
            if inst1 == other_inst1 or inst1 == other_inst2:
                overlaps += 1
            if inst2 == other_inst1 or inst2 == other_inst2:
                overlaps += 1
            
            # Apply penalty for each overlap
            penalty += overlaps * poids
        
        # Divide by 2 since we'll count each pair twice when processing all matches
        return penalty / 2.0
    
    @staticmethod
    def _format_slots(
        creneaux_disponibles: Optional[List[Creneau]],
        solution: Solution,
        gymnases: Optional[List[Gymnase]] = None,
        config: Optional[Config] = None
    ) -> Dict[str, List[Dict]]:
        """Format slot data (available and occupied).
        
        IMPORTANT: Cette fonction prend en compte la durée réelle des matchs (configurable).
        Un match à 15h occupe un terrain de 15h à 16h30 (handball) ou 17h (volley), donc il 
        réduit la capacité disponible des créneaux adjacents.
        """
        from collections import Counter, defaultdict
        
        # Récupérer la durée d'un match depuis la config (défaut: 90 min)
        match_duration_minutes = config.duree_match_minutes if config else 90
        
        # Helper function: convertir horaire "14h00" en minutes depuis minuit
        def horaire_to_minutes(horaire: str) -> int:
            """Convertit '14h00' en 840 (14*60)"""
            if not horaire or 'h' not in horaire:
                return 0
            parts = horaire.lower().split('h')
            heures = int(parts[0])
            minutes = int(parts[1]) if len(parts) > 1 and parts[1] else 0
            return heures * 60 + minutes
        
        # Helper function: vérifier si deux créneaux se chevauchent
        def creneaux_se_chevauchent(horaire_match: str, horaire_creneau: str) -> bool:
            """
            Vérifie si un match à horaire_match chevauche le créneau horaire_creneau.
            Exemple: Match à 15h (15h-16h30) chevauche les créneaux 14h, 16h mais pas 18h.
            """
            match_start = horaire_to_minutes(horaire_match)
            match_end = match_start + match_duration_minutes
            
            creneau_start = horaire_to_minutes(horaire_creneau)
            creneau_end = creneau_start + 120  # Créneaux de 2h (120 minutes)
            
            # Chevauchement si: début_match < fin_créneau ET fin_match > début_créneau
            return match_start < creneau_end and match_end > creneau_start
        
        # Compter le nombre de matchs par créneau (horaire exact)
        slot_occupation = Counter()
        occupied_with_matches = {}  # Pour garder l'info des matchs occupant les slots
        
        # Compter l'occupation réelle par créneau en tenant compte des chevauchements
        # Format: {(gymnase, semaine, horaire_creneau): nb_terrains_occupes}
        real_occupation = defaultdict(int)
        
        for idx, match in enumerate(solution.matchs_planifies):
            if match.creneau:
                # Occupation du créneau exact où le match est planifié
                slot_key = (match.creneau.gymnase, match.creneau.semaine, match.creneau.horaire)
                slot_occupation[slot_key] += 1
                
                match_id = f"M_{idx:04d}"
                slot_id = f"S_{match.creneau.gymnase}_{match.creneau.semaine}_{match.creneau.horaire}_{slot_occupation[slot_key]}"
                
                occupied_with_matches[slot_id] = {
                    "slot_id": slot_id,
                    "gymnase": match.creneau.gymnase,
                    "semaine": match.creneau.semaine,
                    "horaire": match.creneau.horaire,
                    "status": "occupé",
                    "match_id": match_id,
                }
        
        # Calculer l'occupation réelle avec chevauchements
        if creneaux_disponibles:
            for idx, match in enumerate(solution.matchs_planifies):
                if match.creneau:
                    # Pour chaque créneau disponible, vérifier si ce match le chevauche
                    for creneau in creneaux_disponibles:
                        if (creneau.gymnase == match.creneau.gymnase and 
                            creneau.semaine == match.creneau.semaine):
                            # Vérifier le chevauchement temporel
                            if creneaux_se_chevauchent(match.creneau.horaire, creneau.horaire):
                                key = (creneau.gymnase, creneau.semaine, creneau.horaire)
                                real_occupation[key] += 1
        
        available = []
        occupied = list(occupied_with_matches.values())
        
        # Add available slots from creneaux_disponibles
        if creneaux_disponibles:
            # Créer un mapping gymnase -> capacité
            gymnase_capacities = {}
            if gymnases:
                for gym in gymnases:
                    gymnase_capacities[gym.nom] = gym.capacite
            
            for creneau in creneaux_disponibles:
                slot_key = (creneau.gymnase, creneau.semaine, creneau.horaire)
                
                # Utiliser l'occupation réelle (avec chevauchements) au lieu de l'occupation simple
                nb_matchs_occupes = real_occupation.get(slot_key, 0)
                
                # Récupérer la capacité du gymnase (défaut: 1)
                capacite = gymnase_capacities.get(creneau.gymnase, 1)
                
                # Calculer le nombre de slots disponibles
                nb_slots_disponibles = max(0, capacite - nb_matchs_occupes)
                
                # Générer les slots disponibles
                for i in range(nb_slots_disponibles):
                    slot_id = f"S_{creneau.gymnase}_{creneau.semaine}_{creneau.horaire}_{nb_matchs_occupes + i + 1}"
                    slot_data = {
                        "slot_id": slot_id,
                        "gymnase": creneau.gymnase,
                        "semaine": creneau.semaine,
                        "horaire": creneau.horaire,
                        "status": "libre"
                    }
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
        """Calculate comprehensive statistics.
        
        IMPORTANT: Les matchs "entente" (matchs sans créneau entre institutions en entente)
        sont comptés comme PLANIFIÉS car ils seront joués en dehors du calendrier.
        """
        
        # Compter les matchs entente (non planifiés mais considérés comme joués)
        nb_matchs_entente = sum(1 for m in solution.matchs_non_planifies 
                                if m.metadata.get("is_entente", False))
        
        # Total de matchs réellement planifiés = matchs avec créneau + matchs entente
        nb_reellement_planifies = len(solution.matchs_planifies) + nb_matchs_entente
        
        # Total de matchs NON planifiés = matchs sans créneau (excluant les ententes)
        nb_reellement_non_planifies = len(solution.matchs_non_planifies) - nb_matchs_entente
        
        total_matchs = len(solution.matchs_planifies) + len(solution.matchs_non_planifies)
        
        # Taux de planification corrigé (inclut les ententes)
        taux_planification = (nb_reellement_planifies / total_matchs * 100) if total_matchs > 0 else 0.0
        
        # Global statistics
        nb_matchs_fixes = sum(1 for m in solution.matchs_planifies if m.metadata.get("is_fixed", False))
        nb_matchs_auto = len(solution.matchs_planifies) - nb_matchs_fixes
        
        global_stats = {
            "taux_planification": taux_planification,  # Taux corrigé incluant les ententes
            "score_total": float(solution.score),
            "score_moyen_par_match": float(solution.score / total_matchs) if total_matchs > 0 else 0.0,
            "nb_matchs_total": total_matchs,
            "nb_matchs_planifies": nb_reellement_planifies,  # Inclut les ententes
            "nb_matchs_non_planifies": nb_reellement_non_planifies,  # Exclut les ententes
            "nb_matchs_entente": nb_matchs_entente,  # Nouveau : nombre de matchs entente
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
        """Calculate statistics per pool.
        
        IMPORTANT: Les matchs "entente" sont comptés comme PLANIFIÉS.
        """
        stats = defaultdict(lambda: {"nb_matchs_planifies": 0, "nb_matchs_non_planifies": 0, "nb_matchs_entente": 0})
        
        # Matchs avec créneau = planifiés
        for match in solution.matchs_planifies:
            stats[match.poule]["nb_matchs_planifies"] += 1
        
        # Matchs sans créneau : distinguer ententes (= planifiés) vs vrais non-planifiés
        for match in solution.matchs_non_planifies:
            is_entente = match.metadata.get("is_entente", False)
            if is_entente:
                # Match entente = considéré comme planifié
                stats[match.poule]["nb_matchs_planifies"] += 1
                stats[match.poule]["nb_matchs_entente"] += 1
            else:
                # Vrai match non planifié
                stats[match.poule]["nb_matchs_non_planifies"] += 1
        
        # Calculate completion rate (inclut les ententes dans les planifiés)
        for poule in stats:
            total = stats[poule]["nb_matchs_planifies"] + stats[poule]["nb_matchs_non_planifies"]
            stats[poule]["taux_completion"] = (stats[poule]["nb_matchs_planifies"] / total * 100) if total > 0 else 0.0
        
        return dict(stats)
    
    @staticmethod
    def _stats_par_gymnase(solution: Solution, gymnases: List[Gymnase]) -> Dict[str, Dict[str, Any]]:
        """Calculate statistics per venue."""
        from collections import defaultdict
        
        stats = defaultdict(lambda: {"nb_matchs": 0, "capacite": 1, "nb_creneaux_disponibles": 0})
        
        # Initialize with venue data
        for gymnase in gymnases:
            stats[gymnase.nom]["capacite"] = gymnase.capacite
        
        # Count matches per venue
        for match in solution.matchs_planifies:
            if match.creneau:
                stats[match.creneau.gymnase]["nb_matchs"] += 1
        
        # Calculate total available slots for each venue
        # This requires knowing the schedule structure (weeks, time slots)
        # For accurate calculation, this should be passed from the caller
        # For now, we estimate based on matches if creneaux_disponibles not available
        
        # Extract unique weeks and time slots from scheduled matches
        semaines = set()
        horaires = set()
        for match in solution.matchs_planifies:
            if match.creneau:
                semaines.add(match.creneau.semaine)
                horaires.add(match.creneau.horaire)
        
        nb_weeks = len(semaines) if semaines else 1
        nb_time_slots = len(horaires) if horaires else 1
        
        # Calculate occupation rate for each venue
        for gymnase_nom in stats:
            gymnase = next((g for g in gymnases if g.nom == gymnase_nom), None)
            if gymnase:
                # Total theoretical capacity = weeks × time_slots × capacity
                total_capacity = nb_weeks * nb_time_slots * gymnase.capacite
                
                # Actual usage
                nb_matchs = stats[gymnase_nom]["nb_matchs"]
                
                # Occupation rate
                if total_capacity > 0:
                    stats[gymnase_nom]["taux_occupation"] = round((nb_matchs / total_capacity) * 100, 1)
                else:
                    stats[gymnase_nom]["taux_occupation"] = 0.0
                
                stats[gymnase_nom]["nb_creneaux_disponibles"] = total_capacity
            else:
                stats[gymnase_nom]["taux_occupation"] = 0.0
        
        return dict(stats)
    
    @staticmethod
    def _stats_par_equipe(solution: Solution, equipes: List[Equipe]) -> Dict[str, Dict[str, Any]]:
        """Calculate statistics per team.
        
        IMPORTANT: Les matchs "entente" sont comptés comme PLANIFIÉS.
        """
        stats = defaultdict(lambda: {
            "nb_matchs_planifies": 0,
            "nb_matchs_non_planifies": 0,
            "nb_matchs_entente": 0,
            "horaires_repartition": defaultdict(int),
        })
        
        # Count scheduled matches (avec créneau)
        for match in solution.matchs_planifies:
            for equipe in [match.equipe1, match.equipe2]:
                equipe_id = equipe.id_unique
                stats[equipe_id]["nb_matchs_planifies"] += 1
                if match.creneau:
                    stats[equipe_id]["horaires_repartition"][match.creneau.horaire] += 1
        
        # Count unscheduled matches : distinguer ententes vs vrais non-planifiés
        for match in solution.matchs_non_planifies:
            is_entente = match.metadata.get("is_entente", False)
            for equipe in [match.equipe1, match.equipe2]:
                equipe_id = equipe.id_unique
                if is_entente:
                    # Match entente = considéré comme planifié
                    stats[equipe_id]["nb_matchs_planifies"] += 1
                    stats[equipe_id]["nb_matchs_entente"] += 1
                else:
                    # Vrai match non planifié
                    stats[equipe_id]["nb_matchs_non_planifies"] += 1
        
        # Convert defaultdict to dict
        result = {}
        for equipe_id, data in stats.items():
            result[equipe_id] = {
                "nb_matchs_planifies": data["nb_matchs_planifies"],
                "nb_matchs_non_planifies": data["nb_matchs_non_planifies"],
                "nb_matchs_entente": data["nb_matchs_entente"],
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
