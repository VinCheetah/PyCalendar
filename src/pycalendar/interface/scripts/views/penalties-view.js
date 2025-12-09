/**
 * Vue Pénalités - décomposition complète des scores
 */

class PenaltiesView {
    constructor(dataManager, container) {
        this.dataManager = dataManager;
        this.container = container;
        this.chartInstances = [];
        this.options = {
            chartMode: 'absolute',
            showPerMatchTable: true
        };
        this.data = null;
        this.breakdown = null;
        this.unsubscribe = null;

        if (this.dataManager && typeof this.dataManager.subscribe === 'function') {
            this.unsubscribe = this.dataManager.subscribe(() => this._handleDataUpdate());
        }

        if (typeof window !== 'undefined') {
            window.penaltiesView = this;
        }
    }

    init() {
        this.render();
    }

    destroy() {
        this._destroyCharts();
        if (this.unsubscribe) {
            this.unsubscribe();
            this.unsubscribe = null;
        }
        if (this.container) {
            this.container.innerHTML = '';
        }
    }

    getDisplayOptions() {
        return {
            title: 'Options Pénalités',
            options: [
                {
                    type: 'select',
                    id: 'penalties-chart-mode',
                    label: 'Mode graphique',
                    values: [
                        { value: 'absolute', text: 'Valeurs absolues' },
                        { value: 'percent', text: 'Pourcentage du total' }
                    ],
                    default: this.options.chartMode,
                    action: (value) => {
                        this.options.chartMode = value;
                        this.render();
                    }
                },
                {
                    type: 'checkbox',
                    id: 'penalties-show-matches',
                    label: 'Afficher les matchs les plus pénalisés',
                    default: this.options.showPerMatchTable,
                    action: (checked) => {
                        this.options.showPerMatchTable = checked;
                        this.render();
                    }
                }
            ]
        };
    }

    render() {
        this._refreshData();

        if (!this.breakdown) {
            this._destroyCharts();
            this._showNoDataMessage();
            return;
        }

        this._destroyCharts();
        this.palette = this._buildPalette();

        const sections = [
            this._renderHeader(),
            this._renderSummaryCards(),
            this._renderCharts(),
            this._renderDetailedBreakdown()
        ];

        if (this.options.showPerMatchTable) {
            sections.push(this._renderTopMatches());
        }

        this.container.innerHTML = `
            <div class="penalties-view">
                <div class="penalties-shell">
                    ${sections.join('\n')}
                </div>
            </div>
        `;

        this._attachEventListeners();
    }

    _handleDataUpdate() {
        const viewContainer = typeof document !== 'undefined'
            ? document.querySelector('[data-view-content="penalties"]')
            : null;

        if (viewContainer && viewContainer.classList.contains('active')) {
            this.render();
        } else {
            // Force rafraîchissement la prochaine fois que la vue devient active
            this.data = null;
            this.breakdown = null;
        }
    }

    _refreshData() {
        if (!this.dataManager || typeof this.dataManager.getData !== 'function') {
            this.data = null;
            this.breakdown = null;
            return;
        }
        this.data = this.dataManager.getData();
        this.breakdown = this.data?.metadata?.penalty_breakdown || null;
    }

    _showNoDataMessage() {
        this.container.innerHTML = `
            <div style="padding: 40px; text-align: center; color: #666;">
                <div style="font-size: 48px; margin-bottom: 20px;">📊</div>
                <h2 style="margin-bottom: 10px;">Aucune décomposition disponible</h2>
                <p>Relancez la génération de solution avec l'option de décomposition des pénalités pour alimenter cette vue.</p>
            </div>
        `;
    }

    _renderHeader() {
        const score = this.breakdown?.score_total ?? 0;
        const scoreClass = score < 0 ? 'excellent' : score < 100 ? 'good' : score < 500 ? 'average' : 'poor';
        const scoreLabel = score < 0 ? 'Excellente' : score < 100 ? 'Bonne' : score < 500 ? 'Moyenne' : 'Problématique';

        return `
            <section class="penalties-header surface-card">
                <div class="score-display ${scoreClass}">
                    <div class="score-label">Score total</div>
                    <div class="score-value">${score.toFixed(2)}</div>
                    <div class="score-quality">${scoreLabel}</div>
                </div>

                <div class="score-info">
                    <div>
                        <h2>📊 Décomposition des pénalités</h2>
                        <p>Bonus <strong>(valeurs négatives)</strong> vs pénalités <strong>(valeurs positives)</strong></p>
                        <div class="score-legend">
                            <div class="legend-item">
                                <span class="legend-color positive"></span>
                                <span>Bonus gagnés</span>
                            </div>
                            <div class="legend-item">
                                <span class="legend-color negative"></span>
                                <span>Pénalités subies</span>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="actions">
                    <button class="btn-export" onclick="window.penaltiesView?._exportBreakdown()">
                        💾 Exporter JSON
                    </button>
                    <button class="btn-export" onclick="window.penaltiesView?._exportDetailedCSV()">
                        📑 Exporter CSV détaillé
                    </button>
                </div>
            </section>
        `;
    }

