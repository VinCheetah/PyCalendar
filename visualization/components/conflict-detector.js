/**
 * Conflict Detector - Détection de conflits en temps réel
 * Détecte les violations de contraintes et conflits dans le calendrier
 */

class ConflictDetector {
    constructor() {
        this.conflicts = new Map(); // matchId -> [conflicts]
        this.conflictTypes = {
            DOUBLE_BOOKING: 'double_booking',      // Même gymnase, même horaire (dépasse capacité)
            TEAM_OVERLAP: 'team_overlap',          // Même équipe joue 2 fois en même temps
            REST_TIME: 'rest_time',                // Temps de repos insuffisant entre matchs
            TIME_PREFERENCE: 'time_preference',    // Match avant horaires préférés des équipes
            VENUE_CONSTRAINT: 'venue_constraint'   // Gymnase interdit pour cette équipe
        };
        
        this.minRestMinutes = 90; // Temps minimum entre 2 matchs de la même équipe
        
        // Capacités des gymnases (nombre de terrains)
        this.venueCapacities = {
            'DESCARTES': 1,
            'ECL': 1,
            'ESA': 1,
            'LYON 2 HC': 3,
            'LAENNEC': 3,
            'BESSON': 3,
            'L. J. HAUT': 1
        };
    }
    
    /**
     * Met à jour les capacités des gymnases depuis les données
     */
    setVenueCapacities(capacities) {
        this.venueCapacities = capacities;
    }

    /**
     * Détecte tous les conflits dans un ensemble de matchs
     * @param {Array} matches - Liste des matchs
     * @returns {Map} - Map de matchId -> array de conflits
     */
    detectAllConflicts(matches) {
        console.log('🔍 Détection des conflits pour', matches.length, 'matchs...');
        this.conflicts.clear();
        
        // Index pour accès rapide
        const byWeekTimeVenue = this.indexMatches(matches);
        const byTeam = this.indexByTeam(matches);
        
        matches.forEach(match => {
            const matchConflicts = [];
            
            // 1. Détection double booking (dépasse capacité du gymnase)
            const doubleBooking = this.checkDoubleBooking(match, byWeekTimeVenue);
            if (doubleBooking.length > 0) {
                matchConflicts.push(...doubleBooking);
            }
            
            // 2. Détection équipe joue 2 fois en même temps
            const teamOverlap = this.checkTeamOverlap(match, byTeam);
            if (teamOverlap.length > 0) {
                matchConflicts.push(...teamOverlap);
            }
            
            // 3. Détection temps de repos insuffisant
            const restTime = this.checkRestTime(match, byTeam);
            if (restTime.length > 0) {
                matchConflicts.push(...restTime);
            }
            
            // 4. Détection violation des préférences horaires
            const timePreference = this.checkTimePreference(match);
            if (timePreference.length > 0) {
                matchConflicts.push(...timePreference);
            }
            
            if (matchConflicts.length > 0) {
                this.conflicts.set(match.match_id, matchConflicts);
            }
        });
        
        console.log('✅ Détection terminée:', this.conflicts.size, 'matchs avec conflits');
        return this.conflicts;
    }

    /**
     * Index les matchs par semaine/horaire/gymnase pour recherche rapide
     */
    indexMatches(matches) {
        const index = new Map();
        matches.forEach(match => {
            const key = `${match.semaine}_${match.horaire}_${match.gymnase}`;
            if (!index.has(key)) {
                index.set(key, []);
            }
            index.get(key).push(match);
        });
        return index;
    }

    /**
     * Index les matchs par équipe (avec genre)
     */
    indexByTeam(matches) {
        const index = new Map();
        matches.forEach(match => {
            const teams = this.extractTeamsWithGender(match);
            teams.forEach(team => {
                if (!index.has(team)) {
                    index.set(team, []);
                }
                index.get(team).push(match);
            });
        });
        return index;
    }

