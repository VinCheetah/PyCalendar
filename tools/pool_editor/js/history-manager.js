/**
 * PyCalendar Pool Editor - History Manager
 * Handles undo/redo functionality and action tracking
 */

class HistoryManager {
    constructor() {
        this.actions = [];
        this.undoneActions = [];
        this.maxHistory = 50;
    }
    
    /**
     * Add an action to history
     */
    addAction(action) {
        // Clear redo stack
        this.undoneActions = [];
        
        // Add timestamp
        action.timestamp = new Date();
        
        // Add to history
        this.actions.push(action);
        
        // Trim if too long
        if (this.actions.length > this.maxHistory) {
            this.actions.shift();
        }
        
        this.updateUI();
    }
    
    /**
     * Undo last action
     */
    undo() {
        if (this.actions.length === 0) {
            Utils.showToast('Rien à annuler', 'info');
            return;
        }
        
        const action = this.actions.pop();
        
        if (action.undo && typeof action.undo === 'function') {
            try {
                action.undo();
                this.undoneActions.push(action);
                Utils.showToast(`Annulé: ${this.getActionDescription(action)}`, 'info');
                poolRenderer.render();
            } catch (error) {
                console.error('Error undoing action:', error);
                Utils.showToast('Erreur lors de l\'annulation', 'error');
            }
        }
        
        this.updateUI();
    }
    
    /**
     * Redo last undone action
     */
    redo() {
        if (this.undoneActions.length === 0) {
            Utils.showToast('Rien à rétablir', 'info');
            return;
        }
        
        const action = this.undoneActions.pop();
        
        if (action.redo && typeof action.redo === 'function') {
            try {
                action.redo();
                this.actions.push(action);
                Utils.showToast(`Rétabli: ${this.getActionDescription(action)}`, 'info');
                poolRenderer.render();
            } catch (error) {
                console.error('Error redoing action:', error);
                Utils.showToast('Erreur lors du rétablissement', 'error');
            }
        }
        
        this.updateUI();
    }
    
    /**
     * Get action description
     */
    getActionDescription(action) {
        // If a custom description is provided, use it
        if (action.description) {
            return action.description;
        }
        
        switch (action.type) {
            case 'moveTeam':
                return `Déplacement de ${action.teamName}`;
            case 'addTeam':
                return `Ajout de ${action.teamName}`;
            case 'editTeam':
                return `Modification de ${action.teamName}`;
            case 'deleteTeam':
                return `Suppression de ${action.teamName}`;
            case 'addPool':
                return `Ajout de ${action.poolName}`;
            case 'editPool':
                return `Modification de ${action.poolName}`;
            case 'deletePool':
                return `Suppression de ${action.poolName}`;
            case 'autoCreate':
                return 'Création automatique';
            case 'balance':
                return 'Équilibrage';
            default:
                return 'Action';
        }
    }
    
    /**
     * Get action icon
     */
    getActionIcon(action) {
        const icons = {
            'moveTeam': '↔️',
            'addTeam': '➕',
            'editTeam': '✏️',
            'deleteTeam': '🗑️',
            'addPool': '➕',
            'editPool': '✏️',
            'deletePool': '🗑️',
            'autoCreate': '🎯',
            'balance': '⚖️'
        };
        return icons[action.type] || '📝';
    }
    
    /**
     * Update history panel and buttons
     */
    updateUI() {
        this.updateHistoryPanel();
        this.updateButtons();
    }
    
    /**
     * Update history panel
     */
    updateHistoryPanel() {
        const panel = document.getElementById('history-panel');
        if (!panel) return;
        
        if (this.actions.length === 0) {
            panel.innerHTML = '<p class="empty-message">Aucune action récente</p>';
            return;
        }
        
        // Show last 10 actions (newest first)
        const recentActions = this.actions.slice(-10).reverse();
        
        panel.innerHTML = recentActions.map((action, index) => {
            const timeAgo = Utils.getTimeAgo(action.timestamp);
            const canUndo = index === 0;
            
            return `
                <div class="history-item">
                    <span class="history-icon">${this.getActionIcon(action)}</span>
                    <div class="history-content">
                        <div class="history-action">${this.getActionDescription(action)}</div>
                        <div class="history-time">${timeAgo}</div>
                    </div>
                    ${canUndo ? '<button class="history-undo" onclick="historyManager.undo()">Annuler</button>' : ''}
                </div>
            `;
        }).join('');
    }
    
    /**
     * Update undo/redo buttons
     */
    updateButtons() {
        const undoBtn = document.getElementById('btn-undo');
        const redoBtn = document.getElementById('btn-redo');
        
        if (undoBtn) {
            undoBtn.disabled = this.actions.length === 0;
        }
        
        if (redoBtn) {
            redoBtn.disabled = this.undoneActions.length === 0;
        }
    }
    
    /**
     * Clear history
     */
    clear() {
        this.actions = [];
        this.undoneActions = [];
        this.updateUI();
    }
    
    /**
     * Check if can undo
     */
    canUndo() {
        return this.actions.length > 0;
    }
    
    /**
     * Check if can redo
     */
    canRedo() {
        return this.undoneActions.length > 0;
    }
}

// Create global instance
window.historyManager = new HistoryManager();
