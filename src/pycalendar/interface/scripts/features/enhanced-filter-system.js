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
            equipe: null,
            venue: null,
            horaireStart: null,  // Nouveau: début de plage
            horaireEnd: null,    // Nouveau: fin de plage
            days: [],            // Jours de la semaine
            timeStart: null,     // Heure de début
            timeEnd: null,       // Heure de fin
            states: [],          // États des matchs
            search: '',
            status: 'all' // Pour la vue Matchs: 'all', 'fixed', 'scheduled', 'unscheduled', 'entente'
        };
        
        this.callbacks = [];
        this.initialized = false;
        
        // Variables pour la timeline
        this.availableHoraires = [];
        this.minMinutes = 0;
        this.maxMinutes = 0;
        this.horaireStart = 0;
        this.horaireEnd = 0;
        
        console.log('🔍 EnhancedFilterSystem: Initialisation avec timeline horaire');
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
        
        // Selects (institution, pool, venue, week, equipe, horaire)
        ['week', 'pool', 'institution', 'equipe', 'venue', 'horaire'].forEach(key => {
            const select = document.getElementById(`filter-${key}`);
            if (select && this.filters[key]) {
                select.value = this.filters[key];
            }
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
        
        // Équipes - Groupées par nom (institution + numéro) sans afficher M/F
        const equipeSelect = document.getElementById('filter-equipe');
        if (equipeSelect && data.entities?.equipes) {
            console.log('🏐 Population du filtre équipes (groupées)...');
            equipeSelect.innerHTML = '<option value="">Toutes les équipes</option>';
            
            // Grouper les équipes par nom (institution + numéro)
            const equipeGroups = {};
            data.entities.equipes.forEach(equipe => {
                const numero = equipe.nom.match(/\((\d+)\)/)?.[1] || equipe.numero_equipe || '';
                const key = `${equipe.institution}|(${numero})`;
                
                if (!equipeGroups[key]) {
                    equipeGroups[key] = {
                        name: `${equipe.institution} (${numero})`,
                        institution: equipe.institution,
                        numero: numero,
                        ids: []
                    };
                }
                equipeGroups[key].ids.push(equipe.id);
            });
            
            // Trier par institution puis numéro
            const sortedGroups = Object.values(equipeGroups).sort((a, b) => {
                if (a.institution !== b.institution) {
                    return a.institution.localeCompare(b.institution);
                }
                return parseInt(a.numero || 0) - parseInt(b.numero || 0);
            });
            
            sortedGroups.forEach(group => {
                const option = document.createElement('option');
                // Stocker tous les IDs séparés par des virgules
                option.value = group.ids.join(',');
                // Affichage simple : juste Institution (numéro)
                option.textContent = group.name;
                equipeSelect.appendChild(option);
            });
            
            // Mettre à jour le compteur
            const equipeCount = document.getElementById('equipe-count');
            if (equipeCount) {
                equipeCount.textContent = `(${sortedGroups.length})`;
            }
            
            console.log(`✅ ${sortedGroups.length} groupes d'équipes ajoutés au filtre`);
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
        
        // Horaires - Timeline interactive
        const horaires = new Set();
        if (data.matches?.scheduled) {
            data.matches.scheduled.forEach(match => {
                if (match.horaire) {
                    horaires.add(match.horaire);
                }
            });
        }
        
        // Convertir les horaires en minutes depuis minuit pour faciliter les calculs
        this.availableHoraires = Array.from(horaires).sort().map(h => {
            const [hours, minutes] = h.split(':').map(Number);
            return {
                time: h,
                minutes: hours * 60 + minutes
            };
        });
        
        // Initialiser la timeline avec les horaires disponibles
        this.initHoraireTimeline();
        
        console.log('📊 Options de filtres peuplées:', {
            institutions: institutions.size,
            equipes: data.entities?.equipes?.length || 0,
            poules: data.entities?.poules?.length || 0,
            gymnases: data.entities?.gymnases?.length || 0,
            semaines: weeks.size,
            horaires: horaires.size
        });
    }
    
    /**
     * Met à jour dynamiquement les options selon les filtres actifs (FILTRAGE INTELLIGENT)
     */
    updateDynamicOptions() {
        if (!window.dataManager) return;
        
        const data = window.dataManager.getData();
        if (!data || !data.entities?.equipes) return;
        
        console.log('🔄 Mise à jour intelligente des filtres...', this.filters);
        
        // Filtrer les équipes pour les institutions (sans le filtre institution lui-même)
        let equipesForInstitutions = [...data.entities.equipes];
        if (this.filters.gender) {
            equipesForInstitutions = equipesForInstitutions.filter(e => e.genre === this.filters.gender);
        }
        if (this.filters.pool) {
            equipesForInstitutions = equipesForInstitutions.filter(e => e.poule === this.filters.pool);
        }
        
        // Filtrer les équipes pour les autres dropdowns (avec le filtre institution)
        let availableEquipes = [...data.entities.equipes];
        if (this.filters.gender) {
            availableEquipes = availableEquipes.filter(e => e.genre === this.filters.gender);
        }
        if (this.filters.institution) {
            availableEquipes = availableEquipes.filter(e => e.institution === this.filters.institution);
        }
        if (this.filters.pool) {
            availableEquipes = availableEquipes.filter(e => e.poule === this.filters.pool);
        }
        
        // Extraire les institutions disponibles (SANS filtre institution pour voir toutes les options)
        const availableInstitutions = [...new Set(equipesForInstitutions.map(e => e.institution))].sort();
        
        // Extraire les poules disponibles
        const availablePools = [...new Set(availableEquipes.map(e => e.poule).filter(Boolean))].sort();
        
        // Mettre à jour le select Institution
        const institutionSelect = document.getElementById('filter-institution');
        if (institutionSelect) {
            const currentValue = institutionSelect.value;
            institutionSelect.innerHTML = '<option value="">Toutes</option>';
            availableInstitutions.forEach(inst => {
                const option = document.createElement('option');
                option.value = inst;
                // Compter avec equipesForInstitutions (sans filtre institution)
                option.textContent = `${inst} (${equipesForInstitutions.filter(e => e.institution === inst).length})`;
                institutionSelect.appendChild(option);
            });
            // Restaurer la valeur si elle est toujours disponible
            if (availableInstitutions.includes(currentValue)) {
                institutionSelect.value = currentValue;
            } else if (currentValue && !availableInstitutions.includes(currentValue)) {
                // La valeur n'est plus disponible, réinitialiser
                this.filters.institution = null;
            }
        }
        
        // Mettre à jour le select Équipe (groupées par nom simple)
        const equipeSelect = document.getElementById('filter-equipe');
        if (equipeSelect) {
            const currentValue = equipeSelect.value;
            equipeSelect.innerHTML = '<option value="">Toutes les équipes</option>';
            
            // Grouper les équipes disponibles par nom
            const equipeGroups = {};
            availableEquipes.forEach(equipe => {
                const numero = equipe.nom.match(/\((\d+)\)/)?.[1] || equipe.numero_equipe || '';
                const key = `${equipe.institution}|(${numero})`;
                
                if (!equipeGroups[key]) {
                    equipeGroups[key] = {
                        name: `${equipe.institution} (${numero})`,
                        institution: equipe.institution,
                        numero: numero,
                        ids: []
                    };
                }
                equipeGroups[key].ids.push(equipe.id);
            });
            
            // Trier par institution puis numéro
            const sortedGroups = Object.values(equipeGroups).sort((a, b) => {
                if (a.institution !== b.institution) {
                    return a.institution.localeCompare(b.institution);
                }
                return parseInt(a.numero || 0) - parseInt(b.numero || 0);
            });
            
            sortedGroups.forEach(group => {
                const option = document.createElement('option');
                option.value = group.ids.join(',');
                // Affichage simple sans genre
                option.textContent = group.name;
                equipeSelect.appendChild(option);
            });
            
            // Restaurer la valeur si elle est toujours disponible
            const allAvailableIds = sortedGroups.flatMap(g => g.ids);
            const currentIds = currentValue ? currentValue.split(',') : [];
            const stillAvailable = currentIds.some(id => allAvailableIds.includes(id));
            
            if (stillAvailable) {
                equipeSelect.value = currentValue;
            } else if (currentValue) {
                // La valeur n'est plus disponible, réinitialiser
                this.filters.equipe = null;
            }
            
            // Mettre à jour le compteur
            const equipeCount = document.getElementById('equipe-count');
            if (equipeCount) {
                equipeCount.textContent = `(${sortedGroups.length})`;
            }
        }
        
        // Mettre à jour le select Poule
        const poolSelect = document.getElementById('filter-pool');
        if (poolSelect) {
            const currentValue = poolSelect.value;
            poolSelect.innerHTML = '<option value="">Toutes</option>';
            availablePools.forEach(pool => {
                const option = document.createElement('option');
                option.value = pool;
                const count = availableEquipes.filter(e => e.poule === pool).length;
                option.textContent = `${pool} (${count})`;
                poolSelect.appendChild(option);
            });
            // Restaurer la valeur si elle est toujours disponible
            if (availablePools.includes(currentValue)) {
                poolSelect.value = currentValue;
            } else if (currentValue && !availablePools.includes(currentValue)) {
                // La valeur n'est plus disponible, réinitialiser
                this.filters.pool = null;
            }
        }
        
        // Filtrer les matchs disponibles avec les filtres actuels
        const availableMatches = this.filterMatches(data.matches?.scheduled || []);
        
        // Mettre à jour le select Gymnase (seulement ceux avec des matchs)
        const venueSelect = document.getElementById('filter-venue');
        if (venueSelect) {
            const currentValue = venueSelect.value;
            const availableVenues = [...new Set(availableMatches.map(m => m.gymnase).filter(Boolean))].sort();
            venueSelect.innerHTML = '<option value="">Tous</option>';
            availableVenues.forEach(venue => {
                const option = document.createElement('option');
                option.value = venue;
                const count = availableMatches.filter(m => m.gymnase === venue).length;
                option.textContent = `${venue} (${count})`;
                venueSelect.appendChild(option);
            });
            // Restaurer la valeur si elle est toujours disponible
            if (availableVenues.includes(currentValue)) {
                venueSelect.value = currentValue;
            } else if (currentValue && !availableVenues.includes(currentValue)) {
                this.filters.venue = null;
            }
        }
        
        // Mettre à jour le select Semaine (seulement celles avec des matchs)
        const weekSelect = document.getElementById('filter-week');
        if (weekSelect) {
            const currentValue = weekSelect.value;
            const availableWeeks = [...new Set(availableMatches.map(m => m.semaine).filter(Boolean))].sort((a, b) => a - b);
            weekSelect.innerHTML = '<option value="">Toutes</option>';
            availableWeeks.forEach(week => {
                const option = document.createElement('option');
                option.value = week;
                const count = availableMatches.filter(m => m.semaine === week).length;
                option.textContent = `Semaine ${week} (${count})`;
                weekSelect.appendChild(option);
            });
            // Restaurer la valeur si elle est toujours disponible
            if (availableWeeks.includes(parseInt(currentValue))) {
                weekSelect.value = currentValue;
            } else if (currentValue && !availableWeeks.includes(parseInt(currentValue))) {
                this.filters.week = null;
            }
        }
        
        console.log('✅ Filtres intelligents mis à jour:', {
            institutions: availableInstitutions.length,
            equipes: availableEquipes.length,
            poules: availablePools.length,
            matchs: availableMatches.length
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
        
        // Status radio buttons (pour la vue Matchs)
        document.querySelectorAll('input[name="filter-status"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.filters.status = e.target.value || 'all';
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
                console.log('🏛️ Filtre institution changé:', this.filters.institution);
                this.apply();
            });
        }
        
        // Équipe select
        const equipeSelect = document.getElementById('filter-equipe');
        if (equipeSelect) {
            equipeSelect.addEventListener('change', (e) => {
                this.filters.equipe = e.target.value || null;
                console.log('🏐 Filtre équipe changé:', this.filters.equipe);
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
        
        // Horaire select (NOUVEAU - simplifié)
        const horaireSelect = document.getElementById('filter-horaire');
        if (horaireSelect) {
            horaireSelect.addEventListener('change', (e) => {
                this.filters.horaire = e.target.value || null;
                console.log('🕐 Filtre horaire changé:', this.filters.horaire);
                this.apply();
            });
        }
        
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
        console.log('🎯 Application des filtres:', this.filters);
        
        // Mettre à jour les options dynamiques (filtrage intelligent)
        this.updateDynamicOptions();
        
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
        if (window.teamsView && typeof window.teamsView.setFilters === 'function') {
            window.teamsView.setFilters(this.filters);
        }
        if (window.matchesView && typeof window.matchesView.updateFilters === 'function') {
            window.matchesView.updateFilters(this.filters);
        }
        
        console.log('🔍 Filtres appliqués:', this.filters);
    }
    
    /**
     * Efface tous les filtres
     */
    clear() {
        console.log('🧹 Réinitialisation des filtres (avec timeline horaire)');
        
        // Reset UI
        // Gender
        const genderAll = document.querySelector('input[name="filter-gender"][value=""]');
        if (genderAll) genderAll.checked = true;
        
        // Status
        const statusAll = document.querySelector('input[name="filter-status"][value="all"]');
        if (statusAll) statusAll.checked = true;
        
        // Selects
        ['filter-week', 'filter-pool', 'filter-institution', 'filter-equipe', 'filter-venue'].forEach(id => {
            const select = document.getElementById(id);
            if (select) select.value = '';
        });
        
        // Reset timeline horaire à la plage complète
        if (this.availableHoraires && this.availableHoraires.length > 0) {
            this.horaireStart = this.minMinutes;
            this.horaireEnd = this.maxMinutes;
            this.updateHoraireDisplay();
        }
        
        // Search
        const searchInput = document.getElementById('filter-search');
        if (searchInput) searchInput.value = '';
        
        // Reset filters object APRÈS avoir réinitialisé la timeline
        // Car updateHoraireDisplay() définit horaireStart et horaireEnd
        this.filters.gender = null;
        this.filters.week = null;
        this.filters.pool = null;
        this.filters.institution = null;
        this.filters.equipe = null;
        this.filters.venue = null;
        this.filters.days = [];
        this.filters.timeStart = null;
        this.filters.timeEnd = null;
        this.filters.states = [];
        // horaireStart et horaireEnd sont déjà définis par updateHoraireDisplay()
        this.filters.search = '';
        this.filters.status = 'all';
        
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
        
        if (this.filters.equipe) {
            // Récupérer le nom formaté de l'équipe (ou groupe d'équipes)
            const data = window.dataManager?.getData();
            let equipeName = this.filters.equipe;
            if (data?.entities?.equipes) {
                // Le filtre peut contenir plusieurs IDs (équipes M et/ou F du même nom)
                const equipeIds = this.filters.equipe.split(',');
                const equipe = data.entities.equipes.find(e => e.id === equipeIds[0]);
                if (equipe) {
                    const numero = equipe.nom.match(/\((\d+)\)/)?.[1] || equipe.numero_equipe || '';
                    equipeName = `${equipe.institution} (${numero})`;
                }
            }
            tags.push(this.createTag(`🏐 ${equipeName}`, 'equipe'));
        }
        
        if (this.filters.venue) {
            tags.push(this.createTag(`🏟️ ${this.filters.venue}`, 'venue'));
        }
        
        // Plage horaire - toujours affichée si définie
        if (this.filters.horaireStart && this.filters.horaireEnd) {
            tags.push(this.createTag(`⏰ ${this.filters.horaireStart} → ${this.filters.horaireEnd}`, 'horaire'));
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
        if (this.filters.equipe) count++;
        if (this.filters.venue) count++;
        // Le filtre horaire est toujours actif (affiche toujours une plage)
        if (this.filters.horaireStart && this.filters.horaireEnd) count++;
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
            // Compatibilité v2.0: utiliser equipe1_id/equipe2_id ou equipes[0]/equipes[1]
            const equipe1Id = match.equipe1_id || match.equipes?.[0];
            const equipe2Id = match.equipe2_id || match.equipes?.[1];
            
            if (!equipe1Id || !equipe2Id) {
                console.warn('Match sans équipes valides:', match);
                return false;
            }
            
            // Gender
            if (this.filters.gender) {
                const equipe1 = data.entities.equipes.find(e => e.id === equipe1Id);
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
                const equipe1 = data.entities.equipes.find(e => e.id === equipe1Id);
                if (!equipe1 || equipe1.poule !== this.filters.pool) {
                    return false;
                }
            }
            
            // Institution
            if (this.filters.institution) {
                const equipe1 = data.entities.equipes.find(e => e.id === equipe1Id);
                const equipe2 = data.entities.equipes.find(e => e.id === equipe2Id);
                if ((!equipe1 || equipe1.institution !== this.filters.institution) &&
                    (!equipe2 || equipe2.institution !== this.filters.institution)) {
                    return false;
                }
            }
            
            // Équipe - Filtre si le match implique une des équipes du groupe
            if (this.filters.equipe) {
                // Le filtre peut contenir plusieurs IDs séparés par des virgules (groupe M+F)
                const equipeIds = this.filters.equipe.split(',');
                if (!equipeIds.includes(equipe1Id) && !equipeIds.includes(equipe2Id)) {
                    return false;
                }
            }
            
            // Venue
            if (this.filters.venue) {
                if (match.gymnase !== this.filters.venue) {
                    return false;
                }
            }
            
            // Plage horaire (NOUVEAU - filtrage par plage avec chevauchement de créneaux)
            if (this.filters.horaireStart && this.filters.horaireEnd) {
                // Si le match n'a pas d'horaire, on le garde visible (matchs non planifiés ou ententes)
                if (!match.horaire) {
                    // Match sans horaire = visible
                } else {
                    // Convertir l'horaire du match en minutes
                    const [hours, minutes] = match.horaire.split(':').map(Number);
                    const matchStartMinutes = hours * 60 + minutes;
                    
                    // Durée standard d'un match (ajuster selon vos besoins, ex: 90 minutes)
                    const matchDuration = 90;
                    const matchEndMinutes = matchStartMinutes + matchDuration;
                    
                    // Convertir la plage sélectionnée en minutes
                    const [startHours, startMinutes] = this.filters.horaireStart.split(':').map(Number);
                    const [endHours, endMinutes] = this.filters.horaireEnd.split(':').map(Number);
                    const rangeStart = startHours * 60 + startMinutes;
                    const rangeEnd = endHours * 60 + endMinutes;
                    
                    // Le match est visible si son créneau chevauche la plage sélectionnée
                    // Chevauchement = le début du match est avant la fin de la plage ET la fin du match est après le début de la plage
                    const overlaps = matchStartMinutes < rangeEnd && matchEndMinutes > rangeStart;
                    
                    if (!overlaps) {
                        return false;
                    }
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
