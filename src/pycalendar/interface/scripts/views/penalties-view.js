/**
 * Vue Pénalités - Affichage et analyse de la décomposition des pénalités
 * 
 * Affiche une décomposition complète du score avec :
 * - Visualisation graphique (graphiques circulaires/barres)
 * - Tableau récapitulatif par catégorie
 * - Détails par match
 * - Export des données
 */

class PenaltiesView {
    constructor(dataManager, container) {
        this.dataManager = dataManager;
        this.container = container;
        this.data = dataManager.getData();
        this.breakdown = this.data.metadata?.penalty_breakdown || null;
        
        // DEBUG: Log pour comprendre le problème
        console.log('PenaltiesView - Constructor called');
        console.log('PenaltiesView - Data:', this.data);
        console.log('PenaltiesView - Metadata:', this.data.metadata);
        console.log('PenaltiesView - Breakdown:', this.breakdown);
    }
    
    /**
     * Initialise la vue
     */
    init() {
        console.log('PenaltiesView - init() called');
        
        // Vue en développement - afficher un message
        this._showDevelopmentMessage();
    }
    
    _showDevelopmentMessage() {
        this.container.innerHTML = `
            <div style="padding: 40px; text-align: center; color: #666;">
                <div style="font-size: 64px; margin-bottom: 20px;">🚧</div>
                <h2 style="margin-bottom: 10px;">Vue Pénalités en Développement</h2>
                <p style="font-size: 16px; color: #888; max-width: 600px; margin: 20px auto;">
                    Cette vue est actuellement en cours de développement.
                </p>
                <p style="font-size: 14px; color: #999; margin-top: 30px;">
                    Les informations de pénalités sont disponibles dans les autres vues (Agenda, Matchs, Poules).
                </p>
            </div>
        `;
    }
    
    _showNoDataMessage() {
        this.container.innerHTML = `
            <div style="padding: 40px; text-align: center; color: #666;">
                <div style="font-size: 48px; margin-bottom: 20px;">📊</div>
                <h2 style="margin-bottom: 10px;">Décomposition des Pénalités Non Disponible</h2>
                <p>Cette solution a été générée sans calcul de décomposition des pénalités.</p>
                <p style="margin-top: 20px; font-size: 14px; color: #999;">
                    Relancez la résolution pour obtenir les détails des pénalités.
                </p>
            </div>
        `;
    }
    
    render() {
        const html = `
            <div class="penalties-view">
                ${this._renderHeader()}
                ${this._renderSummaryCards()}
                ${this._renderCharts()}
                ${this._renderDetailedBreakdown()}
            </div>
        `;
        
        this.container.innerHTML = html;
        this._attachEventListeners();
    }
    
    _renderHeader() {
        const score = this.breakdown.score_total;
        const scoreClass = score < 0 ? 'excellent' : score < 100 ? 'good' : score < 1000 ? 'average' : 'poor';
        const scoreLabel = score < 0 ? 'Excellente' : score < 100 ? 'Bonne' : score < 1000 ? 'Moyenne' : 'Problématique';
        
        return `
            <div class="penalties-header">
                <div class="score-display ${scoreClass}">
                    <div class="score-label">Score Total</div>
                    <div class="score-value">${score.toFixed(2)}</div>
                    <div class="score-quality">${scoreLabel}</div>
                </div>
                
                <div class="score-info">
                    <h2>📊 Décomposition des Pénalités</h2>
                    <p>Analyse détaillée du score de la solution</p>
                    <div class="score-legend">
                        <div class="legend-item">
                            <span class="legend-color" style="background: #4caf50"></span>
                            <span>Bonus (valeurs négatives)</span>
                        </div>
                        <div class="legend-item">
                            <span class="legend-color" style="background: #f44336"></span>
                            <span>Pénalités (valeurs positives)</span>
                        </div>
                    </div>
                </div>
                
                <div class="actions">
                    <button class="btn-export" onclick="window.penaltiesView._exportBreakdown()">
                        � Exporter JSON
                    </button>
                    <button class="btn-export" onclick="window.penaltiesView._exportDetailedCSV()">
                        � Exporter CSV Détaillé
                    </button>
                </div>
            </div>
        `;
    }
    
