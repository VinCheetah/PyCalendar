"""
Module de calcul des pénalités pour un match planifié.

Permet de calculer rétrospectivement les pénalités d'un match déjà planifié,
utile pour le filtrage de qualité et l'analyse.
"""

import logging
from typing import Any, Dict, List, Set, Optional

from .models import Match, Creneau, Equipe
from .config import Config
from .penalties import (
    compute_time_preference_penalty,
    compute_gym_preference_penalty,
    compute_gym_level_penalty,
    compute_gym_gender_priority_penalty,
    compaction_penalty_for_week,
    spacing_penalty_for_gap,
    aller_retour_gap_penalty,
    is_retour_match,
)

logger = logging.getLogger(__name__)


class PenaltyCalculator:
    """Calcule les pénalités détaillées pour les matchs planifiés."""
    
    def __init__(
        self,
        config: Config,
        all_matches: Optional[List[Match]] = None,
        niveaux_gymnases: Optional[Dict[str, str]] = None,
        priorites_genre_gymnases: Optional[Dict[str, str]] = None,
    ):
        self.config = config
        self.all_matches = all_matches or []
        self.niveaux_gymnases = self._normalize_levels(niveaux_gymnases or {})
        self.priorites_genre_gymnases = self._normalize_priorities(priorites_genre_gymnases or {})

    @staticmethod
    def _normalize_levels(levels: Dict[str, str]) -> Dict[str, str]:
        normalized = {}
        for gym, value in levels.items():
            if not value:
                continue
            text = str(value).strip().lower()
            if 'haut' in text:
                normalized[gym] = 'haut'
            elif 'bas' in text:
                normalized[gym] = 'bas'
            else:
                normalized[gym] = text
        return normalized

    @staticmethod
    def _normalize_priorities(priorities: Dict[str, str]) -> Dict[str, str]:
        normalized = {}
        for gym, value in priorities.items():
            if not value:
                continue
            genre = str(value).strip().upper()
            if genre in {'M', 'F'}:
                normalized[gym] = genre
        return normalized
        
    def calculate_match_penalties(self, match: Match) -> Dict[str, float]:
        """Retourne le détail des pénalités associées à un match planifié."""
        if not match.est_planifie():
            return {}

        penalties: Dict[str, float] = {}
        creneau = match.creneau
        if not creneau:
            return {}

        # 1. Horaires
        time_ctx = compute_time_preference_penalty(match, creneau, self.config)
        penalties['horaire_prefere'] = time_ctx.penalty
        penalties['horaire_prefere_equipes_avant'] = time_ctx.equipes_avant
        penalties['horaire_prefere_equipes_apres'] = time_ctx.equipes_apres

        # 2. Gymnases
        penalties['gymnase_prefere'] = compute_gym_preference_penalty(match, creneau, self.config)
        penalties['niveau_gymnase'] = compute_gym_level_penalty(match, creneau, self.config, self.niveaux_gymnases)
        penalties['priorite_genre_gymnase'] = compute_gym_gender_priority_penalty(
            match,
            creneau,
            self.config,
            self.priorites_genre_gymnases,
        )

        # 3. Espacement
        if self.all_matches:
            penalties['espacement'] = self._calculate_spacing_penalty(match)

        # 4. Compaction
        if self.config.compaction_temporelle_actif and creneau:
            penalties['compaction'] = compaction_penalty_for_week(self.config, creneau.semaine)

        # 5. Overlaps institutionnels
        if self.config.overlap_institution_actif and self.all_matches:
            penalties['overlap'] = self._calculate_overlap_penalty(match)

        # 6. Aller / Retour
        if self.config.aller_retour_espacement_actif and self.all_matches:
            penalties['aller_retour'] = self._calculate_aller_retour_penalty(match)

        # 7. Contraintes temporelles souples
        if self.config.contrainte_temporelle_actif and not self.config.contrainte_temporelle_dure:
            penalties['contrainte_temporelle'] = self._calculate_contrainte_temporelle_penalty(match, creneau)

        penalties['total'] = sum(v for v in penalties.values() if isinstance(v, (int, float)))
        return penalties

    def _calculate_spacing_penalty(self, match: Match) -> float:
        if not match.creneau:
            return 0.0

        penalty = 0.0
        semaine_match = match.creneau.semaine

        for equipe in (match.equipe1, match.equipe2):
            autres = [
                m for m in self.all_matches
                if m != match
                and m.est_planifie()
                and (m.equipe1.id_unique == equipe.id_unique or m.equipe2.id_unique == equipe.id_unique)
            ]

            for autre_match in autres:
                if not autre_match.creneau:
                    continue
                semaine_autre = autre_match.creneau.semaine
                if semaine_autre <= semaine_match:
                    continue
                weeks_rest = max(0, semaine_autre - semaine_match - 1)
                penalty += spacing_penalty_for_gap(self.config, weeks_rest)

        return penalty
    
    def _calculate_overlap_penalty(self, match: Match) -> float:
        """Calcule la pénalité d'overlap institutionnel."""
        penalty = 0.0
        
        if not match.creneau:
            return 0.0
        
        key_creneau = (match.creneau.semaine, match.creneau.horaire, match.creneau.gymnase)
        
        for autre_match in self.all_matches:
            if autre_match == match or not autre_match.est_planifie() or not autre_match.creneau:
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
    
    def _calculate_aller_retour_penalty(self, match: Match) -> float:
        """
        Calcule la pénalité d'espacement aller-retour.
        
        Vérifie si le match fait partie d'une paire aller-retour et si oui,
        applique les pénalités selon l'espacement des semaines.
        """
        penalty = 0.0
        
        if not match.creneau or not self.all_matches:
            return 0.0
        
        is_retour = is_retour_match(match)
        ordre_penalite = getattr(self.config, "aller_retour_penalite_ordre_retour", 0.0) or 0.0

        # Trouver le match opposé (aller ↔ retour)
        for autre_match in self.all_matches:
            if autre_match == match or not autre_match.est_planifie() or not autre_match.creneau:
                continue

            if (
                match.equipe1.id_unique == autre_match.equipe2.id_unique
                and match.equipe2.id_unique == autre_match.equipe1.id_unique
                and match.poule == autre_match.poule
            ):
                semaine_diff = abs(match.creneau.semaine - autre_match.creneau.semaine)
                penalty += aller_retour_gap_penalty(self.config, semaine_diff)

                if is_retour and match.creneau.semaine <= autre_match.creneau.semaine and ordre_penalite > 0:
                    penalty += ordre_penalite
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
        if not contrainte.est_respectee(creneau.semaine):  # type: ignore[attr-defined]
            penalty = self.config.contrainte_temporelle_penalite
        
        return penalty
    
    def _get_contrainte_temporelle(self, match: Match) -> Optional[Any]:
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
        time_ctx = compute_time_preference_penalty(match, creneau, self.config)
        penalty_horaire = time_ctx.penalty
        penalty_gymnase = compute_gym_preference_penalty(match, creneau, self.config)
        penalty_niveau = compute_gym_level_penalty(match, creneau, self.config, self.niveaux_gymnases)
        
        estimation_totale = penalty_horaire + penalty_gymnase + penalty_niveau
        
        # Seuil = 50% du seuil qualité configuré
        qualite_seuil = getattr(self.config, 'qualite_match_seuil', 0)
        seuil_estimation = qualite_seuil * 0.5
        
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


def annotate_solution_with_penalties(
    solution,
    config: Config,
    niveaux_gymnases: Optional[Dict[str, str]] = None,
    priorites_genre_gymnases: Optional[Dict[str, str]] = None,
):
    """
    Fonction utilitaire pour annoter tous les matchs d'une solution avec leurs pénalités.
    
    Args:
        solution: Solution à annoter
        config: Configuration
        niveaux_gymnases: Mapping gymnase → niveau ("haut" ou "bas"), optionnel
        priorites_genre_gymnases: Mapping gymnase → genre prioritaire ("M" ou "F"), optionnel
    """
    niveaux = niveaux_gymnases or {}
    calculator = PenaltyCalculator(
        config,
        solution.matchs_planifies,
        niveaux_gymnases=niveaux,
        priorites_genre_gymnases=priorites_genre_gymnases or {},
    )
    calculator.annotate_matches_with_penalties(solution.matchs_planifies)
