"""
Module de vérification post-solution des contraintes.
Vérifie qu'une solution générée respecte toute            # Usage des créneaux
            key_creneau = (creneau.semaine, creneau.gymnase, creneau.horaire)
            etat['creneaux_usage'][key_creneau] += 1
            
            # Équipes par créneau (semaine, horaire) pour détecter conflits
            # IMPORTANT: Utiliser id_unique pour distinguer équipes de même nom mais genre différent
            key_equipes = (creneau.semaine, creneau.horaire)
            etat['equipes_par_creneau'][key_equipes].add(match.equipe1.id_unique)
            etat['equipes_par_creneau'][key_equipes].add(match.equipe2.id_unique)
            
            # Matchs par équipe et semaine
            etat['matchs_par_equipe_semaine'][(match.equipe1.id_unique, creneau.semaine)] += 1
            etat['matchs_par_equipe_semaine'][(match.equipe2.id_unique, creneau.semaine)] += 1intes.
"""

from typing import List, Dict, Tuple
from dataclasses import dataclass
from collections import defaultdict

from core.models import Match, Creneau, Gymnase, Solution
from core.config import Config


@dataclass
class ViolationDetail:
    """Détail d'une violation de contrainte."""
    type_contrainte: str
    severite: str  # "DURE" ou "SOUPLE"
    description: str
    match_concerne: str = ""
    creneau_concerne: str = ""
    penalite: float = 0.0


