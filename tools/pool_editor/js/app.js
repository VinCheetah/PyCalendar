/**
 * PyCalendar Pool Editor - Main Application
 * Entry point and orchestration
 */

class App {
    constructor() {
        this.initialized = false;
        this.currentSport = null;
        this.configPath = null;
    }
    
    /**
     * Initialize the application
     */
    async init() {
        console.log('🏐 Pool Editor - Initializing...');
        
        // Initialize all managers
        teamEditor.init();
        poolEditor.init();
        autoPools.init();
        statistics.init();
        
        // Setup UI
        this.setupTheme();
        this.setupEventListeners();
        this.setupKeyboardShortcuts();
        
        // Show config modal on start
        this.showConfigModal();
        
        this.initialized = true;
        console.log('✅ Pool Editor - Ready');
    }
    
    /**
     * Setup theme
     */
    setupTheme() {
        // Load saved theme
        const savedTheme = localStorage.getItem('poolEditorTheme') || 'light';
        document.documentElement.setAttribute('data-theme', savedTheme);
        
        // Update toggle button icons visibility
        const lightIcon = document.querySelector('.theme-icon-light');
        const darkIcon = document.querySelector('.theme-icon-dark');
        
        if (lightIcon && darkIcon) {
            lightIcon.style.display = savedTheme === 'light' ? 'inline' : 'none';
            darkIcon.style.display = savedTheme === 'dark' ? 'inline' : 'none';
        }
    }
    
    /**
     * Toggle theme
     */
    toggleTheme() {
        const current = document.documentElement.getAttribute('data-theme');
        const newTheme = current === 'dark' ? 'light' : 'dark';
        
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('poolEditorTheme', newTheme);
        
        // Update toggle button icons visibility
        const lightIcon = document.querySelector('.theme-icon-light');
        const darkIcon = document.querySelector('.theme-icon-dark');
        
        if (lightIcon && darkIcon) {
            lightIcon.style.display = newTheme === 'light' ? 'inline' : 'none';
            darkIcon.style.display = newTheme === 'dark' ? 'inline' : 'none';
        }
    }
    
    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Theme toggle
        document.getElementById('btn-theme')?.addEventListener('click', () => {
            this.toggleTheme();
        });
        
        // Help button
        document.getElementById('btn-help')?.addEventListener('click', () => {
            this.showModal('modal-help');
        });
        
        // Toolbar buttons
        document.getElementById('btn-export')?.addEventListener('click', () => {
            this.showModal('modal-export');
        });
        
        document.getElementById('btn-undo')?.addEventListener('click', () => {
            historyManager.undo();
        });
        
        document.getElementById('btn-redo')?.addEventListener('click', () => {
            historyManager.redo();
        });
        
        document.getElementById('btn-add-team')?.addEventListener('click', () => {
            teamEditor.openModal();
        });
        
        document.getElementById('btn-add-pool')?.addEventListener('click', () => {
            poolEditor.openModal();
        });
        
        document.getElementById('btn-auto-create')?.addEventListener('click', () => {
            this.showModal('modal-auto-create');
        });
        
        document.getElementById('btn-balance')?.addEventListener('click', () => {
            autoPools.balancePools();
        });
        
        document.getElementById('btn-import')?.addEventListener('click', () => {
            this.showModal('modal-import');
        });
        
        // Clear cache button
        document.getElementById('btn-clear-cache')?.addEventListener('click', () => {
            if (confirm('⚠️ Attention !\n\nCeci va effacer toutes les données en cache et recharger la page.\n\nVos modifications non sauvegardées seront perdues.\n\nContinuer ?')) {
                dataManager.clearStorage();
                window.location.reload();
            }
        });
        
        // Clear filters
        document.getElementById('btn-clear-filters')?.addEventListener('click', () => {
            document.getElementById('filter-institution').value = 'all';
            document.getElementById('filter-time').value = 'all';
            document.getElementById('filter-level').value = 'all';
            poolRenderer.clearFilters();
        });
        
