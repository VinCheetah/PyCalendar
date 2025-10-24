/**
 * Vue Grille Horaire - Interface type Google Calendar
 * Affiche les matchs dans une grille horaire avec gymnases en colonnes
 */

class CalendarGridView {
    constructor() {
        this.currentWeek = null;
        this.timeSlotMinutes = 60; // Granularité : 30, 60 ou 120 minutes (défaut 1h)
        this.startHour = 8;  // Sera calculé dynamiquement
        this.endHour = 22;   // Sera calculé dynamiquement
        this.matchDuration = 120; // Durée d'un match en minutes (2h)
        this.marginMinutes = 30; // Marge avant/après pour le visuel
    }

    /**
     * Point d'entrée principal
     */
    render(container, allMatches, availableSlots, filters, preferences) {
        // Logs de débogage réduits (décommenter si nécessaire pour le debug)
        // console.log('🔵 CalendarGridView.render() - Container:', container ? 'OK' : 'NULL', 'Matches:', allMatches?.length || 0);
        
        // Utiliser timeSlotMinutes depuis preferences, mais seulement si c'est une valeur valide
        if (preferences?.timeSlotMinutes && [30, 60, 120].includes(preferences.timeSlotMinutes)) {
            this.timeSlotMinutes = preferences.timeSlotMinutes;
        } else {
            // Valeur par défaut sécurisée
            this.timeSlotMinutes = 60;
        }
        
        // Validation du container
        if (!container) {
            console.error('❌ ERREUR: Container est null ou undefined !');
            return;
        }
        
        // Validation des données
        if (!allMatches || allMatches.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">📭</div>
                    <h3 class="empty-title">Aucun match disponible</h3>
                    <p class="empty-text">Les données de matchs sont vides ou non chargées</p>
                </div>
            `;
            return;
        }
        
        // Initialiser ou conserver la semaine courante
        if (!this.currentWeek || this.currentWeek === null) {
            const weeks = [...new Set(allMatches.map(m => m.semaine))].sort((a, b) => a - b);
            this.currentWeek = weeks[0] || 1;
        }
        
        // Appliquer les filtres
        let filteredMatches = this.applyFilters(allMatches, filters);
        
        // Déterminer le mode d'affichage basé sur les filtres
        const displayMode = this.determineDisplayMode(filters);
        
        // Si un filtre de semaine est actif, synchroniser this.currentWeek
        if (filters.week) {
            this.currentWeek = parseInt(filters.week);
        }
        
        // Filtrer par semaine si mode semaine ET si pas déjà filtré par semaine
        let weekMatches, weekSlots;
        if (displayMode === 'week') {
            // Si filters.week existe, les matchs sont déjà filtrés, pas besoin de re-filtrer
            if (filters.week) {
                weekMatches = filteredMatches;
                weekSlots = availableSlots ? availableSlots.filter(s => s.semaine == this.currentWeek) : [];
            } else {
                // Sinon, filtrer par currentWeek (navigation normale)
                weekMatches = filteredMatches.filter(m => m.semaine == this.currentWeek);
                weekSlots = availableSlots ? availableSlots.filter(s => s.semaine == this.currentWeek) : [];
            }
        } else {
            weekMatches = filteredMatches;
            weekSlots = availableSlots || [];
        }
        
        // CRITICAL FIX: Calculer la plage horaire sur TOUS les matchs (sans filtres)
        // Cela garantit que la grille a TOUJOURS les mêmes dimensions, peu importe:
        // - La semaine affichée
        // - Les filtres appliqués (genre, institution, équipe, poule)
        // Sinon, les matchs seront mal positionnés car la grille change de taille
        this.calculateTimeRange(allMatches, availableSlots || []);
        
        // Obtenir les axes selon le mode d'affichage
        // IMPORTANT: Utiliser allMatches pour les axes, pas weekMatches, pour que la structure reste visible
        const axes = this.getAxes(allMatches, displayMode, filters, this.currentWeek);
        
        if (axes.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">📭</div>
                    <h3 class="empty-title">Aucune donnée disponible</h3>
                    <p class="empty-text">Les données de base sont vides</p>
                </div>
            `;
            return;
        }
        
        try {
            // Construire le HTML
            const html = this.buildHTML(allMatches, weekMatches, weekSlots, axes, displayMode, filters, preferences);
            
            // Injecter dans le container
            container.innerHTML = html;
            
            // Attacher les événements de navigation
            this.setupEventListeners(container, allMatches, availableSlots, filters, preferences);
            
        } catch (error) {
            console.error('❌ ERREUR lors du rendu:', error);
            console.error('Stack trace:', error.stack);
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">⚠️</div>
                    <h3 class="empty-title">Erreur de rendu</h3>
                    <p class="empty-text">${error.message}</p>
                </div>
            `;
        }
    }
    
    /**
     * Applique les filtres sur les matchs
     */
    applyFilters(matches, filters) {
        let filtered = [...matches];
        
        // Filtre genre
        if (filters.gender) {
            filtered = filtered.filter(m => {
                const gender = Utils.getGender(m);
                // Mapper les filtres M, F, X vers male, female, mixed
                if (filters.gender === 'M') return gender === 'male';
                if (filters.gender === 'F') return gender === 'female';
                if (filters.gender === 'X') return gender === 'mixed';
                return true;
            });
        }
        
        // Filtre institution
        if (filters.institution) {
            filtered = filtered.filter(m => 
                m.institution1 === filters.institution || m.institution2 === filters.institution
            );
        }
        
        // Filtre équipe
        if (filters.team) {
            filtered = filtered.filter(m => 
                m.equipe1 === filters.team || m.equipe2 === filters.team
            );
        }
        
        // Filtre poule
        if (filters.pool) {
            filtered = filtered.filter(m => m.poule === filters.pool);
        }
        
        // Filtre gymnase
        if (filters.venue) {
            filtered = filtered.filter(m => m.gymnase === filters.venue);
        }
        
        // Filtre semaine
        if (filters.week) {
            filtered = filtered.filter(m => m.semaine == filters.week);
        }
        
        return filtered;
    }
    
    /**
     * Détermine le mode d'affichage basé sur les filtres actifs
     */
    determineDisplayMode(filters) {
        // Si filtre équipe -> afficher toutes les semaines
        if (filters.team) return 'team';
        
        // Si filtre gymnase -> afficher toutes les semaines
        if (filters.venue) return 'venue';
        
        // Si filtre poule -> afficher UNE semaine avec navigation (mode normal)
        // Note: le filtre de poule ne change PAS le mode d'affichage, seulement les données
        // if (filters.pool) return 'pool';
        
        // Par défaut -> afficher une semaine
        return 'week';
    }
    
    /**
     * Obtient les axes selon le mode d'affichage
     * @param {Array} allMatches - Tous les matchs disponibles (pour déterminer la structure)
     * @param {String} displayMode - Mode d'affichage actuel
     * @param {Object} filters - Filtres actifs
     * @param {Number} currentWeek - Semaine courante (optionnel)
     */
    getAxes(allMatches, displayMode, filters, currentWeek = null) {
        switch (displayMode) {
            case 'team':
                // Si équipe filtrée, afficher les semaines en colonnes (toutes les semaines disponibles)
                return [...new Set(allMatches.map(m => m.semaine))].sort((a, b) => a - b);
            
            case 'venue':
                // Si gymnase filtré, afficher les semaines en colonnes (toutes les semaines disponibles)
                return [...new Set(allMatches.map(m => m.semaine))].sort((a, b) => a - b);
            
            case 'week':
            default:
                // Par défaut, afficher les gymnases en colonnes (tous les gymnases disponibles)
                // Filtrer par semaine courante si nécessaire pour obtenir les bons gymnases
                let matchesForAxes = allMatches;
                if (currentWeek && !filters.week) {
                    matchesForAxes = allMatches.filter(m => m.semaine == currentWeek);
                }
                return [...new Set(matchesForAxes.map(m => m.gymnase))].sort();
        }
    }
    
    /**
     * Construit tout le HTML de la vue
     */
    buildHTML(allMatches, weekMatches, weekSlots, axes, displayMode, filters, preferences) {
        const showAvailable = preferences?.showAvailableSlots !== false;
        const colorMode = preferences?.colorMode || 'genre';
        
        let html = `<div class="calendar-grid-container color-${colorMode}">`;
        
        // Navigation
        html += this.renderNavigationBar(allMatches, displayMode, filters);
        
        // Message d'information si aucun match filtré
        if (weekMatches.length === 0) {
            html += `
                <div class="calendar-empty-notice">
                    <div class="empty-notice-content">
                        <span class="empty-notice-icon">ℹ️</span>
                        <span class="empty-notice-text">Aucun match ne correspond aux filtres actifs pour cette période. La structure du calendrier reste visible pour la navigation.</span>
                    </div>
                </div>
            `;
        }
        
        // Grille
        html += '<div class="calendar-grid-wrapper">';
        
        // Colonne des heures
        html += this.renderTimeColumn();
        
        // Colonnes selon le mode
        html += '<div class="calendar-venues-container">';
        axes.forEach((axis) => {
            const axisMatches = this.getAxisMatches(weekMatches, axis, displayMode, filters);
            const axisSlots = showAvailable ? this.getAxisSlots(weekSlots, axis, displayMode, filters) : [];
            html += this.renderAxisColumn(axis, axisMatches, axisSlots, displayMode, preferences, filters);
        });
        html += '</div>'; // calendar-venues-container
        
        html += '</div>'; // calendar-grid-wrapper
        html += '</div>'; // calendar-grid-container
        
        return html;
    }
    
    /**
     * Obtient les matchs pour un axe donné
     * Trie les matchs pour un affichage cohérent
     */
    getAxisMatches(matches, axis, displayMode, filters) {
        let filtered;
        switch (displayMode) {
            case 'team':
            case 'venue':
                // Axe = semaine
                filtered = matches.filter(m => m.semaine == axis);
                break;
            case 'week':
            default:
                // Axe = gymnase
                filtered = matches.filter(m => m.gymnase === axis);
                break;
        }
        
        // TRI pour affichage cohérent: horaire → equipe1 → equipe2
        return filtered.sort((a, b) => {
            // 1. Par horaire
            if (a.horaire !== b.horaire) {
                return (a.horaire || '').localeCompare(b.horaire || '');
            }
            
            // 2. Par equipe1
            if (a.equipe1 !== b.equipe1) {
                return (a.equipe1 || '').localeCompare(b.equipe1 || '');
            }
            
            // 3. Par equipe2
            return (a.equipe2 || '').localeCompare(b.equipe2 || '');
        });
    }
    
    /**
     * Obtient les créneaux disponibles pour un axe donné
     */
    getAxisSlots(slots, axis, displayMode, filters) {
        switch (displayMode) {
            case 'team':
            case 'venue':
                // Axe = semaine
                const venue = filters.venue || (slots[0] ? slots[0].gymnase : null);
                return slots.filter(s => s.semaine == axis && (!venue || s.gymnase === venue));
            case 'week':
            default:
                // Axe = gymnase
                return slots.filter(s => s.gymnase === axis);
        }
    }
    
    /**
     * Rendu d'une colonne (remplace renderVenueColumn avec gestion multi-mode)
     */
    renderAxisColumn(axis, matches, availableSlots, displayMode, preferences, filters) {
        const slotHeight = this.getSlotHeight();
        const timeSlots = this.generateTimeSlots();
        
        // Déterminer le label et l'icône selon le mode
        let label, icon, count;
        switch (displayMode) {
            case 'team':
            case 'venue':
                // Axe = semaine - utiliser semaine_display si disponible
                const sampleMatch = matches.length > 0 ? matches[0] : null;
                if (sampleMatch && sampleMatch.semaine_display) {
                    label = sampleMatch.semaine_display;
                } else {
                    label = `Semaine ${axis}`;
                }
                icon = '📅';
                break;
            case 'week':
            default:
                label = axis;
                icon = '🏢';
                break;
        }
        
        // NOUVEAU: Grouper les matchs par créneau horaire pour gérer les matchs simultanés
        const matchesBySlot = this.groupMatchesByTimeSlot(matches);
        
        // Calculer le nombre maximum de matchs simultanés pour dimensionner la colonne
        const maxSimultaneous = Math.max(1, ...Object.values(matchesBySlot).map(arr => arr.length));
        
        let html = '<div class="calendar-venue-column">';
        
        // En-tête
        html += `
            <div class="calendar-venue-header">
                <div class="venue-name">${icon} ${label}</div>
                <div class="venue-count">${matches.length} matchs</div>
            </div>
        `;
        
        // Grille avec lignes horaires de fond
        html += `<div class="calendar-venue-grid drop-zone" 
                     data-week="${displayMode === 'week' ? (filters.week || 1) : axis}"
                     data-venue="${displayMode === 'week' ? axis : (filters.venue || '')}"
                     ondragover="CalendarGridView.handleDragOver(event)"
                     ondragleave="CalendarGridView.handleDragLeave(event)"
                     ondrop="CalendarGridView.handleDrop(event)">`;
        
        // Lignes de fond
        timeSlots.forEach((slot, index) => {
            const cssClass = slot.isHour ? 'hour-mark' : '';
            const lineTop = index * slotHeight;
            html += `<div class="calendar-grid-line ${cssClass}" style="top: ${lineTop}px; height: ${slotHeight}px"></div>`;
        });
        
        // Créneaux disponibles (blocs verts) - SIMPLIFIÉ: ne pas afficher si matchs simultanés
        availableSlots.forEach(slot => {
            const pos = this.calculateBlockPosition(slot.horaire, this.matchDuration);
            if (pos) {
                // Vérifier combien de matchs simultanés à cet horaire
                const simultaneousMatches = matchesBySlot[slot.horaire] || [];
                const count = simultaneousMatches.length;
                
                // N'afficher le créneau libre que s'il n'y a pas de matchs simultanés
                if (count === 0) {
                    html += `
                        <div class="calendar-available-block" 
                             style="top: ${pos.top}px; height: ${pos.height}px"
                             title="Créneau libre: ${slot.horaire}">
                            ✓
                        </div>
                    `;
                }
                // Si des matchs existent à cet horaire, on n'affiche pas le créneau libre
                // pour éviter les conflits de positionnement
            }
        });
        
        // NOUVEAU: Blocs de matchs avec gestion des sous-colonnes
        Object.keys(matchesBySlot).forEach(timeSlot => {
            const simultaneousMatches = matchesBySlot[timeSlot];
            const count = simultaneousMatches.length;
            
            simultaneousMatches.forEach((match, index) => {
                const pos = this.calculateBlockPosition(match.horaire, this.matchDuration);
                if (pos) {
                    // Ajouter les informations de sous-colonne
                    pos.subColumnIndex = index;
                    pos.subColumnCount = count;
                    html += this.renderMatchBlock(match, pos, displayMode, preferences);
                }
            });
        });
        
        html += '</div>'; // calendar-venue-grid
        html += '</div>'; // calendar-venue-column
        
        return html;
    }
    
    /**
     * Groupe les matchs par créneau horaire pour gérer les matchs simultanés
     * IMPORTANT: Trie les matchs de manière déterministe pour éviter le désordre après modifications
     */
    groupMatchesByTimeSlot(matches) {
        const grouped = {};
        
        matches.forEach(match => {
            const key = match.horaire;
            if (!grouped[key]) {
                grouped[key] = [];
            }
            grouped[key].push(match);
        });
        
        // TRI DÉTERMINISTE: pour chaque créneau horaire, trier les matchs
        // Ordre: gymnase → equipe1 → equipe2 → poule
        Object.keys(grouped).forEach(timeSlot => {
            grouped[timeSlot].sort((a, b) => {
                // 1. Par gymnase
                if (a.gymnase !== b.gymnase) {
                    return (a.gymnase || '').localeCompare(b.gymnase || '');
                }
                
                // 2. Par equipe1
                if (a.equipe1 !== b.equipe1) {
                    return (a.equipe1 || '').localeCompare(b.equipe1 || '');
                }
                
                // 3. Par equipe2
                if (a.equipe2 !== b.equipe2) {
                    return (a.equipe2 || '').localeCompare(b.equipe2 || '');
                }
                
                // 4. Par poule
                return (a.poule || '').localeCompare(b.poule || '');
            });
        });
        
        return grouped;
    }

    /**
     * Calcule la plage horaire optimale basée sur les données réelles
     * IMPORTANT: Cette fonction doit être appelée avec TOUS les matchs (toutes semaines confondues)
     * pour garantir que la grille a les mêmes dimensions quelle que soit la semaine affichée.
     * Sinon, les matchs seraient mal positionnés lors du changement de semaine.
     */
    calculateTimeRange(weekMatches, weekSlots) {
        // Récupérer tous les horaires (matchs + créneaux disponibles)
        const allTimes = [
            ...weekMatches.map(m => m.horaire),
            ...weekSlots.map(s => s.horaire)
        ].filter(h => h); // Filtrer les valeurs nulles
        
        if (allTimes.length === 0) {
            // Par défaut si aucune donnée
            this.startHour = 8;
            this.endHour = 22;
            return;
        }
        
        // Convertir en minutes
        const allMinutes = allTimes.map(time => Utils.parseTime(time));
        
        // Trouver min et max
        const minMinutes = Math.min(...allMinutes);
        const maxMinutes = Math.max(...allMinutes);
        
        // Ajouter la durée d'un match au max (car le dernier match dure 90 min)
        const maxWithDuration = maxMinutes + this.matchDuration;
        
        // Ajouter des marges pour le confort visuel
        const startWithMargin = minMinutes - this.marginMinutes;
        const endWithMargin = maxWithDuration + this.marginMinutes;
        
        // Arrondir aux heures entières (floor pour le début, ceil pour la fin)
        this.startHour = Math.floor(startWithMargin / 60);
        this.endHour = Math.ceil(endWithMargin / 60);
        
        // Limites de sécurité
        this.startHour = Math.max(6, this.startHour);  // Pas avant 6h
        this.endHour = Math.min(24, this.endHour);     // Pas après minuit
    }

    /**
     * Barre de navigation adaptée au mode d'affichage
     */
    renderNavigationBar(allMatches, displayMode, filters) {
        // En mode 'week' : navigation par semaine
        // En mode 'team' ou 'venue' : affichage de toutes les semaines d'un coup
        
        let navigationHTML = '';
        let titleHTML = '';
        
        if (displayMode === 'week') {
            // Mode semaine : navigation classique
            const weeks = [...new Set(allMatches.map(m => m.semaine))].sort((a, b) => a - b);
            const minWeek = weeks[0];
            const maxWeek = weeks[weeks.length - 1];
            const canGoPrev = this.currentWeek > minWeek;
            const canGoNext = this.currentWeek < maxWeek;
            
            navigationHTML = `
                <div class="calendar-nav-left">
                    <button class="btn-nav btn-prev-week" ${canGoPrev ? '' : 'disabled'}>
                        ← Semaine précédente
                    </button>
                    <button class="btn-nav btn-first-week">
                        ⏮ Première
                    </button>
                    <button class="btn-nav btn-next-week" ${canGoNext ? '' : 'disabled'}>
                        Semaine suivante →
                    </button>
                </div>
            `;
            
            // Trouver un match de la semaine courante pour obtenir semaine_display
            const currentWeekMatch = allMatches.find(m => m.semaine == this.currentWeek);
            const weekDisplay = currentWeekMatch && currentWeekMatch.semaine_display 
                ? currentWeekMatch.semaine_display 
                : `Semaine ${this.currentWeek}`;
            
            // Si un filtre de poule est actif, l'afficher dans le titre
            if (filters.pool) {
                titleHTML = `
                    <h2 class="calendar-title">
                        🏆 ${filters.pool} - ${weekDisplay}
                    </h2>
                `;
            } else {
                titleHTML = `
                    <h2 class="calendar-title">
                        📅 ${weekDisplay}
                    </h2>
                `;
            }
        } else if (displayMode === 'team') {
            // Mode équipe : afficher le nom de l'équipe
            titleHTML = `
                <h2 class="calendar-title">
                    👥 ${filters.team || 'Équipe'}
                </h2>
            `;
        } else if (displayMode === 'venue') {
            // Mode gymnase : afficher le nom du gymnase
            titleHTML = `
                <h2 class="calendar-title">
                    🏢 ${filters.venue || 'Gymnase'}
                </h2>
            `;
        }

        return `
            <div class="calendar-nav">
                ${navigationHTML}
                
                <div class="calendar-nav-center">
                    ${titleHTML}
                    <div class="calendar-time-range">
                        ⏰ ${this.startHour}h - ${this.endHour}h • Zoom: ${this.timeSlotMinutes}min
                    </div>
                </div>
            </div>
        `;
    }
    
    /**
     * Colonne des horaires (fixe à gauche)
     */
    renderTimeColumn() {
        const slots = this.generateTimeSlots();
        const slotHeight = this.getSlotHeight();
        
        let html = '<div class="calendar-time-column">';
        html += '<div class="calendar-time-header">Horaire</div>';
        
        slots.forEach(slot => {
            html += `<div class="calendar-time-slot" style="height: ${slotHeight}px">${slot.label}</div>`;
        });
        
        html += '</div>';
        return html;
    }

    /**
     * Bloc de match avec préférences d'affichage
     */
    renderMatchBlock(match, pos, displayMode = 'week', preferences = {}) {
        const gender = Utils.getGender(match);
        const colorClass = gender === 'M' || gender === 'male' ? 'male' : gender === 'F' || gender === 'female' ? 'female' : 'mixed';
        const category = Utils.getCategory(match.poule);
        
        // Déterminer le niveau de détail selon la hauteur réelle calculée
        const height = pos.height;
        const detailLevel = height < 70 ? 'minimal' : height < 150 ? 'compact' : 'full';
        
        // Icône genre
        const genderIcon = colorClass === 'male' ? '♂' : colorClass === 'female' ? '♀' : '⚥';
        
        // Use match_id from data (double underscore format from Phase 1)
        const matchId = match.match_id || `${match.equipe1}_${match.equipe2}_${match.poule}`;
        
        // NOUVEAU: Gérer le positionnement en sous-colonnes
        const subColumnIndex = pos.subColumnIndex || 0;
        const subColumnCount = pos.subColumnCount || 1;
        const widthPercent = 100 / subColumnCount;
        const leftPercent = (100 / subColumnCount) * subColumnIndex;
        
        // Adapter la taille du texte selon le nombre de sous-colonnes
        const maxLength = subColumnCount === 1 ? 20 : subColumnCount === 2 ? 14 : subColumnCount === 3 ? 10 : 8;
        const truncate = (text, max) => text && text.length > max ? text.substring(0, max - 1) + '…' : text;
        
        // Raccourcir les noms d'équipes
        const team1 = truncate(match.equipe1, detailLevel === 'minimal' ? maxLength - 2 : maxLength);
        const team2 = truncate(match.equipe2, detailLevel === 'minimal' ? maxLength - 2 : maxLength);
        
        // Extraire catégorie et numéro de poule (utiliser categoryCode pour éviter conflit)
        const pouleMatch = match.poule ? match.poule.match(/^([A-Z]+)([A-Z]\d+)(.*)$/) : null;
        const categoryCode = pouleMatch ? pouleMatch[1] : '';
        const level = pouleMatch ? pouleMatch[2] : '';
        const poolNum = pouleMatch ? pouleMatch[3] : match.poule
        
        // Style de positionnement en sous-colonne
        const subColumnStyle = `top: ${pos.top}px; height: ${pos.height}px; left: ${leftPercent}%; width: ${widthPercent}%;`;
        
        // Tooltip enrichi avec TOUTES les infos
        const tooltipParts = [
            `${match.equipe1} vs ${match.equipe2}`,
            match.horaire ? `⏰ ${match.horaire}` : '',
            match.poule ? `🎯 ${match.poule}` : '',
            match.gymnase ? `🏢 ${match.gymnase}` : '',
            match.institution1 && match.institution2 ? `🏛️ ${match.institution1} vs ${match.institution2}` : '',
            !match.has_score ? `⏳ Score non saisi` : '',
            match.equipe1_horaires_preferes && match.equipe1_horaires_preferes.length > 0 ? 
                `⏰ Préf. ${match.equipe1}: ${match.equipe1_horaires_preferes.join(', ')}` : '',
            match.equipe2_horaires_preferes && match.equipe2_horaires_preferes.length > 0 ? 
                `⏰ Préf. ${match.equipe2}: ${match.equipe2_horaires_preferes.join(', ')}` : ''
        ].filter(p => p).join('\n');
        
        // Escape single quotes in match data for onclick
        const escapeQuotes = (str) => str ? str.replace(/'/g, "\\'") : '';
        
        // === RENDU MINIMAL (créneaux < 70px - granularité 30min ou 120min) ===
        if (detailLevel === 'minimal') {
            return `
                <div class="calendar-match-block calendar-match-${colorClass} detail-minimal ${!match.has_score ? 'no-score' : ''}" 
                     draggable="true"
                     ondragstart="CalendarGridView.handleDragStart(event)"
                     ondragend="CalendarGridView.handleDragEnd(event)"
                     style="top: ${pos.top}px; height: ${pos.height}px;"
                     data-match-id="${matchId}"
                     data-gender="${colorClass}"
                     data-category="${category}"
                     data-pool="${Utils.escapeHtml(match.poule)}"
                     data-institution1="${Utils.escapeHtml(match.institution1)}"
                     data-institution2="${Utils.escapeHtml(match.institution2)}"
                     data-subcolumn-count="${subColumnCount}"
                     data-subcolumn-index="${subColumnIndex}"
                     title="${tooltipParts}">
                    <button class="match-edit-btn" onclick="editModal.open({
                        match_id: '${matchId}',
                        equipe1: '${escapeQuotes(match.equipe1)}',
                        equipe2: '${escapeQuotes(match.equipe2)}',
                        poule: '${escapeQuotes(match.poule)}',
                        semaine: ${match.semaine},
                        horaire: '${escapeQuotes(match.horaire)}',
                        gymnase: '${escapeQuotes(match.gymnase)}'
                    }, this.closest('.calendar-match-block'))">✏️</button>
                    <div class="match-content-minimal">
                        <div class="match-teams-minimal">
                            <div class="team-name-minimal">${team1}</div>
                            <div class="match-vs-minimal">vs</div>
                            <div class="team-name-minimal">${team2}</div>
                        </div>
                    </div>
                </div>
            `;
        }
        
        // === RENDU COMPACT (créneaux 70-150px - granularité 60min) ===
        if (detailLevel === 'compact') {
            // Priorité: Équipes > Gymnase/Semaine > Catégorie
            let contextBadge = '';
            if (displayMode !== 'week' && match.gymnase) {
                contextBadge = `<span class="context-badge">📍 ${truncate(match.gymnase, 10)}</span>`;
            } else if (categoryCode) {
                contextBadge = `<span class="context-badge">${categoryCode}</span>`;
            }
            
            // Indicateur pour les matchs auto-programmés
            const autoIndicator = !match.is_fixed ? '<span class="auto-indicator">🤖</span>' : '';
            
            return `
                <div class="calendar-match-block calendar-match-${colorClass} detail-compact ${!match.has_score ? 'no-score' : ''} ${!match.is_fixed ? 'auto-scheduled' : ''}" 
                     draggable="true"
                     ondragstart="CalendarGridView.handleDragStart(event)"
                     ondragend="CalendarGridView.handleDragEnd(event)"
                     style="top: ${pos.top}px; height: ${pos.height}px;"
                     data-match-id="${matchId}"
                     data-gender="${colorClass}"
                     data-category="${category}"
                     data-pool="${Utils.escapeHtml(match.poule)}"
                     data-institution1="${Utils.escapeHtml(match.institution1)}"
                     data-institution2="${Utils.escapeHtml(match.institution2)}"
                     data-subcolumn-count="${subColumnCount}"
                     data-subcolumn-index="${subColumnIndex}"
                     title="${tooltipParts}">
                    <button class="match-edit-btn" onclick="editModal.open({
                        match_id: '${matchId}',
                        equipe1: '${escapeQuotes(match.equipe1)}',
                        equipe2: '${escapeQuotes(match.equipe2)}',
                        poule: '${escapeQuotes(match.poule)}',
                        semaine: ${match.semaine},
                        horaire: '${escapeQuotes(match.horaire)}',
                        gymnase: '${escapeQuotes(match.gymnase)}'
                    }, this.closest('.calendar-match-block'))">✏️</button>
                    <div class="match-content-compact">
                        <div class="match-header-compact">
                            ${contextBadge}
                            <span class="gender-badge-compact">${genderIcon}</span>
                            ${autoIndicator}
                        </div>
                        <div class="match-teams-compact">
                            <div class="team-name-compact">${team1}</div>
                            <div class="match-vs-compact">vs</div>
                            <div class="team-name-compact">${team2}</div>
                        </div>
                    </div>
                </div>
            `;
        }
        
        // === RENDU COMPLET (créneaux > 150px) ===
        // Priorité complète: Équipes > Gymnase/Semaine > Catégorie > Poule > Genre > Horaires préférés
        let contextLine = '';
        if (displayMode !== 'week' && match.gymnase) {
            contextLine = `<div class="context-line">📍 ${truncate(match.gymnase, 12)}</div>`;
        } else if (displayMode !== 'venue' && match.semaine) {
            contextLine = `<div class="context-line">📅 S${match.semaine}</div>`;
        }
        
        let poolLine = '';
        if (categoryCode && poolNum) {
            poolLine = `<div class="pool-line"><span class="category-badge">${categoryCode}</span> <span class="level-badge">${level}</span> <span class="pool-badge">${poolNum}</span></div>`;
        }
        
        // Horaires préférés (affichés seulement si espace suffisant et si préférences activées)
        let prefLine = '';
        if (preferences?.showPreferences && height > 180 && subColumnCount <= 2) {
            const pref1 = match.equipe1_horaires_preferes && match.equipe1_horaires_preferes.length > 0;
            const pref2 = match.equipe2_horaires_preferes && match.equipe2_horaires_preferes.length > 0;
            if (pref1 || pref2) {
                const prefIcons = `${pref1 ? '⏰' : ''}${pref2 ? '⏰' : ''}`;
                prefLine = `<div class="pref-line">${prefIcons}</div>`;
            }
        }
        
        // Indicateur pour les matchs auto-programmés
        const autoIndicator = !match.is_fixed ? '<span class="auto-indicator">🤖</span>' : '';
        
        return `
            <div class="calendar-match-block calendar-match-${colorClass} detail-full ${!match.has_score ? 'no-score' : ''} ${!match.is_fixed ? 'auto-scheduled' : ''}" 
                 draggable="true"
                 ondragstart="CalendarGridView.handleDragStart(event)"
                 ondragend="CalendarGridView.handleDragEnd(event)"
                 style="top: ${pos.top}px; height: ${pos.height}px;"
                 data-match-id="${matchId}"
                 data-gender="${colorClass}"
                 data-category="${category}"
                 data-pool="${Utils.escapeHtml(match.poule)}"
                 data-institution1="${Utils.escapeHtml(match.institution1)}"
                 data-institution2="${Utils.escapeHtml(match.institution2)}"
                 data-subcolumn-count="${subColumnCount}"
                 data-subcolumn-index="${subColumnIndex}"
                 title="${tooltipParts}">
                <button class="match-edit-btn" onclick="editModal.open({
                    match_id: '${matchId}',
                    equipe1: '${escapeQuotes(match.equipe1)}',
                    equipe2: '${escapeQuotes(match.equipe2)}',
                    poule: '${escapeQuotes(match.poule)}',
                    semaine: ${match.semaine},
                    horaire: '${escapeQuotes(match.horaire)}',
                    gymnase: '${escapeQuotes(match.gymnase)}'
                }, this.closest('.calendar-match-block'))">✏️</button>
                <div class="match-content-full">
                    <div class="match-header-full">
                        <span class="horaire-badge match-time">${match.horaire}</span>
                        <span class="gender-badge-full">${genderIcon}</span>
                        ${autoIndicator}
                    </div>
                    <div class="match-teams-full">
                        <div class="team-name-full">${team1}</div>
                        <div class="match-vs-full">VS</div>
                        <div class="team-name-full">${team2}</div>
                    </div>
                    ${contextLine}
                    ${poolLine}
                    ${prefLine}
                </div>
            </div>
        `;
    }

    /**
     * Génère les créneaux horaires
     */
    generateTimeSlots() {
        const slots = [];
        const totalMinutes = (this.endHour - this.startHour) * 60;
        
        for (let offset = 0; offset < totalMinutes; offset += this.timeSlotMinutes) {
            const totalMins = this.startHour * 60 + offset;
            const hour = Math.floor(totalMins / 60);
            const minute = totalMins % 60;
            
            slots.push({
                label: `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`,
                minutes: totalMins,
                isHour: minute === 0
            });
        }
        
        return slots;
    }

    /**
     * Calcule position et hauteur d'un bloc
     */
    calculateBlockPosition(timeStr, durationMinutes) {
        const matchMinutes = Utils.parseTime(timeStr);
        const gridStartMinutes = this.startHour * 60;
        const gridEndMinutes = this.endHour * 60;
        
        // Vérifier si dans la plage (retourner null si hors plage)
        if (matchMinutes < gridStartMinutes || matchMinutes >= gridEndMinutes) {
            return null;
        }
        
        const offsetMinutes = matchMinutes - gridStartMinutes;
        const pixelsPerMinute = this.getSlotHeight() / this.timeSlotMinutes;
        
        const pos = {
            top: offsetMinutes * pixelsPerMinute,
            height: durationMinutes * pixelsPerMinute
        };
        
        return pos;
    }

    /**
     * Hauteur d'un créneau en pixels
     * Calcule dynamiquement pour que la grille ne nécessite jamais de scroll vertical
     */
    getSlotHeight() {
        // Calculer la hauteur disponible pour la grille
        // Hauteur fenêtre - (header app + title/stats ~150px + controls section ~180px + nav calendrier ~95px + header grille ~60px + padding/marges ~80px)
        const fixedElementsHeight = 565;
        
        // Gérer le cas où window n'est pas défini (génération côté serveur)
        const windowHeight = (typeof window !== 'undefined' && window.innerHeight) ? window.innerHeight : 800; // Valeur par défaut raisonnable
        const availableHeight = windowHeight - fixedElementsHeight;
        
        // Calculer le nombre total de créneaux
        const totalMinutes = (this.endHour - this.startHour) * 60;
        const totalSlots = totalMinutes / this.timeSlotMinutes;
        
        // Calculer la hauteur optimale par créneau
        const calculatedHeight = Math.floor(availableHeight / totalSlots);
        
        // Définir des hauteurs minimales par granularité pour garder la lisibilité
        const minHeights = {
            30: 35,  // Au moins 35px pour 30min
            60: 45,  // Au moins 45px pour 60min
            120: 30  // Au moins 30px pour 120min
        };
        
        const minHeight = minHeights[this.timeSlotMinutes] || 45;
        
        // Retourner le maximum entre la hauteur calculée et la hauteur minimale
        // Gérer le cas où calculatedHeight est NaN ou Infinity
        let finalHeight = calculatedHeight;
        if (isNaN(finalHeight) || !isFinite(finalHeight) || finalHeight < minHeight) {
            finalHeight = minHeight;
        }
        
        return finalHeight;
    }

    /**
     * Configure les événements
     */
    setupEventListeners(container, allMatches, availableSlots, filters, preferences) {
        const weeks = [...new Set(allMatches.map(m => m.semaine))].sort((a, b) => a - b);
        
        // Bouton semaine précédente
        const btnPrev = container.querySelector('.btn-prev-week');
        if (btnPrev) {
            btnPrev.addEventListener('click', () => {
                const idx = weeks.indexOf(this.currentWeek);
                if (idx > 0) {
                    this.currentWeek = weeks[idx - 1];
                    this.render(container, allMatches, availableSlots, filters, preferences);
                }
            });
        }
        
        // Bouton semaine suivante
        const btnNext = container.querySelector('.btn-next-week');
        if (btnNext) {
            btnNext.addEventListener('click', () => {
                const idx = weeks.indexOf(this.currentWeek);
                if (idx < weeks.length - 1) {
                    this.currentWeek = weeks[idx + 1];
                    this.render(container, allMatches, availableSlots, filters, preferences);
                }
            });
        }
        
        // Bouton première semaine
        const btnFirst = container.querySelector('.btn-first-week');
        if (btnFirst) {
            btnFirst.addEventListener('click', () => {
                this.currentWeek = weeks[0];
                this.render(container, allMatches, availableSlots, filters, preferences);
            });
        }
    }
    
    /**
     * Handle drag start event on match blocks
     */
    static handleDragStart(e) {
        const matchBlock = e.currentTarget;
        const matchId = matchBlock.dataset.matchId;
        
        // Add dragging class for visual feedback
        matchBlock.classList.add('dragging');
        
        // Force show available slots during drag
        const availableBlocks = document.querySelectorAll('.calendar-available-block');
        availableBlocks.forEach(block => {
            block.classList.add('drag-active');
            block.style.display = 'flex'; // Force display
        });
        
        // Also make available slots droppable
        availableBlocks.forEach(block => {
            if (!block.hasAttribute('data-drop-listeners')) {
                block.setAttribute('data-drop-listeners', 'true');
                block.addEventListener('dragover', CalendarGridView.handleAvailableSlotDragOver);
                block.addEventListener('dragleave', CalendarGridView.handleAvailableSlotDragLeave);
                block.addEventListener('drop', CalendarGridView.handleAvailableSlotDrop);
            }
        });
        
        // Make other match blocks droppable for swap
        const otherMatchBlocks = document.querySelectorAll('.calendar-match-block:not(.dragging)');
        otherMatchBlocks.forEach(block => {
            block.classList.add('swap-target');
            if (!block.hasAttribute('data-swap-listeners')) {
                block.setAttribute('data-swap-listeners', 'true');
                block.addEventListener('dragover', CalendarGridView.handleMatchBlockDragOver);
                block.addEventListener('dragleave', CalendarGridView.handleMatchBlockDragLeave);
                block.addEventListener('drop', CalendarGridView.handleMatchBlockDrop);
            }
        });
        
        // Find match data from the global matches array
        const match = window.allMatches?.find(m => m.match_id === matchId);
        
        if (match) {
            // Store match data in drag transfer
            const matchData = {
                match_id: match.match_id,
                equipe1: match.equipe1,
                equipe2: match.equipe2,
                poule: match.poule,
                semaine: match.semaine,
                horaire: match.horaire,
                gymnase: match.gymnase,
                institution1: match.institution1 || '',
                institution2: match.institution2 || ''
            };
            
            e.dataTransfer.effectAllowed = 'move';
            e.dataTransfer.setData('application/json', JSON.stringify(matchData));
            e.dataTransfer.setData('text/plain', `${match.equipe1} vs ${match.equipe2}`);
            
            console.log('Drag started:', matchData);
        } else {
            console.warn('Match not found for ID:', matchId);
        }
    }
    
    /**
     * Handle drag end event on match blocks
     */
    static handleDragEnd(e) {
        const matchBlock = e.currentTarget;
        
        // Remove dragging class
        matchBlock.classList.remove('dragging');
        
        // Remove drag-active class from available slots
        document.querySelectorAll('.calendar-available-block').forEach(block => {
            block.classList.remove('drag-active', 'highlight-drop');
        });
        
        // Remove swap-target class from match blocks
        document.querySelectorAll('.calendar-match-block').forEach(block => {
            block.classList.remove('swap-target', 'swap-highlight');
        });
        
        // Remove any active drop zone highlights
        document.querySelectorAll('.drop-zone-active').forEach(zone => {
            zone.classList.remove('drop-zone-active');
            delete zone.dataset.targetTime;
        });
    }
    
    /**
     * Handle drag over event on match blocks (for swap)
     */
    static handleMatchBlockDragOver(e) {
        e.preventDefault();
        e.stopPropagation();
        const matchBlock = e.currentTarget;
        e.dataTransfer.dropEffect = 'move';
        matchBlock.classList.add('swap-highlight');
    }
    
    /**
     * Handle drag leave event on match blocks
     */
    static handleMatchBlockDragLeave(e) {
        e.preventDefault();
        const matchBlock = e.currentTarget;
        if (!matchBlock.contains(e.relatedTarget)) {
            matchBlock.classList.remove('swap-highlight');
        }
    }
    
    /**
     * Handle drop event on match blocks (for swap)
     */
    static handleMatchBlockDrop(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const targetMatchBlock = e.currentTarget;
        targetMatchBlock.classList.remove('swap-highlight');
        
        try {
            // Get dragged match data
            const draggedMatchDataStr = e.dataTransfer.getData('application/json');
            if (!draggedMatchDataStr) {
                console.warn('No match data in drop event');
                return;
            }
            
            const draggedMatchData = JSON.parse(draggedMatchDataStr);
            
            // Get target match data
            const targetMatchId = targetMatchBlock.dataset.matchId;
            const targetMatch = window.allMatches?.find(m => m.match_id === targetMatchId);
            
            if (!targetMatch) {
                console.warn('Target match not found');
                return;
            }
            
            if (draggedMatchData.match_id === targetMatch.match_id) {
                console.log('Cannot swap match with itself');
                return;
            }
            
            console.log('Swapping matches:', draggedMatchData.match_id, '↔', targetMatch.match_id);
            
            // Create swap modifications
            const modifications = [
                {
                    match_id: draggedMatchData.match_id,
                    original: {
                        week: draggedMatchData.semaine,
                        time: draggedMatchData.horaire,
                        venue: draggedMatchData.gymnase
                    },
                    new: {
                        week: targetMatch.semaine,
                        time: targetMatch.horaire,
                        venue: targetMatch.gymnase
                    }
                },
                {
                    match_id: targetMatch.match_id,
                    original: {
                        week: targetMatch.semaine,
                        time: targetMatch.horaire,
                        venue: targetMatch.gymnase
                    },
                    new: {
                        week: draggedMatchData.semaine,
                        time: draggedMatchData.horaire,
                        venue: draggedMatchData.gymnase
                    }
                }
            ];
            
            // Save both modifications
            modifications.forEach(mod => {
                CalendarGridView.saveModification(mod);
            });
            
            // Show feedback
            const dropZone = targetMatchBlock.closest('.drop-zone');
            if (dropZone) {
                CalendarGridView.showDropFeedback(dropZone, '🔄 Matchs échangés!');
            }
            
            // Re-render calendar after a brief delay
            setTimeout(() => {
                if (window.app && typeof window.app.reloadAndRender === 'function') {
                    window.app.reloadAndRender();
                } else {
                    console.warn('window.app.reloadAndRender not available');
                }
            }, 300);
            
        } catch (error) {
            console.error('Error handling match block drop:', error);
        }
    }
    
    /**
     * Handle drag over event on available slots
     */
    static handleAvailableSlotDragOver(e) {
        e.preventDefault();
        e.stopPropagation();
        const availableBlock = e.currentTarget;
        e.dataTransfer.dropEffect = 'move';
        availableBlock.classList.add('highlight-drop');
    }
    
    /**
     * Handle drag leave event on available slots
     */
    static handleAvailableSlotDragLeave(e) {
        e.preventDefault();
        const availableBlock = e.currentTarget;
        if (!availableBlock.contains(e.relatedTarget)) {
            availableBlock.classList.remove('highlight-drop');
        }
    }
    
    /**
     * Handle drop event on available slots
     */
    static handleAvailableSlotDrop(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const availableBlock = e.currentTarget;
        availableBlock.classList.remove('highlight-drop');
        
        try {
            // Get match data from drag
            const matchDataStr = e.dataTransfer.getData('application/json');
            if (!matchDataStr) {
                console.warn('No match data in drop event');
                return;
            }
            
            const matchData = JSON.parse(matchDataStr);
            
            // Extract time from title attribute
            const title = availableBlock.getAttribute('title');
            const timeMatch = title.match(/Créneau libre: (\d{2}:\d{2})/);
            if (!timeMatch) {
                console.warn('Could not extract time from available slot');
                return;
            }
            const targetTime = timeMatch[1];
            
            // Get venue and week from parent drop zone
            const dropZone = availableBlock.closest('.drop-zone');
            const targetWeek = parseInt(dropZone?.dataset.week);
            const targetVenue = dropZone?.dataset.venue;
            
            // Create modification
            const modification = {
                match_id: matchData.match_id,
                original: {
                    week: matchData.semaine,
                    time: matchData.horaire,
                    venue: matchData.gymnase
                },
                new: {
                    week: targetWeek || matchData.semaine,
                    time: targetTime,
                    venue: targetVenue || matchData.gymnase
                }
            };
            
            console.log('Dropping on available slot:', modification);
            
            // Save modification
            CalendarGridView.saveModification(modification);
            
            // Re-render calendar after a brief delay
            setTimeout(() => {
                if (window.app && typeof window.app.reloadAndRender === 'function') {
                    window.app.reloadAndRender();
                } else {
                    console.warn('window.app.reloadAndRender not available');
                }
            }, 300);
            
        } catch (error) {
            console.error('Error handling available slot drop:', error);
        }
    }
    
    /**
     * Handle drag over event on drop zones
     */
    static handleDragOver(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const dropZone = e.currentTarget;
        e.dataTransfer.dropEffect = 'move';
        
        // Calculate time slot from cursor position
        const rect = dropZone.getBoundingClientRect();
        const relativeY = e.clientY - rect.top;
        const timeSlot = CalendarGridView.getTimeSlotFromPosition(dropZone, relativeY);
        
        // Highlight drop zone
        dropZone.classList.add('drop-zone-active');
        
        // Store target time for visual feedback
        dropZone.dataset.targetTime = timeSlot;
    }
    
    /**
     * Handle drag leave event
     */
    static handleDragLeave(e) {
        e.preventDefault();
        const dropZone = e.currentTarget;
        
        // Only remove highlighting if leaving the drop zone entirely
        if (!dropZone.contains(e.relatedTarget)) {
            dropZone.classList.remove('drop-zone-active');
            delete dropZone.dataset.targetTime;
        }
    }
    
    /**
     * Handle drop event
     */
    static handleDrop(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const dropZone = e.currentTarget;
        dropZone.classList.remove('drop-zone-active');
        
        try {
            // Get match data from drag
            const matchDataStr = e.dataTransfer.getData('application/json');
            if (!matchDataStr) {
                console.warn('No match data in drop event');
                return;
            }
            
            const matchData = JSON.parse(matchDataStr);
            
            // Calculate time slot from drop position
            const rect = dropZone.getBoundingClientRect();
            const relativeY = e.clientY - rect.top;
            const targetTime = CalendarGridView.getTimeSlotFromPosition(dropZone, relativeY);
            
            // Get target week and venue from drop zone
            const targetWeek = parseInt(dropZone.dataset.week);
            const targetVenue = dropZone.dataset.venue;
            
            // Check if dropping on another match (for swap)
            const targetMatch = CalendarGridView.findMatchAtPosition(targetWeek, targetVenue, targetTime);
            
            if (targetMatch && targetMatch.match_id !== matchData.match_id) {
                // SWAP: Valider avant d'échanger
                const swapValid = CalendarGridView.validateSwap(matchData, targetMatch);
                
                if (!swapValid.canSwap) {
                    CalendarGridView.showDropFeedback(dropZone, `❌ ${swapValid.reason}`, true);
                    return;
                }
                
                if (swapValid.warnings && swapValid.warnings.length > 0) {
                    // Demander confirmation si avertissements
                    if (!confirm(`⚠️ Avertissement:\n${swapValid.warnings.join('\n')}\n\nContinuer quand même?`)) {
                        return;
                    }
                }
                
                // SWAP: Two matches exchange positions
                console.log('Swap detected between:', matchData.match_id, 'and', targetMatch.match_id);
                
                const modifications = [
                    {
                        match_id: matchData.match_id,
                        original: {
                            week: matchData.semaine,
                            time: matchData.horaire,
                            venue: matchData.gymnase
                        },
                        new: {
                            week: targetMatch.semaine,
                            time: targetMatch.horaire,
                            venue: targetMatch.gymnase
                        }
                    },
                    {
                        match_id: targetMatch.match_id,
                        original: {
                            week: targetMatch.semaine,
                            time: targetMatch.horaire,
                            venue: targetMatch.gymnase
                        },
                        new: {
                            week: matchData.semaine,
                            time: matchData.horaire,
                            venue: matchData.gymnase
                        }
                    }
                ];
                
                // Save both modifications
                modifications.forEach(mod => {
                    CalendarGridView.saveModification(mod);
                });
                
                CalendarGridView.showDropFeedback(dropZone, '🔄 Matchs échangés!');
                
            } else {
                // MOVE: Valider avant de déplacer
                const moveValid = CalendarGridView.validateMove(matchData, targetWeek, targetVenue, targetTime);
                
                if (!moveValid.canMove) {
                    CalendarGridView.showDropFeedback(dropZone, `❌ ${moveValid.reason}`, true);
                    return;
                }
                
                if (moveValid.warnings && moveValid.warnings.length > 0) {
                    // Demander confirmation si avertissements
                    if (!confirm(`⚠️ Avertissement:\n${moveValid.warnings.join('\n')}\n\nContinuer quand même?`)) {
                        return;
                    }
                }
                
                // MOVE: Simple relocation
                const modification = {
                    match_id: matchData.match_id,
                    original: {
                        week: matchData.semaine,
                        time: matchData.horaire,
                        venue: matchData.gymnase
                    },
                    new: {
                        week: targetWeek || matchData.semaine,
                        time: targetTime || matchData.horaire,
                        venue: targetVenue || matchData.gymnase
                    }
                };
                
                // Check if actually changed
                const changed = modification.original.week !== modification.new.week ||
                               modification.original.time !== modification.new.time ||
                               modification.original.venue !== modification.new.venue;
                
                if (!changed) {
                    console.log('No change detected, ignoring drop');
                    return;
                }
                
                // Save modification
                CalendarGridView.saveModification(modification);
                CalendarGridView.showDropFeedback(dropZone, '✅ Match déplacé!');
            }
            
            // Re-render calendar after a brief delay
            setTimeout(() => {
                if (window.app && typeof window.app.reloadAndRender === 'function') {
                    window.app.reloadAndRender();
                } else {
                    console.warn('window.app.reloadAndRender not available');
                }
            }, 300);
            
        } catch (error) {
            console.error('Error handling drop:', error);
            CalendarGridView.showDropFeedback(dropZone, '❌ Erreur!');
        }
    }
    
    /**
     * Find match at specific position
     */
    static findMatchAtPosition(week, venue, time) {
        if (!window.allMatches) return null;
        
        return window.allMatches.find(m => 
            m.semaine === week && 
            m.gymnase === venue && 
            m.horaire === time
        );
    }
    
    /**
     * Valider un déplacement de match
     * Retourne {canMove: boolean, reason?: string, warnings?: string[]}
     */
    static validateMove(match, targetWeek, targetVenue, targetTime) {
        const warnings = [];
        
        // 1. Vérifier qu'il n'y a pas déjà un match à cet endroit
        const existingMatch = CalendarGridView.findMatchAtPosition(targetWeek, targetVenue, targetTime);
        if (existingMatch) {
            return {
                canMove: false,
                reason: 'Un match existe déjà à cet emplacement'
            };
        }
        
        // 2. Utiliser le détecteur de conflits si disponible
        if (window.conflictDetector) {
            // Créer une copie temporaire du match avec la nouvelle position
            const tempMatch = {
                ...match,
                semaine: targetWeek,
                horaire: targetTime,
                gymnase: targetVenue
            };
            
            const conflicts = window.conflictDetector.checkConflictsForMatch(tempMatch);
            
            // Séparer conflits critiques et avertissements
            const criticalConflicts = conflicts.filter(c => c.severity === 'critical');
            const warningConflicts = conflicts.filter(c => c.severity === 'warning');
            
            if (criticalConflicts.length > 0) {
                return {
                    canMove: false,
                    reason: `Conflit critique: ${criticalConflicts[0].message}`
                };
            }
            
            if (warningConflicts.length > 0) {
                warnings.push(...warningConflicts.map(c => c.message));
            }
        }
        
        // 3. Vérifier la disponibilité du créneau avec SlotManager
        if (window.slotManager) {
            const slotId = `${targetWeek}_${targetTime}_${targetVenue}`;
            const slot = window.slotManager.slots.get(slotId);
            
            if (slot && slot.statut === 'occupé' && slot.match_id !== match.match_id) {
                return {
                    canMove: false,
                    reason: 'Créneau déjà occupé'
                };
            }
        }
        
        return {
            canMove: true,
            warnings: warnings.length > 0 ? warnings : null
        };
    }
    
    /**
     * Valider un échange de matchs
     * Retourne {canSwap: boolean, reason?: string, warnings?: string[]}
     */
    static validateSwap(match1, match2) {
        const warnings = [];
        
        // 1. Utiliser le détecteur de conflits pour les deux positions
        if (window.conflictDetector) {
            // Match1 à la position de Match2
            const tempMatch1 = {
                ...match1,
                semaine: match2.semaine,
                horaire: match2.horaire,
                gymnase: match2.gymnase
            };
            
            // Match2 à la position de Match1
            const tempMatch2 = {
                ...match2,
                semaine: match1.semaine,
                horaire: match1.horaire,
                gymnase: match1.gymnase
            };
            
            const conflicts1 = window.conflictDetector.checkConflictsForMatch(tempMatch1);
            const conflicts2 = window.conflictDetector.checkConflictsForMatch(tempMatch2);
            
            const criticalConflicts = [
                ...conflicts1.filter(c => c.severity === 'critical'),
                ...conflicts2.filter(c => c.severity === 'critical')
            ];
            
            if (criticalConflicts.length > 0) {
                return {
                    canSwap: false,
                    reason: `Conflit critique: ${criticalConflicts[0].message}`
                };
            }
            
            const warningConflicts = [
                ...conflicts1.filter(c => c.severity === 'warning'),
                ...conflicts2.filter(c => c.severity === 'warning')
            ];
            
            if (warningConflicts.length > 0) {
                warnings.push(...warningConflicts.map(c => c.message));
            }
        }
        
        return {
            canSwap: true,
            warnings: warnings.length > 0 ? warnings : null
        };
    }
    
    /**
     * Save modification helper with slot management
     */
    static saveModification(modification) {
        // 1. Update slot manager: free old slot + occupy new slot
        if (window.slotManager) {
            const success = window.slotManager.moveMatch(
                modification.match_id,
                modification.original,  // old slot
                modification.new        // new slot
            );
            
            if (!success) {
                console.error('❌ SlotManager failed to move match');
                return;
            }
        } else {
            console.warn('⚠️ SlotManager not available');
        }
        
        // 2. Save modification via DataManager (qui notifiera automatiquement)
        if (window.dataManager) {
            window.dataManager.saveModification(modification);
        } else if (window.editModal && typeof window.editModal.saveModification === 'function') {
            // Fallback: ancien système
            window.editModal.saveModification(modification);
        } else {
            console.error('❌ Neither DataManager nor editModal available');
        }
    }
    
    /**
     * Calculate time slot from Y position in grid
     */
    static getTimeSlotFromPosition(dropZone, relativeY) {
        // Get all available time slots (assuming 15-min intervals from 8:00 to 22:00)
        const startHour = 8;
        const endHour = 22;
        const intervalMinutes = 15;
        
        const totalMinutes = (endHour - startHour) * 60;
        const slotCount = totalMinutes / intervalMinutes;
        
        const gridHeight = dropZone.offsetHeight;
        const slotHeight = gridHeight / slotCount;
        
        const slotIndex = Math.floor(relativeY / slotHeight);
        const minutesFromStart = slotIndex * intervalMinutes;
        
        const hour = startHour + Math.floor(minutesFromStart / 60);
        const minute = minutesFromStart % 60;
        
        return `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`;
    }
    
    /**
     * Show visual feedback after drop
     */
    static showDropFeedback(element, message, isError = false) {
        const feedback = document.createElement('div');
        feedback.className = `drop-feedback ${isError ? 'error' : 'success'}`;
        feedback.textContent = message;
        feedback.style.cssText = `
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: ${isError ? '#f44336' : '#4CAF50'};
            color: white;
            padding: 10px 20px;
            border-radius: 4px;
            font-weight: bold;
            z-index: 10000;
            pointer-events: none;
            animation: fadeInOut 2s ease;
        `;
        
        element.style.position = 'relative';
        element.appendChild(feedback);
        
        setTimeout(() => {
            if (feedback.parentNode) {
                feedback.parentNode.removeChild(feedback);
            }
        }, 2000);
    }
}
