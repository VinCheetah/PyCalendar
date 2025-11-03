# Audit des Boutons - Interface PyCalendar FFSU

## ✅ Boutons FONCTIONNELS (avec event listeners)

### Header
- **Thèmes** (☀️/🌙/🇫🇷) - `data-theme="light|dark|tricolore"`
  - Event: `click` → `setTheme(theme)`
  - Initialisé dans: `initializeTheme()`
  - ✅ FONCTIONNE

### Sidebar Gauche

#### Sports (🏐/🤾/⚽/🏀)
- `data-sport="volleyball|handball|football|basketball"`
- Event: `click` → `setSport(sport)`
- Initialisé dans: `initializeSportSwitching()`
- ✅ FONCTIONNE

#### Vues (📋/🎯/🃏/📅/📊)
- `data-view="agenda|pools|cards|calendar|stats"`
- Event: `click` → `switchView(viewName)`
- Initialisé dans: `initializeViewSwitching()`
- ✅ FONCTIONNE

#### Actions
- **Export** (`btn-export-modifications`) - 💾
  - Event: `click` → `openExportModal()`
  - Initialisé dans: `initializeActionButtons()`
  - ✅ FONCTIONNE

- **Reset** (`btn-reset-modifications`) - 🔄
  - Event: `click` → confirm + `modificationManager.clearAll()`
  - Initialisé dans: `initializeActionButtons()`
  - ✅ FONCTIONNE (mais incomplet, voir ci-dessous)

#### Collapse Sidebar Gauche
- `btn-collapse-left` - ◀
- Event: `click` → toggle `collapsed` class
- Initialisé dans: `initializeSidebarCollapse()`
- ✅ FONCTIONNE

### Sidebar Droite

#### Clear Filters
- `btn-clear-filters`
- Event: `click` → `clearAllFilters()`
- Initialisé dans: `initializeFilters()`
- ✅ FONCTIONNE

#### Filtres
- **Genre** (`input[name="filter-gender"]`) - radio buttons
  - Event: `change` → `applyFilters()`
  - ✅ FONCTIONNE

- **Semaine/Poule/Institution/Gymnase** - selects
  - Event: `change` → `applyFilters()`
  - ✅ FONCTIONNE

- **Jours** (`input[name="filter-day"]`) - checkboxes
  - Event: `change` → `applyFilters()`
  - ✅ FONCTIONNE

- **Horaires** (`filter-time-start`, `filter-time-end`)
  - Event: `change` → `applyFilters()`
  - ✅ FONCTIONNE

- **États** (`input[name="filter-state"]`) - checkboxes
  - Event: `change` → `applyFilters()`
  - ✅ FONCTIONNE

- **Recherche** (`filter-search`)
  - Event: `input` → `debounce(applyFilters, 300)`
  - ✅ FONCTIONNE

#### Collapse Sidebar Droite
- `btn-collapse-right` - ▶
- Event: `click` → toggle `collapsed` class
- Initialisé dans: `initializeSidebarCollapse()`
- ✅ FONCTIONNE

---

## ❌ Boutons NON FONCTIONNELS (manque event listeners)

### Header
- **Help** (`btn-help`) - ❓
  - Fonction existe: `openHelpModal()`
  - ❌ MANQUE: Event listener
  - **FIX REQUIS**: Ajouter dans `initializeActionButtons()`

### Sidebar Gauche - Actions
- **Print** (`btn-print`) - 🖨️
  - Fonction requise: `window.print()`
  - ❌ MANQUE: Event listener
  - **FIX REQUIS**: Ajouter dans `initializeActionButtons()`

### Sidebar Gauche - Options
- Tous les checkboxes d'options (`opt-show-conflicts`, `opt-show-unscheduled`, etc.)
  - ❌ MANQUE: Event listeners
  - **FIX REQUIS**: Créer fonction `initializeDisplayOptions()` pour gérer ces options

---

## ⚠️ Boutons PARTIELLEMENT FONCTIONNELS

### Reset Button
**Problème**: Appelle `modificationManager.clearAll()` ET `dataManager.revertAllModifications()` mais:
1. Le code est tronqué dans le template (ligne 941 incomplète)
2. N'actualise pas les vues après reset
3. N'actualise pas les statistiques

**FIX REQUIS**:
```javascript
btnReset.addEventListener('click', () => {
    if (confirm('Réinitialiser toutes les modifications ?')) {
        if (window.modificationManager) {
            window.modificationManager.clearAll();
        }
        if (window.dataManager) {
            window.dataManager.revertAllModifications();
        }
        // Actualiser les vues
        updateCurrentView();
        updateStatsDisplay();
        // Notification
        console.log('✅ Toutes les modifications ont été réinitialisées');
    }
});
```

---

## 🔧 SYSTÈME DE FILTRES - Amélioration Requise

### Problème Actuel
Le template utilise `initializeFilters()` avec système de filtres basique intégré dans le template.

### Solution
Remplacer par **EnhancedFilterSystem** (`scripts/features/enhanced-filter-system.js`):
- 610 lignes de code complet
- Persistence localStorage
- Callbacks pour vues
- Meilleure performance
- UI synchronisée

