"""Main scheduling pipeline orchestrator."""

from typing import Dict, List, Optional
from pathlib import Path
from pycalendar.core.models import Equipe, Gymnase, Solution, CoachGroup
from pycalendar.core.config import Config
from pycalendar.data.data_source import DataSource
from pycalendar.data.validators import DataValidator
from pycalendar.data.transformers import DataTransformer
from pycalendar.generators.multi_pool_generator import MultiPoolGenerator
from pycalendar.exporters.excel_exporter import ExcelExporter
from pycalendar.core.statistics import Statistics
from pycalendar.interface.core.generator import InterfaceGenerator
from pycalendar.validation.solution_validator import SolutionValidator, afficher_rapport_validation
from pycalendar.analysis import calculate_penalty_breakdown
from pycalendar.core.console import (
    print_banner, print_header, print_section, print_subsection,
    print_success, print_error, print_warning, print_info, print_detail,
    print_key_value, print_separator, print_blank, format_solution_summary,
    LoadingReport, LoadingResult
)

try:
    from pycalendar.solvers.cpsat_solver import CPSATSolver
    CPSAT_AVAILABLE = True
except ImportError:
    CPSAT_AVAILABLE = False


class SchedulingPipeline:
    """Main pipeline for sports scheduling."""
    
    def __init__(self, config: Config):
        self.config = config
        self.calendar_manager = config.calendar_manager
        self.source = DataSource(config.fichier_donnees, self.calendar_manager)
        self.obligations_presence = {}
        self.groupes_non_simultaneite = {}
        self.ententes = {}
        self.contraintes_temporelles = {}
        self.niveaux_gymnases = {}
        self.priorites_genre_gymnases = {}
        self.coach_groups = {}
        self.types_poules = {}  # Store pool types for export
    
    def run(self):
        """Execute the complete scheduling pipeline."""
        # Déterminer l'emoji du sport depuis la config
        sport_emoji = "🏐"  # Par défaut volleyball
        sport_name = getattr(self.config, 'sport', 'Sports')
        if hasattr(self.config, 'sport'):
            sport = self.config.sport.lower()
            if 'basket' in sport:
                sport_emoji = "🏀"
            elif 'hand' in sport:
                sport_emoji = "🤾"
            elif 'foot' in sport:
                sport_emoji = "⚽"
        
        print_banner(sport_name, sport_emoji)
        
        # ══════════════════════════════════════════════════════════════
        # PHASE 1: CHARGEMENT DES DONNÉES
        # ══════════════════════════════════════════════════════════════
        print_header("PHASE 1: CHARGEMENT DES DONNÉES")
        loading_report = LoadingReport()
        
        equipes = self._load_equipes(loading_report)
        gymnases = self._load_gymnases(loading_report)
        self.obligations_presence = self._load_obligations(loading_report)
        self.groupes_non_simultaneite = self._load_groupes_non_simultaneite(loading_report)
        self.coach_groups = self._load_coach_groups(equipes, loading_report)
        self.ententes = self._load_ententes(loading_report)
        self.contraintes_temporelles = self._load_contraintes_temporelles(loading_report)
        self.niveaux_gymnases = self._load_niveaux_gymnases(loading_report)
        self.priorites_genre_gymnases = self._load_priorites_genres(loading_report)
        matchs_fixes = self._load_matchs_fixes(equipes, loading_report)
        
        loading_report.display_summary()
        
        # ══════════════════════════════════════════════════════════════
        # PHASE 2: VALIDATION ET PRÉPARATION
        # ══════════════════════════════════════════════════════════════
        print_header("PHASE 2: VALIDATION ET PRÉPARATION")
        
        if not self._validate_data(equipes, gymnases):
            print_error("Erreurs de validation. Arrêt du pipeline.")
            return None
        print_success("Données validées")
        
        poules = self.source.get_poules_dict(equipes)
        self._afficher_info_donnees(equipes, poules, gymnases)
        
        matchs = self._generer_matchs(poules)
        
        # Exclure les matchs déjà fixés de la génération
        if matchs_fixes:
            matchs = self._exclure_matchs_fixes(matchs, matchs_fixes)
        
        creneaux = DataTransformer.generer_creneaux(gymnases, self.config.nb_semaines, self.calendar_manager)
        
        # Exclure les créneaux occupés par les matchs fixes
        if matchs_fixes:
            creneaux = self._exclure_creneaux_fixes(creneaux, matchs_fixes, gymnases)
        
        print_blank()
        print_info(f"{len(matchs)} matchs à planifier sur {len(creneaux)} créneaux disponibles")
        if matchs_fixes:
            print_detail(f"{len(matchs_fixes)} matchs fixes déjà planifiés")
        
        # ══════════════════════════════════════════════════════════════
        # PHASE 3: RÉSOLUTION
        # ══════════════════════════════════════════════════════════════
        print_header("PHASE 3: RÉSOLUTION")
        
        solution = self._resoudre(matchs, creneaux.copy(), gymnases, matchs_fixes)
        
        if solution:
            # Intégrer les matchs fixes dans la solution
            if matchs_fixes:
                solution = self._integrer_matchs_fixes(solution, matchs_fixes, gymnases)
            
            # Calculer les créneaux restants
            creneaux_utilises = {(m.creneau.gymnase, m.creneau.semaine, m.creneau.horaire) 
                                for m in solution.matchs_planifies if m.creneau}
            creneaux_restants = [c for c in creneaux 
                                if (c.gymnase, c.semaine, c.horaire) not in creneaux_utilises]
            
            # ══════════════════════════════════════════════════════════════
            # PHASE 4: RÉSULTATS ET VALIDATION
            # ══════════════════════════════════════════════════════════════
            print_header("PHASE 4: RÉSULTATS ET VALIDATION")
            
            Statistics.afficher_stats(solution, creneaux_restants)
            self._ensure_penalty_breakdown(solution, gymnases)
            
            # Sauvegarder la solution avec les matchs fixes pour traçabilité
            self._save_solution(solution, matchs, creneaux, gymnases, matchs_fixes)
            
            # Validation post-solution
            self._valider_solution(solution, gymnases)
            
            # ══════════════════════════════════════════════════════════════
            # PHASE 5: EXPORT
            # ══════════════════════════════════════════════════════════════
            print_header("PHASE 5: EXPORT")
            
            self._exporter_solution(solution)
            return solution
        
        print_error("Aucune solution trouvée")
        return None
    
    def _load_equipes(self, report: LoadingReport = None) -> List[Equipe]:
        """Load teams from file."""
        equipes = self.source.charger_equipes()
        if report:
            report.add(LoadingResult(
                name="Équipes",
                count=len(equipes),
                details=[f"{len(set(e.institution for e in equipes))} institutions"]
            ))
        return equipes
    
    def _load_gymnases(self, report: LoadingReport = None) -> List[Gymnase]:
        """Load venues from file."""
        gymnases = self.source.charger_gymnases()
        if report:
            capacite_totale = sum(len(g.horaires_disponibles) * g.capacite for g in gymnases)
            report.add(LoadingResult(
                name="Gymnases",
                count=len(gymnases),
                details=[f"~{capacite_totale} créneaux/sem"]
            ))
        return gymnases
    
    def _load_obligations(self, report: LoadingReport = None) -> Dict[str, str]:
        """Load presence obligations."""
        obligations = self.source.charger_obligations_presence()
        if report and obligations:
            report.add(LoadingResult(
                name="Obligations de présence",
                count=len(obligations)
            ))
        return obligations
    
    def _load_groupes_non_simultaneite(self, report: LoadingReport = None) -> Dict:
        """Load non-simultaneity groups."""
        try:
            groupes = self.source.charger_groupes_non_simultaneite()
            if report and groupes:
                report.add(LoadingResult(
                    name="Groupes non-simultanéité",
                    count=len(groupes)
                ))
            return groupes
        except Exception as e:
            if report:
                report.add(LoadingResult(
                    name="Groupes non-simultanéité",
                    count=0,
                    success=False,
                    errors=[str(e)]
                ))
            return {}

    def _load_coach_groups(self, equipes: List[Equipe], report: LoadingReport = None) -> Dict[str, CoachGroup]:
        """Load coach groups for overlap handling."""
        if not self.config.coach_overlap_actif:
            return {}

        try:
            groups = self.source.charger_groupes_coachs(equipes)
            if report and groups:
                report.add(LoadingResult(
                    name="Groupes coachs",
                    count=len(groups)
                ))
            return groups
        except Exception as e:
            if report:
                report.add(LoadingResult(
                    name="Groupes coachs",
                    count=0,
                    success=False,
                    errors=[str(e)]
                ))
            return {}
    
    def _load_ententes(self, report: LoadingReport = None) -> Dict:
        """Load ententes (special match pairs with reduced unscheduled penalty)."""
        if not self.config.entente_actif:
            return {}
        
        try:
            ententes = self.source.charger_ententes()
            if report and ententes:
                report.add(LoadingResult(
                    name="Ententes",
                    count=len(ententes)
                ))
            return ententes
        except Exception as e:
            if report:
                report.add(LoadingResult(
                    name="Ententes",
                    count=0,
                    success=False,
                    errors=[str(e)]
                ))
            return {}
    
    def _load_contraintes_temporelles(self, report: LoadingReport = None) -> Dict:
        """Load temporal constraints (before/after specific week)."""
        if not self.config.contrainte_temporelle_actif:
            return {}
        
        try:
            contraintes = self.source.charger_contraintes_temporelles()
            if report and contraintes:
                mode = "dure" if self.config.contrainte_temporelle_dure else "souple"
                report.add(LoadingResult(
                    name="Contraintes temporelles",
                    count=len(contraintes),
                    details=[f"mode {mode}"]
                ))
            return contraintes
        except Exception as e:
            if report:
                report.add(LoadingResult(
                    name="Contraintes temporelles",
                    count=0,
                    success=False,
                    errors=[str(e)]
                ))
            return {}
    
    def _load_niveaux_gymnases(self, report: LoadingReport = None) -> Dict[str, str]:
        """Load gymnasium level classifications (high/low level)."""
        try:
            niveaux = self.source.charger_niveaux_gymnases()
            if report and niveaux:
                haut = sum(1 for n in niveaux.values() if n == 'haut')
                bas = len(niveaux) - haut
                report.add(LoadingResult(
                    name="Niveaux gymnases",
                    count=len(niveaux),
                    details=[f"{haut} haut, {bas} bas"]
                ))
            return niveaux
        except Exception as e:
            if report:
                report.add(LoadingResult(
                    name="Niveaux gymnases",
                    count=0,
                    success=False,
                    errors=[str(e)]
                ))
            return {}

    def _load_priorites_genres(self, report: LoadingReport = None) -> Dict[str, str]:
        """Load optional gender priority per venue."""
        try:
            priorites = self.source.charger_priorites_genre_gymnases()
            if report and priorites:
                report.add(LoadingResult(
                    name="Genres prioritaires",
                    count=len(priorites)
                ))
            return priorites
        except Exception as e:
            if report:
                report.add(LoadingResult(
                    name="Genres prioritaires",
                    count=0,
                    success=False,
                    errors=[str(e)]
                ))
            return {}

    def _load_matchs_fixes(self, equipes: List[Equipe], report: LoadingReport = None):
        """Load fixed/already played matches."""
        try:
            matchs_fixes = self.source.charger_matchs_fixes(equipes)
            if report and matchs_fixes:
                report.add(LoadingResult(
                    name="Matchs fixes",
                    count=len(matchs_fixes)
                ))
            return matchs_fixes
        except Exception as e:
            if report:
                report.add(LoadingResult(
                    name="Matchs fixes",
                    count=0,
                    success=False,
                    errors=[str(e)]
                ))
            return []
    
    def _exclure_matchs_fixes(self, matchs, matchs_fixes):
        """
        Exclut les matchs déjà fixés de la liste des matchs à planifier.
        
        IMPORTANT: Pour les poules Classiques, A→B == B→A (même match).
                   Pour les poules Aller-Retour, A→B ≠ B→A (matchs distincts).
        
        BUG FIX: Version précédente utilisait l'ordre exact pour toutes les poules,
                 causant des doublons dans les poules Classiques.
        """
        if not matchs_fixes:
            return matchs
        
        # Charger les types de poules si pas déjà fait
        if not hasattr(self, 'types_poules') or not self.types_poules:
            self.types_poules = self.source.charger_types_poules()
        
        # Créer un ensemble des matchs fixés
        matchs_fixes_set = set()
        for match_fixe in matchs_fixes:
            poule = match_fixe.poule
            type_poule = self.types_poules.get(poule, 'Classique')
            est_aller_retour = (type_poule == 'Aller-Retour')
            
            if est_aller_retour:
                # Aller-Retour: ordre exact (A→B ≠ B→A)
                key = (match_fixe.equipe1.id_unique, match_fixe.equipe2.id_unique, poule)
            else:
                # Classique: ordre trié (A→B == B→A)
                key = tuple(sorted([match_fixe.equipe1.id_unique, match_fixe.equipe2.id_unique])) + (poule,)
            
            matchs_fixes_set.add(key)
        
        # Filtrer les matchs
        matchs_a_planifier = []
        for match in matchs:
            poule = match.poule
            type_poule = self.types_poules.get(poule, 'Classique')
            est_aller_retour = (type_poule == 'Aller-Retour')
            
            if est_aller_retour:
                # Aller-Retour: ordre exact
                key = (match.equipe1.id_unique, match.equipe2.id_unique, poule)
            else:
                # Classique: ordre trié
                key = tuple(sorted([match.equipe1.id_unique, match.equipe2.id_unique])) + (poule,)
            
            if key not in matchs_fixes_set:
                matchs_a_planifier.append(match)
        
        nb_exclus = len(matchs) - len(matchs_a_planifier)
        if nb_exclus > 0:
            print_info(f"{nb_exclus} matchs exclus (déjà fixés)")
        
        return matchs_a_planifier
    
    def _exclure_creneaux_fixes(self, creneaux, matchs_fixes, gymnases):
        """
        ANCIEN COMPORTEMENT (INCORRECT):
        Excluait complètement les créneaux occupés par matchs fixes.
        → Bloquait les gymnases multi-capacités !
        
        NOUVEAU COMPORTEMENT (CORRECT):
        Ne fait RIEN - les créneaux restent disponibles.
        La gestion de capacité est faite dans les solveurs qui soustraient
        les matchs fixés de la capacité disponible.
        
        Cette fonction est conservée pour compatibilité mais devient un no-op.
        """
        # Ne rien faire - garder TOUS les créneaux disponibles
        # Les solveurs gèrent la capacité restante après matchs fixés
        
        # Afficher un message informatif
        if matchs_fixes:
            # Compter combien de créneaux ont des matchs fixés (pour info)
            creneaux_avec_fixes = set()
            for match_fixe in matchs_fixes:
                meta = match_fixe.metadata
                creneaux_avec_fixes.add((meta['gymnase'], meta['semaine'], meta['horaire']))
            print_detail(f"{len(creneaux_avec_fixes)} créneaux partiellement occupés par matchs fixes")
        
        # Retourner TOUS les créneaux sans exclusion
        return creneaux
    
    def _integrer_matchs_fixes(self, solution, matchs_fixes, gymnases):
        """Intègre les matchs fixes dans la solution finale."""
        from pycalendar.core.models import Creneau
        
        # Créer les créneaux pour les matchs fixes
        for match_fixe in matchs_fixes:
            meta = match_fixe.metadata
            
            # Vérifier si c'est un match en entente
            is_entente = meta.get('is_entente', False)
            
            if is_entente:
                # Pour les matchs en entente, ne pas créer de créneau
                # Ils seront ajoutés aux matchs non planifiés mais marqués comme entente
                match_fixe.creneau = None
                solution.matchs_non_planifies.append(match_fixe)
            else:
                # Pour les autres matchs fixes, créer le créneau correspondant
                creneau = Creneau(
                    semaine=meta['semaine'],
                    horaire=meta['horaire'],
                    gymnase=meta['gymnase']
                )
                
                # Assigner le créneau au match
                match_fixe.creneau = creneau
                
                # Ajouter aux matchs planifiés
                solution.matchs_planifies.append(match_fixe)
        
        # Trier par semaine pour un affichage cohérent
        solution.matchs_planifies.sort(key=lambda m: (m.creneau.semaine, m.creneau.horaire) if m.creneau else (999, ''))
        
        return solution
    
    def _validate_data(self, equipes: List[Equipe], gymnases: List[Gymnase]) -> bool:
        """Validate loaded data."""
        return DataValidator.validate_all(equipes, gymnases)
    
    def _afficher_info_donnees(self, equipes: List[Equipe], poules: Dict, gymnases: List[Gymnase]):
        """Display data information."""
        print_section("Résumé des données", "📊")
        
        tailles_poules = [len(eq) for eq in poules.values()]
        total_creneaux = sum(len(g.horaires_disponibles) * g.capacite for g in gymnases)
        
        print_key_value("Équipes", f"{len(equipes)} réparties en {len(poules)} poules")
        print_key_value("Tailles poules", f"min={min(tailles_poules)}, max={max(tailles_poules)}, moy={sum(tailles_poules)/len(tailles_poules):.1f}")
        print_key_value("Gymnases", f"{len(gymnases)}, ~{total_creneaux} créneaux/semaine")
        print_key_value("Semaines", self.config.nb_semaines)
    
    def _generer_matchs(self, poules: Dict):
        """Generate matches for all pools according to their types."""
        print_section("Génération des matchs", "⚙️")
        
        # Load pool types
        self.types_poules = self.source.charger_types_poules()
        
        # Display pool types summary
        if self.types_poules:
            nb_aller_retour = sum(1 for t in self.types_poules.values() if t == 'Aller-Retour')
            nb_classique = len(self.types_poules) - nb_aller_retour
            if nb_aller_retour > 0:
                print_detail(f"{nb_classique} poule(s) Classique, {nb_aller_retour} poule(s) Aller-Retour")
        
        # Generate matches with per-pool types
        generator = MultiPoolGenerator(self.types_poules if self.types_poules else False)
        matchs = generator.generer_tous_matchs(poules)
        
        # Marquer les matchs d'entente
        if self.ententes:
            nb_ententes = 0
            for match in matchs:
                inst1 = match.equipe1.institution
                inst2 = match.equipe2.institution
                # Créer une clé triée comme dans le chargement des ententes
                cle = tuple(sorted([inst1, inst2]))
                if cle in self.ententes:
                    match.metadata['is_entente'] = True
                    nb_ententes += 1
            if nb_ententes > 0:
                print_detail(f"{nb_ententes} match(s) d'entente identifié(s)")
        
        print_success(f"{len(matchs)} matchs générés")
        return matchs
    
    def _resoudre(self, matchs, creneaux, gymnases, matchs_fixes=None):
        """Solve the scheduling problem with optional warm start.
        
        Args:
            matchs: Matchs à planifier (sans les matchs fixés)
            creneaux: Créneaux disponibles (sans ceux occupés par matchs fixés)
            gymnases: Dictionnaire des gymnases
            matchs_fixes: Matchs déjà planifiés/fixés (pour calcul des pénalités)
        """
        print_section("Résolution CP-SAT", "🧮")
        
        gymnases_dict = {g.nom: g for g in gymnases}
        
        if not CPSAT_AVAILABLE:
            raise ImportError("OR-Tools n'est pas installé. Installez-le avec: pip install ortools")
        
        # ──── RAPPORT DES OPTIONS DU SOLVER ────
        self._afficher_options_solver()
        
        solver = CPSATSolver(
            self.config,
            groupes_non_simultaneite=self.groupes_non_simultaneite,
            ententes=self.ententes,
            contraintes_temporelles=self.contraintes_temporelles,
            niveaux_gymnases=self.niveaux_gymnases,
            priorites_genre_gymnases=self.priorites_genre_gymnases,
            coach_groups=self.coach_groups
        )
        
        # CP-SAT avec warm start activé par défaut
        use_warm_start = getattr(self.config, 'cpsat_warm_start', True)
        solution = solver.solve(matchs, creneaux, gymnases_dict, 
                               self.obligations_presence,
                               use_warm_start=use_warm_start,
                               matchs_fixes=matchs_fixes)
        
        return solution
    
    def _afficher_options_solver(self):
        """Affiche les options et modes du solver activés."""
        # Mode rapide
        mode_fast = getattr(self.config, 'cpsat_mode_fast', False)
        
        # Options de performance
        use_prefilter = getattr(self.config, 'cpsat_use_prefilter', True)
        enable_espacement_repos = getattr(self.config, 'cpsat_enable_espacement_repos', True)
        enable_aller_retour = getattr(self.config, 'cpsat_enable_aller_retour', True)
        espacement_repos_simplifie = getattr(self.config, 'cpsat_espacement_repos_simplifie', False)
        aller_retour_simplifie = getattr(self.config, 'cpsat_aller_retour_simplifie', False)
        equilibrage_mode_simplifie = getattr(self.config, 'equilibrage_mode_simplifie', False)
        
        # Contraintes _actif
        equilibrage_actif = getattr(self.config, 'equilibrage_actif', True)
        compaction_actif = getattr(self.config, 'compaction_temporelle_actif', False)
        overlap_institution_actif = getattr(self.config, 'overlap_institution_actif', False)
        coach_overlap_actif = getattr(self.config, 'coach_overlap_actif', False)
        entente_actif = getattr(self.config, 'entente_actif', False)
        contrainte_temporelle_actif = getattr(self.config, 'contrainte_temporelle_actif', False)
        aller_retour_espacement_actif = getattr(self.config, 'aller_retour_espacement_actif', False)
        
        # Appliquer mode_fast
        if mode_fast:
            enable_espacement_repos = False
            enable_aller_retour = False
            espacement_repos_simplifie = True
            aller_retour_simplifie = True
            equilibrage_mode_simplifie = True
        
        # Construire le rapport
        print_subsection("Options du Solver")
        
        if mode_fast:
            print_info("⚡ Mode FAST activé - contraintes coûteuses désactivées")
        
        # Contraintes principales (activables/désactivables)
        contraintes_on = []
        contraintes_off = []
        
        # Équilibrage
        if equilibrage_actif:
            mode = " (simplifié)" if equilibrage_mode_simplifie else ""
            contraintes_on.append(f"Équilibrage{mode}")
        else:
            contraintes_off.append("Équilibrage")
        
        # Compaction temporelle
        if compaction_actif:
            contraintes_on.append("Compaction temporelle")
        else:
            contraintes_off.append("Compaction temporelle")
        
        # Overlap institution
        if overlap_institution_actif:
            contraintes_on.append("Overlap institution")
        else:
            contraintes_off.append("Overlap institution")
        
        # Coach overlap
        if coach_overlap_actif:
            contraintes_on.append("Coach overlap")
        else:
            contraintes_off.append("Coach overlap")
        
        # Ententes
        if entente_actif:
            contraintes_on.append("Ententes")
        else:
            contraintes_off.append("Ententes")
        
        # Contraintes temporelles (CFE)
        if contrainte_temporelle_actif:
            contraintes_on.append("Contraintes temporelles")
        else:
            contraintes_off.append("Contraintes temporelles")
        
        # Aller-retour espacement
        if aller_retour_espacement_actif and enable_aller_retour:
            mode = " (simplifié)" if aller_retour_simplifie else ""
            contraintes_on.append(f"Espacement aller-retour{mode}")
        elif aller_retour_espacement_actif and not enable_aller_retour:
            contraintes_off.append("Espacement aller-retour (désactivé pour performance)")
        else:
            contraintes_off.append("Espacement aller-retour")
        
        # Espacement repos
        if enable_espacement_repos:
            mode = " (simplifié)" if espacement_repos_simplifie else ""
            contraintes_on.append(f"Espacement repos{mode}")
        else:
            contraintes_off.append("Espacement repos")
        
        # Préfiltrage (option technique)
        if use_prefilter:
            contraintes_on.append("Préfiltrage (réduction modèle)")
        else:
            contraintes_off.append("Préfiltrage")
        
        # Affichage
        if contraintes_on:
            print_info("Contraintes activées:")
            for opt in contraintes_on:
                print_detail(f"  ✓ {opt}")
        if contraintes_off:
            print_info("Contraintes désactivées:")
            for opt in contraintes_off:
                print_detail(f"  ✗ {opt}")
    
    def _ensure_penalty_breakdown(self, solution: Solution, gymnases: List[Gymnase]):
        """Garantit que la solution contient la décomposition des pénalités."""
        if not solution or not gymnases:
            return
        if solution.metadata is None:
            solution.metadata = {}
        solution.metadata.setdefault('niveaux_gymnases', self.niveaux_gymnases)
        solution.metadata.setdefault('priorites_genre_gymnases', self.priorites_genre_gymnases)
        if solution.metadata.get('penalty_breakdown'):
            return
        try:
            penalty_breakdown = calculate_penalty_breakdown(
                solution,
                self.config,
                gymnases=gymnases,
                niveaux_gymnases=self.niveaux_gymnases,
                priorites_genre_gymnases=self.priorites_genre_gymnases,
                ententes=self.ententes,
                obligations_presence=self.obligations_presence,
                groupes_non_simultaneite=self.groupes_non_simultaneite,
            )
            solution.metadata['penalty_breakdown'] = penalty_breakdown
        except Exception as e:
            print_warning(f"Impossible de calculer la décomposition des pénalités: {e}")

    def _save_solution(self, solution: Solution, matchs, creneaux, gymnases, matchs_fixes=None):
        """Sauvegarde la solution avec sa signature pour réutilisation future."""
        try:
            from pycalendar.core.solution_store import SolutionStore
            
            # Créer le store avec le nom de fichier configuré
            solution_name = getattr(self.config, 'cpsat_warm_start_file', 'default')
            store = SolutionStore(solution_name=solution_name)
            
            # Créer la signature de configuration
            equipes = self.source.charger_equipes()
            
            # Utiliser la source YAML réelle si disponible, sinon fallback
            if getattr(self.config, 'source_path', None):
                config_yaml_path = Path(self.config.source_path)
            else:
                config_yaml_path = Path("configs/default.yaml")
                for possible_path in [Path("configs/default.yaml"), Path("config.yaml")]:
                    if possible_path.exists():
                        config_yaml_path = possible_path
                        break
            if not config_yaml_path.exists():
                print_warning(f"Fichier YAML introuvable pour la signature ({config_yaml_path}), fallback sur configs/default.yaml")
                config_yaml_path = Path("configs/default.yaml")
            
            signature = store.create_signature(
                yaml_path=config_yaml_path,
                config_manager=self.source.loader.config,  # ConfigManager est dans le loader
                equipes=equipes,
                gymnases=[g.nom for g in gymnases],
                nb_creneaux=len(creneaux),
                nb_semaines=self.config.nb_semaines
            )
            
            # Sauvegarder la solution
            saved_path = store.save_solution(
                solution=solution,
                signature=signature,
                config=self.config,  # Passer l'objet Config complet
                config_name=str(self.source.fichier_config),
                fixed_matches=matchs_fixes,
                equipes=equipes,  # Passer les objets Equipe complets
                gymnases=gymnases,  # Passer les objets Gymnase complets
                creneaux=creneaux,  # Passer TOUS les créneaux (disponibles + occupés)
                types_poules=self.types_poules  # Passer les types de poules
            )
            
            # Validation automatique après sauvegarde
            if saved_path:
                self._validate_solution_json(saved_path)
            
        except Exception as e:
            print_warning(f"Erreur lors de la sauvegarde de la solution: {e}")
            import traceback
            traceback.print_exc()
            # Continue sans sauvegarder (non-bloquant)
    
    def _valider_solution(self, solution: Solution, gymnases: List[Gymnase]):
        """Valide la solution générée contre toutes les contraintes."""
        gymnases_dict = {g.nom: g for g in gymnases}
        validator = SolutionValidator(self.config, gymnases_dict, self.obligations_presence, self.groupes_non_simultaneite)
        est_valide, rapport = validator.valider_solution(solution)
        afficher_rapport_validation(rapport)
        return est_valide
    
    def _validate_solution_json(self, solution_path: Path):
        """
        Valide le fichier JSON généré.
        
        Args:
            solution_path: Chemin vers le fichier JSON à valider
        """
        try:
            import json
            from pycalendar.interface.core.validator import SolutionValidator as SolutionValidatorV2
            from pycalendar.interface.core.validator import Severity
            
            print_section("Validation JSON", "🔍")
            
            # Charger le JSON
            with open(solution_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Valider
            validator = SolutionValidatorV2()
            try:
                is_valid, issues = validator.validate_full(data)
            except Exception as e:
                print_warning(f"Erreur lors de la validation: {e}")
                import traceback
                traceback.print_exc()
                return
            
            # Afficher résumé
            errors = sum(1 for i in issues if i.severity == Severity.ERROR)
            warnings = sum(1 for i in issues if i.severity == Severity.WARNING)
            infos = sum(1 for i in issues if i.severity == Severity.INFO)
            
            if errors == 0 and warnings == 0 and infos == 0:
                print_success("Fichier JSON valide")
            else:
                if errors > 0:
                    print_error(f"{errors} erreur(s) dans le JSON")
                elif warnings > 0:
                    print_warning(f"{warnings} avertissement(s)")
                
                if errors > 0 or warnings > 0:
                    # Afficher rapport détaillé si erreurs ou warnings
                    report = validator.generate_report(issues)
                    print(report)
            
        except Exception as e:
            print_warning(f"Erreur lors de la validation: {e}")
            import traceback
            traceback.print_exc()
    
    def _exporter_solution(self, solution: Solution):
        """Export solution to files."""
        print_section("Export des fichiers", "💾")
        ExcelExporter.export(solution, self.config.fichier_sortie)
        print_success(f"Excel: {self.config.fichier_sortie}")
        
        # Générer TOUS les créneaux possibles (occupés et libres)
        gymnases = self.source.charger_gymnases()
        self._ensure_penalty_breakdown(solution, gymnases)
        
        tous_creneaux = DataTransformer.generer_creneaux(gymnases, self.config.nb_semaines, self.calendar_manager)
        
        # Stocker TOUS les créneaux dans metadata pour l'interface
        solution.metadata['creneaux_disponibles'] = tous_creneaux
        
        # Générer l'interface HTML interactive
        html_path = self.config.fichier_sortie.replace('.xlsx', '.html')
        generator = InterfaceGenerator()
        html_file = generator.generate(solution, html_path, self.config, types_poules=self.types_poules)
        print_success(f"HTML: {html_file}")
        
        print_blank()
        print_info("Ouvrez le calendrier dans votre navigateur:")
        print(f"     file://{html_file}")
