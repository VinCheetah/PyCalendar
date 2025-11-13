# 📋 Guide Complet des Modifications de Style PyCalendar

## 🎯 Vue d'Ensemble

Ce document liste **tous les éléments stylistiques** de l'interface PyCalendar qui peuvent être modifiés, avec les **précautions à prendre** et les **fonctionnalités à protéger**.

---

## 📁 Architecture des Fichiers CSS

### Structure Modulaire
```
assets/styles/
├── 00-variables.css          ⭐ CRITIQUE - Tokens de design centralisés
├── 01-reset.css              ⚠️  Normalisation - Ne PAS modifier sauf besoin
├── 02-base.css               ✅ Styles de base (body, html, typographie)
├── 03-layout.css             ⭐ Layout principal (header, sidebars, grid)
├── 04-enhancements.css       ✅ Animations et effets visuels
├── 05-backgrounds-france.css ✅ Décorations thématiques (remplaçables)
├── components/               ⭐ Composants réutilisables
│   ├── filters.css
│   ├── loading.css
│   ├── match-card.css
│   ├── modals.css
│   ├── tabs.css
│   ├── view-options.css
│   └── views.css
├── themes/                   ✅ Thèmes light/dark
│   ├── dark.css
│   └── default-light.css
└── views/                    ⭐ Vues spécifiques
    ├── agenda-view.css
    └── pools-view.css
```

**Légende :**
- ⭐ **CRITIQUE** : Modifications requièrent grande attention
- ⚠️ **SENSIBLE** : Peut casser la mise en page
- ✅ **MODIFIABLE** : Modifications sûres

---

## 🎨 1. VARIABLES CSS (00-variables.css)

### 🔴 CRITIQUE - Système de Design Central

#### 1.1 Couleurs Principales
**Éléments modifiables :**
```css
--primary: #3B82F6;           /* Couleur primaire (liens, boutons CTA) */
--primary-hover: #2563EB;     /* État hover du primary */
--primary-dark: #1E40AF;      /* Variante sombre */
--primary-light: rgba(59, 130, 246, 0.12);  /* Fond léger */
--primary-gradient: linear-gradient(...);    /* Gradient primary */
```

**⚠️ ATTENTION :**
- Ces couleurs sont utilisées partout (150+ références)
- Vérifier le contraste WCAG AA (minimum 4.5:1 pour texte)
- Tester en mode clair ET sombre
- Les valeurs `rgba()` doivent respecter la couleur de base

**🔒 FONCTIONNALITÉS À PROTÉGER :**
- Visibilité des boutons d'action
- Lisibilité des liens
- Feedback visuel des interactions

---

#### 1.2 Couleurs Sémantiques
**Éléments modifiables :**
```css
--danger: #EF4444;     /* Erreurs, suppression */
--success: #10B981;    /* Validation, succès */
--warning: #F59E0B;    /* Avertissements */
--info: #3B82F6;       /* Informations */
```

**⚠️ ATTENTION :**
- Respecter les conventions (rouge = danger, vert = succès)
- Utilisées pour états de matchs, notifications, badges
- Le warning doit rester distinct du danger

**🔒 FONCTIONNALITÉS À PROTÉGER :**
- Indication visuelle des matchs non planifiés (warning)
- États de validation dans les modales
- Badges de statut des équipes

---

#### 1.3 Couleurs de Sport
**Éléments modifiables :**
```css
--sport-volleyball: #FF6B35;   /* Orange volleyball */
--sport-basketball: #FF8C42;   /* Orange basketball */
--sport-handball: #4ECDC4;     /* Teal handball */
--sport-football: #95E1D3;     /* Vert football */
```

**✅ SÛRES À MODIFIER :**
- Utilisées uniquement pour coloration thématique
- N'affectent pas la fonctionnalité
- Peuvent être adaptées aux couleurs de votre fédération

**💡 RECOMMANDATIONS :**
- Garder des couleurs distinctes entre sports
- Privilégier des couleurs vives et identifiables

---

#### 1.4 Couleurs de Genre
**Éléments modifiables :**
```css
--genre-male: #3B82F6;      /* Bleu pour masculin */
--genre-female: #EC4899;    /* Rose pour féminin */
--genre-mixed: #8B5CF6;     /* Violet pour mixte */
```

**⚠️ ATTENTION :**
- Utilisées dans le filtre "Coloration par genre"
- Doivent rester distinctes visuellement
- Éviter les couleurs trop proches

**🔒 FONCTIONNALITÉS À PROTÉGER :**
- Option "Colorer par genre" dans les filtres
- `.color-genre .match-card.male/female/mixed`

---

#### 1.5 Glassmorphism & Effets
**Éléments modifiables :**
```css
--glass-bg: rgba(255, 255, 255, 0.7);
--glass-bg-light: rgba(255, 255, 255, 0.5);
--glass-bg-strong: rgba(255, 255, 255, 0.9);
--glass-border: rgba(255, 255, 255, 0.2);
--glass-blur: blur(10px);
--glass-blur-strong: blur(20px);
```

**💡 RECOMMANDATIONS :**
- Ajuster l'opacité (0.5-0.95) selon goût
- Blur entre 5px-20px optimal
- Tester sur différents arrière-plans

**🔒 FONCTIONNALITÉS À PROTÉGER :**
- Lisibilité du texte sur fond transparent
- Séparation visuelle des couches (sidebars, modales)

---

#### 1.6 Espacements & Dimensions
**Éléments modifiables :**
```css
--spacing-xs: 0.25rem;    /* 4px */
--spacing-sm: 0.5rem;     /* 8px */
--spacing-md: 0.75rem;    /* 12px */
--spacing-lg: 1rem;       /* 16px */
--spacing-xl: 1.5rem;     /* 24px */
--spacing-2xl: 2rem;      /* 32px */
```

