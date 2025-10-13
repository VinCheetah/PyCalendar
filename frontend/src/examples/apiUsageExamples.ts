/**
 * Exemples d'utilisation des API clients PyCalendar.
 * 
 * Ce fichier démontre comment utiliser les API clients créés.
 * À supprimer avant production - uniquement pour référence.
 */

import * as projectsApi from '@/services/projectsApi'
import * as teamsApi from '@/services/teamsApi'
import * as venuesApi from '@/services/venuesApi'
import * as matchesApi from '@/services/matchesApi'
import { 
  getErrorMessage, 
  isNotFoundError, 
  isBadRequestError,
  isValidationError 
} from '@/utils/apiHelpers'

// ========================================
// EXEMPLE 1 : Projets
// ========================================

async function exampleProjects() {
  try {
    // Lister tous les projets
    const projects = await projectsApi.getProjects()
    console.log('Projets:', projects)

    // Récupérer un projet par ID
    const project = await projectsApi.getProject(1)
    console.log('Config YAML:', project.config_data)
    console.log('Nb semaines:', project.nb_semaines)

    // Créer un nouveau projet
    const newProject = await projectsApi.createProject({
      nom: 'Test Volleyball 2025',
      sport: 'Volleyball',
      nb_semaines: 10,
      semaine_min: 2,
      config_data: {
        sport: 'Volleyball',
        semaines: { nb_semaines: 10, semaine_minimum: 2 },
        contraintes: {
          poids: {
            respect_repos: 10,
            equilibre_domicile_exterieur: 5,
            respect_indisponibilites: 8,
            respect_preferences: 3
          }
        },
        solver: { strategie: 'optimal', temps_max_secondes: 300 },
        fichiers: { donnees: 'data.xlsx' }
      }
    })
    console.log('Projet créé:', newProject)

    // Récupérer les statistiques
    const stats = await projectsApi.getProjectStats(1)
    console.log('Stats:', stats)
    console.log('Matchs planifiés:', `${stats.nb_matchs_planifies}/${stats.nb_matchs_total}`)

  } catch (error) {
    console.error('Erreur projets:', getErrorMessage(error))
  }
}

// ========================================
// EXEMPLE 2 : Équipes avec filtres
// ========================================

async function exampleTeams() {
  try {
    // Lister toutes les équipes d'un projet
    const allTeams = await teamsApi.getTeams(1)
    console.log('Toutes les équipes:', allTeams)

    // Filtrer par poule
    const p1Teams = await teamsApi.getTeams(1, { poule: 'P1' })
    console.log('Équipes P1:', p1Teams)

    // Filtrer par genre
    const boysTeams = await teamsApi.getTeams(1, { genre: 'Garçons' })
    console.log('Équipes garçons:', boysTeams)

    // Filtrer par institution
    const lyceeATeams = await teamsApi.getTeams(1, { institution: 'Lycée A' })
    console.log('Équipes Lycée A:', lyceeATeams)

    // Mettre à jour les préférences d'une équipe
    const updatedTeam = await teamsApi.updateTeam(1, {
      horaires_preferes: ['14:00', '16:00'],
      lieux_preferes: ['Gymnase Central', 'Gymnase Nord']
    })
    console.log('Équipe mise à jour:', updatedTeam)

  } catch (error) {
    console.error('Erreur équipes:', getErrorMessage(error))
  }
}

// ========================================
// EXEMPLE 3 : Gymnases
// ========================================

async function exampleVenues() {
  try {
    // Lister tous les gymnases
    const venues = await venuesApi.getVenues(1)
    console.log('Gymnases:', venues)

    // Récupérer un gymnase
    const venue = await venuesApi.getVenue(1)
    console.log('Gymnase:', venue)
    console.log('Capacité:', venue.capacite, 'terrains')

    // Mettre à jour les horaires disponibles
    const updatedVenue = await venuesApi.updateVenue(1, {
      horaires_disponibles: ['14:00', '16:00', '18:00']
    })
    console.log('Gymnase mis à jour:', updatedVenue)

  } catch (error) {
    console.error('Erreur gymnases:', getErrorMessage(error))
  }
}

// ========================================
// EXEMPLE 4 : Matchs avec filtres
// ========================================

async function exampleMatches() {
  try {
    // Lister tous les matchs d'un projet
    const allMatches = await matchesApi.getMatches(1)
    console.log('Tous les matchs:', allMatches)

    // Filtrer par semaine
    const week3Matches = await matchesApi.getMatches(1, { semaine: 3 })
    console.log('Matchs semaine 3:', week3Matches)

    // Filtrer par poule
    const p1Matches = await matchesApi.getMatches(1, { poule: 'P1' })
    console.log('Matchs poule P1:', p1Matches)

    // Filtrer par gymnase
    const gymMatches = await matchesApi.getMatches(1, { 
      gymnase: 'Gymnase Central' 
    })
    console.log('Matchs Gymnase Central:', gymMatches)

    // Filtrer par statut
    const planifiedMatches = await matchesApi.getMatches(1, { 
      statut: 'planifie' 
    })
    console.log('Matchs planifiés:', planifiedMatches)

    // Récupérer un match
    const match = await matchesApi.getMatch(1)
    console.log('Match:', match)

  } catch (error) {
    console.error('Erreur matchs:', getErrorMessage(error))
  }
}

