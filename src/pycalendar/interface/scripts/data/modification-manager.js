/**
 * ModificationManager - Manages calendar modifications with export capability
 * 
 * Responsibilities:
 * - Store modifications in localStorage
 * - Track modification history
 * - Export modifications to JSON
 * - Import modifications from JSON
 * - Undo/Redo functionality
 * 
 * Storage Format (localStorage):
 * {
 *   base_solution: "solution_file.json",
 *   modifications: [...],
 *   last_updated: "ISO timestamp"
 * }
 */

class ModificationManager {
    constructor(baseSolutionName = 'unknown') {
        this.baseSolutionName = baseSolutionName;
        this.storageKey = 'pycalendar_modifications';
        this.modifications = [];
        this.history = {
            past: [],
            future: []
        };
        this.listeners = []; // Pour les abonnements
        
        this._loadFromStorage();
    }
    
    // ==================== GESTION DES ÉCOUTEURS ====================

    /**
     * S'abonner aux changements.
     * @param {function} listener - La fonction à appeler lors d'un changement.
     */
    subscribe(listener) {
        this.listeners.push(listener);
    }

    /**
     * Se désabonner.
     * @param {function} listener - La fonction à retirer.
     */
    unsubscribe(listener) {
        this.listeners = this.listeners.filter(l => l !== listener);
    }

    /**
     * Notifie tous les écouteurs d'un changement.
     */
    _notify() {
        this.listeners.forEach(listener => {
            try {
                listener();
            } catch (error) {
                console.error("Erreur dans un écouteur de ModificationManager:", error);
            }
        });
    }

    // ==================== MODIFICATION MANAGEMENT ====================
    
    /**
     * Add a new modification
     */
    addModification(modification) {
        // Validate modification format
        if (!this._validateModification(modification)) {
            return false;
        }
        
        // Check if modification already exists for this match
        const existingIndex = this.modifications.findIndex(
            m => m.match_id === modification.match_id
        );
        
        if (existingIndex >= 0) {
            // Update existing modification
            this.modifications[existingIndex] = modification;
        } else {
            // Add new modification
            this.modifications.push(modification);
        }
        
        // Clear redo history when new modification is made
        this.history.future = [];
        
        // Save to storage
        this._saveToStorage();
        
        // Notifier les écouteurs
        this._notify();

        return true;
    }
    
    /**
     * Remove a modification
     */
    removeModification(matchId) {
        const index = this.modifications.findIndex(m => m.match_id === matchId);
        
        if (index >= 0) {
            const removed = this.modifications.splice(index, 1)[0];
            this._saveToStorage();
            this._notify(); // Notifier
            return removed;
        }
        
        return null;
    }
    
    /**
     * Get all modifications
     */
    getAllModifications() {
        return [...this.modifications];
    }
    
    /**
     * Get modification for a specific match
     */
    getModification(matchId) {
        return this.modifications.find(m => m.match_id === matchId);
    }
    
    /**
     * Check if a match has been modified
     */
    hasModification(matchId) {
        return this.modifications.some(m => m.match_id === matchId);
    }
    
    /**
     * Get number of modifications
     */
    getModificationCount() {
        return this.modifications.length;
    }
    
    /**
     * Clear all modifications
     */
    clearAll() {
        this.modifications = [];
        this.history = { past: [], future: [] };
        this._saveToStorage();
        this._notify(); // Notifier
    }
    
    // ==================== UNDO/REDO ====================
    
    /**
     * Undo last modification
     */
    undo() {
        if (this.modifications.length === 0) {
            return null;
        }
        
        const lastModification = this.modifications.pop();
        this.history.past.push([...this.modifications]);
        this.history.future.push(lastModification);
        
        this._saveToStorage();
        this._notify(); // Notifier
        
        return lastModification;
    }
    
    /**
     * Redo last undone modification
     */
    redo() {
        if (this.history.future.length === 0) {
            return null;
        }
        
        const modification = this.history.future.pop();
        this.modifications.push(modification);
        this.history.past.push([...this.modifications]);
        
        this._saveToStorage();
        this._notify(); // Notifier
        
        return modification;
    }
    
    /**
     * Check if undo is available
     */
    canUndo() {
        return this.modifications.length > 0;
    }
    
    /**
     * Check if redo is available
     */
    canRedo() {
        return this.history.future.length > 0;
    }
    
