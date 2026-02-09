"""
Module de vérification post-solution des contraintes.

Vérifie qu'une solution générée respecte toutes les contraintes définies :
- Contraintes dures (bloquantes)
- Contraintes souples (pénalités)

Ce module est utilisé après la résolution pour valider la qualité de la solution.
"""

from typing import List, Dict, Tuple, Set
from dataclasses import dataclass
from collections import defaultdict

from pycalendar.core.models import Match, Creneau, Gymnase, Solution
from pycalendar.core.config import Config


@dataclass
class ViolationDetail:
    """Détail d'une violation de contrainte."""
    type_contrainte: str
    severite: str  # "DURE", "SOUPLE", ou "DURE_FIXE" (match fixe)
    description: str
    match_concerne: str = ""
    creneau_concerne: str = ""
    penalite: float = 0.0
    est_match_fixe: bool = False  # True si la violation concerne un match fixé manuellement


class SolutionValidator:
    """Valide une solution complète contre toutes les contraintes."""
    
    def __init__(self, config: Config, gymnases: Dict[str, Gymnase], 
                 obligations_presence: Dict[str, str] = {},
                 groupes_non_simultaneite: Dict[str, Set[str]] = {}):
        self.config = config
        self.gymnases = gymnases
        self.obligations_presence = obligations_presence if obligations_presence else {}
        self.groupes_non_simultaneite = groupes_non_simultaneite if groupes_non_simultaneite else {}
        self.violations: List[ViolationDetail] = []
    
    def valider_solution(self, solution: Solution) -> Tuple[bool, Dict]:
        """
        Valide une solution complète.
        
        Returns:
            (est_valide, rapport_detaille)
        """
        self.violations = []
        
        # Cas spécial : aucun match planifié
        if not solution or not solution.matchs_planifies:
            nb_non_planifies = len(solution.matchs_non_planifies) if solution else 0
            return False, {
                'est_valide': False,
                'aucun_match': True,  # Flag pour affichage spécial
                'message': 'Aucun match planifié',
                'violations': [],
                'nb_violations_dures': 0,
                'nb_violations_souples': 0,
                'violations_dures': [],
                'violations_souples': [],
                'nb_matchs_planifies': 0,
                'nb_matchs_non_planifies': nb_non_planifies,
                'taux_planification': 0.0,
                'stats_compaction': None,
                'stats_overlaps': None,
                'stats_preferences_horaires': None
            }
        
        # Construire l'état de la solution pour les vérifications
        etat_solution = self._construire_etat_solution(solution.matchs_planifies)
        
        # Exécuter toutes les vérifications
        self._verifier_disponibilite_equipes(solution.matchs_planifies)
        self._verifier_disponibilite_gymnases(solution.matchs_planifies)
        self._verifier_capacite_gymnases(solution.matchs_planifies, etat_solution)
        self._verifier_unicite_equipes_par_creneau(solution.matchs_planifies, etat_solution)
        self._verifier_max_matchs_par_semaine(solution.matchs_planifies, etat_solution)
        self._verifier_obligations_presence(solution.matchs_planifies)
        self._verifier_preferences_horaires(solution.matchs_planifies)
        self._verifier_preferences_lieux(solution.matchs_planifies)
        
        # Nouvelles vérifications (contraintes souples)
        stats_compaction = self._verifier_compaction_temporelle(solution.matchs_planifies)
        stats_overlaps = self._verifier_overlaps_institution(solution.matchs_planifies)
        
        # Séparer violations par catégorie:
        # - DURE: violations graves sur matchs planifiés par le solver
        # - DURE_FIXE: violations sur matchs importés manuellement (moins grave, hors contrôle solver)
        # - SOUPLE: pénalités d'optimisation
        violations_dures = [v for v in self.violations if v.severite == "DURE"]
        violations_dures_fixes = [v for v in self.violations if v.severite == "DURE_FIXE"]
        violations_souples = [v for v in self.violations if v.severite == "SOUPLE"]
        
        # La solution est valide si pas de violations dures (hors matchs fixes)
        # Les matchs fixes sont importés manuellement, leurs violations ne comptent pas
        est_valide = len(violations_dures) == 0
        
        # Statistiques sur les ententes
        from pycalendar.core.models import EntenteStatus
        nb_ententes = sum(1 for m in solution.matchs_planifies + solution.matchs_non_planifies 
                         if m.is_entente)
        ententes_par_status = {}
        for status in EntenteStatus:
            count = sum(1 for m in solution.matchs_planifies + solution.matchs_non_planifies 
                       if m.entente_status == status)
            if count > 0:
                ententes_par_status[status.value] = count
        
        rapport = {
            'est_valide': est_valide,
            'nb_violations_dures': len(violations_dures),
            'nb_violations_dures_fixes': len(violations_dures_fixes),
            'nb_violations_souples': len(violations_souples),
            'violations_dures': violations_dures,
            'violations_dures_fixes': violations_dures_fixes,
            'violations_souples': violations_souples,
            'nb_matchs_planifies': len(solution.matchs_planifies),
            'nb_matchs_non_planifies': len(solution.matchs_non_planifies),
            'nb_ententes': nb_ententes,
            'ententes_par_status': ententes_par_status,
            'taux_planification': solution.taux_planification(),
            'stats_compaction': stats_compaction,
            'stats_overlaps': stats_overlaps,
            'stats_preferences_horaires': getattr(self, '_stats_preferences_horaires', None)
        }
        
        return est_valide, rapport
    
    def _construire_etat_solution(self, matchs: List[Match]) -> Dict:
        """Construit l'état de la solution pour les vérifications."""
        etat = {
            'creneaux_usage': defaultdict(int),  # (semaine, gymnase, horaire) -> count
            'equipes_par_creneau': defaultdict(set),  # (semaine, horaire) -> {equipes}
            'matchs_par_equipe_semaine': defaultdict(int),  # (equipe, semaine) -> count
            'matchs_par_poule': defaultdict(int),  # poule -> count
            'matchs_par_gymnase': defaultdict(int),  # gymnase -> count
        }
        
        for match in matchs:
            if not match.creneau:
                continue
            
            creneau = match.creneau
            
            # Usage des créneaux
            key_creneau = (creneau.semaine, creneau.gymnase, creneau.horaire)
            etat['creneaux_usage'][key_creneau] += 1
            
            # Équipes par créneau
            # IMPORTANT: Utiliser id_unique pour distinguer équipes de même nom mais genre différent
            key_equipes = (creneau.semaine, creneau.horaire)
            etat['equipes_par_creneau'][key_equipes].add(match.equipe1.id_unique)
            etat['equipes_par_creneau'][key_equipes].add(match.equipe2.id_unique)
            
            # Matchs par équipe et semaine
            etat['matchs_par_equipe_semaine'][(match.equipe1.id_unique, creneau.semaine)] += 1
            etat['matchs_par_equipe_semaine'][(match.equipe2.id_unique, creneau.semaine)] += 1
            
            # Statistiques
            etat['matchs_par_poule'][match.poule] += 1
            etat['matchs_par_gymnase'][creneau.gymnase] += 1
        
        return etat
    
    def _is_fixed_match(self, match: Match) -> bool:
        """Vérifie si un match est fixé manuellement (importé, pas planifié par le solver)."""
        return match.is_fixed  # Utilise la propriété du modèle Match
    
    def _is_entente_match(self, match: Match) -> bool:
        """Vérifie si un match est une entente (joué hors calendrier)."""
        return match.is_entente  # Utilise la propriété du modèle Match
    
    def _get_severity(self, match: Match, base_severity: str = "DURE") -> str:
        """
        Retourne la sévérité appropriée selon que le match est fixe ou non.
        
        Les matchs fixes ont été importés manuellement et leurs violations ne sont pas
        la responsabilité du solver - on les signale mais avec une sévérité réduite.
        
        Les ententes ne sont pas validées de la même façon car elles sont jouées
        hors calendrier officiel.
        """
        if self._is_fixed_match(match):
            return "DURE_FIXE"  # Sera affiché séparément
        return base_severity
    
    def _verifier_disponibilite_equipes(self, matchs: List[Match]):
        """Vérifie que toutes les équipes sont disponibles."""
        for match in matchs:
            if not match.creneau:
                continue
            
            semaine = match.creneau.semaine
            horaire = match.creneau.horaire
            is_fixed = self._is_fixed_match(match)
            
            if not match.equipe1.est_disponible(semaine, horaire):
                self.violations.append(ViolationDetail(
                    type_contrainte="Disponibilité équipe",
                    severite=self._get_severity(match),
                    description=f"L'équipe {match.equipe1.nom} n'est pas disponible semaine {semaine} à {horaire}",
                    match_concerne=f"{match.equipe1.nom} vs {match.equipe2.nom}",
                    creneau_concerne=f"S{semaine} - {match.creneau.gymnase} - {horaire}",
                    penalite=10000,
                    est_match_fixe=is_fixed
                ))
            
            if not match.equipe2.est_disponible(semaine, horaire):
                self.violations.append(ViolationDetail(
                    type_contrainte="Disponibilité équipe",
                    severite=self._get_severity(match),
                    description=f"L'équipe {match.equipe2.nom} n'est pas disponible semaine {semaine} à {horaire}",
                    match_concerne=f"{match.equipe1.nom} vs {match.equipe2.nom}",
                    creneau_concerne=f"S{semaine} - {match.creneau.gymnase} - {horaire}",
                    penalite=10000,
                    est_match_fixe=is_fixed
                ))
    
    def _verifier_disponibilite_gymnases(self, matchs: List[Match]):
        """Vérifie que tous les gymnases sont disponibles."""
        for match in matchs:
            if not match.creneau:
                continue
            
            creneau = match.creneau
            gymnase = self.gymnases.get(creneau.gymnase)
            is_fixed = self._is_fixed_match(match)
            
            if not gymnase:
                self.violations.append(ViolationDetail(
                    type_contrainte="Gymnase inexistant",
                    severite=self._get_severity(match),
                    description=f"Le gymnase {creneau.gymnase} n'existe pas",
                    match_concerne=f"{match.equipe1.nom} vs {match.equipe2.nom}",
                    creneau_concerne=f"S{creneau.semaine} - {creneau.gymnase} - {creneau.horaire}",
                    penalite=10000,
                    est_match_fixe=is_fixed
                ))
                continue
            
            if not gymnase.est_disponible(creneau.semaine, creneau.horaire):
                self.violations.append(ViolationDetail(
                    type_contrainte="Disponibilité gymnase",
                    severite=self._get_severity(match),
                    description=f"Le gymnase {creneau.gymnase} n'est pas disponible à {creneau.horaire}",
                    match_concerne=f"{match.equipe1.nom} vs {match.equipe2.nom}",
                    creneau_concerne=f"S{creneau.semaine} - {creneau.gymnase} - {creneau.horaire}",
                    penalite=10000,
                    est_match_fixe=is_fixed
                ))
    
    def _verifier_capacite_gymnases(self, matchs: List[Match], etat: Dict):
        """Vérifie que la capacité des gymnases n'est pas dépassée.
        
        IMPORTANT: Cette vérification prend en compte la durée réelle des matchs (configurable).
        Un match à 15h occupe un terrain de 15h à 16h30 (handball) ou 17h (volley), donc il 
        réduit la capacité disponible des créneaux adjacents.
        
        NOTE: Les matchs en entente ne sont pas comptabilisés car ils sont joués hors calendrier.
        """
        from collections import defaultdict
        
        # Récupérer la durée d'un match depuis la config
        match_duration_minutes = self.config.duree_match_minutes
        
        # Helper function: convertir horaire "14h00" ou "14:00" en minutes depuis minuit
        def horaire_to_minutes(horaire: str) -> int:
            """Convertit '14h00' ou '14:00' en 840 (14*60)"""
            if not horaire:
                return 0
            # Normaliser: remplacer 'h' par ':' si présent
            horaire_norm = horaire.lower().replace('h', ':')
            if ':' not in horaire_norm:
                return 0
            parts = horaire_norm.split(':')
            heures = int(parts[0])
            minutes = int(parts[1]) if len(parts) > 1 and parts[1] else 0
            return heures * 60 + minutes
        
        # Helper function: vérifier si deux créneaux se chevauchent
        def creneaux_se_chevauchent(horaire_match: str, horaire_creneau: str) -> bool:
            """
            Vérifie si un match à horaire_match chevauche le créneau horaire_creneau.
            """
            match_start = horaire_to_minutes(horaire_match)
            match_end = match_start + match_duration_minutes
            
            creneau_start = horaire_to_minutes(horaire_creneau)
            creneau_end = creneau_start + 120  # Créneaux de 2h (120 minutes)
            
            # Chevauchement si: début_match < fin_créneau ET fin_match > début_créneau
            return match_start < creneau_end and match_end > creneau_start
        
        # Calculer l'occupation réelle par créneau en tenant compte des chevauchements
        # Format: {(semaine, gymnase, horaire): nb_terrains_occupes}
        occupation_reelle = defaultdict(int)
        # Tracker les matchs par créneau pour déterminer si fixes ou non
        matchs_par_creneau = defaultdict(list)
        
        for match in matchs:
            if not match.creneau:
                continue
            # Ignorer les matchs en entente (joués hors calendrier)
            if self._is_entente_match(match):
                continue
            key = (match.creneau.semaine, match.creneau.gymnase, match.creneau.horaire)
            matchs_par_creneau[key].append(match)
        
        for key_match, count_match in etat['creneaux_usage'].items():
            semaine_match, gymnase_match, horaire_match = key_match
            
            # Pour chaque match, vérifier tous les créneaux qu'il chevauche
            for key_creneau in etat['creneaux_usage'].keys():
                semaine_creneau, gymnase_creneau, horaire_creneau = key_creneau
                
                # Même gymnase et même semaine ?
                if gymnase_match == gymnase_creneau and semaine_match == semaine_creneau:
                    # Les horaires se chevauchent ?
                    if creneaux_se_chevauchent(horaire_match, horaire_creneau):
                        occupation_reelle[key_creneau] += count_match
        
        # Vérifier que la capacité n'est pas dépassée
        for key_creneau, nb_matchs_chevauchants in occupation_reelle.items():
            semaine, gymnase_nom, horaire = key_creneau
            gymnase = self.gymnases.get(gymnase_nom)
            
            if not gymnase:
                continue
            
            if nb_matchs_chevauchants > gymnase.capacite:
                # Compter le nombre de matchs à cet horaire exact (pour le message)
                nb_matchs_exact = etat['creneaux_usage'].get(key_creneau, 0)
                
                # Déterminer si la violation est due à des matchs fixes
                matchs_creneau = matchs_par_creneau.get(key_creneau, [])
                nb_fixes = sum(1 for m in matchs_creneau if self._is_fixed_match(m))
                tous_fixes = nb_fixes == len(matchs_creneau) if matchs_creneau else False
                
                self.violations.append(ViolationDetail(
                    type_contrainte="Capacité gymnase",
                    severite="DURE_FIXE" if tous_fixes else "DURE",
                    description=f"Capacité dépassée: {nb_matchs_chevauchants}/{gymnase.capacite} matchs chevauchants au gymnase {gymnase_nom} (dont {nb_matchs_exact} à cet horaire exact)",
                    creneau_concerne=f"S{semaine} - {gymnase_nom} - {horaire}",
                    penalite=500,
                    est_match_fixe=tous_fixes
                ))
    
    def _verifier_unicite_equipes_par_creneau(self, matchs: List[Match], etat: Dict):
        """Vérifie qu'une équipe ne joue pas plusieurs fois au même créneau."""
        for key_creneau, equipes in etat['equipes_par_creneau'].items():
            semaine, horaire = key_creneau
            
            # Compter les occurrences de chaque équipe (avec id_unique pour distinguer les genres)
            matchs_creneau = [m for m in matchs if m.creneau and 
                            m.creneau.semaine == semaine and 
                            m.creneau.horaire == horaire]
            
            equipes_count = defaultdict(int)
            equipes_matchs = defaultdict(list)  # Pour tracker les matchs par équipe
            for match in matchs_creneau:
                equipes_count[match.equipe1.id_unique] += 1
                equipes_count[match.equipe2.id_unique] += 1
                equipes_matchs[match.equipe1.id_unique].append(match)
                equipes_matchs[match.equipe2.id_unique].append(match)
            
            for equipe_id, count in equipes_count.items():
                if count > 1:
                    # Déterminer si tous les matchs impliqués sont fixes
                    matchs_equipe = equipes_matchs[equipe_id]
                    tous_fixes = all(self._is_fixed_match(m) for m in matchs_equipe)
                    
                    # Afficher le nom complet avec le genre pour différencier les équipes
                    equipe_nom_complet = equipe_id.replace('|', ' ')
                    self.violations.append(ViolationDetail(
                        type_contrainte="Équipe joue plusieurs fois simultanément",
                        severite="DURE_FIXE" if tous_fixes else "DURE",
                        description=f"L'équipe {equipe_nom_complet} joue {count} fois au même créneau",
                        creneau_concerne=f"S{semaine} - {horaire}",
                        penalite=1000.0,
                        est_match_fixe=tous_fixes
                    ))
    
    def _verifier_max_matchs_par_semaine(self, matchs: List[Match], etat: Dict):
        """Vérifie que les équipes ne jouent pas trop de matchs par semaine."""
        max_matchs = self.config.max_matchs_par_equipe_par_semaine
        
        # Construire un index des matchs par équipe et semaine
        matchs_par_equipe_semaine = defaultdict(list)
        for match in matchs:
            if not match.creneau:
                continue
            matchs_par_equipe_semaine[(match.equipe1.id_unique, match.creneau.semaine)].append(match)
            matchs_par_equipe_semaine[(match.equipe2.id_unique, match.creneau.semaine)].append(match)
        
        for key, count in etat['matchs_par_equipe_semaine'].items():
            equipe_id, semaine = key
            
            if count > max_matchs:
                # Déterminer si tous les matchs impliqués sont fixes
                matchs_equipe = matchs_par_equipe_semaine.get(key, [])
                tous_fixes = all(self._is_fixed_match(m) for m in matchs_equipe) if matchs_equipe else False
                
                # Afficher le nom complet avec le genre
                equipe_nom_complet = equipe_id.replace('|', ' ')
                self.violations.append(ViolationDetail(
                    type_contrainte="Trop de matchs par semaine",
                    severite="DURE_FIXE" if tous_fixes else "DURE",
                    description=f"L'équipe {equipe_nom_complet} joue {count} matchs semaine {semaine} (max: {max_matchs})",
                    penalite=500.0,
                    est_match_fixe=tous_fixes
                ))
    
    def _verifier_obligations_presence(self, matchs: List[Match]):
        """Vérifie les obligations de présence des institutions dans leurs gymnases."""
        for match in matchs:
            if not match.creneau:
                continue
            
            gymnase_nom = match.creneau.gymnase
            institution_requise = self.obligations_presence.get(gymnase_nom)
            
            if not institution_requise:
                continue
            
            inst1 = match.equipe1.institution
            inst2 = match.equipe2.institution
            is_fixed = self._is_fixed_match(match)
            
            if institution_requise not in [inst1, inst2]:
                self.violations.append(ViolationDetail(
                    type_contrainte="Obligation de présence",
                    severite=self._get_severity(match),
                    description=f"Match au gymnase {gymnase_nom} mais aucune équipe de {institution_requise}",
                    match_concerne=f"{match.equipe1.nom} ({inst1}) vs {match.equipe2.nom} ({inst2})",
                    creneau_concerne=f"S{match.creneau.semaine} - {gymnase_nom} - {match.creneau.horaire}",
                    penalite=1000.0,
                    est_match_fixe=is_fixed
                ))
    
    def _parse_horaire(self, horaire_str: str) -> int:
        """
        Convertit une chaîne d'horaire en minutes depuis minuit.
        Supporte: "14:00", "14H00", "14H", "14h00", "14h"
        """
        horaire_str = horaire_str.upper().replace('H', ':')
        if ':' in horaire_str:
            parts = horaire_str.split(':')
            heures = int(parts[0])
            minutes = int(parts[1]) if len(parts) > 1 and parts[1] else 0
        else:
            heures = int(horaire_str)
            minutes = 0
        return heures * 60 + minutes
    
    def _verifier_preferences_horaires(self, matchs: List[Match]):
        """
        Vérifie le respect des préférences d'horaires (contrainte souple).
        Calcule des statistiques détaillées sur les violations.
        """
        stats = {
            'nb_matchs_avec_preferences': 0,
            'nb_matchs_respectes': 0,
            'nb_matchs_dans_tolerance': 0,
            'nb_violations_avant_1_equipe': 0,
            'nb_violations_avant_2_equipes': 0,
            'nb_violations_apres': 0,
            'distance_totale': 0.0,
            'distance_max': 0.0,
            'penalite_totale': 0.0,
            'tolerance_minutes': self.config.penalite_horaire_tolerance
        }
        
        for match in matchs:
            if not match.creneau:
                continue
            
            horaire = match.creneau.horaire
            
            # Vérifier si au moins une équipe a une préférence
            equipe1_a_pref = match.equipe1.horaires_preferes and len(match.equipe1.horaires_preferes) > 0
            equipe2_a_pref = match.equipe2.horaires_preferes and len(match.equipe2.horaires_preferes) > 0
            
            if not equipe1_a_pref and not equipe2_a_pref:
                continue
            
            stats['nb_matchs_avec_preferences'] += 1
            
            # Parser l'horaire du match
            try:
                horaire_match_minutes = self._parse_horaire(horaire)
            except:
                continue
            
            # Analyser chaque équipe
            violations_equipe = []
            equipes_avant = 0
            
            for idx, (equipe, equipe_nom) in enumerate([(match.equipe1, "équipe1"), (match.equipe2, "équipe2")]):
                if not equipe.horaires_preferes or len(equipe.horaires_preferes) == 0:
                    continue
                
                # Parser l'horaire préféré (on prend le premier si plusieurs)
                try:
                    horaire_pref_minutes = self._parse_horaire(equipe.horaires_preferes[0])
                except:
                    continue
                
                # Calculer la distance en minutes
                distance_minutes = abs(horaire_match_minutes - horaire_pref_minutes)
                distance_heures = distance_minutes / 60.0  # Pour l'affichage
                
                # Vérifier si le match est avant l'horaire préféré
                est_avant = horaire_match_minutes < horaire_pref_minutes
                
                if est_avant:
                    equipes_avant += 1
                
                # Appliquer la tolérance
                tolerance = self.config.penalite_horaire_tolerance
                dans_tolerance = distance_minutes <= tolerance
                
                # Si pas égal mais dans la tolérance, pas de violation
                if distance_minutes > 0 and not dans_tolerance:
                    violations_equipe.append({
                        'equipe': equipe,
                        'equipe_nom': equipe_nom,
                        'horaire_pref': equipe.horaires_preferes[0],
                        'distance_minutes': distance_minutes,
                        'distance_heures': distance_heures,
                        'est_avant': est_avant,
                        'dans_tolerance': False
                    })
                    
                    stats['distance_totale'] += distance_heures
                    stats['distance_max'] = max(stats['distance_max'], distance_heures)
                elif distance_minutes > 0 and dans_tolerance:
                    # Dans la tolérance : compter séparément
                    violations_equipe.append({
                        'equipe': equipe,
                        'equipe_nom': equipe_nom,
                        'horaire_pref': equipe.horaires_preferes[0],
                        'distance_minutes': distance_minutes,
                        'distance_heures': distance_heures,
                        'est_avant': est_avant,
                        'dans_tolerance': True
                    })
            
            # Si aucune violation hors tolérance, le match respecte les préférences
            violations_hors_tolerance = [v for v in violations_equipe if not v.get('dans_tolerance', False)]
            violations_dans_tolerance = [v for v in violations_equipe if v.get('dans_tolerance', False)]
            
            if len(violations_equipe) == 0:
                stats['nb_matchs_respectes'] += 1
                continue
            elif len(violations_hors_tolerance) == 0:
                # Toutes les violations sont dans la tolérance
                stats['nb_matchs_dans_tolerance'] += 1
                continue
            
            # Déterminer le multiplicateur de pénalité
            if equipes_avant == 2:
                multiplicateur = self.config.penalite_avant_horaire_min_deux
                stats['nb_violations_avant_2_equipes'] += 1
                
                # Ajouter les violations avec pénalité calculée (uniquement hors tolérance)
                # Utiliser le même calcul que CP-SAT : pénalité sur distance TOTALE (pas seulement l'excédent)
                diviseur = self.config.penalite_horaire_diviseur
                
                for viol in violations_hors_tolerance:
                    # Calculer la pénalité sur la distance TOTALE (pas distance - tolerance)
                    penalite = multiplicateur * ((viol['distance_minutes'] / diviseur) ** 2)
                    stats['penalite_totale'] += penalite
                    
                    direction = "avant" if viol['est_avant'] else "après"
                    
                    self.violations.append(ViolationDetail(
                        type_contrainte="Préférence horaire",
                        severite="SOUPLE",
                        description=f"{viol['equipe'].nom} préfère {viol['horaire_pref']} mais joue à {horaire} "
                                    f"({direction}, distance: {viol['distance_heures']:.1f}h, mult: {multiplicateur:.0f})",
                        match_concerne=f"{match.equipe1.nom} vs {match.equipe2.nom}",
                        creneau_concerne=f"S{match.creneau.semaine} - {match.creneau.gymnase} - {horaire}",
                        penalite=penalite
                    ))
            elif equipes_avant == 1:
                # Ne pas relever de violation si seulement une équipe joue avant son horaire préféré
                stats['nb_violations_avant_1_equipe'] += 1
                continue
            else:
                # Les deux équipes jouent après leur horaire préféré - violation normale
                multiplicateur = 10.0
                stats['nb_violations_apres'] += len(violations_equipe)
                
                # Ajouter les violations avec pénalité calculée (uniquement hors tolérance)
                diviseur = self.config.penalite_horaire_diviseur
                
                for viol in violations_hors_tolerance:
                    # Calculer la pénalité sur la distance TOTALE (pas distance - tolerance)
                    penalite = multiplicateur * ((viol['distance_minutes'] / diviseur) ** 2)
                    stats['penalite_totale'] += penalite
                    
                    direction = "avant" if viol['est_avant'] else "après"
                    
                    self.violations.append(ViolationDetail(
                        type_contrainte="Préférence horaire",
                        severite="SOUPLE",
                        description=f"{viol['equipe'].nom} préfère {viol['horaire_pref']} mais joue à {horaire} "
                                    f"({direction}, distance: {viol['distance_heures']:.1f}h, mult: {multiplicateur:.0f})",
                        match_concerne=f"{match.equipe1.nom} vs {match.equipe2.nom}",
                        creneau_concerne=f"S{match.creneau.semaine} - {match.creneau.gymnase} - {horaire}",
                        penalite=penalite
                    ))
        
        # Stocker les stats pour le rapport
        self._stats_preferences_horaires = stats
    
    def _verifier_preferences_lieux(self, matchs: List[Match]):
        """Vérifie le respect des préférences de lieux (contrainte souple)."""
        for match in matchs:
            if not match.creneau:
                continue
            
            gymnase = match.creneau.gymnase
            
            # Calculer la pénalité avec le système de bonus
            if not self.config.bonus_preferences_gymnases:
                continue
                
            base_penalty = 2 * max(self.config.bonus_preferences_gymnases)
            
            # Vérifier équipe 1
            if match.equipe1.lieux_preferes:
                rang_trouve = None
                for rang, gymnase_pref in enumerate(match.equipe1.lieux_preferes):
                    if gymnase_pref == gymnase:
                        rang_trouve = rang
                        break
                
                if rang_trouve is not None:
                    bonus = self.config.bonus_preferences_gymnases[rang_trouve] if rang_trouve < len(self.config.bonus_preferences_gymnases) else 0
                    penalite = base_penalty - bonus
                else:
                    # Afficher les préférences non-None
                    prefs_non_vides = [g for g in match.equipe1.lieux_preferes[:3] if g is not None]
                    penalite = base_penalty
                    self.violations.append(ViolationDetail(
                        type_contrainte="Préférence lieu",
                        severite="SOUPLE",
                        description=f"{match.equipe1.nom} préfère {prefs_non_vides} mais joue à {gymnase}",
                        match_concerne=f"{match.equipe1.nom} vs {match.equipe2.nom}",
                        creneau_concerne=f"S{match.creneau.semaine} - {gymnase} - {match.creneau.horaire}",
                        penalite=penalite
                    ))
            
            # Vérifier équipe 2
            if match.equipe2.lieux_preferes:
                rang_trouve = None
                for rang, gymnase_pref in enumerate(match.equipe2.lieux_preferes):
                    if gymnase_pref == gymnase:
                        rang_trouve = rang
                        break
                
                if rang_trouve is not None:
                    bonus = self.config.bonus_preferences_gymnases[rang_trouve] if rang_trouve < len(self.config.bonus_preferences_gymnases) else 0
                    penalite = base_penalty - bonus
                else:
                    # Afficher les préférences non-None
                    prefs_non_vides = [g for g in match.equipe2.lieux_preferes[:3] if g is not None]
                    penalite = base_penalty
                    self.violations.append(ViolationDetail(
                        type_contrainte="Préférence lieu",
                        severite="SOUPLE",
                        description=f"{match.equipe2.nom} préfère {prefs_non_vides} mais joue à {gymnase}",
                        match_concerne=f"{match.equipe1.nom} vs {match.equipe2.nom}",
                        creneau_concerne=f"S{match.creneau.semaine} - {gymnase} - {match.creneau.horaire}",
                        penalite=penalite
                    ))
    
    def _verifier_compaction_temporelle(self, matchs: List[Match]) -> Dict:
        """
        Vérifie la compaction temporelle (distribution des matchs dans le calendrier).
        
        Returns:
            Dict avec statistiques sur la répartition temporelle
        """
        stats = {
            'matchs_par_semaine': defaultdict(int),
            'matchs_palier_ideal': 0,
            'matchs_palier_acceptable': 0,
            'matchs_tardifs': 0,
            'penalite_compaction': 0.0
        }
        
        if not self.config.compaction_temporelle_actif:
            return stats

        penalites_config = self.config.compaction_penalites_par_semaine or []
        if not penalites_config:
            return stats
        
        for match in matchs:
            if not match.creneau:
                continue
            
            semaine = match.creneau.semaine
            stats['matchs_par_semaine'][semaine] += 1
            
            # Récupérer la pénalité pour cette semaine (indice 0 = semaine 1)
            if semaine <= len(penalites_config):
                penalty = penalites_config[semaine - 1]
            else:
                # Si on dépasse le nb de semaines définies, utiliser la dernière pénalité
                penalty = penalites_config[-1]
            
            # Statistiques par catégorie (pour compatibilité avec l'ancienne version)
            if penalty == 0:
                stats['matchs_palier_ideal'] += 1
            elif penalty <= 15:  # Pénalités faibles
                stats['matchs_palier_acceptable'] += 1
            else:  # Pénalités fortes
                stats['matchs_tardifs'] += 1
            
            if penalty > 0:
                stats['penalite_compaction'] += penalty
                self.violations.append(ViolationDetail(
                    type_contrainte="Compaction temporelle",
                    severite="SOUPLE",
                    description=f"Match en semaine {semaine} (pénalité: {penalty})",
                    match_concerne=f"{match.equipe1.nom} vs {match.equipe2.nom}",
                    creneau_concerne=f"S{semaine} - {match.creneau.gymnase} - {match.creneau.horaire}",
                    penalite=penalty
                ))
        
        return stats
    
    def _verifier_overlaps_institution(self, matchs: List[Match]) -> Dict:
        """
        Vérifie les overlaps d'institution (matchs simultanés de même institution).
        
        Returns:
            Dict avec statistiques sur les overlaps
        """
        stats = {
            'nb_overlaps': 0,
            'penalite_overlaps': 0.0,
            'overlaps_details': []
        }
        
        if not self.config.overlap_institution_actif:
            return stats
        
        # Grouper les matchs par créneau (semaine, horaire, gymnase)
        matchs_par_creneau = defaultdict(list)
        for match in matchs:
            if match.creneau:
                key = (match.creneau.semaine, match.creneau.horaire, match.creneau.gymnase)
                matchs_par_creneau[key].append(match)
        
        # Vérifier les overlaps pour chaque créneau
        for key_creneau, matchs_liste in matchs_par_creneau.items():
            if len(matchs_liste) < 2:
                continue
            
            # Comparer chaque paire de matchs
            for i, match1 in enumerate(matchs_liste):
                for match2 in matchs_liste[i+1:]:
                    inst1 = {match1.equipe1.institution, match1.equipe2.institution}
                    inst2 = {match2.equipe1.institution, match2.equipe2.institution}
                    
                    # Vérifier si les institutions se chevauchent
                    overlap_institutions = inst1 & inst2
                    if overlap_institutions:
                        # Vérifier si ces institutions appartiennent au même groupe de non-simultanéité
                        doit_signaler = False
                        if self.groupes_non_simultaneite:
                            # Vérifier si les institutions qui se chevauchent sont dans le même groupe
                            for groupe, institutions_groupe in self.groupes_non_simultaneite.items():
                                if any(inst in institutions_groupe for inst in overlap_institutions):
                                    doit_signaler = True
                                    break
                        else:
                            # Mode legacy: surveiller toutes les institutions
                            institutions_a_surveiller = self.config.overlap_institution_institutions
                            if not institutions_a_surveiller or any(inst in institutions_a_surveiller for inst in overlap_institutions):
                                doit_signaler = True
                        
                        if doit_signaler:
                            stats['nb_overlaps'] += 1
                            stats['penalite_overlaps'] += self.config.overlap_institution_poids
                            
                            semaine, horaire, gymnase = key_creneau
                            overlap_detail = {
                                'match1': f"{match1.equipe1.nom} vs {match1.equipe2.nom}",
                                'match2': f"{match2.equipe1.nom} vs {match2.equipe2.nom}",
                                'institutions_partagees': list(overlap_institutions),
                                'creneau': f"S{semaine} - {gymnase} - {horaire}"
                            }
                            stats['overlaps_details'].append(overlap_detail)
                            
                            self.violations.append(ViolationDetail(
                                type_contrainte="Overlap institution",
                                severite="SOUPLE",
                                description=f"Institution(s) {', '.join(overlap_institutions)} avec matchs simultanés",
                                match_concerne=f"{match1.equipe1.nom} vs {match1.equipe2.nom} ET {match2.equipe1.nom} vs {match2.equipe2.nom}",
                                creneau_concerne=f"S{semaine} - {gymnase} - {horaire}",
                                penalite=self.config.overlap_institution_poids
                            ))
        
        return stats


