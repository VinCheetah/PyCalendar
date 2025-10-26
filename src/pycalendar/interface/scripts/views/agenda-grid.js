/**
 * AgendaGridView - Vue agenda avec colonnes adaptatives
 * 
 * Fonctionnalités principales de la vue agenda.
 */
class AgendaGridView {
    constructor(dataManager, container) {
        this.dataManager = dataManager;
        this.container = container;
        
        // Modules utilitaires
        this.viewManager = new AgendaViewManager(dataManager);
        this.slotManager = new SlotManager();
        this.cardRenderer = new MatchCardRenderer(dataManager);
        this.availableSlotsManager = new AvailableSlotsManager();
        
        // Filtres actifs
        this.filters = {
            institution: '',
            pool: '',
            venue: '',
            team: '',
            gender: ''
        };
        
    }
    
    /**
     * Initialise la vue
     */
    init() {
        this.render();
    }
    
    /**
     * Filtre les matchs selon les critères actifs
     */
    filterMatches(matches) {
        let filtered = [...matches];
        
        if (this.filters.gender) {
            filtered = filtered.filter(m => {
                const genre = m.equipe1_genre || m.equipe2_genre;
                return genre === this.filters.gender;
            });
        }
        
        if (this.filters.institution) {
            filtered = filtered.filter(m => 
                m.equipe1_institution === this.filters.institution || 
                m.equipe2_institution === this.filters.institution
            );
        }
        
        if (this.filters.pool) {
            filtered = filtered.filter(m => m.poule === this.filters.pool);
        }
        
        if (this.filters.venue) {
            filtered = filtered.filter(m => m.gymnase === this.filters.venue);
        }
        
        if (this.filters.team) {
            filtered = filtered.filter(m =>
                m.equipe1_nom.toLowerCase().includes(this.filters.team.toLowerCase()) ||
                m.equipe2_nom.toLowerCase().includes(this.filters.team.toLowerCase())
            );
        }
        
        return filtered;
    }
    
    /**
     * Calcule le nombre maximum de matchs + créneaux disponibles au même horaire pour chaque colonne
     * @param {Array} columns - Les colonnes à analyser
     * @param {Array} matches - Les matchs filtrés
     * @returns {Map} - Map avec columnId => maxSimultaneousSlots
     */
    calculateMaxSimultaneousSlotsPerColumn(columns, matches) {
        const maxSlotsMap = new Map();
        
        columns.forEach(column => {
            const columnMatches = this.viewManager.getMatchesForColumn(column, matches);
            const matchesByTime = this.groupMatchesByExactTime(columnMatches);
            
            let maxSlots = 0;
            matchesByTime.forEach(group => {
                // Compter les matchs existants
                let slotsAtThisTime = group.matches.length;
                
                // Ajouter les créneaux disponibles si activés
                if (this.availableSlotsManager.showAvailableSlots) {
                    const capacity = column.capacity || 1;
                    const available = this.availableSlotsManager.calculateAvailable(group.matches, capacity);
                    slotsAtThisTime += available;
                }
                
                maxSlots = Math.max(maxSlots, slotsAtThisTime);
            });
            
            // Assurer un minimum de 1
            maxSlots = Math.max(1, maxSlots);
            maxSlotsMap.set(column.id, maxSlots);
        });
        
        return maxSlotsMap;
    }

