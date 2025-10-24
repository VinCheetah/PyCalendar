/**
 * PyCalendar Pro - Gestion des Filtres
 * Gère tous les filtres et préférences d'affichage
 */

class FilterManager {
    constructor() {
        this.filters = {
            gender: '',
            institution: '',
            team: '',
            pool: '',
            venue: '',
            week: ''
        };
        
        this.preferences = {
            showPreferences: false,
            showInstitutions: true,
            showGenreBadges: true,
            showWeekBadges: false, // Badge de semaine (par défaut désactivé)
            showPoolBadges: false, // Badge de poule (par défaut désactivé)
            showAvailableSlots: true,
            columnsCount: 3, // Nombre de colonnes (2 à 8)
            timeSlotMinutes: 60, // 30, 60 ou 120 (pour la vue grille)
            viewMode: 'total', // 'total', 'day', 'team', 'venue'
            colorMode: 'genre' // 'genre', 'level', 'both', 'pool', 'institution'
        };
        
        this.callbacks = [];
        this.loadFromStorage();
    }

    /**
     * Charge les préférences depuis localStorage
     */
    loadFromStorage() {
        const stored = Utils.loadPreferences();
        if (stored) {
            // Migration depuis ancien système viewSize vers columnsCount
            if (stored.viewSize && !stored.columnsCount) {
                const viewSizeMap = { 'compact': 3, 'normal': 4, 'large': 5 };
                stored.columnsCount = viewSizeMap[stored.viewSize] || 3;
                delete stored.viewSize;
            }
            this.preferences = { ...this.preferences, ...stored };
            this.applyPreferences();
        }
    }

    /**
     * Sauvegarde les préférences
     */
    saveToStorage() {
        Utils.savePreferences(this.preferences);
    }

    /**
     * Applique les préférences visuelles
     */
    applyPreferences() {
        const container = document.querySelector('.app-container');
        if (!container) {
            console.error('❌ Container .app-container non trouvé !');
            return;
        }

        // Nombre de colonnes
        // Supprimer toutes les anciennes classes view-*
        container.classList.remove('view-2', 'view-3', 'view-4', 'view-5', 'view-6', 'view-7', 'view-8');
        container.classList.remove('view-compact', 'view-normal', 'view-large'); // anciennes classes
        
        // Ajouter la nouvelle classe
        const colClass = `view-${this.preferences.columnsCount}`;
        container.classList.add(colClass);

        // Horaires préférés
        if (this.preferences.showPreferences) {
            container.classList.add('show-preferences');
        } else {
            container.classList.remove('show-preferences');
        }

        // Institutions
        if (this.preferences.showInstitutions) {
            container.classList.remove('hide-institutions');
        } else {
            container.classList.add('hide-institutions');
        }
        
        // Badges genre
        if (this.preferences.showGenreBadges) {
            container.classList.remove('hide-genre-badges');
        } else {
            container.classList.add('hide-genre-badges');
        }
        
        // Badges semaine
        if (this.preferences.showWeekBadges) {
            container.classList.remove('hide-week-badges');
        } else {
            container.classList.add('hide-week-badges');
        }
        
        // Badges poule
        if (this.preferences.showPoolBadges) {
            container.classList.remove('hide-pool-badges');
        } else {
            container.classList.add('hide-pool-badges');
        }
        
        // Mode de coloration des cartes
        // Retirer toutes les classes de mode de couleur
        container.classList.remove('color-genre', 'color-level', 'color-both', 'color-pool', 'color-institution');
        // Ajouter la classe du mode actuel
        container.classList.add(`color-${this.preferences.colorMode}`);
        
        // Mise à jour des toggles UI
        this.updateToggleUI('togglePreferences', this.preferences.showPreferences);
        this.updateToggleUI('toggleInstitutions', this.preferences.showInstitutions);
        this.updateToggleUI('toggleGenreBadges', this.preferences.showGenreBadges);
        this.updateToggleUI('toggleWeekBadges', this.preferences.showWeekBadges);
        this.updateToggleUI('togglePoolBadges', this.preferences.showPoolBadges);
        this.updateToggleUI('toggleAvailableSlots', this.preferences.showAvailableSlots);
    }

