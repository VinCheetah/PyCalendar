/**
 * MatchCardRenderer - Génération optimisée des cartes de matchs
 * 
 * Responsabilités:
 * - Rendu des cartes individuelles de matchs
 * - Gestion des styles selon le contexte (compact, normal, conflits)
 * - Badges et indicateurs visuels
 * - Affichage enrichi: genre, préférences, championnat, numéro équipe
 */

class MatchCardRenderer {
    constructor(dataManager = null) {
        this.dataManager = dataManager;
        this.compactThreshold = 3; // À partir de 3 matchs, mode compact
    }
    
    /**
     * Génère une carte de match enrichie
     * @param {Object} match - Données du match
     * @param {boolean} isCompact - Mode compact
     * @param {number} index - Index du match dans le slot (pour numérotation)
     * @param {boolean} isDraggable - Le match peut être déplacé
     * @param {Object} conflicts - Conflits détectés (si applicable)
     * @returns {string} - HTML de la carte
     */
    renderMatchCard(match, isCompact = false, index = null, isDraggable = true, conflicts = null) {
        const classes = ['match-card'];
        if (isCompact) classes.push('match-card-compact');
        if (match.is_fixed) classes.push('match-fixed');
        if (match.is_external) classes.push('match-external');
        if (isDraggable && !match.is_fixed) classes.push('match-draggable');
        
        // Genre
        const genre = match.equipe1_genre || match.equipe2_genre;
        if (genre) {
            classes.push(genre === 'M' ? 'match-male' : 'match-female');
        }
        
        // Pénalités
        const hasPenalties = match.penalties && match.penalties.total > 0;
        const penaltyClass = this.getPenaltyClass(match.penalties?.total || 0);
        if (hasPenalties) classes.push(penaltyClass);
        
        // Conflits
        if (conflicts && conflicts.hasConflict) {
            classes.push(conflicts.level === 'critical' ? 'match-conflict-critical' : 'match-conflict-warning');
        }
        
        // Récupérer les données des équipes pour les préférences
        const equipe1Data = this.dataManager ? this.dataManager.getEquipe(match.equipe1_id) : null;
        const equipe2Data = this.dataManager ? this.dataManager.getEquipe(match.equipe2_id) : null;
        
        return `
            <div class="${classes.join(' ')}" 
                 data-match-id="${match.match_id}"
                 ${isDraggable && !match.is_fixed ? 'draggable="true"' : ''}
                 title="${this.buildMatchTooltip(match, equipe1Data, equipe2Data)}">
                
                ${conflicts && conflicts.hasConflict ? this.renderConflictBadge(conflicts) : ''}
                
                <div class="match-header">
                    ${this.renderMatchBadges(match)}
                    ${this.renderGenreIndicator(genre)}
                    ${match.horaire ? `<span class="match-time">${match.horaire}</span>` : ''}
                </div>
                
                <div class="match-teams">
                    ${this.renderTeam(
                        match.equipe1_nom, 
                        match.equipe1_num, 
                        match.equipe1_institution, 
                        equipe1Data,
                        isCompact
                    )}
                    <div class="match-vs">vs</div>
                    ${this.renderTeam(
                        match.equipe2_nom, 
                        match.equipe2_num, 
                        match.equipe2_institution, 
                        equipe2Data,
                        isCompact
                    )}
                </div>
                
                ${!isCompact ? this.renderMatchDetails(match) : ''}
                
                ${hasPenalties ? this.renderPenaltyIndicator(match.penalties) : ''}
            </div>
        `;
    }
    
    /**
     * Rendu d'une équipe avec toutes les informations
     */
    renderTeam(nom, num, institution, equipeData, isCompact) {
        const displayName = isCompact ? this.shortenName(nom) : nom;
        const displayNum = num ? `#${num}` : '';
        
        return `
            <div class="team-info" title="${nom} ${displayNum}${institution ? ` (${institution})` : ''}">
                <div class="team-name-row">
                    ${displayNum ? `<span class="team-num">${displayNum}</span>` : ''}
                    <span class="team-name">${displayName}</span>
                </div>
                ${!isCompact && institution ? `<span class="team-institution">${institution}</span>` : ''}
                ${!isCompact && equipeData ? this.renderTeamPreferences(equipeData) : ''}
            </div>
        `;
    }
    
    /**
     * Affiche les préférences d'une équipe (compact)
     */
    renderTeamPreferences(equipeData) {
        const prefs = [];
        
        if (equipeData.horaires_preferes && equipeData.horaires_preferes.length > 0) {
            prefs.push(`⏰ ${equipeData.horaires_preferes[0]}`);
        }
        
        if (equipeData.lieux_preferes && equipeData.lieux_preferes.length > 0) {
            prefs.push(`📍`);
        }
        
        if (prefs.length === 0) return '';
        
        return `<span class="team-prefs">${prefs.join(' ')}</span>`;
    }
    
    /**
     * Indicateur de genre
     */
    renderGenreIndicator(genre) {
        if (!genre) return '';
        
        const icon = genre === 'M' ? '♂️' : genre === 'F' ? '♀️' : '⚥';
        const label = genre === 'M' ? 'Masculin' : genre === 'F' ? 'Féminin' : 'Mixte';
        
        return `<span class="genre-indicator" title="${label}">${icon}</span>`;
    }
    
