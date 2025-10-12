"""HTML calendar visualizer V2 - Architecture modulaire professionnelle."""

import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from core.models import Solution, Match, Creneau
from core.config import Config
from constraints.base import ConstraintValidator
from constraints.team_constraints import (
    TeamAvailabilityConstraint,
    MaxMatchesPerWeekConstraint,
    TeamNotPlayingSimultaneouslyConstraint
)
from constraints.schedule_constraints import (
    MinSpacingConstraint,
    LoadBalancingConstraint,
    PreferredTimeConstraint
)


class HTMLVisualizerV2:
    """Génère une visualisation HTML moderne avec architecture modulaire."""
    
    @staticmethod
    def generate(solution: Solution, output_path: str, config: Optional[Config] = None):
        """Génère la visualisation HTML V2."""
        
        # Préparer les données
        matches_data = HTMLVisualizerV2._prepare_matches_data(
            solution.matchs_planifies, 
            solution, 
            config
        )
        unscheduled_data = HTMLVisualizerV2._prepare_unscheduled_data(solution.matchs_non_planifies)
        available_slots_data = HTMLVisualizerV2._prepare_available_slots_data(
            solution.metadata.get('creneaux_disponibles', [])
        )
        
        # Charger le template HTML
        template_path = Path(__file__).parent / 'templates' / 'main.html'
        with open(template_path, 'r', encoding='utf-8') as f:
            html_template = f.read()
        
        # Charger les composants
        components_dir = Path(__file__).parent / 'components'
        
        # CSS
        css_content = HTMLVisualizerV2._load_component(components_dir / 'styles.css')
        css_html = f'<style>\n{css_content}\n</style>'
        
        # JavaScript modules
        js_modules = [
            'utils.js',
            'match-card.js',
            'calendar-view.js',
            'calendar-grid-view.js',  # Nouvelle vue calendrier type Google
            'penalties-view.js',  # Vue des pénalités
            'filters.js'
        ]
        
        js_html = ''
        for module in js_modules:
            js_content = HTMLVisualizerV2._load_component(components_dir / module)
            js_html += f'<script>\n{js_content}\n</script>\n'
        
        # Remplacer les placeholders
        html_content = html_template.replace('<!-- STYLES_PLACEHOLDER -->', css_html)
        html_content = html_content.replace('<!-- SCRIPTS_PLACEHOLDER -->', js_html)
        
        # Injecter les données
        html_content = html_content.replace(
            '{{MATCHES_DATA}}',
            json.dumps(matches_data, ensure_ascii=False, indent=2)
        )
        html_content = html_content.replace(
            '{{UNSCHEDULED_DATA}}',
            json.dumps(unscheduled_data, ensure_ascii=False, indent=2)
        )
        html_content = html_content.replace(
            '{{AVAILABLE_SLOTS_DATA}}',
            json.dumps(available_slots_data, ensure_ascii=False, indent=2)
        )
        
        # Écrire le fichier
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✓ Visualisation HTML V2 générée: {output_path}")
        return str(output_file.absolute())
    
    @staticmethod
    def _load_component(path: Path) -> str:
        """Charge un fichier composant."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"⚠️  Composant introuvable: {path}")
            return ''
    
    @staticmethod
    def _build_validator(config: Config) -> ConstraintValidator:
        """Build constraint validator with all constraints."""
        validator = ConstraintValidator()
        
        validator.add_constraint(TeamAvailabilityConstraint(
            weight=config.poids_indisponibilite
        ))
        validator.add_constraint(MaxMatchesPerWeekConstraint(
            max_matches=config.max_matchs_par_equipe_par_semaine,
            weight=config.poids_capacite_gymnase
        ))
        validator.add_constraint(TeamNotPlayingSimultaneouslyConstraint(
            weight=config.poids_indisponibilite
        ))
        validator.add_constraint(MinSpacingConstraint(
            penalty_list=config.penalites_espacement_repos
        ))
        validator.add_constraint(LoadBalancingConstraint(
            weight=config.poids_equilibrage_charge
        ))
        validator.add_constraint(PreferredTimeConstraint(
            weight=config.penalite_apres_horaire_min,
            penalty_before_one=config.penalite_avant_horaire_min,
            penalty_before_both=config.penalite_avant_horaire_min_deux,
            divisor=config.penalite_horaire_diviseur,
            tolerance=config.penalite_horaire_tolerance
        ))
        # Note: Les préférences de gymnase sont maintenant gérées directement dans les solveurs
        
        return validator
    
    @staticmethod
    def _calculate_match_penalties(solution: Solution, config: Optional[Config]) -> Dict[str, float]:
        """Calculate penalty for each match in the solution."""
        if config is None:
            return {}
        
        penalties = {}
        validator = HTMLVisualizerV2._build_validator(config)
        
        # Build solution state
        solution_state = {
            'matchs_planifies': [],
            'creneaux_utilises': set(),
            'matchs_par_equipe': {},
            'matchs_par_semaine': {}
        }
        
        for match in solution.matchs_planifies:
            if match.creneau:
                # Calculate penalty for this match
                _, penalty = validator.validate_assignment(match, match.creneau, solution_state)
                
                # Create unique key for this match
                match_key = f"{match.equipe1.id_unique}_{match.equipe2.id_unique}_{match.poule}"
                penalties[match_key] = penalty
                
                # Update solution state for next match
                solution_state['matchs_planifies'].append(match)
                solution_state['creneaux_utilises'].add(
                    (match.creneau.gymnase, match.creneau.semaine, match.creneau.horaire)
                )
                
                # Update matchs par équipe
                for equipe in [match.equipe1, match.equipe2]:
                    equipe_id = equipe.id_unique
                    if equipe_id not in solution_state['matchs_par_equipe']:
                        solution_state['matchs_par_equipe'][equipe_id] = []
                    solution_state['matchs_par_equipe'][equipe_id].append(match)
                
                # Update matchs par semaine
                semaine = match.creneau.semaine
                if semaine not in solution_state['matchs_par_semaine']:
                    solution_state['matchs_par_semaine'][semaine] = []
                solution_state['matchs_par_semaine'][semaine].append(match)
        
        return penalties
    
    @staticmethod
    def _prepare_matches_data(matches: List[Match], solution: Solution, config: Optional[Config] = None) -> List[Dict]:
        """Prépare les données des matchs planifiés."""
        # Calculate penalties if config is provided
        penalties = HTMLVisualizerV2._calculate_match_penalties(solution, config)
        
        data = []
        for match in matches:
            if match.creneau:
                # Create match key to lookup penalty
                match_key = f"{match.equipe1.id_unique}_{match.equipe2.id_unique}_{match.poule}"
                penalty = penalties.get(match_key, 0.0)
                
                data.append({
                    'equipe1': match.equipe1.nom,
                    'equipe2': match.equipe2.nom,
                    'equipe1_genre': match.equipe1.genre,
                    'equipe2_genre': match.equipe2.genre,
                    'equipe1_horaires_preferes': match.equipe1.horaires_preferes if match.equipe1.horaires_preferes else [],
                    'equipe2_horaires_preferes': match.equipe2.horaires_preferes if match.equipe2.horaires_preferes else [],
                    'institution1': match.equipe1.institution,
                    'institution2': match.equipe2.institution,
                    'poule': match.poule,
                    'semaine': match.creneau.semaine,
                    'horaire': match.creneau.horaire,
                    'gymnase': match.creneau.gymnase,
                    'penalty': penalty
                })
        return data
    
    @staticmethod
    def _prepare_unscheduled_data(matches: List[Match]) -> List[Dict]:
        """Prépare les données des matchs non planifiés."""
        data = []
        for match in matches:
            data.append({
                'equipe1': match.equipe1.nom,
                'equipe2': match.equipe2.nom,
                'equipe1_genre': match.equipe1.genre,
                'equipe2_genre': match.equipe2.genre,
                'equipe1_horaires_preferes': match.equipe1.horaires_preferes if match.equipe1.horaires_preferes else [],
                'equipe2_horaires_preferes': match.equipe2.horaires_preferes if match.equipe2.horaires_preferes else [],
                'institution1': match.equipe1.institution,
                'institution2': match.equipe2.institution,
                'poule': match.poule
            })
        return data
    
    @staticmethod
    def _prepare_available_slots_data(slots: List[Creneau]) -> List[Dict]:
        """Prépare les données des créneaux disponibles."""
        data = []
        for slot in slots:
            data.append({
                'semaine': slot.semaine,
                'horaire': slot.horaire,
                'gymnase': slot.gymnase
            })
        return data
