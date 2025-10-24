/**
 * DataManager - Central data management for PyCalendar Interface
 * 
 * Responsibilities:
 * - Load and store solution data
 * - Manage current state (original + modifications)
 * - Provide data access to all views
 * - Notify observers of data changes
 * 
 * Data Flow:
 * 1. Load solution JSON (v2.0 format)
 * 2. Load modifications from localStorage
 * 3. Compute current state = original + modifications
 * 4. Expose data through clean API
 * 5. Notify components on changes
 */

class DataManager {
    constructor(solutionData) {
        // ==================== ORIGINAL DATA (IMMUTABLE) ====================
        this.original = Object.freeze(JSON.parse(JSON.stringify(solutionData)));
        
        // ==================== CURRENT STATE (COMPUTED) ====================
        this.current = {
            matches: {
                scheduled: [],
                unscheduled: []
            },
            slots: {
                available: [],
                occupied: []
            },
            entities: {
                equipes: [],
                gymnases: [],
                poules: []
            },
            statistics: {}
        };
        
        // ==================== INDEXES FOR FAST LOOKUP ====================
        this.indexes = {
            matchesById: new Map(),
            equipesById: new Map(),
            gymnasesById: new Map(),
            poulesById: new Map(),
            slotsById: new Map(),
            matchesByWeek: new Map(),
            matchesByPool: new Map(),
            matchesByVenue: new Map()
        };
        
        // ==================== OBSERVERS ====================
        this.observers = new Set();
        
        // ==================== INITIALIZATION ====================
        this._buildIndexes();
        this._recomputeState();
        
        console.log('📊 DataManager initialized:', {
            version: this.original.version,
            scheduledMatches: this.original.matches.scheduled.length,
            unscheduledMatches: this.original.matches.unscheduled.length,
            equipes: this.original.entities.equipes.length,
            gymnases: this.original.entities.gymnases.length,
            poules: this.original.entities.poules.length
        });
    }
    
    // ==================== DATA ACCESS METHODS ====================
    
    /**
     * Get all data (current state with modifications applied)
     * Returns complete data structure for views
     */
    getData() {
        return {
            version: this.current.version,
            metadata: this.current.metadata,
            config: this.current.config,
            entities: this.current.entities,
            matches: this.current.matches,
            slots: this.current.slots,
            statistics: this.current.statistics
        };
    }
    
    /**
     * Get all scheduled matches (current state with modifications applied)
     */
    getScheduledMatches() {
        return this.current.matches.scheduled;
    }
    
    /**
     * Get all unscheduled matches
     */
    getUnscheduledMatches() {
        return this.current.matches.unscheduled;
    }
    
    /**
     * Get match by ID
     */
    getMatch(matchId) {
        return this.indexes.matchesById.get(matchId);
    }
    
    /**
     * Alias for getMatch (used by views)
     */
    getMatchById(matchId) {
        return this.getMatch(matchId);
    }
    
    /**
     * Get matches for a specific week
     */
    getMatchesByWeek(week) {
        return this.indexes.matchesByWeek.get(week) || [];
    }
    
    /**
     * Get matches for a specific pool
     */
    getMatchesByPool(poolId) {
        return this.indexes.matchesByPool.get(poolId) || [];
    }
    
    /**
     * Get matches for a specific venue
     */
    getMatchesByVenue(venueId) {
        return this.indexes.matchesByVenue.get(venueId) || [];
    }
    
    /**
     * Get all teams
     */
    getEquipes() {
        return this.current.entities.equipes;
    }
    
    /**
     * Get team by ID
     */
    getEquipe(equipeId) {
        return this.indexes.equipesById.get(equipeId);
    }
    
    /**
     * Get multiple teams by IDs
     */
    getEquipesByIds(equipeIds) {
        if (!Array.isArray(equipeIds)) return [];
        return equipeIds.map(id => this.getEquipe(id)).filter(Boolean);
    }
    
