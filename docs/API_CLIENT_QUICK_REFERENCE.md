# 🚀 PyCalendar API Client - Guide de Référence Rapide

## 📦 Import

```typescript
import * as projectsApi from '@/services/projectsApi'
import * as teamsApi from '@/services/teamsApi'
import * as venuesApi from '@/services/venuesApi'
import * as matchesApi from '@/services/matchesApi'
import { getErrorMessage, isNotFoundError } from '@/utils/apiHelpers'
```

## 🔧 Projects API

| Fonction | Endpoint | Description |
|----------|----------|-------------|
| `getProjects(params?)` | `GET /projects` | Liste tous les projets |
| `getProject(id)` | `GET /projects/{id}` | Détails d'un projet |
| `createProject(data)` | `POST /projects` | Créer un projet |
| `updateProject(id, data)` | `PUT /projects/{id}` | Modifier un projet |
| `deleteProject(id)` | `DELETE /projects/{id}` | Supprimer un projet |
| `getProjectStats(id)` | `GET /projects/{id}/stats` | Statistiques du projet |

**Exemple** :
```typescript
const projects = await projectsApi.getProjects()
const project = await projectsApi.getProject(1)
const stats = await projectsApi.getProjectStats(1)
```

## 👥 Teams API

| Fonction | Endpoint | Description |
|----------|----------|-------------|
| `getTeams(projectId, params?)` | `GET /projects/{id}/teams` | Liste équipes d'un projet |
| `getTeam(id)` | `GET /teams/{id}` | Détails d'une équipe |
| `createTeam(data)` | `POST /projects/{id}/teams` | Créer une équipe |
| `updateTeam(id, data)` | `PUT /teams/{id}` | Modifier une équipe |
| `deleteTeam(id)` | `DELETE /teams/{id}` | Supprimer une équipe |

**Filtres disponibles** : `poule`, `institution`, `genre`

**Exemple** :
```typescript
const allTeams = await teamsApi.getTeams(1)
const p1Teams = await teamsApi.getTeams(1, { poule: 'P1' })
const boysTeams = await teamsApi.getTeams(1, { genre: 'Garçons' })
```

## 🏟️ Venues API

| Fonction | Endpoint | Description |
|----------|----------|-------------|
| `getVenues(projectId, params?)` | `GET /projects/{id}/venues` | Liste gymnases d'un projet |
| `getVenue(id)` | `GET /venues/{id}` | Détails d'un gymnase |
| `createVenue(data)` | `POST /projects/{id}/venues` | Créer un gymnase |
| `updateVenue(id, data)` | `PUT /venues/{id}` | Modifier un gymnase |
| `deleteVenue(id)` | `DELETE /venues/{id}` | Supprimer un gymnase |

**Exemple** :
```typescript
const venues = await venuesApi.getVenues(1)
const venue = await venuesApi.getVenue(1)
```

## 🏐 Matches API

| Fonction | Endpoint | Description |
|----------|----------|-------------|
| `getMatches(projectId, params?)` | `GET /projects/{id}/matches` | Liste matchs d'un projet |
| `getMatch(id)` | `GET /matches/{id}` | Détails d'un match |
| `createMatch(data)` | `POST /projects/{id}/matches` | Créer un match |
| `updateMatch(id, data)` | `PUT /matches/{id}` | Modifier un match |
| `deleteMatch(id)` | `DELETE /matches/{id}` | Supprimer un match |
| `moveMatch(id, payload)` | `POST /matches/{id}/move` | Déplacer un match |
| `fixMatch(id)` | `POST /matches/{id}/fix` | Fixer un match |
| `unfixMatch(id)` | `POST /matches/{id}/unfix` | Défixer un match |

**Filtres disponibles** : `semaine`, `poule`, `gymnase`, `est_fixe`, `statut`

**Exemple** :
```typescript
const allMatches = await matchesApi.getMatches(1)
const week3 = await matchesApi.getMatches(1, { semaine: 3 })
const p1Matches = await matchesApi.getMatches(1, { poule: 'P1' })

const moved = await matchesApi.moveMatch(1, { nouvelle_semaine: 5 })
const fixed = await matchesApi.fixMatch(1)
const unfixed = await matchesApi.unfixMatch(1)
```

## ❌ Error Handling

| Helper | Type d'erreur | Code HTTP |
|--------|--------------|-----------|
| `getErrorMessage(error)` | Extraction message | - |
| `isNotFoundError(error)` | Ressource non trouvée | 404 |
| `isBadRequestError(error)` | Requête invalide | 400 |
| `isValidationError(error)` | Validation échouée | 422 |
| `isServerError(error)` | Erreur serveur | 5xx |
| `isNetworkError(error)` | Problème réseau | - |

**Exemple** :
```typescript
try {
  const match = await matchesApi.getMatch(999)
} catch (error) {
  if (isNotFoundError(error)) {
    console.error('Match introuvable')
  } else {
    console.error(getErrorMessage(error))
  }
}
```

## 🔄 React Query Preview (Tâche 2.4)

```typescript
// Hook pour lister les matchs
import { useQuery } from '@tanstack/react-query'

export function useMatches(projectId: number, filters?: MatchQueryParams) {
  return useQuery({
    queryKey: ['matches', projectId, filters],
    queryFn: () => matchesApi.getMatches(projectId, filters)
  })
}

// Hook pour déplacer un match
export function useMoveMatch() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }) => matchesApi.moveMatch(id, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['matches'] })
  })
}
```

## 📝 Notes importantes

1. **Proxy Vite** : `/api` → `http://localhost:8000` (en développement)
2. **Types** : Tous les retours sont typés avec TypeScript (Project, Team, Venue, Match)
3. **Erreurs** : FastAPI retourne `{ detail: "Message" }`, accessible via `getErrorMessage(error)`
4. **Structure** : Match denormalisé (equipe1_nom, equipe2_nom - pas de FK)
5. **Validation** : moveMatch valide backend (est_fixe = false, semaine >= semaine_min)

## 🔗 Fichiers de référence

- **Types** : `frontend/src/types/`
- **API clients** : `frontend/src/services/`
- **Error helpers** : `frontend/src/utils/apiHelpers.ts`
- **Exemples** : `frontend/src/examples/apiUsageExamples.ts`
- **Doc complète** : `docs/TASK_2.3_API_CLIENT_COMPLETE.md`
