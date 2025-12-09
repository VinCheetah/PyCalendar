"""
Schema de validation et documentation des structures de données PyCalendar.

Ce module sert à la fois de :
1. Documentation de référence pour toutes les structures de données
2. Validation automatique des types et formats
3. Source de vérité unique pour l'architecture des données

Usage:
    from pycalendar.core.data_schema import validate_equipe, validate_solution
    
    # Valider une structure
    errors = validate_equipe(equipe)
    if errors:
        print(f"Erreurs: {errors}")
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Any, Tuple
from enum import Enum


# ============================================================================
# ENUMS ET CONSTANTES
# ============================================================================

class TypePoule(Enum):
    """Types de poules possibles."""
    SIMPLE = "Simple"  # Matchs uniques
    ALLER_RETOUR = "Aller-Retour"  # Chaque paire joue 2 fois


class NiveauGymnase(Enum):
    """Niveaux de classification des gymnases."""
    HAUT = "haut"  # Gymnases de haut niveau (pour équipes A1, A2)
    BAS = "bas"    # Gymnases de bas niveau (pour équipes A3, A4)


# ============================================================================
# SCHEMA: Equipe
# ============================================================================

@dataclass
class EquipeSchema:
    """
    Schema de validation pour la classe Equipe.
    
    IMPORTANT: Convention de nommage
    - 'nom' doit TOUJOURS être SANS suffixe de genre [M] ou [F]
    - Format: "LYON 1 (1)", jamais "LYON 1 (1) [M]"
    - Le genre est stocké séparément dans 'genre'
    
    Champs obligatoires:
        nom (str): Nom de l'équipe SANS genre. Ex: "LYON 1 (1)"
        poule (str): Identifiant de la poule. Ex: "A1", "A2"
    
    Champs optionnels:
        institution (str): Nom de l'institution. Ex: "INSA", "ECL"
        numero_equipe (str): Numéro d'équipe. Ex: "1", "2"
        genre (str): Genre ('M', 'F', ou vide)
        horaires_preferes (List[str]): Horaires préférés. Format: ["HH:MM"]
        lieux_preferes (List[Optional[str]]): Gymnases préférés par ordre de préférence.
                                              Peut contenir None pour préserver les rangs.
        semaines_indisponibles (Dict[int, Set[str]]): {semaine: {horaires_indispo}}
        dispos_gymnases_specifiques (Dict[str, str]): {nom_gymnase: horaire_min_dispo}
    
    Propriétés calculées:
        nom_complet (str): "{institution} ({numero_equipe})"
        id_unique (str): "{nom}|{genre}" - Identifiant unique incluant genre
    
    Exemples:
        >>> equipe = Equipe(
        ...     nom="LYON 1 (1)",
        ...     poule="A1",
        ...     institution="INSA",
        ...     numero_equipe="1",
        ...     genre="M",
        ...     horaires_preferes=["18:00", "19:00"],
        ...     lieux_preferes=["Gymnase1", "Gymnase2", None]  # None préserve rang 3
        ... )
        >>> equipe.id_unique
        'LYON 1 (1)|M'
    
    Validation:
        - nom ne doit PAS contenir [M] ou [F]
        - genre doit être 'M', 'F', ou vide
        - horaires_preferes: format "HH:MM" (ex: "18:00")
        - semaines_indisponibles: semaine >= 1
    """
    
    # Obligatoires
    nom: str
    poule: str
    
    # Optionnels avec défauts
    institution: str = ""
    numero_equipe: str = ""
    genre: str = ""  # 'M', 'F', ou ''
    
    # Listes
    horaires_preferes: List[str] = field(default_factory=list)
    lieux_preferes: List[Optional[str]] = field(default_factory=list)
    
    # Dictionnaires
    semaines_indisponibles: Dict[int, Set[str]] = field(default_factory=dict)
    dispos_gymnases_specifiques: Dict[str, str] = field(default_factory=dict)


def validate_equipe(equipe) -> List[str]:
    """
    Valide une instance d'Equipe.
    
    Returns:
        Liste des erreurs (vide si valide)
    """
    errors = []
    
    # Vérifier que nom ne contient pas de genre
    if '[M]' in equipe.nom or '[F]' in equipe.nom:
        errors.append(f"nom contient genre: '{equipe.nom}' (devrait être sans [M]/[F])")
    
    # Vérifier genre valide
    if equipe.genre not in ('M', 'F', ''):
        errors.append(f"genre invalide: '{equipe.genre}' (attendu: 'M', 'F', ou '')")
    
    # Vérifier format horaires
    for horaire in equipe.horaires_preferes:
        if not isinstance(horaire, str) or ':' not in horaire:
            errors.append(f"horaire_prefere invalide: '{horaire}' (format attendu: 'HH:MM')")
    
    # Vérifier semaines >= 1
    for semaine in equipe.semaines_indisponibles.keys():
        if semaine < 1:
            errors.append(f"semaine_indisponible invalide: {semaine} (doit être >= 1)")
    
    return errors


# ============================================================================
# SCHEMA: Gymnase
# ============================================================================

@dataclass
class GymnaseSchema:
    """
    Schema de validation pour la classe Gymnase.
    
    Champs obligatoires:
        nom (str): Nom unique du gymnase. Ex: "Gymnase INSA", "Doua Sports"
    
    Champs optionnels:
        capacite (int): Nombre de matchs simultanés possibles. Défaut: 1
        horaires_disponibles (List[str]): Horaires où le gymnase est ouvert.
                                          Format: ["HH:MM"]
        semaines_indisponibles (Dict[int, Set[str]]): {semaine: {horaires_indispo}}
        capacite_reduite (Dict[int, Dict[str, int]]): {semaine: {horaire: capacite}}
    
    Méthodes importantes:
        est_disponible(semaine, horaire) -> bool: Vérifie disponibilité
        get_capacite_disponible(semaine, horaire) -> int: Capacité restante
    
    Exemples:
        >>> gymnase = Gymnase(
        ...     nom="Gymnase INSA",
        ...     capacite=2,
        ...     horaires_disponibles=["18:00", "19:00", "20:00"],
        ...     semaines_indisponibles={5: {"18:00"}},  # Indispo semaine 5 à 18h
        ...     capacite_reduite={3: {"19:00": 1}}  # Semaine 3 à 19h: capacité=1
        ... )
        >>> gymnase.est_disponible(5, "18:00")
        False
        >>> gymnase.get_capacite_disponible(3, "19:00")
        1
    
    Validation:
        - capacite >= 0
        - horaires_disponibles: format "HH:MM"
        - capacite_reduite <= capacite normale
    """
    
    nom: str
    capacite: int = 1
    horaires_disponibles: List[str] = field(default_factory=list)
    semaines_indisponibles: Dict[int, Set[str]] = field(default_factory=dict)
    capacite_reduite: Dict[int, Dict[str, int]] = field(default_factory=dict)


def validate_gymnase(gymnase) -> List[str]:
    """Valide une instance de Gymnase."""
    errors = []
    
    if gymnase.capacite < 0:
        errors.append(f"capacite invalide: {gymnase.capacite} (doit être >= 0)")
    
    for horaire in gymnase.horaires_disponibles:
        if not isinstance(horaire, str) or ':' not in horaire:
            errors.append(f"horaire_disponible invalide: '{horaire}'")
    
    for semaine, horaires_capa in gymnase.capacite_reduite.items():
        for horaire, capa in horaires_capa.items():
            if capa > gymnase.capacite:
                errors.append(f"capacite_reduite trop élevée S{semaine} {horaire}: {capa} > {gymnase.capacite}")

    return errors


# ============================================================================
# SCHEMA: Creneau
# ============================================================================

@dataclass(frozen=True)
class CreneauSchema:
    """
    Schema de validation pour la classe Creneau.
    
    IMPORTANT: Immuable (frozen=True)
    
    Champs obligatoires:
        semaine (int): Numéro de semaine. Ex: 1, 2, 3...
        horaire (str): Horaire du créneau. Format: "HH:MM"
        gymnase (str): Nom du gymnase (STRING, pas objet Gymnase!)
    
    ATTENTION CRITIQUE:
        - gymnase est un STRING (nom du gymnase)
        - PAS un objet Gymnase
        - Utiliser gymnase.nom va planter!
    
    Représentation:
        __repr__ retourne: "S{semaine}_{gymnase}_{horaire}"
    
    Exemples:
        >>> creneau = Creneau(semaine=5, horaire="18:00", gymnase="Gymnase INSA")
        >>> creneau.gymnase  # STRING
        'Gymnase INSA'
        >>> str(creneau)
        'S5_Gymnase INSA_18:00'
    
    Validation:
        - semaine >= 1
        - horaire format "HH:MM"
        - gymnase est un string (pas un objet)
    """
    
    semaine: int
    horaire: str
    gymnase: str  # ATTENTION: String, pas objet!


def validate_creneau(creneau) -> List[str]:
    """Valide une instance de Creneau."""
    errors = []
    
    if creneau.semaine < 1:
        errors.append(f"semaine invalide: {creneau.semaine} (doit être >= 1)")
    
    if not isinstance(creneau.horaire, str) or ':' not in creneau.horaire:
        errors.append(f"horaire invalide: '{creneau.horaire}' (format: 'HH:MM')")
    
    if not isinstance(creneau.gymnase, str):
        errors.append(f"gymnase invalide: type {type(creneau.gymnase)} (attendu: str)")
    
    return errors


# ============================================================================
# SCHEMA: Match
# ============================================================================

@dataclass
class MatchSchema:
    """
    Schema de validation pour la classe Match.
    
    Champs obligatoires:
        equipe1 (Equipe): Première équipe
        equipe2 (Equipe): Deuxième équipe
        poule (str): Identifiant de poule. Ex: "A1"
    
    Champs optionnels:
        creneau (Optional[Creneau]): Créneau assigné (None si non planifié)
        priorite (int): Priorité du match. Défaut: 0
        metadata (Dict): Données additionnelles
            - 'is_fixed' (bool): Match fixé manuellement
            - 'semaine' (int): Pour matchs fixes
            - 'horaire' (str): Pour matchs fixes
            - 'gymnase' (str): Pour matchs fixes
            - 'penalties' (Dict): Pénalités calculées (ajouté par PenaltyCalculator)
    
    Méthodes importantes:
        est_planifie() -> bool: True si creneau != None
        get_equipes_tuple() -> Tuple[str, str]: Noms triés des équipes
    
    Structure metadata['penalties']:
        {
            'horaire_prefere': float,     # Pénalité écart horaire préféré
            'gymnase_prefere': float,     # Pénalité gymnase non préféré
            'niveau_gymnase': float,      # Pénalité inadéquation niveau
            'espacement': float,          # Pénalité espacement entre matchs
            'compaction': float,          # Pénalité matchs trop rapprochés
            'overlap': float,             # Pénalité overlaps institutionnels
            'total': float                # Somme de toutes les pénalités
        }
    
    Exemples:
        >>> match = Match(equipe1=eq1, equipe2=eq2, poule="A1")
        >>> match.est_planifie()
        False
        >>> match.creneau = Creneau(semaine=1, horaire="18:00", gymnase="Gym1")
        >>> match.est_planifie()
        True
        >>> match.metadata['is_fixed'] = True
        >>> match.metadata['penalties'] = {'total': 125.5, ...}
    
    Validation:
        - equipe1 et equipe2 doivent être différentes
        - si creneau: doit être un Creneau valide
        - metadata['penalties']: doit contenir 'total' si présent
    """
    
    equipe1: Any  # Equipe
    equipe2: Any  # Equipe
    poule: str
    creneau: Optional[Any] = None  # Optional[Creneau]
    priorite: int = 0
    metadata: Dict = field(default_factory=dict)


def validate_match(match) -> List[str]:
    """Valide une instance de Match."""
    errors = []
    
    if match.equipe1 == match.equipe2:
        errors.append(f"equipe1 == equipe2: {match.equipe1.nom}")
    
    if match.creneau is not None:
        creneau_errors = validate_creneau(match.creneau)
        errors.extend([f"creneau.{e}" for e in creneau_errors])
    
    if 'penalties' in match.metadata:
        penalties = match.metadata['penalties']
        if 'total' not in penalties:
            errors.append("metadata['penalties'] manque 'total'")
    
    return errors


# ============================================================================
# SCHEMA: Solution
# ============================================================================

@dataclass
class SolutionSchema:
    """
    Schema de validation pour la classe Solution.
    
    Champs:
        matchs_planifies (List[Match]): Matchs avec créneau assigné
        matchs_non_planifies (List[Match]): Matchs sans créneau
        score (float): Score d'optimisation. Défaut: 0.0
        metadata (Dict): Métadonnées de la solution
    
    Méthodes importantes:
        taux_planification() -> float: Pourcentage de matchs planifiés
        est_complete() -> bool: True si tous les matchs sont planifiés
        get_matchs_par_semaine() -> Dict[int, List[Match]]
    
    Structure metadata:
        {
            'solver': str,              # Nom du solver utilisé
            'temps_resolution': float,  # Temps en secondes
            'statut': str,              # 'OPTIMAL', 'FEASIBLE', etc.
            'version': str              # Version format solution
        }
    
    Exemples:
        >>> solution = Solution(
        ...     matchs_planifies=[match1, match2],
        ...     matchs_non_planifies=[match3],
        ...     score=1234.5,
        ...     metadata={'solver': 'cpsat', 'statut': 'OPTIMAL'}
        ... )
        >>> solution.taux_planification()
        66.67
        >>> solution.est_complete()
        False
    
    Validation:
        - matchs_planifies: tous doivent avoir creneau != None
        - matchs_non_planifies: tous doivent avoir creneau == None
        - score >= 0 (si optimisation valide)
        - pas de doublons entre planifiés/non planifiés
    """
    
    matchs_planifies: List[Any] = field(default_factory=list)  # List[Match]
    matchs_non_planifies: List[Any] = field(default_factory=list)  # List[Match]
    score: float = 0.0
    metadata: Dict = field(default_factory=dict)


def validate_solution(solution) -> List[str]:
    """Valide une instance de Solution."""
    errors = []
    
    # Vérifier que matchs planifiés ont un créneau
    for i, match in enumerate(solution.matchs_planifies):
        if not match.est_planifie():
            errors.append(f"matchs_planifies[{i}] n'a pas de créneau: {match}")
    
    # Vérifier que matchs non planifiés n'ont pas de créneau
    for i, match in enumerate(solution.matchs_non_planifies):
        if match.est_planifie():
            errors.append(f"matchs_non_planifies[{i}] a un créneau: {match}")
    
    # Vérifier pas de doublons
    all_matches = solution.matchs_planifies + solution.matchs_non_planifies
    match_set = set()
    for match in all_matches:
        key = (match.equipe1.id_unique, match.equipe2.id_unique)
        if key in match_set or (key[1], key[0]) in match_set:
            errors.append(f"Match dupliqué: {match.equipe1.nom} vs {match.equipe2.nom}")
        match_set.add(key)
    
    return errors


# ============================================================================
# SCHEMA: Config
# ============================================================================

CONFIG_FIELDS_DOCUMENTATION = """
Configuration PyCalendar - Documentation des champs
===================================================

