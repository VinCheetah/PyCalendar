/**
 * app.js - Initialisation principale de l'application
 * 
 * Coordonne tous les composants et gère l'initialisation.
 */

document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

/**
 * Point d'entrée de l'application.
 */
function initializeApp() {
    try {
        loadSavedTheme();
        loadSavedPalette();

        const solutionData = loadSolutionData();
        if (!solutionData) return;

        initializeManagers(solutionData);
        initializeViews();
        initializeViewOptions();
        initializeFilters();
        
        setupEventListeners();
        
        updateStatistics();
        switchView('pools');

    } catch (error) {
        showError(`Erreur critique d'initialisation: ${error.message}`);
        console.error(error);
    }
}

/**
 * Charge les données de la solution depuis le DOM.
 * @returns {object|null} Les données de la solution ou null en cas d'erreur.
 */
function loadSolutionData() {
    const solutionDataElement = document.getElementById('solution-data');
    if (!solutionDataElement) {
        showError('Impossible de trouver les données du calendrier.');
        return null;
    }
    try {
        return JSON.parse(solutionDataElement.textContent);
    } catch (error) {
        showError('Format de données JSON invalide.');
        return null;
    }
}

/**
 * Initialise les managers globaux (données, modifications, options).
 */
function initializeManagers(solutionData) {
    const solutionName = solutionData.metadata?.solution_name || 'unknown';
    
    window.dataManager = new DataManager(solutionData);
    window.modificationManager = new ModificationManager(solutionName);
    window.viewOptionsManager = new ViewOptionsManager(document.getElementById('view-options-container'));

    // Abonnements pour les mises à jour automatiques
    window.dataManager.subscribe('matches', updateStatistics);
    window.modificationManager.subscribe(updateStatistics);
}

/**
 * Initialise les instances de chaque vue (Agenda, Poules, etc.).
 */
function initializeViews() {
    const viewConfigs = [
        { name: 'agenda', constructor: 'AgendaView', containerId: 'agenda-view' },
        { name: 'pools', constructor: 'PoolsView', containerId: 'pools-view' },
        { name: 'teams', constructor: 'TeamsView', containerId: 'teams-view' },
        { name: 'matches', constructor: 'MatchesView', containerId: 'matches-view' },
        { name: 'penalties', constructor: 'PenaltiesView', containerId: 'penalties-view' }
    ];

    viewConfigs.forEach(config => {
        const container = document.getElementById(config.containerId);
        
        // DEBUG: Plus de détails sur le problème
        console.log(`Initializing ${config.name}:`, {
            constructor: config.constructor,
            constructorExists: !!window[config.constructor],
            containerId: config.containerId,
            containerExists: !!container
        });
        
        if (window[config.constructor] && container) {
            const viewInstance = new window[config.constructor](window.dataManager, container);
            if (typeof viewInstance.init === 'function') {
                viewInstance.init();
            }
            window[`${config.name}View`] = viewInstance;
        } else {
            if (!window[config.constructor]) {
                console.error(`❌ Constructor ${config.constructor} not found in window`);
            }
            if (!container) {
                console.error(`❌ Container #${config.containerId} not found in DOM`);
            }
            console.warn(`Vue ${config.name} ou son conteneur non trouvé.`);
        }
    });
}

/**
 * Enregistre les vues auprès du gestionnaire d'options.
 */
function initializeViewOptions() {
    if (window.agendaView) {
        window.viewOptionsManager.registerView('agenda', window.agendaView);
    }
    if (window.poolsView) {
        window.viewOptionsManager.registerView('pools', window.poolsView);
    }
    if (window.teamsView) {
        window.viewOptionsManager.registerView('teams', window.teamsView);
    }
    if (window.matchesView) {
        window.viewOptionsManager.registerView('matches', window.matchesView);
    }
    // Enregistrer d'autres vues ici à l'avenir...
}

/**
 * Initialise le panneau de filtres.
 */
function initializeFilters() {
    // Initialiser le système de filtres amélioré
    if (window.filterSystem && typeof window.filterSystem.init === 'function') {
        window.filterSystem.init();
    }

    // Initialiser le panneau de filtres (legacy)
    const filtersContainer = document.querySelector('.filters-container');
    if (!filtersContainer || !window.FilterPanel) return;

    window.filterPanel = new FilterPanel(window.dataManager, filtersContainer);
    window.filterPanel.onChange((filters) => {
        // Appliquer les filtres à toutes les vues enregistrées
        ['agendaView', 'poolsView', 'teamsView', 'matchesView'].forEach(viewName => {
            if (window[viewName] && typeof window[viewName].setFilters === 'function') {
                window[viewName].setFilters(filters);
            } else if (window[viewName] && typeof window[viewName].updateFilters === 'function') {
                window[viewName].updateFilters(filters);
            }
        });
    });
}

