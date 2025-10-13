/**
 * API client pour les matchs PyCalendar.
 * 
 * Endpoints backend :
 * - GET    /projects/{project_id}/matches     : Liste tous les matchs d'un projet
 * - POST   /projects/{project_id}/matches     : Créer un nouveau match
 * - GET    /matches/{id}                      : Détails d'un match
 * - PUT    /matches/{id}                      : Mettre à jour un match
 * - DELETE /matches/{id}                      : Supprimer un match
 * - POST   /matches/{id}/move                 : Déplacer un match vers une nouvelle semaine
 * - POST   /matches/{id}/fix                  : Fixer un match (non modifiable par solver)
 * - POST   /matches/{id}/unfix                : Défixer un match (modifiable par solver)
 */

import api from './api'
import type { 
  Match, 
  MatchCreate, 
  MatchUpdate, 
  MatchMovePayload,
  MatchQueryParams 
} from '@/types'

/**
 * Liste tous les matchs d'un projet.
 * 
 * Filtres optionnels :
 * - semaine : Matchs d'une semaine spécifique
 * - poule : Matchs d'une poule spécifique
 * - gymnase : Matchs dans un gymnase spécifique
 * - est_fixe : Matchs fixes ou non
 * - statut : Statut du match (a_planifier, planifie, fixe, termine, annule)
 */
export async function getMatches(
  projectId: number, 
  params?: MatchQueryParams
): Promise<Match[]> {
  const { data } = await api.get<Match[]>(`/matches/`, { 
    params: { ...params, project_id: projectId } 
  })
  return data
}

/**
 * Récupère un match par ID.
 */
export async function getMatch(id: number): Promise<Match> {
  const { data } = await api.get<Match>(`/matches/${id}/`)
  return data
}

/**
 * Crée un nouveau match.
 * 
 * Note : Les matchs sont généralement créés automatiquement par MultiPoolGenerator.
 * La création manuelle est rare.
 */
export async function createMatch(match: MatchCreate): Promise<Match> {
  const { data } = await api.post<Match>(`/projects/${match.project_id}/matches`, match)
  return data
}

/**
 * Met à jour un match existant.
 * 
 * Permet de modifier :
 * - semaine, horaire, gymnase
 * - est_fixe : Marquer comme fixe/non fixe
 * - statut : Changer le statut
 * - score_equipe1, score_equipe2 : Enregistrer les scores
 * - notes : Ajouter des notes
 */
export async function updateMatch(
  id: number, 
  updates: MatchUpdate
): Promise<Match> {
  const { data } = await api.put<Match>(`/matches/${id}`, updates)
  return data
}

/**
 * Supprime un match.
 */
export async function deleteMatch(id: number): Promise<void> {
  await api.delete(`/matches/${id}`)
}

/**
 * Déplace un match vers une nouvelle semaine/horaire/gymnase.
 * 
 * Validation backend :
 * - Match non fixé (est_fixe = false)
 * - Semaine actuelle >= semaine_min du projet
 * 
 * @throws Error si le match n'est pas modifiable
 */
export async function moveMatch(
  id: number, 
  payload: MatchMovePayload
): Promise<Match> {
  const { data } = await api.post<Match>(`/matches/${id}/move`, payload)
  return data
}

/**
 * Fixe un match (le rend non modifiable par le solver).
 * 
 * Un match fixé :
 * - Ne peut plus être déplacé automatiquement par le solver
 * - Peut toujours être modifié manuellement via updateMatch
 * - Utile pour verrouiller les matchs confirmés
 */
export async function fixMatch(id: number): Promise<Match> {
  const { data } = await api.post<Match>(`/matches/${id}/fix`)
  return data
}

/**
 * Défixe un match (le rend modifiable par le solver).
 * 
 * Permet au solver de déplacer ce match lors de la replanification.
 */
export async function unfixMatch(id: number): Promise<Match> {
  const { data } = await api.post<Match>(`/matches/${id}/unfix`)
  return data
}
