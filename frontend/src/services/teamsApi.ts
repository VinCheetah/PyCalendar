/**
 * API client pour les équipes PyCalendar.
 * 
 * Endpoints backend :
 * - GET    /projects/{project_id}/teams     : Liste toutes les équipes d'un projet
 * - POST   /projects/{project_id}/teams     : Créer une nouvelle équipe
 * - GET    /teams/{id}                      : Détails d'une équipe
 * - PUT    /teams/{id}                      : Mettre à jour une équipe
 * - DELETE /teams/{id}                      : Supprimer une équipe
 */

import api from './api'
import type { 
  Team, 
  TeamCreate, 
  TeamUpdate, 
  TeamQueryParams 
} from '@/types'

/**
 * Liste toutes les équipes d'un projet.
 * 
 * Filtres optionnels :
 * - poule : Filtrer par poule (P1, P2, etc.)
 * - institution : Filtrer par institution (Lycée A, etc.)
 * - genre : Filtrer par genre (Garçons, Filles, Mixte)
 */
export async function getTeams(
  projectId: number, 
  params?: TeamQueryParams
): Promise<Team[]> {
  const { data } = await api.get<Team[]>(`/projects/${projectId}/teams`, { params })
  return data
}

/**
 * Récupère une équipe par ID.
 */
export async function getTeam(id: number): Promise<Team> {
  const { data } = await api.get<Team>(`/teams/${id}`)
  return data
}

/**
 * Crée une nouvelle équipe.
 * 
 * Note : Les équipes sont généralement créées automatiquement lors de l'import Excel.
 * La création manuelle est rare.
 */
export async function createTeam(team: TeamCreate): Promise<Team> {
  const { data } = await api.post<Team>(`/projects/${team.project_id}/teams`, team)
  return data
}

/**
 * Met à jour une équipe existante.
 * 
 * Permet de modifier :
 * - nom, institution, numero_equipe, genre, poule
 * - horaires_preferes : Liste d'horaires préférés ["14:00", "16:00"]
 * - lieux_preferes : Liste de gymnases préférés ["Gymnase A", "Gymnase B"]
 */
export async function updateTeam(
  id: number, 
  updates: TeamUpdate
): Promise<Team> {
  const { data } = await api.put<Team>(`/teams/${id}`, updates)
  return data
}

/**
 * Supprime une équipe.
 * 
 * Tous les matchs impliquant cette équipe seront également supprimés.
 */
export async function deleteTeam(id: number): Promise<void> {
  await api.delete(`/teams/${id}`)
}
