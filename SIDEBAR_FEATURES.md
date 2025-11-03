# 🎨 Nouvelles Fonctionnalités des Sidebars

## ✨ Fonctionnalités Implémentées

### 1. 📐 **Collapse/Expand des Sidebars**

#### Boutons de collapse
- **Sidebar gauche** : Bouton `◀` dans l'en-tête
- **Sidebar droite** : Bouton `▶` dans l'en-tête
- Cliquer sur le bouton masque la sidebar avec animation fluide
- L'icône change automatiquement (◀ ↔ ▶)
- L'état est **sauvegardé** dans localStorage

#### Boutons de réapparition
Quand une sidebar est masquée :
- **Sidebar gauche** : Un bouton `▶` apparaît à gauche de l'écran (position fixe)
- **Sidebar droite** : Un bouton `◀` apparaît à droite de l'écran (position fixe)
- Ces boutons sont visibles au milieu de la hauteur de l'écran
- Cliquer dessus réaffiche la sidebar instantanément
- Style : boutons flottants bleus avec ombre

### 2. 📏 **Redimensionnement des Sidebars**

#### Poignées de redimensionnement
- **Poignée gauche** : Entre la sidebar gauche et le contenu central
- **Poignée droite** : Entre le contenu central et la sidebar droite
- Largeur : 4px (transparente, devient bleue au survol)
- Cursor : `col-resize` au survol

#### Fonctionnement
- **Drag & drop** : Cliquer et maintenir sur la poignée, puis glisser
- **Limites** : 
  - Largeur minimale : 250px
  - Largeur maximale : 600px
- **Effet visuel** : 
  - La poignée devient bleue pendant le drag
  - Le curseur change en `col-resize`
  - La sélection de texte est désactivée pendant le drag
- **Sauvegarde** : Les largeurs sont automatiquement sauvegardées dans localStorage

#### Restauration
- Au rechargement de la page :
  - Les largeurs personnalisées sont restaurées
  - Les états collapsed/expanded sont restaurés
  - Le layout s'adapte automatiquement

### 3. 🎨 **Coloration des Matchs**

#### Options disponibles
Dans **Vue Poules** et **Vue Agenda** :
- 🎨 **Aucune** : Pas de coloration spéciale
- 📊 **Par statut** : Couleurs selon l'état (assigné, modifié, etc.)
- 🏢 **Par lieu** : Chaque gymnase une couleur différente
- 👥 **Par genre** : Hommes vs Femmes
- 📈 **Par niveau** : Couleurs selon le niveau de compétition

#### Utilisation
1. Aller dans les options d'affichage (sidebar gauche)
2. Sélectionner "🎨 Coloration des matchs"
3. Choisir un schéma dans le menu déroulant
4. Les matchs sont immédiatement recolorés
5. La préférence est sauvegardée dans localStorage

## 🔧 Architecture Technique

### HTML
- Boutons collapse dans `index.html` :
  - `#btn-collapse-left` et `#btn-collapse-right`
- Boutons show :
  - `#btn-show-left` et `#btn-show-right` (position: fixed)
- Poignées de resize :
  - `#resize-handle-left` et `#resize-handle-right`

### CSS (03-layout.css)
- **Layout Grid** : `grid-template-columns: 320px 4px 1fr 4px 280px`
  - Colonne 1 : Sidebar gauche
  - Colonne 2 : Poignée gauche
  - Colonne 3 : Contenu central
  - Colonne 4 : Poignée droite
  - Colonne 5 : Sidebar droite
- **Classes** :
  - `.sidebar.collapsed` : Sidebar masquée (width: 0)
  - `.resize-handle` : Poignées de redimensionnement
  - `.btn-show-sidebar` : Boutons flottants de réapparition

### JavaScript (app.js)

#### setupSidebarControls()
- Gère les boutons collapse/expand
- Gère les boutons show
- Sauvegarde/restaure l'état dans localStorage
- Change les icônes dynamiquement

#### setupSidebarResize()
- Gère le drag & drop des poignées
- Utilise les événements : `mousedown`, `mousemove`, `mouseup`
- Validation des limites (250-600px)
- Mise à jour dynamique de `grid-template-columns`
- Sauvegarde des largeurs dans localStorage
- MutationObserver pour détecter les changements de classe