    /**
     * Rend la vue
     */
    render() {
        try {
            console.log('[AgendaGridView] Début du rendu...');
            const data = this.dataManager.getData();
            if (!data || !data.matches) {
                console.warn('[AgendaGridView] Aucune donnée de match disponible. Affichage de l\'état vide.');
                this.container.innerHTML = '<div class="empty-state">Aucune donnée disponible</div>';
                return;
            }
            
            console.log('[AgendaGridView] Données chargées, filtrage des matchs...');
            const allMatches = data.matches.scheduled || [];
            const filteredMatches = this.filterMatches(allMatches);
            
            // Calculer la plage horaire dynamique
            console.log('[AgendaGridView] Calcul de la plage horaire...');
            this.viewManager.calculateTimeRange(filteredMatches);
            
            // Obtenir les colonnes selon le mode d'affichage
            console.log('[AgendaGridView] Récupération des colonnes...');
            const columns = this.viewManager.getColumns(filteredMatches);
            
            // Calculer le max de slots simultanés par colonne
            console.log('[AgendaGridView] Calcul des slots simultanés maximum...');
            this.maxSlotsPerColumn = this.calculateMaxSimultaneousSlotsPerColumn(columns, filteredMatches);
            
            // Générer le HTML
            console.log('[AgendaGridView] Génération du HTML...');
            const html = this.generateHTML(filteredMatches, columns, data);
            this.container.innerHTML = html;
            
            // Attacher les événements
            console.log('[AgendaGridView] Attachement des événements...');
            this.attachEvents();
            
            console.log('[AgendaGridView] Rendu terminé avec succès.');
            
        } catch (error) {
            console.error('[AgendaGridView] Erreur critique pendant le rendu:', error);
            this.container.innerHTML = `
                <div class="error-state">
                    <h3>⚠️ Erreur d'affichage</h3>
                    <p>${error.message}</p>
                    <button onclick="location.reload()">Recharger la page</button>
                </div>
            `;
        }
    }
    
    /**
     * Génère le HTML complet
     */
    generateHTML(matches, columns, data) {
        return `
            <div class="agenda-grid-view">
                ${this.generateToolbar(matches, columns, data)}
                ${this.generateGrid(matches, columns)}
                ${this.generateLegend()}
            </div>
        `;
    }
    
    /**
     * Génère la barre d'outils
     */
    generateToolbar(matches, columns, data) {
        const navData = this.viewManager.getNavigationData();
        const stats = this.viewManager.getViewStats(matches, columns);
        
        return `
            <div class="agenda-toolbar">
                <div class="toolbar-left">
                    <!-- Sélecteur de vue -->
                    <div class="toolbar-group">
                        <label for="grid-display-mode">Vue:</label>
                        <select id="grid-display-mode" class="form-select">
                            <option value="venues" ${this.viewManager.displayMode === 'venues' ? 'selected' : ''}>
                                Par gymnase
                            </option>
                            <option value="weeks" ${this.viewManager.displayMode === 'weeks' ? 'selected' : ''}>
                                Par semaine
                            </option>
                        </select>
                    </div>
                    
                    <!-- Navigation -->
                    ${navData.mode === 'venues' ? `
                    <div class="toolbar-group toolbar-navigation">
                        <button id="grid-prev-week" 
                                class="btn btn-sm btn-secondary" 
                                ${!navData.hasPrevious ? 'disabled' : ''}
                                title="Semaine précédente">
                            ◄
                        </button>
                        <span class="navigation-label">${navData.currentLabel}</span>
                        <button id="grid-next-week" 
                                class="btn btn-sm btn-secondary"
                                ${!navData.hasNext ? 'disabled' : ''}
                                title="Semaine suivante">
                            ►
                        </button>
                        <span class="navigation-counter">(${navData.index}/${navData.total})</span>
                    </div>
                    ` : ''}
                </div>
                
                <div class="toolbar-center">
                    <!-- Statistiques -->
                    <div class="toolbar-stats">
                        <span class="stat-item">
                            <strong>${stats.visibleMatches}</strong> match${stats.visibleMatches > 1 ? 's' : ''} affiché${stats.visibleMatches > 1 ? 's' : ''}
                        </span>
                        <span class="stat-item">
                            <strong>${stats.totalColumns}</strong> ${this.viewManager.displayMode === 'venues' ? 'gymnase' : 'semaine'}${stats.totalColumns > 1 ? 's' : ''}
                        </span>
                        <span class="stat-item">
                            ${stats.timeRange}
                        </span>
                        ${stats.totalMatches !== stats.visibleMatches ? `
                        <span class="stat-item stat-filtered">
                            (sur ${stats.totalMatches} total)
                        </span>
                        ` : ''}
                    </div>
                </div>
                
                <div class="toolbar-right">
                    <!-- Options d'affichage -->
                    <div class="toolbar-group">
                        <label class="checkbox-label">
                            <input type="checkbox" 
                                   id="grid-show-available" 
                                   ${this.availableSlotsManager.showAvailableSlots ? 'checked' : ''}>
                            <span>Créneaux disponibles</span>
                        </label>
                    </div>
                    
                    <!-- Filtres rapides -->
                    ${this.generateQuickFilters(data)}
                </div>
            </div>
        `;
    }
    
