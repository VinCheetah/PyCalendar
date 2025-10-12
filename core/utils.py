#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fonctions utilitaires pour PyCalendar.
"""

import re
from typing import Optional


def extraire_genre_depuis_poule(nom_poule: str) -> str:
    """
    Extrait le genre depuis le code de la poule.
    
    Format attendu: (sport)(genre)(niveau)(poule)
    Exemples:
    - HBFA1PA -> 'F' (Handball Féminin Accession niveau 1 Poule A)
    - HBMA2PB -> 'M' (Handball Masculin Accession niveau 2 Poule B)
    - VBA3PA  -> 'A' (Volley Ball  mixte/Accession niveau 3 Poule A)
    
    Args:
        nom_poule: Le nom de la poule (ex: "HBFA1PA", "HBMA2PB")
        
    Returns:
        'M' pour masculin, 'F' pour féminin, ou '' si le genre ne peut pas être déterminé
    """
    if not nom_poule:
        return ''
    
    nom_poule = nom_poule.strip().upper()
    
    # Pattern pour extraire le code: (2 lettres sport)(1 lettre genre)(1-2 caractères niveau/type)(1-2 caractères poule)
    # Exemples: HB F A1PA, HB M A2PB, VB F 3PA
    match = re.match(r'^[A-Z]{2}([FM]).*$', nom_poule)
    
    if match:
        genre_letter = match.group(1)
        return genre_letter  # 'M' ou 'F'
    
    # Si le pattern ne correspond pas, retourner une chaîne vide
    return ''


def parser_code_poule(nom_poule: str) -> dict:
    """
    Parse le code complet de la poule et retourne ses composants.
    
    Format: (sport)(genre)(niveau/type)(poule)
    Exemples:
    - HBFA1PA -> {'sport': 'HB', 'genre': 'F', 'niveau': 'A1', 'poule': 'PA'}
    - HBMA2PB -> {'sport': 'HB', 'genre': 'M', 'niveau': 'A2', 'poule': 'PB'}
    
    Args:
        nom_poule: Le nom de la poule
        
    Returns:
        Dictionnaire avec les composants: sport, genre, niveau, poule
    """
    if not nom_poule:
        return {'sport': '', 'genre': '', 'niveau': '', 'poule': ''}
    
    nom_poule = nom_poule.strip().upper()
    
    # Pattern général: 2 lettres sport + 1 lettre genre + reste
    match = re.match(r'^([A-Z]{2})([FM])([A-Z0-9]+)$', nom_poule)
    
    if match:
        sport = match.group(1)
        genre = match.group(2)
        reste = match.group(3)
        
        # Extraire niveau et poule du reste
        # Généralement: A1PA -> niveau=A1, poule=PA
        match_reste = re.match(r'^([A-Z]?\d+)([P][A-Z])$', reste)
        if match_reste:
            niveau = match_reste.group(1)
            poule = match_reste.group(2)
        else:
            niveau = reste
            poule = ''
        
        return {
            'sport': sport,
            'genre': genre,
            'niveau': niveau,
            'poule': poule
        }
    
    # Si le pattern ne correspond pas, retourner des valeurs vides
    return {'sport': '', 'genre': '', 'niveau': '', 'poule': ''}


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
