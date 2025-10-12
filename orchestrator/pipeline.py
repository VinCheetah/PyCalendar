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
        
        if not self._validate_data(equipes, gymnases):
            print("❌ Erreurs de validation. Arrêt du pipeline.")
            return None
        
        poules = self.source.get_poules_dict(equipes)
        self._afficher_info_donnees(equipes, poules, gymnases)
        
        matchs = self._generer_matchs(poules)
        creneaux = DataTransformer.generer_creneaux(gymnases, self.config.nb_semaines)
        
        print(f"✓ {len(matchs)} matchs à planifier sur {len(creneaux)} créneaux disponibles\n")
        
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
        """Load temporal constraints (before/after specific week)."""
        if not self.config.contrainte_temporelle_actif:
            return {}
        
        print("⏰ Chargement des contraintes temporelles...")
        try:
            contraintes = self.source.charger_contraintes_temporelles()
            
            if contraintes:
                mode = "dure (blocage)" if self.config.contrainte_temporelle_dure else f"souple (pénalité {self.config.contrainte_temporelle_penalite})"
                print(f"✓ {len(contraintes)} contraintes temporelles chargées (mode {mode}):")
                for (eq1, eq2), contrainte in sorted(contraintes.items()):
                    horaires_info = f", horaires: {', '.join(contrainte.horaires_possibles)}" if contrainte.horaires_possibles else ""
                    print(f"  • {eq1} ↔ {eq2}: {contrainte.type_contrainte} semaine {contrainte.semaine_limite}{horaires_info}")
            else:
                print("  ℹ️  Aucune contrainte temporelle définie")
            print()
            return contraintes
        except Exception as e:
            print(f"  ⚠️  Erreur lors du chargement des contraintes temporelles: {e}")
            print()
            return {}
    
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
