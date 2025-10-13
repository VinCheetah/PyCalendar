# PROMPT 2.2 : Définir Types TypeScript

## Contexte Projet

**PyCalendar V2 Frontend** : Types TypeScript mirrorant schemas Pydantic backend pour type-safety.

## État Actuel

- ✅ React project setup
- ⏳ Définir types API

## Objectif

Types TypeScript pour Match, Project, Team, Venue = schemas Pydantic backend.

**Durée** : 20 min

## Instructions

### Types Match

**Fichier** : `frontend/src/types/match.ts`

```typescript
export type MatchStatus = 'a_planifier' | 'planifie' | 'fixe' | 'termine' | 'annule'

export interface Match {
  id: number
  project_id: number
  
  equipe1_nom: string
  equipe1_institution: string
  equipe1_genre: string
  equipe2_nom: string
  equipe2_institution: string
  equipe2_genre: string
  
  poule: string
  
  semaine: number | null
  horaire: string | null
  gymnase: string | null
  
  est_fixe: boolean
  statut: MatchStatus
  priorite: number
  
  score_equipe1: number | null
  score_equipe2: number | null
  notes: string
  
  created_at: string
  updated_at: string | null
}

export interface MatchUpdate {
  semaine?: number
  horaire?: string
  gymnase?: string
  est_fixe?: boolean
  statut?: MatchStatus
  score_equipe1?: number
  score_equipe2?: number
  notes?: string
}

export interface MatchMove {
  semaine: number
  horaire: string
  gymnase: string
}
```

### Types Project

**Fichier** : `frontend/src/types/project.ts`

```typescript
export interface Project {
  id: number
  nom: string
  sport: string
  config_yaml_path: string | null
  nb_semaines: number
  semaine_min: number
  created_at: string
  updated_at: string | null
}

export interface ProjectUpdate {
  nom?: string
  nb_semaines?: number
  semaine_min?: number
}
```

### Types Team & Venue

**Fichier** : `frontend/src/types/team.ts`

```typescript
export interface Team {
  id: number
  project_id: number
  nom: string
  institution: string | null
  numero_equipe: string | null
  genre: string | null
  poule: string
  horaires_preferes: string[] | null
  lieux_preferes: string[] | null
  created_at: string
}
```

**Fichier** : `frontend/src/types/venue.ts`

```typescript
export interface Venue {
  id: number
  project_id: number
  nom: string
  capacite: number
  horaires_disponibles: string[] | null
  created_at: string
}
```

### Index

**Fichier** : `frontend/src/types/index.ts`

```typescript
export * from './match'
export * from './project'
export * from './team'
export * from './venue'
```

## Validation

```typescript
// Test compilation
import type { Match, MatchStatus, MatchMove } from '@/types'

const match: Match = {
  id: 1,
  project_id: 1,
  equipe1_nom: "A",
  equipe1_institution: "",
  equipe1_genre: "M",
  equipe2_nom: "B",
  equipe2_institution: "",
  equipe2_genre: "M",
  poule: "P1",
  semaine: 3,
  horaire: "14:00",
  gymnase: "Gym A",
  est_fixe: false,
  statut: "planifie",
  priorite: 0,
  score_equipe1: null,
  score_equipe2: null,
  notes: "",
  created_at: new Date().toISOString(),
  updated_at: null
}

// Type checking
const status: MatchStatus = "planifie" // ✅
// const invalid: MatchStatus = "invalid" // ❌ Error
```

## Critères de Réussite

- [ ] 4 fichiers types (match, project, team, venue)
- [ ] Union type `MatchStatus`
- [ ] Interfaces correspondent aux schemas Pydantic
- [ ] Timestamps en `string` (ISO format)
- [ ] Arrays JSON en `string[] | null`
- [ ] Compilation TypeScript sans erreur

## Prochaine Étape

➡️ **Prompt 2.3** : Créer API client Axios
