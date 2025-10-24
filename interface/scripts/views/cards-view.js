/**
 * cards-view.js - Vue Cartes (grille de cartes filtrables)
 * 
 * Affiche tous les matchs sous forme de cartes dans une grille.
 * Priorité 3 selon les spécifications.
 */

class CardsView {
    constructor(dataManager, container) {
        this.dataManager = dataManager;
        this.container = container;
        this.selectedFilters = {};
        this.sortBy = 'week'; // week, pool, venue, penalties
        this.colorMode = 'gender'; // gender, level, institution
        
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
     * Change le mode de tri
     */
    setSortMode(sortBy) {
        this.sortBy = sortBy;
        this.render();
    }
    
    /**
     * Change le mode de coloration
     */
    setColorMode(colorMode) {
        this.colorMode = colorMode;
        this.render();
    }
    
    /**
     * Affiche la vue complète
     */
    render() {
        const data = this.dataManager.getData();
        
        if (!data || !data.matches) {
            this.renderEmpty();
            return;
        }
        
        // Appliquer les filtres
        const filteredMatches = this._applyFilters(data.matches.scheduled);
        
        if (filteredMatches.length === 0) {
            this.renderNoResults();
            return;
        }
        
        // Trier les matchs
        const sortedMatches = this._sortMatches(filteredMatches);
        
        // Générer le HTML
        const html = this._generateHTML(sortedMatches, data);
        
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
                <div class="empty-state-icon">🃏</div>
                <h3 class="empty-state-title">Aucun match</h3>
                <p class="empty-state-message">Les matchs apparaîtront ici une fois planifiés.</p>
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
                <h3 class="empty-state-title">Aucun résultat</h3>
                <p class="empty-state-message">Aucun match ne correspond aux filtres sélectionnés.</p>
            </div>
        `;
    }
    
    /**
     * Applique les filtres aux matchs
     */
    _applyFilters(matches) {
        if (Object.keys(this.selectedFilters).length === 0) {
            return matches;
        }
        
        return matches.filter(match => {
            // Filtre par genre
            if (this.selectedFilters.gender && match.genre !== this.selectedFilters.gender) {
                return false;
            }
            
            // Filtre par institution
            if (this.selectedFilters.institution) {
                const equipes = this.dataManager.getEquipesByIds(match.equipes);
                const hasInstitution = equipes.some(e => e.institution === this.selectedFilters.institution);
                if (!hasInstitution) return false;
            }
            
            // Filtre par poule
            if (this.selectedFilters.pool && match.poule !== this.selectedFilters.pool) {
                return false;
            }
            
            // Filtre par gymnase
            if (this.selectedFilters.venue && match.gymnase !== this.selectedFilters.venue) {
                return false;
            }
            
            // Filtre par semaine
            if (this.selectedFilters.week && match.semaine !== parseInt(this.selectedFilters.week)) {
                return false;
            }
            
            return true;
        });
    }
    
    /**
     * Trie les matchs selon le mode choisi
     */
    _sortMatches(matches) {
        const sorted = [...matches];
        
        switch (this.sortBy) {
            case 'week':
                sorted.sort((a, b) => {
                    if (a.semaine !== b.semaine) return a.semaine - b.semaine;
                    return a.horaire.localeCompare(b.horaire);
                });
                break;
                
            case 'pool':
                sorted.sort((a, b) => {
                    if (a.poule !== b.poule) return a.poule.localeCompare(b.poule);
                    return a.semaine - b.semaine;
                });
                break;
                
            case 'venue':
                sorted.sort((a, b) => {
                    if (a.gymnase !== b.gymnase) return a.gymnase.localeCompare(b.gymnase);
                    return a.semaine - b.semaine;
                });
                break;
                
            case 'penalties':
                sorted.sort((a, b) => {
                    const penA = Object.values(a.penalties || {}).reduce((sum, p) => sum + p, 0);
                    const penB = Object.values(b.penalties || {}).reduce((sum, p) => sum + p, 0);
                    return penB - penA; // Décroissant
                });
                break;
        }
        
        return sorted;
    }
    
    /**
     * Génère le HTML de la vue
     */
    _generateHTML(matches, data) {
        let html = '<div class="cards-view">';
        
        // Contrôles de la vue
        html += this._generateControls(matches);
        
        // Grille de cartes
        html += '<div class="cards-grid">';
        
        matches.forEach(match => {
            html += this._generateMatchCard(match, data);
        });
        
        html += '</div></div>';
        
        return html;
    }
    
    /**
     * Génère les contrôles de la vue
     */
    _generateControls(matches) {
        return `
            <div class="cards-controls">
                <div class="control-group">
                    <label>Trier par :</label>
                    <select class="sort-select" id="cards-sort">
                        <option value="week" ${this.sortBy === 'week' ? 'selected' : ''}>Semaine</option>
                        <option value="pool" ${this.sortBy === 'pool' ? 'selected' : ''}>Poule</option>
                        <option value="venue" ${this.sortBy === 'venue' ? 'selected' : ''}>Gymnase</option>
                        <option value="penalties" ${this.sortBy === 'penalties' ? 'selected' : ''}>Pénalités</option>
                    </select>
                </div>
                
                <div class="control-group">
                    <label>Coloration :</label>
                    <select class="color-select" id="cards-color">
                        <option value="gender" ${this.colorMode === 'gender' ? 'selected' : ''}>Genre</option>
                        <option value="level" ${this.colorMode === 'level' ? 'selected' : ''}>Niveau</option>
                        <option value="institution" ${this.colorMode === 'institution' ? 'selected' : ''}>Institution</option>
                    </select>
                </div>
                
                <div class="cards-count">
                    ${matches.length} match${matches.length > 1 ? 's' : ''}
                </div>
            </div>
        `;
    }
    
    /**
     * Génère une carte de match
     */
    _generateMatchCard(match, data) {
        const equipes = this.dataManager.getEquipesByIds(match.equipes);
        const gymnase = this.dataManager.getGymnaseById(match.gymnase);
        const poule = this.dataManager.getPouleById(match.poule);
        
        const equipe1 = equipes[0] || { nom: 'Équipe 1', institution: 'N/A' };
        const equipe2 = equipes[1] || { nom: 'Équipe 2', institution: 'N/A' };
        
        // Calculer la classe de couleur selon le mode
        let colorClass = '';
        switch (this.colorMode) {
            case 'gender':
                colorClass = match.genre === 'M' ? 'color-male' : 'color-female';
                break;
            case 'level':
                colorClass = poule ? `color-level-${poule.niveau || 1}` : 'color-neutral';
                break;
            case 'institution':
                // Hash simple du nom d'institution pour couleur consistante
                const hash = (equipe1.institution || '').split('').reduce((a, b) => {
                    a = ((a << 5) - a) + b.charCodeAt(0);
                    return a & a;
                }, 0);
                colorClass = `color-institution-${Math.abs(hash) % 5}`;
                break;
        }
        
        // Calculer les pénalités
        const penalties = match.penalties || {};
        const totalPenalties = Object.values(penalties).reduce((sum, p) => sum + p, 0);
        const penaltyClass = totalPenalties > 10 ? 'high' : totalPenalties > 5 ? 'medium' : 'low';
        
        // Icône de genre
        const genderIcon = match.genre === 'M' ? '♂️' : '♀️';
        
        return `
            <div class="match-card ${colorClass}" data-match-id="${match.match_id}">
                <div class="card-header">
                    <span class="card-week">S${match.semaine}</span>
                    <span class="card-gender">${genderIcon}</span>
                    <span class="card-penalty penalty-${penaltyClass}">${totalPenalties.toFixed(1)}</span>
                </div>
                
                <div class="card-body">
                    <div class="card-pool">${poule?.nom || match.poule || 'N/A'}</div>
                    
                    <div class="card-teams">
                        <div class="team">
                            <div class="team-name">${equipe1.nom}</div>
                            <div class="team-institution">${equipe1.institution}</div>
                        </div>
                        
                        <div class="vs">VS</div>
                        
                        <div class="team">
                            <div class="team-name">${equipe2.nom}</div>
                            <div class="team-institution">${equipe2.institution}</div>
                        </div>
                    </div>
                    
                    <div class="card-info">
                        <div class="info-item">
                            <span class="icon">📅</span>
                            <span>${match.jour || 'N/A'}</span>
                        </div>
                        <div class="info-item">
                            <span class="icon">🕐</span>
                            <span>${match.horaire}</span>
                        </div>
                        <div class="info-item">
                            <span class="icon">📍</span>
                            <span>${gymnase?.nom || 'N/A'}</span>
                        </div>
                    </div>
                </div>
                
                ${totalPenalties > 0 ? this._generatePenaltiesDetail(penalties) : ''}
            </div>
        `;
    }
    
    /**
     * Génère le détail des pénalités
     */
    _generatePenaltiesDetail(penalties) {
        const items = Object.entries(penalties)
            .filter(([_, value]) => value > 0)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 3); // Top 3
        
        if (items.length === 0) return '';
        
        let html = '<div class="card-penalties">';
        html += '<div class="penalties-title">Pénalités :</div>';
        html += '<div class="penalties-list">';
        
        items.forEach(([type, value]) => {
            const label = this._getPenaltyLabel(type);
            html += `<div class="penalty-item">${label}: ${value.toFixed(1)}</div>`;
        });
        
        html += '</div></div>';
        
        return html;
    }
    
    /**
     * Obtient le label d'un type de pénalité
     */
    _getPenaltyLabel(type) {
        const labels = {
            'consecutive_home': 'Domicile consécutif',
            'consecutive_away': 'Extérieur consécutif',
            'same_day': 'Même jour',
            'unavailable_slot': 'Créneau indispo',
            'capacity': 'Capacité',
            'institution_conflict': 'Conflit établ.',
            'total': 'Total'
        };
        
        return labels[type] || type;
    }
    
    /**
     * Attache les event listeners
     */
    _attachEventListeners() {
        // Tri
        const sortSelect = this.container.querySelector('#cards-sort');
        if (sortSelect) {
            sortSelect.addEventListener('change', (e) => {
                this.setSortMode(e.target.value);
            });
        }
        
        // Coloration
        const colorSelect = this.container.querySelector('#cards-color');
        if (colorSelect) {
            colorSelect.addEventListener('change', (e) => {
                this.setColorMode(e.target.value);
            });
        }
        
        // Double-clic sur carte pour éditer
        const matchCards = this.container.querySelectorAll('.match-card');
        matchCards.forEach(card => {
            card.addEventListener('dblclick', (e) => {
                const matchId = e.currentTarget.dataset.matchId;
                this._editMatch(matchId);
            });
        });
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
    }
}

// Export pour utilisation
window.CardsView = CardsView;
