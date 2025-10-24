/**
 * DataManager - Source de vérité unique pour toutes les données du calendrier
 * 
 * RESPONSABILITÉS:
 * - Stocker les données originales (immuables)
 * - Gérer les modifications (localStorage)
 * - Calculer l'état actuel des matchs (original + modifications)
 * - Synchroniser avec SlotManager
 * - Notifier les observateurs des changements
 * 
 * PRINCIPES:
 * 1. Une seule source de vérité
 * 2. Immutabilité des données originales
 * 3. État calculé = Original + Modifications
 * 4. Synchronisation automatique
 */

class DataManager {
    constructor(originalMatches, originalSlots, unscheduledMatches) {
        // ============ DONNÉES ORIGINALES (IMMUABLES) ============
        this.originalMatches = this._deepFreeze(originalMatches);
        this.originalSlots = this._deepFreeze(originalSlots);
        this.unscheduledMatches = unscheduledMatches;
        
        // ============ ÉTAT ACTUEL (CALCULÉ) ============
        this.currentMatches = [];
        this.modifications = this._loadModifications();
        
        // ============ OBSERVATEURS ============
        this.observers = new Set();
        
        // ============ INITIALISATION ============
        this._recalculateCurrentState();
        
        console.log('📊 DataManager initialized:', {
            originalMatches: this.originalMatches.length,
            modifications: Object.keys(this.modifications).length,
            currentMatches: this.currentMatches.length
        });
    }
    
    /**
     * Deep freeze pour garantir l'immutabilité
     */
    _deepFreeze(data) {
        const frozen = JSON.parse(JSON.stringify(data));
        Object.freeze(frozen);
        return frozen;
    }
    
    /**
     * Charger les modifications depuis localStorage
     */
    _loadModifications() {
        try {
            const saved = localStorage.getItem('matchModifications');
            return saved ? JSON.parse(saved) : {};
        } catch (e) {
            console.error('❌ Error loading modifications:', e);
            return {};
        }
    }
    
    /**
     * Sauvegarder les modifications dans localStorage
     */
    _saveModifications() {
        try {
            localStorage.setItem('matchModifications', JSON.stringify(this.modifications));
            console.log('💾 Modifications saved:', Object.keys(this.modifications).length);
        } catch (e) {
            console.error('❌ Error saving modifications:', e);
        }
    }
    
    /**
     * MÉTHODE CENTRALE: Recalculer l'état actuel
     * État actuel = Données originales + Modifications appliquées
     */
    _recalculateCurrentState() {
        console.log('🔄 Recalculating current state...');
        
        // Step 1: Clone original data
        this.currentMatches = JSON.parse(JSON.stringify(this.originalMatches));
        
        // Step 2: Apply all modifications
        Object.entries(this.modifications).forEach(([matchId, mod]) => {
            const match = this.currentMatches.find(m => m.match_id === matchId);
            if (match) {
                match.semaine = mod.new.week;
                match.horaire = mod.new.time;
                match.gymnase = mod.new.venue;
                console.log(`  ✏️ Applied: ${matchId} → ${mod.new.week}/${mod.new.time}/${mod.new.venue}`);
            } else {
                console.warn(`  ⚠️ Match ${matchId} not found`);
            }
        });
        
        console.log('✅ Current state recalculated:', this.currentMatches.length, 'matches');
    }
    
    /**
     * LECTURE: Obtenir l'état actuel des matchs
     */
    getCurrentMatches() {
        return [...this.currentMatches]; // Return copy to prevent external mutation
    }
    
    /**
     * LECTURE: Obtenir les données originales
     */
    getOriginalMatches() {
        return this.originalMatches; // Already frozen, safe to return
    }
    
    /**
     * LECTURE: Obtenir les slots originaux
     */
    getOriginalSlots() {
        return this.originalSlots; // Already frozen, safe to return
    }
    
    /**
     * LECTURE: Obtenir les modifications
     */
    getModifications() {
        return {...this.modifications}; // Return copy
    }
    
