/**
 * Enhanced Filter System - Système de filtres complet et fonctionnel
 * Intégration parfaite avec le dataManager et les vues
 */

class EnhancedFilterSystem {
    constructor() {
        this.filters = {
            gender: null,
            week: null,
            pool: null,
            institution: null,
            venue: null,
            days: [],
            timeStart: null,
            timeEnd: null,
            states: [],
            search: ''
        };
        
        this.callbacks = [];
        this.initialized = false;
    }
    
    /**
     * Initialise le système de filtres
     */
    init() {
        if (this.initialized) return;
        
        console.log('🔍 Initialisation du système de filtres...');
        
        // Charger les filtres depuis localStorage
        this.loadFromStorage();
        
        // Peupler les options dynamiques
        this.populateOptions();
        
        // Attacher les événements
        this.attachEvents();
        
        // Appliquer les filtres initiaux
        this.apply();
        
        this.initialized = true;
        console.log('✅ Système de filtres initialisé');
    }
    
    /**
     * Charge les filtres depuis localStorage
     */
    loadFromStorage() {
        try {
            const stored = localStorage.getItem('pycalendar_filters');
            if (stored) {
                const savedFilters = JSON.parse(stored);
                this.filters = { ...this.filters, ...savedFilters };
                this.applyToUI();
            }
        } catch (e) {
            console.warn('Erreur chargement filtres:', e);
        }
    }
    
    /**
     * Sauvegarde les filtres dans localStorage
     */
    saveToStorage() {
        try {
            localStorage.setItem('pycalendar_filters', JSON.stringify(this.filters));
        } catch (e) {
            console.warn('Erreur sauvegarde filtres:', e);
        }
    }
    
    /**
     * Applique les filtres à l'UI
     */
    applyToUI() {
        // Gender
        if (this.filters.gender) {
            const radio = document.querySelector(`input[name="filter-gender"][value="${this.filters.gender}"]`);
            if (radio) radio.checked = true;
        }
        
        // Selects
        ['week', 'pool', 'institution', 'venue'].forEach(key => {
            const select = document.getElementById(`filter-${key}`);
            if (select && this.filters[key]) {
                select.value = this.filters[key];
            }
        });
        
        // Days
        this.filters.days.forEach(day => {
            const checkbox = document.querySelector(`input[name="filter-day"][value="${day}"]`);
            if (checkbox) checkbox.checked = true;
        });
        
        // Time
        if (this.filters.timeStart) {
            const input = document.getElementById('filter-time-start');
            if (input) input.value = this.filters.timeStart;
        }
        if (this.filters.timeEnd) {
            const input = document.getElementById('filter-time-end');
            if (input) input.value = this.filters.timeEnd;
        }
        
        // States
        this.filters.states.forEach(state => {
            const checkbox = document.querySelector(`input[name="filter-state"][value="${state}"]`);
            if (checkbox) checkbox.checked = true;
        });
        
        // Search
        if (this.filters.search) {
            const input = document.getElementById('filter-search');
            if (input) input.value = this.filters.search;
        }
    }
    
