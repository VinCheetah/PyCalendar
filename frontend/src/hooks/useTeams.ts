/**
 * Hooks React Query pour les équipes PyCalendar.
 * 
 * Gère les opérations CRUD sur les équipes avec filtrage par poule/institution/genre.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as teamsApi from '@/services/teamsApi'
import type { Team, TeamCreate, TeamUpdate, TeamQueryParams } from '@/types'

// ============================================
// Query Keys
// ============================================

/**
 * Clés hiérarchiques pour les queries équipes.
 * Inclut projectId et filtres dans la clé pour cache séparé.
 */
export const teamKeys = {
  all: ['teams'] as const,
  lists: () => [...teamKeys.all, 'list'] as const,
  list: (projectId: number, params?: TeamQueryParams) => 
    [...teamKeys.lists(), projectId, params] as const,
  details: () => [...teamKeys.all, 'detail'] as const,
  detail: (id: number) => [...teamKeys.details(), id] as const,
}

// ============================================
// Queries (GET)
// ============================================

/**
 * Hook pour lister les équipes d'un projet.
 * 
 * Filtres : poule, institution, genre
 * 
 * Usage :
 *   const { data: teams } = useTeams(1, { poule: 'P1', genre: 'M' })
 */
export function useTeams(projectId: number, params?: TeamQueryParams) {
  return useQuery({
    queryKey: teamKeys.list(projectId, params),
    queryFn: () => teamsApi.getTeams(projectId, params),
    enabled: !!projectId,
  })
}

/**
 * Hook pour récupérer une équipe par ID.
 * 
 * Usage :
 *   const { data: team } = useTeam(1)
 */
export function useTeam(id: number) {
  return useQuery({
    queryKey: teamKeys.detail(id),
    queryFn: () => teamsApi.getTeam(id),
    enabled: !!id,
  })
}

// ============================================
// Mutations (POST, PUT, DELETE)
// ============================================

/**
 * Hook pour créer une équipe.
 * 
 * Usage :
 *   const createTeam = useCreateTeam()
 *   createTeam.mutate({
 *     project_id: 1,
 *     nom: "Équipe A",
 *     poule: "P1",
 *     institution: "Lycée X",
 *     genre: "M"
 *   })
 */
export function useCreateTeam() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (data: TeamCreate) => teamsApi.createTeam(data),
    onSuccess: (newTeam) => {
      queryClient.invalidateQueries({ 
        queryKey: teamKeys.list(newTeam.project_id) 
      })
    },
  })
}

/**
 * Hook pour mettre à jour une équipe.
 * 
 * Usage :
 *   const updateTeam = useUpdateTeam()
 *   updateTeam.mutate({ id: 1, updates: { nom: "Nouveau nom" } })
 */
export function useUpdateTeam() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ id, updates }: { id: number; updates: TeamUpdate }) =>
      teamsApi.updateTeam(id, updates),
    onSuccess: (updatedTeam) => {
      queryClient.invalidateQueries({ queryKey: teamKeys.detail(updatedTeam.id) })
      queryClient.invalidateQueries({ 
        queryKey: teamKeys.list(updatedTeam.project_id) 
      })
    },
  })
}

/**
 * Hook pour supprimer une équipe.
 * 
 * Supprime aussi tous les matchs impliquant cette équipe.
 * 
 * Usage :
 *   const deleteTeam = useDeleteTeam()
 *   deleteTeam.mutate({ id: 1, projectId: 1 })
 */
export function useDeleteTeam() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ id, projectId }: { id: number; projectId: number }) =>
      teamsApi.deleteTeam(id),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ 
        queryKey: teamKeys.list(variables.projectId) 
      })
      // Invalider aussi les matchs car équipe supprimée
      queryClient.invalidateQueries({ queryKey: ['matches'] })
    },
  })
}
