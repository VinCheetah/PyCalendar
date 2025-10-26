/**
 * agenda-view.js - Wrapper de compatibilité
 *
 * Certaines parties du code s'attendent à une classe `AgendaView`.
 * Le projet actuel définit `AgendaGridView`. Ce fichier crée une
 * classe légère `AgendaView` qui délègue vers `AgendaGridView` afin
 * d'assurer la compatibilité ascendante sans modifier le code appelant.
 */

class AgendaView {
    constructor(dataManager, container) {
        if (typeof window !== 'undefined' && window.AgendaGridView) {
            this._impl = new window.AgendaGridView(dataManager, container);
        } else {
            // Implémentation de secours minimale
            this._impl = null;
            this.container = container;
        }
    }

    init() {
        if (this._impl && typeof this._impl.init === 'function') {
            this._impl.init();
        } else if (this.container) {
            // Afficher un message d'erreur léger au lieu d'une page blanche
            this.container.innerHTML = `<div class="empty-state">Vue agenda indisponible</div>`;
        }
    }

    setFilters(filters) {
        if (this._impl && typeof this._impl.updateFilters === 'function') {
            this._impl.updateFilters(filters);
        } else if (this._impl && typeof this._impl.setFilters === 'function') {
            this._impl.setFilters(filters);
        }
    }

    // Déléguation générique pour les autres appels potentiels
    __get(target) {
        return this._impl ? this._impl[target] : undefined;
    }
}

// Export global
if (typeof window !== 'undefined') {
    window.AgendaView = AgendaView;
}
