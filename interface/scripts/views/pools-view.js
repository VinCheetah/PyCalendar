/**
 * pools-view.js - Vue Poules (classements et matchs par poule)
 * 
 * Affiche les matchs organisés par poule avec classements.
 * Priorité 2 selon les spécifications.
 */

class PoolsView {
    constructor(dataManager, container) {
        this.dataManager = dataManager;
        this.container = container;
        this.expandedPools = new Set();
        this.selectedFilters = {};
        
        // Subscribe to data changes
        this.dataManager.subscribe('matches', () => this.render());
    }
    
    /**
     * Initialise la vue
     */
    init() {
        this.render();
    }
    
    /**
     * Définit les filtres actifs
     */
    setFilters(filters) {
        this.selectedFilters = filters;
        this.render();
    }
    
    /**
     * Affiche la vue complète
     */
    render() {
        const data = this.dataManager.getData();
        
        if (!data || !data.entities?.poules) {
            this.renderEmpty();
            return;
        }
        
        // Filtrer les poules selon les filtres actifs
        const filteredPools = this._filterPools(data.entities.poules);
        
        if (filteredPools.length === 0) {
            this.renderNoResults();
            return;
        }
        
        // Générer le HTML
        const html = this._generateHTML(filteredPools, data);
        
        this.container.innerHTML = html;
        
        // Attacher les event listeners
        this._attachEventListeners();
    }
    
    /**
     * Affiche l'état vide
     */
    renderEmpty() {
        this.container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">🎯</div>
                <h3 class="empty-state-title">Aucune poule</h3>
                <p class="empty-state-message">Les poules apparaîtront ici une fois configurées.</p>
            </div>
        `;
    }
    
    /**
     * Affiche aucun résultat
     */
    renderNoResults() {
        this.container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">🔍</div>
                <h3 class="empty-state-title">Aucune poule correspondante</h3>
                <p class="empty-state-message">Aucune poule ne correspond aux filtres sélectionnés.</p>
            </div>
        `;
    }
    
    /**
     * Filtre les poules selon les filtres actifs
     */
    _filterPools(pools) {
        return pools.filter(pool => {
            // Filtre par genre
            if (this.selectedFilters.gender && pool.genre !== this.selectedFilters.gender) {
                return false;
            }
            
            // Filtre par poule (ID exact)
            if (this.selectedFilters.pool && pool.id !== this.selectedFilters.pool) {
                return false;
            }
            
            return true;
        });
    }
    
    /**
     * Génère le HTML de la vue
     */
    _generateHTML(pools, data) {
        let html = '<div class="pools-view">';
        
        // En-tête avec résumé
        html += this._generateSummary(pools, data);
        
        // Liste des poules
        html += '<div class="pools-list">';
        
        pools.forEach(pool => {
            html += this._generatePoolCard(pool, data);
        });
        
        html += '</div></div>';
        
        return html;
    }
    
    /**
     * Génère le résumé global
     */
    _generateSummary(pools, data) {
        const totalTeams = pools.reduce((sum, p) => sum + p.nb_equipes, 0);
        const totalMatches = pools.reduce((sum, p) => {
            const stats = data.statistics?.by_pool?.[p.id];
            return sum + (stats?.nb_matchs || 0);
        }, 0);
        
        return `
            <div class="pools-summary">
                <div class="summary-card">
                    <div class="summary-value">${pools.length}</div>
                    <div class="summary-label">Poules</div>
                </div>
                <div class="summary-card">
                    <div class="summary-value">${totalTeams}</div>
                    <div class="summary-label">Équipes</div>
                </div>
                <div class="summary-card">
                    <div class="summary-value">${totalMatches}</div>
                    <div class="summary-label">Matchs</div>
                </div>
            </div>
        `;
    }
    
