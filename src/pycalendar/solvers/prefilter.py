"""
Prefiltering module for CP-SAT solver.

Filters out impossible match-slot combinations BEFORE creating variables.
This dramatically reduces the model size and speeds up solving.
"""

from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, field

from pycalendar.core.models import Match, Creneau, Gymnase
from pycalendar.core.config import Config
from pycalendar.core.penalties import horaire_to_minutes


@dataclass
class PrefilterStats:
    """Statistics about prefiltering results."""
    total_combinations: int = 0
    blocked_by_schedule: int = 0  # horaire_avant_interdit
    blocked_by_availability: int = 0  # équipe indisponible
    blocked_by_gym_availability: int = 0  # gymnase indisponible
    blocked_by_capacity: int = 0  # capacité dépassée
    blocked_by_obligation: int = 0  # obligation de présence non respectée
    blocked_by_temporal: int = 0  # contrainte temporelle
    blocked_by_max_week: int = 0  # max matchs par semaine dépassé
    remaining_valid: int = 0
    
    # Statistiques additionnelles
    matchs_sans_creneau: int = 0  # Matchs sans aucun créneau valide
    
    def __str__(self):
        return (
            f"Prefilter Stats:\n"
            f"  Total combinations: {self.total_combinations:,}\n"
            f"  Blocked by schedule: {self.blocked_by_schedule:,} ({self.pct(self.blocked_by_schedule)}%)\n"
            f"  Blocked by availability: {self.blocked_by_availability:,} ({self.pct(self.blocked_by_availability)}%)\n"
            f"  Blocked by gym: {self.blocked_by_gym_availability:,} ({self.pct(self.blocked_by_gym_availability)}%)\n"
            f"  Blocked by capacity: {self.blocked_by_capacity:,} ({self.pct(self.blocked_by_capacity)}%)\n"
            f"  Blocked by obligation: {self.blocked_by_obligation:,} ({self.pct(self.blocked_by_obligation)}%)\n"
            f"  Blocked by temporal: {self.blocked_by_temporal:,} ({self.pct(self.blocked_by_temporal)}%)\n"
            f"  Remaining valid: {self.remaining_valid:,} ({self.pct(self.remaining_valid)}%)\n"
            f"  Reduction: {100 - self.pct(self.remaining_valid):.1f}%"
        )
    
    def pct(self, value):
        if self.total_combinations == 0:
            return 0
        return round(100 * value / self.total_combinations, 1)