    /**
     * Met à jour l'UI d'un toggle
     */
    updateToggleUI(id, active) {
        const element = document.getElementById(id);
        if (element) {
            if (active) {
                element.classList.add('active');
            } else {
                element.classList.remove('active');
            }
        }
    }

    /**
     * Met à jour la visibilité des options selon l'onglet actif
     */
    updateDisplayOptionsVisibility(activeTab) {
        // Récupérer tous les éléments avec data-visible-tabs
        const elements = document.querySelectorAll('[data-visible-tabs]');
        
        elements.forEach(element => {
            const visibleTabs = element.getAttribute('data-visible-tabs').split(',').map(t => t.trim());
            
            // Si l'onglet actif est dans la liste, afficher l'élément
            if (visibleTabs.includes(activeTab)) {
                element.style.display = 'flex';
            } else {
                element.style.display = 'none';
            }
        });
    }

    /**
     * Définit un filtre
     */
    setFilter(name, value) {
        this.filters[name] = value;
        this.notifyChange();
    }

    /**
     * Définit une préférence
     */
    setPreference(name, value) {
        this.preferences[name] = value;
        this.applyPreferences();
        this.saveToStorage();
        this.notifyChange();
    }

    /**
     * Bascule une préférence booléenne
     */
    togglePreference(name) {
        this.preferences[name] = !this.preferences[name];
        this.applyPreferences();
        this.saveToStorage();
        this.notifyChange();
    }

    /**
     * Réinitialise tous les filtres
     */
    resetFilters() {
        this.filters = {
            gender: '',
            institution: '',
            team: '',
            pool: '',
            venue: '',
            week: ''
        };
        this.notifyChange();
    }

    /**
     * Réinitialise toutes les préférences d'affichage
     */
    resetDisplayPreferences() {
        this.preferences = {
            showPreferences: false,
            showInstitutions: true,
            showGenreBadges: true,
            showWeekBadges: false,
            showPoolBadges: false,
            showAvailableSlots: true,
            columnsCount: 3,
            timeSlotMinutes: 60,
            viewMode: 'total',
            colorMode: 'genre'
        };
        this.applyPreferences();
        this.saveToStorage();
        this.notifyChange();
    }

    /**
     * Enregistre un callback appelé lors des changements
     */
    onChange(callback) {
        this.callbacks.push(callback);
    }

    /**
     * Notifie tous les callbacks
     */
    notifyChange() {
        this.callbacks.forEach(cb => cb(this.filters, this.preferences));
    }

    /**
     * Obtient les matchs filtrés
     */
    getFilteredMatches(matches) {
        return Utils.filterMatches(matches, this.filters);
    }

    /**
     * Obtient les matchs non planifiés filtrés
     */
    getFilteredUnscheduled(unscheduled) {
        return Utils.filterUnscheduled(unscheduled, this.filters);
    }

    /**
     * Initialise les éléments UI des filtres
     */
    initializeUI(stats) {
        this.populateFilters(stats);
        this.setupEventListeners();
        this.setupZoomControl();
        this.setupViewModeControl();
    }

    /**
     * Remplit les listes déroulantes
     */
    populateFilters(stats) {
        // Institution
        this.populateSelect('filterInstitution', stats.institutions, (value) => {
            this.setFilter('institution', value);
            this.updateTeamFilter(stats);
        });

        // Team
        this.populateSelect('filterTeam', stats.teams, (value) => {
            this.setFilter('team', value);
        });

        // Pool
        this.populateSelect('filterPool', stats.pools, (value) => {
            this.setFilter('pool', value);
        });

        // Venue
        this.populateSelect('filterVenue', stats.venues, (value) => {
            this.setFilter('venue', value);
        });

        // Week
        const weekOptions = stats.weeks.map(w => ({ value: w, label: `Semaine ${w}` }));
        this.populateSelect('filterWeek', weekOptions, (value) => {
            this.setFilter('week', value);
        }, true);
    }