    // ==================== EXPORT/IMPORT ====================
    
    /**
     * Export modifications to JSON format
     * @returns {Object} Export data matching modification_schema.json
     */
    exportToJSON() {
        const exportData = {
            export_version: "1.0",
            exported_at: new Date().toISOString(),
            base_solution: this.baseSolutionName,
            modifications: this.modifications.map(mod => ({
                match_id: mod.match_id,
                timestamp: mod.timestamp,
                original: {
                    semaine: mod.original.semaine,
                    horaire: mod.original.horaire,
                    gymnase: mod.original.gymnase
                },
                new: {
                    semaine: mod.new.semaine,
                    horaire: mod.new.horaire,
                    gymnase: mod.new.gymnase
                },
                reason: mod.reason || '',
                author: mod.author || 'user'
            })),
            statistics: this._calculateStatistics()
        };
        
        return exportData;
    }
    
    /**
     * Export and download as JSON file
     */
    exportAndDownload(filename = null) {
        const exportData = this.exportToJSON();
        
        // Generate filename if not provided
        if (!filename) {
            const date = new Date().toISOString().split('T')[0];
            filename = `pycalendar_modifications_${date}.json`;
        }
        
        // Create blob and download
        const blob = new Blob([JSON.stringify(exportData, null, 2)], {
            type: 'application/json'
        });
        
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
        
        return exportData;
    }
    
    /**
     * Import modifications from JSON
     */
    importFromJSON(jsonData) {
        try {
            // Validate import data
            if (!jsonData.export_version || !jsonData.modifications) {
                throw new Error('Invalid import data format');
            }
            
            // Clear existing modifications (or merge?)
            const shouldClear = confirm(
                'Clear existing modifications before import?\n' +
                'Click OK to replace, Cancel to merge.'
            );
            
            if (shouldClear) {
                this.modifications = [];
            }
            
            // Import modifications
            jsonData.modifications.forEach(mod => {
                this.addModification(mod);
            });
            
            return true;
            
        } catch (error) {
            return false;
        }
    }
    
    // ==================== STATISTICS ====================
    
    /**
     * Calculate statistics about modifications
     */
    _calculateStatistics() {
        const stats = {
            total_modifications: this.modifications.length,
            matches_modified: new Set(this.modifications.map(m => m.match_id)).size,
            conflicts_resolved: 0, // TODO: Implement conflict tracking
            penalty_delta: 0 // TODO: Implement penalty calculation
        };
        
        return stats;
    }
    
    // ==================== STORAGE ====================
    
    /**
     * Load modifications from localStorage
     */
    _loadFromStorage() {
        try {
            const stored = localStorage.getItem(this.storageKey);
            if (stored) {
                const data = JSON.parse(stored);
                this.modifications = data.modifications || [];
                this.baseSolutionName = data.base_solution || this.baseSolutionName;
                
            }
        } catch (error) {
            this.modifications = [];
        }
    }
    
    /**
     * Save modifications to localStorage
     */
    _saveToStorage() {
        try {
            const data = {
                base_solution: this.baseSolutionName,
                modifications: this.modifications,
                last_updated: new Date().toISOString()
            };
            
            localStorage.setItem(this.storageKey, JSON.stringify(data));
            
        } catch (error) {
            
            // Check if quota exceeded
            if (error.name === 'QuotaExceededError') {
                alert('Storage quota exceeded. Consider exporting modifications and clearing old data.');
            }
        }
    }
    
    /**
     * Clear localStorage
     */
    clearStorage() {
        localStorage.removeItem(this.storageKey);
    }
    
    // ==================== VALIDATION ====================
    
    /**
     * Validate modification format
     */
    _validateModification(modification) {
        // Required fields
        const requiredFields = ['match_id', 'timestamp', 'original', 'new'];
        for (const field of requiredFields) {
            if (!(field in modification)) {
                return false;
            }
        }
        
        // Validate slot structure
        const requiredSlotFields = ['semaine', 'horaire', 'gymnase'];
        for (const slotField of requiredSlotFields) {
            if (!(slotField in modification.original)) {
                return false;
            }
            if (!(slotField in modification.new)) {
                return false;
            }
        }
        
        return true;
    }
}

// Export for use in other modules
window.ModificationManager = ModificationManager;
