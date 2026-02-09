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
        
        // Options d'affichage enrichies
        this.displayOptions = {
            format: 'cards', // 'cards', 'compact', 'list'
            showTeams: true,
            showLevelSeparators: true,
            showPreferences: false,
            // Nouvelles options
            showStats: true,
            showStandings: true,
            showMatches: true,
            showGlobalSummary: true,
            autoExpandPools: false,
            compactCards: false
        };
        
        // Subscribe to data changes
        this.dataManager.subscribe('matches', () => this.render());
    }
    
    /**
     * Vérifie si un match a un score valide (match joué).
     * Centralise la logique de détection des matchs terminés.
     * 
     * @param {Object} match - Le match à vérifier
     * @returns {boolean} true si le match a un score valide
     */
    _hasValidScore(match) {
        return match.score && 
               match.score.has_score && 
               match.score.equipe1 !== null && 
               match.score.equipe1 !== undefined &&
               match.score.equipe2 !== null && 
               match.score.equipe2 !== undefined;
    }
    
    /**
     * Échappe les caractères HTML pour prévenir les injections XSS.
     * Convertit les caractères spéciaux en entités HTML sécurisées.
     * 
     * @param {string} text - Le texte à échapper
     * @returns {string} Texte échappé et sécurisé
     */
    _escapeHtml(text) {
        if (typeof text !== 'string') return text;
        
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        
        return text.replace(/[&<>"']/g, char => map[char]);
    }
    
    /**
     * Extrait la catégorie/niveau du match (A1, A2, A3, A4, CFE, CFU)
     * @param {Object} match - Le match
     * @returns {string} La catégorie (ex: 'A1', 'CFU', 'CFE')
     */
    _extractCategory(match) {
        // 1. PRIORITÉ: Utiliser le champ championship_type si disponible
        if (match.championship_type) {
            const type = match.championship_type.toUpperCase();
            // CFU et CFE sont directement retournés
            if (type === 'CFU' || type === 'CFE') {
                return type;
            }
            // Pour 'Acad', extraire le niveau depuis la poule (A1, A2, A3, A4)
            if (type === 'ACAD' && match.poule) {
                const pouleMatch = match.poule.match(/A([1-4])/i);
                if (pouleMatch) {
                    return `A${pouleMatch[1]}`;
                }
            }
            // 'Autre' type
            if (type === 'AUTRE') {
                return 'Autre';
            }
        }
        
        // 2. FALLBACK: Essayer d'extraire depuis le champ poule (ex: "VBFA1PA" -> "A1")
        if (match.poule) {
            // Chercher A1-A4
            const pouleMatch = match.poule.match(/A([1-4])/i);
            if (pouleMatch) {
                return `A${pouleMatch[1]}`;
            }
            
            // Chercher CFE ou CFU dans la poule
            const cfeMatch = match.poule.match(/CF[EU]/i);
            if (cfeMatch) {
                return cfeMatch[0].toUpperCase();
            }
        }
        
        // 3. FALLBACK: Essayer d'extraire depuis le nom de l'équipe
        const teamNames = [match.equipe1_nom, match.equipe2_nom].join(' ');
        
        // Chercher A1, A2, A3, A4
        const categoryMatch = teamNames.match(/A([1-4])/i);
        if (categoryMatch) {
            return `A${categoryMatch[1]}`;
        }
        
        // Chercher CFE ou CFU
        const cfeMatch = teamNames.match(/CF[EU]/i);
        if (cfeMatch) {
            return cfeMatch[0].toUpperCase();
        }
        
        // 4. FALLBACK: Si le match a un champ category/niveau (ancien format)
        if (match.category) {
            const cat = match.category.toUpperCase();
            if (cat.match(/^(A[1-4]|CFE|CFU)$/)) {
                return cat;
            }
        }
        
        if (match.niveau) {
            const niv = match.niveau.toUpperCase();
            if (niv.match(/^(A[1-4]|CFE|CFU)$/)) {
                return niv;
            }
        }
        
        // Par défaut
        return '';
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
     * Options enrichies pour personnaliser l'affichage des poules.
     */
    getDisplayOptions() {
        return {
            title: "Options - Vue Poules",
            options: [
                // Contenu des cartes de poule
                {
                    type: 'checkbox',
                    id: 'pools-show-stats',
                    label: '📊 Afficher statistiques',
                    default: this.displayOptions.showStats,
                    action: (checked) => {
                        this.displayOptions.showStats = checked;
                        this.render();
                    }
                },
                {
                    type: 'checkbox',
                    id: 'pools-show-standings',
                    label: '🏆 Afficher classement',
                    default: this.displayOptions.showStandings,
                    action: (checked) => {
                        this.displayOptions.showStandings = checked;
                        this.render();
                    }
                },
                {
                    type: 'checkbox',
                    id: 'pools-show-matches',
                    label: '🏐 Afficher matchs',
                    default: this.displayOptions.showMatches,
                    action: (checked) => {
                        this.displayOptions.showMatches = checked;
                        this.render();
                    }
                },
                {
                    type: 'checkbox',
                    id: 'pools-show-teams',
                    label: '👥 Afficher équipes',
                    default: this.displayOptions.showTeams,
                    action: (checked) => {
                        this.displayOptions.showTeams = checked;
                        this.render();
                    }
                },
                
                // Options de mise en page
                {
                    type: 'checkbox',
                    id: 'pools-show-summary',
                    label: '📋 Afficher résumé global',
                    default: this.displayOptions.showGlobalSummary,
                    action: (checked) => {
                        this.displayOptions.showGlobalSummary = checked;
                        this.render();
                    }
                },
                {
                    type: 'checkbox',
                    id: 'pools-level-separators',
                    label: '📈 Afficher séparateurs de niveau',
                    default: this.displayOptions.showLevelSeparators,
                    action: (checked) => {
                        this.displayOptions.showLevelSeparators = checked;
                        this.render();
                    }
                },
                {
                    type: 'checkbox',
                    id: 'pools-compact',
                    label: '📦 Mode compact',
                    default: this.displayOptions.compactCards,
                    action: (checked) => {
                        this.displayOptions.compactCards = checked;
                        this.render();
                    }
                },
                {
                    type: 'checkbox',
                    id: 'pools-auto-expand',
                    label: '🔓 Déplier toutes les poules',
                    default: this.displayOptions.autoExpandPools,
                    action: (checked) => {
                        this.displayOptions.autoExpandPools = checked;
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
                <div class="empty-state__icon">🎯</div>
                <h3 class="empty-state__title">Aucune poule</h3>
                <p class="empty-state__message">Les poules apparaîtront ici une fois configurées.</p>
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
                <h3 class="empty-state__title">Aucune poule correspondante</h3>
                <p class="empty-state__message">Aucune poule ne correspond aux filtres sélectionnés.</p>
            </div>
        `;
    }
    
    /**
     * Filtre les poules selon les filtres actifs
     */
    _filterPools(pools) {
        // Validation des entrées
        if (!Array.isArray(pools)) {
            console.warn('[PoolsView] _filterPools: pools n\'est pas un tableau', pools);
            return [];
        }
        
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
                // Validation: s'assurer que equipe est une string
                if (typeof this.selectedFilters.equipe !== 'string') {
                    console.warn('[PoolsView] selectedFilters.equipe devrait être une string', this.selectedFilters.equipe);
                    return true; // Ignorer ce filtre s'il est mal formé
                }
                
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
        const compactClass = this.displayOptions.compactCards ? 'pools-view--compact' : '';
        let html = `<div class="pools-view ${compactClass}">`;
        
        // En-tête avec résumé global (optionnel)
        if (this.displayOptions.showGlobalSummary) {
            html += this._generateGlobalSummary(pools, data);
        }
        
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
        const poolMatches = pools.reduce((sum, p) => 
            sum + (p.nb_matchs_planifies || 0) + (p.nb_matchs_non_planifies || 0), 0);
        const scheduledPoolMatches = pools.reduce((sum, p) => 
            sum + (p.nb_matchs_planifies || 0), 0);
        const unscheduledPoolMatches = pools.reduce((sum, p) => 
            sum + (p.nb_matchs_non_planifies || 0), 0);
        
        // Comptabiliser aussi les matchs sans poule (CFE/CFU)
        let noPoolMatches = 0;
        let noPoolScheduled = 0;
        if (data && data.matches) {
            const allMatches = [
                ...(data.matches.scheduled || []),
                ...(data.matches.unscheduled || [])
            ];
            const noPool = allMatches.filter(m => !m.poule || m.poule === '');
            noPoolMatches = noPool.length;
            noPoolScheduled = noPool.filter(m => m.semaine).length;
        }
        
        // Totaux incluant les matchs sans poule
        const totalMatches = poolMatches + noPoolMatches;
        const scheduledMatches = scheduledPoolMatches + noPoolScheduled;
        const unscheduledMatches = totalMatches - scheduledMatches;
        
        // Utiliser SportUtils pour l'emoji et le nom du sport
        const sportEmoji = window.sportUtils?.getEmoji() || '🏐';
        const sportName = window.sportUtils?.getName() || 'Sport';
        const completionRate = totalMatches > 0 ? Math.round((scheduledMatches / totalMatches) * 100) : 0;
        
        // Info sur les matchs hors poules
        const noPoolInfo = noPoolMatches > 0 ? ` + ${noPoolMatches} CFE/CFU` : '';
        
        return `
            <div class="pools-summary">
                <div class="pools-summary__header">
                    <span class="pools-summary__icon">${sportEmoji}</span>
                    <div>
                        <h2 class="pools-summary__title">Vue Poules - ${sportName}</h2>
                        <p class="pools-summary__subtitle">${pools.length} poules • ${totalTeams} équipes${noPoolInfo} • ${completionRate}% de complétion</p>
                    </div>
                </div>
                <div class="pools-summary__cards">
                    <div class="summary-card">
                        <div class="summary-card__value summary-card__value--primary">${pools.length}</div>
                        <div class="summary-card__label">Poules</div>
                    </div>
                    <div class="summary-card">
                        <div class="summary-card__value summary-card__value--primary">${totalTeams}</div>
                        <div class="summary-card__label">Équipes</div>
                    </div>
                    <div class="summary-card">
                        <div class="summary-card__value summary-card__value--primary">${totalMatches}</div>
                        <div class="summary-card__label">Matchs</div>
                    </div>
                    <div class="summary-card">
                        <div class="summary-card__value summary-card__value--success">${scheduledMatches}</div>
                        <div class="summary-card__label">Planifiés</div>
                    </div>
                    <div class="summary-card">
                        <div class="summary-card__value summary-card__value--danger">${unscheduledMatches}</div>
                        <div class="summary-card__label">Non Planifiés</div>
                    </div>
                    <div class="summary-card">
                        <div class="summary-card__value summary-card__value--info">${completionRate}%</div>
                        <div class="summary-card__label">Complétion</div>
                    </div>
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
        
        // Section spéciale pour les matchs sans poule (CFE/CFU)
        html += this._generateNoPoolSection(data);
        
        html += '</div>';
        
        return html;
    }
    
    /**
     * Génère une section pour les matchs sans poule (CFE/CFU interrégionaux)
     */
    _generateNoPoolSection(data) {
        if (!data || !data.matches) return '';
        
        // Récupérer les matchs sans poule
        const allMatches = [
            ...(data.matches.scheduled || []),
            ...(data.matches.unscheduled || [])
        ];
        
        const noPoolMatches = allMatches.filter(m => !m.poule || m.poule === '');
        
        if (noPoolMatches.length === 0) return '';
        
        // Grouper par type de championnat
        const byType = {
            CFU: noPoolMatches.filter(m => m.championship_type === 'CFU'),
            CFE: noPoolMatches.filter(m => m.championship_type === 'CFE'),
            Other: noPoolMatches.filter(m => m.championship_type !== 'CFU' && m.championship_type !== 'CFE')
        };
        
        let html = '';
        
        // Section CFU
        if (byType.CFU.length > 0) {
            html += this._generateChampionshipSection('CFU', byType.CFU, data);
        }
        
        // Section CFE
        if (byType.CFE.length > 0) {
            html += this._generateChampionshipSection('CFE', byType.CFE, data);
        }
        
        // Autres matchs sans poule
        if (byType.Other.length > 0) {
            html += this._generateChampionshipSection('Interrégionaux', byType.Other, data);
        }
        
        return html;
    }
    
    /**
     * Génère une section pour un type de championnat (CFU, CFE)
     */
    _generateChampionshipSection(type, matches, data) {
        const typeLabel = type === 'CFU' ? 'Championnat de France Universitaire' :
                         type === 'CFE' ? 'Championnat de France des Écoles' :
                         'Matchs Interrégionaux';
        const typeIcon = type === 'CFU' ? '🏆' : type === 'CFE' ? '🎓' : '🌐';
        
        // Grouper par genre
        const byGender = {
            F: matches.filter(m => (m.genre || m.equipe1_genre || m.equipe2_genre) === 'F'),
            M: matches.filter(m => (m.genre || m.equipe1_genre || m.equipe2_genre) === 'M')
        };
        
        const scheduledCount = matches.filter(m => m.semaine).length;
        const unscheduledCount = matches.length - scheduledCount;
        
        let html = `
            <div class="championship-section">
                <div class="championship-separator">
                    <div class="championship-separator__content">
                        <div class="championship-separator__line championship-separator__line--left"></div>
                        <div class="championship-separator__badge">
                            <span class="championship-separator__icon">${typeIcon}</span>
                            <div class="championship-separator__info">
                                <span class="championship-separator__title">${typeLabel}</span>
                                <span class="championship-separator__stats">${matches.length} match${matches.length > 1 ? 's' : ''} • ${scheduledCount} planifié${scheduledCount > 1 ? 's' : ''} • ${unscheduledCount} non planifié${unscheduledCount > 1 ? 's' : ''}</span>
                            </div>
                        </div>
                        <div class="championship-separator__line championship-separator__line--right"></div>
                    </div>
                </div>
                <div class="championship-matches">
        `;
        
        // Afficher les matchs par genre
        if (byGender.F.length > 0) {
            html += `<div class="championship-gender-section championship-gender-section--female">
                <h4 class="championship-gender-title">♀️ Féminin (${byGender.F.length})</h4>
                <div class="championship-matches-grid">`;
            byGender.F.forEach(match => {
                html += this._generateMatchCardNew(match, data, type);
            });
            html += '</div></div>';
        }
        
        if (byGender.M.length > 0) {
            html += `<div class="championship-gender-section championship-gender-section--male">
                <h4 class="championship-gender-title">♂️ Masculin (${byGender.M.length})</h4>
                <div class="championship-matches-grid">`;
            byGender.M.forEach(match => {
                html += this._generateMatchCardNew(match, data, type);
            });
            html += '</div></div>';
        }
        
        html += '</div></div>';
        
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
     * Génère une section de genre avec séparateur visuel
     */
    _generateGenderSection(gender, pools, data) {
        const genderLabel = gender === 'F' ? 'Féminin' : 'Masculin';
        const genderIcon = gender === 'F' ? '♀️' : '♂️';
        const genderClass = gender === 'F' ? 'female' : 'male';
        const genderColor = gender === 'F' ? '#E91E63' : '#2196F3';
        
        const totalTeams = pools.reduce((sum, p) => sum + (p.nb_equipes || 0), 0);
        const totalMatches = pools.reduce((sum, p) => 
            sum + (p.nb_matchs_planifies || 0) + (p.nb_matchs_non_planifies || 0), 0);
        
        let html = this._generateGenderSeparator(gender, pools, totalTeams, totalMatches);
        
        html += `<div class="pools-list ${this.displayOptions.format}">`;
        
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
        
        html += '</div>';
        
        return html;
    }
    
    /**
     * Génère un séparateur de genre avec classes CSS
     */
    _generateGenderSeparator(gender, pools, totalTeams, totalMatches) {
        const genderLabel = gender === 'F' ? 'Féminin' : 'Masculin';
        const genderIcon = gender === 'F' ? '♀️' : '♂️';
        const genderClass = gender === 'F' ? 'female' : 'male';
        
        return `
            <div class="gender-separator gender-separator--${genderClass}">
                <div class="gender-separator__content">
                    <div class="gender-separator__line gender-separator__line--left"></div>
                    <div class="gender-separator__badge">
                        <span class="gender-separator__icon">${genderIcon}</span>
                        <div class="gender-separator__info">
                            <span class="gender-separator__title">${genderLabel}</span>
                            <span class="gender-separator__stats">${pools.length} poule${pools.length > 1 ? 's' : ''} • ${totalTeams} équipe${totalTeams > 1 ? 's' : ''} • ${totalMatches} match${totalMatches > 1 ? 's' : ''}</span>
                        </div>
                    </div>
                    <div class="gender-separator__line gender-separator__line--right"></div>
                </div>
            </div>
        `;
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
     * Génère un séparateur de niveau avec classes CSS
     */
    _generateLevelSeparator(level, pools, data) {
        const totalTeams = pools.reduce((sum, p) => sum + (p.nb_equipes || 0), 0);
        
        return `
            <div class="level-separator">
                <div class="level-separator__line"></div>
                <div class="level-separator__badge">
                    <span class="level-separator__title">Niveau ${level}</span>
                    <span class="level-separator__stats">${pools.length} poule${pools.length > 1 ? 's' : ''} • ${totalTeams} équipe${totalTeams > 1 ? 's' : ''}</span>
                </div>
                <div class="level-separator__line"></div>
            </div>
        `;
    }
    
    /**
     * Génère le balisage pour une poule (format cards uniquement).
     */
    _generatePoolMarkup(pool, data, gender) {
        return this._generatePoolCard(pool, data, gender);
    }

    /**
     * Génère la carte d'une poule avec statistiques détaillées
     */
    _generatePoolCard(pool, data, gender) {
        const isExpanded = this.expandedPools.has(pool.id);
        const genderClass = gender === 'F' ? 'female' : 'male';
        const genderIcon = gender === 'F' ? '♀️' : '♂️';
        
        // Échapper le nom de la poule pour prévenir XSS
        const poolNom = this._escapeHtml(pool.nom);
        const poolNiveau = this._escapeHtml(this._formatLevel(pool.niveau || pool.nom));
        
        // Récupérer les matchs de la poule
        const poolMatches = this.dataManager.getMatchesByPool(pool.id);
        const scheduledMatches = poolMatches.filter(m => m.semaine);
        const unscheduledMatches = poolMatches.filter(m => !m.semaine);
        
        // Un match est joué SEULEMENT s'il a un score valide
        const playedMatches = scheduledMatches.filter(m => this._hasValidScore(m));
        
        // Les matchs à venir sont ceux planifiés mais sans score
        const upcomingMatches = scheduledMatches.filter(m => !this._hasValidScore(m));
        
        // Calculer le taux de complétion
        const completionRate = poolMatches.length > 0 ? (scheduledMatches.length / poolMatches.length) * 100 : 0;
        
        let html = `
            <div class="pool-card pool-card--${genderClass} ${isExpanded ? 'expanded' : ''}" data-pool-id="${pool.id}">
                <div class="pool-header pool-header--${genderClass}" data-toggle-pool="${pool.id}">
                    <div class="pool-header__watermark">${genderIcon}</div>
                    <div class="pool-header__top">
                        <h3 class="pool-header__title">${poolNom}</h3>
                        <button class="pool-header__expand-btn ${isExpanded ? 'expanded' : ''}" aria-label="Développer">
                            ${isExpanded ? '▼' : '▶'}
                        </button>
                    </div>
                    <div class="pool-header__info">
                        <span class="pool-header__chip">📊 ${poolNiveau}</span>
                        <span class="pool-header__stat">👥 <strong>${pool.nb_equipes}</strong> équipes</span>
                        <span class="pool-header__stat">⚽ <strong>${poolMatches.length}</strong> matchs</span>
                        <span class="pool-header__stat">✓ ${completionRate.toFixed(0)}% planifié</span>
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
     * Respecte les options d'affichage pour montrer/cacher les sections.
     */
    _generateExpandedContent(pool, data) {
        const poolMatches = this.dataManager.getMatchesByPool(pool.id);
        const scheduledMatches = poolMatches.filter(m => m.semaine);
        
        // Un match est joué SEULEMENT s'il a un score valide
        const playedMatches = scheduledMatches.filter(m => this._hasValidScore(m));
        
        // Les matchs à venir sont ceux planifiés mais sans score
        const upcomingMatches = scheduledMatches.filter(m => !this._hasValidScore(m));
        
        const unscheduledMatches = poolMatches.filter(m => !m.semaine);

        let html = '<div class="pool-content">';
            
        // Afficher les équipes si l'option est activée
        if (this.displayOptions.showTeams) {
            html += this._generateTeamsList(pool, data);
        }
        
        // Conteneur flex pour stats et classement (si au moins l'un des deux est affiché)
        if (this.displayOptions.showStats || this.displayOptions.showStandings) {
            html += '<div class="pool-details-grid">';

            // Statistiques détaillées
            if (this.displayOptions.showStats) {
                html += '<div class="pool-content-section">';
                html += '<h4 class="pool-content-section__title">📊 Statistiques</h4>';
                html += this._generatePoolStats(pool, playedMatches, upcomingMatches, unscheduledMatches);
                html += '</div>';
            }
            
            // Classement
            if (this.displayOptions.showStandings) {
                html += '<div class="pool-content-section">';
                html += '<h4 class="pool-content-section__title">🏆 Classement</h4>';
                // Passer tous les matchs de la poule pour calculer les stats correctement
                html += this._generateStandings(pool, data, poolMatches);
                html += '</div>';
            }

            html += '</div>'; // Fin de pool-details-grid
        }
        
        // Matchs avec onglets
        if (this.displayOptions.showMatches) {
            html += '<div class="pool-content-section">';
            html += '<h4 class="pool-content-section__title">⚽ Matchs</h4>';
            html += this._generatePoolMatchesWithTabs(pool.id, playedMatches, upcomingMatches, data);
            html += '</div>';
        }
        
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
            const teamNom = this._escapeHtml(team.nom);
            const sportEmoji = window.sportUtils?.getEmoji() || '🏐';
            
            html += `
                <div class="team-item">
                    <div class="team-item-icon">${sportEmoji}</div>
                    <div class="team-item-content">
                        <div class="team-item-name">${teamNom}</div>
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
            <div class="pool-stats">
                <div class="stat-item stat-item--success">
                    <div class="stat-item__value stat-item__value--success">${playedMatches.length}</div>
                    <div class="stat-item__label">Joués</div>
                    <div class="stat-item__detail">${playedRate}% du total</div>
                </div>
                <div class="stat-item stat-item--info">
                    <div class="stat-item__value stat-item__value--info">${upcomingMatches.length}</div>
                    <div class="stat-item__label">À venir</div>
                </div>
                <div class="stat-item stat-item--danger">
                    <div class="stat-item__value stat-item__value--danger">${unscheduledMatches.length}</div>
                    <div class="stat-item__label">Non planifiés</div>
                </div>
                ${ententeMatches.length > 0 ? `
                <div class="stat-item stat-item--warning">
                    <div class="stat-item__value stat-item__value--warning">${ententeMatches.length}</div>
                    <div class="stat-item__label">Entente</div>
                </div>
                ` : ''}
                <div class="stat-item stat-item--primary">
                    <div class="stat-item__value stat-item__value--primary">${completionRate}%</div>
                    <div class="stat-item__label">Planifiés</div>
                    <div class="stat-item__detail">${scheduledMatches}/${totalMatches}</div>
                </div>
            </div>
        `;
    }
    
    /**
     * Génère le classement d'une poule avec données améliorées.
     * Affiche différentes colonnes selon le sport:
     * - Volleyball: J (joués), ? (sans score), V (victoires), D (défaites), Pts
     * - Autres sports: J (joués), V, N (nuls), D, Pts
     * 
     * @param {Object} pool - La poule
     * @param {Object} data - Données complètes
     * @param {Array} allPoolMatches - Tous les matchs de la poule (avec ou sans score)
     */
    _generateStandings(pool, data, allPoolMatches) {
        // Récupérer les équipes de la poule
        const teams = this._getPoolTeams(pool.id, data);
        
        if (teams.length === 0) {
            return '<div class="standings-empty">Aucune équipe dans cette poule</div>';
        }
        
        // Calculer les stats des équipes basées sur tous les matchs de la poule
        const standings = this._calculateDetailedStandings(teams, allPoolMatches);
        
        const sportType = window.sportUtils?.getType() || 'volleyball';
        const isVolleyball = sportType === 'volleyball';
        
        let html = `
            <div class="pool-standings">
                <table class="standings-table">
                    <thead>
                        <tr class="standings-table__header-row">
                            <th class="standings-table__th standings-table__th--rank">#</th>
                            <th class="standings-table__th standings-table__th--team">Équipe</th>
                            <th class="standings-table__th standings-table__th--stat" title="Matchs Joués">J</th>
                            <th class="standings-table__th standings-table__th--stat" title="Matchs sans score">?</th>
                            <th class="standings-table__th standings-table__th--stat" title="Victoires">V</th>
                            ${!isVolleyball ? '<th class="standings-table__th standings-table__th--stat" title="Nuls">N</th>' : ''}
                            <th class="standings-table__th standings-table__th--stat" title="Défaites">D</th>
                            <th class="standings-table__th standings-table__th--stat" title="Différence de ${isVolleyball ? 'sets' : 'buts'}">+/-</th>
                            <th class="standings-table__th standings-table__th--points" title="Points">Pts</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        standings.forEach((team, index) => {
            const positionClass = index < 3 ? `standings-table__row--position-${index + 1}` : '';
            
            // Échapper les noms d'équipes
            const teamNom = this._escapeHtml(team.nom);
            const teamNomComplet = this._escapeHtml(team.nom_complet || team.nom);
            
            // Calculer la différence de sets/buts
            const diff = team.setsFor - team.setsAgainst;
            const diffDisplay = diff > 0 ? `+${diff}` : diff.toString();
            const diffClass = diff > 0 ? 'standings-table__td--positive' : (diff < 0 ? 'standings-table__td--negative' : '');
            
            // Formater les victoires/défaites pour le volleyball (avec détail tie-break)
            let wonDisplay, lostDisplay;
            if (isVolleyball && (team.wonTieBreak > 0 || team.lostTieBreak > 0)) {
                // Afficher le détail si au moins un tie-break
                wonDisplay = team.won;
                lostDisplay = team.lost;
            } else {
                wonDisplay = team.won;
                lostDisplay = team.lost;
            }
            
            // Tooltip détaillé pour le volleyball
            const wonTooltip = isVolleyball 
                ? `Victoires: ${team.wonClassic} classiques (3-0/3-1) + ${team.wonTieBreak} tie-breaks (3-2)`
                : `${team.won} victoire(s)`;
            const lostTooltip = isVolleyball
                ? `Défaites: ${team.lostClassic} classiques (0-3/1-3) + ${team.lostTieBreak} tie-breaks (2-3)`
                : `${team.lost} défaite(s)`;
            
            html += `
                <tr class="standings-table__row ${positionClass}">
                    <td class="standings-table__td standings-table__td--rank ${index < 3 ? 'standings-table__td--top3' : ''}">${index + 1}</td>
                    <td class="standings-table__td standings-table__td--team" title="${teamNomComplet}">${teamNom}</td>
                    <td class="standings-table__td standings-table__td--played">${team.played}</td>
                    <td class="standings-table__td standings-table__td--noscore ${team.noScore > 0 ? 'standings-table__td--warning' : ''}" title="Matchs planifiés sans score">${team.noScore}</td>
                    <td class="standings-table__td standings-table__td--won" title="${wonTooltip}">${wonDisplay}</td>
                    ${!isVolleyball ? `<td class="standings-table__td standings-table__td--drawn">${team.drawn}</td>` : ''}
                    <td class="standings-table__td standings-table__td--lost" title="${lostTooltip}">${lostDisplay}</td>
                    <td class="standings-table__td standings-table__td--diff ${diffClass}" title="${team.setsFor} - ${team.setsAgainst}">${diffDisplay}</td>
                    <td class="standings-table__td standings-table__td--points">${team.points}</td>
                </tr>
            `;
        });
        
        html += `
                    </tbody>
                </table>
            </div>
        `;
        
        // Légende pour le volleyball
        if (isVolleyball) {
            html += `
                <div class="standings-legend">
                    <small class="standings-legend__text">
                        <span title="Victoire classique (3-0 ou 3-1): 3 pts">V: 3 ou 2 pts</span> · 
                        <span title="Défaite tie-break (2-3): 1 pt">D(tb): 1 pt</span> · 
                        <span title="Défaite classique (0-3 ou 1-3): 0 pt">D: 0 pt</span>
                    </small>
                </div>
            `;
        }
        
        return html;
    }
    
    /**
     * Récupère les équipes d'une poule
     */
    _getPoolTeams(poolId, data) {
        // Validation des données
        if (!data?.entities?.equipes || !Array.isArray(data.entities.equipes)) {
            console.warn('[PoolsView] _getPoolTeams: données équipes invalides');
            return [];
        }
        
        if (!poolId) {
            console.warn('[PoolsView] _getPoolTeams: poolId manquant');
            return [];
        }
        
        return data.entities.equipes.filter(e => e.poule === poolId);
    }
    
    /**
     * Calcule le classement détaillé avec victoires/défaites basé sur les scores réels.
     * Supporte différents systèmes de points selon le sport:
     * - Volleyball: 3pts victoire classique (3-0/3-1), 2pts victoire tie-break (3-2),
     *               1pt défaite tie-break (2-3), 0pts défaite classique (0-3/1-3)
     * - Autres sports: 3pts victoire, 1pt nul, 0pts défaite
     */
    _calculateDetailedStandings(teams, matches) {
        const stats = {};
        const sportType = window.sportUtils?.getType() || 'volleyball';
        const isVolleyball = sportType === 'volleyball';
        
        // Initialiser les stats
        teams.forEach(team => {
            stats[team.id] = {
                id: team.id,
                nom: team.nom,
                nom_complet: team.nom_complet,
                played: 0,           // Matchs joués (avec score)
                noScore: 0,          // Matchs sans score (assignés à cette équipe mais pas de score)
                won: 0,              // Total victoires
                wonClassic: 0,       // Victoires classiques (3-0, 3-1) - volley
                wonTieBreak: 0,      // Victoires tie-break (3-2) - volley
                drawn: 0,            // Match nul (autres sports)
                lost: 0,             // Total défaites
                lostTieBreak: 0,     // Défaites tie-break (2-3) - volley
                lostClassic: 0,      // Défaites classiques (0-3, 1-3) - volley
                points: 0,
                setsFor: 0,          // Sets gagnés (volley) / Buts marqués (autres)
                setsAgainst: 0       // Sets perdus (volley) / Buts encaissés (autres)
            };
        });
        
        // Compter les matchs sans score pour chaque équipe
        // Les matchs sont passés en paramètre (inclut matchs planifiés + non planifiés)
        // Un match sans score = match planifié (has_score: false ou is_fixed: true sans score)
        matches.forEach(match => {
            if (!this._hasValidScore(match)) {
                // Match sans score valide
                if (stats[match.equipe1_id]) stats[match.equipe1_id].noScore++;
                if (stats[match.equipe2_id]) stats[match.equipe2_id].noScore++;
            }
        });
        
        // Analyser les matchs avec scores
        matches.forEach(match => {
            // Un match est joué seulement s'il a un score valide
            if (!this._hasValidScore(match)) return;
            
            const team1Id = match.equipe1_id;
            const team2Id = match.equipe2_id;
            const score1 = match.score.equipe1;
            const score2 = match.score.equipe2;
            
            // Vérifications de sécurité
            if (!stats[team1Id] || !stats[team2Id]) return;
            
            // Incrémenter les matchs joués
            stats[team1Id].played++;
            stats[team2Id].played++;
            
            // Enregistrer les sets/buts
            stats[team1Id].setsFor += score1;
            stats[team1Id].setsAgainst += score2;
            stats[team2Id].setsFor += score2;
            stats[team2Id].setsAgainst += score1;
            
            // Déterminer le résultat et attribuer les points selon le sport
            if (isVolleyball) {
                // Système de points volleyball
                this._applyVolleyballPoints(stats, team1Id, team2Id, score1, score2);
            } else {
                // Système de points classique (autres sports)
                this._applyClassicPoints(stats, team1Id, team2Id, score1, score2);
            }
        });
        
        // Trier par points, puis sets/goal average, puis sets/buts marqués, puis nom
        return Object.values(stats).sort((a, b) => {
            // D'abord par points
            if (b.points !== a.points) return b.points - a.points;
            
            // Puis par différence de sets/buts
            const diffA = a.setsFor - a.setsAgainst;
            const diffB = b.setsFor - b.setsAgainst;
            if (diffB !== diffA) return diffB - diffA;
            
            // Puis par sets/buts marqués
            if (b.setsFor !== a.setsFor) return b.setsFor - a.setsFor;
            
            // Puis par nombre de victoires
            if (b.won !== a.won) return b.won - a.won;
            
            // Enfin par nom
            return a.nom.localeCompare(b.nom);
        });
    }
    
    /**
     * Applique le système de points volleyball:
     * - Victoire 3-0 ou 3-1: 3 points pour le gagnant, 0 pour le perdant
     * - Victoire 3-2 (tie-break): 2 points pour le gagnant, 1 pour le perdant
     * - Si le score n'est pas classique (ex: gagnant < 3 sets), considéré comme sans tie-break
     */
    _applyVolleyballPoints(stats, team1Id, team2Id, score1, score2) {
        const maxScore = Math.max(score1, score2);
        const minScore = Math.min(score1, score2);
        
        // Déterminer si c'est un tie-break (3-2)
        // Un tie-break valide est exactement 3-2
        // Si le score n'est pas classique (gagnant != 3), on considère pas de tie-break
        const isTieBreak = (maxScore === 3 && minScore === 2);
        
        if (score1 > score2) {
            // Victoire équipe 1
            stats[team1Id].won++;
            stats[team2Id].lost++;
            
            if (isTieBreak) {
                // Victoire au tie-break: 2pts gagnant, 1pt perdant
                stats[team1Id].wonTieBreak++;
                stats[team1Id].points += 2;
                stats[team2Id].lostTieBreak++;
                stats[team2Id].points += 1;
            } else {
                // Victoire classique: 3pts gagnant, 0pt perdant
                stats[team1Id].wonClassic++;
                stats[team1Id].points += 3;
                stats[team2Id].lostClassic++;
            }
        } else if (score2 > score1) {
            // Victoire équipe 2
            stats[team2Id].won++;
            stats[team1Id].lost++;
            
            if (isTieBreak) {
                // Victoire au tie-break: 2pts gagnant, 1pt perdant
                stats[team2Id].wonTieBreak++;
                stats[team2Id].points += 2;
                stats[team1Id].lostTieBreak++;
                stats[team1Id].points += 1;
            } else {
                // Victoire classique: 3pts gagnant, 0pt perdant
                stats[team2Id].wonClassic++;
                stats[team2Id].points += 3;
                stats[team1Id].lostClassic++;
            }
        }
        // Pas de match nul en volleyball
    }
    
    /**
     * Applique le système de points classique (football, handball, basket...):
     * - Victoire: 3 points
     * - Nul: 1 point
     * - Défaite: 0 point
     */
    _applyClassicPoints(stats, team1Id, team2Id, score1, score2) {
        if (score1 > score2) {
            // Victoire équipe 1
            stats[team1Id].won++;
            stats[team1Id].wonClassic++;
            stats[team1Id].points += 3;
            stats[team2Id].lost++;
            stats[team2Id].lostClassic++;
        } else if (score2 > score1) {
            // Victoire équipe 2
            stats[team2Id].won++;
            stats[team2Id].wonClassic++;
            stats[team2Id].points += 3;
            stats[team1Id].lost++;
            stats[team1Id].lostClassic++;
        } else {
            // Match nul
            stats[team1Id].drawn++;
            stats[team1Id].points += 1;
            stats[team2Id].drawn++;
            stats[team2Id].points += 1;
        }
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
                
                <div class="matches-tabs">
                    <button class="match-tab ${activeTab === 'upcoming' ? 'match-tab--active' : ''}" 
                            data-tab="upcoming" data-pool="${poolId}">
                        À venir
                        <span class="match-tab__count">${upcomingMatches.length}</span>
                    </button>
                    <button class="match-tab ${activeTab === 'played' ? 'match-tab--active' : ''}" 
                            data-tab="played" data-pool="${poolId}">
                        Joués
                        <span class="match-tab__count">${playedMatches.length}</span>
                    </button>
                    ${unscheduledMatches.length > 0 ? `
                    <button class="match-tab match-tab--unscheduled ${activeTab === 'unscheduled' ? 'match-tab--active' : ''}" 
                            data-tab="unscheduled" data-pool="${poolId}">
                        Non planifiés
                        <span class="match-tab__count">${unscheduledMatches.length}</span>
                    </button>
                    ` : ''}
                    <button class="match-tab ${activeTab === 'all' ? 'match-tab--active' : ''}" 
                            data-tab="all" data-pool="${poolId}">
                        Tous
                        <span class="match-tab__count">${allMatches.length}</span>
                    </button>
                </div>
                
                <div class="matches-content ${activeTab === 'upcoming' ? 'matches-content--active' : ''}" 
                     data-content="upcoming" data-pool="${poolId}">
                    ${this._generateMatchesList(upcomingMatches, data, 'upcoming')}
                </div>
                
                <div class="matches-content ${activeTab === 'played' ? 'matches-content--active' : ''}" 
                     data-content="played" data-pool="${poolId}">
                    ${this._generateMatchesList(playedMatches, data, 'played')}
                </div>
                
                ${unscheduledMatches.length > 0 ? `
                <div class="matches-content ${activeTab === 'unscheduled' ? 'matches-content--active' : ''}" 
                     data-content="unscheduled" data-pool="${poolId}">
                    ${this._generateMatchesList(unscheduledMatches, data, 'unscheduled')}
                </div>
                ` : ''}
                
                <div class="matches-content ${activeTab === 'all' ? 'matches-content--active' : ''}" 
                     data-content="all" data-pool="${poolId}">
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
            return `<div class="matches-empty">${emptyMessage}</div>`;
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
            html += `<h5 class="week-group__title">📅 Semaine ${week}</h5>`;
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
        // Validation des données du match
        if (!match || !match.match_id) {
            console.warn('[PoolsView] _generateMatchCardNew: match invalide', match);
            return '';
        }
        
        const gymnase = this.dataManager?.getGymnaseById(match.gymnase);
        
        // Échapper les noms pour prévenir XSS - éviter d'afficher "EXTERNE" pour les équipes hors championnat
        const equipe1NomRaw = (match.equipe1_nom_complet && match.equipe1_nom_complet !== 'EXTERNE') 
            ? match.equipe1_nom_complet 
            : (match.equipe1_nom || 'Équipe 1');
        const equipe2NomRaw = (match.equipe2_nom_complet && match.equipe2_nom_complet !== 'EXTERNE') 
            ? match.equipe2_nom_complet 
            : (match.equipe2_nom || 'Équipe 2');
        const equipe1Nom = this._escapeHtml(equipe1NomRaw);
        const equipe2Nom = this._escapeHtml(equipe2NomRaw);
        const equipe1Num = match.equipe1_num ? `#${this._escapeHtml(String(match.equipe1_num))}` : '';
        const equipe2Num = match.equipe2_num ? `#${this._escapeHtml(String(match.equipe2_num))}` : '';
        const gymnaseNom = this._escapeHtml(gymnase?.nom || 'Non défini');

        // Déterminer si le match est réellement joué (a un score valide)
        const hasScore = this._hasValidScore(match);
        
        // Déterminer si le match est planifié
        const isScheduled = match.semaine && match.horaire && match.gymnase;
        
        const statusClass = hasScore ? 'played' : (isScheduled ? 'upcoming' : 'unscheduled');
        const statusLabel = hasScore ? 'Terminé' : (isScheduled ? 'À venir' : 'Non planifié');
        const statusIcon = hasScore ? '✅' : (isScheduled ? '⏳' : '❌');
        
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
            <div class="match-badge match-badge--entente">
                <span class="match-badge__icon">🤝</span>
                Entente
            </div>
        ` : '';
        
        // Déterminer la catégorie du match (CFU, CFE, A1, etc.)
        const category = this._extractCategory(match);
        
        // Badge CFU
        const cfuBadge = category === 'CFU' ? `<div class="match-badge match-badge--cfu">CFU</div>` : '';
        
        // Badge CFE
        const cfeBadge = category === 'CFE' ? `<div class="match-badge match-badge--cfe">CFE</div>` : '';
        
        // Déterminer le genre pour les classes CSS - utiliser match.genre en priorité
        const genre = match.genre || match.equipe1_genre || match.equipe2_genre;
        const genreClass = genre === 'M' ? 'match-card--male' : genre === 'F' ? 'match-card--female' : '';

        // Use total field directly, or sum only numeric values (ignore nested objects)
        const penalties = match.penalties || {};
        const totalPenalties = typeof penalties.total === 'number' 
            ? penalties.total 
            : Object.values(penalties).reduce((sum, p) => typeof p === 'number' ? sum + p : sum, 0);
        const penaltyClass = totalPenalties > 10 ? 'match-penalty--high' : totalPenalties > 5 ? 'match-penalty--medium' : 'match-penalty--low';
        
        // Classes CSS pour la carte
        let cardClasses = ['match-card', `match-card--${statusClass}`, genreClass];
        if (category === 'CFU') cardClasses.push('match-card--cfu');
        if (category === 'CFE') cardClasses.push('match-card--cfe');
        if (!isScheduled) cardClasses.push('match-card--unscheduled');

        return `
            <div class="${cardClasses.join(' ')}" data-match-id="${match.match_id}">
                <div class="match-card__header">
                    <div class="match-card__badges">
                        <div class="match-card__status match-card__status--${statusClass}">
                            <span class="match-card__status-icon">${statusIcon}</span>
                            <span class="match-card__status-label">${statusLabel}</span>
                        </div>
                        ${cfuBadge}
                        ${cfeBadge}
                        ${ententeBadge}
                    </div>
                    <div class="match-card__week">
                        ${isScheduled ? `Semaine ${match.semaine}` : 'À planifier'}
                    </div>
                </div>

                <div class="match-card__body">
                    <div class="match-card__team match-card__team--left ${team1Winner ? 'match-card__team--winner' : ''}">
                        <div class="match-card__team-info">
                            <div class="match-card__team-details">
                                ${equipe1Num ? `<span class="match-card__team-num">${equipe1Num}</span>` : ''}
                                <span class="match-card__team-name ${team1Winner ? 'match-card__team-name--winner' : ''}">${equipe1Nom}</span>
                            </div>
                            ${hasScore ? `<span class="match-card__score ${team1Winner ? 'match-card__score--winner' : ''}">${match.score.equipe1}</span>` : ''}
                            ${team1Winner ? '<span class="match-card__trophy">🏆</span>' : ''}
                        </div>
                    </div>
                    <div class="match-card__versus">
                        <span class="match-card__vs">VS</span>
                    </div>
                    <div class="match-card__team match-card__team--right ${team2Winner ? 'match-card__team--winner' : ''}">
                        <div class="match-card__team-info match-card__team-info--reverse">
                            ${team2Winner ? '<span class="match-card__trophy">🏆</span>' : ''}
                            ${hasScore ? `<span class="match-card__score ${team2Winner ? 'match-card__score--winner' : ''}">${match.score.equipe2}</span>` : ''}
                            <div class="match-card__team-details">
                                <span class="match-card__team-name ${team2Winner ? 'match-card__team-name--winner' : ''}">${equipe2Nom}</span>
                                ${equipe2Num ? `<span class="match-card__team-num">${equipe2Num}</span>` : ''}
                            </div>
                        </div>
                    </div>
                </div>

                <div class="match-card__footer">
                    ${isScheduled ? `
                    <div class="match-card__info match-card__info--location">
                        <span class="match-card__info-icon">📍</span>
                        <span class="match-card__info-text">${gymnaseNom}</span>
                    </div>
                    <div class="match-card__info match-card__info--time">
                        <span class="match-card__info-icon">🕒</span>
                        <span class="match-card__info-text match-card__info-text--mono">${this._escapeHtml(match.jour || '')} ${this._escapeHtml(match.horaire || '')}</span>
                    </div>
                    ` : `
                    <div class="match-card__info match-card__info--warning">
                        <span class="match-card__info-icon">⚠️</span>
                        <span class="match-card__info-text">Ce match nécessite une planification</span>
                    </div>
                    `}
                    ${totalPenalties > 0 ? `
                    <div class="match-card__info match-card__info--penalty ${penaltyClass}" title="Pénalités: ${totalPenalties.toFixed(1)}">
                        <span class="match-card__info-icon">⚠️</span>
                        <span class="match-card__info-text match-card__info-text--mono">${totalPenalties.toFixed(1)}</span>
                    </div>` : ''}
                </div>
            </div>
        `;
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
        const matchCards = this.container.querySelectorAll('.match-card, .match-card-new');
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

