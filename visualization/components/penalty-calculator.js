/**
 * PyCalendar Pro - Calculateur de Pénalités
 * Reproduit la logique Python de calcul des pénalités pour permettre
 * le recalcul dynamique après chaque modification
 */

class PenaltyCalculator {
    /**
     * @param {Object} config - Configuration des pénalités
     */
    constructor(config = {}) {
        // Paramètres pour horaires préférés
        this.weight = config.weight || 10.0;
        this.penaltyBeforeOne = config.penaltyBeforeOne || 100.0;
        this.penaltyBeforeBoth = config.penaltyBeforeBoth || 300.0;
        this.divisor = config.divisor || 60.0;
        this.tolerance = config.tolerance || 0.0;
        
        // Paramètres pour espacement entre matchs
        this.penaltyList = config.penaltyList || [500, 100, 50, 30, 20, 10];
        this.minSpacing = config.minSpacing || 2; // jours minimum entre matchs
        
        console.log('🧮 PenaltyCalculator initialized:', {
            weight: this.weight,
            penaltyBeforeOne: this.penaltyBeforeOne,
            penaltyBeforeBoth: this.penaltyBeforeBoth,
            divisor: this.divisor,
            tolerance: this.tolerance,
            minSpacing: this.minSpacing
        });
    }
    
    /**
     * Convertit un horaire (format "14H30", "20H00") en minutes depuis minuit
     */
    _parseHoraire(horaire) {
        try {
            const cleaned = horaire.trim().toUpperCase().replace('H', ':');
            let timeStr = cleaned;
            if (!timeStr.includes(':')) {
                timeStr += ':00';
            }
            
            const parts = timeStr.split(':');
            const heures = parseInt(parts[0]);
            const minutes = parts.length > 1 ? parseInt(parts[1]) : 0;
            
            return heures * 60 + minutes;
        } catch (e) {
            console.warn('Error parsing horaire:', horaire, e);
            return 14 * 60; // Défaut 14h
        }
    }
    
    /**
     * Calcule la pénalité d'horaire préféré pour une équipe
     * Retourne [pénalité_distance, is_before]
     */
    _calculatePenaltyForEquipe(equipe, creaneauHoraire, equipeHorairesPreferes) {
        // Utiliser les horaires préférés fournis ou ceux de l'équipe
        const horairesPreferes = equipeHorairesPreferes || [];
        
        if (!horairesPreferes || horairesPreferes.length === 0) {
            return [0.0, false];
        }
        
        // Si le créneau correspond exactement à un horaire préféré
        if (horairesPreferes.includes(creaneauHoraire)) {
            return [0.0, false];
        }
        
        // Parser les horaires
        const horaireMatch = this._parseHoraire(creaneauHoraire);
        const horairePref = this._parseHoraire(horairesPreferes[0]); // Prendre le premier
        
        // Calculer la distance en minutes
        const distanceMinutes = Math.abs(horaireMatch - horairePref);
        
        // Vérifier la tolérance
        if (distanceMinutes <= this.tolerance) {
            return [0.0, false];
        }
        
        // Hors tolérance : distance totale
        const isBefore = horaireMatch < horairePref;
        
        return [distanceMinutes, isBefore];
    }
    
    /**
     * Calcule la pénalité d'horaire préféré pour un match
     */
    calculatePreferredTimePenalty(match) {
        const [distance1, isBefore1] = this._calculatePenaltyForEquipe(
            match.equipe1,
            match.horaire,
            match.equipe1_horaires_preferes || []
        );
        
        const [distance2, isBefore2] = this._calculatePenaltyForEquipe(
            match.equipe2,
            match.horaire,
            match.equipe2_horaires_preferes || []
        );
        
        // Si aucune distance, pas de pénalité
        if (distance1 === 0 && distance2 === 0) {
            return 0.0;
        }
        
        // Compter les équipes HORS tolérance qui jouent AVANT
        let nbEquipesAvantHorsTolerance = 0;
        if (distance1 > 0 && isBefore1) nbEquipesAvantHorsTolerance++;
        if (distance2 > 0 && isBefore2) nbEquipesAvantHorsTolerance++;
        
        // Déterminer le multiplicateur
        let multiplicateur;
        if (nbEquipesAvantHorsTolerance === 2) {
            multiplicateur = this.penaltyBeforeBoth;
        } else if (nbEquipesAvantHorsTolerance === 1) {
            multiplicateur = this.penaltyBeforeOne;
        } else {
            multiplicateur = this.weight;
        }
        
        // Calculer la pénalité totale
        let penalty = 0.0;
        if (distance1 > 0) {
            penalty += multiplicateur * Math.pow(distance1 / this.divisor, 2);
        }
        if (distance2 > 0) {
            penalty += multiplicateur * Math.pow(distance2 / this.divisor, 2);
        }
        
        return penalty;
    }
    