FICHIERS:
---------
fichier_donnees: str                # Chemin fichier Excel d'entrée
fichier_sortie: str                 # Chemin fichier Excel de sortie

PLANIFICATION:
--------------
nb_semaines: int                    # Nombre de semaines de compétition
semaine_min: int                    # Semaine de début (pour saisons commencées)
taille_poule_min: int              # Taille minimale d'une poule
taille_poule_max: int              # Taille maximale d'une poule

SOLVER:
-------
temps_max_secondes: int            # Timeout pour CP-SAT
cpsat_warm_start: bool             # Utiliser solution précédente
cpsat_warm_start_file: str         # Nom fichier solution (ex: 'volley')

PRÉFÉRENCES GYMNASE:
--------------------
bonus_preferences_gymnases: List[float]         # [bonus_rang1, rang2, ...]

PONDÉRATIONS NIVEAU GYMNASE (bonus/malus):
-----------------------------------------
poids_niveaux_gymnases_haut: List[float]       # Valeurs négatives = bonus pour alignement A1/A2 sur gym haut
poids_niveaux_gymnases_bas: List[float]        # Valeurs positives = pénalité pour matchs élevés sur gym bas (et inversement)

ESPACEMENT:
-----------
penalites_espacement_repos: List[float]        # Pénalité par semaines de repos

