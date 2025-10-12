#!/usr/bin/env python3
"""Script pour mettre à jour calendar-grid-view.js avec le nouveau système de sous-colonnes."""

import re

# Lire le fichier
with open('visualization/components/calendar-grid-view.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Nouvelle fonction renderMatchBlock
new_render_match_block = '''    /**
     * Bloc de match avec préférences d'affichage - NOUVEAU DESIGN
     */
    renderMatchBlock(match, pos, displayMode = 'week', preferences = {}) {
        const gender = Utils.getGender(match);
        const colorClass = gender === 'M' || gender === 'male' ? 'male' : gender === 'F' || gender === 'female' ? 'female' : 'mixed';
        
        // Déterminer le niveau de détail selon la hauteur réelle calculée
        const height = pos.height;
        const detailLevel = height < 70 ? 'minimal' : height < 150 ? 'compact' : 'full';
        
        // Icône genre
        const genderIcon = colorClass === 'male' ? '♂' : colorClass === 'female' ? '♀' : '⚥';
        
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
        
        // Extraire catégorie et numéro de poule (ex: "VBMA1PA" → catégorie:"VBM" niveau:"A1" poule:"PA")
        const pouleMatch = match.poule ? match.poule.match(/^([A-Z]+)([A-Z]\\d+)(.*)$/) : null;
        const category = pouleMatch ? pouleMatch[1] : '';
        const level = pouleMatch ? pouleMatch[2] : '';
        const poolNum = pouleMatch ? pouleMatch[3] : match.poule;
        
        // Tooltip enrichi avec TOUTES les infos
        const tooltipParts = [
            `${match.equipe1} vs ${match.equipe2}`,
            match.horaire ? `⏰ ${match.horaire}` : '',
            match.poule ? `🎯 ${match.poule}` : '',
            match.gymnase ? `🏢 ${match.gymnase}` : '',
            match.institution1 && match.institution2 ? `🏛️ ${match.institution1} vs ${match.institution2}` : '',
            match.equipe1_horaires_preferes && match.equipe1_horaires_preferes.length > 0 ? 
                `⏰ Préf. ${match.equipe1}: ${match.equipe1_horaires_preferes.join(', ')}` : '',
            match.equipe2_horaires_preferes && match.equipe2_horaires_preferes.length > 0 ? 
                `⏰ Préf. ${match.equipe2}: ${match.equipe2_horaires_preferes.join(', ')}` : ''
        ].filter(p => p).join('\\n');
        
        // Style de positionnement en sous-colonne
        const subColumnStyle = `top: ${pos.top}px; height: ${pos.height}px; left: ${leftPercent}%; width: ${widthPercent}%;`;
        
        // === RENDU MINIMAL (créneaux < 70px - granularité 30min ou 120min) ===
        if (detailLevel === 'minimal') {
            return `
                <div class="calendar-match-block calendar-match-${colorClass} detail-minimal" 
                     style="${subColumnStyle}"
                     title="${tooltipParts}">
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
            } else if (category) {
                contextBadge = `<span class="context-badge">${category}</span>`;
            }
            
            return `
                <div class="calendar-match-block calendar-match-${colorClass} detail-compact" 
                     style="${subColumnStyle}"
                     title="${tooltipParts}">
                    <div class="match-content-compact">
                        <div class="match-header-compact">
                            ${contextBadge}
                            <span class="gender-badge-compact">${genderIcon}</span>
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
        if (category && poolNum) {
            poolLine = `<div class="pool-line"><span class="category-badge">${category}</span> <span class="level-badge">${level}</span> <span class="pool-badge">${poolNum}</span></div>`;
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
        
        return `
            <div class="calendar-match-block calendar-match-${colorClass} detail-full" 
                 style="${subColumnStyle}"
                 title="${tooltipParts}">
                <div class="match-content-full">
                    <div class="match-header-full">
                        <span class="horaire-badge">${match.horaire}</span>
                        <span class="gender-badge-full">${genderIcon}</span>
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
    }'''

# Pattern pour trouver la fonction actuelle
pattern = r'    /\*\*\s*\n\s*\* Bloc de match avec préférences d\'affichage\s*\n\s*\*/\s*\n\s*renderMatchBlock\(match, pos, displayMode = \'week\', preferences = \{\}\) \{.*?\n    \}'

# Remplacer
new_content = re.sub(pattern, new_render_match_block, content, flags=re.DOTALL)

# Vérifier si le remplacement a fonctionné
if new_content == content:
    print("❌ ERREUR: Le pattern n'a pas été trouvé!")
    exit(1)

# Écrire le fichier modifié
with open('visualization/components/calendar-grid-view.js', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("✅ Fonction renderMatchBlock mise à jour avec succès!")
print(f"   Taille avant: {len(content)} caractères")
print(f"   Taille après: {len(new_content)} caractères")
