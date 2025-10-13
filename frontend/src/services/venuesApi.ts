/**
 * API client pour les gymnases PyCalendar.
 * 
 * Endpoints backend :
 * - GET    /venues/?project_id={id}          : Liste tous les gymnases d'un projet
 * - POST   /venues/                          : Créer un nouveau gymnase
 * - GET    /venues/{id}                      : Détails d'un gymnase
 * - PUT    /venues/{id}                      : Mettre à jour un gymnase
 * - DELETE /venues/{id}                      : Supprimer un gymnase
 */

import api from './api'
import type { 
  Venue, 
  VenueCreate, 
  VenueUpdate, 
  VenueQueryParams 
} from '@/types'

/**
 * Liste tous les gymnases d'un projet.
 * 
 * Filtres optionnels via params (si implémentés dans le backend).
 */
export async function getVenues(
  projectId: number, 
  params?: VenueQueryParams
): Promise<Venue[]> {
  const { data } = await api.get<Venue[]>('/venues/', { 
    params: { project_id: projectId, ...params } 
  })
  return data
}

/**
 * Récupère un gymnase par ID.
 */
export async function getVenue(id: number): Promise<Venue> {
  const { data } = await api.get<Venue>(`/venues/${id}`)
  return data
}

/**
 * Crée un nouveau gymnase.
 * 
 * Note : Les gymnases sont généralement créés automatiquement lors de l'import Excel.
 * La création manuelle est rare.
 */
export async function createVenue(venue: VenueCreate): Promise<Venue> {
  const { data } = await api.post<Venue>('/venues/', venue)
  return data
}

/**
 * Met à jour un gymnase existant.
 * 
 * Permet de modifier :
 * - nom : Nom du gymnase
 * - capacite : Nombre de terrains simultanés (default: 1)
 * - horaires_disponibles : Liste d'horaires disponibles ["14:00", "16:00"]
 */
export async function updateVenue(
  id: number, 
  updates: VenueUpdate
): Promise<Venue> {
  const { data } = await api.put<Venue>(`/venues/${id}`, updates)
  return data
}

/**
 * Supprime un gymnase.
 * 
 * Tous les matchs planifiés dans ce gymnase devront être replanifiés.
 */
export async function deleteVenue(id: number): Promise<void> {
  await api.delete(`/venues/${id}`)
}
