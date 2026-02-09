/**
 * PyCalendar Pool Editor - Utilities
 * Helper functions and constants
 */

const Utils = {
    // ==================== Constants ====================
    LEVELS: ['A1', 'A2', 'A3', 'A4'],
    GENDERS: ['F', 'M'],
    TIMES: ['14H', '16H', '18H', '20H'],
    POOL_LETTERS: ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'],
    
    // Time icons
    TIME_ICONS: {
        '14H': '🌤️',
        '16H': '☀️',
        '18H': '🌆',
        '20H': '🌙'
    },
    
    // Institution colors (will be assigned dynamically)
    institutionColors: new Map(),
    colorIndex: 0,
    
    // ==================== ID Generation ====================
    
    /**
     * Generate unique ID
     */
    generateId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2, 9);
    },
    
    /**
     * Generate team ID from name and gender
     */
    generateTeamId(name, gender) {
        const cleanName = name.replace(/\s+/g, '_').replace(/[^a-zA-Z0-9_]/g, '');
        return `${cleanName}_${gender}_${this.generateId().substr(0, 4)}`;
    },
    
    /**
     * Generate pool name from components
     * Format: [PREFIX][GENDER][LEVEL]P[LETTER]
     */
    generatePoolName(prefix, gender, level, letter) {
        return `${prefix}${gender}${level}P${letter}`;
    },
    
    /**
     * Parse pool name to extract components
     */
    parsePoolName(poolName) {
        // Pattern: XXFFA1PA or similar
        const match = poolName.match(/^([A-Z]{2})([FM])([A-Z]\d)P([A-Z])$/);
        if (match) {
            return {
                prefix: match[1],
                gender: match[2],
                level: match[3],
                letter: match[4]
            };
        }
        return null;
    },
    
    // ==================== Institution Colors ====================
    
    /**
     * Get color for institution
     */
    getInstitutionColor(institution) {
        if (!institution) return null;
        
        const key = institution.toLowerCase().trim();
        if (!this.institutionColors.has(key)) {
            // Assign next color from CSS variables
            this.colorIndex++;
            const colorNum = ((this.colorIndex - 1) % 20) + 1;
            this.institutionColors.set(key, `var(--inst-${colorNum})`);
        }
        
        return this.institutionColors.get(key);
    },
    
    /**
     * Get all institution colors as array
     */
    getAllInstitutionColors() {
        return Array.from(this.institutionColors.entries()).map(([name, color]) => ({
            name,
            color
        }));
    },
    
    /**
     * Reset institution colors
     */
    resetInstitutionColors() {
        this.institutionColors.clear();
        this.colorIndex = 0;
    },
    
    // ==================== Statistics ====================
    
    /**
     * Calculate number of matches for a pool
     * @param {number} teamCount - Number of teams
     * @param {boolean} isAllerRetour - Is it a round-trip pool
     */
    calculateMatches(teamCount, isAllerRetour = false) {
        if (teamCount < 2) return 0;
        const matches = (teamCount * (teamCount - 1)) / 2;
        return isAllerRetour ? matches * 2 : matches;
    },
    
    /**
     * Get match time based on two teams' preferred times
     * Returns the latest time
     */
    getMatchTime(time1, time2) {
        const timeOrder = { '14H': 0, '16H': 1, '18H': 2, '20H': 3 };
        const order1 = timeOrder[time1] ?? 0;
        const order2 = timeOrder[time2] ?? 0;
        return order1 >= order2 ? time1 : time2;
    },
    
    /**
     * Calculate time distribution for a pool
     */
    calculateTimeDistribution(teams, isAllerRetour = false) {
        const distribution = { '14H': 0, '16H': 0, '18H': 0, '20H': 0 };
        const multiplier = isAllerRetour ? 2 : 1;
        
        for (let i = 0; i < teams.length; i++) {
            for (let j = i + 1; j < teams.length; j++) {
                const matchTime = this.getMatchTime(
                    teams[i].horaire || '14H',
                    teams[j].horaire || '14H'
                );
                distribution[matchTime] += multiplier;
            }
        }
        
        return distribution;
    },
    
    // ==================== Formatting ====================
    
    /**
     * Format date
     */
    formatDate(date, format = 'DD/MM/YYYY HH:mm') {
        const d = new Date(date);
        const pad = (n) => n.toString().padStart(2, '0');
        
        return format
            .replace('DD', pad(d.getDate()))
            .replace('MM', pad(d.getMonth() + 1))
            .replace('YYYY', d.getFullYear())
            .replace('HH', pad(d.getHours()))
            .replace('mm', pad(d.getMinutes()));
    },
    
    /**
     * Get time ago string
     */
    getTimeAgo(date) {
        const now = new Date();
        const diff = Math.floor((now - new Date(date)) / 1000);
        
        if (diff < 60) return 'À l\'instant';
        if (diff < 3600) return `Il y a ${Math.floor(diff / 60)} min`;
        if (diff < 86400) return `Il y a ${Math.floor(diff / 3600)} h`;
        return this.formatDate(date, 'DD/MM HH:mm');
    },
    
    // ==================== DOM Helpers ====================
    
    /**
     * Create element with attributes
     */
    createElement(tag, attrs = {}, children = []) {
        const el = document.createElement(tag);
        
        Object.entries(attrs).forEach(([key, value]) => {
            if (key === 'className') {
                el.className = value;
            } else if (key === 'style' && typeof value === 'object') {
                Object.assign(el.style, value);
            } else if (key.startsWith('data')) {
                el.setAttribute(key.replace(/([A-Z])/g, '-$1').toLowerCase(), value);
            } else if (key.startsWith('on') && typeof value === 'function') {
                el.addEventListener(key.slice(2).toLowerCase(), value);
            } else {
                el.setAttribute(key, value);
            }
        });
        
        children.forEach(child => {
            if (typeof child === 'string') {
                el.appendChild(document.createTextNode(child));
            } else if (child instanceof Node) {
                el.appendChild(child);
            }
        });
        
        return el;
    },
    
    /**
     * Show toast message
     */
    showToast(message, type = 'info', duration = 3000) {
        const container = document.getElementById('toast-container');
        if (!container) return;
        
        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };
        
        const toast = this.createElement('div', { className: `toast ${type}` }, [
            this.createElement('span', { className: 'toast-icon' }, [icons[type] || 'ℹ️']),
            this.createElement('div', { className: 'toast-content' }, [
                this.createElement('span', { className: 'toast-message' }, [message])
            ]),
            this.createElement('button', { 
                className: 'toast-close',
                onClick: () => toast.remove()
            }, ['×'])
        ]);
        
        container.appendChild(toast);
        
        setTimeout(() => toast.remove(), duration);
    },
    
    // ==================== Data Helpers ====================
    
    /**
     * Deep clone object
     */
    deepClone(obj) {
        return JSON.parse(JSON.stringify(obj));
    },
    
    /**
     * Sort teams by time then name
     */
    sortTeams(teams) {
        const timeOrder = { '14H': 0, '16H': 1, '18H': 2, '20H': 3 };
        return [...teams].sort((a, b) => {
            const timeA = timeOrder[a.horaire] ?? 0;
            const timeB = timeOrder[b.horaire] ?? 0;
            if (timeA !== timeB) return timeA - timeB;
            return (a.nom || '').localeCompare(b.nom || '');
        });
    },
    
    /**
     * Sort pools by level then letter
     */
    sortPools(pools) {
        const levelOrder = { 'A1': 0, 'A2': 1, 'A3': 2, 'A4': 3 };
        return [...pools].sort((a, b) => {
            if (a.gender !== b.gender) return a.gender === 'F' ? -1 : 1;
            const levelA = levelOrder[a.level] ?? 0;
            const levelB = levelOrder[b.level] ?? 0;
            if (levelA !== levelB) return levelA - levelB;
            return (a.letter || '').localeCompare(b.letter || '');
        });
    },
    
    /**
     * Group teams by gender and level
     */
    groupTeamsByGenderAndLevel(teams) {
        const groups = {};
        
        this.GENDERS.forEach(gender => {
            groups[gender] = {};
            this.LEVELS.forEach(level => {
                groups[gender][level] = [];
            });
        });
        
        teams.forEach(team => {
            const gender = team.genre || 'M';
            const level = team.niveau || 'A1';
            if (groups[gender] && groups[gender][level]) {
                groups[gender][level].push(team);
            }
        });
        
        return groups;
    },
    
    // ==================== Validation ====================
    
    /**
     * Check if two objects have real differences (for history tracking)
     * Compares only relevant team fields
     */
    hasRealChanges(oldData, newData) {
        // Fields to compare for teams
        const teamFields = ['nom', 'genre', 'niveau', 'horaire', 'institution', 'poule', 'horaireAmenage'];
        
        for (const field of teamFields) {
            const oldVal = oldData[field];
            const newVal = newData[field];
            
            // Normalize null/undefined/empty string
            const normalizedOld = (oldVal === null || oldVal === undefined || oldVal === '') ? null : oldVal;
            const normalizedNew = (newVal === null || newVal === undefined || newVal === '') ? null : newVal;
            
            if (normalizedOld !== normalizedNew) {
                return true;
            }
        }
        
        // Check gymnasesAmenages array
        const oldGymnases = oldData.gymnasesAmenages || [];
        const newGymnases = newData.gymnasesAmenages || [];
        
        if (oldGymnases.length !== newGymnases.length) {
            return true;
        }
        
        for (let i = 0; i < oldGymnases.length; i++) {
            if (oldGymnases[i] !== newGymnases[i]) {
                return true;
            }
        }
        
        return false;
    },
    
    /**
     * Validate team data
     */
    validateTeam(team) {
        const errors = [];
        
        if (!team.nom || team.nom.trim() === '') {
            errors.push('Le nom est obligatoire');
        }
        if (!team.genre || !['F', 'M'].includes(team.genre)) {
            errors.push('Le genre doit être F ou M');
        }
        if (!team.niveau || !this.LEVELS.includes(team.niveau)) {
            errors.push('Le niveau doit être A1, A2, A3 ou A4');
        }
        if (!team.horaire || !this.TIMES.includes(team.horaire)) {
            errors.push('L\'horaire doit être 14H, 16H, 18H ou 20H');
        }
        
        return {
            valid: errors.length === 0,
            errors
        };
    },
    
    /**
     * Validate pool data
     */
    validatePool(pool, existingPools) {
        const errors = [];
        
        if (!pool.gender || !['F', 'M'].includes(pool.gender)) {
            errors.push('Le genre doit être F ou M');
        }
        if (!pool.level || !this.LEVELS.includes(pool.level)) {
            errors.push('Le niveau doit être A1, A2, A3 ou A4');
        }
        if (!pool.letter || !this.POOL_LETTERS.includes(pool.letter)) {
            errors.push('La lettre de poule est invalide');
        }
        
        // Check for duplicate
        if (existingPools) {
            const duplicate = existingPools.find(p => 
                p.id !== pool.id &&
                p.gender === pool.gender &&
                p.level === pool.level &&
                p.letter === pool.letter
            );
            if (duplicate) {
                errors.push('Une poule avec ces paramètres existe déjà');
            }
        }
        
        return {
            valid: errors.length === 0,
            errors
        };
    },
    
    // ==================== File Helpers ====================
    
    /**
     * Download data as file
     */
    downloadFile(content, filename, type = 'application/json') {
        const blob = new Blob([content], { type });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    },
    
    /**
     * Read file as text
     */
    readFileAsText(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = (e) => reject(e);
            reader.readAsText(file);
        });
    },
    
    /**
     * Read file as ArrayBuffer (for Excel)
     */
    readFileAsArrayBuffer(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = (e) => reject(e);
            reader.readAsArrayBuffer(file);
        });
    }
};

// Export for use in other modules
window.Utils = Utils;
