/**
 * Conflict Panel UI - Interface utilisateur pour les conflits
 */

class ConflictPanel {
    constructor(conflictDetector) {
        this.conflictDetector = conflictDetector;
        this.panel = null;
        this.isVisible = false;
        this.createPanel();
    }

    /**
     * Crée le panel HTML
     */
    createPanel() {
        this.panel = document.createElement('div');
        this.panel.className = 'conflict-panel';
        this.panel.innerHTML = `
            <div class="conflict-panel-header">
                <div class="conflict-panel-title">
                    <span>⚠️</span>
                    <span>Conflits Détectés</span>
                </div>
                <button class="conflict-panel-close" onclick="window.conflictPanel.hide()">×</button>
            </div>
            <div class="conflict-panel-body">
                <div class="conflict-list"></div>
            </div>
        `;
        document.body.appendChild(this.panel);
    }

    /**
     * Met à jour l'affichage des conflits
     */
    update(matches) {
        const conflicts = this.conflictDetector.detectAllConflicts(matches);
        const summary = this.conflictDetector.getConflictSummary();
        
        // Mettre à jour le header avec les stats
        const header = this.panel.querySelector('.conflict-panel-title');
        header.innerHTML = `
            <span>⚠️</span>
            <span>Conflits Détectés</span>
            <div class="conflict-stats">
                <span class="conflict-stat critical">${summary.bySeverity.critical} critiques</span>
                <span class="conflict-stat warning">${summary.bySeverity.warning} avertissements</span>
            </div>
        `;
        
        // Remplir la liste
        const list = this.panel.querySelector('.conflict-list');
        
        if (summary.details.length === 0) {
            list.innerHTML = `
                <div style="text-align: center; padding: 40px; color: var(--gray);">
                    <div style="font-size: 48px; margin-bottom: 16px;">✅</div>
                    <div>Aucun conflit détecté</div>
                </div>
            `;
            return;
        }
        
        list.innerHTML = summary.details.map(conflict => `
            <div class="conflict-item ${conflict.severity}" 
                 onclick="window.conflictPanel.jumpToMatch('${conflict.matchId}')">
                <div class="conflict-item-header">
                    <div class="conflict-item-type">${this.getConflictTypeLabel(conflict.type)}</div>
                    <div class="conflict-item-severity ${conflict.severity}">${conflict.severity}</div>
                </div>
                <div class="conflict-item-message">${conflict.message}</div>
            </div>
        `).join('');
    }

    /**
     * Libellé du type de conflit
     */
    getConflictTypeLabel(type) {
        const labels = {
            'double_booking': '📍 Surcharge Gymnase',
            'team_overlap': '👥 Équipe x2',
            'rest_time': '⏱️ Repos Insuffisant',
            'time_preference': '🕐 Horaire Non Préféré',
            'venue_constraint': '🏟️ Contrainte Gymnase'
        };
        return labels[type] || type;
    }

    /**
     * Saute vers un match en conflit
     */
    jumpToMatch(matchId) {
        const card = document.querySelector(`[data-match-id="${matchId}"]`);
        if (card) {
            card.scrollIntoView({ behavior: 'smooth', block: 'center' });
            
            // Highlight temporaire
            card.style.animation = 'none';
            setTimeout(() => {
                card.style.animation = 'highlight-flash 1s ease-in-out';
            }, 10);
        }
    }

    /**
     * Affiche le panel
     */
    show() {
        this.panel.classList.add('show');
        this.isVisible = true;
    }

    /**
     * Cache le panel
     */
    hide() {
        this.panel.classList.remove('show');
        this.isVisible = false;
    }

    /**
     * Toggle le panel
     */
    toggle() {
        if (this.isVisible) {
            this.hide();
        } else {
            this.show();
        }
    }

