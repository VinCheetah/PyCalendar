"""Core data models for sports scheduling."""

from dataclasses import dataclass, field
from typing import List, Set, Tuple, Optional, Dict
from datetime import time


@dataclass
class Equipe:
    """Represents a sports team."""
    nom: str
    poule: str
    institution: str = ""
    numero_equipe: str = ""
    genre: str = ""  # M (Masculin), F (Féminin), ou vide si non défini
    horaires_preferes: List[str] = field(default_factory=list)
    lieux_preferes: List[Optional[str]] = field(default_factory=list)  # Peut contenir None pour préserver les rangs
    semaines_indisponibles: Dict[int, Set[str]] = field(default_factory=dict)
    
    @property
    def nom_complet(self) -> str:
        """Returns full team name: institution (numero).
        
        Le genre n'est pas inclus dans le nom d'affichage mais est utilisé
        pour la différenciation interne des équipes (hash et égalité).
        """
        if self.numero_equipe:
            return f"{self.institution} ({self.numero_equipe})"
        return self.institution if self.institution else self.nom
    
    def __hash__(self):
        # Inclure le genre dans le hash pour permettre des équipes avec même nom mais genre différent
        return hash((self.nom, self.genre))
    
    def __eq__(self, other):
        # Deux équipes sont égales si elles ont le même nom ET le même genre
        return isinstance(other, Equipe) and self.nom == other.nom and self.genre == other.genre
    
    def est_disponible(self, semaine: int, horaire: Optional[str] = None) -> bool:
        """
        Vérifie si l'équipe est disponible pour une semaine et un horaire donnés.
        
        Args:
            semaine: Numéro de la semaine
            horaire: Créneau horaire (optionnel). Si None, vérifie si toute la semaine est disponible.
        
        Returns:
            True si l'équipe est disponible, False sinon
        """
        if semaine not in self.semaines_indisponibles:
            return True
        
        # Si aucun horaire spécifique n'est demandé, vérifier s'il existe des créneaux dispo
        if horaire is None:
            return False  # Si la semaine est dans indisponibles, considérer comme indisponible
        
        # Vérifier si l'horaire spécifique est indisponible
        return horaire not in self.semaines_indisponibles[semaine]
    
    @property
    def id_unique(self) -> str:
        """Returns unique identifier including genre to distinguish teams with same name.
        
        Format: "NOM|GENRE" (ex: "LYON 1 (1)|M" ou "LYON 1 (1)|F")
        """
        return f"{self.nom}|{self.genre}"


@dataclass(frozen=True)
class Creneau:
    """Represents a time slot (week + time + venue)."""
    semaine: int
    horaire: str
    gymnase: str
    
    def __repr__(self):
        return f"S{self.semaine}_{self.gymnase}_{self.horaire}"


@dataclass
class Gymnase:
    """Represents a sports venue."""
    nom: str
    capacite: int = 1
    horaires_disponibles: List[str] = field(default_factory=list)
    semaines_indisponibles: Dict[int, Set[str]] = field(default_factory=dict)
    # Nouvelle structure pour capacité partielle : {semaine: {horaire: capacite_reduite}}
    capacite_reduite: Dict[int, Dict[str, int]] = field(default_factory=dict)
    
    def est_disponible(self, semaine: int, horaire: str) -> bool:
        """Vérifie si le gymnase est disponible (pas dans indisponibilités complètes)."""
        if semaine in self.semaines_indisponibles:
            return horaire not in self.semaines_indisponibles[semaine]
        return True
    
    def get_capacite_disponible(self, semaine: int, horaire: str) -> int:
        """
        Retourne la capacité disponible pour un créneau donné.
        
        Returns:
            Capacité disponible (0 = indisponible, capacite = pleinement disponible)
        """
        # Si complètement indisponible
        if not self.est_disponible(semaine, horaire):
            return 0
        
        # Si capacité réduite définie
        if semaine in self.capacite_reduite:
            if horaire in self.capacite_reduite[semaine]:
                return self.capacite_reduite[semaine][horaire]
        
        # Sinon, capacité complète
        return self.capacite
    
    def __hash__(self):
        return hash(self.nom)


