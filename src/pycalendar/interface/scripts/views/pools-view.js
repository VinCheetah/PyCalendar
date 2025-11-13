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
            <div class="empty-state" style="display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 4rem 2rem; text-align: center;">
                <div class="empty-state-icon" style="font-size: 5rem; margin-bottom: 1.5rem; opacity: 0.5;">🎯</div>
                <h3 class="empty-state-title" style="font-size: 1.5rem; font-weight: 700; color: #333; margin: 0 0 0.75rem 0; font-family: 'Inter', 'Roboto', sans-serif;">Aucune poule</h3>
                <p class="empty-state-message" style="font-size: 1rem; color: #666; margin: 0; font-family: 'Roboto', sans-serif;">Les poules apparaîtront ici une fois configurées.</p>
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
                <h3 class="empty-state-title" style="font-size: 1.5rem; font-weight: 700; color: #333; margin: 0 0 0.75rem 0; font-family: 'Inter', 'Roboto', sans-serif;">Aucune poule correspondante</h3>
                <p class="empty-state-message" style="font-size: 1rem; color: #666; margin: 0; font-family: 'Roboto', sans-serif;">Aucune poule ne correspond aux filtres sélectionnés.</p>
            </div>
        `;
    }
    
    /**
     * Filtre les poules selon les filtres actifs
     */
    _filterPools(pools) {
        if (!this.dataManager) return pools;
        const data = this.dataManager.getData();
        
        return pools.filter(pool => {
            // Filtre par genre
            if (this.selectedFilters.gender && pool.genre !== this.selectedFilters.gender) {
                return false;
            }
            
            // Filtre par poule (ID exact)
            if (this.selectedFilters.pool && pool.id !== this.selectedFilters.pool) {
                return false;
            }
            
            // Filtre par institution - vérifier si au moins une équipe de la poule correspond
            if (this.selectedFilters.institution && data?.entities?.equipes) {
                const poolTeams = data.entities.equipes.filter(e => e.poule === pool.id);
                const hasInstitution = poolTeams.some(e => e.institution === this.selectedFilters.institution);
                if (!hasInstitution) {
                    return false;
                }
            }
            
            // Filtre par équipe - vérifier si l'équipe (ou groupe d'équipes) est dans cette poule
            if (this.selectedFilters.equipe && data?.entities?.equipes) {
                const equipeIds = this.selectedFilters.equipe.split(',');
                const poolTeams = data.entities.equipes.filter(e => e.poule === pool.id);
                const hasEquipe = poolTeams.some(e => equipeIds.includes(e.id));
                if (!hasEquipe) {
                    return false;
                }
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
            <div class="pools-summary" style="display: flex; gap: 1rem; margin-bottom: 1.5rem; flex-wrap: wrap; padding: 1rem; background: linear-gradient(135deg, rgba(0, 85, 164, 0.05) 0%, rgba(0, 85, 164, 0.02) 100%); border-radius: 12px;">
                <div class="summary-card" style="flex: 1; min-width: 140px; padding: 1rem; background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1); border: 1px solid rgba(0, 85, 164, 0.1); text-align: center;">
                    <div class="summary-value" style="font-size: 2rem; font-weight: 900; color: #0055A4; font-family: 'Roboto Mono', monospace; margin-bottom: 0.5rem;">${pools.length}</div>
                    <div class="summary-label" style="font-size: 0.75rem; font-weight: 700; color: #666; text-transform: uppercase; letter-spacing: 0.08em; font-family: 'Roboto', sans-serif;">Poules</div>
                </div>
                <div class="summary-card" style="flex: 1; min-width: 140px; padding: 1rem; background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1); border: 1px solid rgba(0, 85, 164, 0.1); text-align: center;">
                    <div class="summary-value" style="font-size: 2rem; font-weight: 900; color: #0055A4; font-family: 'Roboto Mono', monospace; margin-bottom: 0.5rem;">${totalTeams}</div>
                    <div class="summary-label" style="font-size: 0.75rem; font-weight: 700; color: #666; text-transform: uppercase; letter-spacing: 0.08em; font-family: 'Roboto', sans-serif;">Équipes</div>
                </div>
                <div class="summary-card" style="flex: 1; min-width: 140px; padding: 1rem; background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1); border: 1px solid rgba(0, 85, 164, 0.1); text-align: center;">
                    <div class="summary-value" style="font-size: 2rem; font-weight: 900; color: #0055A4; font-family: 'Roboto Mono', monospace; margin-bottom: 0.5rem;">${totalMatches}</div>
                    <div class="summary-label" style="font-size: 0.75rem; font-weight: 700; color: #666; text-transform: uppercase; letter-spacing: 0.08em; font-family: 'Roboto', sans-serif;">Matchs Total</div>
                </div>
                <div class="summary-card" style="flex: 1; min-width: 140px; padding: 1rem; background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1); border: 1px solid rgba(0, 85, 164, 0.1); text-align: center;">
                    <div class="summary-value" style="font-size: 2rem; font-weight: 900; color: #27AE60; font-family: 'Roboto Mono', monospace; margin-bottom: 0.5rem;">${scheduledMatches}</div>
                    <div class="summary-label" style="font-size: 0.75rem; font-weight: 700; color: #666; text-transform: uppercase; letter-spacing: 0.08em; font-family: 'Roboto', sans-serif;">Planifiés</div>
                </div>
                <div class="summary-card" style="flex: 1; min-width: 140px; padding: 1rem; background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1); border: 1px solid rgba(239, 65, 53, 0.1); text-align: center;">
                    <div class="summary-value" style="font-size: 2rem; font-weight: 900; color: #EF4135; font-family: 'Roboto Mono', monospace; margin-bottom: 0.5rem;">${unscheduledMatches}</div>
                    <div class="summary-label" style="font-size: 0.75rem; font-weight: 700; color: #666; text-transform: uppercase; letter-spacing: 0.08em; font-family: 'Roboto', sans-serif;">Non Planifiés</div>
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
        
        // Un match est joué SEULEMENT s'il a un score valide
        const playedMatches = scheduledMatches.filter(m => 
            m.score && m.score.has_score && 
            m.score.equipe1 !== null && m.score.equipe1 !== undefined &&
            m.score.equipe2 !== null && m.score.equipe2 !== undefined
        );
        
        // Les matchs à venir sont ceux planifiés mais sans score
        const upcomingMatches = scheduledMatches.filter(m => 
            !m.score || !m.score.has_score ||
            m.score.equipe1 === null || m.score.equipe1 === undefined ||
            m.score.equipe2 === null || m.score.equipe2 === undefined
        );
        
        let html = `
            <div class="pool-card ${genderClass} ${isExpanded ? 'expanded' : ''}" data-pool-id="${pool.id}" style="background: white; border: 2px solid rgba(0, 85, 164, 0.15); border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08); margin-bottom: 1.5rem; transition: all 0.3s ease;">
                <div class="pool-header" data-toggle-pool="${pool.id}" style="padding: 1.25rem; background: linear-gradient(135deg, #0055A4 0%, rgba(0, 85, 164, 0.9) 100%); color: white; cursor: pointer; position: relative; border-bottom: 3px solid rgba(255, 255, 255, 0.2);">
                    <div class="pool-title" style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.75rem;">
                        <h3 style="margin: 0; font-size: 1.25rem; font-weight: 800; color: white; font-family: 'Inter', 'Roboto', sans-serif; letter-spacing: 0.02em; text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);">${pool.nom}</h3>
                        <button class="expand-btn ${isExpanded ? 'expanded' : ''}" aria-label="Développer" style="background: rgba(255, 255, 255, 0.2); border: 1px solid rgba(255, 255, 255, 0.3); color: white; font-size: 1rem; font-weight: 700; padding: 0.4rem 0.8rem; border-radius: 6px; cursor: pointer; transition: all 0.2s ease; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);">
                            ${isExpanded ? '▼' : '▶'}
                        </button>
                    </div>
                    <div class="pool-info" style="display: flex; gap: 1.5rem; flex-wrap: wrap; align-items: center;">
                        <span class="pool-level" style="font-size: 0.75rem; font-weight: 800; padding: 0.3rem 0.6rem; background: rgba(255, 255, 255, 0.25); border-radius: 6px; text-transform: uppercase; letter-spacing: 0.08em; font-family: 'Roboto', sans-serif; border: 1px solid rgba(255, 255, 255, 0.2); box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);">${this._formatLevel(pool.niveau || pool.nom)}</span>
                        <span class="pool-teams" style="font-size: 0.85rem; font-weight: 600; color: rgba(255, 255, 255, 0.95); display: inline-flex; align-items: center; gap: 0.4rem;">👥 ${pool.nb_equipes} équipes</span>
                        <span class="pool-matches" style="font-size: 0.85rem; font-weight: 600; color: rgba(255, 255, 255, 0.95); display: inline-flex; align-items: center; gap: 0.4rem;">⚽ ${poolMatches.length} matchs</span>
                    </div>
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
        
        // Un match est joué SEULEMENT s'il a un score valide
        const playedMatches = scheduledMatches.filter(m => 
            m.score && m.score.has_score && 
            m.score.equipe1 !== null && m.score.equipe1 !== undefined &&
            m.score.equipe2 !== null && m.score.equipe2 !== undefined
        );
        
        // Les matchs à venir sont ceux planifiés mais sans score
        const upcomingMatches = scheduledMatches.filter(m => 
            !m.score || !m.score.has_score ||
            m.score.equipe1 === null || m.score.equipe1 === undefined ||
            m.score.equipe2 === null || m.score.equipe2 === undefined
        );
        
        const unscheduledMatches = poolMatches.filter(m => !m.semaine);

        let html = '<div class="pool-content" style="padding: 1.5rem; background: rgba(0, 85, 164, 0.02);">';
            
        // Afficher les équipes si l'option est activée
        if (this.displayOptions.showTeams) {
            html += this._generateTeamsList(pool, data);
        }
        
        // Conteneur flex pour stats et classement
        html += '<div class="pool-details-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; margin-bottom: 1.5rem;">';

        // Statistiques détaillées
        html += '<div class="pool-content-section" style="background: white; border-radius: 10px; padding: 1.25rem; box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06); border: 1px solid rgba(0, 85, 164, 0.1);">';
        html += '<h4 class="pool-content-section-title" style="margin: 0 0 1rem 0; font-size: 1rem; font-weight: 800; color: #0055A4; display: flex; align-items: center; gap: 0.5rem; font-family: \'Inter\', \'Roboto\', sans-serif; border-bottom: 2px solid rgba(0, 85, 164, 0.1); padding-bottom: 0.75rem;">📊 Statistiques</h4>';
        html += this._generatePoolStats(pool, playedMatches, upcomingMatches, unscheduledMatches);
        html += '</div>';
        
        // Classement
        html += '<div class="pool-content-section" style="background: white; border-radius: 10px; padding: 1.25rem; box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06); border: 1px solid rgba(0, 85, 164, 0.1);">';
        html += '<h4 class="pool-content-section-title" style="margin: 0 0 1rem 0; font-size: 1rem; font-weight: 800; color: #0055A4; display: flex; align-items: center; gap: 0.5rem; font-family: \'Inter\', \'Roboto\', sans-serif; border-bottom: 2px solid rgba(0, 85, 164, 0.1); padding-bottom: 0.75rem;">🏆 Classement</h4>';
        html += this._generateStandings(pool, data, playedMatches);
        html += '</div>';

        html += '</div>'; // Fin de pool-details-grid
        
        // Matchs avec onglets
        html += '<div class="pool-content-section" style="background: white; border-radius: 10px; padding: 1.25rem; box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06); border: 1px solid rgba(0, 85, 164, 0.1);">';
        html += '<h4 class="pool-content-section-title" style="margin: 0 0 1rem 0; font-size: 1rem; font-weight: 800; color: #0055A4; display: flex; align-items: center; gap: 0.5rem; font-family: \'Inter\', \'Roboto\', sans-serif; border-bottom: 2px solid rgba(0, 85, 164, 0.1); padding-bottom: 0.75rem;">⚽ Matchs</h4>';
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
        const scheduledMatches = playedMatches.length + upcomingMatches.length;
        
        // Pourcentage de complétude (planification)
        const completionRate = totalMatches > 0 
            ? Math.round((scheduledMatches / totalMatches) * 100) 
            : 0;
        
        // Pourcentage de matchs joués (parmi les planifiés)
        const playedRate = scheduledMatches > 0 
            ? Math.round((playedMatches.length / scheduledMatches) * 100) 
            : 0;
        
        // Compter les matchs entente
        const ententeMatches = [...playedMatches, ...upcomingMatches].filter(m => m.is_entente);
        
        return `
            <div class="pool-stats" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(100px, 1fr)); gap: 1rem;">
                <div class="stat-item" style="text-align: center; padding: 0.75rem; background: rgba(39, 174, 96, 0.08); border-radius: 8px; border: 1px solid rgba(39, 174, 96, 0.2);">
                    <div class="stat-item-value" style="font-size: 1.5rem; font-weight: 900; color: #27AE60; font-family: 'Roboto Mono', monospace; margin-bottom: 0.25rem;">${playedMatches.length}</div>
                    <div class="stat-item-label" style="font-size: 0.7rem; font-weight: 700; color: #666; text-transform: uppercase; letter-spacing: 0.05em; font-family: 'Roboto', sans-serif;">Joués</div>
                    <div class="stat-item-detail" style="font-size: 0.65rem; color: #999; margin-top: 0.25rem;">${playedRate}% du total</div>
                </div>
                <div class="stat-item" style="text-align: center; padding: 0.75rem; background: rgba(0, 123, 255, 0.08); border-radius: 8px; border: 1px solid rgba(0, 123, 255, 0.2);">
                    <div class="stat-item-value" style="font-size: 1.5rem; font-weight: 900; color: #007BFF; font-family: 'Roboto Mono', monospace; margin-bottom: 0.25rem;">${upcomingMatches.length}</div>
                    <div class="stat-item-label" style="font-size: 0.7rem; font-weight: 700; color: #666; text-transform: uppercase; letter-spacing: 0.05em; font-family: 'Roboto', sans-serif;">À venir</div>
                </div>
                <div class="stat-item" style="text-align: center; padding: 0.75rem; background: rgba(239, 65, 53, 0.08); border-radius: 8px; border: 1px solid rgba(239, 65, 53, 0.2);">
                    <div class="stat-item-value" style="font-size: 1.5rem; font-weight: 900; color: #EF4135; font-family: 'Roboto Mono', monospace; margin-bottom: 0.25rem;">${unscheduledMatches.length}</div>
                    <div class="stat-item-label" style="font-size: 0.7rem; font-weight: 700; color: #666; text-transform: uppercase; letter-spacing: 0.05em; font-family: 'Roboto', sans-serif;">Non planifiés</div>
                </div>
                ${ententeMatches.length > 0 ? `
                <div class="stat-item" style="text-align: center; padding: 0.75rem; background: rgba(255, 193, 7, 0.08); border-radius: 8px; border: 1px solid rgba(255, 193, 7, 0.2);">
                    <div class="stat-item-value" style="font-size: 1.5rem; font-weight: 900; color: #FFC107; font-family: 'Roboto Mono', monospace; margin-bottom: 0.25rem;">${ententeMatches.length}</div>
                    <div class="stat-item-label" style="font-size: 0.7rem; font-weight: 700; color: #666; text-transform: uppercase; letter-spacing: 0.05em; font-family: 'Roboto', sans-serif;">Entente</div>
                </div>
                ` : ''}
                <div class="stat-item" style="text-align: center; padding: 0.75rem; background: rgba(0, 85, 164, 0.08); border-radius: 8px; border: 1px solid rgba(0, 85, 164, 0.2);">
                    <div class="stat-item-value" style="font-size: 1.5rem; font-weight: 900; color: #0055A4; font-family: 'Roboto Mono', monospace; margin-bottom: 0.25rem;">${completionRate}%</div>
                    <div class="stat-item-label" style="font-size: 0.7rem; font-weight: 700; color: #666; text-transform: uppercase; letter-spacing: 0.05em; font-family: 'Roboto', sans-serif;">Planifiés</div>
                    <div class="stat-item-detail" style="font-size: 0.65rem; color: #999; margin-top: 0.25rem;">${scheduledMatches}/${totalMatches}</div>
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
            return '<div class="no-matches" style="text-align: center; padding: 2rem; color: #999; font-size: 0.9rem; font-family: \'Roboto\', sans-serif;">Aucune équipe dans cette poule</div>';
        }
        
        // Calculer les stats des équipes basées sur les matchs joués
        const standings = this._calculateDetailedStandings(teams, playedMatches);
        
        let html = `
            <div class="pool-standings" style="overflow-x: auto;">
                <table class="standings-table" style="width: 100%; border-collapse: collapse; font-size: 0.85rem; font-family: 'Roboto', sans-serif;">
                    <thead>
                        <tr style="background: rgba(0, 85, 164, 0.08); border-bottom: 2px solid rgba(0, 85, 164, 0.2);">
                            <th style="padding: 0.6rem 0.5rem; text-align: center; font-size: 0.7rem; font-weight: 800; color: #666; text-transform: uppercase; letter-spacing: 0.05em;">#</th>
                            <th style="padding: 0.6rem 0.75rem; text-align: left; font-size: 0.7rem; font-weight: 800; color: #666; text-transform: uppercase; letter-spacing: 0.05em;">Équipe</th>
                            <th style="padding: 0.6rem 0.5rem; text-align: center; font-size: 0.7rem; font-weight: 800; color: #666; text-transform: uppercase; letter-spacing: 0.05em;" title="Matchs Joués">J</th>
                            <th style="padding: 0.6rem 0.5rem; text-align: center; font-size: 0.7rem; font-weight: 800; color: #666; text-transform: uppercase; letter-spacing: 0.05em;" title="Victoires">G</th>
                            <th style="padding: 0.6rem 0.5rem; text-align: center; font-size: 0.7rem; font-weight: 800; color: #666; text-transform: uppercase; letter-spacing: 0.05em;" title="Nuls">N</th>
                            <th style="padding: 0.6rem 0.5rem; text-align: center; font-size: 0.7rem; font-weight: 800; color: #666; text-transform: uppercase; letter-spacing: 0.05em;" title="Défaites">P</th>
                            <th style="padding: 0.6rem 0.5rem; text-align: center; font-size: 0.7rem; font-weight: 800; color: #0055A4; text-transform: uppercase; letter-spacing: 0.05em;" title="Points">Pts</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        standings.forEach((team, index) => {
            const positionClass = index < 3 ? `position-${index + 1}` : '';
            let rowStyle = 'border-bottom: 1px solid rgba(0, 85, 164, 0.1);';
            if (index === 0) rowStyle += ' background: rgba(255, 215, 0, 0.1);'; // Or pour 1er
            else if (index === 1) rowStyle += ' background: rgba(192, 192, 192, 0.1);'; // Argent pour 2e
            else if (index === 2) rowStyle += ' background: rgba(205, 127, 50, 0.1);'; // Bronze pour 3e
            
            html += `
                <tr class="${positionClass}" style="${rowStyle}">
                    <td style="padding: 0.6rem 0.5rem; text-align: center; font-weight: 700; color: ${index < 3 ? '#0055A4' : '#666'}; font-family: 'Roboto Mono', monospace;">${index + 1}</td>
                    <td class="team-name" title="${team.nom_complet || team.nom}" style="padding: 0.6rem 0.75rem; font-weight: 600; color: #333;">${team.nom}</td>
                    <td style="padding: 0.6rem 0.5rem; text-align: center; font-weight: 600; color: #666; font-family: 'Roboto Mono', monospace;">${team.played}</td>
                    <td style="padding: 0.6rem 0.5rem; text-align: center; font-weight: 600; color: #27AE60; font-family: 'Roboto Mono', monospace;">${team.won}</td>
                    <td style="padding: 0.6rem 0.5rem; text-align: center; font-weight: 600; color: #FF9500; font-family: 'Roboto Mono', monospace;">${team.drawn}</td>
                    <td style="padding: 0.6rem 0.5rem; text-align: center; font-weight: 600; color: #EF4135; font-family: 'Roboto Mono', monospace;">${team.lost}</td>
                    <td class="points" style="padding: 0.6rem 0.5rem; text-align: center; font-weight: 900; font-size: 1rem; color: #0055A4; font-family: 'Roboto Mono', monospace;">${team.points}</td>
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
     * Calcule le classement détaillé avec victoires/défaites basé sur les scores réels
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
                points: 0,
                goalsFor: 0,
                goalsAgainst: 0
            };
        });
        
        // Analyser les matchs avec scores
        matches.forEach(match => {
            // Un match est joué seulement s'il a un score valide
            if (!match.score || !match.score.has_score) return;
            
            const team1Id = match.equipe1_id;
            const team2Id = match.equipe2_id;
            const score1 = match.score.equipe1;
            const score2 = match.score.equipe2;
            
            // Vérifier que les scores sont valides
            if (score1 === null || score1 === undefined || score2 === null || score2 === undefined) return;
            if (!stats[team1Id] || !stats[team2Id]) return;
            
            // Incrémenter les matchs joués
            stats[team1Id].played++;
            stats[team2Id].played++;
            
            // Enregistrer les buts
            stats[team1Id].goalsFor += score1;
            stats[team1Id].goalsAgainst += score2;
            stats[team2Id].goalsFor += score2;
            stats[team2Id].goalsAgainst += score1;
            
            // Déterminer le résultat et attribuer les points
            if (score1 > score2) {
                // Victoire équipe 1
                stats[team1Id].won++;
                stats[team1Id].points += 3;
                stats[team2Id].lost++;
            } else if (score2 > score1) {
                // Victoire équipe 2
                stats[team2Id].won++;
                stats[team2Id].points += 3;
                stats[team1Id].lost++;
            } else {
                // Match nul
                stats[team1Id].drawn++;
                stats[team1Id].points += 1;
                stats[team2Id].drawn++;
                stats[team2Id].points += 1;
            }
        });
        
        // Trier par points, puis goal average, puis buts marqués, puis nom
        return Object.values(stats).sort((a, b) => {
            // D'abord par points
            if (b.points !== a.points) return b.points - a.points;
            
            // Puis par goal average (différence de buts)
            const diffA = a.goalsFor - a.goalsAgainst;
            const diffB = b.goalsFor - b.goalsAgainst;
            if (diffB !== diffA) return diffB - diffA;
            
            // Puis par buts marqués
            if (b.goalsFor !== a.goalsFor) return b.goalsFor - a.goalsFor;
            
            // Enfin par nom
            return a.nom.localeCompare(b.nom);
        });
    }
    
    /**
     * Génère les matchs avec onglets (joués / à venir / non planifiés)
     */
    _generatePoolMatchesWithTabs(poolId, playedMatches, upcomingMatches, data) {
        // Récupérer les matchs non planifiés
        const allMatches = this.dataManager.getMatchesByPool(poolId);
        const unscheduledMatches = allMatches.filter(m => !m.semaine);
        
        // Déterminer l'onglet actif
        const activeTab = this.activeMatchTabs[poolId] || (unscheduledMatches.length > 0 ? 'unscheduled' : 'upcoming');
        
        let html = `
            <div class="pool-matches">
                
                <div class="matches-tabs" style="display: flex; gap: 0.5rem; margin-bottom: 1rem; border-bottom: 2px solid rgba(0, 85, 164, 0.1); padding-bottom: 0.5rem;">
                    <button class="match-tab ${activeTab === 'upcoming' ? 'active' : ''}" 
                            data-tab="upcoming" data-pool="${poolId}"
                            style="flex: 1; padding: 0.6rem 1rem; background: ${activeTab === 'upcoming' ? 'linear-gradient(135deg, #0055A4 0%, rgba(0, 85, 164, 0.9) 100%)' : 'rgba(0, 85, 164, 0.05)'}; color: ${activeTab === 'upcoming' ? 'white' : '#0055A4'}; border: 1px solid ${activeTab === 'upcoming' ? '#0055A4' : 'rgba(0, 85, 164, 0.2)'}; border-radius: 8px; font-weight: 700; font-size: 0.85rem; cursor: pointer; transition: all 0.2s ease; font-family: 'Roboto', sans-serif; display: flex; align-items: center; justify-content: center; gap: 0.5rem; box-shadow: ${activeTab === 'upcoming' ? '0 2px 6px rgba(0, 85, 164, 0.3)' : 'none'};">
                        À venir
                        <span class="match-tab-count" style="display: inline-flex; align-items: center; justify-content: center; min-width: 24px; height: 24px; background: ${activeTab === 'upcoming' ? 'rgba(255, 255, 255, 0.25)' : 'rgba(0, 85, 164, 0.15)'}; border-radius: 50%; font-size: 0.75rem; font-weight: 900; font-family: 'Roboto Mono', monospace; padding: 0 0.3rem;">${upcomingMatches.length}</span>
                    </button>
                    <button class="match-tab ${activeTab === 'played' ? 'active' : ''}" 
                            data-tab="played" data-pool="${poolId}"
                            style="flex: 1; padding: 0.6rem 1rem; background: ${activeTab === 'played' ? 'linear-gradient(135deg, #0055A4 0%, rgba(0, 85, 164, 0.9) 100%)' : 'rgba(0, 85, 164, 0.05)'}; color: ${activeTab === 'played' ? 'white' : '#0055A4'}; border: 1px solid ${activeTab === 'played' ? '#0055A4' : 'rgba(0, 85, 164, 0.2)'}; border-radius: 8px; font-weight: 700; font-size: 0.85rem; cursor: pointer; transition: all 0.2s ease; font-family: 'Roboto', sans-serif; display: flex; align-items: center; justify-content: center; gap: 0.5rem; box-shadow: ${activeTab === 'played' ? '0 2px 6px rgba(0, 85, 164, 0.3)' : 'none'};">
                        Joués
                        <span class="match-tab-count" style="display: inline-flex; align-items: center; justify-content: center; min-width: 24px; height: 24px; background: ${activeTab === 'played' ? 'rgba(255, 255, 255, 0.25)' : 'rgba(0, 85, 164, 0.15)'}; border-radius: 50%; font-size: 0.75rem; font-weight: 900; font-family: 'Roboto Mono', monospace; padding: 0 0.3rem;">${playedMatches.length}</span>
                    </button>
                    ${unscheduledMatches.length > 0 ? `
                    <button class="match-tab ${activeTab === 'unscheduled' ? 'active' : ''}" 
                            data-tab="unscheduled" data-pool="${poolId}"
                            style="flex: 1; padding: 0.6rem 1rem; background: ${activeTab === 'unscheduled' ? 'linear-gradient(135deg, #EF4135 0%, rgba(239, 65, 53, 0.9) 100%)' : 'rgba(239, 65, 53, 0.05)'}; color: ${activeTab === 'unscheduled' ? 'white' : '#EF4135'}; border: 1px solid ${activeTab === 'unscheduled' ? '#EF4135' : 'rgba(239, 65, 53, 0.2)'}; border-radius: 8px; font-weight: 700; font-size: 0.85rem; cursor: pointer; transition: all 0.2s ease; font-family: 'Roboto', sans-serif; display: flex; align-items: center; justify-content: center; gap: 0.5rem; box-shadow: ${activeTab === 'unscheduled' ? '0 2px 6px rgba(239, 65, 53, 0.3)' : 'none'};">
                        Non planifiés
                        <span class="match-tab-count" style="display: inline-flex; align-items: center; justify-content: center; min-width: 24px; height: 24px; background: ${activeTab === 'unscheduled' ? 'rgba(255, 255, 255, 0.25)' : 'rgba(239, 65, 53, 0.15)'}; border-radius: 50%; font-size: 0.75rem; font-weight: 900; font-family: 'Roboto Mono', monospace; padding: 0 0.3rem;">${unscheduledMatches.length}</span>
                    </button>
                    ` : ''}
                    <button class="match-tab ${activeTab === 'all' ? 'active' : ''}" 
                            data-tab="all" data-pool="${poolId}"
                            style="flex: 1; padding: 0.6rem 1rem; background: ${activeTab === 'all' ? 'linear-gradient(135deg, #0055A4 0%, rgba(0, 85, 164, 0.9) 100%)' : 'rgba(0, 85, 164, 0.05)'}; color: ${activeTab === 'all' ? 'white' : '#0055A4'}; border: 1px solid ${activeTab === 'all' ? '#0055A4' : 'rgba(0, 85, 164, 0.2)'}; border-radius: 8px; font-weight: 700; font-size: 0.85rem; cursor: pointer; transition: all 0.2s ease; font-family: 'Roboto', sans-serif; display: flex; align-items: center; justify-content: center; gap: 0.5rem; box-shadow: ${activeTab === 'all' ? '0 2px 6px rgba(0, 85, 164, 0.3)' : 'none'};">
                        Tous
                        <span class="match-tab-count" style="display: inline-flex; align-items: center; justify-content: center; min-width: 24px; height: 24px; background: ${activeTab === 'all' ? 'rgba(255, 255, 255, 0.25)' : 'rgba(0, 85, 164, 0.15)'}; border-radius: 50%; font-size: 0.75rem; font-weight: 900; font-family: 'Roboto Mono', monospace; padding: 0 0.3rem;">${allMatches.length}</span>
                    </button>
                </div>
                
                <div class="matches-content ${activeTab === 'upcoming' ? 'active' : ''}" 
                     data-content="upcoming" data-pool="${poolId}"
                     style="display: ${activeTab === 'upcoming' ? 'block' : 'none'};">
                    ${this._generateMatchesList(upcomingMatches, data, 'upcoming')}
                </div>
                
                <div class="matches-content ${activeTab === 'played' ? 'active' : ''}" 
                     data-content="played" data-pool="${poolId}"
                     style="display: ${activeTab === 'played' ? 'block' : 'none'};">
                    ${this._generateMatchesList(playedMatches, data, 'played')}
                </div>
                
                ${unscheduledMatches.length > 0 ? `
                <div class="matches-content ${activeTab === 'unscheduled' ? 'active' : ''}" 
                     data-content="unscheduled" data-pool="${poolId}"
                     style="display: ${activeTab === 'unscheduled' ? 'block' : 'none'};">
                    ${this._generateMatchesList(unscheduledMatches, data, 'unscheduled')}
                </div>
                ` : ''}
                
                <div class="matches-content ${activeTab === 'all' ? 'active' : ''}" 
                     data-content="all" data-pool="${poolId}"
                     style="display: ${activeTab === 'all' ? 'block' : 'none'};">
                    ${this._generateMatchesList(allMatches, data, 'all')}
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
            return `<div class="no-matches" style="text-align: center; padding: 3rem 2rem; color: #999; font-size: 0.95rem; font-weight: 600; background: rgba(0, 85, 164, 0.03); border-radius: 8px; border: 1px dashed rgba(0, 85, 164, 0.2); font-family: 'Roboto', sans-serif;">${emptyMessage}</div>`;
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
            
            html += `<div class="week-group" style="margin-bottom: 1.5rem;">`;
            html += `<h5 style="font-size: 0.9rem; font-weight: 800; color: #0055A4; margin: 0 0 0.75rem 0; padding: 0.5rem 0.75rem; background: rgba(0, 85, 164, 0.08); border-left: 4px solid #0055A4; border-radius: 6px; font-family: 'Roboto', sans-serif; display: flex; align-items: center; gap: 0.5rem;">📅 Semaine ${week}</h5>`;
            html += `<div class="matches-grid" style="display: grid; gap: 0.75rem;">`;
            
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
        const equipe1Num = match.equipe1_num ? `#${match.equipe1_num}` : '';
        const equipe2Num = match.equipe2_num ? `#${match.equipe2_num}` : '';

        // Déterminer si le match est réellement joué (a un score)
        const hasScore = match.score && match.score.has_score && 
                        match.score.equipe1 !== null && match.score.equipe1 !== undefined &&
                        match.score.equipe2 !== null && match.score.equipe2 !== undefined;
        
        // Déterminer si le match est planifié
        const isScheduled = match.semaine && match.horaire && match.gymnase;
        
        const statusClass = hasScore ? 'played' : (isScheduled ? 'upcoming' : 'unscheduled');
        const statusLabel = hasScore ? 'Terminé' : (isScheduled ? 'À venir' : 'Non planifié');
        const statusIcon = hasScore ? '✅' : (isScheduled ? '⏳' : '❌');
        const statusBg = hasScore ? 'rgba(39, 174, 96, 0.1)' : (isScheduled ? 'rgba(0, 123, 255, 0.1)' : 'rgba(239, 65, 53, 0.1)');
        const statusBorder = hasScore ? 'rgba(39, 174, 96, 0.25)' : (isScheduled ? 'rgba(0, 123, 255, 0.25)' : 'rgba(239, 65, 53, 0.25)');
        const statusColor = hasScore ? '#27AE60' : (isScheduled ? '#007BFF' : '#EF4135');
        
        // Déterminer le gagnant si le match a un score
        let team1Winner = false;
        let team2Winner = false;
        if (hasScore) {
            if (match.score.equipe1 > match.score.equipe2) {
                team1Winner = true;
            } else if (match.score.equipe2 > match.score.equipe1) {
                team2Winner = true;
            }
        }
        
        // Badge entente
        const isEntente = match.is_entente === true;
        const ententeBadge = isEntente ? `
            <div class="match-badge-entente" style="display: inline-flex; align-items: center; gap: 0.3rem; padding: 0.2rem 0.5rem; background: rgba(255, 193, 7, 0.15); border: 1px solid rgba(255, 193, 7, 0.4); border-radius: 6px; font-size: 0.65rem; font-weight: 800; color: #F57C00; font-family: 'Roboto', sans-serif; text-transform: uppercase; letter-spacing: 0.05em;">
                <span style="font-size: 0.8rem;">🤝</span>
                Entente
            </div>
        ` : '';
        
        // Déterminer la couleur de fond selon le genre
        const genre = match.equipe1_genre || match.equipe2_genre;
        let bgGradient = 'linear-gradient(135deg, rgba(0, 85, 164, 0.08) 0%, rgba(0, 85, 164, 0.03) 100%)';
        if (genre === 'M') {
            bgGradient = 'linear-gradient(135deg, rgba(0, 123, 255, 0.08) 0%, rgba(0, 123, 255, 0.03) 100%)';
        } else if (genre === 'F') {
            bgGradient = 'linear-gradient(135deg, rgba(255, 20, 147, 0.08) 0%, rgba(255, 20, 147, 0.03) 100%)';
        }

        const totalPenalties = Object.values(match.penalties || {}).reduce((sum, p) => sum + p, 0);
        const penaltyColor = totalPenalties > 10 ? '#EF4135' : totalPenalties > 5 ? '#FF9500' : '#27AE60';

        return `
            <div class="match-card-new ${statusClass}" data-match-id="${match.match_id}" style="background: white; border: 1px solid rgba(0, 85, 164, 0.15); border-radius: 10px; padding: 1rem; margin-bottom: 0.75rem; box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06); transition: all 0.2s ease; ${!isScheduled ? 'border-left: 4px solid #EF4135;' : ''}">
                <div class="match-card-new-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem; padding-bottom: 0.5rem; border-bottom: 1px solid rgba(0, 85, 164, 0.1);">
                    <div style="display: flex; gap: 0.5rem; align-items: center;">
                        <div class="match-card-new-status" style="display: inline-flex; align-items: center; gap: 0.4rem; padding: 0.25rem 0.6rem; background: ${statusBg}; border-radius: 6px; border: 1px solid ${statusBorder};">
                            <span class="status-icon" style="font-size: 0.9rem;">${statusIcon}</span>
                            <span class="status-label" style="font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: ${statusColor}; font-family: 'Roboto', sans-serif;">${statusLabel}</span>
                        </div>
                        ${ententeBadge}
                    </div>
                    <div class="match-card-new-week" style="font-size: 0.75rem; font-weight: 800; color: #666; font-family: 'Roboto Mono', monospace; padding: 0.25rem 0.6rem; background: rgba(0, 85, 164, 0.08); border-radius: 6px; border: 1px solid rgba(0, 85, 164, 0.15);">
                        ${isScheduled ? `Semaine ${match.semaine}` : 'À planifier'}
                    </div>
                </div>

                <div class="match-card-new-body" style="display: flex; align-items: center; gap: 1rem; margin-bottom: 0.75rem; background: ${bgGradient}; padding: 0.75rem; border-radius: 8px;">
                    <div class="team-info" style="flex: 1; display: flex; flex-direction: column; align-items: flex-start; ${team1Winner ? 'background: rgba(255, 215, 0, 0.15); padding: 0.5rem; border-radius: 6px; border: 2px solid rgba(255, 215, 0, 0.4);' : ''}">
                        <div style="display: flex; align-items: center; gap: 0.4rem; width: 100%; justify-content: space-between;">
                            <div style="display: flex; align-items: center; gap: 0.4rem;">
                                ${equipe1Num ? `<span style="font-size: 0.65rem; font-weight: 800; background: rgba(0, 85, 164, 0.15); padding: 0.15rem 0.4rem; border-radius: 4px; font-family: 'Roboto Mono', monospace; color: #0055A4;">${equipe1Num}</span>` : ''}
                                <span class="team-name" style="font-size: 0.85rem; font-weight: ${team1Winner ? '900' : '700'}; color: ${team1Winner ? '#0055A4' : '#333'}; font-family: 'Inter', 'Roboto', sans-serif; text-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);">${equipe1Nom}</span>
                            </div>
                            ${hasScore ? `<span style="font-size: 1.1rem; font-weight: 900; color: ${team1Winner ? '#FFD700' : '#333'}; font-family: 'Roboto Mono', monospace; min-width: 30px; text-align: center;">${match.score.equipe1}</span>` : ''}
                            ${team1Winner ? '<span style="font-size: 1.2rem; margin-left: 0.3rem;">🏆</span>' : ''}
                        </div>
                    </div>
                    <div class="match-center" style="display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                        <span class="vs-circle" style="display: inline-flex; align-items: center; justify-content: center; width: 36px; height: 36px; background: white; border: 2px solid rgba(0, 85, 164, 0.2); border-radius: 50%; font-size: 0.65rem; font-weight: 900; color: #0055A4; box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1); font-family: 'Roboto', sans-serif;">VS</span>
                    </div>
                    <div class="team-info team-info-right" style="flex: 1; display: flex; flex-direction: column; align-items: flex-end; ${team2Winner ? 'background: rgba(255, 215, 0, 0.15); padding: 0.5rem; border-radius: 6px; border: 2px solid rgba(255, 215, 0, 0.4);' : ''}">
                        <div style="display: flex; align-items: center; gap: 0.4rem; width: 100%; justify-content: space-between; flex-direction: row-reverse;">
                            <div style="display: flex; align-items: center; gap: 0.4rem;">
                                <span class="team-name" style="font-size: 0.85rem; font-weight: ${team2Winner ? '900' : '700'}; color: ${team2Winner ? '#0055A4' : '#333'}; font-family: 'Inter', 'Roboto', sans-serif; text-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);">${equipe2Nom}</span>
                                ${equipe2Num ? `<span style="font-size: 0.65rem; font-weight: 800; background: rgba(0, 85, 164, 0.15); padding: 0.15rem 0.4rem; border-radius: 4px; font-family: 'Roboto Mono', monospace; color: #0055A4;">${equipe2Num}</span>` : ''}
                            </div>
                            ${hasScore ? `<span style="font-size: 1.1rem; font-weight: 900; color: ${team2Winner ? '#FFD700' : '#333'}; font-family: 'Roboto Mono', monospace; min-width: 30px; text-align: center;">${match.score.equipe2}</span>` : ''}
                            ${team2Winner ? '<span style="font-size: 1.2rem; margin-right: 0.3rem;">🏆</span>' : ''}
                        </div>
                    </div>
                </div>

                <div class="match-card-new-footer" style="display: flex; gap: 1rem; flex-wrap: wrap; font-size: 0.75rem;">
                    ${isScheduled ? `
                    <div class="footer-info location" style="display: inline-flex; align-items: center; gap: 0.3rem; padding: 0.25rem 0.5rem; background: rgba(0, 85, 164, 0.06); border-radius: 6px; border: 1px solid rgba(0, 85, 164, 0.1);">
                        <span class="footer-icon" style="font-size: 0.85rem;">📍</span>
                        <span style="font-weight: 600; color: #555; font-family: 'Roboto', sans-serif;">${gymnase?.nom || 'Non défini'}</span>
                    </div>
                    <div class="footer-info time" style="display: inline-flex; align-items: center; gap: 0.3rem; padding: 0.25rem 0.5rem; background: rgba(0, 85, 164, 0.06); border-radius: 6px; border: 1px solid rgba(0, 85, 164, 0.1);">
                        <span class="footer-icon" style="font-size: 0.85rem;">🕒</span>
                        <span style="font-weight: 800; color: #555; font-family: 'Roboto Mono', monospace;">${match.jour || ''} ${match.horaire || ''}</span>
                    </div>
                    ` : `
                    <div class="footer-info unscheduled-note" style="display: inline-flex; align-items: center; gap: 0.3rem; padding: 0.25rem 0.5rem; background: rgba(239, 65, 53, 0.1); border-radius: 6px; border: 1px solid rgba(239, 65, 53, 0.25);">
                        <span class="footer-icon" style="font-size: 0.85rem;">⚠️</span>
                        <span style="font-weight: 700; color: #EF4135; font-family: 'Roboto', sans-serif; font-size: 0.7rem; text-transform: uppercase;">Ce match nécessite une planification</span>
                    </div>
                    `}
                    ${totalPenalties > 0 ? `<div class="footer-info penalty" style="display: inline-flex; align-items: center; gap: 0.3rem; padding: 0.25rem 0.5rem; background: rgba(${totalPenalties > 10 ? '239, 65, 53' : totalPenalties > 5 ? '255, 149, 0' : '39, 174, 96'}, 0.1); border-radius: 6px; border: 1px solid rgba(${totalPenalties > 10 ? '239, 65, 53' : totalPenalties > 5 ? '255, 149, 0' : '39, 174, 96'}, 0.25);" title="Pénalités: ${totalPenalties.toFixed(1)}">
                        <span class="footer-icon" style="font-size: 0.85rem;">⚠️</span>
                        <span style="font-weight: 900; color: ${penaltyColor}; font-family: 'Roboto Mono', monospace;">${totalPenalties.toFixed(1)}</span>
                    </div>` : ''}
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