    /**
     * Extrait les noms d'équipes d'un match (sans genre, pour affichage)
     */
    extractTeams(match) {
        // Utiliser equipe1 et equipe2 si disponibles
        if (match.equipe1 && match.equipe2) {
            return [match.equipe1, match.equipe2];
        }
        
        if (match.equipes) {
            return match.equipes.split(' vs ').map(t => t.trim());
        }
        if (match.match_id) {
            // Format: "EQUIPE1_vs_EQUIPE2" ou "EQUIPE1|GENRE__EQUIPE2|GENRE__POULE"
            if (match.match_id.includes('__')) {
                const parts = match.match_id.split('__');
                if (parts.length >= 2) {
                    const team1 = parts[0].split('|')[0];
                    const team2 = parts[1].split('|')[0];
                    return [team1, team2];
                }
            }
            const parts = match.match_id.split('_vs_');
            if (parts.length === 2) {
                return parts.map(t => t.trim());
            }
        }
        return [];
    }

    /**
     * Extrait les équipes AVEC genre (pour détection de conflits)
     * Format retourné: "NOM_EQUIPE|GENRE" (ex: "INSA (1)|F", "LYON 1 (3)|M")
     */
    extractTeamsWithGender(match) {
        const teams = [];
        
        // Méthode principale: equipe1/equipe2 + equipe1_genre/equipe2_genre
        const genre1 = match.equipe1_genre || 'UNKNOWN';
        const genre2 = match.equipe2_genre || 'UNKNOWN';
        
        if (match.equipe1) {
            teams.push(`${match.equipe1}|${genre1}`);
        }
        
        if (match.equipe2) {
            teams.push(`${match.equipe2}|${genre2}`);
        }
        
        // Méthode 3: match_id avec format "EQUIPE|GENRE__EQUIPE|GENRE__POULE" (fallback)
        if (teams.length === 0 && match.match_id && match.match_id.includes('__')) {
            const parts = match.match_id.split('__');
            if (parts.length >= 2) {
                const team1Parts = parts[0].split('|');
                const team2Parts = parts[1].split('|');
                
                if (team1Parts.length >= 2 && team2Parts.length >= 2) {
                    return [
                        `${team1Parts[0]}|${team1Parts[1]}`,
                        `${team2Parts[0]}|${team2Parts[1]}`
                    ];
                }
            }
        }
        
        return teams;
    }

    /**
     * Vérifie les doubles réservations (dépasse la capacité du gymnase)
     */
    checkDoubleBooking(match, byWeekTimeVenue) {
        const key = `${match.semaine}_${match.horaire}_${match.gymnase}`;
        const sameSlot = byWeekTimeVenue.get(key) || [];
        
        // Capacité du gymnase (par défaut 1 terrain)
        const capacity = this.venueCapacities[match.gymnase] || 1;
        
        const conflicts = [];
        
        // Seulement signaler si le nombre de matchs dépasse la capacité
        if (sameSlot.length > capacity) {
            sameSlot.forEach(other => {
                if (other.match_id !== match.match_id) {
                    conflicts.push({
                        type: this.conflictTypes.DOUBLE_BOOKING,
                        severity: 'critical',
                        message: `Surcharge: ${match.gymnase} (${sameSlot.length} matchs, capacité ${capacity})`,
                        conflictingMatch: other.match_id,
                        details: {
                            venue: match.gymnase,
                            time: match.horaire,
                            week: match.semaine,
                            matchCount: sameSlot.length,
                            capacity: capacity
                        }
                    });
                }
            });
        }
        
        return conflicts;
    }

    /**
     * Vérifie si une équipe joue 2 fois en même temps
     */
    checkTeamOverlap(match, byTeam) {
        const teams = this.extractTeamsWithGender(match);
        const conflicts = [];
        
        teams.forEach(teamWithGender => {
            const teamMatches = byTeam.get(teamWithGender) || [];
            teamMatches.forEach(other => {
                if (other.match_id !== match.match_id && 
                    other.semaine === match.semaine && 
                    other.horaire === match.horaire) {
                    
                    // Extraire le nom sans le genre pour l'affichage
                    const teamName = teamWithGender.split('|')[0];
                    const genre = teamWithGender.split('|')[1];
                    
                    conflicts.push({
                        type: this.conflictTypes.TEAM_OVERLAP,
                        severity: 'critical',
                        message: `${teamName} (${genre}) joue 2 fois en même temps`,
                        conflictingMatch: other.match_id,
                        details: {
                            team: teamName,
                            gender: genre,
                            teamWithGender: teamWithGender,
                            time: match.horaire,
                            week: match.semaine,
                            venues: [match.gymnase, other.gymnase]
                        }
                    });
                }
            });
        });
        
        return conflicts;
    }

