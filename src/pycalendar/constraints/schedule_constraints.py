"""Schedule-related constraints."""

from typing import Dict, Tuple, List, Optional
from pycalendar.core.models import Match, Creneau
from .base import Constraint


class MinSpacingConstraint(Constraint):
    """Ensures spacing between matches of the same team with configurable penalties.
    
    Penalty is based on the number of weeks of rest between consecutive matches.
    The penalty list defines penalties for [0 weeks rest, 1 week rest, 2 weeks rest, ...].
    If rest weeks >= len(penalty_list), penalty is 0 (sufficient rest).
    
    Example:
        penalty_list = [100.0, 50.0, 10.0]
        - 0 weeks rest (consecutive matches): penalty = 100.0
        - 1 week rest (1 week between matches): penalty = 50.0
        - 2 weeks rest: penalty = 10.0
        - 3+ weeks rest: penalty = 0.0 (sufficient spacing)
    """
    
    def __init__(self, penalty_list: Optional[List[float]] = None):
        # Note: weight is not used as it's embedded in the penalty_list
        super().__init__(weight=1.0, hard=False)
        self.penalty_list = penalty_list if penalty_list is not None else [100.0, 50.0]
    
    def _get_penalty_for_rest(self, weeks_rest: int) -> float:
        """Get penalty for a given number of weeks of rest.
        
        Args:
            weeks_rest: Number of weeks between two matches (0 = consecutive weeks)
            
        Returns:
            Penalty value (0 if weeks_rest >= len(penalty_list))
        """
        if weeks_rest >= len(self.penalty_list):
            return 0.0
        return self.penalty_list[weeks_rest]
    
    def validate(self, match: Match, creneau: Creneau, solution_state: Dict) -> Tuple[bool, float]:
        """Validate spacing constraint with penalty based on weeks of rest.
        
        Calculates penalty based on the number of weeks of rest since the last match
        for each team involved in the current match.
        
        IMPORTANT: Utilise id_unique pour distinguer équipes de même nom mais genre différent.
        """
        derniers_matchs_equipe1 = solution_state.get('derniers_matchs', {}).get(match.equipe1.id_unique, [])
        derniers_matchs_equipe2 = solution_state.get('derniers_matchs', {}).get(match.equipe2.id_unique, [])
        
        penalty = 0.0
        
        # Pour chaque équipe, trouver le match le plus récent et calculer les semaines de repos
        if derniers_matchs_equipe1:
            # Trouver le match le plus proche (le plus récent avant, ou le plus proche après)
            semaine_plus_proche = min(derniers_matchs_equipe1, key=lambda s: abs(s - creneau.semaine))
            weeks_rest = abs(creneau.semaine - semaine_plus_proche) - 1
            weeks_rest = max(0, weeks_rest)  # Ne peut pas être négatif
            penalty += self._get_penalty_for_rest(weeks_rest)
        
        if derniers_matchs_equipe2:
            semaine_plus_proche = min(derniers_matchs_equipe2, key=lambda s: abs(s - creneau.semaine))
            weeks_rest = abs(creneau.semaine - semaine_plus_proche) - 1
            weeks_rest = max(0, weeks_rest)
            penalty += self._get_penalty_for_rest(weeks_rest)
        
        # Contrainte souple : toujours valide, seule la pénalité varie
        return True, penalty
    
    def get_name(self) -> str:
        return "MinSpacing"


class LoadBalancingConstraint(Constraint):
    """Balances load across weeks and venues."""
    
    def __init__(self, weight: float = 50.0):
        super().__init__(weight=weight, hard=False)
    
    def validate(self, match: Match, creneau: Creneau, solution_state: Dict) -> Tuple[bool, float]:
        matchs_semaine = solution_state.get('matchs_par_semaine', {}).get(creneau.semaine, 0)
        matchs_gymnase = solution_state.get('matchs_par_gymnase', {}).get(creneau.gymnase, 0)
        
        avg_matchs_semaine = solution_state.get('avg_matchs_semaine', 0)
        avg_matchs_gymnase = solution_state.get('avg_matchs_gymnase', 0)
        
        penalty = 0.0
        
        if avg_matchs_semaine > 0:
            ecart_semaine = abs(matchs_semaine - avg_matchs_semaine)
            penalty += self.weight * ecart_semaine * 0.5
        
        if avg_matchs_gymnase > 0:
            ecart_gymnase = abs(matchs_gymnase - avg_matchs_gymnase)
            penalty += self.weight * ecart_gymnase * 0.5
        
        return True, penalty
    
    def get_name(self) -> str:
        return "LoadBalancing"