### Vues (pools-view.js, agenda-grid.js)

#### applyColorScheme(scheme)
- Applique l'attribut `data-color-scheme` sur le conteneur
- Valeurs : 'none', 'by-status', 'by-venue', 'by-gender', 'by-level'
- Sauvegarde la préférence dans localStorage
- Re-render la vue pour appliquer les changements

## 📦 Fichiers Modifiés

1. **src/pycalendar/interface/templates/index.html**
   - Ajout des boutons show
   - Ajout des poignées de resize

2. **src/pycalendar/interface/scripts/app.js**
   - `setupSidebarControls()` : Gestion collapse/expand + show
   - `setupSidebarResize()` : Gestion du redimensionnement

3. **src/pycalendar/interface/assets/styles/03-layout.css**
   - Layout grid 5 colonnes
   - Styles des poignées de resize
   - Styles des boutons show
   - Animations et transitions

4. **src/pycalendar/interface/scripts/views/pools-view.js**
   - Option "🎨 Coloration des matchs"
   - Méthode `applyColorScheme()`

5. **src/pycalendar/interface/scripts/views/agenda-grid.js**
   - Option "🎨 Coloration des matchs"
   - Méthode `applyColorScheme()`

6. **src/pycalendar/interface/scripts/managers/view-options-manager.js**
   - Fix : utilisation de `option.default` au lieu de `option.currentValue`
   - Fix : ajout de `selected` sur les options select
   - Fix : utilisation de `option.default` pour les checkboxes

## 🎯 Utilisation

### Masquer une sidebar
1. Cliquer sur le bouton `◀` (gauche) ou `▶` (droite) dans l'en-tête
2. La sidebar se masque avec animation
3. Un bouton flottant apparaît sur le bord de l'écran

### Réafficher une sidebar
1. Cliquer sur le bouton flottant `▶` (gauche) ou `◀` (droite)
2. La sidebar réapparaît avec animation
3. Le bouton flottant disparaît

### Redimensionner une sidebar
1. Survoler la zone entre la sidebar et le contenu central
2. Le curseur change en `col-resize`
3. Cliquer et maintenir
4. Glisser horizontalement
5. Relâcher pour fixer la largeur

### Colorer les matchs
1. Ouvrir les options d'affichage (sidebar gauche)
2. Descendre jusqu'à "🎨 Coloration des matchs"
3. Sélectionner un schéma
4. Les matchs sont immédiatement recolorés

## 💾 Persistance

Toutes les préférences utilisateur sont sauvegardées dans **localStorage** :

- `sidebar-left-collapsed` : État de la sidebar gauche (true/false)
- `sidebar-right-collapsed` : État de la sidebar droite (true/false)
- `sidebar-left-width` : Largeur de la sidebar gauche (ex: "350px")
- `sidebar-right-width` : Largeur de la sidebar droite (ex: "320px")
- `pools-color-scheme` : Schéma de couleurs pour la vue Poules
- `agenda-color-scheme` : Schéma de couleurs pour la vue Agenda

Les préférences sont automatiquement restaurées au rechargement de la page.

## ✅ Tests à Effectuer

1. ✓ Collapse sidebar gauche → bouton show apparaît
2. ✓ Collapse sidebar droite → bouton show apparaît
3. ✓ Show sidebar gauche → sidebar réapparaît
4. ✓ Show sidebar droite → sidebar réapparaît
5. ✓ Resize sidebar gauche (250-600px)
6. ✓ Resize sidebar droite (250-600px)
7. ✓ Coloration matchs Vue Poules (5 schémas)
8. ✓ Coloration matchs Vue Agenda (5 schémas)
9. ✓ Persistance au reload (états + largeurs + couleurs)
10. ✓ Responsive au resize de fenêtre

## 🚀 Fichiers Générés

- **calendar.html** : 869 KB (généré le 27/10/2025 à 19:41)
- **new_calendar.html** : 869 KB (généré le 27/10/2025 à 19:40)

Les deux fichiers contiennent toutes les nouvelles fonctionnalités et sont prêts à être utilisés.
