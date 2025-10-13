# React Query Hooks - Guide de Référence Rapide

## Import

```typescript
import { 
  useProjects, useProject, useProjectStats,
  useMatches, useMatch, useMoveMatch, useFixMatch, useUnfixMatch,
  useTeams, useTeam,
  useVenues, useVenue,
  useCreateProject, useUpdateProject, useDeleteProject,
  useCreateMatch, useUpdateMatch, useDeleteMatch,
  useCreateTeam, useUpdateTeam, useDeleteTeam,
  useCreateVenue, useUpdateVenue, useDeleteVenue
} from '@/hooks'
```

## Projects

| Hook | Type | Usage | Retour |
|------|------|-------|--------|
| `useProjects(params?)` | Query | Liste projets | `UseQueryResult<Project[]>` |
| `useProject(id)` | Query | Détail projet | `UseQueryResult<Project>` |
| `useProjectStats(id)` | Query | Stats projet | `UseQueryResult<ProjectStats>` |
| `useCreateProject()` | Mutation | Créer projet | `UseMutationResult<Project, unknown, ProjectCreate>` |
| `useUpdateProject()` | Mutation | MAJ projet | `UseMutationResult<Project, unknown, {id, updates}>` |
| `useDeleteProject()` | Mutation | Supprimer projet | `UseMutationResult<void, unknown, number>` |

**Exemples** :
```typescript
const { data: projects } = useProjects()
const { data: project } = useProject(1)
const { data: stats } = useProjectStats(1)

const createProject = useCreateProject()
createProject.mutate({ nom: "Projet", sport: "Volleyball" })

const updateProject = useUpdateProject()
updateProject.mutate({ id: 1, updates: { nom: "Nouveau nom" } })

const deleteProject = useDeleteProject()
deleteProject.mutate(1)
```

## Matches

| Hook | Type | Filtres | Usage |
|------|------|---------|-------|
| `useMatches(projectId, params?)` | Query | semaine, poule, gymnase, est_fixe, statut | Liste matchs |
| `useMatch(id)` | Query | - | Détail match |
| `useCreateMatch()` | Mutation | - | Créer match |
| `useUpdateMatch()` | Mutation | - | MAJ match |
| `useDeleteMatch()` | Mutation | - | Supprimer match |
| `useMoveMatch()` | Mutation | - | Déplacer match (nouvelle_semaine) |
| `useFixMatch()` | Mutation | - | Fixer match (non modifiable) |
| `useUnfixMatch()` | Mutation | - | Défixer match (modifiable) |

**Exemples** :
```typescript
// Queries avec filtrage
const { data: matches } = useMatches(1, { semaine: 3, poule: 'P1' })
const { data: match } = useMatch(1)

// Mutations CRUD
const createMatch = useCreateMatch()
createMatch.mutate({ project_id: 1, equipe_domicile_id: 1, equipe_exterieur_id: 2 })

const updateMatch = useUpdateMatch()
updateMatch.mutate({ id: 1, updates: { gymnase_id: 2 } })

const deleteMatch = useDeleteMatch()
deleteMatch.mutate({ id: 1, projectId: 1 })

// Mutations spéciales
const moveMatch = useMoveMatch()
moveMatch.mutate({ id: 1, payload: { nouvelle_semaine: 5 } })

const fixMatch = useFixMatch()
fixMatch.mutate(1)

const unfixMatch = useUnfixMatch()
unfixMatch.mutate(1)
```

## Teams

| Hook | Type | Filtres | Usage |
|------|------|---------|-------|
| `useTeams(projectId, params?)` | Query | poule, institution, genre | Liste équipes |
| `useTeam(id)` | Query | - | Détail équipe |
| `useCreateTeam()` | Mutation | - | Créer équipe |
| `useUpdateTeam()` | Mutation | - | MAJ équipe |
| `useDeleteTeam()` | Mutation | - | Supprimer équipe |

**Exemples** :
```typescript
const { data: teams } = useTeams(1, { poule: 'P1', genre: 'M' })
const { data: team } = useTeam(1)

const createTeam = useCreateTeam()
createTeam.mutate({ project_id: 1, nom: "Équipe A", poule: "P1" })

const updateTeam = useUpdateTeam()
updateTeam.mutate({ id: 1, updates: { nom: "Nouveau nom" } })

const deleteTeam = useDeleteTeam()
deleteTeam.mutate({ id: 1, projectId: 1 })
```

## Venues

| Hook | Type | Usage |
|------|------|-------|
| `useVenues(projectId, params?)` | Query | Liste gymnases |
| `useVenue(id)` | Query | Détail gymnase |
| `useCreateVenue()` | Mutation | Créer gymnase |
| `useUpdateVenue()` | Mutation | MAJ gymnase |
| `useDeleteVenue()` | Mutation | Supprimer gymnase |

**Exemples** :
```typescript
const { data: venues } = useVenues(1)
const { data: venue } = useVenue(1)

const createVenue = useCreateVenue()
createVenue.mutate({ project_id: 1, nom: "Gymnase Nord", capacite: 2 })

const updateVenue = useUpdateVenue()
updateVenue.mutate({ id: 1, updates: { capacite: 3 } })

const deleteVenue = useDeleteVenue()
deleteVenue.mutate({ id: 1, projectId: 1 })
```

## Query Keys

