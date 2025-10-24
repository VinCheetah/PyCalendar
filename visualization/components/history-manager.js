/**
 * History Manager - Gestion de l'historique avec undo/redo
 * Système de pile pour annuler/refaire les modifications
 */

class HistoryManager {
    constructor(maxHistorySize = 50) {
        this.undoStack = [];
        this.redoStack = [];
        this.maxHistorySize = maxHistorySize;
        this.listeners = new Set();
        
        // Charger l'historique depuis localStorage
        this.loadFromStorage();
        
        // Écouter les raccourcis clavier
        this.setupKeyboardShortcuts();
    }

    /**
     * Enregistre une action dans l'historique
     * @param {Object} action - { type, data, timestamp, description }
     */
    pushAction(action) {
        const historyEntry = {
            ...action,
            timestamp: action.timestamp || new Date().toISOString(),
            id: this.generateId()
        };
        
        // Ajouter à la pile d'undo
        this.undoStack.push(historyEntry);
        
        // Vider la pile de redo (nouvelle branche d'historique)
        this.redoStack = [];
        
        // Limiter la taille de l'historique
        if (this.undoStack.length > this.maxHistorySize) {
            this.undoStack.shift();
        }
        
        // Sauvegarder dans localStorage
        this.saveToStorage();
        
        // Notifier les listeners
        this.notifyListeners();
        
        console.log('📝 Action enregistrée:', historyEntry.description || historyEntry.type);
    }

    /**
     * Annule la dernière action
     * @returns {Object|null} - Action annulée ou null
     */
    undo() {
        if (this.undoStack.length === 0) {
            console.log('⚠️ Rien à annuler');
            return null;
        }
        
        const action = this.undoStack.pop();
        this.redoStack.push(action);
        
        this.saveToStorage();
        this.notifyListeners();
        
        console.log('↶ Undo:', action.description || action.type);
        return action;
    }

    /**
     * Refait la dernière action annulée
     * @returns {Object|null} - Action refaite ou null
     */
    redo() {
        if (this.redoStack.length === 0) {
            console.log('⚠️ Rien à refaire');
            return null;
        }
        
        const action = this.redoStack.pop();
        this.undoStack.push(action);
        
        this.saveToStorage();
        this.notifyListeners();
        
        console.log('↷ Redo:', action.description || action.type);
        return action;
    }

    /**
     * Récupère l'historique complet
     */
    getHistory() {
        return {
            undo: [...this.undoStack],
            redo: [...this.redoStack],
            canUndo: this.canUndo(),
            canRedo: this.canRedo()
        };
    }

    /**
     * Vérifie si on peut annuler
     */
    canUndo() {
        return this.undoStack.length > 0;
    }

    /**
     * Vérifie si on peut refaire
     */
    canRedo() {
        return this.redoStack.length > 0;
    }

    /**
     * Efface tout l'historique
     */
    clear() {
        this.undoStack = [];
        this.redoStack = [];
        this.saveToStorage();
        this.notifyListeners();
        console.log('🗑️ Historique effacé');
    }

    /**
     * Sauvegarde l'historique dans localStorage
     */
    saveToStorage() {
        try {
            const data = {
                undo: this.undoStack,
                redo: this.redoStack,
                savedAt: new Date().toISOString()
            };
            localStorage.setItem('calendarHistory', JSON.stringify(data));
        } catch (error) {
            console.error('❌ Erreur sauvegarde historique:', error);
        }
    }

    /**
     * Charge l'historique depuis localStorage
     */
    loadFromStorage() {
        try {
            const stored = localStorage.getItem('calendarHistory');
            if (stored) {
                const data = JSON.parse(stored);
                this.undoStack = data.undo || [];
                this.redoStack = data.redo || [];
                console.log('📂 Historique chargé:', this.undoStack.length, 'actions');
            }
        } catch (error) {
            console.error('❌ Erreur chargement historique:', error);
            this.undoStack = [];
            this.redoStack = [];
        }
    }

    /**
     * Ajoute un listener pour les changements d'historique
     */
    addListener(callback) {
        this.listeners.add(callback);
    }

    /**
     * Retire un listener
     */
    removeListener(callback) {
        this.listeners.delete(callback);
    }

    /**
     * Notifie tous les listeners
     */
    notifyListeners() {
        const state = {
            canUndo: this.canUndo(),
            canRedo: this.canRedo(),
            undoCount: this.undoStack.length,
            redoCount: this.redoStack.length
        };
        
        this.listeners.forEach(callback => {
            try {
                callback(state);
            } catch (error) {
                console.error('❌ Erreur listener historique:', error);
            }
        });
    }

    /**
     * Configure les raccourcis clavier
     */
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl+Z ou Cmd+Z : Undo
            if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
                e.preventDefault();
                const action = this.undo();
                if (action && window.historyPanel) {
                    window.historyPanel.handleUndo(action);
                }
            }
            
            // Ctrl+Shift+Z ou Cmd+Shift+Z ou Ctrl+Y : Redo
            if (((e.ctrlKey || e.metaKey) && e.key === 'z' && e.shiftKey) || 
                ((e.ctrlKey || e.metaKey) && e.key === 'y')) {
                e.preventDefault();
                const action = this.redo();
                if (action && window.historyPanel) {
                    window.historyPanel.handleRedo(action);
                }
            }
        });
        
        console.log('⌨️ Raccourcis historique activés (Ctrl+Z / Ctrl+Shift+Z)');
    }

    /**
     * Génère un ID unique
     */
    generateId() {
        return `action_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Formate une action pour l'affichage
     */
    formatAction(action) {
        const date = new Date(action.timestamp);
        const timeStr = date.toLocaleTimeString('fr-FR', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
        
        return {
            id: action.id,
            time: timeStr,
            description: action.description || action.type,
            type: action.type,
            data: action.data
        };
    }

    /**
     * Récupère les N dernières actions
     */
    getRecentActions(count = 10) {
        return this.undoStack
            .slice(-count)
            .reverse()
            .map(action => this.formatAction(action));
    }

    /**
     * Recherche dans l'historique
     */
    searchHistory(query) {
        const lowerQuery = query.toLowerCase();
        return this.undoStack
            .filter(action => {
                const desc = (action.description || action.type).toLowerCase();
                return desc.includes(lowerQuery);
            })
            .map(action => this.formatAction(action));
    }

    /**
     * Revenir à un point spécifique de l'historique
     */
    revertToAction(actionId) {
        const index = this.undoStack.findIndex(a => a.id === actionId);
        if (index === -1) {
            console.error('❌ Action non trouvée:', actionId);
            return null;
        }
        
        // Annuler toutes les actions jusqu'à celle-ci
        const actionsToUndo = [];
        while (this.undoStack.length > index + 1) {
            actionsToUndo.push(this.undo());
        }
        
        console.log('↶ Retour à:', this.undoStack[index].description);
        return actionsToUndo;
    }

    /**
     * Exporte l'historique au format JSON
     */
    exportHistory() {
        return JSON.stringify({
            undo: this.undoStack,
            redo: this.redoStack,
            exportedAt: new Date().toISOString()
        }, null, 2);
    }

    /**
     * Importe un historique depuis JSON
     */
    importHistory(jsonData) {
        try {
            const data = JSON.parse(jsonData);
            this.undoStack = data.undo || [];
            this.redoStack = data.redo || [];
            this.saveToStorage();
            this.notifyListeners();
            console.log('✅ Historique importé:', this.undoStack.length, 'actions');
            return true;
        } catch (error) {
            console.error('❌ Erreur import historique:', error);
            return false;
        }
    }
}