**⚠️ ATTENTION :**
- Modifier = recalculer toute la mise en page
- Risque de débordement/chevauchement
- Recommandé : créer de nouvelles variables plutôt que modifier

**🔒 FONCTIONNALITÉS À PROTÉGER :**
- Alignement des cartes de match
- Padding des sidebars
- Espacement dans les formulaires

---

#### 1.7 Animations
**Éléments modifiables :**
```css
--transition-fast: 0.15s;
--transition-base: 0.3s;
--transition-slow: 0.5s;

--anim-scale-hover: 1.05;
--anim-scale-active: 0.98;
--anim-translate-hover: -2px;
```

**✅ SÛRES À MODIFIER :**
- Vitesse des transitions (0.1s - 1s)
- Intensité des effets (scale, translate)
- Aucun impact fonctionnel

**💡 RECOMMANDATIONS :**
- Transitions < 0.5s pour réactivité
- Hover scale entre 1.02-1.08
- Active scale entre 0.95-0.98

**🔒 FONCTIONNALITÉS À PROTÉGER :**
- System `data-animation-level="0|1|2|3"` doit fonctionner

---

## 🏗️ 2. LAYOUT (03-layout.css)

### 2.1 Header Principal

#### Header Content
**Éléments modifiables :**
```css
.main-header {
    background: var(--gradient-primary);  ✅ Changeable
    height: 80px;                         ⚠️  Attention
    box-shadow: var(--shadow-xl);         ✅ Changeable
}
```

**⚠️ ATTENTION - Height du Header :**
- Si modifié, ajuster `.app-wrapper` et `.main-layout`
- Impacte le calcul de `calc(100vh - header)`
- Risque de scroll indésirable

**🔒 FONCTIONNALITÉS À PROTÉGER :**
- Logo + titre alignés verticalement
- Stats centrées et visibles
- Boutons thème accessibles

---

#### Header Stats (Statistiques)
**Éléments modifiables :**
```css
.header-stat {
    background: var(--glass-bg);          ✅ Changeable
    padding: var(--spacing-md);           ⚠️  Attention
    border-radius: var(--radius-xl);      ✅ Changeable
}

.header-stat:hover {
    transform: translateY(-2px);          ✅ Changeable
    box-shadow: var(--shadow-lg);         ✅ Changeable
}
```

**💡 RECOMMANDATIONS :**
- Garder le glassmorphism pour cohérence
- Hover subtle (translateY entre -2px et -5px)
- Box-shadow plus intense au hover

**🔒 FONCTIONNALITÉS À PROTÉGER :**
- Compteurs mis à jour dynamiquement par JS
- Classes `.warning` pour modifications non sauvegardées
- Icônes emoji doivent rester visibles

---

### 2.2 Sidebars (Colonnes Latérales)

#### Structure Sidebar
**Éléments modifiables :**
```css
.sidebar-left {
    width: 280px;                ⚠️  Peut modifier
    min-width: 250px;            ⚠️  Limite minimale
    max-width: 600px;            ⚠️  Limite maximale
    background: var(--glass-bg-strong);  ✅ Changeable
}

.sidebar.collapsed {
    width: 0 !important;         🔴 NE PAS MODIFIER
    opacity: 0;                  🔴 NE PAS MODIFIER
}
```

**⚠️ ATTENTION - Widths :**
- Width par défaut : préférence visuelle
- Min-width : évite sidebar trop étroite (contenu tronqué)
- Max-width : évite sidebar qui mange tout l'écran
- Ces valeurs sont aussi dans `app.js` (`setupSidebarResize()`)

**🔒 FONCTIONNALITÉS À PROTÉGER :**
- Système de collapse/expand (`.collapsed`)
- Redimensionnement par drag (`resize-handle`)
- Persistance localStorage
- Boutons show/hide (`.btn-show-sidebar`)

---

#### Boutons Collapse/Show
**Éléments modifiables :**
```css
.btn-collapse {
    background: var(--glass-bg);          ✅ Changeable
    border: 2px solid var(--glass-border);✅ Changeable
    border-radius: var(--radius-full);    ✅ Changeable
}

.btn-collapse:hover {
    transform: scale(1.08) rotate(90deg); ✅ Changeable
    background: var(--primary);           ✅ Changeable
}

.btn-show-sidebar {
    background: var(--gradient-primary);  ✅ Changeable
    animation: pulse 2s infinite;         ✅ Changeable
}
```

**💡 RECOMMANDATIONS :**
- Rotation au hover pour feedback dynamique
- Pulse sur btn-show pour attirer l'œil
- Couleur primary pour visibilité

**🔒 FONCTIONNALITÉS À PROTÉGER :**
- `opacity: 0/1` et `pointer-events: none/auto` pour show/hide
- Sélecteur `.sidebar-left.collapsed + .btn-show-left`
- Position fixed des boutons show

---

#### Resize Handles (Poignées)
**Éléments modifiables :**
```css
.resize-handle {
    width: 4px;                          ⚠️  Peut modifier
    background: var(--glass-border);     ✅ Changeable
}

.resize-handle:hover {
    width: 6px;                          ✅ Changeable
    background: var(--primary);          ✅ Changeable
}

.resize-handle::after {
    content: '⋮';                        ✅ Changeable
}
```

**⚠️ ATTENTION - Width :**
- Width doit correspondre au `grid-template-columns` du `.main-layout`
- Si modifié, ajuster aussi dans `updateGridColumns()` (app.js)

