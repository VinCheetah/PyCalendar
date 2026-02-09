/**
 * PyCalendar Pool Editor - Statistics
 * Calculate and display statistics
 */

class Statistics {
    /**
     * Initialize statistics
     */
    init() {
        console.log('📊 Statistics initialized');
        // Subscribe to data changes if needed
        this.update();
    }
    
    /**
     * Update all statistics
     */
    update() {
        this.updateTimeDistribution();
        this.updatePoolTypeStats();
        this.updateTotalMatches();
    }
    
    /**
     * Update time distribution stats
     */
    updateTimeDistribution() {
        const pools = dataManager.getPools();
        const distribution = { '14H': 0, '16H': 0, '18H': 0, '20H': 0 };
        
        pools.forEach(pool => {
            const teams = dataManager.getPoolTeams(pool.id);
            const isAR = pool.type === 'aller-retour';
            const poolDistrib = Utils.calculateTimeDistribution(teams, isAR);
            
            Utils.TIMES.forEach(time => {
                distribution[time] += poolDistrib[time];
            });
        });
        
        // Update UI
        const el = (id) => document.getElementById(id);
        if (el('stat-time-14')) el('stat-time-14').textContent = distribution['14H'];
        if (el('stat-time-16')) el('stat-time-16').textContent = distribution['16H'];
        if (el('stat-time-18')) el('stat-time-18').textContent = distribution['18H'];
        if (el('stat-time-20')) el('stat-time-20').textContent = distribution['20H'];
    }
    
    /**
     * Update pool type stats
     */
    updatePoolTypeStats() {
        const pools = dataManager.getPools();
        const arPools = pools.filter(p => p.type === 'aller-retour').length;
        
        const el = document.getElementById('stat-ar-pools');
        if (el) el.textContent = arPools;
    }
    
    /**
     * Update total matches stat
     */
    updateTotalMatches() {
        const pools = dataManager.getPools();
        let totalMatches = 0;
        
        pools.forEach(pool => {
            const teams = dataManager.getPoolTeams(pool.id);
            const isAR = pool.type === 'aller-retour';
            totalMatches += Utils.calculateMatches(teams.length, isAR);
        });
        
        // Update header stat - try both IDs for compatibility
        const el = document.getElementById('stat-total-matches') || document.getElementById('stat-matches');
        if (el) el.textContent = totalMatches;
    }
    
    /**
     * Get detailed statistics
     */
    getDetailedStats() {
        const teams = dataManager.getTeams();
        const pools = dataManager.getPools();
        
        const stats = {
            teams: {
                total: teams.length,
                byGender: { F: 0, M: 0 },
                byLevel: { A1: 0, A2: 0, A3: 0, A4: 0 },
                byTime: { '14H': 0, '16H': 0, '18H': 0, '20H': 0 },
                assigned: 0,
                unassigned: 0
            },
            pools: {
                total: pools.length,
                byGender: { F: 0, M: 0 },
                byType: { classique: 0, 'aller-retour': 0 },
                avgSize: 0,
                minSize: 0,
                maxSize: 0
            },
            matches: {
                total: 0,
                byTime: { '14H': 0, '16H': 0, '18H': 0, '20H': 0 }
            },
            institutions: {
                count: 0,
                distribution: {}
            }
        };
        
        // Teams stats
        teams.forEach(team => {
            stats.teams.byGender[team.genre] = (stats.teams.byGender[team.genre] || 0) + 1;
            stats.teams.byLevel[team.niveau] = (stats.teams.byLevel[team.niveau] || 0) + 1;
            stats.teams.byTime[team.horaire] = (stats.teams.byTime[team.horaire] || 0) + 1;
            
            if (team.poule) {
                stats.teams.assigned++;
            } else {
                stats.teams.unassigned++;
            }
            
            if (team.institution) {
                stats.institutions.distribution[team.institution] = 
                    (stats.institutions.distribution[team.institution] || 0) + 1;
            }
        });
        
        stats.institutions.count = Object.keys(stats.institutions.distribution).length;
        
        // Pool stats
        const poolSizes = [];
        
        pools.forEach(pool => {
            const poolTeams = dataManager.getPoolTeams(pool.id);
            const isAR = pool.type === 'aller-retour';
            const matchCount = Utils.calculateMatches(poolTeams.length, isAR);
            
            stats.pools.byGender[pool.gender] = (stats.pools.byGender[pool.gender] || 0) + 1;
            stats.pools.byType[pool.type] = (stats.pools.byType[pool.type] || 0) + 1;
            
            poolSizes.push(poolTeams.length);
            stats.matches.total += matchCount;
            
            // Time distribution
            const timeDistrib = Utils.calculateTimeDistribution(poolTeams, isAR);
            Utils.TIMES.forEach(time => {
                stats.matches.byTime[time] += timeDistrib[time];
            });
        });
        
        if (poolSizes.length > 0) {
            stats.pools.avgSize = (poolSizes.reduce((a, b) => a + b, 0) / poolSizes.length).toFixed(1);
            stats.pools.minSize = Math.min(...poolSizes);
            stats.pools.maxSize = Math.max(...poolSizes);
        }
        
        return stats;
    }
    
    /**
     * Generate statistics report
     */
    generateReport() {
        const stats = this.getDetailedStats();
        
        let report = `# Rapport Statistiques - Éditeur de Poules\n\n`;
        report += `Date: ${Utils.formatDate(new Date())}\n\n`;
        
        report += `## Équipes\n`;
        report += `- Total: ${stats.teams.total}\n`;
        report += `- Féminines: ${stats.teams.byGender.F}\n`;
        report += `- Masculines: ${stats.teams.byGender.M}\n`;
        report += `- Assignées: ${stats.teams.assigned}\n`;
        report += `- Non assignées: ${stats.teams.unassigned}\n\n`;
        
        report += `### Par niveau\n`;
        Utils.LEVELS.forEach(level => {
            report += `- ${level}: ${stats.teams.byLevel[level]}\n`;
        });
        
        report += `\n### Par horaire préféré\n`;
        Utils.TIMES.forEach(time => {
            report += `- ${time}: ${stats.teams.byTime[time]}\n`;
        });
        
        report += `\n## Poules\n`;
        report += `- Total: ${stats.pools.total}\n`;
        report += `- Féminines: ${stats.pools.byGender.F}\n`;
        report += `- Masculines: ${stats.pools.byGender.M}\n`;
        report += `- Classiques: ${stats.pools.byType.classique}\n`;
        report += `- Aller-retour: ${stats.pools.byType['aller-retour']}\n`;
        report += `- Taille moyenne: ${stats.pools.avgSize}\n`;
        report += `- Taille min: ${stats.pools.minSize}\n`;
        report += `- Taille max: ${stats.pools.maxSize}\n\n`;
        
        report += `## Matchs\n`;
        report += `- Total: ${stats.matches.total}\n\n`;
        
        report += `### Par horaire\n`;
        Utils.TIMES.forEach(time => {
            report += `- ${time}: ${stats.matches.byTime[time]}\n`;
        });
        
        report += `\n## Institutions\n`;
        report += `- Nombre: ${stats.institutions.count}\n\n`;
        
        // Sort by count
        const sortedInsts = Object.entries(stats.institutions.distribution)
            .sort((a, b) => b[1] - a[1]);
        
        sortedInsts.forEach(([name, count]) => {
            report += `- ${name}: ${count} équipe(s)\n`;
        });
        
        return report;
    }
}

// Create global instance
window.statistics = new Statistics();
