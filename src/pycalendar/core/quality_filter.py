"""
Module de filtrage de qualité des matchs.

Ce module permet de retirer les matchs planifiés avec des pénalités trop élevées,
indiquant qu'ils sont placés dans des conditions trop contraignantes pour les équipes.
"""

import logging
from typing import List, Tuple, Dict
from dataclasses import dataclass

from .models import Match
from .config import Config

logger = logging.getLogger(__name__)


@dataclass
class RejectionReason:
    """Raison du rejet d'un match."""
    match_id: str
    equipe1: str
    equipe2: str
    penalite_totale: float
    seuil: float
    penalties_detail: Dict[str, float]


class QualityFilter:
    """Filtre les matchs selon leur qualité (niveau de pénalités)."""
    
    def __init__(self, config: Config):
        self.config = config
        self.rejections: List[RejectionReason] = []
    
    def filter_matches(self, matches: List[Match]) -> Tuple[List[Match], List[Match]]:
        """
        Sépare les matchs en deux groupes: acceptables et rejetés.
        
        Args:
            matches: Liste des matchs planifiés
            
        Returns:
            Tuple (matchs_acceptables, matchs_rejetes)
        """
        if not self.config.qualite_match_actif:
            logger.debug("Filtrage de qualité désactivé")
            return matches, []
        
        seuil = self.config.qualite_match_seuil
        matchs_ok = []
        matchs_rejetes = []
        self.rejections = []
        
        for match in matches:
            penalite_totale = self._compute_total_penalty(match)
            
            if penalite_totale > seuil:
                # Rejet
                matchs_rejetes.append(match)
                
                # Enregistrer la raison
                reason = RejectionReason(
                    match_id=getattr(match, 'match_id', 'unknown'),
                    equipe1=match.equipe1.nom if hasattr(match, 'equipe1') else str(match),
                    equipe2=match.equipe2.nom if hasattr(match, 'equipe2') else str(match),
                    penalite_totale=penalite_totale,
                    seuil=seuil,
                    penalties_detail=self._get_penalties_detail(match)
                )
                self.rejections.append(reason)
                
                # Log si activé
                if self.config.qualite_match_log_rejets:
                    self._log_rejection(reason)
            else:
                # Acceptable
                matchs_ok.append(match)
        
        # Résumé
        if matchs_rejetes:
            logger.info(
                f"🚫 Filtrage qualité: {len(matchs_rejetes)} match(s) rejeté(s) "
                f"sur {len(matches)} (seuil: {seuil:.0f})"
            )
            
            # Statistiques par raison principale
            if self.config.qualite_match_log_rejets:
                self._log_statistics()
        else:
            logger.debug(f"✅ Tous les matchs respectent le seuil de qualité ({seuil:.0f})")
        
        return matchs_ok, matchs_rejetes
    
    def _compute_total_penalty(self, match: Match) -> float:
        """Calcule la pénalité totale d'un match."""
        # Vérifier dans les métadonnées (peut être ajouté par les exporters)
        if hasattr(match, 'metadata') and isinstance(match.metadata, dict):
            if 'penalties' in match.metadata:
                penalties = match.metadata['penalties']
                if isinstance(penalties, dict):
                    if 'total' in penalties:
                        return penalties['total']
                    # Calculer la somme
                    return sum(v for k, v in penalties.items() if isinstance(v, (int, float)))
            
            # Chercher une clé spécifique
            if 'penalty_total' in match.metadata:
                return match.metadata['penalty_total']
        
        # Si le match n'est pas planifié, pénalité = 0 (sera accepté)
        if not match.est_planifie():
            logger.debug(f"Match non planifié {match}, considéré comme acceptable")
            return 0.0
        
        # Si aucune info disponible, log et considérer comme acceptable
        # (Le filtrage ne s'appliquera qu'aux matchs avec pénalités calculées)
        logger.debug(
            f"Impossible de calculer les pénalités pour le match {match}, "
            f"accepté par défaut (ajoutez 'penalties' dans metadata pour le filtrer)"
        )
        return 0.0
    
    def _get_penalties_detail(self, match: Match) -> Dict[str, float]:
        """Récupère le détail des pénalités d'un match."""
        if hasattr(match, 'metadata') and isinstance(match.metadata, dict):
            if 'penalties' in match.metadata:
                penalties = match.metadata['penalties']
                if isinstance(penalties, dict):
                    # Exclure 'total' pour ne garder que les détails
                    return {k: v for k, v in penalties.items() 
                           if k != 'total' and isinstance(v, (int, float))}
        return {}
    
    def _log_rejection(self, reason: RejectionReason):
        """Log les détails d'un rejet."""
        logger.warning(
            f"⚠️  Match rejeté: {reason.equipe1} vs {reason.equipe2}\n"
            f"   Pénalité totale: {reason.penalite_totale:.0f} > seuil: {reason.seuil:.0f}\n"
            f"   Détails: {self._format_penalties(reason.penalties_detail)}"
        )
    
    def _format_penalties(self, penalties: Dict[str, float]) -> str:
        """Formate les pénalités pour l'affichage."""
        if not penalties:
            return "{}"
        
        items = [f"{k}: {v:.0f}" for k, v in sorted(penalties.items(), key=lambda x: -x[1])]
        return "{ " + ", ".join(items) + " }"
    
    def _log_statistics(self):
        """Affiche des statistiques sur les raisons de rejet."""
        if not self.rejections:
            return
        
        # Compter les raisons principales (pénalité dominante)
        raisons_principales = {}
        
        for rejection in self.rejections:
            if rejection.penalties_detail:
                # Trouver la pénalité la plus élevée
                raison_max = max(rejection.penalties_detail.items(), key=lambda x: x[1])
                raison_nom = raison_max[0]
                raisons_principales[raison_nom] = raisons_principales.get(raison_nom, 0) + 1
        
        if raisons_principales:
            logger.info("📊 Raisons principales de rejet:")
            for raison, count in sorted(raisons_principales.items(), key=lambda x: -x[1]):
                logger.info(f"   • {raison}: {count} match(s)")
    
    def get_rejection_report(self) -> str:
        """Génère un rapport détaillé des rejets."""
        if not self.rejections:
            return "Aucun match rejeté pour qualité insuffisante."
        
        lines = [
            f"\n{'='*80}",
            f"RAPPORT DE FILTRAGE QUALITÉ - {len(self.rejections)} match(s) rejeté(s)",
            f"Seuil: {self.config.qualite_match_seuil:.0f}",
            f"{'='*80}\n"
        ]
        
        for i, rejection in enumerate(self.rejections, 1):
            lines.append(f"{i}. {rejection.equipe1} vs {rejection.equipe2}")
            lines.append(f"   Pénalité: {rejection.penalite_totale:.0f} (seuil: {rejection.seuil:.0f})")
            lines.append(f"   Détail: {self._format_penalties(rejection.penalties_detail)}\n")
        
        return "\n".join(lines)


def filter_low_quality_matches(
    matches_planned: List[Match],
    matches_unplanned: List[Match],
    config: Config
) -> Tuple[List[Match], List[Match]]:
    """
    Fonction utilitaire pour filtrer les matchs de mauvaise qualité.
    
    Args:
        matches_planned: Matchs planifiés à filtrer
        matches_unplanned: Matchs non planifiés existants
        config: Configuration
        
    Returns:
        Tuple (matchs_planifies_ok, matchs_non_planifies_total)
    """
    if not config.qualite_match_actif:
        return matches_planned, matches_unplanned
    
    quality_filter = QualityFilter(config)
    matchs_ok, matchs_rejetes = quality_filter.filter_matches(matches_planned)
    
    # Fusionner les matchs rejetés avec les non planifiés
    matchs_non_planifies_total = matches_unplanned + matchs_rejetes
    
    return matchs_ok, matchs_non_planifies_total