    /**
     * Génère les filtres rapides
     */
    generateQuickFilters(data) {
        return `
            <div class="toolbar-group quick-filters">
                <select id="filter-gender" class="form-select form-select-sm">
                    <option value="">Tous genres</option>
                    <option value="M" ${this.filters.gender === 'M' ? 'selected' : ''}>♂️ Masculin</option>
                    <option value="F" ${this.filters.gender === 'F' ? 'selected' : ''}>♀️ Féminin</option>
                </select>
                
                <input type="text" 
                       id="filter-team" 
                       class="form-input form-input-sm" 
                       placeholder="🔍 Équipe..."
                       value="${this.filters.team}">
            </div>
        `;
    }
    
    /**
     * Génère la grille principale avec échelle horaire continue
     */
    generateGrid(matches, columns) {
        // Calculer la largeur minimale de colonne selon la capacité
        const minColWidth = 150; // Base réduite pour plus de flexibilité
        const colWidthIncrement = 120; // Augmentation par slot supplémentaire
        
        // Paramètres de l'échelle horaire
        const minHour = this.viewManager.minHour; // ex: 8
        const maxHour = this.viewManager.maxHour; // ex: 23
        const pixelsPerHour = 80; // Hauteur en pixels pour 1 heure
        const totalHeight = (maxHour - minHour) * pixelsPerHour;

        return `
            <div class="grid-container" onscroll="window.syncScroll(this)">
                <div class="time-grid time-grid-continuous">
                    <!-- En-tête avec colonne des heures + colonnes gymnases/semaines -->
                    <div class="grid-header" id="grid-header">
                        <div class="time-column header-cell">Horaire</div>
                        <div class="header-columns-container">
                            ${columns.map(col => this.generateColumnHeader(col, minColWidth, colWidthIncrement)).join('')}
                        </div>
                    </div>
                    
                    <!-- Corps de la grille avec échelle continue -->
                    <div class="grid-body-continuous" style="position: relative; height: ${totalHeight}px;">
                        <!-- Colonne des heures (échelle verticale) -->
                        <div class="time-scale-column" style="height: ${totalHeight}px;">
                            ${this.generateTimeScale(minHour, maxHour, pixelsPerHour)}
                        </div>
                        
                        <!-- Colonnes de contenu (gymnases/semaines) -->
                        <div class="columns-container">
                            ${columns.map((col, idx) => this.generateColumnContent(col, matches, minHour, maxHour, pixelsPerHour, idx, minColWidth, colWidthIncrement)).join('')}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    /**
     * Génère l'échelle horaire verticale
     */
    generateTimeScale(minHour, maxHour, pixelsPerHour) {
        let html = '';
        for (let hour = minHour; hour <= maxHour; hour++) {
            const top = (hour - minHour) * pixelsPerHour;
            html += `
                <div class="time-marker" style="position: absolute; top: ${top}px; left: 0; right: 0;">
                    <span class="time-label">${hour}h</span>
                    <div class="time-line"></div>
                </div>
            `;
        }
        return html;
    }
    
    /**
     * Génère le contenu d'une colonne avec matchs positionnés absolument
     */
    generateColumnContent(column, allMatches, minHour, maxHour, pixelsPerHour, columnIndex, minColWidth, colWidthIncrement) {
        const columnMatches = this.viewManager.getMatchesForColumn(column, allMatches);
        
        // Utiliser le max de slots calculé au lieu de la capacité théorique
        const maxSlots = this.maxSlotsPerColumn.get(column.id) || 1;
        const columnWidth = minColWidth + (maxSlots - 1) * colWidthIncrement;
        
        return `
            <div class="column-content" 
                 data-column="${column.id}"
                 data-column-index="${columnIndex}"
                 data-capacity="${column.capacity || 1}"
                 data-max-slots="${maxSlots}"
                 style="
                     position: relative;
                     width: ${columnWidth}px;
                     height: 100%;
                     flex-shrink: 0;
                     border-right: 1px solid var(--border-color, #dee2e6);
                 ">
                ${this.renderColumnMatches(columnMatches, column, minHour, pixelsPerHour)}
            </div>
        `;
    }
    
    /**
     * Rendu des matchs d'une colonne avec positionnement absolu
     */
    renderColumnMatches(matches, column, minHour, pixelsPerHour) {
        if (!matches || matches.length === 0) {
            return '';
        }
        
        // Grouper les matchs par horaire exact
        const matchesByTime = this.groupMatchesByExactTime(matches);
        
        let html = '';
        matchesByTime.forEach(group => {
            html += this.renderMatchGroup(group, column, minHour, pixelsPerHour);
        });
        
        return html;
    }
    
    /**
     * Groupe les matchs par horaire exact (heure et minute)
     */
    groupMatchesByExactTime(matches) {
        const groups = new Map();
        
        matches.forEach(match => {
            const timeKey = match.horaire || '00:00'; // ex: "18:00", "19:30"
            
            if (!groups.has(timeKey)) {
                groups.set(timeKey, {
                    time: timeKey,
                    matches: []
                });
            }
            groups.get(timeKey).matches.push(match);
        });
        
        const result = Array.from(groups.values());
        return result;
    }
    
    /**
     * Rendu d'un groupe de matchs au même horaire
     */
    renderMatchGroup(group, column, minHour, pixelsPerHour) {
        const capacity = column.capacity || 1;
        const matches = group.matches;
        
        // Calculer la position verticale basée sur l'horaire exact
        const [hours, minutes] = group.time.split(':').map(Number);
        const fractionalHour = hours + (minutes / 60);
        const topPosition = (fractionalHour - minHour) * pixelsPerHour;
        
        // Calculer la hauteur (supposer 2h par défaut, peut être ajusté)
        const matchDuration = 2; // heures
        const matchHeight = matchDuration * pixelsPerHour;
        
        // Détecter les conflits
        const conflicts = this.slotManager.detectConflicts(matches, capacity);
        
        // Calculer la disponibilité
        const available = this.availableSlotsManager.calculateAvailable(matches, capacity);
        
        const isCompact = matches.length >= this.cardRenderer.compactThreshold;
        
        // Générer les cartes de matchs
        const matchCards = matches.map((match, index) => 
            this.cardRenderer.renderMatchCard(match, isCompact, index, true, conflicts)
        ).join('');
        
        // Générer les cartes disponibles
        let availableCards = '';
        if (available > 0 && this.availableSlotsManager.showAvailableSlots) {
            for (let i = 0; i < available; i++) {
                availableCards += `
                    <div class="available-slot-card" 
                         data-slot-index="${i}"
                         title="Terrain disponible - Glisser un match ici">
                        <div class="available-slot-icon">✓</div>
                    </div>
                `;
            }
        }
        
        return `
            <div class="match-group" 
                 data-time="${group.time}"
                 data-column="${column.id}"
                 data-drop-zone="true"
                 style="
                     position: absolute;
                     top: ${topPosition}px;
                     left: 0;
                     right: 0;
                     height: ${matchHeight}px;
                     padding: 4px;
                 ">
                <div class="match-group-content"
                     style="
                         display: flex;
                         flex-direction: row;
                         gap: 8px;
                         align-items: stretch;
                         width: 100%;
                         height: 100%;
                     ">
                    ${matchCards}
                    ${availableCards}
                </div>
            </div>
        `;
    }
    
    /**
     * Génère l'en-tête d'une colonne
     */
    generateColumnHeader(column, minWidth, widthIncrement) {
        const maxSlots = this.maxSlotsPerColumn.get(column.id) || 1;
        const columnWidth = minWidth + (maxSlots - 1) * widthIncrement;
        
        return `
            <div class="column-header header-cell" 
                 style="width: ${columnWidth}px; flex-shrink: 0;"
                 title="${column.sublabel || ''}">
                <span class="column-title">${column.label}</span>
                ${column.sublabel ? `<span class="column-subtitle">${column.sublabel}</span>` : ''}
            </div>
        `;
    }
    
    /**
     * Génère la légende
     */
    generateLegend() {
        const venues = this.dataManager.getGymnases() || [];

        return `
            <div class="grid-legend">
                <div class="legend-section" data-section-id="gymnases">
                    <h4>Gymnases</h4>
                    <div class="legend-items">
                        ${venues.map(v => `
                            <div class="legend-item">
                                <span class="legend-badge" style="background: ${v.color || '#ccc'}; color: white;">${v.id}</span>
                                <span>${v.nom}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
                <div class="legend-section">
                    <h4>Genres</h4>
                    <div class="legend-items">
                        <div class="legend-item">
                            <span class="legend-badge match-male">♂️</span>
                            <span>Masculin</span>
                        </div>
                        <div class="legend-item">
                            <span class="legend-badge match-female">♀️</span>
                            <span>Féminin</span>
                        </div>
                    </div>
                </div>
                
                <div class="legend-section">
                    <h4>Badges</h4>
                    <div class="legend-items">
                        <div class="legend-item">
                            <span class="legend-badge">📌</span>
                            <span>Match fixé</span>
                        </div>
                        <div class="legend-item">
                            <span class="legend-badge">🔗</span>
                            <span>Match externe</span>
                        </div>
                        <div class="legend-item">
                            <span class="legend-badge">🤝</span>
                            <span>Entente</span>
                        </div>
                    </div>
                </div>
                
                <div class="legend-section">
                    <h4>Pénalités</h4>
                    <div class="legend-items">
                        <div class="legend-item">
                            <span class="legend-badge penalty-low">⚡ 0-5</span>
                            <span>Faible</span>
                        </div>
                        <div class="legend-item">
                            <span class="legend-badge penalty-medium">⚡ 5-10</span>
                            <span>Moyenne</span>
                        </div>
                        <div class="legend-item">
                            <span class="legend-badge penalty-high">⚡ 10+</span>
                            <span>Élevée</span>
                        </div>
                    </div>
                </div>
                
                ${this.availableSlotsManager.showAvailableSlots ? `
                <div class="legend-section">
                    <h4>Disponibilité</h4>
                    <div class="legend-items">
                        <div class="legend-item">
                            <span class="legend-badge available-slot-card">✓</span>
                            <span>Terrain libre</span>
                        </div>
                    </div>
                </div>
                ` : ''}
            </div>
        `;
    }
    
    /**
     * Attache les événements
     */
    attachEvents() {
        // Sélecteur de vue
        const modeSelect = this.container.querySelector('#grid-display-mode');
        if (modeSelect) {
            modeSelect.addEventListener('change', (e) => {
                this.viewManager.setDisplayMode(e.target.value);
                this.render();
            });
        }
        
        // Navigation semaine
        const prevWeekBtn = this.container.querySelector('#grid-prev-week');
        if (prevWeekBtn) {
            prevWeekBtn.addEventListener('click', () => {
                if (this.viewManager.previousWeek()) {
                    this.render();
                }
            });
        }
        
        const nextWeekBtn = this.container.querySelector('#grid-next-week');
        if (nextWeekBtn) {
            nextWeekBtn.addEventListener('click', () => {
                if (this.viewManager.nextWeek()) {
                    this.render();
                }
            });
        }
        
        // Toggle créneaux disponibles
        const showAvailableCheckbox = this.container.querySelector('#grid-show-available');
        if (showAvailableCheckbox) {
            showAvailableCheckbox.addEventListener('change', (e) => {
                this.availableSlotsManager.setShow(e.target.checked);
                this.render();
            });
        }
        
        // Filtres rapides
        const genderFilter = this.container.querySelector('#filter-gender');
        if (genderFilter) {
            genderFilter.addEventListener('change', (e) => {
                this.filters.gender = e.target.value;
                this.render();
            });
        }
        
        const teamFilter = this.container.querySelector('#filter-team');
        if (teamFilter) {
            teamFilter.addEventListener('input', (e) => {
                this.filters.team = e.target.value;
                this.render();
            });
        }
        
        // Clic sur les cartes de match
        this.container.querySelectorAll('[data-match-id]').forEach(card => {
            card.addEventListener('click', (e) => {
                // Ne pas ouvrir si on commence un drag
                if (e.target.closest('.match-card').classList.contains('dragging')) {
                    return;
                }
                
                const matchId = card.dataset.matchId;
                const match = this.dataManager.getMatch(matchId);
                if (match && window.editModal) {
                    window.editModal.open(match);
                }
            });
        });
    }
    
    /**
     * Met à jour les filtres externes
     */
    updateFilters(filters) {
        this.filters = { ...this.filters, ...filters };
        this.render();
    }
}

// Export
window.AgendaGridView = AgendaGridView;