        // View mode toggle
        document.querySelectorAll('.view-mode-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const viewMode = e.currentTarget.dataset.view;
                if (viewMode) {
                    // Update button states
                    document.querySelectorAll('.view-mode-btn').forEach(b => b.classList.remove('active'));
                    e.currentTarget.classList.add('active');
                    // Switch view
                    poolRenderer.setViewMode(viewMode);
                }
            });
        });
        
        // Filters
        document.getElementById('filter-level')?.addEventListener('change', (e) => {
            poolRenderer.setFilter('level', e.target.value);
        });
        
        document.getElementById('filter-time')?.addEventListener('change', (e) => {
            poolRenderer.setFilter('time', e.target.value);
        });
        
        document.getElementById('filter-institution')?.addEventListener('change', (e) => {
            poolRenderer.setFilter('institution', e.target.value);
        });
        
        // Import modal tabs
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });
        
        // File inputs - Excel direct
        document.getElementById('file-excel-direct')?.addEventListener('change', (e) => {
            this.handleExcelDirectFileChange(e);
        });
        
        // File inputs - YAML
        document.getElementById('file-yaml')?.addEventListener('change', (e) => {
            this.handleYamlFileChange(e);
        });
        
        // File inputs - Excel for YAML
        document.getElementById('file-excel')?.addEventListener('change', (e) => {
            this.handleExcelFileChange(e);
        });
        
        // File inputs - JSON
        document.getElementById('file-json')?.addEventListener('change', (e) => {
            this.handleJsonFileChange(e);
        });
        
        // Import buttons - new direct buttons
        document.getElementById('btn-import-excel')?.addEventListener('click', () => {
            this.importExcelDirect();
        });
        
        document.getElementById('btn-import-json')?.addEventListener('click', () => {
            this.importJson();
        });
        
        // Legacy import button (keep for compatibility)
        document.getElementById('btn-do-import')?.addEventListener('click', () => {
            this.doImport();
        });
        
        document.getElementById('btn-load-demo')?.addEventListener('click', () => {
            this.loadDemoData();
        });
        
        // Export buttons
        document.getElementById('btn-export-json')?.addEventListener('click', () => {
            this.exportJson();
        });
        
        document.getElementById('btn-export-csv')?.addEventListener('click', () => {
            this.exportCsv();
        });
        
        document.getElementById('btn-export-clipboard')?.addEventListener('click', () => {
            this.exportClipboard();
        });
        
        // Auto create modal
        document.getElementById('btn-do-auto-create')?.addEventListener('click', () => {
            this.doAutoCreate();
        });
        
        // Toggle unassigned section
        document.getElementById('toggle-unassigned')?.addEventListener('click', () => {
            const grid = document.getElementById('unassigned-grid');
            const btn = document.getElementById('toggle-unassigned');
            if (grid.style.display === 'none') {
                grid.style.display = 'grid';
                btn.textContent = '▼';
            } else {
                grid.style.display = 'none';
                btn.textContent = '▶';
            }
        });
        
        // Close modal buttons
        document.querySelectorAll('[data-close]').forEach(btn => {
            btn.addEventListener('click', () => {
                const modal = btn.closest('.modal');
                if (modal) {
                    this.closeModal(modal.id);
                }
            });
        });
        
        // Click backdrop to close
        document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
            backdrop.addEventListener('click', () => {
                const modal = backdrop.closest('.modal');
                if (modal) {
                    this.closeModal(modal.id);
                }
            });
        });
        
        // Data manager events
        dataManager.on('dataLoaded', () => {
            this.onDataLoaded();
        });
        
        dataManager.on('dataChanged', () => {
            poolRenderer.render();
            statistics.update();
            this.updateInstitutionFilter();
        });
    }
    
    /**
     * Setup keyboard shortcuts
     */
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + Z: Undo
            if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
                e.preventDefault();
                historyManager.undo();
            }
            
            // Ctrl/Cmd + Shift + Z or Ctrl/Cmd + Y: Redo
            if ((e.ctrlKey || e.metaKey) && (e.key === 'y' || (e.key === 'z' && e.shiftKey))) {
                e.preventDefault();
                historyManager.redo();
            }
            
            // Ctrl/Cmd + S: Save
            if ((e.ctrlKey || e.metaKey) && e.key === 's') {
                e.preventDefault();
                this.save();
            }
            
            // Escape: Close modals
            if (e.key === 'Escape') {
                document.querySelectorAll('.modal.active').forEach(modal => {
                    this.closeModal(modal.id);
                });
            }
        });
    }
    
    /**
     * Show modal
     */
    showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('active');
            // Focus first input
            const firstInput = modal.querySelector('input, select, textarea');
            if (firstInput) {
                setTimeout(() => firstInput.focus(), 100);
            }
        }
    }
    
    /**
     * Close modal
     */
    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('active');
        }
    }
    
    /**
     * Show config modal
     */
    showConfigModal() {
        this.showModal('modal-import');
    }
    
    /**
     * Switch import tab
     */
    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabName);
        });
        
        // Update tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.toggle('active', content.id === `tab-${tabName}`);
        });
    }
    
    /**
     * Handle Excel direct file change
     */
    handleExcelDirectFileChange(event) {
        const file = event.target.files[0];
        if (file) {
            document.getElementById('excel-direct-filename').textContent = file.name;
            document.getElementById('excel-direct-filename').classList.add('has-file');
            this.excelDirectFile = file;
        }
    }
    
    /**
     * Handle YAML file change
     */
    handleYamlFileChange(event) {
        const file = event.target.files[0];
        if (file) {
            document.getElementById('yaml-filename').textContent = file.name;
            this.yamlFile = file;
        }
    }
    
    /**
     * Handle JSON file change
     */
    handleJsonFileChange(event) {
        const file = event.target.files[0];
        if (file) {
            document.getElementById('json-filename').textContent = file.name;
            document.getElementById('json-filename').classList.add('has-file');
            this.jsonFile = file;
        }
    }
    
    /**
     * Handle Excel file change (for YAML import)
     */
    handleExcelFileChange(event) {
        const file = event.target.files[0];
        if (file) {
            document.getElementById('excel-filename').textContent = file.name;
            this.excelFile = file;
        }
    }
    
    /**
     * Do import - simplified version without tabs
     * Detects what file is available and imports accordingly
     */
    async doImport() {
        try {
            // Priority: Excel first, then JSON
            if (this.excelDirectFile) {
                await this.importExcelDirect();
            } else if (this.jsonFile) {
                await this.importJson();
            } else {
                Utils.showToast('Veuillez sélectionner un fichier à importer', 'warning');
            }
        } catch (error) {
            console.error('Import error:', error);
            Utils.showToast('Erreur: ' + error.message, 'error');
        }
    }
    
    /**
     * Do import based on active tab - legacy method for compatibility
     */
    async doImportLegacy() {
        const activeTab = document.querySelector('.tab-btn.active')?.dataset.tab;
        
        try {
            switch (activeTab) {
                case 'excel':
                    await this.importExcelDirect();
                    break;
                case 'yaml':
                    await this.importYaml();
                    break;
                case 'json':
                    await this.importJson();
                    break;
                case 'demo':
                    this.loadDemoData();
                    break;
                default:
                    Utils.showToast('Sélectionnez un type d\'import', 'warning');
            }
        } catch (error) {
            console.error('Import error:', error);
            Utils.showToast('Erreur: ' + error.message, 'error');
        }
    }
    
    /**
     * Import directly from Excel file
     */
    async importExcelDirect() {
        if (!this.excelDirectFile) {
            Utils.showToast('Veuillez sélectionner un fichier Excel', 'error');
            return;
        }
        
        const sport = document.getElementById('excel-sport')?.value || 'volleyball';
        this.handleSportChange(sport);
        
        const dataContent = await this.readFileAsArrayBuffer(this.excelDirectFile);
        const workbook = XLSX.read(dataContent, { type: 'array' });
        
        // Find teams sheet
        const teamsSheet = workbook.Sheets['Equipes'] || workbook.Sheets['equipes'] || workbook.Sheets[workbook.SheetNames[0]];
        
        if (!teamsSheet) {
            Utils.showToast('Feuille "Equipes" non trouvée', 'error');
            return;
        }
        
        const teamsData = XLSX.utils.sheet_to_json(teamsSheet);
        
        // Load Types_Poules if available
        let poolTypes = {};
        const typesSheet = workbook.Sheets['Types_Poules'];
        if (typesSheet) {
            const typesData = XLSX.utils.sheet_to_json(typesSheet);
            typesData.forEach(row => {
                const poule = row['Poule'] || row['poule'];
                const type = row['Type'] || row['type'];
                if (poule && type) {
                    const normalizedType = type.toString().toLowerCase();
                    if (normalizedType.includes('aller') && normalizedType.includes('retour')) {
                        poolTypes[poule.toString().trim()] = 'aller-retour';
                    } else {
                        poolTypes[poule.toString().trim()] = 'classique';
                    }
                }
            });
            console.log('Pool types loaded:', poolTypes);
        }
        
        console.log('Imported teams data:', teamsData);
        
        // Pass pool types to data manager
        dataManager.poolTypes = poolTypes;
        await dataManager.loadFromExcel(teamsData, { sport: { type: sport } });
        
        this.closeModal('modal-import');
        
        const teams = dataManager.getTeams();
        const pools = dataManager.getPools();
        Utils.showToast(`${teams.length} équipes et ${pools.length} poules importées`, 'success');
    }
    
    /**
     * Import from YAML + Excel
     * The YAML contains:
     * - fichiers.donnees: path to Excel file (e.g., "data/handball/config_handball.xlsx")
     * - sport.type: sport type ("volleyball", "handball", "basketball")
     */
    async importYaml() {
        if (!this.yamlFile) {
            Utils.showToast('Veuillez sélectionner un fichier YAML', 'error');
            return;
        }
        
        // Read YAML config
        const configContent = await this.readFileAsText(this.yamlFile);
        const config = jsyaml.load(configContent);
        
        console.log('YAML config loaded:', config);
        
        // Extract sport type from config
        const sportType = config?.sport?.type || 'volleyball';
        this.handleSportChange(sportType);
        
        // Show Excel path info from YAML if available
        const excelPath = config?.fichiers?.donnees;
        if (excelPath) {
            console.log('Excel path from YAML:', excelPath);
            Utils.showToast(`Config: ${excelPath}`, 'info');
        }
        
        // Check for Excel file - user must provide it as we can't access local filesystem
        if (!this.excelFile) {
            const msg = excelPath 
                ? `Veuillez sélectionner le fichier Excel: ${excelPath}`
                : 'Veuillez sélectionner un fichier Excel';
            Utils.showToast(msg, 'warning');
            return;
        }
        
        try {
            // Read Excel file
            const dataContent = await this.readFileAsArrayBuffer(this.excelFile);
            
            // Load using data manager with full YAML config
            await dataManager.loadFromYamlAndExcel(configContent, dataContent);
            
            // Update sport display
            this.handleSportChange(sportType);
            
            this.closeModal('modal-import');
            
            const teams = dataManager.getTeams();
            const pools = dataManager.getPools();
            Utils.showToast(
                `${teams.length} équipes et ${pools.length} poules importées (${sportType})`, 
                'success'
            );
        } catch (error) {
            console.error('Import error:', error);
            Utils.showToast('Erreur: ' + error.message, 'error');
        }
    }
    
    /**
     * Import from JSON
     */
    async importJson() {
        if (!this.jsonFile) {
            Utils.showToast('Veuillez sélectionner un fichier JSON', 'error');
            return;
        }
        
        const content = await this.readFileAsText(this.jsonFile);
        const data = JSON.parse(content);
        
        dataManager.loadFromJson(data);
        
        this.closeModal('modal-import');
        Utils.showToast('Données importées avec succès', 'success');
    }
    
    /**
     * Handle config file change
     */
    handleConfigFileChange(event) {
        const file = event.target.files[0];
        if (file) {
            document.getElementById('config-filename').textContent = file.name;
        }
    }
    
    /**
     * Handle data file change
     */
    handleDataFileChange(event) {
        const file = event.target.files[0];
        if (file) {
            document.getElementById('data-filename').textContent = file.name;
        }
    }
    
    /**
     * Handle sport change
     */
    handleSportChange(sport) {
        this.currentSport = sport;
        
        // Update UI based on sport
        const sportInfo = {
            volleyball: { prefix: 'VB', name: 'Volleyball', icon: '🏐' },
            basketball: { prefix: 'BB', name: 'Basketball', icon: '🏀' },
            handball: { prefix: 'HB', name: 'Handball', icon: '🤾' }
        };
        
        const info = sportInfo[sport];
        if (info) {
            document.getElementById('sport-name').textContent = info.name;
            document.getElementById('sport-icon').textContent = info.icon;
            Utils.SPORT_PREFIX = info.prefix;
        }
    }
    
    /**
     * Load configuration - kept for backward compatibility
     */
    async loadConfiguration() {
        await this.doImport();
    }
    
    /**
     * Read file as text
     */
    readFileAsText(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = (e) => reject(new Error('Erreur de lecture du fichier'));
            reader.readAsText(file);
        });
    }
    
    /**
     * Read file as array buffer
     */
    readFileAsArrayBuffer(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = (e) => reject(new Error('Erreur de lecture du fichier'));
            reader.readAsArrayBuffer(file);
        });
    }
    
    /**
     * On data loaded
     */
    onDataLoaded() {
        // Enable toolbar buttons
        document.querySelectorAll('.toolbar .btn').forEach(btn => {
            btn.disabled = false;
        });
        
        // Initialize managers
        dragDropManager.init();
        
        // Initial render
        poolRenderer.render();
        statistics.update();
        
        // Update institution filter
        this.updateInstitutionFilter();
        
        // Update sport label
        const sportLabel = document.getElementById('current-sport-label');
        if (sportLabel && this.currentSport) {
            sportLabel.textContent = this.currentSport.charAt(0).toUpperCase() + 
                                    this.currentSport.slice(1);
        }
    }
    
    /**
     * Update institution filter dropdown
     */
    updateInstitutionFilter() {
        const select = document.getElementById('filter-institution');
        if (!select) return;
        
        const institutions = dataManager.getInstitutions();
        
        // Clear existing options
        select.innerHTML = '<option value="">Toutes les institutions</option>';
        
        // Add institution options
        institutions.sort().forEach(inst => {
            const option = document.createElement('option');
            option.value = inst;
            option.textContent = inst;
            select.appendChild(option);
        });
    }
    
    /**
     * Do auto create pools
     */
    doAutoCreate() {
        try {
            autoPools.createAutoPools();
            this.closeModal('modal-auto-create');
        } catch (error) {
            console.error('Auto create error:', error);
            Utils.showToast('Erreur: ' + error.message, 'error');
        }
    }
    
    /**
     * Show auto pools modal - kept for backward compatibility
     */
    showAutoPoolsModal() {
        // Update summary
        const teams = dataManager.getTeams();
        const unassigned = teams.filter(t => !t.poule);
        
        const summary = document.getElementById('auto-pool-summary');
        if (summary) {
            summary.textContent = `${unassigned.length} équipes non assignées sur ${teams.length} total`;
        }
        
        this.showModal('modal-auto-create');
    }
    
    /**
     * Execute auto pools - kept for backward compatibility
     */
    executeAutoPools() {
        this.doAutoCreate();
    }
    
    /**
     * Show stats modal - for detailed statistics
     */
    showStatsModal() {
        const stats = statistics.getDetailedStats();
        
        // Update modal content if elements exist
        const el = (id) => document.getElementById(id);
        
        if (el('stats-teams-total')) el('stats-teams-total').textContent = stats.teams.total;
        if (el('stats-teams-assigned')) el('stats-teams-assigned').textContent = stats.teams.assigned;
        if (el('stats-teams-unassigned')) el('stats-teams-unassigned').textContent = stats.teams.unassigned;
        if (el('stats-pools-total')) el('stats-pools-total').textContent = stats.pools.total;
        if (el('stats-pools-ar')) el('stats-pools-ar').textContent = stats.pools.byType['aller-retour'];
        if (el('stats-matches-total')) el('stats-matches-total').textContent = stats.matches.total;
        if (el('stats-institutions')) el('stats-institutions').textContent = stats.institutions.count;
        
        this.showModal('modal-stats');
    }
    
    /**
     * Export stats as markdown
     */
    exportStats() {
        const report = statistics.generateReport();
        
        const blob = new Blob([report], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `stats_poules_${Utils.formatDate(new Date()).replace(/\//g, '-')}.md`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        
        URL.revokeObjectURL(url);
        
        Utils.showToast('Rapport exporté', 'success');
    }
    
    /**
     * Export as JSON
     */
    exportJson() {
        const data = dataManager.exportData();
        
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `poules_${Utils.formatDate(new Date()).replace(/\//g, '-')}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        
        URL.revokeObjectURL(url);
        
        this.closeModal('modal-export');
        Utils.showToast('Export JSON téléchargé', 'success');
    }
    
    /**
     * Export as CSV
     */
    exportCsv() {
        const teams = dataManager.getTeams();
        const pools = dataManager.getPools();
        
        // Create CSV content
        let csv = 'Équipe,Institution,Genre,Niveau,Horaire,Poule\n';
        
        teams.forEach(team => {
            const pool = pools.find(p => p.id === team.poule);
            const poolName = pool ? pool.name : '';
            csv += `"${team.nom}","${team.institution || ''}","${team.genre}","${team.niveau}","${team.horaire}","${poolName}"\n`;
        });
        
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `equipes_${Utils.formatDate(new Date()).replace(/\//g, '-')}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        
        URL.revokeObjectURL(url);
        
        this.closeModal('modal-export');
        Utils.showToast('Export CSV téléchargé', 'success');
    }
    
    /**
     * Export to clipboard
     */
    async exportClipboard() {
        const data = dataManager.exportData();
        
        try {
            await navigator.clipboard.writeText(JSON.stringify(data, null, 2));
            this.closeModal('modal-export');
            Utils.showToast('Données copiées dans le presse-papiers', 'success');
        } catch (error) {
            Utils.showToast('Erreur lors de la copie', 'error');
        }
    }
    
    /**
     * Save current state - generic save
     */
    save() {
        this.exportJson();
    }
    
    /**
     * Load demo data for testing
     */
    loadDemoData() {
        console.log('Loading demo data...');
        
        // Use the dataManager's built-in demo data
        try {
            dataManager.loadDemoData();
            this.closeModal('modal-import');
            Utils.showToast('Données de démo chargées !', 'success');
        } catch (error) {
            console.error('Error loading demo data:', error);
            Utils.showToast('Erreur: ' + error.message, 'error');
        }
    }
}

// Create global instance and initialize
const app = new App();

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    app.init();
});

// Export for use in other modules
window.app = app;