def afficher_rapport_validation(rapport: Dict) -> None:
    """Affiche un rapport de validation formaté."""
    from pycalendar.core.console import (
        print_header, print_section, print_subsection,
        print_success, print_error, print_warning, print_info,
        print_key_value, print_detail, print_separator, print_blank
    )
    
    print_section("Validation des contraintes", "🔍")
    
    # Cas spécial : aucun match planifié
    if rapport.get('aucun_match'):
        print_warning(f"Aucun match planifié ({rapport['nb_matchs_non_planifies']} matchs non planifiés)")
        print_info("La validation des contraintes n'est pas applicable")
        return
    
    # Résumé concis
    print_key_value("Matchs planifiés", f"{rapport['nb_matchs_planifies']} ({rapport['taux_planification']:.1f}%)")
    if rapport['nb_matchs_non_planifies'] > 0:
        print_key_value("Non planifiés", rapport['nb_matchs_non_planifies'])
    
    # Récupérer les violations sur matchs fixes (si présentes)
    violations_fixes = rapport.get('violations_dures_fixes', [])
    nb_fixes = rapport.get('nb_violations_dures_fixes', len(violations_fixes))
    
    # Statut principal
    print_blank()
    if rapport['est_valide']:
        if rapport['nb_violations_souples'] == 0 and nb_fixes == 0:
            print_success("Solution valide - toutes les contraintes respectées")
        elif nb_fixes > 0:
            # Solution valide (solver OK) mais problèmes sur matchs importés
            print_success(f"Solution valide")
            print_warning(f"{nb_fixes} problème(s) sur matchs importés (hors contrôle solver)")
        else:
            print_success(f"Solution valide ({rapport['nb_violations_souples']} contrainte(s) souple(s) non optimale(s))")
    else:
        print_error(f"Solution invalide - {rapport['nb_violations_dures']} contrainte(s) dure(s) violée(s)")
    
    # Détails des violations dures (matchs planifiés par le solver)
    if rapport['violations_dures']:
        print_subsection("Contraintes dures violées")
        
        violations_par_type = defaultdict(list)
        for v in rapport['violations_dures']:
            violations_par_type[v.type_contrainte].append(v)
        
        for type_contrainte, violations in violations_par_type.items():
            print_detail(f"{type_contrainte}: {len(violations)} violation(s)", 1)
            for v in violations[:3]:
                print_detail(f"{v.description}", 2)
            if len(violations) > 3:
                print_detail(f"... +{len(violations) - 3} autre(s)", 2)
    
    # Violations sur matchs fixes (affichage réduit, informatif)
    if violations_fixes:
        print_subsection("Problèmes sur matchs importés (📌)")
        print_info("Ces matchs ont été importés manuellement - vérifiez les données sources")
        
        violations_par_type = defaultdict(list)
        for v in violations_fixes:
            violations_par_type[v.type_contrainte].append(v)
        
        for type_contrainte, violations in violations_par_type.items():
            print_detail(f"{type_contrainte}: {len(violations)}", 1)
            # Montrer seulement 2 exemples pour les matchs fixes
            for v in violations[:2]:
                print_detail(f"{v.description}", 2)
            if len(violations) > 2:
                print_detail(f"... +{len(violations) - 2} autre(s)", 2)
    
    # Résumé des violations souples (juste les totaux)
    if rapport['violations_souples']:
        print_subsection("Contraintes souples (pénalités)")
        
        violations_par_type = defaultdict(list)
        for v in rapport['violations_souples']:
            violations_par_type[v.type_contrainte].append(v)
        
        for type_contrainte, violations in violations_par_type.items():
            penalite_totale = sum(v.penalite for v in violations)
            print_detail(f"{type_contrainte}: {len(violations)} (pénalité: {penalite_totale:.0f})", 1)
    
    # Statistiques préférences horaires (si pertinentes)
    if rapport.get('stats_preferences_horaires'):
        stats = rapport['stats_preferences_horaires']
        if stats.get('nb_matchs_avec_preferences', 0) > 0:
            print_subsection("Préférences d'horaires")
            
            nb_prefs = stats['nb_matchs_avec_preferences']
            nb_respectes = stats['nb_matchs_respectes']
            nb_tolerance = stats.get('nb_matchs_dans_tolerance', 0)
            taux = ((nb_respectes + nb_tolerance) / nb_prefs * 100) if nb_prefs > 0 else 100
            
            print_detail(f"Respectées: {nb_respectes + nb_tolerance}/{nb_prefs} ({taux:.0f}%)", 1)
            if stats.get('penalite_totale', 0) > 0:
                print_detail(f"Pénalité: {stats['penalite_totale']:.0f}", 1)
