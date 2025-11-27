"""CP-SAT solver using OR-Tools."""

try:
    from ortools.sat.python import cp_model
    ORTOOLS_AVAILABLE = True
except ImportError:
    ORTOOLS_AVAILABLE = False

from typing import List, Dict, Optional, Set
from pycalendar.core.models import Match, Creneau, Gymnase, Solution
from pycalendar.core.config import Config
from .base_solver import BaseSolver


class CPSATSolver(BaseSolver):
    """Optimal solver using CP-SAT (OR-Tools)."""
    
    def __init__(self, config: Config, groupes_non_simultaneite: Optional[Dict[str, Set[str]]] = None,
                 ententes: Optional[Dict] = None, contraintes_temporelles: Optional[Dict] = None,
                 niveaux_gymnases: Optional[Dict[str, str]] = None):
        if not ORTOOLS_AVAILABLE:
            raise ImportError("OR-Tools not installed. Install with: pip install ortools")
        super().__init__(config)
        self.groupes_non_simultaneite = groupes_non_simultaneite or {}
        self.ententes = ententes or {}  # Dict avec paires d'institutions et leurs pénalités
        self.contraintes_temporelles = contraintes_temporelles or {}  # Dict avec paires d'équipes et leurs contraintes temporelles
        self.niveaux_gymnases = niveaux_gymnases or {}  # Dict avec niveaux des gymnases
    
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
        from pycalendar.core.utils import matcher_contrainte_avec_genre
        
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
        
        Cette méthode est utilisée pour la contrainte d'overlap : éviter que plusieurs matchs
        liés par un groupe (ex: même institution, même ville) jouent simultanément.
        
        Logique:
        - Si groupes_non_simultaneite est configuré: vérifie si les matchs partagent une entité
          dans un des groupes (institutions OU noms d'équipes)
        - Si groupes_non_simultaneite est vide (mode legacy): applique à TOUTES les institutions
          qui se chevauchent (déprécié car trop large et coûteux)
        
        Args:
            match1: Premier match
            match2: Deuxième match
            
        Returns:
            True si les matchs doivent être soumis à la contrainte de non-simultanéité
        """
        if not self.groupes_non_simultaneite:
            # Mode legacy (déprécié): appliquer à toutes les institutions communes
            # NOTE: Ce mode est inefficace et sera supprimé. Configurez des groupes explicites.
            inst1 = {match1.equipe1.institution, match1.equipe2.institution}
            inst2 = {match2.equipe1.institution, match2.equipe2.institution}
            return bool(inst1 & inst2)
        
        # Mode configuré (recommandé): vérifier si les matchs partagent une entité dans un groupe
        # Les entités peuvent être des institutions OU des noms d'équipes
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
        
        # Vérifier si les matchs partagent une entité dans un des groupes configurés
        for groupe_nom, groupe_entites in self.groupes_non_simultaneite.items():
            # Entités du match1 qui sont dans ce groupe
            entites1_dans_groupe = entites1 & groupe_entites
            # Entités du match2 qui sont dans ce groupe
            entites2_dans_groupe = entites2 & groupe_entites
            
            # Si les deux matchs ont au moins une entité dans ce groupe → conflit
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
        
        if self.config.afficher_progression:
            print(f"   → {len(matchs_normaux_indices)} matchs normaux à planifier")
            print(f"   → {len(matchs_ententes_indices)} ententes disponibles (fallback)")
        
        # Filtrer les créneaux valides selon semaine_min
        creneaux_valides = [creneau for creneau in creneaux if creneau.semaine >= self.config.semaine_min]
        creneau_index_map = {j: i for i, j in enumerate([idx for idx, c in enumerate(creneaux) if c.semaine >= self.config.semaine_min])}
        
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
                    horaire_creneau_min = self._parse_horaire(creneau.horaire)
                    violation = False
                    
                    for equipe in [match.equipe1, match.equipe2]:
                        if equipe.horaires_preferes:
                            horaire_prefere_min = self._parse_horaire(equipe.horaires_preferes[0])
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
        
        # Pénalités pour préférences horaires (sophistiquée avec distance)
        # Appliqué uniquement aux matchs normaux (ententes non assignées à créneaux)
        for i in matchs_normaux_indices:
            match = matchs[i]
            for j, creneau in enumerate(creneaux_valides):
                penalty = self._calculate_time_preference_penalty(match, creneau)
                
                if penalty > 0 and (i, j) in assignment_vars:
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
            base_penalty = 2 * max(self.config.bonus_preferences_gymnases)
            
            for i in matchs_normaux_indices:
                match = matchs[i]
                for j, creneau in enumerate(creneaux_valides):
                    if (i, j) not in assignment_vars:
                        continue
                    
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
        
        # Pénalités pour gymnases par niveau (classification haut/bas niveau)
        # Applique une pénalité quand un match est assigné à un gymnase inapproprié
        # Appliqué uniquement aux matchs normaux
        # Valeurs positives = pénalité (augmente le coût, à éviter)
        if self.niveaux_gymnases and (self.config.penalite_niveau_gymnases_haut or self.config.penalite_niveau_gymnases_bas):
            for i in matchs_normaux_indices:
                match = matchs[i]
                # Déterminer le niveau du match (basé sur la poule: A1=0, A2=1, A3=2, A4=3)
                niveau_match = self._get_niveau_match(match)
                if niveau_match is None:
                    continue
                
                for j, creneau in enumerate(creneaux_valides):
                    if (i, j) not in assignment_vars:
                        continue
                    
                    # Récupérer le niveau du gymnase
                    niveau_gymnase = self.niveaux_gymnases.get(creneau.gymnase)
                    if not niveau_gymnase:
                        continue
                    
                    # Calculer la pénalité selon le niveau du gymnase et du match
                    penalite = 0
                    if niveau_gymnase == 'haut' and niveau_match < len(self.config.penalite_niveau_gymnases_haut):
                        penalite = self.config.penalite_niveau_gymnases_haut[niveau_match]
                    elif niveau_gymnase == 'bas' and niveau_match < len(self.config.penalite_niveau_gymnases_bas):
                        penalite = self.config.penalite_niveau_gymnases_bas[niveau_match]
                    
                    # Ajouter la pénalité à l'objectif avec signe NÉGATIF (on maximise l'objectif global)
                    # Pénalité positive = contribution négative = à éviter
                    # Exemple: penalite=10 pour A1 en bas niveau -> objective_terms.append(-10) -> on veut éviter
                    if penalite != 0:
                        objective_terms.append(-int(penalite) * assignment_vars[(i, j)])


        
        # CONTRAINTE SOUPLE: Espacement entre matchs d'une même équipe
        # Pour chaque équipe, pénaliser les matchs trop rapprochés
        # Appliqué uniquement aux matchs normaux
        if self.config.penalites_espacement_repos:
            # Grouper les créneaux par semaine pour chaque équipe
            for equipe_id in equipes_uniques:
                # Pour chaque paire de semaines, détecter si l'équipe joue aux deux
                for semaine1 in range(self.config.semaine_min, self.config.nb_semaines + 1):
                    for semaine2 in range(semaine1 + 1, self.config.nb_semaines + 1):
                        # Calculer le nombre de semaines de repos entre ces deux semaines
                        weeks_rest = semaine2 - semaine1 - 1
                        
                        # Vérifier si on doit pénaliser cet écart
                        if weeks_rest < len(self.config.penalites_espacement_repos):
                            penalty_value = self.config.penalites_espacement_repos[weeks_rest]
                            
                            if penalty_value > 0:
                                # Trouver tous les créneaux valides de semaine1 et semaine2
                                creneaux_s1 = [j for j, c in enumerate(creneaux_valides) if c.semaine == semaine1]
                                creneaux_s2 = [j for j, c in enumerate(creneaux_valides) if c.semaine == semaine2]
                                
                                # Trouver tous les matchs NORMAUX où cette équipe joue
                                matchs_equipe = [i for i in matchs_normaux_indices 
                                               if matchs[i].equipe1.id_unique == equipe_id or matchs[i].equipe2.id_unique == equipe_id]
                                
                                # Créer une variable pour détecter si l'équipe joue aux deux semaines
                                plays_s1 = model.NewBoolVar(f'plays_{equipe_id}_s{semaine1}')
                                plays_s2 = model.NewBoolVar(f'plays_{equipe_id}_s{semaine2}')
                                
                                # plays_s1 = 1 si l'équipe joue en semaine1
                                vars_s1 = [assignment_vars[(i, j)] 
                                          for i in matchs_equipe for j in creneaux_s1 if (i, j) in assignment_vars]
                                if vars_s1:
                                    model.Add(sum(vars_s1) >= 1).OnlyEnforceIf(plays_s1)
                                    model.Add(sum(vars_s1) == 0).OnlyEnforceIf(plays_s1.Not())
                                
                                # plays_s2 = 1 si l'équipe joue en semaine2
                                vars_s2 = [assignment_vars[(i, j)] 
                                          for i in matchs_equipe for j in creneaux_s2 if (i, j) in assignment_vars]
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
        # Appliqué uniquement aux matchs normaux
        if self.config.compaction_temporelle_actif:
            for i in matchs_normaux_indices:
                for j, creneau in enumerate(creneaux_valides):
                    if (i, j) not in assignment_vars:
                        continue
                    
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
        
        # CONTRAINTE SOUPLE 3: Espacement aller-retour (pour poules de type Aller-Retour)
        # Appliqué uniquement aux matchs normaux
        if self.config.aller_retour_espacement_actif:
            # Détecter toutes les paires aller-retour
            paires_aller_retour = []
            for i1 in matchs_normaux_indices:
                for i2 in matchs_normaux_indices:
                    if i1 < i2 and self._sont_matchs_aller_retour(matchs[i1], matchs[i2]):
                        paires_aller_retour.append((i1, i2))
            
            if paires_aller_retour:
                if self.config.afficher_progression:
                    print(f"   Détecté {len(paires_aller_retour)} paire(s) aller-retour")
                
                # Pour chaque paire aller-retour
                for i1, i2 in paires_aller_retour:
                    # Variables pour détecter si planifiés dans même semaine ou semaines consécutives
                    for j1, creneau1 in enumerate(creneaux_valides):
                        for j2, creneau2 in enumerate(creneaux_valides):
                            # Vérifier que les variables existent
                            if (i1, j1) not in assignment_vars or (i2, j2) not in assignment_vars:
                                continue
                            
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
                from pycalendar.core.solution_store import SolutionStore
                
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
