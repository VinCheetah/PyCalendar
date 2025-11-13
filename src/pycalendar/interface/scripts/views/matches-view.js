/**
 * matches-view.js - Vue Matchs (anciennement Cartes)
 * 
 * Affiche tous les matchs sous forme de cartes détaillées avec filtrage avancé
 * et options de groupement multiples.
 */

class MatchesView {
    constructor(dataManager, container) {
        this.dataManager = dataManager;
        this.container = container;
        
        // État des filtres
        this.activeFilters = {
            status: 'all', // 'all', 'fixed', 'scheduled', 'unscheduled', 'entente'
            gender: '',
            institution: '',
            pool: '',
            venue: '',
            week: '',
            team: ''
        };
        
        // Options de groupement
        this.groupBy = 'week'; // 'week', 'venue', 'pool', 'gender', 'level', 'none'
        
        // Options d'affichage
        this.sortBy = 'week'; // 'week', 'penalties', 'pool'
        this.showPenalties = true;
        this.showPoolInfo = true;
        
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
     * Met à jour les filtres
     */
    updateFilters(filters) {
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
     * Retourne la configuration des options d'affichage pour le panneau latéral
     */
    getDisplayOptions() {
        return {
            title: "Options d'affichage",
            options: [
                {
                    type: 'button-group',
                    id: 'matches-group-by',
                    label: 'Grouper par',
                    values: [
                        { value: 'none', text: 'Aucun' },
                        { value: 'week', text: '📅 Semaine' },
                        { value: 'venue', text: '🏛️ Gymnase' },
                        { value: 'pool', text: '🏆 Poule' },
                        { value: 'gender', text: '👥 Genre' },
                        { value: 'level', text: '🎯 Niveau' }
                    ],
                    default: this.groupBy,
                    action: (value) => {
                        this.setGroupBy(value);
                    }
                },
                {
                    type: 'select',
                    id: 'matches-sort-by',
                    label: 'Trier par',
                    values: [
                        { value: 'week', text: 'Semaine' },
                        { value: 'penalties', text: 'Pénalités' },
                        { value: 'pool', text: 'Poule' }
                    ],
                    default: this.sortBy,
                    action: (value) => {
                        this.setSortBy(value);
                    }
                },
                {
                    type: 'checkbox',
                    id: 'matches-show-penalties',
                    label: 'Afficher les pénalités détaillées',
                    default: this.showPenalties,
                    action: (checked) => {
                        this.showPenalties = checked;
                        this.render();
                    }
                },
                {
                    type: 'checkbox',
                    id: 'matches-show-pool-info',
                    label: 'Afficher les informations de poule',
                    default: this.showPoolInfo,
                    action: (checked) => {
                        this.showPoolInfo = checked;
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
        
        if (!data || !data.matches) {
            this.renderEmpty();
            return;
        }
        
        // Combiner tous les matchs (planifiés, non planifiés, fixes)
        const allMatches = this._getAllMatches(data);
        
        // Appliquer les filtres
        const filteredMatches = this._applyFilters(allMatches);
        
        if (filteredMatches.length === 0) {
            this.renderNoResults();
            return;
        }
        
        // Trier les matchs
        const sortedMatches = this._sortMatches(filteredMatches);
        
        // Grouper les matchs
        const groupedMatches = this._groupMatches(sortedMatches);
        
        // Générer le HTML
        const html = this._generateHTML(groupedMatches, filteredMatches.length, data);
        
        this.container.innerHTML = html;
        
        // Attacher les event listeners
        this._attachEventListeners();
    }
    
    /**
     * Affiche l'état vide
     */
    renderEmpty() {
        this.container.innerHTML = `
            <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 60vh; text-align: center; padding: 2rem;">
                <div style="font-size: 5rem; margin-bottom: 1.5rem; opacity: 0.5;">🏐</div>
                <h3 style="font-size: 1.5rem; font-weight: 700; color: #333; margin-bottom: 0.75rem; font-family: 'Inter', 'Roboto', sans-serif;">Aucun match</h3>
                <p style="font-size: 1rem; color: #666; font-family: 'Roboto', sans-serif;">Les matchs apparaîtront ici une fois planifiés.</p>
            </div>
        `;
    }
    
    /**
     * Affiche aucun résultat
     */
    renderNoResults() {
        this.container.innerHTML = `
            <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 60vh; text-align: center; padding: 2rem;">
                <div style="font-size: 5rem; margin-bottom: 1.5rem; opacity: 0.5;">🔍</div>
                <h3 style="font-size: 1.5rem; font-weight: 700; color: #333; margin-bottom: 0.75rem; font-family: 'Inter', 'Roboto', sans-serif;">Aucun résultat</h3>
                <p style="font-size: 1rem; color: #666; font-family: 'Roboto', sans-serif;">Aucun match ne correspond aux filtres sélectionnés.</p>
            </div>
        `;
    }
    
    /**
     * Récupère tous les matchs (planifiés + non planifiés + fixes + ententes)
     */
    _getAllMatches(data) {
        const allMatches = [];
        
        // Matchs planifiés
        if (data.matches.scheduled) {
            data.matches.scheduled.forEach(match => {
                allMatches.push({
                    ...match,
                    status: this._determineMatchStatus(match)
                });
            });
        }
        
        // Matchs non planifiés (peuvent inclure des ententes)
        if (data.matches.unscheduled) {
            data.matches.unscheduled.forEach(match => {
                const matchWithNulls = {
                    ...match,
                    semaine: null,
                    horaire: null,
                    gymnase: null,
                    jour: null
                };
                // Déterminer si c'est une entente ou un match non planifié normal
                matchWithNulls.status = this._determineMatchStatus(matchWithNulls);
                allMatches.push(matchWithNulls);
            });
        }
        
        return allMatches;
    }
    
    /**
     * Détermine le statut d'un match
     * Une entente est un match NON PLANIFIÉ entre institutions de la liste des ententes
     */
    _determineMatchStatus(match) {
        // Vérifier si c'est un match fixé avant planification
        if (match.is_fixed === true || match.fixed === true) {
            return 'fixed';
        }
        
        // Vérifier si le match a un gymnase et un horaire (= planifié par le solveur)
        if (match.gymnase && match.horaire && match.semaine) {
            return 'scheduled';
        }
        
        // Si le match n'est pas planifié, vérifier si c'est une entente
        // Une entente = match non planifié spécial (moins pénalisé)
        if (match.is_entente || (match.penalties && match.penalties.entente !== undefined)) {
            return 'entente';
        }
        
        // Sinon non planifié normal
        return 'unscheduled';
    }
    
    /**
     * Applique les filtres aux matchs
     */
    _applyFilters(matches) {
        let filtered = matches;
        
        // Filtre par statut
        if (this.activeFilters.status !== 'all') {
            filtered = filtered.filter(m => m.status === this.activeFilters.status);
        }
        
        // Filtre par genre
        if (this.activeFilters.gender) {
            filtered = filtered.filter(m => {
                const genre = m.equipe1_genre || m.equipe2_genre;
                return genre === this.activeFilters.gender;
            });
        }
        
        // Filtre par institution
        if (this.activeFilters.institution) {
            filtered = filtered.filter(m => 
                m.equipe1_institution === this.activeFilters.institution || 
                m.equipe2_institution === this.activeFilters.institution
            );
        }
        
        // Filtre par poule
        if (this.activeFilters.pool) {
            filtered = filtered.filter(m => m.poule === this.activeFilters.pool);
        }
        
        // Filtre par gymnase
        if (this.activeFilters.venue) {
            filtered = filtered.filter(m => m.gymnase === this.activeFilters.venue);
        }
        
        // Filtre par semaine
        if (this.activeFilters.week) {
            const weekNum = parseInt(this.activeFilters.week);
            filtered = filtered.filter(m => m.semaine === weekNum);
        }
        
        // Filtre par équipe - support des IDs multiples (groupe M+F)
        if (this.activeFilters.equipe) {
            const equipeIds = this.activeFilters.equipe.split(',');
            filtered = filtered.filter(m => {
                const equipe1Id = m.equipe1_id || m.equipes?.[0];
                const equipe2Id = m.equipe2_id || m.equipes?.[1];
                return equipeIds.includes(equipe1Id) || equipeIds.includes(equipe2Id);
            });
        }
        
        // Filtre par équipe (recherche texte - ancienne méthode)
        if (this.activeFilters.team) {
            const searchTerm = this.activeFilters.team.toLowerCase();
            filtered = filtered.filter(m =>
                (m.equipe1_nom && m.equipe1_nom.toLowerCase().includes(searchTerm)) ||
                (m.equipe2_nom && m.equipe2_nom.toLowerCase().includes(searchTerm)) ||
                (m.equipe1_nom_complet && m.equipe1_nom_complet.toLowerCase().includes(searchTerm)) ||
                (m.equipe2_nom_complet && m.equipe2_nom_complet.toLowerCase().includes(searchTerm))
            );
        }
        
        return filtered;
    }
    
    /**
     * Trie les matchs selon le mode choisi
     */
    _sortMatches(matches) {
        const sorted = [...matches];
        
        switch (this.sortBy) {
            case 'week':
                sorted.sort((a, b) => {
                    // Non planifiés à la fin
                    if (!a.semaine && b.semaine) return 1;
                    if (a.semaine && !b.semaine) return -1;
                    if (!a.semaine && !b.semaine) return 0;
                    
                    // Tri par semaine puis horaire
                    if (a.semaine !== b.semaine) return a.semaine - b.semaine;
                    if (a.horaire && b.horaire) return a.horaire.localeCompare(b.horaire);
                    return 0;
                });
                break;
                
            case 'penalties':
                sorted.sort((a, b) => {
                    const penA = this._getTotalPenalties(a);
                    const penB = this._getTotalPenalties(b);
                    return penB - penA; // Décroissant
                });
                break;
                
            case 'pool':
                sorted.sort((a, b) => {
                    if (a.poule !== b.poule) return a.poule.localeCompare(b.poule);
                    if (a.semaine && b.semaine && a.semaine !== b.semaine) return a.semaine - b.semaine;
                    return 0;
                });
                break;
        }
        
        return sorted;
    }
    
    /**
     * Groupe les matchs selon le mode choisi
     */
    _groupMatches(matches) {
        if (this.groupBy === 'none') {
            return { 'Tous les matchs': matches };
        }
        
        const groups = {};
        
        matches.forEach(match => {
            let groupKey;
            
            switch (this.groupBy) {
                case 'week':
                    groupKey = match.semaine ? `Semaine ${match.semaine}` : 'Non planifiés';
                    break;
                    
                case 'venue':
                    groupKey = match.gymnase || 'Sans gymnase';
                    break;
                    
                case 'pool':
                    groupKey = match.poule || 'Sans poule';
                    break;
                    
                case 'gender':
                    const genre = match.equipe1_genre || match.equipe2_genre;
                    groupKey = genre === 'M' ? 'Masculin' : genre === 'F' ? 'Féminin' : 'Non défini';
                    break;
                    
                case 'level':
                    const poule = this.dataManager.getPouleById(match.poule);
                    if (poule && poule.niveau) {
                        groupKey = `Niveau ${poule.niveau}`;
                    } else {
                        groupKey = 'Niveau non défini';
                    }
                    break;
                    
                default:
                    groupKey = 'Tous les matchs';
            }
            
            if (!groups[groupKey]) {
                groups[groupKey] = [];
            }
            groups[groupKey].push(match);
        });
        
        return groups;
    }
    
    /**
     * Calcule le total des pénalités
     */
    _getTotalPenalties(match) {
        if (!match.penalties) return 0;
        return Object.values(match.penalties).reduce((sum, p) => sum + (p || 0), 0);
    }
    
    /**
     * Génère le HTML de la vue
     */
    _generateHTML(groupedMatches, totalMatches, data) {
        let html = '<div class="matches-view-container" style="padding: 1.5rem;">';
        
        // En-tête avec statistiques
        html += this._generateHeader(totalMatches, groupedMatches);
        
        // Groupes de matchs
        const groupKeys = Object.keys(groupedMatches).sort((a, b) => {
            // Trier les groupes de manière logique
            if (this.groupBy === 'week') {
                if (a === 'Non planifiés') return 1;
                if (b === 'Non planifiés') return -1;
                const numA = parseInt(a.match(/\d+/)?.[0] || 0);
                const numB = parseInt(b.match(/\d+/)?.[0] || 0);
                return numA - numB;
            }
            return a.localeCompare(b);
        });
        
        groupKeys.forEach(groupKey => {
            const matches = groupedMatches[groupKey];
            html += this._generateGroup(groupKey, matches, data);
        });
        
        html += '</div>';
        
        return html;
    }
    
    /**
     * Génère l'en-tête avec statistiques
     */
    _generateHeader(totalMatches, groupedMatches) {
        const groupCount = Object.keys(groupedMatches).length;
        
        return `
            <div style="background: linear-gradient(135deg, rgba(0, 85, 164, 0.08) 0%, rgba(0, 85, 164, 0.03) 100%); border: 1px solid rgba(0, 85, 164, 0.15); border-radius: 12px; padding: 1.25rem; margin-bottom: 1.5rem; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
                    <div>
                        <h2 style="font-size: 1.5rem; font-weight: 800; color: #0055A4; margin: 0 0 0.5rem 0; font-family: 'Inter', 'Roboto', sans-serif;">Vue Matchs</h2>
                        <p style="font-size: 0.9rem; color: #666; margin: 0; font-family: 'Roboto', sans-serif;">
                            <span style="font-weight: 700; font-family: 'Roboto Mono', monospace; color: #0055A4;">${totalMatches}</span> match${totalMatches > 1 ? 's' : ''} affiché${totalMatches > 1 ? 's' : ''}
                            ${this.groupBy !== 'none' ? ` • <span style="font-weight: 700; font-family: 'Roboto Mono', monospace;">${groupCount}</span> groupe${groupCount > 1 ? 's' : ''}` : ''}
                        </p>
                    </div>
                    <div style="display: flex; gap: 0.75rem; flex-wrap: wrap;">
                        ${this._generateStatusBadges()}
                    </div>
                </div>
            </div>
        `;
    }
    
    /**
     * Génère les badges de statut
     */
    _generateStatusBadges() {
        const data = this.dataManager.getData();
        if (!data || !data.matches) return '';
        
        const allMatches = this._getAllMatches(data);
        const fixedCount = allMatches.filter(m => m.status === 'fixed').length;
        const scheduledCount = allMatches.filter(m => m.status === 'scheduled').length;
        const unscheduledCount = allMatches.filter(m => m.status === 'unscheduled').length;
        const ententeCount = allMatches.filter(m => m.status === 'entente').length;
        
        return `
            <div style="display: inline-flex; align-items: center; gap: 0.4rem; padding: 0.4rem 0.75rem; background: rgba(138, 43, 226, 0.1); border-radius: 8px; border: 1px solid rgba(138, 43, 226, 0.25);">
                <span style="font-size: 0.85rem;">🔒</span>
                <span style="font-size: 0.75rem; font-weight: 800; color: #8A2BE2; font-family: 'Roboto Mono', monospace;">${fixedCount}</span>
                <span style="font-size: 0.75rem; font-weight: 600; color: #8A2BE2; font-family: 'Roboto', sans-serif;">Fixés</span>
            </div>
            <div style="display: inline-flex; align-items: center; gap: 0.4rem; padding: 0.4rem 0.75rem; background: rgba(39, 174, 96, 0.1); border-radius: 8px; border: 1px solid rgba(39, 174, 96, 0.25);">
                <span style="font-size: 0.85rem;">✅</span>
                <span style="font-size: 0.75rem; font-weight: 800; color: #27AE60; font-family: 'Roboto Mono', monospace;">${scheduledCount}</span>
                <span style="font-size: 0.75rem; font-weight: 600; color: #27AE60; font-family: 'Roboto', sans-serif;">Planifiés</span>
            </div>
            <div style="display: inline-flex; align-items: center; gap: 0.4rem; padding: 0.4rem 0.75rem; background: rgba(239, 65, 53, 0.1); border-radius: 8px; border: 1px solid rgba(239, 65, 53, 0.25);">
                <span style="font-size: 0.85rem;">❌</span>
                <span style="font-size: 0.75rem; font-weight: 800; color: #EF4135; font-family: 'Roboto Mono', monospace;">${unscheduledCount}</span>
                <span style="font-size: 0.75rem; font-weight: 600; color: #EF4135; font-family: 'Roboto', sans-serif;">Non planifiés</span>
            </div>
            ${ententeCount > 0 ? `
            <div style="display: inline-flex; align-items: center; gap: 0.4rem; padding: 0.4rem 0.75rem; background: rgba(255, 149, 0, 0.1); border-radius: 8px; border: 1px solid rgba(255, 149, 0, 0.25);">
                <span style="font-size: 0.85rem;">🤝</span>
                <span style="font-size: 0.75rem; font-weight: 800; color: #FF9500; font-family: 'Roboto Mono', monospace;">${ententeCount}</span>
                <span style="font-size: 0.75rem; font-weight: 600; color: #FF9500; font-family: 'Roboto', sans-serif;">Ententes</span>
            </div>
            ` : ''}
        `;
    }
    
    /**
     * Génère un groupe de matchs
     */
    _generateGroup(groupTitle, matches, data) {
        let html = `
            <div style="margin-bottom: 2rem;">
                <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 2px solid rgba(0, 85, 164, 0.15);">
                    <h3 style="font-size: 1.25rem; font-weight: 800; color: #0055A4; margin: 0; font-family: 'Inter', 'Roboto', sans-serif;">${groupTitle}</h3>
                    <span style="font-size: 0.85rem; font-weight: 700; color: #666; font-family: 'Roboto Mono', monospace; padding: 0.25rem 0.6rem; background: rgba(0, 85, 164, 0.08); border-radius: 6px;">${matches.length}</span>
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(380px, 1fr)); gap: 1.25rem;">
        `;
        
        matches.forEach(match => {
            html += this._generateMatchCard(match, data);
        });
        
        html += '</div></div>';
        
        return html;
    }
    
    /**
     * Génère une carte de match détaillée
     */
    _generateMatchCard(match, data) {
        const gymnase = match.gymnase ? this.dataManager.getGymnaseById(match.gymnase) : null;
        const poule = match.poule ? this.dataManager.getPouleById(match.poule) : null;
        
        // Informations d'équipes
        const equipe1Nom = match.equipe1_nom_complet || match.equipe1_nom || 'Équipe 1';
        const equipe2Nom = match.equipe2_nom_complet || match.equipe2_nom || 'Équipe 2';
        const equipe1Num = match.equipe1_num ? `#${match.equipe1_num}` : '';
        const equipe2Num = match.equipe2_num ? `#${match.equipe2_num}` : '';
        
        // Statut et couleurs
        const statusInfo = this._getStatusInfo(match);
        
        // Genre
        const genre = match.equipe1_genre || match.equipe2_genre || 'M';
        const genreIcon = genre === 'M' ? '♂️' : '♀️';
        const genreBg = genre === 'M' ? 
            'linear-gradient(135deg, rgba(0, 123, 255, 0.08) 0%, rgba(0, 123, 255, 0.03) 100%)' :
            'linear-gradient(135deg, rgba(255, 20, 147, 0.08) 0%, rgba(255, 20, 147, 0.03) 100%)';
        
        // Pénalités
        const totalPenalties = this._getTotalPenalties(match);
        const penaltyColor = totalPenalties > 10 ? '#EF4135' : totalPenalties > 5 ? '#FF9500' : '#27AE60';
        
        // Score si disponible
        const hasScore = match.score && match.score.has_score && 
                        match.score.equipe1 !== null && match.score.equipe2 !== null;
        let scoreDisplay = '';
        if (hasScore) {
            const team1Winner = match.score.equipe1 > match.score.equipe2;
            const team2Winner = match.score.equipe2 > match.score.equipe1;
            scoreDisplay = `
                <div style="display: flex; align-items: center; gap: 0.5rem; margin-top: 0.5rem; padding: 0.5rem; background: rgba(0, 85, 164, 0.05); border-radius: 6px;">
                    <span style="font-size: 1.1rem; font-weight: 900; color: ${team1Winner ? '#FFD700' : '#333'}; font-family: 'Roboto Mono', monospace;">${match.score.equipe1}</span>
                    <span style="font-size: 0.8rem; color: #999;">-</span>
                    <span style="font-size: 1.1rem; font-weight: 900; color: ${team2Winner ? '#FFD700' : '#333'}; font-family: 'Roboto Mono', monospace;">${match.score.equipe2}</span>
                    ${team1Winner || team2Winner ? '<span style="font-size: 1rem; margin-left: 0.25rem;">🏆</span>' : ''}
                </div>
            `;
        }
        
        return `
            <div class="match-card-detailed" data-match-id="${match.match_id}" style="background: white; border: 2px solid ${statusInfo.borderColor}; border-radius: 12px; padding: 1.25rem; box-shadow: 0 3px 10px rgba(0, 0, 0, 0.08); transition: all 0.2s ease; cursor: pointer; position: relative; overflow: hidden;">
                
                <!-- Badge de statut -->
                <div style="position: absolute; top: 0; right: 0; padding: 0.4rem 0.8rem; background: ${statusInfo.bgColor}; color: white; font-size: 0.7rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em; border-bottom-left-radius: 8px; font-family: 'Roboto', sans-serif; box-shadow: -2px 2px 6px rgba(0, 0, 0, 0.1);">
                    ${statusInfo.icon} ${statusInfo.label}
                </div>
                
                <!-- En-tête -->
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem; padding-right: 4rem;">
                    <div>
                        ${match.semaine ? `
                        <div style="font-size: 0.8rem; font-weight: 800; color: #0055A4; font-family: 'Roboto Mono', monospace; background: rgba(0, 85, 164, 0.08); padding: 0.25rem 0.6rem; border-radius: 6px; display: inline-block; margin-bottom: 0.5rem;">
                            SEMAINE ${match.semaine}
                        </div>
                        ` : ''}
                        ${this.showPoolInfo && poule ? `
                        <div style="font-size: 0.75rem; color: #666; font-family: 'Roboto', sans-serif; margin-top: 0.25rem;">
                            <span style="font-weight: 700;">${poule.nom}</span>
                            ${poule.niveau ? ` • Niveau ${poule.niveau}` : ''}
                        </div>
                        ` : ''}
                    </div>
                    <div style="text-align: right;">
                        <span style="font-size: 1.5rem;">${genreIcon}</span>
                        ${totalPenalties > 0 ? `
                        <div style="font-size: 0.75rem; font-weight: 900; color: ${penaltyColor}; font-family: 'Roboto Mono', monospace; margin-top: 0.25rem;">
                            ⚠️ ${totalPenalties.toFixed(1)}
                        </div>
                        ` : ''}
                    </div>
                </div>
                
                <!-- Corps: Équipes -->
                <div style="background: ${genreBg}; border-radius: 10px; padding: 1rem; margin-bottom: 1rem;">
                    <div style="display: flex; align-items: center; justify-content: space-between; gap: 1rem;">
                        <!-- Équipe 1 -->
                        <div style="flex: 1; text-align: left;">
                            <div style="display: flex; align-items: center; gap: 0.4rem; margin-bottom: 0.25rem;">
                                ${equipe1Num ? `<span style="font-size: 0.65rem; font-weight: 800; background: rgba(0, 85, 164, 0.15); padding: 0.15rem 0.4rem; border-radius: 4px; font-family: 'Roboto Mono', monospace; color: #0055A4;">${equipe1Num}</span>` : ''}
                                <span style="font-size: 0.95rem; font-weight: 800; color: #0055A4; font-family: 'Inter', 'Roboto', sans-serif;">${equipe1Nom}</span>
                            </div>
                            ${match.equipe1_institution ? `
                            <div style="font-size: 0.7rem; color: #666; font-family: 'Roboto', sans-serif;">
                                ${match.equipe1_institution}
                            </div>
                            ` : ''}
                            ${this._getPreferredTimeBadge(match.equipe1_horaires_preferes, match.horaire)}
                        </div>
                        
                        <!-- VS -->
                        <div style="flex-shrink: 0;">
                            <div style="display: inline-flex; align-items: center; justify-content: center; width: 40px; height: 40px; background: white; border: 2px solid rgba(0, 85, 164, 0.2); border-radius: 50%; font-size: 0.7rem; font-weight: 900; color: #0055A4; box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1); font-family: 'Roboto', sans-serif;">
                                VS
                            </div>
                        </div>
                        
                        <!-- Équipe 2 -->
                        <div style="flex: 1; text-align: right;">
                            <div style="display: flex; align-items: center; gap: 0.4rem; justify-content: flex-end; margin-bottom: 0.25rem;">
                                <span style="font-size: 0.95rem; font-weight: 800; color: #0055A4; font-family: 'Inter', 'Roboto', sans-serif;">${equipe2Nom}</span>
                                ${equipe2Num ? `<span style="font-size: 0.65rem; font-weight: 800; background: rgba(0, 85, 164, 0.15); padding: 0.15rem 0.4rem; border-radius: 4px; font-family: 'Roboto Mono', monospace; color: #0055A4;">${equipe2Num}</span>` : ''}
                            </div>
                            ${match.equipe2_institution ? `
                            <div style="font-size: 0.7rem; color: #666; font-family: 'Roboto', sans-serif;">
                                ${match.equipe2_institution}
                            </div>
                            ` : ''}
                            <div style="display: flex; justify-content: flex-end;">
                                ${this._getPreferredTimeBadge(match.equipe2_horaires_preferes, match.horaire)}
                            </div>
                        </div>
                    </div>
                    ${scoreDisplay}
                </div>
                
                <!-- Informations de planification -->
                ${match.gymnase || match.horaire || match.jour ? `
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 0.75rem; margin-bottom: ${this.showPenalties && totalPenalties > 0 ? '1rem' : '0'};">
                    ${match.gymnase ? `
                    <div style="display: flex; align-items: center; gap: 0.4rem; padding: 0.5rem 0.75rem; background: rgba(0, 85, 164, 0.06); border-radius: 8px; border: 1px solid rgba(0, 85, 164, 0.1);">
                        <span style="font-size: 0.9rem;">📍</span>
                        <div style="flex: 1; min-width: 0;">
                            <div style="font-size: 0.65rem; font-weight: 700; text-transform: uppercase; color: #999; font-family: 'Roboto', sans-serif; letter-spacing: 0.05em;">Gymnase</div>
                            <div style="font-size: 0.8rem; font-weight: 700; color: #333; font-family: 'Roboto', sans-serif; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${gymnase?.nom || match.gymnase}">${gymnase?.nom || match.gymnase}</div>
                        </div>
                    </div>
                    ` : ''}
                    ${match.jour ? `
                    <div style="display: flex; align-items: center; gap: 0.4rem; padding: 0.5rem 0.75rem; background: rgba(0, 85, 164, 0.06); border-radius: 8px; border: 1px solid rgba(0, 85, 164, 0.1);">
                        <span style="font-size: 0.9rem;">📅</span>
                        <div style="flex: 1;">
                            <div style="font-size: 0.65rem; font-weight: 700; text-transform: uppercase; color: #999; font-family: 'Roboto', sans-serif; letter-spacing: 0.05em;">Jour</div>
                            <div style="font-size: 0.8rem; font-weight: 700; color: #333; font-family: 'Roboto', sans-serif;">${match.jour}</div>
                        </div>
                    </div>
                    ` : ''}
                    ${match.horaire ? `
                    <div style="display: flex; align-items: center; gap: 0.4rem; padding: 0.5rem 0.75rem; background: rgba(0, 85, 164, 0.06); border-radius: 8px; border: 1px solid rgba(0, 85, 164, 0.1);">
                        <span style="font-size: 0.9rem;">🕒</span>
                        <div style="flex: 1;">
                            <div style="font-size: 0.65rem; font-weight: 700; text-transform: uppercase; color: #999; font-family: 'Roboto', sans-serif; letter-spacing: 0.05em;">Horaire</div>
                            <div style="font-size: 0.8rem; font-weight: 900; color: #333; font-family: 'Roboto Mono', monospace;">${match.horaire}</div>
                        </div>
                    </div>
                    ` : ''}
                </div>
                ` : ''}
                
                <!-- Pénalités détaillées -->
                ${this.showPenalties && totalPenalties > 0 ? this._generatePenaltiesDetail(match.penalties) : ''}
            </div>
        `;
    }
    
    /**
     * Retourne les informations de statut pour un match
     */
    _getStatusInfo(match) {
        switch (match.status) {
            case 'fixed':
                return {
                    label: 'Fixé',
                    icon: '🔒',
                    bgColor: '#8A2BE2',
                    borderColor: 'rgba(138, 43, 226, 0.3)'
                };
            case 'scheduled':
                return {
                    label: 'Planifié',
                    icon: '✅',
                    bgColor: '#27AE60',
                    borderColor: 'rgba(39, 174, 96, 0.3)'
                };
            case 'entente':
                return {
                    label: 'Entente',
                    icon: '🤝',
                    bgColor: '#FF9500',
                    borderColor: 'rgba(255, 149, 0, 0.3)'
                };
            case 'unscheduled':
            default:
                return {
                    label: 'Non planifié',
                    icon: '❌',
                    bgColor: '#EF4135',
                    borderColor: 'rgba(239, 65, 53, 0.3)'
                };
        }
    }
    
    /**
     * Génère le badge d'horaire préféré pour une équipe
     * URGENT (rouge) si le match démarre AVANT l'horaire préféré
     * INFO (orange) si le match démarre APRÈS l'horaire préféré
     * Affiche aussi pour les matchs non planifiés/ententes
     */
    _getPreferredTimeBadge(preferredTimes, matchTime) {
        if (!preferredTimes || preferredTimes.length === 0) {
            return '';
        }
        
        // Pour les matchs non planifiés/ententes, afficher simplement l'horaire préféré
        if (!matchTime) {
            const prefTime = preferredTimes[0];
            return `
                <div style="display: inline-flex; align-items: center; gap: 0.3rem; padding: 0.25rem 0.5rem; background: rgba(0, 85, 164, 0.1); border: 1px solid rgba(0, 85, 164, 0.25); border-radius: 6px; margin-top: 0.3rem;">
                    <span style="font-size: 0.7rem;">🕒</span>
                    <span style="font-size: 0.7rem; font-weight: 700; color: #0055A4; font-family: 'Roboto Mono', monospace;">Préf: ${prefTime}</span>
                </div>
            `;
        }
        
        const matchMinutes = this._timeToMinutes(matchTime);
        
        // Trouver le premier horaire préféré différent de l'horaire du match
        for (const prefTime of preferredTimes) {
            if (prefTime !== matchTime) {
                const prefMinutes = this._timeToMinutes(prefTime);
                const isBefore = matchMinutes < prefMinutes; // Match démarre AVANT l'horaire préféré
                
                if (isBefore) {
                    // Match AVANT l'horaire préféré = URGENT = TRÈS VISIBLE (rouge)
                    return `
                        <div style="display: inline-flex; align-items: center; gap: 0.3rem; padding: 0.25rem 0.5rem; background: rgba(239, 65, 53, 0.15); border: 1.5px solid rgba(239, 65, 53, 0.4); border-radius: 6px; margin-top: 0.3rem;">
                            <span style="font-size: 0.7rem;">⚠️</span>
                            <span style="font-size: 0.7rem; font-weight: 900; color: #EF4135; font-family: 'Roboto Mono', monospace;">Préf: ${prefTime}</span>
                        </div>
                    `;
                } else {
                    // Match APRÈS l'horaire préféré = INFO (orange discret)
                    return `
                        <div style="display: inline-flex; align-items: center; gap: 0.3rem; padding: 0.25rem 0.5rem; background: rgba(255, 149, 0, 0.1); border: 1px solid rgba(255, 149, 0, 0.25); border-radius: 6px; margin-top: 0.3rem;">
                            <span style="font-size: 0.7rem;">⏰</span>
                            <span style="font-size: 0.7rem; font-weight: 700; color: #FF9500; font-family: 'Roboto Mono', monospace;">Préf: ${prefTime}</span>
                        </div>
                    `;
                }
            }
        }
        
        return '';
    }
    
    /**
     * Convertit un horaire "HH:MM" en minutes depuis minuit
     */
    _timeToMinutes(timeStr) {
        if (!timeStr) return 0;
        const [hours, minutes] = timeStr.split(':').map(Number);
        return hours * 60 + (minutes || 0);
    }
    
    /**
     * Génère le détail des pénalités
     */
    _generatePenaltiesDetail(penalties) {
        if (!penalties) return '';
        
        const items = Object.entries(penalties)
            .filter(([key, value]) => value > 0 && key !== 'total')
            .sort((a, b) => b[1] - a[1])
            .slice(0, 5); // Top 5
        
        if (items.length === 0) return '';
        
        let html = `
            <div style="background: rgba(255, 149, 0, 0.05); border: 1px solid rgba(255, 149, 0, 0.15); border-radius: 8px; padding: 0.75rem;">
                <div style="font-size: 0.75rem; font-weight: 800; text-transform: uppercase; color: #FF9500; margin-bottom: 0.5rem; font-family: 'Roboto', sans-serif; letter-spacing: 0.05em;">
                    ⚠️ Pénalités détaillées
                </div>
                <div style="display: grid; gap: 0.4rem;">
        `;
        
        items.forEach(([type, value]) => {
            const label = this._getPenaltyLabel(type);
            html += `
                <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.75rem; padding: 0.25rem 0.5rem; background: white; border-radius: 4px;">
                    <span style="color: #666; font-family: 'Roboto', sans-serif;">${label}</span>
                    <span style="font-weight: 900; color: #FF9500; font-family: 'Roboto Mono', monospace;">${value.toFixed(1)}</span>
                </div>
            `;
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
            'unavailable_slot': 'Créneau indisponible',
            'capacity': 'Capacité dépassée',
            'institution_conflict': 'Conflit établissement',
            'time_preference': 'Horaire non préféré',
            'venue_preference': 'Lieu non préféré',
            'rest_weeks': 'Semaines de repos',
            'entente': 'Entente non planifiée'
        };
        
        return labels[type] || type;
    }
    
    /**
     * Attache les event listeners
     */
    _attachEventListeners() {
        // Hover sur les cartes
        const matchCards = this.container.querySelectorAll('.match-card-detailed');
        matchCards.forEach(card => {
            card.addEventListener('mouseenter', (e) => {
                e.currentTarget.style.transform = 'translateY(-4px)';
                e.currentTarget.style.boxShadow = '0 6px 20px rgba(0, 0, 0, 0.15)';
            });
            
            card.addEventListener('mouseleave', (e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = '0 3px 10px rgba(0, 0, 0, 0.08)';
            });
            
            // Double-clic pour éditer
            card.addEventListener('dblclick', (e) => {
                const matchId = e.currentTarget.dataset.matchId;
                // TODO: Ouvrir modal d'édition
                console.log('Éditer match:', matchId);
            });
        });
    }
    
    /**
     * Nettoie la vue
     */
    destroy() {
        this.container.innerHTML = '';
    }
}

// Export pour utilisation
if (typeof window !== 'undefined') {
    window.MatchesView = MatchesView;
}