    /**
     * Génère la carte d'une poule
     */
    _generatePoolCard(pool, data) {
        const isExpanded = this.expandedPools.has(pool.id);
        const genderClass = pool.genre === 'M' ? 'male' : 'female';
        const genderIcon = pool.genre === 'M' ? '♂️' : '♀️';
        
        // Récupérer les équipes de la poule
        const poolTeams = this._getPoolTeams(pool.id, data);
        
        // Récupérer les matchs de la poule
        const poolMatches = this.dataManager.getMatchesByPool(pool.id);
        
        // Stats de la poule
        const stats = data.statistics?.by_pool?.[pool.id] || {};
        
        let html = `
            <div class="pool-card ${genderClass}" data-pool-id="${pool.id}">
                <div class="pool-header" data-toggle-pool="${pool.id}">
                    <div class="pool-title">
                        <h3>${pool.nom}</h3>
                        <span class="pool-gender">${genderIcon}</span>
                    </div>
                    <div class="pool-info">
                        <span class="pool-level">Niveau ${pool.niveau || 'N/A'}</span>
                        <span class="pool-teams">👥 ${pool.nb_equipes} équipes</span>
                        <span class="pool-matches">⚽ ${poolMatches.length} matchs</span>
                    </div>
                    <button class="expand-btn ${isExpanded ? 'expanded' : ''}">
                        ${isExpanded ? '▼' : '▶'}
                    </button>
                </div>
        `;
        
        if (isExpanded) {
            html += '<div class="pool-content">';
            
            // Classement
            html += this._generateStandings(poolTeams, poolMatches, data);
            
            // Liste des matchs
            html += this._generatePoolMatches(poolMatches, data);
            
            html += '</div>';
        }
        
        html += '</div>';
        
        return html;
    }
    
    /**
     * Récupère les équipes d'une poule
     */
    _getPoolTeams(poolId, data) {
        if (!data.entities?.equipes) return [];
        
        return data.entities.equipes.filter(e => e.poule === poolId);
    }
    
