/**
 * PyCalendar Pool Editor - Drag & Drop
 * Handles drag and drop functionality for teams
 */

class DragDropManager {
    constructor() {
        this.draggedTeam = null;
        this.draggedElement = null;
        this.dropZones = [];
        this.isInitialized = false;
        
        // Level change hover state
        this.levelChangeTimer = null;
        this.levelChangeDelay = 1500; // 1.5 seconds to trigger level change
        this.currentHoverZone = null;
        this.levelChangeProgress = null;
    }
    
    /**
     * Initialize drag & drop
     */
    init() {
        if (this.isInitialized) return;
        
        // Global drag end handler
        document.addEventListener('dragend', () => this.handleDragEnd());
        
        // Touch support for mobile
        this.initTouchSupport();
        
        this.isInitialized = true;
        console.log('✅ Drag & Drop initialized');
    }
    
    /**
     * Initialize touch support for mobile devices
     */
    initTouchSupport() {
        let touchStartY = 0;
        let touchStartX = 0;
        let touchElement = null;
        
        document.addEventListener('touchstart', (e) => {
            const teamCard = e.target.closest('.team-card');
            if (teamCard) {
                touchStartX = e.touches[0].clientX;
                touchStartY = e.touches[0].clientY;
                touchElement = teamCard;
            }
        }, { passive: true });
        
        document.addEventListener('touchmove', (e) => {
            if (touchElement && touchElement.classList.contains('dragging')) {
                e.preventDefault();
            }
        }, { passive: false });
        
        document.addEventListener('touchend', () => {
            touchElement = null;
        });
    }
    
    /**
     * Make team card draggable
     */
    makeDraggable(element, team) {
        element.draggable = true;
        element.dataset.teamId = team.id;
        
        element.addEventListener('dragstart', (e) => this.handleDragStart(e, team));
        element.addEventListener('dragend', (e) => this.handleDragEnd(e));
        
        // Add grab cursor
        element.style.cursor = 'grab';
    }
    
    /**
     * Make element a drop zone
     */
    makeDropZone(element, targetPoolId, options = {}) {
        // Avoid duplicate listeners
        if (element.dataset.isDropZone) return;
        element.dataset.isDropZone = 'true';
        
        element.addEventListener('dragover', (e) => this.handleDragOver(e, element, targetPoolId, options));
        element.addEventListener('dragenter', (e) => this.handleDragEnter(e, element, targetPoolId, options));
        element.addEventListener('dragleave', (e) => this.handleDragLeave(e, element));
        element.addEventListener('drop', (e) => this.handleDrop(e, element, targetPoolId, options));
        
        this.dropZones.push({ element, targetPoolId, options });
    }
    
    /**
     * Handle drag start
     */
    handleDragStart(e, team) {
        this.draggedTeam = team;
        this.draggedElement = e.target;
        
        // Set drag data
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/plain', team.id);
        
        // Create custom drag image
        const dragImage = e.target.cloneNode(true);
        dragImage.style.position = 'absolute';
        dragImage.style.top = '-1000px';
        dragImage.style.opacity = '0.8';
        dragImage.style.transform = 'rotate(3deg)';
        document.body.appendChild(dragImage);
        e.dataTransfer.setDragImage(dragImage, 50, 25);
        setTimeout(() => dragImage.remove(), 0);
        
        // Add dragging class
        setTimeout(() => {
            if (this.draggedElement) {
                this.draggedElement.classList.add('dragging');
                this.draggedElement.style.cursor = 'grabbing';
            }
        }, 0);
        
        // Highlight valid drop zones
        this.highlightDropZones(team);
    }
    
    /**
     * Handle drag end
     */
    handleDragEnd(e) {
        if (this.draggedElement) {
            this.draggedElement.classList.remove('dragging');
            this.draggedElement.style.cursor = 'grab';
        }
        
        // Remove all highlights
        this.clearDropZoneHighlights();
        
        // Clear level change timer
        this.clearLevelChangeTimer();
        
        this.draggedTeam = null;
        this.draggedElement = null;
    }
    
    /**
     * Handle drag over
     */
    handleDragOver(e, element, targetPoolId, options) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        
        // Add visual feedback for position
        const rect = element.getBoundingClientRect();
        const y = e.clientY - rect.top;
        const height = rect.height;
        
        // Show insertion indicator
        if (y < height / 2) {
            element.classList.add('drop-top');
            element.classList.remove('drop-bottom');
        } else {
            element.classList.add('drop-bottom');
            element.classList.remove('drop-top');
        }
        
