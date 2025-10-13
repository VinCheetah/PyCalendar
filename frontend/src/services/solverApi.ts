/**
 * API client pour la résolution de projets (solver).
 * 
 * Endpoints backend :
 * - POST /projects/{id}/solve : Résoudre un projet avec une stratégie
 */

import api from './api'

/**
 * Interface pour la réponse de résolution.
 */
export interface SolveResponse {
  project_id: number
  strategy: string
  nb_matchs_total: number
  nb_matchs_fixes: number
  nb_matchs_planifies: number
  nb_matchs_updated: number
  execution_time: number
  solution_score?: number
  erreurs?: string[]
}

/**
 * Résout un projet avec la stratégie spécifiée.
 * 
 * @param projectId - ID du projet à résoudre
 * @param strategy - Stratégie de résolution ('cpsat' ou 'greedy')
 * @returns Résultat de la résolution avec métriques
 */
export async function solveProject(
  projectId: number,
  strategy: 'cpsat' | 'greedy' = 'greedy'
): Promise<SolveResponse> {
  const { data } = await api.post<SolveResponse>(
    `/projects/${projectId}/solve`,
    { strategy }
  )
  return data
}
