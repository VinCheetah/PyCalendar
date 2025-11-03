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

    render() {
        if (this._impl && typeof this._impl.render === 'function') {
            this._impl.render();
        } else if (this._impl && typeof this._impl.init === 'function') {
            // Fallback vers init si render n'existe pas
            this._impl.init();
        } else if (this.container) {
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

    /**
     * Retourne la configuration des options d'affichage pour cette vue.
     * @returns {object|null} Configuration pour ViewOptionsManager, ou null si aucune option.
     */
    getDisplayOptions() {
        // Tente de récupérer les options de l'implémentation réelle (AgendaGridView)
        if (this._impl && typeof this._impl.getDisplayOptions === 'function') {
            return this._impl.getDisplayOptions();
        }

        // Si l'implémentation ne fournit pas d'options, on retourne une configuration par défaut.
        // Cela assure la compatibilité et permet au wrapper de fonctionner même si AgendaGridView n'est pas à jour.
        return {
            title: "Options de l'Agenda",
            options: [
                {
                    type: 'select',
                    id: 'agenda-display-mode',
                    label: 'Afficher par',
                    values: [
                        { value: 'venue', text: 'Gymnase' },
                        { value: 'week', text: 'Semaine' }
                    ],
                    action: (value) => {
                        if (this._impl && typeof this._impl.setDisplayMode === 'function') {
                            this._impl.setDisplayMode(value);
                        } else {
                            console.warn("La méthode setDisplayMode n'est pas implémentée.");
                        }
                    }
                },
                {
                    type: 'checkbox',
                    id: 'agenda-show-available',
                    label: 'Afficher créneaux libres',
                    default: true,
                    action: (checked) => {
                        if (this._impl && typeof this._impl.setShowAvailableSlots === 'function') {
                            this._impl.setShowAvailableSlots(checked);
                        } else {
                            console.warn("La méthode setShowAvailableSlots n'est pas implémentée.");
                        }
                    }
                }
            ]
        };
    }
}

// Export global
if (typeof window !== 'undefined') {
    window.AgendaView = AgendaView;
}