**🔒 FONCTIONNALITÉS À PROTÉGER :**
- Cursor col-resize
- Event listeners (mousedown, mousemove, mouseup)
- Double-click reset
- Classe `.resizing` sur body

---

### 2.3 Main Content (Zone Centrale)

**Éléments modifiables :**
```css
.main-content {
    background: var(--bg-secondary);     ✅ Changeable
    padding: var(--spacing-2xl);         ⚠️  Attention
    overflow-y: auto;                    🔴 NE PAS MODIFIER
}
```

**⚠️ ATTENTION - Padding :**
- Réduit l'espace disponible pour les cartes
- Si trop grand, force scroll prématuré
- Recommandé : entre 1rem et 2rem

**🔒 FONCTIONNALITÉS À PROTÉGER :**
- `overflow-y: auto` nécessaire pour scroll
- Custom scrollbar (`::-webkit-scrollbar`)
- Grid layout des vues (`.view-container`)

---

## 🎴 3. COMPOSANTS

### 3.1 Match Cards (Cartes de Match)

#### Style de Base
**Éléments modifiables :**
```css
.match-card {
    background: var(--glass-bg-strong);   ✅ Changeable
    border-radius: var(--radius-xl);      ✅ Changeable
    padding: var(--spacing-lg);           ⚠️  Attention
    border-left: 4px solid var(--primary);✅ Changeable
    box-shadow: var(--shadow-md);         ✅ Changeable
}

.match-card:hover {
    transform: translateY(-2px) scale(1.01); ✅ Changeable
    box-shadow: var(--shadow-xl);            ✅ Changeable
    border-left-width: 6px;                  ✅ Changeable
}
```

**💡 RECOMMANDATIONS :**
- Border-left distinctif par sport/statut
- Hover léger mais perceptible
- Glassmorphism pour effet moderne

**⚠️ ATTENTION - Padding :**
- Contient beaucoup d'infos (équipes, scores, horaires)
- Si < 1rem : risque de chevauchement
- Tester avec noms d'équipes longs

**🔒 FONCTIONNALITÉS À PROTÉGER :**
- Classes `.unscheduled`, `.no-score`, `.auto-scheduled`
- Coloration par genre (`.color-genre .match-card.male/female/mixed`)
- Coloration par niveau (`.color-level .match-card[data-category]`)
- Drag & drop (`.match-card[draggable="true"]`)
- Highlight (`.match-card.highlighted`)

---

#### Badges de Match
**Éléments modifiables :**
```css
.badge {
    padding: var(--spacing-xs) var(--spacing-md);  ⚠️  Attention
    border-radius: var(--radius-full);             ✅ Changeable
    font-size: var(--text-xs);                     ⚠️  Attention
    font-weight: 700;                              ✅ Changeable
}

.badge-sport-volleyball {
    background: var(--sport-volleyball-light);     ✅ Changeable
    color: var(--sport-volleyball);                ✅ Changeable
}
```

**⚠️ ATTENTION :**
- Font-size < 0.75rem = illisible
- Padding trop grand = badges envahissants
- Badges multiples doivent tenir sur une ligne

**🔒 FONCTIONNALITÉS À PROTÉGER :**
- Classes `.badge-sport-*`, `.badge-genre-*`, `.badge-category-*`
- Affichage conditionnel selon filtres
- Hover effects

---

#### Équipes et Scores
**Éléments modifiables :**
```css
.match-teams {
    display: flex;                      🔴 NE PAS MODIFIER (layout)
    gap: var(--spacing-md);             ✅ Changeable
}

.team-name {
    font-size: var(--text-lg);          ✅ Changeable
    font-weight: 700;                   ✅ Changeable
    color: var(--text-primary);         ✅ Changeable
}

.team-score {
    font-size: var(--text-3xl);         ✅ Changeable
    font-weight: 900;                   ✅ Changeable
    color: var(--primary);              ✅ Changeable
}

.team-score.winner {
    color: var(--success);              ✅ Changeable
    text-shadow: 0 0 10px currentColor; ✅ Changeable
}
```

**💡 RECOMMANDATIONS :**
- Score très visible (3xl = 1.875rem)
- Winner en vert avec glow subtil
- Team name lisible mais pas dominante

**🔒 FONCTIONNALITÉS À PROTÉGER :**
- Classe `.winner` ajoutée dynamiquement
- Affichage conditionnel score/no-score
- VS circle au centre (`.vs-circle`)

---

#### États Spéciaux
**Éléments modifiables :**
```css
.match-card.unscheduled {
    border-left-color: var(--warning);   ✅ Changeable
    opacity: 0.85;                       ✅ Changeable
}

.match-card.unscheduled::after {
    content: '⚠️ Non planifié';          ✅ Changeable texte
    background: var(--warning);          ✅ Changeable
}

.match-card.no-score {
    border-left-color: var(--info);      ✅ Changeable
}

.match-card.auto-scheduled {
    border-left-color: var(--success);   ✅ Changeable
}

.match-card.highlighted {
    animation: pulse 3s infinite;        ✅ Changeable
    box-shadow: 0 0 20px var(--primary); ✅ Changeable
}
```

**💡 RECOMMANDATIONS :**
- Unscheduled = warning orange
- No-score = info bleu (match à venir)
- Auto-scheduled = success vert
- Highlighted = animation pour recherche/filtre

**🔒 FONCTIONNALITÉS À PROTÉGER :**
- Ces classes sont ajoutées par le JS selon état du match
- Ne pas supprimer les classes, modifier seulement le style

---

