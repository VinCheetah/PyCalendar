"""Configuration management for PyCalendar."""

import yaml
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from pathlib import Path


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
    
    # Advanced settings
    max_matchs_par_equipe_par_semaine: int
    afficher_progression: bool
    niveau_log: int
    
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
        # Find default config relative to this file
        this_dir = Path(__file__).parent
        default_path = this_dir.parent / "configs" / "default.yaml"
        
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
        
        # Store extra parameters
        config_dict['extra'] = merged_data.get('extra', {})
        
        return cls(**config_dict)
    
    def to_yaml(self, filepath: str):
        """Save configuration to YAML file."""
        data = {
            'fichiers': {
                'donnees': self.fichier_donnees,
                'sortie': self.fichier_sortie,
            },
            'planification': {
                'nb_semaines': self.nb_semaines,
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
                'penalite_avant_horaire_min': self.penalite_avant_horaire_min,
                'max_matchs_par_equipe_par_semaine': self.max_matchs_par_equipe_par_semaine,
                'penalites_espacement_repos': self.penalites_espacement_repos,
                # Compaction temporelle
                'compaction_temporelle_actif': self.compaction_temporelle_actif,
                'compaction_penalites_par_semaine': self.compaction_penalites_par_semaine,
                # Overlaps institution
                'overlap_institution_actif': self.overlap_institution_actif,
                'overlap_institution_poids': self.overlap_institution_poids,
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
