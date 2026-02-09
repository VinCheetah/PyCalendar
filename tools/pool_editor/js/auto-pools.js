/**
 * PyCalendar Pool Editor - Auto Pools
 * Automatic pool creation and balancing
 */

class AutoPools {
    constructor() {
        this.modal = null;
    }
    
    /**
     * Initialize
     */
    init() {
        this.modal = document.getElementById('modal-auto-create');
        this.setupEventListeners();
    }
    
    /**
     * Setup event listeners
     */
    setupEventListeners() {
        document.getElementById('btn-do-auto-create')?.addEventListener('click', () => {
            this.createAutoPools();
        });
    }
    
    /**
     * Open auto create modal
     */
    openModal() {
        // Ensure modal is initialized
        if (!this.modal) {
            this.modal = document.getElementById('modal-auto-create');
        }
        
        if (!this.modal) {
            console.error('Auto pools modal not found');
            return;
        }
        
        this.modal.classList.add('active');
    }
    
    /**
     * Close modal
     */
    closeModal() {
        if (this.modal) {
            this.modal.classList.remove('active');
        }
    }
    
    /**
     * Create pools automatically
     */
    createAutoPools() {
        const genderFilter = document.getElementById('auto-gender').value;
        const levelFilter = document.getElementById('auto-level').value;
        const minSize = parseInt(document.getElementById('auto-min-size').value) || 3;
        const maxSize = parseInt(document.getElementById('auto-max-size').value) || 5;
        const balanceTime = document.getElementById('auto-time-balance').checked;
        const diversifyInst = document.getElementById('auto-institution-diversity').checked;
        
        // Get unassigned teams matching filters
        let teams = dataManager.getUnassignedTeams();
        
        if (genderFilter !== 'all') {
            teams = teams.filter(t => t.genre === genderFilter);
        }
        if (levelFilter !== 'all') {
            teams = teams.filter(t => t.niveau === levelFilter);
        }
        
        if (teams.length === 0) {
            Utils.showToast('Aucune équipe non assignée correspondante', 'warning');
            return;
        }
        
        // Group by gender and level
        const grouped = {};
        teams.forEach(team => {
            const key = `${team.genre}-${team.niveau}`;
            if (!grouped[key]) {
                grouped[key] = {
                    gender: team.genre,
                    level: team.niveau,
                    teams: []
                };
            }
            grouped[key].teams.push(team);
        });
        
        // Track created pools and moves for undo
        const createdPools = [];
        const teamMoves = [];
        
        // Create pools for each group
        Object.values(grouped).forEach(group => {
            const pools = this.distributeTeams(
                group.teams,
                minSize,
                maxSize,
                balanceTime,
                diversifyInst
            );
            
            pools.forEach((poolTeams, index) => {
                // Find next available letter
                const letter = this.getNextAvailableLetter(group.gender, group.level);
                
                try {
                    const pool = dataManager.addPool({
                        gender: group.gender,
                        level: group.level,
                        letter,
                        type: 'classique'
                    });
                    
                    createdPools.push(pool);
                    
                    // Assign teams
                    poolTeams.forEach(team => {
                        teamMoves.push({
                            teamId: team.id,
                            oldPoolId: null,
                            newPoolId: pool.id
                        });
                        dataManager.moveTeam(team.id, pool.id);
                    });
                } catch (error) {
                    console.error('Error creating pool:', error);
                }
            });
        });
        
        // Record action for undo
        const action = {
            type: 'autoCreate',
            description: `Création de ${createdPools.length} poule(s)`,
            createdPools,
            teamMoves,
            undo: () => {
                // Move teams back
                teamMoves.forEach(move => {
                    dataManager.moveTeam(move.teamId, move.oldPoolId);
                });
                // Delete pools
                createdPools.forEach(pool => {
                    dataManager.deletePool(pool.id);
                });
            },
            redo: () => {
                // Recreate pools
                createdPools.forEach(pool => {
                    try {
                        dataManager.addPool({
                            gender: pool.gender,
                            level: pool.level,
                            letter: pool.letter,
                            type: pool.type
                        });
                    } catch (e) { /* ignore */ }
                });
                // Move teams
                teamMoves.forEach(move => {
                    dataManager.moveTeam(move.teamId, move.newPoolId);
                });
            }
        };
        
        historyManager.addAction(action);
        
        this.closeModal();
        poolRenderer.render();
        
        Utils.showToast(
            `${createdPools.length} poule(s) créée(s) avec ${teamMoves.length} équipe(s)`,
            'success'
        );
    }
    