class PreferredTimeConstraint(Constraint):
    """Contrainte souple pour horaires préférés avec système de tolérance sophistiqué.
    
    LOGIQUE DE TOLÉRANCE:
    - Fenêtre de tolérance (en minutes) où une équipe peut jouer plus tôt/tard sans pénalité
    - Si distance <= tolérance : PAS de pénalité (match accepté dans la zone de tolérance)
    - Si distance > tolérance : pénalité calculée sur la distance TOTALE
    
    MULTIPLICATEURS selon position du match par rapport à l'horaire préféré:
    - 300x : match AVANT horaire préféré des 2 équipes (violation grave)
    - 100x : match AVANT horaire préféré d'1 seule équipe (violation moyenne)
    - 10x : match APRÈS horaire préféré (dégradation acceptable)
    
    FORMULE DE PÉNALITÉ:
    pénalité = multiplicateur × ((distance / diviseur)²)
    où:
    - distance = distance totale en minutes (si > tolérance)
    - diviseur = paramètre de normalisation (60=heures, 90=poids plus faible)
    
    EXEMPLE avec tolérance=30 minutes, diviseur=90:
    - Match à +20min : distance=20 <= 30 → AUCUNE pénalité
    - Match à +45min : distance=45 > 30 → pénalité = 10 × (45/90)² = 2.5
    - Match à -50min (1 équipe avant) : distance=50 > 30 → pénalité = 100 × (50/90)² ≈ 30.9
    - Match à -70min (2 équipes avant) : distance=70 > 30 → pénalité = 300 × (70/90)² ≈ 181.5
    
    Cette implémentation utilise EXACTEMENT la même logique que CP-SAT pour garantir
    la cohérence entre les deux solveurs (CP-SAT et Greedy).
    """
    
    def __init__(self, weight: float = 10.0, penalty_before_one: float = 100.0, 
                 penalty_before_both: float = 300.0, divisor: float = 60.0, tolerance: float = 0.0):
        super().__init__(weight=weight, hard=False)
        self.penalty_before_one = penalty_before_one
        self.penalty_before_both = penalty_before_both
        self.divisor = divisor
        self.tolerance = tolerance
    
    def _parse_horaire(self, horaire: str) -> int:
        """
        Convertit un horaire en minutes depuis minuit.
        Format attendu: "14H", "14H30", "20H00"
        
        Returns:
            Nombre de minutes depuis minuit
        """
        try:
            # Nettoyer l'horaire
            horaire = horaire.strip().upper().replace('H', ':')
            
            # Ajouter ":00" si pas de minutes
            if ':' not in horaire:
                horaire += ':00'
            
            parts = horaire.split(':')
            heures = int(parts[0])
            minutes = int(parts[1]) if len(parts) > 1 else 0
            
            return heures * 60 + minutes
        except (ValueError, IndexError):
            # En cas d'erreur de parsing, retourner une valeur par défaut (14h)
            return 14 * 60
    
    def _calculate_penalty_for_equipe(self, equipe, creneau_horaire: str) -> tuple[float, bool]:
        """
        Calcule la pénalité pour une équipe donnée selon la nouvelle logique sophistiquée.
        
        Returns:
            (penalty, is_before): pénalité calculée et si le match est avant l'horaire préféré
        """
        if not equipe.horaires_preferes:
            return 0.0, False
        
        if creneau_horaire in equipe.horaires_preferes:
            return 0.0, False
        
        # Parser l'horaire préféré (prendre le premier si plusieurs)
        horaire_match = self._parse_horaire(creneau_horaire)
        horaire_pref = self._parse_horaire(equipe.horaires_preferes[0])
        
        # Calculer la distance en minutes
        distance_minutes = abs(horaire_match - horaire_pref)
        
        # Vérifier la tolérance
        if distance_minutes <= self.tolerance:
            return 0.0, False
        
        # Hors tolérance : utiliser la distance TOTALE (pas seulement l'excédent)
        # Vérifier si le match est avant l'horaire préféré
        is_before = horaire_match < horaire_pref
        
        # Retourner la distance totale (pénalité calculée au niveau du match avec le multiplicateur)
        return distance_minutes, is_before
    
    def validate(self, match: Match, creneau: Creneau, solution_state: Dict) -> Tuple[bool, float]:
        """
        Valide les horaires préférés avec la logique sophistiquée.
        
        Utilise les mêmes multiplicateurs que CP-SAT:
        - 300 si le match est avant l'horaire préféré des 2 équipes (hors tolérance)
        - 100 si le match est avant l'horaire préféré d'1 équipe (hors tolérance)
        - 10 (weight) sinon
        
        CORRECTION : Le multiplicateur doit être déterminé APRÈS avoir exclu les équipes
        dans la tolérance, sinon une équipe dans sa tolérance peut influencer le multiplicateur.
        """
        # Analyser chaque équipe
        distance1, is_before1 = self._calculate_penalty_for_equipe(match.equipe1, creneau.horaire)
        distance2, is_before2 = self._calculate_penalty_for_equipe(match.equipe2, creneau.horaire)
        
        # Si aucune distance, pas de pénalité
        if distance1 == 0 and distance2 == 0:
            return True, 0.0
        
        # CORRECTION : Compter uniquement les équipes HORS tolérance qui jouent AVANT
        nb_equipes_avant_hors_tolerance = 0
        if distance1 > 0 and is_before1:
            nb_equipes_avant_hors_tolerance += 1
        if distance2 > 0 and is_before2:
            nb_equipes_avant_hors_tolerance += 1
        
        # Déterminer le multiplicateur (seulement basé sur les équipes hors tolérance)
        if nb_equipes_avant_hors_tolerance == 2:
            multiplicateur = self.penalty_before_both
        elif nb_equipes_avant_hors_tolerance == 1:
            multiplicateur = self.penalty_before_one
        else:
            multiplicateur = self.weight
        
        # Calculer la pénalité totale avec le bon multiplicateur
        penalty = 0.0
        if distance1 > 0:
            penalty += multiplicateur * ((distance1 / self.divisor) ** 2)
        if distance2 > 0:
            penalty += multiplicateur * ((distance2 / self.divisor) ** 2)
        
        return True, penalty
    
    def get_name(self) -> str:
        return "PreferredTime"
