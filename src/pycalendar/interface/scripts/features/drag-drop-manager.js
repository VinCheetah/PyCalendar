/**
 * DragDropManager - Stub minimal pour le drag & drop
 *
 * Fournit une implémentation légère qui évite les erreurs si le module complet
 * n'est pas présent. Elle expose l'API utilisée par `AgendaGridView` :
 * - constructeur(dataManager, modificationManager)
 * - initializeDragDrop(container)
 * - onModification (callback)
 */

class DragDropManager {
    constructor(dataManager, modificationManager) {
        this.dataManager = dataManager;
        this.modificationManager = modificationManager;
        this.onModification = null; // callback à appeler quand une modification est faite
    }

    /**
     * Initialise le drag & drop dans le conteneur. Implémentation no-op sûre.
     */
    initializeDragDrop(container) {
        // Si nécessaire, on peut attacher des listeners basiques pour UX minimal
        // Mais par défaut, on ne fait rien pour rester non-intrusif.
        this.container = container;

        // Exemple : détecter le drop d'un élément avec data-match-id et appeler la callback
        container.querySelectorAll('[data-drop-zone]').forEach(zone => {
            zone.addEventListener('dragover', (e) => e.preventDefault());
            zone.addEventListener('drop', (e) => {
                e.preventDefault();
                try {
                    const matchId = e.dataTransfer?.getData('text/match-id');
                    if (matchId && this.modificationManager && typeof this.modificationManager.applyDrop === 'function') {
                        // appeler l'API de modification si disponible
                        this.modificationManager.applyDrop(matchId, zone.dataset.time, zone.dataset.column);
                        if (typeof this.onModification === 'function') this.onModification();
                    }
                } catch (err) {
                    // silencieux
                }
            });
        });
    }

    /**
     * Méthode utilitaire pour déclencher la callback (utile pour tests)
     */
    triggerModification() {
        if (typeof this.onModification === 'function') this.onModification();
    }
}

// Export global
if (typeof window !== 'undefined') {
    window.DragDropManager = DragDropManager;
}