    /**
     * Vérifie le temps de repos entre matchs d'une équipe
     */
    checkRestTime(match, byTeam) {
        const teams = this.extractTeamsWithGender(match);
        const conflicts = [];

        // Parcourir chaque équipe concernée par le match
        teams.forEach(teamWithGender => {
            const teamMatches = byTeam.get(teamWithGender) || [];

            teamMatches.forEach(other => {
                // Ignorer le même match et ne comparer que les matchs de la même semaine
                if (other.match_id === match.match_id || other.semaine !== match.semaine) {
                    return;
                }

                // Les deux matchs doivent avoir un horaire valide
                if (!match.horaire || !other.horaire) {
                    return;
                }

                const timeDiff = this.calculateTimeDifference(match.horaire, other.horaire);
                if (timeDiff === null) {
                    return;
                }

                if (timeDiff > 0 && timeDiff < this.minRestMinutes) {
                    // Extraire le nom sans le genre pour l'affichage
                    const teamName = teamWithGender.split('|')[0];
                    const genre = teamWithGender.split('|')[1] || 'UNKNOWN';

                    conflicts.push({
                        type: this.conflictTypes.REST_TIME,
                        severity: 'warning',
                        message: `${teamName} (${genre}): seulement ${timeDiff}min entre 2 matchs (min ${this.minRestMinutes}min)`,
                        conflictingMatch: other.match_id,
                        details: {
                            team: teamName,
                            gender: genre,
                            teamWithGender: teamWithGender,
                            restMinutes: timeDiff,
                            requiredMinutes: this.minRestMinutes,
                            match1Time: match.horaire,
                            match2Time: other.horaire
                        }
                    });
                }
            });
        });

        return conflicts;
    }

    /**
     * Vérifie les violations de préférences horaires
     */
    checkTimePreference(match) {
        const conflicts = [];
        
        // Ne traiter que les matchs planifiés avec un horaire
        if (!match.horaire) {
            return conflicts;
        }
        
        // Vérifier si le match a des préférences horaires
        if (!match.equipe1_horaires_preferes && !match.equipe2_horaires_preferes) {
            return conflicts;
        }
        
        const matchTime = this.timeToMinutes(match.horaire);
        
        // Vérifier équipe 1
        let team1Violated = false;
        if (match.equipe1_horaires_preferes && match.equipe1_horaires_preferes.length > 0) {
            const validPreferredTimes = match.equipe1_horaires_preferes.filter(t => t && typeof t === 'string');
            if (validPreferredTimes.length > 0) {
                const preferredTimes = validPreferredTimes.map(t => this.timeToMinutes(t)).filter(t => t !== null);
                if (preferredTimes.length > 0) {
                    const minPreferred = Math.min(...preferredTimes);
                    
                    if (matchTime !== null && matchTime < minPreferred) {
                        team1Violated = true;
                    }
                }
            }
        }
        
        // Vérifier équipe 2
        let team2Violated = false;
        if (match.equipe2_horaires_preferes && match.equipe2_horaires_preferes.length > 0) {
            const validPreferredTimes = match.equipe2_horaires_preferes.filter(t => t && typeof t === 'string');
            if (validPreferredTimes.length > 0) {
                const preferredTimes = validPreferredTimes.map(t => this.timeToMinutes(t)).filter(t => t !== null);
                if (preferredTimes.length > 0) {
                    const minPreferred = Math.min(...preferredTimes);
                    
                    if (matchTime !== null && matchTime < minPreferred) {
                        team2Violated = true;
                    }
                }
            }
        }
        
        // Créer le conflit selon la gravité
        if (team1Violated && team2Violated) {
            conflicts.push({
                type: this.conflictTypes.TIME_PREFERENCE,
                severity: 'critical',
                message: `Match à ${match.horaire} avant les horaires préférés des 2 équipes`,
                details: {
                    matchTime: match.horaire,
                    team1Preferences: match.equipe1_horaires_preferes,
                    team2Preferences: match.equipe2_horaires_preferes,
                    bothTeamsViolated: true
                }
            });
        } else if (team1Violated || team2Violated) {
            const violatedTeam = team1Violated ? match.equipe1 : match.equipe2;
            const preferences = team1Violated ? match.equipe1_horaires_preferes : match.equipe2_horaires_preferes;
            
            conflicts.push({
                type: this.conflictTypes.TIME_PREFERENCE,
                severity: 'warning',
                message: `${violatedTeam}: match à ${match.horaire} avant horaires préférés (${preferences.join(', ')})`,
                details: {
                    matchTime: match.horaire,
                    violatedTeam: violatedTeam,
                    preferences: preferences
                }
            });
        }
        
        return conflicts;
    }

