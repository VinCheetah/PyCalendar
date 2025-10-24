/**
 * SimpleAgendaView - Nouvelle vue Google Agenda simplifiée
 * Version épurée avec positionnement clair et simple
 */

class SimpleAgendaView {
    constructor() {
        this.currentWeek = 1;
        this.matchDuration = 120; // minutes (2 heures)
        this.slotHeight = 100; // pixels par heure (augmenté de 60 à 100 pour plus d'espace)
    }

    /**
     * Point d'entrée principal - Rend la vue
     */
    render(container, allMatches, filters, preferences) {
        console.log('🆕 SimpleAgendaView - Rendu de', allMatches.length, 'matchs');
        
        // Filtrer les matchs pour la semaine courante
        const weekMatches = this.filterByWeek(allMatches, this.currentWeek);
        
        // Construire le HTML
        const html = this.buildHTML(allMatches, weekMatches, filters, preferences);
        
        // Injecter dans le container
        container.innerHTML = html;
        
        // Attacher les événements
        this.attachEvents(container, allMatches, filters, preferences);
    }

    /**
     * Filtre les matchs par semaine
     */
    filterByWeek(matches, week) {
        return matches.filter(m => m.semaine == week);
    }

    /**
     * Construit le HTML complet de la vue
     */
    buildHTML(allMatches, weekMatches, filters, preferences) {
        let html = '<div class="simple-agenda-container">';
        
        // Navigation
        html += this.buildNavigation(allMatches);
        
        // Grille principale
        html += this.buildGrid(weekMatches);
        
        html += '</div>';
        return html;
    }

    /**
     * Construit la barre de navigation
     */
    buildNavigation(allMatches) {
        const weeks = [...new Set(allMatches.map(m => m.semaine))].sort((a, b) => a - b);
        const minWeek = weeks[0] || 1;
        const maxWeek = weeks[weeks.length - 1] || 1;
        const canGoPrev = this.currentWeek > minWeek;
        const canGoNext = this.currentWeek < maxWeek;
        
        return `
            <div class="simple-agenda-nav">
                <button class="btn-nav btn-prev" ${canGoPrev ? '' : 'disabled'} onclick="SimpleAgendaView.instance.previousWeek()">
                    ◀ Précédent
                </button>
                <div class="week-display">
                    <span class="week-label">Semaine</span>
                    <span class="week-number">${this.currentWeek}</span>
                </div>
                <button class="btn-nav btn-next" ${canGoNext ? '' : 'disabled'} onclick="SimpleAgendaView.instance.nextWeek()">
                    Suivant ▶
                </button>
            </div>
        `;
    }

    /**
     * Construit la grille avec les matchs
     */
    buildGrid(weekMatches) {
        if (weekMatches.length === 0) {
            return `
                <div class="simple-agenda-empty">
                    <div class="empty-icon">📅</div>
                    <div class="empty-text">Aucun match cette semaine</div>
                </div>
            `;
        }
        
        // Grouper par gymnase
        const byVenue = this.groupByVenue(weekMatches);
        const venues = Object.keys(byVenue).sort();
        
        // Calculer la plage horaire
        const timeRange = this.calculateTimeRange(weekMatches);
        
        let html = '<div class="simple-agenda-grid">';
        
        // En-têtes des colonnes (gymnases)
        html += '<div class="agenda-headers">';
        html += '<div class="agenda-time-header">Horaire</div>';
        venues.forEach(venue => {
            const count = byVenue[venue].length;
            html += `
                <div class="agenda-venue-header">
                    <div class="venue-name">🏢 ${venue}</div>
                    <div class="venue-count">${count} match${count > 1 ? 's' : ''}</div>
                </div>
            `;
        });
        html += '</div>';
        
        // Grille avec timeline et colonnes
        html += '<div class="agenda-grid-content">';
        
        // Colonne timeline (horaires)
        html += this.buildTimeline(timeRange);
        
        // Colonnes des gymnases
        venues.forEach(venue => {
            html += this.buildVenueColumn(byVenue[venue], timeRange);
        });
        
        html += '</div>';
        html += '</div>';
        
        return html;
    }

    /**
     * Groupe les matchs par gymnase
     */
    groupByVenue(matches) {
        const grouped = {};
        matches.forEach(match => {
            const venue = match.gymnase || 'Non assigné';
            if (!grouped[venue]) {
                grouped[venue] = [];
            }
            grouped[venue].push(match);
        });
        return grouped;
    }

    /**
     * Calcule la plage horaire (min/max)
     */
    calculateTimeRange(matches) {
        const times = matches.map(m => this.parseTime(m.horaire)).filter(t => t !== null);
        
        if (times.length === 0) {
            return { startHour: 8, endHour: 22 };
        }
        
        const minMinutes = Math.min(...times);
        const maxMinutes = Math.max(...times);
        
        // Arrondir aux heures
        const startHour = Math.floor(minMinutes / 60);
        const endHour = Math.ceil((maxMinutes + this.matchDuration) / 60);
        
        return {
            startHour: Math.max(6, startHour),
            endHour: Math.min(24, endHour)
        };
    }

