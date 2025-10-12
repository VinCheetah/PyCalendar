/**
 * PyCalendar Pro - Composants de Match
 * Rendu des cartes et blocs de match
 */

class MatchCard {
    /**
     * Rend une carte de match complète (pour vue cartes)
     */
    static render(match, isUnscheduled = false, filters = {}, preferences = {}) {
        const gender = Utils.getGender(match.poule);
        const category = Utils.getCategory(match.poule);
        const team1Class = Utils.shouldHighlight(match.equipe1, match.institution1, filters) ? 'team highlighted' : 'team';
        const team2Class = Utils.shouldHighlight(match.equipe2, match.institution2, filters) ? 'team highlighted' : 'team';
        
        const showInst = preferences.showInstitutions !== false;
        const showGenre = preferences.showGenreBadges !== false;
        
        // Icônes de genre
        const genderIcon = gender === 'male' ? '♂' : gender === 'female' ? '♀' : '⚥';
        
        return `
            <div class="match-card ${gender} ${isUnscheduled ? 'unscheduled' : ''}" 
                 data-match-id="${match.equipe1}_${match.equipe2}_${match.poule}"
                 data-tooltip="${match.equipe1} vs ${match.equipe2}">
                
                <!-- En-tête avec badges et horaire -->
                <div class="match-header">
                    <div class="match-badges">
                        <span class="badge badge-poule">${Utils.escapeHtml(match.poule)}</span>
                        ${showGenre ? `<span class="badge badge-gender-${gender}">${genderIcon} ${gender === 'male' ? 'M' : 'F'}</span>` : ''}
                        <span class="badge badge-cat-${category}">${category.toUpperCase()}</span>
                        ${isUnscheduled ? '<span class="badge badge-unscheduled">⚠️ Non planifié</span>' : ''}
                    </div>
                    ${!isUnscheduled ? `
                        <div class="match-time">
                            <span class="time-icon">⏰</span>
                            <span class="time-value">${Utils.escapeHtml(match.horaire)}</span>
                        </div>
                    ` : ''}
                </div>
                
                <!-- Section équipes - Symétrique et claire -->
                <div class="match-teams-container">
                    <!-- Équipe 1 -->
                    <div class="team-block team-1">
                        ${Utils.formatHorairesLeft(match.equipe1_horaires_preferes)}
                        <div class="${team1Class}">
                            <span class="team-name">${Utils.escapeHtml(match.equipe1)}</span>
                        </div>
                        ${showInst ? `<div class="team-institution">🏛️ ${Utils.escapeHtml(match.institution1)}</div>` : ''}
                    </div>
                    
                    <!-- Séparateur VS central -->
                    <div class="vs-divider">
                        <div class="vs-circle">
                            <span class="vs-text">VS</span>
                        </div>
                    </div>
                    
                    <!-- Équipe 2 -->
                    <div class="team-block team-2">
                        ${Utils.formatHorairesRight(match.equipe2_horaires_preferes)}
                        <div class="${team2Class}">
                            <span class="team-name">${Utils.escapeHtml(match.equipe2)}</span>
                        </div>
                        ${showInst ? `<div class="team-institution">🏛️ ${Utils.escapeHtml(match.institution2)}</div>` : ''}
                    </div>
                </div>
                
                <!-- Pied avec gymnase ou alerte -->
                ${!isUnscheduled ? `
                    <div class="match-footer">
                        <div class="match-venue">
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
}

// Export pour utilisation
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MatchCard;
}