#### Drag & Drop
**Éléments modifiables :**
```css
.match-card[draggable="true"] {
    cursor: grab;                        🔴 NE PAS MODIFIER
}

.match-card[draggable="true"]:active {
    cursor: grabbing;                    🔴 NE PAS MODIFIER
}

.match-card.dragging {
    opacity: 0.5;                        ✅ Changeable
    transform: rotate(2deg);             ✅ Changeable
}

.match-card.drop-target {
    border: 2px dashed var(--primary);   ✅ Changeable
    background: var(--primary-light);    ✅ Changeable
}
```

**🔒 FONCTIONNALITÉS À PROTÉGER :**
- Cursor grab/grabbing pour UX
- Attribut `[draggable="true"]`
- Event listeners (dragstart, dragover, drop)
- Classes `.dragging` et `.drop-target`

---

### 3.2 Filtres (Sidebar Droite)

#### Sections de Filtre
**Éléments modifiables :**
```css
.filter-section {
    background: var(--glass-bg-light);   ✅ Changeable
    padding: var(--spacing-lg);          ⚠️  Attention
    border-radius: var(--radius-xl);     ✅ Changeable
    border: 1px solid var(--glass-border);✅ Changeable
}

.filter-section:hover {
    background: var(--glass-bg);         ✅ Changeable
    border-color: var(--primary-light);  ✅ Changeable
}

.filter-section-title {
    font-size: var(--text-md);           ✅ Changeable
    font-weight: 700;                    ✅ Changeable
    color: var(--text-primary);          ✅ Changeable
}

.filter-section-title::before {
    content: '▼';                        ✅ Changeable
    color: var(--primary);               ✅ Changeable
}
```

**💡 RECOMMANDATIONS :**
- Sections bien séparées visuellement
- Hover subtil pour interactivité
- Icône before pour sections collapsibles

**🔒 FONCTIONNALITÉS À PROTÉGER :**
- Structure HTML (filter-section > filter-options > filter-option)
- Classes pour collapse (si implémentées)

---

#### Options de Filtre (Radio/Checkbox)
**Éléments modifiables :**
```css
.filter-option {
    display: flex;                       🔴 NE PAS MODIFIER (layout)
    padding: var(--spacing-md);          ⚠️  Attention
    border-radius: var(--radius-lg);     ✅ Changeable
    transition: var(--transition-base);  ✅ Changeable
}

.filter-option::before {
    content: '';                         ✅ Peut ajouter décoration
    background: var(--gradient-primary); ✅ Changeable
    opacity: 0;                          🔴 Doit rester 0 par défaut
}

.filter-option:hover {
    background: var(--primary-light);    ✅ Changeable
    transform: translateX(4px);          ✅ Changeable
}

.filter-option:hover::before {
    opacity: 1;                          ✅ Changeable
}

.filter-option:has(input:checked) {
    background: var(--primary-light);    ✅ Changeable
    border-left: 3px solid var(--primary);✅ Changeable
}
```

**⚠️ ATTENTION :**
- Input radio/checkbox doivent rester fonctionnels
- Padding impact clickable area
- `display: flex` nécessaire pour alignment

**🔒 FONCTIONNALITÉS À PROTÉGER :**
- Input `type="radio"` et `type="checkbox"`
- Sélecteur `:has(input:checked)` pour état actif
- Label associé (`.filter-option-label`)
- Événements onChange gérés par JS

---

#### Bouton "Effacer les filtres"
**Éléments modifiables :**
```css
.btn-clear-filters {
    background: var(--danger-light);     ✅ Changeable
    color: var(--danger);                ✅ Changeable
    border: 2px solid var(--danger);     ✅ Changeable
    padding: var(--spacing-md);          ✅ Changeable
    border-radius: var(--radius-lg);     ✅ Changeable
}

.btn-clear-filters:hover {
    background: var(--danger);           ✅ Changeable
    color: white;                        ✅ Changeable
    transform: scale(1.05);              ✅ Changeable
}
```

**💡 RECOMMANDATIONS :**
- Couleur danger pour action "destructive"
- Hover inversé (bg danger, texte blanc)
- Bien visible mais pas trop imposant

**🔒 FONCTIONNALITÉS À PROTÉGER :**
- ID `#btn-clear-filters`
- Event listener click
- Réinitialise tous les filtres

---

### 3.3 Modales

#### Overlay et Container
**Éléments modifiables :**
```css
.modal-overlay {
    background: rgba(0, 0, 0, 0.6);      ✅ Changeable opacité
    backdrop-filter: blur(5px);          ✅ Changeable blur
}

.modal {
    background: var(--glass-bg-strong);  ✅ Changeable
    border-radius: var(--radius-2xl);    ✅ Changeable
    box-shadow: var(--shadow-2xl);       ✅ Changeable
    max-width: 90vw;                     ⚠️  Attention
    max-height: 90vh;                    ⚠️  Attention
}

.modal-sm { width: 400px; }              ✅ Changeable
.modal-md { width: 600px; }              ✅ Changeable
.modal-lg { width: 800px; }              ✅ Changeable
.modal-xl { width: 1200px; }             ✅ Changeable
```

**⚠️ ATTENTION - Dimensions :**
- Max-width/height évitent débordement sur petits écrans
- Widths fixes pour tailles prédéfinies
- Tester responsive < 768px

**🔒 FONCTIONNALITÉS À PROTÉGER :**
- Classe `.hidden` pour show/hide
- Z-index élevé (z-index: 1000)
- Click outside to close
- Escape key to close

---