    /**
     * Ajoute des badges de conflit aux cartes de match
     * IMPORTANT: N'affecte pas le layout (position absolute)
     */
    addConflictBadges(matches) {
        // D'ABORD: Nettoyer tous les badges et informations de conflit existants
        document.querySelectorAll('.conflict-badge').forEach(badge => badge.remove());
        document.querySelectorAll('.conflict-info').forEach(info => info.remove());
        document.querySelectorAll('.has-conflict-critical, .has-conflict-warning').forEach(card => {
            card.classList.remove('has-conflict-critical', 'has-conflict-warning');
        });
        
        // ENSUITE: Ajouter les nouveaux badges et informations
        matches.forEach(match => {
            const card = document.querySelector(`[data-match-id="${match.match_id}"]`);
            if (!card) return;
            
            const conflicts = this.conflictDetector.getConflictsForMatch(match.match_id);
            
            if (conflicts.length > 0) {
                const hasCritical = conflicts.some(c => c.severity === 'critical');
                const severity = hasCritical ? 'critical' : 'warning';
                
                // Ajouter bordure colorée
                card.classList.add(`has-conflict-${severity}`);
                
                // Créer et ajouter le badge (avec position absolute pour ne pas affecter le layout)
                const badge = document.createElement('div');
                badge.className = `conflict-badge ${severity}`;
                badge.textContent = conflicts.length;

                // Ajouter les événements de survol pour le tooltip
                let tooltipTimeout;
                badge.addEventListener('mouseenter', (e) => {
                    clearTimeout(tooltipTimeout);
                    tooltipTimeout = setTimeout(() => this.showConflictTooltip(e, conflicts), 300);
                });
                badge.addEventListener('mouseleave', () => {
                    clearTimeout(tooltipTimeout);
                    tooltipTimeout = setTimeout(() => this.hideConflictTooltip(), 200);
                });

                // S'assurer que la carte est positioned pour que le badge soit positionné correctement
                const cardPosition = window.getComputedStyle(card).position;
                if (cardPosition === 'static') {
                    card.style.position = 'relative';
                }

                // Insérer au début pour éviter de changer l'ordre des éléments visibles
                card.insertBefore(badge, card.firstChild);
            }
        });
    }

    /**
     * Affiche un tooltip avec les détails des conflits
     */
    showConflictTooltip(event, conflicts) {
        // Supprimer tout tooltip existant
        this.hideConflictTooltip();

        // Créer le tooltip
        const tooltip = document.createElement('div');
        tooltip.className = 'conflict-tooltip';
        tooltip.id = 'conflict-tooltip';

        // Trier par sévérité (critical d'abord)
        const sortedConflicts = [...conflicts].sort((a, b) => {
            if (a.severity === 'critical' && b.severity !== 'critical') return -1;
            if (a.severity !== 'critical' && b.severity === 'critical') return 1;
            return 0;
        });

        const conflictTypeLabels = {
            'double_booking': '🏟️ Surcharge de gymnase',
            'team_overlap': '👥 Équipe joue 2 fois simultanément',
            'rest_time': '⏰ Temps de repos insuffisant',
            'time_preference': '🕐 Horaire avant préférences',
            'venue_constraint': '🏢 Gymnase interdit'
        };

        // Créer le contenu des conflits
        const conflictsHtml = sortedConflicts.map(c => `
            <div class="conflict-tooltip-item ${c.severity}">
                <div class="conflict-type">${conflictTypeLabels[c.type] || c.type}</div>
                <div class="conflict-message">${c.message}</div>
            </div>
        `).join('');

        tooltip.innerHTML = `
            <div class="conflict-tooltip-title">
                <span class="conflict-icon">${conflicts.some(c => c.severity === 'critical') ? '🔴' : '⚠️'}</span>
                <span>${conflicts.length} conflit${conflicts.length > 1 ? 's' : ''}</span>
            </div>
            <div class="conflict-tooltip-list">
                ${conflictsHtml}
            </div>
        `;

        // Positionner le tooltip près du curseur
        document.body.appendChild(tooltip);

        // Calculer la position optimale
        const rect = tooltip.getBoundingClientRect();
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;

        let left = event.pageX + 10;
        let top = event.pageY + 10;

        // Ajuster si le tooltip dépasse à droite
        if (left + rect.width > viewportWidth) {
            left = event.pageX - rect.width - 10;
        }

        // Ajuster si le tooltip dépasse en bas
        if (top + rect.height > viewportHeight) {
            top = event.pageY - rect.height - 10;
        }

        // S'assurer que le tooltip reste dans les limites
        left = Math.max(10, Math.min(left, viewportWidth - rect.width - 10));
        top = Math.max(10, Math.min(top, viewportHeight - rect.height - 10));

        tooltip.style.left = left + 'px';
        tooltip.style.top = top + 'px';
        tooltip.style.opacity = '1';
    }

    /**
     * Masque le tooltip des conflits
     */
    hideConflictTooltip() {
        const tooltip = document.getElementById('conflict-tooltip');
        if (tooltip) {
            tooltip.remove();
        }
    }
}

