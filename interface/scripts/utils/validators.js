/**
 * validators.js - Utilitaires de validation
 * 
 * Fonctions pour valider les données, contraintes, etc.
 * Exposé globalement via window.Validators
 */

window.Validators = {
    /**
     * Valide qu'un match a tous les champs requis
     */
    validateMatch(match) {
        const errors = [];
        
        if (!match) {
            return { valid: false, errors: ['Match vide'] };
        }
        
        if (!match.match_id) errors.push('ID manquant');
        if (!match.equipes || match.equipes.length !== 2) {
            errors.push('Deux équipes requises');
        }
        
        return {
            valid: errors.length === 0,
            errors
        };
    },

    /**
     * Valide qu'un créneau a tous les champs requis
     */
    validateSlot(slot) {
        const errors = [];
        
        if (!slot) {
            return { valid: false, errors: ['Créneau vide'] };
        }
        
        if (slot.semaine !== null && slot.semaine !== undefined) {
            if (!slot.horaire) errors.push('Horaire manquant');
            if (!slot.gymnase) errors.push('Gymnase manquant');
        }
        
        return {
            valid: errors.length === 0,
            errors
        };
    },

    /**
     * Valide un format d'horaire (HH:MM)
     */
    isValidTime(time) {
        if (!time) return false;
        
        const timeRegex = /^([0-1][0-9]|2[0-3]):([0-5][0-9])$/;
        return timeRegex.test(time);
    },

    /**
     * Valide un numéro de semaine
     */
    isValidWeek(week, maxWeek = 52) {
        if (week === null || week === undefined) return true;
        
        return Number.isInteger(week) && week >= 1 && week <= maxWeek;
    },

    /**
     * Valide qu'un ID d'équipe existe dans les données
     */
    isValidEquipe(equipeId, equipes) {
        if (!equipeId || !equipes) return false;
        
        return equipes.some(e => e.id === equipeId);
    },

    /**
     * Valide qu'un ID de gymnase existe dans les données
     */
    isValidGymnase(gymnaseId, gymnases) {
        if (!gymnaseId || !gymnases) return false;
        
        return gymnases.some(g => g.id === gymnaseId);
    },

    /**
     * Valide une modification avant de l'appliquer
     */
    validateModification(modification, context) {
        const errors = [];
        
        if (!modification) {
            return { valid: false, errors: ['Modification vide'] };
        }
        
        if (!modification.match_id) {
            errors.push('ID du match manquant');
        }
        
        if (!modification.new) {
            errors.push('Nouveau créneau manquant');
        } else {
            const newSlot = modification.new;
            
            if (newSlot.semaine !== null && newSlot.semaine !== undefined) {
                if (!this.isValidTime(newSlot.horaire)) {
                    errors.push('Horaire invalide (format HH:MM attendu)');
                }
                
                if (!this.isValidWeek(newSlot.semaine)) {
                    errors.push('Semaine invalide');
                }
                
                if (context?.gymnases && !this.isValidGymnase(newSlot.gymnase, context.gymnases)) {
                    errors.push('Gymnase invalide ou inexistant');
                }
            }
        }
        
        return {
            valid: errors.length === 0,
            errors
        };
    },

    /**
     * Vérifie si deux équipes peuvent jouer ensemble
     */
    canTeamsPlay(equipe1, equipe2) {
        if (!equipe1 || !equipe2) return false;
        
        if (equipe1.id === equipe2.id) return false;
        
        if (equipe1.genre !== equipe2.genre) return false;
        
        return true;
    },

    /**
     * Vérifie si un créneau est disponible (pas de conflit)
     */
    isSlotAvailable(slot, matches, excludeMatchId = null) {
        if (!slot || !matches) return false;
        
        const { semaine, horaire, gymnase } = slot;
        
        if (semaine === null || semaine === undefined) return true;
        
        const conflict = matches.find(match => {
            if (excludeMatchId && match.match_id === excludeMatchId) {
                return false;
            }
            
            return match.semaine === semaine &&
                   match.horaire === horaire &&
                   match.gymnase === gymnase;
        });
        
        return !conflict;
    },

    /**
     * Vérifie si une équipe a déjà un match dans ce créneau
     */
    hasTeamConflict(equipeId, slot, matches, excludeMatchId = null) {
        if (!equipeId || !slot || !matches) return false;
        
        const { semaine, horaire } = slot;
        
        if (semaine === null || semaine === undefined) return false;
        
        const conflict = matches.find(match => {
            if (excludeMatchId && match.match_id === excludeMatchId) {
                return false;
            }
            
            // Format v2.0: les IDs d'équipe sont dans equipe1_id et equipe2_id
            return match.semaine === semaine &&
                   match.horaire === horaire &&
                   (match.equipe1_id === equipeId || match.equipe2_id === equipeId);
        });
        
        return !!conflict;
    },

    /**
     * Calcule le score de validité d'une affectation (0-100)
     */
    calculateAssignmentScore(match, context = {}) {
        let score = 100;
        
        if (!match || !match.penalties) return score;
        
        const penalties = match.penalties;
        
        Object.values(penalties).forEach(penalty => {
            if (typeof penalty === 'number') {
                score -= penalty;
            }
        });
        
        return Math.max(0, score);
    },

    /**
     * Valide un export JSON de modifications
     */
    validateExport(exportData) {
        const errors = [];
        
        if (!exportData) {
            return { valid: false, errors: ['Export vide'] };
        }
        
        if (!exportData.export_version) {
            errors.push('Version d\'export manquante');
        }
        
        if (!exportData.metadata) {
            errors.push('Métadonnées manquantes');
        } else {
            if (!exportData.metadata.export_date) {
                errors.push('Date d\'export manquante');
            }
        }
        
        if (!exportData.modifications || !Array.isArray(exportData.modifications)) {
            errors.push('Liste de modifications manquante ou invalide');
        }
        
        return {
            valid: errors.length === 0,
            errors
        };
    }
};