#### Modal Header
**Éléments modifiables :**
```css
.modal-header {
    background: var(--gradient-glass);   ✅ Changeable
    padding: var(--spacing-xl);          ⚠️  Attention
    border-bottom: 2px solid var(--glass-border);✅ Changeable
}

.modal-title {
    font-size: var(--text-2xl);          ✅ Changeable
    font-weight: 800;                    ✅ Changeable
    color: var(--text-primary);          ✅ Changeable
}

.modal-close {
    background: var(--glass-bg);         ✅ Changeable
    border-radius: var(--radius-full);   ✅ Changeable
    width: 40px;                         ⚠️  Touch target
    height: 40px;                        ⚠️  Touch target
}

.modal-close:hover {
    background: var(--danger);           ✅ Changeable
    color: white;                        ✅ Changeable
    transform: rotate(90deg) scale(1.1); ✅ Changeable
}
```

**⚠️ ATTENTION :**
- Bouton close min 40x40px (accessibilité touch)
- Padding header impact hauteur totale

**🔒 FONCTIONNALITÉS À PROTÉGER :**
- Classe `.modal-close` avec event listener
- Icon × doit rester visible

---

#### Modal Body & Footer
**Éléments modifiables :**
```css
.modal-body {
    padding: var(--spacing-2xl);         ⚠️  Attention
    overflow-y: auto;                    🔴 NE PAS MODIFIER
    max-height: calc(90vh - 200px);      ⚠️  Dépend header/footer
}

.modal-footer {
    padding: var(--spacing-xl);          ⚠️  Attention
    border-top: 2px solid var(--glass-border);✅ Changeable
    display: flex;                       🔴 NE PAS MODIFIER (layout)
    justify-content: space-between;      🔴 NE PAS MODIFIER
}
```

**⚠️ ATTENTION :**
- Overflow-y nécessaire pour long contenu
- Max-height calculé selon header/footer
- Footer flex pour alignement boutons

**🔒 FONCTIONNALITÉS À PROTÉGER :**
- Custom scrollbar
- Boutons dans footer (Annuler, Valider)
- Classes variantes (`.modal-confirm`, `.modal-danger`, `.modal-success`)

---

### 3.4 Tabs (Onglets)

**Éléments modifiables :**
```css
.tabs-container {
    display: flex;                       🔴 NE PAS MODIFIER (layout)
    border-bottom: 2px solid var(--border-color);✅ Changeable
    gap: var(--spacing-md);              ✅ Changeable
}

.tab-btn {
    padding: var(--spacing-md) var(--spacing-xl);⚠️  Attention
    border: none;                        ✅ Changeable
    background: transparent;             ✅ Changeable
    color: var(--text-secondary);        ✅ Changeable
    border-bottom: 3px solid transparent;✅ Changeable
}

.tab-btn:hover {
    color: var(--primary);               ✅ Changeable
    background: var(--primary-light);    ✅ Changeable
}

.tab-btn.active {
    color: var(--primary);               ✅ Changeable
    border-bottom-color: var(--primary); ✅ Changeable
    font-weight: 700;                    ✅ Changeable
}
```

**💡 RECOMMANDATIONS :**
- Border-bottom pour indiquer tab active
- Hover sur inactive pour feedback
- Couleur primary pour cohérence

**🔒 FONCTIONNALITÉS À PROTÉGER :**
- Classe `.active` gérée par JS
- Display flex pour horizontal layout
- Event listeners sur click

---

### 3.5 Loading & États de Chargement

**Éléments modifiables :**
```css
.loading-spinner {
    width: 60px;                         ✅ Changeable
    height: 60px;                        ✅ Changeable
    border: 5px solid var(--glass-border);✅ Changeable
    border-top-color: var(--primary);    ✅ Changeable
    border-radius: 50%;                  🔴 NE PAS MODIFIER (cercle)
    animation: spin 1s linear infinite;  ✅ Changeable vitesse
}

@keyframes spin {
    to { transform: rotate(360deg); }    🔴 NE PAS MODIFIER
}

.loading-overlay {
    background: rgba(0, 0, 0, 0.5);      ✅ Changeable opacité
    backdrop-filter: blur(3px);          ✅ Changeable
}
```

**💡 RECOMMANDATIONS :**
- Spinner visible mais pas intrusif (40-80px)
- Animation fluide (0.8s-1.2s)
- Overlay semi-transparent

**🔒 FONCTIONNALITÉS À PROTÉGER :**
- Transform rotate pour animation
- Border-radius 50% pour cercle parfait
- Position absolute/fixed selon contexte

---

## 📊 4. VUES SPÉCIFIQUES

### 4.1 Vue Agenda (agenda-view.css)

#### Timeline & Slots
**Éléments modifiables :**
```css
.agenda-timeline {
    display: grid;                       🔴 NE PAS MODIFIER (layout)
    grid-template-columns: 80px 1fr;     ⚠️  Peut ajuster
    gap: var(--spacing-md);              ✅ Changeable
}

.time-slot {
    padding: var(--spacing-md);          ✅ Changeable
    background: var(--glass-bg);         ✅ Changeable
    border-left: 3px solid var(--primary);✅ Changeable
}

.time-slot:hover {
    background: var(--primary-light);    ✅ Changeable
    transform: translateX(4px);          ✅ Changeable
}
```

**⚠️ ATTENTION - Grid Columns :**
- 80px = largeur colonne horaires
- 1fr = espace disponible pour matchs
- Si changé, vérifier alignement

**🔒 FONCTIONNALITÉS À PROTÉGER :**
- Grid layout pour alignement temporel
- Drag & drop de matchs entre slots
- Highlight des slots au survol

---

#### Groupement par Jour
**Éléments modifiables :**
```css
.agenda-day-group {
    margin-bottom: var(--spacing-2xl);   ✅ Changeable
    background: var(--glass-bg-light);   ✅ Changeable
    border-radius: var(--radius-xl);     ✅ Changeable
}

.agenda-day-header {
    padding: var(--spacing-lg);          ✅ Changeable
    background: var(--gradient-primary); ✅ Changeable
    color: white;                        ✅ Changeable
    font-size: var(--text-xl);           ✅ Changeable
}
```

