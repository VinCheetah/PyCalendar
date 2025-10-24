/**
 * Slot Manager - Gestion des créneaux avec statut libre/occupé
 * 
 * ARCHITECTURE:
 * - Tous les créneaux (gymnase × horaire × semaine) sont générés au départ
 * - Chaque créneau a un statut: 'libre' ou 'occupé'
 * - Quand un match bouge: libérer ancien créneau + occuper nouveau
 * - Synchronisation avec localStorage pour persistance
 */

class SlotManager {
    constructor(slotsData) {
        // Index des créneaux par slot_id
        this.slots = new Map();
        
        // Initialiser avec les données
        slotsData.forEach(slot => {
            this.slots.set(slot.slot_id, {
                ...slot,
                statut: slot.statut || 'libre',
                match_id: slot.match_id || null
            });
        });
        
        console.log(`📋 SlotManager initialisé avec ${this.slots.size} créneaux`);
        this.logStats();
        
        // ============ OBSERVER PATTERN ============
        // S'abonner au DataManager pour synchroniser automatiquement
        this.subscribeToDataManager();
    }
    
    /**
     * S'abonner aux changements du DataManager
     * Synchronise automatiquement les créneaux quand un match est modifié
     */
    subscribeToDataManager() {
        if (!window.dataManager) {
            console.warn('⚠️ SlotManager: DataManager not available yet, will retry...');
            // Réessayer après un délai
            setTimeout(() => this.subscribeToDataManager(), 100);
            return;
        }
        
        this.unsubscribe = window.dataManager.subscribe((event) => {
            console.log('🔔 SlotManager received event:', event.type);
            
            switch (event.type) {
                case 'MODIFICATION_SAVED':
                    // Un match a été déplacé
                    const mod = event.modification;
                    this.handleMatchMove(event.matchId, mod.original, mod.new);
                    break;
                    
                case 'MODIFICATION_UNDONE':
                    // Une modification a été annulée
                    // Recharger depuis localStorage ou recalculer
                    this.loadFromLocalStorage();
                    break;
                    
                case 'ALL_MODIFICATIONS_RESET':
                    // Toutes les modifications annulées
                    this.reset();
                    break;
            }
        });
        
        console.log('✅ SlotManager subscribed to DataManager');
    }
    
    /**
     * Gérer le déplacement d'un match
     */
    handleMatchMove(matchId, originalSlot, newSlot) {
        console.log(`🔄 SlotManager: Handling move for ${matchId}`);
        console.log('  Original slot:', originalSlot);
        console.log('  New slot:', newSlot);
        
        // Convertir les propriétés week/time/venue vers semaine/horaire/gymnase
        const oldSlot = {
            semaine: originalSlot.week,
            horaire: originalSlot.time,
            gymnase: originalSlot.venue
        };
        
        const newSlotConverted = {
            semaine: newSlot.week,
            horaire: newSlot.time,
            gymnase: newSlot.venue
        };
        
        // Libérer l'ancien créneau
        this.freeSlot(oldSlot.semaine, oldSlot.horaire, oldSlot.gymnase);
        
        // Occuper le nouveau créneau
        this.occupySlot(newSlotConverted.semaine, newSlotConverted.horaire, newSlotConverted.gymnase, matchId);
        
        // Sauvegarder
        this.saveToLocalStorage();
        
        console.log('✅ SlotManager: Move handled successfully');
    }
    
    /**
     * Obtenir un créneau par ses coordonnées
     */
    getSlot(semaine, horaire, gymnase) {
        const slotId = `${semaine}_${horaire}_${gymnase}`;
        return this.slots.get(slotId);
    }
    
    /**
     * Vérifier si un créneau est libre
     */
    isSlotFree(semaine, horaire, gymnase) {
        const slot = this.getSlot(semaine, horaire, gymnase);
        return slot && slot.statut === 'libre';
    }
    
    /**
     * Occuper un créneau avec un match
     */
    occupySlot(semaine, horaire, gymnase, matchId) {
        const slotId = `${semaine}_${horaire}_${gymnase}`;
        const slot = this.slots.get(slotId);
        
        if (!slot) {
            console.warn(`⚠️ Créneau inexistant: ${slotId}`);
            return false;
        }
        
        if (slot.statut === 'occupé' && slot.match_id !== matchId) {
            console.warn(`⚠️ Créneau ${slotId} déjà occupé par ${slot.match_id}`);
            return false;
        }
        
        slot.statut = 'occupé';
        slot.match_id = matchId;
        
        console.log(`✅ Créneau ${slotId} occupé par ${matchId}`);
        return true;
    }
    
