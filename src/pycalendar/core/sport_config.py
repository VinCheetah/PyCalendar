"""
Sport configuration and presets management for PyCalendar.

This module provides:
- Loading sport presets from YAML configuration
- Sport-specific parameters and settings
- Validation of sport configuration
"""

import yaml
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class SportConfig:
    """
    Configuration d'un sport spécifique.
    
    Contient tous les paramètres propres à un sport (durée des matchs,
    format des scores, préfixe de poule, etc.)
    """
    # Identifiants
    type: str                                    # Identifiant unique du sport (ex: "volleyball")
    prefix: str                                  # Préfixe dans les codes de poule (ex: "VB")
    name: str                                    # Nom complet (ex: "Volleyball")
    name_short: str = ""                         # Nom court (ex: "Volley")
    emoji: str = "🏆"                            # Emoji du sport
    
    # Durées et timing
    duree_match_minutes: int = 90                # Durée d'un match
    duree_entre_matchs_minutes: int = 15         # Temps entre deux matchs
    temps_echauffement_minutes: int = 15         # Temps d'échauffement
    
    # Configuration par défaut
    niveaux: List[str] = field(default_factory=lambda: ["A1", "A2", "A3", "A4"])
    genres: List[str] = field(default_factory=lambda: ["M", "F"])
    types_championnat: List[str] = field(default_factory=lambda: ["Acad", "CFE", "CFU"])
    
    # Format des scores
    score_format: str = "points"                 # "sets" ou "points"
    score_separator: str = "-"
    
    # Couleurs UI
    color_primary: str = "#3B82F6"
    color_light: str = "rgba(59, 130, 246, 0.12)"
    color_dark: str = "#2563EB"
    
    # Paramètres additionnels spécifiques au sport
    extra: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SportConfig":
        """
        Crée une instance SportConfig à partir d'un dictionnaire.
        
        Args:
            data: Dictionnaire contenant les paramètres du sport
            
        Returns:
            Instance SportConfig
        """
        # Champs principaux
        config = cls(
            type=data.get("type", "unknown"),
            prefix=data.get("prefix", "XX"),
            name=data.get("name", "Unknown Sport"),
            name_short=data.get("name_short", data.get("name", "Unknown")[:6]),
            emoji=data.get("emoji", "🏆"),
            duree_match_minutes=data.get("duree_match_minutes", 90),
            duree_entre_matchs_minutes=data.get("duree_entre_matchs_minutes", 15),
            temps_echauffement_minutes=data.get("temps_echauffement_minutes", 15),
            niveaux=data.get("niveaux", ["A1", "A2", "A3", "A4"]),
            genres=data.get("genres", ["M", "F"]),
            types_championnat=data.get("types_championnat", ["Acad", "CFE", "CFU"]),
            score_format=data.get("score_format", "points"),
            score_separator=data.get("score_separator", "-"),
            color_primary=data.get("color_primary", "#3B82F6"),
            color_light=data.get("color_light", "rgba(59, 130, 246, 0.12)"),
            color_dark=data.get("color_dark", "#2563EB"),
        )
        
        # Stocker les paramètres additionnels non mappés
        known_keys = {
            "type", "prefix", "name", "name_short", "emoji",
            "duree_match_minutes", "duree_entre_matchs_minutes", 
            "temps_echauffement_minutes", "niveaux", "genres",
            "types_championnat", "score_format", "score_separator",
            "color_primary", "color_light", "color_dark"
        }
        config.extra = {k: v for k, v in data.items() if k not in known_keys}
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit la configuration en dictionnaire."""
        result = {
            "type": self.type,
            "prefix": self.prefix,
            "name": self.name,
            "name_short": self.name_short,
            "emoji": self.emoji,
            "duree_match_minutes": self.duree_match_minutes,
            "duree_entre_matchs_minutes": self.duree_entre_matchs_minutes,
            "temps_echauffement_minutes": self.temps_echauffement_minutes,
            "niveaux": self.niveaux,
            "genres": self.genres,
            "types_championnat": self.types_championnat,
            "score_format": self.score_format,
            "score_separator": self.score_separator,
            "color_primary": self.color_primary,
            "color_light": self.color_light,
            "color_dark": self.color_dark,
        }
        result.update(self.extra)
        return result


class SportPresetsManager:
    """
    Gestionnaire des présets de sport.
    
    Charge et fournit les configurations prédéfinies pour chaque sport.
    """
    
    _instance: Optional["SportPresetsManager"] = None
    _presets: Dict[str, SportConfig] = {}
    _aliases: Dict[str, str] = {}
    
    def __new__(cls):
        """Singleton pattern pour éviter de recharger les présets."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_presets()
        return cls._instance
    
    def _find_presets_file(self) -> Path:
        """Trouve le fichier sports_presets.yaml."""
        # Essayer plusieurs emplacements
        possible_paths = [
            Path(__file__).parent.parent.parent.parent / "configs" / "sports_presets.yaml",  # Depuis src/pycalendar/core
            Path(__file__).parent.parent.parent / "configs" / "sports_presets.yaml",
            Path(__file__).parent.parent / "configs" / "sports_presets.yaml",
            Path("configs") / "sports_presets.yaml",
        ]
        
        for path in possible_paths:
            if path.exists():
                return path.resolve()
        
        raise FileNotFoundError(
            f"Fichier sports_presets.yaml non trouvé. "
            f"Chemins essayés: {[str(p) for p in possible_paths]}"
        )
    
    def _load_presets(self):
        """Charge les présets depuis le fichier YAML."""
        try:
            presets_file = self._find_presets_file()
            
            with open(presets_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            # Charger les sports
            sports_data = data.get("sports", {})
            for sport_id, sport_config in sports_data.items():
                self._presets[sport_id] = SportConfig.from_dict(sport_config)
                # Ajouter aussi le préfixe comme alias
                prefix = sport_config.get("prefix", "").upper()
                if prefix:
                    self._aliases[prefix] = sport_id
            
            # Charger les alias supplémentaires
            aliases_data = data.get("aliases", {})
            for alias, sport_id in aliases_data.items():
                self._aliases[alias.lower()] = sport_id
                self._aliases[alias.upper()] = sport_id
            
            logger.info(f"Chargé {len(self._presets)} présets de sport depuis {presets_file}")
            
        except FileNotFoundError as e:
            logger.warning(f"Fichier de présets non trouvé: {e}")
            # Créer un préset par défaut (volleyball)
            self._presets["volleyball"] = SportConfig(
                type="volleyball",
                prefix="VB",
                name="Volleyball",
                name_short="Volley",
                emoji="🏐",
                duree_match_minutes=120,
            )
            self._aliases["VB"] = "volleyball"
            self._aliases["volley"] = "volleyball"
        except Exception as e:
            logger.error(f"Erreur lors du chargement des présets: {e}")
            raise
    
    def get_sport(self, sport_identifier: str) -> Optional[SportConfig]:
        """
        Récupère la configuration d'un sport.
        
        Args:
            sport_identifier: Identifiant du sport (type, prefix, ou alias)
            
        Returns:
            SportConfig ou None si non trouvé
        """
        # Essayer directement le type
        if sport_identifier in self._presets:
            return self._presets[sport_identifier]
        
        # Essayer les alias
        sport_id = self._aliases.get(sport_identifier.lower()) or self._aliases.get(sport_identifier.upper())
        if sport_id and sport_id in self._presets:
            return self._presets[sport_id]
        
        return None
    
    def get_sport_by_prefix(self, prefix: str) -> Optional[SportConfig]:
        """
        Récupère la configuration d'un sport par son préfixe.
        
        Args:
            prefix: Préfixe du sport (ex: "VB", "HB")
            
        Returns:
            SportConfig ou None si non trouvé
        """
        prefix_upper = prefix.upper()
        for sport in self._presets.values():
            if sport.prefix == prefix_upper:
                return sport
        return None
    
    def get_sport_by_pool_code(self, pool_code: str) -> Optional[SportConfig]:
        """
        Détecte le sport à partir d'un code de poule.
        
        Args:
            pool_code: Code de poule (ex: "VBFA1PA", "HBMA2PB")
            
        Returns:
            SportConfig ou None si non détecté
        """
        if not pool_code or len(pool_code) < 2:
            return None
        
        # Les 2 premiers caractères sont le préfixe du sport
        prefix = pool_code[:2].upper()
        return self.get_sport_by_prefix(prefix)
    
    def list_sports(self) -> List[SportConfig]:
        """Retourne la liste de tous les sports configurés."""
        return list(self._presets.values())
    
    def list_prefixes(self) -> List[str]:
        """Retourne la liste de tous les préfixes de sport."""
        return [sport.prefix for sport in self._presets.values()]
    
    @property
    def default_sport(self) -> SportConfig:
        """Retourne le sport par défaut (volleyball)."""
        return self.get_sport("volleyball") or list(self._presets.values())[0]


# Singleton global pour accès facile
def get_sport_presets() -> SportPresetsManager:
    """Retourne l'instance du gestionnaire de présets de sport."""
    return SportPresetsManager()


def get_sport_config(sport_identifier: str) -> Optional[SportConfig]:
    """
    Raccourci pour obtenir la configuration d'un sport.
    
    Args:
        sport_identifier: Identifiant du sport (type, prefix, ou alias)
        
    Returns:
        SportConfig ou None
    """
    return get_sport_presets().get_sport(sport_identifier)


def detect_sport_from_pool(pool_code: str) -> Optional[SportConfig]:
    """
    Détecte le sport à partir d'un code de poule.
    
    Args:
        pool_code: Code de poule (ex: "VBFA1PA")
        
    Returns:
        SportConfig ou None
    """
    return get_sport_presets().get_sport_by_pool_code(pool_code)
