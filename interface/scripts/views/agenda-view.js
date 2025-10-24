/**
 * agenda-view.js - Vue Agenda (calendrier par semaine)
 * 
 * Affiche les matchs organisés par semaine dans un format calendrier.
 * Priorité 1 selon les spécifications.
 */

class AgendaView {
    constructor(dataManager, container) {
        this.dataManager = dataManager;
        this.container = container;
        this.currentWeek = null;
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
        
        if (!data || !data.matches) {
            this.renderEmpty();
            return;
        }
        
        // Grouper les matchs par semaine
        const matchesByWeek = this._groupByWeek(data.matches.scheduled);
        
        // Appliquer les filtres
        const filteredMatches = this._applyFilters(matchesByWeek);
        
        // Générer le HTML
        const html = this._generateHTML(filteredMatches, data);
        
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
                <div class="empty-state-icon">📋</div>
                <h3 class="empty-state-title">Aucun match planifié</h3>
                <p class="empty-state-message">Les matchs apparaîtront ici une fois planifiés.</p>
            </div>
        `;
    }
    
    /**
     * Groupe les matchs par semaine
     */
    _groupByWeek(matches) {
        const grouped = new Map();
        
        matches.forEach(match => {
            const week = match.semaine;
            if (!grouped.has(week)) {
                grouped.set(week, []);
            }
            grouped.get(week).push(match);
        });
        
        // Trier par semaine
        return new Map([...grouped.entries()].sort((a, b) => a[0] - b[0]));
    }
    
    /**
     * Applique les filtres aux matchs
     */
    _applyFilters(matchesByWeek) {
        if (Object.keys(this.selectedFilters).length === 0) {
            return matchesByWeek;
        }
        
        const filtered = new Map();
        
        matchesByWeek.forEach((matches, week) => {
            const filteredMatches = matches.filter(match => {
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
            
            if (filteredMatches.length > 0) {
                filtered.set(week, filteredMatches);
            }
        });
        
        return filtered;
    }
    
    /**
     * Génère le HTML de la vue
     */
    _generateHTML(matchesByWeek, data) {
        if (matchesByWeek.size === 0) {
            return `
                <div class="empty-state">
                    <div class="empty-state-icon">🔍</div>
                    <h3 class="empty-state-title">Aucun résultat</h3>
                    <p class="empty-state-message">Aucun match ne correspond aux filtres sélectionnés.</p>
                </div>
            `;
        }
        
        let html = '<div class="agenda-view">';
        
        // Navigation semaines
        html += this._generateWeekNavigation(matchesByWeek);
        
        // Contenu par semaine
        matchesByWeek.forEach((matches, week) => {
            html += this._generateWeekSection(week, matches, data);
        });
        
        html += '</div>';
        
        return html;
    }
    
    /**
     * Génère la navigation entre semaines
     */
    _generateWeekNavigation(matchesByWeek) {
        const weeks = Array.from(matchesByWeek.keys());
        
        let html = '<div class="week-navigation">';
        html += '<div class="week-tabs">';
        
        weeks.forEach((week, index) => {
            const isActive = this.currentWeek === week || (this.currentWeek === null && index === 0);
            html += `
                <button class="week-tab ${isActive ? 'active' : ''}" data-week="${week}">
                    Semaine ${week}
                </button>
            `;
        });
        
        html += '</div></div>';
        
        return html;
    }
    
    /**
     * Génère la section d'une semaine
     */
    _generateWeekSection(week, matches, data) {
        const isActive = this.currentWeek === week || (this.currentWeek === null && week === 1);
        
        // Grouper par jour/horaire
        const bySlot = this._groupBySlot(matches);
        
        let html = `<div class="week-section ${isActive ? 'active' : ''}" data-week="${week}">`;
        html += `<h2 class="week-title">📅 Semaine ${week}</h2>`;
        
        // Stats de la semaine
        const stats = data.statistics?.by_week?.[week];
        if (stats) {
            html += `
                <div class="week-stats">
                    <span class="stat-item">⚽ ${stats.nb_matchs} matchs</span>
                    <span class="stat-item">🏟️ ${stats.nb_gymnases} gymnases</span>
                </div>
            `;
        }
        
        // Grille de matchs
        html += '<div class="agenda-grid">';
        
        bySlot.forEach((slotMatches, slotKey) => {
            html += this._generateSlot(slotKey, slotMatches, data);
        });
        
        html += '</div></div>';
        
        return html;
    }
    
    /**
     * Groupe les matchs par créneau (jour + horaire)
     */
    _groupBySlot(matches) {
        const grouped = new Map();
        
        matches.forEach(match => {
            const key = `${match.jour || 'Non défini'}_${match.horaire}`;
            if (!grouped.has(key)) {
                grouped.set(key, []);
            }
            grouped.get(key).push(match);
        });
        
        // Trier par horaire
        return new Map([...grouped.entries()].sort((a, b) => {
            const timeA = a[0].split('_')[1];
            const timeB = b[0].split('_')[1];
            return timeA.localeCompare(timeB);
        }));
    }
    
    /**
     * Génère un créneau horaire avec ses matchs
     */
    _generateSlot(slotKey, matches, data) {
        const [jour, horaire] = slotKey.split('_');
        
        let html = '<div class="time-slot">';
        html += `
            <div class="slot-header">
                <span class="slot-day">${jour}</span>
                <span class="slot-time">🕐 ${horaire}</span>
            </div>
        `;
        
        html += '<div class="slot-matches">';
        
        matches.forEach(match => {
            html += this._generateMatchCard(match, data);
        });
        
        html += '</div></div>';
        
        return html;
    }
    
    /**
     * Génère une carte de match
     */
    _generateMatchCard(match, data) {
        const equipes = this.dataManager.getEquipesByIds(match.equipes);
        const gymnase = this.dataManager.getGymnaseById(match.gymnase);
        
        const equipe1 = equipes[0] || { nom: 'Équipe 1' };
        const equipe2 = equipes[1] || { nom: 'Équipe 2' };
        
        const genderClass = match.genre === 'M' ? 'male' : 'female';
        const totalPenalties = Object.values(match.penalties || {}).reduce((sum, p) => sum + p, 0);
        const penaltyClass = totalPenalties > 10 ? 'high' : totalPenalties > 5 ? 'medium' : 'low';
        
        return `
            <div class="match-card compact ${genderClass}" data-match-id="${match.match_id}">
                <div class="match-header">
                    <span class="match-pool">${match.poule || 'N/A'}</span>
                    <span class="match-penalty penalty-${penaltyClass}">${totalPenalties.toFixed(1)}</span>
                </div>
                <div class="match-teams">
                    <div class="team">${equipe1.nom}</div>
                    <div class="vs">vs</div>
                    <div class="team">${equipe2.nom}</div>
                </div>
                <div class="match-footer">
                    <span class="match-venue">📍 ${gymnase?.nom || 'N/A'}</span>
                </div>
            </div>
        `;
    }
    
    /**
     * Attache les event listeners
     */
    _attachEventListeners() {
        // Navigation entre semaines
        const weekTabs = this.container.querySelectorAll('.week-tab');
        weekTabs.forEach(tab => {
            tab.addEventListener('click', (e) => {
                const week = parseInt(e.target.dataset.week);
                this.switchToWeek(week);
            });
        });
        
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
     * Bascule vers une semaine spécifique
     */
    switchToWeek(week) {
        this.currentWeek = week;
        
        // Update tabs
        this.container.querySelectorAll('.week-tab').forEach(tab => {
            tab.classList.toggle('active', parseInt(tab.dataset.week) === week);
        });
        
        // Update sections
        this.container.querySelectorAll('.week-section').forEach(section => {
            section.classList.toggle('active', parseInt(section.dataset.week) === week);
        });
    }
    
    /**
     * Édite un match (à implémenter avec le modal)
     */
    _editMatch(matchId) {
        // TODO: Ouvrir le modal d'édition
        console.log('Edit match:', matchId);
        
        // Pour l'instant, log simple
        const match = this.dataManager.getMatchById(matchId);
        if (match) {
            console.log('Match data:', match);
        }
    }
    
    /**
     * Nettoie la vue
     */
    destroy() {
        this.container.innerHTML = '';
    }
}

// Export pour utilisation
window.AgendaView = AgendaView;
