/**
 * Hooks React Query pour les gymnases PyCalendar.
 * 
 * Gère les opérations CRUD sur les gymnases/lieux de rencontre.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as venuesApi from '@/services/venuesApi'
import type { Venue, VenueCreate, VenueUpdate, VenueQueryParams } from '@/types'

// ============================================
// Query Keys
// ============================================

/**
 * Clés hiérarchiques pour les queries gymnases.
 * Inclut projectId et filtres dans la clé pour cache séparé.
 */
export const venueKeys = {
  all: ['venues'] as const,
  lists: () => [...venueKeys.all, 'list'] as const,
  list: (projectId: number, params?: VenueQueryParams) => 
    [...venueKeys.lists(), projectId, params] as const,
  details: () => [...venueKeys.all, 'detail'] as const,
  detail: (id: number) => [...venueKeys.details(), id] as const,
}

// ============================================
// Queries (GET)
// ============================================

/**
 * Hook pour lister les gymnases d'un projet.
 * 
 * Usage :
 *   const { data: venues } = useVenues(1)
 */
export function useVenues(projectId: number, params?: VenueQueryParams) {
  return useQuery({
    queryKey: venueKeys.list(projectId, params),
    queryFn: () => venuesApi.getVenues(projectId, params),
    enabled: !!projectId,
  })
}

/**
 * Hook pour récupérer un gymnase par ID.
 * 
 * Usage :
 *   const { data: venue } = useVenue(1)
 */
export function useVenue(id: number) {
  return useQuery({
    queryKey: venueKeys.detail(id),
    queryFn: () => venuesApi.getVenue(id),
    enabled: !!id,
  })
}

// ============================================
// Mutations (POST, PUT, DELETE)
// ============================================

/**
 * Hook pour créer un gymnase.
 * 
 * Usage :
 *   const createVenue = useCreateVenue()
 *   createVenue.mutate({
 *     project_id: 1,
 *     nom: "Gymnase Nord",
 *     capacite: 2,
 *     horaires_disponibles: ["09:00", "10:00", "11:00"]
 *   })
 */
export function useCreateVenue() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (data: VenueCreate) => venuesApi.createVenue(data),
    onSuccess: (newVenue) => {
      queryClient.invalidateQueries({ 
        queryKey: venueKeys.list(newVenue.project_id) 
      })
    },
  })
}

/**
 * Hook pour mettre à jour un gymnase.
 * 
 * Usage :
 *   const updateVenue = useUpdateVenue()
 *   updateVenue.mutate({ id: 1, updates: { capacite: 3 } })
 */
export function useUpdateVenue() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ id, updates }: { id: number; updates: VenueUpdate }) =>
      venuesApi.updateVenue(id, updates),
    onSuccess: (updatedVenue) => {
      queryClient.invalidateQueries({ queryKey: venueKeys.detail(updatedVenue.id) })
      queryClient.invalidateQueries({ 
        queryKey: venueKeys.list(updatedVenue.project_id) 
      })
    },
  })
}

/**
 * Hook pour supprimer un gymnase.
 * 
 * Les matchs dans ce gymnase doivent être replanifiés.
 * 
 * Usage :
 *   const deleteVenue = useDeleteVenue()
 *   deleteVenue.mutate({ id: 1, projectId: 1 })
 */
export function useDeleteVenue() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ id, projectId }: { id: number; projectId: number }) =>
      venuesApi.deleteVenue(id),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ 
        queryKey: venueKeys.list(variables.projectId) 
      })
      // Invalider aussi les matchs car gymnase supprimé
      queryClient.invalidateQueries({ queryKey: ['matches'] })
    },
  })
}
