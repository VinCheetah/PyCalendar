/**
 * Export centralisé des API clients PyCalendar.
 * 
 * Usage :
 *   import * as projectsApi from '@/services/projectsApi'
 *   import * as matchesApi from '@/services/matchesApi'
 *   
 *   const projects = await projectsApi.getProjects()
 *   const matches = await matchesApi.getMatches(projectId)
 */

// Export des API clients par module
export * as projectsApi from './projectsApi'
export * as teamsApi from './teamsApi'
export * as venuesApi from './venuesApi'
export * as matchesApi from './matchesApi'
export * as solverApi from './solverApi'

// Export de l'instance Axios pour usage avancé
export { default as api } from './api'

// Export des types Axios pour gestion d'erreurs
export type { AxiosError, AxiosResponse } from 'axios'
