"""
Module de calcul des pénalités pour un match planifié.

Permet de calculer rétrospectivement les pénalités d'un match déjà planifié,
utile pour le filtrage de qualité et l'analyse.
"""

import logging
from typing import Dict, List, Set, Optional
from datetime import time

from .models import Match, Creneau, Equipe
from .config import Config

logger = logging.getLogger(__name__)


class PenaltyCalculator:
    """Calcule les pénalités détaillées pour les matchs planifiés."""
    
    def __init__(self, config: Config, all_matches: List[Match] = None, niveaux_gymnases: Dict[str, str] = None):
        self.config = config
        self.all_matches = all_matches or []
        self.niveaux_gymnases = niveaux_gymnases or {}
        
    def calculate_match_penalties(self, match: Match) -> Dict[str, float]:
        """
        Calcule toutes les pénalités d'un match planifié.
        
        Args:
            match: Match à analyser (doit être planifié avec un créneau)
            
        Returns:
            Dict avec le détail des pénalités par catégorie
        """
        if not match.est_planifie():
            return {}
        
        penalties = {}
        creneau = match.creneau
        
        # 1. Horaires préférés
        penalties['horaire_prefere'] = self._calculate_preferred_time_penalty(match, creneau)
        
        # 2. Préférences de gymnase (bonus négatif = pénalité positive)
        penalties['gymnase_prefere'] = self._calculate_gym_preference_penalty(match, creneau)
        
        # 3. Niveau de gymnase
        penalties['niveau_gymnase'] = self._calculate_gym_level_penalty(match, creneau)
        
        # 4. Espacement des matchs (si d'autres matchs planifiés fournis)
        if self.all_matches:
            penalties['espacement'] = self._calculate_spacing_penalty(match)
        
        # 5. Compaction temporelle
        if self.config.compaction_temporelle_actif:
            penalties['compaction'] = self._calculate_compaction_penalty(creneau)
        
        # 6. Overlaps d'institution
        if self.config.overlap_institution_actif and self.all_matches:
            penalties['overlap'] = self._calculate_overlap_penalty(match)
        
        # 7. Aller-retour espacement (si autres matchs fournis)
        if self.config.aller_retour_espacement_actif and self.all_matches:
            penalties['aller_retour'] = self._calculate_aller_retour_penalty(match)
        
        # 8. Contraintes temporelles (soft)
        if self.config.contrainte_temporelle_actif and not self.config.contrainte_temporelle_dure:
            penalties['contrainte_temporelle'] = self._calculate_contrainte_temporelle_penalty(match, creneau)
        
        # Total
        penalties['total'] = sum(v for v in penalties.values() if isinstance(v, (int, float)))
        
        return penalties
    
    def _calculate_preferred_time_penalty(self, match: Match, creneau: Creneau) -> float:
        """Calcule la pénalité liée aux horaires préférés."""
        penalty = 0.0
        
        horaire_creneau = self._parse_time(creneau.horaire)
        
        for equipe in [match.equipe1, match.equipe2]:
            if not hasattr(equipe, 'horaires_preferes') or not equipe.horaires_preferes:
                continue
                
            horaire_prefere = self._parse_time(equipe.horaires_preferes[0])
            
            if horaire_creneau > horaire_prefere:
                # Après horaire préféré
                diff_minutes = (horaire_creneau.hour * 60 + horaire_creneau.minute) - \
                              (horaire_prefere.hour * 60 + horaire_prefere.minute)
                
                if diff_minutes > self.config.penalite_horaire_tolerance:
                    diff_penalisable = diff_minutes - self.config.penalite_horaire_tolerance
                    penalty += (diff_penalisable / self.config.penalite_horaire_diviseur) * \
                              self.config.penalite_apres_horaire_min
                              
            elif horaire_creneau < horaire_prefere:
                # Avant horaire préféré
                diff_minutes = (horaire_prefere.hour * 60 + horaire_prefere.minute) - \
                              (horaire_creneau.hour * 60 + horaire_creneau.minute)
                
                if diff_minutes > self.config.penalite_horaire_tolerance:
                    diff_penalisable = diff_minutes - self.config.penalite_horaire_tolerance
                    penalty += (diff_penalisable / self.config.penalite_horaire_diviseur) * \
                              self.config.penalite_avant_horaire_min
        
        return penalty
    
    def _calculate_gym_preference_penalty(self, match: Match, creneau: Creneau) -> float:
        """Calcule la pénalité/bonus pour les préférences de gymnase."""
        penalty = 0.0
        
        if not self.config.bonus_preferences_gymnases:
            return 0.0
        
        # Pénalité de base = 2x le bonus maximum
        base_penalty = 2 * max(self.config.bonus_preferences_gymnases)
        
        for equipe in [match.equipe1, match.equipe2]:
            if not hasattr(equipe, 'lieux_preferes') or not equipe.lieux_preferes:
                # Pas de préférences = pénalité de base complète
                penalty += base_penalty
                continue
            
            # Chercher le gymnase dans les préférences
            equipe_penalty = base_penalty
            for rang, lieu in enumerate(equipe.lieux_preferes):
                if lieu == creneau.gymnase and rang < len(self.config.bonus_preferences_gymnases):
                    # Bonus trouvé = réduction de la pénalité
                    equipe_penalty -= self.config.bonus_preferences_gymnases[rang]
                    break
            
            penalty += equipe_penalty
        
        return penalty
    
    def _calculate_gym_level_penalty(self, match: Match, creneau: Creneau) -> float:
        """Calcule la pénalité pour le niveau de gymnase."""
        if not self.niveaux_gymnases:
            return 0.0
        
        # Extraire le niveau du match depuis la poule (A1, A2, etc.)
        niveau_match = self._get_niveau_match(match)
        if niveau_match is None:
            return 0.0
        
        # Obtenir le niveau du gymnase (haut/bas)
        niveau_gymnase = self.niveaux_gymnases.get(creneau.gymnase)
        if not niveau_gymnase:
            return 0.0
        
        # Appliquer la pénalité selon la configuration
        if niveau_gymnase == "haut" and self.config.penalite_niveau_gymnases_haut:
            if niveau_match < len(self.config.penalite_niveau_gymnases_haut):
                penalty = self.config.penalite_niveau_gymnases_haut[niveau_match]
                # Bonus négatif = pénalité nulle ou négative (avantage)
                return max(0.0, penalty)
        
        elif niveau_gymnase == "bas" and self.config.penalite_niveau_gymnases_bas:
            if niveau_match < len(self.config.penalite_niveau_gymnases_bas):
                penalty = self.config.penalite_niveau_gymnases_bas[niveau_match]
                return max(0.0, penalty)
        
        return 0.0
    
    def _get_niveau_match(self, match: Match) -> Optional[int]:
        """
        Extrait le niveau du match depuis le nom de la poule.
        
        Returns:
            Index du niveau (A1=0, A2=1, A3=2, A4=3, etc.) ou None si impossible
        """
        poule = match.poule
        if not poule:
            return None
        
        # Format attendu: "A1", "A2", "A3", "A4"
        if poule.startswith('A') and len(poule) >= 2:
            try:
                niveau = int(poule[1])
                return niveau - 1  # A1 → 0, A2 → 1, etc.
            except ValueError:
                pass
        
        return None
    
    def _calculate_spacing_penalty(self, match: Match) -> float:
        """Calcule la pénalité d'espacement."""
        penalty = 0.0
        
        if not match.creneau:
            return 0.0
        
        semaine_match = match.creneau.semaine
        
        # Vérifier pour chaque équipe
        for equipe in [match.equipe1, match.equipe2]:
            # Trouver les autres matchs de cette équipe
            matchs_equipe = [
                m for m in self.all_matches 
                if m != match and m.est_planifie() and 
                (m.equipe1.id_unique == equipe.id_unique or 
                 m.equipe2.id_unique == equipe.id_unique)
            ]
            
            for autre_match in matchs_equipe:
                semaine_diff = abs(semaine_match - autre_match.creneau.semaine)
                
                if semaine_diff < len(self.config.penalites_espacement_repos):
                    penalty += self.config.penalites_espacement_repos[semaine_diff]
        
        return penalty
    
    def _calculate_compaction_penalty(self, creneau: Creneau) -> float:
        """Calcule la pénalité de compaction temporelle."""
        semaine = creneau.semaine
        
        if semaine <= len(self.config.compaction_penalites_par_semaine):
            return self.config.compaction_penalites_par_semaine[semaine - 1]
        else:
            return self.config.compaction_penalites_par_semaine[-1]
    
    def _calculate_overlap_penalty(self, match: Match) -> float:
        """Calcule la pénalité d'overlap institutionnel."""
        penalty = 0.0
        
        if not match.creneau:
            return 0.0
        
        key_creneau = (match.creneau.semaine, match.creneau.horaire, match.creneau.gymnase)
        
        for autre_match in self.all_matches:
            if autre_match == match or not autre_match.est_planifie():
                continue
            
            key_autre = (autre_match.creneau.semaine, autre_match.creneau.horaire, 
                        autre_match.creneau.gymnase)
            
            if key_creneau == key_autre:
                # Vérifier si partagent une institution
                inst1 = {match.equipe1.institution, match.equipe2.institution}
                inst2 = {autre_match.equipe1.institution, autre_match.equipe2.institution}
                
                if inst1 & inst2:  # Intersection non vide
                    penalty += self.config.overlap_institution_poids
        
        return penalty
    
    def _parse_time(self, time_str: str) -> time:
        """Parse une chaîne d'horaire en objet time."""
        try:
            parts = time_str.split(':')
            return time(int(parts[0]), int(parts[1]) if len(parts) > 1 else 0)
        except (ValueError, AttributeError):
            return time(14, 0)  # Défaut: 14h
    
    def _calculate_aller_retour_penalty(self, match: Match) -> float:
        """
        Calcule la pénalité d'espacement aller-retour.
        
        Vérifie si le match fait partie d'une paire aller-retour et si oui,
        applique les pénalités selon l'espacement des semaines.
        """
        penalty = 0.0
        
        if not match.creneau or not self.all_matches:
            return 0.0
        
        # Trouver le match retour (équipes inversées)
        for autre_match in self.all_matches:
            if autre_match == match or not autre_match.est_planifie() or not autre_match.creneau:
                continue
            
            # Vérifier si c'est le match retour
            if (match.equipe1.id_unique == autre_match.equipe2.id_unique and
                match.equipe2.id_unique == autre_match.equipe1.id_unique and
                match.poule == autre_match.poule):
                
                semaine_diff = abs(match.creneau.semaine - autre_match.creneau.semaine)
                
                # Pénalité si même semaine
                if semaine_diff == 0:
                    penalty += self.config.aller_retour_penalite_meme_semaine
                
                # Pénalité si semaines consécutives
                elif semaine_diff == 1:
                    penalty += self.config.aller_retour_penalite_consecutives
                
                # Note: pour violations entre 2 et min_semaines, on pourrait interpoler
                # mais le solveur n'a que les deux pénalités ci-dessus
                
                break
        
        return penalty
    
    def _calculate_contrainte_temporelle_penalty(self, match: Match, creneau: Creneau) -> float:
        """
        Calcule la pénalité de contrainte temporelle (soft).
        
        Si une contrainte temporelle existe pour le match et n'est pas respectée,
        applique la pénalité configurée.
        """
        penalty = 0.0
        
        # Vérifier s'il y a une contrainte temporelle sur ce match
        contrainte = self._get_contrainte_temporelle(match)
        if not contrainte:
            return 0.0
        
        # Vérifier si la contrainte est respectée
        if not contrainte.est_respectee(creneau.semaine):
            penalty = self.config.contrainte_temporelle_penalite
        
        return penalty
    
    def _get_contrainte_temporelle(self, match: Match) -> Optional[object]:
        """
        Récupère la contrainte temporelle associée au match.
        
        Note: Implémentation simplifiée - nécessite accès aux contraintes du solveur.
        """
        # Vérifier si le match a une contrainte dans ses métadonnées
        if hasattr(match, 'metadata') and 'contrainte_temporelle' in match.metadata:
            return match.metadata['contrainte_temporelle']
        return None
    
    def _calculate_guidance_qualite_penalty(self, match: Match, creneau: Creneau) -> float:
        """
        Calcule la pénalité de guidance qualité.
        
        Combine les pénalités statiques (horaire, gymnase, niveau) pour détecter
        les créneaux intrinsèquement mauvais et ajouter une grosse pénalité dissuasive.
        """
        # Estimation statique combinée
        penalty_horaire = self._calculate_preferred_time_penalty(match, creneau)
        penalty_gymnase = self._calculate_gym_preference_penalty(match, creneau)
        penalty_niveau = self._calculate_gym_level_penalty(match, creneau)
        
        estimation_totale = penalty_horaire + penalty_gymnase + penalty_niveau
        
        # Seuil = 50% du seuil qualité configuré
        seuil_estimation = self.config.qualite_match_seuil * 0.5
        
        # Si l'estimation dépasse le seuil, retourner la pénalité de guidance
        if estimation_totale > seuil_estimation:
            return 100000  # Grosse pénalité dissuasive
        
        return 0.0
    
    def annotate_matches_with_penalties(self, matches: List[Match]):
        """
        Ajoute les pénalités dans les métadonnées de chaque match.
        
        Modifie les matchs en place en ajoutant match.metadata['penalties'].
        """
        for match in matches:
            if match.est_planifie():
                penalties = self.calculate_match_penalties(match)
                if 'penalties' not in match.metadata:
                    match.metadata['penalties'] = penalties
                else:
                    match.metadata['penalties'].update(penalties)


def annotate_solution_with_penalties(solution, config: Config, niveaux_gymnases: Dict[str, str] = None):
    """
    Fonction utilitaire pour annoter tous les matchs d'une solution avec leurs pénalités.
    
    Args:
        solution: Solution à annoter
        config: Configuration
        niveaux_gymnases: Mapping gymnase → niveau ("haut" ou "bas"), optionnel
    """
    niveaux = niveaux_gymnases or {}
    calculator = PenaltyCalculator(config, solution.matchs_planifies, niveaux)
    calculator.annotate_matches_with_penalties(solution.matchs_planifies)
