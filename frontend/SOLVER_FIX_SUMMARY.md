# 🔧 Correction des Bugs Solvers - Résumé

## 🎯 Problèmes Corrigés

### Bug #1 : Timeout après 10 secondes ⏱️

**Erreur originale** :
```
[API] Response error: timeout of 10000ms exceeded
❌ Erreur résolution: timeout of 10000ms exceeded
```

**Solution** : Augmentation timeout **10s → 5 minutes**

```diff
// frontend/src/services/api.ts

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
- timeout: 10000,  // 10s timeout
+ timeout: 300000,  // 5 minutes timeout (pour les solvers CP-SAT)
})
```

---

### Bug #2 : Message d'erreur générique 💬

**Erreur originale** :
```
❌ Erreur résolution: Request failed with status code 400
```

**Message réel du backend** (caché) :
```
"Erreur lors de la résolution : Aucune solution trouvée par le solveur"
```

**Solution #1** : Extraction dans `useSolver.ts`

```diff
// frontend/src/hooks/useSolver.ts

- onError: (error) => {
-   console.error('❌ Erreur résolution:', error)
- },
+ onError: (error: any) => {
+   const errorMessage = error.response?.data?.detail || error.message || 'Erreur inconnue'
+   console.error('❌ Erreur résolution:', errorMessage)
+   console.error('Détails complets:', error)
+ },
```

**Solution #2** : Toast amélioré dans `CalendarPage.tsx`

```diff
// frontend/src/pages/CalendarPage.tsx

  } catch (error: any) {
    toast.dismiss(loadingToast)
    
+   const errorMessage = error.response?.data?.detail || error.message || 'Erreur inconnue'
    
    toast.error(
-     `❌ Erreur lors de la résolution: ${(error as Error).message}`,
-     { duration: 7000 }
+     () => (
+       <div className="flex flex-col gap-1">
+         <div className="font-semibold">❌ Erreur lors de la résolution</div>
+         <div className="text-sm text-gray-600">{errorMessage}</div>
+         {error.response?.data?.erreurs && (
+           <div className="text-xs text-red-600 mt-1">
+             {error.response.data.erreurs.join(', ')}
+           </div>
+         )}
+       </div>
+     ),
+     { duration: 10000, style: { maxWidth: '500px' } }
    )
  }
```

---

### Bug #3 : Pas d'indication de temps pour CP-SAT ⏳

**Solution** : Indicateur ajouté au toast de chargement

```diff
// frontend/src/pages/CalendarPage.tsx

  const loadingToast = toast.loading(
-   `🔄 Résolution en cours avec ${strategy === 'cpsat' ? 'CP-SAT (optimal)' : 'Greedy (rapide)'}...`,
+   `🔄 Résolution en cours avec ${strategy === 'cpsat' ? 'CP-SAT (optimal)' : 'Greedy (rapide)'}...\n${strategy === 'cpsat' ? '⏱️ Peut prendre plusieurs minutes pour les gros projets' : ''}`,
    { duration: Infinity }
  )
```

---

## 📊 Avant / Après

### Scénario 1 : Solver CP-SAT long (>10s)

**AVANT** ❌
```
🔄 Résolution en cours avec CP-SAT (optimal)...
[Attend 10s]
❌ timeout of 10000ms exceeded
```

**APRÈS** ✅
```
🔄 Résolution en cours avec CP-SAT (optimal)...
⏱️ Peut prendre plusieurs minutes pour les gros projets
[Attend jusqu'à 5 minutes]
✅ Résolution terminée ! 145/145 matchs planifiés
```

---

### Scénario 2 : Aucune solution trouvée

**AVANT** ❌
```
❌ Erreur lors de la résolution: Request failed with status code 400
```

**APRÈS** ✅
```
❌ Erreur lors de la résolution
Erreur lors de la résolution : Aucune solution trouvée par le solveur
```

---

### Scénario 3 : Erreurs multiples

**AVANT** ❌
```
❌ Erreur lors de la résolution: Request failed with status code 400
```

**APRÈS** ✅
```
❌ Erreur lors de la résolution
Conflit d'horaire détecté
Gymnase non disponible le mercredi, Équipe absente semaine 3
```

---

## ✅ Checklist

- [x] Timeout API 10s → 5min
- [x] Messages d'erreur backend extraits et affichés
- [x] Toast erreur agrandi (500px) et durée 10s
- [x] Erreurs multiples listées
- [x] Indicateur CP-SAT "peut prendre plusieurs minutes"
- [x] Logging console amélioré
- [x] TypeScript 0 erreur

---

## 🚀 Impact

**CP-SAT** :
- ✅ Ne timeout plus après 10s
- ✅ A 5 minutes pour trouver la solution optimale
- ✅ Indicateur clair pour l'utilisateur

**Greedy** :
- ✅ Même timeout (5min, largement suffisant pour <1s)
- ✅ Messages d'erreur clairs

**UX** :
- ✅ Messages d'erreur compréhensibles
- ✅ Toast plus lisible et détaillé
- ✅ Utilisateur informé des temps d'attente

---

## 📂 Fichiers Modifiés

```
frontend/src/
├── services/
│   └── api.ts                  ✅ timeout 300000ms
├── hooks/
│   └── useSolver.ts            ✅ extraction erreur
└── pages/
    └── CalendarPage.tsx        ✅ toast amélioré + indicateur
```

---

## 🧪 Test

```bash
cd frontend
npm run dev
```

1. **Tester CP-SAT** avec gros projet (>100 matchs)
   - Voir toast avec indicateur de temps
   - Pas de timeout après 10s
   - Résolution complète

2. **Tester erreur** (projet impossible)
   - Message détaillé du backend
   - Pas de "Request failed with status code 400"
   - Erreurs multiples listées

---

**Documentation** : `SOLVER_BUGS_FIX.md`