    /**
     * Badges du match (fixed, external, etc.)
     */
    renderMatchBadges(match) {
        const badges = [];
        
        if (match.is_fixed) {
            badges.push('<span class="match-badge badge-fixed" title="Match fixé">📌</span>');
        }
        
        if (match.is_external) {
            badges.push('<span class="match-badge badge-external" title="Match externe">🔗</span>');
        }
        
        if (match.is_entente) {
            badges.push('<span class="match-badge badge-entente" title="Entente">🤝</span>');
        }
        
        if (badges.length === 0) return '';
        
        return `<div class="match-badges">${badges.join('')}</div>`;
    }
    
    /**
     * Détails du match (poule/championnat, score si disponible)
     */
    renderMatchDetails(match) {
        const details = [];
        
        // Poule ou championnat
        if (match.poule && match.poule !== 'nan' && match.poule !== 'null') {
            details.push(`<span class="detail-poule" title="Poule">${match.poule}</span>`);
        } else if (match.championnat) {
            details.push(`<span class="detail-championnat" title="Championnat">${match.championnat}</span>`);
        }
        
        // Score si disponible
        if (match.score && match.score.has_score) {
            details.push(`
                <span class="detail-score" title="Score">
                    ${match.score.equipe1} - ${match.score.equipe2}
                </span>
            `);
        }
        
        if (details.length === 0) return '';
        
        return `<div class="match-details">${details.join(' • ')}</div>`;
    }
    
    /**
     * Construit un tooltip riche pour le match
     */
    buildMatchTooltip(match, equipe1Data, equipe2Data) {
        const lines = [];
        
        // Équipes
        lines.push(`${match.equipe1_nom} #${match.equipe1_num || '?'} vs ${match.equipe2_nom} #${match.equipe2_num || '?'}`);
        
        // Poule/Championnat
        if (match.poule && match.poule !== 'nan') {
            lines.push(`Poule: ${match.poule}`);
        } else if (match.championnat) {
            lines.push(`Championnat: ${match.championnat}`);
        }
        
        // Genre
        const genre = match.equipe1_genre || match.equipe2_genre;
        if (genre) {
            lines.push(`Genre: ${genre === 'M' ? 'Masculin' : 'Féminin'}`);
        }
        
        // Horaire et lieu
        if (match.horaire) {
            lines.push(`Horaire: ${match.horaire}`);
        }
        if (match.gymnase_nom) {
            lines.push(`Lieu: ${match.gymnase_nom}`);
        }
        
        // Préférences équipe 1
        if (equipe1Data) {
            const prefs1 = [];
            if (equipe1Data.horaires_preferes && equipe1Data.horaires_preferes.length > 0) {
                prefs1.push(`⏰ ${equipe1Data.horaires_preferes.join(', ')}`);
            }
            if (equipe1Data.lieux_preferes && equipe1Data.lieux_preferes.length > 0) {
                prefs1.push(`📍 ${equipe1Data.lieux_preferes.join(', ')}`);
            }
            if (prefs1.length > 0) {
                lines.push(`${match.equipe1_nom}: ${prefs1.join(' ')}`);
            }
        }
        
        // Préférences équipe 2
        if (equipe2Data) {
            const prefs2 = [];
            if (equipe2Data.horaires_preferes && equipe2Data.horaires_preferes.length > 0) {
                prefs2.push(`⏰ ${equipe2Data.horaires_preferes.join(', ')}`);
            }
            if (equipe2Data.lieux_preferes && equipe2Data.lieux_preferes.length > 0) {
                prefs2.push(`📍 ${equipe2Data.lieux_preferes.join(', ')}`);
            }
            if (prefs2.length > 0) {
                lines.push(`${match.equipe2_nom}: ${prefs2.join(' ')}`);
            }
        }
        
        // Pénalités
        if (match.penalties && match.penalties.total > 0) {
            lines.push(`⚡ Pénalités: ${match.penalties.total.toFixed(0)}`);
        }
        
        // Badges
        if (match.is_fixed) lines.push('📌 Match fixé');
        if (match.is_external) lines.push('🔗 Match externe');
        if (match.is_entente) lines.push('🤝 Entente');
        
        return lines.join('\n');
    }
    
    /**
     * Indicateur de pénalités avec tooltip
     */
    renderPenaltyIndicator(penalties) {
        const total = penalties.total || 0;
        const className = this.getPenaltyClass(total);
        const tooltip = this.buildPenaltyTooltip(penalties);
        
        return `
            <div class="penalty-indicator ${className}" title="${tooltip}">
                <span class="penalty-icon">⚡</span>
                <span class="penalty-value">${total.toFixed(0)}</span>
            </div>
        `;
    }
    
