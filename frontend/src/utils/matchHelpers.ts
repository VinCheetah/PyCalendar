/**
 * Fonctions utilitaires pour manipuler les matchs.
 */

import type { Match, MatchExtended } from '@/types'

/**
 * Vérifie si un match est modifiable.
 * 
 * Un match est NON modifiable si :
 * - Il est fixé (est_fixe = true)
 * - Sa semaine est < semaine_min du projet
 * 
 * @param match Match à vérifier
 * @param semaineMin Semaine minimum du projet
 * @returns true si le match peut être modifié par le solver, false sinon
 */
export function isMatchModifiable(match: Match, semaineMin: number): boolean {
  // Match fixé = non modifiable
  if (match.est_fixe) {
    return false
  }
  
  // Match dans une semaine < semaine_min = non modifiable
  if (match.semaine !== null && match.semaine < semaineMin) {
    return false
  }
  
  return true
}

/**
 * Transforme un Match en MatchExtended avec informations calculées.
 * 
 * Ajoute :
 * - est_modifiable : calculé selon est_fixe et semaine_min
 * - titre : nom du match formaté (ex: "Lycée A - 1 vs Lycée B - 2")
 * - couleur : couleur pour affichage calendrier (basée sur poule)
 * 
 * @param match Match de base
 * @param semaineMin Semaine minimum du projet
 * @returns MatchExtended avec champs calculés
 */
export function toMatchExtended(match: Match, semaineMin: number): MatchExtended {
  // Générer titre du match
  const titre = `${match.equipe1_nom} vs ${match.equipe2_nom}`
  
  // Calculer si modifiable
  const est_modifiable = isMatchModifiable(match, semaineMin)
  
  // Générer couleur (par poule si disponible)
  const couleur = match.poule 
    ? getPouleColor(match.poule)
    : '#3b82f6'  // Bleu par défaut
  
  return {
    ...match,
    est_modifiable,
    titre,
    couleur,
  }
}

/**
 * Attribue une couleur à une poule pour affichage calendrier.
 * 
 * Couleurs distinctes pour faciliter la visualisation des poules.
 * 
 * @param poule Nom de la poule (ex: "P1", "P2", etc.)
 * @returns Code couleur hexadécimal
 */
export function getPouleColor(poule: string): string {
  const colors: Record<string, string> = {
    'P1': '#ef4444',  // Rouge (Tailwind red-500)
    'P2': '#3b82f6',  // Bleu (Tailwind blue-500)
    'P3': '#10b981',  // Vert (Tailwind green-500)
    'P4': '#f59e0b',  // Orange (Tailwind amber-500)
    'P5': '#8b5cf6',  // Violet (Tailwind violet-500)
    'P6': '#ec4899',  // Rose (Tailwind pink-500)
    'P7': '#06b6d4',  // Cyan (Tailwind cyan-500)
    'P8': '#14b8a6',  // Teal (Tailwind teal-500)
  }
  
  return colors[poule] || '#6b7280'  // Gris par défaut (Tailwind gray-500)
}

/**
 * Formate un horaire pour affichage.
 * 
 * @param horaire Horaire au format "HH:MM" ou null
 * @returns Horaire formaté ou "Non planifié"
 */
export function formatHoraire(horaire: string | null): string {
  if (!horaire) {
    return 'Non planifié'
  }
  return horaire
}

/**
 * Formate une semaine pour affichage.
 * 
 * @param semaine Numéro de semaine ou null
 * @returns Texte formaté (ex: "Semaine 3" ou "Non planifié")
 */
export function formatSemaine(semaine: number | null): string {
  if (semaine === null) {
    return 'Non planifié'
  }
  return `Semaine ${semaine}`
}
