/**
 * filter-panel.js - Gestionnaire de panneau de filtres
 * 
 * Gère l'affichage et la logique des filtres pour toutes les vues.
 * Exposé globalement via window.FilterPanel
 */

window.FilterPanel = class FilterPanel {
    constructor(dataManager, container) {
        this.dataManager = dataManager;
        this.container = container;
        
        // État des filtres
        this.activeFilters = {
            gender: '',
            institution: '',
            pool: '',
            venue: '',
            week: ''
        };
        
        // Callbacks
        this.onFilterChange = null;
        
        // Initialiser
        this.init();
    }
    
    /**
     * Initialise le panneau
     */
    init() {
        this.render();
        this.attachEventListeners();
        this.loadFromStorage();
    }
    
    /**
     * Rendu du panneau
     */
    render() {
        const data = this.dataManager.getData();
        if (!data) return;
        
        // Extraire les valeurs uniques
        const genders = this._extractGenders(data);
        const institutions = this._extractInstitutions(data);
        const pools = this._extractPools(data);
        const venues = this._extractVenues(data);
        const weeks = this._extractWeeks(data);
        
        this.container.innerHTML = `
            <div class="filter-panel">
                <h3 class="filter-title">
                    <span class="filter-icon">🔍</span>
                    Filtres
                    <button class="filter-reset-btn" id="filter-reset" title="Réinitialiser">
                        🔄
                    </button>
                </h3>
                
                <div class="filters-grid">
                    ${this._renderFilter('gender', 'Genre', genders, {
                        'M': '♂ Masculin',
                        'F': '♀ Féminin'
                    })}
                    
                    ${this._renderFilter('institution', 'Institution', institutions)}
                    
                    ${this._renderFilter('pool', 'Poule', pools)}
                    
                    ${this._renderFilter('venue', 'Gymnase', venues)}
                    
                    ${this._renderFilter('week', 'Semaine', weeks, null, 'Semaine')}
                </div>
                
                <div class="filter-status">
                    <span id="filter-active-count">0</span> filtre(s) actif(s)
                </div>
            </div>
        `;
    }
    
    /**
     * Rendu d'un filtre individuel
     */
    _renderFilter(id, label, values, customLabels = null, prefix = '') {
        if (!values || values.length === 0) {
            return '';
        }
        
        const options = values.map(value => {
            const displayValue = customLabels && customLabels[value] 
                ? customLabels[value]
                : prefix ? `${prefix} ${value}` : value;
            
            return `<option value="${value}">${displayValue}</option>`;
        }).join('');
        
        return `
            <div class="filter-group">
                <label class="filter-label" for="filter-${id}">${label}</label>
                <select class="filter-select" id="filter-${id}" data-filter="${id}">
                    <option value="">Tous</option>
                    ${options}
                </select>
            </div>
        `;
    }
    
    /**
     * Attache les événements
     */
    attachEventListeners() {
        // Changement de filtre
        this.container.querySelectorAll('.filter-select').forEach(select => {
            select.addEventListener('change', (e) => {
                const filterType = e.target.dataset.filter;
                const value = e.target.value;
                this.setFilter(filterType, value);
            });
        });
        
        // Réinitialisation
        const resetBtn = this.container.querySelector('#filter-reset');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => this.resetFilters());
        }
    }
    
    /**
     * Définit un filtre
     */
    setFilter(type, value) {
        this.activeFilters[type] = value;
        this.saveToStorage();
        this.updateStatus();
        
        if (this.onFilterChange) {
            this.onFilterChange(this.activeFilters);
        }
    }
    
    /**
     * Réinitialise tous les filtres
     */
    resetFilters() {
        this.activeFilters = {
            gender: '',
            institution: '',
            pool: '',
            venue: '',
            week: ''
        };
        
        // Reset UI
        this.container.querySelectorAll('.filter-select').forEach(select => {
            select.value = '';
        });
        
        this.saveToStorage();
        this.updateStatus();
        
        if (this.onFilterChange) {
            this.onFilterChange(this.activeFilters);
        }
    }
    
    /**
     * Met à jour le statut
     */
    updateStatus() {
        const count = Object.values(this.activeFilters).filter(v => v !== '').length;
        const statusEl = this.container.querySelector('#filter-active-count');
        if (statusEl) {
            statusEl.textContent = count;
        }
    }
    
    /**
     * Applique les filtres à une liste de matchs
     */
    filterMatches(matches) {
        if (!matches) return [];
        
        return matches.filter(match => {
            // Récupérer les entités
            const data = this.dataManager.getData();
            const equipe1 = data.entities.equipes.find(e => e.id === match.equipes[0]);
            const equipe2 = data.entities.equipes.find(e => e.id === match.equipes[1]);
            
            if (!equipe1 || !equipe2) return false;
            
            // Filtre genre
            if (this.activeFilters.gender) {
                if (equipe1.genre !== this.activeFilters.gender) {
                    return false;
                }
            }
            
            // Filtre institution
            if (this.activeFilters.institution) {
                if (equipe1.institution !== this.activeFilters.institution &&
                    equipe2.institution !== this.activeFilters.institution) {
                    return false;
                }
            }
            
            // Filtre poule
            if (this.activeFilters.pool) {
                if (equipe1.poule !== this.activeFilters.pool) {
                    return false;
                }
            }
            
            // Filtre gymnase
            if (this.activeFilters.venue) {
                if (match.gymnase !== this.activeFilters.venue) {
                    return false;
                }
            }
            
            // Filtre semaine
            if (this.activeFilters.week) {
                if (match.semaine !== parseInt(this.activeFilters.week)) {
                    return false;
                }
            }
            
            return true;
        });
    }
    
    /**
     * Sauvegarde dans localStorage
     */
    saveToStorage() {
        try {
            localStorage.setItem('pycalendar_filters', JSON.stringify(this.activeFilters));
        } catch (e) {
            console.warn('Impossible de sauvegarder les filtres:', e);
        }
    }
    
    /**
     * Charge depuis localStorage
     */
    loadFromStorage() {
        try {
            const stored = localStorage.getItem('pycalendar_filters');
            if (stored) {
                const filters = JSON.parse(stored);
                this.activeFilters = { ...this.activeFilters, ...filters };
                
                // Appliquer aux selects
                Object.entries(this.activeFilters).forEach(([type, value]) => {
                    const select = this.container.querySelector(`#filter-${type}`);
                    if (select && value) {
                        select.value = value;
                    }
                });
                
                this.updateStatus();
            }
        } catch (e) {
            console.warn('Impossible de charger les filtres:', e);
        }
    }
    
    /**
     * Extrait les genres
     */
    _extractGenders(data) {
        const genders = new Set();
        data.entities.equipes.forEach(e => {
            if (e.genre) genders.add(e.genre);
        });
        return Array.from(genders).sort();
    }
    
    /**
     * Extrait les institutions
     */
    _extractInstitutions(data) {
        const institutions = new Set();
        data.entities.equipes.forEach(e => {
            if (e.institution) institutions.add(e.institution);
        });
        return Array.from(institutions).sort();
    }
    
    /**
     * Extrait les poules
     */
    _extractPools(data) {
        return data.entities.poules.map(p => p.id).sort();
    }
    
    /**
     * Extrait les gymnases
     */
    _extractVenues(data) {
        return data.entities.gymnases.map(g => g.id).sort();
    }
    
    /**
     * Extrait les semaines
     */
    _extractWeeks(data) {
        const weeks = new Set();
        data.matches.scheduled.forEach(m => {
            if (m.semaine) weeks.add(m.semaine);
        });
        return Array.from(weeks).sort((a, b) => a - b);
    }
    
    /**
     * Obtient les filtres actifs
     */
    getActiveFilters() {
        return { ...this.activeFilters };
    }
    
    /**
     * Définit un callback
     */
    onChange(callback) {
        this.onFilterChange = callback;
    }
};
