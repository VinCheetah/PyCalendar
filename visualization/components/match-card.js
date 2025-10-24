/**
 * PyCalendar Pro - Composants de Match
 * Rendu des cartes et blocs de match
 */

class MatchCard {
    /**
     * Rend une carte de match complète (pour vue cartes)
     * @param {Object} match - Données du match
     * @param {boolean} isUnscheduled - Si le match est non planifié
     * @param {Object} filters - Filtres actifs
     * @param {Object} preferences - Préférences d'affichage
     * @param {boolean} showWeekBadge - Si true, affiche le badge de semaine (par défaut: true pour vues gymnase/poule/pénalités, false pour vue semaine)
     * @param {boolean} showPoolBadge - Si true, affiche le badge de poule (par défaut: true pour vues gymnase/semaine, false pour vue poule)
     */
    static render(match, isUnscheduled = false, filters = {}, preferences = {}, showWeekBadge = true, showPoolBadge = true) {
        const gender = Utils.getGender(match.poule);
        const category = Utils.getCategory(match.poule);
        const team1Class = Utils.shouldHighlight(match.equipe1, match.institution1, filters) ? 'team highlighted' : 'team';
        const team2Class = Utils.shouldHighlight(match.equipe2, match.institution2, filters) ? 'team highlighted' : 'team';
        
        const showInst = preferences.showInstitutions !== false;
        const showGenre = preferences.showGenreBadges !== false;
        
        // Contrôle intelligent des badges via préférences
        const showWeek = showWeekBadge && preferences.showWeekBadges !== false;
        const showPool = showPoolBadge && preferences.showPoolBadges !== false;
        
        // Icônes de genre
        const genderIcon = gender === 'male' ? '♂' : gender === 'female' ? '♀' : '⚥';
        
        // Use match_id from data (double underscore format from Phase 1)
        const matchId = match.match_id || `${match.equipe1}_${match.equipe2}_${match.poule}`;
        
        // Prepare match data for drag-and-drop
        const matchData = JSON.stringify({
            match_id: matchId,
            equipe1: match.equipe1,
            equipe2: match.equipe2,
            poule: match.poule,
            semaine: match.semaine,
            horaire: match.horaire,
            gymnase: match.gymnase
        }).replace(/"/g, '&quot;');
        
        return `
            <div class="match-card ${gender} ${isUnscheduled ? 'unscheduled' : ''} ${!match.has_score ? 'no-score' : ''} ${!match.is_fixed && !isUnscheduled ? 'auto-scheduled' : ''}" 
                 data-match-id="${matchId}"
                 data-gender="${gender}"
                 data-category="${category}"
                 data-pool="${Utils.escapeHtml(match.poule)}"
                 data-institution1="${Utils.escapeHtml(match.institution1)}"
                 data-institution2="${Utils.escapeHtml(match.institution2)}"
                 data-match-data="${matchData}"
                 data-tooltip="${match.equipe1} vs ${match.equipe2}"
                 ${!isUnscheduled ? 'draggable="true"' : ''}
                 ondragstart="MatchCard.handleDragStart(event)"
                 ondragend="MatchCard.handleDragEnd(event)">
                
                ${!isUnscheduled ? `
                    <button class="match-edit-btn" onclick="editModal.open({
                        match_id: '${matchId}',
                        equipe1: '${Utils.escapeHtml(match.equipe1).replace(/'/g, "\\'")}',
                        equipe2: '${Utils.escapeHtml(match.equipe2).replace(/'/g, "\\'")}',
                        poule: '${Utils.escapeHtml(match.poule)}',
                        semaine: ${match.semaine},
                        horaire: '${Utils.escapeHtml(match.horaire)}',
                        gymnase: '${Utils.escapeHtml(match.gymnase)}'
                    }, this.closest('.match-card'))">✏️</button>
                ` : ''}
                
                <div class="match-header">
                    <div class="match-badges">
                        ${showPool ? `<span class="badge badge-poule">${Utils.escapeHtml(match.poule)}</span>` : ''}
                        ${showGenre ? `<span class="badge badge-gender-${gender}">${genderIcon} ${gender === 'male' ? 'M' : 'F'}</span>` : ''}
                        <span class="badge badge-cat-${category}">${category.toUpperCase()}</span>
                        ${showWeek && !isUnscheduled ? `<span class="badge badge-week">📅 S${match.semaine}</span>` : ''}
                        ${!match.has_score && !isUnscheduled && match.is_fixed ? '<span class="badge badge-no-score">⏳ Score attendu</span>' : ''}
                        ${isUnscheduled ? '<span class="badge badge-unscheduled">⚠️ Non planifié</span>' : ''}
                    </div>
                    ${!isUnscheduled ? `
                        <div class="match-time">
                            <span class="time-icon">⏰</span>
                            <span class="time-value match-time">${Utils.escapeHtml(match.horaire)}</span>
                        </div>
                    ` : ''}
                </div>
                
                <div class="match-teams-container">
                    <div class="team-block team-1">
                        ${Utils.formatHorairesLeft(match.equipe1_horaires_preferes)}
                        <div class="${team1Class}">
                            <span class="team-name">${Utils.escapeHtml(match.equipe1)}</span>
                        </div>
                        ${showInst ? `<div class="team-institution">🏛️ ${Utils.escapeHtml(match.institution1)}</div>` : ''}
                    </div>
                    
                    <div class="vs-divider">
                        ${match.score ? `
                            <div class="score-display">
                                <span class="score-text">${match.score}</span>
                            </div>
                        ` : `
                            <div class="vs-circle">
                                <span class="vs-text">VS</span>
                            </div>
                        `}
                    </div>
                    
                    <div class="team-block team-2">
                        ${Utils.formatHorairesRight(match.equipe2_horaires_preferes)}
                        <div class="${team2Class}">
                            <span class="team-name">${Utils.escapeHtml(match.equipe2)}</span>
                        </div>
                        ${showInst ? `<div class="team-institution">🏛️ ${Utils.escapeHtml(match.institution2)}</div>` : ''}
                    </div>
                </div>
                
                ${!isUnscheduled ? `
                    <div class="match-footer">
                        <div class="match-venue match-venue">
                            <span class="venue-icon">🏢</span>
                            <span class="venue-name">${Utils.escapeHtml(match.gymnase)}</span>
                        </div>
                    </div>
                ` : `
                    <div class="match-footer unscheduled">
                        <div class="unscheduled-alert">
                            <span class="alert-icon">❌</span>
                            <span class="alert-text">Match non planifié</span>
                        </div>
                    </div>
                `}
            </div>
        `;
    }
    
    /**
     * Handle drag start event
     */
    static handleDragStart(e) {
        const card = e.currentTarget;
        const matchData = card.getAttribute('data-match-data');
        
        if (!matchData) return;
        
        // Set drag data
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('application/json', matchData.replace(/&quot;/g, '"'));
        e.dataTransfer.setData('text/plain', card.getAttribute('data-match-id'));
        
        // Visual feedback
        card.classList.add('dragging');
        card.style.opacity = '0.4';
        
        // Store dragged element reference
        window.draggedMatchCard = card;
    }
    
    /**
     * Handle drag end event
     */
    static handleDragEnd(e) {
        const card = e.currentTarget;
        
        // Remove visual feedback
        card.classList.remove('dragging');
        card.style.opacity = '1';
        
        // Clean up reference
        window.draggedMatchCard = null;
        
        // Remove all drop zone highlighting
        document.querySelectorAll('.drop-zone-active, .drop-zone-invalid').forEach(el => {
            el.classList.remove('drop-zone-active', 'drop-zone-invalid');
        });
    }
}

// Export pour utilisation
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MatchCard;
}