    /**
     * Remplit un select
     */
    populateSelect(id, options, onChange, useObjectFormat = false) {
        const select = document.getElementById(id);
        if (!select) return;

        // Garder la première option (Tous...)
        while (select.options.length > 1) {
            select.remove(1);
        }

        const items = useObjectFormat ? options : options.map(v => ({ value: v, label: v }));
        
        items.forEach(item => {
            const opt = document.createElement('option');
            opt.value = item.value;
            opt.textContent = item.label;
            select.appendChild(opt);
        });

        select.addEventListener('change', (e) => onChange(e.target.value));
    }

    /**
     * Met à jour le filtre d'équipes selon institution et genre
     */
    updateTeamFilter(stats) {
        const teamSelect = document.getElementById('filterTeam');
        if (!teamSelect) return;

        const selectedTeam = this.filters.team;
        
        teamSelect.innerHTML = '<option value="">Toutes les équipes</option>';
        
        // Filtrer les équipes
        let teams = stats.teams;
        
        if (this.filters.institution) {
            const instTeams = new Set();
            window.matchsData.forEach(m => {
                if (m.institution1 === this.filters.institution) instTeams.add(m.equipe1);
                if (m.institution2 === this.filters.institution) instTeams.add(m.equipe2);
            });
            teams = Array.from(instTeams).sort();
        }
        
        if (this.filters.gender) {
            const genderTeams = new Set();
            window.matchsData.forEach(m => {
                if (m.equipe1_genre === this.filters.gender) genderTeams.add(m.equipe1);
                if (m.equipe2_genre === this.filters.gender) genderTeams.add(m.equipe2);
            });
            teams = teams.filter(t => genderTeams.has(t));
        }
        
        teams.forEach(team => {
            const opt = document.createElement('option');
            opt.value = team;
            opt.textContent = team;
            if (team === selectedTeam) opt.selected = true;
            teamSelect.appendChild(opt);
        });
        
        if (this.filters.team && !teams.includes(this.filters.team)) {
            this.setFilter('team', '');
        }
    }

