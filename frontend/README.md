# Frontend PyCalendar V2# React + TypeScript + Vite



Application web React pour la gestion et l'optimisation de calendriers sportifs.This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.



## 🚀 Quick StartCurrently, two official plugins are available:



```bash- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) (or [oxc](https://oxc.rs) when used in [rolldown-vite](https://vite.dev/guide/rolldown)) for Fast Refresh

# Installer les dépendances- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

npm install

## React Compiler

# Démarrer le serveur de développement

nvm use 22  # Utiliser Node.js 22+The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

npm run dev

## Expanding the ESLint configuration

# Ouvrir http://localhost:5173

```If you are developing a production application, we recommend updating the configuration to enable type-aware lint rules:



## 📁 Structure```js

export default defineConfig([

```  globalIgnores(['dist']),

src/  {

├── assets/           # Images, styles    files: ['**/*.{ts,tsx}'],

├── components/       # Composants React    extends: [

│   ├── Calendar/     # Composant calendrier      // Other configs...

│   ├── Project/      # Gestion projets

│   └── Layout/       # Layout (Header, Sidebar)      // Remove tseslint.configs.recommended and replace with this

├── hooks/            # Custom hooks React Query      tseslint.configs.recommendedTypeChecked,

├── services/         # API clients Axios      // Alternatively, use this for stricter rules

├── types/            # Interfaces TypeScript      tseslint.configs.strictTypeChecked,

├── utils/            # Fonctions utilitaires      // Optionally, add this for stylistic rules

├── App.tsx           # Routing      tseslint.configs.stylisticTypeChecked,

└── main.tsx          # Point d'entrée + React Query

```      // Other configs...

    ],

## 🛠️ Stack Technique    languageOptions: {

      parserOptions: {

- **React 18** + **TypeScript**        project: ['./tsconfig.node.json', './tsconfig.app.json'],

- **Vite 7** - Build tool ultra-rapide        tsconfigRootDir: import.meta.dirname,

- **React Router 6** - Routing      },

- **React Query** - Data fetching & cache      // other options...

- **Axios** - HTTP client    },

- **FullCalendar** - Calendrier interactif  },

- **Tailwind CSS v4** - Framework CSS])

```

## 🔗 Configuration

You can also install [eslint-plugin-react-x](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-x) and [eslint-plugin-react-dom](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-dom) for React-specific lint rules:

### Proxy API

```js

Le proxy Vite redirige `/api/*` vers le backend FastAPI (`http://localhost:8000`).// eslint.config.js

import reactX from 'eslint-plugin-react-x'

### Path Aliasesimport reactDom from 'eslint-plugin-react-dom'



Usage :export default defineConfig([

```typescript  globalIgnores(['dist']),

import api from '@services/api'  {

import { useProjects } from '@hooks/useProjects'    files: ['**/*.{ts,tsx}'],

```    extends: [

      // Other configs...

## 🧪 Commandes      // Enable lint rules for React

      reactX.configs['recommended-typescript'],

```bash      // Enable lint rules for React DOM

npm run dev      # Dev server      reactDom.configs.recommended,

npm run build    # Build production    ],

npm run preview  # Preview build    languageOptions: {

npm run lint     # Linter      parserOptions: {

```        project: ['./tsconfig.node.json', './tsconfig.app.json'],

        tsconfigRootDir: import.meta.dirname,

## 📡 API Client      },

      // other options...

Exemple :    },

```typescript  },

// services/projectsApi.ts])

export const projectsApi = {```

  getAll: () => api.get<Project[]>('/projects'),
}

// hooks/useProjects.ts
export const useProjects = () => {
  return useQuery({
    queryKey: ['projects'],
    queryFn: () => projectsApi.getAll(),
  })
}
```

## 🚦 Routes

- `/` → `/calendar`
- `/calendar` → Page calendrier
- `/projects` → Gestion projets
- `/stats` → Statistiques

## 🐛 Debug

- **React Query DevTools** : Panneau bas gauche
- **Logs API** : Console navigateur

---

**Version** : 2.0.0
