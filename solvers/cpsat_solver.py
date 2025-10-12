"""CP-SAT solver using OR-Tools."""

try:
    from ortools.sat.python import cp_model
    ORTOOLS_AVAILABLE = True
except ImportError:
    ORTOOLS_AVAILABLE = False

from typing import List, Dict, Optional, Set
from core.models import Match, Creneau, Gymnase, Solution
from core.config import Config
from .base_solver import BaseSolver


class CPSATSolver(BaseSolver):
    """Optimal solver using CP-SAT (OR-Tools)."""
    
    def __init__(self, config: Config, groupes_non_simultaneite: Optional[Dict[str, Set[str]]] = None,
                 ententes: Optional[Dict] = None, contraintes_temporelles: Optional[Dict] = None):
        if not ORTOOLS_AVAILABLE:
            raise ImportError("OR-Tools not installed. Install with: pip install ortools")
        super().__init__(config)
        self.groupes_non_simultaneite = groupes_non_simultaneite or {}
        self.ententes = ententes or {}  # Dict avec paires d'institutions et leurs pénalités
        self.contraintes_temporelles = contraintes_temporelles or {}  # Dict avec paires d'équipes et leurs contraintes temporelles
    
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
        Récupère la pénalité de non-planification pour une entente.
        
        Returns:
            Pénalité spécifique ou pénalité par défaut du YAML
        """
        inst1 = match.equipe1.institution
        inst2 = match.equipe2.institution
        cle = tuple(sorted([inst1, inst2]))
        
        penalite = self.ententes.get(cle)
        if penalite is None:
            # Pas de pénalité spécifiée dans Excel, utiliser défaut YAML
            return self.config.entente_penalite_non_planif
        return penalite
    
    def _get_contrainte_temporelle(self, match: Match):
        """
        Récupère la contrainte temporelle pour un match s'il en existe une.
        
        Gère le matching avec/sans genre:
        - Si contrainte spécifie un genre, s'applique uniquement à ce genre
        - Si contrainte sans genre, s'applique à toutes les équipes de ce nom
        
        Args:
            match: Le match à vérifier
            
        Returns:
            ContrainteTemporelle si elle existe, None sinon
        """
        from core.utils import matcher_contrainte_avec_genre
        
        if not self.config.contrainte_temporelle_actif or not self.contraintes_temporelles:
            return None
        
        # Extraire les infos des équipes
        eq1_nom = match.equipe1.nom
        eq1_genre = match.equipe1.genre
        eq2_nom = match.equipe2.nom
        eq2_genre = match.equipe2.genre
        
        # Parcourir toutes les contraintes pour trouver celle qui matche
        for contrainte_key, contrainte in self.contraintes_temporelles.items():
            if matcher_contrainte_avec_genre(eq1_nom, eq1_genre, eq2_nom, eq2_genre, contrainte_key):
                return contrainte
        
        return None
    
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
    
    def _parse_horaire(self, horaire: str) -> int:
        """
        Convertit un horaire en minutes depuis minuit.
        Format: "14:00", "14H", "14H30", "20:00"
        
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
            print(f"ERREUR: Impossible de parser l'horaire '{horaire}'. Utilisation de 14:00 par défaut.")
            # En cas d'erreur, retourner 14h par défaut
            return 14 * 60
    
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
    
    def _calculate_time_preference_penalty(self, match: Match, creneau: Creneau) -> float:
        """Calcule la pénalité pour les horaires préférés avec système de tolérance sophistiqué.
        
        LOGIQUE DE TOLÉRANCE:
        - Fenêtre de tolérance (en minutes) où une équipe peut jouer plus tôt/tard sans pénalité
        - Si distance <= tolérance : PAS de pénalité (match accepté dans la zone de tolérance)
        - Si distance > tolérance : pénalité calculée sur la distance TOTALE (pas seulement l'excédent)
        
        MULTIPLICATEURS selon position du match par rapport à l'horaire préféré:
        - 300x : match AVANT horaire préféré des 2 équipes (violation grave)
        - 100x : match AVANT horaire préféré d'1 seule équipe (violation moyenne)
        - 10x : match APRÈS horaire préféré (dégradation acceptable)
        
        FORMULE DE PÉNALITÉ:
        pénalité = multiplicateur × ((distance / diviseur)²)
        où:
        - distance = distance totale en minutes (si > tolérance)
        - diviseur = paramètre de normalisation (60=heures, 90=poids plus faible)
        
        ALGORITHME:
        1. Parser les horaires préférés de chaque équipe
        2. Si horaire match exactement dans préférés → pas de pénalité
        3. Calculer distance en minutes entre horaire match et horaire préféré
        4. Vérifier si distance <= tolérance → pas de pénalité (accepté)
        5. Sinon, déterminer multiplicateur selon combien d'équipes jouent AVANT leur horaire préféré
        6. Appliquer formule: pénalité += multiplicateur × ((distance / diviseur)²)
        
        Returns:
            float: Pénalité totale pour ce match/créneau
        """
        penalty_total = 0.0
        
        horaire_match_min = self._parse_horaire(creneau.horaire)
        
        # Analyser chaque équipe
        equipes = [match.equipe1, match.equipe2]
        horaires_preferes_parsed = []
        distances = []
        est_avant = []
        
        for equipe in equipes:
            if not equipe.horaires_preferes:
                distances.append(0)
                est_avant.append(False)
                horaires_preferes_parsed.append(None)
                continue
            
            # Parser l'horaire préféré (un seul par équipe)
            h_pref_str = equipe.horaires_preferes[0]
            h_pref_min = self._parse_horaire(h_pref_str)
            horaires_preferes_parsed.append(h_pref_min)
            
            # Si l'horaire match correspond exactement, pas de pénalité
            if creneau.horaire == h_pref_str:
                distances.append(0)
                est_avant.append(False)
                continue
            
            # Calculer la distance en minutes
            distance_min = abs(horaire_match_min - h_pref_min)
            distances.append(distance_min)
            
            # Vérifier si le match est AVANT l'horaire préféré
            est_avant.append(horaire_match_min < h_pref_min)
        
        # Appliquer la tolérance : si distance <= tolérance, pas de pénalité
        tolerance = self.config.penalite_horaire_tolerance
        diviseur = self.config.penalite_horaire_diviseur
        
        # CORRECTION : Calculer les pénalités individuellement pour chaque équipe
        # et déterminer le multiplicateur APRÈS avoir exclu les équipes dans la tolérance
        
        # Étape 1 : Identifier les équipes HORS tolérance
        equipes_hors_tolerance = []
        for i, distance in enumerate(distances):
            if distance > tolerance:
                equipes_hors_tolerance.append((i, distance, est_avant[i]))
        
        # Si toutes les équipes sont dans la tolérance, pas de pénalité
        if not equipes_hors_tolerance:
            return 0.0
        
        # Étape 2 : Compter combien d'équipes HORS tolérance jouent AVANT leur horaire préféré
        nb_equipes_avant_hors_tolerance = sum(1 for _, _, avant in equipes_hors_tolerance if avant)
        
        # Étape 3 : Déterminer le multiplicateur selon les cas (seulement pour les équipes HORS tolérance)
        if nb_equipes_avant_hors_tolerance == 2:
            # Les 2 équipes (hors tolérance) jouent avant leur horaire préféré
            multiplicateur = self.config.penalite_avant_horaire_min_deux
        elif nb_equipes_avant_hors_tolerance == 1:
            # 1 seule équipe (hors tolérance) joue avant son horaire préféré
            multiplicateur = self.config.penalite_avant_horaire_min
        else:
            # Les équipes (hors tolérance) jouent après leur horaire préféré
            multiplicateur = self.config.penalite_apres_horaire_min
        
        # Étape 4 : Calculer la pénalité totale avec le bon multiplicateur
        for i, distance, _ in equipes_hors_tolerance:
            # Pénalité = multiplicateur * (distance / diviseur)²
            penalty_total += multiplicateur * ((distance / diviseur) ** 2)
        
        return penalty_total
    
    def solve(self, matchs: List[Match], creneaux: List[Creneau], 
             gymnases: Dict[str, Gymnase], obligations_presence: Optional[Dict[str, str]] = None,
             use_warm_start: bool = True, solution_store = None) -> Solution:
        """
        Solve using CP-SAT constraint programming with optional warm start.
        
        Args:
            matchs: Liste des matchs à planifier
            creneaux: Liste des créneaux disponibles
            gymnases: Dictionnaire des gymnases
            obligations_presence: Contraintes de présence par gymnase
            use_warm_start: Si True, tente d'utiliser une solution précédente comme point de départ
            solution_store: Instance de SolutionStore (créée automatiquement si None)
            
        Returns:
            Solution trouvée
        """
        
        if self.config.afficher_progression:
            print("CP-SAT solver - Création du modèle...")
        
        if obligations_presence is None:
            obligations_presence = {}
        
        model = cp_model.CpModel()
        
        assignment_vars = {}
        match_assigned = []
        
        # Créer les variables
        for i, match in enumerate(matchs):
            # Variable pour savoir si le match est assigné
            assigned_var = model.NewBoolVar(f'match_{i}_assigned')
            match_assigned.append(assigned_var)
            
            for j, creneau in enumerate(creneaux):
                var = model.NewBoolVar(f'match_{i}_creneau_{j}')
                assignment_vars[(i, j)] = var
        
        # CONTRAINTE 1: Chaque match est assigné à exactement 1 créneau (ou aucun)
        for i in range(len(matchs)):
            model.Add(sum(assignment_vars[(i, j)] for j in range(len(creneaux))) == match_assigned[i])
        
        # CONTRAINTE 2: Capacité des gymnases (avec support de capacité réduite)
        for j in range(len(creneaux)):
            creneau = creneaux[j]
            gymnase = gymnases.get(creneau.gymnase)
            if gymnase:
                # Utiliser la capacité disponible (qui peut être réduite)
                capacite_disponible = gymnase.get_capacite_disponible(creneau.semaine, creneau.horaire)
                model.Add(sum(assignment_vars[(i, j)] for i in range(len(matchs))) <= capacite_disponible)
        
        # CONTRAINTE 3: Disponibilité des équipes (DURE)
        for i, match in enumerate(matchs):
            for j, creneau in enumerate(creneaux):
                if not match.equipe1.est_disponible(creneau.semaine, creneau.horaire):
                    model.Add(assignment_vars[(i, j)] == 0)
                if not match.equipe2.est_disponible(creneau.semaine, creneau.horaire):
                    model.Add(assignment_vars[(i, j)] == 0)
        
        # CONTRAINTE 3bis: Contraintes temporelles (mode dur si activé)
        if self.config.contrainte_temporelle_actif and self.config.contrainte_temporelle_dure:
            for i, match in enumerate(matchs):
                contrainte = self._get_contrainte_temporelle(match)
                if contrainte:
                    for j, creneau in enumerate(creneaux):
                        # Si la contrainte n'est pas respectée, bloquer ce placement
                        if not contrainte.est_respectee(creneau.semaine):
                            model.Add(assignment_vars[(i, j)] == 0)
        
        # CONTRAINTE 4: Une équipe ne peut jouer qu'une fois par (semaine, horaire)
        # Grouper les créneaux par (semaine, horaire)
        creneaux_par_semaine_horaire = {}
        for j, creneau in enumerate(creneaux):
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
                # Trouver tous les matchs où cette équipe joue à ce (semaine, horaire)
                vars_equipe = []
                for i, match in enumerate(matchs):
                    if match.equipe1.id_unique == equipe_id or match.equipe2.id_unique == equipe_id:
                        for j in indices_creneaux:
                            vars_equipe.append(assignment_vars[(i, j)])
                
                # L'équipe ne peut jouer qu'une fois à ce (semaine, horaire)
                if len(vars_equipe) > 1:
                    model.Add(sum(vars_equipe) <= 1)
        
        # CONTRAINTE 5: Max matchs par équipe par semaine
        max_matchs_semaine = self.config.max_matchs_par_equipe_par_semaine
        
        for equipe_id in equipes_uniques:
            for semaine in range(1, self.config.nb_semaines + 1):
                # Trouver tous les créneaux de cette semaine
                indices_semaine = [j for j, c in enumerate(creneaux) if c.semaine == semaine]
                
                # Trouver tous les matchs où cette équipe joue
                vars_equipe_semaine = []
                for i, match in enumerate(matchs):
                    if match.equipe1.id_unique == equipe_id or match.equipe2.id_unique == equipe_id:
                        for j in indices_semaine:
                            vars_equipe_semaine.append(assignment_vars[(i, j)])
                
                # Limiter le nombre de matchs
                if vars_equipe_semaine:
                    model.Add(sum(vars_equipe_semaine) <= max_matchs_semaine)
        
        # CONTRAINTE 6: Obligations de présence
        for i, match in enumerate(matchs):
            for j, creneau in enumerate(creneaux):
                institution_requise = obligations_presence.get(creneau.gymnase)
                
                if institution_requise:
                    # Vérifier si au moins une équipe est de l'institution requise
                    inst1 = match.equipe1.institution
                    inst2 = match.equipe2.institution
                    
                    if institution_requise not in [inst1, inst2]:
                        # Interdire ce match à ce gymnase
                        model.Add(assignment_vars[(i, j)] == 0)
        
        # CONTRAINTE 7: Disponibilité des gymnases
        for i, match in enumerate(matchs):
            for j, creneau in enumerate(creneaux):
                gymnase = gymnases.get(creneau.gymnase)
                if gymnase and not gymnase.est_disponible(creneau.semaine, creneau.horaire):
                    model.Add(assignment_vars[(i, j)] == 0)
        
        # Fonction objectif : MAXIMISER les matchs assignés ET minimiser les pénalités
        objective_terms = []
        
        # Grand bonus pour chaque match assigné (poids très élevé)
        # SAUF pour les ententes qui ont un bonus réduit (= pénalité plus faible si non planifiés)
        for i, match in enumerate(matchs):
            if self._est_entente(match):
                # Match entente : bonus réduit = pénalité faible si non planifié
                bonus = int(self._get_penalite_entente(match))
            else:
                # Match normal : grand bonus = forte pénalité si non planifié
                bonus = 10000
            objective_terms.append(bonus * match_assigned[i])
        
        # Pénalités pour préférences horaires (sophistiquée avec distance)
        for i, match in enumerate(matchs):
            for j, creneau in enumerate(creneaux):
                penalty = self._calculate_time_preference_penalty(match, creneau)
                
                if penalty > 0:
                    objective_terms.append(-int(penalty) * assignment_vars[(i, j)])
        
        # Pénalité pour contraintes temporelles violées (mode souple uniquement)
        if self.config.contrainte_temporelle_actif and not self.config.contrainte_temporelle_dure:
            for i, match in enumerate(matchs):
                contrainte = self._get_contrainte_temporelle(match)
                if contrainte:
                    for j, creneau in enumerate(creneaux):
                        # Si la contrainte n'est pas respectée, ajouter une pénalité
                        if not contrainte.est_respectee(creneau.semaine):
                            penalty = int(self.config.contrainte_temporelle_penalite)
                            objective_terms.append(-penalty * assignment_vars[(i, j)])
        
        # Pénalités pour préférences de gymnases (système de bonus)
        if self.config.bonus_preferences_gymnases:
            base_penalty = 2 * max(self.config.bonus_preferences_gymnases)
            
            for i, match in enumerate(matchs):
                for j, creneau in enumerate(creneaux):
                    penalty = base_penalty
                    
                    # Soustraire bonus si équipe 1 a ce gymnase dans ses préférences
                    if match.equipe1.lieux_preferes:
                        for rang, gymnase in enumerate(match.equipe1.lieux_preferes):
                            if gymnase == creneau.gymnase and rang < len(self.config.bonus_preferences_gymnases):
                                penalty -= self.config.bonus_preferences_gymnases[rang]
                                break
                    
                    # Soustraire bonus si équipe 2 a ce gymnase dans ses préférences
                    if match.equipe2.lieux_preferes:
                        for rang, gymnase in enumerate(match.equipe2.lieux_preferes):
                            if gymnase == creneau.gymnase and rang < len(self.config.bonus_preferences_gymnases):
                                penalty -= self.config.bonus_preferences_gymnases[rang]
                                break
                    
                    # Ajouter la pénalité (négative car on maximise)
                    objective_terms.append(-int(penalty) * assignment_vars[(i, j)])
        
        # CONTRAINTE SOUPLE: Espacement entre matchs d'une même équipe
        # Pour chaque équipe, pénaliser les matchs trop rapprochés
        if self.config.penalites_espacement_repos:
            # Grouper les créneaux par semaine pour chaque équipe
            for equipe_id in equipes_uniques:
                # Pour chaque paire de semaines, détecter si l'équipe joue aux deux
                for semaine1 in range(1, self.config.nb_semaines + 1):
                    for semaine2 in range(semaine1 + 1, self.config.nb_semaines + 1):
                        # Calculer le nombre de semaines de repos entre ces deux semaines
                        weeks_rest = semaine2 - semaine1 - 1
                        
                        # Vérifier si on doit pénaliser cet écart
                        if weeks_rest < len(self.config.penalites_espacement_repos):
                            penalty_value = self.config.penalites_espacement_repos[weeks_rest]
                            
                            if penalty_value > 0:
                                # Trouver tous les créneaux de semaine1 et semaine2
                                creneaux_s1 = [j for j, c in enumerate(creneaux) if c.semaine == semaine1]
                                creneaux_s2 = [j for j, c in enumerate(creneaux) if c.semaine == semaine2]
                                
                                # Trouver tous les matchs où cette équipe joue
                                matchs_equipe = [i for i, m in enumerate(matchs) 
                                               if m.equipe1.id_unique == equipe_id or m.equipe2.id_unique == equipe_id]
                                
                                # Créer une variable pour détecter si l'équipe joue aux deux semaines
                                plays_s1 = model.NewBoolVar(f'plays_{equipe_id}_s{semaine1}')
                                plays_s2 = model.NewBoolVar(f'plays_{equipe_id}_s{semaine2}')
                                
                                # plays_s1 = 1 si l'équipe joue en semaine1
                                vars_s1 = [assignment_vars[(i, j)] 
                                          for i in matchs_equipe for j in creneaux_s1]
                                if vars_s1:
                                    model.Add(sum(vars_s1) >= 1).OnlyEnforceIf(plays_s1)
                                    model.Add(sum(vars_s1) == 0).OnlyEnforceIf(plays_s1.Not())
                                
                                # plays_s2 = 1 si l'équipe joue en semaine2
                                vars_s2 = [assignment_vars[(i, j)] 
                                          for i in matchs_equipe for j in creneaux_s2]
                                if vars_s2:
                                    model.Add(sum(vars_s2) >= 1).OnlyEnforceIf(plays_s2)
                                    model.Add(sum(vars_s2) == 0).OnlyEnforceIf(plays_s2.Not())
                                
                                # Créer une variable pour détecter si l'équipe joue aux DEUX semaines
                                plays_both = model.NewBoolVar(f'plays_both_{equipe_id}_s{semaine1}_s{semaine2}')
                                model.Add(plays_s1 + plays_s2 >= 2).OnlyEnforceIf(plays_both)
                                model.Add(plays_s1 + plays_s2 <= 1).OnlyEnforceIf(plays_both.Not())
                                
                                # Pénaliser si l'équipe joue aux deux semaines
                                objective_terms.append(-int(penalty_value) * plays_both)
        
        # CONTRAINTE SOUPLE 1: Compaction temporelle (prioriser les matchs en début de calendrier)
        if self.config.compaction_temporelle_actif:
            for i in range(len(matchs)):
                for j, creneau in enumerate(creneaux):
                    semaine = creneau.semaine
                    
                    # Récupérer la pénalité pour cette semaine (indice 0 = semaine 1)
                    if semaine <= len(self.config.compaction_penalites_par_semaine):
                        penalty = int(self.config.compaction_penalites_par_semaine[semaine - 1])
                    else:
                        # Si on dépasse le nb de semaines définies, utiliser la dernière pénalité
                        penalty = int(self.config.compaction_penalites_par_semaine[-1])
                    
                    if penalty > 0:
                        objective_terms.append(-penalty * assignment_vars[(i, j)])
        
        # CONTRAINTE SOUPLE 2: Éviter les overlaps d'institution (matchs simultanés de même institution/équipe)
        # Appliqué seulement aux groupes configurés dans groupes_non_simultaneite
        if self.config.overlap_institution_actif:
            # Grouper les créneaux identiques (même semaine, même horaire, même gymnase)
            creneaux_identiques = {}
            for j, creneau in enumerate(creneaux):
                key = (creneau.semaine, creneau.horaire, creneau.gymnase)
                if key not in creneaux_identiques:
                    creneaux_identiques[key] = []
                creneaux_identiques[key].append(j)
            
            # Pour chaque créneau unique, pénaliser si plusieurs matchs partagent un groupe de non-simultanéité
            for creneaux_list in creneaux_identiques.values():
                if len(creneaux_list) > 1:
                    # Pour chaque paire de créneaux simultanés
                    for j1 in creneaux_list:
                        for j2 in creneaux_list:
                            if j1 < j2:  # Éviter de compter deux fois
                                # Pour chaque paire de matchs
                                for i1, match1 in enumerate(matchs):
                                    for i2, match2 in enumerate(matchs):
                                        if i1 < i2:  # Éviter de compter deux fois
                                            # Vérifier si les matchs partagent un groupe de non-simultanéité
                                            if self._matchs_partagent_groupe_non_simultaneite(match1, match2):
                                                # Créer une variable pour détecter l'overlap
                                                overlap_var = model.NewBoolVar(f'overlap_{i1}_{i2}_{j1}_{j2}')
                                                
                                                # overlap_var = 1 si les deux matchs sont assignés simultanément
                                                model.Add(assignment_vars[(i1, j1)] + assignment_vars[(i2, j2)] >= 2).OnlyEnforceIf(overlap_var)
                                                model.Add(assignment_vars[(i1, j1)] + assignment_vars[(i2, j2)] <= 1).OnlyEnforceIf(overlap_var.Not())
                                                
                                                # Pénaliser l'overlap
                                                penalty = int(self.config.overlap_institution_poids)
                                                objective_terms.append(-penalty * overlap_var)
        
        # CONTRAINTE SOUPLE 3: Espacement aller-retour (pour poules de type Aller-Retour)
        if self.config.aller_retour_espacement_actif:
            # Détecter toutes les paires aller-retour
            paires_aller_retour = []
            for i1, match1 in enumerate(matchs):
                for i2, match2 in enumerate(matchs):
                    if i1 < i2 and self._sont_matchs_aller_retour(match1, match2):
                        paires_aller_retour.append((i1, i2))
            
            if paires_aller_retour:
                if self.config.afficher_progression:
                    print(f"   Détecté {len(paires_aller_retour)} paire(s) aller-retour")
                
                # Pour chaque paire aller-retour
                for i1, i2 in paires_aller_retour:
                    # Variables pour détecter si planifiés dans même semaine ou semaines consécutives
                    for j1, creneau1 in enumerate(creneaux):
                        for j2, creneau2 in enumerate(creneaux):
                            semaine_diff = abs(creneau1.semaine - creneau2.semaine)
                            
                            # Pénalité si dans même semaine
                            if semaine_diff == 0:
                                conflict_var = model.NewBoolVar(f'aller_retour_meme_semaine_{i1}_{i2}_{j1}_{j2}')
                                # conflict_var = 1 si les deux matchs sont planifiés dans ces créneaux
                                model.Add(assignment_vars[(i1, j1)] + assignment_vars[(i2, j2)] >= 2).OnlyEnforceIf(conflict_var)
                                model.Add(assignment_vars[(i1, j1)] + assignment_vars[(i2, j2)] <= 1).OnlyEnforceIf(conflict_var.Not())
                                
                                penalty = int(self.config.aller_retour_penalite_meme_semaine)
                                objective_terms.append(-penalty * conflict_var)
                            
                            # Pénalité si dans semaines consécutives
                            elif semaine_diff == 1:
                                conflict_var = model.NewBoolVar(f'aller_retour_consecutif_{i1}_{i2}_{j1}_{j2}')
                                # conflict_var = 1 si les deux matchs sont planifiés dans ces créneaux
                                model.Add(assignment_vars[(i1, j1)] + assignment_vars[(i2, j2)] >= 2).OnlyEnforceIf(conflict_var)
                                model.Add(assignment_vars[(i1, j1)] + assignment_vars[(i2, j2)] <= 1).OnlyEnforceIf(conflict_var.Not())
                                
                                penalty = int(self.config.aller_retour_penalite_consecutives)
                                objective_terms.append(-penalty * conflict_var)
        
        # MAXIMISER (bonus - pénalités)
        if objective_terms:
            model.Maximize(sum(objective_terms))
        
        # ============================================================================
        # WARM START : Utiliser une solution précédente comme point de départ
        # ============================================================================
        if use_warm_start:
            try:
                from core.solution_store import SolutionStore
                
                if solution_store is None:
                    # Utiliser le nom de fichier configuré
                    solution_name = getattr(self.config, 'cpsat_warm_start_file', 'default')
                    solution_store = SolutionStore(solution_name=solution_name)
                
                previous_solution = solution_store.load_latest()
                
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
                        previous_solution, matchs, creneaux, assignment_vars, model
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
        
        status = solver.Solve(model, solution_printer)
        
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
            for i, match in enumerate(matchs):
                assigned = False
                for j, creneau in enumerate(creneaux):
                    if solver.Value(assignment_vars[(i, j)]) == 1:
                        match.creneau = creneau
                        matchs_planifies.append(match)
                        assigned = True
                        break
                
                if not assigned:
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
