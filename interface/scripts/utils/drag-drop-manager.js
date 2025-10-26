/**
 * DragDropManager - Gestion du drag & drop des matchs
 * 
 * Responsabilités:
 * - Gestion des événements drag & drop
 * - Validation des déplacements
 * - Swap de matchs
 * - Notification des modifications
 * - Feedback visuel
 */

class DragDropManager {
    constructor(dataManager, modificationManager) {
        this.dataManager = dataManager;
        this.modificationManager = modificationManager;
        
        // État du drag en cours
        this.dragState = {
            active: false,
            matchId: null,
            originalSlot: null,
            ghostElement: null
        };
        
        // Callbacks
        this.onModification = null; // Callback appelé lors d'une modification
        this.onDragStart = null;
        this.onDragEnd = null;
    }
    
    /**
     * Initialise les événements de drag & drop sur un conteneur
     */
    initializeDragDrop(container) {
        // Drag start sur les matchs
        container.addEventListener('dragstart', (e) => this.handleDragStart(e));
        
        // Drag over sur les zones de drop
        container.addEventListener('dragover', (e) => this.handleDragOver(e));
        
        // Drop sur une zone
        container.addEventListener('drop', (e) => this.handleDrop(e));
        
        // Drag end
        container.addEventListener('dragend', (e) => this.handleDragEnd(e));
        
        // Drag enter/leave pour feedback visuel
        container.addEventListener('dragenter', (e) => this.handleDragEnter(e));
        container.addEventListener('dragleave', (e) => this.handleDragLeave(e));
        
        console.log('🎯 Drag & Drop initialized');
    }
    
    /**
     * Début du drag
     */
    handleDragStart(e) {
        const matchCard = e.target.closest('.match-card');
        if (!matchCard || !matchCard.draggable) return;
        
        const matchId = matchCard.dataset.matchId;
        const match = this.dataManager.getMatch(matchId);
        
        // Ne pas permettre le drag des matchs fixés
        if (match?.is_fixed) {
            e.preventDefault();
            return;
        }
        
        this.dragState.active = true;
        this.dragState.matchId = matchId;
        this.dragState.originalSlot = {
            semaine: match.semaine,
            horaire: match.horaire,
            gymnase: match.gymnase
        };
        
        // Styling
        matchCard.classList.add('dragging');
        
        // Data transfer
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/plain', matchId);
        
        // Callback
        if (this.onDragStart) {
            this.onDragStart(match);
        }
        
        console.log('🎯 Drag started:', matchId);
    }
    
    /**
     * Drag over une zone
     */
    handleDragOver(e) {
        if (!this.dragState.active) return;
        
        const dropZone = e.target.closest('[data-drop-zone], .match-card, .available-slot');
        if (!dropZone) return;
        
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
    }
    
    /**
     * Entrée dans une zone de drop
     */
    handleDragEnter(e) {
        if (!this.dragState.active) return;
        
        const dropZone = e.target.closest('[data-drop-zone], .match-card, .available-slot');
        if (!dropZone) return;
        
        dropZone.classList.add('drag-over');
    }
    
    /**
     * Sortie d'une zone de drop
     */
    handleDragLeave(e) {
        if (!this.dragState.active) return;
        
        const dropZone = e.target.closest('[data-drop-zone], .match-card, .available-slot');
        if (!dropZone) return;
        
        // Vérifier que l'on sort vraiment de l'élément
        if (!dropZone.contains(e.relatedTarget)) {
            dropZone.classList.remove('drag-over');
        }
    }
    
    /**
     * Drop du match
     */
    handleDrop(e) {
        e.preventDefault();
        
        if (!this.dragState.active) return;
        
        const dropZone = e.target.closest('[data-drop-zone], .match-card, .available-slot');
        if (!dropZone) {
            this.cancelDrag();
            return;
        }
        
        dropZone.classList.remove('drag-over');
        
        const matchId = this.dragState.matchId;
        const match = this.dataManager.getMatch(matchId);
        
        // Déterminer le type de drop
        if (dropZone.classList.contains('match-card')) {
            // Swap avec un autre match
            this.handleSwapMatches(match, dropZone.dataset.matchId);
        } else {
            // Déplacement vers un créneau disponible
            this.handleMoveToSlot(match, dropZone);
        }
    }
    
    /**
     * Fin du drag
     */
    handleDragEnd(e) {
        if (!this.dragState.active) return;
        
        const matchCard = e.target.closest('.match-card');
        if (matchCard) {
            matchCard.classList.remove('dragging');
        }
        
        // Nettoyer tous les indicateurs
        document.querySelectorAll('.drag-over').forEach(el => {
            el.classList.remove('drag-over');
        });
        
        // Callback
        if (this.onDragEnd) {
            this.onDragEnd();
        }
        
        // Reset state
        this.dragState = {
            active: false,
            matchId: null,
            originalSlot: null,
            ghostElement: null
        };
        
        console.log('🎯 Drag ended');
    }
    
    /**
     * Swap deux matchs
     */
    handleSwapMatches(match1, match2Id) {
        const match2 = this.dataManager.getMatch(match2Id);
        
        if (!match2 || match2.is_fixed) {
            console.warn('Cannot swap with fixed match');
            this.cancelDrag();
            return;
        }
        
        // Échanger les slots
        const slot1 = {
            semaine: match1.semaine,
            horaire: match1.horaire,
            gymnase: match1.gymnase
        };
        
        const slot2 = {
            semaine: match2.semaine,
            horaire: match2.horaire,
            gymnase: match2.gymnase
        };
        
        // Créer les modifications
        this.modificationManager.addModification(match1.match_id, slot2, 'swap');
        this.modificationManager.addModification(match2.match_id, slot1, 'swap');
        
        console.log('🔄 Swapped matches:', match1.match_id, '↔️', match2.match_id);
        
        // Notification
        if (this.onModification) {
            this.onModification({
                type: 'swap',
                matches: [match1, match2],
                slots: [slot2, slot1]
            });
        }
    }
    
    /**
     * Déplace un match vers un créneau
     */
    handleMoveToSlot(match, dropZone) {
        const newSlot = {
            semaine: parseInt(dropZone.dataset.semaine) || match.semaine,
            horaire: dropZone.dataset.time || dropZone.dataset.horaire,
            gymnase: dropZone.dataset.column || dropZone.dataset.gymnase
        };
        
        // Vérifier que le slot a changé
        if (newSlot.semaine === match.semaine && 
            newSlot.horaire === match.horaire && 
            newSlot.gymnase === match.gymnase) {
            console.log('No change in slot');
            this.cancelDrag();
            return;
        }
        
        // Vérifier la disponibilité
        const isAvailable = this.dataManager.isSlotAvailable(
            newSlot.semaine,
            newSlot.horaire,
            newSlot.gymnase
        );
        
        if (!isAvailable) {
            console.warn('Slot not available');
            this.cancelDrag();
            return;
        }
        
        // Créer la modification
        this.modificationManager.addModification(match.match_id, newSlot, 'move');
        
        console.log('📦 Moved match:', match.match_id, 'to', newSlot);
        
        // Notification
        if (this.onModification) {
            this.onModification({
                type: 'move',
                match: match,
                oldSlot: this.dragState.originalSlot,
                newSlot: newSlot
            });
        }
    }
    
    /**
     * Annule le drag en cours
     */
    cancelDrag() {
        console.log('❌ Drag cancelled');
        this.dragState.active = false;
    }
}

// Export global
window.DragDropManager = DragDropManager;
