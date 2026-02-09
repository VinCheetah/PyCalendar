"""Configuration management for PyCalendar."""

import yaml
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from pathlib import Path
from .calendar_manager import CalendarManager, CalendarConfig
from .sport_config import SportConfig, get_sport_presets


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
    cpsat_use_prefilter: bool  # Si True, préfiltre les combinaisons impossibles (plus rapide)
    cpsat_num_search_workers: int  # Nombre de threads pour la recherche parallèle
    cpsat_relative_gap_limit: float  # Limite d'écart relatif (0 = continuer jusqu'au timeout)
    cpsat_absolute_gap_limit: float  # Limite d'écart absolu (0 = continuer jusqu'au timeout)
    
    # Mode performance - contrôle la complexité du modèle
    cpsat_mode_fast: bool  # Si True, désactive automatiquement les contraintes coûteuses
    cpsat_enable_espacement_repos: bool  # Activer l'espacement repos (coûteux O(équipes×semaines²))
    cpsat_enable_aller_retour: bool  # Activer l'espacement aller-retour (coûteux O(paires×créneaux²))
    cpsat_espacement_repos_simplifie: bool  # Mode simplifié pour espacement repos
    cpsat_aller_retour_simplifie: bool  # Mode simplifié pour aller-retour
    
    # Soft constraints weights
    # Préférences de gymnase (nouveau système avec bonus)
    bonus_preferences_gymnases: List[float]  # Bonus par rang [rang1, rang2, ...]
    
    # Pondérations pour l'adéquation niveau match / niveau gymnase
    # Valeurs négatives = bonus (match prioritaire sur bon gymnase)
    # Valeurs positives = malus (match d'un niveau élevé sur gymnase faible)
    poids_niveaux_gymnases_haut: List[float]
    poids_niveaux_gymnases_bas: List[float]
    penalite_gymnase_priorite_genre: float
    
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
    coach_overlap_actif: bool
    coach_overlap_penalite_simultane_diff_gym: float
    coach_overlap_penalite_simultane_meme_gym: float
    coach_overlap_penalite_deplacement: float
    coach_overlap_bonus_consecutif: float
    coach_overlap_simultane_minutes: int
    coach_overlap_consecutif_min_minutes: int
    coach_overlap_consecutif_max_minutes: int
    coach_overlap_semaine_min: int
    
    # Équilibrage des matchs (système max-min avec bonus progressif)
    equilibrage_actif: bool  # Activer le système de bonus progressif
    equilibrage_bonus_base: float  # Bonus pour le 1er match d'une équipe
    equilibrage_facteur_decroissance: float  # Multiplicateur pour chaque match suivant
    equilibrage_bonus_minimum: float  # Bonus plancher (éviter d'atteindre 0)
    equilibrage_mode_simplifie: bool  # Mode simplifié O(équipes×seuils) sans gestion fine des ententes
    
    # Ententes (specific institution pairs - reduced priority)
    entente_actif: bool  # Activer/désactiver la contrainte
    entente_facteur_reduction_bonus: float  # Facteur de réduction multiplicative du bonus total de l'équipe (ex: 0.90 = 10% de réduction par entente)
    
    # Contraintes temporelles (matches before/after specific week - e.g. CFE)
    contrainte_temporelle_actif: bool  # Activer/désactiver la contrainte
    contrainte_temporelle_penalite: float  # Pénalité si contrainte violée (mode souple)
    contrainte_temporelle_dure: bool  # Si True: contrainte dure (bloquante), sinon souple (pénalité)
    
    # Espacement aller-retour (pour poules de type Aller-Retour)
    aller_retour_espacement_actif: bool  # Activer/désactiver la contrainte d'espacement
    aller_retour_penalites_par_ecart: List[float]  # Liste de pénalités par écart en semaines
    aller_retour_bonus_retour: float  # Ratio appliqué au bonus équil. pour les matchs retour
    
    # Calendar management
    calendrier_actif: bool  # Activer/désactiver la gestion calendrier avec dates réelles
    calendrier_date_debut: str  # Date de début de saison (format: YYYY-MM-DD)
    calendrier_jour_match: str  # Jour des matchs (ex: "jeudi", "Thursday")
    calendrier_semaines_banalisees: List[int]  # Liste des numéros de semaines banalisées (vacances)
    
    # Advanced settings
    max_matchs_par_equipe_par_semaine: int
    afficher_progression: bool
    
    # Sport-specific parameters (from sport presets)
    sport_type: str = "volleyball"           # Type de sport (ex: "volleyball", "handball")
    sport_prefix: str = "VB"                 # Préfixe dans les codes de poule (ex: "VB", "HB")
    sport_name: str = "Volleyball"           # Nom complet du sport
    sport_name_short: str = "Volley"         # Nom court
    sport_emoji: str = "🏐"                  # Emoji du sport
    duree_match_minutes: int = 90            # Durée d'un match en minutes
    duree_entre_matchs_minutes: int = 15     # Temps entre deux matchs
    sport_score_format: str = "points"       # Format des scores (sets ou points)
    sport_niveaux: List[str] = field(default_factory=lambda: ["A1", "A2", "A3", "A4"])
    sport_genres: List[str] = field(default_factory=lambda: ["M", "F"])
    sport_types_championnat: List[str] = field(default_factory=lambda: ["Acad", "CFE", "CFU"])
    
    # Additional parameters
    extra: Dict[str, Any] = field(default_factory=dict)
    # Metadata
    source_path: Optional[str] = None  # Fichier YAML d'origine
    
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
            config_dict['cpsat_warm_start'] = c.get('warm_start', True)  # Par défaut True
            config_dict['cpsat_warm_start_file'] = c.get('warm_start_file', 'default')  # Par défaut "default"
            config_dict['cpsat_use_prefilter'] = c.get('use_prefilter', True)  # Par défaut True (préfiltrage actif)
            config_dict['cpsat_num_search_workers'] = c.get('num_search_workers', 8)  # Par défaut 8 threads
            config_dict['cpsat_relative_gap_limit'] = c.get('relative_gap_limit', 0.0)  # Par défaut 0
            config_dict['cpsat_absolute_gap_limit'] = c.get('absolute_gap_limit', 0.0)  # Par défaut 0
            
            # Mode performance
            config_dict['cpsat_mode_fast'] = c.get('mode_fast', False)  # Par défaut False
            config_dict['cpsat_enable_espacement_repos'] = c.get('enable_espacement_repos', True)
            config_dict['cpsat_enable_aller_retour'] = c.get('enable_aller_retour_espacement', True)
            config_dict['cpsat_espacement_repos_simplifie'] = c.get('espacement_repos_simplifie', False)
            config_dict['cpsat_aller_retour_simplifie'] = c.get('aller_retour_simplifie', False)
        
        # Constraints
        if 'contraintes' in merged_data:
            ct = merged_data['contraintes']
            config_dict['penalite_apres_horaire_min'] = ct['penalite_apres_horaire_min']
            
            # Nouvelles préférences de gymnase avec bonus par rang
            config_dict['bonus_preferences_gymnases'] = ct['bonus_preferences_gymnases']
            
            # Adéquation niveau match / niveau gymnase
            poids_haut = ct.get('poids_niveaux_gymnases_haut', ct.get('penalite_niveau_gymnases_haut'))
            poids_bas = ct.get('poids_niveaux_gymnases_bas', ct.get('penalite_niveau_gymnases_bas'))
            if poids_haut is None or poids_bas is None:
                raise KeyError("Les pondérations de niveaux de gymnase sont manquantes dans la configuration")
            config_dict['poids_niveaux_gymnases_haut'] = poids_haut
            config_dict['poids_niveaux_gymnases_bas'] = poids_bas
            config_dict['penalite_gymnase_priorite_genre'] = ct.get('penalite_gymnase_priorite_genre', 0.0)

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
            config_dict['coach_overlap_actif'] = ct.get('coach_overlap_actif', False)
            config_dict['coach_overlap_penalite_simultane_diff_gym'] = ct.get('coach_overlap_penalite_simultane_diff_gym', 0.0)
            config_dict['coach_overlap_penalite_simultane_meme_gym'] = ct.get('coach_overlap_penalite_simultane_meme_gym', 0.0)
            config_dict['coach_overlap_penalite_deplacement'] = ct.get('coach_overlap_penalite_deplacement', 0.0)
            config_dict['coach_overlap_bonus_consecutif'] = ct.get('coach_overlap_bonus_consecutif', 0.0)
            config_dict['coach_overlap_simultane_minutes'] = ct.get('coach_overlap_simultane_minutes', 60)
            config_dict['coach_overlap_consecutif_min_minutes'] = ct.get('coach_overlap_consecutif_min_minutes', 60)
            config_dict['coach_overlap_consecutif_max_minutes'] = ct.get('coach_overlap_consecutif_max_minutes', 180)
            config_dict['coach_overlap_semaine_min'] = ct.get(
                'coach_overlap_semaine_min',
                config_dict.get('semaine_min', 1)
            )
            
            # Équilibrage des matchs (système max-min avec bonus progressif)
            config_dict['equilibrage_actif'] = ct.get('equilibrage_actif', True)
            config_dict['equilibrage_bonus_base'] = ct.get('equilibrage_bonus_base', 100000.0)
            config_dict['equilibrage_facteur_decroissance'] = ct.get('equilibrage_facteur_decroissance', 0.5)
            config_dict['equilibrage_bonus_minimum'] = ct.get('equilibrage_bonus_minimum', 1000.0)
            config_dict['equilibrage_mode_simplifie'] = ct.get('equilibrage_mode_simplifie', False)
            
            # Ententes (paires d'institutions spécifiques)
            config_dict['entente_actif'] = ct['entente_actif']
            config_dict['entente_facteur_reduction_bonus'] = ct.get('entente_facteur_reduction_bonus', 0.90)
            
            # Contraintes temporelles (matchs avant/après semaine X)
            config_dict['contrainte_temporelle_actif'] = ct.get('contrainte_temporelle_actif', True)
            config_dict['contrainte_temporelle_penalite'] = ct.get('contrainte_temporelle_penalite', 500.0)
            config_dict['contrainte_temporelle_dure'] = ct.get('contrainte_temporelle_dure', False)
            
            # Espacement aller-retour (pour poules de type Aller-Retour)
            config_dict['aller_retour_espacement_actif'] = ct.get('aller_retour_espacement_actif', True)
            config_dict['aller_retour_penalites_par_ecart'] = ct.get('aller_retour_penalites_par_ecart', [])
            config_dict['aller_retour_bonus_retour'] = ct.get('aller_retour_bonus_retour', 1.0)
        
        # Calendar management
        if 'calendrier' in merged_data:
            cal = merged_data['calendrier']
            config_dict['calendrier_actif'] = cal.get('actif', False)
            config_dict['calendrier_date_debut'] = cal.get('date_debut', '2025-09-01')
            config_dict['calendrier_jour_match'] = cal.get('jour_match', 'jeudi')
            config_dict['calendrier_semaines_banalisees'] = cal.get('semaines_banalisees', [])
        
        # Sport-specific parameters - Load from presets first, then override with config
        sport_data = merged_data.get('sport', {})
        sport_type_or_preset = sport_data.get('type', sport_data.get('preset', 'volleyball'))
        
        # Get sport preset as base
        sport_presets = get_sport_presets()
        sport_preset = sport_presets.get_sport(sport_type_or_preset) or sport_presets.default_sport
        
        # Apply preset values as defaults, then override with explicit config
        config_dict['sport_type'] = sport_data.get('type', sport_preset.type)
        config_dict['sport_prefix'] = sport_data.get('prefix', sport_preset.prefix)
        config_dict['sport_name'] = sport_data.get('name', sport_preset.name)
        config_dict['sport_name_short'] = sport_data.get('name_short', sport_preset.name_short)
        config_dict['sport_emoji'] = sport_data.get('emoji', sport_preset.emoji)
        config_dict['duree_match_minutes'] = sport_data.get('duree_match_minutes', sport_preset.duree_match_minutes)
        config_dict['duree_entre_matchs_minutes'] = sport_data.get('duree_entre_matchs_minutes', sport_preset.duree_entre_matchs_minutes)
        config_dict['sport_score_format'] = sport_data.get('score_format', sport_preset.score_format)
        config_dict['sport_niveaux'] = sport_data.get('niveaux', sport_preset.niveaux)
        config_dict['sport_genres'] = sport_data.get('genres', sport_preset.genres)
        config_dict['sport_types_championnat'] = sport_data.get('types_championnat', sport_preset.types_championnat)
        
        # Store extra parameters
        config_dict['extra'] = merged_data.get('extra', {})

        # Keep track of YAML path for diagnostics / warm start
        config_dict['source_path'] = str(user_path)
        
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
                'warm_start': self.cpsat_warm_start,
                'warm_start_file': self.cpsat_warm_start_file,
                'use_prefilter': self.cpsat_use_prefilter,
                'num_search_workers': self.cpsat_num_search_workers,
                'relative_gap_limit': self.cpsat_relative_gap_limit,
                'absolute_gap_limit': self.cpsat_absolute_gap_limit,
            },
            'contraintes': {
                'penalite_apres_horaire_min': self.penalite_apres_horaire_min,
                # Préférences de gymnase
                'bonus_preferences_gymnases': self.bonus_preferences_gymnases,
                # Pénalités pour gymnases par niveau
                'poids_niveaux_gymnases_haut': self.poids_niveaux_gymnases_haut,
                'poids_niveaux_gymnases_bas': self.poids_niveaux_gymnases_bas,
                'penalite_gymnase_priorite_genre': self.penalite_gymnase_priorite_genre,
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
                'coach_overlap_actif': self.coach_overlap_actif,
                'coach_overlap_penalite_simultane_diff_gym': self.coach_overlap_penalite_simultane_diff_gym,
                'coach_overlap_penalite_simultane_meme_gym': self.coach_overlap_penalite_simultane_meme_gym,
                'coach_overlap_penalite_deplacement': self.coach_overlap_penalite_deplacement,
                'coach_overlap_bonus_consecutif': self.coach_overlap_bonus_consecutif,
                'coach_overlap_simultane_minutes': self.coach_overlap_simultane_minutes,
                'coach_overlap_consecutif_min_minutes': self.coach_overlap_consecutif_min_minutes,
                'coach_overlap_consecutif_max_minutes': self.coach_overlap_consecutif_max_minutes,
                'coach_overlap_semaine_min': self.coach_overlap_semaine_min,
                # Équilibrage des matchs (système max-min avec bonus progressif)
                'equilibrage_actif': self.equilibrage_actif,
                'equilibrage_bonus_base': self.equilibrage_bonus_base,
                'equilibrage_facteur_decroissance': self.equilibrage_facteur_decroissance,
                'equilibrage_bonus_minimum': self.equilibrage_bonus_minimum,
                # Ententes (paires d'institutions spécifiques)
                'entente_actif': self.entente_actif,
                'entente_facteur_reduction_bonus': self.entente_facteur_reduction_bonus,
                # Contraintes temporelles (matchs avant/après semaine X)
                'contrainte_temporelle_actif': self.contrainte_temporelle_actif,
                'contrainte_temporelle_penalite': self.contrainte_temporelle_penalite,
                'contrainte_temporelle_dure': self.contrainte_temporelle_dure,
                # Espacement aller-retour
                'aller_retour_espacement_actif': self.aller_retour_espacement_actif,
                'aller_retour_penalites_par_ecart': self.aller_retour_penalites_par_ecart,
                'aller_retour_bonus_retour': self.aller_retour_bonus_retour,
            },
            'calendrier': {
                'actif': self.calendrier_actif,
                'date_debut': self.calendrier_date_debut,
                'jour_match': self.calendrier_jour_match,
                'semaines_banalisees': self.calendrier_semaines_banalisees,
            },
            'sport': {
                'type': self.sport_type,
                'prefix': self.sport_prefix,
                'name': self.sport_name,
                'name_short': self.sport_name_short,
                'emoji': self.sport_emoji,
                'duree_match_minutes': self.duree_match_minutes,
                'duree_entre_matchs_minutes': self.duree_entre_matchs_minutes,
                'score_format': self.sport_score_format,
                'niveaux': self.sport_niveaux,
                'genres': self.sport_genres,
                'types_championnat': self.sport_types_championnat,
            },
            'extra': self.extra,
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
