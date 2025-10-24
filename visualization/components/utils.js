/**
 * PyCalendar Pro - Utilitaires
 * Fonctions helper pour manipulation de données, calculs, formatage
 */

const Utils = {
    /**
     * Détermine le genre basé sur un match ou le nom d'une poule
     */
    getGender(matchOrPoolName) {
        // Si c'est un objet match, extraire la catégorie ou la poule
        let poolName = matchOrPoolName;
        if (typeof matchOrPoolName === 'object' && matchOrPoolName !== null) {
            poolName = matchOrPoolName.categorie || matchOrPoolName.poule || '';
        }
        
        // Vérifier que c'est bien une chaîne
        if (typeof poolName !== 'string') {
            console.warn('getGender: poolName n\'est pas une chaîne:', poolName);
            return 'mixed';
        }
        
        // Gérer les catégories mixtes (vérifier en premier)
        if (poolName.includes('X') || poolName.toLowerCase().includes('mixte')) {
            return 'mixed';
        }
        
        // Féminin si contient 'HBF' (vérifier AVANT 'F' seul pour éviter confusion)
        // Ex: HBFA1PA = féminin, HBMA1PA = masculin
        if (poolName.includes('FA')) {
            return 'female';
        }
        
        // Masculin si contient 'HBM'
        if (poolName.includes('MA')) {
            return 'male';
        }
        
        // Cas génériques : vérifier 'F' ou 'M' en début ou après espace
        // Pour éviter confusion avec lettres dans le milieu du mot
        const upperPool = poolName.toUpperCase();
        if (upperPool.match(/^F[A-Z0-9]|[^A-Z]F[A-Z0-9]/)) {
            return 'female';
        }
        if (upperPool.match(/^M[A-Z0-9]|[^A-Z]M[A-Z0-9]/)) {
            return 'male';
        }
        
        // Par défaut, considérer comme mixte
        return 'mixed';
    },

    /**
     * Détermine la catégorie basée sur un match ou le nom d'une poule
     */
    getCategory(matchOrPoolName) {
        // Si c'est un objet match, extraire la catégorie ou la poule
        let poolName = matchOrPoolName;
        if (typeof matchOrPoolName === 'object' && matchOrPoolName !== null) {
            poolName = matchOrPoolName.categorie || matchOrPoolName.poule || '';
        }
        
        // Vérifier que c'est bien une chaîne
        if (typeof poolName !== 'string') {
            console.warn('getCategory: poolName n\'est pas une chaîne:', poolName);
            return 'a1';
        }
        
        if (poolName.includes('A1') || poolName.includes('1P')) return 'a1';
        if (poolName.includes('A2') || poolName.includes('2P')) return 'a2';
        if (poolName.includes('A3') || poolName.includes('3P')) return 'a3';
        if (poolName.includes('A4') || poolName.includes('4P')) return 'a4';
        return 'a1';
    },

    /**
     * Détermine si une équipe doit être mise en surbrillance
     */
    shouldHighlight(team, institution, filters) {
        if (filters.team && team === filters.team) return true;
        if (filters.institution && !filters.team && institution === filters.institution) return true;
        return false;
    },

    /**
     * Calcule les statistiques globales
     */
    calculateStats(matches) {
        const stats = {
            weeks: new Set(),
            pools: new Set(),
            venues: new Set(),
            institutions: new Set(),
            teams: new Set(),
            timeSlots: new Set()
        };
        
        matches.forEach(m => {
            if (m.semaine) stats.weeks.add(m.semaine);
            if (m.poule) stats.pools.add(m.poule);
            if (m.gymnase) stats.venues.add(m.gymnase);
            if (m.institution1) stats.institutions.add(m.institution1);
            if (m.institution2) stats.institutions.add(m.institution2);
            if (m.equipe1) stats.teams.add(m.equipe1);
            if (m.equipe2) stats.teams.add(m.equipe2);
            if (m.horaire) stats.timeSlots.add(m.horaire);
        });
        
        return {
            totalMatches: matches.length,
            totalWeeks: stats.weeks.size,
            totalPools: stats.pools.size,
            totalVenues: stats.venues.size,
            weeks: Array.from(stats.weeks).sort((a, b) => a - b),
            pools: Array.from(stats.pools).sort(),
            venues: Array.from(stats.venues).sort(),
            institutions: Array.from(stats.institutions).sort(),
            teams: Array.from(stats.teams).sort(),
            timeSlots: Array.from(stats.timeSlots).sort((a, b) => {
                return Utils.parseTime(a) - Utils.parseTime(b);
            })
        };
    },

    /**
     * Parse une heure au format "HH:MM" en minutes depuis minuit
     */
    parseTime(timeStr) {
        // Vérifier si timeStr est null, undefined ou vide
        if (!timeStr || typeof timeStr !== 'string') {
            return 0; // Retourner 0 pour minuit par défaut
        }
        
        const [hours, minutes] = timeStr.split(':').map(Number);
        return hours * 60 + (minutes || 0);
    },

    /**
     * Formate une heure
     */
    formatTime(timeStr) {
        return timeStr;
    },

    /**
     * Groupe les matchs par clé
     */
    groupBy(matches, keyFn) {
        const grouped = {};
        matches.forEach(m => {
            const key = keyFn(m);
            if (!grouped[key]) grouped[key] = [];
            grouped[key].push(m);
        });
        return grouped;
    },

    /**
     * Filtre les matchs selon les critères
     */
    filterMatches(matches, filters) {
        return matches.filter(m => {
            if (filters.gender && m.equipe1_genre !== filters.gender && m.equipe2_genre !== filters.gender) {
                return false;
            }
            if (filters.institution && m.institution1 !== filters.institution && m.institution2 !== filters.institution) {
                return false;
            }
            if (filters.team && m.equipe1 !== filters.team && m.equipe2 !== filters.team) {
                return false;
            }
            if (filters.pool && m.poule !== filters.pool) {
                return false;
            }
            if (filters.venue && m.gymnase !== filters.venue) {
                return false;
            }
            if (filters.week && m.semaine != filters.week) {
                return false;
            }
            return true;
        });
    },

    /**
     * Filtre les matchs non planifiés
     */
    filterUnscheduled(matches, filters) {
        return matches.filter(m => {
            if (filters.gender && m.equipe1_genre !== filters.gender && m.equipe2_genre !== filters.gender) {
                return false;
            }
            if (filters.institution && m.institution1 !== filters.institution && m.institution2 !== filters.institution) {
                return false;
            }
            if (filters.team && m.equipe1 !== filters.team && m.equipe2 !== filters.team) {
                return false;
            }
            if (filters.pool && m.poule !== filters.pool) {
                return false;
            }
            return true;
        });
    },

    /**
     * Formate les horaires préférés (gauche)
     */
    formatHorairesLeft(horaires) {
        if (!horaires || horaires.length === 0) {
            return `<span class="horaires-preferes no-preferences" title="Aucun horaire préféré défini">⏰ −</span>`;
        }
        const horaireStr = horaires[0];
        return `<span class="horaires-preferes" title="Horaire préféré: ${horaireStr}">⏰ ${horaireStr}</span>`;
    },

    /**
     * Formate les horaires préférés (droite) - maintenant centré comme gauche
     */
    formatHorairesRight(horaires) {
        if (!horaires || horaires.length === 0) {
            return `<span class="horaires-preferes no-preferences" title="Aucun horaire préféré défini">⏰ −</span>`;
        }
        const horaireStr = horaires[0];
        return `<span class="horaires-preferes" title="Horaire préféré: ${horaireStr}">⏰ ${horaireStr}</span>`;
    },

    /**
     * Sauvegarde les préférences dans localStorage
     */
    savePreferences(prefs) {
        try {
            localStorage.setItem('pycalendar_preferences', JSON.stringify(prefs));
        } catch (e) {
            console.warn('Impossible de sauvegarder les préférences:', e);
        }
    },

    /**
     * Charge les préférences depuis localStorage
     */
    loadPreferences() {
        try {
            const stored = localStorage.getItem('pycalendar_preferences');
            return stored ? JSON.parse(stored) : null;
        } catch (e) {
            console.warn('Impossible de charger les préférences:', e);
            return null;
        }
    },

    /**
     * Échappe le HTML
     */
    escapeHtml(text) {
        if (text == null) {
            return '';
        }
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    },

    /**
     * Débounce une fonction
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * Calcule la position verticale d'un match dans la grille (en px)
     */
    getMatchPosition(horaire, startTime, slotHeight) {
        const matchMinutes = this.parseTime(horaire);
        const startMinutes = this.parseTime(startTime);
        const offsetMinutes = matchMinutes - startMinutes;
        return (offsetMinutes / 60) * slotHeight;
    },

    /**
     * Calcule la hauteur d'un match dans la grille (assume 1h par défaut)
     */
    getMatchHeight(slotHeight, duration = 60) {
        return (duration / 60) * slotHeight;
    },

    /**
     * Génère une échelle de temps
     */
    generateTimeScale(startHour, endHour, intervalMinutes = 60) {
        const times = [];
        for (let hour = startHour; hour <= endHour; hour++) {
            for (let minute = 0; minute < 60; minute += intervalMinutes) {
                if (hour === endHour && minute > 0) break;
                const timeStr = `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`;
                times.push(timeStr);
            }
        }
        return times;
    },

    /**
     * Détecte les heures min et max des matchs
     */
    getTimeRange(matches) {
        if (matches.length === 0) return { min: '08:00', max: '20:00' };
        
        const times = matches.map(m => this.parseTime(m.horaire));
        const minMinutes = Math.min(...times);
        const maxMinutes = Math.max(...times);
        
        // Arrondir à l'heure inférieure/supérieure
        const minHour = Math.floor(minMinutes / 60);
        const maxHour = Math.ceil((maxMinutes + 60) / 60); // +60 pour la durée du match
        
        return {
            min: `${String(minHour).padStart(2, '0')}:00`,
            max: `${String(maxHour).padStart(2, '0')}:00`
        };
    },

    /**
     * Crée une structure de créneaux pour la grille
     */
    createSlotStructure(venues, timeSlots, week, matches, availableSlots) {
        const structure = {};
        
        venues.forEach(venue => {
            structure[venue] = {};
            timeSlots.forEach(time => {
                const key = `${venue}_${week}_${time}`;
                const match = matches.find(m => 
                    m.gymnase === venue && 
                    m.semaine === week && 
                    m.horaire === time
                );
                
                const isAvailable = availableSlots.some(slot => 
                    slot.gymnase === venue && 
                    slot.semaine === week && 
                    slot.horaire === time
                );
                
                structure[venue][time] = {
                    match: match || null,
                    available: isAvailable && !match
                };
            });
        });
        
        return structure;
    }
};

// Export pour utilisation
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Utils;
}