class SolutionValidator:
    """Valide une solution complète contre toutes les contraintes."""
    
    def __init__(self, config: Config, gymnases: Dict[str, Gymnase], 
                 obligations_presence: Dict[str, str] = {}):
        self.config = config
        self.gymnases = gymnases
        self.obligations_presence = obligations_presence if obligations_presence else {}
        self.violations: List[ViolationDetail] = []
    
    def valider_solution(self, solution: Solution) -> Tuple[bool, Dict]:
        """
        Valide une solution complète.
        
        Returns:
            (est_valide, rapport_detaille)
        """
        self.violations = []
        
        if not solution or not solution.matchs_planifies:
            return False, {
                'est_valide': False,
                'message': 'Aucun match planifié',
                'violations': []
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
        
        # Séparer violations dures et souples
        violations_dures = [v for v in self.violations if v.severite == "DURE"]
        violations_souples = [v for v in self.violations if v.severite == "SOUPLE"]
        
        est_valide = len(violations_dures) == 0
        
        rapport = {
            'est_valide': est_valide,
            'nb_violations_dures': len(violations_dures),
            'nb_violations_souples': len(violations_souples),
            'violations_dures': violations_dures,
            'violations_souples': violations_souples,
            'nb_matchs_planifies': len(solution.matchs_planifies),
            'nb_matchs_non_planifies': len(solution.matchs_non_planifies),
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
    
    def _verifier_disponibilite_equipes(self, matchs: List[Match]):
        """Vérifie que toutes les équipes sont disponibles."""
        for match in matchs:
            if not match.creneau:
                continue
            
            semaine = match.creneau.semaine
            horaire = match.creneau.horaire
            
            if not match.equipe1.est_disponible(semaine, horaire):
                self.violations.append(ViolationDetail(
                    type_contrainte="Disponibilité équipe",
                    severite="DURE",
                    description=f"L'équipe {match.equipe1.nom} n'est pas disponible semaine {semaine} à {horaire}",
                    match_concerne=f"{match.equipe1.nom} vs {match.equipe2.nom}",
                    creneau_concerne=f"S{semaine} - {match.creneau.gymnase} - {horaire}",
                    penalite=self.config.poids_indisponibilite
                ))
            
            if not match.equipe2.est_disponible(semaine, horaire):
                self.violations.append(ViolationDetail(
                    type_contrainte="Disponibilité équipe",
                    severite="DURE",
                    description=f"L'équipe {match.equipe2.nom} n'est pas disponible semaine {semaine} à {horaire}",
                    match_concerne=f"{match.equipe1.nom} vs {match.equipe2.nom}",
                    creneau_concerne=f"S{semaine} - {match.creneau.gymnase} - {horaire}",
                    penalite=self.config.poids_indisponibilite
                ))
    
    def _verifier_disponibilite_gymnases(self, matchs: List[Match]):
        """Vérifie que tous les gymnases sont disponibles."""
        for match in matchs:
            if not match.creneau:
                continue
            
            creneau = match.creneau
            gymnase = self.gymnases.get(creneau.gymnase)
            
            if not gymnase:
                self.violations.append(ViolationDetail(
                    type_contrainte="Gymnase inexistant",
                    severite="DURE",
                    description=f"Le gymnase {creneau.gymnase} n'existe pas",
                    match_concerne=f"{match.equipe1.nom} vs {match.equipe2.nom}",
                    creneau_concerne=f"S{creneau.semaine} - {creneau.gymnase} - {creneau.horaire}",
                    penalite=self.config.poids_indisponibilite
                ))
                continue
            
            if not gymnase.est_disponible(creneau.semaine, creneau.horaire):
                self.violations.append(ViolationDetail(
                    type_contrainte="Disponibilité gymnase",
                    severite="DURE",
                    description=f"Le gymnase {creneau.gymnase} n'est pas disponible à {creneau.horaire}",
                    match_concerne=f"{match.equipe1.nom} vs {match.equipe2.nom}",
                    creneau_concerne=f"S{creneau.semaine} - {creneau.gymnase} - {creneau.horaire}",
                    penalite=self.config.poids_indisponibilite
                ))
    
    def _verifier_capacite_gymnases(self, matchs: List[Match], etat: Dict):
        """Vérifie que la capacité des gymnases n'est pas dépassée."""
        for key_creneau, count in etat['creneaux_usage'].items():
            semaine, gymnase_nom, horaire = key_creneau
            gymnase = self.gymnases.get(gymnase_nom)
            
            if not gymnase:
                continue
            
            if count > gymnase.capacite:
                self.violations.append(ViolationDetail(
                    type_contrainte="Capacité gymnase",
                    severite="DURE",
                    description=f"Capacité dépassée: {count}/{gymnase.capacite} matchs au gymnase {gymnase_nom}",
                    creneau_concerne=f"S{semaine} - {gymnase_nom} - {horaire}",
                    penalite=self.config.poids_capacite_gymnase
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
            for match in matchs_creneau:
                equipes_count[match.equipe1.id_unique] += 1
                equipes_count[match.equipe2.id_unique] += 1
            
            for equipe_id, count in equipes_count.items():
                if count > 1:
                    # Extraire le nom pour l'affichage (avant le |)
                    equipe_nom = equipe_id.split('|')[0]
                    self.violations.append(ViolationDetail(
                        type_contrainte="Équipe joue plusieurs fois simultanément",
                        severite="DURE",
                        description=f"L'équipe {equipe_nom} joue {count} fois au même créneau",
                        creneau_concerne=f"S{semaine} - {horaire}",
                        penalite=1000.0
                    ))
    
    def _verifier_max_matchs_par_semaine(self, matchs: List[Match], etat: Dict):
        """Vérifie que les équipes ne jouent pas trop de matchs par semaine."""
        max_matchs = self.config.max_matchs_par_equipe_par_semaine
        
        for key, count in etat['matchs_par_equipe_semaine'].items():
            equipe, semaine = key
            
            if count > max_matchs:
                self.violations.append(ViolationDetail(
                    type_contrainte="Trop de matchs par semaine",
                    severite="DURE",
                    description=f"L'équipe {equipe} joue {count} matchs semaine {semaine} (max: {max_matchs})",
                    penalite=500.0
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
            
            if institution_requise not in [inst1, inst2]:
                self.violations.append(ViolationDetail(
                    type_contrainte="Obligation de présence",
                    severite="DURE",
                    description=f"Match au gymnase {gymnase_nom} mais aucune équipe de {institution_requise}",
                    match_concerne=f"{match.equipe1.nom} ({inst1}) vs {match.equipe2.nom} ({inst2})",
                    creneau_concerne=f"S{match.creneau.semaine} - {gymnase_nom} - {match.creneau.horaire}",
                    penalite=1000.0
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
            elif equipes_avant == 1:
                multiplicateur = self.config.penalite_avant_horaire_min
                stats['nb_violations_avant_1_equipe'] += 1
            else:
                multiplicateur = 10.0
                stats['nb_violations_apres'] += len(violations_equipe)
            
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
        
        for match in matchs:
            if not match.creneau:
                continue
            
            semaine = match.creneau.semaine
            stats['matchs_par_semaine'][semaine] += 1
            
            # Récupérer la pénalité pour cette semaine (indice 0 = semaine 1)
            if semaine <= len(self.config.compaction_penalites_par_semaine):
                penalty = self.config.compaction_penalites_par_semaine[semaine - 1]
            else:
                # Si on dépasse le nb de semaines définies, utiliser la dernière pénalité
                penalty = self.config.compaction_penalites_par_semaine[-1]
            
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
    print("\n" + "="*60)
    print("RAPPORT DE VALIDATION DES CONTRAINTES")
    print("="*60)
    
    print(f"\n📊 Résumé:")
    print(f"  • Matchs planifiés: {rapport['nb_matchs_planifies']}")
    print(f"  • Matchs non planifiés: {rapport['nb_matchs_non_planifies']}")
    print(f"  • Taux de planification: {rapport['taux_planification']:.1f}%")
    
    print(f"\n🔍 Contraintes:")
    print(f"  • Violations DURES: {rapport['nb_violations_dures']}")
    print(f"  • Violations SOUPLES: {rapport['nb_violations_souples']}")
    
    if rapport['est_valide']:
        print(f"\n✅ SOLUTION VALIDE - Toutes les contraintes dures sont respectées!")
    else:
        print(f"\n❌ SOLUTION INVALIDE - {rapport['nb_violations_dures']} contrainte(s) dure(s) violée(s)")
    
    # Afficher les violations dures
    if rapport['violations_dures']:
        print("\n" + "="*60)
        print("⚠️  VIOLATIONS DE CONTRAINTES DURES")
        print("="*60)
        
        violations_par_type = defaultdict(list)
        for v in rapport['violations_dures']:
            violations_par_type[v.type_contrainte].append(v)
        
        for type_contrainte, violations in violations_par_type.items():
            print(f"\n🔴 {type_contrainte} ({len(violations)} violation(s)):")
            for i, v in enumerate(violations[:5], 1):  # Limiter à 5 par type
                print(f"  {i}. {v.description}")
                if v.match_concerne:
                    print(f"     Match: {v.match_concerne}")
                if v.creneau_concerne:
                    print(f"     Créneau: {v.creneau_concerne}")
            
            if len(violations) > 5:
                print(f"  ... et {len(violations) - 5} autre(s)")
    
    # Afficher les violations souples
    if rapport['violations_souples']:
        print("\n" + "="*60)
        print("ℹ️  VIOLATIONS DE CONTRAINTES SOUPLES")
        print("="*60)
        
        violations_par_type = defaultdict(list)
        for v in rapport['violations_souples']:
            violations_par_type[v.type_contrainte].append(v)
        
        for type_contrainte, violations in violations_par_type.items():
            print(f"\n🟡 {type_contrainte} ({len(violations)} violation(s)):")
            # Juste compter pour les souples, ne pas tout afficher
            penalite_totale = sum(v.penalite for v in violations)
            print(f"   Pénalité totale: {penalite_totale:.0f}")
    
    # Afficher les statistiques détaillées sur les préférences d'horaires
    if rapport.get('stats_preferences_horaires'):
        stats = rapport['stats_preferences_horaires']
        print("\n" + "="*60)
        print("⏰ STATISTIQUES PRÉFÉRENCES D'HORAIRES")
        print("="*60)
        
        # Afficher la tolérance configurée
        tolerance = stats.get('tolerance_minutes', 0)
        if tolerance > 0:
            print(f"\n⚙️  Tolérance configurée: {tolerance:.0f} minutes ({tolerance/60:.1f}h)")
        
        print(f"\n📊 Vue d'ensemble:")
        print(f"  • Matchs avec préférences: {stats['nb_matchs_avec_preferences']}")
        print(f"  • Matchs respectés exactement: {stats['nb_matchs_respectes']}")
        if tolerance > 0:
            print(f"  • Matchs dans la tolérance: {stats.get('nb_matchs_dans_tolerance', 0)}")
            nb_total_acceptables = stats['nb_matchs_respectes'] + stats.get('nb_matchs_dans_tolerance', 0)
            if stats['nb_matchs_avec_preferences'] > 0:
                taux_respect_total = (nb_total_acceptables / stats['nb_matchs_avec_preferences']) * 100
                print(f"  • Taux de respect total (exact + tolérance): {taux_respect_total:.1f}%")
        if stats['nb_matchs_avec_preferences'] > 0:
            taux_respect_exact = (stats['nb_matchs_respectes'] / stats['nb_matchs_avec_preferences']) * 100
            print(f"  • Taux de respect exact: {taux_respect_exact:.1f}%")
        
        print(f"\n📉 Violations hors tolérance par catégorie:")
        print(f"  • Match AVANT horaire (1 équipe): {stats['nb_violations_avant_1_equipe']} (mult. 100)")
        print(f"  • Match AVANT horaire (2 équipes): {stats['nb_violations_avant_2_equipes']} (mult. 300)")
        print(f"  • Match APRÈS horaire: {stats['nb_violations_apres']} (mult. 10)")
        
        print(f"\n📏 Distances (hors tolérance uniquement):")
        print(f"  • Distance totale: {stats['distance_totale']:.1f}h")
        print(f"  • Distance maximale: {stats['distance_max']:.1f}h")
        nb_matchs_acceptables = stats['nb_matchs_respectes'] + stats.get('nb_matchs_dans_tolerance', 0)
        if stats['nb_matchs_avec_preferences'] > nb_matchs_acceptables:
            nb_violations = stats['nb_matchs_avec_preferences'] - nb_matchs_acceptables
            distance_moyenne = stats['distance_totale'] / nb_violations if nb_violations > 0 else 0
            print(f"  • Distance moyenne par violation: {distance_moyenne:.1f}h")
        
        print(f"\n💰 Pénalités:")
        print(f"  • Pénalité totale: {stats['penalite_totale']:.0f}")
    
    print("\n" + "="*60)
