#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ajouter la méthode saveModification à EditModal dans le HTML"""

# Lire le fichier
with open('calendrier_volley_FIXED.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Trouver où insérer la nouvelle méthode (juste avant saveModifications)
old_savemodifications = '''    /**
     * Save modifications to localStorage
     */
    saveModifications() {'''

new_code_with_both_methods = '''    /**
     * Save a single modification (called from drag-and-drop)
     * @param {Object} modification - Modification object with match_id, original, new
     */
    saveModification(modification) {
        console.log('📝 EditModal.saveModification called with:', modification);
        
        const matchId = modification.match_id;
        
        this.modifications[matchId] = {
            original: modification.original,
            new: modification.new,
            timestamp: new Date().toISOString(),
            teams: modification.teams || 'Unknown'
        };
        
        this.saveModifications();
        this.updateMatchCardUI(matchId, true);
        
        console.log('✅ Modification saved for', matchId);
    }

    /**
     * Save modifications to localStorage
     */
    saveModifications() {'''

# Remplacer
content = content.replace(old_savemodifications, new_code_with_both_methods)

# Écrire la version FINALE
with open('calendrier_volley_FINAL.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Version FINAL créée avec saveModification() ajoutée à EditModal")
print("   La méthode saveModification() (singulier) est maintenant disponible")