    /**
     * Configure les event listeners
     */
    setupEventListeners() {
        // Boutons de genre
        document.querySelectorAll('.gender-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const gender = btn.dataset.gender;
                this.setFilter('gender', gender);
                
                // Mise à jour UI
                document.querySelectorAll('.gender-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                
                // Mise à jour du filtre d'équipes
                const stats = Utils.calculateStats(window.matchsData);
                this.updateTeamFilter(stats);
            });
        });

        // Bouton reset filtres
        const resetBtn = document.querySelector('.btn-reset');
        if (resetBtn && !resetBtn.id) { // Only the filters reset button (no id)
            resetBtn.addEventListener('click', () => {
                this.resetFilters();
                
                // Reset UI
                document.querySelectorAll('.gender-btn').forEach(btn => {
                    btn.classList.remove('active');
                    if (btn.dataset.gender === '') btn.classList.add('active');
                });
                
                document.getElementById('filterInstitution').value = '';
                document.getElementById('filterTeam').value = '';
                document.getElementById('filterPool').value = '';
                document.getElementById('filterVenue').value = '';
                document.getElementById('filterWeek').value = '';
                
                const stats = Utils.calculateStats(window.matchsData);
                this.updateTeamFilter(stats);
            });
        }

        // Bouton reset affichage
        const resetDisplayBtn = document.getElementById('btnResetDisplay');
        if (resetDisplayBtn) {
            resetDisplayBtn.addEventListener('click', () => {
                this.resetDisplayPreferences();
                
                // Reset UI du zoom (non géré par applyPreferences)
                this.updateZoomUI();
                
                // Reset UI du sélecteur de couleur
                const colorModeSelect = document.getElementById('colorModeSelect');
                if (colorModeSelect) {
                    colorModeSelect.value = this.preferences.colorMode;
                }
            });
        }

        // Toggles
        this.setupToggle('togglePreferences', 'showPreferences');
        this.setupToggle('toggleInstitutions', 'showInstitutions');
        this.setupToggle('toggleGenreBadges', 'showGenreBadges');
        this.setupToggle('toggleWeekBadges', 'showWeekBadges');
        this.setupToggle('togglePoolBadges', 'showPoolBadges');
        this.setupToggle('toggleAvailableSlots', 'showAvailableSlots');
        
        // Sélecteur de mode de couleur
        const colorModeSelect = document.getElementById('colorModeSelect');
        if (colorModeSelect) {
            // Définir la valeur initiale
            colorModeSelect.value = this.preferences.colorMode;
            
            colorModeSelect.addEventListener('change', (e) => {
                this.setPreference('colorMode', e.target.value);
            });
        }
        
        // Boutons de collapse
        this.setupCollapseButtons();
    }

    /**
     * Configure un toggle
     */
    setupToggle(id, prefName) {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener('click', () => {
                this.togglePreference(prefName);
            });
        }
    }

    /**
     * Met à jour l'UI des contrôles de zoom (colonnes et grid)
     */
    updateZoomUI() {
        this.updateZoomCardDisplay();
        this.updateZoomGridDisplay();
    }

    /**
     * Configure le contrôle de zoom
     */
    setupZoomControl() {
        // ===== COLONNES CARDS (pour vues en liste) =====
        const zoomCardIn = document.getElementById('zoomCardIn');
        const zoomCardOut = document.getElementById('zoomCardOut');
        
        if (zoomCardIn) {
            zoomCardIn.addEventListener('click', () => {
                // Augmenter le nombre de colonnes : max 8
                if (this.preferences.columnsCount < 8) {
                    this.setPreference('columnsCount', this.preferences.columnsCount + 1);
                }
                this.updateZoomCardDisplay();
            });
        }
        
        if (zoomCardOut) {
            zoomCardOut.addEventListener('click', () => {
                // Réduire le nombre de colonnes : min 2
                if (this.preferences.columnsCount > 2) {
                    this.setPreference('columnsCount', this.preferences.columnsCount - 1);
                }
                this.updateZoomCardDisplay();
            });
        }
        
        // ===== ZOOM GRID (pour vue grille) =====
        const zoomGridIn = document.getElementById('zoomGridIn');
        const zoomGridOut = document.getElementById('zoomGridOut');
        
        if (zoomGridIn) {
            zoomGridIn.addEventListener('click', () => {
                // Augmenter la taille des créneaux (zoomer)
                if (this.preferences.timeSlotMinutes === 30) {
                    this.setPreference('timeSlotMinutes', 60);
                } else if (this.preferences.timeSlotMinutes === 60) {
                    this.setPreference('timeSlotMinutes', 120);
                }
                this.updateZoomGridDisplay();
            });
        }
        
        if (zoomGridOut) {
            zoomGridOut.addEventListener('click', () => {
                // Réduire la taille des créneaux (dézoomer)
                if (this.preferences.timeSlotMinutes === 120) {
                    this.setPreference('timeSlotMinutes', 60);
                } else if (this.preferences.timeSlotMinutes === 60) {
                    this.setPreference('timeSlotMinutes', 30);
                }
                this.updateZoomGridDisplay();
            });
        }
        
        this.updateZoomCardDisplay();
        this.updateZoomGridDisplay();
    }

    /**
     * Met à jour l'affichage du nombre de colonnes
     */
    updateZoomCardDisplay() {
        const display = document.getElementById('zoomCardValue');
        if (display) {
            const count = this.preferences.columnsCount || 3;
            display.textContent = `${count} colonnes`;
        }
    }

    /**
     * Met à jour l'affichage du zoom grid
     */
    updateZoomGridDisplay() {
        const display = document.getElementById('zoomGridValue');
        if (display) {
            const labels = {
                30: '30min',
                60: '60min',
                120: '120min'
            };
            display.textContent = labels[this.preferences.timeSlotMinutes] || '60min';
        }
    }

    /**
     * Configure le contrôle du mode de vue
     */
    setupViewModeControl() {
        document.querySelectorAll('.view-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const mode = btn.dataset.mode;
                this.setPreference('viewMode', mode);
                
                // Mise à jour UI
                document.querySelectorAll('.view-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            });
        });
        
        // Active le bouton correspondant au mode actuel
        const activeBtn = document.querySelector(`.view-btn[data-mode="${this.preferences.viewMode}"]`);
        if (activeBtn) {
            activeBtn.classList.add('active');
        }
    }

    /**
     * Configure les boutons de collapse/expand
     */
    setupCollapseButtons() {
        // Bouton pour les filtres
        const collapseFiltersBtn = document.getElementById('collapseFilters');
        const filtersContent = document.getElementById('filtersContent');
        
        if (collapseFiltersBtn && filtersContent) {
            collapseFiltersBtn.addEventListener('click', () => {
                collapseFiltersBtn.classList.toggle('collapsed');
                filtersContent.classList.toggle('collapsed');
                
                // Sauvegarde de l'état
                const isCollapsed = filtersContent.classList.contains('collapsed');
                localStorage.setItem('filtersCollapsed', isCollapsed);
            });
            
            // Restauration de l'état
            const filtersCollapsed = localStorage.getItem('filtersCollapsed') === 'true';
            if (filtersCollapsed) {
                collapseFiltersBtn.classList.add('collapsed');
                filtersContent.classList.add('collapsed');
            }
        }

        // Bouton pour les options
        const collapseOptionsBtn = document.getElementById('collapseOptions');
        const optionsContent = document.getElementById('optionsContent');
        
        if (collapseOptionsBtn && optionsContent) {
            collapseOptionsBtn.addEventListener('click', () => {
                collapseOptionsBtn.classList.toggle('collapsed');
                optionsContent.classList.toggle('collapsed');
                
                // Sauvegarde de l'état
                const isCollapsed = optionsContent.classList.contains('collapsed');
                localStorage.setItem('optionsCollapsed', isCollapsed);
            });
            
            // Restauration de l'état
            const optionsCollapsed = localStorage.getItem('optionsCollapsed') === 'true';
            if (optionsCollapsed) {
                collapseOptionsBtn.classList.add('collapsed');
                optionsContent.classList.add('collapsed');
            }
        }
    }

    /**
     * Met à jour la visibilité des options d'affichage selon l'onglet actif
     */
    updateDisplayOptionsVisibility(currentTab) {
        // Afficher/masquer les toggles selon l'onglet actif
        document.querySelectorAll('.toggle-container').forEach(toggle => {
            const visibleTabs = toggle.getAttribute('data-visible-tabs');
            if (visibleTabs) {
                const tabs = visibleTabs.split(',');
                if (tabs.includes(currentTab)) {
                    toggle.style.display = 'flex';
                } else {
                    toggle.style.display = 'none';
                }
            }
        });
        
        // Afficher/masquer le sélecteur de mode de couleur selon l'onglet actif
        const colorModeSelector = document.querySelector('.color-mode-selector');
        if (colorModeSelector) {
            const visibleTabs = colorModeSelector.getAttribute('data-visible-tabs');
            if (visibleTabs) {
                const tabs = visibleTabs.split(',');
                if (tabs.includes(currentTab)) {
                    colorModeSelector.style.display = 'block';
                } else {
                    colorModeSelector.style.display = 'none';
                }
            }
        }
        
        // Afficher/masquer les contrôles compacts selon l'onglet actif
        document.querySelectorAll('.compact-control').forEach(control => {
            const visibleTabs = control.getAttribute('data-visible-tabs');
            if (visibleTabs) {
                const tabs = visibleTabs.split(',');
                if (tabs.includes(currentTab)) {
                    control.style.display = 'flex';
                } else {
                    control.style.display = 'none';
                }
            }
        });
    }
}

// Export pour utilisation
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FilterManager;
}
