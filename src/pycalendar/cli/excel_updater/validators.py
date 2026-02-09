"""
Column and cell validators for Excel configuration.

Provides validation logic for different types of data columns.
"""

import re
import difflib
import pandas as pd
from datetime import datetime
from typing import Any, Dict, Optional, Set

from .reports import ValidationResult, Severity


class ColumnValidator:
    """Validateur de colonnes avec règles spécifiques par type."""
    
    @staticmethod
    def valider_semaine(valeur: Any, nb_semaines_max: int = 52,
                        semaines_valides: Optional[Set[int]] = None,
                        week_dates: Optional[Dict[int, datetime]] = None,
                        semaines_banalisees: Optional[Set[int]] = None) -> ValidationResult:
        """
        Valide une semaine (doit être un entier entre 1 et nb_semaines_max).
        
        Args:
            valeur: Valeur à valider - peut être "N" ou "N (dd/mm)"
            nb_semaines_max: Nombre maximum de semaines
            semaines_valides: Set de semaines valides (si None, accepte 1-nb_semaines_max)
            week_dates: Mapping {semaine: date} pour afficher les dates
            semaines_banalisees: Set des semaines banalisées (vacances, etc.)
        """
        if pd.isna(valeur) or str(valeur).strip() == '':
            return ValidationResult.error("Semaine vide")
        
        valeur_str = str(valeur).strip()
        
        # Extraire le numéro de semaine - peut être "N" ou "N (dd/mm)"
        # Regex pour capturer le numéro avant tout espace ou parenthèse
        import re
        match = re.match(r'^(\d+)', valeur_str)
        if not match:
            return ValidationResult.error(
                f"Format semaine invalide: '{valeur}' (attendu: entier ou 'N (dd/mm)')"
            )
        
        try:
            semaine = int(match.group(1))
            
            # Vérifier si c'est une semaine banalisée (message spécifique)
            if semaines_banalisees and semaine in semaines_banalisees:
                return ValidationResult.error(
                    f"Semaine {semaine} banalisée (vacances/période sans match)"
                )
            
            if semaines_valides is not None:
                if semaine not in semaines_valides:
                    # Déterminer si hors limites ou juste non valide
                    max_semaine = max(semaines_valides) if semaines_valides else nb_semaines_max
                    if semaine > max_semaine:
                        return ValidationResult.error(
                            f"Semaine {semaine} hors calendrier (max: {max_semaine})"
                        )
                    
                    # Afficher les semaines valides avec leurs dates
                    if week_dates:
                        valides_parts = []
                        for s in sorted(semaines_valides)[:8]:
                            if s in week_dates:
                                date_str = week_dates[s].strftime("%d/%m")
                                valides_parts.append(f"{s} ({date_str})")
                            else:
                                valides_parts.append(str(s))
                        valides_str = ", ".join(valides_parts)
                    else:
                        valides_str = ", ".join(str(s) for s in sorted(semaines_valides)[:10])
                    if len(semaines_valides) > 8:
                        valides_str += "..."
                    return ValidationResult.error(
                        f"Semaine {semaine} non valide (semaines actives: {valides_str})"
                    )
            elif not (1 <= semaine <= nb_semaines_max):
                return ValidationResult.error(
                    f"Semaine {semaine} hors limites (1-{nb_semaines_max})"
                )
            return ValidationResult.ok(semaine)
        except (ValueError, TypeError):
            return ValidationResult.error(
                f"Format semaine invalide: '{valeur}' (attendu: entier ou 'N (dd/mm)')"
            )
    
    @staticmethod
    def valider_capacite(valeur: Any, capacite_max: int = 100) -> ValidationResult:
        """Valide une capacité occupée (entier positif)."""
        if pd.isna(valeur) or str(valeur).strip() == '':
            return ValidationResult.ok()  # Capacité optionnelle
        
        try:
            capacite = int(float(valeur))
            if capacite < 0:
                return ValidationResult.error(
                    f"Capacité occupée négative: {capacite}",
                    suggestion=0,
                    auto_correctable=True
                )
            elif capacite > capacite_max:
                return ValidationResult.warning(
                    f"Capacité occupée ({capacite}) > capacité max probable ({capacite_max})"
                )
            return ValidationResult.ok(capacite)
        except (ValueError, TypeError):
            return ValidationResult.error(
                f"Format capacité invalide: '{valeur}' (attendu: entier positif)"
            )
    
    @staticmethod
    def valider_horaire(valeur: Any) -> ValidationResult:
        """Valide un horaire (format HH:MM, HH:MM:SS, ou HHhMM)."""
        if pd.isna(valeur) or str(valeur).strip() == '':
            return ValidationResult.ok()  # Horaire optionnel
        
        valeur_str = str(valeur).strip()
        
        # Formats acceptés
        patterns = [
            (r'^(\d{1,2}):(\d{2})(?::\d{2})?$', lambda m: f"{int(m.group(1)):02d}:{m.group(2)}"),
            (r'^(\d{1,2})[hH](\d{2})?$', lambda m: f"{int(m.group(1)):02d}:{m.group(2) or '00'}"),
        ]
        
        for pattern, formatter in patterns:
            match = re.match(pattern, valeur_str)
            if match:
                horaire_formate = formatter(match)
                heures, minutes = map(int, horaire_formate.split(':'))
                if 0 <= heures < 24 and 0 <= minutes < 60:
                    if horaire_formate != valeur_str:
                        return ValidationResult.warning(
                            f"Horaire reformaté",
                            suggestion=horaire_formate,
                            auto_correctable=True
                        )
                    return ValidationResult.ok(horaire_formate)
        
        return ValidationResult.error(
            f"Format horaire invalide: '{valeur}' (attendu: HH:MM ou HHhMM)"
        )
    
    @staticmethod
    def valider_date(valeur: Any, format_attendu: str = "%d/%m/%y") -> ValidationResult:
        """Valide une date et la normalise au format attendu."""
        if pd.isna(valeur) or str(valeur).strip() == '':
            return ValidationResult.ok()  # Date optionnelle
        
        from pycalendar.core.constants import parse_user_date, format_user_date
        
        valeur_str = str(valeur).strip()
        
        try:
            # Essayer de parser avec pandas (plus tolérant)
            parsed = pd.to_datetime(valeur_str, dayfirst=True)
            date_formatted = format_user_date(parsed.to_pydatetime())
            
            if date_formatted != valeur_str:
                return ValidationResult.warning(
                    f"Date reformatée",
                    suggestion=date_formatted,
                    auto_correctable=True
                )
            return ValidationResult.ok(date_formatted)
        except Exception:
            return ValidationResult.error(
                f"Format date invalide: '{valeur}' (attendu: DD/MM/YY)"
            )
    
    @staticmethod
    def valider_institution(valeur: Any, institutions_valides: Set[str]) -> ValidationResult:
        """Valide une institution (doit exister dans la liste)."""
        if pd.isna(valeur) or str(valeur).strip() == '':
            return ValidationResult.error("Institution vide")
        
        valeur_str = str(valeur).strip()
        
        if valeur_str in institutions_valides:
            return ValidationResult.ok(valeur_str)
        
        # Recherche floue
        matches = difflib.get_close_matches(valeur_str, institutions_valides, n=1, cutoff=0.6)
        if matches:
            return ValidationResult.error(
                f"Institution '{valeur_str}' non trouvée. Vouliez-vous dire '{matches[0]}'?",
                suggestion=matches[0],
                auto_correctable=True
            )
        
        return ValidationResult.error(f"Institution '{valeur_str}' inconnue")
    
    @staticmethod
    def valider_gymnase(valeur: Any, gymnases_valides: Set[str]) -> ValidationResult:
        """Valide un gymnase (doit exister dans la liste)."""
        if pd.isna(valeur) or str(valeur).strip() == '':
            return ValidationResult.error("Gymnase vide")
        
        valeur_str = str(valeur).strip()
        
        # Cas spécial: ENTENTE est toujours valide
        if valeur_str.upper() == 'ENTENTE':
            return ValidationResult.ok('ENTENTE')
        
        if valeur_str in gymnases_valides:
            return ValidationResult.ok(valeur_str)
        
        # Recherche floue
        matches = difflib.get_close_matches(valeur_str, gymnases_valides, n=1, cutoff=0.6)
        if matches:
            return ValidationResult.error(
                f"Gymnase '{valeur_str}' non trouvé. Vouliez-vous dire '{matches[0]}'?",
                suggestion=matches[0],
                auto_correctable=True
            )
        
        return ValidationResult.error(f"Gymnase '{valeur_str}' inconnu")
    
    @staticmethod
    def valider_equipe(valeur: Any, equipes_valides: Set[str]) -> ValidationResult:
        """
        Valide une équipe.
        
        Formats acceptés:
        - 'Institution (numéro)' : ex: "LYON 1 (1)"
        - 'Institution (numéro) [M]' : ex: "LYON 1 (1) [M]"
        - 'Institution (numéro) [F]' : ex: "LYON 1 (1) [F]"
        """
        if pd.isna(valeur) or str(valeur).strip() == '':
            return ValidationResult.error("Équipe vide")
        
        valeur_str = str(valeur).strip()
        
        # Vérifier format
        if not re.match(r'^.+\s*\(\d+\)\s*(\s*\[(M|F)\])?\s*$', valeur_str):
            return ValidationResult.warning(
                f"Format équipe invalide: '{valeur_str}' (attendu: 'Institution (numéro)' ou 'Institution (numéro) [M/F]')"
            )
        
        if valeur_str in equipes_valides:
            return ValidationResult.ok(valeur_str)
        
        # Recherche floue
        matches = difflib.get_close_matches(valeur_str, equipes_valides, n=1, cutoff=0.7)
        if matches:
            return ValidationResult.error(
                f"Équipe '{valeur_str}' non trouvée. Vouliez-vous dire '{matches[0]}'?",
                suggestion=matches[0],
                auto_correctable=True
            )
        
        return ValidationResult.error(f"Équipe '{valeur_str}' non trouvée dans la liste")
    
    @staticmethod
    def valider_genre(valeur: Any, obligatoire: bool = True) -> ValidationResult:
        """Valide un genre (M ou F)."""
        if pd.isna(valeur) or str(valeur).strip() == '':
            if obligatoire:
                return ValidationResult.error("Genre manquant (doit être 'M' ou 'F')")
            return ValidationResult.ok()
        
        valeur_str = str(valeur).strip().upper()
        
        if valeur_str in ('M', 'F'):
            # Auto-correct casing
            if valeur_str != str(valeur).strip():
                return ValidationResult.warning(
                    "Genre normalisé en majuscule",
                    suggestion=valeur_str,
                    auto_correctable=True
                )
            return ValidationResult.ok(valeur_str)
        
        # Accept H for Hommes
        if valeur_str == 'H':
            return ValidationResult.warning(
                "'H' converti en 'M' (Masculin)",
                suggestion='M',
                auto_correctable=True
            )
        
        return ValidationResult.error(
            f"Genre invalide: '{valeur}' (doit être 'M' ou 'F')"
        )
    
    @staticmethod
    def valider_niveau(valeur: Any) -> ValidationResult:
        """Valide un niveau de gymnase (Haut niveau ou Bas niveau)."""
        if pd.isna(valeur) or str(valeur).strip() == '':
            return ValidationResult.ok()  # Optionnel
        
        valeur_str = str(valeur).strip().lower()
        
        if 'haut' in valeur_str:
            correction = "Haut niveau"
        elif 'bas' in valeur_str:
            correction = "Bas niveau"
        else:
            return ValidationResult.error(
                "Niveau invalide: saisir 'Haut niveau' ou 'Bas niveau'"
            )
        
        if correction.lower() != valeur_str:
            return ValidationResult.warning(
                "Niveau normalisé",
                suggestion=correction,
                auto_correctable=True
            )
        return ValidationResult.ok(correction)
    
    @staticmethod
    def valider_niveau_equipe(valeur: Any, obligatoire: bool = False) -> ValidationResult:
        """
        Valide un niveau d'équipe (A1, A2, A3, A4, etc.).
        
        Args:
            valeur: Valeur à valider
            obligatoire: Si True, une valeur vide est une erreur
            
        Returns:
            ValidationResult
        """
        if pd.isna(valeur) or str(valeur).strip() == '':
            if obligatoire:
                return ValidationResult.error("Niveau d'équipe obligatoire")
            return ValidationResult.ok()  # Optionnel par défaut
        
        valeur_str = str(valeur).strip().upper()
        
        # Patterns acceptés: A1, A2, A3, A4, etc.
        niveaux_valides = {'A1', 'A2', 'A3', 'A4'}
        
        if valeur_str in niveaux_valides:
            # Auto-correct casing
            if valeur_str != str(valeur).strip():
                return ValidationResult.warning(
                    "Niveau normalisé en majuscule",
                    suggestion=valeur_str,
                    auto_correctable=True
                )
            return ValidationResult.ok(valeur_str)
        
        # Essayer de corriger les formats proches
        for niveau in niveaux_valides:
            if niveau.lower() == valeur_str.lower():
                return ValidationResult.warning(
                    f"Niveau normalisé",
                    suggestion=niveau,
                    auto_correctable=True
                )
        
        # Essayer de parser un format comme "1", "2" -> "A1", "A2"
        if valeur_str.isdigit() and 1 <= int(valeur_str) <= 4:
            suggestion = f"A{valeur_str}"
            return ValidationResult.warning(
                f"Niveau converti de '{valeur}' à '{suggestion}'",
                suggestion=suggestion,
                auto_correctable=True
            )
        
        return ValidationResult.error(
            f"Niveau invalide: '{valeur}' (valeurs acceptées: A1, A2, A3, A4)"
        )
    
    @staticmethod
    def valider_genre_equipe(valeur: Any, obligatoire: bool = False) -> ValidationResult:
        """
        Valide un genre d'équipe (M, F ou X pour mixte).
        
        Args:
            valeur: Valeur à valider
            obligatoire: Si True, une valeur vide est une erreur
            
        Returns:
            ValidationResult
        """
        if pd.isna(valeur) or str(valeur).strip() == '':
            if obligatoire:
                return ValidationResult.error("Genre d'équipe obligatoire")
            return ValidationResult.ok()  # Optionnel par défaut
        
        valeur_str = str(valeur).strip().upper()
        
        # Genres valides: M (Masculin), F (Féminin), X (Mixte)
        genres_valides = {'M', 'F', 'X'}
        
        if valeur_str in genres_valides:
            # Auto-correct casing
            if valeur_str != str(valeur).strip():
                return ValidationResult.warning(
                    "Genre normalisé en majuscule",
                    suggestion=valeur_str,
                    auto_correctable=True
                )
            return ValidationResult.ok(valeur_str)
        
        # Accept 'H' for Hommes -> M
        if valeur_str == 'H':
            return ValidationResult.warning(
                "'H' converti en 'M' (Masculin)",
                suggestion='M',
                auto_correctable=True
            )
        
        # Accept common variations
        if valeur_str in ('MASCULIN', 'MASC', 'HOMME', 'HOMMES', 'GARCON', 'GARÇON', 'GARCONS', 'GARÇONS'):
            return ValidationResult.warning(
                f"'{valeur}' converti en 'M' (Masculin)",
                suggestion='M',
                auto_correctable=True
            )
        
        if valeur_str in ('FEMININ', 'FÉMININ', 'FEM', 'FEMME', 'FEMMES', 'FILLE', 'FILLES', 'DAMES'):
            return ValidationResult.warning(
                f"'{valeur}' converti en 'F' (Féminin)",
                suggestion='F',
                auto_correctable=True
            )
        
        if valeur_str in ('MIXTE', 'MIX', 'MIXED'):
            return ValidationResult.warning(
                f"'{valeur}' converti en 'X' (Mixte)",
                suggestion='X',
                auto_correctable=True
            )
        
        return ValidationResult.error(
            f"Genre invalide: '{valeur}' (valeurs acceptées: M, F, X)"
        )
    
    @staticmethod
    def valider_type_contrainte(valeur: Any) -> ValidationResult:
        """Valide un type de contrainte temporelle (Avant ou Apres)."""
        if pd.isna(valeur) or str(valeur).strip() == '':
            return ValidationResult.error("Type de contrainte obligatoire")
        
        valeur_str = str(valeur).strip()
        
        # Normalisation
        valeur_lower = valeur_str.lower()
        if valeur_lower in ('avant', 'before'):
            correction = 'Avant'
        elif valeur_lower in ('apres', 'après', 'after'):
            correction = 'Apres'
        else:
            return ValidationResult.error(
                f"Type invalide: '{valeur}' (doit être 'Avant' ou 'Apres')"
            )
        
        if correction != valeur_str:
            return ValidationResult.warning(
                "Type normalisé",
                suggestion=correction,
                auto_correctable=True
            )
        return ValidationResult.ok(correction)
    
    @staticmethod
    def valider_type_championnat(valeur: Any) -> ValidationResult:
        """Valide un type de championnat (CFE, CFU, Acad, Autre)."""
        if pd.isna(valeur) or str(valeur).strip() == '':
            return ValidationResult.ok()  # Optionnel (défaut = Acad)
        
        valeur_str = str(valeur).strip()
        types_valides = {'CFE', 'CFU', 'Acad', 'Autre'}
        
        if valeur_str in types_valides:
            return ValidationResult.ok(valeur_str)
        
        # Tentative de correction de casse
        for t in types_valides:
            if valeur_str.lower() == t.lower():
                return ValidationResult.warning(
                    f"Type normalisé",
                    suggestion=t,
                    auto_correctable=True
                )
        
        return ValidationResult.error(
            f"Type '{valeur_str}' invalide. Valeurs acceptées: {', '.join(sorted(types_valides))}"
        )
    
    @staticmethod
    def valider_type_poule(valeur: Any) -> ValidationResult:
        """Valide un type de poule (Classique ou Aller-Retour)."""
        if pd.isna(valeur) or str(valeur).strip() == '':
            return ValidationResult.error("Type de poule obligatoire")
        
        valeur_str = str(valeur).strip()
        types_valides = {'Classique', 'Aller-Retour'}
        
        if valeur_str in types_valides:
            return ValidationResult.ok(valeur_str)
        
        # Fuzzy matching
        valeur_lower = valeur_str.lower()
        if 'classique' in valeur_lower or 'simple' in valeur_lower:
            return ValidationResult.warning(
                "Type normalisé",
                suggestion='Classique',
                auto_correctable=True
            )
        elif 'retour' in valeur_lower or 'double' in valeur_lower:
            return ValidationResult.warning(
                "Type normalisé",
                suggestion='Aller-Retour',
                auto_correctable=True
            )
        
        return ValidationResult.error(
            f"Type '{valeur_str}' invalide. Valeurs acceptées: Classique, Aller-Retour"
        )
    
    @staticmethod
    def valider_score(valeur: Any) -> ValidationResult:
        """Valide un score de match."""
        if pd.isna(valeur) or str(valeur).strip() == '':
            return ValidationResult.ok()  # Optionnel
        
        valeur_str = str(valeur).strip()
        
        # Patterns de score valides
        # "3-1", "25-23", "3-0 (25-20, 25-18, 25-15)", etc.
        if re.search(r'\d+\s*[-–]\s*\d+', valeur_str):
            return ValidationResult.ok(valeur_str)
        
        return ValidationResult.warning(
            f"Format de score potentiellement invalide: '{valeur_str}'. "
            f"Exemples: '3-1', '25-23', '3-0 (25-20, 25-18, 25-15)'"
        )
    
    @staticmethod
    def valider_texte_libre(valeur: Any) -> ValidationResult:
        """Valide un texte libre (remarques, notes, etc.)."""
        return ValidationResult.ok()  # Toujours valide
