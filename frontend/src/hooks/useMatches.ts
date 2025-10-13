/**
 * Hooks React Query pour les matchs PyCalendar.
 * 
 * Gère les opérations CRUD sur les matchs + opérations spéciales (move, fix, unfix).
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as matchesApi from '@/services/matchesApi'
import type { 
  Match,
  MatchCreate,
  MatchUpdate,
  MatchMovePayload,
  MatchQueryParams 
} from '@/types'

// ============================================
// Query Keys
// ============================================

/**
 * Clés hiérarchiques pour les queries matchs.
 * Inclut projectId et filtres dans la clé pour cache séparé.
 */
export const matchKeys = {
  all: ['matches'] as const,
  lists: () => [...matchKeys.all, 'list'] as const,
  list: (projectId: number, filters?: MatchQueryParams) => 
    [...matchKeys.lists(), projectId, filters] as const,
  details: () => [...matchKeys.all, 'detail'] as const,
  detail: (id: number) => [...matchKeys.details(), id] as const,
}

// ============================================
// Queries (GET)
// ============================================

/**
 * Hook pour lister les matchs d'un projet.
 * 
 * Filtres optionnels : semaine, poule, gymnase, est_fixe, statut
 * 
 * Usage :
 *   const { data: matches } = useMatches(1, { semaine: 3, poule: 'P1' })
 */
export function useMatches(projectId: number, params?: MatchQueryParams) {
  return useQuery({
    queryKey: matchKeys.list(projectId, params),
    queryFn: () => matchesApi.getMatches(projectId, params),
    enabled: !!projectId,
  })
}

/**
 * Hook pour récupérer un match par ID.
 * 
 * Usage :
 *   const { data: match } = useMatch(1)
 */
export function useMatch(id: number) {
  return useQuery({
    queryKey: matchKeys.detail(id),
    queryFn: () => matchesApi.getMatch(id),
    enabled: !!id,
  })
}

// ============================================
// Mutations (POST, PUT, DELETE)
// ============================================

/**
 * Hook pour créer un nouveau match.
 * 
 * Usage :
 *   const createMatch = useCreateMatch()
 *   createMatch.mutate({
 *     project_id: 1,
 *     equipe_domicile_id: 1,
 *     equipe_exterieur_id: 2,
 *     gymnase_id: 1,
 *     semaine: 3
 *   })
 */
export function useCreateMatch() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (data: MatchCreate) => matchesApi.createMatch(data),
    onSuccess: (newMatch) => {
      // Invalider listes de matchs du projet
      queryClient.invalidateQueries({ 
        queryKey: matchKeys.list(newMatch.project_id) 
      })
    },
  })
}

/**
 * Hook pour mettre à jour un match.
 * 
 * Usage :
 *   const updateMatch = useUpdateMatch()
 *   updateMatch.mutate({ id: 1, updates: { gymnase_id: 2 } })
 */
export function useUpdateMatch() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ id, updates }: { id: number; updates: MatchUpdate }) =>
      matchesApi.updateMatch(id, updates),
    onSuccess: (updatedMatch) => {
      // Invalider détail du match
      queryClient.invalidateQueries({ queryKey: matchKeys.detail(updatedMatch.id) })
      // Invalider listes du projet
      queryClient.invalidateQueries({ 
        queryKey: matchKeys.list(updatedMatch.project_id) 
      })
    },
  })
}

/**
 * Hook pour supprimer un match.
 * 
 * Usage :
 *   const deleteMatch = useDeleteMatch()
 *   deleteMatch.mutate({ id: 1, projectId: 1 })
 */
export function useDeleteMatch() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ id, projectId }: { id: number; projectId: number }) =>
      matchesApi.deleteMatch(id),
    onSuccess: (_, variables) => {
      // Invalider listes du projet
      queryClient.invalidateQueries({ 
        queryKey: matchKeys.list(variables.projectId) 
      })
    },
  })
}

/**
 * Hook pour déplacer un match vers une nouvelle semaine.
 * 
 * IMPORTANT : Validation backend (match non fixé, semaine >= semaine_min)
 * 
 * Usage :
 *   const moveMatch = useMoveMatch()
 *   moveMatch.mutate({ id: 1, payload: { nouvelle_semaine: 5 } })
 */
export function useMoveMatch() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: MatchMovePayload }) =>
      matchesApi.moveMatch(id, payload),
    onSuccess: (movedMatch) => {
      // Invalider détail
      queryClient.invalidateQueries({ queryKey: matchKeys.detail(movedMatch.id) })
      // Invalider listes du projet
      queryClient.invalidateQueries({ 
        queryKey: matchKeys.list(movedMatch.project_id) 
      })
    },
  })
}

/**
 * Hook pour fixer un match (non modifiable par solver).
 * 
 * Usage :
 *   const fixMatch = useFixMatch()
 *   fixMatch.mutate(1)
 */
export function useFixMatch() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (id: number) => matchesApi.fixMatch(id),
    onSuccess: (fixedMatch) => {
      queryClient.invalidateQueries({ queryKey: matchKeys.detail(fixedMatch.id) })
      queryClient.invalidateQueries({ 
        queryKey: matchKeys.list(fixedMatch.project_id) 
      })
    },
  })
}

/**
 * Hook pour défixer un match (modifiable par solver).
 * 
 * Usage :
 *   const unfixMatch = useUnfixMatch()
 *   unfixMatch.mutate(1)
 */
export function useUnfixMatch() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (id: number) => matchesApi.unfixMatch(id),
    onSuccess: (unfixedMatch) => {
      queryClient.invalidateQueries({ queryKey: matchKeys.detail(unfixedMatch.id) })
      queryClient.invalidateQueries({ 
        queryKey: matchKeys.list(unfixedMatch.project_id) 
      })
    },
  })
}