**💡 RECOMMANDATIONS :**
- Headers de jour bien distincts
- Gradient pour attirer l'œil
- Spacing généreux entre jours

**🔒 FONCTIONNALITÉS À PROTÉGER :**
- Structure HTML (day-group > day-header + time-slots)
- Affichage conditionnel selon filtre date

---

### 4.2 Vue Poules (pools-view.css)

#### Cartes de Poule
**Éléments modifiables :**
```css
.pool-card {
    background: var(--glass-bg-strong);  ✅ Changeable
    border-radius: var(--radius-2xl);    ✅ Changeable
    padding: var(--spacing-xl);          ⚠️  Attention
    box-shadow: var(--shadow-lg);        ✅ Changeable
}

.pool-card:hover {
    transform: translateY(-4px);         ✅ Changeable
    box-shadow: var(--shadow-2xl);       ✅ Changeable
}

.pool-header {
    background: var(--gradient-primary); ✅ Changeable
    padding: var(--spacing-lg);          ✅ Changeable
    border-radius: var(--radius-xl);     ✅ Changeable
}
```

**💡 RECOMMANDATIONS :**
- Cards volumineuses (contiennent tableau + matchs)
- Hover subtil (lift effect)
- Header coloré pour identification rapide

**🔒 FONCTIONNALITÉS À PROTÉGER :**
- Structure (pool-header + pool-content)
- Tableau des équipes (`.pool-table`)
- Liste des matchs (`.pool-match-list`)

---

#### Tableaux de Classement
**Éléments modifiables :**
```css
.pool-table {
    width: 100%;                         🔴 NE PAS MODIFIER
    border-collapse: collapse;           🔴 NE PAS MODIFIER
}

.pool-table th {
    background: var(--primary-light);    ✅ Changeable
    padding: var(--spacing-md);          ✅ Changeable
    font-weight: 700;                    ✅ Changeable
    text-align: left;                    ⚠️  Peut ajuster
}

.pool-table tbody tr:hover {
    background: var(--primary-lighter);  ✅ Changeable
}

.pool-table td {
    padding: var(--spacing-md);          ✅ Changeable
    border-bottom: 1px solid var(--border-color);✅ Changeable
}
```

**⚠️ ATTENTION :**
- Width 100% nécessaire pour responsive
- Border-collapse pour jointures propres
- Text-align impact lisibilité (nombres vs texte)

**🔒 FONCTIONNALITÉS À PROTÉGER :**
- Structure table (thead + tbody)
- Classes colonnes (`.rank-col`, `.team-col`, `.stat-col`)
- Tri au click sur headers (si implémenté)

---

#### Matchs de Poule
**Éléments modifiables :**
```css
.pool-match {
    display: flex;                       🔴 NE PAS MODIFIER (layout)
    justify-content: space-between;      🔴 NE PAS MODIFIER
    padding: var(--spacing-md);          ✅ Changeable
    background: var(--glass-bg);         ✅ Changeable
    border-radius: var(--radius-lg);     ✅ Changeable
}

.pool-match:hover {
    background: var(--primary-light);    ✅ Changeable
    transform: translateX(4px);          ✅ Changeable
}

.pool-match.played {
    opacity: 0.7;                        ✅ Changeable
    border-left: 3px solid var(--success);✅ Changeable
}

.pool-match.upcoming {
    border-left: 3px solid var(--info);  ✅ Changeable
}
```

**💡 RECOMMANDATIONS :**
- Matchs joués en opacité réduite
- Border-left pour état visuel rapide
- Hover pour feedback interactif

**🔒 FONCTIONNALITÉS À PROTÉGER :**
- Classes `.played`, `.upcoming`, `.modified`
- Flex layout pour teams vs score
- Click handler pour détails

---

## 🎨 5. THÈMES (Light / Dark)

### 5.1 Mode Clair (Défaut)

**Variables à modifier dans `:root` :**
```css
--bg-primary: #FFFFFF;           ✅ Blanc par défaut
--bg-secondary: #F8FAFC;         ✅ Gris très clair
--bg-tertiary: #F1F5F9;          ✅ Gris clair

--text-primary: #0F172A;         ✅ Presque noir
--text-secondary: #475569;       ✅ Gris foncé
--text-tertiary: #94A3B8;        ✅ Gris moyen

--border-color: #E2E8F0;         ✅ Gris border
```

**💡 RECOMMANDATIONS :**
- Contraste élevé pour lisibilité
- Backgrounds progressifs (primary > secondary > tertiary)
- Textes avec hiérarchie visuelle

---

### 5.2 Mode Sombre (dark.css)

**Variables à modifier dans `[data-theme="dark"]` :**
```css
--bg-primary: #0F172A;           ✅ Presque noir
--bg-secondary: #1E293B;         ✅ Gris très foncé
--bg-tertiary: #334155;          ✅ Gris foncé

--text-primary: #F8FAFC;         ✅ Presque blanc
--text-secondary: #CBD5E1;       ✅ Gris clair
--text-tertiary: #64748B;        ✅ Gris moyen

--glass-bg: rgba(30, 41, 59, 0.7);        ✅ Glass sombre
--glass-bg-strong: rgba(30, 41, 59, 0.9); ✅ Glass opaque
--glass-border: rgba(148, 163, 184, 0.2); ✅ Border sombre

--shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.5);✅ Ombres plus fortes
```