/**
 * Met à jour les indicateurs statistiques dans l'en-tête.
 */
function updateStatistics() {
    if (!window.dataManager) return;
    const data = window.dataManager.getData();
    
    const stats = {
        'stat-scheduled': data.matches.scheduled.length,
        'stat-unscheduled': data.matches.unscheduled.length,
        'stat-weeks': new Set(data.matches.scheduled.map(m => m.semaine).filter(Boolean)).size,
        'stat-pools': data.entities.poules.length,
        'stat-venues': data.entities.gymnases.length,
        'stat-modifications': window.modificationManager ? window.modificationManager.getModificationCount() : 0
    };

    for (const [id, value] of Object.entries(stats)) {
        const element = document.getElementById(id);
        if (element) element.textContent = value;
    }
}

/**
 * Configure les écouteurs d'événements globaux de l'interface.
 */
function setupEventListeners() {
    // Navigation entre les vues
    document.querySelectorAll('.view-btn').forEach(btn => {
        btn.addEventListener('click', () => switchView(btn.dataset.view));
    });

    // Actions de la barre d'outils
    const exportBtn = document.getElementById('btn-export-modifications');
    if (exportBtn) exportBtn.addEventListener('click', openExportModal);

    const resetBtn = document.getElementById('btn-reset-modifications');
    if (resetBtn) {
        resetBtn.addEventListener('click', () => {
            if (confirm('Voulez-vous vraiment réinitialiser toutes les modifications ?')) {
                window.modificationManager.clearAll();
                window.dataManager.revertAllModifications();
            }
        });
    }
    
    // Gestion des boutons de thème
    setupThemeControls();
    
    // Gestion des boutons de palette
    setupPaletteControls();
    
    // Gestion du niveau d'animations (si checkbox existe)
    setupAnimationControls();
    
    // Gestion des sidebars (collapse/expand)
    setupSidebarControls();
    
    // Gestion du redimensionnement des sidebars
    setupSidebarResize();
}

/**
 * Configure les contrôles de collapse des sidebars
 */
function setupSidebarControls() {
    const btnCollapseLeft = document.getElementById('btn-collapse-left');
    const btnCollapseRight = document.getElementById('btn-collapse-right');
    const btnShowLeft = document.getElementById('btn-show-left');
    const btnShowRight = document.getElementById('btn-show-right');
    const sidebarLeft = document.querySelector('.sidebar-left');
    const sidebarRight = document.querySelector('.sidebar-right');
    
    // Fonction helper pour toggle une sidebar
    function toggleSidebar(sidebar, btnCollapse, side) {
        if (!sidebar) return;
        
        const isCollapsed = sidebar.classList.contains('collapsed');
        
        if (isCollapsed) {
            // Expand
            sidebar.classList.remove('collapsed');
            if (btnCollapse) {
                btnCollapse.querySelector('span').textContent = side === 'left' ? '◀' : '▶';
                btnCollapse.setAttribute('title', 'Réduire');
            }
        } else {
            // Collapse
            sidebar.classList.add('collapsed');
            if (btnCollapse) {
                btnCollapse.querySelector('span').textContent = side === 'left' ? '▶' : '◀';
                btnCollapse.setAttribute('title', 'Développer');
            }
        }
        
        // Sauvegarder l'état
        localStorage.setItem(`sidebar-${side}-collapsed`, !isCollapsed);
        
        // Mettre à jour le layout
        setTimeout(() => updateGridColumns(), 50);
    }
    
    // Setup sidebar gauche
    if (btnCollapseLeft && sidebarLeft) {
        btnCollapseLeft.addEventListener('click', () => {
            toggleSidebar(sidebarLeft, btnCollapseLeft, 'left');
        });
        
        // Restaurer l'état sauvegardé
        const savedStateLeft = localStorage.getItem('sidebar-left-collapsed');
        if (savedStateLeft === 'true') {
            sidebarLeft.classList.add('collapsed');
            btnCollapseLeft.querySelector('span').textContent = '▶';
            btnCollapseLeft.setAttribute('title', 'Développer');
        }
    }
    
    // Bouton pour réafficher la sidebar gauche
    if (btnShowLeft && sidebarLeft) {
        btnShowLeft.addEventListener('click', () => {
            toggleSidebar(sidebarLeft, btnCollapseLeft, 'left');
        });
    }
    
    // Setup sidebar droite
    if (btnCollapseRight && sidebarRight) {
        btnCollapseRight.addEventListener('click', () => {
            toggleSidebar(sidebarRight, btnCollapseRight, 'right');
        });
        
        // Restaurer l'état sauvegardé
        const savedStateRight = localStorage.getItem('sidebar-right-collapsed');
        if (savedStateRight === 'true') {
            sidebarRight.classList.add('collapsed');
            btnCollapseRight.querySelector('span').textContent = '◀';
            btnCollapseRight.setAttribute('title', 'Développer');
        }
    }
    
    // Bouton pour réafficher la sidebar droite
    if (btnShowRight && sidebarRight) {
        btnShowRight.addEventListener('click', () => {
            toggleSidebar(sidebarRight, btnCollapseRight, 'right');
        });
    }
    
    // Ajouter support du clavier (Ctrl+B pour gauche, Ctrl+Shift+B pour droite)
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 'b') {
            e.preventDefault();
            if (e.shiftKey) {
                toggleSidebar(sidebarRight, btnCollapseRight, 'right');
            } else {
                toggleSidebar(sidebarLeft, btnCollapseLeft, 'left');
            }
        }
    });
}