// ========================================
// EXEMPLE 5 : Déplacer et fixer des matchs
// ========================================

async function exampleMatchOperations() {
  try {
    // Déplacer un match (uniquement nouvelle semaine)
    const movedMatch = await matchesApi.moveMatch(1, {
      nouvelle_semaine: 5
    })
    console.log('Match déplacé:', movedMatch)

    // Fixer un match (verrouiller)
    const fixedMatch = await matchesApi.fixMatch(1)
    console.log('Match fixé:', fixedMatch)
    console.log('Est fixe:', fixedMatch.est_fixe)  // true

    // Défixer un match (déverrouiller)
    const unfixedMatch = await matchesApi.unfixMatch(1)
    console.log('Match défixé:', unfixedMatch)
    console.log('Est fixe:', unfixedMatch.est_fixe)  // false

    // Mettre à jour les scores
    const scoredMatch = await matchesApi.updateMatch(1, {
      score_equipe1: 25,
      score_equipe2: 23,
      statut: 'termine'
    })
    console.log('Match avec scores:', scoredMatch)

  } catch (error) {
    if (isBadRequestError(error)) {
      console.error('Match non modifiable (probablement fixé)')
    } else {
      console.error('Erreur opération match:', getErrorMessage(error))
    }
  }
}

// ========================================
// EXEMPLE 6 : Gestion d'erreurs complète
// ========================================

async function exampleErrorHandling() {
  try {
    // Tenter de récupérer un match inexistant
    await matchesApi.getMatch(999)

  } catch (error) {
    if (isNotFoundError(error)) {
      console.error('❌ Ressource introuvable (404)')
    } else if (isBadRequestError(error)) {
      console.error('❌ Requête invalide (400)')
    } else if (isValidationError(error)) {
      console.error('❌ Erreur de validation (422)')
    } else {
      console.error('❌ Erreur:', getErrorMessage(error))
    }
  }

  try {
    // Tenter de déplacer un match fixé
    await matchesApi.moveMatch(1, { nouvelle_semaine: 5 })

  } catch (error) {
    if (isBadRequestError(error)) {
      console.error('❌ Match non modifiable (est_fixe = true ou semaine < semaine_min)')
    } else {
      console.error('❌ Erreur:', getErrorMessage(error))
    }
  }
}

// ========================================
// EXEMPLE 7 : Workflow complet
// ========================================

async function exampleCompleteWorkflow() {
  try {
    console.log('🚀 Démarrage workflow complet...\n')

    // 1. Créer un projet
    console.log('1️⃣ Création du projet...')
    const project = await projectsApi.createProject({
      nom: 'Championnat Volleyball 2025',
      sport: 'Volleyball',
      nb_semaines: 12,
      semaine_min: 2,
      config_data: null  // Config YAML sera chargé plus tard
    })
    console.log('✅ Projet créé:', project.nom)

    // 2. Lister les matchs
    console.log('\n2️⃣ Récupération des matchs...')
    const matches = await matchesApi.getMatches(project.id)
    console.log(`✅ ${matches.length} matchs trouvés`)

    // 3. Filtrer les matchs de la semaine 3
    console.log('\n3️⃣ Filtrage semaine 3...')
    const week3 = await matchesApi.getMatches(project.id, { semaine: 3 })
    console.log(`✅ ${week3.length} matchs en semaine 3`)

    // 4. Récupérer les statistiques
    console.log('\n4️⃣ Récupération des stats...')
    const stats = await projectsApi.getProjectStats(project.id)
    console.log(`✅ Stats:`)
    console.log(`   - Total: ${stats.nb_matchs_total} matchs`)
    console.log(`   - Planifiés: ${stats.nb_matchs_planifies} matchs`)
    console.log(`   - Fixes: ${stats.nb_matchs_fixes} matchs`)
    console.log(`   - À planifier: ${stats.nb_matchs_a_planifier} matchs`)

    console.log('\n🎉 Workflow terminé avec succès!')

  } catch (error) {
    console.error('❌ Erreur workflow:', getErrorMessage(error))
  }
}

// ========================================
// EXEMPLE 8 : Usage avec React Query (Preview)
// ========================================

/**
 * Exemple de hook React Query utilisant ces API clients.
 * (Sera implémenté dans Tâche 2.4)
 */
/*
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

// Hook pour lister les matchs
export function useMatches(projectId: number, filters?: MatchQueryParams) {
  return useQuery({
    queryKey: ['matches', projectId, filters],
    queryFn: () => matchesApi.getMatches(projectId, filters),
    staleTime: 5 * 60 * 1000,  // 5 minutes
  })
}

// Hook pour déplacer un match
export function useMoveMatch() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ id, payload }: { id: number, payload: MatchMovePayload }) => 
      matchesApi.moveMatch(id, payload),
    onSuccess: (_, { id }) => {
      // Invalider les requêtes de matchs après déplacement
      queryClient.invalidateQueries({ queryKey: ['matches'] })
      queryClient.invalidateQueries({ queryKey: ['match', id] })
    }
  })
}
*/

// ========================================
// Exporter les exemples (pour tests)
// ========================================

export {
  exampleProjects,
  exampleTeams,
  exampleVenues,
  exampleMatches,
  exampleMatchOperations,
  exampleErrorHandling,
  exampleCompleteWorkflow,
}
