/**
 * PyCalendar Pro - Vue Pénalités
 * Affiche les matchs triés par pénalité pour identifier les matchs les plus contraints
 */

class PenaltiesView {
    /**
     * Rend la vue des matchs pénalisés
     */
    static render(matches, filters, preferences) {
        const container = document.getElementById('penalizedContent');
        
        if (matches.length === 0) {
            container.innerHTML = this.renderEmptyState();
            return;
        }
        
        // Trier les matchs par pénalité (décroissant)
        const sortedMatches = [...matches].sort((a, b) => (b.penalty || 0) - (a.penalty || 0));
        
        // Calculer statistiques
        const totalPenalty = sortedMatches.reduce((sum, m) => sum + (m.penalty || 0), 0);
        const avgPenalty = totalPenalty / sortedMatches.length;
        const maxPenalty = sortedMatches[0]?.penalty || 0;
        const matchesWithPenalty = sortedMatches.filter(m => (m.penalty || 0) > 0).length;
        
        let html = `
            <div class="penalties-header">
                <div class="penalties-stats">
                    <div class="penalty-stat">
                        <div class="stat-value">${matchesWithPenalty}</div>
                        <div class="stat-label">Matchs pénalisés</div>
                    </div>
                    <div class="penalty-stat">
                        <div class="stat-value">${totalPenalty.toFixed(1)}</div>
                        <div class="stat-label">Pénalité totale</div>
                    </div>
                    <div class="penalty-stat">
                        <div class="stat-value">${avgPenalty.toFixed(1)}</div>
                        <div class="stat-label">Pénalité moyenne</div>
                    </div>
                    <div class="penalty-stat">
                        <div class="stat-value">${maxPenalty.toFixed(1)}</div>
                        <div class="stat-label">Pénalité max</div>
                    </div>
                </div>
                <div class="penalties-description">
                    💰 Les matchs avec les pénalités les plus élevées sont ceux qui violent le plus de contraintes souples (horaires préférés, espacement entre matchs, etc.).
                </div>
            </div>
            
            <div class="penalties-list">
        `;
        
        // Grouper par niveau de pénalité pour un affichage plus clair
        const penaltyLevels = [
            { min: 100, max: Infinity, label: 'Très élevées (≥100)', color: '#dc2626', icon: '🔴' },
            { min: 50, max: 100, label: 'Élevées (50-100)', color: '#ea580c', icon: '🟠' },
            { min: 10, max: 50, label: 'Modérées (10-50)', color: '#f59e0b', icon: '🟡' },
            { min: 0.1, max: 10, label: 'Faibles (<10)', color: '#84cc16', icon: '🟢' },
            { min: 0, max: 0.1, label: 'Aucune pénalité', color: '#22c55e', icon: '✅' }
        ];
        
        penaltyLevels.forEach(level => {
            const levelMatches = sortedMatches.filter(m => {
                const penalty = m.penalty || 0;
                return penalty >= level.min && penalty < level.max;
            });
            
            if (levelMatches.length > 0) {
                html += `
                    <div class="penalty-level-section">
                        <div class="penalty-level-header">
                            <span class="penalty-level-icon">${level.icon}</span>
                            <span class="penalty-level-title">${level.label}</span>
                            <span class="penalty-level-count">${levelMatches.length} match${levelMatches.length > 1 ? 's' : ''}</span>
                        </div>
                        <div class="matches-grid">
                            ${levelMatches.map(m => this.renderPenaltyCard(m, filters, preferences)).join('')}
                        </div>
                    </div>
                `;
            }
        });
        
        html += `
            </div>
        `;
        
        container.innerHTML = html;
    }
    
    /**
     * Rend une carte de match avec informations de pénalité
     */
    static renderPenaltyCard(match, filters, preferences) {
        const penalty = match.penalty || 0;
        
        // Déterminer la couleur de la pénalité
        let penaltyColor = '#22c55e';
        if (penalty >= 100) penaltyColor = '#dc2626';
        else if (penalty >= 50) penaltyColor = '#ea580c';
        else if (penalty >= 10) penaltyColor = '#f59e0b';
        else if (penalty > 0) penaltyColor = '#84cc16';
        
        // Utiliser le MatchCard existant et ajouter l'indicateur de pénalité
        const baseCard = MatchCard.render(match, false, filters, preferences);
        
        // Ajouter un badge de pénalité en haut de la carte
        const penaltyBadge = `
            <div class="penalty-badge" style="background-color: ${penaltyColor}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600; margin-bottom: 8px; text-align: center;">
                💰 Pénalité: ${penalty.toFixed(1)}
            </div>
        `;
        
        // Insérer le badge au début de la carte
        return baseCard.replace('<div class="match-card', penaltyBadge + '<div class="match-card');
    }
    
    /**
     * Rend un état vide
     */
    static renderEmptyState() {
        return `
            <div style="padding: 60px 20px; text-align: center; color: #94a3b8;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">💰</div>
                <h3 style="color: #64748b; font-weight: 500; margin-bottom: 0.5rem;">Aucun match à afficher</h3>
                <p>Les pénalités des matchs apparaîtront ici</p>
            </div>
        `;
    }
}