        // Check for level change timer (refresh check on dragover)
        if (this.draggedTeam && options) {
            this.checkForLevelChange(element, targetPoolId, options);
        }
    }
    
    /**
     * Handle drag enter
     */
    handleDragEnter(e, element, targetPoolId, options) {
        e.preventDefault();
        element.classList.add('drag-over');
        
        // Check if this is a different level zone for potential level change
        if (this.draggedTeam && options) {
            this.checkForLevelChange(element, targetPoolId, options);
        }
    }
    
    /**
     * Handle drag leave
     */
    handleDragLeave(e, element) {
        // Only remove if leaving the element entirely
        if (!element.contains(e.relatedTarget)) {
            element.classList.remove('drag-over', 'drop-top', 'drop-bottom', 'level-change-pending');
            
            // Clear level change timer if leaving the zone
            if (this.currentHoverZone === element) {
                this.clearLevelChangeTimer();
            }
        }
    }
    
    /**
     * Handle drop
     */
    handleDrop(e, element, targetPoolId, options) {
        e.preventDefault();
        e.stopPropagation();
        
        element.classList.remove('drag-over', 'drop-top', 'drop-bottom');
        
        // Clear any pending level change timer
        this.clearLevelChangeTimer();
        
        const teamId = e.dataTransfer.getData('text/plain');
        const team = dataManager.getTeam(teamId);
        
        if (!team) {
            console.warn('Team not found:', teamId);
            return;
        }
        
        // Check if dropping to unassigned zone
        if (options.isUnassigned) {
            // For unassigned zones, check if level change is needed
            if (options.level && options.level !== team.niveau && options.gender === team.genre) {
                // Level is different - prompt for level change
                this.promptLevelChangeForUnassigned(team, options.level, options.gender);
                return;
            }
            // Same level or no level specified - just set pool to null
            targetPoolId = null;
        } else if (targetPoolId) {
            // Check pool compatibility
            const pool = dataManager.getPool(targetPoolId);
            if (pool) {
                if (pool.gender !== team.genre) {
                    Utils.showToast(`Cette poule est pour ${pool.gender === 'F' ? 'féminines' : 'masculines'}`, 'warning');
                    return;
                }
                if (pool.level !== team.niveau) {
                    // Level is different - prompt for level change and add to pool
                    this.promptLevelChangeForPool(team, pool);
                    return;
                }
            }
        }
        
        const oldPoolId = team.poule;
        
        // Don't do anything if dropping to same pool
        if (oldPoolId === targetPoolId) {
            return;
        }
        
        // Record action for undo
        const action = {
            type: 'moveTeam',
            teamName: team.nom,
            teamId: team.id,
            oldPoolId,
            newPoolId: targetPoolId,
            undo: () => {
                dataManager.moveTeam(team.id, oldPoolId);
            },
            redo: () => {
                dataManager.moveTeam(team.id, targetPoolId);
            }
        };
        
        // Move team
        dataManager.moveTeam(team.id, targetPoolId);
        
        // Add to history
        historyManager.addAction(action);
        
        // Re-render
        poolRenderer.render();
        
        // Show feedback
        const oldName = oldPoolId || 'non assignées';
        const newName = targetPoolId || 'non assignées';
        Utils.showToast(`${team.nom}: ${oldName} → ${newName}`, 'success');
    }
    
    /**
     * Prompt for level change when dropping to unassigned zone
     */
    promptLevelChangeForUnassigned(team, newLevel, gender) {
        // IMPORTANT: Get fresh team data from dataManager to avoid stale references
        const freshTeam = dataManager.getTeam(team.id);
        if (!freshTeam) {
            console.error('Team not found:', team.id);
            return;
        }
        
        const confirmed = confirm(
            `Voulez-vous changer le niveau de "${freshTeam.nom}" ?\n\n` +
            `Niveau actuel : ${freshTeam.niveau}\n` +
            `Nouveau niveau : ${newLevel}\n\n` +
            `L'équipe sera également retirée de sa poule actuelle.`
        );
        
        if (confirmed) {
            const oldData = Utils.deepClone(freshTeam);
            const newData = {
                ...oldData,
                niveau: newLevel,
                poule: null
            };
            
            const action = {
                type: 'editTeam',
                teamName: freshTeam.nom,
                teamId: freshTeam.id,
                oldData,
                newData: Utils.deepClone(newData),
                description: `Changement de niveau: ${oldData.niveau} → ${newLevel}`,
                undo: () => {
                    dataManager.updateTeam(freshTeam.id, oldData);
                },
                redo: () => {
                    dataManager.updateTeam(freshTeam.id, newData);
                }
            };
            
            dataManager.updateTeam(freshTeam.id, newData);
            historyManager.addAction(action);
            
            Utils.showToast(`${freshTeam.nom}: niveau changé ${oldData.niveau} → ${newLevel}`, 'success');
            poolRenderer.render();
        }
    }
    
    /**
     * Prompt for level change when dropping to a pool with different level
     */
    promptLevelChangeForPool(team, pool) {
        // IMPORTANT: Get fresh team data from dataManager to avoid stale references
        const freshTeam = dataManager.getTeam(team.id);
        if (!freshTeam) {
            console.error('Team not found:', team.id);
            return;
        }
        
        const confirmed = confirm(
            `Voulez-vous changer le niveau de "${freshTeam.nom}" et l'ajouter à "${pool.name}" ?\n\n` +
            `Niveau actuel : ${freshTeam.niveau}\n` +
            `Nouveau niveau : ${pool.level}\n\n` +
            `L'équipe sera déplacée dans la poule ${pool.name}.`
        );
        
        if (confirmed) {
            const oldData = Utils.deepClone(freshTeam);
            const newData = {
                ...oldData,
                niveau: pool.level,
                poule: pool.id
            };
            
            const action = {
                type: 'editTeam',
                teamName: freshTeam.nom,
                teamId: freshTeam.id,
                oldData,
                newData: Utils.deepClone(newData),
                description: `Changement de niveau: ${oldData.niveau} → ${pool.level} + poule ${pool.name}`,
                undo: () => {
                    dataManager.updateTeam(freshTeam.id, oldData);
                },
                redo: () => {
                    dataManager.updateTeam(freshTeam.id, newData);
                }
            };
            
            dataManager.updateTeam(freshTeam.id, newData);
            historyManager.addAction(action);
            
            Utils.showToast(`${freshTeam.nom}: niveau changé ${oldData.niveau} → ${pool.level}, ajoutée à ${pool.name}`, 'success');
            poolRenderer.render();
        }
    }
    
    /**
     * Highlight valid drop zones
     * Zones where level change is possible are highlighted differently
     */
    highlightDropZones(team) {
        this.dropZones.forEach(({ element, targetPoolId, options }) => {
            let isValid = true;
            let isLevelChangePossible = false;
            
            if (options.isUnassigned) {
                // For unassigned zones, check gender and level
                const sameGender = !options.gender || team.genre === options.gender;
                const sameLevel = !options.level || team.niveau === options.level;
                
                if (sameGender && sameLevel) {
                    isValid = true;
                } else if (sameGender && !sameLevel) {
                    // Different level but same gender - level change is possible
                    isValid = true;
                    isLevelChangePossible = true;
                } else {
                    isValid = false;
                }
            } else if (targetPoolId) {
                const pool = dataManager.getPool(targetPoolId);
                if (pool) {
                    const sameGender = pool.gender === team.genre;
                    const sameLevel = pool.level === team.niveau;
                    
                    if (sameGender && sameLevel) {
                        isValid = pool.id !== team.poule;
                    } else if (sameGender && !sameLevel) {
                        // Different level but same gender - level change is possible
                        isValid = true;
                        isLevelChangePossible = true;
                    } else {
                        isValid = false;
                    }
                }
            }
            
            if (isValid) {
                if (isLevelChangePossible) {
                    element.classList.add('drop-zone-level-change');
                } else {
                    element.classList.add('drop-zone-active');
                }
            } else {
                element.classList.add('drop-zone-invalid');
            }
        });
    }
    
    /**
     * Clear drop zone highlights
     */
    clearDropZoneHighlights() {
        document.querySelectorAll('.drop-zone-active, .drop-zone-invalid, .drag-over, .drop-top, .drop-bottom, .drop-zone-level-change, .level-change-pending').forEach(el => {
            el.classList.remove('drop-zone-active', 'drop-zone-invalid', 'drag-over', 'drop-top', 'drop-bottom', 'drop-zone-level-change', 'level-change-pending');
        });
    }
    
    /**
     * Reset drop zones (called before re-render)
     */
    reset() {
        this.dropZones = [];
        this.clearDropZoneHighlights();
        this.clearLevelChangeTimer();
        
        // Remove drop zone markers from all elements
        document.querySelectorAll('[data-is-drop-zone]').forEach(el => {
            delete el.dataset.isDropZone;
        });
    }
    
    /**
     * Check if we should start a level change timer
     */
    checkForLevelChange(element, targetPoolId, options) {
        if (!this.draggedTeam) return;
        
        const team = this.draggedTeam;
        let targetLevel = null;
        let targetGender = team.genre;
        
        // Determine target level from options or pool
        if (options.isUnassigned) {
            targetLevel = options.level;
            if (options.gender) targetGender = options.gender;
        } else if (targetPoolId) {
            const pool = dataManager.getPool(targetPoolId);
            if (pool) {
                targetLevel = pool.level;
                targetGender = pool.gender;
            }
        }
        
        // Check if level is different (and gender is same - we don't auto-change gender)
        if (targetLevel && targetLevel !== team.niveau && targetGender === team.genre) {
            // Start timer if not already started for this zone
            if (this.currentHoverZone !== element) {
                this.startLevelChangeTimer(element, team, targetLevel, options);
            }
        } else {
            // Clear timer if hovering over compatible zone
            if (this.currentHoverZone === element) {
                this.clearLevelChangeTimer();
            }
        }
    }
    
    /**
     * Start level change timer
     */
    startLevelChangeTimer(element, team, newLevel, options) {
        this.clearLevelChangeTimer();
        
        this.currentHoverZone = element;
        element.classList.add('level-change-pending');
        
        // Show visual progress indicator
        this.showLevelChangeProgress(element, team, newLevel);
        
        this.levelChangeTimer = setTimeout(() => {
            this.confirmAndChangeLevelDrop(element, team, newLevel, options);
        }, this.levelChangeDelay);
    }
    
    /**
     * Clear level change timer
     */
    clearLevelChangeTimer() {
        if (this.levelChangeTimer) {
            clearTimeout(this.levelChangeTimer);
            this.levelChangeTimer = null;
        }
        
        if (this.currentHoverZone) {
            this.currentHoverZone.classList.remove('level-change-pending');
        }
        this.currentHoverZone = null;
        
        // Remove progress indicator
        this.hideLevelChangeProgress();
    }
    
    /**
     * Show level change progress indicator
     */
    showLevelChangeProgress(element, team, newLevel) {
        this.hideLevelChangeProgress();
        
        const progress = document.createElement('div');
        progress.className = 'level-change-progress';
        progress.innerHTML = `
            <div class="level-change-content">
                <div class="level-change-icon">⚠️</div>
                <div class="level-change-text">
                    <strong>Changer le niveau de ${team.nom}</strong>
                    <span>${team.niveau} → ${newLevel}</span>
                </div>
                <div class="level-change-bar">
                    <div class="level-change-bar-fill"></div>
                </div>
            </div>
        `;
        
        // Position near element
        const rect = element.getBoundingClientRect();
        progress.style.position = 'fixed';
        progress.style.left = `${rect.left}px`;
        progress.style.top = `${rect.top - 80}px`;
        progress.style.zIndex = '10000';
        
        document.body.appendChild(progress);
        this.levelChangeProgress = progress;
        
        // Animate the bar
        setTimeout(() => {
            const bar = progress.querySelector('.level-change-bar-fill');
            if (bar) {
                bar.style.width = '100%';
                bar.style.transition = `width ${this.levelChangeDelay}ms linear`;
            }
        }, 10);
    }
    
    /**
     * Hide level change progress indicator
     */
    hideLevelChangeProgress() {
        if (this.levelChangeProgress) {
            this.levelChangeProgress.remove();
            this.levelChangeProgress = null;
        }
    }
    
    /**
     * Confirm and execute level change with drop
     */
    confirmAndChangeLevelDrop(element, team, newLevel, options) {
        this.hideLevelChangeProgress();
        element.classList.remove('level-change-pending');
        
        // IMPORTANT: Get fresh team data from dataManager to avoid stale references
        const freshTeam = dataManager.getTeam(team.id);
        if (!freshTeam) {
            console.error('Team not found:', team.id);
            this.clearLevelChangeTimer();
            return;
        }
        
        // Show confirmation dialog
        const confirmed = confirm(
            `Voulez-vous changer le niveau de "${freshTeam.nom}" ?\n\n` +
            `Niveau actuel : ${freshTeam.niveau}\n` +
            `Nouveau niveau : ${newLevel}\n\n` +
            `L'équipe sera également retirée de sa poule actuelle.`
        );
        
        if (confirmed) {
            const oldData = Utils.deepClone(freshTeam);
            const newData = {
                ...oldData,
                niveau: newLevel,
                poule: null // Remove from current pool
            };
            
            const action = {
                type: 'editTeam',
                teamName: freshTeam.nom,
                teamId: freshTeam.id,
                oldData,
                newData,
                description: `Changement de niveau: ${oldData.niveau} → ${newLevel}`,
                undo: () => {
                    dataManager.updateTeam(freshTeam.id, oldData);
                },
                redo: () => {
                    dataManager.updateTeam(freshTeam.id, newData);
                }
            };
            
            // Apply the change
            dataManager.updateTeam(freshTeam.id, newData);
            historyManager.addAction(action);
            
            Utils.showToast(`${freshTeam.nom}: niveau changé ${oldData.niveau} → ${newLevel}`, 'success');
            
            // Re-render
            poolRenderer.render();
        }
        
        this.clearLevelChangeTimer();
    }
}

// Create global instance
window.dragDropManager = new DragDropManager();