    _renderSummaryCards() {
        const {contraintes_dures, preferences_gymnases, niveau_gymnases, 
               horaires_preferes, compaction_temporelle} = this.breakdown;
        
        const cards = [
            {
                title: 'Contraintes Dures',
                icon: '🚫',
                value: contraintes_dures.indisponibilite.penalty + contraintes_dures.capacite.penalty,
                color: contraintes_dures.indisponibilite.violations + contraintes_dures.capacite.violations > 0 ? '#f44336' : '#4caf50',
                details: `${contraintes_dures.indisponibilite.violations + contraintes_dures.capacite.violations} violation(s)`
            },
            {
                title: 'Préférences Gymnases',
                icon: '🏟️',
                value: preferences_gymnases.bonus_total,
                color: preferences_gymnases.bonus_total < 0 ? '#4caf50' : '#ff9800',
                details: `${preferences_gymnases.matchs_en_gymnases_preferes} match(s) en gymnases préférés`
            },
            {
                title: 'Niveau Gymnases',
                icon: '🏆',
                value: niveau_gymnases.bonus_total + niveau_gymnases.penalty_total,
                color: (niveau_gymnases.bonus_total + niveau_gymnases.penalty_total) < 0 ? '#4caf50' : '#ff9800',
                details: `${niveau_gymnases.matchs_bien_assignes} bien assignés, ${niveau_gymnases.matchs_mal_assignes} mal assignés`
            },
            {
                title: 'Horaires Préférés',
                icon: '⏰',
                value: horaires_preferes.matchs_apres.penalty + 
                       horaires_preferes.matchs_avant_1_equipe.penalty + 
                       horaires_preferes.matchs_avant_2_equipes.penalty,
                color: horaires_preferes.matchs_ok > (horaires_preferes.matchs_apres.count + 
                       horaires_preferes.matchs_avant_1_equipe.count + 
                       horaires_preferes.matchs_avant_2_equipes.count) ? '#4caf50' : '#ff9800',
                details: `${horaires_preferes.matchs_ok} OK, ${horaires_preferes.matchs_avant_2_equipes.count} urgents`
            },
            {
                title: 'Compaction Temporelle',
                icon: '📅',
                value: compaction_temporelle.penalty_total,
                color: compaction_temporelle.penalty_total < 50 ? '#4caf50' : '#ff9800',
                details: `${Object.keys(compaction_temporelle.par_semaine).length} semaines utilisées`
            }
        ];
        
        return `
            <div class="summary-cards">
                ${cards.map(card => `
                    <div class="summary-card" style="border-left: 4px solid ${card.color}">
                        <div class="card-icon">${card.icon}</div>
                        <div class="card-content">
                            <div class="card-title">${card.title}</div>
                            <div class="card-value" style="color: ${card.color}">
                                ${card.value >= 0 ? '+' : ''}${card.value.toFixed(1)}
                            </div>
                            <div class="card-details">${card.details}</div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    _renderCharts() {
        return `
            <div class="charts-section">
                <div class="chart-container">
                    <h3>Répartition des Pénalités par Catégorie</h3>
                    <canvas id="penaltiesChart"></canvas>
                </div>
                <div class="chart-container">
                    <h3>Bonus vs Pénalités</h3>
                    <canvas id="bonusVsPenaltiesChart"></canvas>
                </div>
            </div>
        `;
    }
    
    _renderDetailedBreakdown() {
        return `
            <div class="detailed-breakdown">
                <h3>📋 Décomposition Détaillée</h3>
                
                <div class="breakdown-section">
                    <h4>🚫 Contraintes Dures</h4>
                    ${this._renderHardConstraints()}
                </div>
                
                <div class="breakdown-section">
                    <h4>🏟️ Préférences et Niveau de Gymnases</h4>
                    ${this._renderGymPreferences()}
                </div>
                
                <div class="breakdown-section">
                    <h4>⏰ Horaires Préférés</h4>
                    ${this._renderTimePreferences()}
                </div>
                
                <div class="breakdown-section">
                    <h4>📅 Compaction Temporelle</h4>
                    ${this._renderCompaction()}
                </div>
                
                <div class="breakdown-section">
                    <h4>🏫 Contraintes Institutionnelles</h4>
                    ${this._renderInstitutionalConstraints()}
                </div>
            </div>
        `;
    }
    
    _renderHardConstraints() {
        const {contraintes_dures} = this.breakdown;
        
        return `
            <table class="breakdown-table">
                <tr>
                    <td>Indisponibilité équipes/institutions</td>
                    <td class="violations">${contraintes_dures.indisponibilite.violations}</td>
                    <td class="penalty ${contraintes_dures.indisponibilite.penalty > 0 ? 'negative' : 'positive'}">
                        ${contraintes_dures.indisponibilite.penalty > 0 ? '+' : ''}${contraintes_dures.indisponibilite.penalty.toFixed(2)}
                    </td>
                </tr>
                <tr>
                    <td>Capacité gymnases dépassée</td>
                    <td class="violations">${contraintes_dures.capacite.violations}</td>
                    <td class="penalty ${contraintes_dures.capacite.penalty > 0 ? 'negative' : 'positive'}">
                        ${contraintes_dures.capacite.penalty > 0 ? '+' : ''}${contraintes_dures.capacite.penalty.toFixed(2)}
                    </td>
                </tr>
            </table>
        `;
    }
    
    _renderGymPreferences() {
        const {preferences_gymnases, niveau_gymnases} = this.breakdown;
        
        return `
            <table class="breakdown-table">
                <tr>
                    <td>Matchs en gymnases préférés</td>
                    <td class="count">${preferences_gymnases.matchs_en_gymnases_preferes}</td>
                    <td class="penalty positive">
                        ${preferences_gymnases.bonus_total.toFixed(2)}
                    </td>
                </tr>
                <tr>
                    <td>Matchs bien assignés (niveau gymnase ↔ niveau match)</td>
                    <td class="count">${niveau_gymnases.matchs_bien_assignes}</td>
                    <td class="penalty positive">
                        ${niveau_gymnases.bonus_total.toFixed(2)}
                    </td>
                </tr>
                <tr>
                    <td>Matchs mal assignés (niveau gymnase ↔ niveau match)</td>
                    <td class="count">${niveau_gymnases.matchs_mal_assignes}</td>
                    <td class="penalty negative">
                        +${niveau_gymnases.penalty_total.toFixed(2)}
                    </td>
                </tr>
            </table>
        `;
    }
    
    _renderTimePreferences() {
        const {horaires_preferes} = this.breakdown;
        
        return `
            <table class="breakdown-table">
                <tr>
                    <td>✅ Matchs dans horaire préféré (ou tolérance)</td>
                    <td class="count">${horaires_preferes.matchs_ok}</td>
                    <td class="penalty positive">0.00</td>
                </tr>
                <tr>
                    <td>🟡 Matchs après horaire préféré</td>
                    <td class="count">${horaires_preferes.matchs_apres.count}</td>
                    <td class="penalty negative">
                        +${horaires_preferes.matchs_apres.penalty.toFixed(2)}
                    </td>
                </tr>
                <tr>
                    <td>🟠 Matchs avant horaire préféré (1 équipe)</td>
                    <td class="count">${horaires_preferes.matchs_avant_1_equipe.count}</td>
                    <td class="penalty negative">
                        +${horaires_preferes.matchs_avant_1_equipe.penalty.toFixed(2)}
                    </td>
                </tr>
                <tr>
                    <td>🔴 Matchs avant horaire préféré (2 équipes)</td>
                    <td class="count">${horaires_preferes.matchs_avant_2_equipes.count}</td>
                    <td class="penalty negative">
                        +${horaires_preferes.matchs_avant_2_equipes.penalty.toFixed(2)}
                    </td>
                </tr>
            </table>
        `;
    }
    
    _renderCompaction() {
        const {compaction_temporelle} = this.breakdown;
        const weeks = Object.entries(compaction_temporelle.par_semaine)
            .sort((a, b) => parseInt(a[0]) - parseInt(b[0]));
        
        return `
            <table class="breakdown-table">
                <thead>
                    <tr>
                        <th>Semaine</th>
                        <th>Nb Matchs</th>
                        <th>Pénalité</th>
                    </tr>
                </thead>
                <tbody>
                    ${weeks.map(([week, data]) => `
                        <tr>
                            <td>Semaine ${week}</td>
                            <td class="count">${data.nb_matchs}</td>
                            <td class="penalty ${data.penalty > 0 ? 'negative' : 'positive'}">
                                ${data.penalty > 0 ? '+' : ''}${data.penalty.toFixed(2)}
                            </td>
                        </tr>
                    `).join('')}
                    <tr class="total-row">
                        <td colspan="2"><strong>Total Compaction</strong></td>
                        <td class="penalty negative">
                            <strong>+${compaction_temporelle.penalty_total.toFixed(2)}</strong>
                        </td>
                    </tr>
                </tbody>
            </table>
        `;
    }
    
    _renderInstitutionalConstraints() {
        const {contraintes_institutionnelles} = this.breakdown;
        
        return `
            <table class="breakdown-table">
                <tr>
                    <td>Overlaps institution (matchs simultanés)</td>
                    <td class="violations">${contraintes_institutionnelles.overlaps.count}</td>
                    <td class="penalty ${contraintes_institutionnelles.overlaps.penalty > 0 ? 'negative' : 'positive'}">
                        ${contraintes_institutionnelles.overlaps.penalty > 0 ? '+' : ''}${contraintes_institutionnelles.overlaps.penalty.toFixed(2)}
                    </td>
                </tr>
                <tr>
                    <td>Ententes planifiées</td>
                    <td class="count">${contraintes_institutionnelles.ententes.planifiees}</td>
                    <td class="penalty positive">0.00</td>
                </tr>
                <tr>
                    <td>Ententes non planifiées</td>
                    <td class="violations">${contraintes_institutionnelles.ententes.non_planifiees}</td>
                    <td class="penalty negative">
                        +${contraintes_institutionnelles.ententes.penalty.toFixed(2)}
                    </td>
                </tr>
            </table>
        `;
    }
    
    _attachEventListeners() {
        // Initialiser les graphiques après un court délai (pour que le DOM soit prêt)
        setTimeout(() => this._initializeCharts(), 100);
    }
    
    _initializeCharts() {
        // Note: Nécessite Chart.js - à charger dans index.html
        if (typeof Chart === 'undefined') {
            console.warn('Chart.js non chargé, graphiques non disponibles');
            return;
        }
        
        this._createPenaltiesChart();
        this._createBonusVsPenaltiesChart();
    }
    
    _createPenaltiesChart() {
        const ctx = document.getElementById('penaltiesChart');
        if (!ctx) return;
        
        // Préparer les données
        const labels = [];
        const values = [];
        const colors = [];
        
        const categories = this._getCategoriesWithValues();
        categories.forEach(cat => {
            labels.push(cat.label);
            values.push(Math.abs(cat.value));
            colors.push(cat.value < 0 ? '#4caf50' : '#f44336');
        });
        
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Valeur Absolue',
                    data: values,
                    backgroundColor: colors
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {display: false},
                    title: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    _createBonusVsPenaltiesChart() {
        const ctx = document.getElementById('bonusVsPenaltiesChart');
        if (!ctx) return;
        
        const categories = this._getCategoriesWithValues();
        const totalBonus = categories.filter(c => c.value < 0).reduce((sum, c) => sum + Math.abs(c.value), 0);
        const totalPenalties = categories.filter(c => c.value > 0).reduce((sum, c) => sum + c.value, 0);
        
        new Chart(ctx, {
            type: 'pie',
            data: {
                labels: ['Bonus', 'Pénalités'],
                datasets: [{
                    data: [totalBonus, totalPenalties],
                    backgroundColor: ['#4caf50', '#f44336']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
    
    _getCategoriesWithValues() {
        const {contraintes_dures, preferences_gymnases, niveau_gymnases,
               horaires_preferes, espacement_repos, compaction_temporelle,
               contraintes_institutionnelles, contraintes_temporelles, aller_retour,
               equilibrage_charge} = this.breakdown;
        
        return [
            {label: 'Indisponibilité', value: contraintes_dures.indisponibilite.penalty},
            {label: 'Capacité', value: contraintes_dures.capacite.penalty},
            {label: 'Préf. Gymnases', value: preferences_gymnases.bonus_total},
            {label: 'Niveau Gymnases', value: niveau_gymnases.bonus_total + niveau_gymnases.penalty_total},
            {label: 'Horaires', value: horaires_preferes.matchs_apres.penalty + 
                                       horaires_preferes.matchs_avant_1_equipe.penalty +
                                       horaires_preferes.matchs_avant_2_equipes.penalty},
            {label: 'Espacement', value: espacement_repos.penalty},
            {label: 'Compaction', value: compaction_temporelle.penalty_total},
            {label: 'Overlaps', value: contraintes_institutionnelles.overlaps.penalty},
            {label: 'Ententes', value: contraintes_institutionnelles.ententes.penalty},
            {label: 'Contraintes Temp.', value: contraintes_temporelles.penalty},
            {label: 'Aller-Retour', value: aller_retour.meme_semaine.penalty + aller_retour.consecutives.penalty},
            {label: 'Équilibrage', value: equilibrage_charge.penalty}
        ].filter(cat => cat.value !== 0);
    }
    
    _exportBreakdown() {
        const json = JSON.stringify(this.breakdown, null, 2);
        const blob = new Blob([json], {type: 'application/json'});
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `penalty_breakdown_${new Date().toISOString().slice(0,10)}.json`;
        a.click();
        URL.revokeObjectURL(url);
    }
    
    _exportDetailedCSV() {
        // Export CSV avec ligne par catégorie de pénalité
        const rows = [
            ['Catégorie', 'Sous-catégorie', 'Count/Violations', 'Valeur']
        ];
        
        const {contraintes_dures, preferences_gymnases, niveau_gymnases,
               horaires_preferes, compaction_temporelle, contraintes_institutionnelles} = this.breakdown;
        
        // Contraintes dures
        rows.push(['Contraintes Dures', 'Indisponibilité', contraintes_dures.indisponibilite.violations, contraintes_dures.indisponibilite.penalty]);
        rows.push(['Contraintes Dures', 'Capacité', contraintes_dures.capacite.violations, contraintes_dures.capacite.penalty]);
        
        // Préférences gymnases
        rows.push(['Préférences Gymnases', 'Matchs préférés', preferences_gymnases.matchs_en_gymnases_preferes, preferences_gymnases.bonus_total]);
        
        // Niveau gymnases
        rows.push(['Niveau Gymnases', 'Bien assignés', niveau_gymnases.matchs_bien_assignes, niveau_gymnases.bonus_total]);
        rows.push(['Niveau Gymnases', 'Mal assignés', niveau_gymnases.matchs_mal_assignes, niveau_gymnases.penalty_total]);
        
        // Horaires
        rows.push(['Horaires Préférés', 'OK', horaires_preferes.matchs_ok, 0]);
        rows.push(['Horaires Préférés', 'Après', horaires_preferes.matchs_apres.count, horaires_preferes.matchs_apres.penalty]);
        rows.push(['Horaires Préférés', 'Avant 1 eq', horaires_preferes.matchs_avant_1_equipe.count, horaires_preferes.matchs_avant_1_equipe.penalty]);
        rows.push(['Horaires Préférés', 'Avant 2 eq', horaires_preferes.matchs_avant_2_equipes.count, horaires_preferes.matchs_avant_2_equipes.penalty]);
        
        // Compaction
        Object.entries(compaction_temporelle.par_semaine).forEach(([week, data]) => {
            rows.push(['Compaction', `Semaine ${week}`, data.nb_matchs, data.penalty]);
        });
        
        // Institutions
        rows.push(['Institutions', 'Overlaps', contraintes_institutionnelles.overlaps.count, contraintes_institutionnelles.overlaps.penalty]);
        rows.push(['Institutions', 'Ententes planifiées', contraintes_institutionnelles.ententes.planifiees, 0]);
        rows.push(['Institutions', 'Ententes non planifiées', contraintes_institutionnelles.ententes.non_planifiees, contraintes_institutionnelles.ententes.penalty]);
        
        const csv = rows.map(row => row.join(',')).join('\n');
        const blob = new Blob([csv], {type: 'text/csv'});
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `penalties_detailed_${new Date().toISOString().slice(0,10)}.csv`;
        a.click();
        URL.revokeObjectURL(url);
    }
}

// Export global
if (typeof window !== 'undefined') {
    window.PenaltiesView = PenaltiesView;
}
