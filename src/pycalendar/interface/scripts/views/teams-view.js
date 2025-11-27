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
            equipe: ''
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
            <div class="empty-state" style="display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 4rem 2rem; text-align: center;">
                <div class="empty-state-icon" style="font-size: 5rem; margin-bottom: 1.5rem; opacity: 0.5;">👥</div>
                <h3 class="empty-state-title" style="font-size: 1.5rem; font-weight: 700; color: #333; margin: 0 0 0.75rem 0; font-family: 'Inter', 'Roboto', sans-serif;">Aucune équipe</h3>
                <p class="empty-state-message" style="font-size: 1rem; color: #666; margin: 0; font-family: 'Roboto', sans-serif;">Les équipes apparaîtront ici une fois configurées.</p>
            </div>
        `;
    }
    
    /**
     * Affiche aucun résultat
     */
    renderNoResults() {
        this.container.innerHTML = `
            <div class="empty-state" style="display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 4rem 2rem; text-align: center;">
                <div class="empty-state-icon" style="font-size: 5rem; margin-bottom: 1.5rem; opacity: 0.5;">🔍</div>
                <h3 class="empty-state-title" style="font-size: 1.5rem; font-weight: 700; color: #333; margin: 0 0 0.75rem 0; font-family: 'Inter', 'Roboto', sans-serif;">Aucune équipe correspondante</h3>
                <p class="empty-state-message" style="font-size: 1rem; color: #666; margin: 0; font-family: 'Roboto', sans-serif;">Aucune équipe ne correspond aux filtres sélectionnés.</p>
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
        
        // Matchs planifiés = matchs avec créneau + matchs entente sans créneau
        const scheduledMatches = teamMatches.filter(m => m.semaine || m.is_entente);
        
        // Matchs NON planifiés = matchs sans créneau ET non entente
        const unscheduledMatches = teamMatches.filter(m => !m.semaine && !m.is_entente);
        
        // Matchs joués (avec score) - uniquement parmi les matchs planifiés avec créneau
        const playedMatches = scheduledMatches.filter(m => 
            m.semaine && // Doit avoir un créneau pour être considéré "joué"
            m.score && m.score.has_score &&
            m.score.equipe1 !== null && m.score.equipe1 !== undefined &&
            m.score.equipe2 !== null && m.score.equipe2 !== undefined
        );
        
        const upcomingMatches = scheduledMatches.filter(m => 
            m.semaine && // Matchs avec créneau seulement
            (!m.score || !m.score.has_score ||
            m.score.equipe1 === null || m.score.equipe1 === undefined ||
            m.score.equipe2 === null || m.score.equipe2 === undefined)
        );
        
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
        const weeksPlayed = new Set(scheduledMatches.map(m => m.semaine)).size;
        const venuesUsed = new Set(scheduledMatches.map(m => m.gymnase)).size;
        
        // Pénalités
        const totalPenalties = teamMatches.reduce((sum, m) => {
            if (!m.penalties) return sum;
            return sum + Object.values(m.penalties).reduce((s, p) => s + p, 0);
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
                            const matchDuration = 90; // Durée standard d'un match
                            const matchEndMinutes = matchStartMinutes + matchDuration;
                            
                            // Vérifier le chevauchement
                            const overlaps = matchStartMinutes < rangeEnd && matchEndMinutes > rangeStart;
                            if (!overlaps) {
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
        let html = '<div class="teams-view" style="padding: 1.5rem;">';
        
        // En-tête avec résumé global
        html += this._generateGlobalSummary(teams);
        
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
        const avgCompletion = totalTeams > 0 
            ? teams.reduce((sum, t) => sum + t.stats.completionRate, 0) / totalTeams 
            : 0;
        
        return `
            <div class="teams-summary" style="background: white; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08); border: 1px solid rgba(0, 85, 164, 0.15);">
                <h2 style="margin: 0 0 1rem 0; font-size: 1.5rem; font-weight: 800; color: #0055A4; font-family: 'Inter', 'Roboto', sans-serif; display: flex; align-items: center; gap: 0.5rem;">
                    <span style="font-size: 1.8rem;">👥</span>
                    Vue Équipes
                    <span style="font-size: 0.9rem; font-weight: 600; color: #666; margin-left: auto;">${totalTeams} équipe${totalTeams > 1 ? 's' : ''}</span>
                </h2>
                <div class="summary-stats" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; margin-top: 1rem;">
                    <div class="summary-stat" style="text-align: center; padding: 0.75rem; background: rgba(0, 85, 164, 0.05); border-radius: 8px; border: 1px solid rgba(0, 85, 164, 0.1);">
                        <div style="font-size: 1.5rem; font-weight: 900; color: #0055A4; font-family: 'Roboto Mono', monospace;">${totalMatches}</div>
                        <div style="font-size: 0.7rem; font-weight: 700; color: #666; text-transform: uppercase; margin-top: 0.25rem;">Matchs Total</div>
                    </div>
                    <div class="summary-stat" style="text-align: center; padding: 0.75rem; background: rgba(39, 174, 96, 0.05); border-radius: 8px; border: 1px solid rgba(39, 174, 96, 0.1);">
                        <div style="font-size: 1.5rem; font-weight: 900; color: #27AE60; font-family: 'Roboto Mono', monospace;">${totalPlayed}</div>
                        <div style="font-size: 0.7rem; font-weight: 700; color: #666; text-transform: uppercase; margin-top: 0.25rem;">Matchs Joués</div>
                    </div>
                    <div class="summary-stat" style="text-align: center; padding: 0.75rem; background: rgba(239, 65, 53, 0.05); border-radius: 8px; border: 1px solid rgba(239, 65, 53, 0.1);">
                        <div style="font-size: 1.5rem; font-weight: 900; color: #EF4135; font-family: 'Roboto Mono', monospace;">${totalUnscheduled}</div>
                        <div style="font-size: 0.7rem; font-weight: 700; color: #666; text-transform: uppercase; margin-top: 0.25rem;">Non Planifiés</div>
                    </div>
                    <div class="summary-stat" style="text-align: center; padding: 0.75rem; background: rgba(0, 123, 255, 0.05); border-radius: 8px; border: 1px solid rgba(0, 123, 255, 0.1);">
                        <div style="font-size: 1.5rem; font-weight: 900; color: #007BFF; font-family: 'Roboto Mono', monospace;">${avgCompletion.toFixed(0)}%</div>
                        <div style="font-size: 0.7rem; font-weight: 700; color: #666; text-transform: uppercase; margin-top: 0.25rem;">Complétion Moy.</div>
                    </div>
                </div>
            </div>
        `;
    }
    
    /**
     * Génère le tableau des équipes (sans groupement)
     */
    _generateTeamsTable(teams, data) {
        let html = `
            <div class="teams-table-container" style="background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08); border: 1px solid rgba(0, 85, 164, 0.15);">
                <div style="overflow-x: auto;">
                    <table class="teams-table" style="width: 100%; border-collapse: collapse; font-size: ${this.compactMode ? '0.8rem' : '0.85rem'}; font-family: 'Roboto', sans-serif;">
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
        const compact = this.compactMode;
        
        return `
            <thead>
                <tr style="background: linear-gradient(135deg, #0055A4 0%, rgba(0, 85, 164, 0.9) 100%); color: white; border-bottom: 2px solid rgba(0, 85, 164, 0.3);">
                    <th style="padding: ${compact ? '0.6rem 0.75rem' : '0.8rem 1rem'}; text-align: left; font-weight: 800; font-size: ${compact ? '0.7rem' : '0.75rem'}; text-transform: uppercase; letter-spacing: 0.05em; position: sticky; left: 0; background: linear-gradient(135deg, #0055A4 0%, rgba(0, 85, 164, 0.9) 100%); z-index: 10;">Équipe</th>
                    <th style="padding: ${compact ? '0.6rem 0.5rem' : '0.8rem 0.75rem'}; text-align: center; font-weight: 800; font-size: ${compact ? '0.7rem' : '0.75rem'}; text-transform: uppercase; letter-spacing: 0.05em;" title="Poule">Poule</th>
                    ${this.showPerformance ? `
                    <th style="padding: ${compact ? '0.6rem 0.5rem' : '0.8rem 0.75rem'}; text-align: center; font-weight: 800; font-size: ${compact ? '0.7rem' : '0.75rem'}; text-transform: uppercase; letter-spacing: 0.05em;" title="Matchs Joués">J</th>
                    <th style="padding: ${compact ? '0.6rem 0.5rem' : '0.8rem 0.75rem'}; text-align: center; font-weight: 800; font-size: ${compact ? '0.7rem' : '0.75rem'}; text-transform: uppercase; letter-spacing: 0.05em;" title="Victoires">G</th>
                    <th style="padding: ${compact ? '0.6rem 0.5rem' : '0.8rem 0.75rem'}; text-align: center; font-weight: 800; font-size: ${compact ? '0.7rem' : '0.75rem'}; text-transform: uppercase; letter-spacing: 0.05em;" title="Nuls">N</th>
                    <th style="padding: ${compact ? '0.6rem 0.5rem' : '0.8rem 0.75rem'}; text-align: center; font-weight: 800; font-size: ${compact ? '0.7rem' : '0.75rem'}; text-transform: uppercase; letter-spacing: 0.05em;" title="Défaites">P</th>
                    <th style="padding: ${compact ? '0.6rem 0.5rem' : '0.8rem 0.75rem'}; text-align: center; font-weight: 800; font-size: ${compact ? '0.7rem' : '0.75rem'}; text-transform: uppercase; letter-spacing: 0.05em;" title="Points">Pts</th>
                    <th style="padding: ${compact ? '0.6rem 0.5rem' : '0.8rem 0.75rem'}; text-align: center; font-weight: 800; font-size: ${compact ? '0.7rem' : '0.75rem'}; text-transform: uppercase; letter-spacing: 0.05em;" title="Différence de points marqués">+/-</th>
                    ` : ''}
                    ${this.showPlanning ? `
                    <th style="padding: ${compact ? '0.6rem 0.5rem' : '0.8rem 0.75rem'}; text-align: center; font-weight: 800; font-size: ${compact ? '0.7rem' : '0.75rem'}; text-transform: uppercase; letter-spacing: 0.05em;" title="Planifiés (normaux + entente) / Non planifiés">Planning</th>
                    <th style="padding: ${compact ? '0.6rem 0.5rem' : '0.8rem 0.75rem'}; text-align: center; font-weight: 800; font-size: ${compact ? '0.7rem' : '0.75rem'}; text-transform: uppercase; letter-spacing: 0.05em;" title="Taux de complétion">%</th>
                    ` : ''}
                    ${this.showPenalties ? `
                    <th style="padding: ${compact ? '0.6rem 0.5rem' : '0.8rem 0.75rem'}; text-align: center; font-weight: 800; font-size: ${compact ? '0.7rem' : '0.75rem'}; text-transform: uppercase; letter-spacing: 0.05em;" title="Pénalités totales">Pén.</th>
                    ` : ''}
                    <th style="padding: ${compact ? '0.6rem 0.5rem' : '0.8rem 0.75rem'}; text-align: center; font-weight: 800; font-size: ${compact ? '0.7rem' : '0.75rem'}; text-transform: uppercase; letter-spacing: 0.05em;"></th>
                </tr>
            </thead>
        `;
    }
    
    /**
     * Calcule la couleur de fond d'une équipe selon le critère de coloration
     */
    _getTeamRowColor(stats, index, allTeams) {
        if (this.colorBy === 'none') {
            return index % 2 === 0 ? 'rgba(0, 85, 164, 0.02)' : 'white';
        }
        
        let value, maxValue, minValue;
        
        switch (this.colorBy) {
            case 'completion':
                // Vert pour taux élevé, rouge pour taux faible
                value = stats.completionRate;
                if (value >= 80) return 'rgba(39, 174, 96, 0.15)'; // Vert clair
                if (value >= 60) return 'rgba(255, 193, 7, 0.15)'; // Jaune clair
                if (value >= 40) return 'rgba(255, 149, 0, 0.15)'; // Orange clair
                return 'rgba(239, 65, 53, 0.15)'; // Rouge clair
                
            case 'performance':
                // Vert pour beaucoup de points, rouge pour peu
                maxValue = Math.max(...allTeams.map(t => t.stats.points));
                minValue = Math.min(...allTeams.map(t => t.stats.points));
                value = stats.points;
                
                if (maxValue === minValue) return index % 2 === 0 ? 'rgba(0, 85, 164, 0.02)' : 'white';
                
                const pointsRatio = (value - minValue) / (maxValue - minValue);
                if (pointsRatio >= 0.75) return 'rgba(39, 174, 96, 0.15)';
                if (pointsRatio >= 0.5) return 'rgba(255, 193, 7, 0.15)';
                if (pointsRatio >= 0.25) return 'rgba(255, 149, 0, 0.15)';
                return 'rgba(239, 65, 53, 0.15)';
                
            case 'pointsDiff':
                // Vert pour diff positive, rouge pour négative
                value = stats.pointsDiff;
                if (value > 20) return 'rgba(39, 174, 96, 0.15)';
                if (value > 5) return 'rgba(39, 174, 96, 0.08)';
                if (value >= -5) return index % 2 === 0 ? 'rgba(0, 85, 164, 0.02)' : 'white';
                if (value >= -20) return 'rgba(239, 65, 53, 0.08)';
                return 'rgba(239, 65, 53, 0.15)';
                
            case 'penalties':
                // Rouge pour beaucoup de pénalités, vert pour peu
                value = stats.totalPenalties;
                if (value <= 10) return 'rgba(39, 174, 96, 0.15)';
                if (value <= 30) return 'rgba(255, 193, 7, 0.15)';
                if (value <= 50) return 'rgba(255, 149, 0, 0.15)';
                return 'rgba(239, 65, 53, 0.15)';
                
            default:
                return index % 2 === 0 ? 'rgba(0, 85, 164, 0.02)' : 'white';
        }
    }
    
    /**
     * Génère une ligne d'équipe
     */
    _generateTeamRow(team, index, data, allTeams) {
        const isExpanded = this.expandedTeams.has(team.id);
        const rowBg = this._getTeamRowColor(team.stats, index, allTeams);
        const compact = this.compactMode;
        const stats = team.stats;
        
        // Badges
        const genderIcon = team.genre === 'F' ? '♀️' : '♂️';
        const genderColor = team.genre === 'F' ? '#FF1493' : '#007BFF';
        const ententeBadge = stats.entente > 0 ? `<span style="font-size: 0.8rem; margin-left: 0.3rem;" title="${stats.entente} match(s) entente">🤝</span>` : '';
        
        // Couleur pour la différence de points
        const pointsDiffColor = stats.pointsDiff > 0 ? '#27AE60' : stats.pointsDiff < 0 ? '#EF4135' : '#666';
        const pointsDiffSign = stats.pointsDiff > 0 ? '+' : '';
        
        // Couleur pour le taux de complétion
        const completionColor = stats.completionRate >= 80 ? '#27AE60' : stats.completionRate >= 50 ? '#FF9500' : '#EF4135';
        
        // Couleur pour les pénalités
        const penaltyColor = stats.totalPenalties > 50 ? '#EF4135' : stats.totalPenalties > 20 ? '#FF9500' : '#27AE60';
        
        let html = `
            <tr class="team-row" data-team-id="${team.id}" style="background: ${rowBg}; border-bottom: 1px solid rgba(0, 85, 164, 0.08); cursor: pointer; transition: background 0.2s ease;">
                <td style="padding: ${compact ? '0.6rem 0.75rem' : '0.8rem 1rem'}; font-weight: 700; position: sticky; left: 0; background: ${rowBg}; z-index: 5; border-right: 1px solid rgba(0, 85, 164, 0.1);">
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <span style="color: ${genderColor}; font-size: 1rem;">${genderIcon}</span>
                        <div style="display: flex; flex-direction: column;">
                            <span style="font-size: ${compact ? '0.85rem' : '0.9rem'}; color: #0055A4;">${team.nom_complet || team.nom}</span>
                            <span style="font-size: 0.7rem; color: #999; font-weight: 600;">${team.institution}${ententeBadge}</span>
                        </div>
                    </div>
                </td>
                <td style="padding: ${compact ? '0.6rem 0.5rem' : '0.8rem 0.75rem'}; text-align: center;">
                    <span style="font-size: 0.7rem; font-weight: 700; padding: 0.2rem 0.5rem; background: rgba(0, 85, 164, 0.1); border-radius: 4px; color: #0055A4;">${team.poule}</span>
                </td>
                ${this.showPerformance ? `
                <td style="padding: ${compact ? '0.6rem 0.5rem' : '0.8rem 0.75rem'}; text-align: center; font-weight: 700; font-family: 'Roboto Mono', monospace;">${stats.played}</td>
                <td style="padding: ${compact ? '0.6rem 0.5rem' : '0.8rem 0.75rem'}; text-align: center; font-weight: 700; color: #27AE60; font-family: 'Roboto Mono', monospace;">${stats.won}</td>
                <td style="padding: ${compact ? '0.6rem 0.5rem' : '0.8rem 0.75rem'}; text-align: center; font-weight: 700; color: #FF9500; font-family: 'Roboto Mono', monospace;">${stats.drawn}</td>
                <td style="padding: ${compact ? '0.6rem 0.5rem' : '0.8rem 0.75rem'}; text-align: center; font-weight: 700; color: #EF4135; font-family: 'Roboto Mono', monospace;">${stats.lost}</td>
                <td style="padding: ${compact ? '0.6rem 0.5rem' : '0.8rem 0.75rem'}; text-align: center; font-weight: 900; color: #0055A4; font-size: ${compact ? '0.9rem' : '1rem'}; font-family: 'Roboto Mono', monospace;">${stats.points}</td>
                <td style="padding: ${compact ? '0.6rem 0.5rem' : '0.8rem 0.75rem'}; text-align: center; font-weight: 700; color: ${pointsDiffColor}; font-family: 'Roboto Mono', monospace;">${pointsDiffSign}${stats.pointsDiff}</td>
                ` : ''}
                ${this.showPlanning ? `
                <td style="padding: ${compact ? '0.6rem 0.5rem' : '0.8rem 0.75rem'}; text-align: center;">
                    <span style="font-size: 0.75rem; font-weight: 700;">
                        <span style="color: #27AE60;" title="Planifiés normaux">${stats.scheduledNonEntente}</span>
                        ${stats.scheduledEntente > 0 ? `<span style="color: #999;"> + </span><span style="color: #27AE60;" title="Planifiés entente">🤝${stats.scheduledEntente}</span>` : ''}
                        <span style="color: #999;"> / </span>
                        <span style="color: #EF4135;" title="Non planifiés">${stats.unscheduled}</span>
                    </span>
                </td>
                <td style="padding: ${compact ? '0.6rem 0.5rem' : '0.8rem 0.75rem'}; text-align: center;">
                    <span style="font-size: 0.85rem; font-weight: 900; color: ${completionColor}; font-family: 'Roboto Mono', monospace;">${stats.completionRate.toFixed(0)}%</span>
                </td>
                ` : ''}
                ${this.showPenalties ? `
                <td style="padding: ${compact ? '0.6rem 0.5rem' : '0.8rem 0.75rem'}; text-align: center;">
                    <span style="font-size: 0.8rem; font-weight: 800; color: ${penaltyColor}; font-family: 'Roboto Mono', monospace;">${stats.totalPenalties.toFixed(1)}</span>
                </td>
                ` : ''}
                <td style="padding: ${compact ? '0.6rem 0.5rem' : '0.8rem 0.75rem'}; text-align: center;">
                    <button class="expand-btn ${isExpanded ? 'expanded' : ''}" style="background: rgba(0, 85, 164, 0.1); border: 1px solid rgba(0, 85, 164, 0.2); color: #0055A4; padding: 0.3rem 0.6rem; border-radius: 4px; font-weight: 700; cursor: pointer; transition: all 0.2s ease;">
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
        
        return `
            <tr class="team-expanded-row" data-team-id="${team.id}">
                <td colspan="100%" style="padding: 0; background: rgba(0, 85, 164, 0.02); border-bottom: 2px solid rgba(0, 85, 164, 0.15);">
                    <div style="padding: 1.5rem; display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem;">
                        
                        <!-- Statistiques détaillées -->
                        <div style="background: white; border-radius: 8px; padding: 1rem; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.06); border: 1px solid rgba(0, 85, 164, 0.1);">
                            <h4 style="margin: 0 0 0.75rem 0; font-size: 0.9rem; font-weight: 800; color: #0055A4; font-family: 'Roboto', sans-serif; border-bottom: 2px solid rgba(0, 85, 164, 0.1); padding-bottom: 0.5rem;">📊 Statistiques Détaillées</h4>
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; font-size: 0.8rem;">
                                <div><span style="color: #666;">Total matchs:</span> <strong>${stats.totalMatches}</strong></div>
                                <div><span style="color: #666;">Joués:</span> <strong style="color: #27AE60;">${stats.played}</strong></div>
                                <div><span style="color: #666;">À venir:</span> <strong style="color: #007BFF;">${stats.upcoming}</strong></div>
                                <div><span style="color: #666;">Non planifiés:</span> <strong style="color: #EF4135;">${stats.unscheduled}</strong></div>
                                <div><span style="color: #666;">Points pour:</span> <strong style="color: #27AE60;">${stats.pointsFor}</strong></div>
                                <div><span style="color: #666;">Points contre:</span> <strong style="color: #EF4135;">${stats.pointsAgainst}</strong></div>
                                <div><span style="color: #666;">Semaines jouées:</span> <strong>${stats.weeksPlayed}</strong></div>
                                <div><span style="color: #666;">Gymnases utilisés:</span> <strong>${stats.venuesUsed}</strong></div>
                            </div>
                        </div>
                        
                        ${this.showPreferences ? `
                        <!-- Préférences -->
                        <div style="background: white; border-radius: 8px; padding: 1rem; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.06); border: 1px solid rgba(0, 85, 164, 0.1);">
                            <h4 style="margin: 0 0 0.75rem 0; font-size: 0.9rem; font-weight: 800; color: #0055A4; font-family: 'Roboto', sans-serif; border-bottom: 2px solid rgba(0, 85, 164, 0.1); padding-bottom: 0.5rem;">⭐ Préférences</h4>
                            <div style="font-size: 0.8rem; line-height: 1.6;">
                                ${team.horaires_preferes && team.horaires_preferes.length > 0 ? `
                                <div style="margin-bottom: 0.5rem;">
                                    <span style="color: #666; font-weight: 600;">🕐 Horaires préférés:</span><br>
                                    <span style="color: #0055A4; font-weight: 700;">${team.horaires_preferes.join(', ')}</span>
                                </div>
                                ` : ''}
                                ${team.lieux_preferes && team.lieux_preferes.length > 0 ? `
                                <div style="margin-bottom: 0.5rem;">
                                    <span style="color: #666; font-weight: 600;">📍 Lieux préférés:</span><br>
                                    <span style="color: #0055A4; font-weight: 700;">${team.lieux_preferes.join(', ')}</span>
                                </div>
                                ` : ''}
                                ${team.semaines_indisponibles && Object.keys(team.semaines_indisponibles).length > 0 ? `
                                <div>
                                    <span style="color: #666; font-weight: 600;">❌ Indisponibilités:</span><br>
                                    <span style="color: #EF4135; font-weight: 700;">Semaines ${Object.keys(team.semaines_indisponibles).join(', ')}</span>
                                </div>
                                ` : ''}
                                <div style="margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid rgba(0, 85, 164, 0.1);">
                                    <span style="color: #666;">Taux de respect:</span>
                                    <strong style="color: ${stats.preferenceRate >= 70 ? '#27AE60' : stats.preferenceRate >= 40 ? '#FF9500' : '#EF4135'}; font-size: 0.9rem;">${stats.preferenceRate.toFixed(0)}%</strong>
                                </div>
                            </div>
                        </div>
                        ` : ''}
                        
                        <!-- Récapitulatif des matchs -->
                        <div style="background: white; border-radius: 8px; padding: 1rem; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.06); border: 1px solid rgba(0, 85, 164, 0.1); ${this.showPreferences ? '' : 'grid-column: 1 / -1;'}">
                            <h4 style="margin: 0 0 0.75rem 0; font-size: 0.9rem; font-weight: 800; color: #0055A4; font-family: 'Roboto', sans-serif; border-bottom: 2px solid rgba(0, 85, 164, 0.1); padding-bottom: 0.5rem;">⚽ Matchs (${stats.matches.length})</h4>
                            <div style="max-height: 300px; overflow-y: auto; font-size: 0.75rem;">
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
            return '<div style="text-align: center; padding: 2rem; color: #999;">Aucun match</div>';
        }
        
        let html = '<div style="display: grid; gap: 0.5rem;">';
        
        matches.forEach(match => {
            const isTeam1 = match.equipe1_id === team.id;
            const opponent = isTeam1 ? match.equipe2_nom : match.equipe1_nom;
            const isScheduled = match.semaine && match.horaire && match.gymnase;
            const hasScore = match.score && match.score.has_score;
            const isEntente = match.is_entente;
            
            let statusBg = 'rgba(0, 85, 164, 0.05)';
            let statusColor = '#0055A4';
            let statusText = 'À planifier';
            
            if (isEntente && !isScheduled) {
                // Match entente sans créneau = à jouer hors calendrier
                statusBg = 'rgba(156, 39, 176, 0.1)'; // Violet
                statusColor = '#9C27B0';
                statusText = 'Entente';
            } else if (hasScore) {
                statusBg = 'rgba(39, 174, 96, 0.1)';
                statusColor = '#27AE60';
                statusText = 'Terminé';
            } else if (isScheduled) {
                statusBg = 'rgba(0, 123, 255, 0.1)';
                statusColor = '#007BFF';
                statusText = 'À venir';
            } else {
                statusBg = 'rgba(239, 65, 53, 0.1)';
                statusColor = '#EF4135';
            }
            
            let scoreDisplay = '';
            if (hasScore) {
                const teamScore = isTeam1 ? match.score.equipe1 : match.score.equipe2;
                const oppScore = isTeam1 ? match.score.equipe2 : match.score.equipe1;
                const isWin = teamScore > oppScore;
                const isDraw = teamScore === oppScore;
                scoreDisplay = `<span style="font-weight: 900; color: ${isWin ? '#27AE60' : isDraw ? '#FF9500' : '#EF4135'}; font-family: 'Roboto Mono', monospace;">${teamScore} - ${oppScore}</span>`;
            }
            
            html += `
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.5rem; background: ${statusBg}; border-radius: 6px; border: 1px solid ${statusColor}33;">
                    <div style="flex: 1;">
                        <div style="font-weight: 700; color: #333; margin-bottom: 0.2rem;">
                            vs ${opponent}
                            ${isEntente ? '<span style="font-size: 0.9rem; margin-left: 0.3rem;" title="Match en entente">🤝</span>' : ''}
                        </div>
                        ${isScheduled ? `<div style="color: #666; font-size: 0.7rem;">S${match.semaine} • ${match.horaire} • ${match.gymnase}</div>` : ''}
                        ${isEntente && !isScheduled ? `<div style="color: ${statusColor}; font-size: 0.7rem; font-style: italic;">À jouer hors calendrier officiel</div>` : ''}
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        ${scoreDisplay}
                        <span style="font-size: 0.65rem; font-weight: 700; padding: 0.2rem 0.4rem; background: white; border-radius: 4px; color: ${statusColor}; text-transform: uppercase;">${statusText}</span>
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
                <div class="teams-group" style="margin-bottom: 2rem;">
                    <h3 style="margin: 0 0 1rem 0; font-size: 1.2rem; font-weight: 800; color: #0055A4; font-family: 'Inter', 'Roboto', sans-serif; padding-bottom: 0.75rem; border-bottom: 3px solid rgba(0, 85, 164, 0.2);">
                        ${this._getGroupIcon()} ${groupName}
                        <span style="font-size: 0.85rem; font-weight: 600; color: #666; margin-left: 0.5rem;">(${groupTeams.length})</span>
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