    /**
     * Badge d'avertissement de conflit (coin supérieur droit)
     * @param {Object} conflicts - Informations sur les conflits
     * @returns {string} - HTML du badge
     */
    renderConflictBadge(conflicts) {
        const isCritical = conflicts.level === 'critical';
        const icon = isCritical ? '🔴' : '🟡';
        const severity = isCritical ? 'critical' : 'warning';
        const tooltip = this.buildConflictTooltip(conflicts);
        
        return `
            <div class="match-conflict-badge match-conflict-${severity}">
                <span class="conflict-icon">${icon}</span>
                <div class="conflict-tooltip">${tooltip}</div>
            </div>
        `;
    }
    
    /**
     * Construit le tooltip des conflits enrichi et détaillé
     * @param {Object} conflicts - Informations sur les conflits
     * @returns {string} - HTML du tooltip
     */
    buildConflictTooltip(conflicts) {
        if (!conflicts || !conflicts.hasConflict) {
            return 'Aucun conflit';
        }
        
        const parts = [];
        
        // Titre avec sévérité
        const severityLabel = conflicts.severity === 'critical' 
            ? '<strong style="color: #ff4444;">🔴 CONFLIT CRITIQUE</strong>' 
            : '<strong style="color: #ffaa00;">🟡 AVERTISSEMENT</strong>';
        parts.push(severityLabel);
        
        // Détails des conflits
        if (conflicts.details && conflicts.details.length > 0) {
            parts.push('<div style="margin-top: 0.5rem;">');
            conflicts.details.forEach(detail => {
                parts.push(
                    `<div style="margin: 0.4rem 0; padding-left: 0.5rem; border-left: 2px solid rgba(255,255,255,0.3);">` +
                    `<div style="font-weight: 600;">${detail.icon} ${this.getConflictTypeLabel(detail.type)}</div>` +
                    `<div style="font-size: 0.75rem; opacity: 0.9; margin-top: 0.2rem;">${detail.message}</div>` +
                    `</div>`
                );
            });
            parts.push('</div>');
        }
        
        // Informations supplémentaires selon le type
        if (conflicts.types.includes('over_capacity')) {
            parts.push(
                '<div style="margin-top: 0.75rem; padding: 0.5rem; background: rgba(255,0,0,0.15); border-radius: 4px; font-size: 0.75rem;">' +
                '💡 <strong>Action requise:</strong> Certains matchs doivent être déplacés vers un autre créneau ou un autre gymnase.' +
                '</div>'
            );
        }
        
        if (conflicts.types.includes('team_duplicate')) {
            parts.push(
                '<div style="margin-top: 0.75rem; padding: 0.5rem; background: rgba(255,0,0,0.15); border-radius: 4px; font-size: 0.75rem;">' +
                '💡 <strong>Action requise:</strong> Une équipe ne peut pas jouer plusieurs matchs en même temps. Décalez l\'un des matchs.' +
                '</div>'
            );
        }
        
        return parts.join('');
    }
    
    /**
     * Retourne le label explicite d'un type de conflit
     */
    getConflictTypeLabel(type) {
        const labels = {
            'over_capacity': 'Dépassement de capacité',
            'team_duplicate': 'Équipe en double',
            'institution_overlap': 'Concentration d\'institutions'
        };
        return labels[type] || type;
    }
    
    /**
     * Construit le tooltip des pénalités
     */
    buildPenaltyTooltip(penalties) {
        const parts = [];
        
        if (penalties.horaire_prefere > 0) {
            parts.push(`⏰ Horaire: ${penalties.horaire_prefere.toFixed(1)}`);
        }
        if (penalties.espacement > 0) {
            parts.push(`📅 Espacement: ${penalties.espacement.toFixed(1)}`);
        }
        if (penalties.indisponibilite > 0) {
            parts.push(`🚫 Indispo: ${penalties.indisponibilite.toFixed(1)}`);
        }
        if (penalties.compaction > 0) {
            parts.push(`📦 Compaction: ${penalties.compaction.toFixed(1)}`);
        }
        if (penalties.overlap > 0) {
            parts.push(`🔀 Overlap: ${penalties.overlap.toFixed(1)}`);
        }
        
        return parts.length > 0 ? parts.join('\n') : 'Aucune pénalité';
    }
    
    /**
     * Classe CSS selon la sévérité de la pénalité
     */
    getPenaltyClass(total) {
        if (total === 0) return 'penalty-none';
        if (total < 20) return 'penalty-low';
        if (total < 50) return 'penalty-medium';
        if (total < 100) return 'penalty-high';
        return 'penalty-critical';
    }
    
    /**
     * Raccourcit un nom d'équipe pour le mode compact
     */
    shortenName(name) {
        // Garder juste l'institution et le numéro
        // Ex: "LYON 1 (5)" → "LYON 1 (5)"
        // Ex: "CENTRALE LYON (2)" → "CENTRALE (2)"
        if (name.length <= 15) return name;
        
        const match = name.match(/^(.+?)\s*\((\d+)\)$/);
        if (match) {
            const [, inst, num] = match;
            const shortInst = inst.split(' ').slice(0, 2).join(' ');
            return `${shortInst} (${num})`;
        }
        
        return name.substring(0, 15) + '...';
    }
}

// Export
if (typeof window !== 'undefined') {
    window.MatchCardRenderer = MatchCardRenderer;
}
