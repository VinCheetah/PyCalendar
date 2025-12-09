"""CP-SAT solver using OR-Tools."""

try:
    from ortools.sat.python import cp_model
    ORTOOLS_AVAILABLE = True
except ImportError:
    ORTOOLS_AVAILABLE = False

from typing import List, Dict, Optional, Set, Tuple
from pathlib import Path
from pycalendar.core.models import Match, Creneau, Gymnase, Solution, CoachGroup, Equipe
from pycalendar.core.config import Config
from pycalendar.core.penalties import (
    compute_time_preference_penalty,
    compute_gym_preference_penalty,
    compute_gym_level_penalty,
    compute_gym_gender_priority_penalty,
    spacing_penalty_for_gap,
    aller_retour_gap_penalty,
    compaction_penalty_for_week,
    horaire_to_minutes,
    is_retour_match,
)
from .base_solver import BaseSolver
from collections import defaultdict


class CPSATSolver(BaseSolver):
    """Optimal solver using CP-SAT (OR-Tools)."""
    
    def __init__(self, config: Config, groupes_non_simultaneite: Optional[Dict[str, Set[str]]] = None,
                 ententes: Optional[Dict] = None, contraintes_temporelles: Optional[Dict] = None,
                 niveaux_gymnases: Optional[Dict[str, str]] = None,
                 priorites_genre_gymnases: Optional[Dict[str, str]] = None,
                 coach_groups: Optional[Dict[str, CoachGroup]] = None):
        if not ORTOOLS_AVAILABLE:
            raise ImportError("OR-Tools not installed. Install with: pip install ortools")
        super().__init__(config)
        self.groupes_non_simultaneite = groupes_non_simultaneite or {}
        self.ententes = ententes or {}  # Dict avec paires d'institutions et leurs pénalités
        self.contraintes_temporelles = contraintes_temporelles or {}  # Dict avec paires d'équipes et leurs contraintes temporelles
        self.niveaux_gymnases = niveaux_gymnases or {}  # Dict avec niveaux des gymnases
        self.priorites_genre_gymnases = priorites_genre_gymnases or {}
        self.coach_groups = coach_groups or {}
    
    def _est_entente(self, match: Match) -> bool:
        """
        Vérifie si un match est une entente (paire d'institutions configurée).
        
        Returns:
            True si le match est une entente, False sinon
        """
        if not self.config.entente_actif or not self.ententes:
            return False
        
        inst1 = match.equipe1.institution
        inst2 = match.equipe2.institution
        
        # Créer clé triée pour détection bidirectionnelle
        cle = tuple(sorted([inst1, inst2]))
        
        return cle in self.ententes
    
    def _get_penalite_entente(self, match: Match) -> float:
        """
        Récupère le bonus réduit pour une entente (dans le cadre du système progressif).
        
        Dans le système progressif, les ententes reçoivent un bonus réduit par rapport
        aux matchs normaux, ce qui les rend moins prioritaires.
        
        Returns:
            Bonus spécifique (si défini dans Excel) ou bonus réduit calculé
        """
        inst1 = match.equipe1.institution
        inst2 = match.equipe2.institution
        cle = tuple(sorted([inst1, inst2]))
        
        # Vérifier si une pénalité spécifique est définie dans Excel
        penalite = self.ententes.get(cle)
        if penalite is not None:
            # Utiliser la valeur spécifique de l'Excel
            return penalite
        
        # Sinon, utiliser la pénalité par défaut du YAML
        # (sera utilisé si le système progressif est désactivé)
        return self.config.entente_penalite_non_planif
    
    def _calcul_bonus_progressif(self, n: int, est_entente: bool = False) -> int:
        """
        Calcule le bonus pour le n-ième match d'une équipe (système max-min fairness).
        
        Le bonus décroit exponentiellement selon la formule:
        bonus(n) = bonus_base × (facteur_decroissance ^ n)
        
        Pour les ententes, le bonus est réduit par le facteur_reduction.
        
        Args:
            n: Index du match (0 = premier match, 1 = deuxième match, etc.)
            est_entente: Si True, applique le facteur de réduction pour ententes
            
        Returns:
            Bonus entier pour ce match
            
        Exemple avec bonus_base=100000, facteur=0.5:
            n=0 (1er match): 100000
            n=1 (2ème match): 50000
            n=2 (3ème match): 25000
            n=3 (4ème match): 12500
            etc.
        """
        # Calculer le bonus de base avec décroissance exponentielle
        bonus = self.config.equilibrage_bonus_base * (self.config.equilibrage_facteur_decroissance ** n)
        
        # Appliquer le bonus minimum (éviter que le bonus ne devienne trop faible)
        bonus = max(bonus, self.config.equilibrage_bonus_minimum)
        
        return int(bonus)
    
    def _get_contrainte_temporelle(self, match: Match):
        """Retourne la contrainte temporelle applicable à ce match (si configurée)."""
        if not self.contraintes_temporelles:
            return None

        def _candidats(equipe: Equipe) -> Set[str]:
            candidats = set()
            if getattr(equipe, 'id_unique', None):
                candidats.add(equipe.id_unique)
            nom_sans_genre = (equipe.id_unique.split('|')[0] if getattr(equipe, 'id_unique', None) else equipe.nom)
            if nom_sans_genre:
                candidats.add(nom_sans_genre)
                candidats.add(nom_sans_genre.upper())
            if equipe.nom:
                candidats.add(equipe.nom)
                candidats.add(equipe.nom.upper())
            return {c for c in candidats if c}

        candidats_eq1 = _candidats(match.equipe1)
        candidats_eq2 = _candidats(match.equipe2)

        for id1 in candidats_eq1:
            for id2 in candidats_eq2:
                cle = tuple(sorted([id1, id2]))
                contrainte = self.contraintes_temporelles.get(cle)
                if contrainte:
                    return contrainte
        return None

    def _matchs_partagent_groupe_non_simultaneite(self, match1: Match, match2: Match) -> bool:
        """Vérifie si deux matchs partagent une entité d'un groupe de non-simultanéité."""
        if not self.groupes_non_simultaneite:
            return False

        def _collecte_entites(match: Match) -> Set[str]:
            entites: Set[str] = set()
            for equipe in (match.equipe1, match.equipe2):
                if equipe.id_unique:
                    entites.add(equipe.id_unique.lower())
                if equipe.nom:
                    entites.add(equipe.nom.lower())
                if equipe.institution:
                    entites.add(equipe.institution.lower())
            return entites

        entites1 = _collecte_entites(match1)
        entites2 = _collecte_entites(match2)

        for groupe_entites in self.groupes_non_simultaneite.values():
            groupe_normalise = {ent.lower() for ent in groupe_entites}
            if entites1 & groupe_normalise and entites2 & groupe_normalise:
                return True
        return False

    def _est_match_retour(self, match: Match) -> bool:
        """Détermine si le match correspond au retour (ordre inversé)."""
        return is_retour_match(match)
    
    def solve(self, matchs: List[Match], creneaux: List[Creneau], 
             gymnases: Dict[str, Gymnase], obligations_presence: Optional[Dict[str, str]] = None,
             use_warm_start: bool = True, solution_store = None, 
             matchs_fixes: Optional[List[Match]] = None) -> Solution:
        """
        Solve using CP-SAT constraint programming with optional warm start.
        
        Args:
            matchs: Liste des matchs à planifier
            creneaux: Liste des créneaux disponibles
            gymnases: Dictionnaire des gymnases
            obligations_presence: Contraintes de présence par gymnase
            use_warm_start: Si True, tente d'utiliser une solution précédente comme point de départ
            solution_store: Instance de SolutionStore (créée automatiquement si None)
            matchs_fixes: Matchs déjà planifiés/fixés (pour calcul des contraintes)
            
        Returns:
            Solution trouvée
        """
        
        if self.config.afficher_progression:
            print("CP-SAT solver - Création du modèle...")
        
        if obligations_presence is None:
            obligations_presence = {}
        
        # Compter les matchs fixes par équipe/semaine et par créneau
        # pour les contraintes de max matchs par semaine et capacité des gymnases
        matchs_fixes_par_equipe_semaine = {}
        matchs_fixes_par_creneau = {}  # Nouveau: compte matchs fixés par créneau (semaine, gymnase, horaire)
        if matchs_fixes:
            for match_fixe in matchs_fixes:
                if match_fixe.metadata and 'semaine' in match_fixe.metadata:
                    semaine = match_fixe.metadata['semaine']
                    # Compter par équipe/semaine
                    for equipe_id in [match_fixe.equipe1.id_unique, match_fixe.equipe2.id_unique]:
                        key = (equipe_id, semaine)
                        matchs_fixes_par_equipe_semaine[key] = matchs_fixes_par_equipe_semaine.get(key, 0) + 1
                    
                    # Compter par créneau pour gérer la capacité
                    if 'horaire' in match_fixe.metadata and 'gymnase' in match_fixe.metadata:
                        # Normaliser l'horaire (strip whitespace)
                        horaire_normalise = match_fixe.metadata['horaire'].strip()
                        gymnase_normalise = match_fixe.metadata['gymnase'].strip()
                        creneau_key = (semaine, gymnase_normalise, horaire_normalise)
                        matchs_fixes_par_creneau[creneau_key] = matchs_fixes_par_creneau.get(creneau_key, 0) + 1
        
        # Debug: afficher les matchs fixés par créneau
        if matchs_fixes_par_creneau and self.config.afficher_progression:
            print(f"\n📌 Matchs fixés détectés sur créneaux:")
            for key, count in matchs_fixes_par_creneau.items():
                semaine, gym, horaire = key
                print(f"   S{semaine}, {gym}, {horaire}: {count} match(s) fixé(s)")

        coaches_by_team = defaultdict(set)
        if self.coach_groups:
            for coach_name, group in self.coach_groups.items():
                for team_id in group.team_ids:
                    coaches_by_team[team_id].add(coach_name)

        coach_fixed_events = defaultdict(list)
        if self.config.coach_overlap_actif and coaches_by_team and matchs_fixes:
            semaine_min_coach = max(self.config.coach_overlap_semaine_min, self.config.semaine_min)
            for match_fixe in matchs_fixes:
                meta = match_fixe.metadata or {}
                semaine = meta.get('semaine')
                horaire = meta.get('horaire')
                gymnase = meta.get('gymnase')
                if semaine is None or horaire is None or gymnase is None:
                    continue
                try:
                    semaine_int = int(semaine)
                except (ValueError, TypeError):
                    continue
                if semaine_int < semaine_min_coach:
                    continue
                start_min = horaire_to_minutes(str(horaire))
                gym_nom = str(gymnase).strip()
                for equipe in [match_fixe.equipe1, match_fixe.equipe2]:
                    for coach_name in coaches_by_team.get(equipe.id_unique, []):
                        coach_fixed_events[coach_name].append({
                            'semaine': semaine_int,
                            'start': start_min,
                            'gymnase': gym_nom
                        })
        
        if obligations_presence is None:
            obligations_presence = {}
        
        model = cp_model.CpModel()
        
        assignment_vars = {}
        match_assigned = []
        entente_activated = {}  # Variables pour ententes activées (sans créneau)
        
        # Séparer matchs normaux et ententes
        matchs_normaux_indices = []
        matchs_ententes_indices = []
        
        for i, match in enumerate(matchs):
            if self._est_entente(match):
                matchs_ententes_indices.append(i)
            else:
                matchs_normaux_indices.append(i)
        
        aller_retour_pairs: List[Tuple[int, int]] = []
        aller_retour_fixed_pairs: List[Tuple[int, int]] = []  # (match_idx, semaine_fix)
        match_is_retour = [False] * len(matchs)
        paire_index = defaultdict(list)
        for idx in matchs_normaux_indices:
            match = matchs[idx]
            key = (match.poule, tuple(sorted([match.equipe1.id_unique, match.equipe2.id_unique])))
            paire_index[key].append(idx)

        fixed_allers = defaultdict(list)
        fixed_retours = defaultdict(list)
        if matchs_fixes:
            for match_fixe in matchs_fixes:
                meta = match_fixe.metadata or {}
                semaine = meta.get('semaine')
                if semaine is None:
                    continue
                try:
                    semaine_int = int(semaine)
                except (TypeError, ValueError):
                    continue
                key = (match_fixe.poule, tuple(sorted([match_fixe.equipe1.id_unique, match_fixe.equipe2.id_unique])))
                if self._est_match_retour(match_fixe):
                    fixed_retours[key].append(semaine_int)
                else:
                    fixed_allers[key].append(semaine_int)

        for key, indices in paire_index.items():
            allers = [i for i in indices if not self._est_match_retour(matchs[i])]
            retours = [i for i in indices if self._est_match_retour(matchs[i])]

            if allers and retours:
                for aller_idx, retour_idx in zip(sorted(allers), sorted(retours)):
                    if aller_idx == retour_idx:
                        continue
                    aller_retour_pairs.append((aller_idx, retour_idx))
                    match_is_retour[retour_idx] = True

            if allers:
                for semaine_fix in fixed_retours.get(key, []):
                    for aller_idx in allers:
                        aller_retour_fixed_pairs.append((aller_idx, semaine_fix))
            if retours:
                for semaine_fix in fixed_allers.get(key, []):
                    for retour_idx in retours:
                        aller_retour_fixed_pairs.append((retour_idx, semaine_fix))

        if self.config.afficher_progression:
            print(f"   → {len(matchs_normaux_indices)} matchs normaux à planifier")
            print(f"   → {len(matchs_ententes_indices)} ententes disponibles (fallback)")

        match_coachs = {i: set() for i in range(len(matchs))}
        if coaches_by_team:
            for i, match in enumerate(matchs):
                for equipe in [match.equipe1, match.equipe2]:
                    if equipe.id_unique in coaches_by_team:
                        match_coachs[i].update(coaches_by_team[equipe.id_unique])

        coach_match_indices = defaultdict(list)
        if coaches_by_team:
            for i in matchs_normaux_indices:
                for coach_name in match_coachs.get(i, []):
                    coach_match_indices[coach_name].append(i)
        
        # Filtrer les créneaux valides selon semaine_min
        creneaux_valides = [creneau for creneau in creneaux if creneau.semaine >= self.config.semaine_min]
        
        if self.config.afficher_progression:
            print(f"   → {len(creneaux_valides)} créneaux valides sur {len(creneaux)} total (semaine_min={self.config.semaine_min})")
        
        # Créer les variables pour TOUS les matchs (normaux + ententes)
        for i in range(len(matchs)):
            # Variable pour savoir si le match est assigné (planifié OU entente activée)
            assigned_var = model.NewBoolVar(f'match_{i}_assigned')
            match_assigned.append(assigned_var)
        
        # Variables pour MATCHS NORMAUX : assignation à créneaux
        for i in matchs_normaux_indices:
            for j, creneau in enumerate(creneaux_valides):
                var = model.NewBoolVar(f'match_{i}_creneau_{j}')
                assignment_vars[(i, j)] = var
            
            # CONTRAINTE: match normal assigné = somme des créneaux
            model.Add(sum(assignment_vars[(i, j)] for j in range(len(creneaux_valides))) == match_assigned[i])
        
        # Variables pour ENTENTES : activation sans créneau
        for i in matchs_ententes_indices:
            var = model.NewBoolVar(f'entente_{i}_activated')
            entente_activated[i] = var
            
            # CONTRAINTE: entente "assignée" = entente activée (pas de créneau)
            model.Add(entente_activated[i] == match_assigned[i])
        
        # CONTRAINTE 1bis: Interdiction stricte de jouer avant l'horaire préféré (optionnel)
        if self.config.horaire_avant_interdit:
            if self.config.afficher_progression:
                print(f"   → Contrainte DURE: Interdiction matchs avant horaire préféré (tolérance: {self.config.horaire_avant_tolerance}min)")
            
            # Appliquer uniquement aux matchs NORMAUX (les ententes n'ont pas de créneau)
            for i in matchs_normaux_indices:
                match = matchs[i]
                for j, creneau in enumerate(creneaux_valides):
                    # Vérifier si ce créneau viole la contrainte pour ce match
                    horaire_creneau_min = horaire_to_minutes(creneau.horaire)
                    violation = False
                    
                    for equipe in [match.equipe1, match.equipe2]:
                        if equipe.horaires_preferes:
                            horaire_prefere_min = horaire_to_minutes(equipe.horaires_preferes[0])
                            diff_minutes = horaire_creneau_min - horaire_prefere_min
                            
                            # Si avant (négatif) et au-delà de la tolérance
                            if diff_minutes < -self.config.horaire_avant_tolerance:
                                violation = True
                                break
                    
                    # Si violation, interdire cette assignation
                    if violation:
                        model.Add(assignment_vars[(i, j)] == 0)
        
        # CONTRAINTE 2: Capacité des gymnases (avec support de capacité réduite et matchs fixés)
        capacites_debug = []  # Pour debug
        for j in range(len(creneaux_valides)):
            creneau = creneaux_valides[j]
            gymnase = gymnases.get(creneau.gymnase)
            if gymnase:
                # Utiliser la capacité disponible (qui peut être réduite)
                capacite_disponible = gymnase.get_capacite_disponible(creneau.semaine, creneau.horaire)
                
                # Soustraire le nombre de matchs fixés déjà placés sur ce créneau
                # Normaliser pour assurer la correspondance
                creneau_key = (creneau.semaine, creneau.gymnase.strip(), creneau.horaire.strip())
                matchs_fixes_sur_creneau = matchs_fixes_par_creneau.get(creneau_key, 0)
                capacite_restante = capacite_disponible - matchs_fixes_sur_creneau
                
                # Debug
                if matchs_fixes_sur_creneau > 0:
                    capacites_debug.append({
                        'creneau': f"S{creneau.semaine}, {creneau.gymnase}, {creneau.horaire}",
                        'capacite_dispo': capacite_disponible,
                        'matchs_fixes': matchs_fixes_sur_creneau,
                        'capacite_restante': capacite_restante
                    })
                
                # S'assurer que la capacité restante est positive
                if capacite_restante > 0:
                    # Ne compter que les matchs NORMAUX (les ententes n'occupent pas de créneau)
                    model.Add(sum(assignment_vars[(i, j)] for i in matchs_normaux_indices if (i, j) in assignment_vars) <= capacite_restante)
                else:
                    # Pas de capacité restante, interdire tous les matchs normaux sur ce créneau
                    for i in matchs_normaux_indices:
                        if (i, j) in assignment_vars:
                            model.Add(assignment_vars[(i, j)] == 0)
        
        # Afficher le debug des capacités
        if capacites_debug and self.config.afficher_progression:
            print(f"\n🏟️  Capacités réduites par matchs fixés:")
            for info in capacites_debug:
                print(f"   {info['creneau']}: {info['capacite_dispo']} - {info['matchs_fixes']} = {info['capacite_restante']}")
        
        # CONTRAINTE 3: Disponibilité des équipes (DURE)
        # Vérifier la disponibilité avec le gymnase pour tenir compte des disponibilités anticipées
        # Appliquer uniquement aux matchs NORMAUX (les ententes n'ont pas de créneau)
        for i in matchs_normaux_indices:
            match = matchs[i]
            for j, creneau in enumerate(creneaux_valides):
                if not match.equipe1.est_disponible(creneau.semaine, creneau.horaire, creneau.gymnase):
                    model.Add(assignment_vars[(i, j)] == 0)
                if not match.equipe2.est_disponible(creneau.semaine, creneau.horaire, creneau.gymnase):
                    model.Add(assignment_vars[(i, j)] == 0)
        
        # CONTRAINTE 3bis: Contraintes temporelles (mode dur si activé)
        if self.config.contrainte_temporelle_actif and self.config.contrainte_temporelle_dure:
            # Appliquer uniquement aux matchs NORMAUX (les ententes n'ont pas de créneau)
            for i in matchs_normaux_indices:
                match = matchs[i]
                contrainte = self._get_contrainte_temporelle(match)
                if contrainte:
                    for j, creneau in enumerate(creneaux_valides):
                        # Si la contrainte n'est pas respectée, bloquer ce placement
                        if not contrainte.est_respectee(creneau.semaine):
                            model.Add(assignment_vars[(i, j)] == 0)
        
        # CONTRAINTE 4: Une équipe ne peut jouer qu'une fois par (semaine, horaire)
        # Grouper les créneaux valides par (semaine, horaire)
        creneaux_par_semaine_horaire = {}
        for j, creneau in enumerate(creneaux_valides):
            key = (creneau.semaine, creneau.horaire)
            if key not in creneaux_par_semaine_horaire:
                creneaux_par_semaine_horaire[key] = []
            creneaux_par_semaine_horaire[key].append(j)
        
        # Pour chaque équipe et chaque (semaine, horaire), elle ne joue qu'une fois
        # IMPORTANT: Utiliser id_unique pour distinguer les équipes de même nom mais genre différent
        equipes_uniques = set()
        for match in matchs:
            equipes_uniques.add(match.equipe1.id_unique)
            equipes_uniques.add(match.equipe2.id_unique)
        
        for equipe_id in equipes_uniques:
            for (semaine, horaire), indices_creneaux in creneaux_par_semaine_horaire.items():
                # Trouver tous les matchs NORMAUX où cette équipe joue à ce (semaine, horaire)
                vars_equipe = []
                for i in matchs_normaux_indices:
                    match = matchs[i]
                    if match.equipe1.id_unique == equipe_id or match.equipe2.id_unique == equipe_id:
                        for j in indices_creneaux:
                            if (i, j) in assignment_vars:
                                vars_equipe.append(assignment_vars[(i, j)])
                
                # L'équipe ne peut jouer qu'une fois à ce (semaine, horaire)
                if len(vars_equipe) > 1:
                    model.Add(sum(vars_equipe) <= 1)
        
        # CONTRAINTE 5: Max matchs par équipe par semaine
        max_matchs_semaine = self.config.max_matchs_par_equipe_par_semaine
        
        for equipe_id in equipes_uniques:
            for semaine in range(self.config.semaine_min, self.config.nb_semaines + 1):
                # Compter les matchs fixés déjà planifiés pour cette équipe/semaine
                matchs_fixes_count = matchs_fixes_par_equipe_semaine.get((equipe_id, semaine), 0)
                
                # Trouver tous les créneaux valides de cette semaine
                indices_semaine_valides = [j for j, c in enumerate(creneaux_valides) if c.semaine == semaine]
                
                # Trouver tous les matchs NORMAUX où cette équipe joue
                # Note: les ententes activées comptent aussi dans match_assigned mais pas ici
                vars_equipe_semaine = []
                for i in matchs_normaux_indices:
                    match = matchs[i]
                    if match.equipe1.id_unique == equipe_id or match.equipe2.id_unique == equipe_id:
                        for j in indices_semaine_valides:
                            if (i, j) in assignment_vars:
                                vars_equipe_semaine.append(assignment_vars[(i, j)])
                
                # Limiter le nombre de matchs (en tenant compte des matchs déjà fixés)
                if vars_equipe_semaine:
                    limite = max(0, max_matchs_semaine - matchs_fixes_count)
                    model.Add(sum(vars_equipe_semaine) <= limite)
        
        # CONTRAINTE 6: Obligations de présence
        # Appliquer uniquement aux matchs NORMAUX (les ententes n'ont pas de créneau)
        for i in matchs_normaux_indices:
            match = matchs[i]
            for j, creneau in enumerate(creneaux_valides):
                institution_requise = obligations_presence.get(creneau.gymnase)
                
                if institution_requise:
                    # Vérifier si au moins une équipe est de l'institution requise
                    inst1 = match.equipe1.institution
                    inst2 = match.equipe2.institution
                    
                    if institution_requise not in [inst1, inst2]:
                        # Interdire ce match à ce gymnase
                        model.Add(assignment_vars[(i, j)] == 0)
        
        # CONTRAINTE 7: Disponibilité des gymnases
        # Appliquer uniquement aux matchs NORMAUX (les ententes n'ont pas de gymnase)
        for i in matchs_normaux_indices:
            for j, creneau in enumerate(creneaux_valides):
                gymnase = gymnases.get(creneau.gymnase)
                if gymnase and not gymnase.est_disponible(creneau.semaine, creneau.horaire):
                    model.Add(assignment_vars[(i, j)] == 0)
        
        # ============================================================================
        # FONCTION OBJECTIF : SYSTÈME MAX-MIN AVEC BONUS PROGRESSIF
        # ============================================================================
        objective_terms = []
        
        if self.config.equilibrage_actif:
            # NOUVEAU SYSTÈME: Bonus progressif pour garantir max-min fairness
            # Principe: Chaque équipe reçoit un bonus décroissant pour chaque match planifié
            # Bonus 1er match > Bonus 2ème match > Bonus 3ème match, etc.
            # Cela garantit que le solver priorise donner 1 match à chaque équipe
            # avant de donner 2 matchs à qui que ce soit
            
            if self.config.afficher_progression:
                print("   → Utilisation du système de bonus progressif (max-min fairness)")
            
            # Compter les matchs DÉJÀ FIXÉS par équipe (CRUCIAL pour l'équilibrage)
            matchs_fixes_normaux_par_equipe = {}  # equipe_id -> nombre de matchs normaux déjà fixés
            matchs_fixes_ententes_par_equipe = {}  # equipe_id -> nombre de matchs ententes déjà fixés
            
            if matchs_fixes:
                for match_fixe in matchs_fixes:
                    eq1_id = match_fixe.equipe1.id_unique
                    eq2_id = match_fixe.equipe2.id_unique
                    est_entente = self._est_entente(match_fixe)
                    
                    # Choisir le bon dictionnaire selon le type
                    dict_cible = matchs_fixes_ententes_par_equipe if est_entente else matchs_fixes_normaux_par_equipe
                    
                    dict_cible[eq1_id] = dict_cible.get(eq1_id, 0) + 1
                    dict_cible[eq2_id] = dict_cible.get(eq2_id, 0) + 1
            
            # Grouper TOUS les matchs par équipe (normaux + ententes ensemble)
            matchs_par_equipe = {}  # equipe_id -> liste des indices de TOUS les matchs
            
            for i, match in enumerate(matchs):
                eq1_id = match.equipe1.id_unique
                eq2_id = match.equipe2.id_unique
                
                if eq1_id not in matchs_par_equipe:
                    matchs_par_equipe[eq1_id] = []
                if eq2_id not in matchs_par_equipe:
                    matchs_par_equipe[eq2_id] = []
                
                matchs_par_equipe[eq1_id].append(i)
                matchs_par_equipe[eq2_id].append(i)
            
            # NOUVEAU SYSTÈME: Bonus progressif UNIFIÉ pour chaque équipe
            # Le bonus total de l'équipe est réduit multiplicativement par (facteur ^ nb_ententes)
            for equipe_id, indices_matchs in matchs_par_equipe.items():
                nb_matchs_a_planifier = len(indices_matchs)
                
                # Compter matchs fixés (normaux + ententes)
                nb_fixes_normaux = matchs_fixes_normaux_par_equipe.get(equipe_id, 0)
                nb_fixes_ententes = matchs_fixes_ententes_par_equipe.get(equipe_id, 0)
                nb_matchs_total_fixes = nb_fixes_normaux + nb_fixes_ententes
                nb_matchs_total_possibles = nb_matchs_a_planifier + nb_matchs_total_fixes
                
                # Variable: nombre TOTAL de matchs planifiés (normaux + ententes activées)
                nb_planifies = model.NewIntVar(0, nb_matchs_a_planifier, f'nb_matchs_planifies_{equipe_id}')
                model.Add(nb_planifies == sum(match_assigned[i] for i in indices_matchs))
                
                # Variable: nombre d'ENTENTES activées pour cette équipe
                indices_ententes_equipe = [i for i in indices_matchs if i in matchs_ententes_indices]
                nb_ententes_activees = model.NewIntVar(0, len(indices_ententes_equipe), f'nb_ententes_{equipe_id}')
                if indices_ententes_equipe:
                    model.Add(nb_ententes_activees == sum(entente_activated[i] for i in indices_ententes_equipe))
                else:
                    model.Add(nb_ententes_activees == 0)
                
                # Total ententes (fixes + activées)
                nb_ententes_total = nb_fixes_ententes + nb_ententes_activees
                
                # Créer variables booléennes pour chaque seuil de bonus
                for seuil in range(1, nb_matchs_total_possibles + 1):
                    has_n_matchs = model.NewBoolVar(f'{equipe_id}_has_{seuil}_matchs')
                    
                    # Nombre de matchs à planifier pour atteindre ce seuil
                    nb_total_requis = seuil - nb_matchs_total_fixes
                    
                    if nb_total_requis <= 0:
                        # Seuil déjà atteint par matchs fixés
                        model.Add(has_n_matchs == 1)
                    elif nb_total_requis > nb_matchs_a_planifier:
                        # Impossible d'atteindre ce seuil
                        model.Add(has_n_matchs == 0)
                    else:
                        # Seuil atteignable
                        model.Add(nb_planifies >= nb_total_requis).OnlyEnforceIf(has_n_matchs)
                        model.Add(nb_planifies < nb_total_requis).OnlyEnforceIf(has_n_matchs.Not())
                    
                    # Bonus de base pour ce seuil (sans réduction)
                    bonus_base_seuil = self._calcul_bonus_progressif(seuil - 1, est_entente=False)
                    
                    # Appliquer réduction multiplicative basée sur nombre d'ententes
                    # Pour chaque nombre d'ententes possible (0, 1, 2, ...), créer une variable
                    # et appliquer le facteur de réduction correspondant
                    max_ententes_possibles = len(indices_ententes_equipe) + nb_fixes_ententes
                    
                    if max_ententes_possibles > 0:
                        # Créer des variables pour détecter le nombre exact d'ententes
                        for nb_ent in range(max_ententes_possibles + 1):
                            has_exact_n_ententes = model.NewBoolVar(f'{equipe_id}_has_exactly_{nb_ent}_ententes_at_seuil_{seuil}')
                            
                            # Contrainte: has_exact_n_ententes = 1 si nb_ententes_total == nb_ent
                            model.Add(nb_ententes_total == nb_ent).OnlyEnforceIf(has_exact_n_ententes)
                            model.Add(nb_ententes_total != nb_ent).OnlyEnforceIf(has_exact_n_ententes.Not())
                            
                            # Bonus réduit selon formule: bonus_base × (facteur ^ nb_ententes)
                            facteur_reduction = self.config.entente_facteur_reduction_bonus ** nb_ent
                            bonus_reduit = int(bonus_base_seuil * facteur_reduction)
                            
                            # Contribuer au bonus si ce seuil est atteint ET on a exactement nb_ent ententes
                            contrib_var = model.NewBoolVar(f'{equipe_id}_contrib_{seuil}_{nb_ent}ent')
                            model.Add(has_n_matchs + has_exact_n_ententes >= 2).OnlyEnforceIf(contrib_var)
                            model.Add(has_n_matchs + has_exact_n_ententes <= 1).OnlyEnforceIf(contrib_var.Not())
                            
                            objective_terms.append(bonus_reduit * contrib_var)
                    else:
                        # Pas d'ententes possibles, bonus complet
                        objective_terms.append(bonus_base_seuil * has_n_matchs)
        
        else:
            # ANCIEN SYSTÈME (désactivé par défaut): Bonus fixe par match
            # Conservé uniquement pour compatibilité si quelqu'un désactive le système progressif
            if self.config.afficher_progression:
                print("   ⚠️  Utilisation du système de bonus fixe (ancien système)")
            
            for i, match in enumerate(matchs):
                if self._est_entente(match):
                    # Match entente : bonus réduit
                    bonus = int(self._get_penalite_entente(match))
                else:
                    # Match normal : bonus fixe
                    bonus = int(self.config.equilibrage_bonus_base)
                objective_terms.append(bonus * match_assigned[i])

        retour_ratio = getattr(self.config, 'aller_retour_bonus_retour', 1.0) or 1.0
        if retour_ratio < 1.0:
            retour_penalty = int(self.config.equilibrage_bonus_base * max(0.0, 1.0 - retour_ratio))
            if retour_penalty > 0:
                for i in matchs_normaux_indices:
                    if match_is_retour[i]:
                        objective_terms.append(-retour_penalty * match_assigned[i])
        
        # Pénalités pour préférences horaires (sophistiquée avec distance)
        # Appliqué uniquement aux matchs normaux (ententes non assignées à créneaux)
        for i in matchs_normaux_indices:
            match = matchs[i]
            for j, creneau in enumerate(creneaux_valides):
                if (i, j) not in assignment_vars:
                    continue
                penalty_ctx = compute_time_preference_penalty(match, creneau, self.config)
                penalty = penalty_ctx.penalty
                if penalty > 0:
                    objective_terms.append(-int(penalty) * assignment_vars[(i, j)])
        
        # Pénalité pour contraintes temporelles violées (mode souple uniquement)
        # Appliqué uniquement aux matchs normaux
        if self.config.contrainte_temporelle_actif and not self.config.contrainte_temporelle_dure:
            for i in matchs_normaux_indices:
                match = matchs[i]
                contrainte = self._get_contrainte_temporelle(match)
                if contrainte:
                    for j, creneau in enumerate(creneaux_valides):
                        # Si la contrainte n'est pas respectée, ajouter une pénalité
                        if not contrainte.est_respectee(creneau.semaine) and (i, j) in assignment_vars:
                            penalty = int(self.config.contrainte_temporelle_penalite)
                            objective_terms.append(-penalty * assignment_vars[(i, j)])
        
        # Pénalités pour préférences de gymnases (système de bonus)
        # Appliqué uniquement aux matchs normaux
        if self.config.bonus_preferences_gymnases:
            for i in matchs_normaux_indices:
                match = matchs[i]
                for j, creneau in enumerate(creneaux_valides):
                    if (i, j) not in assignment_vars:
                        continue
                    penalty = compute_gym_preference_penalty(match, creneau, self.config)
                    if penalty != 0:
                        objective_terms.append(-int(penalty) * assignment_vars[(i, j)])
        
        # Pénalités pour gymnases par niveau (classification haut/bas niveau)
        # Applique une pénalité quand un match est assigné à un gymnase inapproprié
        # Appliqué uniquement aux matchs normaux
        # Valeurs positives = pénalité (augmente le coût, à éviter)
        poids_haut = (
            getattr(self.config, 'poids_niveaux_gymnases_haut', None)
            or getattr(self.config, 'penalite_niveau_gymnases_haut', [])
        )
        poids_bas = (
            getattr(self.config, 'poids_niveaux_gymnases_bas', None)
            or getattr(self.config, 'penalite_niveau_gymnases_bas', [])
        )

        if self.niveaux_gymnases and (poids_haut or poids_bas):
            for i in matchs_normaux_indices:
                match = matchs[i]
                for j, creneau in enumerate(creneaux_valides):
                    if (i, j) not in assignment_vars:
                        continue
                    penalite = compute_gym_level_penalty(match, creneau, self.config, self.niveaux_gymnases)
                    if penalite != 0:
                        objective_terms.append(-int(penalite) * assignment_vars[(i, j)])

        penalite_priorite_genre = getattr(self.config, 'penalite_gymnase_priorite_genre', 0.0) or 0.0
        if self.priorites_genre_gymnases and penalite_priorite_genre > 0:
            for i in matchs_normaux_indices:
                match = matchs[i]
                for j, creneau in enumerate(creneaux_valides):
                    if (i, j) not in assignment_vars:
                        continue
                    penalite = compute_gym_gender_priority_penalty(
                        match,
                        creneau,
                        self.config,
                        self.priorites_genre_gymnases,
                    )
                    if penalite != 0:
                        objective_terms.append(-int(penalite) * assignment_vars[(i, j)])

        # CONTRAINTE SOUPLE: Espacement entre matchs d'une même équipe
        # Pour chaque équipe, pénaliser les matchs trop rapprochés
        # Appliqué uniquement aux matchs normaux
        if self.config.penalites_espacement_repos:
            for equipe_id in equipes_uniques:
                for semaine1 in range(self.config.semaine_min, self.config.nb_semaines + 1):
                    for semaine2 in range(semaine1 + 1, self.config.nb_semaines + 1):
                        weeks_rest = semaine2 - semaine1 - 1
                        penalty_value = spacing_penalty_for_gap(self.config, weeks_rest)
                        if penalty_value <= 0:
                            continue

                        creneaux_s1 = [j for j, c in enumerate(creneaux_valides) if c.semaine == semaine1]
                        creneaux_s2 = [j for j, c in enumerate(creneaux_valides) if c.semaine == semaine2]
                        matchs_equipe = [i for i in matchs_normaux_indices
                                         if matchs[i].equipe1.id_unique == equipe_id or matchs[i].equipe2.id_unique == equipe_id]

                        plays_s1 = model.NewBoolVar(f'plays_{equipe_id}_s{semaine1}')
                        plays_s2 = model.NewBoolVar(f'plays_{equipe_id}_s{semaine2}')

                        vars_s1 = [assignment_vars[(i, j)]
                                   for i in matchs_equipe for j in creneaux_s1 if (i, j) in assignment_vars]
                        if vars_s1:
                            model.Add(sum(vars_s1) >= 1).OnlyEnforceIf(plays_s1)
                            model.Add(sum(vars_s1) == 0).OnlyEnforceIf(plays_s1.Not())

                        vars_s2 = [assignment_vars[(i, j)]
                                   for i in matchs_equipe for j in creneaux_s2 if (i, j) in assignment_vars]
                        if vars_s2:
                            model.Add(sum(vars_s2) >= 1).OnlyEnforceIf(plays_s2)
                            model.Add(sum(vars_s2) == 0).OnlyEnforceIf(plays_s2.Not())

                        plays_both = model.NewBoolVar(f'plays_both_{equipe_id}_s{semaine1}_s{semaine2}')
                        model.Add(plays_s1 + plays_s2 >= 2).OnlyEnforceIf(plays_both)
                        model.Add(plays_s1 + plays_s2 <= 1).OnlyEnforceIf(plays_both.Not())

                        objective_terms.append(-int(penalty_value) * plays_both)
        
        # CONTRAINTE SOUPLE 1: Compaction temporelle (prioriser les matchs en début de calendrier)
        # Appliqué uniquement aux matchs normaux
        if self.config.compaction_temporelle_actif:
            compaction_penalties = list(self.config.compaction_penalites_par_semaine or [])
            penalties_defined = len(compaction_penalties)
            if penalties_defined == 0:
                print("   ⚠️  Compaction active mais aucune pénalité définie (valeur 0 appliquée).")
            elif penalties_defined < self.config.nb_semaines:
                print(f"   ⚠️  Compaction: seulement {penalties_defined}/{self.config.nb_semaines} semaines ont une pénalité définie (0 appliqué ensuite).")

            for i in matchs_normaux_indices:
                for j, creneau in enumerate(creneaux_valides):
                    if (i, j) not in assignment_vars:
                        continue

                    penalty = int(compaction_penalty_for_week(self.config, creneau.semaine))
                    if penalty > 0:
                        objective_terms.append(-penalty * assignment_vars[(i, j)])
        
        # CONTRAINTE SOUPLE 2: Éviter les overlaps d'institution (matchs simultanés de même institution/équipe)
        # Appliqué seulement aux groupes configurés dans groupes_non_simultaneite
        # Appliqué uniquement aux matchs normaux
        if self.config.overlap_institution_actif:
            # Vérifier si la contrainte est applicable
            if not self.groupes_non_simultaneite:
                if self.config.afficher_progression:
                    print("   ⚠️  Contrainte overlap activée mais aucun groupe configuré - désactivation")
            else:
                # PRÉ-CALCUL: Identifier toutes les paires de matchs conflictuelles (une seule fois)
                # Ceci évite de recalculer pour chaque combinaison de créneaux
                paires_conflictuelles = set()
                for i1 in matchs_normaux_indices:
                    for i2 in matchs_normaux_indices:
                        if i1 < i2:  # Éviter duplicatas
                            match1 = matchs[i1]
                            match2 = matchs[i2]
                            if self._matchs_partagent_groupe_non_simultaneite(match1, match2):
                                paires_conflictuelles.add((i1, i2))
                
                if self.config.afficher_progression and paires_conflictuelles:
                    print(f"   Détecté {len(paires_conflictuelles)} paire(s) de matchs avec contrainte overlap")
                
                if paires_conflictuelles:
                    # Grouper les créneaux par (semaine, horaire) - SANS le gymnase
                    # Car des matchs peuvent être simultanés dans des gymnases différents
                    creneaux_par_moment = {}
                    for j, creneau in enumerate(creneaux_valides):
                        key = (creneau.semaine, creneau.horaire)
                        if key not in creneaux_par_moment:
                            creneaux_par_moment[key] = []
                        creneaux_par_moment[key].append(j)
                    
                    nb_contraintes_overlap = 0
                    
                    # Pour chaque paire de matchs conflictuels
                    for i1, i2 in paires_conflictuelles:
                        # Pour chaque moment (semaine, horaire)
                        for creneaux_list in creneaux_par_moment.values():
                            # Trouver tous les créneaux où chaque match pourrait être assigné
                            creneaux_i1 = [j for j in creneaux_list if (i1, j) in assignment_vars]
                            creneaux_i2 = [j for j in creneaux_list if (i2, j) in assignment_vars]
                            
                            if creneaux_i1 and creneaux_i2:
                                # Créer une variable pour détecter si les deux matchs jouent au même moment
                                overlap_var = model.NewBoolVar(f'overlap_{i1}_{i2}_w{creneaux_valides[creneaux_i1[0]].semaine}_h{creneaux_valides[creneaux_i1[0]].horaire}')
                                
                                # overlap_var = 1 si au moins un créneau de i1 ET un créneau de i2 sont assignés
                                vars_i1 = [assignment_vars[(i1, j)] for j in creneaux_i1]
                                vars_i2 = [assignment_vars[(i2, j)] for j in creneaux_i2]
                                
                                # Si les deux matchs jouent à ce moment → overlap
                                i1_plays = model.NewBoolVar(f'i1_plays_{i1}_{creneaux_i1[0]}')
                                i2_plays = model.NewBoolVar(f'i2_plays_{i2}_{creneaux_i2[0]}')
                                
                                model.Add(sum(vars_i1) >= 1).OnlyEnforceIf(i1_plays)
                                model.Add(sum(vars_i1) == 0).OnlyEnforceIf(i1_plays.Not())
                                
                                model.Add(sum(vars_i2) >= 1).OnlyEnforceIf(i2_plays)
                                model.Add(sum(vars_i2) == 0).OnlyEnforceIf(i2_plays.Not())
                                
                                # overlap = les deux jouent
                                model.Add(i1_plays + i2_plays >= 2).OnlyEnforceIf(overlap_var)
                                model.Add(i1_plays + i2_plays <= 1).OnlyEnforceIf(overlap_var.Not())
                                
                                # Pénaliser l'overlap
                                penalty = int(self.config.overlap_institution_poids)
                                objective_terms.append(-penalty * overlap_var)
                                nb_contraintes_overlap += 1
                    
                    if self.config.afficher_progression and nb_contraintes_overlap > 0:
                        print(f"   Créé {nb_contraintes_overlap} contrainte(s) overlap pour éviter matchs simultanés")

        # CONTRAINTE SOUPLE 2bis: Gestion des coachs (overlaps et bonus consécutifs)
        if (self.config.coach_overlap_actif and coach_match_indices and
                (self.config.coach_overlap_penalite_simultane_diff_gym > 0 or
                 self.config.coach_overlap_penalite_simultane_meme_gym > 0 or
                 self.config.coach_overlap_penalite_deplacement > 0 or
                 self.config.coach_overlap_bonus_consecutif > 0)):

            creneau_minutes = [horaire_to_minutes(c.horaire) for c in creneaux_valides]
            creneaux_par_semaine = defaultdict(list)
            for idx, creneau in enumerate(creneaux_valides):
                creneaux_par_semaine[creneau.semaine].append(idx)

            sim_window = max(0, int(self.config.coach_overlap_simultane_minutes))
            consecutif_min = max(0, int(self.config.coach_overlap_consecutif_min_minutes))
            consecutif_max = max(consecutif_min, int(self.config.coach_overlap_consecutif_max_minutes))
            pen_sim_diff = int(self.config.coach_overlap_penalite_simultane_diff_gym)
            pen_sim_same = int(self.config.coach_overlap_penalite_simultane_meme_gym)
            pen_move = int(self.config.coach_overlap_penalite_deplacement)
            bonus_consec = int(self.config.coach_overlap_bonus_consecutif)

            nb_coach_vars = 0
            nb_coach_terms = 0

            def _sanitize(name: str) -> str:
                return ''.join(ch if ch.isalnum() else '_' for ch in name)

            for coach_name, match_indices in coach_match_indices.items():
                if len(match_indices) >= 2:
                    for idx_a in range(len(match_indices)):
                        for idx_b in range(idx_a + 1, len(match_indices)):
                            i1 = match_indices[idx_a]
                            i2 = match_indices[idx_b]
                            # Pour chaque semaine possible
                            for semaine, indices_sem in creneaux_par_semaine.items():
                                creneaux_i1 = [j for j in indices_sem if (i1, j) in assignment_vars]
                                creneaux_i2 = [j for j in indices_sem if (i2, j) in assignment_vars]
                                if not creneaux_i1 or not creneaux_i2:
                                    continue
                                for j1 in creneaux_i1:
                                    for j2 in creneaux_i2:
                                        delta = abs(creneau_minutes[j1] - creneau_minutes[j2])
                                        same_gym = creneaux_valides[j1].gymnase == creneaux_valides[j2].gymnase
                                        if sim_window > 0 and delta <= sim_window:
                                            penalty = pen_sim_same if same_gym else pen_sim_diff
                                            if penalty <= 0:
                                                continue
                                            var_name = f"coach_overlap_{_sanitize(coach_name)}_{i1}_{i2}_{j1}_{j2}"
                                            conflict_var = model.NewBoolVar(var_name)
                                            model.Add(assignment_vars[(i1, j1)] + assignment_vars[(i2, j2)] >= 2).OnlyEnforceIf(conflict_var)
                                            model.Add(assignment_vars[(i1, j1)] + assignment_vars[(i2, j2)] <= 1).OnlyEnforceIf(conflict_var.Not())
                                            objective_terms.append(-penalty * conflict_var)
                                            nb_coach_vars += 1
                                            nb_coach_terms += 1
                                        elif consecutif_min <= delta <= consecutif_max:
                                            if same_gym and bonus_consec > 0:
                                                var_name = f"coach_bonus_{_sanitize(coach_name)}_{i1}_{i2}_{j1}_{j2}"
                                                bonus_var = model.NewBoolVar(var_name)
                                                model.Add(assignment_vars[(i1, j1)] + assignment_vars[(i2, j2)] >= 2).OnlyEnforceIf(bonus_var)
                                                model.Add(assignment_vars[(i1, j1)] + assignment_vars[(i2, j2)] <= 1).OnlyEnforceIf(bonus_var.Not())
                                                objective_terms.append(bonus_consec * bonus_var)
                                                nb_coach_vars += 1
                                                nb_coach_terms += 1
                                            elif (not same_gym) and pen_move > 0:
                                                var_name = f"coach_move_{_sanitize(coach_name)}_{i1}_{i2}_{j1}_{j2}"
                                                move_var = model.NewBoolVar(var_name)
                                                model.Add(assignment_vars[(i1, j1)] + assignment_vars[(i2, j2)] >= 2).OnlyEnforceIf(move_var)
                                                model.Add(assignment_vars[(i1, j1)] + assignment_vars[(i2, j2)] <= 1).OnlyEnforceIf(move_var.Not())
                                                objective_terms.append(-pen_move * move_var)
                                                nb_coach_vars += 1
                                                nb_coach_terms += 1

                # Interactions avec les matchs déjà fixés
                fixed_events = coach_fixed_events.get(coach_name, [])
                if fixed_events:
                    for i in match_indices:
                        for event in fixed_events:
                            indices_sem = creneaux_par_semaine.get(event['semaine'], [])
                            if not indices_sem:
                                continue
                            for j in indices_sem:
                                if (i, j) not in assignment_vars:
                                    continue
                                delta = abs(creneau_minutes[j] - event['start'])
                                same_gym = creneaux_valides[j].gymnase == event['gymnase']
                                if sim_window > 0 and delta <= sim_window:
                                    penalty = pen_sim_same if same_gym else pen_sim_diff
                                    if penalty > 0:
                                        objective_terms.append(-penalty * assignment_vars[(i, j)])
                                        nb_coach_terms += 1
                                elif consecutif_min <= delta <= consecutif_max:
                                    if same_gym and bonus_consec > 0:
                                        objective_terms.append(bonus_consec * assignment_vars[(i, j)])
                                        nb_coach_terms += 1
                                    elif (not same_gym) and pen_move > 0:
                                        objective_terms.append(-pen_move * assignment_vars[(i, j)])
                                        nb_coach_terms += 1

            if self.config.afficher_progression and nb_coach_terms > 0:
                print(f"   Coach overlap: {nb_coach_terms} terme(s) ajouté(s), {nb_coach_vars} variable(s) auxiliaire(s)")
        
        # CONTRAINTE SOUPLE 3: Espacement aller-retour (pour poules de type Aller-Retour)
        # Appliqué uniquement aux matchs normaux
        if self.config.aller_retour_espacement_actif and (aller_retour_pairs or aller_retour_fixed_pairs):
            if self.config.afficher_progression:
                print(f"   Aller/Retour: {len(aller_retour_pairs)} paire(s) détectée(s)")
                if aller_retour_fixed_pairs:
                    print(f"      + {len(aller_retour_fixed_pairs)} paire(s) avec match fixé")

            for aller_idx, retour_idx in aller_retour_pairs:
                for j_aller, creneau_aller in enumerate(creneaux_valides):
                    if (aller_idx, j_aller) not in assignment_vars:
                        continue
                    var_aller = assignment_vars[(aller_idx, j_aller)]

                    for j_retour, creneau_retour in enumerate(creneaux_valides):
                        if (retour_idx, j_retour) not in assignment_vars:
                            continue
                        var_retour = assignment_vars[(retour_idx, j_retour)]

                        semaine_diff = abs(creneau_retour.semaine - creneau_aller.semaine)
                        gap_penalty = aller_retour_gap_penalty(self.config, semaine_diff)
                        if gap_penalty <= 0:
                            continue

                        joint_var = model.NewBoolVar(
                            f'aller_retour_pair_{aller_idx}_{retour_idx}_{j_aller}_{j_retour}'
                        )
                        model.Add(var_aller + var_retour >= 2).OnlyEnforceIf(joint_var)
                        model.Add(var_aller + var_retour <= 1).OnlyEnforceIf(joint_var.Not())

                        objective_terms.append(-int(round(gap_penalty)) * joint_var)

            if aller_retour_fixed_pairs:
                for match_idx, semaine_fixe in aller_retour_fixed_pairs:
                    for j, creneau in enumerate(creneaux_valides):
                        if (match_idx, j) not in assignment_vars:
                            continue
                        semaine_diff = abs(creneau.semaine - semaine_fixe)
                        gap_penalty = aller_retour_gap_penalty(self.config, semaine_diff)
                        if gap_penalty <= 0:
                            continue
                        objective_terms.append(-int(round(gap_penalty)) * assignment_vars[(match_idx, j)])
        
        # MAXIMISER (bonus - pénalités)
        if objective_terms:
            model.Maximize(sum(objective_terms))

        
        # ============================================================================
        # WARM START : Utiliser une solution précédente comme point de départ
        # ============================================================================
        if use_warm_start:
            try:
                from pycalendar.core.solution_store import SolutionStore
                
                if solution_store is None:
                    # Utiliser le nom de fichier configuré
                    solution_name = getattr(self.config, 'cpsat_warm_start_file', 'default')
                    solution_store = SolutionStore(solution_name=solution_name)
                
                previous_solution = solution_store.load_latest()
                current_config_source = getattr(self.config, 'source_path', None)
                previous_config_source = None
                if previous_solution:
                    previous_config_source = previous_solution.get('metadata', {}).get('config_source')
                    if current_config_source and previous_config_source:
                        try:
                            if Path(previous_config_source).resolve() != Path(current_config_source).resolve():
                                print("\n⚠️  Warm Start ignoré: configuration YAML différente de la solution sauvegardée")
                                previous_solution = None
                        except OSError:
                            print("\n⚠️  Warm Start: impossible de comparer les chemins de configuration, désactivation par sécurité")
                            previous_solution = None
                
                if previous_solution:
                    solution_name = previous_solution['metadata'].get('solution_name', 'unknown')
                    
                    # Message toujours affiché (important pour l'utilisateur)
                    print(f"\n� Warm Start activé - Chargement solution '{solution_name}'")
                    
                    if self.config.afficher_progression:
                        print(f"   Date: {previous_solution['metadata']['date']}")
                        print(f"   Score précédent: {previous_solution['metadata']['score']}")
                        print(f"   Matchs planifiés: {previous_solution['metadata']['matchs_planifies']}")
                    
                    # Valider et adapter la solution à la nouvelle configuration
                    # Note: La signature sera créée/passée depuis l'orchestrateur
                    # Pour l'instant, on fait une validation basique
                    hint, stats = self._apply_warm_start_basic(
                        previous_solution, matchs, creneaux_valides, assignment_vars, model
                    )
                    
                    # Toujours afficher les statistiques de réutilisation (important!)
                    pct = (stats['valid_assignments'] / stats['total_assignments'] * 100) if stats['total_assignments'] > 0 else 0
                    
                    if stats['valid_assignments'] > 0:
                        print(f"   ✅ {stats['valid_assignments']}/{stats['total_assignments']} assignments réutilisés ({pct:.1f}%)")
                        
                        if self.config.afficher_progression and (stats['invalid_match'] > 0 or stats['invalid_creneau'] > 0):
                            if stats['invalid_match'] > 0:
                                print(f"      ⚠️  {stats['invalid_match']} matchs non trouvés")
                            if stats['invalid_creneau'] > 0:
                                print(f"      ⚠️  {stats['invalid_creneau']} créneaux non trouvés")
                    else:
                        # Afficher le nombre total (important pour comprendre pourquoi ça ne marche pas)
                        print(f"   ⚠️  Aucun assignment réutilisable sur {stats['total_assignments']} tentatives")
                        print(f"      Matchs invalides: {stats['invalid_match']}, Créneaux invalides: {stats['invalid_creneau']}")
                else:
                    # Message toujours affiché
                    print("\n🆕 Première résolution - Aucune solution précédente")
                        
            except Exception as e:
                # Toujours afficher les erreurs de warm start (important pour debug)
                print(f"   ⚠️  Erreur lors du chargement de la solution précédente: {e}")
                if self.config.afficher_progression:
                    import traceback
                    traceback.print_exc()
                # Continue sans warm start
        
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = self.config.temps_max_secondes
        solver.parameters.log_search_progress = self.config.afficher_progression
        
        # Configuration pour améliorer la recherche
        solver.parameters.num_search_workers = 8  # Utiliser plusieurs threads pour exploration parallèle
        solver.parameters.relative_gap_limit = 0.0  # Ne pas s'arrêter avant le temps max
        solver.parameters.absolute_gap_limit = 0.0  # Continuer jusqu'au temps max
        
        # Log pour débugger
        if self.config.afficher_progression:
            print(f"\n🔧 Configuration CP-SAT:")
            print(f"   Temps max: {solver.parameters.max_time_in_seconds}s")
            print(f"   Workers: {solver.parameters.num_search_workers}")
            print(f"   Relative gap limit: {solver.parameters.relative_gap_limit}")
            print(f"   Absolute gap limit: {solver.parameters.absolute_gap_limit}")
        
        # Callback pour capturer les solutions intermédiaires
        class SolutionPrinter(cp_model.CpSolverSolutionCallback):
            def __init__(self, show_progress: bool):
                cp_model.CpSolverSolutionCallback.__init__(self)
                self._solution_count = 0
                self._show_progress = show_progress
                self._solutions = []  # Stocker (temps, score) pour chaque solution
                self._start_time = None
            
            def on_solution_callback(self):
                import time
                if self._start_time is None:
                    self._start_time = time.time()
                
                self._solution_count += 1
                current_time = time.time() - self._start_time
                score = self.ObjectiveValue()
                self._solutions.append((current_time, score))
                
                if self._show_progress:
                    print(f"   Solution #{self._solution_count}: Score = {score:.0f} (à {current_time:.2f}s)")
            
            def solution_count(self):
                return self._solution_count
            
            def get_solutions(self):
                return self._solutions
        
        solution_printer = SolutionPrinter(self.config.afficher_progression)
        
        if self.config.afficher_progression:
            print("\nCP-SAT solver - Résolution...")
        
        import time
        start_time = time.time()
        status = solver.Solve(model, solution_printer)
        elapsed_time = time.time() - start_time
        
        # Afficher les statistiques du solver
        print(f"\n⏱️  Statistiques de résolution:")
        print(f"   Temps écoulé: {elapsed_time:.2f}s / {self.config.temps_max_secondes}s")
        print(f"   Statut: {solver.StatusName(status)}")
        print(f"   Branches: {solver.NumBranches()}")
        print(f"   Conflits: {solver.NumConflicts()}")
        print(f"   Temps utilisé: {solver.WallTime():.2f}s")
        
        # Vérifier si le temps max a été atteint
        if elapsed_time >= self.config.temps_max_secondes * 0.95:
            print(f"   ⚠️  Temps maximum atteint ! Le solver a utilisé presque tout le temps alloué.")
        elif elapsed_time < self.config.temps_max_secondes * 0.1:
            print(f"   ℹ️  Le solver s'est arrêté rapidement (< 10% du temps max)")
            if status == cp_model.OPTIMAL:
                print(f"      → Solution optimale prouvée")
            else:
                print(f"      → Vérifiez s'il y a des problèmes de contraintes")
        
        # Afficher le résumé de l'évolution des solutions
        solutions = solution_printer.get_solutions()
        if solutions:
            print(f"\n📊 Évolution des solutions trouvées:")
            print(f"   Nombre total de solutions: {len(solutions)}")
            
            # Afficher les 5 premières solutions
            nb_to_show = min(5, len(solutions))
            print(f"   Premières solutions:")
            for i, (temps, score) in enumerate(solutions[:nb_to_show]):
                print(f"      #{i+1}: Score {score:.0f} (trouvée à {temps:.2f}s)")
            
            if len(solutions) > nb_to_show:
                print(f"      ... ({len(solutions) - nb_to_show} solutions intermédiaires)")
            
            # Afficher la solution finale
            if len(solutions) > 1:
                temps_final, score_final = solutions[-1]
                print(f"   Solution finale:")
                print(f"      Score {score_final:.0f} (trouvée à {temps_final:.2f}s)")
                
                # Calculer l'amélioration
                _, score_initial = solutions[0]
                improvement = score_final - score_initial
                pct_improvement = (improvement / abs(score_initial) * 100) if score_initial != 0 else 0
                print(f"   Amélioration: {improvement:+.0f} ({pct_improvement:+.1f}%)")
        
        matchs_planifies = []
        matchs_non_planifies = []
        
        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            # Traiter les matchs normaux (assignment_vars)
            for i in matchs_normaux_indices:
                match = matchs[i]
                assigned = False
                for j, creneau in enumerate(creneaux_valides):
                    if (i, j) in assignment_vars and solver.Value(assignment_vars[(i, j)]) == 1:
                        match.creneau = creneau
                        matchs_planifies.append(match)
                        assigned = True
                        break
                
                if not assigned:
                    matchs_non_planifies.append(match)
            
            # Traiter les ententes (entente_activated)
            for i in matchs_ententes_indices:
                match = matchs[i]
                # Vérifier si l'entente a été activée
                if i in entente_activated and solver.Value(entente_activated[i]) == 1:
                    # Entente activée : pas de créneau assigné, mais comptée comme planifiée
                    match.creneau = None  # Entente n'a pas de créneau
                    matchs_planifies.append(match)
                else:
                    matchs_non_planifies.append(match)
        else:
            matchs_non_planifies = matchs
        
        return Solution(
            matchs_planifies=matchs_planifies,
            matchs_non_planifies=matchs_non_planifies,
            score=solver.ObjectiveValue() if status in [cp_model.OPTIMAL, cp_model.FEASIBLE] else float('inf'),
            metadata={'solver': 'cpsat', 'status': solver.StatusName(status)}
        )
    
    def _apply_warm_start_basic(self, solution_data: dict, matchs: List[Match],
                                creneaux: List[Creneau], assignment_vars: dict,
                                model) -> tuple:
        """
        Applique un warm start basique sans validation de signature.
        
        Cette méthode est utilisée quand on appelle solve() directement
        sans passer par l'orchestrateur. Pour une validation complète,
        utiliser SolutionStore.validate_and_adapt_solution().
        
        Args:
            solution_data: Données de la solution précédente
            matchs: Liste des matchs actuels
            creneaux: Liste des créneaux actuels
            assignment_vars: Variables d'assignment du modèle CP-SAT
            model: Modèle CP-SAT
            
        Returns:
            Tuple (hint, stats)
        """
        stats = {
            'total_assignments': len(solution_data.get("assignments", [])),
            'valid_assignments': 0,
            'invalid_match': 0,
            'invalid_creneau': 0,
        }
        
        # Créer des lookups rapides
        matchs_lookup = {}
        for idx, match in enumerate(matchs):
            # Clé bidirectionnelle
            key1 = (match.equipe1.id_unique, match.equipe2.id_unique)
            key2 = (match.equipe2.id_unique, match.equipe1.id_unique)
            matchs_lookup[key1] = idx
            matchs_lookup[key2] = idx
        
        creneaux_lookup = {
            (c.semaine, c.horaire, c.gymnase): idx
            for idx, c in enumerate(creneaux)
        }
        
        hint = {}
        
        # Valider chaque assignment
        for assignment in solution_data.get("assignments", []):
            # Trouver le match
            eq1_id = assignment.get("equipe1_id")
            eq2_id = assignment.get("equipe2_id")
            
            if not eq1_id or not eq2_id:
                # Format ancien, essayer avec nom+genre
                eq1_id = f"{assignment['equipe1_nom']}|{assignment['equipe1_genre']}"
                eq2_id = f"{assignment['equipe2_nom']}|{assignment['equipe2_genre']}"
            
            match_idx = matchs_lookup.get((eq1_id, eq2_id))
            
            if match_idx is None:
                stats['invalid_match'] += 1
                continue
            
            # Trouver le créneau
            creneau_key = (
                assignment["semaine"],
                assignment["horaire"],
                assignment["gymnase"]
            )
            creneau_idx = creneaux_lookup.get(creneau_key)
            
            if creneau_idx is None:
                stats['invalid_creneau'] += 1
                continue
            
            # Assignment valide : ajouter comme hint
            var = assignment_vars.get((match_idx, creneau_idx))
            if var is not None:  # Important: ne pas évaluer var comme booléen (erreur OR-Tools)
                model.AddHint(var, 1)
                hint[(match_idx, creneau_idx)] = 1
                stats['valid_assignments'] += 1
        
        return hint, stats
    
    def get_name(self) -> str:
        return "CP-SAT"