HORAIRES PRÉFÉRÉS:
------------------
penalite_apres_horaire_min: float              # Multiplicateur après horaire
penalite_avant_horaire_min: float              # Multiplicateur avant horaire
penalite_avant_horaire_min_deux: float         # Multiplicateur bien avant
penalite_horaire_diviseur: float               # Diviseur minutes
penalite_horaire_tolerance: float              # Tolérance minutes

COMPACTION TEMPORELLE:
----------------------
compaction_temporelle_actif: bool              # Activer contrainte
compaction_penalites_par_semaine: List[float]  # Pénalité par semaine

OVERLAP INSTITUTIONNEL:
-----------------------
overlap_institution_actif: bool                # Activer contrainte
overlap_institution_poids: float               # Poids pénalité
overlap_institution_institutions: List[str]    # Institutions surveillées

ÉQUILIBRAGE MATCHS:
-------------------
equilibrage_actif: bool                        # Système bonus progressif
equilibrage_bonus_base: float                  # Bonus 1er match
equilibrage_facteur_decroissance: float        # Multiplicateur suivants
equilibrage_bonus_minimum: float               # Bonus plancher

ENTENTES:
---------
entente_actif: bool                            # Activer gestion ententes
entente_penalite_non_planif: float            # Bonus réduit si non planifié
entente_facteur_reduction: float              # Facteur réduction (ex: 0.1)