    /**
     * Get all venues
     */
    getGymnases() {
        return this.current.entities.gymnases;
    }
    
    /**
     * Get venue by ID
     */
    getGymnase(gymnaseId) {
        return this.indexes.gymnasesById.get(gymnaseId);
    }
    
    /**
     * Alias for getGymnase (used by views)
     */
    getGymnaseById(gymnaseId) {
        return this.getGymnase(gymnaseId);
    }
    
    /**
     * Get all pools
     */
    getPoules() {
        return this.current.entities.poules;
    }
    
    /**
     * Get pool by ID
     */
    getPoule(pouleId) {
        return this.indexes.poulesById.get(pouleId);
    }
    
    /**
     * Alias for getPoule (used by views)
     */
    getPouleById(pouleId) {
        return this.getPoule(pouleId);
    }
    
    /**
     * Get all available slots
     */
    getAvailableSlots() {
        return this.current.slots.available;
    }
    
    /**
     * Get all occupied slots
     */
    getOccupiedSlots() {
        return this.current.slots.occupied;
    }
    
    /**
     * Get slot by ID
     */
    getSlot(slotId) {
        return this.indexes.slotsById.get(slotId);
    }
    
    /**
     * Check if a slot is available
     */
    isSlotAvailable(semaine, horaire, gymnase) {
        const slotId = `S_${gymnase}_${semaine}_${horaire}`;
        const slot = this.indexes.slotsById.get(slotId);
        return slot && slot.status === 'libre';
    }
    
    /**
     * Get statistics
     */
    getStatistics() {
        return this.current.statistics;
    }
    
    /**
     * Get metadata
     */
    getMetadata() {
        return this.original.metadata;
    }
    
    /**
     * Get config
     */
    getConfig() {
        return this.original.config;
    }
    
    // ==================== MODIFICATION METHODS ====================
    
    /**
     * Apply a modification to a match
     * This will trigger a state recomputation and notify observers
     */
    applyModification(matchId, newSlot) {
        const match = this.getMatch(matchId);
        if (!match) {
            console.error(`Match ${matchId} not found`);
            return false;
        }
        
        // Check if slot is available
        if (!this.isSlotAvailable(newSlot.semaine, newSlot.horaire, newSlot.gymnase)) {
            console.warn(`Slot ${newSlot.semaine}/${newSlot.horaire}/${newSlot.gymnase} is not available`);
            return false;
        }
        
        // Store original state
        const original = {
            semaine: match.semaine,
            horaire: match.horaire,
            gymnase: match.gymnase
        };
        
        // Create modification record
        const modification = {
            match_id: matchId,
            timestamp: new Date().toISOString(),
            original: original,
            new: newSlot,
            author: 'user'
        };
        
        // Delegate to modification manager
        if (window.modificationManager) {
            window.modificationManager.addModification(modification);
        }
        
        // Recompute state
        this._recomputeState();
        
        // Notify observers
        this._notifyObservers({
            type: 'MODIFICATION_APPLIED',
            matchId,
            modification
        });
        
        return true;
    }
    
    /**
     * Revert all modifications
     */
    revertAllModifications() {
        if (window.modificationManager) {
            window.modificationManager.clearAll();
        }
        
        this._recomputeState();
        
        this._notifyObservers({
            type: 'ALL_MODIFICATIONS_REVERTED'
        });
    }
    
    // ==================== OBSERVER PATTERN ====================
    
    /**
     * Subscribe to data changes
     * @param {Function} callback - Called with event object
     * @returns {Function} Unsubscribe function
     */
    subscribe(callback) {
        this.observers.add(callback);
        return () => this.observers.delete(callback);
    }
    
    /**
     * Notify all observers of a change
     */
    _notifyObservers(event) {
        this.observers.forEach(callback => {
            try {
                callback(event);
            } catch (error) {
                console.error('Observer error:', error);
            }
        });
    }
    
    // ==================== INTERNAL METHODS ====================
    
