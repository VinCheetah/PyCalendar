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
        
        // Genre - Add proper classes for color coding
        const genre = match.equipe1_genre || match.equipe2_genre;
        if (genre) {
            if (genre === 'M') {
                classes.push('match-male', 'male');
            } else if (genre === 'F') {
                classes.push('match-female', 'female');
            } else if (genre === 'X') {
                classes.push('mixed');
            }
        }
        
        // Niveau/Catégorie - Extract from match data
        const category = this.extractCategory(match);
        
        // Classes spéciales pour CFU et CFE
        if (category === 'CFU') {
            classes.push('match-cfu');
        } else if (category === 'CFE') {
            classes.push('match-cfe');
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
        
        const html = `
            <div class="${classes.join(' ')}" 
                 data-match-id="${match.match_id}"
                 data-category="${category}"
                 data-genre="${genre || ''}"
                 data-penalties="${match.penalties?.total || 0}"
                 ${isDraggable && !match.is_fixed ? 'draggable="true"' : ''}>
                
                <div class="match-card-content" title="${this.buildMatchTooltip(match, equipe1Data, equipe2Data)}" style="display: flex; flex-direction: column; height: 100%; font-size: 0.7rem;">
                    
                    <div class="match-header" style="margin-bottom: 0.3rem; padding-bottom: 0.3rem; border-bottom: 1px solid rgba(255, 255, 255, 0.25); display: flex; justify-content: space-between; align-items: flex-start;">
                        <div class="match-header-left" style="display: flex; align-items: center; gap: 0.3rem; flex-wrap: wrap;">
                            ${this.renderMatchBadges(match)}
                            ${this.renderGenreIndicator(genre)}
                            ${this.renderCompactCategory(match)}
                        </div>
                        <div class="match-header-right" style="display: flex; align-items: center; gap: 0.3rem; flex-wrap: wrap;">
                            ${conflicts && conflicts.hasConflict ? this.renderConflictBadge(conflicts) : ''}
                            ${match.horaire ? `<span class="match-time" style="font-size: 0.625rem; font-weight: 800; padding: 0.15rem 0.4rem; background: rgba(255, 255, 255, 0.3); border-radius: 4px; font-family: 'Roboto Mono', monospace; letter-spacing: 0.03em; box-shadow: 0 1px 2px rgba(0, 0, 0, 0.15); border: 1px solid rgba(255, 255, 255, 0.2);">${match.horaire}</span>` : ''}
                        </div>
                    </div>
                    
                    <div class="match-teams" style="display: flex; flex-direction: column; gap: 0.3rem; flex: 1;">
                        ${this.renderTeamCompact(
                            match.equipe1_nom, 
                            match.equipe1_num,
                            equipe1Data,
                            match
                        )}
                        <div class="match-vs" style="font-size: 0.625rem; font-weight: 900; margin: 0.3rem 0; opacity: 0.8; text-transform: uppercase; letter-spacing: 0.1em; color: rgba(255, 255, 255, 0.9); text-align: center; font-family: 'Roboto', sans-serif;">vs</div>
                        ${this.renderTeamCompact(
                            match.equipe2_nom, 
                            match.equipe2_num,
                            equipe2Data,
                            match
                        )}
                    </div>
                    
                    ${this.renderCompactMatchInfo(match)}
                    
                </div>
                ${hasPenalties ? this.renderPenaltyIndicator(match.penalties) : ''}
            </div>
        `;
        
        return html;
    }
    
    /**
     * Rendu d'une équipe avec toutes les informations
     */
    renderTeam(nom, num, institution, equipeData, isCompact) {
        const displayName = isCompact ? this.shortenName(nom) : nom;
        const displayNum = num ? `#${num}` : '';
        const fullTitle = `${nom} ${displayNum}${institution ? ` (${institution})` : ''}`;
        
        return `
            <div class="team-info" title="${fullTitle}">
                <div class="team-name-row">
                    ${displayNum ? `<span class="team-num">${displayNum}</span>` : ''}
                    <span class="team-name">${displayName}</span>
                </div>
                ${!isCompact && institution ? `<span class="team-institution">${this.shortenInstitution(institution)}</span>` : ''}
            </div>
        `;
    }
    
    /**
     * Rendu compact d'une équipe (sans institution, plus petit)
     */
    renderTeamCompact(nom, num, equipeData, match) {
        const displayName = this.shortenName(nom);
        const displayNum = num ? `#${num}` : '';
        
        // Horaires préférés - afficher SEULEMENT si l'horaire n'est PAS préféré
        let prefTimeDisplay = '';
        
        if (equipeData && equipeData.horaires_preferes && equipeData.horaires_preferes.length > 0) {
            const matchTime = match.horaire;
            const preferredTime = equipeData.horaires_preferes[0]; // Premier horaire préféré
            const hasPreferredTime = matchTime && matchTime.includes(preferredTime);
            
            if (!hasPreferredTime) {
                // L'horaire n'est PAS préféré - afficher l'horaire préféré
                prefTimeDisplay = `<span class="pref-time" style="font-size: 0.625rem; font-weight: 700; padding: 0.15rem 0.4rem; background: rgba(255, 223, 0, 0.25); border-radius: 4px; display: inline-flex; align-items: center; gap: 0.15rem; border: 1px solid rgba(255, 223, 0, 0.4); box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2), 0 0 8px rgba(255, 223, 0, 0.3); font-family: 'Roboto Mono', monospace; letter-spacing: 0.03em;" title="Horaire préféré">⏰${preferredTime}</span>`;
            }
        }
        
        return `
            <div class="team-info-compact" style="display: flex; flex-direction: row; align-items: center; gap: 0.3rem; width: 100%;">
                ${displayNum ? `<span class="team-num-compact" style="font-size: 0.65rem; font-weight: 800; background: rgba(255, 255, 255, 0.25); padding: 0.15rem 0.35rem; border-radius: 4px; letter-spacing: 0.03em; font-family: 'Roboto Mono', 'Courier New', monospace; box-shadow: 0 1px 2px rgba(0, 0, 0, 0.15); border: 1px solid rgba(255, 255, 255, 0.15);">${displayNum}</span>` : ''}
                <div class="team-content" style="display: flex; flex-direction: column; gap: 0.15rem; flex: 1; min-width: 0;">
                    <span class="team-name-compact" style="font-size: 0.75rem; font-weight: 700; line-height: 1.3; text-shadow: 0 1px 3px rgba(0, 0, 0, 0.3); letter-spacing: 0.02em; font-family: 'Inter', 'Segoe UI', -apple-system, sans-serif; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${displayName}</span>
                    ${prefTimeDisplay}
                </div>
            </div>
        `;
    }
    
    /**
     * Raccourcit le nom d'une institution
     */
    shortenInstitution(institution) {
        if (!institution) return '';
        if (institution.length <= 25) return institution;
        return institution.substring(0, 22) + '...';
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
        
        return `<span class="genre-indicator" style="font-size: 0.8rem; filter: drop-shadow(0 1px 3px rgba(0, 0, 0, 0.3)); margin-right: 0.15rem;" title="${label}">${icon}</span>`;
    }
    
    /**
     * Catégorie/Niveau compact
     */
    renderCompactCategory(match) {
        const category = this.extractCategory(match);
        if (!category) return '';
        
        // Ne pas afficher CFU et CFE ici car ils sont déjà affichés comme badges
        const isCFU = category === 'CFU';
        const isCFE = category === 'CFE';
        
        if (isCFU || isCFE) {
            return ''; // Les badges CFU/CFE sont gérés par renderMatchBadges
        }
        
        let cssClass = 'category-compact';
        let title = 'Niveau';
        let inlineStyle = 'font-size: 0.65rem; font-weight: 900; padding: 0.15rem 0.4rem; border-radius: 4px;';
        
        return `<span class="${cssClass}" style="${inlineStyle}" title="${title}">${category}</span>`;
    }
    
    /**
     * Informations compactes du match (poule + score + horaires préférés)
     */
    renderCompactMatchInfo(match) {
        const info = [];
        
        // Poule
        if (match.poule && match.poule !== 'nan' && match.poule !== 'null') {
            info.push(`<span class="info-poule" style="font-weight: 800; padding: 0.15rem 0.4rem; background: rgba(255, 255, 255, 0.3); border-radius: 4px; text-transform: uppercase; letter-spacing: 0.05em; font-family: 'Roboto', sans-serif; box-shadow: 0 1px 2px rgba(0, 0, 0, 0.15); border: 1px solid rgba(255, 255, 255, 0.2);">${match.poule}</span>`);
        }
        
        // Score si disponible - vérifier tous les champs nécessaires
        if (match.score && match.score.has_score && 
            match.score.equipe1 !== null && match.score.equipe1 !== undefined &&
            match.score.equipe2 !== null && match.score.equipe2 !== undefined) {
            info.push(`<span class="info-score" style="font-weight: 900; padding: 0.2rem 0.5rem; background: rgba(255, 255, 255, 0.4); border-radius: 5px; letter-spacing: 0.08em; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.25); font-family: 'Roboto Mono', monospace; font-size: 0.7rem; border: 1px solid rgba(255, 255, 255, 0.25);">${match.score.equipe1}-${match.score.equipe2}</span>`);
        }
        
        if (info.length === 0) return '';
        
        return `<div class="match-info-compact" style="display: flex; gap: 0.4rem; align-items: center; justify-content: center; margin-top: 0.4rem; padding-top: 0.4rem; border-top: 1px solid rgba(255, 255, 255, 0.3); font-size: 0.625rem;">${info.join(' ')}</div>`;
    }
    
    /**
     * Badges du match (fixed, external, etc.)
     */
    renderMatchBadges(match) {
        const badges = [];
        
        if (match.is_fixed) {
            badges.push('<span class="match-badge badge-fixed" style="font-size: 0.7rem; padding: 0.15rem 0.3rem; border-radius: 4px; background: rgba(255, 255, 255, 0.25); box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);" title="Match fixé">📌</span>');
        }
        
        if (match.is_external) {
            badges.push('<span class="match-badge badge-external" style="font-size: 0.7rem; padding: 0.15rem 0.3rem; border-radius: 4px; background: rgba(255, 255, 255, 0.25); box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);" title="Match externe">🔗</span>');
        }
        
        if (match.is_entente) {
            badges.push('<span class="match-badge badge-entente" style="font-size: 0.7rem; padding: 0.15rem 0.3rem; border-radius: 4px; background: rgba(255, 255, 255, 0.25); box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);" title="Entente">🤝</span>');
        }
        
        // Badge spécial pour CFU
        const category = this.extractCategory(match);
        if (category === 'CFU') {
            badges.push('<span class="match-badge badge-cfu" style="font-size: 0.75rem; padding: 0.2rem 0.5rem; border-radius: 5px; background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%); color: #000; border: 2px solid #FFB700; box-shadow: 0 2px 8px rgba(255, 215, 0, 0.5), 0 0 15px rgba(255, 215, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.5); text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3); font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;" title="Championnat de France Universitaire">CFU</span>');
        }
        
        // Badge spécial pour CFE
        if (category === 'CFE') {
            badges.push('<span class="match-badge badge-cfe" style="font-size: 0.75rem; padding: 0.2rem 0.5rem; border-radius: 5px; background: linear-gradient(135deg, #4A90E2 0%, #357ABD 100%); color: #FFF; border: 2px solid #2E5F8D; box-shadow: 0 2px 8px rgba(74, 144, 226, 0.5), 0 0 15px rgba(74, 144, 226, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.3); text-shadow: 0 1px 3px rgba(0, 0, 0, 0.4); font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;" title="Championnat de France Établissement">CFE</span>');
        }
        
        return badges.join(' ');
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
        if (total === 0) return '';
        
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
        const icon = '⚠️';
        const severity = isCritical ? 'critical' : 'warning';
        const tooltip = this.buildConflictTooltip(conflicts);
        
        return `
            <div class="match-conflict-badge match-conflict-${severity}" title="${tooltip}">
                <span class="conflict-icon">${icon}</span>
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
        const severityLabel = conflicts.level === 'critical' 
            ? '🔴 CONFLIT CRITIQUE' 
            : '🟡 AVERTISSEMENT';
        parts.push(severityLabel);
        
        // Détails des conflits
        if (conflicts.details && conflicts.details.length > 0) {
            conflicts.details.forEach(detail => {
                parts.push(
                    `\n- ${this.getConflictTypeLabel(detail.type)}: ${detail.message}`
                );
            });
        }
        
        // Informations supplémentaires
        if (conflicts.types.includes('over_capacity')) {
            parts.push('\n\nAction requise: Déplacez des matchs vers un autre créneau/gymnase.');
        }
        if (conflicts.types.includes('team_duplicate')) {
            parts.push('\n\nAction requise: Une équipe ne peut pas jouer deux matchs en même temps.');
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
            parts.push(`⏰ Horaire préféré: ${penalties.horaire_prefere.toFixed(1)}`);
        }
        if (penalties.gymnase_prefere > 0) {
            parts.push(`🏟️ Gymnase préféré: ${penalties.gymnase_prefere.toFixed(1)}`);
        }
        if (penalties.niveau_gymnase > 0) {
            parts.push(`📊 Niveau gymnase: ${penalties.niveau_gymnase.toFixed(1)}`);
        }
        if (penalties.espacement > 0) {
            parts.push(`📅 Espacement: ${penalties.espacement.toFixed(1)}`);
        }
        if (penalties.compaction > 0) {
            parts.push(`📦 Compaction: ${penalties.compaction.toFixed(1)}`);
        }
        if (penalties.overlap_institution > 0) {
            parts.push(`🔀 Overlap institution: ${penalties.overlap_institution.toFixed(1)}`);
        }
        if (penalties.aller_retour > 0) {
            parts.push(`↔️ Aller-retour: ${penalties.aller_retour.toFixed(1)}`);
        }
        if (penalties.contrainte_temporelle > 0) {
            parts.push(`⏱️ Contrainte temporelle: ${penalties.contrainte_temporelle.toFixed(1)}`);
        }
        if (penalties.guidance_qualite > 0) {
            parts.push(`⚠️ Guidance qualité: ${penalties.guidance_qualite.toFixed(1)}`);
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
    
    /**
    /**
     * Extrait la catégorie/niveau du match (A1, A2, A3, A4, CFE, CFU)
     * Cherche dans le nom des équipes ou dans les données du match
     */
    extractCategory(match) {
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
}

// Export
if (typeof window !== 'undefined') {
    window.MatchCardRenderer = MatchCardRenderer;
}
