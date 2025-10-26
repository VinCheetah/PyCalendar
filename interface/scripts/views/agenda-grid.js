/**
 * AgendaGridView - Vue en grille horaire type planning
 * Heures en vertical, gymnases/semaines en horizontal
 * Chaque match occupe précisément son créneau de 2h
 * 
 * Architecture modulaire:
 * - SlotManager: Gestion des créneaux et organisation des matchs
 * - MatchCardRenderer: Rendu des cartes de matchs
 */

class AgendaGridView {
    constructor(dataManager, container) {
        this.dataManager = dataManager;
        this.container = container;
        
        // Modules utilitaires
        this.slotManager = new SlotManager();
        this.cardRenderer = new MatchCardRenderer();
        
        // Configuration de la grille
        this.matchDurationHours = 2; // Durée d'un match en heures
        this.minHour = 8;  // Heure de début (sera calculé dynamiquement)
        this.maxHour = 22; // Heure de fin (sera calculé dynamiquement)
        this.hourStep = 2; // Pas de la grille (2h pour correspondre à la durée des matchs)
        
        // Options d'affichage
        this.showEmptySlots = true;
        this.showConflicts = false; // Masquer les conflits par défaut
        this.displayMode = 'venues'; // 'venues' ou 'weeks'
        this.currentWeek = null;
        this.availableWeeks = []; // Liste des semaines disponibles
        
        // Filtres actifs
        this.filters = {
            week: null,
            gender: '',
            institution: '',
            pool: '',
            venue: ''
        };
    }
    
    /**
     * Initialise la vue
     */
    init() {
        this.render();
    }
    
    /**
     * Calcule la plage horaire à afficher basée sur les données
     */
    calculateTimeRange(matches) {
        if (!matches || matches.length === 0) {
            return { minHour: 8, maxHour: 22 };
        }
        
        const hours = matches
            .map(m => m.horaire)
            .filter(h => h)
            .map(h => {
                const parts = h.split(':');
                return parseInt(parts[0]);
            });
        
        if (hours.length === 0) {
            return { minHour: 8, maxHour: 22 };
        }
        
        const min = Math.min(...hours);
        const max = Math.max(...hours) + this.matchDurationHours;
        
        // Arrondir pour avoir des heures pleines
        this.minHour = Math.max(6, Math.floor(min / 2) * 2);
        this.maxHour = Math.min(24, Math.ceil(max / 2) * 2);
    }
    
    /**
     * Obtient les colonnes (gymnases ou semaines)
     */
    getColumns(matches) {
        if (this.displayMode === 'venues') {
            // Récupérer tous les gymnases
            const venueIds = [...new Set(matches.map(m => m.gymnase))].filter(v => v);
            return venueIds.map(id => {
                const venue = this.dataManager.getGymnaseById(id);
                return {
                    id: id,
                    label: venue?.nom || id,
                    type: 'venue'
                };
            }).sort((a, b) => a.label.localeCompare(b.label));
        } else {
            // Récupérer toutes les semaines
            const weeks = [...new Set(matches.map(m => m.semaine))].filter(w => w);
            return weeks.sort((a, b) => a - b).map(w => ({
                id: w,
                label: `Semaine ${w}`,
                type: 'week'
            }));
        }
    }
    
    /**
     * Filtre les matchs selon les critères actifs
     */
    filterMatches(matches) {
        let filtered = [...matches];
        
        if (this.filters.week) {
            filtered = filtered.filter(m => m.semaine == this.filters.week);
        }
        
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
        
        return filtered;
    }
    
    /**
     * Convertit une heure HH:MM en index de ligne
     */
    timeToRow(timeStr) {
        const [hours, minutes] = timeStr.split(':').map(Number);
        const totalMinutes = (hours - this.minHour) * 60 + minutes;
        return totalMinutes / (this.hourStep * 60);
    }
    
