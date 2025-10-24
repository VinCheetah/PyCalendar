/**
 * PyCalendar Pro - Vue Cartes
 * Gère les vues par semaine, poule, gymnase avec cartes de matchs
 */

class CalendarView {
    /**
     * Rend la vue par semaines
     */
    static renderByWeek(matches, filters, preferences) {
        const container = document.getElementById('calendarContent');
        
        if (matches.length === 0) {
            container.innerHTML = this.renderEmptyState();
            return;
        }
        
        // Grouper par semaine
        const byWeek = Utils.groupBy(matches, m => m.semaine);
        
        let html = '';
        Object.keys(byWeek).sort((a, b) => a - b).forEach(week => {
            const weekMatches = byWeek[week];
            html += `
                <section class="week-section">
                    <div class="week-header">
                        <div class="week-title">📅 Semaine ${week}</div>
                        <div class="week-count">${weekMatches.length} match${weekMatches.length > 1 ? 's' : ''}</div>
                    </div>
                    <div class="matches-grid">
                        ${weekMatches.map(m => MatchCard.render(m, false, filters, preferences, false, true)).join('')}
                    </div>
                </section>
            `;
        });
        
        container.innerHTML = html;
    }

    /**
     * Rend la vue par poules
     */
    static renderByPool(matches, filters, preferences) {
        const container = document.getElementById('poolsContent');
        
        if (matches.length === 0) {
            container.innerHTML = this.renderEmptyState();
            return;
        }
        
        // Grouper par poule
        const byPool = Utils.groupBy(matches, m => m.poule);
        
        let html = '';
        Object.keys(byPool).sort().forEach(pool => {
            const poolMatches = byPool[pool];
            html += `
                <section class="week-section">
                    <div class="week-header">
                        <div class="week-title">🎯 ${pool}</div>
                        <div class="week-count">${poolMatches.length} match${poolMatches.length > 1 ? 's' : ''}</div>
                    </div>
                    <div class="matches-grid">
                        ${poolMatches.map(m => MatchCard.render(m, false, filters, preferences, true, false)).join('')}
                    </div>
                </section>
            `;
        });
        
        container.innerHTML = html;
    }

    /**
     * Rend la vue par gymnases
     */
    static renderByVenue(matches, filters, preferences) {
        const container = document.getElementById('venuesContent');
        
        if (matches.length === 0) {
            container.innerHTML = this.renderEmptyState();
            return;
        }
        
        // Grouper par gymnase
        const byVenue = Utils.groupBy(matches, m => m.gymnase);
        
        let html = '';
        Object.keys(byVenue).sort().forEach(venue => {
            const venueMatches = byVenue[venue];
            html += `
                <section class="week-section">
                    <div class="week-header">
                        <div class="week-title">🏢 ${venue}</div>
                        <div class="week-count">${venueMatches.length} match${venueMatches.length > 1 ? 's' : ''}</div>
                    </div>
                    <div class="matches-grid">
                        ${venueMatches.map(m => MatchCard.render(m, false, filters, preferences, true, true)).join('')}
                    </div>
                </section>
            `;
        });
        
        container.innerHTML = html;
    }

    /**
     * Rend la vue des matchs non planifiés
     */
    static renderUnscheduled(matches, filters, preferences) {
        const container = document.getElementById('unscheduledContent');
        
        if (matches.length === 0) {
            container.innerHTML = this.renderSuccessState();
            return;
        }
        
        // Grouper par poule pour une meilleure organisation
        const byPool = Utils.groupBy(matches, m => m.poule);
        
        let html = `
            <div class="unscheduled-header">
                <div class="unscheduled-title">⚠️ Matchs Non Planifiés</div>
                <div class="unscheduled-count">${matches.length} match${matches.length > 1 ? 's' : ''} à planifier</div>
            </div>
        `;
        
        Object.keys(byPool).sort().forEach(pool => {
            const poolMatches = byPool[pool];
            html += `
                <section class="pool-section">
                    <div class="pool-header">
                        <div class="pool-title">🏆 ${pool}</div>
                        <div class="pool-count">${poolMatches.length} match${poolMatches.length > 1 ? 's' : ''}</div>
                    </div>
                    <div class="matches-grid">
                        ${poolMatches.map(m => MatchCard.render(m, true, filters, preferences, true, false)).join('')}
                    </div>
                </section>
            `;
        });
        
        container.innerHTML = html;
    }

    /**
     * Rend un état vide
     */
    static renderEmptyState() {
        return `
            <div class="empty-state">
                <div class="empty-icon">🔍</div>
                <h3 class="empty-title">Aucun match trouvé</h3>
                <p class="empty-text">Essayez de modifier vos filtres</p>
            </div>
        `;
    }

    /**
     * Rend un état de succès
     */
    static renderSuccessState() {
        return `
            <div class="success-state">
                <div class="success-icon">✅</div>
                <h2 class="success-title">Tous les matchs sont planifiés !</h2>
                <p class="success-text">Aucun match non planifié</p>
            </div>
        `;
    }

    /**
     * Met à jour les informations de filtre
     */
    static updateFilterInfo(matches, unscheduled, filters) {
        const container = document.getElementById('filterInfo');
        
        if (!filters.institution && !filters.team) {
            container.classList.remove('active');
            return;
        }
        
        container.classList.add('active');
        
        const title = filters.team ? `👥 ${filters.team}` : `🏛️ ${filters.institution}`;
        const subtitle = filters.team ? "Détails de l'équipe" : "Détails de l'institution";
        
        const weeks = new Set(matches.map(m => m.semaine));
        const venues = new Set(matches.map(m => m.gymnase));
        
        container.innerHTML = `
            <div class="filter-info-title">${title}</div>
            <div class="filter-info-subtitle">${subtitle}</div>
            <div class="filter-stats">
                <div class="filter-stat">
                    <div class="filter-stat-value">${matches.length}</div>
                    <div class="filter-stat-label">Planifiés</div>
                </div>
                <div class="filter-stat">
                    <div class="filter-stat-value">${unscheduled.length}</div>
                    <div class="filter-stat-label">Non planifiés</div>
                </div>
                <div class="filter-stat">
                    <div class="filter-stat-value">${weeks.size}</div>
                    <div class="filter-stat-label">Semaines</div>
                </div>
                <div class="filter-stat">
                    <div class="filter-stat-value">${venues.size}</div>
                    <div class="filter-stat-label">Gymnases</div>
                </div>
            </div>
        `;
    }
}

// Export pour utilisation
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CalendarView;
}