    /**
     * Build indexes for fast data access
     */
    _buildIndexes() {
        // Index entities
        this.original.entities.equipes.forEach(equipe => {
            this.indexes.equipesById.set(equipe.id, equipe);
        });
        
        this.original.entities.gymnases.forEach(gymnase => {
            this.indexes.gymnasesById.set(gymnase.id, gymnase);
        });
        
        this.original.entities.poules.forEach(poule => {
            this.indexes.poulesById.set(poule.id, poule);
        });
        
        // Index matches
        this.original.matches.scheduled.forEach(match => {
            this.indexes.matchesById.set(match.match_id, match);
            
            // By week
            if (!this.indexes.matchesByWeek.has(match.semaine)) {
                this.indexes.matchesByWeek.set(match.semaine, []);
            }
            this.indexes.matchesByWeek.get(match.semaine).push(match);
            
            // By pool
            if (!this.indexes.matchesByPool.has(match.poule)) {
                this.indexes.matchesByPool.set(match.poule, []);
            }
            this.indexes.matchesByPool.get(match.poule).push(match);
            
            // By venue
            if (!this.indexes.matchesByVenue.has(match.gymnase)) {
                this.indexes.matchesByVenue.set(match.gymnase, []);
            }
            this.indexes.matchesByVenue.get(match.gymnase).push(match);
        });
        
        // Index slots
        [...this.original.slots.available, ...this.original.slots.occupied].forEach(slot => {
            this.indexes.slotsById.set(slot.slot_id, slot);
        });
    }
    
    /**
     * Recompute current state from original + modifications
     */
    _recomputeState() {
        // Clone original data
        this.current = JSON.parse(JSON.stringify(this.original));
        
        // Apply modifications if modification manager exists
        if (window.modificationManager) {
            const modifications = window.modificationManager.getAllModifications();
            
            modifications.forEach(mod => {
                const match = this.current.matches.scheduled.find(m => m.match_id === mod.match_id);
                if (match) {
                    // Update match slot
                    match.semaine = mod.new.semaine;
                    match.horaire = mod.new.horaire;
                    match.gymnase = mod.new.gymnase;
                    
                    // Update slot status
                    this._updateSlotStatus(mod.original, 'libre', null);
                    this._updateSlotStatus(mod.new, 'occupé', mod.match_id);
                }
            });
        }
        
        // Rebuild indexes with current data
        this._rebuildIndexes();
    }
    
    /**
     * Rebuild indexes after state change
     */
    _rebuildIndexes() {
        // Clear match indexes
        this.indexes.matchesById.clear();
        this.indexes.matchesByWeek.clear();
        this.indexes.matchesByPool.clear();
        this.indexes.matchesByVenue.clear();
        
        // Rebuild from current state
        this.current.matches.scheduled.forEach(match => {
            this.indexes.matchesById.set(match.match_id, match);
            
            if (!this.indexes.matchesByWeek.has(match.semaine)) {
                this.indexes.matchesByWeek.set(match.semaine, []);
            }
            this.indexes.matchesByWeek.get(match.semaine).push(match);
            
            if (!this.indexes.matchesByPool.has(match.poule)) {
                this.indexes.matchesByPool.set(match.poule, []);
            }
            this.indexes.matchesByPool.get(match.poule).push(match);
            
            if (!this.indexes.matchesByVenue.has(match.gymnase)) {
                this.indexes.matchesByVenue.set(match.gymnase, []);
            }
            this.indexes.matchesByVenue.get(match.gymnase).push(match);
        });
    }
    
    /**
     * Update slot status
     */
    _updateSlotStatus(slotInfo, status, matchId) {
        const slotId = `S_${slotInfo.gymnase}_${slotInfo.semaine}_${slotInfo.horaire}`;
        const slot = this.indexes.slotsById.get(slotId);
        
        if (slot) {
            slot.status = status;
            slot.match_id = matchId;
        }
    }
}

// Export for use in other modules
window.DataManager = DataManager;
