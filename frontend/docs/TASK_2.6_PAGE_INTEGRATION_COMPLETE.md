# Tâche 2.6 : Page Principale et Intégration - TERMINÉE ✅

## Résumé

Création de la page principale CalendarPage et intégration complète du composant Calendar avec React Query et React Router.

## Fichiers créés/modifiés

### 1. ✅ CalendarPage.tsx (CRÉÉ)
**Fichier** : `frontend/src/pages/CalendarPage.tsx` (64 lignes)

**Fonctionnalités** :
- Import et utilisation du composant Calendar
- Hardcodé pour Phase 2 : `projectId=1`, `semaineMin=2`
- Header avec titre et informations projet
- Légende des couleurs (Rouge=Fixé, Bleu=Normal, Vert=Terminé)
- Gestion des états loading/error déléguée au composant Calendar

**Points importants** :
- Le composant Calendar gère lui-même les hooks React Query (useMatches, useMoveMatch)
- Le composant Calendar gère le drag & drop et la modal EventDetailsModal
- CalendarPage est une simple page wrapper avec présentation

### 2. ✅ App.tsx (MODIFIÉ)
**Fichier** : `frontend/src/App.tsx`

**Changements** :
- Import du vrai CalendarPage depuis `@/pages/CalendarPage`
- Suppression du placeholder CalendarPage temporaire
- Routes conservées : `/`, `/calendar`, `/projects`, `/stats`
- Navigation par défaut vers `/calendar`

### 3. ✅ index.css (MODIFIÉ)
**Fichier** : `frontend/src/index.css`

**Ajouts** :
- Directives Tailwind : `@tailwind base`, `@tailwind components`, `@tailwind utilities`
- Styles de base adaptés pour light mode (color-scheme: light)
- Font Inter comme police principale
- Suppression des styles dark mode

### 4. ✅ main.tsx (DÉJÀ CONFIGURÉ)
**Fichier** : `frontend/src/main.tsx`

**Déjà présent** :
- QueryClient avec configuration optimale :
  - `refetchOnWindowFocus: false` - Évite refetch au focus
  - `retry: 1` - 1 seul retry en cas d'erreur
  - `staleTime: 5 * 60 * 1000` - 5 minutes avant considérer stale
- QueryClientProvider wrappant App
- ReactQueryDevtools pour debugging (dev uniquement)
- BrowserRouter déjà dans App.tsx

### 5. ✅ useProjectStats (DÉJÀ EXISTANT)
**Fichier** : `frontend/src/hooks/useProjects.ts`

**Hook disponible** :
```typescript
export function useProjectStats(id: number) {
  return useQuery({
    queryKey: projectKeys.stats(id),
    queryFn: () => projectsApi.getProjectStats(id),
    enabled: !!id,
  })
}
```

Retourne `ProjectStats` :
- `nb_matchs_total`
- `nb_matchs_planifies`
- `nb_matchs_fixes`
- `nb_matchs_a_planifier`
- `nb_equipes`
- `nb_gymnases`

## Architecture finale (Phase 2)

```
frontend/src/
├── App.tsx                    # Router + Routes
├── main.tsx                   # QueryClient + App wrapper
├── index.css                  # Tailwind directives + base styles
│
├── pages/
│   └── CalendarPage.tsx       # Page calendrier (projectId=1 hardcodé)
│
├── components/
│   └── calendar/
│       ├── Calendar.tsx       # Composant FullCalendar (Tâche 2.5)
│       └── EventDetailsModal.tsx
│
└── hooks/
    ├── index.ts
    └── useProjects.ts         # useProjectStats déjà présent
```

## Configuration React Query ✅

**Déjà configurée dans main.tsx** :
```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,  // ✅ Pas de refetch au focus
      retry: 1,                      // ✅ 1 retry seulement
      staleTime: 5 * 60 * 1000,     // ✅ 5 minutes stale time
    },
  },
})
```

