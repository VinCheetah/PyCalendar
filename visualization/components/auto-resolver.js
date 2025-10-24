/**
 * Auto-Resolver - Résolution automatique des conflits
 * Suggère des échanges intelligents pour résoudre les conflits
 */

class AutoResolver {
    constructor(conflictDetector) {
        this.conflictDetector = conflictDetector;
        this.suggestions = [];
    }

    /**
     * Génère des suggestions pour résoudre tous les conflits
     * @param {Array} matches - Liste de tous les matchs
     * @param {Array} availableSlots - Créneaux disponibles
     * @returns {Array} - Liste de suggestions
     */
    generateSuggestions(matches, availableSlots = []) {
        console.log('🤖 Génération de suggestions de résolution...');
        this.suggestions = [];
        
        const conflicts = this.conflictDetector.getConflictSummary();
        console.log('📊 Conflits à résoudre:', conflicts);
        
        // Traiter d'abord les conflits critiques
        const criticalConflicts = conflicts.details.filter(c => c.severity === 'critical');
        
        criticalConflicts.forEach(conflict => {
            const suggestions = this.resolveSingleConflict(conflict, matches, availableSlots);
            if (suggestions.length > 0) {
                this.suggestions.push(...suggestions);
            }
        });
        
        // Dédupliquer et trier par score
        this.suggestions = this.deduplicateAndScore(this.suggestions);
        
        console.log('✅', this.suggestions.length, 'suggestions générées');
        return this.suggestions;
    }

    /**
     * Résout un conflit spécifique
     */
    resolveSingleConflict(conflict, matches, availableSlots) {
        switch (conflict.type) {
            case 'double_booking':
                return this.resolveDoubleBooking(conflict, matches, availableSlots);
            case 'team_overlap':
                return this.resolveTeamOverlap(conflict, matches, availableSlots);
            case 'rest_time':
                return this.resolveRestTime(conflict, matches, availableSlots);
            default:
                return [];
        }
    }

    /**
     * Résout un conflit de double réservation
     */
    resolveDoubleBooking(conflict, matches, availableSlots) {
        const suggestions = [];
        const match = matches.find(m => m.match_id === conflict.matchId);
        const conflictingMatch = matches.find(m => m.match_id === conflict.conflictingMatch);
        
        if (!match || !conflictingMatch) return [];
        
        // Option 1: Déplacer le match vers un créneau disponible
        const freeSlots = this.findFreeSlotsForMatch(match, availableSlots, matches);
        freeSlots.slice(0, 3).forEach(slot => { // Top 3 créneaux
            suggestions.push({
                type: 'move',
                priority: this.calculatePriority(match, slot),
                description: `Déplacer ${this.formatMatch(match)} vers ${slot.gymnase} à ${slot.horaire}`,
                action: {
                    type: 'move',
                    matchId: match.match_id,
                    from: {
                        week: match.semaine,
                        time: match.horaire,
                        venue: match.gymnase
                    },
                    to: {
                        week: slot.semaine,
                        time: slot.horaire,
                        venue: slot.gymnase
                    }
                },
                impact: {
                    resolves: [conflict.matchId],
                    creates: [] // Vérifier plus tard
                }
            });
        });
        
        // Option 2: Échanger avec un autre match
        const swapCandidates = this.findSwapCandidates(match, conflictingMatch, matches);
        swapCandidates.slice(0, 2).forEach(candidate => {
            suggestions.push({
                type: 'swap',
                priority: candidate.score,
                description: `Échanger ${this.formatMatch(match)} avec ${this.formatMatch(candidate.match)}`,
                action: {
                    type: 'swap',
                    match1: match.match_id,
                    match2: candidate.match.match_id,
                    slots: [
                        { week: match.semaine, time: match.horaire, venue: match.gymnase },
                        { week: candidate.match.semaine, time: candidate.match.horaire, venue: candidate.match.gymnase }
                    ]
                },
                impact: {
                    resolves: [conflict.matchId, conflict.conflictingMatch],
                    creates: []
                }
            });
        });
        
        return suggestions;
    }

