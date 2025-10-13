/**
 * Types utilitaires pour l'API.
 */

/**
 * Réponse API générique paginée.
 * 
 * Utilisé si le backend implémente la pagination pour les listes.
 */
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  per_page: number
  total_pages: number
}

/**
 * Erreur API standardisée.
 * 
 * Format FastAPI standard pour les erreurs HTTP.
 */
export interface ApiError {
  detail: string
  status_code: number
}

/**
 * Options de query pour lister les matchs.
 */
export interface MatchQueryParams {
  project_id?: number
  semaine?: number
  poule?: string
  gymnase?: string
  est_fixe?: boolean
  statut?: string
}

/**
 * Options de query pour lister les équipes.
 */
export interface TeamQueryParams {
  project_id?: number
  poule?: string
  genre?: string
  institution?: string
}

/**
 * Options de query pour lister les gymnases.
 */
export interface VenueQueryParams {
  project_id?: number
}

/**
 * Options de query pour lister les projets.
 */
export interface ProjectQueryParams {
  sport?: string
}