    /**
     * Génère le classement d'une poule
     */
    _generateStandings(teams, matches, data) {
        // Calculer les stats des équipes
        const standings = this._calculateStandings(teams, matches);
        
        let html = `
            <div class="pool-standings">
                <h4>📊 Classement</h4>
                <table class="standings-table">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Équipe</th>
                            <th>J</th>
                            <th>G</th>
                            <th>N</th>
                            <th>P</th>
                            <th>Pts</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        standings.forEach((team, index) => {
            html += `
                <tr>
                    <td>${index + 1}</td>
                    <td class="team-name">${team.nom}</td>
                    <td>${team.played}</td>
                    <td>${team.won}</td>
                    <td>${team.drawn}</td>
                    <td>${team.lost}</td>
                    <td class="points"><strong>${team.points}</strong></td>
                </tr>
            `;
        });
        
        html += `
                    </tbody>
                </table>
            </div>
        `;
        
        return html;
    }
    
    /**
     * Calcule le classement
     */
    _calculateStandings(teams, matches) {
        const stats = {};
        
        // Initialiser les stats
        teams.forEach(team => {
            stats[team.id] = {
                id: team.id,
                nom: team.nom,
                played: 0,
                won: 0,
                drawn: 0,
                lost: 0,
                points: 0
            };
        });
        
        // Compter les matchs (simplifié - pas de scores réels)
        matches.forEach(match => {
            if (match.equipes && match.equipes.length === 2) {
                const [team1, team2] = match.equipes;
                
                if (stats[team1]) stats[team1].played++;
                if (stats[team2]) stats[team2].played++;
                
                // Note: Sans scores réels, on ne peut pas calculer victoires/défaites
                // On affiche juste les matchs joués
            }
        });
        
        // Trier par points puis nom
        return Object.values(stats).sort((a, b) => {
            if (b.points !== a.points) return b.points - a.points;
            return a.nom.localeCompare(b.nom);
        });
    }
    
    /**
     * Génère la liste des matchs d'une poule
     */
    _generatePoolMatches(matches, data) {
        if (matches.length === 0) {
            return `
                <div class="pool-matches">
                    <h4>⚽ Matchs</h4>
                    <p class="no-matches">Aucun match planifié</p>
                </div>
            `;
        }
        
        // Grouper par semaine
        const byWeek = new Map();
        matches.forEach(match => {
            const week = match.semaine || 'Non planifié';
            if (!byWeek.has(week)) {
                byWeek.set(week, []);
            }
            byWeek.get(week).push(match);
        });
        
        let html = `
            <div class="pool-matches">
                <h4>⚽ Matchs (${matches.length})</h4>
        `;
        
        // Trier les semaines
        const sortedWeeks = Array.from(byWeek.keys()).sort((a, b) => {
            if (a === 'Non planifié') return 1;
            if (b === 'Non planifié') return -1;
            return a - b;
        });
        
        sortedWeeks.forEach(week => {
            const weekMatches = byWeek.get(week);
            
            html += `<div class="week-group">`;
            html += `<h5>Semaine ${week}</h5>`;
            html += `<div class="matches-grid">`;
            
            weekMatches.forEach(match => {
                html += this._generateMatchCard(match, data);
            });
            
            html += `</div></div>`;
        });
        
        html += `</div>`;
        
        return html;
    }
    
    /**
     * Génère une carte de match compacte
     */
    _generateMatchCard(match, data) {
        const equipes = this.dataManager.getEquipesByIds(match.equipes);
        const gymnase = this.dataManager.getGymnaseById(match.gymnase);
        
        const equipe1 = equipes[0] || { nom: 'Équipe 1' };
        const equipe2 = equipes[1] || { nom: 'Équipe 2' };
        
        const totalPenalties = Object.values(match.penalties || {}).reduce((sum, p) => sum + p, 0);
        const penaltyClass = totalPenalties > 10 ? 'high' : totalPenalties > 5 ? 'medium' : 'low';
        
        return `
            <div class="match-card mini" data-match-id="${match.match_id}">
                <div class="match-time">
                    ${match.jour || 'N/A'} ${match.horaire}
                </div>
                <div class="match-teams-mini">
                    <span class="team">${equipe1.nom}</span>
                    <span class="vs">-</span>
                    <span class="team">${equipe2.nom}</span>
                </div>
                <div class="match-venue-mini">
                    📍 ${gymnase?.nom || 'N/A'}
                </div>
                <span class="match-penalty-badge penalty-${penaltyClass}">${totalPenalties.toFixed(1)}</span>
            </div>
        `;
    }
    
    /**
     * Attache les event listeners
     */
    _attachEventListeners() {
        // Toggle expand/collapse
        const toggleBtns = this.container.querySelectorAll('[data-toggle-pool]');
        toggleBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const poolId = e.currentTarget.dataset.togglePool;
                this.togglePool(poolId);
            });
        });
        
        // Double-clic sur match pour éditer
        const matchCards = this.container.querySelectorAll('.match-card');
        matchCards.forEach(card => {
            card.addEventListener('dblclick', (e) => {
                const matchId = e.currentTarget.dataset.matchId;
                this._editMatch(matchId);
            });
        });
    }
    
    /**
     * Toggle l'expansion d'une poule
     */
    togglePool(poolId) {
        if (this.expandedPools.has(poolId)) {
            this.expandedPools.delete(poolId);
        } else {
            this.expandedPools.add(poolId);
        }
        
        this.render();
    }
    
    /**
     * Édite un match
     */
    _editMatch(matchId) {
        // TODO: Ouvrir le modal d'édition
        console.log('Edit match:', matchId);
    }
    
    /**
     * Nettoie la vue
     */
    destroy() {
        this.container.innerHTML = '';
        this.expandedPools.clear();
    }
}

// Export pour utilisation
window.PoolsView = PoolsView;
