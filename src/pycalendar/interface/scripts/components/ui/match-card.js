/**
 * match-card.js - Composant de carte de match réutilisable
 * 
 * Génère des cartes de match cohérentes pour toutes les vues.
 * Gère le drag & drop, l'édition, et l'affichage adaptatif.
 * Exposé globalement via window.MatchCard
 */

window.MatchCard = class MatchCard {
    /**
     * Constructeur
     * @param {Object} dataManager - Gestionnaire de données
     * @param {Object} modificationManager - Gestionnaire de modifications
     */
    constructor(dataManager, modificationManager) {
        this.dataManager = dataManager;
        this.modificationManager = modificationManager;
        this.draggedCard = null;
    }
    
    /**
     * Crée une carte de match
     * @param {Object} match - Données du match
     * @param {Object} options - Options d'affichage
     * @returns {HTMLElement} Élément DOM de la carte
     */
    create(match, options = {}) {
        const {
            showWeek = true,
            showPool = true,
            showTime = true,
            showInstitution = true,
            showGenre = true,
            showPenalties = false,
            draggable = true,
            compact = false,
            highlighted = []
        } = options;
        
        // Validation
        const validation = window.Validators.validateMatch(match);
        if (!validation.valid) {
        }
        
        // Récupérer les entités
        const data = this.dataManager.getData();
        const equipe1 = data.entities.equipes.find(e => e.id === match.equipes[0]);
        const equipe2 = data.entities.equipes.find(e => e.id === match.equipes[1]);
        const poule = data.entities.poules.find(p => equipe1?.poule === p.id);
        const gymnase = match.gymnase ? data.entities.gymnases.find(g => g.id === match.gymnase) : null;
        
        if (!equipe1 || !equipe2) {
            return this._createErrorCard(match);
        }
        
        // Créer l'élément
        const card = document.createElement('div');
        card.className = this._buildCardClasses(match, poule, compact);
        card.dataset.matchId = match.match_id;
        
        // Attributs pour drag & drop
        if (draggable && match.semaine) {
            card.draggable = true;
            card.addEventListener('dragstart', (e) => this._handleDragStart(e, match));
            card.addEventListener('dragend', (e) => this._handleDragEnd(e));
        }
        
        // Double-clic pour édition
        card.addEventListener('dblclick', () => this._handleEdit(match));
        
        // Construction du contenu
        card.innerHTML = `
            ${this._renderHeader(match, poule, { showWeek, showPool, showGenre, showTime })}
            ${this._renderTeams(equipe1, equipe2, { showInstitution, highlighted, compact })}
            ${this._renderFooter(match, gymnase, { showPenalties })}
        `;
        
        return card;
    }
    
    /**
     * Construit les classes CSS de la carte
     */
    _buildCardClasses(match, poule, compact) {
        const classes = ['match-card'];
        
        // Genre
        if (poule) {
            classes.push(`genre-${poule.genre.toLowerCase()}`);
            classes.push(`niveau-${poule.niveau.toLowerCase()}`);
        }
        
        // État
        if (!match.semaine) {
            classes.push('unscheduled');
        }
        
        if (match.is_fixed) {
            classes.push('fixed');
        }
        
        if (compact) {
            classes.push('compact');
        }
        
        // Score de pénalités
        if (match.penalties) {
            const totalPenalties = Object.values(match.penalties).reduce((sum, p) => sum + p, 0);
            if (totalPenalties > 10) {
                classes.push('high-penalties');
            } else if (totalPenalties > 5) {
                classes.push('medium-penalties');
            }
        }
        
        return classes.join(' ');
    }
    
    /**
     * Rendu de l'en-tête
     */
    _renderHeader(match, poule, options) {
        const { showWeek, showPool, showGenre, showTime } = options;
        
        const badges = [];
        
        if (showPool && poule) {
            badges.push(`<span class="badge badge-poule">${poule.nom}</span>`);
        }
        
        if (showGenre && poule) {
            const genderIcon = poule.genre === 'M' ? '♂' : '♀';
            badges.push(`<span class="badge badge-genre badge-${poule.genre.toLowerCase()}">
                ${genderIcon} ${window.Formatters.formatGenderShort(poule.genre)}
            </span>`);
        }
        
        if (poule) {
            badges.push(`<span class="badge badge-niveau">${poule.niveau}</span>`);
        }
        
        if (showWeek && match.semaine) {
            badges.push(`<span class="badge badge-semaine">📅 S${match.semaine}</span>`);
        }
        
        if (match.is_fixed) {
            badges.push(`<span class="badge badge-fixed">📌 Fixé</span>`);
        }
        
        return `
            <div class="match-header">
                <div class="match-badges">
                    ${badges.join('')}
                </div>
                ${showTime && match.horaire ? `
                    <div class="match-time">
                        <span class="time-icon">⏰</span>
                        <span class="time-value">${window.Formatters.formatTime(match.horaire)}</span>
                    </div>
                ` : ''}
                <button class="match-edit-btn" title="Éditer">
                    ✏️
                </button>
            </div>
        `;
    }
    
    /**
     * Rendu des équipes
     */
    _renderTeams(equipe1, equipe2, options) {
        const { showInstitution, highlighted, compact } = options;
        
        const team1Highlighted = highlighted.includes(equipe1.id);
        const team2Highlighted = highlighted.includes(equipe2.id);
        
        return `
            <div class="match-teams ${compact ? 'compact' : ''}">
                <div class="team team-1 ${team1Highlighted ? 'highlighted' : ''}">
                    <div class="team-name">${window.Formatters.formatTeamName(equipe1.nom, compact ? 25 : 40)}</div>
                    ${showInstitution && !compact ? `
                        <div class="team-institution">🏛️ ${equipe1.institution}</div>
                    ` : ''}
                </div>
                
                <div class="vs-divider">VS</div>
                
                <div class="team team-2 ${team2Highlighted ? 'highlighted' : ''}">
                    <div class="team-name">${window.Formatters.formatTeamName(equipe2.nom, compact ? 25 : 40)}</div>
                    ${showInstitution && !compact ? `
                        <div class="team-institution">🏛️ ${equipe2.institution}</div>
                    ` : ''}
                </div>
            </div>
        `;
    }
    
    /**
     * Rendu du pied de page
     */
    _renderFooter(match, gymnase, options) {
        const { showPenalties } = options;
        
        const parts = [];
        
        // Gymnase
        if (gymnase) {
            parts.push(`
                <div class="match-venue">
                    <span class="venue-icon">🏟️</span>
                    <span class="venue-name">${gymnase.nom}</span>
                </div>
            `);
        }
        
        // Pénalités
        if (showPenalties && match.penalties) {
            const totalPenalties = Object.values(match.penalties).reduce((sum, p) => sum + p, 0);
            const penaltyClass = totalPenalties > 10 ? 'high' : totalPenalties > 5 ? 'medium' : 'low';
            
            parts.push(`
                <div class="match-penalties">
                    <span class="penalty-icon">⚠️</span>
                    <span class="penalty-value penalty-${penaltyClass}">${totalPenalties.toFixed(1)}</span>
                </div>
            `);
        }
        
        if (parts.length === 0) {
            return '';
        }
        
        return `
            <div class="match-footer">
                ${parts.join('')}
            </div>
        `;
    }
    
    /**
     * Crée une carte d'erreur
     */
    _createErrorCard(match) {
        const card = document.createElement('div');
        card.className = 'match-card error';
        card.innerHTML = `
            <div class="match-error">
                <span class="error-icon">⚠️</span>
                <span class="error-message">Erreur: Match ${match.match_id} invalide</span>
            </div>
        `;
        return card;
    }
    
    /**
     * Gère le début du drag
     */
    _handleDragStart(event, match) {
        this.draggedCard = event.target;
        event.dataTransfer.effectAllowed = 'move';
        event.dataTransfer.setData('application/json', JSON.stringify(match));
        
        // Style visuel
        setTimeout(() => {
            event.target.classList.add('dragging');
        }, 0);
        
        // Notifier les drop zones
        document.dispatchEvent(new CustomEvent('match-drag-start', {
            detail: { match }
        }));
    }
    
    /**
     * Gère la fin du drag
     */
    _handleDragEnd(event) {
        event.target.classList.remove('dragging');
        this.draggedCard = null;
        
        // Notifier les drop zones
        document.dispatchEvent(new CustomEvent('match-drag-end'));
    }
    
    /**
     * Gère l'édition du match
     */
    _handleEdit(match) {
        // Émettre un événement pour ouvrir le modal d'édition
        document.dispatchEvent(new CustomEvent('match-edit-requested', {
            detail: { match }
        }));
    }
    
    /**
     * Crée une carte de match non planifié
     */
    createUnscheduledCard(match, options = {}) {
        return this.create(match, {
            ...options,
            showWeek: false,
            showTime: false,
            draggable: false
        });
    }
    
    /**
     * Crée une carte compacte
     */
    createCompactCard(match, options = {}) {
        return this.create(match, {
            ...options,
            compact: true,
            showInstitution: false,
            showPenalties: false
        });
    }
};