/**
 * History Panel UI - Interface pour l'historique
 */

class HistoryPanel {
    constructor(historyManager) {
        this.historyManager = historyManager;
        this.panel = null;
        this.isVisible = false;
        this.createPanel();
        
        // Écouter les changements d'historique
        this.historyManager.addListener((state) => this.updateButtons(state));
    }

    /**
     * Crée le panel HTML
     */
    createPanel() {
        this.panel = document.createElement('div');
        this.panel.className = 'history-panel';
        this.panel.innerHTML = `
            <div class="history-panel-header">
                <div class="history-panel-title">
                    <span>📜</span>
                    <span>Historique</span>
                </div>
                <div class="history-controls">
                    <button class="history-btn undo" onclick="window.historyPanel.undo()">
                        <span>↶</span>
                        <span>Annuler</span>
                    </button>
                    <button class="history-btn redo" onclick="window.historyPanel.redo()">
                        <span>↷</span>
                        <span>Refaire</span>
                    </button>
                </div>
                <button class="conflict-panel-close" onclick="window.historyPanel.hide()">×</button>
            </div>
            <div class="history-panel-body">
                <div class="history-list"></div>
            </div>
        `;
        document.body.appendChild(this.panel);
        this.updateHistory();
    }

    /**
     * Met à jour l'affichage de l'historique
     */
    updateHistory() {
        const history = this.historyManager.getHistory();
        const list = this.panel.querySelector('.history-list');
        
        if (history.undo.length === 0) {
            list.innerHTML = `
                <div class="history-empty">
                    <div class="history-empty-icon">📝</div>
                    <div>Aucune action enregistrée</div>
                </div>
            `;
            return;
        }
        
        const recentActions = this.historyManager.getRecentActions(20);
        list.innerHTML = recentActions.map(action => `
            <div class="history-item" onclick="window.historyPanel.revertTo('${action.id}')">
                <div class="history-item-header">
                    <span class="history-item-time">${action.time}</span>
                    <span class="history-item-type">${action.type}</span>
                </div>
                <div class="history-item-description">${action.description}</div>
            </div>
        `).join('');
    }

    /**
     * Met à jour l'état des boutons
     */
    updateButtons(state) {
        const undoBtn = this.panel.querySelector('.history-btn.undo');
        const redoBtn = this.panel.querySelector('.history-btn.redo');
        
        undoBtn.disabled = !state.canUndo;
        redoBtn.disabled = !state.canRedo;
        
        this.updateHistory();
    }

    /**
     * Annule la dernière action
     */
    undo() {
        const action = this.historyManager.undo();
        if (action) {
            this.handleUndo(action);
        }
    }

    /**
     * Refait la dernière action annulée
     */
    redo() {
        const action = this.historyManager.redo();
        if (action) {
            this.handleRedo(action);
        }
    }

    /**
     * Gère l'annulation d'une action
     */
    handleUndo(action) {
        if (action.type === 'move' && window.editModal) {
            // Restaurer l'ancienne position
            const modification = {
                match_id: action.data.matchId,
                original: action.data.to,
                new: action.data.from
            };
            window.editModal.saveModification(modification);
            
            if (window.app && window.app.reloadAndRender) {
                setTimeout(() => window.app.reloadAndRender(), 100);
            }
        }
    }

    /**
     * Gère la réexécution d'une action
     */
    handleRedo(action) {
        if (action.type === 'move' && window.editModal) {
            const modification = {
                match_id: action.data.matchId,
                original: action.data.from,
                new: action.data.to
            };
            window.editModal.saveModification(modification);
            
            if (window.app && window.app.reloadAndRender) {
                setTimeout(() => window.app.reloadAndRender(), 100);
            }
        }
    }

    /**
     * Revient à un point spécifique
     */
    revertTo(actionId) {
        const actions = this.historyManager.revertToAction(actionId);
        if (actions && actions.length > 0) {
            actions.forEach(action => this.handleUndo(action));
        }
    }

    /**
     * Affiche le panel
     */
    show() {
        this.panel.classList.add('show');
        this.isVisible = true;
    }

    /**
     * Cache le panel
     */
    hide() {
        this.panel.classList.remove('show');
        this.isVisible = false;
    }

    /**
     * Toggle le panel
     */
    toggle() {
        if (this.isVisible) {
            this.hide();
        } else {
            this.show();
        }
    }
}

/**
 * Resolver Panel UI - Interface pour les suggestions
 */