    /**
     * Convertit un horaire en minutes depuis minuit
     */
    timeToMinutes(time) {
        if (!time || typeof time !== 'string') {
            return null;
        }
        const [hours, minutes] = time.split(':').map(Number);
        return hours * 60 + minutes;
    }

    /**
     * Calcule la différence en minutes entre deux horaires
     */
    calculateTimeDifference(time1, time2) {
        if (!time1 || !time2 || typeof time1 !== 'string' || typeof time2 !== 'string') {
            return null;
        }
        const [h1, m1] = time1.split(':').map(Number);
        const [h2, m2] = time2.split(':').map(Number);
        const minutes1 = h1 * 60 + m1;
        const minutes2 = h2 * 60 + m2;
        return Math.abs(minutes1 - minutes2);
    }

    /**
     * Récupère les conflits pour un match spécifique
     */
    getConflictsForMatch(matchId) {
        return this.conflicts.get(matchId) || [];
    }

    /**
     * Récupère tous les matchs en conflit
     */
    getAllConflictingMatches() {
        return Array.from(this.conflicts.keys());
    }

    /**
     * Compte les conflits par sévérité
     */
    getConflictStats() {
        const stats = {
            critical: 0,
            warning: 0,
            total: 0
        };
        
        this.conflicts.forEach(conflictArray => {
            conflictArray.forEach(conflict => {
                stats.total++;
                if (conflict.severity === 'critical') {
                    stats.critical++;
                } else if (conflict.severity === 'warning') {
                    stats.warning++;
                }
            });
        });
        
        return stats;
    }

    /**
     * Génère un résumé des conflits pour l'UI
     */
    getConflictSummary() {
        const summary = {
            totalMatches: this.conflicts.size,
            byType: {},
            bySeverity: { critical: 0, warning: 0 },
            details: []
        };
        
        this.conflicts.forEach((conflictArray, matchId) => {
            conflictArray.forEach(conflict => {
                // Compte par type
                if (!summary.byType[conflict.type]) {
                    summary.byType[conflict.type] = 0;
                }
                summary.byType[conflict.type]++;
                
                // Compte par sévérité
                summary.bySeverity[conflict.severity]++;
                
                // Ajoute les détails
                summary.details.push({
                    matchId,
                    ...conflict
                });
            });
        });
        
        return summary;
    }

    /**
     * Vérifie si un match a des conflits critiques
     */
    hasCriticalConflicts(matchId) {
        const conflicts = this.getConflictsForMatch(matchId);
        return conflicts.some(c => c.severity === 'critical');
    }

    /**
     * Vérifie si un match a des avertissements
     */
    hasWarnings(matchId) {
        const conflicts = this.getConflictsForMatch(matchId);
        return conflicts.some(c => c.severity === 'warning');
    }
}