/**
 * Configure le redimensionnement des sidebars par drag & drop
 */
function setupSidebarResize() {
    const resizeHandleLeft = document.getElementById('resize-handle-left');
    const resizeHandleRight = document.getElementById('resize-handle-right');
    const sidebarLeft = document.querySelector('.sidebar-left');
    const sidebarRight = document.querySelector('.sidebar-right');
    
    const MIN_WIDTH = 250;
    const MAX_WIDTH = 600;
    const DEFAULT_LEFT_WIDTH = 280;
    const DEFAULT_RIGHT_WIDTH = 320;
    
    let isResizing = false;
    let currentSidebar = null;
    let currentHandle = null;
    let startX = 0;
    let startWidth = 0;
    
    // Fonction pour mettre à jour le grid layout
    function updateGridColumns() {
        const mainLayout = document.querySelector('.main-layout');
        if (!mainLayout) return;
        
        const leftWidth = sidebarLeft && !sidebarLeft.classList.contains('collapsed') 
            ? (sidebarLeft.offsetWidth || DEFAULT_LEFT_WIDTH) + 'px'
            : '0px';
        const rightWidth = sidebarRight && !sidebarRight.classList.contains('collapsed') 
            ? (sidebarRight.offsetWidth || DEFAULT_RIGHT_WIDTH) + 'px'
            : '0px';
        
        const leftHandle = leftWidth !== '0px' ? '4px' : '0px';
        const rightHandle = rightWidth !== '0px' ? '4px' : '0px';
        
        mainLayout.style.gridTemplateColumns = `${leftWidth} ${leftHandle} 1fr ${rightHandle} ${rightWidth}`;
    }
    
    // Exposer globalement pour être appelée par d'autres fonctions
    window.updateGridColumns = updateGridColumns;
    
    // Restaurer les largeurs sauvegardées
    function restoreSidebarWidths() {
        const savedLeftWidth = localStorage.getItem('sidebar-left-width');
        const savedRightWidth = localStorage.getItem('sidebar-right-width');
        
        if (sidebarLeft && savedLeftWidth) {
            const width = parseInt(savedLeftWidth);
            if (width >= MIN_WIDTH && width <= MAX_WIDTH) {
                sidebarLeft.style.width = width + 'px';
            }
        }
        
        if (sidebarRight && savedRightWidth) {
            const width = parseInt(savedRightWidth);
            if (width >= MIN_WIDTH && width <= MAX_WIDTH) {
                sidebarRight.style.width = width + 'px';
            }
        }
        
        updateGridColumns();
    }
    
    // Restaurer au chargement
    restoreSidebarWidths();
    
    // Double-clic pour reset à la largeur par défaut
    function setupDoubleClickReset(handle, sidebar, defaultWidth) {
        if (!handle || !sidebar) return;
        
        handle.addEventListener('dblclick', () => {
            sidebar.style.width = defaultWidth + 'px';
            localStorage.setItem(`sidebar-${sidebar.classList.contains('sidebar-left') ? 'left' : 'right'}-width`, defaultWidth);
            updateGridColumns();
            
            // Animation de feedback
            handle.style.transform = 'scaleX(2)';
            setTimeout(() => {
                handle.style.transform = '';
            }, 200);
        });
    }
    
    setupDoubleClickReset(resizeHandleLeft, sidebarLeft, DEFAULT_LEFT_WIDTH);
    setupDoubleClickReset(resizeHandleRight, sidebarRight, DEFAULT_RIGHT_WIDTH);
    
    // Démarrer le resize
    function startResize(e, handle, sidebar) {
        if (!sidebar || sidebar.classList.contains('collapsed')) return;
        
        isResizing = true;
        currentHandle = handle;
        currentSidebar = sidebar;
        startX = e.clientX;
        startWidth = sidebar.offsetWidth;
        
        handle.classList.add('resizing');
        document.body.classList.add('resizing');
        
        e.preventDefault();
    }
    
    // Arrêter le resize
    function stopResize() {
        if (!isResizing) return;
        
        isResizing = false;
        
        if (currentHandle) {
            currentHandle.classList.remove('resizing');
        }
        
        document.body.classList.remove('resizing');
        
        // Sauvegarder la largeur finale
        if (currentSidebar) {
            const side = currentSidebar.classList.contains('sidebar-left') ? 'left' : 'right';
            localStorage.setItem(`sidebar-${side}-width`, currentSidebar.offsetWidth);
        }
        
        currentHandle = null;
        currentSidebar = null;
    }
    
    // Effectuer le resize
    function resize(e) {
        if (!isResizing || !currentSidebar) return;
        
        const isLeft = currentSidebar.classList.contains('sidebar-left');
        const delta = isLeft ? (e.clientX - startX) : (startX - e.clientX);
        const newWidth = Math.max(MIN_WIDTH, Math.min(MAX_WIDTH, startWidth + delta));
        
        currentSidebar.style.width = newWidth + 'px';
        updateGridColumns();
    }
    
    // Event listeners pour sidebar gauche
    if (resizeHandleLeft && sidebarLeft) {
        resizeHandleLeft.addEventListener('mousedown', (e) => {
            startResize(e, resizeHandleLeft, sidebarLeft);
        });
    }
    
    // Event listeners pour sidebar droite
    if (resizeHandleRight && sidebarRight) {
        resizeHandleRight.addEventListener('mousedown', (e) => {
            startResize(e, resizeHandleRight, sidebarRight);
        });
    }
    
    // Event listeners globaux
    document.addEventListener('mousemove', resize);
    document.addEventListener('mouseup', stopResize);
    
    // Mettre à jour le layout au resize de la fenêtre
    window.addEventListener('resize', () => {
        updateGridColumns();
    });
    
    // Mettre à jour le layout après un court délai (pour laisser le temps aux animations)
    setTimeout(() => {
        updateGridColumns();
    }, 100);
}

