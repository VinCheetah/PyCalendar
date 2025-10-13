# 🧪 Tâche 2.8 : Guide de test - ProjectStats

## 📋 Vue d'ensemble

Ce guide présente les tests fonctionnels à effectuer pour valider le composant `ProjectStats` qui affiche les statistiques d'un projet sous forme de 4 cartes.

## 🎯 Composants à tester

- **ProjectStats** : Composant principal avec 4 cartes statistiques
- **CalendarPage** : Intégration du composant dans la page
- **useProjectStats** : Hook React Query pour fetch des stats

## ✅ Tests fonctionnels

### Test 1 : Affichage initial des statistiques

**Objectif :** Vérifier que les 4 cartes s'affichent correctement au chargement

**Pré-requis :**
- Backend lancé sur `http://localhost:8000`
- Frontend lancé sur `http://localhost:5173`
- Au moins 1 projet avec des données

**Étapes :**
1. Ouvrir `http://localhost:5173/calendar`
2. Sélectionner un projet dans le dropdown

**Résultat attendu :**
- ✅ 4 cartes s'affichent sous le sélecteur de projet
- ✅ Carte 1 (bleu) : "Équipes" avec nombre d'équipes
- ✅ Carte 2 (vert) : "Gymnases" avec nombre de gymnases
- ✅ Carte 3 (violet) : "Matchs planifiés" avec "X sur Y"
- ✅ Carte 4 (orange) : "Matchs fixés" avec "X sur Y"
- ✅ Icônes correctement affichées
- ✅ Couleurs cohérentes avec le design

### Test 2 : État de chargement (Loading)

**Objectif :** Vérifier l'affichage du skeleton lors du fetch

**Étapes :**
1. Rafraîchir la page avec DevTools Network throttling à "Slow 3G"
2. Sélectionner un projet

**Résultat attendu :**
- ✅ 4 rectangles gris animés (pulse) s'affichent
- ✅ Animation pulse visible pendant le chargement
- ✅ Les cartes apparaissent dès que les données arrivent

### Test 3 : Gestion des erreurs

**Objectif :** Vérifier l'affichage en cas d'erreur API

**Étapes :**
1. Arrêter le backend (`pkill -f uvicorn`)
2. Dans le frontend, sélectionner un projet

**Résultat attendu :**
- ✅ Message d'erreur rouge s'affiche
- ✅ Texte : "Erreur lors du chargement des statistiques"
- ✅ Fond rouge-50, bordure rouge-200
- ✅ Pas de crash de l'application

### Test 4 : Changement de projet

**Objectif :** Vérifier que les stats se mettent à jour

**Pré-requis :**
- Backend avec au moins 2 projets différents

**Étapes :**
1. Sélectionner le Projet 1
2. Noter les valeurs des 4 cartes
3. Sélectionner le Projet 2
4. Comparer les nouvelles valeurs

**Résultat attendu :**
- ✅ Les valeurs se mettent à jour instantanément
- ✅ Les stats correspondent au nouveau projet
- ✅ Pas de valeurs "fantômes" de l'ancien projet
- ✅ Animation de chargement si nécessaire

### Test 5 : Responsive design

**Objectif :** Vérifier l'adaptation mobile/tablette/desktop

**Étapes :**
1. Ouvrir DevTools (F12)
2. Passer en mode responsive (Ctrl+Shift+M)
3. Tester les breakpoints :
   - 375px (mobile)
   - 768px (tablette)
   - 1280px (desktop)

**Résultat attendu :**

**Mobile (< 640px) :**
- ✅ 1 colonne, cartes empilées verticalement
- ✅ Chaque carte prend toute la largeur

**Tablette (640-1024px) :**
- ✅ 2 colonnes, grid 2×2
- ✅ Équipes + Gymnases sur première ligne
- ✅ Matchs planifiés + Matchs fixés sur deuxième ligne

**Desktop (≥ 1024px) :**
- ✅ 4 colonnes, une seule ligne
- ✅ Toutes les cartes visibles d'un coup

### Test 6 : Animation hover

**Objectif :** Vérifier les effets au survol

**Étapes :**
1. Survoler chaque carte avec la souris

**Résultat attendu :**
- ✅ Carte s'agrandit légèrement (scale-105)
- ✅ Transition fluide
- ✅ Curseur reste "default" (pas de pointer)

### Test 7 : Affichage des sous-valeurs

**Objectif :** Vérifier les informations contextuelles

**Étapes :**
1. Sélectionner un projet avec des matchs
2. Observer les cartes "Matchs planifiés" et "Matchs fixés"

**Résultat attendu :**

**Matchs planifiés :**
- ✅ Valeur principale : nombre de matchs planifiés (ex: 45)
- ✅ Sous-valeur : "sur 60" (total de matchs)
- ✅ Texte gris plus petit en dessous

**Matchs fixés :**
- ✅ Valeur principale : nombre de matchs fixés (ex: 12)
- ✅ Sous-valeur : "sur 45" (matchs planifiés)
- ✅ Texte gris plus petit en dessous

**Équipes et Gymnases :**
- ✅ Pas de sous-valeur
- ✅ Seulement le nombre principal

### Test 8 : Intégration avec Calendar

**Objectif :** Vérifier que ProjectStats et Calendar fonctionnent ensemble

**Étapes :**
1. Sélectionner un projet
2. Comparer les stats avec le calendrier en dessous