    /**
     * Rend la vue
     */
    render() {
        const data = this.dataManager.getData();
        if (!data || !data.matches) {
            this.container.innerHTML = '<div class="empty-state">Aucune donnée disponible</div>';
            return;
        }
        
        const allMatches = data.matches.scheduled || [];
        
        // Mettre à jour la liste des semaines disponibles
        this.availableWeeks = [...new Set(allMatches.map(m => m.semaine))].filter(w => w).sort((a, b) => a - b);
        
        // Si aucune semaine n'est sélectionnée, prendre la première
        if (this.currentWeek === null && this.availableWeeks.length > 0) {
            this.currentWeek = this.availableWeeks[0];
        }
        
        // Filtrer par semaine courante si en mode "Par gymnase"
        let filteredMatches = allMatches;
        if (this.displayMode === 'venues' && this.currentWeek !== null) {
            filteredMatches = allMatches.filter(m => m.semaine === this.currentWeek);
        } else {
            filteredMatches = this.filterMatches(allMatches);
        }
        
        // Calculer la plage horaire
        this.calculateTimeRange(allMatches);
        
        // Obtenir les colonnes
        const columns = this.getColumns(this.displayMode === 'venues' ? filteredMatches : allMatches);
        
        // Générer le HTML
        this.container.innerHTML = this.generateHTML(filteredMatches, columns, data);
        
        // Attacher les événements
        this.attachEvents();
    }
    
    /**
     * Génère le HTML de la grille
     */
    generateHTML(matches, columns, data) {
        const hours = this.generateHours();
        
        return `
            <div class="agenda-grid-view">
                <!-- Barre d'options -->
                ${this.generateToolbar(matches)}
                
                <!-- Conteneur de la grille avec scroll -->
                <div class="grid-container">
                    <!-- Grille horaire -->
                    <div class="time-grid">
                        <!-- En-tête avec les colonnes -->
                        <div class="grid-header">
                            <div class="time-column-header">
                                <span class="hour-label">Heure</span>
                            </div>
                            ${columns.map(col => `
                                <div class="column-header" data-column-id="${col.id}">
                                    <span class="column-label">${col.label}</span>
                                    <span class="column-count">${this.countMatchesInColumn(matches, col)}</span>
                                </div>
                            `).join('')}
                        </div>
                        
                        <!-- Corps de la grille -->
                        <div class="grid-body">
                            <!-- Colonne des heures -->
                            <div class="time-column">
                                ${hours.map(hour => `
                                    <div class="time-slot" data-hour="${hour}">
                                        <span class="time-label">${hour}:00</span>
                                    </div>
                                `).join('')}
                            </div>
                            
                            <!-- Colonnes de données -->
                            ${columns.map(col => this.generateColumn(col, matches, hours, data)).join('')}
                        </div>
                    </div>
                </div>
                
                <!-- Légende -->
                ${this.generateLegend(data)}
            </div>
        `;
    }
    
    /**
     * Génère la barre d'outils
     */
    generateToolbar(matches) {
        const data = this.dataManager.getData();
        const currentIndex = this.availableWeeks.indexOf(this.currentWeek);
        const hasPrevious = currentIndex > 0;
        const hasNext = currentIndex < this.availableWeeks.length - 1;
        
        return `
            <div class="grid-toolbar">
                <div class="toolbar-section">
                    <label class="toolbar-label">
                        <span>Mode d'affichage:</span>
                        <select id="grid-display-mode" class="toolbar-select">
                            <option value="venues" ${this.displayMode === 'venues' ? 'selected' : ''}>Par gymnase</option>
                            <option value="weeks" ${this.displayMode === 'weeks' ? 'selected' : ''}>Par semaine</option>
                        </select>
                    </label>
                </div>
                
                ${this.displayMode === 'venues' ? `
                <div class="toolbar-section week-navigation">
                    <button id="grid-prev-week" class="week-nav-btn" ${!hasPrevious ? 'disabled' : ''}>
                        ◀ Précédent
                    </button>
                    <span class="current-week-label">Semaine ${this.currentWeek}</span>
                    <button id="grid-next-week" class="week-nav-btn" ${!hasNext ? 'disabled' : ''}>
                        Suivant ▶
                    </button>
                </div>
                ` : ''}
                
                <div class="toolbar-section">
                    <label class="toolbar-checkbox">
                        <input type="checkbox" id="grid-show-empty" ${this.showEmptySlots ? 'checked' : ''}>
                        <span>Afficher les créneaux vides</span>
                    </label>
                </div>
                
                <div class="toolbar-section">
                    <label class="toolbar-checkbox">
                        <input type="checkbox" id="grid-show-conflicts" ${this.showConflicts ? 'checked' : ''}>
                        <span>Afficher les conflits</span>
                    </label>
                </div>
                
                <div class="toolbar-section toolbar-info">
                    <span class="info-badge">
                        ${matches.length} match${matches.length > 1 ? 's' : ''}
                    </span>
                </div>
            </div>
        `;
    }
    
