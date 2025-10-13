"""Main scheduling pipeline orchestrator."""

from typing import Dict, List
from pathlib import Path
from core.models import Equipe, Gymnase, Solution
from core.config import Config
from data.data_source import DataSource
from data.validators import DataValidator
from data.transformers import DataTransformer
from generators.multi_pool_generator import MultiPoolGenerator
from solvers.greedy_solver import GreedySolver
from exporters.excel_exporter import ExcelExporter
from visualization.statistics import Statistics
from visualization.html_visualizer import HTMLVisualizer
from visualization.html_visualizer_pro import HTMLVisualizerPro as HTMLVisualizerPremium
from visualization.html_visualizer_v2 import HTMLVisualizerV2
from validation.solution_validator import SolutionValidator, afficher_rapport_validation

try:
    from solvers.cpsat_solver import CPSATSolver
    CPSAT_AVAILABLE = True
except ImportError:
    CPSAT_AVAILABLE = False


class SchedulingPipeline:
    """Main pipeline for sports scheduling."""
    
    def __init__(self, config: Config):
        self.config = config
        self.source = DataSource(config.fichier_donnees)
        self.obligations_presence = {}
        self.groupes_non_simultaneite = {}
        self.ententes = {}
        self.contraintes_temporelles = {}
    
    def run(self):
        """Execute the complete scheduling pipeline."""
        print("\n" + "="*60)
        print("PYCALENDAR - Planification de calendrier sportif")
        print("="*60 + "\n")
        
        equipes = self._load_equipes()
        gymnases = self._load_gymnases()
        self.obligations_presence = self._load_obligations()
        self.groupes_non_simultaneite = self._load_groupes_non_simultaneite()
        self.ententes = self._load_ententes()
        self.contraintes_temporelles = self._load_contraintes_temporelles()
        matchs_fixes_data = self._load_matchs_fixes()
        
        if not self._validate_data(equipes, gymnases):
            print("❌ Erreurs de validation. Arrêt du pipeline.")
            return None
        
        poules = self.source.get_poules_dict(equipes)
        self._afficher_info_donnees(equipes, poules, gymnases)
        
        matchs = self._generer_matchs(poules)
        
        # Appliquer les matchs fixés sur les matchs générés
        matchs = self._appliquer_matchs_fixes(matchs, matchs_fixes_data, equipes)
        
        creneaux = DataTransformer.generer_creneaux(gymnases, self.config.nb_semaines)
        
        # Filtrer les créneaux occupés par les matchs fixés ET respecter semaine_minimum
        creneaux = self._filtrer_creneaux(creneaux, matchs_fixes_data)
        
        # Compter matchs à planifier vs fixés
        nb_fixes = sum(1 for m in matchs if m.est_fixe)
        nb_a_planifier = len(matchs) - nb_fixes
        
        print(f"📅 Résumé de planification:")
        if nb_fixes > 0:
            print(f"  • {nb_fixes} matchs déjà fixés")
        print(f"  • {nb_a_planifier} matchs à planifier")
        print(f"  • {len(creneaux)} créneaux disponibles\n")
        
        solution = self._resoudre(matchs, creneaux.copy(), gymnases)
        
        if solution:
            # Calculer les créneaux restants
            creneaux_utilises = {(m.creneau.gymnase, m.creneau.semaine, m.creneau.horaire) 
                                for m in solution.matchs_planifies if m.creneau}
            creneaux_restants = [c for c in creneaux 
                                if (c.gymnase, c.semaine, c.horaire) not in creneaux_utilises]
            
            Statistics.afficher_stats(solution, creneaux_restants)
            
            # Validation post-solution
            self._valider_solution(solution, gymnases)
            
            self._exporter_solution(solution)
            return solution
        
        return None
    
    def _load_equipes(self) -> List[Equipe]:
        """Load teams from file."""
        print("📂 Chargement des équipes...")
        equipes = self.source.charger_equipes()
        print(f"✓ {len(equipes)} équipes chargées avec contraintes institutionnelles\n")
        return equipes
    
    def _load_gymnases(self) -> List[Gymnase]:
        """Load venues from file."""
        print("\n📂 Chargement des gymnases...")
        gymnases = self.source.charger_gymnases()
        print(f"✓ {len(gymnases)} gymnases chargés\n")
        return gymnases
    
    def _load_obligations(self) -> Dict[str, str]:
        """Load presence obligations."""
        print("📋 Chargement des obligations de présence...")
        obligations = self.source.charger_obligations_presence()
        
        if obligations:
            print(f"✓ {len(obligations)} gymnases avec obligation de présence:")
            for gymnase, institution in obligations.items():
                print(f"  • {gymnase} → {institution} obligatoire")
        else:
            print("  ℹ️  Aucune obligation de présence définie")
        print()
        return obligations
    
    def _load_groupes_non_simultaneite(self) -> Dict:
        """Load non-simultaneity groups."""
        print("🚫 Chargement des groupes de non-simultanéité...")
        try:
            groupes = self.source.charger_groupes_non_simultaneite()
            
            if groupes:
                print(f"✓ {len(groupes)} groupes de non-simultanéité chargés:")
                for nom_groupe, entites in groupes.items():
                    print(f"  • {nom_groupe}: {', '.join(sorted(entites))}")
            else:
                print("  ℹ️  Aucun groupe de non-simultanéité défini (mode legacy)")
                print("  ℹ️  La contrainte s'appliquera à toutes les institutions")
            print()
            return groupes
        except Exception as e:
            print(f"  ⚠️  Erreur lors du chargement des groupes: {e}")
            print("  ℹ️  Utilisation du mode legacy (toutes institutions)")
            print()
            return {}
    
    def _load_ententes(self) -> Dict:
        """Load ententes (special match pairs with reduced unscheduled penalty)."""
        if not self.config.entente_actif:
            return {}
        
        print("🤝 Chargement des ententes...")
        try:
            ententes = self.source.charger_ententes()
            
            if ententes:
                print(f"✓ {len(ententes)} ententes chargées:")
                for (inst1, inst2), penalite in sorted(ententes.items()):
                    print(f"  • {inst1} ↔ {inst2}: pénalité non-planif {penalite}")
            else:
                print("  ℹ️  Aucune entente définie")
            print()
            return ententes
        except Exception as e:
            print(f"  ⚠️  Erreur lors du chargement des ententes: {e}")
            print()
            return {}
    
    def _load_contraintes_temporelles(self) -> Dict:
        """Load temporal constraints on specific matches."""
        if not self.config.contrainte_temporelle_actif:
            return {}
        
        print("⏰ Chargement des contraintes temporelles...")
        try:
            contraintes = self.source.charger_contraintes_temporelles()
            
            if contraintes:
                print(f"✓ {len(contraintes)} contraintes temporelles chargées:")
                for (eq1, eq2), contrainte in sorted(contraintes.items()):
                    print(f"  • {eq1} vs {eq2}: {contrainte.type_contrainte} semaine {contrainte.semaine_limite}")
            else:
                print("  ℹ️  Aucune contrainte temporelle définie")
            print()
            return contraintes
        except Exception as e:
            print(f"  ⚠️  Erreur lors du chargement des contraintes temporelles: {e}")
            print()
            return {}
    
    def _load_matchs_fixes(self) -> Dict:
        """Load fixed matches that cannot be rescheduled."""
        if not self.config.respecter_matchs_fixes:
            return {'creneaux_occupes': {}, 'matchs_par_equipe': {}, 'details': []}
        
        print("🔒 Chargement des matchs fixés...")
        try:
            matchs_fixes = self.source.charger_matchs_fixes()
            
            if matchs_fixes['details']:
                print(f"✓ {len(matchs_fixes['details'])} matchs fixés chargés")
                print(f"  • {len(matchs_fixes['creneaux_occupes'])} créneaux réservés")
                print(f"  • {len(matchs_fixes['matchs_par_equipe'])} équipes concernées")
                
                # Afficher quelques exemples
                for i, match_info in enumerate(matchs_fixes['details'][:3]):
                    print(f"  • S{match_info['semaine']} {match_info['horaire']} {match_info['gymnase']}: "
                          f"{match_info['equipe1_nom']} vs {match_info['equipe2_nom']} [{match_info['statut']}]")
                if len(matchs_fixes['details']) > 3:
                    print(f"  ... et {len(matchs_fixes['details']) - 3} autres")
            else:
                print("  ℹ️  Aucun match fixé défini")
            print()
            return matchs_fixes
        except Exception as e:
            print(f"  ⚠️  Erreur lors du chargement des matchs fixés: {e}")
            print()
            return {'creneaux_occupes': {}, 'matchs_par_equipe': {}, 'details': []}
    
    def _validate_data(self, equipes: List[Equipe], gymnases: List[Gymnase]) -> bool:
        """Validate loaded data."""
        print("\n🔍 Validation des données...")
        return DataValidator.validate_all(equipes, gymnases)
    
    def _afficher_info_donnees(self, equipes: List[Equipe], poules: Dict, gymnases: List[Gymnase]):
        """Display data information."""
        print(f"\n📊 Informations:")
        print(f"  - {len(equipes)} équipes réparties en {len(poules)} poules")
        
        tailles_poules = [len(eq) for eq in poules.values()]
        print(f"  - Tailles de poules: min={min(tailles_poules)}, max={max(tailles_poules)}, moy={sum(tailles_poules)/len(tailles_poules):.1f}")
        
        total_creneaux = sum(len(g.horaires_disponibles) * g.capacite for g in gymnases)
        print(f"  - {len(gymnases)} gymnases, ~{total_creneaux} créneaux/semaine")
        print(f"  - Planification sur {self.config.nb_semaines} semaines\n")
    
    def _generer_matchs(self, poules: Dict):
        """Generate matches for all pools according to their types."""
        print("⚙️  Génération des matchs...")
        
        # Load pool types
        types_poules = self.source.charger_types_poules()
        
        # Display pool types summary
        if types_poules:
            nb_aller_retour = sum(1 for t in types_poules.values() if t == 'Aller-Retour')
            nb_classique = len(types_poules) - nb_aller_retour
            if nb_aller_retour > 0:
                print(f"   Types: {nb_classique} poule(s) Classique, {nb_aller_retour} poule(s) Aller-Retour")
        
        # Generate matches with per-pool types
        generator = MultiPoolGenerator(types_poules if types_poules else False)
        matchs = generator.generer_tous_matchs(poules)
        
        print(f"✓ {len(matchs)} matchs générés")
        return matchs
    
    def _appliquer_matchs_fixes(self, matchs: List, matchs_fixes_data: Dict, equipes: List[Equipe]) -> List:
        """
        Applique les matchs fixés sur la liste des matchs générés.
        
        Marque les matchs correspondants comme fixés avec leur créneau.
        """
        from core.models import Match, Creneau
        
        if not matchs_fixes_data['details']:
            return matchs
        
        print("🔧 Application des matchs fixés...")
        
        # Créer un dict d'équipes par id pour lookup rapide
        equipes_dict = {eq.id_unique: eq for eq in equipes}
        
        nb_fixes = 0
        nb_non_trouves = 0
        
        for match in matchs:
            eq1_id = match.equipe1.id_unique
            eq2_id = match.equipe2.id_unique
            
            # Chercher dans les matchs fixés (dans les deux sens)
            match_info = None
            for info in matchs_fixes_data['details']:
                if ((info['equipe1_id'] == eq1_id and info['equipe2_id'] == eq2_id) or
                    (info['equipe1_id'] == eq2_id and info['equipe2_id'] == eq1_id)):
                    match_info = info
                    break
            
            if match_info:
                # Créer le créneau
                creneau = Creneau(
                    semaine=match_info['semaine'],
                    horaire=match_info['horaire'],
                    gymnase=match_info['gymnase']
                )
                
                # Marquer le match comme fixé
                match.creneau = creneau
                match.est_fixe = True
                match.statut = match_info['statut']
                match.score_equipe1 = match_info['score1']
                match.score_equipe2 = match_info['score2']
                match.notes = match_info['notes']
                
                nb_fixes += 1
        
        # Vérifier s'il y a des matchs fixés qui n'ont pas été trouvés dans les matchs générés
        matchs_generes_ids = set()
        for match in matchs:
            eq1_id = match.equipe1.id_unique
            eq2_id = match.equipe2.id_unique
            matchs_generes_ids.add((eq1_id, eq2_id))
            matchs_generes_ids.add((eq2_id, eq1_id))  # Bidirectionnel
        
        for info in matchs_fixes_data['details']:
            if (info['equipe1_id'], info['equipe2_id']) not in matchs_generes_ids:
                nb_non_trouves += 1
                print(f"  ⚠️  Match fixé non trouvé dans les matchs générés: "
                      f"{info['equipe1_nom']} vs {info['equipe2_nom']}")
        
        if nb_fixes > 0:
            print(f"✓ {nb_fixes} matchs marqués comme fixés")
        if nb_non_trouves > 0:
            print(f"  ⚠️  {nb_non_trouves} matchs fixés non trouvés dans les poules (vérifier vos données)")
        print()
        
        return matchs
    
    def _filtrer_creneaux(self, creneaux: List, matchs_fixes_data: Dict) -> List:
        """
        Filtre les créneaux en enlevant:
        1. Les créneaux occupés par les matchs fixés
        2. Les créneaux avant la semaine_minimum (si configurée)
        """
        from core.models import Creneau
        
        print("🔍 Filtrage des créneaux disponibles...")
        nb_initial = len(creneaux)
        
        # 1. Filtrer par semaine_minimum
        if self.config.semaine_minimum > 1:
            creneaux = [c for c in creneaux if c.semaine >= self.config.semaine_minimum]
            nb_semaine_min = nb_initial - len(creneaux)
            if nb_semaine_min > 0:
                print(f"  • {nb_semaine_min} créneaux exclus (avant semaine {self.config.semaine_minimum})")
        
        # 2. Filtrer les créneaux occupés par matchs fixés
        if matchs_fixes_data['creneaux_occupes']:
            creneaux_occupes_keys = set(matchs_fixes_data['creneaux_occupes'].keys())
            nb_avant_fixes = len(creneaux)
            
            creneaux = [
                c for c in creneaux 
                if (c.semaine, c.horaire, c.gymnase) not in creneaux_occupes_keys
            ]
            
            nb_occupes = nb_avant_fixes - len(creneaux)
            if nb_occupes > 0:
                print(f"  • {nb_occupes} créneaux occupés par matchs fixés")
        
        print(f"✓ {len(creneaux)} créneaux disponibles pour planification\n")
        
        return creneaux
    
    def _resoudre(self, matchs, creneaux, gymnases):
        """Solve the scheduling problem with optional warm start."""
        print(f"🧮 Résolution avec algorithme: {self.config.strategie.upper()}\n")
        
        gymnases_dict = {g.nom: g for g in gymnases}
        
        if self.config.strategie == "greedy":
            solver = GreedySolver(self.config, self.groupes_non_simultaneite, self.ententes, self.contraintes_temporelles)
            solution = solver.solve(matchs, creneaux, gymnases_dict, self.obligations_presence)
            
            # Sauvegarder la solution pour utilisation future
            if solution and solution.matchs_planifies:
                self._save_solution(solution, matchs, creneaux, gymnases)
            
            return solution
        
        elif self.config.strategie == "cpsat":
            if not CPSAT_AVAILABLE:
                print("⚠️  OR-Tools non installé, basculement vers Greedy")
                solver = GreedySolver(self.config, self.groupes_non_simultaneite, self.ententes, self.contraintes_temporelles)
                return solver.solve(matchs, creneaux, gymnases_dict, self.obligations_presence)
            
            solver = CPSATSolver(self.config, self.groupes_non_simultaneite, self.ententes, self.contraintes_temporelles)
            try:
                # CP-SAT avec warm start activé par défaut
                use_warm_start = getattr(self.config, 'cpsat_warm_start', True)
                solution = solver.solve(matchs, creneaux, gymnases_dict, 
                                       self.obligations_presence,
                                       use_warm_start=use_warm_start)
                
                # Sauvegarder la solution pour utilisation future
                if solution and solution.matchs_planifies:
                    self._save_solution(solution, matchs, creneaux, gymnases)
                
                return solution
                
            except Exception as e:
                if self.config.fallback_greedy:
                    print(f"⚠️  CP-SAT a échoué ({e}), basculement vers Greedy")
                    solver = GreedySolver(self.config, self.groupes_non_simultaneite, self.ententes)
                    return solver.solve(matchs, creneaux, gymnases_dict, self.obligations_presence)
                raise
        
        else:
            print(f"❌ Stratégie inconnue: {self.config.strategie}")
            return None
    
    def _save_solution(self, solution: Solution, matchs, creneaux, gymnases):
        """Sauvegarde la solution avec sa signature pour réutilisation future."""
        try:
            from core.solution_store import SolutionStore
            
            # Créer le store avec le nom de fichier configuré
            solution_name = getattr(self.config, 'cpsat_warm_start_file', 'default')
            store = SolutionStore(solution_name=solution_name)
            
            # Créer la signature de configuration
            equipes = self.source.charger_equipes()
            
            # Trouver le fichier YAML de config (heuristique)
            # Note: Idéalement, Config devrait stocker son chemin d'origine
            config_yaml_path = Path("configs/default.yaml")
            for possible_path in [Path("configs/default.yaml"), Path("config.yaml")]:
                if possible_path.exists():
                    config_yaml_path = possible_path
                    break
            
            signature = store.create_signature(
                yaml_path=config_yaml_path,
                config_manager=self.source.loader.config,  # ConfigManager est dans le loader
                equipes=equipes,
                gymnases=[g.nom for g in gymnases],
                nb_creneaux=len(creneaux),
                nb_semaines=self.config.nb_semaines
            )
            
            # Sauvegarder
            store.save_solution(
                solution=solution,
                signature=signature,
                config_name=str(self.source.fichier_config)
            )
            
        except Exception as e:
            print(f"  ⚠️  Erreur lors de la sauvegarde de la solution: {e}")
            # Continue sans sauvegarder (non-bloquant)
    
    def _valider_solution(self, solution: Solution, gymnases: List[Gymnase]):
        """Valide la solution générée contre toutes les contraintes."""
        gymnases_dict = {g.nom: g for g in gymnases}
        validator = SolutionValidator(self.config, gymnases_dict, self.obligations_presence)
        est_valide, rapport = validator.valider_solution(solution)
        afficher_rapport_validation(rapport)
        return est_valide
    
    def _exporter_solution(self, solution: Solution):
        """Export solution to files."""
        print("💾 Export de la solution...")
        ExcelExporter.export(solution, self.config.fichier_sortie)
        
        # Calculer les créneaux restants pour passer au visualizer
        creneaux_utilises = {(m.creneau.gymnase, m.creneau.semaine, m.creneau.horaire) 
                            for m in solution.matchs_planifies if m.creneau}
        
        # Récupérer tous les créneaux depuis les données
        gymnases = self.source.charger_gymnases()
        tous_creneaux = DataTransformer.generer_creneaux(gymnases, self.config.nb_semaines)
        creneaux_restants = [c for c in tous_creneaux 
                            if (c.gymnase, c.semaine, c.horaire) not in creneaux_utilises]
        
        # Stocker dans metadata de la solution
        solution.metadata['creneaux_disponibles'] = creneaux_restants
        
        html_path = self.config.fichier_sortie.replace('.xlsx', '.html')
        #html_file = HTMLVisualizer.generate(solution, html_path)
        #html_file_premium = HTMLVisualizerPremium.generate(solution, html_path.replace('.html', '_premium.html'))
        html_file_v2 = HTMLVisualizerV2.generate(solution, html_path, self.config)
        
        print(f"\n🌐 Ouvrez le calendrier dans votre navigateur:")
        #print(f"   file://{html_file} (version classique)")
        #print(f"   file://{html_file_premium} (version premium)")
        print(f"   file://{html_file_v2}")