**FIX REQUIS**:
1. Instancier `window.filterSystem = new EnhancedFilterSystem()`
2. Appeler `filterSystem.init()` dans l'initialisation
3. Connecter callbacks: `filterSystem.onChange((filters) => { updateCurrentView(); })`
4. Supprimer l'ancienne fonction `initializeFilters()`

---

## 📋 ORDRE DE CHARGEMENT DES SCRIPTS

Actuellement dans `JS_PLACEHOLDER`:
1. ✅ Core: `data-manager.js`, `modification-manager.js`
2. ⚠️ Features: **MANQUE** `enhanced-filter-system.js`
3. ✅ Views: `agenda-view.js`, `pools-view.js`, `cards-view.js`
4. ✅ Template inline scripts

**FIX REQUIS**: Ajouter dans generator.py avant les vues:
```python
'scripts/features/enhanced-filter-system.js',
```

---

## 🎯 PLAN D'ACTION

### 1. Corriger initializeActionButtons()
```javascript
function initializeActionButtons() {
    // Export button
    const btnExport = document.getElementById('btn-export-modifications');
    if (btnExport) {
        btnExport.addEventListener('click', openExportModal);
    }
    
    // Reset button
    const btnReset = document.getElementById('btn-reset-modifications');
    if (btnReset) {
        btnReset.addEventListener('click', () => {
            if (confirm('Réinitialiser toutes les modifications ?')) {
                if (window.modificationManager) {
                    window.modificationManager.clearAll();
                }
                if (window.dataManager) {
                    window.dataManager.revertAllModifications();
                }
                updateCurrentView();
                updateStatsDisplay();
                console.log('✅ Modifications réinitialisées');
            }
        });
    }
    
    // Print button
    const btnPrint = document.getElementById('btn-print');
    if (btnPrint) {
        btnPrint.addEventListener('click', () => {
            window.print();
        });
    }
    
    // Help button
    const btnHelp = document.getElementById('btn-help');
    if (btnHelp) {
        btnHelp.addEventListener('click', openHelpModal);
    }
}
```

### 2. Ajouter initializeDisplayOptions()
```javascript
function initializeDisplayOptions() {
    const options = ['show-conflicts', 'show-unscheduled', 'show-details', 'compact-mode', 'animations'];
    
    options.forEach(optionId => {
        const checkbox = document.getElementById(`opt-${optionId}`);
        if (checkbox) {
            // Charger depuis localStorage
            const savedValue = localStorage.getItem(`pycalendar-opt-${optionId}`);
            if (savedValue !== null) {
                checkbox.checked = savedValue === 'true';
            }
            
            // Event listener
            checkbox.addEventListener('change', () => {
                localStorage.setItem(`pycalendar-opt-${optionId}`, checkbox.checked);
                updateCurrentView();
                
                // Options spécifiques
                if (optionId === 'animations') {
                    document.documentElement.style.setProperty('--transition-duration', checkbox.checked ? '0.3s' : '0s');
                } else if (optionId === 'compact-mode') {
                    document.documentElement.classList.toggle('compact-mode', checkbox.checked);
                }
            });
        }
    });
}
```

### 3. Remplacer initializeFilters() par EnhancedFilterSystem
```javascript
// Supprimer l'ancienne fonction initializeFilters()
// Ajouter ceci dans initializeApp():

if (window.EnhancedFilterSystem) {
    window.filterSystem = new EnhancedFilterSystem();
    window.filterSystem.init();
    
    // Connecter aux vues
    window.filterSystem.onChange((filters) => {
        if (window.agendaView) window.agendaView.setFilters(filters);
        if (window.poolsView) window.poolsView.setFilters(filters);
        if (window.cardsView) window.cardsView.setFilters(filters);
    });
}
```

### 4. Mettre à jour initializeApp()
```javascript
function initializeApp() {
    console.log('🚀 Initialisation de PyCalendar FFSU...');
    
    // 1. Thème
    initializeTheme();
    
    // 2. Navigation
    initializeViewSwitching();
    initializeSportSwitching();
    
    // 3. Sidebars
    initializeSidebarCollapse();
    
    // 4. Options d'affichage
    initializeDisplayOptions();
    
    // 5. Filtres (nouveau système)
    if (window.EnhancedFilterSystem) {
        window.filterSystem = new EnhancedFilterSystem();
        window.filterSystem.init();
        window.filterSystem.onChange((filters) => {
            updateCurrentView();
        });
    }
    
    // 6. Actions
    initializeActionButtons();
    
    // 7. Stats
    updateStatsDisplay();
    
    // 8. Vue initiale
    switchView('agenda');
    
    console.log('✅ Interface prête !');
}

// Démarrer l'application
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeApp);
} else {
    initializeApp();
}
```

---

## ✅ CHECKLIST FINALE

- [ ] Corriger `initializeActionButtons()` (print + help)
- [ ] Ajouter `initializeDisplayOptions()`
- [ ] Remplacer système de filtres par `EnhancedFilterSystem`
- [ ] Compléter le code du reset button
- [ ] Ajouter `enhanced-filter-system.js` dans l'ordre de chargement
- [ ] Créer fonction `initializeApp()` complète
- [ ] Ajouter event listener `DOMContentLoaded`
- [ ] Régénérer l'interface
- [ ] Tester tous les boutons
