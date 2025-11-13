"""Core data models for sports scheduling."""

from dataclasses import dataclass, field
from typing import List, Set, Tuple, Optional, Dict
from datetime import time


@dataclass
class Equipe:
    """Represents a sports team.
    
    CONVENTION IMPORTANTE pour le champ 'nom':
    - Le champ 'nom' doit TOUJOURS être SANS le suffixe de genre [M] ou [F]
    - Format attendu: "LYON 1 (1)", jamais "LYON 1 (1) [M]"
    - Le genre est stocké séparément dans le champ 'genre' ('M', 'F', ou '')
    - L'identifiant unique combinant nom et genre est disponible via la propriété 'id_unique'
    
    Cette convention garantit:
    - Cohérence dans toutes les recherches (indispos, dispos, contraintes)
    - Fonctionnement correct de __eq__ et __hash__ pour distinguer équipes M/F
    - Clés de dictionnaire prévisibles et fiables (format: "NOM|GENRE")
    """
    nom: str  # TOUJOURS sans genre: "LYON 1 (1)"
    poule: str
    institution: str = ""
    numero_equipe: str = ""
    genre: str = ""  # M (Masculin), F (Féminin), ou vide si non défini
    horaires_preferes: List[str] = field(default_factory=list)
    lieux_preferes: List[Optional[str]] = field(default_factory=list)  # Peut contenir None pour préserver les rangs
    semaines_indisponibles: Dict[int, Set[str]] = field(default_factory=dict)
    dispos_gymnases_specifiques: Dict[str, str] = field(default_factory=dict)  # {gymnase: horaire_dispo_anticipe}
    
    @property
    def nom_complet(self) -> str:
        """Returns full team name: institution (numero).
        
        Le genre n'est pas inclus dans le nom d'affichage mais est utilisé
        pour la différenciation interne des équipes (hash et égalité).
        
        IMPORTANT: Cette propriété retourne le nom SANS genre, conforme à la convention.
        Pour un identifiant incluant le genre, utilisez 'id_unique'.
        """
        if self.numero_equipe:
            return f"{self.institution} ({self.numero_equipe})"
        return self.institution if self.institution else self.nom
    
    def __hash__(self):
        # Inclure le genre dans le hash pour permettre des équipes avec même nom mais genre différent
        # Puisque self.nom est TOUJOURS sans genre, le hash (nom, genre) est toujours cohérent
        return hash((self.nom, self.genre))
    
    def __eq__(self, other):
        # Deux équipes sont égales si elles ont le même nom ET le même genre
        # Puisque self.nom est TOUJOURS sans genre, cette comparaison est toujours cohérente
        return isinstance(other, Equipe) and self.nom == other.nom and self.genre == other.genre
    
    def est_disponible(self, semaine: int, horaire: Optional[str] = None, gymnase: Optional[str] = None) -> bool:
        """
        Vérifie si l'équipe est disponible pour une semaine, un horaire et un gymnase donnés.
        
        Cette méthode vérifie uniquement les CONTRAINTES DURES d'indisponibilité, c'est-à-dire
        les créneaux où l'équipe NE PEUT PAS jouer (indisponibilités explicites).
        
        Les horaires préférés (horaires_preferes) sont des PRÉFÉRENCES SOUPLES gérées
        par PreferredTimeConstraint avec des pénalités, PAS des contraintes dures d'indisponibilité.
        
        Args:
            semaine: Numéro de la semaine
            horaire: Créneau horaire (optionnel). Si None, vérifie si toute la semaine est disponible.
            gymnase: Nom du gymnase (optionnel). Permet de vérifier les disponibilités anticipées.
        
        Returns:
            True si l'équipe est disponible (peut jouer), False sinon (indisponible)
            
        Note:
            - Les semaines_indisponibles sont des contraintes DURES (l'équipe ne peut pas jouer)
            - Les dispos_gymnases_specifiques sont aussi des contraintes DURES (horaire minimum sur gymnase)
            - Les horaires_preferes sont des PRÉFÉRENCES SOUPLES (géré par PreferredTimeConstraint)
        """
        # Vérifier d'abord les indisponibilités explicites (priorité absolue)
        if semaine in self.semaines_indisponibles:
            # Si aucun horaire spécifique n'est demandé, vérifier s'il existe des créneaux dispo
            if horaire is None:
                return False  # Si la semaine est dans indisponibles, considérer comme indisponible
            
            # Vérifier si l'horaire spécifique est indisponible
            if horaire in self.semaines_indisponibles[semaine]:
                # Debug: signaler qu'une indisponibilité bloque ce placement
                import logging
                logger = logging.getLogger(__name__)
                logger.debug(f"❌ INDISPO: {self.nom} [{self.genre}] indisponible S{semaine} {horaire}")
                return False
        
        # Si pas d'horaire spécifié, équipe est disponible (pas dans indisponibles)
        if horaire is None:
            return True
        
        # Vérifier les disponibilités anticipées sur gymnases spécifiques
        # Ces disponibilités anticipées sont des CONTRAINTES DURES (l'équipe ne peut pas jouer avant)
        if gymnase and gymnase in self.dispos_gymnases_specifiques:
            horaire_dispo_anticipe = self.dispos_gymnases_specifiques[gymnase]
            # L'équipe est disponible à partir de cet horaire sur ce gymnase
            return horaire >= horaire_dispo_anticipe
        
        # IMPORTANT: Les horaires préférés (horaires_preferes) sont des PRÉFÉRENCES SOUPLES,
        # pas des contraintes d'indisponibilité. Ils sont gérés par PreferredTimeConstraint
        # avec des pénalités, pas ici comme contraintes dures.
        # Par défaut, l'équipe est disponible si elle n'est pas explicitement indisponible
        return True
    
    @property
    def id_unique(self) -> str:
        """Returns unique identifier including genre to distinguish teams with same name.
        
        Format: "NOM|GENRE" (ex: "LYON 1 (1)|M" ou "LYON 1 (1)|F")
        
        IMPORTANT: Puisque self.nom est TOUJOURS sans genre (convention), cet identifiant
        est toujours cohérent et prévisible. Il est utilisé comme clé de dictionnaire dans
        les contraintes et l'état de la solution.
        
        Exemples:
        - Équipe masculine: id_unique = "LYON 1 (1)|M"
        - Équipe féminine: id_unique = "LYON 1 (1)|F"
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
    metadata: Dict = field(default_factory=dict)  # Métadonnées additionnelles (ex: matchs fixes)
    
    def get_equipes_tuple(self) -> Tuple[str, str]:
        equipes = sorted([self.equipe1.nom_complet, self.equipe2.nom_complet])
        return (equipes[0], equipes[1])
    
    def est_planifie(self) -> bool:
        return self.creneau is not None
    
    def __repr__(self):
        creneau_str = str(self.creneau) if self.creneau else "Non planifié"
        return f"{self.equipe1.nom_complet} vs {self.equipe2.nom_complet} [{creneau_str}]"


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
    horaires_possibles: Optional[List[str]] = None  # Horaires préférés (optionnel)
    
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
