/**
 * AvailableSlotsManager - Gestion des créneaux disponibles
 * 
 * Responsabilités:
 * - Calcul des créneaux disponibles (terrains libres)
 * - Rendu visuel des cases vertes
 * - Gestion du toggle affichage/masquage
 * - Zones de drop pour drag & drop
 */

class AvailableSlotsManager {
    constructor() {
        this.showAvailableSlots = false;
    }
    
    /**
     * Toggle l'affichage des créneaux disponibles
     */
    toggle() {
        this.showAvailableSlots = !this.showAvailableSlots;
        return this.showAvailableSlots;
    }
    
    /**
     * Active/désactive l'affichage
     */
    setShow(show) {
        this.showAvailableSlots = show;
    }
    
    /**
     * Calcule les créneaux disponibles pour un slot
     * @param {Array} slotMatches - Matchs déjà dans le créneau
     * @param {number} capacity - Capacité du gymnase
     * @returns {number} - Nombre de terrains disponibles
     */
    calculateAvailable(slotMatches, capacity) {
        return Math.max(0, capacity - slotMatches.length);
    }
    
    /**
     * Génère les cases de créneaux disponibles
     * @param {number} available - Nombre de terrains disponibles
     * @param {Object} slotInfo - Informations sur le créneau (time, column)
     * @returns {string} - HTML des cases vertes
     */
    renderAvailableSlots(available, slotInfo) {
        if (!this.showAvailableSlots || available <= 0) {
            return '';
        }
        
        const slots = [];
        for (let i = 0; i < available; i++) {
            slots.push(this.renderSingleSlot(slotInfo, i));
        }
        
        return slots.join('');
    }
    
    /**
     * Génère une case de créneau disponible
     */
    renderSingleSlot(slotInfo, index) {
        return `
            <div class="available-slot" 
                 data-slot-type="available"
                 data-time="${slotInfo.time}"
                 data-column="${slotInfo.columnId}"
                 data-index="${index}"
                 title="Terrain disponible\nClic pour ajouter un match">
                <div class="available-slot-content">
                    <span class="available-slot-icon">✓</span>
                    <span class="available-slot-text">Disponible</span>
                </div>
            </div>
        `;
    }
    
    /**
     * Génère un indicateur visuel de disponibilité (sans prendre de place)
     */
    renderAvailabilityIndicator(available, capacity) {
        if (!this.showAvailableSlots || available <= 0) {
            return '';
        }
        
        const percentage = (available / capacity) * 100;
        const className = percentage >= 75 ? 'high' : percentage >= 50 ? 'medium' : 'low';
        
        return `
            <div class="availability-indicator ${className}">
                <span>${available}/${capacity} libres</span>
            </div>
        `;
    }
    
    /**
     * Vérifie si un créneau peut accueillir un match
     */
    canAcceptMatch(slotMatches, capacity) {
        return slotMatches.length < capacity;
    }
    
    /**
     * Génère un overlay de créneau disponible pour drag & drop
     */
    renderDropZone(slotInfo, isActive = false) {
        const classes = ['drop-zone'];
        if (isActive) classes.push('drop-zone-active');
        
        return `
            <div class="${classes.join(' ')}"
                 data-drop-zone="true"
                 data-time="${slotInfo.time}"
                 data-column="${slotInfo.columnId}">
                <div class="drop-zone-content">
                    <span class="drop-zone-icon">+</span>
                    <span class="drop-zone-text">Déposer ici</span>
                </div>
            </div>
        `;
    }
}

// Export global
window.AvailableSlotsManager = AvailableSlotsManager;
