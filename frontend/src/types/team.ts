/**
 * Types pour les équipes.
 * 
 * Source Excel : Feuille "Equipes" avec colonnes :
 * - Nom, Institution, Numéro équipe, Genre, Poule
 * 
 * Correspond au schéma Pydantic TeamResponse.
 */

export interface Team {
  id: number
  project_id: number
  
  // Identité équipe (depuis feuille Equipes)
  nom: string
  institution: string | null
  numero_equipe: string | null  // String car peut contenir "1", "2", "A", "B", etc.
  genre: string | null          // "Garçons", "Filles", "Mixte"
  poule: string | null          // "P1", "P2", "P3", etc.
  
  // Préférences (depuis feuille Equipes ou Preferences_Gymnases)
  horaires_preferes: string[] | null  // Ex: ["Mercredi 14:00", "Vendredi 18:00"]
  lieux_preferes: string[] | null     // Ex: ["Gymnase A", "Gymnase B"]
  
  // Timestamps
  created_at: string  // ISO 8601
}

/**
 * Données pour créer une nouvelle équipe.
 * 
 * Correspond au schéma Pydantic TeamCreate.
 */
export interface TeamCreate {
  project_id: number
  nom: string
  institution?: string | null
  numero_equipe?: string | null
  genre?: string | null
  poule?: string | null
  horaires_preferes?: string[] | null
  lieux_preferes?: string[] | null
}

/**
 * Données pour mettre à jour une équipe (PATCH).
 * 
 * Correspond au schéma Pydantic TeamUpdate.
 */
export interface TeamUpdate {
  nom?: string
  institution?: string | null
  numero_equipe?: string | null
  genre?: string | null
  poule?: string | null
  horaires_preferes?: string[] | null
  lieux_preferes?: string[] | null
}
