/**
 * PyCalendar Pool Editor - Data Manager
 * Handles data loading, saving, and state management
 */

class DataManager {
    constructor() {
        this.data = {
            teams: [],
            pools: [],
            sport: null,
            config: null,
            gymnases: []  // Liste des gymnases disponibles
        };
        
        this.settings = {
            sport: 'handball',
            prefix: 'HB',
            minPoolSize: 3,
            maxPoolSize: 5
        };
        
        this.changeCount = 0;
        this.listeners = new Map();
        this.storageKey = 'pycalendar_pool_editor';
    }
    
    // ==================== Event System ====================
    
    on(event, callback) {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, []);
        }
        this.listeners.get(event).push(callback);
    }
    
    off(event, callback) {
        if (this.listeners.has(event)) {
            const listeners = this.listeners.get(event);
            const index = listeners.indexOf(callback);
            if (index > -1) listeners.splice(index, 1);
        }
    }
    
    emit(event, data) {
        if (this.listeners.has(event)) {
            this.listeners.get(event).forEach(cb => cb(data));
        }
    }
    
    // ==================== Initialization ====================
    
    async init() {
        // Try to load from localStorage
        const saved = this.loadFromStorage();
        if (saved) {
            this.data = saved.data;
            this.settings = { ...this.settings, ...saved.settings };
            this.emit('dataLoaded', this.data);
            return true;
        }
        return false;
    }
    
    // ==================== Data Loading ====================
    
    /**
     * Load data from YAML config and Excel file
     */
    async loadFromYamlAndExcel(yamlContent, excelBuffer) {
        try {
            // Parse YAML
            const config = jsyaml.load(yamlContent);
            this.data.config = config;
            
            // Extract sport settings
            if (config.sport) {
                this.settings.sport = config.sport.type || 'handball';
                this.settings.prefix = this.getSportPrefix(config.sport.type);
            }
            
            // Parse Excel
            const workbook = XLSX.read(excelBuffer, { type: 'array' });
            
            // Find the "Equipes" sheet
            const equipesSheet = workbook.Sheets['Equipes'] || workbook.Sheets['equipes'] || workbook.Sheets[workbook.SheetNames[0]];
            
            if (!equipesSheet) {
                throw new Error('Feuille "Equipes" non trouvée dans le fichier Excel');
            }
            
            // Convert to JSON
            const rawData = XLSX.utils.sheet_to_json(equipesSheet);
            
            // Parse teams
            this.data.teams = this.parseTeamsFromExcel(rawData);
            
            // Load Types_Poules if available
            const typesSheet = workbook.Sheets['Types_Poules'];
            if (typesSheet) {
                const typesData = XLSX.utils.sheet_to_json(typesSheet);
                this.poolTypes = this.parsePoolTypes(typesData);
            } else {
                this.poolTypes = {};
            }
            
            // Load Gymnases if available
            const gymnasesSheet = workbook.Sheets['Gymnases'];
            if (gymnasesSheet) {
                const gymnasesData = XLSX.utils.sheet_to_json(gymnasesSheet);
                this.data.gymnases = this.parseGymnases(gymnasesData);
            } else {
                this.data.gymnases = [];
            }
            
            // Load Dispos_Gymnases_Equipes if available (horaires aménagés)
            const disposSheet = workbook.Sheets['Dispos_Gymnases_Equipes'];
            if (disposSheet) {
                const disposData = XLSX.utils.sheet_to_json(disposSheet);
                this.applyDisposToTeams(disposData);
            }
            
            // Build pools from teams
            this.buildPoolsFromTeams();
            
            // Assign institution colors
            this.assignInstitutionColors();
            
            this.changeCount = 0;
            this.emit('dataLoaded', this.data);
            this.saveToStorage();
            
            return true;
        } catch (error) {
            console.error('Error loading data:', error);
            throw error;
        }
    }
    
    /**
     * Parse pool types from Types_Poules sheet
     */
    parsePoolTypes(typesData) {
        const types = {};
        typesData.forEach(row => {
            const poule = row['Poule'] || row['poule'];
            const type = row['Type'] || row['type'];
            if (poule && type) {
                const normalizedType = type.toString().toLowerCase();
                if (normalizedType.includes('aller') && normalizedType.includes('retour')) {
                    types[poule.toString().trim()] = 'aller-retour';
                } else {
                    types[poule.toString().trim()] = 'classique';
                }
            }
        });
        return types;
    }
    
    /**
     * Parse gymnases from Gymnases sheet
     */
    parseGymnases(gymnasesData) {
        const gymnases = [];
        gymnasesData.forEach(row => {
            const nom = row['Gymnase'] || row['gymnase'] || row['Nom'];
            if (nom) {
                gymnases.push({
                    nom: nom.toString().trim(),
                    adresse: row['Adresse'] || '',
                    capacite: row['Capacite'] || 1
                });
            }
        });
        return gymnases;
    }
    
    /**
     * Apply disponibilites (horaires aménagés) to teams from Dispos_Gymnases_Equipes sheet
     */
    applyDisposToTeams(disposData) {
        disposData.forEach(row => {
            const equipeName = row['Equipe'] || row['equipe'];
            const genre = row['Genre'] || row['genre'];
            const horaireDispo = row['Horaire_Dispo'] || row['horaire_dispo'];
            
            if (!equipeName || !horaireDispo) return;
            
            // Collect gymnases
            const gymnases = [];
            for (let i = 1; i <= 5; i++) {
                const gym = row[`Gymnase_${i}`] || row[`gymnase_${i}`];
                if (gym && gym.toString().trim()) {
                    gymnases.push(gym.toString().trim());
                }
            }
            
            if (gymnases.length === 0) return;
            
            // Find matching team
            const team = this.data.teams.find(t => 
                t.nom === equipeName.toString().trim() &&
                (!genre || t.genre === genre.toString().trim())
            );
            
            if (team) {
                // Convert horaire from 18:00 to 18H format
                let horaireAmenage = horaireDispo.toString().trim();
                if (horaireAmenage.includes(':')) {
                    const h = horaireAmenage.split(':')[0];
                    horaireAmenage = `${h}H`;
                }
                
                team.horaireAmenage = horaireAmenage;
                team.gymnasesAmenages = gymnases;
            }
        });
    }
    
    /**
     * Get list of available gymnases
     */
    getGymnases() {
        return this.data.gymnases || [];
    }
    
    /**
     * Parse pool code to extract sport, gender, level, letter
     * Format: {SPORT}{GENRE}{NIVEAU}{POULE}
     * Example: VBFA1PA -> {sport: 'VB', gender: 'F', level: 'A1', letter: 'A'}
     */
    parsePoolCode(poolCode) {
        if (!poolCode || poolCode.length < 4) return null;
        
        const code = poolCode.toString().trim().toUpperCase();
        
        // Pattern: 2 lettres sport + 1 lettre genre (F/M/X) + niveau (A1, A2, etc) + optionnel P + lettre
        const match = code.match(/^([A-Z]{2})([FMX])([A-Z]?\d+)(P[A-Z])?$/);
        
        if (match) {
            return {
                sport: match[1],
                gender: match[2],
                level: match[3],
                letter: match[4] ? match[4].slice(1) : 'A' // Remove 'P' prefix
            };
        }
        
        // Fallback: try simpler pattern
        const simpleMatch = code.match(/^([A-Z]{2})([FMX])(.+)$/);
        if (simpleMatch) {
            const rest = simpleMatch[3];
            // Extract level (A1, A2, A3, A4)
            const levelMatch = rest.match(/^([A-Z]?\d+)/);
            const level = levelMatch ? levelMatch[1] : 'A1';
            // Letter is the last character after P if present
            const letterMatch = rest.match(/P([A-Z])$/);
            const letter = letterMatch ? letterMatch[1] : 'A';
            
            return {
                sport: simpleMatch[1],
                gender: simpleMatch[2],
                level: level,
                letter: letter
            };
        }
        
        return null;
    }
    
    /**
     * Parse teams from Excel data
     */
    parseTeamsFromExcel(rawData) {
        const teams = [];
        
        rawData.forEach((row, index) => {
            // Try different column name variations
            const equipe = row['Equipe'] || row['equipe'] || row['Équipe'] || row['EQUIPE'];
            
            // Genre_Equipe column (new preferred column)
            const genreEquipeCol = row['Genre_Equipe'] || row['genre_equipe'] || row['GENRE_EQUIPE'];
            // Legacy Genre column for fallback
            const genreCol = row['Genre'] || row['genre'] || row['GENRE'];
            
            // Niveau_Equipe column (preferred)
            const niveauEquipeCol = row['Niveau_Equipe'] || row['niveau_equipe'] || row['NIVEAU_EQUIPE'];
            // Legacy Niveau column for fallback
            const niveauCol = row['Niveau'] || row['niveau'] || row['NIVEAU'];
            
            const horaireRaw = row['Horaire_Prefere'] || row['Horaire'] || row['horaire'] || row['HORAIRE'];
            const poule = row['Poule'] || row['poule'] || row['POULE'];
            
            if (!equipe) return;
            
            // Parse horaire
            let horaire = this.parseHoraire(horaireRaw);
            
            // Extract institution from team name (before parentheses)
            const institution = this.extractInstitution(equipe);
            
            // Parse level and gender
            // Priority: 
            // 1. Genre_Equipe/Niveau_Equipe columns (explicit values, even without pool)
            // 2. Pool code parsing (if pool is defined)
            // 3. Old Genre/Niveau columns (fallback for compatibility)
            // 4. null if nothing found (don't default to M/A1)
            let genre = null;
            let niveau = null;
            
            // First, try to get values from dedicated columns (highest priority)
            if (genreEquipeCol) {
                genre = this.parseGenreStrict(genreEquipeCol);
            }
            if (niveauEquipeCol) {
                niveau = this.parseNiveau(niveauEquipeCol);
            }
            
            // Parse pool code to get gender/level if not already set
            if (poule) {
                const parsed = this.parsePoolCode(poule);
                if (parsed) {
                    // Only use pool values if columns were not defined
                    if (!genre) {
                        genre = parsed.gender;
                    }
                    if (!niveau) {
                        niveau = parsed.level;
                    }
                }
            }
            
            // Fallback to legacy column values if still not set
            if (!genre && genreCol) {
                genre = this.parseGenreStrict(genreCol);
            }
            if (!niveau && niveauCol) {
                niveau = this.parseNiveau(niveauCol);
            }
            
            const team = {
                id: Utils.generateId(),
                nom: equipe.toString().trim(),
                genre: genre,  // Can be null for unassigned teams
                niveau: niveau,  // Can be null for unassigned teams
                horaire: horaire,
                institution: institution,
                poule: poule ? poule.toString().trim() : null,
                originalIndex: index
            };
            
            teams.push(team);
        });
        
        return teams;
    }
    
    /**
     * Parse horaire from various formats
     */
    parseHoraire(value) {
        if (!value) return '14H';
        
        const str = value.toString().trim().toUpperCase();
        
        // Already in correct format
        if (['14H', '16H', '18H', '20H'].includes(str)) {
            return str;
        }
        
        // Try parsing time formats like "14:00", "14h00", "14"
        const match = str.match(/(\d{1,2})/);
        if (match) {
            const hour = parseInt(match[1]);
            if (hour === 14) return '14H';
            if (hour === 16) return '16H';
            if (hour === 18) return '18H';
            if (hour === 20) return '20H';
        }
        
        return '14H'; // Default
    }
    
    /**
     * Parse genre from various formats
     */
    parseGenre(value) {
        if (!value) return 'M';
        
        const str = value.toString().trim().toUpperCase();
        
        if (str.startsWith('F') || str.includes('FEM') || str.includes('DAME')) {
            return 'F';
        }
        
        if (str === 'X' || str.includes('MIXTE') || str.includes('MIX')) {
            return 'X';
        }
        
        return 'M';
    }
    
    /**
     * Parse genre strictly - returns null if not recognized
     * Used for explicit column values where we don't want to default to 'M'
     */
    parseGenreStrict(value) {
        if (!value) return null;
        
        const str = value.toString().trim().toUpperCase();
        
        if (str === 'M' || str === 'MASCULIN' || str === 'MASC' || str === 'H' || str === 'HOMME') {
            return 'M';
        }
        
        if (str === 'F' || str === 'FEMININ' || str === 'FEM' || str === 'FEMME' || str === 'FÉMININ') {
            return 'F';
        }
        
        if (str === 'X' || str === 'MIXTE' || str === 'MIX') {
            return 'X';
        }
        
        return null;
    }
    
    /**
     * Parse niveau from various formats
     */
    parseNiveau(value) {
        if (!value) return 'A1';
        
        const str = value.toString().trim().toUpperCase();
        
        if (str.includes('A1') || str === '1') return 'A1';
        if (str.includes('A2') || str === '2') return 'A2';
        if (str.includes('A3') || str === '3') return 'A3';
        if (str.includes('A4') || str === '4') return 'A4';
        
        return 'A1';
    }
    
    /**
     * Extract institution from team name
     * Format expected: "INSTITUTION (numéro)" where INSTITUTION can contain numbers (e.g., "LYON 1", "PARIS 3")
     * Examples:
     *   - "LYON 1 (3)" -> "LYON 1"
     *   - "PARIS (1)" -> "PARIS"
     *   - "CENTRALE NANTES (2)" -> "CENTRALE NANTES"
     *   - "LYON 3 JEAN MOULIN (1)" -> "LYON 3 JEAN MOULIN"
     */
    extractInstitution(teamName) {
        if (!teamName) return '';
        
        const name = teamName.toString().trim();
        
        // Pattern: everything before the last " (number)" pattern
        // This handles cases like "LYON 1 (3)" correctly
        const match = name.match(/^(.+?)\s*\(\d+\)\s*$/);
        if (match) {
            return match[1].trim();
        }
        
        // No parentheses with number found, return the full name
        return name;
    }
    
    /**
     * Build pools from team assignments
     * IMPORTANT: pool.teams is NOT used anywhere - we only store pool metadata
     * Teams are linked to pools via team.poule, and getPoolTeams() is the single source of truth
     */
    buildPoolsFromTeams() {
        const poolsMap = new Map();
        
        this.data.teams.forEach(team => {
            if (!team.poule) return;
            
            if (!poolsMap.has(team.poule)) {
                const parsed = this.parsePoolCode(team.poule);
                
                // Get pool type from Types_Poules sheet if available
                const poolType = (this.poolTypes && this.poolTypes[team.poule]) 
                    ? this.poolTypes[team.poule] 
                    : 'classique';
                
                // Pool only stores metadata - NO teams array
                poolsMap.set(team.poule, {
                    id: team.poule,
                    name: team.poule,
                    gender: parsed ? parsed.gender : team.genre,
                    level: parsed ? parsed.level : team.niveau,
                    letter: parsed ? parsed.letter : 'A',
                    type: poolType
                    // NO teams array - use getPoolTeams(pool.id) instead
                });
            }
        });
        
        this.data.pools = Array.from(poolsMap.values());
        
        // Update statistics
        if (typeof statistics !== 'undefined') {
            statistics.update();
        }
    }
    
    /**
     * Get sport prefix
     */
    getSportPrefix(sportType) {
        const prefixes = {
            'volleyball': 'VB',
            'handball': 'HB',
            'basketball': 'BB',
            'football': 'FB'
        };
        return prefixes[sportType] || 'SP';
    }
    
    /**
     * Assign colors to institutions
     */
    assignInstitutionColors() {
        Utils.resetInstitutionColors();
        
        // Get unique institutions sorted by frequency
        const counts = {};
        this.data.teams.forEach(team => {
            if (team.institution) {
                counts[team.institution] = (counts[team.institution] || 0) + 1;
            }
        });
        
        // Sort by frequency (most common first)
        const sorted = Object.entries(counts)
            .sort((a, b) => b[1] - a[1])
            .map(([name]) => name);
        
        // Assign colors
        sorted.forEach(inst => Utils.getInstitutionColor(inst));
    }
    
    /**
     * Load from JSON object (not string)
     */
    loadFromJson(data) {
        try {
            // If data is a string, parse it
            if (typeof data === 'string') {
                data = JSON.parse(data);
            }
            
            if (data.teams && Array.isArray(data.teams)) {
                this.data.teams = data.teams;
            }
            if (data.pools && Array.isArray(data.pools)) {
                this.data.pools = data.pools;
            }
            if (data.settings) {
                this.settings = { ...this.settings, ...data.settings };
            }
            
            this.assignInstitutionColors();
            this.changeCount = 0;
            this.emit('dataLoaded', this.data);
            this.saveToStorage();
            
            return true;
        } catch (error) {
            console.error('Error loading JSON:', error);
            throw error;
        }
    }
    
    /**
     * Load from Excel data array and config
     */
    async loadFromExcel(teamsData, config) {
        try {
            this.data.config = config;
            
            // Extract sport settings
            if (config && config.sport) {
                this.settings.sport = config.sport.type || 'handball';
                this.settings.prefix = this.getSportPrefix(config.sport.type);
            }
            
            // Parse teams from Excel data
            this.data.teams = this.parseTeamsFromExcel(teamsData);
            
            // Build pools from teams
            this.buildPoolsFromTeams();
            
            // Assign institution colors
            this.assignInstitutionColors();
            
            this.changeCount = 0;
            this.emit('dataLoaded', this.data);
            this.saveToStorage();
            
            return true;
        } catch (error) {
            console.error('Error loading from Excel:', error);
            throw error;
        }
    }
    
    /**
     * Load from config only (for testing)
     */
    async loadFromConfig(config) {
        this.data.config = config;
        
        if (config && config.sport) {
            this.settings.sport = config.sport.type || 'handball';
            this.settings.prefix = this.getSportPrefix(config.sport.type);
        }
        
        this.data.teams = [];
        this.data.pools = [];
        
        this.changeCount = 0;
        this.emit('dataLoaded', this.data);
        
        return true;
    }
    
    /**
     * Load from array of teams
     */
    loadFromArray(teams) {
        this.data.teams = teams;
        this.buildPoolsFromTeams();
        this.assignInstitutionColors();
        
        this.changeCount = 0;
        this.emit('dataLoaded', this.data);
        this.saveToStorage();
        
        return true;
    }
    
    /**
     * Export data
     */
    exportData() {
        return {
            teams: this.data.teams,
            pools: this.data.pools,
            settings: this.settings,
            exportDate: new Date().toISOString()
        };
    }
    
    /**
     * Load demo data
     */
    loadDemoData() {
        const institutions = [
            'Paris 1 Panthéon-Sorbonne',
            'Paris Sciences et Lettres',
            'Sorbonne Université',
            'Université Paris-Saclay',
            'Paris Dauphine',
            'INSEP',
            'Paris Cité',
            'CY Cergy Paris',
            'UPEC',
            'Paris Nanterre'
        ];
        
        const teams = [];
        const pools = [];
        let teamId = 1;
        
        // Generate teams and pools
        Utils.GENDERS.forEach(gender => {
            Utils.LEVELS.forEach(level => {
                // Create 1-2 pools per gender/level
                const numPools = Math.random() > 0.5 ? 2 : 1;
                
                for (let p = 0; p < numPools; p++) {
                    const poolLetter = Utils.POOL_LETTERS[p];
                    const poolId = Utils.generatePoolName(this.settings.prefix, gender, level, poolLetter);
                    
                    // Pool only stores metadata - NO teams array
                    const pool = {
                        id: poolId,
                        name: poolId,
                        gender,
                        level,
                        letter: poolLetter,
                        type: Math.random() > 0.8 ? 'aller-retour' : 'classique'
                        // NO teams array - use getPoolTeams(pool.id) instead
                    };
                    
                    // Add 3-5 teams to pool (via team.poule reference)
                    const numTeams = 3 + Math.floor(Math.random() * 3);
                    for (let t = 0; t < numTeams; t++) {
                        const institution = institutions[Math.floor(Math.random() * institutions.length)];
                        const team = {
                            id: `team_${teamId++}`,
                            nom: `${institution} (${Math.ceil(Math.random() * 2)})`,
                            genre: gender,
                            niveau: level,
                            horaire: Utils.TIMES[Math.floor(Math.random() * 4)],
                            institution,
                            poule: poolId  // Team references the pool
                        };
                        teams.push(team);
                    }
                    
                    pools.push(pool);
                }
            });
        });
        
        // Add some unassigned teams
        for (let i = 0; i < 8; i++) {
            const institution = institutions[Math.floor(Math.random() * institutions.length)];
            const gender = Utils.GENDERS[Math.floor(Math.random() * 2)];
            const level = Utils.LEVELS[Math.floor(Math.random() * 4)];
            
            teams.push({
                id: `team_${teamId++}`,
                nom: `${institution} (${Math.ceil(Math.random() * 3)})`,
                genre: gender,
                niveau: level,
                horaire: Utils.TIMES[Math.floor(Math.random() * 4)],
                institution,
                poule: null
            });
        }
        
        this.data.teams = teams;
        this.data.pools = pools;
        
        this.assignInstitutionColors();
        this.changeCount = 0;
        this.emit('dataLoaded', this.data);
        this.saveToStorage();
        
        return true;
    }
    
    // ==================== Data Access ====================
    
    getTeams() {
        return this.data.teams;
    }
    
    getPools() {
        return this.data.pools;
    }
    
    getTeam(teamId) {
        return this.data.teams.find(t => t.id === teamId);
    }
    
    getPool(poolId) {
        return this.data.pools.find(p => p.id === poolId);
    }
    
    getUnassignedTeams() {
        return this.data.teams.filter(t => !t.poule);
    }
    
    getPoolTeams(poolId) {
        return this.data.teams.filter(t => t.poule === poolId);
    }
    
    getInstitutions() {
        const insts = new Set();
        this.data.teams.forEach(t => {
            if (t.institution) insts.add(t.institution);
        });
        return Array.from(insts).sort();
    }
    
    // ==================== Data Modification ====================
    
    /**
     * Move team to a different pool
     * Handles all cases: from pool to pool, from null to pool, from pool to null
     * Note: pool.teams is NOT used - getPoolTeams() is the single source of truth based on team.poule
     */
    moveTeam(teamId, targetPoolId) {
        const team = this.getTeam(teamId);
        if (!team) return false;
        
        const oldPoolId = team.poule;
        
        // Don't do anything if same pool
        if (oldPoolId === targetPoolId) {
            return false;
        }
        
        // Simply update the team's pool reference - getPoolTeams() will reflect this
        team.poule = targetPoolId || null;
        
        this.markChanged();
        this.emit('teamMoved', { team, oldPoolId, newPoolId: targetPoolId });
        
        return true;
    }
    
    /**
     * Update team
     * Note: pool.teams is NOT used - getPoolTeams() is the single source of truth based on team.poule
     */
    updateTeam(teamId, updates) {
        const team = this.getTeam(teamId);
        if (!team) return false;
        
        const oldData = Utils.deepClone(team);
        const oldPoolId = team.poule;
        const newPoolId = updates.poule !== undefined ? updates.poule : oldPoolId;
        
        // Apply all updates to team - getPoolTeams() will reflect any pool change
        Object.assign(team, updates);
        
        this.markChanged();
        this.emit('teamUpdated', { team, oldData, poolChanged: oldPoolId !== newPoolId });
        
        return true;
    }
    
    /**
     * Add new team
     * Note: No need to add to pool.teams - getPoolTeams() is the single source of truth based on team.poule
     */
    addTeam(teamData) {
        const team = {
            id: teamData.id || Utils.generateId(),
            nom: teamData.nom,
            genre: teamData.genre || null,  // Allow null for unassigned teams
            niveau: teamData.niveau || null,  // Allow null for unassigned teams
            horaire: teamData.horaire || '14H',
            institution: teamData.institution || '',
            poule: teamData.poule || null
        };
        
        this.data.teams.push(team);
        
        // Assign color
        if (team.institution) {
            Utils.getInstitutionColor(team.institution);
        }
        
        this.markChanged();
        this.emit('teamAdded', team);
        
        return team;
    }
    
    /**
     * Delete team
     * Note: No need to update pool.teams - getPoolTeams() is the single source of truth
     */
    deleteTeam(teamId) {
        const team = this.getTeam(teamId);
        if (!team) return false;
        
        // Remove from teams list - this is the only change needed
        this.data.teams = this.data.teams.filter(t => t.id !== teamId);
        
        this.markChanged();
        this.emit('teamDeleted', team);
        
        return true;
    }
    
    /**
     * Add new pool
     * Pool only stores metadata - teams are linked via team.poule
     */
    addPool(poolData) {
        const poolId = poolData.id || Utils.generatePoolName(
            this.settings.prefix,
            poolData.gender,
            poolData.level,
            poolData.letter
        );
        
        // Check for duplicate
        if (this.getPool(poolId)) {
            throw new Error('Une poule avec cet identifiant existe déjà');
        }
        
        // Pool only stores metadata - NO teams array
        const pool = {
            id: poolId,
            name: poolData.name || poolId,
            gender: poolData.gender,
            level: poolData.level,
            letter: poolData.letter,
            type: poolData.type || 'classique'
            // NO teams array - use getPoolTeams(pool.id) instead
        };
        
        this.data.pools.push(pool);
        
        this.markChanged();
        this.emit('poolAdded', pool);
        
        return pool;
    }
    
    /**
     * Update pool
     */
    updatePool(poolId, updates) {
        const pool = this.getPool(poolId);
        if (!pool) return false;
        
        const oldData = Utils.deepClone(pool);
        
        // Only allow updating type (not gender/level/letter as it would change the ID)
        if (updates.type !== undefined) {
            pool.type = updates.type;
        }
        
        this.markChanged();
        this.emit('poolUpdated', { pool, oldData });
        
        return true;
    }
    
    /**
     * Delete pool
     * Uses getPoolTeams() to find teams to unassign
     */
    deletePool(poolId) {
        const pool = this.getPool(poolId);
        if (!pool) return false;
        
        // Unassign all teams from this pool using getPoolTeams (single source of truth)
        const teamsInPool = this.getPoolTeams(poolId);
        teamsInPool.forEach(team => {
            team.poule = null;
        });
        
        // Remove pool
        this.data.pools = this.data.pools.filter(p => p.id !== poolId);
        
        this.markChanged();
        this.emit('poolDeleted', pool);
        
        return true;
    }
    
    // ==================== Change Tracking ====================
    
    markChanged() {
        this.changeCount++;
        this.emit('dataChanged', this.changeCount);
        this.saveToStorage();
    }
    
    getChangeCount() {
        return this.changeCount;
    }
    
    resetChangeCount() {
        this.changeCount = 0;
        this.emit('dataChanged', 0);
    }
    
    // ==================== Storage ====================
    
    /**
     * Save to localStorage
     * Cleans up any stale pool.teams arrays before saving
     */
    saveToStorage() {
        try {
            // Clean pools before saving - remove any stale teams arrays
            const cleanPools = this.data.pools.map(pool => ({
                id: pool.id,
                name: pool.name,
                gender: pool.gender,
                level: pool.level,
                letter: pool.letter,
                type: pool.type
                // Explicitly NOT saving teams array
            }));
            
            const dataToSave = {
                teams: this.data.teams,
                pools: cleanPools,
                sport: this.data.sport,
                config: this.data.config,
                gymnases: this.data.gymnases
            };
            
            localStorage.setItem(this.storageKey, JSON.stringify({
                data: dataToSave,
                settings: this.settings,
                timestamp: Date.now()
            }));
        } catch (e) {
            console.warn('Could not save to localStorage:', e);
        }
    }
    
    /**
     * Load from localStorage
     * Migrates old data format if needed
     */
    loadFromStorage() {
        try {
            const saved = localStorage.getItem(this.storageKey);
            if (saved) {
                const parsed = JSON.parse(saved);
                
                // Migration: Remove any stale teams arrays from pools
                if (parsed.data && parsed.data.pools) {
                    parsed.data.pools = parsed.data.pools.map(pool => ({
                        id: pool.id,
                        name: pool.name,
                        gender: pool.gender,
                        level: pool.level,
                        letter: pool.letter,
                        type: pool.type
                        // Remove teams array if present
                    }));
                }
                
                return parsed;
            }
        } catch (e) {
            console.warn('Could not load from localStorage:', e);
        }
        return null;
    }
    
    clearStorage() {
        localStorage.removeItem(this.storageKey);
    }
    
    // ==================== Export ====================
    
    exportToJson() {
        // Prepare teams with amenaged schedule info properly formatted
        const teamsForExport = this.data.teams.map(team => {
            const exportTeam = {
                id: team.id,
                nom: team.nom,
                genre: team.genre,
                niveau: team.niveau,
                horaire: team.horaire,
                institution: team.institution,
                poule: team.poule
            };
            
            // Add horaire aménagé if present
            if (team.horaireAmenage && team.gymnasesAmenages && team.gymnasesAmenages.length > 0) {
                exportTeam.horaireAmenage = team.horaireAmenage;
                exportTeam.gymnasesAmenages = team.gymnasesAmenages;
            }
            
            return exportTeam;
        });
        
        return JSON.stringify({
            teams: teamsForExport,
            pools: this.data.pools,
            gymnases: this.data.gymnases,
            settings: this.settings,
            exportDate: new Date().toISOString()
        }, null, 2);
    }
    
    exportToCsv() {
        const lines = ['Equipe,Genre_Equipe,Niveau_Equipe,Horaire,Institution,Poule,Horaire_Amenage,Gymnases_Amenages'];
        
        this.data.teams.forEach(team => {
            lines.push([
                `"${team.nom}"`,
                team.genre || '',
                team.niveau || '',
                team.horaire,
                `"${team.institution || ''}"`,
                team.poule || '',
                team.horaireAmenage || '',
                `"${(team.gymnasesAmenages || []).join(';')}"`
            ].join(','));
        });
        
        return lines.join('\n');
    }
}

// Create global instance
window.dataManager = new DataManager();