    /**
     * Parse un horaire "HH:MM" en minutes depuis minuit
     */
    parseTime(timeStr) {
        if (!timeStr || typeof timeStr !== 'string') return null;
        const [hours, minutes] = timeStr.split(':').map(Number);
        if (isNaN(hours) || isNaN(minutes)) return null;
        return hours * 60 + (minutes || 0);
    }

    /**
     * Construit la timeline (colonne des horaires)
     */
    buildTimeline(timeRange) {
        const { startHour, endHour } = timeRange;
        let html = '<div class="agenda-timeline">';
        
        for (let hour = startHour; hour < endHour; hour++) {
            const heightPx = this.slotHeight;
            html += `
                <div class="agenda-time-slot" style="height: ${heightPx}px">
                    <span class="time-label">${hour}:00</span>
                </div>
            `;
        }
        
        html += '</div>';
        return html;
    }

    /**
     * Construit une colonne pour un gymnase
     */
    buildVenueColumn(matches, timeRange) {
        const { startHour, endHour } = timeRange;
        const gridHeightPx = (endHour - startHour) * this.slotHeight;
        
        // Détecter les conflits (matchs qui se chevauchent)
        const matchesWithLayout = this.calculateMatchLayout(matches, timeRange);
        const maxConcurrent = Math.max(...matchesWithLayout.map(m => m.columns), 1);
        
        let html = `<div class="agenda-venue-column" style="height: ${gridHeightPx}px">`;
        
        // Lignes de fond
        for (let hour = startHour; hour < endHour; hour++) {
            const lineTop = (hour - startHour) * this.slotHeight;
            html += `<div class="agenda-grid-line" style="top: ${lineTop}px; height: ${this.slotHeight}px"></div>`;
        }
        
        // Blocs de matchs avec positionnement anti-conflit
        matchesWithLayout.forEach(matchData => {
            const block = this.buildMatchBlock(matchData.match, timeRange, matchData.column, matchData.columns);
            if (block) html += block;
        });
        
        html += '</div>';
        return html;
    }

    /**
     * Calcule le layout pour éviter les chevauchements
     * Retourne un tableau avec les informations de positionnement pour chaque match
     */
    calculateMatchLayout(matches, timeRange) {
        // Trier les matchs par horaire
        const sortedMatches = matches.map(match => {
            const startMinutes = this.parseTime(match.horaire);
            return {
                match,
                startMinutes,
                endMinutes: startMinutes + this.matchDuration
            };
        }).filter(m => m.startMinutes !== null)
          .sort((a, b) => a.startMinutes - b.startMinutes);
        
        // Algorithme pour assigner des colonnes aux matchs qui se chevauchent
        const result = [];
        const activeColumns = []; // Tableau de matchs actifs par colonne
        
        sortedMatches.forEach(matchData => {
            // Trouver une colonne libre (où aucun match actif ne chevauche)
            let assignedColumn = -1;
            
            for (let col = 0; col < activeColumns.length; col++) {
                const lastInColumn = activeColumns[col];
                
                // Si le dernier match de cette colonne est terminé, on peut réutiliser la colonne
                if (!lastInColumn || lastInColumn.endMinutes <= matchData.startMinutes) {
                    assignedColumn = col;
                    activeColumns[col] = matchData;
                    break;
                }
            }
            
            // Si aucune colonne libre, créer une nouvelle colonne
            if (assignedColumn === -1) {
                assignedColumn = activeColumns.length;
                activeColumns.push(matchData);
            }
            
            result.push({
                match: matchData.match,
                column: assignedColumn,
                columns: 0 // Sera mis à jour après
            });
        });
        
        // Calculer le nombre max de colonnes pour chaque match
        result.forEach(item => {
            const matchStart = this.parseTime(item.match.horaire);
            const matchEnd = matchStart + this.matchDuration;
            
            // Compter combien de matchs se chevauchent avec celui-ci
            let maxConcurrent = 1;
            result.forEach(other => {
                if (item === other) return;
                
                const otherStart = this.parseTime(other.match.horaire);
                const otherEnd = otherStart + this.matchDuration;
                
                // Vérifier le chevauchement
                if (matchStart < otherEnd && matchEnd > otherStart) {
                    maxConcurrent = Math.max(maxConcurrent, other.column + 1);
                }
            });
            
            item.columns = maxConcurrent;
        });
        
        return result;
    }

