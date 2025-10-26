/**
 * AgendaViewManager - Gestionnaire des vues agenda (par gymnase ou par semaine)
 * 
 * Responsabilités:
 * - Gestion du mode d'affichage (venues/weeks)
 * - Navigation entre semaines/gymnases (précédent/suivant)
 * - Calcul dynamique des plages horaires
 * - Organisation des données pour l'affichage
 * - Intégration avec les filtres
 */

class AgendaViewManager {
    constructor(dataManager) {
        this.dataManager = dataManager;
        
        // Mode d'affichage
        this.displayMode = 'venues'; // 'venues' ou 'weeks'
        
        // Navigation
        this.currentWeek = null;
        this.currentVenue = null;
        this.availableWeeks = [];
        this.availableVenues = [];
        
        // Plage horaire dynamique
        this.minHour = 8;
        this.maxHour = 22;
        this.hourStep = 2; // Pas de 2h (peut être ajusté)
        
        // Options
        this.showAvailableSlots = false;
        this.matchDurationHours = 2;
        
        this._initialize();
    }
    
    /**
     * Initialisation
     */
    _initialize() {
        const matches = this.dataManager.getScheduledMatches();
        
        // Extraire les semaines disponibles
        this.availableWeeks = [...new Set(matches.map(m => m.semaine))]
            .filter(w => w)
            .sort((a, b) => a - b);
        
        // Extraire les gymnases disponibles
        this.availableVenues = [...new Set(matches.map(m => m.gymnase))]
            .filter(v => v)
            .map(id => ({
                id: id,
                data: this.dataManager.getGymnaseById(id)
            }))
            .sort((a, b) => (a.data?.nom || a.id).localeCompare(b.data?.nom || b.id));
        
        // Initialiser la vue
        this.currentWeek = this.availableWeeks[0] || null;
        this.currentVenue = this.availableVenues[0]?.id || null;
    }
    
    /**
     * Change le mode d'affichage
     */
    setDisplayMode(mode) {
        if (mode !== 'venues' && mode !== 'weeks') {
            return;
        }
        
        this.displayMode = mode;
    }
    
    /**
     * Navigation vers la semaine suivante
     */
    nextWeek() {
        const currentIndex = this.availableWeeks.indexOf(this.currentWeek);
        if (currentIndex < this.availableWeeks.length - 1) {
            this.currentWeek = this.availableWeeks[currentIndex + 1];
            return true;
        }
        return false;
    }
    
    /**
     * Navigation vers la semaine précédente
     */
    previousWeek() {
        const currentIndex = this.availableWeeks.indexOf(this.currentWeek);
        if (currentIndex > 0) {
            this.currentWeek = this.availableWeeks[currentIndex - 1];
            return true;
        }
        return false;
    }
    
    /**
     * Navigation vers le gymnase suivant
     */
    nextVenue() {
        const currentIndex = this.availableVenues.findIndex(v => v.id === this.currentVenue);
        if (currentIndex < this.availableVenues.length - 1) {
            this.currentVenue = this.availableVenues[currentIndex + 1].id;
            return true;
        }
        return false;
    }
    
    /**
     * Navigation vers le gymnase précédent
     */
    previousVenue() {
        const currentIndex = this.availableVenues.findIndex(v => v.id === this.currentVenue);
        if (currentIndex > 0) {
            this.currentVenue = this.availableVenues[currentIndex - 1].id;
            return true;
        }
        return false;
    }
    
    /**
     * Calcule la plage horaire dynamique basée sur les matchs à afficher
     */
    calculateTimeRange(matches) {
        if (!matches || matches.length === 0) {
            this.minHour = 8;
            this.maxHour = 22;
            return { minHour: 8, maxHour: 22 };
        }
        
        const hours = matches
            .map(m => m.horaire)
            .filter(h => h)
            .map(h => {
                const parts = h.split(':');
                return parseInt(parts[0]);
            })
            .filter(h => !isNaN(h));
        
        if (hours.length === 0) {
            this.minHour = 8;
            this.maxHour = 22;
            return { minHour: 8, maxHour: 22 };
        }
        
        const minMatch = Math.min(...hours);
        const maxMatch = Math.max(...hours);
        
        // Ajouter 1h avant le premier match et après le dernier
        this.minHour = Math.max(6, Math.floor((minMatch - 1) / 2) * 2);
        this.maxHour = Math.min(24, Math.ceil((maxMatch + this.matchDurationHours + 1) / 2) * 2);
        
        return { minHour: this.minHour, maxHour: this.maxHour };
    }
    
    /**
     * Obtient les créneaux horaires à afficher
     */
    getTimeSlots() {
        const slots = [];
        for (let hour = this.minHour; hour < this.maxHour; hour += this.hourStep) {
            slots.push({
                hour: hour,
                label: `${hour}h - ${hour + this.hourStep}h`,
                start: `${String(hour).padStart(2, '0')}:00`
            });
        }
        return slots;
    }
    
