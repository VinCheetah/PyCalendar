/**
 * agenda-view.js - Vue Agenda (grille horaire type planning)
 * 
 * Affiche les matchs dans une grille horaire avec:
 * - Heures en vertical
 * - Gymnases ou semaines en horizontal
 * - Créneaux de 2h pour chaque match
 */

class AgendaView {
    constructor(dataManager, container) {
        this.dataManager = dataManager;
        this.container = container;
        
        // Créer l'instance de la grille horaire
        this.gridView = new window.AgendaGridView(dataManager, container);
        
        // Subscribe to data changes
        this.dataManager.subscribe('matches', () => this.render());
    }
    
    /**
     * Initialise la vue
     */
    init() {
        this.gridView.init();
    }
    
    /**
     * Définit les filtres actifs
     */
    setFilters(filters) {
        this.gridView.updateFilters(filters);
    }
    
    /**
     * Affiche la vue complète
     */
    render() {
        this.gridView.render();
    }
}

// Export pour utilisation
window.AgendaView = AgendaView;
