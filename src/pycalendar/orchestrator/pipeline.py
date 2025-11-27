"""Main scheduling pipeline orchestrator."""

from typing import Dict, List
from pathlib import Path
from pycalendar.core.models import Equipe, Gymnase, Solution
from pycalendar.core.config import Config
from pycalendar.data.data_source import DataSource
from pycalendar.data.validators import DataValidator
from pycalendar.data.transformers import DataTransformer
from pycalendar.generators.multi_pool_generator import MultiPoolGenerator
from pycalendar.exporters.excel_exporter import ExcelExporter
from pycalendar.core.statistics import Statistics
from pycalendar.interface.core.generator import InterfaceGenerator
from pycalendar.validation.solution_validator import SolutionValidator, afficher_rapport_validation

try:
    from pycalendar.solvers.cpsat_solver import CPSATSolver
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
        self.niveaux_gymnases = {}
        self.types_poules = {}  # Store pool types for export
    
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
        self.niveaux_gymnases = self._load_niveaux_gymnases()
        
        if not self._validate_data(equipes, gymnases):
            print("❌ Erreurs de validation. Arrêt du pipeline.")
            return None
        
        poules = self.source.get_poules_dict(equipes)
        self._afficher_info_donnees(equipes, poules, gymnases)
        
        # Charger les matchs fixes
        matchs_fixes = self._load_matchs_fixes()
        
        matchs = self._generer_matchs(poules)
        
        # Exclure les matchs déjà fixés de la génération
        if matchs_fixes:
            matchs = self._exclure_matchs_fixes(matchs, matchs_fixes)
        
        creneaux = DataTransformer.generer_creneaux(gymnases, self.config.nb_semaines, self.config.calendar_manager)
        
        # Exclure les créneaux occupés par les matchs fixes
        if matchs_fixes:
            creneaux = self._exclure_creneaux_fixes(creneaux, matchs_fixes, gymnases)
        
        print(f"✓ {len(matchs)} matchs à planifier sur {len(creneaux)} créneaux disponibles")
        if matchs_fixes:
            print(f"  ({len(matchs_fixes)} matchs fixes déjà planifiés)")
        print()
        
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
            
            Statistics.afficher_stats(solution, creneaux_restants)
            
            # Sauvegarder la solution avec les matchs fixes pour traçabilité
            self._save_solution(solution, matchs, creneaux, gymnases, matchs_fixes)
            
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
    
    def _load_niveaux_gymnases(self) -> Dict[str, str]:
        """Load gymnasium level classifications (high/low level)."""
        print("🏆 Chargement des niveaux de gymnases...")
        try:
            niveaux = self.source.charger_niveaux_gymnases()
            
            if niveaux:
                haut_niveau = [g for g, n in niveaux.items() if n == 'Haut niveau']
                bas_niveau = [g for g, n in niveaux.items() if n == 'Bas niveau']
                
                print(f"✓ {len(niveaux)} gymnases classés:")
                if haut_niveau:
                    print(f"  • Haut niveau ({len(haut_niveau)}): {', '.join(sorted(haut_niveau))}")
                if bas_niveau:
                    print(f"  • Bas niveau ({len(bas_niveau)}): {', '.join(sorted(bas_niveau))}")
            else:
                print("  ℹ️  Aucun gymnase classé par niveau")
            print()
            return niveaux
        except Exception as e:
            print(f"  ⚠️  Erreur lors du chargement des niveaux de gymnases: {e}")
            print()
            return {}
    
    def _load_matchs_fixes(self):
        """Load fixed/already played matches."""
        print("📌 Chargement des matchs fixes...")
        try:
            matchs_fixes = self.source.charger_matchs_fixes()
            
            if matchs_fixes:
                print(f"✓ {len(matchs_fixes)} matchs fixes chargés:")
                for match in matchs_fixes[:5]:  # Afficher les 5 premiers
                    meta = match.metadata
                    print(f"  • {match.equipe1.nom} vs {match.equipe2.nom} - S{meta['semaine']} {meta['horaire']} @ {meta['gymnase']}")
                if len(matchs_fixes) > 5:
                    print(f"  ... et {len(matchs_fixes) - 5} autres")
            else:
                print("  ℹ️  Aucun match fixe défini")
            print()
            return matchs_fixes
        except Exception as e:
            print(f"  ⚠️  Erreur lors du chargement des matchs fixes: {e}")
            print()
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
            print(f"  ℹ️  {nb_exclus} matchs exclus de la planification (déjà fixés)")
        
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
            print(f"  ℹ️  {len(matchs_fixes)} matchs fixes seront comptés dans la capacité des gymnases")
            
            # Compter combien de créneaux ont des matchs fixés (pour info)
            creneaux_avec_fixes = set()
            for match_fixe in matchs_fixes:
                meta = match_fixe.metadata
                creneaux_avec_fixes.add((meta['gymnase'], meta['semaine'], meta['horaire']))
            print(f"  ℹ️  {len(creneaux_avec_fixes)} créneaux affectés par des matchs fixes")
        
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
        self.types_poules = self.source.charger_types_poules()
        
        # Display pool types summary
        if self.types_poules:
            nb_aller_retour = sum(1 for t in self.types_poules.values() if t == 'Aller-Retour')
            nb_classique = len(self.types_poules) - nb_aller_retour
            if nb_aller_retour > 0:
                print(f"   Types: {nb_classique} poule(s) Classique, {nb_aller_retour} poule(s) Aller-Retour")
        
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
                print(f"   {nb_ententes} match(s) d'entente identifié(s)")
        
        print(f"✓ {len(matchs)} matchs générés")
        return matchs
    
    def _resoudre(self, matchs, creneaux, gymnases, matchs_fixes=None):
        """Solve the scheduling problem with optional warm start.
        
        Args:
            matchs: Matchs à planifier (sans les matchs fixés)
            creneaux: Créneaux disponibles (sans ceux occupés par matchs fixés)
            gymnases: Dictionnaire des gymnases
            matchs_fixes: Matchs déjà planifiés/fixés (pour calcul des pénalités)
        """
        print(f"🧮 Résolution avec CP-SAT\n")
        
        gymnases_dict = {g.nom: g for g in gymnases}
        
        if not CPSAT_AVAILABLE:
            raise ImportError("OR-Tools n'est pas installé. Installez-le avec: pip install ortools")
        
        solver = CPSATSolver(self.config, self.groupes_non_simultaneite, self.ententes, self.contraintes_temporelles, self.niveaux_gymnases)
        
        # CP-SAT avec warm start activé par défaut
        use_warm_start = getattr(self.config, 'cpsat_warm_start', True)
        solution = solver.solve(matchs, creneaux, gymnases_dict, 
                               self.obligations_presence,
                               use_warm_start=use_warm_start,
                               matchs_fixes=matchs_fixes)
        
        return solution
    
    def _save_solution(self, solution: Solution, matchs, creneaux, gymnases, matchs_fixes=None):
        """Sauvegarde la solution avec sa signature pour réutilisation future."""
        try:
            from pycalendar.core.solution_store import SolutionStore
            
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
            
            # Sauvegarder la solution
            print(f"  💾 Sauvegarde de la solution...")
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
            print(f"  ⚠️  Erreur lors de la sauvegarde de la solution: {e}")
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
            from interface.core.validator import SolutionValidator as SolutionValidatorV2
            
            print(f"\n🔍 Validation de la solution...")
            
            # Charger le JSON
            with open(solution_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Valider
            validator = SolutionValidatorV2()
            try:
                is_valid, issues = validator.validate_full(data)
            except Exception as e:
                print(f"  ⚠️  Erreur lors de la validation: {e}")
                import traceback
                traceback.print_exc()
                return
            
            # Afficher résumé
            from interface.core.validator import Severity
            errors = sum(1 for i in issues if i.severity == Severity.ERROR)
            warnings = sum(1 for i in issues if i.severity == Severity.WARNING)
            infos = sum(1 for i in issues if i.severity == Severity.INFO)
            
            if errors == 0 and warnings == 0 and infos == 0:
                print(f"  ✅ Solution valide - aucun problème détecté")
            else:
                print(f"  📊 Résumé validation: {errors} erreur(s), {warnings} avertissement(s), {infos} info(s)")
                
                if errors > 0 or warnings > 0:
                    # Afficher rapport détaillé si erreurs ou warnings
                    report = validator.generate_report(issues)
                    print(report)
                else:
                    # Juste les infos en mode condensé
                    print(f"     💡 Utilisez: python validate_solution.py {solution_path} --verbose pour plus de détails")
            
        except Exception as e:
            print(f"  ⚠️  Erreur lors de la validation: {e}")
            import traceback
            traceback.print_exc()
    
    def _exporter_solution(self, solution: Solution):
        """Export solution to files."""
        print("💾 Export de la solution...")
        ExcelExporter.export(solution, self.config.fichier_sortie)
        
        # Générer TOUS les créneaux possibles (occupés et libres)
        gymnases = self.source.charger_gymnases()
        tous_creneaux = DataTransformer.generer_creneaux(gymnases, self.config.nb_semaines, self.config.calendar_manager)
        
        # Stocker TOUS les créneaux dans metadata pour l'interface
        solution.metadata['creneaux_disponibles'] = tous_creneaux
        
        # Générer l'interface HTML interactive
        html_path = self.config.fichier_sortie.replace('.xlsx', '.html')
        generator = InterfaceGenerator()
        html_file = generator.generate(solution, html_path, self.config, types_poules=self.types_poules)
        
        print(f"\n🌐 Ouvrez le calendrier dans votre navigateur:")
        print(f"   file://{html_file}")
