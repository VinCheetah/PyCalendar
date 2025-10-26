"""Calendar management for sports scheduling.

This module handles the mapping between week numbers and actual dates,
including support for vacation weeks and custom scheduling rules.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field
import calendar as cal


@dataclass
class CalendarConfig:
    """Configuration for calendar management."""
    date_debut: str  # Format: "YYYY-MM-DD"
    jour_match: str = "Thursday"  # Jour des matchs
    semaines_banalisees: Optional[List[int]] = None  # Liste des numéros de semaines banalisées

    def __post_init__(self):
        if self.semaines_banalisees is None:
            self.semaines_banalisees = []


class CalendarManager:
    """Manages the mapping between week numbers and actual dates."""

    # Mapping des jours en français vers anglais
    JOURS_MAPPING = {
        "lundi": "Monday",
        "mardi": "Tuesday",
        "mercredi": "Wednesday",
        "jeudi": "Thursday",
        "vendredi": "Friday",
        "samedi": "Saturday",
        "dimanche": "Sunday"
    }

    def __init__(self, config: CalendarConfig):
        """
        Initialize calendar manager.

        Args:
            config: Calendar configuration
        """
        self.config = config
        self._date_debut = datetime.strptime(config.date_debut, "%Y-%m-%d")
        self._jour_match = config.jour_match
        self._semaines_banalisees = set(config.semaines_banalisees or [])

        # Calculer les dates des semaines
        self._semaine_to_date: Dict[int, datetime] = {}
        self._date_to_semaine: Dict[datetime, int] = {}
        self._build_calendar_mapping()

    def _build_calendar_mapping(self):
        """Construit le mapping semaine ↔ date."""
        current_date = self._date_debut
        
        # Si la date de début n'est pas le jour de match, trouver le prochain
        if current_date.strftime("%A") != self._jour_match:
            # Avancer jusqu'au prochain jour de match
            days_ahead = 0
            target_day = current_date
            while target_day.strftime("%A") != self._jour_match and days_ahead < 7:
                target_day = current_date + timedelta(days=days_ahead + 1)
                days_ahead += 1
            current_date = target_day
        
        # Construire le mapping pour les semaines suivantes
        semaine_num = 1
        while semaine_num <= 52:  # Maximum 52 semaines par année
            if semaine_num not in self._semaines_banalisees:
                self._semaine_to_date[semaine_num] = current_date
                self._date_to_semaine[current_date] = semaine_num
            
            # Passer à la semaine suivante (7 jours)
            current_date += timedelta(days=7)
            semaine_num += 1

    def semaine_to_date(self, semaine: int) -> Optional[datetime]:
        """
        Convertit un numéro de semaine en date.

        Args:
            semaine: Numéro de la semaine (1-52)

        Returns:
            Date du match pour cette semaine, ou None si semaine banalisée
        """
        return self._semaine_to_date.get(semaine)

    def date_to_semaine(self, date: datetime) -> Optional[int]:
        """
        Convertit une date en numéro de semaine.

        Args:
            date: Date à convertir

        Returns:
            Numéro de la semaine, ou None si pas de match cette semaine
        """
        return self._date_to_semaine.get(date)

    def est_semaine_banalisee(self, semaine: int) -> bool:
        """
        Vérifie si une semaine est banalisée.

        Args:
            semaine: Numéro de la semaine

        Returns:
            True si la semaine est banalisée
        """
        return semaine in self._semaines_banalisees

    def get_semaines_actives(self) -> List[int]:
        """
        Retourne la liste des semaines actives (non banalisées).

        Returns:
            Liste triée des numéros de semaines actives
        """
        return sorted(self._semaine_to_date.keys())

    def get_semaines_banalisees(self) -> List[int]:
        """
        Retourne la liste des semaines banalisées.

        Returns:
            Liste triée des numéros de semaines banalisées
        """
        return sorted(self._semaines_banalisees)

    def get_date_range(self) -> Tuple[datetime, datetime]:
        """
        Retourne la plage de dates couvertes par le calendrier.

        Returns:
            Tuple (date_min, date_max) des dates de match
        """
        dates = list(self._semaine_to_date.values())
        if not dates:
            return (self._date_debut, self._date_debut)

        return (min(dates), max(dates))

    def formater_semaine(self, semaine: int) -> str:
        """
        Formate l'affichage d'une semaine avec sa date.

        Args:
            semaine: Numéro de la semaine

        Returns:
            Chaîne formatée "Semaine X (JJ/MM)" ou "Semaine X (Banalisée)"
        """
        if self.est_semaine_banalisee(semaine):
            return f"Semaine {semaine} (Banalisée)"

        date = self.semaine_to_date(semaine)
        if date:
            return f"Semaine {semaine} ({date.strftime('%d/%m')})"

        return f"Semaine {semaine}"

    def get_semaines_dans_periode(self, date_debut: datetime, date_fin: datetime) -> List[int]:
        """
        Retourne les numéros de semaines actives dans une période donnée.

        Args:
            date_debut: Date de début de la période
            date_fin: Date de fin de la période

        Returns:
            Liste des numéros de semaines actives dans la période
        """
        semaines = []
        for semaine, date in self._semaine_to_date.items():
            if date_debut <= date <= date_fin:
                semaines.append(semaine)

        return sorted(semaines)

    @staticmethod
    def normaliser_jour_match(jour: str) -> str:
        """
        Normalise le nom du jour de match.

        Args:
            jour: Nom du jour (français ou anglais)

        Returns:
            Nom du jour en anglais
        """
        jour_lower = jour.lower().strip()

        # Si déjà en anglais
        jours_anglais = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        if jour_lower in jours_anglais:
            return jour_lower.capitalize()

        # Sinon, traduire depuis le français
        if jour_lower in CalendarManager.JOURS_MAPPING:
            return CalendarManager.JOURS_MAPPING[jour_lower]

        # Défaut : Thursday
        return "Thursday"