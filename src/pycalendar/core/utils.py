#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fonctions utilitaires pour PyCalendar.

Ce module fournit des fonctions génériques pour parser les codes de poule,
gérer les genres et manipuler les données d'équipe de manière compatible
avec tous les sports supportés.

Sports supportés (préfixes):
- VB: Volleyball
- HB: Handball
- BB: Basketball
- FB: Football
- FS: Futsal
- RG: Rugby
- BD: Badminton
- TT: Tennis de Table
"""

import re
from typing import Optional, List, Tuple, Dict

# Préfixes de sport connus (pour validation)
SPORT_PREFIXES = ["VB", "HB", "BB", "FB", "FS", "RG", "BD", "TT"]

# Pattern générique pour les codes de poule
# Format: {SPORT}{GENRE}{NIVEAU}{POULE}
# Exemples: VBFA1PA, HBMA2PB, BBMA3PC
POOL_CODE_PATTERN = re.compile(
    r'^([A-Z]{2})([FMX])([A-Z]?\d+)([P][A-Z])?$',
    re.IGNORECASE
)


def extraire_genre_depuis_poule(nom_poule: str) -> str:
    """
    Extrait le genre depuis le code de la poule.
    
    Fonctionne avec tous les sports supportés (VB, HB, BB, FB, FS, RG, BD, TT).
    
    Format attendu: {SPORT}{GENRE}{NIVEAU}{POULE}
    Exemples:
    - VBFA1PA -> 'F' (Volleyball Féminin A1 Poule A)
    - HBMA2PB -> 'M' (Handball Masculin A2 Poule B)
    - BBXA3PC -> 'X' (Basketball Mixte A3 Poule C)
    
    Args:
        nom_poule: Le nom de la poule (ex: "HBFA1PA", "VBMA2PB")
        
    Returns:
        'M' pour masculin, 'F' pour féminin, 'X' pour mixte,
        ou '' si le genre ne peut pas être déterminé
    """
    if not nom_poule:
        return ''
    
    nom_poule = nom_poule.strip().upper()
    
    # Pattern: 2 lettres sport + 1 lettre genre (F/M/X) + reste
    match = re.match(r'^[A-Z]{2}([FMX]).*$', nom_poule)
    
    if match:
        genre_letter = match.group(1)
        return genre_letter  # 'M', 'F', ou 'X'
    
    # Si le pattern ne correspond pas, retourner une chaîne vide
    return ''


def extraire_sport_depuis_poule(nom_poule: str) -> str:
    """
    Extrait le préfixe du sport depuis le code de la poule.
    
    Args:
        nom_poule: Le nom de la poule (ex: "VBFA1PA", "HBMA2PB")
        
    Returns:
        Préfixe du sport (ex: 'VB', 'HB') ou '' si non trouvé
    """
    if not nom_poule or len(nom_poule) < 2:
        return ''
    
    prefix = nom_poule[:2].upper()
    return prefix


def parser_code_poule(nom_poule: str) -> dict:
    """
    Parse le code complet de la poule et retourne ses composants.
    
    Fonctionne avec tous les sports supportés.
    
    Format: {SPORT}{GENRE}{NIVEAU}{POULE}
    Exemples:
    - VBFA1PA -> {'sport': 'VB', 'genre': 'F', 'niveau': 'A1', 'poule': 'PA'}
    - HBMA2PB -> {'sport': 'HB', 'genre': 'M', 'niveau': 'A2', 'poule': 'PB'}
    - BBMA3   -> {'sport': 'BB', 'genre': 'M', 'niveau': 'A3', 'poule': ''}
    
    Args:
        nom_poule: Le nom de la poule
        
    Returns:
        Dictionnaire avec les composants: sport, genre, niveau, poule
    """
    default_result = {'sport': '', 'genre': '', 'niveau': '', 'poule': ''}
    
    if not nom_poule:
        return default_result
    
    nom_poule = nom_poule.strip().upper()
    
    # Pattern complet avec groupe de poule optionnel
    match = POOL_CODE_PATTERN.match(nom_poule)
    
    if match:
        return {
            'sport': match.group(1).upper(),
            'genre': match.group(2).upper(),
            'niveau': match.group(3).upper(),
            'poule': (match.group(4) or '').upper()
        }
    
    # Pattern alternatif plus souple: 2 lettres + 1 lettre genre + reste
    match = re.match(r'^([A-Z]{2})([FMX])(.+)$', nom_poule)
    if match:
        sport = match.group(1)
        genre = match.group(2)
        reste = match.group(3)
        
        # Extraire niveau et poule du reste
        match_reste = re.match(r'^([A-Z]?\d+)([P][A-Z])?$', reste)
        if match_reste:
            niveau = match_reste.group(1)
            poule = match_reste.group(2) or ''
        else:
            niveau = reste
            poule = ''
        
        return {
            'sport': sport,
            'genre': genre,
            'niveau': niveau,
            'poule': poule
        }
    
    return default_result


def construire_code_poule(sport: str, genre: str, niveau: str, poule: str = "") -> str:
    """
    Construit un code de poule à partir de ses composants.
    
    Args:
        sport: Préfixe du sport (ex: 'VB', 'HB')
        genre: Genre ('M', 'F', 'X')
        niveau: Niveau (ex: 'A1', 'A2')
        poule: Identifiant de la poule (ex: 'PA', 'PB') - optionnel
        
    Returns:
        Code de poule (ex: 'VBFA1PA')
    """
    code = f"{sport.upper()}{genre.upper()}{niveau.upper()}"
    if poule:
        code += poule.upper()
    return code


def parser_nom_avec_genre(nom_avec_genre: str) -> tuple[str, str]:
    """
    Parse un nom d'équipe avec indicateur de genre optionnel.
    
    Format accepté: "NOM [M]" ou "NOM [F]" ou "NOM" (sans genre)
    Exemples:
    - "LYON 1 (1) [M]" -> ("LYON 1 (1)", "M")
    - "LYON 1 (1) [F]" -> ("LYON 1 (1)", "F")
    - "LYON 1 (1)" -> ("LYON 1 (1)", "")
    - "CENTRALE (2) [M]" -> ("CENTRALE (2)", "M")
    
    Args:
        nom_avec_genre: Nom de l'équipe potentiellement avec [M] ou [F]
        
    Returns:
        Tuple (nom_sans_genre, genre) où genre est 'M', 'F' ou '' si non spécifié
    """
    if not nom_avec_genre:
        return '', ''
    
    nom = nom_avec_genre.strip()
    
    # Pattern pour extraire [M] ou [F] en fin de chaîne
    match = re.match(r'^(.+?)\s*\[([MF])\]\s*$', nom)
    
    if match:
        nom_sans_genre = match.group(1).strip()
        genre = match.group(2)
        return nom_sans_genre, genre
    
    # Pas de genre spécifié
    return nom, ''


def formater_nom_avec_genre(nom: str, genre: str) -> str:
    """
    Formate un nom d'équipe avec son genre.
    
    Args:
        nom: Nom de l'équipe (ex: "LYON 1 (1)")
        genre: Genre 'M', 'F', ou '' (vide = pas de suffixe)
        
    Returns:
        Nom formaté avec genre si fourni
        - Si genre: "LYON 1 (1) [M]"
        - Si pas de genre: "LYON 1 (1)"
    """
    if not nom:
        return ''
    
    nom = nom.strip()
    
    if genre and genre in ['M', 'F']:
        return f"{nom} [{genre}]"
    
    return nom


def matcher_contrainte_avec_genre(eq1_nom: str, eq1_genre: str, 
                                   eq2_nom: str, eq2_genre: str,
                                   contrainte_key: tuple[str, str]) -> bool:
    """
    Vérifie si une paire d'équipes matche une clé de contrainte.
    
    La logique de matching:
    - Si la contrainte spécifie un genre (ex: "LYON 1 (1)|M"), elle ne s'applique 
      QU'aux équipes de ce genre
    - Si la contrainte ne spécifie PAS de genre (ex: "LYON 1 (1)|"), elle s'applique
      à TOUTES les équipes de ce nom, quel que soit leur genre
    
    Args:
        eq1_nom: Nom de la première équipe (ex: "LYON 1 (1)")
        eq1_genre: Genre de la première équipe ('M', 'F', ou '')
        eq2_nom: Nom de la seconde équipe
        eq2_genre: Genre de la seconde équipe
        contrainte_key: Tuple de clés de contrainte (format: "NOM|GENRE")
            Ex: ("LYON 1 (1)|M", "LYON 2 (1)|F") ou ("LYON 1 (1)|", "LYON 2 (1)|")
    
    Returns:
        True si la paire d'équipes matche la contrainte, False sinon
    
    Exemples:
        # Contrainte spécifique au genre
        >>> matcher_contrainte_avec_genre("LYON 1 (1)", "M", "LYON 2 (1)", "F",
        ...                               ("LYON 1 (1)|M", "LYON 2 (1)|F"))
        True
        
        # Contrainte générique (pas de genre)
        >>> matcher_contrainte_avec_genre("LYON 1 (1)", "M", "LYON 2 (1)", "F",
        ...                               ("LYON 1 (1)|", "LYON 2 (1)|"))
        True
        
        # Pas de match (genre différent)
        >>> matcher_contrainte_avec_genre("LYON 1 (1)", "F", "LYON 2 (1)", "F",
        ...                               ("LYON 1 (1)|M", "LYON 2 (1)|F"))
        False
    """
    # Construire les ids des équipes (format: "NOM|GENRE")
    eq1_id = f"{eq1_nom}|{eq1_genre}"
    eq2_id = f"{eq2_nom}|{eq2_genre}"
    
    # Créer la clé triée des équipes
    equipes_key = tuple(sorted([eq1_id, eq2_id]))
    
    # Match exact: les ids correspondent exactement
    if equipes_key == contrainte_key:
        return True
    
    # Match partiel: la contrainte n'a pas de genre spécifié
    # On extrait les noms sans genre des deux côtés et on compare
    contrainte_noms = tuple(sorted([k.split('|')[0] for k in contrainte_key]))
    equipes_noms = tuple(sorted([eq1_nom, eq2_nom]))
    
    if contrainte_noms != equipes_noms:
        return False
    
    # Les noms matchent, vérifier si la contrainte autorise n'importe quel genre
    contrainte_genres = [k.split('|')[1] for k in contrainte_key]
    
    # Si la contrainte n'a pas de genre spécifié (genre vide), elle s'applique à tous
    if all(genre == '' for genre in contrainte_genres):
        return True
    
    # Sinon, pas de match
    return False


def get_nom_genre_complet(genre_code: str) -> str:
    """
    Convertit le code genre en nom complet.
    
    Args:
        genre_code: 'M', 'F', ou ''
        
    Returns:
        'Masculin', 'Féminin', ou ''
    """
    mapping = {
        'M': 'Masculin',
        'F': 'Féminin'
    }
    return mapping.get(genre_code.upper(), '')


def extraire_niveau_depuis_poule(poule: str) -> str:
    """
    Extrait le niveau (ex: 'A1', 'A2') depuis le nom de la poule.
    
    Format attendu: (sport)(genre)(niveau)(poule)
    Exemples:
    - VBFA1PA -> 'A1'
    - HBMA2PB -> 'A2'
    - VBFA3PC -> 'A3'
    - VBMA4PA -> 'A4'
    
    Args:
        poule: Le nom de la poule (ex: "VBFA1PA", "HBMA2PB")
        
    Returns:
        Niveau au format chaîne ('A1', 'A2', etc.) ou '' si non trouvé
    """
    if not poule:
        return ''
    
    poule = poule.strip().upper()
    
    # Pattern pour extraire le niveau: cherche A suivi d'un chiffre
    match = re.search(r'(A\d+)', poule)
    
    if match:
        return match.group(1)
    
    return ''


def extraire_niveau_match(poule: str) -> Optional[int]:
    """
    Extrait le niveau du match depuis le nom de la poule.
    
    Format attendu: (sport)(genre)(niveau)(poule)
    Exemples:
    - VBFA1PA -> niveau 1 (A1 = niveau 1)
    - HBMA2PB -> niveau 2 (A2 = niveau 2)
    - VBFA3PC -> niveau 3 (A3 = niveau 3)
    - VBMA4PA -> niveau 4 (A4 = niveau 4)
    
    Args:
        poule: Le nom de la poule (ex: "VBFA1PA", "HBMA2PB")
        
    Returns:
        Niveau du match (1, 2, 3, 4, etc.) ou None si non trouvé
    """
    if not poule:
        return None
    
    poule = poule.strip().upper()
    
    # Pattern pour extraire le niveau: cherche A suivi d'un chiffre
    match = re.search(r'A(\d+)', poule)
    
    if match:
        try:
            niveau = int(match.group(1))
            return niveau
        except ValueError:
            return None
    
    return None


def determiner_genre_match(equipe1_genre: str, equipe2_genre: str, poule: str = "") -> str:
    """
    Détermine le genre d'un match basé sur les genres des équipes et éventuellement la poule.
    
    Logique:
    1. Si les deux équipes ont le même genre explicite (M ou F), utiliser ce genre
    2. Si une seule équipe a un genre explicite, utiliser ce genre
    3. Si aucune équipe n'a de genre mais la poule en contient un, extraire depuis la poule
    4. Sinon, retourner 'X' (genre indéterminé/mixte)
    
    Args:
        equipe1_genre: Genre de la première équipe ('M', 'F', ou '')
        equipe2_genre: Genre de la deuxième équipe ('M', 'F', ou '')
        poule: Nom de la poule (optionnel, utilisé comme fallback)
        
    Returns:
        'M' (masculin), 'F' (féminin), ou 'X' (indéterminé/mixte)
        
    Examples:
        >>> determiner_genre_match('M', 'M', '')
        'M'
        >>> determiner_genre_match('F', 'F', '')
        'F'
        >>> determiner_genre_match('M', '', '')
        'M'
        >>> determiner_genre_match('', '', 'VBFA1PA')
        'F'
        >>> determiner_genre_match('', '', '')
        'X'
        >>> determiner_genre_match('M', 'F', '')  # Cas d'erreur - genres différents
        'X'
    """
    # Normaliser les genres en majuscules
    g1 = equipe1_genre.upper().strip() if equipe1_genre else ""
    g2 = equipe2_genre.upper().strip() if equipe2_genre else ""
    
    # Valider les genres
    g1 = g1 if g1 in ['M', 'F'] else ""
    g2 = g2 if g2 in ['M', 'F'] else ""
    
    # Cas 1: Les deux équipes ont le même genre explicite
    if g1 and g2:
        if g1 == g2:
            return g1
        else:
            # Genres différents - match mixte ou erreur de données
            return 'X'
    
    # Cas 2: Une seule équipe a un genre explicite
    if g1:
        return g1
    if g2:
        return g2
    
    # Cas 3: Aucun genre explicite, essayer d'extraire depuis la poule
    if poule:
        genre_poule = extraire_genre_depuis_poule(poule)
        if genre_poule in ['M', 'F']:
            return genre_poule
    
    # Cas 4: Impossible de déterminer le genre
    return 'X'
