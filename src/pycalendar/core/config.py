"""Configuration management for PyCalendar."""

import yaml
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from pathlib import Path
from .calendar_manager import CalendarManager, CalendarConfig


@dataclass
class Config:
    """
    Main configuration class.
    
    All default values are loaded from configs/default.yaml.
    No hardcoded defaults in this class to avoid conflicts.
    """
    
    # Files
    fichier_donnees: str
    fichier_sortie: str
    
    # Planning parameters
    nb_semaines: int
    semaine_min: int  # Semaine minimum pour la planification (permet de simuler une compétition déjà commencée)
    taille_poule_min: int
    taille_poule_max: int
    
    # Solver configuration
    strategie: str
    temps_max_secondes: int
    nb_essais: int
    fallback_greedy: bool
    cpsat_warm_start: bool  # Utilise solution précédente comme point de départ
    cpsat_warm_start_file: str  # Nom du fichier de solution (défaut: "default")
    
    # Hard constraints weights
    poids_indisponibilite: float
    poids_capacite_gymnase: float
    
    # Soft constraints weights
    poids_equilibrage_charge: float
    
    # Préférences de gymnase (nouveau système avec bonus)
    nb_preferences_gymnases: int  # Nombre de gymnases préférés configurables (défaut: 5)
    bonus_preferences_gymnases: List[float]  # Bonus par rang [rang1, rang2, ...]
    
    # Pénalités pour gymnases par niveau (classification haut/bas niveau)
    # Valeurs positives = pénalités (augmentent le coût)
    penalite_niveau_gymnases_haut: List[float]  # Pénalité par niveau de match pour gymnases haut niveau
    penalite_niveau_gymnases_bas: List[float]  # Pénalité par niveau de match pour gymnases bas niveau
    
    # Spacing constraint (list of penalties by weeks of rest)
    penalites_espacement_repos: List[float]
    
    # Preferred time penalties (with tolerance system)
    penalite_apres_horaire_min: float
    penalite_avant_horaire_min: float
    penalite_avant_horaire_min_deux: float
    penalite_horaire_diviseur: float
    penalite_horaire_tolerance: float
    
    # Temporal compaction (soft constraint)
    compaction_temporelle_actif: bool
    compaction_penalites_par_semaine: List[float]
    
    # Institution overlaps (soft constraint)
    overlap_institution_actif: bool
    overlap_institution_poids: float
    overlap_institution_institutions: List[str]  # Liste des institutions à surveiller (vide = toutes)
    
    # Match scheduling (bonus/penalties for scheduled vs unscheduled matches)
    penalite_match_non_planif: float  # Pénalité si match normal non planifié (CP-SAT uniquement)
    
    # Ententes (specific institution pairs - reduced penalty when unscheduled)
    entente_penalite_non_planif: float  # Pénalité par défaut si match entente non planifié
    entente_actif: bool  # Activer/désactiver la contrainte
    
    # Contraintes temporelles (matches before/after specific week - e.g. CFE)
    contrainte_temporelle_actif: bool  # Activer/désactiver la contrainte
    contrainte_temporelle_penalite: float  # Pénalité si contrainte violée (mode souple)
    contrainte_temporelle_dure: bool  # Si True: contrainte dure (bloquante), sinon souple (pénalité)
    
    # Espacement aller-retour (pour poules de type Aller-Retour)
    aller_retour_espacement_actif: bool  # Activer/désactiver la contrainte d'espacement
    aller_retour_min_semaines: int  # Espacement minimum en semaines entre aller et retour
    aller_retour_penalite_meme_semaine: float  # Pénalité si aller et retour dans même semaine
    aller_retour_penalite_consecutives: float  # Pénalité si aller et retour dans semaines consécutives
    
    # Calendar management
    calendrier_actif: bool  # Activer/désactiver la gestion calendrier avec dates réelles
    calendrier_date_debut: str  # Date de début de saison (format: YYYY-MM-DD)
    calendrier_jour_match: str  # Jour des matchs (ex: "jeudi", "Thursday")
    calendrier_semaines_banalisees: List[int]  # Liste des numéros de semaines banalisées (vacances)
    
    # Advanced settings
    max_matchs_par_equipe_par_semaine: int
    afficher_progression: bool
    niveau_log: int
    
    # Solution format
    solution_format: str = "v2.0"  # Format de sauvegarde: 'v1.0' ou 'v2.0' (défaut: 'v2.0')
    
    # Additional parameters
    extra: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def _load_yaml_file(cls, filepath: str) -> Dict[str, Any]:
        """Load and parse a YAML file."""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {filepath}")
        
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    
    @classmethod
    def _merge_dicts(cls, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively merge override dict into base dict.
        Values in override take precedence over values in base.
        """
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = cls._merge_dicts(result[key], value)
            else:
                result[key] = value
        return result
    
    @classmethod
    def from_yaml(cls, filepath: str) -> "Config":
        """
        Load configuration from YAML file.
        
        Always loads configs/default.yaml first, then merges user config on top.
        This ensures all required values have defaults and user can override any value.
        
        Args:
            filepath: Path to user configuration file
            
        Returns:
            Config instance with merged values
        """
        # Find default config - go up to project root from src/pycalendar/core
        this_dir = Path(__file__).parent
        project_root = this_dir.parent.parent.parent  # src/pycalendar/core -> src/pycalendar -> src -> root
        default_path = project_root / "configs" / "default.yaml"
        
        # Load default configuration first
        default_data = cls._load_yaml_file(str(default_path))
        
        # Load user configuration (if different from default)
        user_path = Path(filepath).resolve()
        if user_path == default_path.resolve():
            # User is loading default.yaml directly
            merged_data = default_data
        else:
            # Load user config and merge with defaults
            user_data = cls._load_yaml_file(filepath)
            merged_data = cls._merge_dicts(default_data, user_data)
        
        # Extract values from merged data
        config_dict = {}
        
        # Files
        if 'fichiers' in merged_data:
            config_dict['fichier_donnees'] = merged_data['fichiers'].get('donnees', merged_data['fichiers'].get('config_central'))
            config_dict['fichier_sortie'] = merged_data['fichiers'].get('sortie')
        
        # Planning
        if 'planification' in merged_data:
            p = merged_data['planification']
            config_dict['nb_semaines'] = p['nb_semaines']
            config_dict['semaine_min'] = p.get('semaine_min', 1)  # Par défaut: 1 (début normal)
            config_dict['strategie'] = p['strategie']
            config_dict['fallback_greedy'] = p['fallback_greedy']
            config_dict['taille_poule_min'] = p['taille_poule_min']
            config_dict['taille_poule_max'] = p['taille_poule_max']
        
        # Solver parameters
        if 'greedy' in merged_data:
            config_dict['nb_essais'] = merged_data['greedy']['nb_essais']
        
        if 'cpsat' in merged_data:
            c = merged_data['cpsat']
            config_dict['temps_max_secondes'] = c['temps_max_secondes']
            config_dict['afficher_progression'] = c['afficher_progression']
            config_dict['niveau_log'] = c['niveau_log']
            config_dict['cpsat_warm_start'] = c.get('warm_start', True)  # Par défaut True
            config_dict['cpsat_warm_start_file'] = c.get('warm_start_file', 'default')  # Par défaut "default"
        
        # Constraints
        if 'contraintes' in merged_data:
            ct = merged_data['contraintes']
            config_dict['poids_indisponibilite'] = ct['poids_indisponibilite']
            config_dict['poids_capacite_gymnase'] = ct['poids_capacite_gymnase']
            config_dict['poids_equilibrage_charge'] = ct['poids_equilibrage_charge']
            config_dict['penalite_apres_horaire_min'] = ct['penalite_apres_horaire_min']
            
            # Nouvelles préférences de gymnase avec bonus par rang
            config_dict['nb_preferences_gymnases'] = ct['nb_preferences_gymnases']
            config_dict['bonus_preferences_gymnases'] = ct['bonus_preferences_gymnases']
            
            # Pénalités pour gymnases par niveau (classification haut/bas niveau)
            # Support des anciens noms (bonus_*) pour rétrocompatibilité
            config_dict['penalite_niveau_gymnases_haut'] = ct.get('penalite_niveau_gymnases_haut', 
                                                                    ct.get('bonus_niveau_gymnases_haut', [0, 2, 5, 7]))
            config_dict['penalite_niveau_gymnases_bas'] = ct.get('penalite_niveau_gymnases_bas',
                                                                   ct.get('bonus_niveau_gymnases_bas', [10, 8, 5, 3]))
            
            config_dict['penalite_avant_horaire_min'] = ct['penalite_avant_horaire_min']
            config_dict['penalite_avant_horaire_min_deux'] = ct['penalite_avant_horaire_min_deux']
            config_dict['penalite_horaire_diviseur'] = ct['penalite_horaire_diviseur']
            config_dict['penalite_horaire_tolerance'] = ct['penalite_horaire_tolerance']
            config_dict['max_matchs_par_equipe_par_semaine'] = ct['max_matchs_par_equipe_par_semaine']
            
            # Espacement avec liste de pénalités (nouvelle version)
            config_dict['penalites_espacement_repos'] = ct.get('penalites_espacement_repos', [100.0, 50.0])
            
            # Compaction temporelle
            config_dict['compaction_temporelle_actif'] = ct['compaction_temporelle_actif']
            config_dict['compaction_penalites_par_semaine'] = ct['compaction_penalites_par_semaine']
            
            # Overlaps institution
            config_dict['overlap_institution_actif'] = ct['overlap_institution_actif']
            config_dict['overlap_institution_poids'] = ct['overlap_institution_poids']
            config_dict['overlap_institution_institutions'] = ct.get('overlap_institution_institutions', [])
            
            # Match scheduling (bonus/penalties for scheduled vs unscheduled matches)
            config_dict['penalite_match_non_planif'] = ct.get('penalite_match_non_planif', 10000.0)
            
            # Ententes (paires d'institutions spécifiques)
            config_dict['entente_actif'] = ct['entente_actif']
            config_dict['entente_penalite_non_planif'] = ct['entente_penalite_non_planif']
            
            # Contraintes temporelles (matchs avant/après semaine X)
            config_dict['contrainte_temporelle_actif'] = ct.get('contrainte_temporelle_actif', True)
            config_dict['contrainte_temporelle_penalite'] = ct.get('contrainte_temporelle_penalite', 500.0)
            config_dict['contrainte_temporelle_dure'] = ct.get('contrainte_temporelle_dure', False)
            
            # Espacement aller-retour (pour poules de type Aller-Retour)
            config_dict['aller_retour_espacement_actif'] = ct.get('aller_retour_espacement_actif', True)
            config_dict['aller_retour_min_semaines'] = ct.get('aller_retour_min_semaines', 2)
            config_dict['aller_retour_penalite_meme_semaine'] = ct.get('aller_retour_penalite_meme_semaine', 5000.0)
            config_dict['aller_retour_penalite_consecutives'] = ct.get('aller_retour_penalite_consecutives', 2000.0)
        
        # Calendar management
        if 'calendrier' in merged_data:
            cal = merged_data['calendrier']
            config_dict['calendrier_actif'] = cal.get('actif', False)
            config_dict['calendrier_date_debut'] = cal.get('date_debut', '2025-09-01')
            config_dict['calendrier_jour_match'] = cal.get('jour_match', 'jeudi')
            config_dict['calendrier_semaines_banalisees'] = cal.get('semaines_banalisees', [])
        
        # Store extra parameters
        config_dict['extra'] = merged_data.get('extra', {})
        
        return cls(**config_dict)
    
    @property
    def calendar_manager(self) -> Optional[CalendarManager]:
        """Get calendar manager if calendar is active."""
        if not self.calendrier_actif:
            return None
        
        calendar_config = CalendarConfig(
            date_debut=self.calendrier_date_debut,
            jour_match=self.calendrier_jour_match,
            semaines_banalisees=self.calendrier_semaines_banalisees
        )
        return CalendarManager(calendar_config)
    
    def to_yaml(self, filepath: str):
        """Save configuration to YAML file."""
        data = {
            'fichiers': {
                'donnees': self.fichier_donnees,
                'sortie': self.fichier_sortie,
            },
            'planification': {
                'nb_semaines': self.nb_semaines,
                'semaine_min': self.semaine_min,
                'strategie': self.strategie,
                'fallback_greedy': self.fallback_greedy,
                'taille_poule_min': self.taille_poule_min,
                'taille_poule_max': self.taille_poule_max,
            },
            'greedy': {
                'nb_essais': self.nb_essais,
            },
            'cpsat': {
                'temps_max_secondes': self.temps_max_secondes,
                'afficher_progression': self.afficher_progression,
                'niveau_log': self.niveau_log,
            },
            'contraintes': {
                'poids_indisponibilite': self.poids_indisponibilite,
                'poids_capacite_gymnase': self.poids_capacite_gymnase,
                'poids_equilibrage_charge': self.poids_equilibrage_charge,
                'penalite_apres_horaire_min': self.penalite_apres_horaire_min,
                # Nouvelles préférences de gymnase
                'nb_preferences_gymnases': self.nb_preferences_gymnases,
                'bonus_preferences_gymnases': self.bonus_preferences_gymnases,
                # Pénalités pour gymnases par niveau (classification haut/bas niveau)
                'penalite_niveau_gymnases_haut': self.penalite_niveau_gymnases_haut,
                'penalite_niveau_gymnases_bas': self.penalite_niveau_gymnases_bas,
                'penalite_avant_horaire_min': self.penalite_avant_horaire_min,
                'penalite_avant_horaire_min_deux': self.penalite_avant_horaire_min_deux,
                'penalite_horaire_diviseur': self.penalite_horaire_diviseur,
                'penalite_horaire_tolerance': self.penalite_horaire_tolerance,
                'max_matchs_par_equipe_par_semaine': self.max_matchs_par_equipe_par_semaine,
                'penalites_espacement_repos': self.penalites_espacement_repos,
                # Compaction temporelle
                'compaction_temporelle_actif': self.compaction_temporelle_actif,
                'compaction_penalites_par_semaine': self.compaction_penalites_par_semaine,
                # Overlaps institution
                'overlap_institution_actif': self.overlap_institution_actif,
                'overlap_institution_poids': self.overlap_institution_poids,
                'overlap_institution_institutions': self.overlap_institution_institutions,
                # Match scheduling (bonus/penalties for scheduled vs unscheduled matches)
                'penalite_match_non_planif': self.penalite_match_non_planif,
                # Ententes (paires d'institutions spécifiques)
                'entente_actif': self.entente_actif,
                'entente_penalite_non_planif': self.entente_penalite_non_planif,
                # Contraintes temporelles (matchs avant/après semaine X)
                'contrainte_temporelle_actif': self.contrainte_temporelle_actif,
                'contrainte_temporelle_penalite': self.contrainte_temporelle_penalite,
                'contrainte_temporelle_dure': self.contrainte_temporelle_dure,
            },
            'extra': self.extra,
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
