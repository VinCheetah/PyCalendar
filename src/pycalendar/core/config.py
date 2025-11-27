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
    
    # Solver configuration (CP-SAT uniquement)
    temps_max_secondes: int
    cpsat_warm_start: bool  # Utilise solution précédente comme point de départ
    cpsat_warm_start_file: str  # Nom du fichier de solution (défaut: "default")
    
    # Soft constraints weights
    # Préférences de gymnase (nouveau système avec bonus)
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
    
    # Hard constraint: No matches before preferred time (optional)
    horaire_avant_interdit: bool  # If True, strictly forbid matches before preferred time
    horaire_avant_tolerance: int  # Tolerance in minutes (0 = strict)
    
    # Temporal compaction (soft constraint)
    compaction_temporelle_actif: bool
    compaction_penalites_par_semaine: List[float]
    
    # Institution overlaps (soft constraint)
    overlap_institution_actif: bool
    overlap_institution_poids: float
    
    # Équilibrage des matchs (système max-min avec bonus progressif)
    equilibrage_actif: bool  # Activer le système de bonus progressif
    equilibrage_bonus_base: float  # Bonus pour le 1er match d'une équipe
    equilibrage_facteur_decroissance: float  # Multiplicateur pour chaque match suivant
    equilibrage_bonus_minimum: float  # Bonus plancher (éviter d'atteindre 0)
    
    # Ententes (specific institution pairs - reduced priority)
    entente_actif: bool  # Activer/désactiver la contrainte
    entente_penalite_non_planif: float  # Bonus réduit pour ententes (si système progressif désactivé)
    entente_facteur_reduction_bonus: float  # Facteur de réduction multiplicative du bonus total de l'équipe (ex: 0.90 = 10% de réduction par entente)
    
    # Contraintes temporelles (matches before/after specific week - e.g. CFE)
    contrainte_temporelle_actif: bool  # Activer/désactiver la contrainte
    contrainte_temporelle_penalite: float  # Pénalité si contrainte violée (mode souple)
    contrainte_temporelle_dure: bool  # Si True: contrainte dure (bloquante), sinon souple (pénalité)
    
    # Espacement aller-retour (pour poules de type Aller-Retour)
    aller_retour_espacement_actif: bool  # Activer/désactiver la contrainte d'espacement
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
    
    # Sport-specific parameters
    duree_match_minutes: int  # Durée d'un match en minutes (ex: 90 pour handball, 120 pour volley)
    
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
        
        # Solver parameters (CP-SAT uniquement)
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
            config_dict['penalite_apres_horaire_min'] = ct['penalite_apres_horaire_min']
            
            # Nouvelles préférences de gymnase avec bonus par rang
            config_dict['bonus_preferences_gymnases'] = ct['bonus_preferences_gymnases']
            
            # Adéquation niveau match / niveau gymnase
            # Convention: valeurs NÉGATIVES = bonus (réduction coût), POSITIVES = pénalité (augmentation coût)
            config_dict['penalite_niveau_gymnases_haut'] = ct['penalite_niveau_gymnases_haut']
            config_dict['penalite_niveau_gymnases_bas'] = ct['penalite_niveau_gymnases_bas']
            
            config_dict['penalite_avant_horaire_min'] = ct['penalite_avant_horaire_min']
            config_dict['penalite_avant_horaire_min_deux'] = ct['penalite_avant_horaire_min_deux']
            config_dict['penalite_horaire_diviseur'] = ct['penalite_horaire_diviseur']
            config_dict['penalite_horaire_tolerance'] = ct['penalite_horaire_tolerance']
            
            # Hard constraint: no matches before preferred time (optional)
            config_dict['horaire_avant_interdit'] = ct.get('horaire_avant_interdit', False)
            config_dict['horaire_avant_tolerance'] = ct.get('horaire_avant_tolerance', 0)
            
            config_dict['max_matchs_par_equipe_par_semaine'] = ct['max_matchs_par_equipe_par_semaine']
            
            # Espacement avec liste de pénalités (nouvelle version)
            config_dict['penalites_espacement_repos'] = ct.get('penalites_espacement_repos', [100.0, 50.0])
            
            # Compaction temporelle
            config_dict['compaction_temporelle_actif'] = ct['compaction_temporelle_actif']
            config_dict['compaction_penalites_par_semaine'] = ct['compaction_penalites_par_semaine']
            
            # Overlaps institution
            config_dict['overlap_institution_actif'] = ct['overlap_institution_actif']
            config_dict['overlap_institution_poids'] = ct['overlap_institution_poids']
            
            # Équilibrage des matchs (système max-min avec bonus progressif)
            config_dict['equilibrage_actif'] = ct.get('equilibrage_actif', True)
            config_dict['equilibrage_bonus_base'] = ct.get('equilibrage_bonus_base', 100000.0)
            config_dict['equilibrage_facteur_decroissance'] = ct.get('equilibrage_facteur_decroissance', 0.5)
            config_dict['equilibrage_bonus_minimum'] = ct.get('equilibrage_bonus_minimum', 1000.0)
            
            # Ententes (paires d'institutions spécifiques)
            config_dict['entente_actif'] = ct['entente_actif']
            config_dict['entente_penalite_non_planif'] = ct.get('entente_penalite_non_planif', 30.0)
            config_dict['entente_facteur_reduction_bonus'] = ct.get('entente_facteur_reduction_bonus', 0.90)
            
            # Contraintes temporelles (matchs avant/après semaine X)
            config_dict['contrainte_temporelle_actif'] = ct.get('contrainte_temporelle_actif', True)
            config_dict['contrainte_temporelle_penalite'] = ct.get('contrainte_temporelle_penalite', 500.0)
            config_dict['contrainte_temporelle_dure'] = ct.get('contrainte_temporelle_dure', False)
            
            # Espacement aller-retour (pour poules de type Aller-Retour)
            config_dict['aller_retour_espacement_actif'] = ct.get('aller_retour_espacement_actif', True)
            config_dict['aller_retour_penalite_meme_semaine'] = ct.get('aller_retour_penalite_meme_semaine', 5000.0)
            config_dict['aller_retour_penalite_consecutives'] = ct.get('aller_retour_penalite_consecutives', 2000.0)
        
        # Calendar management
        if 'calendrier' in merged_data:
            cal = merged_data['calendrier']
            config_dict['calendrier_actif'] = cal.get('actif', False)
            config_dict['calendrier_date_debut'] = cal.get('date_debut', '2025-09-01')
            config_dict['calendrier_jour_match'] = cal.get('jour_match', 'jeudi')
            config_dict['calendrier_semaines_banalisees'] = cal.get('semaines_banalisees', [])
        
        # Sport-specific parameters
        if 'sport' in merged_data:
            sport = merged_data['sport']
            config_dict['duree_match_minutes'] = sport.get('duree_match_minutes', 90)
        
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
            },
            'cpsat': {
                'temps_max_secondes': self.temps_max_secondes,
                'afficher_progression': self.afficher_progression,
                'niveau_log': self.niveau_log,
                'warm_start': self.cpsat_warm_start,
                'warm_start_file': self.cpsat_warm_start_file,
            },
            'contraintes': {
                'penalite_apres_horaire_min': self.penalite_apres_horaire_min,
                # Préférences de gymnase
                'bonus_preferences_gymnases': self.bonus_preferences_gymnases,
                # Pénalités pour gymnases par niveau
                'penalite_niveau_gymnases_haut': self.penalite_niveau_gymnases_haut,
                'penalite_niveau_gymnases_bas': self.penalite_niveau_gymnases_bas,
                'penalite_avant_horaire_min': self.penalite_avant_horaire_min,
                'penalite_avant_horaire_min_deux': self.penalite_avant_horaire_min_deux,
                'penalite_horaire_diviseur': self.penalite_horaire_diviseur,
                'penalite_horaire_tolerance': self.penalite_horaire_tolerance,
                'horaire_avant_interdit': self.horaire_avant_interdit,
                'horaire_avant_tolerance': self.horaire_avant_tolerance,
                'max_matchs_par_equipe_par_semaine': self.max_matchs_par_equipe_par_semaine,
                'penalites_espacement_repos': self.penalites_espacement_repos,
                # Compaction temporelle
                'compaction_temporelle_actif': self.compaction_temporelle_actif,
                'compaction_penalites_par_semaine': self.compaction_penalites_par_semaine,
                # Overlaps institution
                'overlap_institution_actif': self.overlap_institution_actif,
                'overlap_institution_poids': self.overlap_institution_poids,
                # Équilibrage des matchs (système max-min avec bonus progressif)
                'equilibrage_actif': self.equilibrage_actif,
                'equilibrage_bonus_base': self.equilibrage_bonus_base,
                'equilibrage_facteur_decroissance': self.equilibrage_facteur_decroissance,
                'equilibrage_bonus_minimum': self.equilibrage_bonus_minimum,
                # Ententes (paires d'institutions spécifiques)
                'entente_actif': self.entente_actif,
                'entente_penalite_non_planif': self.entente_penalite_non_planif,
                'entente_facteur_reduction_bonus': self.entente_facteur_reduction_bonus,
                # Contraintes temporelles (matchs avant/après semaine X)
                'contrainte_temporelle_actif': self.contrainte_temporelle_actif,
                'contrainte_temporelle_penalite': self.contrainte_temporelle_penalite,
                'contrainte_temporelle_dure': self.contrainte_temporelle_dure,
                # Espacement aller-retour
                'aller_retour_espacement_actif': self.aller_retour_espacement_actif,
                'aller_retour_penalite_meme_semaine': self.aller_retour_penalite_meme_semaine,
                'aller_retour_penalite_consecutives': self.aller_retour_penalite_consecutives,
            },
            'calendrier': {
                'actif': self.calendrier_actif,
                'date_debut': self.calendrier_date_debut,
                'jour_match': self.calendrier_jour_match,
                'semaines_banalisees': self.calendrier_semaines_banalisees,
            },
            'sport': {
                'duree_match_minutes': self.duree_match_minutes,
            },
            'extra': self.extra,
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
