/**
 * SlotManager - Gestion des créneaux et organisation des matchs
 * 
 * Responsabilités:
 * - Organiser les matchs par créneau horaire
 * - Détecter les superpositions et conflits
 * - Optimiser l'affichage côte à côte des matchs simultanés
 */

class SlotManager {
    constructor(capacity = 1) {
        this.capacity = capacity; // Capacité du gymnase (nombre de terrains)
    }
    
    /**
     * Organise les matchs d'un créneau pour un affichage optimal côte à côte
     * IMPORTANT: Organisation HORIZONTALE uniquement (pas de grille verticale)
     * @param {Array} matches - Liste des matchs au même horaire
     * @param {number} capacity - Capacité du gymnase
     * @returns {Object} - Structure d'affichage optimisée
     */
    organizeSlotMatches(matches, capacity) {
        if (!matches || matches.length === 0) {
            return {
                isEmpty: true,
                matchCount: 0,
                layout: 'horizontal',
                matches: [],
                conflicts: {
                    hasConflict: false,
                    severity: 'none',
                    types: [],
                    details: []
                }
            };
        }
        
        const matchCount = matches.length;
        
        // TOUJOURS en ligne horizontale (côte à côte)
        // Pas de grille 2x2, 2x3, etc.
        const layout = 'horizontal';
        const columns = matchCount; // Autant de colonnes que de matchs
        const isOverCapacity = matchCount > capacity;
        
        // Détecter les conflits
        const conflicts = this.detectConflicts(matches, capacity);
        
        return {
            isEmpty: false,
            matchCount,
            capacity,
            isOverCapacity,
            layout,
            columns,
            rows: 1, // Toujours 1 seule ligne
            matches: this.sortMatchesForDisplay(matches),
            conflicts: conflicts
        };
    }
    
    /**
     * Trie les matchs pour un affichage optimal
     * Priorité: matchs fixes > horaire > institution
     */
    sortMatchesForDisplay(matches) {
        return [...matches].sort((a, b) => {
            // 1. Matchs fixes en premier
            if (a.is_fixed && !b.is_fixed) return -1;
            if (!a.is_fixed && b.is_fixed) return 1;
            
            // 2. Par institution (pour regrouper visuellement)
            const instCompare = (a.equipe1_institution || '').localeCompare(b.equipe1_institution || '');
            if (instCompare !== 0) return instCompare;
            
            // 3. Par nom d'équipe
            return (a.equipe1_nom || '').localeCompare(b.equipe1_nom || '');
        });
    }
    
    /**
     * Calcule la hauteur optimale d'un slot selon le nombre de matchs
     * HAUTEUR FIXE pour maintenir l'échelle horaire
     * @param {number} matchCount - Nombre de matchs
     * @param {number} baseHeight - Hauteur de base (120px pour 2h)
     * @returns {number} - Hauteur en pixels (toujours la même)
     */
    calculateSlotHeight(matchCount, baseHeight = 120) {
        // HAUTEUR FIXE : toujours la même quelle que soit le nombre de matchs
        // Les matchs sont côte à côte horizontalement, pas empilés verticalement
        return baseHeight;
    }
    
    /**
     * Détecte les conflits dans un slot
     * @param {Array} matches - Matchs du slot
     * @param {number} capacity - Capacité du lieu
     * @returns {Object} - Informations sur les conflits
     */
    detectConflicts(matches, capacity) {
        const conflicts = {
            hasConflict: false,
            severity: 'none', // 'none', 'warning', 'critical'
            types: [],
            details: []
        };
        
        if (matches.length === 0) return conflicts;
        
        // 1. Vérifier la capacité
        if (matches.length > capacity) {
            conflicts.hasConflict = true;
            conflicts.severity = 'critical';
            conflicts.types.push('over_capacity');
            conflicts.details.push({
                type: 'over_capacity',
                message: `${matches.length} matchs pour ${capacity} terrain(s)`,
                icon: '🏟️'
            });
        }
        
        // 2. Vérifier les doublons d'équipes
        const teamOccurrences = new Map();
        matches.forEach((match, idx) => {
            [match.equipe1_id, match.equipe2_id].forEach(teamId => {
                if (!teamOccurrences.has(teamId)) {
                    teamOccurrences.set(teamId, []);
                }
                teamOccurrences.get(teamId).push(idx);
            });
        });
        
        const duplicateTeams = [];
        teamOccurrences.forEach((occurrences, teamId) => {
            if (occurrences.length > 1) {
                const teamName = matches[occurrences[0]].equipe1_id === teamId 
                    ? matches[occurrences[0]].equipe1_nom 
                    : matches[occurrences[0]].equipe2_nom;
                duplicateTeams.push(teamName);
            }
        });
        
        if (duplicateTeams.length > 0) {
            conflicts.hasConflict = true;
            conflicts.severity = 'critical';
            conflicts.types.push('team_duplicate');
            conflicts.details.push({
                type: 'team_duplicate',
                message: `Équipe(s) en double: ${duplicateTeams.join(', ')}`,
                icon: '⚠️'
            });
        }
        
        // 3. Vérifier les overlaps d'institutions (warning seulement)
        const institutionCount = new Map();
        matches.forEach(match => {
            [match.equipe1_institution, match.equipe2_institution].forEach(inst => {
                if (inst) {
                    institutionCount.set(inst, (institutionCount.get(inst) || 0) + 1);
                }
            });
        });
        
        const overlappingInstitutions = [];
        institutionCount.forEach((count, inst) => {
            if (count > 2) { // Plus de 2 fois = potentiel problème logistique
                overlappingInstitutions.push(`${inst} (${count}×)`);
            }
        });
        
        if (overlappingInstitutions.length > 0 && conflicts.severity === 'none') {
            conflicts.hasConflict = true;
            conflicts.severity = 'warning';
            conflicts.types.push('institution_overlap');
            conflicts.details.push({
                type: 'institution_overlap',
                message: `Institutions multiples: ${overlappingInstitutions.join(', ')}`,
                icon: 'ℹ️'
            });
        }
        
        return conflicts;
    }
    
    /**
     * Génère les statistiques d'un slot
     */
    getSlotStats(matches) {
        const stats = {
            total: matches.length,
            fixed: 0,
            external: 0,
            ententes: 0,
            withPenalties: 0,
            totalPenalty: 0
        };
        
        matches.forEach(match => {
            if (match.is_fixed) stats.fixed++;
            if (match.is_external) stats.external++;
            if (match.is_entente) stats.ententes++;
            if (match.penalties && match.penalties.total > 0) {
                stats.withPenalties++;
                stats.totalPenalty += match.penalties.total;
            }
        });
        
        stats.avgPenalty = stats.total > 0 ? stats.totalPenalty / stats.total : 0;
        
        return stats;
    }
}

// Export pour utilisation dans d'autres modules
if (typeof window !== 'undefined') {
    window.SlotManager = SlotManager;
}