/**
 * Bascule vers une nouvelle vue.
 * @param {string} viewName - Le nom de la vue à afficher ('agenda', 'pools', 'matches', etc.).
 */
function switchView(viewName) {
    // Met à jour l'état actif des boutons de navigation
    document.querySelectorAll('.view-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.view === viewName);
    });
    
    // Affiche le conteneur de la vue correspondante
    document.querySelectorAll('.view-container').forEach(container => {
        container.classList.toggle('active', container.dataset.viewContent === viewName);
    });

    // Affiche/masque le filtre de statut selon la vue
    const statusFilter = document.getElementById('filter-section-status');
    if (statusFilter) {
        statusFilter.style.display = viewName === 'matches' ? 'block' : 'none';
    }

    // Met à jour les options dans la barre latérale
    window.viewOptionsManager.switchView(viewName);

    // Déclenche le rendu de la vue activée
    const viewInstance = window[`${viewName}View`];
    if (viewInstance && typeof viewInstance.render === 'function') {
        viewInstance.render();
    }
}

/**
 * ==================== GESTION DU THÈME ET DES ANIMATIONS ====================
 */

/**
 * Configure les boutons de sélection de thème.
 */
function setupThemeControls() {
    const themeButtons = document.querySelectorAll('.theme-btn');
    
    themeButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const theme = btn.dataset.theme;
            if (theme) {
                setTheme(theme);
                
                // Mettre à jour les boutons actifs
                themeButtons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            }
        });
    });
}

/**
 * Configure les boutons de sélection de palette de couleurs.
 */
function setupPaletteControls() {
    const paletteButtons = document.querySelectorAll('.palette-btn');
    
    paletteButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const palette = btn.dataset.palette;
            if (palette) {
                setPalette(palette);
                
                // Mettre à jour les boutons actifs
                paletteButtons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            }
        });
    });
}

/**
 * Applique une palette de couleurs à l'application.
 * @param {string} palette - 'purple', 'ocean', 'sunset', ou 'forest'
 */
function setPalette(palette) {
    const html = document.documentElement;
    html.setAttribute('data-palette', palette);
    localStorage.setItem('pycalendar-palette', palette);
}