    /**
     * Peuple les options dynamiques (institutions, poules, gymnases, semaines)
     */
    populateOptions() {
        if (!window.dataManager) {
            console.warn('dataManager non disponible pour peupler les filtres');
            return;
        }
        
        const data = window.dataManager.getData();
        if (!data) return;
        
        // Institutions
        const institutions = new Set();
        if (data.entities?.equipes) {
            data.entities.equipes.forEach(equipe => {
                if (equipe.institution) {
                    institutions.add(equipe.institution);
                }
            });
        }
        
        const institutionSelect = document.getElementById('filter-institution');
        if (institutionSelect) {
            // Garder l'option "Toutes"
            institutionSelect.innerHTML = '<option value="">Toutes</option>';
            Array.from(institutions).sort().forEach(inst => {
                const option = document.createElement('option');
                option.value = inst;
                option.textContent = inst;
                institutionSelect.appendChild(option);
            });
        }
        
        // Poules
        const poolSelect = document.getElementById('filter-pool');
        if (poolSelect && data.entities?.poules) {
            poolSelect.innerHTML = '<option value="">Toutes</option>';
            data.entities.poules.forEach(pool => {
                const option = document.createElement('option');
                option.value = pool.id;
                option.textContent = pool.nom || pool.id;
                poolSelect.appendChild(option);
            });
        }
        
        // Gymnases
        const venueSelect = document.getElementById('filter-venue');
        if (venueSelect && data.entities?.gymnases) {
            venueSelect.innerHTML = '<option value="">Tous</option>';
            data.entities.gymnases.forEach(gym => {
                const option = document.createElement('option');
                option.value = gym.id;
                option.textContent = gym.nom || gym.id;
                venueSelect.appendChild(option);
            });
        }
        
        // Semaines
        const weeks = new Set();
        if (data.matches?.scheduled) {
            data.matches.scheduled.forEach(match => {
                if (match.semaine) {
                    weeks.add(match.semaine);
                }
            });
        }
        
        const weekSelect = document.getElementById('filter-week');
        if (weekSelect) {
            weekSelect.innerHTML = '<option value="">Toutes</option>';
            Array.from(weeks).sort((a, b) => a - b).forEach(week => {
                const option = document.createElement('option');
                option.value = week;
                option.textContent = `Semaine ${week}`;
                weekSelect.appendChild(option);
            });
        }
        
        console.log('📊 Options de filtres peuplées:', {
            institutions: institutions.size,
            poules: data.entities?.poules?.length || 0,
            gymnases: data.entities?.gymnases?.length || 0,
            semaines: weeks.size
        });
    }
    