    /**
     * Libérer un créneau
     */
    freeSlot(semaine, horaire, gymnase) {
        const slotId = `${semaine}_${horaire}_${gymnase}`;
        const slot = this.slots.get(slotId);
        
        if (!slot) {
            console.warn(`⚠️ Créneau inexistant: ${slotId}`);
            return false;
        }
        
        const previousMatchId = slot.match_id;
        slot.statut = 'libre';
        slot.match_id = null;
        
        console.log(`🆓 Créneau ${slotId} libéré (était occupé par ${previousMatchId})`);
        return true;
    }
    
    /**
     * Déplacer un match: libérer ancien créneau + occuper nouveau
     */
    moveMatch(matchId, oldSlot, newSlot) {
        console.log(`🔄 Déplacement match ${matchId}:`, {
            from: oldSlot,
            to: newSlot
        });
        
        // CONVERSION: week/time/venue → semaine/horaire/gymnase
        // Car DataManager utilise {week, time, venue} mais SlotManager attend {semaine, horaire, gymnase}
        const oldSlotConverted = oldSlot ? {
            semaine: oldSlot.week || oldSlot.semaine,
            horaire: oldSlot.time || oldSlot.horaire,
            gymnase: oldSlot.venue || oldSlot.gymnase
        } : null;
        
        const newSlotConverted = {
            semaine: newSlot.week || newSlot.semaine,
            horaire: newSlot.time || newSlot.horaire,
            gymnase: newSlot.venue || newSlot.gymnase
        };
        
        // Libérer ancien créneau
        if (oldSlotConverted) {
            this.freeSlot(oldSlotConverted.semaine, oldSlotConverted.horaire, oldSlotConverted.gymnase);
        }
        
        // Occuper nouveau créneau
        const success = this.occupySlot(
            newSlotConverted.semaine, 
            newSlotConverted.horaire, 
            newSlotConverted.gymnase, 
            matchId
        );
        
        if (success) {
            this.logStats();
            this.saveToLocalStorage();
        }
        
        return success;
    }
    
    /**
     * Obtenir tous les créneaux libres
     */
    getFreeSlots() {
        const freeSlots = [];
        this.slots.forEach(slot => {
            if (slot.statut === 'libre') {
                freeSlots.push(slot);
            }
        });
        return freeSlots;
    }
    
    /**
     * Obtenir tous les créneaux occupés
     */
    getOccupiedSlots() {
        const occupiedSlots = [];
        this.slots.forEach(slot => {
            if (slot.statut === 'occupé') {
                occupiedSlots.push(slot);
            }
        });
        return occupiedSlots;
    }
    
    /**
     * Statistiques des créneaux
     */
    logStats() {
        const free = this.getFreeSlots().length;
        const occupied = this.getOccupiedSlots().length;
        const total = this.slots.size;
        
        console.log(`📊 Créneaux: ${occupied} occupés / ${free} libres / ${total} total`);
    }
    
    /**
     * Sauvegarder l'état dans localStorage
     */
    saveToLocalStorage() {
        try {
            const slotsArray = Array.from(this.slots.values());
            localStorage.setItem('slotsState', JSON.stringify(slotsArray));
            console.log('💾 État des créneaux sauvegardé');
        } catch (e) {
            console.error('❌ Erreur sauvegarde créneaux:', e);
        }
    }
    
    /**
     * Charger l'état depuis localStorage
     */
    loadFromLocalStorage() {
        try {
            const saved = localStorage.getItem('slotsState');
            if (saved) {
                const slotsArray = JSON.parse(saved);
                this.slots.clear();
                
                slotsArray.forEach(slot => {
                    this.slots.set(slot.slot_id, slot);
                });
                
                console.log('📥 État des créneaux chargé depuis localStorage');
                this.logStats();
                return true;
            }
        } catch (e) {
            console.error('❌ Erreur chargement créneaux:', e);
        }
        return false;
    }
    
    /**
     * Réinitialiser tous les créneaux
     */
    reset() {
        this.slots.forEach(slot => {
            slot.statut = 'libre';
            slot.match_id = null;
        });
        
        localStorage.removeItem('slotsState');
        console.log('🔄 Créneaux réinitialisés');
        this.logStats();
    }
}
