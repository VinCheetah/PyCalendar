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
            equipe: '',
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
        
        // Extraire les valeurs avec filtrage intelligent
        const availableOptions = this._getAvailableOptions(data);
        
        this.container.innerHTML = `
            <div class="filter-panel" style="padding: 1rem; background: rgba(255, 255, 255, 0.95); border-radius: 12px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);">
                <h3 class="filter-title" style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.5rem; font-size: 1.125rem; font-weight: 700; color: #1e293b;">
                    <span style="display: flex; align-items: center; gap: 0.5rem;">
                        <span class="filter-icon">🔍</span>
                        Filtres
                    </span>
                    <button class="filter-reset-btn" id="filter-reset" title="Réinitialiser" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 8px; padding: 0.5rem 0.75rem; cursor: pointer; font-size: 1rem; transition: all 0.2s ease; box-shadow: 0 2px 6px rgba(102, 126, 234, 0.3);">
                        🔄
                    </button>
                </h3>
                
                <div class="filters-grid" style="display: flex; flex-direction: column; gap: 1rem;">
                    ${this._renderFilter('gender', 'Genre', availableOptions.genders, {
                        'M': '♂ Masculin',
                        'F': '♀ Féminin'
                    })}
                    
                    ${this._renderFilter('institution', 'Institution', availableOptions.institutions)}
                    
                    ${this._renderFilter('equipe', 'Équipe', availableOptions.equipes, null, '', true)}
                    
                    ${this._renderFilter('pool', 'Poule', availableOptions.pools)}
                    
                    ${this._renderFilter('venue', 'Gymnase', availableOptions.venues)}
                    
                    ${this._renderFilter('week', 'Semaine', availableOptions.weeks, null, 'Semaine')}
                </div>
                
                <div class="filter-status" style="margin-top: 1.5rem; padding-top: 1rem; border-top: 2px solid #e2e8f0; font-size: 0.875rem; color: #64748b; text-align: center; font-weight: 600;">
                    <span id="filter-active-count">0</span> filtre(s) actif(s)
                </div>
            </div>
        `;
    }
    
    /**
     * Rendu d'un filtre individuel
     */
    _renderFilter(id, label, values, customLabels = null, prefix = '', showEquipeFormat = false) {
        if (!values || values.length === 0) {
            return '';
        }
        
        const count = values.length;
        const options = values.map(value => {
            let displayValue;
            
            if (showEquipeFormat && typeof value === 'object') {
                // Format spécial pour les équipes: "Institution (numéro)"
                displayValue = value.display;
                value = value.id;
            } else if (customLabels && customLabels[value]) {
                displayValue = customLabels[value];
            } else {
                displayValue = prefix ? `${prefix} ${value}` : value;
            }
            
            return `<option value="${value}">${displayValue}</option>`;
        }).join('');
        
        return `
            <div class="filter-group" style="display: flex; flex-direction: column; gap: 0.5rem;">
                <label class="filter-label" for="filter-${id}" style="font-size: 0.875rem; font-weight: 600; color: #1e293b; text-transform: uppercase; letter-spacing: 0.5px;">
                    ${label} <span style="color: #94a3b8; font-weight: 400;">(${count})</span>
                </label>
                <select class="filter-select" id="filter-${id}" data-filter="${id}" style="width: 100%; padding: 0.75rem 1rem; border: 2px solid #e2e8f0; border-radius: 8px; background: white; font-size: 0.875rem; font-weight: 500; cursor: pointer; transition: all 0.2s ease; outline: none; color: #334155;">
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
     * Obtient les options disponibles selon les filtres actifs (filtrage intelligent)
     */
    _getAvailableOptions(data) {
        // Obtenir les matchs filtrés selon les filtres actuels
        const filteredMatches = this._getFilteredMatches(data);
        
        // Extraire équipes impliquées dans ces matchs
        const relevantEquipes = new Set();
        filteredMatches.forEach(match => {
            relevantEquipes.add(match.equipe1_id);
            relevantEquipes.add(match.equipe2_id);
        });
        
        // Filtrer les équipes du dataset
        let availableEquipes = data.entities.equipes.filter(e => relevantEquipes.has(e.id));
        
        // Appliquer filtres en cascade
        if (this.activeFilters.gender) {
            availableEquipes = availableEquipes.filter(e => e.genre === this.activeFilters.gender);
        }
        if (this.activeFilters.institution) {
            availableEquipes = availableEquipes.filter(e => e.institution === this.activeFilters.institution);
        }
        if (this.activeFilters.equipe) {
            availableEquipes = availableEquipes.filter(e => e.id === this.activeFilters.equipe);
        }
        if (this.activeFilters.pool) {
            availableEquipes = availableEquipes.filter(e => e.poule === this.activeFilters.pool);
        }
        
        // Extraire valeurs uniques
        const genders = [...new Set(availableEquipes.map(e => e.genre).filter(Boolean))].sort();
        const institutions = [...new Set(availableEquipes.map(e => e.institution).filter(Boolean))].sort();
        
        // Format équipes: "Institution (numéro)"
        const equipes = availableEquipes
            .map(e => ({
                id: e.id,
                display: `${e.institution} (${e.nom.match(/\((\d+)\)/)?.[1] || e.nom})`,
                institution: e.institution,
                genre: e.genre,
                poule: e.poule
            }))
            .sort((a, b) => a.display.localeCompare(b.display));
        
        // Poules contenant les équipes disponibles
        const relevantPools = [...new Set(availableEquipes.map(e => e.poule).filter(Boolean))].sort();
        
        // Gymnases et semaines avec matchs après filtrage
        const venues = [...new Set(filteredMatches.map(m => m.gymnase).filter(Boolean))].sort();
        const weeks = [...new Set(filteredMatches.map(m => m.semaine).filter(Boolean))].sort((a, b) => a - b);
        
        return {
            genders,
            institutions,
            equipes,
            pools: relevantPools,
            venues,
            weeks
        };
    }
    
    /**
     * Obtient les matchs filtrés selon les filtres actifs (sauf les filtres qu'on veut populer)
     */
    _getFilteredMatches(data) {
        return data.matches.scheduled.filter(match => {
            // Récupérer les équipes
            const equipe1 = data.entities.equipes.find(e => e.id === match.equipe1_id);
            const equipe2 = data.entities.equipes.find(e => e.id === match.equipe2_id);
            
            if (!equipe1 || !equipe2) return false;
            
            // Filtre genre
            if (this.activeFilters.gender) {
                if (equipe1.genre !== this.activeFilters.gender && equipe2.genre !== this.activeFilters.gender) {
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
            
            // Filtre équipe
            if (this.activeFilters.equipe) {
                if (match.equipe1_id !== this.activeFilters.equipe &&
                    match.equipe2_id !== this.activeFilters.equipe) {
                    return false;
                }
            }
            
            // Filtre poule
            if (this.activeFilters.pool) {
                if (equipe1.poule !== this.activeFilters.pool && equipe2.poule !== this.activeFilters.pool) {
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
            equipe: '',
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
            
            // Filtre équipe
            if (this.activeFilters.equipe) {
                if (match.equipes[0] !== this.activeFilters.equipe &&
                    match.equipes[1] !== this.activeFilters.equipe) {
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
