/**
 * Types pour les matchs.
 * 
 * IMPORTANT :
 * - Matchs générés automatiquement par MultiPoolGenerator (backend)
 * - Structure DENORMALISEE : equipe1_nom, equipe2_nom (pas de FK vers Team)
 * - Matchs fixes : définis via UI web (est_fixe = true)
 * - Semaine < semaine_min : Non modifiable par solver
 * 
 * Correspond au schéma Pydantic MatchResponse.
 */

/**
 * Type union pour statut du match.
 */
export type MatchStatus = 'a_planifier' | 'planifie' | 'fixe' | 'termine' | 'annule'

/**
 * Match retourné par l'API.
 * 
 * Structure denormalisée : les noms d'équipes sont stockés directement,
 * pas de relation FK vers Team (simplifie les requêtes).
 */
export interface Match {
  id: number
  project_id: number
  
  // Équipes (denormalisées - pas de FK)
  equipe1_nom: string
  equipe1_institution: string | null
  equipe1_genre: string | null
  
  equipe2_nom: string
  equipe2_institution: string | null
  equipe2_genre: string | null
  
  // Poule
  poule: string | null
  
  // Créneau (optionnel si non planifié)
  semaine: number | null
  horaire: string | null  // Format: "14:00" (HH:MM)
  gymnase: string | null
  
  // État
  est_fixe: boolean          // True = non modifiable par solver
  statut: MatchStatus
  priorite: number
  
  // Scores et notes
  score_equipe1: number | null
  score_equipe2: number | null
  notes: string | null
  
  // Timestamps
  created_at: string  // ISO 8601
  updated_at: string  // ISO 8601
}

/**
 * Données pour créer un nouveau match.
 * 
 * Correspond au schéma Pydantic MatchCreate.
 */
export interface MatchCreate {
  project_id: number
  
  // Équipes (denormalisées)
  equipe1_nom: string
  equipe1_institution?: string | null
  equipe1_genre?: string | null
  equipe2_nom: string
  equipe2_institution?: string | null
  equipe2_genre?: string | null
  
  // Poule
  poule?: string | null
  
  // Créneau (optionnel)
  semaine?: number | null
  horaire?: string | null
  gymnase?: string | null
  
  // État (avec defaults)
  est_fixe?: boolean       // Default: false
  statut?: MatchStatus     // Default: "a_planifier"
  priorite?: number        // Default: 0
}

/**
 * Données pour mettre à jour un match (PATCH).
 * 
 * Correspond au schéma Pydantic MatchUpdate.
 */
export interface MatchUpdate {
  semaine?: number | null
  horaire?: string | null
  gymnase?: string | null
  est_fixe?: boolean
  statut?: MatchStatus
  priorite?: number
  score_equipe1?: number | null
  score_equipe2?: number | null
  notes?: string | null
}

/**
 * Payload pour déplacer un match (drag & drop).
 * 
 * Correspond au schéma Pydantic MatchMove.
 */
export interface MatchMovePayload {
  nouvelle_semaine: number
}

/**
 * Match étendu avec informations calculées côté frontend.
 * 
 * Utile pour l'affichage dans le calendrier avec infos dérivées.
 */
export interface MatchExtended extends Match {
  // Informations calculées côté frontend
  est_modifiable: boolean     // False si est_fixe ou semaine < semaine_min
  titre: string               // Ex: "Lycée A - 1 vs Lycée B - 2"
  couleur?: string            // Couleur pour calendrier (par poule, genre, etc.)
}