/**
 * Charge la palette depuis le localStorage au démarrage.
 */
function loadSavedPalette() {
    const savedPalette = localStorage.getItem('pycalendar-palette') || 'purple';
    setPalette(savedPalette);
    
    // Mettre à jour le bouton actif
    const activeBtn = document.querySelector(`.palette-btn[data-palette="${savedPalette}"]`);
    if (activeBtn) {
        document.querySelectorAll('.palette-btn').forEach(btn => btn.classList.remove('active'));
        activeBtn.classList.add('active');
    }
}

/**
 * Configure les contrôles du niveau d'animation.
 */
function setupAnimationControls() {
    const animCheckbox = document.getElementById('opt-animations');
    
    if (animCheckbox) {
        animCheckbox.addEventListener('change', () => {
            const level = animCheckbox.checked ? 1 : 0;
            setAnimationLevel(level);
        });
        
        // Charger le niveau sauvegardé
        const savedLevel = localStorage.getItem('pycalendar-animation-level') || '1';
        setAnimationLevel(parseInt(savedLevel));
        animCheckbox.checked = savedLevel !== '0';
    }
}

/**
 * Applique un niveau d'animation à l'application.
 * @param {number} level - 0 (none), 1 (subtle), 2 (moderate), 3 (dynamic)
 */
function setAnimationLevel(level) {
    const html = document.documentElement;
    html.setAttribute('data-animation-level', level.toString());
    localStorage.setItem('pycalendar-animation-level', level.toString());
}

/**
 * Charge le thème depuis le localStorage au démarrage.
 */
function loadSavedTheme() {
    const savedTheme = localStorage.getItem('pycalendar-theme') || 'light';
    setTheme(savedTheme);
    
    // Mettre à jour le bouton actif
    const activeBtn = document.querySelector(`.theme-btn[data-theme="${savedTheme}"]`);
    if (activeBtn) {
        document.querySelectorAll('.theme-btn').forEach(btn => btn.classList.remove('active'));
        activeBtn.classList.add('active');
    }
}

/**
 * Applique un thème à l'application.
 * @param {string} theme - 'light' ou 'dark'
 */
function setTheme(theme) {
    const html = document.documentElement;
    html.setAttribute('data-theme', theme);
    localStorage.setItem('pycalendar-theme', theme);
}

/**
 * Affiche un message d'erreur fatal dans la page.
 */
function showError(message) {
    const container = document.querySelector('.app-container') || document.body;
    container.innerHTML = `<div class="error-state">
        <h3>Erreur critique</h3>
        <p>${message}</p>
        <p>Veuillez vérifier la console pour plus de détails.</p>
    </div>`;
    console.error(message);
}

/**
 * ==================== GESTION DES MODALES ====================
 */

/**
 * Ouvre la modale d'export des modifications.
 */
function openExportModal() {
    const modal = document.getElementById('modal-export');
    if (!modal) return;
    
    const count = window.modificationManager ? window.modificationManager.getModificationCount() : 0;
    const countElement = document.getElementById('export-count');
    if (countElement) {
        countElement.textContent = count;
    }
    
    // Générer un nom de fichier par défaut
    const date = new Date().toISOString().split('T')[0];
    const filenameInput = document.getElementById('export-filename');
    if (filenameInput) {
        filenameInput.value = `pycalendar_modifications_${date}.json`;
    }
    
    modal.classList.remove('hidden');
}

/**
 * Ferme la modale d'export.
 */
function closeExportModal() {
    const modal = document.getElementById('modal-export');
    if (modal) {
        modal.classList.add('hidden');
    }
}

/**
 * Exporte les modifications et télécharge le fichier JSON.
 */
function exportModifications() {
    if (window.modificationManager) {
        const filenameInput = document.getElementById('export-filename');
        const filename = filenameInput ? filenameInput.value : null;
        window.modificationManager.exportAndDownload(filename);
        closeExportModal();
    }
}

/**
 * Ouvre la modale d'aide.
 */
function openHelpModal() {
    const modal = document.getElementById('modal-help');
    if (modal) {
        modal.classList.remove('hidden');
    }
}

/**
 * Ferme la modale d'aide.
 */
function closeHelpModal() {
    const modal = document.getElementById('modal-help');
    if (modal) {
        modal.classList.add('hidden');
    }
}

// Exposer les fonctions modales globalement pour les onclick dans le HTML
if (typeof window !== 'undefined') {
    window.openExportModal = openExportModal;
    window.closeExportModal = closeExportModal;
    window.exportModifications = exportModifications;
    window.openHelpModal = openHelpModal;
    window.closeHelpModal = closeHelpModal;
}
