# PROMPT 2.4 : Hooks React Query

## Contexte

**PyCalendar V2** : Hooks React Query pour cache/invalidation données API.

## État

- ✅ API client Axios
- ⏳ Hooks React Query

## Objectif

Wrapper API calls dans hooks useQuery/useMutation.

**Durée** : 30 min

## Instructions

### Setup Provider

**Fichier** : `frontend/src/main.tsx`

```typescript
import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './App'
import './index.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </React.StrictMode>,
)
```

### Hooks Matches

**Fichier** : `frontend/src/hooks/useMatches.ts`

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { matchesApi } from '@/api'
import type { MatchUpdate, MatchMove } from '@/types'

export function useMatches(projectId?: number) {
  return useQuery({
    queryKey: ['matches', projectId],
    queryFn: () => matchesApi.list(projectId),
    enabled: !!projectId,
  })
}

export function useMatch(id: number) {
  return useQuery({
    queryKey: ['matches', id],
    queryFn: () => matchesApi.get(id),
  })
}

export function useUpdateMatch() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: MatchUpdate }) =>
      matchesApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['matches'] })
    },
  })
}

export function useMoveMatch() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, creneau }: { id: number; creneau: MatchMove }) =>
      matchesApi.move(id, creneau),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['matches'] })
    },
  })
}

export function useFixMatch() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id }: { id: number }) => matchesApi.fix(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['matches'] })
    },
  })
}

export function useUnfixMatch() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id }: { id: number }) => matchesApi.unfix(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['matches'] })
    },
  })
}
```

### Hooks Projects

**Fichier** : `frontend/src/hooks/useProjects.ts`

```typescript
import { useQuery } from '@tanstack/react-query'
import { projectsApi } from '@/api'

export function useProjects() {
  return useQuery({
    queryKey: ['projects'],
    queryFn: () => projectsApi.list(),
  })
}

export function useProject(id: number) {
  return useQuery({
    queryKey: ['projects', id],
    queryFn: () => projectsApi.get(id),
  })
}
```

## Validation

```tsx
function TestComponent() {
  const { data: matches, isLoading } = useMatches(1)
  const moveMatch = useMoveMatch()
  
  if (isLoading) return <div>Loading...</div>
  
  return (
    <div>
      <p>Matches: {matches?.length}</p>
      <button onClick={() => {
        moveMatch.mutate({
          id: matches[0].id,
          creneau: { semaine: 5, horaire: "14:00", gymnase: "Gym A" }
        })
      }}>
        Move First Match
      </button>
    </div>
  )
}
```

## Critères

- [ ] QueryClientProvider dans main.tsx
- [ ] Hooks useMatches, useMatch
- [ ] Mutations avec invalidateQueries
- [ ] queryKey cohérentes
- [ ] Types TypeScript corrects

## Prochaine Étape

➡️ **Prompt 2.5** : Composant Calendrier FullCalendar
