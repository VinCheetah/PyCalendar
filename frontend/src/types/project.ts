/**
 * Types pour les projets PyCalendar.
 * 
 * IMPORTANT : Le backend stocke la configuration dans `config_data` (Dict[str, Any])
 * qui peut contenir à la fois les données YAML et Excel selon l'implémentation.
 * 
 * Pour cohérence avec le prompt, nous définissons ConfigYamlData et ConfigExcelData,
 * mais le backend ProjectResponse utilise config_data générique.
 */

// ============================================
// Config YAML Structure
// ============================================

/**
 * Contenu du fichier YAML de configuration.
 * 
 * Source : configs/default.yaml, configs/config_volley.yaml
 */
export interface ConfigYamlData {
  sport: string
  
  semaines: {
    nb_semaines: number
    semaine_minimum: number  // Première semaine modifiable par le solver
  }
  
  contraintes: {
    poids: {
      respect_repos: number
      equilibre_domicile_exterieur: number
      respect_indisponibilites: number
      respect_preferences: number
      respect_semaine_min?: number
      // Autres poids possibles...
    }
  }
  
  solver: {
    strategie: 'optimal' | 'heuristique' | 'hybride'
    temps_max_secondes: number
  }
  
  fichiers: {
    donnees: string  // Chemin vers fichier Excel
  }
}

// ============================================
// Config Excel Metadata
// ============================================

/**
 * Métadonnées du fichier Excel (structure, comptages).
 * 
 * NE CONTIENT PAS les données brutes Excel (trop volumineuses),
 * seulement les métadonnées utiles pour l'affichage.
 */
export interface ConfigExcelData {
  nb_equipes: number
  nb_gymnases: number
  nb_poules: number
  
  feuilles_presentes: string[]  // Ex: ["Equipes", "Gymnases", "Indispos_Gymnases", ...]
  
  // Métadonnées supplémentaires (optionnel)
  niveaux?: string[]            // Ex: ["Minimes", "Cadets", "Juniors"]
  categories?: string[]         // Ex: ["Garçons", "Filles"]
  institutions?: string[]       // Ex: ["Lycée A", "Lycée B"]
}

// ============================================
// Project Types
// ============================================

/**
 * Projet complet retourné par l'API.
 * 
 * Correspond au schéma Pydantic ProjectResponse.
 * 
 * Note: Backend utilise config_data (Any) générique.
 * Pour le frontend, on peut le typer comme ConfigYamlData | ConfigExcelData | null.
 */
export interface Project {
  id: number
  nom: string
  sport: string
  
  // Configuration
  config_yaml_path: string | null
  config_data: any | null  // Backend: Dict[str, Any] - peut contenir YAML ou Excel data
  
  // Paramètres planification
  nb_semaines: number
  semaine_min: number  // Première semaine modifiable (depuis YAML semaine_minimum)
  
  // Timestamps
  created_at: string  // ISO 8601
  updated_at: string  // ISO 8601
}

/**
 * Données pour créer un nouveau projet.
 * 
 * Correspond au schéma Pydantic ProjectCreate.
 */
export interface ProjectCreate {
  nom: string
  sport: string
  
  // Configuration (optionnel)
  config_yaml_path?: string | null
  config_data?: any | null
  
  // Paramètres planification (avec defaults)
  nb_semaines?: number  // Default: 26
  semaine_min?: number  // Default: 1
}

/**
 * Données pour mettre à jour un projet (PATCH).
 * 
 * Correspond au schéma Pydantic ProjectUpdate.
 */
export interface ProjectUpdate {
  nom?: string
  sport?: string
  config_yaml_path?: string | null
  config_data?: any | null
  nb_semaines?: number
  semaine_min?: number
}

/**
 * Statistiques d'un projet.
 * 
 * Correspond au schéma Pydantic ProjectStats.
 */
export interface ProjectStats {
  nb_matchs_total: number
  nb_matchs_planifies: number
  nb_matchs_fixes: number
  nb_matchs_a_planifier: number
  nb_equipes: number
  nb_gymnases: number
}
