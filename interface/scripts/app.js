/**
 * app.js - Initialisation principale de l'application
 * 
 * Coordonne tous les composants et gère l'initialisation.
 */

/**
 * Initialise l'application
 */
function initializeApp() {
    console.log('🚀 Initialisation de PyCalendar Interface...');
    
    // Vérifier que toutes les dépendances sont chargées
    if (!window.DataManager || !window.ModificationManager) {
        console.error('❌ Modules core manquants');
        return;
    }
    
    // Charger les données de la solution
    const solutionDataElement = document.getElementById('solution-data');
    if (!solutionDataElement) {
        console.error('❌ Données de solution introuvables');
        showError('Impossible de charger les données du calendrier');
        return;
    }
    
    let solutionData;
    try {
        solutionData = JSON.parse(solutionDataElement.textContent);
        console.log('✅ Données chargées:', {
            version: solutionData.version,
            matchs_planifiés: solutionData.matches.scheduled.length,
            matchs_non_planifiés: solutionData.matches.unscheduled.length,
            équipes: solutionData.entities.equipes.length,
            gymnases: solutionData.entities.gymnases.length
        });
    } catch (error) {
        console.error('❌ Erreur parsing JSON:', error);
        showError('Format de données invalide');
        return;
    }
    
    // Initialiser les managers
    try {
        initializeManagers(solutionData);
        initializeComponents();
        initializeViews();
        initializeFilters();
        updateStatistics();
        setupEventListeners();
        
        console.log('✅ Application initialisée avec succès');
    } catch (error) {
        console.error('❌ Erreur d\'initialisation:', error);
        showError('Erreur lors de l\'initialisation: ' + error.message);
    }
}

/**
 * Initialise les managers globaux
 */
function initializeManagers(solutionData) {
    const solutionName = solutionData.metadata?.solution_name || 'unknown';
    
    // DataManager - gestion centralisée des données
    window.dataManager = new DataManager(solutionData);
    console.log('✅ DataManager initialisé');
    
    // ModificationManager - gestion des modifications
    window.modificationManager = new ModificationManager(solutionName);
    console.log('✅ ModificationManager initialisé');
    
    // Synchroniser les managers
    window.dataManager.subscribe('matches', (matches) => {
        // Mettre à jour les statistiques quand les matchs changent
        updateStatistics();
    });
}

/**
 * Initialise les composants
 */
function initializeComponents() {
    // MatchCard - composant de carte de match
    if (window.MatchCard) {
        window.matchCardComponent = new MatchCard(
            window.dataManager,
            window.modificationManager
        );
        console.log('✅ MatchCard initialisé');
    }
    
    // EditModal - modal d'édition
    if (window.EditModal) {
        window.editModal = new EditModal(
            window.dataManager,
            window.modificationManager
        );
        console.log('✅ EditModal initialisé');
    }
    
    // FilterPanel - panneau de filtres (sera initialisé par les vues)
    console.log('✅ Composants initialisés');
}

/**
 * Initialise les vues
 */
function initializeViews() {
    const agendaContainer = document.getElementById('agenda-view');
    const poolsContainer = document.getElementById('pools-view');
    const cardsContainer = document.getElementById('cards-view');
    
    // Vue Agenda
    if (window.AgendaView && agendaContainer) {
        window.agendaView = new AgendaView(window.dataManager, agendaContainer);
        window.agendaView.init();
        console.log('✅ AgendaView initialisée');
    }
    
    // Vue Poules
    if (window.PoolsView && poolsContainer) {
        window.poolsView = new PoolsView(window.dataManager, poolsContainer);
        window.poolsView.init();
        console.log('✅ PoolsView initialisée');
    }
    
    // Vue Cartes
    if (window.CardsView && cardsContainer) {
        window.cardsView = new CardsView(window.dataManager, cardsContainer);
        window.cardsView.init();
        console.log('✅ CardsView initialisée');
    }
}

/**
 * Initialise les filtres
 */
function initializeFilters() {
    const filtersContainer = document.querySelector('.filters-container');
    if (!filtersContainer || !window.FilterPanel) {
        console.warn('⚠️  Panneau de filtres non disponible');
        return;
    }
    
    window.filterPanel = new FilterPanel(window.dataManager, filtersContainer);
    
    // Connecter les filtres aux vues
    window.filterPanel.onChange((filters) => {
        // Notifier toutes les vues
        if (window.agendaView) window.agendaView.setFilters(filters);
        if (window.poolsView) window.poolsView.setFilters(filters);
        if (window.cardsView) window.cardsView.setFilters(filters);
    });
    
    console.log('✅ Filtres initialisés');
}

/**
 * Met à jour les statistiques dans l'en-tête
 */
function updateStatistics() {
    const data = window.dataManager.getData();
    
    // Matchs planifiés
    const statScheduled = document.getElementById('stat-scheduled');
    if (statScheduled) {
        statScheduled.textContent = data.matches.scheduled.length;
    }
    
    // Matchs non planifiés
    const statUnscheduled = document.getElementById('stat-unscheduled');
    if (statUnscheduled) {
        statUnscheduled.textContent = data.matches.unscheduled.length;
    }
    
    // Semaines
    const weeks = new Set(data.matches.scheduled.map(m => m.semaine).filter(w => w));
    const statWeeks = document.getElementById('stat-weeks');
    if (statWeeks) {
        statWeeks.textContent = weeks.size;
    }
    
    // Poules
    const statPools = document.getElementById('stat-pools');
    if (statPools) {
        statPools.textContent = data.entities.poules.length;
    }
    
    // Gymnases
    const statVenues = document.getElementById('stat-venues');
    if (statVenues) {
        statVenues.textContent = data.entities.gymnases.length;
    }
    
    // Modifications
    const statModifications = document.getElementById('stat-modifications');
    if (statModifications && window.modificationManager) {
        statModifications.textContent = window.modificationManager.getModificationCount();
    }
}

/**
 * Configure les écouteurs d'événements globaux
 */
function setupEventListeners() {
    // Bouton export
    const exportBtn = document.getElementById('btn-export-modifications');
    if (exportBtn) {
        exportBtn.addEventListener('click', () => {
            openExportModal();
        });
    }
    
    // Bouton reset
    const resetBtn = document.getElementById('btn-reset-modifications');
    if (resetBtn) {
        resetBtn.addEventListener('click', () => {
            if (confirm('Réinitialiser toutes les modifications ?')) {
                window.modificationManager.clearAll();
                window.dataManager.revertAllModifications();
                updateStatistics();
            }
        });
    }
    
    console.log('✅ Événements globaux configurés');
}

/**
 * Affiche une erreur à l'utilisateur
 */
function showError(message) {
    const container = document.querySelector('.app-container');
    if (container) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-banner';
        errorDiv.innerHTML = `
            <div class="error-content">
                <span class="error-icon">⚠️</span>
                <span class="error-message">${message}</span>
            </div>
        `;
        container.insertBefore(errorDiv, container.firstChild);
    }
}

// Initialiser quand le DOM est prêt
document.addEventListener('DOMContentLoaded', initializeApp);
