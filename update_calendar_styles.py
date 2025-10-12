#!/usr/bin/env python3
"""Script pour ajouter les nouveaux styles CSS pour le système de sous-colonnes."""

new_styles = '''

/* ==================== NOUVEAU DESIGN CALENDAR GRID - SOUS-COLONNES ==================== */

/* Ajustement du positionnement de base pour supporter les sous-colonnes */
.calendar-match-block {
    /* Le left et width sont maintenant définis inline via JavaScript */
    position: absolute;
    padding: 6px 4px;
    border-radius: 6px;
    border: 1.5px solid;
    box-shadow: 0 2px 8px rgba(0,0,0,0.12), 
                0 1px 3px rgba(0,0,0,0.08);
    cursor: pointer;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    overflow: hidden;
    z-index: 2;
    backdrop-filter: blur(4px);
}

/* Couleurs genre - Palette Bleu France cohérente */
.calendar-match-male {
    background: linear-gradient(135deg, 
        rgba(0, 85, 164, 0.95) 0%, 
        rgba(30, 58, 138, 0.90) 100%);
    border-color: #60A5FA;
}

.calendar-match-male:hover {
    background: linear-gradient(135deg, 
        rgba(0, 85, 164, 1) 0%, 
        rgba(30, 58, 138, 0.95) 100%);
    border-color: #93C5FD;
    box-shadow: 0 0 0 2px rgba(96, 165, 250, 0.4), 
                0 6px 20px rgba(59, 130, 246, 0.3);
}

.calendar-match-female {
    background: linear-gradient(135deg, 
        rgba(236, 72, 153, 0.95) 0%, 
        rgba(219, 39, 119, 0.90) 100%);
    border-color: #F9A8D4;
}

.calendar-match-female:hover {
    background: linear-gradient(135deg, 
        rgba(236, 72, 153, 1) 0%, 
        rgba(219, 39, 119, 0.95) 100%);
    border-color: #FBCFE8;
    box-shadow: 0 0 0 2px rgba(249, 168, 212, 0.4), 
                0 6px 20px rgba(236, 72, 153, 0.3);
}

.calendar-match-mixed {
    background: linear-gradient(135deg, 
        rgba(139, 92, 246, 0.95) 0%, 
        rgba(109, 40, 217, 0.90) 100%);
    border-color: #C4B5FD;
}

.calendar-match-mixed:hover {
    background: linear-gradient(135deg, 
        rgba(139, 92, 246, 1) 0%, 
        rgba(109, 40, 217, 0.95) 100%);
    border-color: #DDD6FE;
    box-shadow: 0 0 0 2px rgba(196, 181, 253, 0.4), 
                0 6px 20px rgba(139, 92, 246, 0.3);
}

/* ========== NIVEAU MINIMAL ========== */
.match-content-minimal {
    display: flex;
    flex-direction: column;
    justify-content: center;
    height: 100%;
    color: white;
}

.match-teams-minimal {
    display: flex;
    flex-direction: column;
    gap: 2px;
    font-size: 0.7rem;
    line-height: 1.2;
}

.team-name-minimal {
    font-weight: 600;
    text-align: center;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.match-vs-minimal {
    text-align: center;
    font-size: 0.6rem;
    opacity: 0.8;
    font-weight: 500;
}

/* ========== NIVEAU COMPACT ========== */
.match-content-compact {
    display: flex;
    flex-direction: column;
    height: 100%;
    color: white;
}

.match-header-compact {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 4px;
    padding-bottom: 3px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}

.context-badge {
    background: rgba(255, 255, 255, 0.15);
    color: white;
    padding: 2px 5px;
    border-radius: 3px;
    font-size: 0.65rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.3px;
}

.gender-badge-compact {
    font-size: 0.9rem;
    opacity: 0.9;
}

.match-teams-compact {
    display: flex;
    flex-direction: column;
    gap: 3px;
    flex: 1;
    justify-content: center;
}

.team-name-compact {
    font-weight: 600;
    font-size: 0.75rem;
    line-height: 1.2;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.match-vs-compact {
    text-align: center;
    font-size: 0.65rem;
    opacity: 0.7;
    font-weight: 500;
    margin: 1px 0;
}

/* ========== NIVEAU FULL ========== */
.match-content-full {
    display: flex;
    flex-direction: column;
    height: 100%;
    color: white;
}

.match-header-full {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
    padding-bottom: 4px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.25);
}

.horaire-badge {
    background: rgba(255, 255, 255, 0.2);
    color: white;
    padding: 3px 7px;
    border-radius: 4px;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.3px;
}

.gender-badge-full {
    font-size: 1.1rem;
    opacity: 0.95;
}

.match-teams-full {
    display: flex;
    flex-direction: column;
    gap: 4px;
    flex: 1;
}

.team-name-full {
    font-weight: 700;
    font-size: 0.8rem;
    line-height: 1.3;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.match-vs-full {
    text-align: center;
    font-size: 0.7rem;
    opacity: 0.75;
    font-weight: 600;
    margin: 2px 0;
}

.context-line {
    font-size: 0.7rem;
    opacity: 0.85;
    margin-top: 4px;
    padding-top: 4px;
    border-top: 1px solid rgba(255, 255, 255, 0.15);
}

.pool-line {
    display: flex;
    gap: 4px;
    align-items: center;
    margin-top: 4px;
    padding-top: 4px;
    border-top: 1px solid rgba(255, 255, 255, 0.15);
}

.category-badge {
    background: rgba(255, 255, 255, 0.25);
    color: white;
    padding: 2px 5px;
    border-radius: 3px;
    font-size: 0.65rem;
    font-weight: 700;
    text-transform: uppercase;
}

.level-badge {
    background: rgba(255, 255, 255, 0.15);
    color: white;
    padding: 2px 4px;
    border-radius: 3px;
    font-size: 0.6rem;
    font-weight: 600;
}

.pool-badge {
    background: rgba(255, 255, 255, 0.1);
    color: white;
    padding: 2px 4px;
    border-radius: 3px;
    font-size: 0.6rem;
    font-weight: 500;
}

.pref-line {
    font-size: 0.7rem;
    text-align: center;
    margin-top: 3px;
    opacity: 0.9;
}

/* Animations et transitions */
.calendar-match-block:hover {
    transform: scale(1.03);
    z-index: 10;
}

.calendar-match-block:active {
    transform: scale(0.98);
}

/* Responsive - adapter pour petites sous-colonnes */
@media (max-width: 1400px) {
    .team-name-full,
    .team-name-compact {
        font-size: 0.7rem;
    }
    
    .horaire-badge,
    .context-badge {
        font-size: 0.6rem;
        padding: 2px 4px;
    }
}
'''

# Lire le fichier actuel
with open('visualization/components/styles.css', 'r', encoding='utf-8') as f:
    content = f.read()

# Vérifier si les styles sont déjà présents
if 'NOUVEAU DESIGN CALENDAR GRID - SOUS-COLONNES' in content:
    print("⚠️  Les styles sont déjà présents. Suppression de l'ancienne version...")
    # Trouver le début de la section
    start_marker = '/* ==================== NOUVEAU DESIGN CALENDAR GRID - SOUS-COLONNES ==================== */'
    if start_marker in content:
        start_idx = content.find(start_marker)
        # Garder tout avant cette section
        content = content[:start_idx]

# Ajouter les nouveaux styles
content += new_styles

# Écrire le fichier mis à jour
with open('visualization/components/styles.css', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Nouveaux styles CSS ajoutés avec succès!")
print(f"   Taille totale: {len(content)} caractères")
print(f"   Nouveaux styles: {len(new_styles)} caractères")