class ResolverPanel {
    constructor(autoResolver) {
        this.autoResolver = autoResolver;
        this.panel = null;
        this.isVisible = false;
        this.createPanel();
    }

    /**
     * Crée le panel HTML
     */
    createPanel() {
        this.panel = document.createElement('div');
        this.panel.className = 'resolver-panel';
        this.panel.innerHTML = `
            <div class="resolver-panel-header">
                <div class="resolver-panel-title">
                    <span>🤖</span>
                    <span>Suggestions Auto</span>
                </div>
                <button class="conflict-panel-close" onclick="window.resolverPanel.hide()">×</button>
            </div>
            <div class="resolver-panel-body">
                <div class="suggestion-list"></div>
            </div>
        `;
        document.body.appendChild(this.panel);
    }

    /**
     * Met à jour les suggestions
     */
    update(matches, availableSlots) {
        const suggestions = this.autoResolver.generateSuggestions(matches, availableSlots);
        const list = this.panel.querySelector('.suggestion-list');
        
        if (suggestions.length === 0) {
            list.innerHTML = `
                <div class="resolver-empty">
                    <div class="resolver-empty-icon">✨</div>
                    <div>Aucune suggestion disponible</div>
                </div>
            `;
            return;
        }
        
        const topSuggestions = this.autoResolver.getTopSuggestions(10);
        list.innerHTML = topSuggestions.map((sug, idx) => `
            <div class="suggestion-item">
                <div class="suggestion-header">
                    <span class="suggestion-type ${sug.type}">${sug.type}</span>
                    <span class="suggestion-priority ${sug.priority > 150 ? 'high' : ''}">
                        Score: ${sug.priority}
                    </span>
                </div>
                <div class="suggestion-description">${sug.description}</div>
                <div class="suggestion-actions">
                    <button class="suggestion-btn preview" onclick="window.resolverPanel.previewSuggestion(${idx})">
                        👁️ Prévisualiser
                    </button>
                    <button class="suggestion-btn apply" onclick="window.resolverPanel.applySuggestion(${idx})">
                        ✓ Appliquer
                    </button>
                </div>
            </div>
        `).join('');
    }

    /**
     * Prévisualise une suggestion
     */
    previewSuggestion(index) {
        const suggestions = this.autoResolver.getTopSuggestions();
        const suggestion = suggestions[index];
        
        if (!suggestion) return;
        
        // Highlight les matchs concernés
        const { action } = suggestion;
        if (action.type === 'move') {
            const card = document.querySelector(`[data-match-id="${action.matchId}"]`);
            if (card) {
                card.scrollIntoView({ behavior: 'smooth', block: 'center' });
                card.style.animation = 'highlight-flash 1s ease-in-out';
            }
        }
        
        console.log('👁️ Prévisualisation:', suggestion);
    }

    /**
     * Applique une suggestion
     */
    applySuggestion(index) {
        const suggestions = this.autoResolver.getTopSuggestions();
        const suggestion = suggestions[index];
        
        if (!suggestion || !window.matchsData) return;
        
        const success = this.autoResolver.applySuggestion(suggestion, window.matchsData);
        
        if (success) {
            // Enregistrer dans l'historique
            if (window.historyManager) {
                window.historyManager.pushAction({
                    type: suggestion.type,
                    description: suggestion.description,
                    data: suggestion.action
                });
            }
            
            // Recharger et re-détecter
            if (window.app && window.app.reloadAndRender) {
                window.app.reloadAndRender();
            }
            
            // Mettre à jour les conflits et suggestions
            setTimeout(() => {
                if (window.conflictPanel) {
                    window.conflictPanel.update(window.matchsData);
                }
                this.update(window.matchsData, window.availableSlots || []);
            }, 200);
            
            console.log('✅ Suggestion appliquée');
        }
    }

    /**
     * Affiche le panel
     */
    show() {
        this.panel.classList.add('show');
        this.isVisible = true;
    }

    /**
     * Cache le panel
     */
    hide() {
        this.panel.classList.remove('show');
        this.isVisible = false;
    }

    /**
     * Toggle le panel
     */
    toggle() {
        if (this.isVisible) {
            this.hide();
        } else {
            this.show();
        }
    }
}

// Animation CSS à ajouter
const style = document.createElement('style');
style.textContent = `
    @keyframes highlight-flash {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.05); box-shadow: 0 0 30px rgba(59, 130, 246, 0.6); }
    }
`;
document.head.appendChild(style);