    /**
     * Obtient les colonnes à afficher selon le mode
     */
    getColumns(filteredMatches) {
        if (this.displayMode === 'venues') {
            // Vue par gymnase: afficher tous les gymnases pour la semaine courante
            if (!this.currentWeek) return [];
            
            const weekMatches = filteredMatches.filter(m => m.semaine === this.currentWeek);
            const venueIds = [...new Set(weekMatches.map(m => m.gymnase))].filter(v => v);
            
            return venueIds.map(id => {
                const venue = this.dataManager.getGymnaseById(id);
                return {
                    id: id,
                    label: venue?.nom || id,
                    sublabel: null,
                    type: 'venue',
                    capacity: venue?.capacite || 1,
                    data: venue
                };
            }).sort((a, b) => a.label.localeCompare(b.label));
            
        } else {
            // Vue par semaine: afficher toutes les semaines
            const weeks = [...new Set(filteredMatches.map(m => m.semaine))].filter(w => w);
            
            return weeks.sort((a, b) => a - b).map(w => {
                // Pour chaque semaine, identifier les gymnases utilisés
                const weekMatches = filteredMatches.filter(m => m.semaine === w);
                const venues = [...new Set(weekMatches.map(m => m.gymnase))];
                const venueNames = venues
                    .map(id => this.dataManager.getGymnaseById(id)?.nom || id)
                    .sort();
                
                return {
                    id: w,
                    label: `Semaine ${w}`,
                    sublabel: venueNames.length <= 3 
                        ? venueNames.join(', ') 
                        : `${venueNames.slice(0, 2).join(', ')}... (+${venueNames.length - 2})`,
                    type: 'week',
                    capacity: Math.max(...venues.map(id => 
                        this.dataManager.getGymnaseById(id)?.capacite || 1
                    )),
                    venues: venues
                };
            });
        }
    }
    
    /**
     * Obtient les matchs pour une colonne spécifique
     */
    getMatchesForColumn(column, allMatches) {
        if (column.type === 'venue') {
            return allMatches.filter(m => 
                m.gymnase === column.id && 
                m.semaine === this.currentWeek
            );
        } else {
            // Pour la vue par semaine, tous les matchs de cette semaine
            return allMatches.filter(m => m.semaine === column.id);
        }
    }
    
    /**
     * Obtient les matchs pour un créneau spécifique dans une colonne
     */
    getMatchesForSlot(column, timeSlot, allMatches) {
        const columnMatches = this.getMatchesForColumn(column, allMatches);
        
        return columnMatches.filter(m => {
            if (!m.horaire) return false;
            
            const matchHour = parseInt(m.horaire.split(':')[0]);
            return matchHour === timeSlot.hour;
        });
    }
    
    /**
     * Calcule les créneaux disponibles pour une colonne
     */
    getAvailableSlots(column, allMatches) {
        if (!this.showAvailableSlots) return [];
        
        const slots = [];
        const timeSlots = this.getTimeSlots();
        
        for (const timeSlot of timeSlots) {
            const slotMatches = this.getMatchesForSlot(column, timeSlot, allMatches);
            const capacity = column.capacity || 1;
            
            if (slotMatches.length < capacity) {
                // Il reste de la place
                slots.push({
                    time: timeSlot,
                    column: column,
                    availableSlots: capacity - slotMatches.length,
                    totalCapacity: capacity
                });
            }
        }
        
        return slots;
    }
    
    /**
     * Génère les données de navigation
     */
    getNavigationData() {
        if (this.displayMode === 'venues') {
            const currentIndex = this.availableWeeks.indexOf(this.currentWeek);
            return {
                mode: 'venues',
                current: this.currentWeek,
                currentLabel: `Semaine ${this.currentWeek}`,
                hasPrevious: currentIndex > 0,
                hasNext: currentIndex < this.availableWeeks.length - 1,
                total: this.availableWeeks.length,
                index: currentIndex + 1
            };
        } else {
            return {
                mode: 'weeks',
                current: null,
                currentLabel: 'Toutes les semaines',
                hasPrevious: false,
                hasNext: false,
                total: this.availableWeeks.length,
                index: null
            };
        }
    }
    
    /**
     * Obtient des statistiques sur la vue actuelle
     */
    getViewStats(filteredMatches, columns) {
        const totalMatches = this.dataManager.getScheduledMatches().length;
        const visibleMatches = filteredMatches.length;
        
        return {
            displayMode: this.displayMode,
            totalColumns: columns.length,
            totalMatches: totalMatches,
            visibleMatches: visibleMatches,
            timeRange: `${this.minHour}h - ${this.maxHour}h`,
            slotsCount: this.getTimeSlots().length
        };
    }
}

// Export global
window.AgendaViewManager = AgendaViewManager;