    /**
     * Génère les heures de la grille
     */
    generateHours() {
        const hours = [];
        for (let h = this.minHour; h < this.maxHour; h += this.hourStep) {
            hours.push(h);
        }
        return hours;
    }
    
    /**
     * Compte les matchs dans une colonne
     */
    countMatchesInColumn(matches, column) {
        if (column.type === 'venue') {
            return matches.filter(m => m.gymnase === column.id).length;
        } else {
            return matches.filter(m => m.semaine === column.id).length;
        }
    }
    
    /**
     * Génère une colonne de la grille avec gestion optimisée des matchs simultanés
     */
    generateColumn(column, matches, hours, data) {
        // Filtrer les matchs de cette colonne
        const columnMatches = column.type === 'venue' ?
            matches.filter(m => m.gymnase === column.id) :
            matches.filter(m => m.semaine === column.id);
        
        // Récupérer la capacité du gymnase pour ce column
        const capacity = column.type === 'venue' 
            ? (data.entities?.gymnases?.find(g => g.nom === column.id)?.capacite || 1)
            : 1;
        
        // Créer la grille horaire avec organisation optimale des matchs
        const slots = hours.map(hour => {
            const slotMatches = columnMatches.filter(m => {
                if (!m.horaire) return false;
                const matchHour = parseInt(m.horaire.split(':')[0]);
                return matchHour === hour;
            });
            
            // Utiliser le SlotManager pour organiser les matchs
            const slotOrganization = this.slotManager.organizeSlotMatches(slotMatches, capacity);
            const conflicts = this.slotManager.detectConflicts(slotMatches, capacity);
            
            return {
                hour,
                ...slotOrganization,
                conflicts
            };
        });
        
        return `
            <div class="data-column" data-column-id="${column.id}" data-capacity="${capacity}">
                ${slots.map(slot => this.generateSlot(slot, column, data)).join('')}
            </div>
        `;
    }
    
    /**
     * Détecte et analyse les types de conflits pour un créneau
     * Prend en compte la capacité du gymnase
     */
    analyzeConflicts(matches, column, data) {
        const conflicts = {
            types: [],
            severity: 'none',
            description: []
        };
        
        if (matches.length <= 1) {
            return conflicts;
        }
        
        // Récupérer la capacité du gymnase
        const gymnase = data.entities?.gymnases?.find(g => g.nom === column.id);
        const capacity = gymnase?.capacite || 1;
        
        // 1. Vérifier si la capacité est dépassée
        if (matches.length > capacity) {
            conflicts.types.push('venue_capacity');
            conflicts.severity = 'critical';
            conflicts.description.push(`🏟️ <strong>Capacité dépassée !</strong> ${matches.length} matchs sur <strong>${column.label}</strong> (capacité: ${capacity} terrain${capacity > 1 ? 's' : ''})`);
        } else {
            // Pas de conflit de capacité, juste une info
            conflicts.severity = 'info';
            conflicts.description.push(`ℹ️ ${matches.length} matchs simultanés sur <strong>${column.label}</strong> (capacité: ${capacity} terrains)`);
        }
        
        // 2. Vérifier les conflits d'équipes (équipe qui joue 2 fois en même temps)
        const teamIds = [];
        const duplicateTeams = new Set();
        
        matches.forEach(match => {
            if (teamIds.includes(match.equipe1_id)) {
                duplicateTeams.add(match.equipe1_nom);
            } else {
                teamIds.push(match.equipe1_id);
            }
            
            if (teamIds.includes(match.equipe2_id)) {
                duplicateTeams.add(match.equipe2_nom);
            } else {
                teamIds.push(match.equipe2_id);
            }
        });
        
        if (duplicateTeams.size > 0) {
            conflicts.types.push('team_simultaneous');
            if (conflicts.severity === 'none' || conflicts.severity === 'info') {
                conflicts.severity = 'critical';
            }
            const teams = [...duplicateTeams].join(', ');
            conflicts.description.push(`⚠️ <strong>Conflit d'équipe !</strong> Équipe(s) jouant simultanément: <strong>${teams}</strong>`);
        }
        
        // 3. Vérifier les conflits d'institutions (overlap)
        const institutions = {};
        matches.forEach(match => {
            const inst1 = match.equipe1_institution;
            const inst2 = match.equipe2_institution;
            
            if (!institutions[inst1]) institutions[inst1] = 0;
            if (!institutions[inst2]) institutions[inst2] = 0;
            institutions[inst1]++;
            institutions[inst2]++;
        });
        
        const overlapInstitutions = Object.entries(institutions)
            .filter(([inst, count]) => count > 1)
            .map(([inst, count]) => `${inst} (×${count})`);
        
        if (overlapInstitutions.length > 0) {
            conflicts.types.push('institution_overlap');
            conflicts.description.push(`� Institutions en conflit: <strong>${overlapInstitutions.join(', ')}</strong>`);
        }
        
        return conflicts;
    }
    