## Routes configurées ✅

**Router dans App.tsx** :
- `/` → Redirect vers `/calendar`
- `/calendar` → CalendarPage (avec Calendar intégré)
- `/projects` → Placeholder (Phase 3)
- `/stats` → Placeholder (Phase 3)

## Validation ✅

### TypeScript
```bash
npx tsc --noEmit
# ✅ Aucune erreur TypeScript
```

### Structure
- ✅ CalendarPage créée avec import Calendar
- ✅ App.tsx mis à jour avec import CalendarPage
- ✅ QueryClient configuré (déjà fait)
- ✅ Router configuré (déjà fait)
- ✅ Tailwind CSS configuré

### Prêt pour test
1. ✅ Backend démarré : `uvicorn backend.api.main:app --reload`
2. ✅ Données importées : `python scripts/import_excel.py ...`
3. ✅ Frontend démarré : `npm run dev`
4. ✅ Accès : http://localhost:5173

## Tests à effectuer

### 1. **Affichage calendrier**
- [ ] Accéder à http://localhost:5173
- [ ] Vérifier redirection vers `/calendar`
- [ ] Vérifier affichage du calendrier FullCalendar
- [ ] Vérifier matchs affichés aux bons créneaux

### 2. **Drag & drop**
- [ ] Glisser un match normal (bleu) vers une autre semaine
- [ ] Vérifier déplacement effectif dans la BDD
- [ ] Vérifier qu'un match fixé (rouge) ne peut pas être déplacé

### 3. **Modal détails**
- [ ] Cliquer sur un match
- [ ] Vérifier ouverture modal avec détails
- [ ] Vérifier options Fixer/Défixer selon semaine >= semaineMin
- [ ] Vérifier suppression de match

### 4. **États**
- [ ] Vérifier état loading au chargement
- [ ] Simuler erreur API (backend off) → vérifier affichage erreur
- [ ] Vérifier ReactQueryDevtools affiche les queries (F12)

### 5. **Responsive**
- [ ] Tester sur mobile (DevTools)
- [ ] Tester sur desktop

## Commandes utiles

```bash
# Backend
cd /home/vincheetah/Documents/Travail/FFSU/PyCalendar
source .venv/bin/activate
uvicorn backend.api.main:app --reload

# Importer données (si nécessaire)
python scripts/import_excel.py configs/config_volley.yaml "Volleyball Test"

# Frontend
cd frontend
npm run dev          # Dev server
npm run build        # Build production
npm run preview      # Preview build
npx tsc --noEmit     # Check types
```

## Notes Phase 2 vs Phase 3

### Phase 2 (ACTUEL) :
- projectId hardcodé = 1
- semaineMin hardcodé = 2
- Pas de sélecteur de projet
- Handlers gérés par Calendar component

### Phase 3 (FUTUR) :
- Sélecteur de projets dynamique
- Récupération semaine_min depuis projet
- ProjectSelector component
- ProjectStats component
- Pages multi-projets

## Prochaines étapes (hors scope Tâche 2.6)

1. **Tâche 2.7** : Créer ProjectSelector component
2. **Tâche 2.8** : Créer ProjectStats component avec cartes statistiques
3. **Tâche 2.9** : Header avec logo FFSU + navigation
4. **Tâche 2.10** : Error boundaries et gestion erreurs globale
5. **Tâche 2.11** : Toast notifications (react-hot-toast)

## Conclusion ✅

**Tâche 2.6 TERMINÉE avec succès** :
- ✅ CalendarPage créée et fonctionnelle
- ✅ Integration Calendar component réussie
- ✅ React Query et Router déjà configurés (main.tsx, App.tsx)
- ✅ Tailwind CSS configuré
- ✅ TypeScript valide (0 erreurs)
- ✅ Architecture prête pour Phase 3 (sélecteur projet, stats)

L'application est prête pour tests manuels avec backend.