class CreneauPrefilter:
    """
    Pre-filters match-creneau combinations to reduce model size.
    
    This class identifies which (match, creneau) pairs are definitely
    impossible due to hard constraints, avoiding creating variables
    for them in the CP-SAT model.
    
    Contraintes vérifiées :
    - horaire_avant_interdit: équipes ne peuvent pas jouer avant leur horaire préféré
    - disponibilité équipe: indisponibilités spécifiques
    - disponibilité gymnase: fermetures de gymnase
    - capacité: nombre de matchs max par créneau
    - obligations de présence: gymnase réservé à certaines institutions
    - contraintes temporelles: matchs avant/après une semaine donnée (mode dur)
    """
    
    def __init__(self, config: Config, gymnases: Dict[str, Gymnase],
                 matchs_fixes: Optional[List[Match]] = None,
                 obligations_presence: Optional[Dict[str, str]] = None,
                 contraintes_temporelles: Optional[Dict] = None):
        self.config = config
        self.gymnases = gymnases
        self.matchs_fixes = matchs_fixes or []
        self.obligations_presence = obligations_presence or {}
        self.contraintes_temporelles = contraintes_temporelles or {}
        
        # Pre-compute fixed matches data
        self._compute_fixed_matches_data()
    
    def _compute_fixed_matches_data(self):
        """Pre-compute data structures for fixed matches."""
        # Count fixed matches per (equipe, semaine)
        self.matchs_fixes_par_equipe_semaine: Dict[Tuple[str, int], int] = {}
        
        # Count fixed matches per creneau (semaine, gymnase, horaire)
        self.matchs_fixes_par_creneau: Dict[Tuple[int, str, str], int] = {}
        
        for match_fixe in self.matchs_fixes:
            if not match_fixe.metadata:
                continue
                
            semaine = match_fixe.metadata.get('semaine')
            if semaine is None:
                continue
            
            try:
                semaine = int(semaine)
            except (ValueError, TypeError):
                continue
            
            # Count by equipe/semaine
            for equipe_id in [match_fixe.equipe1.id_unique, match_fixe.equipe2.id_unique]:
                key = (equipe_id, semaine)
                self.matchs_fixes_par_equipe_semaine[key] = \
                    self.matchs_fixes_par_equipe_semaine.get(key, 0) + 1
            
            # Count by creneau
            horaire = match_fixe.metadata.get('horaire')
            gymnase = match_fixe.metadata.get('gymnase')
            if horaire and gymnase:
                creneau_key = (semaine, str(gymnase).strip(), str(horaire).strip())
                self.matchs_fixes_par_creneau[creneau_key] = \
                    self.matchs_fixes_par_creneau.get(creneau_key, 0) + 1
    
    def filter(self, matchs: List[Match], creneaux: List[Creneau]
              ) -> Tuple[Dict[int, List[int]], PrefilterStats]:
        """
        Filter match-creneau combinations and return valid ones.
        
        Args:
            matchs: List of matches to schedule
            creneaux: List of available time slots
            
        Returns:
            Tuple of:
            - Dictionary mapping match index -> list of valid creneau indices
            - Prefilter statistics
        """
        stats = PrefilterStats()
        valid_creneaux_par_match: Dict[int, List[int]] = {}
        
        # Pre-compute creneau data for efficiency
        creneau_data = self._precompute_creneau_data(creneaux)
        
        for i, match in enumerate(matchs):
            valid_creneaux = []
            
            for j, creneau in enumerate(creneaux):
                stats.total_combinations += 1
                
                # Check all blocking conditions
                block_reason = self._check_blocking(match, creneau, creneau_data.get(j, {}))
                
                if block_reason == 'schedule':
                    stats.blocked_by_schedule += 1
                elif block_reason == 'availability':
                    stats.blocked_by_availability += 1
                elif block_reason == 'gym':
                    stats.blocked_by_gym_availability += 1
                elif block_reason == 'capacity':
                    stats.blocked_by_capacity += 1
                else:
                    valid_creneaux.append(j)
            
            valid_creneaux_par_match[i] = valid_creneaux
        
        stats.remaining_valid = sum(len(v) for v in valid_creneaux_par_match.values())
        return valid_creneaux_par_match, stats
    
    def _precompute_creneau_data(self, creneaux: List[Creneau]) -> Dict[int, Dict]:
        """Pre-compute data for each creneau for efficiency."""
        data = {}
        for j, creneau in enumerate(creneaux):
            creneau_minutes = horaire_to_minutes(creneau.horaire)
            
            # Get gymnasium
            gymnase = self.gymnases.get(creneau.gymnase)
            
            # Get available capacity (after fixed matches)
            capacity = 0
            if gymnase:
                capacity = gymnase.get_capacite_disponible(creneau.semaine, creneau.horaire)
                creneau_key = (creneau.semaine, creneau.gymnase.strip(), creneau.horaire.strip())
                fixed_on_slot = self.matchs_fixes_par_creneau.get(creneau_key, 0)
                capacity = max(0, capacity - fixed_on_slot)
            
            # Check if gym is available
            gym_available = True
            if gymnase and not gymnase.est_disponible(creneau.semaine, creneau.horaire):
                gym_available = False
            
            data[j] = {
                'minutes': creneau_minutes,
                'gymnase': gymnase,
                'capacity': capacity,
                'gym_available': gym_available,
            }
        return data
    
    def _check_blocking(self, match: Match, creneau: Creneau, 
                       creneau_data: Dict) -> Optional[str]:
        """
        Check if a match-creneau combination is blocked.
        
        Returns:
            None if valid, or the blocking reason ('schedule', 'availability', 'gym', 'capacity')
        """
        # 1. Check schedule constraint (horaire_avant_interdit)
        if self.config.horaire_avant_interdit:
            if self._is_blocked_by_schedule(match, creneau_data.get('minutes', 0)):
                return 'schedule'
        
        # 2. Check team availability
        if not self._is_team_available(match, creneau):
            return 'availability'
        
        # 3. Check gymnasium availability
        if not creneau_data.get('gym_available', True):
            return 'gym'
        
        # 4. Check capacity (already 0 means blocked)
        if creneau_data.get('capacity', 0) <= 0:
            return 'capacity'
        
        return None
    
    def _is_blocked_by_schedule(self, match: Match, creneau_minutes: int) -> bool:
        """Check if match is blocked by horaire_avant_interdit constraint."""
        tolerance = self.config.horaire_avant_tolerance
        
        for equipe in [match.equipe1, match.equipe2]:
            if equipe.horaires_preferes:
                pref_minutes = horaire_to_minutes(equipe.horaires_preferes[0])
                diff = creneau_minutes - pref_minutes
                if diff < -tolerance:
                    return True
        return False
    
    def _is_team_available(self, match: Match, creneau: Creneau) -> bool:
        """Check if both teams are available for this creneau."""
        if not match.equipe1.est_disponible(creneau.semaine, creneau.horaire, creneau.gymnase):
            return False
        if not match.equipe2.est_disponible(creneau.semaine, creneau.horaire, creneau.gymnase):
            return False
        return True
    
    def get_remaining_capacity(self, creneau: Creneau) -> int:
        """Get remaining capacity for a creneau after fixed matches."""
        gymnase = self.gymnases.get(creneau.gymnase)
        if not gymnase:
            return 0
        
        capacity = gymnase.get_capacite_disponible(creneau.semaine, creneau.horaire)
        creneau_key = (creneau.semaine, creneau.gymnase.strip(), creneau.horaire.strip())
        fixed_on_slot = self.matchs_fixes_par_creneau.get(creneau_key, 0)
        
        return max(0, capacity - fixed_on_slot)
