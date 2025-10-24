/**
 * edit-modal.js - Modal d'édition de match
 * 
 * Permet d'éditer les propriétés d'un match (semaine, horaire, gymnase).
 * Détecte les conflits et propose des solutions.
 * Exposé globalement via window.EditModal
 */

window.EditModal = class EditModal {
    constructor(dataManager, modificationManager) {
        this.dataManager = dataManager;
        this.modificationManager = modificationManager;
        this.currentMatch = null;
        this.modal = null;
        
        this.createModal();
        this.attachEventListeners();
    }
    
    /**
     * Crée le HTML du modal
     */
    createModal() {
        const modal = document.createElement('div');
        modal.id = 'edit-modal';
        modal.className = 'modal-overlay hidden';
        
        modal.innerHTML = `
            <div class="modal modal-lg">
                <div class="modal-header">
                    <h2 class="modal-title">✏️ Éditer le Match</h2>
                    <button class="modal-close" id="edit-modal-close">×</button>
                </div>
                
                <div class="modal-body">
                    <!-- Info du match -->
                    <div class="match-info-section">
                        <div class="match-teams-display">
                            <span class="team-name" id="edit-team1">-</span>
                            <span class="vs">VS</span>
                            <span class="team-name" id="edit-team2">-</span>
                        </div>
                        <div class="match-meta">
                            <span class="badge" id="edit-pool">-</span>
                            <span class="badge" id="edit-gender">-</span>
                        </div>
                    </div>
                    
                    <!-- Formulaire d'édition -->
                    <form id="edit-form" class="edit-form">
                        <div class="form-row">
                            <div class="filter-group">
                                <label class="filter-label" for="edit-week">Semaine</label>
                                <input type="number" 
                                       class="filter-input" 
                                       id="edit-week" 
                                       min="1" 
                                       max="52" 
                                       required>
                            </div>
                            
                            <div class="filter-group">
                                <label class="filter-label" for="edit-time">Horaire</label>
                                <select class="filter-select" id="edit-time" required>
                                    <option value="">-- Choisir --</option>
                                </select>
                            </div>
                        </div>
                        
                        <div class="filter-group">
                            <label class="filter-label" for="edit-venue">Gymnase</label>
                            <select class="filter-select" id="edit-venue" required>
                                <option value="">-- Choisir --</option>
                            </select>
                        </div>
                        
                        <!-- Alertes de conflit -->
                        <div class="alert alert-warning hidden" id="edit-conflict-alert">
                            <strong>⚠️ Conflit détecté !</strong>
                            <p id="edit-conflict-message"></p>
                        </div>
                        
                        <!-- Valeurs originales -->
                        <div class="original-values-section">
                            <h4>📋 Valeurs actuelles</h4>
                            <div id="edit-original-values" class="original-values"></div>
                        </div>
                    </form>
                </div>
                
                <div class="modal-footer">
                    <button class="modal-btn modal-btn-danger" id="edit-unschedule">
                        🗑️ Déplanifier
                    </button>
                    <div style="flex: 1;"></div>
                    <button class="modal-btn modal-btn-secondary" id="edit-cancel">
                        Annuler
                    </button>
                    <button class="modal-btn modal-btn-primary" id="edit-save">
                        💾 Enregistrer
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        this.modal = modal;
    }
    
    /**
     * Attache les événements
     */
    attachEventListeners() {
        // Boutons
        document.getElementById('edit-modal-close').addEventListener('click', () => this.close());
        document.getElementById('edit-cancel').addEventListener('click', () => this.close());
        document.getElementById('edit-save').addEventListener('click', () => this.save());
        document.getElementById('edit-unschedule').addEventListener('click', () => this.unschedule());
        
        // Fermeture par clic sur overlay
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.close();
            }
        });
        
        // Validation en temps réel
        document.getElementById('edit-week').addEventListener('input', () => this.validateForm());
        document.getElementById('edit-time').addEventListener('change', () => this.validateForm());
        document.getElementById('edit-venue').addEventListener('change', () => this.validateForm());
        
        // Écouter les demandes d'édition
        document.addEventListener('match-edit-requested', (e) => {
            this.open(e.detail.match);
        });
        
        // ESC pour fermer
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !this.modal.classList.contains('hidden')) {
                this.close();
            }
        });
    }
    
    /**
     * Ouvre le modal pour un match
     */
    open(match) {
        this.currentMatch = match;
        
        // Remplir les infos
        const data = this.dataManager.getData();
        const equipe1 = data.entities.equipes.find(e => e.id === match.equipes[0]);
        const equipe2 = data.entities.equipes.find(e => e.id === match.equipes[1]);
        const poule = data.entities.poules.find(p => p.id === equipe1?.poule);
        
        document.getElementById('edit-team1').textContent = equipe1?.nom || '-';
        document.getElementById('edit-team2').textContent = equipe2?.nom || '-';
        document.getElementById('edit-pool').textContent = poule?.nom || '-';
        document.getElementById('edit-gender').textContent = window.Formatters.formatGender(equipe1?.genre);
        
        // Remplir les valeurs actuelles
        this._populateForm(match, data);
        
        // Afficher les valeurs originales
        this._showOriginalValues(match);
        
        // Afficher le modal
        this.modal.classList.remove('hidden');
    }
    
    /**
     * Remplit le formulaire
     */
    _populateForm(match, data) {
        // Semaine
        document.getElementById('edit-week').value = match.semaine || '';
        
        // Horaires disponibles
        const timeSelect = document.getElementById('edit-time');
        timeSelect.innerHTML = '<option value="">-- Choisir --</option>';
        
        const times = this._getAvailableTimes(data);
        times.forEach(time => {
            const option = document.createElement('option');
            option.value = time;
            option.textContent = window.Formatters.formatTime(time);
            if (time === match.horaire) {
                option.selected = true;
            }
            timeSelect.appendChild(option);
        });
        
        // Gymnases disponibles
        const venueSelect = document.getElementById('edit-venue');
        venueSelect.innerHTML = '<option value="">-- Choisir --</option>';
        
        data.entities.gymnases.forEach(venue => {
            const option = document.createElement('option');
            option.value = venue.id;
            option.textContent = `${venue.nom} (${venue.capacite} places)`;
            if (venue.id === match.gymnase) {
                option.selected = true;
            }
            venueSelect.appendChild(option);
        });
    }
    
    /**
     * Affiche les valeurs originales
     */
    _showOriginalValues(match) {
        const data = this.dataManager.getData();
        const venue = data.entities.gymnases.find(v => v.id === match.gymnase);
        
        const html = `
            <div class="original-value-item">
                <span class="label">Semaine:</span>
                <span class="value">${window.Formatters.formatWeek(match.semaine)}</span>
            </div>
            <div class="original-value-item">
                <span class="label">Horaire:</span>
                <span class="value">${window.Formatters.formatTime(match.horaire)}</span>
            </div>
            <div class="original-value-item">
                <span class="label">Gymnase:</span>
                <span class="value">${venue?.nom || '-'}</span>
            </div>
        `;
        
        document.getElementById('edit-original-values').innerHTML = html;
    }
    
    /**
     * Extrait les horaires disponibles
     */
    _getAvailableTimes(data) {
        const times = new Set();
        
        // Tous les horaires utilisés
        data.matches.scheduled.forEach(m => {
            if (m.horaire) times.add(m.horaire);
        });
        
        // Horaires standards si peu de données
        if (times.size < 5) {
            ['08:00', '10:00', '12:00', '14:00', '16:00', '18:00', '20:00'].forEach(t => times.add(t));
        }
        
        return Array.from(times).sort();
    }
    
    /**
     * Valide le formulaire
     */
    validateForm() {
        const semaine = parseInt(document.getElementById('edit-week').value);
        const horaire = document.getElementById('edit-time').value;
        const gymnase = document.getElementById('edit-venue').value;
        
        if (!semaine || !horaire || !gymnase) {
            this._hideConflictAlert();
            return false;
        }
        
        const newSlot = { semaine, horaire, gymnase };
        
        // Validation du slot
        const validation = window.Validators.validateSlot(newSlot);
        if (!validation.valid) {
            this._showConflictAlert('Créneau invalide: ' + validation.errors.join(', '));
            return false;
        }
        
        // Vérifier disponibilité du créneau
        const data = this.dataManager.getData();
        if (!window.Validators.isSlotAvailable(newSlot, data.matches.scheduled, this.currentMatch.match_id)) {
            this._showConflictAlert('Ce créneau est déjà occupé par un autre match.');
            return false;
        }
        
        // Vérifier conflits d'équipes
        const equipe1Conflict = window.Validators.hasTeamConflict(
            this.currentMatch.equipes[0], 
            newSlot, 
            data.matches.scheduled,
            this.currentMatch.match_id
        );
        
        const equipe2Conflict = window.Validators.hasTeamConflict(
            this.currentMatch.equipes[1], 
            newSlot, 
            data.matches.scheduled,
            this.currentMatch.match_id
        );
        
        if (equipe1Conflict || equipe2Conflict) {
            const conflictTeams = [];
            if (equipe1Conflict) conflictTeams.push(data.entities.equipes.find(e => e.id === this.currentMatch.equipes[0])?.nom);
            if (equipe2Conflict) conflictTeams.push(data.entities.equipes.find(e => e.id === this.currentMatch.equipes[1])?.nom);
            
            this._showConflictAlert(`Conflit d'horaire pour: ${conflictTeams.join(', ')}`);
            return false;
        }
        
        this._hideConflictAlert();
        return true;
    }
    
    /**
     * Affiche l'alerte de conflit
     */
    _showConflictAlert(message) {
        const alert = document.getElementById('edit-conflict-alert');
        const messageEl = document.getElementById('edit-conflict-message');
        
        messageEl.textContent = message;
        alert.classList.remove('hidden');
    }
    
    /**
     * Cache l'alerte de conflit
     */
    _hideConflictAlert() {
        document.getElementById('edit-conflict-alert').classList.add('hidden');
    }
    
    /**
     * Sauvegarde les modifications
     */
    save() {
        if (!this.validateForm()) {
            return;
        }
        
        const semaine = parseInt(document.getElementById('edit-week').value);
        const horaire = document.getElementById('edit-time').value;
        const gymnase = document.getElementById('edit-venue').value;
        
        const originalSlot = {
            semaine: this.currentMatch.semaine,
            horaire: this.currentMatch.horaire,
            gymnase: this.currentMatch.gymnase
        };
        
        const newSlot = { semaine, horaire, gymnase };
        
        // Ajouter la modification
        this.modificationManager.addModification(
            this.currentMatch.match_id,
            originalSlot,
            newSlot
        );
        
        // Mettre à jour le match dans le DataManager
        this.dataManager.updateMatch(this.currentMatch.match_id, newSlot);
        
        this.close();
    }
    
    /**
     * Déplanifie le match
     */
    unschedule() {
        if (!confirm('Voulez-vous vraiment déplanifier ce match ?')) {
            return;
        }
        
        const originalSlot = {
            semaine: this.currentMatch.semaine,
            horaire: this.currentMatch.horaire,
            gymnase: this.currentMatch.gymnase
        };
        
        const newSlot = {
            semaine: null,
            horaire: null,
            gymnase: null
        };
        
        // Ajouter la modification
        this.modificationManager.addModification(
            this.currentMatch.match_id,
            originalSlot,
            newSlot
        );
        
        // Mettre à jour le match
        this.dataManager.updateMatch(this.currentMatch.match_id, newSlot);
        
        this.close();
    }
    
    /**
     * Ferme le modal
     */
    close() {
        this.modal.classList.add('hidden');
        this.currentMatch = null;
        document.getElementById('edit-form').reset();
        this._hideConflictAlert();
    }
};