    /**
     * Génère le descriptif HTML des conflits avec détails
     */
    generateConflictDetails(matches, column, data) {
        const analysis = this.analyzeConflicts(matches, column, data);
        
        if (analysis.description.length === 0) {
            return '<p class="conflict-desc-item">Conflit de planification détecté</p>';
        }
        
        // Appliquer une classe CSS selon la sévérité
        const severityClass = analysis.severity === 'critical' ? 'conflict-critical' : 
                             analysis.severity === 'info' ? 'conflict-info' : '';
        
        return `<div class="conflict-details-wrapper ${severityClass}">` +
            analysis.description.map(desc => 
                `<p class="conflict-desc-item">${desc}</p>`
            ).join('') +
            `</div>`;
    }
    
    /**
     * Calcule la hauteur optimale pour afficher les matchs côte à côte
     */
    calculateSlotHeight(matchCount) {
        // Hauteur de base du slot: 120px
        // Pour plusieurs matchs: on les affiche côte à côte, donc même hauteur mais on agrandit si nécessaire
        // Si plus de 2 matchs, on passe en mode grille 2 colonnes
        const baseHeight = 120;
        
        if (matchCount <= 2) {
            return baseHeight;
        } else {
            // Pour 3-4 matchs: 2 rangées
            // Pour 5-6 matchs: 3 rangées, etc.
            const rows = Math.ceil(matchCount / 2);
            return rows * baseHeight;
        }
    }
    