    /**
     * Construit un bloc de match
     */
    buildMatchBlock(match, timeRange, column = 0, totalColumns = 1) {
        const matchMinutes = this.parseTime(match.horaire);
        if (matchMinutes === null) return '';
        
        const { startHour } = timeRange;
        const gridStartMinutes = startHour * 60;
        const offsetMinutes = matchMinutes - gridStartMinutes;
        
        // Si le match est hors de la plage, ne pas l'afficher
        if (offsetMinutes < 0) return '';
        
        // Calcul de la position verticale
        const pixelsPerMinute = this.slotHeight / 60;
        const top = offsetMinutes * pixelsPerMinute;
        const height = this.matchDuration * pixelsPerMinute;
        
        // Calcul de la position horizontale (pour gérer les conflits)
        const widthPercent = 100 / totalColumns;
        const leftPercent = (column * widthPercent);
        
        // Style inline uniquement pour la position verticale
        // Pour l'horizontal, on utilise le style inline SEULEMENT s'il y a des conflits
        let positionStyle = `top: ${top}px; height: ${height}px;`;
        if (totalColumns > 1) {
            // Il y a des conflits : on utilise le positionnement en pourcentages
            positionStyle += ` left: ${leftPercent}%; width: ${widthPercent}%;`;
        }
        // Sinon, on laisse le CSS gérer left/right/width (marges de 4px)
        
        // Couleur selon le genre du match
        const genre = match.equipe1_genre || match.genre || 'M';
        const colorClass = genre === 'F' ? 'female' : 'male';
        
        // Badge genre
        const genreIcon = genre === 'F' ? '♀️' : '♂️';
        const genreLabel = genre === 'F' ? 'Féminin' : 'Masculin';
        
        // Badges et statut
        const isFixed = match.is_fixed || false;
        const poule = match.poule || '';
        const score = match.score || '';
        
        // Classe pour les matchs en conflit (colonnes multiples)
        const conflictClass = totalColumns > 1 ? 'has-conflict' : '';
        
        // Construction du HTML avec toutes les informations
        return `
            <div class="agenda-match-block ${colorClass} ${isFixed ? 'fixed' : ''} ${conflictClass}" 
                 style="${positionStyle}"
                 title="${match.equipe1} vs ${match.equipe2}${poule ? ' - ' + poule : ''}">
                
                <div class="match-header-row">
                    <div class="match-time">🕐 ${match.horaire}</div>
                    <div class="match-badges">
                        <span class="badge-genre ${colorClass}">${genreIcon} ${genreLabel}</span>
                        ${isFixed ? '<span class="badge-fixed">📌 Fixé</span>' : ''}
                    </div>
                </div>
                
                <div class="match-teams-section">
                    <div class="team-line">
                        <span class="team-name" title="${match.equipe1}">${match.equipe1}</span>
                    </div>
                    <div class="vs-divider">⚔️</div>
                    <div class="team-line">
                        <span class="team-name" title="${match.equipe2}">${match.equipe2}</span>
                    </div>
                </div>
                
                ${poule || score ? `
                    <div class="match-footer-row">
                        ${poule ? `<span class="match-poule">🎯 ${poule}</span>` : ''}
                        ${score ? `<span class="match-score">⚽ ${score}</span>` : ''}
                    </div>
                ` : ''}
            </div>
        `;
    }

    /**
     * Raccourcit le nom d'une équipe
     */
    shortenTeamName(name) {
        if (!name) return '?';
        // Garde juste la partie avant la parenthèse
        const short = name.split('(')[0].trim();
        // Limite à 12 caractères
        return short.length > 12 ? short.substring(0, 12) + '...' : short;
    }

    /**
     * Attache les événements
     */
    attachEvents(container, allMatches, filters, preferences) {
        // Les événements de navigation sont gérés via onclick inline
        // On sauvegarde les données pour pouvoir re-render
        this._container = container;
        this._allMatches = allMatches;
        this._filters = filters;
        this._preferences = preferences;
    }

    /**
     * Navigation - Semaine précédente
     */
    previousWeek() {
        if (this.currentWeek > 1) {
            this.currentWeek--;
            this.render(this._container, this._allMatches, this._filters, this._preferences);
        }
    }

    /**
     * Navigation - Semaine suivante
     */
    nextWeek() {
        const weeks = [...new Set(this._allMatches.map(m => m.semaine))];
        const maxWeek = Math.max(...weeks);
        if (this.currentWeek < maxWeek) {
            this.currentWeek++;
            this.render(this._container, this._allMatches, this._filters, this._preferences);
        }
    }

    /**
     * Instance singleton pour les callbacks
     */
    static get instance() {
        if (!window._simpleAgendaViewInstance) {
            window._simpleAgendaViewInstance = new SimpleAgendaView();
        }
        return window._simpleAgendaViewInstance;
    }
}

// Créer l'instance globale
SimpleAgendaView.instance;
