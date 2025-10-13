/**
 * Hooks React Query pour la résolution de projets (solver).
 * 
 * Gère l'appel au solver et l'invalidation du cache après résolution.
 */

import { useMutation, useQueryClient } from '@tanstack/react-query'
import * as solverApi from '@/services/solverApi'
import type { SolveResponse } from '@/services/solverApi'
import { matchKeys } from './useMatches'
import { projectKeys } from './useProjects'

// ============================================
// Mutations
// ============================================

/**
 * Hook pour résoudre (optimiser) un projet.
 * 
 * Fonctionnalités :
 * - Appelle POST /projects/{id}/solve avec stratégie
 * - Invalide automatiquement le cache des matchs après résolution
 * - Invalide le cache du projet pour mettre à jour les stats
 * 
 * Usage :
 * ```tsx
 * const solveProject = useSolveProject()
 * 
 * const handleSolve = async () => {
 *   try {
 *     const result = await solveProject.mutateAsync({
 *       projectId: 1,
 *       strategy: 'greedy'
 *     })
 *     console.log(`${result.nb_matchs_planifies} matchs planifiés`)
 *   } catch (error) {
 *     console.error('Erreur résolution:', error)
 *   }
 * }
 * ```
 */
export function useSolveProject() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ 
      projectId, 
      strategy 
    }: { 
      projectId: number
      strategy: 'cpsat' | 'greedy' 
    }): Promise<SolveResponse> => {
      return solverApi.solveProject(projectId, strategy)
    },

    onSuccess: (data) => {
      console.log(`✅ Résolution terminée: ${data.nb_matchs_planifies} matchs planifiés`)
      
      // Invalider toutes les queries de matchs pour refetch automatique
      // Cela va rafraîchir le calendrier avec les nouveaux matchs planifiés
      queryClient.invalidateQueries({ queryKey: matchKeys.lists() })
      
      // Invalider le projet pour mettre à jour les stats (nb_matchs_planifies, etc.)
      queryClient.invalidateQueries({ queryKey: projectKeys.detail(data.project_id) })
      
      // Invalider les stats du projet si elles existent
      queryClient.invalidateQueries({ 
        queryKey: [...projectKeys.all, 'stats', data.project_id] 
      })
    },

    onError: (error: any) => {
      // Extraire le message d'erreur détaillé du backend
      const errorMessage = error.response?.data?.detail || error.message || 'Erreur inconnue'
      console.error('❌ Erreur résolution:', errorMessage)
      console.error('Détails complets:', error)
    },
  })
}