**Résultat attendu :**
- ✅ Le nombre de matchs planifiés correspond aux matchs visibles dans le calendrier
- ✅ Le nombre de matchs fixés correspond aux matchs marqués comme fixés
- ✅ Les deux composants utilisent le même projectId
- ✅ Pas de décalage de données

## 🔍 Tests de non-régression

### Composants existants

- [ ] **ProjectSelector** : Fonctionne toujours correctement
- [ ] **Calendar** : S'affiche toujours sous les stats
- [ ] **EventDetailsModal** : S'ouvre toujours au clic sur un match
- [ ] **Drag & drop** : Fonctionne toujours pour déplacer les matchs

### Performance

- [ ] Pas de lag lors du changement de projet
- [ ] Fetch des stats ne bloque pas le reste de l'UI
- [ ] Animations fluides (60 fps)

### Console

- [ ] Aucune erreur TypeScript
- [ ] Aucun warning React
- [ ] Aucune erreur réseau (sauf si backend arrêté volontairement)

## 📊 Checklist de validation

### Avant de merger

- [ ] Tous les tests fonctionnels passent (1 à 8)
- [ ] Tests de non-régression OK
- [ ] TypeScript compile sans erreur (`npx tsc --noEmit`)
- [ ] ESLint sans warning (`npx eslint .`)
- [ ] Build de production OK (`npm run build`)
- [ ] Documentation à jour

### Tests API

Vérifier que l'endpoint backend fonctionne :

```bash
# Test 1 : Stats du projet 1
curl http://localhost:8000/api/projects/1/stats

# Résultat attendu :
{
  "nb_matchs_total": 60,
  "nb_matchs_planifies": 45,
  "nb_matchs_fixes": 12,
  "nb_matchs_a_planifier": 15,
  "nb_equipes": 12,
  "nb_gymnases": 5
}

# Test 2 : Stats du projet 2
curl http://localhost:8000/api/projects/2/stats

# Vérifier que les valeurs diffèrent du projet 1
```

## 🐛 Cas limites à tester

### Cas 1 : Projet sans matchs
**Setup :** Créer un projet vide
**Résultat attendu :**
- nb_matchs_total = 0
- nb_matchs_planifies = 0
- nb_matchs_fixes = 0
- "0 sur 0" affiché correctement

### Cas 2 : Projet avec 0 équipes
**Setup :** Projet sans équipes configurées
**Résultat attendu :**
- Carte "Équipes" affiche 0
- Pas de crash

### Cas 3 : Tous les matchs planifiés
**Setup :** Projet où nb_matchs_planifies === nb_matchs_total
**Résultat attendu :**
- "60 sur 60" affiché
- Indicateur visuel que tout est planifié

### Cas 4 : Tous les matchs fixés
**Setup :** Projet où nb_matchs_fixes === nb_matchs_planifies
**Résultat attendu :**
- "45 sur 45" affiché
- Indicateur visuel que tout est fixé

### Cas 5 : Désélection du projet
**Setup :** Sélectionner un projet puis sélectionner "Aucun projet" (si option existe)
**Résultat attendu :**
- Les stats disparaissent
- Pas d'erreur console
- Message "Veuillez sélectionner un projet" s'affiche

## 📝 Template de rapport de test

```markdown
# Test ProjectStats - [Date]

## Environnement
- Node: v18.19.1
- Backend: http://localhost:8000
- Frontend: http://localhost:5173
- Navigateur: Chrome 120

## Tests fonctionnels

| Test | Statut | Commentaire |
|------|--------|-------------|
| Test 1 : Affichage initial | ✅ | OK |
| Test 2 : Loading skeleton | ✅ | OK |
| Test 3 : Gestion erreurs | ✅ | OK |
| Test 4 : Changement projet | ✅ | OK |
| Test 5 : Responsive | ✅ | OK |
| Test 6 : Hover animation | ✅ | OK |
| Test 7 : Sous-valeurs | ✅ | OK |
| Test 8 : Intégration Calendar | ✅ | OK |

## Non-régression

| Composant | Statut | Commentaire |
|-----------|--------|-------------|
| ProjectSelector | ✅ | OK |
| Calendar | ✅ | OK |
| EventDetailsModal | ✅ | OK |
| Drag & drop | ✅ | OK |

## Cas limites

| Cas | Statut | Commentaire |
|-----|--------|-------------|
| Projet sans matchs | ✅ | Affiche "0 sur 0" |
| Projet 0 équipes | ✅ | Affiche 0 |
| Tous matchs planifiés | ✅ | "60 sur 60" OK |
| Tous matchs fixés | ✅ | "45 sur 45" OK |

## Bugs trouvés

Aucun bug détecté ✅

## Conclusion

✅ Tâche 2.8 validée, prête pour merge
```

## 🔧 Commandes utiles pour les tests

```bash
# Lancer le backend
cd backend
uvicorn app.main:app --reload

# Lancer le frontend
cd frontend
npm run dev

# Tests TypeScript
npx tsc --noEmit

# Tests ESLint
npx eslint .

# Build de production
npm run build

# Preview du build
npm run preview
```

## 🎨 Captures d'écran recommandées

Pour la documentation :

1. **Desktop** : Vue complète avec les 4 cartes en ligne
2. **Tablette** : Grid 2×2
3. **Mobile** : Cartes empilées
4. **Loading** : Skeleton animé
5. **Error** : Message d'erreur
6. **Hover** : Animation scale

---

**Guide créé le :** 2025
**Composant testé :** ProjectStats
**Statut :** ✅ Prêt pour tests manuels
