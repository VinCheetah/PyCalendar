/**
 * EditModal - Modal dialog for editing match details
 * 
 * Features:
 * - Edit week number, time slot, and venue
 * - Show available options (venues and time slots)
 * - Store modifications in localStorage
 * - Export modifications as JSON
 * - Visual feedback for modified matches
 */

class EditModal {
    constructor() {
        this.currentMatch = null;
        this.modifications = this.loadModifications();
        this.modal = null;
        this.createModal();
        this.setupEventListeners();
    }

    /**
     * Load modifications from localStorage
     */
    loadModifications() {
        try {
            const saved = localStorage.getItem('matchModifications');
            return saved ? JSON.parse(saved) : {};
        } catch (e) {
            console.error('Error loading modifications:', e);
            return {};
        }
    }

    /**
     * Save a single modification (called from drag-and-drop)
     * @param {Object} modification - Modification object with match_id, original, new
     */
    saveModification(modification) {
        console.log('📝 EditModal.saveModification called with:', modification);
        
        // Utiliser DataManager pour sauvegarder
        if (window.dataManager) {
            const success = window.dataManager.saveModification(modification);
            if (success) {
                // Synchroniser l'état local
                this.modifications = window.dataManager.getModifications();
                this.updateMatchCardUI(modification.match_id, true);
                console.log('✅ Modification saved via DataManager');
            }
        } else {
            // Fallback: ancien système
            const matchId = modification.match_id;
            
            this.modifications[matchId] = {
                original: modification.original,
                new: modification.new,
                timestamp: new Date().toISOString(),
                teams: modification.teams || 'Unknown'
            };
            
            this.saveModifications();
            this.updateMatchCardUI(matchId, true);
            console.log('✅ Modification saved (legacy mode)');
        }
    }

    /**
     * Save modifications to localStorage (LEGACY - DataManager le fait maintenant)
     */
    saveModifications() {
        try {
            localStorage.setItem('matchModifications', JSON.stringify(this.modifications));
            this.updateModificationCounter();
        } catch (e) {
            console.error('Error saving modifications:', e);
        }
    }

