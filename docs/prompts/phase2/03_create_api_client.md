# PROMPT 2.3 : Client API Axios

## Contexte

**PyCalendar V2 Frontend** : Client HTTP pour appels API backend.

## État

- ✅ Types TypeScript
- ⏳ Client Axios

## Objectif

Client Axios + endpoints typés pour API calls.

**Durée** : 30 min

## Instructions

### Client Base

**Fichier** : `frontend/src/api/client.ts`

```typescript
import axios from 'axios'

export const apiClient = axios.create({
  baseURL: '/api',  // Proxy Vite vers :8000
  headers: {
    'Content-Type': 'application/json',
  },
})

// Interceptor logging (optionnel)
apiClient.interceptors.request.use((config) => {
  console.log(`→ ${config.method?.toUpperCase()} ${config.url}`)
  return config
})

apiClient.interceptors.response.use(
  (response) => {
    console.log(`← ${response.status} ${response.config.url}`)
    return response
  },
  (error) => {
    console.error(`✗ ${error.message}`)
    return Promise.reject(error)
  }
)
```

### Endpoints Matches

**Fichier** : `frontend/src/api/endpoints/matches.ts`

```typescript
import { apiClient } from '../client'
import type { Match, MatchUpdate, MatchMove } from '@/types'

export const matchesApi = {
  list: async (projectId?: number): Promise<Match[]> => {
    const { data } = await apiClient.get('/matches/', {
      params: projectId ? { project_id: projectId } : {}
    })
    return data
  },
  
  get: async (id: number): Promise<Match> => {
    const { data } = await apiClient.get(`/matches/${id}`)
    return data
  },
  
  update: async (id: number, updates: MatchUpdate): Promise<Match> => {
    const { data } = await apiClient.put(`/matches/${id}`, updates)
    return data
  },
  
  move: async (id: number, creneau: MatchMove): Promise<Match> => {
    const { data } = await apiClient.post(`/matches/${id}/move`, creneau)
    return data
  },
  
  fix: async (id: number): Promise<void> => {
    await apiClient.post(`/matches/${id}/fix`)
  },
  
  unfix: async (id: number): Promise<void> => {
    await apiClient.post(`/matches/${id}/unfix`)
  },
  
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/matches/${id}`)
  },
}
```

### Endpoints Projects

**Fichier** : `frontend/src/api/endpoints/projects.ts`

```typescript
import { apiClient } from '../client'
import type { Project, ProjectUpdate } from '@/types'

export const projectsApi = {
  list: async (): Promise<Project[]> => {
    const { data } = await apiClient.get('/projects/')
    return data
  },
  
  get: async (id: number): Promise<Project> => {
    const { data } = await apiClient.get(`/projects/${id}`)
    return data
  },
  
  update: async (id: number, updates: ProjectUpdate): Promise<Project> => {
    const { data } = await apiClient.put(`/projects/${id}`, updates)
    return data
  },
}
```

### Index

**Fichier** : `frontend/src/api/index.ts`

```typescript
export { apiClient } from './client'
export { matchesApi } from './endpoints/matches'
export { projectsApi } from './endpoints/projects'
```

## Validation

```typescript
// Test appel API (backend doit tourner)
import { matchesApi, projectsApi } from '@/api'

async function test() {
  try {
    const projects = await projectsApi.list()
    console.log('Projects:', projects)
    
    if (projects.length > 0) {
      const matches = await matchesApi.list(projects[0].id)
      console.log('Matches:', matches.length)
    }
  } catch (error) {
    console.error('API Error:', error)
  }
}

test()
```

## Critères

- [ ] `api/client.ts` avec instance Axios
- [ ] `api/endpoints/matches.ts` avec tous endpoints
- [ ] `api/endpoints/projects.ts` avec CRUD
- [ ] Proxy Vite fonctionne (pas de CORS errors)
- [ ] Types retours Promise typés
- [ ] Interceptors pour logging

## Prochaine Étape

➡️ **Prompt 2.4** : Hooks React Query