QUALITÉ MATCHS (FILTRAGE):
--------------------------
qualite_match_actif: bool                      # Activer filtrage qualité
qualite_match_seuil: float                     # Pénalité max acceptable
qualite_match_guidance_cpsat: bool             # Guider CP-SAT
qualite_match_log_rejets: bool                 # Logs détaillés

CONTRAINTES TEMPORELLES:
------------------------
contrainte_temporelle_actif: bool              # Activer contraintes avant/après
contrainte_temporelle_penalite: float          # Pénalité si violé (mode souple)
contrainte_temporelle_dure: bool               # true=bloquant, false=pénalité

ALLER-RETOUR:
-------------
aller_retour_espacement_actif: bool            # Activer espacement A/R
aller_retour_penalites_par_ecart: List[float] # Liste pénalités par écart en semaines
aller_retour_bonus_retour: float              # Ratio bonus appliqué aux matchs retour

CALENDRIER:
-----------
calendrier_actif: bool                         # Afficher dates réelles
calendrier_date_debut: str                     # Date début (YYYY-MM-DD)
calendrier_jour_match: str                     # Jour matchs (ex: 'jeudi')
calendrier_semaines_banalisees: List[int]      # Semaines vacances

AVANCÉ:
-------
max_matchs_par_equipe_par_semaine: int        # Limite matchs/semaine
afficher_progression: bool                     # Afficher progression
niveau_log: int                                # Niveau logging (0-3)
solution_format: str                           # Format sortie ('v2.0')
"""


# ============================================================================
# UTILITAIRES DE VALIDATION
# ============================================================================

def validate_all(equipes=None, gymnases=None, matchs=None, solution=None) -> Dict[str, List[str]]:
    """
    Valide toutes les structures fournies.
    
    Args:
        equipes: Liste d'équipes à valider
        gymnases: Liste de gymnases à valider
        matchs: Liste de matchs à valider
        solution: Solution à valider
    
    Returns:
        Dict avec erreurs par catégorie:
        {
            'equipes': [...],
            'gymnases': [...],
            'matchs': [...],
            'solution': [...]
        }
    """
    results = {}
    
    if equipes:
        results['equipes'] = []
        for i, eq in enumerate(equipes):
            errors = validate_equipe(eq)
            if errors:
                results['equipes'].append(f"Equipe[{i}] {eq.nom}: {errors}")
    
    if gymnases:
        results['gymnases'] = []
        for i, gym in enumerate(gymnases):
            errors = validate_gymnase(gym)
            if errors:
                results['gymnases'].append(f"Gymnase[{i}] {gym.nom}: {errors}")
    
    if matchs:
        results['matchs'] = []
        for i, match in enumerate(matchs):
            errors = validate_match(match)
            if errors:
                results['matchs'].append(f"Match[{i}]: {errors}")
    
    if solution:
        results['solution'] = validate_solution(solution)
    
    return results


def print_validation_report(results: Dict[str, List[str]]):
    """Affiche un rapport de validation formaté."""
    total_errors = sum(len(errors) for errors in results.values())
    
    if total_errors == 0:
        print("✅ Toutes les validations ont réussi!")
        return
    
    print(f"⚠️  {total_errors} erreur(s) détectée(s):\n")
    
    for category, errors in results.items():
        if errors:
            print(f"  {category.upper()}:")
            for error in errors:
                print(f"    - {error}")
            print()


# ============================================================================
# EXEMPLES D'UTILISATION
# ============================================================================

if __name__ == "__main__":
    print(__doc__)
    print("\n" + "=" * 80)
    print("SCHÉMAS DE DONNÉES DISPONIBLES")
    print("=" * 80)
    
    schemas = [
        ("Equipe", EquipeSchema),
        ("Gymnase", GymnaseSchema),
        ("Creneau", CreneauSchema),
        ("Match", MatchSchema),
        ("Solution", SolutionSchema)
    ]
    
    for name, schema_class in schemas:
        print(f"\n{name}:")
        print(f"  Champs: {len(schema_class.__dataclass_fields__)}")
        print(f"  Validation: validate_{name.lower()}()")
    
    print("\n" + "=" * 80)
    print("CONFIGURATION")
    print("=" * 80)
    print(CONFIG_FIELDS_DOCUMENTATION)
