/**
 * teams-view.js - Vue Équipes
 * 
 * Affiche la liste des équipes avec statistiques détaillées :
 * - Format tableau condensé avec toutes les statistiques importantes
 * - Tri et groupement flexibles
 * - Compatible avec tous les filtres existants
 * - Design cohérent avec le reste de l'interface
 */

class TeamsView {
    constructor(dataManager, container) {
        this.dataManager = dataManager;
        this.container = container;
        this.expandedTeams = new Set();
        
        // État des filtres (compatible avec le système de filtres global)
        this.activeFilters = {
            gender: '',
            institution: '',
            pool: '',
            venue: '',
            week: '',
            equipe: '',
            horaireStart: null,
            horaireEnd: null
        };
        
        // Options d'affichage
        this.groupBy = 'none'; // 'none', 'gender', 'institution', 'pool', 'level'
        this.sortBy = 'name'; // 'name', 'institution', 'matches', 'scheduled', 'played', 'points', 'victories', 'pointsDiff', 'completion', 'penalties'
        this.sortOrder = 'asc'; // 'asc', 'desc'
        this.colorBy = 'none'; // 'none', 'completion', 'performance', 'penalties', 'pointsDiff'
        this.showPerformance = true;
        this.showPlanning = true;
        this.showPenalties = true;
        this.showPreferences = false;
        this.showGlobalSummary = true;
        this.compactMode = false;
        
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
     * Définit les filtres actifs (compatible avec EnhancedFilterSystem)
     */
    setFilters(filters) {
        this.activeFilters = { ...this.activeFilters, ...filters };
        this.render();
    }
    
    /**
     * Change le mode de groupement
     */
    setGroupBy(groupBy) {
        this.groupBy = groupBy;
        this.render();
    }
    
    /**
     * Change le mode de tri
     */
    setSortBy(sortBy) {
        this.sortBy = sortBy;
        this.render();
    }
    
    /**
     * Change l'ordre de tri
     */
    setSortOrder(order) {
        this.sortOrder = order;
        this.render();
    }
    
    /**
     * Change le critère de coloration
     */
    setColorBy(colorBy) {
        this.colorBy = colorBy;
        this.render();
    }
    
    /**
     * Retourne la configuration des options d'affichage
     */
    getDisplayOptions() {
        return {
            title: "Options - Vue Équipes",
            options: [
                // Grouper par
                {
                    type: 'button-group',
                    id: 'teams-group-by',
                    label: '📊 Grouper par',
                    values: [
                        { value: 'none', text: 'Aucun' },
                        { value: 'gender', text: '👥 Genre' },
                        { value: 'institution', text: '🏫 Institution' },
                        { value: 'pool', text: '🎯 Poule' },
                        { value: 'level', text: '📈 Niveau' }
                    ],
                    default: this.groupBy,
                    action: (value) => {
                        this.setGroupBy(value);
                    }
                },
                
                // Trier par
                {
                    type: 'select',
                    id: 'teams-sort-by',
                    label: '🔄 Trier par',
                    values: [
                        { value: 'name', text: 'Nom' },
                        { value: 'institution', text: 'Institution' },
                        { value: 'matches', text: 'Nombre de matchs total' },
                        { value: 'scheduled', text: 'Matchs effectifs (planifiés + ententes)' },
                        { value: 'played', text: 'Matchs joués (avec score)' },
                        { value: 'points', text: 'Points' },
                        { value: 'victories', text: 'Victoires' },
                        { value: 'pointsDiff', text: 'Différence de points' },
                        { value: 'completion', text: 'Taux de complétion' },
                        { value: 'penalties', text: 'Pénalités' }
                    ],
                    default: this.sortBy,
                    action: (value) => {
                        this.setSortBy(value);
                    }
                },
                
                // Ordre de tri
                {
                    type: 'button-group',
                    id: 'teams-sort-order',
                    label: '↕️ Ordre',
                    values: [
                        { value: 'asc', text: '↑ Croissant' },
                        { value: 'desc', text: '↓ Décroissant' }
                    ],
                    default: this.sortOrder,
                    action: (value) => {
                        this.setSortOrder(value);
                    }
                },
                
                // Coloration des équipes
                {
                    type: 'select',
                    id: 'teams-color-by',
                    label: '🎨 Colorer par',
                    values: [
                        { value: 'none', text: 'Aucune coloration' },
                        { value: 'completion', text: 'Taux de complétion' },
                        { value: 'performance', text: 'Performance (points)' },
                        { value: 'pointsDiff', text: 'Différence de points' },
                        { value: 'penalties', text: 'Pénalités' }
                    ],
                    default: this.colorBy,
                    action: (value) => {
                        this.setColorBy(value);
                    }
                },
                
                // Colonnes à afficher
                {
                    type: 'checkbox',
                    id: 'teams-show-performance',
                    label: '🏆 Afficher performance',
                    default: this.showPerformance,
                    action: (checked) => {
                        this.showPerformance = checked;
                        this.render();
                    }
                },
                
                {
                    type: 'checkbox',
                    id: 'teams-show-planning',
                    label: '📅 Afficher planning',
                    default: this.showPlanning,
                    action: (checked) => {
                        this.showPlanning = checked;
                        this.render();
                    }
                },
                
                {
                    type: 'checkbox',
                    id: 'teams-show-penalties',
                    label: '⚠️ Afficher pénalités',
                    default: this.showPenalties,
                    action: (checked) => {
                        this.showPenalties = checked;
                        this.render();
                    }
                },
                
                {
                    type: 'checkbox',
                    id: 'teams-show-preferences',
                    label: '⭐ Afficher préférences',
                    default: this.showPreferences,
                    action: (checked) => {
                        this.showPreferences = checked;
                        this.render();
                    }
                },
                
                // Mode compact
                {
                    type: 'checkbox',
                    id: 'teams-compact-mode',
                    label: '📦 Mode compact',
                    default: this.compactMode,
                    action: (checked) => {
                        this.compactMode = checked;
                        this.render();
                    }
                },
                
                // Afficher résumé global
                {
                    type: 'checkbox',
                    id: 'teams-show-summary',
                    label: '📋 Afficher résumé global',
                    default: this.showGlobalSummary,
                    action: (checked) => {
                        this.showGlobalSummary = checked;
                        this.render();
                    }
                }
            ]
        };
    }
    
    /**
     * Affiche la vue complète
     */
    render() {
        const data = this.dataManager.getData();
        
        if (!data || !data.entities?.equipes) {
            this.renderEmpty();
            return;
        }
        
        // Filtrer et enrichir les équipes avec leurs statistiques
        const teams = this._getEnrichedTeams(data);
        const filteredTeams = this._filterTeams(teams);
        
        if (filteredTeams.length === 0) {
            this.renderNoResults();
            return;
        }
        
        // Trier les équipes
        const sortedTeams = this._sortTeams(filteredTeams);
        
        // Générer le HTML
        const html = this._generateHTML(sortedTeams, data);
        
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
                <div class="empty-state__icon">👥</div>
                <h3 class="empty-state__title">Aucune équipe</h3>
                <p class="empty-state__message">Les équipes apparaîtront ici une fois configurées.</p>
            </div>
        `;
    }
    
    /**
     * Affiche aucun résultat
     */
    renderNoResults() {
        this.container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state__icon">🔍</div>
                <h3 class="empty-state__title">Aucune équipe correspondante</h3>
                <p class="empty-state__message">Aucune équipe ne correspond aux filtres sélectionnés.</p>
            </div>
        `;
    }
    
    /**
     * Enrichit les équipes avec leurs statistiques
     */
    _getEnrichedTeams(data) {
        return data.entities.equipes.map(team => {
            const stats = this._calculateTeamStats(team, data);
            return {
                ...team,
                stats: stats
            };
        });
    }
    
    /**
     * Calcule les statistiques d'une équipe
     */
    _calculateTeamStats(team, data) {
        // Récupérer tous les matchs de l'équipe (en tant qu'équipe 1 ou 2)
        const allMatches = [
            ...data.matches.scheduled,
            ...data.matches.unscheduled
        ];
        
        const teamMatches = allMatches.filter(m => 
            m.equipe1_id === team.id || m.equipe2_id === team.id
        );
        
        // IMPORTANT: Les matchs "entente" SANS créneau sont considérés comme PLANIFIÉS
        // car ils seront joués en dehors du calendrier officiel
        const ententeMatches = teamMatches.filter(m => m.is_entente);

        const hasRecordedScore = (match) => 
            match.score && match.score.has_score &&
            match.score.equipe1 !== null && match.score.equipe1 !== undefined &&
            match.score.equipe2 !== null && match.score.equipe2 !== undefined;
        
        // Matchs planifiés = matchs avec créneau + matchs entente sans créneau
        const scheduledMatches = teamMatches.filter(m => m.semaine || m.is_entente);
        
        // Matchs NON planifiés = matchs sans créneau ET non entente
        const unscheduledMatches = teamMatches.filter(m => !m.semaine && !m.is_entente);
        
        // Matchs joués = score enregistré, même pour les ententes sans créneau
        const playedMatches = scheduledMatches.filter(hasRecordedScore);
        
        // Matchs à venir = planifiés (créneau ou entente) sans score enregistré
        const upcomingMatches = scheduledMatches.filter(m => !hasRecordedScore(m));
        
        // Statistiques de performance
        let won = 0, drawn = 0, lost = 0, points = 0;
        let pointsFor = 0, pointsAgainst = 0;
        
        playedMatches.forEach(match => {
            const isTeam1 = match.equipe1_id === team.id;
            const score1 = match.score.equipe1;
            const score2 = match.score.equipe2;
            
            if (isTeam1) {
                pointsFor += score1;
                pointsAgainst += score2;
                if (score1 > score2) {
                    won++;
                    points += 3;
                } else if (score1 === score2) {
                    drawn++;
                    points += 1;
                } else {
                    lost++;
                }
            } else {
                pointsFor += score2;
                pointsAgainst += score1;
                if (score2 > score1) {
                    won++;
                    points += 3;
                } else if (score2 === score1) {
                    drawn++;
                    points += 1;
                } else {
                    lost++;
                }
            }
        });
        
        // Statistiques de planning
        const weeksPlayed = new Set(
            scheduledMatches
                .map(m => m.semaine)
                .filter(week => week !== undefined && week !== null)
        ).size;
        const venuesUsed = new Set(
            scheduledMatches
                .map(m => m.gymnase)
                .filter(venue => venue !== undefined && venue !== null)
        ).size;
        
        // Pénalités
        const totalPenalties = teamMatches.reduce((sum, m) => {
            if (!m.penalties) return sum;
            // Use the total field directly if available, otherwise sum numeric values only
            if (typeof m.penalties.total === 'number') {
                return sum + m.penalties.total;
            }
            // Fallback: sum only numeric values (ignore nested objects like equipe1/equipe2)
            return sum + Object.values(m.penalties).reduce((s, p) => 
                typeof p === 'number' ? s + p : s, 0);
        }, 0);
        
        const avgPenalties = teamMatches.length > 0 ? totalPenalties / teamMatches.length : 0;
        
        // Taux de complétion: matchs planifiés / total matchs (y compris ententes planifiées)
        const completionRate = teamMatches.length > 0 
            ? (scheduledMatches.length / teamMatches.length) * 100 
            : 0;
        
        // Préférences respectées
        let preferencesRespected = 0;
        let preferencesTotal = 0;
        
        scheduledMatches.forEach(match => {
            // Vérifier horaires préférés
            if (team.horaires_preferes && team.horaires_preferes.length > 0) {
                preferencesTotal++;
                if (team.horaires_preferes.includes(match.horaire)) {
                    preferencesRespected++;
                }
            }
            
            // Vérifier lieux préférés
            if (team.lieux_preferes && team.lieux_preferes.length > 0) {
                preferencesTotal++;
                if (team.lieux_preferes.includes(match.gymnase)) {
                    preferencesRespected++;
                }
            }
        });
        
        const preferenceRate = preferencesTotal > 0 
            ? (preferencesRespected / preferencesTotal) * 100 
            : 100;
        
        // Statistiques détaillées des ententes
        const scheduledWithSlot = scheduledMatches.filter(m => m.semaine && !m.is_entente);
        const ententeScheduledWithSlot = scheduledMatches.filter(m => m.semaine && m.is_entente);
        const ententeScheduledNoSlot = scheduledMatches.filter(m => !m.semaine && m.is_entente);
        
        return {
            totalMatches: teamMatches.length,
            scheduled: scheduledMatches.length, // Inclut ententes sans créneau
            scheduledNonEntente: scheduledWithSlot.length, // Matchs normaux avec créneau
            scheduledEntente: ententeMatches.length, // TOUTES les ententes (comptées comme planifiées)
            unscheduled: unscheduledMatches.length, // Matchs NON planifiés (sans créneau ET non entente)
            played: playedMatches.length,
            upcoming: upcomingMatches.length,
            entente: ententeMatches.length, // Total ententes
            ententeScheduled: ententeMatches.length, // Toutes les ententes sont "planifiées"
            ententeUnscheduled: 0, // Plus d'ententes non planifiées par définition
            ententeWithSlot: ententeScheduledWithSlot.length, // Ententes avec créneau
            ententeNoSlot: ententeScheduledNoSlot.length, // Ententes sans créneau (= "à jouer hors calendrier")
            won: won,
            drawn: drawn,
            lost: lost,
            points: points,
            pointsFor: pointsFor,
            pointsAgainst: pointsAgainst,
            pointsDiff: pointsFor - pointsAgainst,
            weeksPlayed: weeksPlayed,
            venuesUsed: venuesUsed,
            totalPenalties: totalPenalties,
            avgPenalties: avgPenalties,
            completionRate: completionRate,
            preferenceRate: preferenceRate,
            matches: teamMatches
        };
    }
    
    /**
     * Filtre les équipes selon les filtres actifs
     * Les filtres se COMBINENT : semaine ET gymnase signifie "matchs cette semaine dans ce gymnase"
     */
    _filterTeams(teams) {
        return teams.filter(team => {
            // Filtre par genre (propriété de l'équipe)
            if (this.activeFilters.gender && team.genre !== this.activeFilters.gender) {
                return false;
            }
            
            // Filtre par institution (propriété de l'équipe)
            if (this.activeFilters.institution && team.institution !== this.activeFilters.institution) {
                return false;
            }
            
            // Filtre par poule (propriété de l'équipe)
            if (this.activeFilters.pool && team.poule !== this.activeFilters.pool) {
                return false;
            }
            
            // Filtre par équipe (ID exact ou liste séparée par virgules)
            if (this.activeFilters.equipe) {
                const equipeIds = this.activeFilters.equipe.split(',').map(id => id.trim());
                if (!equipeIds.includes(team.id)) {
                    return false;
                }
            }

            // Filtres combinés sur les matchs (semaine ET/OU gymnase ET/OU plage horaire)
            // Si au moins un filtre de match est actif, on vérifie que l'équipe a au moins un match
            // qui satisfait TOUS les critères de matchs actifs simultanément
            const hasWeekFilter = this.activeFilters.week !== null && this.activeFilters.week !== undefined && this.activeFilters.week !== '';
            const hasVenueFilter = this.activeFilters.venue !== null && this.activeFilters.venue !== undefined && this.activeFilters.venue !== '';
            const hasHoraireFilter = this.activeFilters.horaireStart && this.activeFilters.horaireEnd;
            
            if (hasWeekFilter || hasVenueFilter || hasHoraireFilter) {
                const weekNumber = hasWeekFilter ? parseInt(this.activeFilters.week) : null;
                const venue = hasVenueFilter ? this.activeFilters.venue : null;
                
                let rangeStart, rangeEnd;
                if (hasHoraireFilter) {
                    const [startHours, startMinutes] = this.activeFilters.horaireStart.split(':').map(Number);
                    const [endHours, endMinutes] = this.activeFilters.horaireEnd.split(':').map(Number);
                    rangeStart = startHours * 60 + startMinutes;
                    rangeEnd = endHours * 60 + endMinutes;
                }
                
                // L'équipe doit avoir AU MOINS UN match qui satisfait TOUS les critères actifs
                const hasMatchingMatch = team.stats.matches.some(match => {
                    // Vérifier la semaine (si filtre actif)
                    if (weekNumber !== null && match.semaine !== weekNumber) {
                        return false;
                    }
                    
                    // Vérifier le gymnase (si filtre actif)
                    if (venue !== null && match.gymnase !== venue) {
                        return false;
                    }
                    
                    // Vérifier la plage horaire (si filtre actif)
                    if (hasHoraireFilter) {
                        // Si le match n'a pas d'horaire, il passe le filtre horaire (matchs non planifiés, ententes)
                        if (match.horaire) {
                            const [hours, minutes] = match.horaire.split(':').map(Number);
                            const matchStartMinutes = hours * 60 + minutes;
                            
                            // Un match passe si son heure de DÉBUT est >= rangeStart ET <= rangeEnd
                            const inRange = matchStartMinutes >= rangeStart && matchStartMinutes <= rangeEnd;
                            if (!inRange) {
                                return false;
                            }
                        }
                        // Si pas d'horaire, le match passe le filtre
                    }
                    
                    // Le match satisfait tous les critères actifs
                    return true;
                });
                
                if (!hasMatchingMatch) {
                    return false;
                }
            }
            
            return true;
        });
    }
    
    /**
     * Trie les équipes selon les options de tri
     */
    _sortTeams(teams) {
        const sorted = [...teams].sort((a, b) => {
            let comparison = 0;
            
            switch (this.sortBy) {
                case 'name':
                    comparison = a.nom.localeCompare(b.nom);
                    break;
                case 'institution':
                    comparison = a.institution.localeCompare(b.institution);
                    break;
                case 'matches':
                    comparison = b.stats.totalMatches - a.stats.totalMatches;
                    break;
                case 'scheduled':
                    // Trier par matchs effectifs (planifiés + ententes)
                    comparison = b.stats.scheduled - a.stats.scheduled;
                    break;
                case 'played':
                    // Trier par matchs joués (avec score)
                    comparison = b.stats.played - a.stats.played;
                    break;
                case 'points':
                    comparison = b.stats.points - a.stats.points;
                    break;
                case 'victories':
                    comparison = b.stats.won - a.stats.won;
                    break;
                case 'pointsDiff':
                    comparison = b.stats.pointsDiff - a.stats.pointsDiff;
                    break;
                case 'completion':
                    comparison = b.stats.completionRate - a.stats.completionRate;
                    break;
                case 'penalties':
                    comparison = a.stats.totalPenalties - b.stats.totalPenalties;
                    break;
                default:
                    comparison = 0;
            }
            
            return this.sortOrder === 'asc' ? comparison : -comparison;
        });
        
        return sorted;
    }
    
    /**
     * Génère le HTML de la vue
     */
    _generateHTML(teams, data) {
        const compactClass = this.compactMode ? 'teams-view--compact' : '';
        let html = `<div class="teams-view ${compactClass}">`;
        
        // En-tête avec résumé global (optionnel)
        if (this.showGlobalSummary) {
            html += this._generateGlobalSummary(teams);
        }
        
        // Contenu selon le groupement
        if (this.groupBy === 'none') {
            html += this._generateTeamsTable(teams, data);
        } else {
            html += this._generateGroupedTeams(teams, data);
        }
        
        html += '</div>';
        
        return html;
    }
    
    /**
     * Génère le résumé global
     */
    _generateGlobalSummary(teams) {
        const totalTeams = teams.length;
        const totalMatches = teams.reduce((sum, t) => sum + t.stats.totalMatches, 0);
        const totalPlayed = teams.reduce((sum, t) => sum + t.stats.played, 0);
        const totalUnscheduled = teams.reduce((sum, t) => sum + t.stats.unscheduled, 0);
        const totalEntentes = teams.reduce((sum, t) => sum + t.stats.entente, 0);
        const avgCompletion = totalTeams > 0 
            ? teams.reduce((sum, t) => sum + t.stats.completionRate, 0) / totalTeams 
            : 0;
        
        // Utiliser SportUtils pour l'emoji du sport
        const sportEmoji = window.sportUtils?.getEmoji() || '🏐';
        const sportName = window.sportUtils?.getName() || 'Sport';
        
        return `
            <div class="teams-summary">
                <h2 class="teams-summary__title">
                    <span class="teams-summary__icon">${sportEmoji}</span>
                    Vue Équipes - ${sportName}
                    <span class="teams-summary__count">${totalTeams} équipe${totalTeams > 1 ? 's' : ''}</span>
                </h2>
                <div class="teams-summary__stats">
                    <div class="summary-stat summary-stat--primary">
                        <div class="summary-stat__value">${totalMatches}</div>
                        <div class="summary-stat__label">Matchs Total</div>
                    </div>
                    <div class="summary-stat summary-stat--success">
                        <div class="summary-stat__value">${totalPlayed}</div>
                        <div class="summary-stat__label">Joués</div>
                    </div>
                    <div class="summary-stat summary-stat--danger">
                        <div class="summary-stat__value">${totalUnscheduled}</div>
                        <div class="summary-stat__label">Non Planifiés</div>
                    </div>
                    ${totalEntentes > 0 ? `
                    <div class="summary-stat summary-stat--entente">
                        <div class="summary-stat__value">${totalEntentes}</div>
                        <div class="summary-stat__label">Ententes</div>
                    </div>
                    ` : ''}
                    <div class="summary-stat summary-stat--info">
                        <div class="summary-stat__value">${avgCompletion.toFixed(0)}%</div>
                        <div class="summary-stat__label">Complétion</div>
                    </div>
                </div>
            </div>
        `;
    }
    
    /**
     * Génère le tableau des équipes (sans groupement)
     */
    _generateTeamsTable(teams, data) {
        const compactClass = this.compactMode ? 'teams-table--compact' : '';
        
        let html = `
            <div class="teams-table-container">
                <div class="teams-table-scroll">
                    <table class="teams-table ${compactClass}">
                        ${this._generateTableHeader()}
                        <tbody>
        `;
        
        teams.forEach((team, index) => {
            html += this._generateTeamRow(team, index, data, teams);
        });
        
        html += `
                        </tbody>
                    </table>
                </div>
            </div>
        `;
        
        return html;
    }
    
    /**
     * Génère l'en-tête du tableau
     */
    _generateTableHeader() {
        return `
            <thead>
                <tr class="teams-table__header">
                    <th class="teams-table__th teams-table__th--sticky teams-table__th--team">Équipe</th>
                    <th class="teams-table__th teams-table__th--pool" title="Poule">Poule</th>
                    ${this.showPerformance ? `
                    <th class="teams-table__th teams-table__th--stat" title="Matchs Joués">J</th>
                    <th class="teams-table__th teams-table__th--stat" title="Victoires">G</th>
                    <th class="teams-table__th teams-table__th--stat" title="Nuls">N</th>
                    <th class="teams-table__th teams-table__th--stat" title="Défaites">P</th>
                    <th class="teams-table__th teams-table__th--stat" title="Points">Pts</th>
                    <th class="teams-table__th teams-table__th--stat" title="Différence de points marqués">+/-</th>
                    ` : ''}
                    ${this.showPlanning ? `
                    <th class="teams-table__th teams-table__th--planning" title="Planifiés (normaux + entente) / Non planifiés">Planning</th>
                    <th class="teams-table__th teams-table__th--stat" title="Taux de complétion">%</th>
                    ` : ''}
                    ${this.showPenalties ? `
                    <th class="teams-table__th teams-table__th--stat" title="Pénalités totales">Pén.</th>
                    ` : ''}
                    <th class="teams-table__th teams-table__th--action"></th>
                </tr>
            </thead>
        `;
    }
    
    /**
     * Calcule la classe CSS pour le coloring d'une équipe
     */
    _getTeamRowColorClass(stats, index, allTeams) {
        if (this.colorBy === 'none') {
            return index % 2 === 0 ? 'team-row--even' : 'team-row--odd';
        }
        
        let value, maxValue, minValue;
        
        switch (this.colorBy) {
            case 'completion':
                value = stats.completionRate;
                if (value >= 80) return 'team-row--success';
                if (value >= 60) return 'team-row--warning';
                if (value >= 40) return 'team-row--orange';
                return 'team-row--danger';
                
            case 'performance':
                maxValue = Math.max(...allTeams.map(t => t.stats.points));
                minValue = Math.min(...allTeams.map(t => t.stats.points));
                value = stats.points;
                
                if (maxValue === minValue) return index % 2 === 0 ? 'team-row--even' : 'team-row--odd';
                
                const pointsRatio = (value - minValue) / (maxValue - minValue);
                if (pointsRatio >= 0.75) return 'team-row--success';
                if (pointsRatio >= 0.5) return 'team-row--warning';
                if (pointsRatio >= 0.25) return 'team-row--orange';
                return 'team-row--danger';
                
            case 'pointsDiff':
                value = stats.pointsDiff;
                if (value > 20) return 'team-row--success';
                if (value > 5) return 'team-row--success-light';
                if (value >= -5) return index % 2 === 0 ? 'team-row--even' : 'team-row--odd';
                if (value >= -20) return 'team-row--danger-light';
                return 'team-row--danger';
                
            case 'penalties':
                value = stats.totalPenalties;
                if (value <= 10) return 'team-row--success';
                if (value <= 30) return 'team-row--warning';
                if (value <= 50) return 'team-row--orange';
                return 'team-row--danger';
                
            default:
                return index % 2 === 0 ? 'team-row--even' : 'team-row--odd';
        }
    }
    
    /**
     * Génère une ligne d'équipe
     */
    _generateTeamRow(team, index, data, allTeams) {
        const isExpanded = this.expandedTeams.has(team.id);
        const rowColorClass = this._getTeamRowColorClass(team.stats, index, allTeams);
        const stats = team.stats;
        
        // Badges
        const genderClass = team.genre === 'F' ? 'team-gender--female' : 'team-gender--male';
        const genderIcon = team.genre === 'F' ? '♀️' : '♂️';
        const ententeBadge = stats.entente > 0 ? `<span class="team-entente-badge" title="${stats.entente} match(s) entente">🤝</span>` : '';
        
        // Classes pour les valeurs
        const pointsDiffClass = stats.pointsDiff > 0 ? 'stat--positive' : stats.pointsDiff < 0 ? 'stat--negative' : '';
        const pointsDiffSign = stats.pointsDiff > 0 ? '+' : '';
        const completionClass = stats.completionRate >= 80 ? 'stat--success' : stats.completionRate >= 50 ? 'stat--warning' : 'stat--danger';
        const penaltyClass = stats.totalPenalties > 50 ? 'stat--danger' : stats.totalPenalties > 20 ? 'stat--warning' : 'stat--success';
        
        let html = `
            <tr class="team-row ${rowColorClass}" data-team-id="${team.id}">
                <td class="teams-table__td teams-table__td--team teams-table__td--sticky">
                    <div class="team-cell">
                        <span class="team-gender ${genderClass}">${genderIcon}</span>
                        <div class="team-info">
                            <span class="team-name">${team.nom_complet || team.nom}</span>
                            <span class="team-institution">${team.institution}${ententeBadge}</span>
                        </div>
                    </div>
                </td>
                <td class="teams-table__td teams-table__td--center">
                    <span class="team-pool-badge">${team.poule}</span>
                </td>
                ${this.showPerformance ? `
                <td class="teams-table__td teams-table__td--stat">${stats.played}</td>
                <td class="teams-table__td teams-table__td--stat stat--won">${stats.won}</td>
                <td class="teams-table__td teams-table__td--stat stat--drawn">${stats.drawn}</td>
                <td class="teams-table__td teams-table__td--stat stat--lost">${stats.lost}</td>
                <td class="teams-table__td teams-table__td--stat teams-table__td--points">${stats.points}</td>
                <td class="teams-table__td teams-table__td--stat ${pointsDiffClass}">${pointsDiffSign}${stats.pointsDiff}</td>
                ` : ''}
                ${this.showPlanning ? `
                <td class="teams-table__td teams-table__td--planning">
                    <span class="planning-info">
                        <span class="planning-scheduled" title="Planifiés normaux">${stats.scheduledNonEntente}</span>
                        ${stats.scheduledEntente > 0 ? `<span class="planning-separator"> + </span><span class="planning-entente" title="Planifiés entente">🤝${stats.scheduledEntente}</span>` : ''}
                        <span class="planning-separator"> / </span>
                        <span class="planning-unscheduled" title="Non planifiés">${stats.unscheduled}</span>
                    </span>
                </td>
                <td class="teams-table__td teams-table__td--stat ${completionClass}">${stats.completionRate.toFixed(0)}%</td>
                ` : ''}
                ${this.showPenalties ? `
                <td class="teams-table__td teams-table__td--stat ${penaltyClass}">${stats.totalPenalties.toFixed(1)}</td>
                ` : ''}
                <td class="teams-table__td teams-table__td--action">
                    <button class="expand-btn ${isExpanded ? 'expand-btn--expanded' : ''}">
                        ${isExpanded ? '▼' : '▶'}
                    </button>
                </td>
            </tr>
        `;
        
        // Contenu développé
        if (isExpanded) {
            html += this._generateExpandedContent(team, data);
        }
        
        return html;
    }
    
    /**
     * Génère le contenu développé d'une équipe
     */
    _generateExpandedContent(team, data) {
        const stats = team.stats;
        
        // Utiliser l'emoji du sport
        const sportEmoji = window.sportUtils?.getEmoji() || '🏐';
        
        const preferenceRateClass = stats.preferenceRate >= 70 ? 'stat--success' : stats.preferenceRate >= 40 ? 'stat--warning' : 'stat--danger';
        
        return `
            <tr class="team-expanded-row" data-team-id="${team.id}">
                <td colspan="100%" class="team-expanded-cell">
                    <div class="team-expanded-content">
                        
                        <!-- Statistiques détaillées -->
                        <div class="expanded-section">
                            <h4 class="expanded-section__title">📊 Statistiques Détaillées</h4>
                            <div class="expanded-stats-grid">
                                <div class="expanded-stat"><span class="expanded-stat__label">Total matchs:</span> <strong>${stats.totalMatches}</strong></div>
                                <div class="expanded-stat"><span class="expanded-stat__label">Joués:</span> <strong class="stat--success">${stats.played}</strong></div>
                                <div class="expanded-stat"><span class="expanded-stat__label">À venir:</span> <strong class="stat--info">${stats.upcoming}</strong></div>
                                <div class="expanded-stat"><span class="expanded-stat__label">Non planifiés:</span> <strong class="stat--danger">${stats.unscheduled}</strong></div>
                                <div class="expanded-stat"><span class="expanded-stat__label">Points pour:</span> <strong class="stat--success">${stats.pointsFor}</strong></div>
                                <div class="expanded-stat"><span class="expanded-stat__label">Points contre:</span> <strong class="stat--danger">${stats.pointsAgainst}</strong></div>
                                <div class="expanded-stat"><span class="expanded-stat__label">Semaines jouées:</span> <strong>${stats.weeksPlayed}</strong></div>
                                <div class="expanded-stat"><span class="expanded-stat__label">Gymnases utilisés:</span> <strong>${stats.venuesUsed}</strong></div>
                            </div>
                        </div>
                        
                        ${this.showPreferences ? `
                        <!-- Préférences -->
                        <div class="expanded-section">
                            <h4 class="expanded-section__title">⭐ Préférences</h4>
                            <div class="expanded-preferences">
                                ${team.horaires_preferes && team.horaires_preferes.length > 0 ? `
                                <div class="preference-item">
                                    <span class="preference-item__label">🕐 Horaires préférés:</span>
                                    <span class="preference-item__value">${team.horaires_preferes.join(', ')}</span>
                                </div>
                                ` : ''}
                                ${team.lieux_preferes && team.lieux_preferes.length > 0 ? `
                                <div class="preference-item">
                                    <span class="preference-item__label">📍 Lieux préférés:</span>
                                    <span class="preference-item__value">${team.lieux_preferes.join(', ')}</span>
                                </div>
                                ` : ''}
                                ${team.semaines_indisponibles && Object.keys(team.semaines_indisponibles).length > 0 ? `
                                <div class="preference-item">
                                    <span class="preference-item__label">❌ Indisponibilités:</span>
                                    <span class="preference-item__value preference-item__value--danger">Semaines ${Object.keys(team.semaines_indisponibles).join(', ')}</span>
                                </div>
                                ` : ''}
                                <div class="preference-rate">
                                    <span class="preference-rate__label">Taux de respect:</span>
                                    <strong class="${preferenceRateClass}">${stats.preferenceRate.toFixed(0)}%</strong>
                                </div>
                            </div>
                        </div>
                        ` : ''}
                        
                        <!-- Récapitulatif des matchs -->
                        <div class="expanded-section ${this.showPreferences ? '' : 'expanded-section--full'}">
                            <h4 class="expanded-section__title">${sportEmoji} Matchs (${stats.matches.length})</h4>
                            <div class="expanded-matches-scroll">
                                ${this._generateTeamMatchesList(stats.matches, team)}
                            </div>
                        </div>
                    </div>
                </td>
            </tr>
        `;
    }

    /**
     * Génère la liste des matchs d'une équipe
     */
    _generateTeamMatchesList(matches, team) {
        if (matches.length === 0) {
            return '<div class="team-matches-empty">Aucun match</div>';
        }
        
        // Utiliser l'emoji du sport
        const sportEmoji = window.sportUtils?.getEmoji() || '🏐';
        let html = '<div class="team-matches-list">';
        
        matches.forEach(match => {
            const isTeam1 = match.equipe1_id === team.id;
            const opponent = isTeam1 ? match.equipe2_nom : match.equipe1_nom;
            const isScheduled = match.semaine && match.horaire && match.gymnase;
            const hasScore = match.score && match.score.has_score;
            const isEntente = match.is_entente;
            const ententeStatus = (match.entente_status || 'suggested').toLowerCase();
            
            // Déterminer les classes CSS pour le match
            let itemClass = 'team-match-item';
            let statusClass = 'team-match-item__status';
            let statusText = 'À planifier';
            let statusIcon = '';
            
            if (isEntente) {
                // Classes pour les matchs entente
                itemClass += ` team-match-item--entente-${ententeStatus}`;
                statusClass += ` team-match-item__status--entente-${ententeStatus}`;
                const ententeConfig = {
                    'played': { text: 'Jouée', icon: '✅' },
                    'scheduled': { text: 'Planifiée', icon: '📅' },
                    'confirmed': { text: 'Confirmée', icon: '🤝' },
                    'suggested': { text: 'Suggérée', icon: '💡' }
                };
                const config = ententeConfig[ententeStatus] || ententeConfig['suggested'];
                statusText = config.text;
                statusIcon = config.icon;
            } else if (hasScore) {
                itemClass += ' team-match-item--played';
                statusClass += ' team-match-item__status--played';
                statusText = 'Terminé';
            } else if (isScheduled) {
                itemClass += ' team-match-item--upcoming';
                statusClass += ' team-match-item__status--upcoming';
                statusText = 'À venir';
            } else {
                itemClass += ' team-match-item--unscheduled';
                statusClass += ' team-match-item__status--unscheduled';
            }
            
            // Score display
            let scoreDisplay = '';
            if (hasScore) {
                const teamScore = isTeam1 ? match.score.equipe1 : match.score.equipe2;
                const oppScore = isTeam1 ? match.score.equipe2 : match.score.equipe1;
                const isWin = teamScore > oppScore;
                const isDraw = teamScore === oppScore;
                const scoreClass = isWin ? 'team-match-item__score--win' : isDraw ? 'team-match-item__score--draw' : 'team-match-item__score--loss';
                scoreDisplay = `<span class="team-match-item__score ${scoreClass}">${teamScore} - ${oppScore}</span>`;
            }
            
            // Description pour les ententes selon le statut
            let matchInfo = '';
            if (isEntente) {
                const descriptions = {
                    'played': 'Match d\'entente terminé',
                    'scheduled': `J${match.semaine} • ${match.horaire} • ${match.gymnase}`,
                    'confirmed': 'En attente de créneau',
                    'suggested': 'À confirmer avec les équipes'
                };
                const infoColorClass = {
                    'played': 'team-match-item__info--success',
                    'scheduled': 'team-match-item__info--info',
                    'confirmed': 'team-match-item__info--purple',
                    'suggested': 'team-match-item__info--warning'
                };
                matchInfo = `<div class="team-match-item__info team-match-item__info--entente ${infoColorClass[ententeStatus] || ''}">${descriptions[ententeStatus] || 'Match en entente'}</div>`;
            } else if (isScheduled) {
                matchInfo = `<div class="team-match-item__info">J${match.semaine} • ${match.horaire} • ${match.gymnase}</div>`;
            }
            
            html += `
                <div class="${itemClass}">
                    <div>
                        <div class="team-match-item__opponent">
                            vs ${opponent}
                            ${isEntente ? `<span class="team-match-item__badge" title="Match entente - ${statusText}">${statusIcon || '🤝'}</span>` : ''}
                        </div>
                        ${matchInfo}
                    </div>
                    <div class="team-match-item__right">
                        ${scoreDisplay}
                        <span class="${statusClass}">${statusText}</span>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        return html;
    }
    
    /**
     * Génère les équipes groupées
     */
    _generateGroupedTeams(teams, data) {
        const groups = this._groupTeams(teams);
        
        let html = '';
        
        Object.keys(groups).sort().forEach(groupName => {
            const groupTeams = groups[groupName];
            
            html += `
                <div class="teams-group">
                    <h3 class="teams-group__header">
                        <span class="teams-group__icon">${this._getGroupIcon()}</span>
                        ${groupName}
                        <span class="teams-group__count">(${groupTeams.length})</span>
                    </h3>
                    ${this._generateTeamsTable(groupTeams, data)}
                </div>
            `;
        });
        
        return html;
    }
    
    /**
     * Groupe les équipes selon l'option de groupement
     */
    _groupTeams(teams) {
        const groups = {};
        
        teams.forEach(team => {
            let groupKey = '';
            
            switch (this.groupBy) {
                case 'gender':
                    groupKey = team.genre === 'F' ? 'Féminin' : 'Masculin';
                    break;
                case 'institution':
                    groupKey = team.institution;
                    break;
                case 'pool':
                    groupKey = team.poule;
                    break;
                case 'level':
                    const pool = this.dataManager.getPoule(team.poule);
                    groupKey = pool?.niveau || 'N/A';
                    break;
                default:
                    groupKey = 'Toutes les équipes';
            }
            
            if (!groups[groupKey]) {
                groups[groupKey] = [];
            }
            
            groups[groupKey].push(team);
        });
        
        return groups;
    }
    
    /**
     * Retourne l'icône du groupe
     */
    _getGroupIcon() {
        switch (this.groupBy) {
            case 'gender': return '👥';
            case 'institution': return '🏫';
            case 'pool': return '🎯';
            case 'level': return '📈';
            default: return '📋';
        }
    }
    
    /**
     * Toggle l'expansion d'une équipe
     */
    toggleTeam(teamId) {
        if (this.expandedTeams.has(teamId)) {
            this.expandedTeams.delete(teamId);
        } else {
            this.expandedTeams.add(teamId);
        }
        this.render();
    }
    
    /**
     * Attache les event listeners
     */
    _attachEventListeners() {
        // Click sur une ligne d'équipe pour l'expand/collapse
        const teamRows = this.container.querySelectorAll('.team-row');
        teamRows.forEach(row => {
            row.addEventListener('click', (e) => {
                // Éviter le toggle si on clique sur le bouton expand
                if (e.target.closest('.expand-btn')) {
                    return;
                }
                const teamId = row.dataset.teamId;
                if (teamId) {
                    this.toggleTeam(teamId);
                }
            });
        });
        
        // Click sur les boutons expand
        const expandBtns = this.container.querySelectorAll('.expand-btn');
        expandBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const row = e.target.closest('.team-row');
                const teamId = row?.dataset.teamId;
                if (teamId) {
                    this.toggleTeam(teamId);
                }
            });
        });
    }
}

// Export global
window.TeamsView = TeamsView;
