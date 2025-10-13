/**
 * Hooks React Query pour les projets PyCalendar.
 * 
 * Gère les opérations CRUD sur les projets et leurs statistiques.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as projectsApi from '@/services/projectsApi'
import type { Project, ProjectCreate, ProjectUpdate, ProjectStats, ProjectQueryParams } from '@/types'

// ============================================
// Query Keys
// ============================================

/**
 * Clés hiérarchiques pour les queries projets.
 * Structure : ['projects'] -> ['projects', 'list'] -> ['projects', 'detail', id]
 */
export const projectKeys = {
  all: ['projects'] as const,
  lists: () => [...projectKeys.all, 'list'] as const,
  list: (filters?: ProjectQueryParams) => [...projectKeys.lists(), filters] as const,
  details: () => [...projectKeys.all, 'detail'] as const,
  detail: (id: number) => [...projectKeys.details(), id] as const,
  stats: (id: number) => [...projectKeys.all, 'stats', id] as const,
}

// ============================================
// Queries (GET)
// ============================================

/**
 * Hook pour lister tous les projets.
 * 
 * Usage :
 *   const { data: projects, isLoading, error } = useProjects()
 *   const { data: projects } = useProjects({ actif: true })
 */
export function useProjects(params?: ProjectQueryParams) {
  return useQuery({
    queryKey: projectKeys.list(params),
    queryFn: () => projectsApi.getProjects(params),
  })
}

/**
 * Hook pour récupérer un projet par ID.
 * 
 * Retourne config_yaml_data et config_excel_data.
 * 
 * Usage :
 *   const { data: project, isLoading, error } = useProject(1)
 */
export function useProject(id: number) {
  return useQuery({
    queryKey: projectKeys.detail(id),
    queryFn: () => projectsApi.getProject(id),
    enabled: !!id, // Ne pas exécuter si id est 0 ou undefined
  })
}

/**
 * Hook pour récupérer les statistiques d'un projet.
 * 
 * Usage :
 *   const { data: stats } = useProjectStats(1)
 *   // stats.nb_matchs_total, stats.nb_matchs_planifies, stats.nb_matchs_fixes
 */
export function useProjectStats(id: number) {
  return useQuery({
    queryKey: projectKeys.stats(id),
    queryFn: () => projectsApi.getProjectStats(id),
    enabled: !!id,
  })
}

// ============================================
// Mutations (POST, PUT, DELETE)
// ============================================

/**
 * Hook pour créer un nouveau projet.
 * 
 * Usage :
 *   const createProject = useCreateProject()
 *   createProject.mutate({
 *     nom: "Nouveau Projet",
 *     sport: "Volleyball",
 *     config_yaml_data: {...},
 *     config_excel_data: {...}
 *   })
 */
export function useCreateProject() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: ProjectCreate) => projectsApi.createProject(data),
    onSuccess: () => {
      // Invalider liste des projets pour refetch
      queryClient.invalidateQueries({ queryKey: projectKeys.lists() })
    },
  })
}

/**
 * Hook pour mettre à jour un projet.
 * 
 * Usage :
 *   const updateProject = useUpdateProject()
 *   updateProject.mutate({ id: 1, updates: { nom: "Nouveau nom" } })
 */
export function useUpdateProject() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, updates }: { id: number; updates: ProjectUpdate }) =>
      projectsApi.updateProject(id, updates),
    onSuccess: (updatedProject) => {
      // Invalider détail du projet
      queryClient.invalidateQueries({ queryKey: projectKeys.detail(updatedProject.id) })
      // Invalider liste
      queryClient.invalidateQueries({ queryKey: projectKeys.lists() })
      // Invalider stats (pourraient avoir changé)
      queryClient.invalidateQueries({ queryKey: projectKeys.stats(updatedProject.id) })
    },
  })
}

/**
 * Hook pour supprimer un projet (cascade: équipes, gymnases, matchs).
 * 
 * Usage :
 *   const deleteProject = useDeleteProject()
 *   deleteProject.mutate(1)
 */
export function useDeleteProject() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => projectsApi.deleteProject(id),
    onSuccess: () => {
      // Invalider toutes les queries projets (cascade supprime tout)
      queryClient.invalidateQueries({ queryKey: projectKeys.all })
    },
  })
}