**⚠️ ATTENTION - Mode Sombre :**
- Tester TOUS les composants (certains peuvent devenir invisibles)
- Shadows plus intenses pour contraste
- Glass backgrounds plus opaques
- Vérifier lisibilité des textes secondaires

**🔒 FONCTIONNALITÉS À PROTÉGER :**
- Toggle theme via `data-theme` attribute
- Boutons dans header (☀️/🌙)
- Persistance dans localStorage
- Transition smooth entre thèmes

---

## ⚙️ 6. ANIMATIONS & EFFETS

### 6.1 Animations Globales

**Animations modifiables :**
```css
@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

@keyframes slideIn {
    from { 
        opacity: 0; 
        transform: translateY(20px); 
    }
    to { 
        opacity: 1; 
        transform: translateY(0); 
    }
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.8; }
}

@keyframes shimmer {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
}
```

**✅ SÛRES À MODIFIER :**
- Durée, timing-function, propriétés
- Ajouter des keyframes personnalisés

**🔒 FONCTIONNALITÉS À PROTÉGER :**
- Référencées dans `animation:` properties
- Utilisées conditionnellement selon `data-animation-level`

---

### 6.2 Système de Niveaux d'Animation

**Implémentation actuelle :**
```css
/* Niveau 0 : Aucune animation */
[data-animation-level="0"] * {
    animation: none !important;
    transition: none !important;
}

/* Niveau 1 : Minimal */
[data-animation-level="1"] {
    --transition-fast: 0.1s;
    --transition-base: 0.2s;
}

/* Niveau 2 : Normal (défaut) */
[data-animation-level="2"] {
    --transition-fast: 0.15s;
    --transition-base: 0.3s;
}

/* Niveau 3 : Maximum */
[data-animation-level="3"] {
    --transition-fast: 0.2s;
    --transition-base: 0.4s;
    --transition-slow: 0.8s;
}
```

**⚠️ ATTENTION :**
- Niveau 0 = accessibilité (motion sickness)
- Niveaux impact performance
- Tester sur machines lentes

**🔒 FONCTIONNALITÉS À PROTÉGER :**
- Attribute `data-animation-level` sur `<html>`
- Contrôle via checkbox dans sidebar
- Persistance localStorage

---

## 🔧 7. RESPONSIVE DESIGN

### 7.1 Breakpoints

**Points de rupture actuels :**
```css
/* Tablet : 768px */
@media (max-width: 768px) {
    .header-content { flex-direction: column; }
    .header-stats { display: none; }  /* Caché sur mobile */
    .sidebar-left, 
    .sidebar-right { 
        position: fixed; 
        z-index: 100; 
    }
}

/* Mobile : 480px */
@media (max-width: 480px) {
    .match-card { padding: var(--spacing-md); }
    .modal { max-width: 95vw; }
    .pool-table { font-size: 0.85rem; }
}
```

**⚠️ ATTENTION :**
- Sidebars deviennent modales sur mobile
- Stats cachées pour économiser espace
- Font-size réduits pour tableaux

**🔒 FONCTIONNALITÉS À PROTÉGER :**
- Touch targets min 44x44px
- Scroll horizontal évité
- Navigation accessible au pouce

---

### 7.2 Règles Spécifiques Mobile

**À préserver :**
```css
@media (hover: none) {
    /* Appareils tactiles : désactiver hover effects */
    .match-card:hover { transform: none; }
    .btn:hover { transform: none; }
}

@media (prefers-reduced-motion: reduce) {
    /* Accessibilité : réduire animations */
    * {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }
}
```

**🔒 FONCTIONNALITÉS À PROTÉGER :**
- `prefers-reduced-motion` pour accessibilité
- `hover: none` pour désactiver hovers tactiles
- Mobile-first approach

---

## ⚡ 8. PERFORMANCES & OPTIMISATIONS

### 8.1 CSS à Optimiser

**Bonnes pratiques :**
```css
/* ✅ BON : Utilise transform (GPU) */
.element:hover {
    transform: translateY(-2px);
}

/* ❌ MAUVAIS : Utilise top (CPU) */
.element:hover {
    top: -2px;
}

/* ✅ BON : Will-change pour animations fréquentes */
.match-card {
    will-change: transform;
}

/* ❌ MAUVAIS : Will-change partout */
* {
    will-change: transform, opacity;
}
```

**⚠️ ATTENTION :**
- `will-change` améliore perf mais consomme RAM
- Préférer `transform` et `opacity` (GPU)
- Éviter animations sur `width`, `height`, `top`, `left`

---

### 8.2 Sélecteurs à Éviter

**❌ Mauvaises pratiques :**
```css
/* Trop générique */
* { transition: all 0.3s; }

/* Cascade profonde */
.app > .layout > .content > .card > .header > .title { }

/* Combinateurs multiples */
.sidebar ~ .content + .footer { }
```

**✅ Bonnes pratiques :**
```css
/* Spécifique et performant */
.card-title { }

/* Classes BEM */
.match-card__header { }
.match-card__title { }

/* Un niveau de combinateur max */
.sidebar + .content { }
```

---

## 🔒 9. FONCTIONNALITÉS CRITIQUES À NE JAMAIS CASSER

### 9.1 Système de Filtrage

**Classes essentielles :**
- `.filter-option input[type="radio"]`
- `.filter-option input[type="checkbox"]`
- `.filter-option:has(input:checked)`
- `#btn-clear-filters`

**Ne JAMAIS modifier :**
- Structure HTML des inputs
- Attributs `name`, `value`, `checked`
- Event listeners JavaScript

---

### 9.2 Drag & Drop

**Classes essentielles :**
- `.match-card[draggable="true"]`
- `.match-card.dragging`
- `.match-card.drop-target`
- `.time-slot[data-droppable]`

