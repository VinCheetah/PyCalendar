/**
 * app.js - Initialisation principale de l'application
 *
 * Expose `window.PyCalendarApp` pour orchestrer l'UI depuis n'importe où.
 */

const PyCalendarApp = {
    init() {
        try {
            const ui = window.PyCalendarUI || null;
            ui?.loadSavedTheme?.();
            ui?.loadSavedPalette?.();

            const solutionData = this.loadSolutionData();
            if (!solutionData) return;

            this.initializeManagers(solutionData);
            this.initializeViews();
            this.initializeViewOptions();
            this.initializeFilters();

            ui?.setupEventListeners?.(this);

            this.updateStatistics();
            this.switchView('pools');
        } catch (error) {
            this.notifyError(`Erreur critique d'initialisation: ${error.message}`);
            console.error(error);
        }
    },

    loadSolutionData() {
        const solutionDataElement = document.getElementById('solution-data');
        if (!solutionDataElement) {
            this.notifyError('Impossible de trouver les données du calendrier.');
            return null;
        }
        try {
            return JSON.parse(solutionDataElement.textContent);
        } catch (error) {
            this.notifyError('Format de données JSON invalide.');
            return null;
        }
    },

    initializeManagers(solutionData) {
        const solutionName = solutionData.metadata?.solution_name || 'unknown';

        window.dataManager = new DataManager(solutionData);
        window.modificationManager = new ModificationManager(solutionName);
        window.viewOptionsManager = new ViewOptionsManager(document.getElementById('view-options-container'));

        // Initialiser le gestionnaire de sport
        if (window.sportUtils) {
            window.sportUtils.init(window.dataManager);
            window.sportUtils.updatePageTitle();
            this.updateSportIcons();
        }

        if (!this._statsUpdater) {
            this._statsUpdater = () => this.updateStatistics();
        }

        window.dataManager.subscribe('matches', this._statsUpdater);
        window.modificationManager.subscribe(this._statsUpdater);
    },

    initializeViews() {
        const viewConfigs = [
            { name: 'agenda', constructor: 'AgendaView', containerId: 'agenda-view' },
            { name: 'pools', constructor: 'PoolsView', containerId: 'pools-view' },
            { name: 'teams', constructor: 'TeamsView', containerId: 'teams-view' },
            { name: 'matches', constructor: 'MatchesView', containerId: 'matches-view' },
            { name: 'penalties', constructor: 'PenaltiesView', containerId: 'penalties-view' }
        ];

        viewConfigs.forEach(config => {
            const container = document.getElementById(config.containerId);

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
    },

    initializeViewOptions() {
        const registrations = [
            ['agenda', window.agendaView],
            ['pools', window.poolsView],
            ['teams', window.teamsView],
            ['matches', window.matchesView],
            ['penalties', window.penaltiesView],
        ];

        registrations.forEach(([name, view]) => {
            if (view) {
                window.viewOptionsManager.registerView(name, view);
            }
        });
    },

    initializeFilters() {
        if (window.filterSystem && typeof window.filterSystem.init === 'function') {
            window.filterSystem.init();
        }
    },

    updateStatistics() {
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
    },

    switchView(viewName) {
        document.querySelectorAll('.view-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.view === viewName);
        });

        document.querySelectorAll('.view-container').forEach(container => {
            container.classList.toggle('active', container.dataset.viewContent === viewName);
        });

        const statusFilter = document.getElementById('filter-section-status');
        if (statusFilter) {
            statusFilter.classList.toggle('is-hidden', viewName !== 'matches');
        }

        if (window.viewOptionsManager) {
            window.viewOptionsManager.switchView(viewName);
        }

        const viewInstance = window[`${viewName}View`];
        if (viewInstance && typeof viewInstance.render === 'function') {
            viewInstance.render();
        }
    },

    notifyError(message) {
        if (typeof window !== 'undefined' && typeof window.showError === 'function') {
            window.showError(message);
        } else {
            console.error(message);
        }
    },

    updateSportIcons() {
        if (!window.sportUtils) return;
        
        const emoji = window.sportUtils.getEmoji();
        const name = window.sportUtils.getName();
        
        // Mettre à jour tous les éléments marqués avec data-sport-icon
        document.querySelectorAll('[data-sport-icon]').forEach(el => {
            el.textContent = emoji;
        });
        
        // Mettre à jour le bouton de la vue Matchs spécifiquement
        const matchViewBtn = document.querySelector('[data-sport-match-icon]');
        if (matchViewBtn) matchViewBtn.textContent = emoji;
        
        // Mettre à jour le sous-titre avec le nom du sport
        const logoSubtitle = document.querySelector('[data-sport-subtitle]');
        if (logoSubtitle) {
            logoSubtitle.textContent = `${name} - Fédération Française du Sport Universitaire`;
        }
        
        console.log(`🎯 Icônes de sport mises à jour: ${emoji} (${name})`);
    }
};

/**
 * Voir `scripts/app/ui-controls.js` et `scripts/app/modals.js` pour les contrôles et états globaux.
 */

document.addEventListener('DOMContentLoaded', () => PyCalendarApp.init());

if (typeof window !== 'undefined') {
    window.PyCalendarApp = PyCalendarApp;
    window.switchView = PyCalendarApp.switchView.bind(PyCalendarApp);
}
