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
        this.dragDropManager = new DragDropManager(
            dataManager,
            window.modificationManager
        );
        
        // Callbacks du drag & drop
        this.dragDropManager.onModification = () => this.render();
        
        // Filtres actifs
        this.filters = {
            institution: '',
            pool: '',
            venue: '',
            team: '',
            gender: ''
        };
        
        // Options d'affichage
        this.displayOptions = {
            matchColor: 'by-venue',
            cardSize: 'md',
            showVenues: true,
            showTimes: true,
            showPools: true,
            showTeams: true,
            showConflicts: false,
            compactMode: false,
            highlightWeekends: true,
            animations: true,
            gridDensity: 'normal',
            timeFormat: '24h'
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
            const data = this.dataManager.getData();
            if (!data || !data.matches) {
                this.container.innerHTML = '<div class="empty-state">Aucune donnée disponible</div>';
                return;
            }
            
            const allMatches = data.matches.scheduled || [];
            const filteredMatches = this.filterMatches(allMatches);
            
            // Calculer la plage horaire dynamique
            this.viewManager.calculateTimeRange(filteredMatches);
            
            // Obtenir les colonnes selon le mode d'affichage
            const columns = this.viewManager.getColumns(filteredMatches);
            
            // Calculer le max de slots simultanés par colonne
            this.maxSlotsPerColumn = this.calculateMaxSimultaneousSlotsPerColumn(columns, filteredMatches);
            
            // Générer le HTML
            this.container.innerHTML = this.generateHTML(filteredMatches, columns, data);
            
            // Initialiser le drag & drop
            this.dragDropManager.initializeDragDrop(this.container);
            
            // Attacher les événements
            this.attachEvents();
            
        } catch (error) {
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
                    <!-- Navigation semaine (mode gymnase uniquement) -->
                    ${navData.mode === 'venues' ? `
                    <div class="toolbar-group toolbar-navigation">
                        <button id="grid-prev-week" 
                                class="btn btn-icon btn-secondary" 
                                ${!navData.hasPrevious ? 'disabled' : ''}
                                title="Semaine précédente"
                                aria-label="Semaine précédente">
                            ◄
                        </button>
                        <span class="navigation-label">${navData.currentLabel}</span>
                        <button id="grid-next-week" 
                                class="btn btn-icon btn-secondary"
                                ${!navData.hasNext ? 'disabled' : ''}
                                title="Semaine suivante"
                                aria-label="Semaine suivante">
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
                            <span class="stat-icon">🎯</span>
                            <strong>${stats.visibleMatches}</strong> match${stats.visibleMatches > 1 ? 's' : ''}
                        </span>
                        <span class="stat-separator">•</span>
                        <span class="stat-item">
                            <span class="stat-icon">${this.viewManager.displayMode === 'venues' ? '🏟️' : '📅'}</span>
                            <strong>${stats.totalColumns}</strong> ${this.viewManager.displayMode === 'venues' ? 'gymnase' : 'semaine'}${stats.totalColumns > 1 ? 's' : ''}
                        </span>
                        <span class="stat-separator">•</span>
                        <span class="stat-item">
                            <span class="stat-icon">🕒</span>
                            ${stats.timeRange}
                        </span>
                        ${stats.totalMatches !== stats.visibleMatches ? `
                        <span class="stat-separator">•</span>
                        <span class="stat-item stat-filtered">
                            (${stats.totalMatches} total)
                        </span>
                        ` : ''}
                    </div>
                </div>
                
                <div class="toolbar-right">
                    <!-- Toolbar simplifiée - les options sont dans le panneau latéral -->
                </div>
            </div>
        `;
    }
    
    /**
     * Génère la grille complète avec les colonnes
     */
    generateGrid(matches, columns) {
        // Calculer la largeur de colonne optimisée
        const minColWidth = 180; // Largeur minimale augmentée pour éviter les coupures
        const colWidthIncrement = 160; // Augmentation par slot supplémentaire
        
        // Paramètres de l'échelle horaire
        const minHour = this.viewManager.minHour; // ex: 8
        const maxHour = this.viewManager.maxHour; // ex: 23
        const pixelsPerHour = 100; // Hauteur augmentée pour plus d'espace vertical
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
        
        // Calculer la hauteur avec plus d'espace
        const matchDuration = 2; // heures
        const matchHeight = matchDuration * pixelsPerHour - 8; // Marge entre les groupes
        
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
                     padding: 0.25rem;
                 ">
                <div class="match-group-content">
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
     * Attache les événements
     */
    attachEvents() {
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
     * Met à jour les filtres externes depuis le panneau latéral
     */
    updateFilters(filters) {
        this.filters = { ...this.filters, ...filters };
        this.render();
    }
    
    /**
     * Retourne la configuration des options d'affichage pour cette vue.
     * Options réellement fonctionnelles et utiles pour la vue Agenda.
     */
    getDisplayOptions() {
        return {
            title: "Options - Vue Agenda",
            options: [
                // Mode d'affichage (gymnase vs semaine) - FONCTIONNEL
                {
                    type: 'button-group',
                    id: 'agenda-display-mode',
                    label: '📊 Organiser par',
                    values: [
                        { value: 'venue', text: 'Gymnase' },
                        { value: 'week', text: 'Semaine' }
                    ],
                    default: this.viewManager.displayMode || 'venue',
                    action: (value) => {
                        this.setDisplayMode(value);
                    }
                },
                
                // Coloration des matchs - NOUVEAU
                {
                    type: 'select',
                    id: 'agenda-color-scheme',
                    label: '🎨 Coloration des matchs',
                    values: [
                        { value: 'none', text: 'Aucune' },
                        { value: 'by-status', text: 'Par statut' },
                        { value: 'by-venue', text: 'Par lieu' },
                        { value: 'by-gender', text: 'Par genre' },
                        { value: 'by-level', text: 'Par niveau' }
                    ],
                    default: this.colorScheme || 'none',
                    action: (value) => {
                        this.applyColorScheme(value);
                    }
                },
                
                // Afficher les créneaux disponibles - FONCTIONNEL
                {
                    type: 'checkbox',
                    id: 'agenda-show-available',
                    label: '🆓 Afficher créneaux libres',
                    default: this.availableSlotsManager.showAvailableSlots !== false,
                    action: (checked) => {
                        this.setShowAvailableSlots(checked);
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
        this.colorScheme = scheme;
        
        // Appliquer l'attribut data-color-scheme sur le conteneur
        if (scheme === 'none') {
            this.container.removeAttribute('data-color-scheme');
        } else {
            this.container.setAttribute('data-color-scheme', scheme);
        }
        
        // Sauvegarder la préférence
        localStorage.setItem('agenda-color-scheme', scheme);
        
        // Re-render pour appliquer les changements
        this.render();
    }
    
    /**
     * Met à jour le mode d'affichage depuis le panneau latéral
     */
    setDisplayMode(mode) {
        this.viewManager.setDisplayMode(mode);
        this.render();
    }
    
    /**
     * Met à jour l'affichage des créneaux disponibles depuis le panneau latéral
     */
    setShowAvailableSlots(show) {
        this.availableSlotsManager.setShow(show);
        this.render();
    }
}

// Export
window.AgendaGridView = AgendaGridView;