    _renderSummaryCards() {
        const b = this.breakdown;
        const cards = [
            {
                title: 'Contraintes dures',
                icon: '🚫',
                value: (b.contraintes_dures?.indisponibilite?.penalty || 0) + (b.contraintes_dures?.capacite?.penalty || 0),
                detail: `${(b.contraintes_dures?.indisponibilite?.violations || 0) + (b.contraintes_dures?.capacite?.violations || 0)} violation(s)`
            },
            {
                title: 'Préférences gymnases',
                icon: '🏟️',
                value: b.preferences_gymnases?.bonus_total || 0,
                detail: `${b.preferences_gymnases?.matchs_en_gymnases_preferes || 0} matchs concernés`
            },
            {
                title: 'Niveau gymnases',
                icon: '🏆',
                value: (b.niveau_gymnases?.bonus_total || 0) + (b.niveau_gymnases?.penalty_total || 0),
                detail: `${b.niveau_gymnases?.matchs_bien_assignes || 0} bien assignés`
            },
            {
                title: 'Horaires préférés',
                icon: '⏰',
                value: (b.horaires_preferes?.matchs_apres?.penalty || 0) +
                       (b.horaires_preferes?.matchs_avant_1_equipe?.penalty || 0) +
                       (b.horaires_preferes?.matchs_avant_2_equipes?.penalty || 0),
                detail: `${b.horaires_preferes?.matchs_ok || 0} matchs respectent les souhaits`
            },
            {
                title: 'Compaction',
                icon: '📅',
                value: b.compaction_temporelle?.penalty_total || 0,
                detail: `${Object.keys(b.compaction_temporelle?.par_semaine || {}).length} semaines utilisées`
            }
        ];

        return `
            <section class="summary-section surface-card">
                <div class="section-heading">
                    <div>
                        <h3>Résumé synthétique</h3>
                        <p>Principales sources de bonus et de pénalités</p>
                    </div>
                </div>
                <div class="summary-cards">
                    ${cards.map(card => {
                        const toneClass = card.value > 0 ? 'negative' : 'positive';
                        const formattedValue = card.value === 0
                            ? '0.0'
                            : `${card.value >= 0 ? '+' : ''}${card.value.toFixed(1)}`;
                        return `
                            <div class="summary-card ${toneClass}">
                                <div class="card-icon">${card.icon}</div>
                                <div class="card-content">
                                    <div class="card-title">${card.title}</div>
                                    <div class="card-value">${formattedValue}</div>
                                    <div class="card-details">${card.detail}</div>
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>
            </section>
        `;
    }

    _renderCharts() {
        const modeLabel = this.options.chartMode === 'percent'
            ? 'Affichage en pourcentage du total'
            : 'Affichage en valeur absolue';
        return `
            <section class="charts-section">
                <div class="chart-container surface-card">
                    <div class="chart-header">
                        <h3>Répartition par catégorie</h3>
                        <span class="chart-subtitle">${modeLabel}</span>
                    </div>
                    <div class="chart-wrapper">
                        <canvas id="penaltiesChart"></canvas>
                    </div>
                </div>
                <div class="chart-container surface-card">
                    <div class="chart-header">
                        <h3>Bonus vs pénalités</h3>
                        <span class="chart-subtitle">Comparaison globale</span>
                    </div>
                    <div class="chart-wrapper">
                        <canvas id="bonusVsPenaltiesChart"></canvas>
                    </div>
                </div>
            </section>
        `;
    }

    _renderDetailedBreakdown() {
        return `
            <section class="detailed-breakdown surface-card">
                <h3>📋 Décomposition détaillée</h3>

                <div class="breakdown-section">
                    <h4>🚫 Contraintes dures</h4>
                    ${this._renderHardConstraints()}
                </div>

                <div class="breakdown-section">
                    <h4>🏟️ Gymnases</h4>
                    ${this._renderGymPreferences()}
                </div>

                <div class="breakdown-section">
                    <h4>⏰ Horaires</h4>
                    ${this._renderTimePreferences()}
                </div>

                <div class="breakdown-section">
                    <h4>📅 Compaction & Espacement</h4>
                    ${this._renderCompaction()}
                    ${this._renderSpacing()}
                </div>

                <div class="breakdown-section">
                    <h4>🏫 Institutions & contraintes temps</h4>
                    ${this._renderInstitutionalConstraints()}
                    ${this._renderTemporalConstraints()}
                </div>

                <div class="breakdown-section">
                    <h4>↔️ Aller-retour & équilibrage</h4>
                    ${this._renderAllerRetour()}
                    ${this._renderEquilibrage()}
                </div>
            </section>
        `;
    }

    _renderHardConstraints() {
        const hard = this.breakdown.contraintes_dures || {};
        const indispo = hard.indisponibilite || { violations: 0, penalty: 0 };
        const capacite = hard.capacite || { violations: 0, penalty: 0 };

        return `
            <table class="breakdown-table">
                <tr>
                    <td>Indisponibilités équipes / institutions</td>
                    <td class="violations">${indispo.violations}</td>
                    <td class="penalty ${indispo.penalty > 0 ? 'negative' : 'positive'}">${indispo.penalty >= 0 ? '+' : ''}${indispo.penalty.toFixed(2)}</td>
                </tr>
                <tr>
                    <td>Dépassements de capacité</td>
                    <td class="violations">${capacite.violations}</td>
                    <td class="penalty ${capacite.penalty > 0 ? 'negative' : 'positive'}">${capacite.penalty >= 0 ? '+' : ''}${capacite.penalty.toFixed(2)}</td>
                </tr>
            </table>
        `;
    }

    _renderGymPreferences() {
        const pref = this.breakdown.preferences_gymnases || {};
        const niveau = this.breakdown.niveau_gymnases || {};

        return `
            <table class="breakdown-table">
                <tr>
                    <td>Matchs en gymnases préférés</td>
                    <td class="count">${pref.matchs_en_gymnases_preferes || 0}</td>
                    <td class="penalty ${pref.bonus_total <= 0 ? 'positive' : 'negative'}">${pref.bonus_total >= 0 ? '+' : ''}${(pref.bonus_total || 0).toFixed(2)}</td>
                </tr>
                <tr>
                    <td>Matchs bien assignés (niveau)</td>
                    <td class="count">${niveau.matchs_bien_assignes || 0}</td>
                    <td class="penalty ${niveau.bonus_total <= 0 ? 'positive' : 'negative'}">${niveau.bonus_total >= 0 ? '+' : ''}${(niveau.bonus_total || 0).toFixed(2)}</td>
                </tr>
                <tr>
                    <td>Matchs mal assignés (niveau)</td>
                    <td class="count">${niveau.matchs_mal_assignes || 0}</td>
                    <td class="penalty negative">+${(niveau.penalty_total || 0).toFixed(2)}</td>
                </tr>
            </table>
        `;
    }

    _renderTimePreferences() {
        const pref = this.breakdown.horaires_preferes || {};

        return `
            <table class="breakdown-table">
                <tr>
                    <td>Matchs respectant les horaires préférés</td>
                    <td class="count">${pref.matchs_ok || 0}</td>
                    <td class="penalty positive">0.00</td>
                </tr>
                <tr>
                    <td>Matchs après l'horaire</td>
                    <td class="count">${pref.matchs_apres?.count || 0}</td>
                    <td class="penalty negative">+${(pref.matchs_apres?.penalty || 0).toFixed(2)}</td>
                </tr>
                <tr>
                    <td>Matchs avant l'horaire (1 équipe)</td>
                    <td class="count">${pref.matchs_avant_1_equipe?.count || 0}</td>
                    <td class="penalty negative">+${(pref.matchs_avant_1_equipe?.penalty || 0).toFixed(2)}</td>
                </tr>
                <tr>
                    <td>Matchs avant l'horaire (2 équipes)</td>
                    <td class="count">${pref.matchs_avant_2_equipes?.count || 0}</td>
                    <td class="penalty negative">+${(pref.matchs_avant_2_equipes?.penalty || 0).toFixed(2)}</td>
                </tr>
            </table>
        `;
    }

    _renderCompaction() {
        const compaction = this.breakdown.compaction_temporelle || { par_semaine: {} };
        const weeks = Object.entries(compaction.par_semaine || {}).sort((a, b) => Number(a[0]) - Number(b[0]));

        if (!weeks.length) {
            return '<p>Aucune pénalité de compaction.</p>';
        }

        return `
            <table class="breakdown-table">
                <thead>
                    <tr>
                        <th>Semaine</th>
                        <th>Matchs</th>
                        <th>Pénalité</th>
                    </tr>
                </thead>
                <tbody>
                    ${weeks.map(([week, data]) => `
                        <tr>
                            <td>Semaine ${week}</td>
                            <td class="count">${data.nb_matchs || 0}</td>
                            <td class="penalty ${data.penalty > 0 ? 'negative' : 'positive'}">${data.penalty >= 0 ? '+' : ''}${(data.penalty || 0).toFixed(2)}</td>
                        </tr>
                    `).join('')}
                    <tr>
                        <td colspan="2"><strong>Total compaction</strong></td>
                        <td class="penalty negative"><strong>+${(compaction.penalty_total || 0).toFixed(2)}</strong></td>
                    </tr>
                </tbody>
            </table>
        `;
    }

    _renderSpacing() {
        const espacement = this.breakdown.espacement_repos || { violations: 0, penalty: 0 };
        if (!espacement.violations && !espacement.penalty) {
            return '<p>Aucune alerte d\'espacement.</p>';
        }
        return `
            <table class="breakdown-table">
                <tr>
                    <td>Matchs trop rapprochés</td>
                    <td class="violations">${espacement.violations}</td>
                    <td class="penalty negative">+${(espacement.penalty || 0).toFixed(2)}</td>
                </tr>
            </table>
        `;
    }

    _renderInstitutionalConstraints() {
        const inst = this.breakdown.contraintes_institutionnelles || { overlaps: {}, ententes: {} };
        const overlaps = inst.overlaps || { count: 0, penalty: 0 };
        const ententes = inst.ententes || { planifiees: 0, non_planifiees: 0, penalty: 0 };

        return `
            <table class="breakdown-table">
                <tr>
                    <td>Matchs simultanés mêmes institutions</td>
                    <td class="violations">${overlaps.count || 0}</td>
                    <td class="penalty ${overlaps.penalty > 0 ? 'negative' : 'positive'}">${overlaps.penalty >= 0 ? '+' : ''}${(overlaps.penalty || 0).toFixed(2)}</td>
                </tr>
                <tr>
                    <td>Ententes planifiées</td>
                    <td class="count">${ententes.planifiees || 0}</td>
                    <td class="penalty positive">0.00</td>
                </tr>
                <tr>
                    <td>Ententes non planifiées</td>
                    <td class="violations">${ententes.non_planifiees || 0}</td>
                    <td class="penalty negative">+${(ententes.penalty || 0).toFixed(2)}</td>
                </tr>
            </table>
        `;
    }

    _renderTemporalConstraints() {
        const temp = this.breakdown.contraintes_temporelles || { violations: 0, penalty: 0 };
        if (!temp.violations && !temp.penalty) {
            return '';
        }
        return `
            <table class="breakdown-table">
                <tr>
                    <td>Violations de contraintes calendaires</td>
                    <td class="violations">${temp.violations}</td>
                    <td class="penalty negative">+${(temp.penalty || 0).toFixed(2)}</td>
                </tr>
            </table>
        `;
    }

    _renderAllerRetour() {
        const ar = this.breakdown.aller_retour || { meme_semaine: {}, consecutives: {} };
        const meme = ar.meme_semaine || { count: 0, penalty: 0 };
        const consecutives = ar.consecutives || { count: 0, penalty: 0 };

        if (!meme.count && !consecutives.count) {
            return '<p>Aucune pénalité d\'aller-retour.</p>';
        }

        return `
            <table class="breakdown-table">
                <tr>
                    <td>Aller/retour la même semaine</td>
                    <td class="violations">${meme.count || 0}</td>
                    <td class="penalty negative">+${(meme.penalty || 0).toFixed(2)}</td>
                </tr>
                <tr>
                    <td>Aller/retour sur semaines consécutives</td>
                    <td class="violations">${consecutives.count || 0}</td>
                    <td class="penalty negative">+${(consecutives.penalty || 0).toFixed(2)}</td>
                </tr>
            </table>
        `;
    }

    _renderEquilibrage() {
        const eq = this.breakdown.equilibrage_charge || { penalty: 0 };
        if (!eq.penalty) {
            return '';
        }
        return `
            <table class="breakdown-table">
                <tr>
                    <td>Équilibrage de charge</td>
                    <td class="count">-</td>
                    <td class="penalty ${eq.penalty > 0 ? 'negative' : 'positive'}">${eq.penalty >= 0 ? '+' : ''}${eq.penalty.toFixed(2)}</td>
                </tr>
            </table>
        `;
    }

    _renderTopMatches() {
        const topMatches = this._getTopPenalizedMatches();
        if (!topMatches.length) {
            return '';
        }

        return `
            <section class="surface-card top-matches">
                <h3>🔥 Matchs les plus pénalisés</h3>
                <div class="table-responsive">
                    <table class="breakdown-table">
                        <thead>
                            <tr>
                                <th>Match</th>
                                <th>Créneau</th>
                                <th>Pénalité</th>
                                <th>Détail</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${topMatches.map(match => `
                                <tr>
                                    <td>
                                        <strong>${match.label}</strong><br>
                                        <small>${match.poule}</small>
                                    </td>
                                    <td>${match.slot}</td>
                                    <td class="penalty negative">+${match.total.toFixed(1)}</td>
                                    <td>${match.details}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </section>
        `;
    }

    _getTopPenalizedMatches(limit = 20) {
        const matches = typeof this.dataManager.getScheduledMatches === 'function'
            ? this.dataManager.getScheduledMatches()
            : [];

        return matches
            .filter(match => match.penalties && match.penalties.total > 0)
            .map(match => ({
                id: match.match_id,
                label: `${match.equipe1_nom || 'Équipe 1'} vs ${match.equipe2_nom || 'Équipe 2'}`,
                poule: match.poule || '-',
                slot: this._formatSlot(match),
                total: match.penalties.total,
                details: this._formatPenaltyList(match.penalties)
            }))
            .sort((a, b) => b.total - a.total)
            .slice(0, limit);
    }

    _formatSlot(match) {
        if (!match.gymnase && !match.semaine) {
            return 'Non planifié';
        }
        const week = match.semaine ? `S${match.semaine}` : 'Semaine ?';
        const horaire = match.horaire || '?';
        const gymnase = match.gymnase || 'Gymnase ?';
        return `${week} • ${horaire} • ${gymnase}`;
    }

    _formatPenaltyList(penalties) {
        const entries = Object.entries(penalties || {})
            .filter(([key, value]) => key !== 'total' && value > 0)
            .sort((a, b) => b[1] - a[1]);

        if (!entries.length) {
            return '—';
        }

        return entries
            .map(([key, value]) => `${this._getPenaltyLabel(key)}: ${value.toFixed(1)}`)
            .join('<br>');
    }

    _attachEventListeners() {
        setTimeout(() => this._initializeCharts(), 50);
    }

    _initializeCharts() {
        if (typeof Chart === 'undefined') {
            console.warn('Chart.js non chargé, graphiques indisponibles');
            return;
        }

        const categories = this._getCategoriesWithValues();
        if (!categories.length) {
            return;
        }

        this._createPenaltiesChart(categories);
        this._createBonusVsPenaltiesChart(categories);
    }

    _createPenaltiesChart(categories) {
        const canvas = this._prepareCanvas(document.getElementById('penaltiesChart'));
        if (!canvas) return;

        const dataset = categories.map(cat => Math.abs(cat.value));
        const labels = categories.map(cat => cat.label);
        const total = dataset.reduce((sum, val) => sum + val, 0) || 1;
        const mode = this.options.chartMode;
        const dataValues = mode === 'percent'
            ? dataset.map(val => (val / total) * 100)
            : dataset;
        const label = mode === 'percent' ? '% du total' : 'Valeur absolue';
        const positiveColor = this.palette?.success || '#10B981';
        const negativeColor = this.palette?.danger || '#EF4444';

        const chart = new Chart(canvas, {
            type: 'bar',
            data: {
                labels,
                datasets: [{
                    label,
                    data: dataValues,
                    backgroundColor: categories.map(cat => cat.value <= 0 ? positiveColor : negativeColor)
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: mode === 'percent' ? 100 : undefined,
                        ticks: {
                            callback: mode === 'percent'
                                ? (value) => `${value}%`
                                : undefined
                        }
                    }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });

        this.chartInstances.push(chart);
    }

    _createBonusVsPenaltiesChart(categories) {
        const canvas = this._prepareCanvas(document.getElementById('bonusVsPenaltiesChart'));
        if (!canvas) return;

        const bonus = categories.filter(cat => cat.value < 0).reduce((sum, cat) => sum + Math.abs(cat.value), 0);
        const penalties = categories.filter(cat => cat.value > 0).reduce((sum, cat) => sum + cat.value, 0);
        const total = bonus + penalties;
        const positiveColor = this.palette?.success || '#10B981';
        const negativeColor = this.palette?.danger || '#EF4444';

        const chart = new Chart(canvas, {
            type: 'doughnut',
            data: {
                labels: ['Bonus', 'Pénalités'],
                datasets: [{
                    data: [bonus, penalties],
                    backgroundColor: [positiveColor, negativeColor]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const value = context.parsed;
                                const percentage = total ? ((value / total) * 100).toFixed(1) : 0;
                                return `${context.label}: ${value.toFixed(1)} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });

        this.chartInstances.push(chart);
    }

    _prepareCanvas(canvas, height = 320) {
        if (!canvas) {
            return null;
        }
        const parent = canvas.parentElement;
        if (parent) {
            parent.style.minHeight = `${height}px`;
        }
        canvas.setAttribute('height', height);
        canvas.style.height = `${height}px`;
        canvas.style.maxHeight = `${height}px`;
        canvas.style.width = '100%';
        return canvas;
    }

    _buildPalette() {
        return {
            success: this._getCssVar('--success', '#10B981'),
            danger: this._getCssVar('--danger', '#EF4444'),
            warning: this._getCssVar('--warning', '#F59E0B'),
            info: this._getCssVar('--info', '#3B82F6')
        };
    }

    _getCssVar(token, fallback) {
        if (typeof window === 'undefined' || !window.getComputedStyle) {
            return fallback;
        }
        const styles = getComputedStyle(document.documentElement);
        const value = styles.getPropertyValue(token);
        return value ? value.trim() || fallback : fallback;
    }

    _destroyCharts() {
        this.chartInstances.forEach(chart => {
            try {
                chart.destroy();
            } catch (e) {
            }
        });
        this.chartInstances = [];
    }

    _getCategoriesWithValues() {
        const b = this.breakdown;
        if (!b) return [];

        return [
            { label: 'Indisponibilité', value: b.contraintes_dures?.indisponibilite?.penalty || 0 },
            { label: 'Capacité', value: b.contraintes_dures?.capacite?.penalty || 0 },
            { label: 'Préférences gymnases', value: b.preferences_gymnases?.bonus_total || 0 },
            { label: 'Niveau gymnases', value: (b.niveau_gymnases?.bonus_total || 0) + (b.niveau_gymnases?.penalty_total || 0) },
            { label: 'Horaires préférés', value: (b.horaires_preferes?.matchs_apres?.penalty || 0) + (b.horaires_preferes?.matchs_avant_1_equipe?.penalty || 0) + (b.horaires_preferes?.matchs_avant_2_equipes?.penalty || 0) },
            { label: 'Espacement', value: b.espacement_repos?.penalty || 0 },
            { label: 'Compaction', value: b.compaction_temporelle?.penalty_total || 0 },
            { label: 'Overlaps institutions', value: b.contraintes_institutionnelles?.overlaps?.penalty || 0 },
            { label: 'Ententes', value: b.contraintes_institutionnelles?.ententes?.penalty || 0 },
            { label: 'Contraintes temporelles', value: b.contraintes_temporelles?.penalty || 0 },
            { label: 'Aller-retour', value: (b.aller_retour?.meme_semaine?.penalty || 0) + (b.aller_retour?.consecutives?.penalty || 0) },
            { label: 'Équilibrage', value: b.equilibrage_charge?.penalty || 0 }
        ];
    }

    _getPenaltyLabel(key) {
        const labels = {
            horaire_prefere: 'Horaire préféré',
            gymnase_prefere: 'Gymnase préféré',
            niveau_gymnase: 'Niveau gymnase',
            espacement: 'Espacement',
            compaction: 'Compaction',
            overlap: 'Overlap institution',
            aller_retour: 'Aller-retour',
            contrainte_temporelle: 'Contrainte temporelle',
            guidance_qualite: 'Guidance qualité',
            indisponibilite: 'Indisponibilité'
        };
        return labels[key] || key;
    }

    _exportBreakdown() {
        if (!this.breakdown) return;
        const blob = new Blob([JSON.stringify(this.breakdown, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const anchor = document.createElement('a');
        anchor.href = url;
        anchor.download = `penalty_breakdown_${new Date().toISOString().slice(0, 10)}.json`;
        anchor.click();
        URL.revokeObjectURL(url);
    }

    _exportDetailedCSV() {
        if (!this.breakdown) return;

        const rows = [['Catégorie', 'Sous-catégorie', 'Quantité', 'Valeur']];
        const b = this.breakdown;

        rows.push(['Contraintes dures', 'Indisponibilité', b.contraintes_dures?.indisponibilite?.violations || 0, b.contraintes_dures?.indisponibilite?.penalty || 0]);
        rows.push(['Contraintes dures', 'Capacité', b.contraintes_dures?.capacite?.violations || 0, b.contraintes_dures?.capacite?.penalty || 0]);
        rows.push(['Préférences gymnases', 'Matchs préférés', b.preferences_gymnases?.matchs_en_gymnases_preferes || 0, b.preferences_gymnases?.bonus_total || 0]);
        rows.push(['Niveau gymnases', 'Bien assignés', b.niveau_gymnases?.matchs_bien_assignes || 0, b.niveau_gymnases?.bonus_total || 0]);
        rows.push(['Niveau gymnases', 'Mal assignés', b.niveau_gymnases?.matchs_mal_assignes || 0, b.niveau_gymnases?.penalty_total || 0]);
        rows.push(['Horaires', 'Après préférences', b.horaires_preferes?.matchs_apres?.count || 0, b.horaires_preferes?.matchs_apres?.penalty || 0]);
        rows.push(['Horaires', 'Avant (1 équipe)', b.horaires_preferes?.matchs_avant_1_equipe?.count || 0, b.horaires_preferes?.matchs_avant_1_equipe?.penalty || 0]);
        rows.push(['Horaires', 'Avant (2 équipes)', b.horaires_preferes?.matchs_avant_2_equipes?.count || 0, b.horaires_preferes?.matchs_avant_2_equipes?.penalty || 0]);
        rows.push(['Compaction', 'Total', '-', b.compaction_temporelle?.penalty_total || 0]);
        Object.entries(b.compaction_temporelle?.par_semaine || {}).forEach(([week, data]) => {
            rows.push(['Compaction', `Semaine ${week}`, data.nb_matchs || 0, data.penalty || 0]);
        });
        rows.push(['Espacement', 'Violations', b.espacement_repos?.violations || 0, b.espacement_repos?.penalty || 0]);
        rows.push(['Institutions', 'Overlaps', b.contraintes_institutionnelles?.overlaps?.count || 0, b.contraintes_institutionnelles?.overlaps?.penalty || 0]);
        rows.push(['Institutions', 'Ententes non planifiées', b.contraintes_institutionnelles?.ententes?.non_planifiees || 0, b.contraintes_institutionnelles?.ententes?.penalty || 0]);
        rows.push(['Contraintes temporelles', 'Violations', b.contraintes_temporelles?.violations || 0, b.contraintes_temporelles?.penalty || 0]);
        rows.push(['Aller-retour', 'Même semaine', b.aller_retour?.meme_semaine?.count || 0, b.aller_retour?.meme_semaine?.penalty || 0]);
        rows.push(['Aller-retour', 'Consécutifs', b.aller_retour?.consecutives?.count || 0, b.aller_retour?.consecutives?.penalty || 0]);
        rows.push(['Équilibrage', 'Total', '-', b.equilibrage_charge?.penalty || 0]);

        const csv = rows.map(row => row.join(',')).join('\n');
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const anchor = document.createElement('a');
        anchor.href = url;
        anchor.download = `penalties_detailed_${new Date().toISOString().slice(0, 10)}.csv`;
        anchor.click();
        URL.revokeObjectURL(url);
    }
}

if (typeof window !== 'undefined') {
    window.PenaltiesView = PenaltiesView;
}
