# 🔧 Correction des Bugs Solvers - PyCalendar

**Date**: 13 Octobre 2025  
**Problème**: Timeout et erreurs lors du lancement des solvers CP-SAT et Greedy

---

## 🐛 Bugs Identifiés

### 1. **Timeout de 10 secondes**
```
[API] Response error: timeout of 10000ms exceeded
❌ Erreur résolution: Object { message: "timeout of 10000ms exceeded", ... }
```
**Cause**: Le timeout API était fixé à 10 secondes alors que CP-SAT peut prendre plusieurs minutes

### 2. **Message d'erreur générique**
```
[API] Response error: Object { detail: "Erreur lors de la résolution : Aucune solution trouvée par le solveur" }
❌ Erreur résolution: Object { message: "Request failed with status code 400", ... }
```
**Cause**: Le message d'erreur détaillé du backend (`detail`) n'était pas affiché à l'utilisateur

---

## ✅ Corrections Appliquées

### 1. **Augmentation du Timeout API** (`api.ts`)

**Avant** :
```typescript
timeout: 10000,  // 10s timeout
```

**Après** :
```typescript
timeout: 300000,  // 5 minutes timeout (pour les solvers CP-SAT qui peuvent être longs)
```

**Impact** : Les solvers CP-SAT ont maintenant 5 minutes pour trouver une solution optimale au lieu de 10 secondes.

---

### 2. **Extraction du Message d'Erreur Backend** (`useSolver.ts`)

**Avant** :
```typescript
onError: (error) => {
  console.error('❌ Erreur résolution:', error)
},
```

**Après** :
```typescript
onError: (error: any) => {
  // Extraire le message d'erreur détaillé du backend
  const errorMessage = error.response?.data?.detail || error.message || 'Erreur inconnue'
  console.error('❌ Erreur résolution:', errorMessage)
  console.error('Détails complets:', error)
},
```

**Impact** : Les erreurs du backend (comme "Aucune solution trouvée") sont maintenant extraites et loggées correctement.

---

### 3. **Affichage Amélioré des Erreurs** (`CalendarPage.tsx`)

**Avant** :
```typescript
toast.error(
  `❌ Erreur lors de la résolution: ${(error as Error).message}`,
  { duration: 7000 }
)
```

**Après** :
```typescript
// Extraire le message d'erreur détaillé du backend
const errorMessage = error.response?.data?.detail || error.message || 'Erreur inconnue'

// Toast d'erreur avec message détaillé
toast.error(
  () => (
    <div className="flex flex-col gap-1">
      <div className="font-semibold">❌ Erreur lors de la résolution</div>
      <div className="text-sm text-gray-600">{errorMessage}</div>
      {error.response?.data?.erreurs && (
        <div className="text-xs text-red-600 mt-1">
          {error.response.data.erreurs.join(', ')}
        </div>
      )}
    </div>
  ),
  { 
    duration: 10000,
    style: {
      maxWidth: '500px',
    }
  }
)
```

**Impact** :
- Affichage du message d'erreur réel du backend
- Affichage des erreurs multiples si présentes
- Toast plus grand avec meilleure lisibilité
- Durée augmentée à 10s pour lire l'erreur

---

### 4. **Indicateur de Temps pour CP-SAT** (`CalendarPage.tsx`)

**Avant** :
```typescript
toast.loading(
  `🔄 Résolution en cours avec ${strategy === 'cpsat' ? 'CP-SAT (optimal)' : 'Greedy (rapide)'}...`,
  { duration: Infinity }
)
```

**Après** :
```typescript
toast.loading(
  `🔄 Résolution en cours avec ${strategy === 'cpsat' ? 'CP-SAT (optimal)' : 'Greedy (rapide)'}...\n${strategy === 'cpsat' ? '⏱️ Peut prendre plusieurs minutes pour les gros projets' : ''}`,
  { duration: Infinity }
)
```

**Impact** : L'utilisateur est prévenu que CP-SAT peut être long, évitant la confusion.

---

## 📊 Résultat Final

### Scénario 1 : Timeout
**Avant** : Timeout après 10s avec message générique  
**Après** : Le solver a 5 minutes pour finir + indication que c'est normal si long

### Scénario 2 : Aucune solution trouvée
**Avant** : "Request failed with status code 400"  
**Après** : "Erreur lors de la résolution : Aucune solution trouvée par le solveur" (message backend)

### Scénario 3 : Erreurs multiples
**Avant** : Message générique  
**Après** : Liste des erreurs détaillées du backend

---

## 🎯 Fichiers Modifiés

```
frontend/src/services/
└── api.ts                      ✅ Timeout 10s → 5min

frontend/src/hooks/
└── useSolver.ts                ✅ Extraction message erreur

frontend/src/pages/
└── CalendarPage.tsx            ✅ Toast amélioré + indicateur temps
```

---

## 🧪 Test des Corrections

### 1. **Tester CP-SAT avec timeout long**
```bash
cd frontend
npm run dev
```

1. Cliquer sur le bouton **CP-SAT**
2. Observer le toast : "🔄 Résolution en cours avec CP-SAT (optimal)... ⏱️ Peut prendre plusieurs minutes pour les gros projets"
3. Attendre la résolution (peut prendre >10s maintenant sans timeout)

### 2. **Tester message d'erreur détaillé**

Si le solver échoue :
- **Avant** : "Request failed with status code 400"
- **Après** : Message exact du backend (ex: "Aucune solution trouvée par le solveur")

---

## 📝 Comportement des Solvers

### CP-SAT (Optimal)
- ✅ Timeout : **5 minutes**
- ✅ Indicateur : "Peut prendre plusieurs minutes pour les gros projets"
- ✅ Erreurs détaillées affichées

### Greedy (Rapide)
- ✅ Timeout : **5 minutes** (suffisant, généralement <1s)
- ✅ Pas d'indicateur de temps (rapide)
- ✅ Erreurs détaillées affichées

---

## 🔍 Logging Amélioré

### Console Browser (Avant)
```
❌ Erreur résolution: Object { ... }
```

### Console Browser (Après)
```
❌ Erreur résolution: Erreur lors de la résolution : Aucune solution trouvée par le solveur
Détails complets: Object { response: { data: { detail: "..." } } }
```

---

## ✅ Checklist Qualité

- [x] Timeout API augmenté à 5 minutes
- [x] Messages d'erreur backend extraits
- [x] Toast erreur avec détails complets
- [x] Indicateur temps pour CP-SAT
- [x] Erreurs multiples affichées
- [x] Logging console amélioré
- [x] TypeScript strict (0 erreur)
- [x] Durée toast erreur augmentée (10s)

---

## 🚀 Prochaines Améliorations Possibles

1. **Barre de progression réelle** avec WebSocket pour feedback temps réel
2. **Timeout configurable** par stratégie (CP-SAT: 5min, Greedy: 30s)
3. **Bouton annuler** pour stopper le solver en cours
4. **Retry automatique** avec stratégie dégradée (CP-SAT → Greedy)
5. **Estimation temps** basée sur nb_matchs et historique

---

**Status** : ✅ Bugs corrigés  
**Prêt pour** : Tests avec vrais projets