    /**
     * Résout un conflit d'équipe jouant 2 fois en même temps
     */
    resolveTeamOverlap(conflict, matches, availableSlots) {
        const suggestions = [];
        const match = matches.find(m => m.match_id === conflict.matchId);
        
        if (!match) return [];
        
        // Trouver des créneaux différents pour l'un des matchs
        const freeSlots = this.findFreeSlotsForMatch(match, availableSlots, matches);
        freeSlots.slice(0, 3).forEach(slot => {
            if (slot.horaire !== match.horaire) { // Horaire différent
                suggestions.push({
                    type: 'move',
                    priority: this.calculatePriority(match, slot) + 10, // Priorité haute
                    description: `Déplacer ${this.formatMatch(match)} vers ${slot.horaire} (${slot.gymnase})`,
                    action: {
                        type: 'move',
                        matchId: match.match_id,
                        from: {
                            week: match.semaine,
                            time: match.horaire,
                            venue: match.gymnase
                        },
                        to: {
                            week: slot.semaine,
                            time: slot.horaire,
                            venue: slot.gymnase
                        }
                    },
                    impact: {
                        resolves: [conflict.matchId],
                        creates: []
                    }
                });
            }
        });
        
        return suggestions;
    }

    /**
     * Résout un problème de temps de repos
     */
    resolveRestTime(conflict, matches, availableSlots) {
        const suggestions = [];
        const match = matches.find(m => m.match_id === conflict.matchId);
        
        if (!match) return [];
        
        // Trouver des créneaux avec repos suffisant
        const freeSlots = this.findFreeSlotsForMatch(match, availableSlots, matches);
        const minRestMinutes = conflict.details.requiredMinutes;
        
        freeSlots.forEach(slot => {
            const restTime = this.calculateRestTime(match, slot, matches);
            if (restTime >= minRestMinutes) {
                suggestions.push({
                    type: 'move',
                    priority: this.calculatePriority(match, slot),
                    description: `Déplacer ${this.formatMatch(match)} pour ${restTime}min de repos`,
                    action: {
                        type: 'move',
                        matchId: match.match_id,
                        from: {
                            week: match.semaine,
                            time: match.horaire,
                            venue: match.gymnase
                        },
                        to: {
                            week: slot.semaine,
                            time: slot.horaire,
                            venue: slot.gymnase
                        }
                    },
                    impact: {
                        resolves: [conflict.matchId],
                        creates: []
                    }
                });
            }
        });
        
        return suggestions.slice(0, 3);
    }

    /**
     * Trouve les créneaux libres pour un match
     */
    findFreeSlotsForMatch(match, availableSlots, allMatches) {
        const teams = this.extractTeams(match);
        const freeSlots = [];
        
        availableSlots.forEach(slot => {
            // Vérifier que le créneau est vraiment libre
            const isOccupied = allMatches.some(m => 
                m.semaine === slot.semaine && 
                m.horaire === slot.horaire && 
                m.gymnase === slot.gymnase
            );
            
            if (!isOccupied) {
                freeSlots.push({
                    ...slot,
                    score: this.scoreSlot(match, slot)
                });
            }
        });
        
        // Trier par score (meilleur en premier)
        return freeSlots.sort((a, b) => b.score - a.score);
    }

    /**
     * Trouve des candidats pour un échange
     */
    findSwapCandidates(match1, match2, allMatches) {
        const candidates = [];
        
        allMatches.forEach(candidate => {
            if (candidate.match_id !== match1.match_id && 
                candidate.match_id !== match2.match_id) {
                const score = this.scoreSwap(match1, candidate);
                if (score > 0) {
                    candidates.push({ match: candidate, score });
                }
            }
        });
        
        return candidates.sort((a, b) => b.score - a.score);
    }

