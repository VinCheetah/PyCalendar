"""Greedy solver for sports scheduling."""

import random
from typing import List, Dict, Optional, Set
from pycalendar.core.models import Match, Creneau, Gymnase, Solution
from pycalendar.core.config import Config
from pycalendar.constraints.base import ConstraintValidator
from pycalendar.constraints.venue_constraints import VenueCapacityConstraint, VenueAvailabilityConstraint, VenuePresenceObligationConstraint
from pycalendar.constraints.team_constraints import (TeamAvailabilityConstraint, MaxMatchesPerWeekConstraint, 
                                          TeamNotPlayingSimultaneouslyConstraint)
from pycalendar.constraints.schedule_constraints import (MinSpacingConstraint, LoadBalancingConstraint,
                                              PreferredTimeConstraint)
from .base_solver import BaseSolver


class GreedySolver(BaseSolver):
    """Fast greedy solver for large-scale scheduling."""
    
    def __init__(self, config: Config, groupes_non_simultaneite: Optional[Dict[str, Set[str]]] = None,
                 ententes: Optional[Dict] = None, contraintes_temporelles: Optional[Dict] = None,
                 niveaux_gymnases: Optional[Dict[str, str]] = None):
        super().__init__(config)
        self.groupes_non_simultaneite = groupes_non_simultaneite or {}
        self.ententes = ententes or {}  # Dict avec paires d'institutions et leurs pénalités
        self.contraintes_temporelles = contraintes_temporelles or {}  # Dict avec paires d'équipes et leurs contraintes temporelles
        self.niveaux_gymnases = niveaux_gymnases or {}  # Dict avec niveaux des gymnases
        self.validator = self._build_validator()
    
    def _get_niveau_match(self, match: Match) -> Optional[int]:
        """
        Détermine le niveau d'un match basé sur sa poule.
        
        Args:
            match: Le match dont on veut connaître le niveau
            
        Returns:
            Le niveau (0=A1, 1=A2, 2=A3, 3=A4, etc.) ou None si indéterminé
        """
        poule = match.poule.upper()
        
        # Chercher un pattern comme A1, A2, A3, A4 ou similaire
        import re
        match_niveau = re.search(r'A(\d+)', poule)
        if match_niveau:
            return int(match_niveau.group(1)) - 1  # A1=0, A2=1, A3=2, A4=3
        
        # Autres patterns possibles
        if 'A1' in poule or '1' in poule and 'A' in poule:
            return 0
        elif 'A2' in poule or '2' in poule and 'A' in poule:
            return 1
        elif 'A3' in poule or '3' in poule and 'A' in poule:
            return 2
        elif 'A4' in poule or '4' in poule and 'A' in poule:
            return 3
        
        return None  # Niveau indéterminé
    
    def _est_entente(self, match: Match) -> bool:
        """Vérifie si un match est une entente (paire d'institutions configurée)."""
        if not self.config.entente_actif or not self.ententes:
            return False
        
        inst1 = match.equipe1.institution
        inst2 = match.equipe2.institution
        cle = tuple(sorted([inst1, inst2]))
        
        return cle in self.ententes
    
    def _respecte_contrainte_temporelle(self, match: Match, creneau: Creneau) -> bool:
        """Vérifie si le placement respecte les contraintes temporelles.
        
        Args:
            match: Le match à placer
            creneau: Le créneau où on veut le placer
            
        Returns:
            True si la contrainte est respectée ou inexistante, False sinon
        """
        from pycalendar.core.utils import matcher_contrainte_avec_genre
        
        if not self.config.contrainte_temporelle_actif or not self.contraintes_temporelles:
            return True
        
        # Extraire les infos des équipes
        eq1_nom = match.equipe1.nom
        eq1_genre = match.equipe1.genre
        eq2_nom = match.equipe2.nom
        eq2_genre = match.equipe2.genre
        
        # Parcourir toutes les contraintes pour trouver celles qui matchent
        for contrainte_key, contrainte in self.contraintes_temporelles.items():
            if matcher_contrainte_avec_genre(eq1_nom, eq1_genre, eq2_nom, eq2_genre, contrainte_key):
                # Une contrainte s'applique à ce match, vérifier si elle est respectée
                if not contrainte.est_respectee(creneau.semaine):
                    return False
        
        # Aucune contrainte applicable ou toutes respectées
        return True
    
    def _build_validator(self) -> ConstraintValidator:
        """Build constraint validator with all constraints."""
        validator = ConstraintValidator()
        
        validator.add_constraint(TeamAvailabilityConstraint(
            weight=self.config.poids_indisponibilite
        ))
        validator.add_constraint(MaxMatchesPerWeekConstraint(
            max_matches=self.config.max_matchs_par_equipe_par_semaine,
            weight=self.config.poids_capacite_gymnase
        ))
        validator.add_constraint(TeamNotPlayingSimultaneouslyConstraint(
            weight=self.config.poids_indisponibilite
        ))
        validator.add_constraint(MinSpacingConstraint(
            penalty_list=self.config.penalites_espacement_repos
        ))
        validator.add_constraint(LoadBalancingConstraint(
            weight=self.config.poids_equilibrage_charge
        ))
        validator.add_constraint(PreferredTimeConstraint(
            weight=self.config.penalite_apres_horaire_min,
            penalty_before_one=self.config.penalite_avant_horaire_min,
            penalty_before_both=self.config.penalite_avant_horaire_min_deux,
            divisor=self.config.penalite_horaire_diviseur,
            tolerance=self.config.penalite_horaire_tolerance
        ))
        
        return validator
    
    def _calculer_penalite_gymnase(self, match: Match, creneau: Creneau) -> float:
        """
        Calcule la pénalité/bonus pour les préférences de gymnase.
        
        Logique:
        - Pénalité de base = 2 × max(bonus_preferences_gymnases)
        - Pour chaque équipe, si le gymnase du créneau est dans ses préférences:
          soustraire le bonus correspondant au rang de préférence
        
        Args:
            match: Le match à planifier
            creneau: Le créneau candidat
            
        Returns:
            Pénalité finale (plus petit = meilleur)
        """
        if not self.config.bonus_preferences_gymnases:
            return 0.0
        
        # Pénalité de base
        base_penalty = 2 * max(self.config.bonus_preferences_gymnases)
        penalty = base_penalty
        
        # Vérifier équipe 1
        if match.equipe1.lieux_preferes:
            for rang, gymnase in enumerate(match.equipe1.lieux_preferes):
                if gymnase == creneau.gymnase and rang < len(self.config.bonus_preferences_gymnases):
                    penalty -= self.config.bonus_preferences_gymnases[rang]
                    break
        
        # Vérifier équipe 2
        if match.equipe2.lieux_preferes:
            for rang, gymnase in enumerate(match.equipe2.lieux_preferes):
                if gymnase == creneau.gymnase and rang < len(self.config.bonus_preferences_gymnases):
                    penalty -= self.config.bonus_preferences_gymnases[rang]
                    break
        
        return penalty
    
    def _calculer_penalite_niveau_gymnase(self, match: Match, creneau: Creneau) -> float:
        """
        Calcule la pénalité pour les niveaux de gymnase.
        
        Pénalise les assignations inappropriées de matchs selon le niveau du gymnase.
        Valeurs positives = pénalité (augmente le coût, à éviter).
        
        Args:
            match: Le match à planifier
            creneau: Le créneau candidat
            
        Returns:
            Pénalité finale (valeur positive = pénalité, 0 = neutre)
        """
        if not self.config.penalite_niveau_gymnases_haut or not self.config.penalite_niveau_gymnases_bas or not self.niveaux_gymnases:
            return 0.0
        
        # Déterminer le niveau du match
        niveau_match = self._get_niveau_match(match)
        if niveau_match is None:
            return 0.0
        
        # Récupérer le niveau du gymnase
        niveau_gymnase = self.niveaux_gymnases.get(creneau.gymnase)
        if not niveau_gymnase:
            return 0.0
        
        # Calculer la pénalité selon le niveau du gymnase et du match
        penalite = 0.0
        if niveau_gymnase == 'Haut niveau' and niveau_match < len(self.config.penalite_niveau_gymnases_haut):
            penalite = self.config.penalite_niveau_gymnases_haut[niveau_match]
        elif niveau_gymnase == 'Bas niveau' and niveau_match < len(self.config.penalite_niveau_gymnases_bas):
            penalite = self.config.penalite_niveau_gymnases_bas[niveau_match]
        
        return penalite  # Retourne directement la pénalité (positif = mauvais)
    
    def solve(self, matchs: List[Match], creneaux: List[Creneau], 
             gymnases: Dict[str, Gymnase], obligations_presence: Dict[str, str] = {}, 
             matchs_fixes: Optional[List[Match]] = None) -> Solution:
        """Solve using greedy algorithm with multiple attempts.
        
        Args:
            matchs: List of matches to schedule
            creneaux: List of available time slots
            gymnases: Dict of venues
            obligations_presence: Équipes qui doivent jouer dans un gymnase spécifique
            matchs_fixes: Fixed matches (already scheduled) to consider for penalties
            
        Returns:
            Best solution found
        """
        self.validator = self._build_validator()
        
        if obligations_presence:
            self.validator.add_constraint(VenuePresenceObligationConstraint(
                obligations=obligations_presence,
                weight=self.config.poids_indisponibilite
            ))
        
        # Les matchs fixés ne doivent pas être dans la liste matchs (ils sont déjà exclus par le pipeline)
        # Mais on les utilise pour initialiser le solution_state
        matchs_fixes_list = matchs_fixes or []
        
        best_solution = None
        best_score = float('inf')
        
        for essai in range(self.config.nb_essais):
            if self.config.afficher_progression and self.config.niveau_log >= 1:
                print(f"  Essai {essai + 1}/{self.config.nb_essais}...", end=" ")
            
            solution = self._solve_once(matchs.copy(), creneaux.copy(), gymnases, matchs_fixes_list)
            
            if solution.est_complete() or solution.score < best_score:
                best_solution = solution
                best_score = solution.score
            
            if self.config.afficher_progression and self.config.niveau_log >= 1:
                print(f"{solution.taux_planification():.1f}% planifié")
            
            if solution.est_complete():
                break
        
        return best_solution
    
    def _solve_once(self, matchs: List[Match], creneaux: List[Creneau], 
                   gymnases: Dict[str, Gymnase], matchs_fixes: Optional[List[Match]] = None) -> Solution:
        """Single greedy solve attempt.
        
        Args:
            matchs: Matches to schedule
            creneaux: Available time slots
            gymnases: Dict of venues
            matchs_fixes: Fixed matches (already scheduled) to consider for penalties
        """
        
        # Trier les matchs pour placer les ententes en dernier (priorité plus faible)
        if self.config.entente_actif:
            matchs_normaux = [m for m in matchs if not self._est_entente(m)]
            matchs_ententes = [m for m in matchs if self._est_entente(m)]
            random.shuffle(matchs_normaux)
            random.shuffle(matchs_ententes)
            matchs = matchs_normaux + matchs_ententes
        else:
            random.shuffle(matchs)
        
        random.shuffle(creneaux)
        
        # Créer l'état initial en incluant les matchs fixés
        solution_state = self._create_solution_state(matchs_fixes or [])
        matchs_planifies = []
        matchs_non_planifies = []
        total_penalty = 0.0
        
        for match in matchs:
            best_creneau = None
            best_penalty = float('inf')
            
            for creneau in creneaux:
                if match.creneau:
                    break
                
                # Vérifier la contrainte semaine_min (ne pas planifier avant cette semaine)
                if creneau.semaine < self.config.semaine_min:
                    continue
                
                # Vérifier la contrainte temporelle
                if not self._respecte_contrainte_temporelle(match, creneau):
                    if self.config.contrainte_temporelle_dure:
                        # Mode dur: bloquer ce placement
                        continue
                    else:
                        # Mode souple: on peut placer mais avec pénalité
                        pass  # La pénalité sera ajoutée après
                
                is_valid, penalty = self.validator.validate_assignment(match, creneau, solution_state)
                
                # Ajouter la pénalité pour contrainte temporelle violée (mode souple)
                if self.config.contrainte_temporelle_actif and not self._respecte_contrainte_temporelle(match, creneau):
                    penalty += self.config.contrainte_temporelle_penalite
                
                # Ajouter la pénalité pour les préférences de gymnase
                penalty_gymnase = self._calculer_penalite_gymnase(match, creneau)
                penalty += penalty_gymnase
                
                # Ajouter la pénalité/bonus pour les niveaux de gymnase
                penalty_niveau = self._calculer_penalite_niveau_gymnase(match, creneau)
                penalty += penalty_niveau
                
                if is_valid and penalty < best_penalty:
                    best_creneau = creneau
                    best_penalty = penalty
            
            if best_creneau:
                match.creneau = best_creneau
                self._update_solution_state(solution_state, match, best_creneau)
                matchs_planifies.append(match)
                total_penalty += best_penalty
                
                # Pénalité pour compaction temporelle (prioriser début de calendrier)
                if self.config.compaction_temporelle_actif:
                    semaine = best_creneau.semaine
                    # Récupérer la pénalité pour cette semaine (indice 0 = semaine 1)
                    if semaine <= len(self.config.compaction_penalites_par_semaine):
                        penalty_compaction = self.config.compaction_penalites_par_semaine[semaine - 1]
                    else:
                        # Si on dépasse le nb de semaines définies, utiliser la dernière pénalité
                        penalty_compaction = self.config.compaction_penalites_par_semaine[-1]
                    total_penalty += penalty_compaction
                
                # Pénalité pour overlaps d'institution/équipe (matchs simultanés dans un groupe de non-simultanéité)
                if self.config.overlap_institution_actif:
                    # Vérifier si d'autres matchs partageant un groupe sont déjà planifiés au même moment
                    key_creneau = (best_creneau.semaine, best_creneau.horaire, best_creneau.gymnase)
                    
                    for autre_match in matchs_planifies[:-1]:  # Tous sauf le dernier (celui qu'on vient d'ajouter)
                        if autre_match.creneau:
                            key_autre = (autre_match.creneau.semaine, autre_match.creneau.horaire, 
                                       autre_match.creneau.gymnase)
                            if key_creneau == key_autre:
                                # Vérifier si les matchs partagent un groupe de non-simultanéité
                                if self._matchs_partagent_groupe_non_simultaneite(match, autre_match):
                                    total_penalty += self.config.overlap_institution_poids
                
                # Pénalité pour espacement aller-retour (si poules de type Aller-Retour)
                if self.config.aller_retour_espacement_actif:
                    for autre_match in matchs_planifies[:-1]:  # Tous sauf le dernier (celui qu'on vient d'ajouter)
                        if autre_match.creneau and self._sont_matchs_aller_retour(match, autre_match):
                            semaine_diff = abs(best_creneau.semaine - autre_match.creneau.semaine)
                            
                            if semaine_diff == 0:
                                # Même semaine: pénalité très élevée
                                total_penalty += self.config.aller_retour_penalite_meme_semaine
                            elif semaine_diff == 1:
                                # Semaines consécutives: pénalité modérée
                                total_penalty += self.config.aller_retour_penalite_consecutives
                
                # NE PLUS SUPPRIMER LE CRÉNEAU: la contrainte VenueCapacityConstraint
                # s'occupe de bloquer les créneaux qui ont atteint leur capacité maximale
                # creneaux.remove(best_creneau)  # SUPPRIMÉ - Permet la réutilisation des créneaux
            else:
                matchs_non_planifies.append(match)
        
        return Solution(
            matchs_planifies=matchs_planifies,
            matchs_non_planifies=matchs_non_planifies,
            score=total_penalty,
            metadata={'solver': 'greedy'}
        )
    
    def _sont_matchs_aller_retour(self, match1: Match, match2: Match) -> bool:
        """
        Vérifie si deux matchs sont une paire aller-retour.
        
        Une paire aller-retour a les mêmes équipes mais dans l'ordre inverse:
        - Match aller: Équipe A vs Équipe B
        - Match retour: Équipe B vs Équipe A
        
        Args:
            match1: Premier match
            match2: Deuxième match
            
        Returns:
            True si c'est une paire aller-retour, False sinon
        """
        return (match1.equipe1.nom == match2.equipe2.nom and
                match1.equipe2.nom == match2.equipe1.nom and
                match1.equipe1.genre == match2.equipe2.genre and
                match1.equipe2.genre == match2.equipe1.genre and
                match1.poule == match2.poule)
    
    def _matchs_partagent_groupe_non_simultaneite(self, match1: Match, match2: Match) -> bool:
        """
        Vérifie si deux matchs partagent une entité (institution ou équipe) 
        dans les groupes de non-simultanéité configurés.
        
        Args:
            match1: Premier match
            match2: Deuxième match
            
        Returns:
            True si les matchs doivent être soumis à la contrainte de non-simultanéité
        """
        if not self.groupes_non_simultaneite:
            # Mode legacy : appliquer à toutes les institutions
            inst1 = {match1.equipe1.institution, match1.equipe2.institution}
            inst2 = {match2.equipe1.institution, match2.equipe2.institution}
            return bool(inst1 & inst2)
        
        # Mode configuré : vérifier si les matchs partagent une entité dans un groupe
        # Créer les ensembles d'entités pour chaque match (institutions + noms équipes)
        entites1 = {
            match1.equipe1.institution,
            match1.equipe2.institution,
            match1.equipe1.nom,
            match1.equipe2.nom
        }
        
        entites2 = {
            match2.equipe1.institution,
            match2.equipe2.institution,
            match2.equipe1.nom,
            match2.equipe2.nom
        }
        
        # Vérifier si les matchs partagent une entité dans un des groupes
        for groupe_entites in self.groupes_non_simultaneite.values():
            # Entités du match1 qui sont dans ce groupe
            entites1_dans_groupe = entites1 & groupe_entites
            # Entités du match2 qui sont dans ce groupe
            entites2_dans_groupe = entites2 & groupe_entites
            
            # Si les deux matchs ont au moins une entité dans ce groupe
            if entites1_dans_groupe and entites2_dans_groupe:
                return True
        
        return False
    
    def get_name(self) -> str:
        return "Greedy"
