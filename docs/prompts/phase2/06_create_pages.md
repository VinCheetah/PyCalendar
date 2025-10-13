# PROMPT 2.6 : Page Principale Calendrier

## Contexte

**PyCalendar V2** : Assembler composants dans page fonctionnelle.

## État

- ✅ Composant Calendar
- ⏳ Page complète

## Objectif

Page CalendarPage intégrant Calendar + hooks + gestion erreurs.

**Durée** : 30 min

## Instructions

### Page Calendar

**Fichier** : `frontend/src/pages/CalendarPage.tsx`

```typescript
import { useState } from 'react'
import { Calendar } from '@/components/calendar/Calendar'
import { useMatches, useMoveMatch, useFixMatch, useUnfixMatch } from '@/hooks/useMatches'
import type { Match, MatchMove } from '@/types'

export function CalendarPage() {
  // TODO Phase 3: sélection dynamique
  const [selectedProjectId] = useState(1)
  
  const { data: matches, isLoading, error } = useMatches(selectedProjectId)
  const moveMatch = useMoveMatch()
  const fixMatch = useFixMatch()
  const unfixMatch = useUnfixMatch()
  
  const handleMatchDrop = async (matchId: number, creneau: MatchMove) => {
    try {
      await moveMatch.mutateAsync({ id: matchId, creneau })
      console.log('✅ Match déplacé')
    } catch (error) {
      console.error('❌ Erreur déplacement:', error)
      alert('Impossible de déplacer le match')
    }
  }
  
  const handleMatchClick = (match: Match) => {
    console.log('Match cliqué:', match)
    // TODO Phase 4: Modal détails match
  }
  
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-xl">Chargement du calendrier...</div>
      </div>
    )
  }
  
  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-xl text-red-500">
          Erreur chargement : {(error as Error).message}
        </div>
      </div>
    )
  }
  
  return (
    <div className="container mx-auto p-4">
      <header className="mb-6">
        <h1 className="text-3xl font-bold">Calendrier Sportif</h1>
        <p className="text-gray-600">
          Projet ID: {selectedProjectId} | {matches?.length || 0} matchs
        </p>
      </header>
      
      <div className="bg-white rounded-lg shadow p-4">
        {matches && (
          <Calendar
            matches={matches}
            onMatchDrop={handleMatchDrop}
            onMatchClick={handleMatchClick}
          />
        )}
      </div>
      
      <footer className="mt-4 text-sm text-gray-500">
        <p>🔴 Rouge = Fixé | 🔵 Bleu = Normal | 🟢 Vert = Terminé</p>
      </footer>
    </div>
  )
}
```

### App Router

**Fichier** : `frontend/src/App.tsx`

```typescript
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { CalendarPage } from './pages/CalendarPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<CalendarPage />} />
        {/* Phase 3+: Routes projects, stats, etc. */}
      </Routes>
    </BrowserRouter>
  )
}
```

## Validation

### 1. Backend Running

```bash
# Terminal 1
uvicorn backend.api.main:app --reload
```

### 2. Import Data

```bash
# Terminal 2
python scripts/init_db.py
python scripts/import_excel.py configs/config_volley.yaml "Test"
```

### 3. Frontend

```bash
# Terminal 3
cd frontend
npm run dev
```

### 4. Test Interface

Ouvrir http://localhost:5173

**Vérifier** :
- [ ] Calendrier s'affiche
- [ ] Matchs visibles aux bons créneaux
- [ ] Matchs fixes rouges, normaux bleus
- [ ] Drag & drop fonctionne pour matchs non fixés
- [ ] Drag & drop bloqué pour matchs fixés
- [ ] Console log après drop réussi
- [ ] Alert si erreur

## Critères

- [ ] CalendarPage affiche Calendar
- [ ] Loading state
- [ ] Error state
- [ ] Handler handleMatchDrop avec try/catch
- [ ] Router avec route /
- [ ] Interface complète fonctionnelle

## Phase 2 Complète !

✅ Frontend Foundation terminé :
- React + Vite setup
- Types TypeScript
- API client + hooks
- Calendrier drag & drop
- Page complète

➡️ **Phase 3** : Intégration Solver