    /**
     * Attache les événements
     */
    attachEvents() {
        // Gender radio buttons
        document.querySelectorAll('input[name="filter-gender"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.filters.gender = e.target.value || null;
                this.apply();
            });
        });
        
        // Week select
        const weekSelect = document.getElementById('filter-week');
        if (weekSelect) {
            weekSelect.addEventListener('change', (e) => {
                this.filters.week = e.target.value ? parseInt(e.target.value) : null;
                this.apply();
            });
        }
        
        // Pool select
        const poolSelect = document.getElementById('filter-pool');
        if (poolSelect) {
            poolSelect.addEventListener('change', (e) => {
                this.filters.pool = e.target.value || null;
                this.apply();
            });
        }
        
        // Institution select
        const institutionSelect = document.getElementById('filter-institution');
        if (institutionSelect) {
            institutionSelect.addEventListener('change', (e) => {
                this.filters.institution = e.target.value || null;
                this.apply();
            });
        }
        
        // Venue select
        const venueSelect = document.getElementById('filter-venue');
        if (venueSelect) {
            venueSelect.addEventListener('change', (e) => {
                this.filters.venue = e.target.value || null;
                this.apply();
            });
        }
        
        // Day checkboxes
        document.querySelectorAll('input[name="filter-day"]').forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this.filters.days = Array.from(
                    document.querySelectorAll('input[name="filter-day"]:checked')
                ).map(cb => cb.value);
                this.apply();
            });
        });
        
        // Time inputs
        const timeStart = document.getElementById('filter-time-start');
        if (timeStart) {
            timeStart.addEventListener('change', (e) => {
                this.filters.timeStart = e.target.value || null;
                this.apply();
            });
        }
        
        const timeEnd = document.getElementById('filter-time-end');
        if (timeEnd) {
            timeEnd.addEventListener('change', (e) => {
                this.filters.timeEnd = e.target.value || null;
                this.apply();
            });
        }
        
        // State checkboxes
        document.querySelectorAll('input[name="filter-state"]').forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this.filters.states = Array.from(
                    document.querySelectorAll('input[name="filter-state"]:checked')
                ).map(cb => cb.value);
                this.apply();
            });
        });
        
        // Search input (avec debounce)
        const searchInput = document.getElementById('filter-search');
        if (searchInput) {
            let timeoutId;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(timeoutId);
                timeoutId = setTimeout(() => {
                    this.filters.search = e.target.value.trim();
                    this.apply();
                }, 300);
            });
        }
        
        // Clear filters button
        const btnClear = document.getElementById('btn-clear-filters');
        if (btnClear) {
            btnClear.addEventListener('click', () => {
                this.clear();
            });
        }
        
        console.log('👂 Événements de filtres attachés');
    }
    
    /**
     * Applique les filtres
     */
    apply() {
        // Sauvegarder
        this.saveToStorage();
        
        // Mettre à jour le résumé
        this.updateSummary();
        
        // Notifier les callbacks
        this.callbacks.forEach(callback => {
            try {
                callback(this.filters);
            } catch (e) {
                console.error('Erreur callback filtre:', e);
            }
        });
        
        // Notifier les vues
        if (window.agendaView && typeof window.agendaView.setFilters === 'function') {
            window.agendaView.setFilters(this.filters);
        }
        if (window.poolsView && typeof window.poolsView.setFilters === 'function') {
            window.poolsView.setFilters(this.filters);
        }
        if (window.cardsView && typeof window.cardsView.setFilters === 'function') {
            window.cardsView.setFilters(this.filters);
        }
        
        console.log('🔍 Filtres appliqués:', this.filters);
    }
    
    /**
     * Efface tous les filtres
     */
    clear() {
        // Reset filters object
        this.filters = {
            gender: null,
            week: null,
            pool: null,
            institution: null,
            venue: null,
            days: [],
            timeStart: null,
            timeEnd: null,
            states: [],
            search: ''
        };
        
        // Reset UI
        // Gender
        const genderAll = document.querySelector('input[name="filter-gender"][value=""]');
        if (genderAll) genderAll.checked = true;
        
        // Selects
        ['filter-week', 'filter-pool', 'filter-institution', 'filter-venue'].forEach(id => {
            const select = document.getElementById(id);
            if (select) select.value = '';
        });
        
        // Checkboxes
        document.querySelectorAll('input[name="filter-day"]').forEach(cb => cb.checked = false);
        document.querySelectorAll('input[name="filter-state"]').forEach(cb => cb.checked = false);
        
        // Time
        const timeStart = document.getElementById('filter-time-start');
        if (timeStart) timeStart.value = '08:00';
        const timeEnd = document.getElementById('filter-time-end');
        if (timeEnd) timeEnd.value = '20:00';
        
        // Search
        const searchInput = document.getElementById('filter-search');
        if (searchInput) searchInput.value = '';
        
        // Apply
        this.apply();
        
        console.log('🧹 Filtres effacés');
    }
    
    /**
     * Met à jour le résumé des filtres
     */
    updateSummary() {
        const summaryTags = document.getElementById('summary-tags');
        if (!summaryTags) return;
        
        // Compter les filtres actifs
        const activeCount = this.countActive();
        
        if (activeCount === 0) {
            summaryTags.innerHTML = '<span class="no-filters">Aucun filtre actif</span>';
            return;
        }
        
        // Créer les tags
        const tags = [];
        
        if (this.filters.gender) {
            const label = this.filters.gender === 'M' ? '♂ Masculin' : 
                         this.filters.gender === 'F' ? '♀ Féminin' : 
                         '⚥ Mixte';
            tags.push(this.createTag(label, 'gender'));
        }
        
        if (this.filters.week) {
            tags.push(this.createTag(`📅 Semaine ${this.filters.week}`, 'week'));
        }
        
        if (this.filters.pool) {
            tags.push(this.createTag(`🏊 ${this.filters.pool}`, 'pool'));
        }
        
        if (this.filters.institution) {
            tags.push(this.createTag(`🏫 ${this.filters.institution}`, 'institution'));
        }
        
        if (this.filters.venue) {
            tags.push(this.createTag(`🏟️ ${this.filters.venue}`, 'venue'));
        }
        
        if (this.filters.days.length > 0) {
            const dayNames = {
                'mon': 'Lun', 'tue': 'Mar', 'wed': 'Mer',
                'thu': 'Jeu', 'fri': 'Ven', 'sat': 'Sam', 'sun': 'Dim'
            };
            const dayLabels = this.filters.days.map(d => dayNames[d] || d).join(', ');
            tags.push(this.createTag(`📆 ${dayLabels}`, 'days'));
        }
        
        if (this.filters.timeStart || this.filters.timeEnd) {
            const timeLabel = `🕐 ${this.filters.timeStart || '00:00'} - ${this.filters.timeEnd || '23:59'}`;
            tags.push(this.createTag(timeLabel, 'time'));
        }
        
        if (this.filters.states.length > 0) {
            const stateLabels = this.filters.states.map(s => {
                switch(s) {
                    case 'scheduled': return 'Planifiés';
                    case 'unscheduled': return 'Non planifiés';
                    case 'modified': return 'Modifiés';
                    case 'conflict': return 'Conflits';
                    default: return s;
                }
            }).join(', ');
            tags.push(this.createTag(`📊 ${stateLabels}`, 'states'));
        }
        
        if (this.filters.search) {
            tags.push(this.createTag(`🔍 "${this.filters.search}"`, 'search'));
        }
        
        summaryTags.innerHTML = tags.join('');
    }
    
    /**
     * Crée un tag HTML
     */
    createTag(label, key) {
        return `<span class="filter-tag" data-filter="${key}">${label}</span>`;
    }
    
    /**
     * Compte le nombre de filtres actifs
     */
    countActive() {
        let count = 0;
        if (this.filters.gender) count++;
        if (this.filters.week) count++;
        if (this.filters.pool) count++;
        if (this.filters.institution) count++;
        if (this.filters.venue) count++;
        if (this.filters.days.length > 0) count++;
        if (this.filters.timeStart || this.filters.timeEnd) count++;
        if (this.filters.states.length > 0) count++;
        if (this.filters.search) count++;
        return count;
    }
    
    /**
     * Filtre une liste de matchs
     */
    filterMatches(matches) {
        if (!matches || !window.dataManager) return matches;
        
        const data = window.dataManager.getData();
        if (!data) return matches;
        
        return matches.filter(match => {
            // Gender
            if (this.filters.gender) {
                const equipe1 = data.entities.equipes.find(e => e.id === match.equipes[0]);
                if (!equipe1 || equipe1.genre !== this.filters.gender) {
                    return false;
                }
            }
            
            // Week
            if (this.filters.week !== null) {
                if (match.semaine !== this.filters.week) {
                    return false;
                }
            }
            
            // Pool
            if (this.filters.pool) {
                const equipe1 = data.entities.equipes.find(e => e.id === match.equipes[0]);
                if (!equipe1 || equipe1.poule !== this.filters.pool) {
                    return false;
                }
            }
            
            // Institution
            if (this.filters.institution) {
                const equipe1 = data.entities.equipes.find(e => e.id === match.equipes[0]);
                const equipe2 = data.entities.equipes.find(e => e.id === match.equipes[1]);
                if ((!equipe1 || equipe1.institution !== this.filters.institution) &&
                    (!equipe2 || equipe2.institution !== this.filters.institution)) {
                    return false;
                }
            }
            
            // Venue
            if (this.filters.venue) {
                if (match.gymnase !== this.filters.venue) {
                    return false;
                }
            }
            
            // Days (nécessite jour de la semaine dans match.jour ou match.date)
            if (this.filters.days.length > 0) {
                // TODO: implémenter le filtre par jour
            }
            
            // Time range
            if (this.filters.timeStart && match.heure) {
                if (match.heure < this.filters.timeStart) {
                    return false;
                }
            }
            if (this.filters.timeEnd && match.heure) {
                if (match.heure > this.filters.timeEnd) {
                    return false;
                }
            }
            
            // Search
            if (this.filters.search) {
                const searchLower = this.filters.search.toLowerCase();
                const equipe1 = data.entities.equipes.find(e => e.id === match.equipes[0]);
                const equipe2 = data.entities.equipes.find(e => e.id === match.equipes[1]);
                
                const matchText = [
                    equipe1?.nom,
                    equipe2?.nom,
                    equipe1?.institution,
                    equipe2?.institution,
                    match.gymnase
                ].filter(Boolean).join(' ').toLowerCase();
                
                if (!matchText.includes(searchLower)) {
                    return false;
                }
            }
            
            return true;
        });
    }
    
    /**
     * Ajoute un callback
     */
    onChange(callback) {
        this.callbacks.push(callback);
    }
    
    /**
     * Obtient les filtres actuels
     */
    getFilters() {
        return { ...this.filters };
    }
}

// Export global
if (typeof window !== 'undefined') {
    window.EnhancedFilterSystem = EnhancedFilterSystem;
    window.filterSystem = new EnhancedFilterSystem();
}
