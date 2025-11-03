/**
 * pools-view.js - Vue Poules Améliorée
 * 
 * Affiche les poules organisées par genre et niveau avec :
 * - Organisation claire en colonnes par genre (F/M)
 * - Classement par niveau au sein de chaque genre
 * - Statistiques détaillées et informations riches
 * - Matchs passés, à venir et résultats
 * - Interactions fluides et animations élégantes
 * 
 * Code de haute qualité, maintenable et performant.
 */

class PoolsView {
    constructor(dataManager, container) {
        this.dataManager = dataManager;
        this.container = container;
        this.expandedPools = new Set();
        this.selectedFilters = {};
        this.activeMatchTabs = {}; // Onglet actif par poule (played/upcoming/all)
        
        // Options d'affichage
        this.displayOptions = {
            format: 'cards', // 'cards', 'compact', 'list'
            showTeams: false,
            showLevelSeparators: true,
            showPreferences: false
        };
        
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
     * Retourne la configuration des options d'affichage pour cette vue.
     * Options réellement fonctionnelles et utiles pour la vue Poules.
     */
    getDisplayOptions() {
        return {
            title: "Options - Vue Poules",
            options: [
                // Format d'affichage - FONCTIONNEL
                {
                    type: 'button-group',
                    id: 'pools-format',
                    label: '📐 Format',
                    values: [
                        { value: 'cards', text: 'Cartes' },
                        { value: 'compact', text: 'Compact' },
                        { value: 'list', text: 'Liste' }
                    ],
                    default: this.displayOptions.format,
                    action: (value) => {
                        this.displayOptions.format = value;
                        this.render();
                    }
                },
                
                // Coloration des matchs - NOUVEAU
                {
                    type: 'select',
                    id: 'pools-color-scheme',
                    label: '🎨 Coloration des matchs',
                    values: [
                        { value: 'none', text: 'Aucune' },
                        { value: 'by-status', text: 'Par statut' },
                        { value: 'by-venue', text: 'Par lieu' },
                        { value: 'by-gender', text: 'Par genre' },
                        { value: 'by-level', text: 'Par niveau' }
                    ],
                    default: this.displayOptions.colorScheme || 'none',
                    action: (value) => {
                        this.displayOptions.colorScheme = value;
                        this.applyColorScheme(value);
                    }
                },
                
                // Afficher les équipes - FONCTIONNEL
                {
                    type: 'checkbox',
                    id: 'pools-show-teams',
                    label: '👥 Afficher liste des équipes',
                    default: this.displayOptions.showTeams,
                    action: (checked) => {
                        this.displayOptions.showTeams = checked;
                        this.render();
                    }
                },
                
                // Afficher les préférences - FONCTIONNEL
                {
                    type: 'checkbox',
                    id: 'pools-show-preferences',
                    label: '⭐ Afficher préférences équipes',
                    default: this.displayOptions.showPreferences,
                    action: (checked) => {
                        this.displayOptions.showPreferences = checked;
                        this.render();
                    }
                },
                
                // Séparateurs de niveau - FONCTIONNEL
                {
                    type: 'checkbox',
                    id: 'pools-level-separators',
                    label: '📊 Séparateurs de niveau',
                    default: this.displayOptions.showLevelSeparators,
                    action: (checked) => {
                        this.displayOptions.showLevelSeparators = checked;
                        this.render();
                    }
                },
                
                // Auto-expand - FONCTIONNEL
                {
                    type: 'checkbox',
                    id: 'pools-auto-expand',
                    label: '� Tout développer',
                    default: this.displayOptions.autoExpand || false,
                    action: (checked) => {
                        this.displayOptions.autoExpand = checked;
                        if (checked) {
                            // Expand all pools
                            const data = this.dataManager.getData();
                            if (data?.entities?.poules) {
                                data.entities.poules.forEach(pool => {
                                    this.expandedPools.add(pool.id);
                                });
                            }
                        } else {
                            // Collapse all
                            this.expandedPools.clear();
                        }
                        this.render();
                    }
                }
            ]
        };
    }
    
    /**
     * Applique un schéma de couleurs aux matchs
     * @param {string} scheme - Le schéma à appliquer ('none', 'by-status', 'by-venue', etc.)
     */
    applyColorScheme(scheme) {
        // Appliquer l'attribut data-color-scheme sur le conteneur
        if (scheme === 'none') {
            this.container.removeAttribute('data-color-scheme');
        } else {
            this.container.setAttribute('data-color-scheme', scheme);
        }
        
        // Sauvegarder la préférence
        localStorage.setItem('pools-color-scheme', scheme);
        
        // Si on doit ajouter des attributs spécifiques sur chaque match, on re-render
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
     * Génère le HTML de la vue - Organisation par genre
     */
    _generateHTML(pools, data) {
        let html = '<div class="pools-view">';
        
        // En-tête avec résumé global
        html += this._generateGlobalSummary(pools, data);
        
        // Organisation par genre
        html += this._generatePoolsByGender(pools, data);
        
        html += '</div>';
        
        return html;
    }
    
    /**
     * Supprimé : les options sont maintenant gérées par ViewOptionsManager
     */
    // _generateDisplayOptions() { ... }
    
    /**
     * Génère le résumé global
     */
    _generateGlobalSummary(pools, data) {
        const totalTeams = pools.reduce((sum, p) => sum + (p.nb_equipes || 0), 0);
        const totalMatches = pools.reduce((sum, p) => 
            sum + (p.nb_matchs_planifies || 0) + (p.nb_matchs_non_planifies || 0), 0);
        const scheduledMatches = pools.reduce((sum, p) => 
            sum + (p.nb_matchs_planifies || 0), 0);
        const unscheduledMatches = pools.reduce((sum, p) => 
            sum + (p.nb_matchs_non_planifies || 0), 0);
        
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
                    <div class="summary-label">Matchs Total</div>
                </div>
                <div class="summary-card">
                    <div class="summary-value">${scheduledMatches}</div>
                    <div class="summary-label">Matchs Planifiés</div>
                </div>
                <div class="summary-card">
                    <div class="summary-value">${unscheduledMatches}</div>
                    <div class="summary-label">Non Planifiés</div>
                </div>
            </div>
        `;
    }
    
    /**
     * Génère l'organisation par genre
     */
    _generatePoolsByGender(pools, data) {
        // Grouper par genre
        const byGender = this._groupPoolsByGender(pools);
        
        let html = '<div class="pools-by-gender">';
        
        // Genre Féminin
        if (byGender.F && byGender.F.length > 0) {
            html += this._generateGenderSection('F', byGender.F, data);
        }
        
        // Genre Masculin
        if (byGender.M && byGender.M.length > 0) {
            html += this._generateGenderSection('M', byGender.M, data);
        }
        
        html += '</div>';
        
        return html;
    }
    
    /**
     * Groupe les poules par genre
     */
    _groupPoolsByGender(pools) {
        const grouped = { F: [], M: [] };
        
        pools.forEach(pool => {
            if (pool.genre === 'F') {
                grouped.F.push(pool);
            } else if (pool.genre === 'M') {
                grouped.M.push(pool);
            }
        });
        
        // Trier par niveau au sein de chaque genre
        grouped.F.sort((a, b) => this._comparePoolsByLevel(a, b));
        grouped.M.sort((a, b) => this._comparePoolsByLevel(a, b));
        
        return grouped;
    }
    
    /**
     * Compare deux poules par niveau
     */
    _comparePoolsByLevel(a, b) {
        // Extraire les niveaux (ex: "VBFA1PA" -> 1)
        const levelA = this._extractLevel(a.niveau || a.nom);
        const levelB = this._extractLevel(b.niveau || b.nom);
        
        if (levelA !== levelB) {
            return levelA - levelB;
        }
        
        // Si même niveau, trier par nom
        return a.nom.localeCompare(b.nom);
    }
    
    /**
     * Extrait le niveau numérique d'un nom de poule
     */
    _extractLevel(name) {
        // Chercher un chiffre dans le nom (ex: "VBFA1PA" -> 1)
        const match = name.match(/\d+/);
        return match ? parseInt(match[0]) : 999;
    }
    
    /**
     * Formate le niveau pour affichage (ex: "VBFA1PA" -> "A1")
     */
    _formatLevel(name) {
        // Extraire la lettre de catégorie (A, B, C...) et le chiffre
        // Ex: "VBFA1PA" -> "A1", "VBFA2PB" -> "A2"
        const match = name.match(/([A-Z])(\d+)/);
        if (match) {
            return `${match[1]}${match[2]}`;
        }
        // Fallback: juste le numéro
        const numMatch = name.match(/\d+/);
        return numMatch ? `N${numMatch[0]}` : 'N/A';
    }
    
    /**
     * Génère une section de genre
     */
    _generateGenderSection(gender, pools, data) {
        const genderLabel = gender === 'F' ? 'Féminin' : 'Masculin';
        const genderIcon = gender === 'F' ? '♀️' : '♂️';
        const genderClass = gender === 'F' ? 'female' : 'male';
        
        const totalTeams = pools.reduce((sum, p) => sum + (p.nb_equipes || 0), 0);
        const totalMatches = pools.reduce((sum, p) => 
            sum + (p.nb_matchs_planifies || 0) + (p.nb_matchs_non_planifies || 0), 0);
        
        let html = `
            <div class="gender-section ${genderClass}">
                <div class="gender-header">
                    <div class="gender-icon">${genderIcon}</div>
                    <div class="gender-title">
                        <h2>${genderLabel}</h2>
                        <div class="gender-subtitle">
                            ${pools.length} poule${pools.length > 1 ? 's' : ''} • 
                            ${totalTeams} équipe${totalTeams > 1 ? 's' : ''} • 
                            ${totalMatches} match${totalMatches > 1 ? 's' : ''}
                        </div>
                    </div>
                </div>
                <div class="pools-list ${this.displayOptions.format}">
        `;
        
        // Grouper par niveau si l'option est activée
        if (this.displayOptions.showLevelSeparators) {
            const poolsByLevel = this._groupPoolsByLevel(pools);
            let isFirst = true;
            
            for (const [level, levelPools] of Object.entries(poolsByLevel)) {
                if (!isFirst) {
                    html += this._generateLevelSeparator(level, levelPools, data);
                }
                isFirst = false;
                
                levelPools.forEach(pool => {
                    html += this._generatePoolMarkup(pool, data, gender);
                });
            }
        } else {
            pools.forEach(pool => {
                html += this._generatePoolMarkup(pool, data, gender);
            });
        }
        
        html += '</div></div>';
        
        return html;
    }
    
    /**
     * Groupe les poules par niveau
     */
    _groupPoolsByLevel(pools) {
        const grouped = {};
        
        pools.forEach(pool => {
            const level = this._formatLevel(pool.niveau || pool.nom);
            if (!grouped[level]) {
                grouped[level] = [];
            }
            grouped[level].push(pool);
        });
        
        return grouped;
    }
    
    /**
     * Génère un séparateur de niveau
     */
    _generateLevelSeparator(level, pools, data) {
        const totalTeams = pools.reduce((sum, p) => sum + (p.nb_equipes || 0), 0);
        
        return `
            <div class="level-separator">
                <div class="level-separator-line"></div>
                <div class="level-separator-label">
                    <span class="level-name">Niveau ${level}</span>
                    <span class="level-info">${pools.length} poule${pools.length > 1 ? 's' : ''} • ${totalTeams} équipe${totalTeams > 1 ? 's' : ''}</span>
                </div>
                <div class="level-separator-line"></div>
            </div>
        `;
    }
    
    /**
     * Génère le balisage pour une poule en fonction du format d'affichage.
     */
    _generatePoolMarkup(pool, data, gender) {
        switch (this.displayOptions.format) {
            case 'compact':
                return this._generatePoolCompact(pool, data, gender);
            case 'list':
                // Pour le format 'list', nous pourrions avoir besoin de construire les lignes
                // dans un contexte de tableau plus large, donc cela pourrait être différent.
                // Pour l'instant, traitons-le comme une ligne simple.
                return this._generatePoolListRow(pool, data, gender);
            case 'cards':
            default:
                return this._generatePoolCard(pool, data, gender);
        }
    }

    /**
     * Génère la vue compacte d'une poule.
     */
    _generatePoolCompact(pool, data, gender) {
        const genderClass = gender === 'F' ? 'female' : 'male';
        const poolMatches = this.dataManager.getMatchesByPool(pool.id);
        const completion = poolMatches.length > 0 ? (pool.nb_matchs_planifies / poolMatches.length) * 100 : 0;

        return `
            <div class="pool-compact ${genderClass}" data-pool-id="${pool.id}" onclick="window.poolsView.togglePool('${pool.id}')">
                <div class="pool-compact-main">
                    <span class="pool-compact-name">${pool.nom}</span>
                    <span class="pool-compact-level">${this._formatLevel(pool.niveau || pool.nom)}</span>
                </div>
                <div class="pool-compact-stats">
                    <span class="pool-compact-teams" title="${pool.nb_equipes} équipes">👥 ${pool.nb_equipes}</span>
                    <span class="pool-compact-matches" title="${poolMatches.length} matchs">⚽ ${poolMatches.length}</span>
                    <div class="pool-compact-progress" title="${completion.toFixed(0)}% planifié">
                        <div class="progress-bar" style="width: ${completion}%;"></div>
                    </div>
                </div>
                <button class="expand-btn ${this.expandedPools.has(pool.id) ? 'expanded' : ''}">▶</button>
            </div>
            ${this.expandedPools.has(pool.id) ? this._generateExpandedContent(pool, data) : ''}
        `;
    }

    /**
     * Génère une ligne de liste pour une poule.
     */
    _generatePoolListRow(pool, data, gender) {
        const genderClass = gender === 'F' ? 'female' : 'male';
        const poolMatches = this.dataManager.getMatchesByPool(pool.id);
        const scheduled = pool.nb_matchs_planifies || 0;
        const unscheduled = pool.nb_matchs_non_planifies || 0;

        return `
            <div class="pool-list-row ${genderClass}" data-pool-id="${pool.id}" onclick="window.poolsView.togglePool('${pool.id}')">
                <div class="pool-list-cell name">${pool.nom}</div>
                <div class="pool-list-cell level">${this._formatLevel(pool.niveau || pool.nom)}</div>
                <div class="pool-list-cell teams">${pool.nb_equipes}</div>
                <div class="pool-list-cell scheduled">${scheduled}</div>
                <div class="pool-list-cell unscheduled">${unscheduled}</div>
                <div class="pool-list-cell total">${scheduled + unscheduled}</div>
                <div class="pool-list-cell expand"><button class="expand-btn ${this.expandedPools.has(pool.id) ? 'expanded' : ''}">▶</button></div>
            </div>
            ${this.expandedPools.has(pool.id) ? this._generateExpandedContent(pool, data) : ''}
        `;
    }

    /**
     * Génère la carte d'une poule avec statistiques détaillées
     */
    _generatePoolCard(pool, data, gender) {
        const isExpanded = this.expandedPools.has(pool.id);
        const genderClass = gender === 'F' ? 'female' : 'male';
        const genderIcon = gender === 'F' ? '♀️' : '♂️';
        
        // Récupérer les matchs de la poule
        const poolMatches = this.dataManager.getMatchesByPool(pool.id);
        const scheduledMatches = poolMatches.filter(m => m.semaine);
        const unscheduledMatches = poolMatches.filter(m => !m.semaine);
        
        // Séparer matchs passés et à venir (utiliser la semaine actuelle comme référence)
        const currentWeek = this._getCurrentWeek(data);
        const playedMatches = scheduledMatches.filter(m => m.semaine < currentWeek);
        const upcomingMatches = scheduledMatches.filter(m => m.semaine >= currentWeek);
        
        let html = `
            <div class="pool-card ${genderClass} ${isExpanded ? 'expanded' : ''}" data-pool-id="${pool.id}">
                <div class="pool-header" data-toggle-pool="${pool.id}">
                    <div class="pool-title">
                        <h3>${pool.nom}</h3>
                    </div>
                    <div class="pool-info">
                        <span class="pool-level">${this._formatLevel(pool.niveau || pool.nom)}</span>
                        <span class="pool-teams">👥 ${pool.nb_equipes} équipes</span>
                        <span class="pool-matches">⚽ ${poolMatches.length} matchs</span>
                    </div>
                    <button class="expand-btn ${isExpanded ? 'expanded' : ''}" aria-label="Développer">
                        ${isExpanded ? '▼' : '▶'}
                    </button>
                </div>
        `;
        
        if (isExpanded) {
            html += this._generateExpandedContent(pool, data);
        }
        
        html += '</div>';
        
        return html;
    }

    /**
     * Génère le contenu détaillé (développé) pour une poule.
     * Ce contenu est partagé par tous les formats d'affichage.
     */
    _generateExpandedContent(pool, data) {
        const poolMatches = this.dataManager.getMatchesByPool(pool.id);
        const scheduledMatches = poolMatches.filter(m => m.semaine);
        const currentWeek = this._getCurrentWeek(data);
        const playedMatches = scheduledMatches.filter(m => m.semaine < currentWeek);
        const upcomingMatches = scheduledMatches.filter(m => m.semaine >= currentWeek);
        const unscheduledMatches = poolMatches.filter(m => !m.semaine);

        let html = '<div class="pool-content">';
            
        // Afficher les équipes si l'option est activée
        if (this.displayOptions.showTeams) {
            html += this._generateTeamsList(pool, data);
        }
        
        // Conteneur flex pour stats et classement
        html += '<div class="pool-details-grid">';

        // Statistiques détaillées
        html += '<div class="pool-content-section">';
        html += '<h4 class="pool-content-section-title">📊 Statistiques</h4>';
        html += this._generatePoolStats(pool, playedMatches, upcomingMatches, unscheduledMatches);
        html += '</div>';
        
        // Classement
        html += '<div class="pool-content-section">';
        html += '<h4 class="pool-content-section-title">🏆 Classement</h4>';
        html += this._generateStandings(pool, data, playedMatches);
        html += '</div>';

        html += '</div>'; // Fin de pool-details-grid
        
        // Matchs avec onglets
        html += '<div class="pool-content-section">';
        html += '<h4 class="pool-content-section-title">⚽ Matchs</h4>';
        html += this._generatePoolMatchesWithTabs(pool.id, playedMatches, upcomingMatches, data);
        html += '</div>';
        
        html += '</div>'; // Fin de pool-content

        return html;
    }
    
    /**
     * Génère la liste des équipes d'une poule
     */
    _generateTeamsList(pool, data) {
        if (!pool.equipes || pool.equipes.length === 0) {
            return '';
        }
        
        // Récupérer les détails des équipes
        const teams = pool.equipes.map(teamId => {
            const team = data.entities.equipes.find(t => t.id === teamId);
            return team || { id: teamId, nom: `Équipe ${teamId}` };
        });
        
        let html = `
            <div class="pool-content-section">
                <h4 class="pool-content-section-title">👥 Équipes (${teams.length})</h4>
                <div class="pool-teams-list">
        `;
        
        teams.forEach(team => {
            html += `
                <div class="team-item">
                    <div class="team-item-icon">🏐</div>
                    <div class="team-item-content">
                        <div class="team-item-name">${team.nom}</div>
            `;
            
            // Afficher les préférences si l'option est activée
            if (this.displayOptions.showPreferences) {
                html += '<div class="team-item-details">';
                
                // Horaires préférés
                if (team.horaires_preferes && team.horaires_preferes.length > 0) {
                    html += `
                        <div class="team-preference">
                            <span class="preference-icon">🕐</span>
                            <span class="preference-label">Horaires :</span>
                            <span class="preference-value">${team.horaires_preferes.join(', ')}</span>
                        </div>
                    `;
                }
                
                // Lieux préférés
                if (team.lieux_preferes && team.lieux_preferes.length > 0) {
                    html += `
                        <div class="team-preference">
                            <span class="preference-icon">📍</span>
                            <span class="preference-label">Lieux :</span>
                            <span class="preference-value">${team.lieux_preferes.join(', ')}</span>
                        </div>
                    `;
                }
                
                // Indisponibilités
                if (team.semaines_indisponibles && team.semaines_indisponibles.length > 0) {
                    html += `
                        <div class="team-preference">
                            <span class="preference-icon">❌</span>
                            <span class="preference-label">Indisponible :</span>
                            <span class="preference-value">Semaines ${team.semaines_indisponibles.join(', ')}</span>
                        </div>
                    `;
                }
                
                html += '</div>';
            }
            
            html += `
                    </div>
                </div>
            `;
        });
        
        html += `
                </div>
            </div>
        `;
        
        return html;
    }
    
    /**
     * Récupère la semaine actuelle (pour distinguer passé/futur)
     */
    _getCurrentWeek(data) {
        // Dans un vrai contexte, on utiliserait la date actuelle
        // Ici on prend la médiane des semaines pour simuler
        const allWeeks = data.matches.scheduled
            .map(m => m.semaine)
            .filter(w => w)
            .sort((a, b) => a - b);
        
        if (allWeeks.length === 0) return 1;
        
        return allWeeks[Math.floor(allWeeks.length / 2)] || 1;
    }
    
    /**
     * Génère les statistiques détaillées d'une poule
     */
    _generatePoolStats(pool, playedMatches, upcomingMatches, unscheduledMatches) {
        const totalMatches = pool.nb_matchs_planifies + pool.nb_matchs_non_planifies;
        const completionRate = totalMatches > 0 
            ? Math.round((pool.nb_matchs_planifies / totalMatches) * 100) 
            : 0;
        
        return `
            <div class="pool-stats">
                <div class="stat-item">
                    <div class="stat-item-value">${playedMatches.length}</div>
                    <div class="stat-item-label">Joués</div>
                </div>
                <div class="stat-item">
                    <div class="stat-item-value">${upcomingMatches.length}</div>
                    <div class="stat-item-label">À venir</div>
                </div>
                <div class="stat-item">
                    <div class="stat-item-value">${unscheduledMatches.length}</div>
                    <div class="stat-item-label">Non planifiés</div>
                </div>
                <div class="stat-item">
                    <div class="stat-item-value">${completionRate}%</div>
                    <div class="stat-item-label">Complétude</div>
                </div>
            </div>
        `;
    }
    
    /**
     * Génère le classement d'une poule avec données améliorées
     */
    _generateStandings(pool, data, playedMatches) {
        // Récupérer les équipes de la poule
        const teams = this._getPoolTeams(pool.id, data);
        
        if (teams.length === 0) {
            return '<div class="no-matches">Aucune équipe dans cette poule</div>';
        }
        
        // Calculer les stats des équipes basées sur les matchs joués
        const standings = this._calculateDetailedStandings(teams, playedMatches);
        
        let html = `
            <div class="pool-standings">
                <table class="standings-table">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Équipe</th>
                            <th title="Matchs Joués">J</th>
                            <th title="Victoires">G</th>
                            <th title="Nuls">N</th>
                            <th title="Défaites">P</th>
                            <th title="Points">Pts</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        standings.forEach((team, index) => {
            const positionClass = index < 3 ? `position-${index + 1}` : '';
            html += `
                <tr class="${positionClass}">
                    <td>${index + 1}</td>
                    <td class="team-name" title="${team.nom_complet || team.nom}">${team.nom}</td>
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
     * Récupère les équipes d'une poule
     */
    _getPoolTeams(poolId, data) {
        if (!data.entities?.equipes) return [];
        
        return data.entities.equipes.filter(e => e.poule === poolId);
    }
    
    /**
     * Calcule le classement détaillé avec victoires/défaites
     * Note: Sans scores réels dans les données, affiche uniquement les matchs joués
     */
    _calculateDetailedStandings(teams, matches) {
        const stats = {};
        
        // Initialiser les stats
        teams.forEach(team => {
            stats[team.id] = {
                id: team.id,
                nom: team.nom,
                nom_complet: team.nom_complet,
                played: 0,
                won: 0,
                drawn: 0,
                lost: 0,
                points: 0
            };
        });
        
        // Compter les matchs joués
        matches.forEach(match => {
            const team1Id = match.equipe1_id || match.equipes?.[0];
            const team2Id = match.equipe2_id || match.equipes?.[1];
            
            if (stats[team1Id]) stats[team1Id].played++;
            if (stats[team2Id]) stats[team2Id].played++;
            
            // Note: Sans scores réels dans les données, on ne peut pas calculer
            // les victoires/défaites/points. Ces colonnes resteront à 0.
            // Pour afficher des résultats réels, il faudrait avoir :
            // - match.score1 et match.score2
            // - ou match.resultat
        });
        
        // Trier par matchs joués puis nom (puisqu'on n'a pas de points)
        return Object.values(stats).sort((a, b) => {
            if (b.played !== a.played) return b.played - a.played;
            return a.nom.localeCompare(b.nom);
        });
    }
    
    /**
     * Génère les matchs avec onglets (joués / à venir)
     */
    _generatePoolMatchesWithTabs(poolId, playedMatches, upcomingMatches, data) {
        // Déterminer l'onglet actif
        const activeTab = this.activeMatchTabs[poolId] || 'upcoming';
        
        let html = `
            <div class="pool-matches">
                <h4>⚽ Matchs de la poule</h4>
                
                <div class="matches-tabs">
                    <button class="match-tab ${activeTab === 'upcoming' ? 'active' : ''}" 
                            data-tab="upcoming" data-pool="${poolId}">
                        À venir
                        <span class="match-tab-count">${upcomingMatches.length}</span>
                    </button>
                    <button class="match-tab ${activeTab === 'played' ? 'active' : ''}" 
                            data-tab="played" data-pool="${poolId}">
                        Joués
                        <span class="match-tab-count">${playedMatches.length}</span>
                    </button>
                    <button class="match-tab ${activeTab === 'all' ? 'active' : ''}" 
                            data-tab="all" data-pool="${poolId}">
                        Tous
                        <span class="match-tab-count">${playedMatches.length + upcomingMatches.length}</span>
                    </button>
                </div>
                
                <div class="matches-content ${activeTab === 'upcoming' ? 'active' : ''}" 
                     data-content="upcoming" data-pool="${poolId}">
                    ${this._generateMatchesList(upcomingMatches, data, 'upcoming')}
                </div>
                
                <div class="matches-content ${activeTab === 'played' ? 'active' : ''}" 
                     data-content="played" data-pool="${poolId}">
                    ${this._generateMatchesList(playedMatches, data, 'played')}
                </div>
                
                <div class="matches-content ${activeTab === 'all' ? 'active' : ''}" 
                     data-content="all" data-pool="${poolId}">
                    ${this._generateMatchesList([...playedMatches, ...upcomingMatches], data, 'all')}
                </div>
            </div>
        `;
        
        return html;
    }
    
    /**
     * Génère une liste de matchs
     */
    _generateMatchesList(matches, data, type) {
        if (matches.length === 0) {
            const emptyMessage = type === 'upcoming' ? 'Aucun match à venir' :
                               type === 'played' ? 'Aucun match joué' :
                               'Aucun match';
            return `<div class="no-matches">${emptyMessage}</div>`;
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
        
        // Trier les semaines
        const sortedWeeks = Array.from(byWeek.keys()).sort((a, b) => {
            if (a === 'Non planifié') return 1;
            if (b === 'Non planifié') return -1;
            return type === 'played' ? b - a : a - b; // Ordre décroissant pour "joués"
        });
        
        let html = '';
        
        sortedWeeks.forEach(week => {
            const weekMatches = byWeek.get(week);
            
            html += `<div class="week-group">`;
            html += `<h5>📅 Semaine ${week}</h5>`;
            html += `<div class="matches-grid">`;
            
            weekMatches.forEach(match => {
                html += this._generateMatchCardNew(match, data, type); // Utilisation du nouveau design
            });
            
            html += `</div></div>`;
        });
        
        return html;
    }

    /**
     * Génère une carte de match avec le nouveau design.
     */
    _generateMatchCardNew(match, data, type) {
        const gymnase = this.dataManager.getGymnaseById(match.gymnase);
        const equipe1Nom = match.equipe1_nom_complet || match.equipe1_nom || 'Équipe 1';
        const equipe2Nom = match.equipe2_nom_complet || match.equipe2_nom || 'Équipe 2';

        const statusClass = type === 'played' ? 'played' : 'upcoming';
        const statusLabel = type === 'played' ? 'Terminé' : 'À venir';
        const statusIcon = type === 'played' ? '✅' : '⏳';

        const totalPenalties = Object.values(match.penalties || {}).reduce((sum, p) => sum + p, 0);
        const penaltyClass = totalPenalties > 10 ? 'high' : totalPenalties > 5 ? 'medium' : 'low';

        return `
            <div class="match-card-new ${statusClass}" data-match-id="${match.match_id}">
                <div class="match-card-new-header">
                    <div class="match-card-new-status">
                        <span class="status-icon">${statusIcon}</span>
                        <span class="status-label">${statusLabel}</span>
                    </div>
                    <div class="match-card-new-week">
                        Semaine ${match.semaine || 'N/A'}
                    </div>
                </div>

                <div class="match-card-new-body">
                    <div class="team-info">
                        <span class="team-name">${equipe1Nom}</span>
                    </div>
                    <div class="match-center">
                        <span class="vs-circle">VS</span>
                    </div>
                    <div class="team-info team-info-right">
                        <span class="team-name">${equipe2Nom}</span>
                    </div>
                </div>

                <div class="match-card-new-footer">
                    <div class="footer-info location">
                        <span class="footer-icon">📍</span>
                        <span>${gymnase?.nom || 'Non défini'}</span>
                    </div>
                    <div class="footer-info time">
                        <span class="footer-icon">🕒</span>
                        <span>${match.jour || ''} ${match.horaire || ''}</span>
                    </div>
                    <div class="footer-info penalty penalty-${penaltyClass}" title="Pénalités: ${totalPenalties.toFixed(1)}">
                        <span class="footer-icon">⚠️</span>
                        <span>${totalPenalties.toFixed(1)}</span>
                    </div>
                </div>
            </div>
        `;
    }
    
    /**
     * Génère une carte de match riche en informations
     */
    _generateMatchCard(match, data, type) {
        const gymnase = this.dataManager.getGymnaseById(match.gymnase);
        
        // Les données d'équipe sont dans le match (format v2.0)
        const equipe1Nom = match.equipe1_nom_complet || match.equipe1_nom || 'Équipe 1';
        const equipe2Nom = match.equipe2_nom_complet || match.equipe2_nom || 'Équipe 2';
        
        const totalPenalties = Object.values(match.penalties || {}).reduce((sum, p) => sum + p, 0);
        const penaltyClass = totalPenalties > 10 ? 'high' : totalPenalties > 5 ? 'medium' : 'low';
        
        const statusClass = type === 'played' ? 'played' : 'upcoming';
        const statusLabel = type === 'played' ? 'Terminé' : 'À venir';
        
        let html = `
            <div class="match-card ${statusClass}" data-match-id="${match.match_id}">
                <div class="match-time">
                    ${match.jour || 'N/A'} - ${match.horaire || 'N/A'}
                </div>
                <div class="match-teams-mini">
                    <span class="team">${equipe1Nom}</span>
                    <span class="vs">vs</span>
                    <span class="team">${equipe2Nom}</span>
                </div>
                <div class="match-venue">
                    📍 ${gymnase?.nom || 'Lieu non défini'}
                </div>
                <div class="match-footer">
                    <span class="match-status ${statusClass}">${statusLabel}</span>
                    <span class="match-penalty-badge penalty-${penaltyClass}" 
                          title="Pénalités totales">
                        ${totalPenalties.toFixed(1)}
                    </span>
                </div>
            </div>
        `;
        
        return html;
    }
    
    /**
     * Attache les event listeners
     */
    _attachEventListeners() {
        // Toggle expand/collapse des poules
        const toggleElements = this.container.querySelectorAll('[data-toggle-pool], .pool-compact, .pool-list-row');
        toggleElements.forEach(element => {
            element.addEventListener('click', (e) => {
                // Éviter de déclencher sur un clic de bouton ou de lien à l'intérieur
                if (e.target.closest('button, a')) return;

                const poolId = e.currentTarget.dataset.poolId || e.currentTarget.dataset.togglePool;
                if (poolId) {
                    this.togglePool(poolId);
                }
            });
        });
        
        // Gestion des onglets de matchs
        const matchTabs = this.container.querySelectorAll('.match-tab');
        matchTabs.forEach(tab => {
            tab.addEventListener('click', (e) => {
                const tabName = e.currentTarget.dataset.tab;
                const poolId = e.currentTarget.dataset.pool;
                this.switchMatchTab(poolId, tabName);
            });
        });
        
        // Double-clic sur match pour éditer
        const matchCards = this.container.querySelectorAll('.match-card, .match-card_new');
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
     * Change l'onglet actif pour les matchs d'une poule
     */
    switchMatchTab(poolId, tabName) {
        this.activeMatchTabs[poolId] = tabName;
        this.render();
    }
    
    /**
     * Édite un match (ouvre le formulaire d'édition)
     */
    _editMatch(matchId) {
        // Logique pour ouvrir le formulaire d'édition d'un match
        console.log('Éditer le match:', matchId);
    }
}

// Export global
window.PoolsView = PoolsView;

