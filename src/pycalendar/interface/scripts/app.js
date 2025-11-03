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
        { name: 'cards', constructor: 'CardsView', containerId: 'cards-view' }
    ];

    viewConfigs.forEach(config => {
        const container = document.getElementById(config.containerId);
        if (window[config.constructor] && container) {
            const viewInstance = new window[config.constructor](window.dataManager, container);
            if (typeof viewInstance.init === 'function') {
                viewInstance.init();
            }
            window[`${config.name}View`] = viewInstance;
        } else {
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
        ['agendaView', 'poolsView', 'cardsView'].forEach(viewName => {
            if (window[viewName] && typeof window[viewName].setFilters === 'function') {
                window[viewName].setFilters(filters);
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
    
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) themeToggle.addEventListener('click', toggleTheme);
    
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
    
    if (btnCollapseLeft && sidebarLeft) {
        btnCollapseLeft.addEventListener('click', () => {
            sidebarLeft.classList.toggle('collapsed');
            const isCollapsed = sidebarLeft.classList.contains('collapsed');
            btnCollapseLeft.querySelector('span').textContent = isCollapsed ? '▶' : '◀';
            btnCollapseLeft.setAttribute('title', isCollapsed ? 'Développer' : 'Réduire');
            
            // Sauvegarder l'état
            localStorage.setItem('sidebar-left-collapsed', isCollapsed);
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
            sidebarLeft.classList.remove('collapsed');
            if (btnCollapseLeft) {
                btnCollapseLeft.querySelector('span').textContent = '◀';
                btnCollapseLeft.setAttribute('title', 'Réduire');
            }
            localStorage.setItem('sidebar-left-collapsed', 'false');
        });
    }
    
    if (btnCollapseRight && sidebarRight) {
        btnCollapseRight.addEventListener('click', () => {
            sidebarRight.classList.toggle('collapsed');
            const isCollapsed = sidebarRight.classList.contains('collapsed');
            btnCollapseRight.querySelector('span').textContent = isCollapsed ? '◀' : '▶';
            btnCollapseRight.setAttribute('title', isCollapsed ? 'Développer' : 'Réduire');
            
            // Sauvegarder l'état
            localStorage.setItem('sidebar-right-collapsed', isCollapsed);
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
            sidebarRight.classList.remove('collapsed');
            if (btnCollapseRight) {
                btnCollapseRight.querySelector('span').textContent = '▶';
                btnCollapseRight.setAttribute('title', 'Réduire');
            }
            localStorage.setItem('sidebar-right-collapsed', 'false');
        });
    }
}

/**
 * Configure le redimensionnement des sidebars par drag & drop
 */
function setupSidebarResize() {
    const resizeHandleLeft = document.getElementById('resize-handle-left');
    const resizeHandleRight = document.getElementById('resize-handle-right');
    const sidebarLeft = document.querySelector('.sidebar-left');
    const sidebarRight = document.querySelector('.sidebar-right');
    const mainLayout = document.querySelector('.main-layout');
    
    let isResizing = false;
    let currentHandle = null;
    
    // Récupérer les largeurs sauvegardées
    const savedLeftWidth = localStorage.getItem('sidebar-left-width') || '320px';
    const savedRightWidth = localStorage.getItem('sidebar-right-width') || '280px';
    
    if (sidebarLeft && !sidebarLeft.classList.contains('collapsed')) {
        sidebarLeft.style.width = savedLeftWidth;
    }
    if (sidebarRight && !sidebarRight.classList.contains('collapsed')) {
        sidebarRight.style.width = savedRightWidth;
    }
    
    // Mettre à jour le grid-template-columns
    updateGridColumns();
    
    function updateGridColumns() {
        if (!mainLayout) return;
        
        const leftWidth = sidebarLeft && !sidebarLeft.classList.contains('collapsed') 
            ? sidebarLeft.style.width || savedLeftWidth 
            : '0px';
        const rightWidth = sidebarRight && !sidebarRight.classList.contains('collapsed') 
            ? sidebarRight.style.width || savedRightWidth 
            : '0px';
        
        mainLayout.style.gridTemplateColumns = `${leftWidth} 4px 1fr 4px ${rightWidth}`;
    }
    
    function startResize(e, handle) {
        isResizing = true;
        currentHandle = handle;
        handle.classList.add('resizing');
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';
        e.preventDefault();
    }
    
    function stopResize() {
        if (!isResizing) return;
        
        isResizing = false;
        if (currentHandle) {
            currentHandle.classList.remove('resizing');
        }
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
        currentHandle = null;
        
        // Sauvegarder les largeurs
        if (sidebarLeft) {
            localStorage.setItem('sidebar-left-width', sidebarLeft.style.width);
        }
        if (sidebarRight) {
            localStorage.setItem('sidebar-right-width', sidebarRight.style.width);
        }
    }
    
    function resize(e) {
        if (!isResizing) return;
        
        if (currentHandle === resizeHandleLeft && sidebarLeft) {
            const newWidth = e.clientX;
            if (newWidth >= 250 && newWidth <= 600) {
                sidebarLeft.style.width = newWidth + 'px';
                updateGridColumns();
            }
        } else if (currentHandle === resizeHandleRight && sidebarRight) {
            const newWidth = window.innerWidth - e.clientX;
            if (newWidth >= 250 && newWidth <= 600) {
                sidebarRight.style.width = newWidth + 'px';
                updateGridColumns();
            }
        }
    }
    
    // Event listeners pour le resize
    if (resizeHandleLeft) {
        resizeHandleLeft.addEventListener('mousedown', (e) => startResize(e, resizeHandleLeft));
    }
    
    if (resizeHandleRight) {
        resizeHandleRight.addEventListener('mousedown', (e) => startResize(e, resizeHandleRight));
    }
    
    document.addEventListener('mousemove', resize);
    document.addEventListener('mouseup', stopResize);
    
    // Mettre à jour les colonnes quand on collapse/expand
    const observer = new MutationObserver(() => {
        updateGridColumns();
    });
    
    if (sidebarLeft) {
        observer.observe(sidebarLeft, { attributes: true, attributeFilter: ['class'] });
    }
    if (sidebarRight) {
        observer.observe(sidebarRight, { attributes: true, attributeFilter: ['class'] });
    }
}

/**
 * Bascule vers une nouvelle vue.
 * @param {string} viewName - Le nom de la vue à afficher ('agenda', 'pools', etc.).
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

    // Met à jour les options dans la barre latérale
    window.viewOptionsManager.switchView(viewName);

    // Déclenche le rendu de la vue activée
    const viewInstance = window[`${viewName}View`];
    if (viewInstance && typeof viewInstance.render === 'function') {
        viewInstance.render();
    }
}

/**
 * Gère le basculement du thème (clair/sombre).
 */
function toggleTheme() {
    const newTheme = document.body.classList.contains('dark-theme') ? 'light' : 'dark';
    setTheme(newTheme);
    localStorage.setItem('pycalendar-theme', newTheme);
}

/**
 * Charge le thème depuis le localStorage au démarrage.
 */
function loadSavedTheme() {
    const savedTheme = localStorage.getItem('pycalendar-theme') || 'light';
    setTheme(savedTheme);
}

/**
 * Applique un thème à l'application.
 * @param {string} theme - 'light' ou 'dark'.
 */
function setTheme(theme) {
    document.body.classList.toggle('dark-theme', theme === 'dark');
    document.body.classList.toggle('light-theme', theme === 'light');
    
    const themeIcon = document.getElementById('theme-icon');
    if (themeIcon) {
        themeIcon.textContent = theme === 'dark' ? '☀️' : '🌙';
    }
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