    /**
     * Create modal HTML structure
     */
    createModal() {
        const modalHTML = `
            <div id="editModal" class="edit-modal" style="display: none;">
                <div class="edit-modal-backdrop"></div>
                <div class="edit-modal-content">
                    <div class="edit-modal-header">
                        <h3>✏️ Modifier le Match</h3>
                        <button class="edit-modal-close" id="closeEditModal">&times;</button>
                    </div>
                    
                    <div class="edit-modal-body">
                        <div class="match-info">
                            <div class="match-teams">
                                <span id="editTeam1"></span> <strong>vs</strong> <span id="editTeam2"></span>
                            </div>
                            <div class="match-pool">Poule: <span id="editPool"></span></div>
                        </div>

                        <div class="edit-form">
                            <div class="form-group">
                                <label for="editWeek">Semaine</label>
                                <input type="number" id="editWeek" min="1" max="26" class="form-control">
                            </div>

                            <div class="form-group">
                                <label for="editTime">Horaire</label>
                                <select id="editTime" class="form-control">
                                    <option value="">-- Choisir --</option>
                                </select>
                            </div>

                            <div class="form-group">
                                <label for="editVenue">Gymnase</label>
                                <select id="editVenue" class="form-control">
                                    <option value="">-- Choisir --</option>
                                </select>
                            </div>

                            <div class="conflict-actions" id="conflictActions">
                                <div class="conflict-warning">
                                    <span class="conflict-warning-icon">⚠️</span>
                                    <span>Ce créneau est déjà occupé!</span>
                                </div>
                                <div class="conflict-match-info" id="conflictMatchInfo"></div>
                                <div class="conflict-buttons">
                                    <button class="btn-conflict btn-force-replace" id="btnForceReplace">
                                        🔄 Remplacer
                                    </button>
                                    <button class="btn-conflict btn-swap" id="btnSwap">
                                        ↔️ Échanger
                                    </button>
                                </div>
                            </div>

                            <div class="original-values">
                                <strong>Valeurs originales:</strong>
                                <div id="originalValues"></div>
                            </div>
                        </div>
                    </div>

                    <div class="edit-modal-footer">
                        <button id="unscheduleMatch" class="btn btn-danger-outline">
                            🗑️ Déplanifier
                        </button>
                        <div style="flex: 1;"></div>
                        <button id="cancelEdit" class="btn btn-secondary">Annuler</button>
                        <button id="saveEdit" class="btn btn-primary">💾 Enregistrer</button>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        this.modal = document.getElementById('editModal');
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        document.getElementById('closeEditModal').addEventListener('click', () => this.close());
        document.getElementById('cancelEdit').addEventListener('click', () => this.close());
        document.getElementById('saveEdit').addEventListener('click', () => this.save());
        document.getElementById('unscheduleMatch').addEventListener('click', () => this.unschedule());
        
        // Close on backdrop click
        this.modal.querySelector('.edit-modal-backdrop').addEventListener('click', () => this.close());
        
        // Close on Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.modal.style.display !== 'none') {
                this.close();
            }
        });
        
        // Smart filtering: Week change updates venues and time slots
        document.getElementById('editWeek').addEventListener('change', () => this.onWeekChange());
        
        // Smart filtering: Venue change updates time slots
        document.getElementById('editVenue').addEventListener('change', () => this.onVenueChange());
        
        // Time slot change checks for conflicts
        document.getElementById('editTime').addEventListener('change', () => this.checkConflict());
        
        // Conflict action buttons
        document.getElementById('btnForceReplace').addEventListener('click', () => this.forceReplace());
        document.getElementById('btnSwap').addEventListener('click', () => this.swapMatches());
    }

    /**
     * Handle week change - update venues and time slots
     */
    onWeekChange() {
        const week = parseInt(document.getElementById('editWeek').value);
        const currentVenue = document.getElementById('editVenue').value;
        const currentTime = document.getElementById('editTime').value;
        
        if (week) {
            // Repopulate with current selections
            this.populateVenues(currentVenue, week, currentTime);
            this.populateTimeSlots(currentTime, currentVenue, week);
        }
        
        this.checkConflict();
    }

    /**
     * Handle venue change - update time slots
     */
    onVenueChange() {
        const venue = document.getElementById('editVenue').value;
        const currentTime = document.getElementById('editTime').value;
        const week = parseInt(document.getElementById('editWeek').value);
        
        if (week) {
            // Repopulate time slots filtered by venue (or all if no venue)
            this.populateTimeSlots(currentTime, venue, week);
        }
        
        this.checkConflict();
    }

    /**
     * Check for conflicts and show/hide conflict panel
     */
    checkConflict() {
        const week = parseInt(document.getElementById('editWeek').value);
        const time = document.getElementById('editTime').value;
        const venue = document.getElementById('editVenue').value;
        
        const conflictPanel = document.getElementById('conflictActions');
        const conflictInfo = document.getElementById('conflictMatchInfo');
        
        if (!week || !time || !venue) {
            conflictPanel.classList.remove('active');
            return;
        }
        
        const conflictingMatch = this.getConflictingMatch(week, time, venue);
        
        if (conflictingMatch) {
            conflictInfo.innerHTML = `
                <strong>Match actuel:</strong><br>
                ${conflictingMatch.equipe1} vs ${conflictingMatch.equipe2}<br>
                <em>${conflictingMatch.poule}</em>
            `;
            conflictPanel.classList.add('active');
            this.conflictingMatch = conflictingMatch;
        } else {
            conflictPanel.classList.remove('active');
            this.conflictingMatch = null;
        }
    }

    /**
     * Get the match that conflicts with the selected slot
     */
    getConflictingMatch(week, time, venue) {
        if (!window.allMatches) return null;
        
        const currentMatchId = this.currentMatch?.match_id;
        
        return window.allMatches.find(match => 
            match.match_id !== currentMatchId &&
            match.semaine === week &&
            match.horaire === time &&
            match.gymnase === venue
        );
    }

    /**
     * Force replace - cancel conflicting match and place current one
     */
    forceReplace() {
        if (!this.conflictingMatch || !this.currentMatch) return;
        
        const week = parseInt(document.getElementById('editWeek').value);
        const time = document.getElementById('editTime').value;
        const venue = document.getElementById('editVenue').value;
        
        if (confirm(`⚠️ Voulez-vous vraiment remplacer le match "${this.conflictingMatch.equipe1} vs ${this.conflictingMatch.equipe2}" ?\n\nCe match sera déplacé vers les matchs non planifiés.`)) {
            // Mark conflicting match as unscheduled
            this.modifications[this.conflictingMatch.match_id] = {
                original: {
                    week: this.conflictingMatch.semaine,
                    time: this.conflictingMatch.horaire,
                    venue: this.conflictingMatch.gymnase
                },
                new: {
                    week: null,
                    time: null,
                    venue: null
                },
                timestamp: new Date().toISOString(),
                teams: `${this.conflictingMatch.equipe1} vs ${this.conflictingMatch.equipe2}`,
                action: 'force-replaced'
            };
            
            // Update current match to new slot
            this.saveCurrentMatch(week, time, venue);
            
            this.showNotification(`✅ Match replacé avec succès! Le match ${this.conflictingMatch.equipe1} vs ${this.conflictingMatch.equipe2} a été déplacé.`);
            this.close();
        }
    }

    /**
     * Swap matches - exchange time slots
     */
    swapMatches() {
        if (!this.conflictingMatch || !this.currentMatch) return;
        
        const newWeek = parseInt(document.getElementById('editWeek').value);
        const newTime = document.getElementById('editTime').value;
        const newVenue = document.getElementById('editVenue').value;
        
        if (confirm(`↔️ Échanger les créneaux entre:\n\n"${this.currentMatch.equipe1} vs ${this.currentMatch.equipe2}"\net\n"${this.conflictingMatch.equipe1} vs ${this.conflictingMatch.equipe2}"?`)) {
            // Swap: Move conflicting match to current match's slot
            this.modifications[this.conflictingMatch.match_id] = {
                original: {
                    week: this.conflictingMatch.semaine,
                    time: this.conflictingMatch.horaire,
                    venue: this.conflictingMatch.gymnase
                },
                new: {
                    week: this.currentMatch.semaine,
                    time: this.currentMatch.horaire,
                    venue: this.currentMatch.gymnase
                },
                timestamp: new Date().toISOString(),
                teams: `${this.conflictingMatch.equipe1} vs ${this.conflictingMatch.equipe2}`,
                action: 'swapped'
            };
            
            // Move current match to conflicting match's slot
            this.saveCurrentMatch(newWeek, newTime, newVenue);
            
            this.showNotification(`✅ Matchs échangés avec succès!`);
            this.close();
        }
    }

    /**
     * Save current match modification
     */
    saveCurrentMatch(week, time, venue) {
        const matchId = this.currentMatch.match_id;
        
        this.modifications[matchId] = {
            original: {
                week: this.currentMatch.semaine,
                time: this.currentMatch.horaire,
                venue: this.currentMatch.gymnase
            },
            new: {
                week: week,
                time: time,
                venue: venue
            },
            timestamp: new Date().toISOString(),
            teams: `${this.currentMatch.equipe1} vs ${this.currentMatch.equipe2}`
        };
        
        this.saveModifications();
        this.updateMatchCardUI(matchId, true);
    }

    /**
     * Get available slots for a specific venue and week
     * Returns array of time strings
     */
    getAvailableSlotsForVenue(week, venue) {
        if (!window.availableSlotsData) return [];
        
        return window.availableSlotsData
            .filter(slot => slot.semaine === week && slot.gymnase === venue)
            .map(slot => slot.horaire)
            .sort();
    }

    /**
     * Check if a time slot is already taken by another match
     */
    isSlotTaken(week, time, venue) {
        if (!window.allMatches) return false;
        
        // Exclude current match from check
        const currentMatchId = this.currentMatch?.match_id;
        
        return window.allMatches.some(match => 
            match.match_id !== currentMatchId &&
            match.semaine === week &&
            match.horaire === time &&
            match.gymnase === venue
        );
    }

    /**
     * Get slot status: 'available', 'taken', or 'unavailable'
     */
    getSlotStatus(week, time, venue) {
        const isTaken = this.isSlotTaken(week, time, venue);
        const availableSlots = this.getAvailableSlotsForVenue(week, venue);
        const isConfigured = availableSlots.includes(time);
        
        if (isTaken) {
            // Slot is occupied by another match
            return 'taken';
        }
        
        if (isConfigured) {
            // Slot is in configuration and not taken
            return 'available';
        }
        
        // Slot is not configured (shouldn't normally happen if we're showing it, but just in case)
        return 'unavailable';
    }

    /**
     * Check if venue has any available slots for a given week
     */
    hasAvailableSlots(week, venue) {
        const slots = this.getAvailableSlotsForVenue(week, venue);
        return slots.length > 0;
    }

    /**
     * Open modal for a specific match
     * @param {Object} matchData - Match data
     * @param {HTMLElement} triggerElement - Element that triggered the modal (for positioning)
     */
    open(matchData, triggerElement = null) {
        this.currentMatch = matchData;
        
        // Populate match info
        document.getElementById('editTeam1').textContent = matchData.equipe1;
        document.getElementById('editTeam2').textContent = matchData.equipe2;
        document.getElementById('editPool').textContent = matchData.poule;
        
        // Check if this match has existing modifications
        const existing = this.modifications[matchData.match_id];
        
        // Set current values (modified or original)
        const currentWeek = existing ? existing.new.week : matchData.semaine;
        const currentTime = existing ? existing.new.time : matchData.horaire;
        const currentVenue = existing ? existing.new.venue : matchData.gymnase;
        
        document.getElementById('editWeek').value = currentWeek;
        
        // Populate with smart cross-filtering enabled
        // First populate time slots (may show all if no venue selected)
        this.populateTimeSlots(currentTime, currentVenue, currentWeek);
        // Then populate venues (may filter by time if selected)
        this.populateVenues(currentVenue, currentWeek, currentTime);
        
        // Check for initial conflict
        this.checkConflict();
        
        // Show original values
        const originalHTML = `
            <div>Semaine: ${matchData.semaine}</div>
            <div>Horaire: ${matchData.horaire}</div>
            <div>Gymnase: ${matchData.gymnase}</div>
        `;
        document.getElementById('originalValues').innerHTML = originalHTML;
        
        // Position modal near the trigger element if provided
        if (triggerElement) {
            this.positionModalNearElement(triggerElement);
        }
        
        // Show modal
        this.modal.style.display = 'flex';
        // Don't freeze the body - allow scrolling
        // document.body.style.overflow = 'hidden';  // REMOVED to keep interface responsive
    }

    /**
     * Position modal near a specific element
     */
    positionModalNearElement(element) {
        const modalContent = this.modal.querySelector('.edit-modal-content');
        const rect = element.getBoundingClientRect();
        const viewportHeight = window.innerHeight;
        const modalHeight = 600; // Approximate modal height
        
        // Calculate vertical position
        let top = rect.top;
        
        // Adjust if modal would go off-screen at bottom
        if (top + modalHeight > viewportHeight) {
            top = Math.max(20, viewportHeight - modalHeight - 20);
        }
        
        // Adjust if too close to top
        if (top < 20) {
            top = 20;
        }
        
        // Apply positioning
        modalContent.style.marginTop = `${top}px`;
        
        // Add horizontal centering with slight offset if near edge
        const horizontalCenter = rect.left + (rect.width / 2);
        if (horizontalCenter < window.innerWidth / 3) {
            // Element on left side - position modal slightly to the right
            modalContent.style.marginLeft = '60px';
        } else if (horizontalCenter > (window.innerWidth * 2) / 3) {
            // Element on right side - position modal slightly to the left
            modalContent.style.marginRight = '60px';
        }
    }

    /**
     * Populate time slots dropdown with smart filtering
     * Shows ALL time slots including taken ones, with indicators
     * @param {string} selectedTime - Currently selected time
     * @param {string} venue - Filter by venue (optional)
     * @param {number} week - Week number for availability check (optional)
     */
    populateTimeSlots(selectedTime, venue = null, week = null) {
        const timeSelect = document.getElementById('editTime');
        let times = [];
        
        console.log('populateTimeSlots called:', { selectedTime, venue, week });
        console.log('Available data:', {
            hasAvailableSlotsData: !!window.availableSlotsData,
            availableSlotsCount: window.availableSlotsData?.length,
            hasAllMatches: !!window.allMatches,
            allMatchesCount: window.allMatches?.length
        });
        
        if (week) {
            if (venue) {
                // Venue selected: show this venue's configured slots PLUS any times that have matches
                const configuredSlots = this.getAvailableSlotsForVenue(week, venue);
                
                // Get times that already have matches at this venue/week
                const matchTimes = window.allMatches
                    .filter(m => m.semaine === week && m.gymnase === venue)
                    .map(m => m.horaire);
                
                console.log('Venue mode:', { venue, configuredSlots, matchTimes });
                
                // Combine and deduplicate
                times = [...new Set([...configuredSlots, ...matchTimes])].sort();
                
                console.log('Combined times:', times);
            } else {
                // No venue: show ALL unique time slots across all venues for this week
                // Include both configured slots and slots with existing matches
                const configuredTimes = window.availableSlotsData
                    .filter(slot => slot.semaine === week)
                    .map(slot => slot.horaire);
                
                const matchTimes = window.allMatches
                    .filter(m => m.semaine === week)
                    .map(m => m.horaire);
                
                times = [...new Set([...configuredTimes, ...matchTimes])].sort();
            }
        } else {
            // Fallback: show all standard times
            times = ['09:00', '12:00', '14:00', '16:00', '18:00', '20:00'];
        }
        
        timeSelect.innerHTML = '<option value="">-- Choisir --</option>';
        
        times.forEach(time => {
            const option = document.createElement('option');
            option.value = time;
            
            // Check availability status if week is provided
            if (week) {
                let status = 'available';
                let venueInfo = '';
                
                if (venue) {
                    // Venue selected: check this specific venue
                    status = this.getSlotStatus(week, time, venue);
                    
                    console.log(`Slot ${time} status:`, status);
                    
                    const indicators = {
                        'available': '✅ ',
                        'taken': '⚠️ ',
                        'unavailable': '❌ '
                    };
                    
                    const statusLabels = {
                        'available': ' (libre)',
                        'taken': ' (occupé)',
                        'unavailable': ' (pas configuré)'
                    };
                    
                    option.textContent = `${indicators[status]}${time}${statusLabels[status]}`;
                    
                    // NEVER disable - always allow selection to enable conflict resolution
                    // option.disabled = false;  // All slots clickable
                    
                    option.classList.add(`slot-${status}`);
                } else {
                    // No venue: show which venues have this time slot available
                    const availableVenues = window.availableSlotsData
                        .filter(slot => slot.semaine === week && slot.horaire === time)
                        .map(slot => slot.gymnase);
                    
                    const takenVenues = availableVenues.filter(v => 
                        this.isSlotTaken(week, time, v)
                    );
                    
                    const freeVenues = availableVenues.filter(v => 
                        !this.isSlotTaken(week, time, v)
                    );
                    
                    if (freeVenues.length > 0) {
                        status = 'available';
                        venueInfo = ` (${freeVenues.length} gymnase${freeVenues.length > 1 ? 's' : ''} libre${freeVenues.length > 1 ? 's' : ''})`;
                    } else if (takenVenues.length > 0) {
                        status = 'taken';
                        venueInfo = ` (${takenVenues.length} occupé${takenVenues.length > 1 ? 's' : ''})`;
                    } else {
                        status = 'unavailable';
                        venueInfo = ' (aucun gymnase)';
                    }
                    
                    const indicators = {
                        'available': '✅ ',
                        'taken': '⚠️ ',
                        'unavailable': '❌ '
                    };
                    
                    option.textContent = `${indicators[status]}${time}${venueInfo}`;
                    option.classList.add(`slot-${status}`);
                    
                    // NEVER disable - always allow selection
                    // option.disabled = false;  // All slots clickable
                }
            } else {
                option.textContent = time;
            }
            
            if (time === selectedTime) option.selected = true;
            timeSelect.appendChild(option);
        });
    }

    /**
     * Populate venues dropdown with smart filtering
     * Shows ALL venues, never disabled, with availability indicators
     * @param {string} selectedVenue - Currently selected venue
     * @param {number} week - Filter by week (optional)
     * @param {string} time - Filter by time slot (optional)
     */
    populateVenues(selectedVenue, week = null, time = null) {
        const venueSelect = document.getElementById('editVenue');
        
        // ALWAYS show ALL venues - never filter, never disable
        const venues = [...new Set(window.allMatches.map(m => m.gymnase))].sort();
        
        venueSelect.innerHTML = '<option value="">-- Choisir --</option>';
        
        venues.forEach(venue => {
            const option = document.createElement('option');
            option.value = venue;
            
            // Check availability status if week is provided
            if (week) {
                let status = 'unavailable';  // Default: no slots configured
                let indicator = '❌ ';
                let slotInfo = '';
                
                if (time) {
                    // Time selected: check if this venue has this specific time available
                    const hasTimeSlot = window.availableSlotsData?.some(slot => 
                        slot.semaine === week && 
                        slot.horaire === time && 
                        slot.gymnase === venue
                    );
                    
                    if (hasTimeSlot) {
                        const isTaken = this.isSlotTaken(week, time, venue);
                        status = isTaken ? 'taken' : 'available';
                        indicator = isTaken ? '⚠️ ' : '✅ ';
                        slotInfo = isTaken ? ' (occupé)' : ' (libre)';
                    } else {
                        status = 'unavailable';
                        indicator = '❌ ';
                        slotInfo = ' (pas ce créneau)';
                    }
                } else {
                    // No time: show general availability summary for this week
                    const venueSlots = this.getAllTimesForVenue(week, venue);
                    
                    if (venueSlots.length > 0) {
                        const takenCount = venueSlots.filter(t => 
                            this.isSlotTaken(week, t, venue)
                        ).length;
                        const freeCount = venueSlots.length - takenCount;
                        
                        if (freeCount > 0) {
                            status = 'available';
                            indicator = '✅ ';
                            slotInfo = ` (${freeCount}/${venueSlots.length} libres)`;
                        } else {
                            status = 'taken';
                            indicator = '⚠️ ';
                            slotInfo = ` (${venueSlots.length} occupés)`;
                        }
                    } else {
                        status = 'unavailable';
                        indicator = '❌ ';
                        slotInfo = ' (aucun créneau)';
                    }
                }
                
                option.textContent = `${indicator}${venue}${slotInfo}`;
                option.classList.add(`slot-${status}`);
                
                // NEVER disable - always allow selection
                // option.disabled = false;  // Explicit: all venues clickable
            } else {
                option.textContent = venue;
            }
            
            if (venue === selectedVenue) option.selected = true;
            venueSelect.appendChild(option);
        });
        
        console.log(`[populateVenues] Showing ${venues.length} venues (all clickable), week=${week}, time=${time}`);
    }

    /**
     * Save modifications
     */
    save() {
        if (!this.currentMatch) return;
        
        const newWeek = parseInt(document.getElementById('editWeek').value);
        const newTime = document.getElementById('editTime').value;
        const newVenue = document.getElementById('editVenue').value;
        
        // Validate inputs
        if (!newWeek || !newTime || !newVenue) {
            alert('⚠️ Veuillez remplir tous les champs');
            return;
        }
        
        const matchId = this.currentMatch.match_id;
        
        // Check if values actually changed
        const changed = (
            newWeek !== this.currentMatch.semaine ||
            newTime !== this.currentMatch.horaire ||
            newVenue !== this.currentMatch.gymnase
        );
        
        if (!changed) {
            // If no changes and modification exists, remove it
            if (this.modifications[matchId]) {
                delete this.modifications[matchId];
                this.saveModifications();
                this.updateMatchCardUI(matchId, false);
            }
            this.close();
            return;
        }
        
        // Check for conflicts one more time before saving
        const conflictingMatch = this.getConflictingMatch(newWeek, newTime, newVenue);
        if (conflictingMatch) {
            alert('⚠️ Ce créneau est occupé! Utilisez "Remplacer" ou "Échanger" pour résoudre le conflit.');
            return;
        }
        
        // Save without conflict
        this.saveCurrentMatch(newWeek, newTime, newVenue);
        this.close();
        
        // Show success message
        this.showNotification(`✅ Match modifié: ${this.currentMatch.equipe1} vs ${this.currentMatch.equipe2}`);
    }

    /**
     * Update match card UI to show it's modified
     */
    updateMatchCardUI(matchId, isModified) {
        const cards = document.querySelectorAll(`[data-match-id="${matchId}"]`);
        cards.forEach(card => {
            if (isModified) {
                card.classList.add('match-modified');
                
                // Update displayed values
                const mod = this.modifications[matchId];
                const weekElem = card.querySelector('.match-week');
                const timeElem = card.querySelector('.match-time');
                const venueElem = card.querySelector('.match-venue');
                
                if (weekElem) weekElem.textContent = `S${mod.new.week}`;
                if (timeElem) timeElem.textContent = mod.new.time;
                if (venueElem) venueElem.textContent = mod.new.venue;
            } else {
                card.classList.remove('match-modified');
            }
        });
    }
    
    /**
     * Déplanifier un match (le retirer du calendrier)
     */
    unschedule() {
        if (!this.currentMatch) return;
        
        const matchInfo = `${this.currentMatch.equipe1} vs ${this.currentMatch.equipe2}`;
        const confirmed = confirm(
            `🗑️ Déplanifier ce match ?\n\n${matchInfo}\n\n` +
            `Le match sera retiré du calendrier et ajouté à la liste des matchs non planifiés.`
        );
        
        if (!confirmed) return;
        
        const matchId = this.currentMatch.match_id;
        
        // Créer une "modification" qui marque le match comme déplanifié
        const unscheduleModification = {
            match_id: matchId,
            original: {
                week: this.currentMatch.semaine,
                time: this.currentMatch.horaire,
                venue: this.currentMatch.gymnase
            },
            new: {
                week: null,  // null indique "non planifié"
                time: null,
                venue: null
            },
            action: 'unschedule'  // Marqueur spécial
        };
        
        // Sauvegarder via DataManager
        if (window.dataManager) {
            window.dataManager.saveModification(unscheduleModification);
        }
        
        // Libérer le créneau dans SlotManager
        if (window.slotManager) {
            window.slotManager.freeSlot(
                this.currentMatch.semaine,
                this.currentMatch.horaire,
                this.currentMatch.gymnase
            );
        }
        
        this.close();
        
        // Rafraîchir l'affichage
        setTimeout(() => {
            if (window.app && typeof window.app.reloadAndRender === 'function') {
                window.app.reloadAndRender();
            }
        }, 300);
        
        this.showNotification(`🗑️ Match déplanifié: ${matchInfo}`);
    }

    /**
     * Close modal
     */
    close() {
        // Add closing animation
        this.modal.classList.add('closing');
        
        // Wait for animation to complete before hiding
        setTimeout(() => {
            this.modal.style.display = 'none';
            this.modal.classList.remove('closing');
            
            // Reset positioning styles
            const modalContent = this.modal.querySelector('.edit-modal-content');
            modalContent.style.marginTop = '';
            modalContent.style.marginLeft = '';
            modalContent.style.marginRight = '';
            
            // No need to restore body overflow since we don't freeze it anymore
            // document.body.style.overflow = '';
            
            this.currentMatch = null;
        }, 200); // Match animation duration
    }

    /**
     * Export modifications as JSON
     */
    exportModifications() {
        const count = Object.keys(this.modifications).length;
        
        if (count === 0) {
            alert('ℹ️ Aucune modification à exporter');
            return;
        }
        
        const data = JSON.stringify(this.modifications, null, 2);
        const blob = new Blob([data], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        const date = new Date().toISOString().split('T')[0];
        a.download = `modifications_${date}.json`;
        a.click();
        
        URL.revokeObjectURL(url);
        
        this.showInstructions(count);
    }

    /**
     * Show instructions after export
     */
    showInstructions(count) {
        const instructions = `
✅ ${count} modification(s) exportée(s) !

📝 Pour appliquer les modifications:

1. Ouvrez un terminal dans le dossier PyCalendar
2. Exécutez:
   python scripts/apply_modifications.py \\
       data_volley/calendrier_volley.xlsx \\
       modifications_${new Date().toISOString().split('T')[0]}.json \\
       configs/config_volley.yaml

3. (Optionnel) Regénérez la visualisation:
   python open_calendar.py data_volley/calendrier_volley.xlsx

Le script validera les contraintes avant d'appliquer les changements.
        `;
        
        alert(instructions);
    }

    /**
     * Discard all modifications
     */
    discardAll() {
        const count = Object.keys(this.modifications).length;
        
        if (count === 0) {
            alert('ℹ️ Aucune modification à annuler');
            return;
        }
        
        if (confirm(`⚠️ Annuler ${count} modification(s) ?`)) {
            // Remove UI indicators
            Object.keys(this.modifications).forEach(matchId => {
                this.updateMatchCardUI(matchId, false);
            });
            
            this.modifications = {};
            this.saveModifications();
            this.showNotification(`🗑️ ${count} modification(s) annulée(s)`);
        }
    }

    /**
     * Update modification counter
     */
    updateModificationCounter() {
        const count = Object.keys(this.modifications).length;
        const counter = document.getElementById('modificationCounter');
        const badge = counter?.querySelector('.badge');
        
        if (counter) {
            if (count > 0) {
                counter.style.display = 'block';
                if (badge) badge.textContent = `${count} modification${count > 1 ? 's' : ''}`;
            } else {
                counter.style.display = 'none';
            }
        }
    }

    /**
     * Show notification
     */
    showNotification(message) {
        const notification = document.createElement('div');
        notification.className = 'edit-notification';
        notification.textContent = message;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);
        
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    /**
     * Get modification count
     */
    getModificationCount() {
        return Object.keys(this.modifications).length;
    }

    /**
     * Check if a match is modified
     */
    isMatchModified(matchId) {
        return !!this.modifications[matchId];
    }

    /**
     * Get modification for a match
     */
    getModification(matchId) {
        return this.modifications[matchId];
    }
}

// Initialize edit modal when DOM is ready
let editModal;
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        editModal = new EditModal();
        window.editModal = editModal; // Expose globally for drag-and-drop
    });
} else {
    editModal = new EditModal();
    window.editModal = editModal; // Expose globally for drag-and-drop
}