@dataclass
class Match:
    """Represents a match between two teams."""
    equipe1: Equipe
    equipe2: Equipe
    poule: str
    creneau: Optional[Creneau] = None
    priorite: int = 0
    est_fixe: bool = False  # Si True, le match ne peut pas être replanifié par le solver
    statut: str = "a_planifier"  # "a_planifier", "planifie", "fixe", "termine", "annule"
    score_equipe1: Optional[int] = None  # Score de l'équipe 1 (si match terminé)
    score_equipe2: Optional[int] = None  # Score de l'équipe 2 (si match terminé)
    notes: str = ""  # Notes libres sur le match
    
    def get_equipes_tuple(self) -> Tuple[str, str]:
        equipes = sorted([self.equipe1.nom_complet, self.equipe2.nom_complet])
        return (equipes[0], equipes[1])
    
    @property
    def est_planifie(self) -> bool:
        """Retourne True si le match a un créneau assigné."""
        return self.creneau is not None and self.creneau.semaine is not None
    
    def est_modifiable(self) -> bool:
        """Retourne True si le match peut être replanifié (pas fixe, pas terminé/annulé)."""
        if self.est_fixe:
            return False
        if self.statut in ["fixe", "termine", "annule"]:
            return False
        return True
    
    def __repr__(self):
        creneau_str = str(self.creneau) if self.creneau else "Non planifié"
        fixe_str = " [FIXÉ]" if self.est_fixe else ""
        return f"{self.equipe1.nom_complet} vs {self.equipe2.nom_complet} [{creneau_str}]{fixe_str}"


@dataclass
class Solution:
    """Represents a complete scheduling solution."""
    matchs_planifies: List[Match] = field(default_factory=list)
    matchs_non_planifies: List[Match] = field(default_factory=list)
    score: float = 0.0
    metadata: Dict = field(default_factory=dict)
    
    def taux_planification(self) -> float:
        total = len(self.matchs_planifies) + len(self.matchs_non_planifies)
        return len(self.matchs_planifies) / total * 100 if total > 0 else 0.0
    
    def est_complete(self) -> bool:
        return len(self.matchs_non_planifies) == 0
    
    def get_matchs_par_semaine(self) -> Dict[int, List[Match]]:
        matchs_par_semaine = {}
        for match in self.matchs_planifies:
            if match.creneau:
                semaine = match.creneau.semaine
                if semaine not in matchs_par_semaine:
                    matchs_par_semaine[semaine] = []
                matchs_par_semaine[semaine].append(match)
        return matchs_par_semaine


@dataclass
class ContrainteTemporelle:
    """Represents a temporal constraint on a match (before/after a specific week).
    
    Used for specific matches that must be scheduled before or after a certain week
    (e.g., CFE matches that shouldn't be played too early in the season).
    """
    type_contrainte: str  # "Avant" ou "Apres"
    semaine_limite: int  # Semaine limite (1-52)
    horaires_possibles: Optional[List[str]] = None
    
    def est_respectee(self, semaine_match: int) -> bool:
        """Check if constraint is respected for given match week.
        
        Uses LARGE inequalities:
        - "Avant": semaine_match <= semaine_limite (includes limit week)
        - "Apres": semaine_match >= semaine_limite (includes limit week)
        
        Args:
            semaine_match: Week number where match is scheduled
            
        Returns:
            True if constraint is respected, False otherwise
        """
        if self.type_contrainte == "Avant":
            return semaine_match <= self.semaine_limite
        elif self.type_contrainte == "Apres":
            return semaine_match >= self.semaine_limite
        else:
            # Type invalide, considérer comme respectée
            return True
