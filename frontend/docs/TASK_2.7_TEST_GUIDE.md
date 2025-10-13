# Guide de Test - Tâche 2.7 : ProjectSelector

## 🎯 Objectif du Test

Valider que le composant **ProjectSelector** fonctionne correctement et permet la sélection dynamique de projets.

---

## 📋 Prérequis

### 1. Backend Opérationnel

```bash
cd /home/vincheetah/Documents/Travail/FFSU/PyCalendar
source .venv/bin/activate
uvicorn backend.api.main:app --reload
```

**Vérification** :
```bash
curl http://localhost:8000/health
# Attendu: {"status":"ok"}
```

### 2. Frontend Démarré

```bash
cd /home/vincheetah/Documents/Travail/FFSU/PyCalendar/frontend
npm run dev
```

**Accès** : http://localhost:5173 (ou 5174)

### 3. Données de Test

Vérifier qu'il y a au moins 2 projets dans la base :

```bash
curl http://localhost:8000/api/projects | jq '.[] | {id, nom, sport}'
```

Si pas assez de projets, créer un projet de test :
```bash
curl -X POST http://localhost:8000/api/projects \
  -H "Content-Type: application/json" \
  -d '{
    "nom": "Projet Test Volley",
    "sport": "Volleyball",
    "nb_semaines": 20,
    "semaine_min": 1
  }'
```

---

## ✅ Tests Fonctionnels

### Test 1 : Affichage Initial

**Action** : Charger la page `/calendar`

**Vérifications** :
- [ ] Le sélecteur de projet s'affiche avec "Projet 1" sélectionné par défaut
- [ ] Les métadonnées du projet apparaissent sous le dropdown :
  - Sport (ex: "Volleyball")
  - Semaines (ex: "26 semaines (min: 2)")
  - Config YAML path si disponible
- [ ] Le calendrier charge les matchs du projet 1
- [ ] La légende des couleurs s'affiche en bas

**Résultat attendu** : ✅ Affichage correct avec projet 1 sélectionné

---

### Test 2 : Ouverture du Dropdown

**Action** : Cliquer sur le sélecteur de projet

**Vérifications** :
- [ ] Le dropdown s'ouvre avec une animation fluide
- [ ] La liste des projets s'affiche
- [ ] Chaque projet montre :
  - ✓ Nom en gras pour le projet sélectionné
  - Sport et nombre de semaines (ex: "Volleyball • 26 semaines")
  - Nom du fichier config si disponible (ex: "📄 config_volley.yaml")
  - Nombre d'équipes et gymnases si disponible (ex: "👥 12 équipes 🏟️ 5 gymnases")
- [ ] L'icône ✓ (CheckIcon) apparaît à gauche du projet sélectionné
- [ ] Le hover met en surbrillance les options (fond bleu clair)

**Résultat attendu** : ✅ Dropdown fonctionnel avec toutes les informations

---

### Test 3 : Changement de Projet

**Action** : Cliquer sur un autre projet dans la liste

**Vérifications** :
- [ ] Le dropdown se ferme
- [ ] Le nom du nouveau projet apparaît dans le sélecteur
- [ ] Les métadonnées se mettent à jour sous le dropdown
- [ ] Le calendrier se rafraîchit automatiquement
- [ ] Les matchs du nouveau projet s'affichent
- [ ] L'icône ✓ se déplace vers le nouveau projet si on rouvre le dropdown

**Résultat attendu** : ✅ Changement de projet fluide, calendrier mis à jour

---

### Test 4 : États de Chargement

**Action** : Recharger la page et observer l'état initial

**Vérifications** :
- [ ] Pendant le chargement des projets :
  - Skeleton loader animé s'affiche (rectangle gris pulsant)
- [ ] Une fois chargé :
  - Le sélecteur normal apparaît avec le projet par défaut

**Résultat attendu** : ✅ Loading state visible pendant chargement

---

### Test 5 : Gestion des Erreurs

**Action** : Arrêter le backend, recharger la page

```bash
# Arrêter le backend (Ctrl+C dans le terminal backend)
```

**Vérifications** :
- [ ] Message d'erreur s'affiche : "Erreur lors du chargement des projets"
- [ ] Le message est en rouge sur fond rouge clair
- [ ] Le calendrier affiche aussi une erreur

**Résultat attendu** : ✅ Gestion d'erreur claire et visible

**Action** : Redémarrer le backend

```bash
uvicorn backend.api.main:app --reload
```

---

### Test 6 : Cas Aucun Projet

**Action** : Vider temporairement la base de projets (si possible en dev)

**Vérifications** :
- [ ] Message s'affiche : "Aucun projet disponible"
- [ ] Le message est en gris sur fond gris clair
- [ ] Le calendrier affiche le message de sélection

**Résultat attendu** : ✅ Cas vide géré correctement

---

### Test 7 : Accessibilité

**Action** : Navigation au clavier