    /**
     * Distribute teams into balanced pools
     */
    distributeTeams(teams, minSize, maxSize, balanceTime, diversifyInst) {
        if (teams.length === 0) return [];
        
        // Calculate optimal number of pools
        const optimalSize = Math.round((minSize + maxSize) / 2);
        let numPools = Math.ceil(teams.length / optimalSize);
        
        // Adjust if would create too small pools
        while (numPools > 1 && Math.floor(teams.length / numPools) < minSize) {
            numPools--;
        }
        
        // Create empty pools
        const pools = Array.from({ length: numPools }, () => []);
        
        // Sort teams for balanced distribution
        let sortedTeams = [...teams];
        
        if (balanceTime) {
            // Sort by time to distribute evenly
            sortedTeams.sort((a, b) => {
                const timeOrder = { '14H': 0, '16H': 1, '18H': 2, '20H': 3 };
                return (timeOrder[a.horaire] || 0) - (timeOrder[b.horaire] || 0);
            });
        }
        
        if (diversifyInst) {
            // Group by institution first
            const byInst = {};
            sortedTeams.forEach(team => {
                const inst = team.institution || 'unknown';
                if (!byInst[inst]) byInst[inst] = [];
                byInst[inst].push(team);
            });
            
            // Interleave institutions
            sortedTeams = [];
            const instKeys = Object.keys(byInst);
            let maxLen = Math.max(...Object.values(byInst).map(arr => arr.length));
            
            for (let i = 0; i < maxLen; i++) {
                instKeys.forEach(inst => {
                    if (byInst[inst][i]) {
                        sortedTeams.push(byInst[inst][i]);
                    }
                });
            }
        }
        
        // Distribute using snake pattern for balance
        let poolIndex = 0;
        let direction = 1;
        
        sortedTeams.forEach(team => {
            pools[poolIndex].push(team);
            
            poolIndex += direction;
            if (poolIndex >= numPools || poolIndex < 0) {
                direction *= -1;
                poolIndex += direction;
            }
        });
        
        return pools;
    }
    
    /**
     * Get next available letter for pool
     */
    getNextAvailableLetter(gender, level) {
        const existingPools = dataManager.getPools().filter(p => 
            p.gender === gender && p.level === level
        );
        
        const usedLetters = existingPools.map(p => p.letter);
        
        for (const letter of Utils.POOL_LETTERS) {
            if (!usedLetters.includes(letter)) {
                return letter;
            }
        }
        
        // Fallback
        return 'X';
    }
    
    /**
     * Balance existing pools
     */
    balancePools() {
        const pools = dataManager.getPools();
        
        if (pools.length < 2) {
            Utils.showToast('Besoin d\'au moins 2 poules pour équilibrer', 'warning');
            return;
        }
        
        // Group pools by gender and level
        const grouped = {};
        pools.forEach(pool => {
            const key = `${pool.gender}-${pool.level}`;
            if (!grouped[key]) {
                grouped[key] = [];
            }
            grouped[key].push(pool);
        });
        
        const moves = [];
        
        Object.values(grouped).forEach(groupPools => {
            if (groupPools.length < 2) return;
            
            // Get all teams from these pools
            let allTeams = [];
            groupPools.forEach(pool => {
                const teams = dataManager.getPoolTeams(pool.id);
                teams.forEach(team => {
                    allTeams.push({
                        team,
                        originalPool: pool.id
                    });
                });
            });
            
            // Calculate target size
            const targetSize = Math.ceil(allTeams.length / groupPools.length);
            
            // Sort pools by size (descending)
            groupPools.sort((a, b) => {
                const sizeA = dataManager.getPoolTeams(a.id).length;
                const sizeB = dataManager.getPoolTeams(b.id).length;
                return sizeB - sizeA;
            });
            
            // Move teams from large pools to small pools
            for (let i = 0; i < groupPools.length; i++) {
                const largePool = groupPools[i];
                const largeTeams = dataManager.getPoolTeams(largePool.id);
                
                while (largeTeams.length > targetSize) {
                    // Find smallest pool
                    let smallestPool = null;
                    let smallestSize = Infinity;
                    
                    for (let j = groupPools.length - 1; j > i; j--) {
                        const pool = groupPools[j];
                        const size = dataManager.getPoolTeams(pool.id).length;
                        if (size < smallestSize && size < targetSize) {
                            smallestPool = pool;
                            smallestSize = size;
                        }
                    }
                    
                    if (!smallestPool) break;
                    
                    // Move last team from large to small
                    const teamToMove = largeTeams[largeTeams.length - 1];
                    
                    moves.push({
                        teamId: teamToMove.id,
                        oldPoolId: largePool.id,
                        newPoolId: smallestPool.id
                    });
                    
                    dataManager.moveTeam(teamToMove.id, smallestPool.id);
                }
            }
        });
        
        if (moves.length === 0) {
            Utils.showToast('Les poules sont déjà équilibrées', 'info');
            return;
        }
        
        // Record action for undo
        const action = {
            type: 'balance',
            description: `Équilibrage: ${moves.length} déplacement(s)`,
            moves,
            undo: () => {
                moves.forEach(move => {
                    dataManager.moveTeam(move.teamId, move.oldPoolId);
                });
            },
            redo: () => {
                moves.forEach(move => {
                    dataManager.moveTeam(move.teamId, move.newPoolId);
                });
            }
        };
        
        historyManager.addAction(action);
        poolRenderer.render();
        
        Utils.showToast(`${moves.length} équipe(s) déplacée(s)`, 'success');
    }
}

// Create global instance
window.autoPools = new AutoPools();
