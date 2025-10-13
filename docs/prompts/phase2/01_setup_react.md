# PROMPT 2.1 : Setup Projet React avec Vite

## Contexte Projet

**PyCalendar V2** : Interface web React pour visualiser et éditer calendriers. Frontend communique avec API FastAPI via Axios.

## État Actuel

- ✅ Phase 1 complète : Backend API fonctionnel
- ⏳ Phase 2 : Frontend React

## Objectif

Initialiser projet React TypeScript avec :
- **Vite** bundler
- **TanStack Query** data fetching
- **FullCalendar** affichage calendrier
- **Axios** HTTP client
- **React Router** navigation

**Durée** : 30 min

## Instructions

### 1. Créer Projet Vite

```bash
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
```

### 2. Installer Dépendances

```bash
# State management & data fetching
npm install @tanstack/react-query axios zustand

# Calendrier
npm install @fullcalendar/react @fullcalendar/daygrid @fullcalendar/timegrid @fullcalendar/interaction

# Routing
npm install react-router-dom

# UI (optionnel)
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

### 3. Configurer Vite

**Fichier** : `frontend/vite.config.ts`

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

### 4. Configurer Tailwind (optionnel)

**Fichier** : `frontend/tailwind.config.js`

```javascript
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

**Fichier** : `frontend/src/index.css`

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

### 5. Structure Dossiers

```bash
mkdir -p src/api/endpoints
mkdir -p src/components/calendar
mkdir -p src/components/ui
mkdir -p src/hooks
mkdir -p src/pages
mkdir -p src/types
mkdir -p src/utils
```

## Validation

```bash
cd frontend
npm run dev
```

**Attendu** :
- Server sur http://localhost:5173
- Page React par défaut
- Hot reload fonctionne

### Test Proxy API

```bash
# Backend doit tourner (port 8000)
curl http://localhost:5173/api/health
```

**Attendu** : Réponse `{"status":"healthy"}` (proxé depuis backend)

## Critères de Réussite

- [ ] Projet Vite créé dans dossier `frontend/`
- [ ] Dépendances installées
- [ ] `vite.config.ts` avec alias `@` et proxy `/api`
- [ ] Structure dossiers créée
- [ ] `npm run dev` démarre sur :5173
- [ ] Proxy API fonctionne

## Prochaine Étape

➡️ **Prompt 2.2** : Définir types TypeScript