**Vérifications** :
- [ ] Tab permet de focus le sélecteur
- [ ] Un ring bleu visible apparaît au focus
- [ ] Enter/Space ouvre le dropdown
- [ ] Flèches haut/bas naviguent dans les options
- [ ] Enter sélectionne une option
- [ ] Escape ferme le dropdown

**Résultat attendu** : ✅ Navigation clavier fonctionnelle

---

### Test 8 : Responsive Design

**Action** : Réduire la largeur du navigateur (mode mobile)

**Vérifications** :
- [ ] Le sélecteur s'adapte à la largeur (max 400px)
- [ ] Le texte reste lisible
- [ ] Les métadonnées s'affichent correctement
- [ ] Le dropdown ne dépasse pas de l'écran

**Résultat attendu** : ✅ Interface responsive et utilisable sur mobile

---

## 🐛 Tests de Non-Régression

### Fonctionnalités Tâche 2.6 (doivent toujours fonctionner)

**Action** : Après sélection d'un projet avec matchs

**Vérifications** :
- [ ] Le calendrier affiche les matchs avec FullCalendar
- [ ] Les matchs ont les bonnes couleurs :
  - 🔴 Rouge si is_fixed = true
  - 🔵 Bleu si is_fixed = false
  - 🟢 Vert si terminé
- [ ] Drag & drop fonctionne sur les matchs bleus
- [ ] Clic sur un match ouvre la modal de détails
- [ ] Les actions (fixer/défixer/supprimer) fonctionnent
- [ ] La légende des couleurs est toujours visible

**Résultat attendu** : ✅ Toutes les fonctionnalités antérieures préservées

---

## 📊 Checklist Complète

### Affichage
- [ ] Sélecteur s'affiche correctement
- [ ] Métadonnées visibles et correctes
- [ ] Calendrier s'affiche pour projet sélectionné

### Interactions
- [ ] Dropdown s'ouvre/ferme au clic
- [ ] Sélection change le projet
- [ ] Calendrier se rafraîchit automatiquement
- [ ] Icône ✓ sur projet sélectionné

### États
- [ ] Loading : skeleton animé
- [ ] Error : message d'erreur rouge
- [ ] Empty : message "aucun projet"
- [ ] Success : affichage normal

### Design
- [ ] Style cohérent avec Tailwind
- [ ] Transitions fluides
- [ ] Icons visibles (📄 👥 🏟️ ✓)
- [ ] Responsive mobile

### Accessibilité
- [ ] Focus ring visible
- [ ] Navigation clavier
- [ ] Labels ARIA corrects

### Performance
- [ ] Pas de lag lors du changement
- [ ] Requêtes API optimisées
- [ ] Pas d'erreurs console

---

## 🎯 Critères de Validation

**La Tâche 2.7 est validée si** :

✅ Tous les tests fonctionnels passent  
✅ Aucune régression sur les fonctionnalités antérieures  
✅ 0 erreur TypeScript (`npx tsc --noEmit`)  
✅ Interface utilisable et intuitive  
✅ Performance acceptable (< 1s changement projet)  

---

## 🚨 Problèmes Connus et Solutions

### Problème : Dropdown ne s'ouvre pas
**Solution** : Vérifier que @headlessui/react est bien installé
```bash
npm list @headlessui/react
```

### Problème : Icônes manquantes
**Solution** : Vérifier que @heroicons/react est installé
```bash
npm list @heroicons/react
```

### Problème : Métadonnées undefined
**Solution** : Vérifier que config_data contient nb_equipes et nb_gymnases
```bash
curl http://localhost:8000/api/projects/1 | jq '.config_data'
```

### Problème : Calendrier ne se rafraîchit pas
**Solution** : React Query cache les données, attendre ou désactiver cache :
```typescript
// Dans useMatches hook, forcer refetch
{ refetchInterval: 5000 }
```

---

## 📝 Rapport de Test (à remplir)

**Date** : _______________  
**Testeur** : _______________  

| Test | Résultat | Remarques |
|------|----------|-----------|
| Test 1 : Affichage initial | ☐ ✅ ☐ ❌ | |
| Test 2 : Ouverture dropdown | ☐ ✅ ☐ ❌ | |
| Test 3 : Changement projet | ☐ ✅ ☐ ❌ | |
| Test 4 : États de chargement | ☐ ✅ ☐ ❌ | |
| Test 5 : Gestion erreurs | ☐ ✅ ☐ ❌ | |
| Test 6 : Aucun projet | ☐ ✅ ☐ ❌ | |
| Test 7 : Accessibilité | ☐ ✅ ☐ ❌ | |
| Test 8 : Responsive | ☐ ✅ ☐ ❌ | |
| Non-régression | ☐ ✅ ☐ ❌ | |

**Conclusion** : ☐ VALIDÉ ☐ REFUSÉ

**Bugs identifiés** :
- 
- 

**Améliorations suggérées** :
- 
- 

---

**Prêt pour Tâche 2.8** : ☐ OUI ☐ NON

---

**Date de validation** : _______________
