#!/usr/bin/env python3
"""
Refactorisation du système de créneaux pour PyCalendar.

OBJECTIF:
- Générer TOUS les créneaux possibles (gymnase × horaire × semaine)
- Chaque créneau a un statut: libre/occupé et l'ID du match si occupé
- Quand un match bouge en JS, libérer l'ancien créneau et occuper le nouveau
"""

import sys
from pathlib import Path

# Lire le fichier Python actuel
transformers_path = Path("data/transformers.py")
visualizer_path = Path("visualization/html_visualizer_v2.py")

print("🔧 Refactorisation du système de créneaux")
print("=" * 60)

# ==================== 1. Modifier data/transformers.py ====================
print("\n1️⃣ Modification de data/transformers.py")
print("-" * 60)

with open(transformers_path, 'r', encoding='utf-8') as f:
    transformers_content = f.read()

# Nouvelle méthode pour générer TOUS les créneaux
new_generer_creneaux = '''    @staticmethod
    def generer_creneaux(gymnases: List[Gymnase], nb_semaines: int) -> List[Creneau]:
        """Generate ALL possible time slots (occupied or not).
        
        Changes from previous version:
        - Generates ALL slots (gymnase × horaire × semaine)
        - Doesn't filter by availability yet (done when assigning matches)
        - Each slot is unique: (semaine, horaire, gymnase)
        
        Returns:
            List of ALL possible time slots
        """
        creneaux = []
        
        for semaine in range(1, nb_semaines + 1):
            for gymnase in gymnases:
                for horaire in gymnase.horaires_disponibles:
                    # Create slot for EVERY combination
                    # Availability check happens during match assignment
                    creneau = Creneau(
                        semaine=semaine,
                        horaire=horaire,
                        gymnase=gymnase.nom
                    )
                    creneaux.append(creneau)
        
        return creneaux'''

# Remplacer l'ancienne méthode
old_method_start = transformers_content.find("    @staticmethod\n    def generer_creneaux")
old_method_end = transformers_content.find("        return creneaux", old_method_start) + len("        return creneaux")

if old_method_start != -1:
    transformers_content = (
        transformers_content[:old_method_start] + 
        new_generer_creneaux + 
        transformers_content[old_method_end:]
    )
    
    with open(transformers_path, 'w', encoding='utf-8') as f:
        f.write(transformers_content)
    
    print("✅ generer_creneaux() mis à jour - génère TOUS les créneaux possibles")
else:
    print("❌ Impossible de trouver la méthode generer_creneaux")
    sys.exit(1)

# ==================== 2. Modifier visualization/html_visualizer_v2.py ====================
print("\n2️⃣ Modification de visualization/html_visualizer_v2.py")
print("-" * 60)

with open(visualizer_path, 'r', encoding='utf-8') as f:
    visualizer_content = f.read()

# Nouvelle méthode pour préparer les créneaux avec statut
new_prepare_slots = '''    @staticmethod
    def _prepare_available_slots_data(slots: List[Creneau], matches: List[Match]) -> List[Dict]:
        """Prépare les données de TOUS les créneaux avec leur statut.
        
        Changement majeur:
        - Génère TOUS les créneaux (occupés et libres)
        - Chaque créneau a: semaine, horaire, gymnase, statut, match_id
        - statut = 'libre' ou 'occupé'
        - match_id = ID du match si occupé, null sinon
        
        Args:
            slots: Tous les créneaux possibles (générés par generer_creneaux)
            matches: Matchs planifiés
            
        Returns:
            Liste de créneaux avec leur statut d'occupation
        """
        # Créer un index des créneaux occupés
        occupied_slots = {}
        for match in matches:
            if match.creneau:
                key = f"{match.creneau.semaine}_{match.creneau.horaire}_{match.creneau.gymnase}"
                occupied_slots[key] = match.match_id
        
        # Préparer tous les créneaux avec statut
        data = []
        for slot in slots:
            key = f"{slot.semaine}_{slot.horaire}_{slot.gymnase}"
            
            slot_data = {
                'semaine': slot.semaine,
                'horaire': slot.horaire,
                'gymnase': slot.gymnase,
                'statut': 'occupé' if key in occupied_slots else 'libre',
                'match_id': occupied_slots.get(key, None),
                'slot_id': key  # ID unique du créneau
            }
            data.append(slot_data)
        
        return data'''

# Remplacer l'ancienne méthode _prepare_available_slots_data
old_prepare_start = visualizer_content.find("    @staticmethod\n    def _prepare_available_slots_data")
old_prepare_end = visualizer_content.find("        return data", old_prepare_start) + len("        return data")

