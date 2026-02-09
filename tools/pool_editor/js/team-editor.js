/**
 * PyCalendar Pool Editor - Team Editor
 * Modal for adding/editing teams
 */

class TeamEditor {
    constructor() {
        this.modal = null;
        this.currentTeam = null;
    }
    
    /**
     * Initialize team editor
     */
    init() {
        this.modal = document.getElementById('modal-team');
        this.setupEventListeners();
    }
    
    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Save button
        document.getElementById('btn-save-team')?.addEventListener('click', () => {
            this.save();
        });
        
        // Delete button
        document.getElementById('btn-delete-team')?.addEventListener('click', () => {
            if (this.currentTeam) {
                this.confirmDelete(this.currentTeam);
            }
        });
        
        // Form submit
        document.getElementById('team-form')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.save();
        });
    }
    
    /**
     * Open modal for new or existing team
     */
    openModal(team = null) {
        // Ensure modal is initialized
        if (!this.modal) {
            this.modal = document.getElementById('modal-team');
        }
        
        if (!this.modal) {
            console.error('Team editor modal not found');
            Utils.showToast('Erreur: modal non trouvée', 'error');
            return;
        }
        
        this.currentTeam = team;
        
        // Update title
        const title = document.getElementById('team-modal-title');
        if (title) title.textContent = team ? '✏️ Modifier l\'équipe' : '➕ Nouvelle équipe';
        
        // Show/hide delete button
        const deleteBtn = document.getElementById('btn-delete-team');
        if (deleteBtn) deleteBtn.style.display = team ? 'block' : 'none';
        
        // Populate pool dropdown
        this.populatePoolDropdown();
        
        // Populate gymnases checkboxes
        this.populateGymnasesCheckboxes();
        
        // Fill form
        if (team) {
            const setVal = (id, val) => {
                const el = document.getElementById(id);
                if (el) el.value = val;
            };
            setVal('team-id', team.id);
            setVal('team-name', team.nom || '');
            setVal('team-gender', team.genre || '');
            setVal('team-level', team.niveau || '');
            setVal('team-institution', team.institution || '');
            setVal('team-time', team.horaire || '');
            setVal('team-pool', team.poule || '');
            
            // Fill horaire aménagé fields
            const hasAmenage = team.horaireAmenage && team.gymnasesAmenages && team.gymnasesAmenages.length > 0;
            const checkboxAmenage = document.getElementById('team-has-amenage');
            const amenageDetails = document.getElementById('amenage-details');
            
            if (checkboxAmenage) {
                checkboxAmenage.checked = hasAmenage;
            }
            if (amenageDetails) {
                amenageDetails.style.display = hasAmenage ? 'block' : 'none';
            }
            
            setVal('team-horaire-amenage', team.horaireAmenage || '');
            
            // Check the gymnases
            if (team.gymnasesAmenages) {
                team.gymnasesAmenages.forEach(gym => {
                    const checkbox = document.querySelector(`#gymnases-list input[value="${gym}"]`);
                    if (checkbox) checkbox.checked = true;
                });
            }
        } else {
            const form = document.getElementById('team-form');
            if (form) form.reset();
            const idEl = document.getElementById('team-id');
            if (idEl) idEl.value = '';
            
            // Reset horaire aménagé
            const checkboxAmenage = document.getElementById('team-has-amenage');
            const amenageDetails = document.getElementById('amenage-details');
            if (checkboxAmenage) checkboxAmenage.checked = false;
            if (amenageDetails) amenageDetails.style.display = 'none';
        }
        
        // Setup toggle for horaire aménagé checkbox
        this.setupAmenageToggle();
        
        // Show modal
        this.modal.classList.add('active');
        
        // Focus first field
        const nameEl = document.getElementById('team-name');
        if (nameEl) nameEl.focus();
    }
    
    /**
     * Setup toggle for horaire aménagé section
     */
    setupAmenageToggle() {
        const checkbox = document.getElementById('team-has-amenage');
        const details = document.getElementById('amenage-details');
        
        if (checkbox && details) {
            // Remove old listener
            const newCheckbox = checkbox.cloneNode(true);
            checkbox.parentNode.replaceChild(newCheckbox, checkbox);
            
            newCheckbox.addEventListener('change', () => {
                details.style.display = newCheckbox.checked ? 'block' : 'none';
                
                // Si activé et pas d'équipe existante, sélectionner BESSON par défaut
                if (newCheckbox.checked && !this.currentTeam?.horaireAmenage) {
                    this.selectDefaultGymnase();
                }
            });
        }
    }
    
    /**
     * Sélectionne BESSON par défaut si disponible
     */
    selectDefaultGymnase() {
        // Chercher la checkbox BESSON et la cocher par défaut
        const bessonCheckbox = document.querySelector('#gymnases-list input[value="BESSON"]');
        if (bessonCheckbox) {
            bessonCheckbox.checked = true;
        } else {
            // Sinon, chercher une checkbox contenant "BESSON"
            const checkboxes = document.querySelectorAll('#gymnases-list input[type="checkbox"]');
            for (const cb of checkboxes) {
                if (cb.value.toUpperCase().includes('BESSON')) {
                    cb.checked = true;
                    break;
                }
            }
        }
    }
    
    /**
     * Populate gymnases checkboxes
     */
    populateGymnasesCheckboxes() {
        const container = document.getElementById('gymnases-list');
        if (!container) return;
        
        const gymnases = dataManager.getGymnases();
        
        if (gymnases.length === 0) {
            container.innerHTML = '<p class="empty-message">Chargez d\'abord un fichier Excel pour voir les gymnases</p>';
            return;
        }
        
        container.innerHTML = '';
        
        gymnases.forEach(gym => {
            const item = document.createElement('div');
            item.className = 'gymnase-checkbox-item';
            item.innerHTML = `
                <input type="checkbox" id="gym-${gym.nom}" name="gymnases" value="${gym.nom}">
                <label for="gym-${gym.nom}">${gym.nom}</label>
            `;
            container.appendChild(item);
        });
    }
    
    /**
     * Close modal
     */
    closeModal() {
        if (this.modal) {
            this.modal.classList.remove('active');
        }
        this.currentTeam = null;
    }
    
    /**
     * Populate pool dropdown based on current form values
     */
    populatePoolDropdown() {
        const select = document.getElementById('team-pool');
        
        // Clear options
        select.innerHTML = '<option value="">-- Non assignée --</option>';
        
        // Get pools
        const pools = dataManager.getPools();
        
        // Group by gender
        const grouped = { 'F': [], 'M': [] };
        pools.forEach(pool => {
            if (grouped[pool.gender]) {
                grouped[pool.gender].push(pool);
            }
        });
        
        // Add options
        ['F', 'M'].forEach(gender => {
            if (grouped[gender].length === 0) return;
            
            const optgroup = document.createElement('optgroup');
            optgroup.label = gender === 'F' ? 'Féminines' : 'Masculines';
            
            Utils.sortPools(grouped[gender]).forEach(pool => {
                const option = document.createElement('option');
                option.value = pool.id;
                option.textContent = `${pool.name} (${pool.level})`;
                optgroup.appendChild(option);
            });
            
            select.appendChild(optgroup);
        });
    }
    
    /**
     * Save team
     */
    save() {
        // Get form data
        const teamId = document.getElementById('team-id').value;
        const teamData = {
            nom: document.getElementById('team-name').value.trim(),
            genre: document.getElementById('team-gender').value,
            niveau: document.getElementById('team-level').value,
            institution: document.getElementById('team-institution').value.trim(),
            horaire: document.getElementById('team-time').value,
            poule: document.getElementById('team-pool').value || null
        };
        
        // Get horaire aménagé data
        const hasAmenage = document.getElementById('team-has-amenage')?.checked;
        if (hasAmenage) {
            const horaireAmenage = document.getElementById('team-horaire-amenage')?.value;
            const gymnasesCheckboxes = document.querySelectorAll('#gymnases-list input[type="checkbox"]:checked');
            const gymnasesAmenages = Array.from(gymnasesCheckboxes).map(cb => cb.value);
            
            // Validation: horaire et gymnase sont obligatoires si l'option est activée
            if (!horaireAmenage) {
                Utils.showToast('Veuillez sélectionner l\'horaire aménagé', 'error');
                return;
            }
            if (gymnasesAmenages.length === 0) {
                Utils.showToast('Veuillez sélectionner au moins un gymnase', 'error');
                return;
            }
            
            teamData.horaireAmenage = horaireAmenage;
            teamData.gymnasesAmenages = gymnasesAmenages;
        } else {
            // Clear horaire aménagé if unchecked
            teamData.horaireAmenage = null;
            teamData.gymnasesAmenages = [];
        }
        
        // Validate
        const validation = Utils.validateTeam(teamData);
        if (!validation.valid) {
            Utils.showToast(validation.errors[0], 'error');
            return;
        }
        
        // Check pool compatibility
        if (teamData.poule) {
            const pool = dataManager.getPool(teamData.poule);
            if (pool && (pool.gender !== teamData.genre || pool.level !== teamData.niveau)) {
                Utils.showToast('La poule sélectionnée n\'est pas compatible avec le genre/niveau', 'error');
                return;
            }
        }
        
        if (teamId) {
            // Update existing team
            const oldData = Utils.deepClone(dataManager.getTeam(teamId));
            
            // Check if there are actual changes
            const hasChanges = Utils.hasRealChanges(oldData, teamData);
            
            if (!hasChanges) {
                this.closeModal();
                Utils.showToast('Aucune modification', 'info');
                return;
            }
            
            const action = {
                type: 'editTeam',
                teamName: teamData.nom,
                teamId,
                oldData,
                newData: Utils.deepClone(teamData),
                undo: () => {
                    // updateTeam now handles pool changes internally
                    dataManager.updateTeam(teamId, oldData);
                },
                redo: () => {
                    dataManager.updateTeam(teamId, action.newData);
                }
            };
            
            // updateTeam now handles pool changes internally
            dataManager.updateTeam(teamId, teamData);
            
            historyManager.addAction(action);
            Utils.showToast('Équipe modifiée', 'success');
        } else {
            // Add new team
            const team = dataManager.addTeam(teamData);
            
            const action = {
                type: 'addTeam',
                teamName: teamData.nom,
                teamId: team.id,
                undo: () => {
                    dataManager.deleteTeam(team.id);
                },
                redo: () => {
                    dataManager.addTeam({ ...teamData, id: team.id });
                }
            };
            
            historyManager.addAction(action);
            Utils.showToast('Équipe ajoutée', 'success');
        }
        
        this.closeModal();
        poolRenderer.render();
    }
    
    /**
     * Confirm delete
     */
    confirmDelete(team) {
        if (!confirm(`Supprimer l'équipe "${team.nom}" ?`)) {
            return;
        }
        
        const action = {
            type: 'deleteTeam',
            teamName: team.nom,
            teamId: team.id,
            teamData: Utils.deepClone(team),
            undo: () => {
                dataManager.addTeam(action.teamData);
            },
            redo: () => {
                dataManager.deleteTeam(team.id);
            }
        };
        
        dataManager.deleteTeam(team.id);
        historyManager.addAction(action);
        
        this.closeModal();
        poolRenderer.render();
        
        Utils.showToast(`Équipe "${team.nom}" supprimée`, 'success');
    }
}

// Create global instance
window.teamEditor = new TeamEditor();