```typescript
// Projects
projectKeys.all                 // ['projects']
projectKeys.lists()             // ['projects', 'list']
projectKeys.list({ actif: true }) // ['projects', 'list', { actif: true }]
projectKeys.detail(1)           // ['projects', 'detail', 1]
projectKeys.stats(1)            // ['projects', 'stats', 1]

// Matches
matchKeys.all                   // ['matches']
matchKeys.list(1, { semaine: 3 }) // ['matches', 'list', 1, { semaine: 3 }]
matchKeys.detail(1)             // ['matches', 'detail', 1]

// Teams
teamKeys.list(1, { poule: 'P1' }) // ['teams', 'list', 1, { poule: 'P1' }]

// Venues
venueKeys.list(1)               // ['venues', 'list', 1]
```

## États React Query

```typescript
const { 
  data,           // Données de la query
  isLoading,      // true si première fois en chargement
  isFetching,     // true si refetch en cours
  isError,        // true si erreur
  error,          // Objet erreur
  refetch,        // Fonction pour refetch manuel
} = useProjects()

const { 
  mutate,         // Fonction mutation (fire-and-forget)
  mutateAsync,    // Fonction mutation async (await)
  isPending,      // true si mutation en cours
  isError,        // true si erreur
  error,          // Objet erreur
  reset,          // Reset mutation state
} = useCreateProject()
```

## Gestion d'Erreurs

```typescript
import { getErrorMessage, isNotFoundError, isBadRequestError } from '@/utils/apiHelpers'

// Dans Query
const { data, error } = useProjects()
if (error) {
  console.error(getErrorMessage(error)) // Extrait { detail: "..." }
}

// Dans Mutation (try/catch)
const createProject = useCreateProject()
try {
  await createProject.mutateAsync({ nom: "Projet" })
  alert('Succès')
} catch (err) {
  if (isBadRequestError(err)) {
    alert('Requête invalide')
  } else {
    alert(getErrorMessage(err))
  }
}

// Dans Mutation (onError)
export function useCreateProject() {
  return useMutation({
    mutationFn: (data) => projectsApi.createProject(data),
    onError: (error) => {
      console.error('Erreur:', getErrorMessage(error))
    }
  })
}
```

## Invalidation Cache

```typescript
import { useQueryClient } from '@tanstack/react-query'

const queryClient = useQueryClient()

// Invalider toutes queries projects
queryClient.invalidateQueries({ queryKey: ['projects'] })

// Invalider listes projects
queryClient.invalidateQueries({ queryKey: projectKeys.lists() })

// Invalider détail projet 1
queryClient.invalidateQueries({ queryKey: projectKeys.detail(1) })

// Invalider matchs projet 1
queryClient.invalidateQueries({ queryKey: matchKeys.list(1) })
```

## Workflow Complet

```typescript
import { useProjects, useMatches, useProjectStats, useMoveMatch } from '@/hooks'
import { getErrorMessage } from '@/utils/apiHelpers'

function Dashboard() {
  // 1. Charger projets
  const { data: projects, isLoading } = useProjects()
  
  // 2. Charger matchs du premier projet
  const projectId = projects?.[0]?.id
  const { data: matches } = useMatches(projectId ?? 0, { semaine: 3 })
  
  // 3. Charger stats
  const { data: stats } = useProjectStats(projectId ?? 0)
  
  // 4. Mutation
  const moveMatch = useMoveMatch()
  
  const handleMove = async (matchId: number) => {
    try {
      await moveMatch.mutateAsync({ 
        id: matchId, 
        payload: { nouvelle_semaine: 5 } 
      })
      // Cache invalidé automatiquement, matches refetch
      alert('Match déplacé !')
    } catch (err) {
      alert(getErrorMessage(err))
    }
  }
  
  if (isLoading) return <div>Chargement...</div>
  
  return (
    <div>
      <h2>Stats</h2>
      <p>{stats?.nb_matchs_planifies}/{stats?.nb_matchs_total} planifiés</p>
      
      <h2>Matchs</h2>
      {matches?.map(m => (
        <div key={m.id}>
          {m.equipe_domicile_nom} vs {m.equipe_exterieur_nom}
          <button onClick={() => handleMove(m.id)}>Déplacer</button>
        </div>
      ))}
    </div>
  )
}
```

## React Query DevTools

```typescript
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <YourApp />
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  )
}
```

**Utilisation** :
- Panneau en bas de l'écran
- Observer query keys actives
- Voir états : fresh (vert), stale (gris), fetching (bleu)
- Refetch manuel
- Observer invalidations

## Notes Importantes

### enabled: !!id
Évite d'exécuter query si ID invalide :
```typescript
const { data: project } = useProject(id) // Exécute si id > 0
```

### Filtres dans Query Keys
Cache séparé par filtres :
```typescript
useMatches(1, { semaine: 3 })  // Cache différent de
useMatches(1, { semaine: 4 })  // celui-ci
```

### Invalidation Cascade
```typescript
// useDeleteTeam() invalide :
queryClient.invalidateQueries({ queryKey: teamKeys.list(projectId) })
queryClient.invalidateQueries({ queryKey: ['matches'] }) // Cascade
```

### Mutations Spéciales Matches
- `useMoveMatch()` : Validation backend (match non fixé, semaine >= semaine_min)
- `useFixMatch()` : Match devient non modifiable par solver
- `useUnfixMatch()` : Match redevient modifiable

### Proxy API
Toutes requêtes vont vers `/api/*` (proxy Vite vers `http://localhost:8000`)

---

**Ressources** :
- Documentation complète : `frontend/docs/TASK_2.4_REACT_QUERY_HOOKS_COMPLETE.md`
- TanStack Query Docs : https://tanstack.com/query/latest
