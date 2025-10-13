# Note Technique : Version Node.js

## Problème rencontré

Lors du test de l'application frontend, une erreur de version Node.js a été détectée :

```
You are using Node.js 18.19.1. Vite requires Node.js version 20.19+ or 22.12+.
Please upgrade your Node.js version.
```

## Cause

Le package.json utilise **Vite 7.1.7** qui requiert **Node.js 20.19+** ou **22.12+**.
Le système actuel utilise **Node.js 18.19.1**.

## Solutions possibles

### Solution 1 : Upgrade Node.js (RECOMMANDÉ)
Installer Node.js 20+ ou 22+ via nvm, fnm, ou directement depuis nodejs.org

```bash
# Avec nvm (si disponible)
nvm install 20
nvm use 20

# Avec fnm (si disponible)
fnm install 20
fnm use 20

# Ou télécharger depuis https://nodejs.org/
```

### Solution 2 : Downgrade Vite (NON RECOMMANDÉ)
Modifier package.json pour utiliser Vite 5.x compatible Node 18 :

```bash
cd frontend
npm install vite@^5.4.11 --save-dev
```

⚠️ **Attention** : Vite 5.x peut ne pas supporter toutes les features de Vite 7 (notamment certains plugins Tailwind 4+).

### Solution 3 : Utiliser .nvmrc
Créer un fichier `.nvmrc` dans `frontend/` :

```bash
echo "20" > frontend/.nvmrc
# Puis : nvm use (si nvm installé)
```

## Impact

### Code ✅ VALIDE
- Tous les fichiers TypeScript sont corrects (0 erreurs)
- L'architecture est complète
- Les imports et configurations sont bons

### Tests ⏸️ EN ATTENTE
- L'application ne peut pas être lancée avec Node 18
- Tests manuels nécessitent Node 20+

## Action immédiate

**Pour continuer les tests** :
1. Installer Node.js 20+ ou 22+
2. Relancer `npm install` dans `frontend/`
3. Lancer `npm run dev`

## État actuel Tâche 2.6

- ✅ CalendarPage créée
- ✅ App.tsx configuré
- ✅ Tailwind CSS configuré
- ✅ TypeScript validé (0 erreurs)
- ✅ React Query configuré
- ✅ Router configuré
- ⏸️ Tests manuels en attente (Node 20+ requis)

**Tâche 2.6 : Code complet et valide, prêt pour tests avec Node 20+**