    /**
     * LECTURE: Vérifier si un match a été modifié
     */
    isModified(matchId) {
        return matchId in this.modifications;
    }
    
    /**
     * ÉCRITURE: Enregistrer une modification
     */
    saveModification(modification) {
        const { match_id, original, new: newValues } = modification;
        
        console.log('📝 Saving modification:', match_id);
        
        // Check if modification actually changes something
        const hasChange = 
            original.week !== newValues.week ||
            original.time !== newValues.time ||
            original.venue !== newValues.venue;
        
        if (!hasChange) {
            console.log('  ℹ️ No actual change, ignoring');
            return false;
        }
        
        // Save modification
        this.modifications[match_id] = {
            original: {...original},
            new: {...newValues},
            timestamp: new Date().toISOString()
        };
        
        // Persist to localStorage
        this._saveModifications();
        
        // Recalculate current state
        this._recalculateCurrentState();
        
        // Notify observers
        this._notifyObservers({
            type: 'MODIFICATION_SAVED',
            matchId: match_id,
            modification: this.modifications[match_id]
        });
        
        return true;
    }
    
    /**
     * ÉCRITURE: Annuler une modification
     */
    undoModification(matchId) {
        if (!(matchId in this.modifications)) {
            console.warn('⚠️ No modification to undo for', matchId);
            return false;
        }
        
        console.log('↩️ Undoing modification:', matchId);
        
        delete this.modifications[matchId];
        this._saveModifications();
        this._recalculateCurrentState();
        
        this._notifyObservers({
            type: 'MODIFICATION_UNDONE',
            matchId: matchId
        });
        
        return true;
    }
    
    /**
     * ÉCRITURE: Annuler toutes les modifications
     */
    resetAllModifications() {
        console.log('🔄 Resetting all modifications');
        
        const count = Object.keys(this.modifications).length;
        this.modifications = {};
        
        this._saveModifications();
        this._recalculateCurrentState();
        
        this._notifyObservers({
            type: 'ALL_MODIFICATIONS_RESET',
            count: count
        });
        
        return count;
    }
    
    /**
     * OBSERVATEUR: S'abonner aux changements
     */
    subscribe(callback) {
        this.observers.add(callback);
        console.log('👀 Observer subscribed, total:', this.observers.size);
        
        // Return unsubscribe function
        return () => {
            this.observers.delete(callback);
            console.log('👋 Observer unsubscribed, total:', this.observers.size);
        };
    }
    
    /**
     * OBSERVATEUR: Notifier tous les observateurs
     */
    _notifyObservers(event) {
        console.log('📢 Notifying observers:', event.type);
        this.observers.forEach(callback => {
            try {
                callback(event);
            } catch (e) {
                console.error('❌ Observer callback error:', e);
            }
        });
    }
    
    /**
     * UTILITAIRE: Obtenir un match par ID (état actuel)
     */
    getMatchById(matchId) {
        return this.currentMatches.find(m => m.match_id === matchId);
    }
    
    /**
     * UTILITAIRE: Obtenir un match original par ID
     */
    getOriginalMatchById(matchId) {
        return this.originalMatches.find(m => m.match_id === matchId);
    }
    
    /**
     * UTILITAIRE: Statistiques
     */
    getStats() {
        return {
            totalMatches: this.originalMatches.length,
            modifiedMatches: Object.keys(this.modifications).length,
            unscheduledMatches: this.unscheduledMatches.length,
            modificationRate: (Object.keys(this.modifications).length / this.originalMatches.length * 100).toFixed(1) + '%'
        };
    }
    
    /**
     * DEBUG: Afficher l'état complet
     */
    debugState() {
        console.group('🔍 DataManager State');
        console.log('Original matches:', this.originalMatches.length);
        console.log('Current matches:', this.currentMatches.length);
        console.log('Modifications:', Object.keys(this.modifications).length);
        console.log('Observers:', this.observers.size);
        console.table(this.getStats());
        console.groupEnd();
    }
}