**Ne JAMAIS modifier :**
- Attribut `draggable`
- Cursors (grab/grabbing)
- Event listeners (dragstart, dragover, drop)

---

### 9.3 Sidebars & Layout

**Classes essentielles :**
- `.sidebar.collapsed`
- `.btn-show-sidebar`
- `.btn-collapse`
- `.resize-handle`

**Ne JAMAIS modifier :**
- `opacity: 0/1` pour show/hide
- `pointer-events: none/auto`
- `overflow-y: auto` sur scrollables
- Grid template columns du main-layout

---

### 9.4 Modales

**Classes essentielles :**
- `.modal-overlay.hidden`
- `.modal-close`
- `.modal-body` (overflow-y)

**Ne JAMAIS modifier :**
- Z-index (doit être > 1000)
- Position fixed de l'overlay
- Event listeners (click outside, Escape)

---

### 9.5 États des Matchs

**Classes essentielles :**
- `.match-card.unscheduled`
- `.match-card.no-score`
- `.match-card.auto-scheduled`
- `.match-card.highlighted`
- `.team-score.winner`

**Ne JAMAIS modifier :**
- Ces classes sont ajoutées dynamiquement par JS
- Supprimer = perd l'info visuelle

---

## 📋 10. CHECKLIST AVANT MODIFICATION

### ✅ Questions à se poser :

1. **Impact Fonctionnel**
   - [ ] Est-ce que cette modif casse un event listener ?
   - [ ] Est-ce que ça impacte le drag & drop ?
   - [ ] Est-ce que les filtres marcheront toujours ?

2. **Impact Visuel**
   - [ ] Est-ce que c'est lisible en mode clair ET sombre ?
   - [ ] Est-ce que le contraste est suffisant (WCAG AA) ?
   - [ ] Est-ce que ça fonctionne sur mobile ?

3. **Impact Performance**
   - [ ] Est-ce que j'utilise `transform` plutôt que `top/left` ?
   - [ ] Est-ce que j'évite les sélecteurs universels ?
   - [ ] Est-ce que les animations sont raisonnables ?

4. **Impact Responsive**
   - [ ] Est-ce que ça tient sur 768px de large ?
   - [ ] Est-ce que les touch targets font 44x44px min ?
   - [ ] Est-ce que j'ai testé sur mobile ?

5. **Impact Accessibilité**
   - [ ] Est-ce que `prefers-reduced-motion` est respecté ?
   - [ ] Est-ce que les boutons sont focus-visibles ?
   - [ ] Est-ce que les états sont distinguables ?

---

## 🚀 11. WORKFLOW DE MODIFICATION RECOMMANDÉ

### Étape 1 : Identifier
1. Trouver l'élément dans l'interface
2. Inspecter avec DevTools pour trouver la classe
3. Chercher la classe dans les fichiers CSS

### Étape 2 : Planifier
1. Lister les propriétés à modifier
2. Vérifier les dépendances (JS, autres styles)
3. Prévoir les tests (light/dark, mobile, animations)

### Étape 3 : Modifier
1. Modifier le CSS dans le fichier source
2. Régénérer l'interface (`python generate_interface.py`)
3. Ouvrir dans navigateur

### Étape 4 : Tester
1. Mode clair ET mode sombre
2. Toutes les vues (Agenda, Poules, etc.)
3. Responsive (F12 > Toggle device toolbar)
4. Interactions (hover, click, drag)
5. Filtres et recherche

### Étape 5 : Valider
1. Vérifier console (pas d'erreurs JS)
2. Tester performance (Chrome DevTools > Performance)
3. Valider accessibilité (contraste, focus)

---

## 📞 12. RÉSUMÉ PAR NIVEAU DE RISQUE

### 🟢 MODIFICATIONS SÛRES (Peu de risque)
- Couleurs (primary, danger, success, etc.)
- Font-sizes et font-weights
- Border-radius, box-shadows
- Transitions et animations (durée, intensité)
- Backgrounds et gradients
- Hover effects (transform, colors)

### 🟡 MODIFICATIONS À TESTER (Risque moyen)
- Spacings (padding, margin, gap)
- Widths et heights
- Max/min dimensions
- Z-index (si conflit possible)
- Grid/flex gaps
- Border widths

### 🔴 MODIFICATIONS CRITIQUES (Haut risque)
- Display properties (flex, grid, none)
- Position properties (fixed, absolute, relative)
- Overflow properties
- Opacity pour show/hide (doit être couplé à pointer-events)
- Cursor types (grab, pointer, etc.)
- Grid-template-columns/rows
- Flex-direction et justify-content

### 🚫 NE JAMAIS MODIFIER
- Attributs HTML (`draggable`, `type`, `name`, `value`)
- Event listeners JavaScript
- Structure HTML (ordre des éléments)
- IDs utilisés par JS
- Classes d'état ajoutées dynamiquement
- Sélecteurs `:has()` fonctionnels

---

## 🎓 CONCLUSION

Cette interface PyCalendar est construite sur une **architecture modulaire** avec un **système de design tokens** centralisé dans `00-variables.css`.

**Principes clés :**
1. **Modifier les variables** plutôt que les valeurs en dur
2. **Tester en light ET dark** après chaque changement
3. **Vérifier le responsive** (768px, 480px)
4. **Protéger les fonctionnalités JS** (classes, IDs, attributs)
5. **Préférer les effets GPU** (transform, opacity)

**En cas de doute :**
- Consulter ce guide
- Tester d'abord sur une copie
- Utiliser DevTools pour inspecter
- Vérifier la console pour erreurs JS

Bon design ! 🎨✨