    /**
     * Génère un créneau (slot) de la grille avec rendu optimisé
     */
    generateSlot(slot, column, data) {
        // Slot vide
        if (slot.isEmpty) {
            if (!this.showEmptySlots) {
                return `<div class="grid-slot empty-slot hidden" data-hour="${slot.hour}"></div>`;
            }
            return `
                <div class="grid-slot empty-slot" data-hour="${slot.hour}">
                    <div class="empty-indicator">+</div>
                </div>
            `;
        }
        
        const { matches, matchCount, capacity, isOverCapacity, layout, columns, conflicts } = slot;
        
        // Calculer la hauteur du slot
        const slotHeight = this.slotManager.calculateSlotHeight(matchCount);
        
        // Un seul match - affichage simple
        if (matchCount === 1) {
            return `
                <div class="grid-slot occupied-slot single-match" data-hour="${slot.hour}">
                    ${this.cardRenderer.renderMatchCard(matches[0], false)}
                </div>
            `;
        }
        
        // Matchs multiples
        const shouldShowConflicts = this.showConflicts;
        
        // Si on n'affiche pas les conflits et qu'il y en a plusieurs, montrer juste le premier
        if (!shouldShowConflicts && matchCount > 1) {
            return `
                <div class="grid-slot occupied-slot has-hidden-matches" 
                     data-hour="${slot.hour}" 
                     title="⚠️ ${matchCount} matchs à ce créneau (activez 'Afficher les conflits')">
                    ${this.cardRenderer.renderMatchCard(matches[0], false)}
                    <div class="hidden-matches-indicator" 
                         title="Cliquez sur 'Afficher les conflits' pour voir tous les matchs">
                        +${matchCount - 1}
                    </div>
                </div>
            `;
        }
        
        // Affichage complet des matchs multiples côte à côte
        const severityClass = isOverCapacity ? 'slot-over-capacity' : 'slot-multi-match';
        const isCompact = matchCount >= this.cardRenderer.compactThreshold;
        
        return `
            <div class="grid-slot ${severityClass} layout-${layout}" 
                 data-hour="${slot.hour}" 
                 data-match-count="${matchCount}"
                 data-capacity="${capacity}"
                 style="min-height: ${slotHeight}px;">
                
                <!-- En-tête du slot avec infos -->
                <div class="slot-header">
                    <div class="slot-badge ${isOverCapacity ? 'badge-critical' : 'badge-info'}">
                        <span class="slot-icon">${isOverCapacity ? '⚠️' : 'ℹ️'}</span>
                        <span class="slot-count">${matchCount} MATCH${matchCount > 1 ? 'S' : ''}</span>
                        ${capacity > 1 ? `<span class="slot-capacity">/ ${capacity} terrain${capacity > 1 ? 's' : ''}</span>` : ''}
                    </div>
                </div>
                
                <!-- Détails des conflits si présents -->
                ${conflicts.hasConflict ? this.renderConflictDetails(conflicts) : ''}
                
                <!-- Grille des matchs côte à côte -->
                <div class="slot-matches-grid" 
                     data-layout="${layout}"
                     style="grid-template-columns: repeat(${columns}, 1fr);">
                    ${matches.map((match, idx) => `
                        <div class="slot-match-item" data-match-index="${idx}">
                            ${this.cardRenderer.renderMatchCard(match, isCompact, idx)}
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    /**
     * Rendu des détails de conflits
     */
    renderConflictDetails(conflicts) {
        if (!conflicts.hasConflict || conflicts.details.length === 0) {
            return '';
        }
        
        return `
            <div class="slot-conflicts severity-${conflicts.severity}">
                ${conflicts.details.map(detail => `
                    <div class="conflict-item type-${detail.type}">
                        <span class="conflict-icon">${detail.icon}</span>
                        <span class="conflict-message">${detail.message}</span>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    /**
     * Génère le détail des pénalités pour tooltip
     */
    generatePenaltyTooltip(match) {
        if (!match.penalties) return 'Aucune pénalité';
        
        const penalties = match.penalties;
        const parts = [];
        
        if (penalties.horaire_prefere > 0) {
            parts.push(`⏰ Horaire non préféré: ${penalties.horaire_prefere.toFixed(1)}`);
        }
        if (penalties.espacement > 0) {
            parts.push(`📅 Espacement insuffisant: ${penalties.espacement.toFixed(1)}`);
        }
        if (penalties.indisponibilite > 0) {
            parts.push(`🚫 Indisponibilité: ${penalties.indisponibilite.toFixed(1)}`);
        }
        if (penalties.compaction > 0) {
            parts.push(`📦 Compaction: ${penalties.compaction.toFixed(1)}`);
        }
        if (penalties.overlap > 0) {
            parts.push(`🏫 Conflit institution: ${penalties.overlap.toFixed(1)}`);
        }
        
        if (parts.length === 0) {
            return 'Aucune pénalité';
        }
        
        return parts.join('\n');
    }
    
    /**
     * Génère une carte de match compacte pour la grille
     */
    generateMatchCard(match, data, isCompact) {
        const poule = this.dataManager.getPouleById(match.poule);
        const genderIcon = match.equipe1_genre === 'M' ? '♂️' : match.equipe1_genre === 'F' ? '♀️' : '⚥';
        const genderClass = match.equipe1_genre === 'M' ? 'male' : 'female';
        
        const totalPenalties = Object.values(match.penalties || {}).reduce((sum, p) => sum + (typeof p === 'number' ? p : 0), 0);
        const penaltyClass = totalPenalties > 10 ? 'high' : totalPenalties > 5 ? 'medium' : 'low';
        const penaltyTooltip = this.generatePenaltyTooltip(match);
        
        if (isCompact) {
            return `
                <div class="match-card-mini ${genderClass}" data-match-id="${match.match_id}">
                    <div class="mini-teams">
                        ${match.equipe1_nom} vs ${match.equipe2_nom}
                    </div>
                    <div class="mini-penalty penalty-${penaltyClass}" title="${penaltyTooltip}">${totalPenalties.toFixed(1)}</div>
                </div>
            `;
        }
        
        return `
            <div class="match-card-grid ${genderClass}" data-match-id="${match.match_id}" title="Cliquer pour éditer">
                <div class="card-header-grid">
                    <span class="card-gender">${genderIcon}</span>
                    <span class="card-pool">${poule?.nom || match.poule}</span>
                    <span class="card-penalty penalty-${penaltyClass}" title="${penaltyTooltip}">⚠️ ${totalPenalties.toFixed(1)}</span>
                </div>
                
                <div class="card-teams-grid">
                    <div class="team-name" title="${match.equipe1_nom_complet || match.equipe1_nom}">${match.equipe1_nom}</div>
                    <div class="vs-divider">VS</div>
                    <div class="team-name" title="${match.equipe2_nom_complet || match.equipe2_nom}">${match.equipe2_nom}</div>
                </div>
                
                ${this.displayMode === 'weeks' ? `
                <div class="card-venue">
                    📍 ${match.gymnase}
                </div>
                ` : ''}
            </div>
        `;
    }
    
    /**
     * Génère la légende
     */
    generateLegend(data) {
        return `
            <div class="grid-legend">
                <div class="legend-item">
                    <div class="legend-color male-color"></div>
                    <span>Masculin</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color female-color"></div>
                    <span>Féminin</span>
                </div>
                <div class="legend-item">
                    <div class="legend-badge penalty-low">0-5</div>
                    <span>Pénalité faible</span>
                </div>
                <div class="legend-item">
                    <div class="legend-badge penalty-medium">5-10</div>
                    <span>Pénalité moyenne</span>
                </div>
                <div class="legend-item">
                    <div class="legend-badge penalty-high">10+</div>
                    <span>Pénalité élevée</span>
                </div>
                ${this.showEmptySlots ? `
                <div class="legend-item">
                    <div class="legend-icon">+</div>
                    <span>Créneau disponible</span>
                </div>
                ` : ''}
            </div>
        `;
    }
    
    /**
     * Attache les événements
     */
    attachEvents() {
        // Mode d'affichage
        const modeSelect = this.container.querySelector('#grid-display-mode');
        if (modeSelect) {
            modeSelect.addEventListener('change', (e) => {
                this.displayMode = e.target.value;
                this.render();
            });
        }
        
        // Navigation semaine précédente
        const prevWeekBtn = this.container.querySelector('#grid-prev-week');
        if (prevWeekBtn) {
            prevWeekBtn.addEventListener('click', () => {
                const currentIndex = this.availableWeeks.indexOf(this.currentWeek);
                if (currentIndex > 0) {
                    this.currentWeek = this.availableWeeks[currentIndex - 1];
                    this.render();
                }
            });
        }
        
        // Navigation semaine suivante
        const nextWeekBtn = this.container.querySelector('#grid-next-week');
        if (nextWeekBtn) {
            nextWeekBtn.addEventListener('click', () => {
                const currentIndex = this.availableWeeks.indexOf(this.currentWeek);
                if (currentIndex < this.availableWeeks.length - 1) {
                    this.currentWeek = this.availableWeeks[currentIndex + 1];
                    this.render();
                }
            });
        }
        
        // Afficher créneaux vides
        const showEmptyCheckbox = this.container.querySelector('#grid-show-empty');
        if (showEmptyCheckbox) {
            showEmptyCheckbox.addEventListener('change', (e) => {
                this.showEmptySlots = e.target.checked;
                this.render();
            });
        }
        
        // Afficher les conflits
        const showConflictsCheckbox = this.container.querySelector('#grid-show-conflicts');
        if (showConflictsCheckbox) {
            showConflictsCheckbox.addEventListener('change', (e) => {
                this.showConflicts = e.target.checked;
                this.render();
            });
        }
        
        // Clic sur les cartes de match
        this.container.querySelectorAll('[data-match-id]').forEach(card => {
            card.addEventListener('click', (e) => {
                const matchId = card.dataset.matchId;
                const data = this.dataManager.getData();
                const match = data.matches.scheduled.find(m => m.match_id === matchId);
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