    /**
     * Calcule un score pour un créneau
     */
    scoreSlot(match, slot) {
        let score = 100;
        
        // Même semaine: +50
        if (slot.semaine === match.semaine) score += 50;
        
        // Même jour de semaine: +30
        // (on pourrait extraire le jour si disponible)
        
        // Horaire proche: +20
        const timeDiff = this.calculateTimeDifference(match.horaire, slot.horaire);
        if (timeDiff < 120) score += 20; // Moins de 2h de différence
        
        // Même gymnase: +40
        if (slot.gymnase === match.gymnase) score += 40;
        
        return score;
    }

    /**
     * Calcule un score pour un échange
     */
    scoreSwap(match1, match2) {
        let score = 50;
        
        // Même semaine: +30
        if (match1.semaine === match2.semaine) score += 30;
        
        // Pas d'équipes communes: +40
        const teams1 = this.extractTeams(match1);
        const teams2 = this.extractTeams(match2);
        const hasCommonTeam = teams1.some(t => teams2.includes(t));
        if (!hasCommonTeam) score += 40;
        
        return score;
    }

    /**
     * Calcule la priorité d'une suggestion
     */
    calculatePriority(match, slot) {
        return this.scoreSlot(match, slot);
    }

    /**
     * Calcule le temps de repos si on déplace un match
     */
    calculateRestTime(match, slot, allMatches) {
        const teams = this.extractTeams(match);
        let minRest = Infinity;
        
        teams.forEach(team => {
            const teamMatches = allMatches.filter(m => {
                const mTeams = this.extractTeams(m);
                return m.match_id !== match.match_id && mTeams.includes(team);
            });
            
            teamMatches.forEach(m => {
                if (m.semaine === slot.semaine) {
                    const rest = this.calculateTimeDifference(m.horaire, slot.horaire);
                    minRest = Math.min(minRest, rest);
                }
            });
        });
        
        return minRest === Infinity ? 999 : minRest;
    }

    /**
     * Déduplique et score les suggestions
     */
    deduplicateAndScore(suggestions) {
        const seen = new Set();
        const unique = [];
        
        suggestions.forEach(sug => {
            const key = JSON.stringify(sug.action);
            if (!seen.has(key)) {
                seen.add(key);
                unique.push(sug);
            }
        });
        
        return unique.sort((a, b) => b.priority - a.priority);
    }

    /**
     * Extrait les équipes d'un match (avec genre si disponible)
     */
    extractTeams(match) {
        return this.conflictDetector.extractTeamsWithGender(match);
    }

    /**
     * Calcule la différence de temps
     */
    calculateTimeDifference(time1, time2) {
        return this.conflictDetector.calculateTimeDifference(time1, time2);
    }

    /**
     * Formate un match pour l'affichage
     */
    formatMatch(match) {
        const teams = this.conflictDetector.extractTeams(match); // Sans genre pour affichage
        return teams.length > 0 ? teams.join(' vs ') : match.match_id;
    }

    /**
     * Applique une suggestion
     */
    applySuggestion(suggestion, matches) {
        const { action } = suggestion;
        
        if (action.type === 'move') {
            const match = matches.find(m => m.match_id === action.matchId);
            if (match) {
                match.semaine = action.to.week;
                match.horaire = action.to.time;
                match.gymnase = action.to.venue;
                console.log('✅ Match déplacé:', action.matchId);
                return true;
            }
        } else if (action.type === 'swap') {
            const match1 = matches.find(m => m.match_id === action.match1);
            const match2 = matches.find(m => m.match_id === action.match2);
            
            if (match1 && match2) {
                // Échanger les créneaux
                const temp = {
                    semaine: match1.semaine,
                    horaire: match1.horaire,
                    gymnase: match1.gymnase
                };
                
                match1.semaine = match2.semaine;
                match1.horaire = match2.horaire;
                match1.gymnase = match2.gymnase;
                
                match2.semaine = temp.semaine;
                match2.horaire = temp.horaire;
                match2.gymnase = temp.gymnase;
                
                console.log('✅ Matchs échangés:', action.match1, '<->', action.match2);
                return true;
            }
        }
        
        return false;
    }

    /**
     * Récupère les meilleures suggestions
     */
    getTopSuggestions(count = 5) {
        return this.suggestions.slice(0, count);
    }
}
