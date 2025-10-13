/**
 * Export centralisé des hooks React Query PyCalendar.
 * 
 * Usage :
 *   import { useProjects, useMatches, useMoveMatch } from '@/hooks'
 *   
 *   const { data: projects } = useProjects()
 *   const { data: matches } = useMatches(1, { semaine: 3 })
 *   const moveMatch = useMoveMatch()
 */

// Hooks Projects
export * from './useProjects'

// Hooks Matches
export * from './useMatches'

// Hooks Teams
export * from './useTeams'

// Hooks Venues
export * from './useVenues'

// Hooks Solver
export * from './useSolver'