if old_prepare_start != -1:
    visualizer_content = (
        visualizer_content[:old_prepare_start] + 
        new_prepare_slots + 
        visualizer_content[old_prepare_end:]
    )
    
    # Mettre à jour l'appel avec le bon nombre d'arguments
    old_call = "available_slots_data = HTMLVisualizerV2._prepare_available_slots_data(\n            solution.metadata.get('creneaux_disponibles', [])\n        )"
    new_call = "available_slots_data = HTMLVisualizerV2._prepare_available_slots_data(\n            solution.metadata.get('creneaux_disponibles', []),\n            solution.matchs_planifies\n        )"
    
    visualizer_content = visualizer_content.replace(old_call, new_call)
    
    with open(visualizer_path, 'w', encoding='utf-8') as f:
        f.write(visualizer_content)
    
    print("✅ _prepare_available_slots_data() mis à jour - statut libre/occupé")
else:
    print("❌ Impossible de trouver _prepare_available_slots_data")
    sys.exit(1)

# ==================== 3. Modifier orchestrator/pipeline.py ====================
print("\n3️⃣ Modification de orchestrator/pipeline.py")
print("-" * 60)

pipeline_path = Path("orchestrator/pipeline.py")
with open(pipeline_path, 'r', encoding='utf-8') as f:
    pipeline_content = f.read()

# Remplacer la logique de calcul des créneaux restants
old_creneaux_logic = """        # Calculer les créneaux restants pour passer au visualizer
        creneaux_utilises = {(m.creneau.gymnase, m.creneau.semaine, m.creneau.horaire) 
                            for m in solution.matchs_planifies if m.creneau}
        
        # Récupérer tous les créneaux depuis les données
        gymnases = self.source.charger_gymnases()
        tous_creneaux = DataTransformer.generer_creneaux(gymnases, self.config.nb_semaines, self.config.calendar_manager)
        creneaux_restants = [c for c in tous_creneaux 
                            if (c.gymnase, c.semaine, c.horaire) not in creneaux_utilises]
        
        # Stocker dans metadata de la solution
        solution.metadata['creneaux_disponibles'] = creneaux_restants"""

new_creneaux_logic = """        # Générer TOUS les créneaux possibles (occupés et libres)
        # Le visualizer gérera le statut libre/occupé
        gymnases = self.source.charger_gymnases()
        tous_creneaux = DataTransformer.generer_creneaux(gymnases, self.config.nb_semaines, self.config.calendar_manager)
        
        # Stocker TOUS les créneaux dans metadata (pas seulement les libres)
        solution.metadata['creneaux_disponibles'] = tous_creneaux"""

pipeline_content = pipeline_content.replace(old_creneaux_logic, new_creneaux_logic)

with open(pipeline_path, 'w', encoding='utf-8') as f:
    f.write(pipeline_content)

print("✅ Pipeline mis à jour - génère TOUS les créneaux")

# ==================== 4. Créer le nouveau gestionnaire de créneaux JS ====================
print("\n4️⃣ Création de visualization/components/slot-manager.js")
print("-" * 60)

slot_manager_js = '''/**
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
'''

slot_manager_path = Path("visualization/components/slot-manager.js")
with open(slot_manager_path, 'w', encoding='utf-8') as f:
    f.write(slot_manager_js)

print("✅ slot-manager.js créé")

# ==================== RÉSUMÉ ====================
print("\n" + "=" * 60)
print("🎉 REFACTORISATION TERMINÉE")
print("=" * 60)
print("""
✅ Modifications appliquées:

1. data/transformers.py
   → generer_creneaux() génère TOUS les créneaux possibles

2. visualization/html_visualizer_v2.py
   → _prepare_available_slots_data() ajoute statut libre/occupé
   → Chaque créneau a: slot_id, statut, match_id

3. orchestrator/pipeline.py
   → Génère TOUS les créneaux (plus seulement les libres)

4. visualization/components/slot-manager.js (NOUVEAU)
   → Gestion des créneaux avec statut
   → moveMatch() libère ancien + occupe nouveau
   → Synchronisation localStorage

📝 PROCHAINES ÉTAPES:

1. Ajouter slot-manager.js dans main.html
2. Intégrer avec edit-modal.js pour le drag & drop
3. Mettre à jour conflict-detector.js pour utiliser les créneaux
4. Regénérer le calendrier HTML

Commandes:
  python3 orchestrateur_poules.py configs/config_volley.yaml
""")
