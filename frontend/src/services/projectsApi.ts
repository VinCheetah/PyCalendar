/**
 * API client pour les projets PyCalendar.
 * 
 * Endpoints backend :
 * - GET    /projects                : Liste tous les projets
 * - POST   /projects                : Créer un nouveau projet
 * - GET    /projects/{id}           : Détails d'un projet
 * - PUT    /projects/{id}           : Mettre à jour un projet
 * - DELETE /projects/{id}           : Supprimer un projet (cascade: teams, venues, matches)
 * - GET    /projects/{id}/stats     : Statistiques d'un projet
 */

import api from './api'
import type { 
  Project, 
  ProjectCreate, 
  ProjectUpdate, 
  ProjectStats,
  ProjectQueryParams 
} from '@/types'

/**
 * Liste tous les projets.
 */
export async function getProjects(params?: ProjectQueryParams): Promise<Project[]> {
  const { data } = await api.get<Project[]>('/projects/', { params })
  return data
}

/**
 * Récupère un projet par ID.
 * 
 * Inclut config_data (YAML structure) si disponible.
 */
export async function getProject(id: number): Promise<Project> {
  const { data } = await api.get<Project>(`/projects/${id}`)
  return data
}

/**
 * Crée un nouveau projet.
 * 
 * Note : config_data peut être fourni directement (ConfigYamlData) ou null.
 * Les fichiers Excel/YAML seront traités par le backend si fournis.
 */
export async function createProject(project: ProjectCreate): Promise<Project> {
  const { data } = await api.post<Project>('/projects', project)
  return data
}

/**
 * Met à jour un projet existant.
 */
export async function updateProject(
  id: number, 
  updates: ProjectUpdate
): Promise<Project> {
  const { data } = await api.put<Project>(`/projects/${id}`, updates)
  return data
}

/**
 * Supprime un projet.
 * 
 * Suppression en cascade :
 * - Toutes les équipes du projet
 * - Tous les gymnases du projet
 * - Tous les matchs du projet
 */
export async function deleteProject(id: number): Promise<void> {
  await api.delete(`/projects/${id}`)
}

/**
 * Récupère les statistiques d'un projet.
 * 
 * Retourne :
 * - nb_matchs_total : Nombre total de matchs
 * - nb_matchs_planifies : Matchs avec semaine/horaire/gymnase
 * - nb_matchs_fixes : Matchs marqués comme fixes
 * - nb_matchs_a_planifier : Matchs sans planification
 * - taux_planification : Pourcentage de matchs planifiés
 */
export async function getProjectStats(id: number): Promise<ProjectStats> {
  const { data } = await api.get<ProjectStats>(`/projects/${id}/stats`)
  return data
}
