/**
 * Types pour les gymnases.
 * 
 * Source Excel : Feuille "Gymnases" avec colonnes :
 * - Nom, Capacité
 * - Colonnes horaires dynamiques (ex: "Mercredi 14:00", "Vendredi 18:00")
 * 
 * Correspond au schéma Pydantic VenueResponse.
 */

export interface Venue {
  id: number
  project_id: number
  
  // Informations gymnase (depuis feuille Gymnases)
  nom: string
  capacite: number  // Nombre de terrains simultanés (default: 1)
  
  // Disponibilités (depuis colonnes horaires du Excel)
  horaires_disponibles: string[] | null  // Ex: ["Mercredi 14:00", "Vendredi 18:00"]
  
  // Timestamps
  created_at: string  // ISO 8601
}

/**
 * Données pour créer un nouveau gymnase.
 * 
 * Correspond au schéma Pydantic VenueCreate.
 */
export interface VenueCreate {
  project_id: number
  nom: string
  capacite?: number  // Default: 1
  horaires_disponibles?: string[] | null
}

/**
 * Données pour mettre à jour un gymnase (PATCH).
 * 
 * Correspond au schéma Pydantic VenueUpdate.
 */
export interface VenueUpdate {
  nom?: string
  capacite?: number
  horaires_disponibles?: string[] | null
}