    /**
     * Calcule la pénalité d'espacement entre matchs pour une équipe
     */
    _calculateSpacingPenaltyForEquipe(equipe, weekOfMatch, allMatches) {
        let totalPenalty = 0.0;
        
        // Trouver tous les matchs de cette équipe
        const equipeMatches = allMatches.filter(m => 
            m.semaine && 
            (m.equipe1 === equipe || m.equipe2 === equipe)
        );
        
        // Pour chaque autre match de l'équipe
        for (const otherMatch of equipeMatches) {
            if (otherMatch.semaine === weekOfMatch) continue; // Même semaine, pas d'espacement
            
            const weekDiff = Math.abs(otherMatch.semaine - weekOfMatch);
            
            // Si espacement < minSpacing, appliquer pénalité
            if (weekDiff < this.minSpacing) {
                // weekDiff = 1 → index 0 (penaltyList[0] = 500)
                const penaltyIndex = weekDiff - 1;
                if (penaltyIndex >= 0 && penaltyIndex < this.penaltyList.length) {
                    totalPenalty += this.penaltyList[penaltyIndex];
                }
            }
        }
        
        return totalPenalty;
    }
    
    /**
     * Calcule la pénalité d'espacement pour un match
     */
    calculateSpacingPenalty(match, allMatches) {
        if (!match.semaine) return 0.0;
        
        const penalty1 = this._calculateSpacingPenaltyForEquipe(
            match.equipe1,
            match.semaine,
            allMatches
        );
        
        const penalty2 = this._calculateSpacingPenaltyForEquipe(
            match.equipe2,
            match.semaine,
            allMatches
        );
        
        // Retourner le maximum des deux (une seule pénalité par match)
        return Math.max(penalty1, penalty2);
    }
    
    /**
     * Calcule la pénalité totale pour un match
     */
    calculateTotalPenalty(match, allMatches) {
        // Si match non planifié, pénalité nulle (ou utiliser une pénalité spécifique)
        if (!match.semaine || !match.horaire || !match.gymnase) {
            return 0.0;
        }
        
        const preferredTimePenalty = this.calculatePreferredTimePenalty(match);
        const spacingPenalty = this.calculateSpacingPenalty(match, allMatches);
        
        const totalPenalty = preferredTimePenalty + spacingPenalty;
        
        return totalPenalty;
    }
    
    /**
     * Recalcule les pénalités pour tous les matchs
     */
    recalculateAllPenalties(matches) {
        console.log('🔄 Recalculating penalties for', matches.length, 'matches...');
        
        const updatedMatches = matches.map(match => {
            const penalty = this.calculateTotalPenalty(match, matches);
            
            return {
                ...match,
                penalty: penalty
            };
        });
        
        // Statistiques
        const totalPenalty = updatedMatches.reduce((sum, m) => sum + (m.penalty || 0), 0);
        const avgPenalty = totalPenalty / updatedMatches.length;
        const maxPenalty = Math.max(...updatedMatches.map(m => m.penalty || 0));
        const matchesWithPenalty = updatedMatches.filter(m => (m.penalty || 0) > 0).length;
        
        console.log('✅ Penalties recalculated:', {
            total: totalPenalty.toFixed(1),
            average: avgPenalty.toFixed(1),
            max: maxPenalty.toFixed(1),
            withPenalty: matchesWithPenalty
        });
        
        return updatedMatches;
    }
    
    /**
     * Obtenir les statistiques de pénalités
     */
    getPenaltyStats(matches) {
        const totalPenalty = matches.reduce((sum, m) => sum + (m.penalty || 0), 0);
        const avgPenalty = totalPenalty / matches.length;
        const maxPenalty = Math.max(...matches.map(m => m.penalty || 0));
        const matchesWithPenalty = matches.filter(m => (m.penalty || 0) > 0).length;
        
        return {
            total: totalPenalty,
            average: avgPenalty,
            max: maxPenalty,
            withPenalty: matchesWithPenalty,
            percentage: (matchesWithPenalty / matches.length * 100).toFixed(1)
        };
    }
}

// Export pour utilisation
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PenaltyCalculator;
}
