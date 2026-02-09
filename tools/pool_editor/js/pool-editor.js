/**
 * PyCalendar Pool Editor - Pool Editor
 * Modal for adding/editing pools
 */

class PoolEditor {
    constructor() {
        this.modal = null;
        this.currentPool = null;
    }
    
    /**
     * Initialize pool editor
     */
    init() {
        this.modal = document.getElementById('modal-pool');
        this.setupEventListeners();
    }
    
    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Save button
        document.getElementById('btn-save-pool')?.addEventListener('click', () => {
            this.save();
        });
        
        // Delete button
        document.getElementById('btn-delete-pool')?.addEventListener('click', () => {
            if (this.currentPool) {
                this.confirmDelete(this.currentPool);
            }
        });
        
        // Form change - update preview
        ['pool-gender', 'pool-level', 'pool-letter'].forEach(id => {
            document.getElementById(id)?.addEventListener('change', () => {
                this.updatePreview();
            });
        });
        
        // Form submit
        document.getElementById('pool-form')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.save();
        });
    }
    
    /**
     * Open modal for new or existing pool
     */
    openModal(pool = null, defaultGender = null, defaultLevel = null) {
        // Ensure modal is initialized
        if (!this.modal) {
            this.modal = document.getElementById('modal-pool');
        }
        
        if (!this.modal) {
            console.error('Pool editor modal not found');
            Utils.showToast('Erreur: modal non trouvée', 'error');
            return;
        }
        
        this.currentPool = pool;
        
        // Update title
        const title = document.getElementById('pool-modal-title');
        if (title) title.textContent = pool ? '✏️ Modifier la poule' : '➕ Nouvelle poule';
        
        // Show/hide delete button
        const deleteBtn = document.getElementById('btn-delete-pool');
        if (deleteBtn) deleteBtn.style.display = pool ? 'block' : 'none';
        
        // Disable gender/level/letter for existing pool (would change ID)
        const isEdit = !!pool;
        const genderEl = document.getElementById('pool-gender');
        const levelEl = document.getElementById('pool-level');
        const letterEl = document.getElementById('pool-letter');
        
        if (genderEl) genderEl.disabled = isEdit;
        if (levelEl) levelEl.disabled = isEdit;
        if (letterEl) letterEl.disabled = isEdit;
        
        // Fill form
        if (pool) {
            document.getElementById('pool-id').value = pool.id;
            if (genderEl) genderEl.value = pool.gender || '';
            if (levelEl) levelEl.value = pool.level || '';
            if (letterEl) letterEl.value = pool.letter || '';
            document.getElementById('pool-type').value = pool.type || 'classique';
        } else {
            document.getElementById('pool-form')?.reset();
            document.getElementById('pool-id').value = '';
            
            // Set defaults
            if (defaultGender && genderEl) {
                genderEl.value = defaultGender;
            }
            if (defaultLevel && levelEl) {
                levelEl.value = defaultLevel;
            }
            
            // Auto-select next available letter
            this.selectNextAvailableLetter(defaultGender, defaultLevel);
        }
        
        // Update preview
        this.updatePreview();
        
        // Show modal
        this.modal.classList.add('active');
        
        // Focus first non-disabled field
        if (!isEdit && genderEl) {
            genderEl.focus();
        } else {
            document.getElementById('pool-type').focus();
        }
    }
    
    /**
     * Close modal
     */
    closeModal() {
        this.modal.classList.remove('active');
        this.currentPool = null;
    }
    
    /**
     * Select next available letter for new pool
     */
    selectNextAvailableLetter(gender, level) {
        if (!gender || !level) return;
        
        const existingPools = dataManager.getPools().filter(p => 
            p.gender === gender && p.level === level
        );
        
        const usedLetters = existingPools.map(p => p.letter);
        
        for (const letter of Utils.POOL_LETTERS) {
            if (!usedLetters.includes(letter)) {
                document.getElementById('pool-letter').value = letter;
                break;
            }
        }
        
        this.updatePreview();
    }
    
    /**
     * Update pool name preview
     */
    updatePreview() {
        const gender = document.getElementById('pool-gender').value;
        const level = document.getElementById('pool-level').value;
        const letter = document.getElementById('pool-letter').value;
        
        const preview = document.getElementById('pool-name-preview');
        
        if (gender && level && letter) {
            const name = Utils.generatePoolName(dataManager.settings.prefix, gender, level, letter);
            preview.textContent = name;
            preview.style.color = '';
        } else {
            preview.textContent = '--';
            preview.style.color = 'var(--color-text-muted)';
        }
    }
    
    /**
     * Save pool
     */
    save() {
        const poolId = document.getElementById('pool-id').value;
        const poolData = {
            gender: document.getElementById('pool-gender').value,
            level: document.getElementById('pool-level').value,
            letter: document.getElementById('pool-letter').value,
            type: document.getElementById('pool-type').value
        };
        
        // Validate
        const existingPools = poolId ? 
            dataManager.getPools().filter(p => p.id !== poolId) :
            dataManager.getPools();
        
        const validation = Utils.validatePool(poolData, existingPools);
        if (!validation.valid) {
            Utils.showToast(validation.errors[0], 'error');
            return;
        }
        
        if (poolId) {
            // Update existing pool (only type can change)
            const oldData = Utils.deepClone(dataManager.getPool(poolId));
            
            const action = {
                type: 'editPool',
                poolName: poolId,
                poolId,
                oldData,
                newData: poolData,
                undo: () => {
                    dataManager.updatePool(poolId, oldData);
                },
                redo: () => {
                    dataManager.updatePool(poolId, poolData);
                }
            };
            
            dataManager.updatePool(poolId, { type: poolData.type });
            historyManager.addAction(action);
            
            Utils.showToast('Poule modifiée', 'success');
        } else {
            // Add new pool
            try {
                const pool = dataManager.addPool(poolData);
                
                const action = {
                    type: 'addPool',
                    poolName: pool.id,
                    poolId: pool.id,
                    poolData,
                    undo: () => {
                        dataManager.deletePool(pool.id);
                    },
                    redo: () => {
                        dataManager.addPool(poolData);
                    }
                };
                
                historyManager.addAction(action);
                Utils.showToast('Poule créée', 'success');
            } catch (error) {
                Utils.showToast(error.message, 'error');
                return;
            }
        }
        
        this.closeModal();
        poolRenderer.render();
    }
    
    /**
     * Confirm delete pool
     */
    confirmDelete(pool) {
        const poolTeams = dataManager.getPoolTeams(pool.id);
        const teamCount = poolTeams.length;
        
        let message = `Supprimer la poule "${pool.name}" ?`;
        if (teamCount > 0) {
            message += `\n\n⚠️ ${teamCount} équipe(s) seront déplacées vers "Non assignées".`;
        }
        
        if (!confirm(message)) {
            return;
        }
        
        const deletedTeams = Utils.deepClone(poolTeams);
        const poolData = Utils.deepClone(pool);
        
        const action = {
            type: 'deletePool',
            poolName: pool.name,
            poolId: pool.id,
            poolData,
            deletedTeams,
            undo: () => {
                // Recreate pool
                dataManager.addPool(poolData);
                // Reassign teams
                deletedTeams.forEach(team => {
                    dataManager.moveTeam(team.id, pool.id);
                });
            },
            redo: () => {
                dataManager.deletePool(pool.id);
            }
        };
        
        dataManager.deletePool(pool.id);
        historyManager.addAction(action);
        
        this.closeModal();
        poolRenderer.render();
        
        Utils.showToast(`Poule "${pool.name}" supprimée`, 'success');
    }
}

// Create global instance
window.poolEditor = new PoolEditor();
