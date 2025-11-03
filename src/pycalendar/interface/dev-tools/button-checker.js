/**
 * Button Checker - Vérifie que tous les boutons sont fonctionnels
 * Utilitaire pour diagnostiquer les problèmes de boutons
 */

const ButtonChecker = {
    /**
     * Vérifie tous les boutons de l'interface
     * @returns {Object} Rapport détaillé des boutons
     */
    checkAllButtons() {
        console.group('🔍 Vérification des boutons');
        
        const report = {
            theme: this.checkThemeButtons(),
            sport: this.checkSportButtons(),
            view: this.checkViewButtons(),
            sidebar: this.checkSidebarButtons(),
            action: this.checkActionButtons(),
            filter: this.checkFilterButtons(),
            export: this.checkExportButton(),
            help: this.checkHelpButton()
        };
        
        // Résumé
        const total = Object.values(report).reduce((sum, r) => sum + r.total, 0);
        const working = Object.values(report).reduce((sum, r) => sum + r.working, 0);
        const broken = total - working;
        
        console.log(`\n📊 Résumé: ${working}/${total} boutons fonctionnels`);
        
        if (broken > 0) {
            console.warn(`⚠️  ${broken} bouton(s) nécessite(nt) une correction`);
        } else {
            console.log('✅ Tous les boutons sont fonctionnels !');
        }
        
        console.groupEnd();
        
        return {
            ...report,
            summary: {
                total,
                working,
                broken,
                percentage: Math.round((working / total) * 100)
            }
        };
    },
    
    /**
     * Vérifie les boutons de thème
     */
    checkThemeButtons() {
        console.group('🎨 Boutons de thème');
        
        const buttons = document.querySelectorAll('.theme-btn');
        let working = 0;
        
        buttons.forEach((btn, index) => {
            const theme = btn.dataset.theme;
            const hasListener = this.hasEventListener(btn, 'click');
            const isAccessible = btn.getAttribute('aria-label') !== null;
            
            const status = hasListener && isAccessible;
            
            console.log(
                `${status ? '✅' : '❌'} Thème "${theme}":`,
                `Listener: ${hasListener ? '✓' : '✗'},`,
                `Accessible: ${isAccessible ? '✓' : '✗'}`
            );
            
            if (status) working++;
        });
        
        console.groupEnd();
        
        return {
            total: buttons.length,
            working,
            buttons: Array.from(buttons).map(btn => btn.dataset.theme)
        };
    },
    
    /**
     * Vérifie les boutons de sport
     */
    checkSportButtons() {
        console.group('🏐 Boutons de sport');
        
        const buttons = document.querySelectorAll('.sport-btn');
        let working = 0;
        
        buttons.forEach(btn => {
            const sport = btn.dataset.sport;
            const hasListener = this.hasEventListener(btn, 'click');
            const hasIcon = btn.querySelector('.sport-icon') !== null;
            const isAccessible = btn.getAttribute('aria-label') !== null;
            
            const status = hasListener && hasIcon && isAccessible;
            
            console.log(
                `${status ? '✅' : '❌'} Sport "${sport}":`,
                `Listener: ${hasListener ? '✓' : '✗'},`,
                `Icon: ${hasIcon ? '✓' : '✗'},`,
                `Accessible: ${isAccessible ? '✓' : '✗'}`
            );
            
            if (status) working++;
        });
        
        console.groupEnd();
        
        return {
            total: buttons.length,
            working,
            buttons: Array.from(buttons).map(btn => btn.dataset.sport)
        };
    },
    
    /**
     * Vérifie les boutons de vue
     */
    checkViewButtons() {
        console.group('👁️ Boutons de vue');
        
        const buttons = document.querySelectorAll('.view-btn');
        let working = 0;
        
        buttons.forEach(btn => {
            const view = btn.dataset.view;
            const hasListener = this.hasEventListener(btn, 'click');
            const hasIcon = btn.querySelector('.view-icon') !== null;
            const isAccessible = btn.getAttribute('aria-label') !== null;
            const hasContainer = document.getElementById(`${view}-view`) !== null;
            
            const status = hasListener && hasIcon && isAccessible && hasContainer;
            
            console.log(
                `${status ? '✅' : '❌'} Vue "${view}":`,
                `Listener: ${hasListener ? '✓' : '✗'},`,
                `Icon: ${hasIcon ? '✓' : '✗'},`,
                `Accessible: ${isAccessible ? '✓' : '✗'},`,
                `Container: ${hasContainer ? '✓' : '✗'}`
            );
            
            if (status) working++;
        });
        
        console.groupEnd();
        
        return {
            total: buttons.length,
            working,
            buttons: Array.from(buttons).map(btn => btn.dataset.view)
        };
    },
    
    /**
     * Vérifie les boutons de sidebar
     */
    checkSidebarButtons() {
        console.group('↔️ Boutons de sidebar');
        
        const buttons = [
            { id: 'btn-collapse-left', sidebar: 'sidebar-left' },
            { id: 'btn-collapse-right', sidebar: 'sidebar-right' }
        ];
        
        let working = 0;
        
        buttons.forEach(({ id, sidebar }) => {
            const btn = document.getElementById(id);
            const sidebarEl = document.querySelector(`.${sidebar}`);
            
            if (!btn) {
                console.warn(`❌ Bouton "${id}" non trouvé`);
                return;
            }
            
            const hasListener = this.hasEventListener(btn, 'click');
            const hasSidebar = sidebarEl !== null;
            const hasIcon = btn.querySelector('i') !== null;
            
            const status = hasListener && hasSidebar && hasIcon;
            
            console.log(
                `${status ? '✅' : '❌'} Bouton "${id}":`,
                `Listener: ${hasListener ? '✓' : '✗'},`,
                `Sidebar: ${hasSidebar ? '✓' : '✗'},`,
                `Icon: ${hasIcon ? '✓' : '✗'}`
            );
            
            if (status) working++;
        });
        
        console.groupEnd();
        
        return {
            total: buttons.length,
            working,
            buttons: buttons.map(b => b.id)
        };
    },
    
    /**
     * Vérifie les boutons d'action
     */
    checkActionButtons() {
        console.group('⚡ Boutons d'action');
        
        const buttons = [
            { id: 'btn-export', label: 'Exporter' },
            { id: 'btn-reset', label: 'Réinitialiser' },
            { id: 'btn-print', label: 'Imprimer' },
        ];
        
        let working = 0;
        
        buttons.forEach(({ id, label }) => {
            const btn = document.getElementById(id);
            
            if (!btn) {
                console.warn(`❌ Bouton "${label}" (${id}) non trouvé`);
                return;
            }
            
            const hasListener = this.hasEventListener(btn, 'click');
            const hasIcon = btn.querySelector('i') !== null;
            const isAccessible = btn.getAttribute('aria-label') !== null;
            
            const status = hasListener && hasIcon && isAccessible;
            
            console.log(
                `${status ? '✅' : '❌'} "${label}":`,
                `Listener: ${hasListener ? '✓' : '✗'},`,
                `Icon: ${hasIcon ? '✓' : '✗'},`,
                `Accessible: ${isAccessible ? '✓' : '✗'}`
            );
            
            if (status) working++;
        });
        
        console.groupEnd();
        
        return {
            total: buttons.length,
            working,
            buttons: buttons.map(b => b.id)
        };
    },
    
    /**
     * Vérifie les éléments de filtre
     */
    checkFilterButtons() {
        console.group('🔍 Éléments de filtre');
        
        const elements = {
            gender: document.querySelectorAll('input[name="gender"]'),
            week: document.querySelectorAll('input[name="week"]'),
            pool: document.getElementById('filter-pool'),
            institution: document.getElementById('filter-institution'),
            venue: document.getElementById('filter-venue'),
            days: document.querySelectorAll('input[name="day"]'),
            timeStart: document.getElementById('filter-time-start'),
            timeEnd: document.getElementById('filter-time-end'),
            state: document.querySelectorAll('input[name="state"]'),
            search: document.getElementById('filter-search'),
            clearBtn: document.getElementById('btn-clear-filters')
        };
        
        let working = 0;
        let total = 0;
        
        // Radio buttons (gender, week)
        ['gender', 'week'].forEach(name => {
            const radios = elements[name];
            total += radios.length;
            
            radios.forEach(radio => {
                const hasListener = this.hasEventListener(radio, 'change');
                if (hasListener) working++;
                
                console.log(
                    `${hasListener ? '✅' : '❌'} Radio "${name}" value="${radio.value}":`,
                    `Listener: ${hasListener ? '✓' : '✗'}`
                );
            });
        });
        
        // Select elements
        ['pool', 'institution', 'venue'].forEach(name => {
            const select = elements[name];
            total++;
            
            if (!select) {
                console.warn(`❌ Select "${name}" non trouvé`);
                return;
            }
            
            const hasListener = this.hasEventListener(select, 'change');
            if (hasListener) working++;
            
            console.log(
                `${hasListener ? '✅' : '❌'} Select "${name}":`,
                `Listener: ${hasListener ? '✓' : '✗'}`
            );
        });
        
        // Checkboxes (days, state)
        ['days', 'state'].forEach(name => {
            const checkboxes = elements[name];
            total += checkboxes.length;
            
            checkboxes.forEach(checkbox => {
                const hasListener = this.hasEventListener(checkbox, 'change');
                if (hasListener) working++;
                
                console.log(
                    `${hasListener ? '✅' : '❌'} Checkbox "${name}" value="${checkbox.value}":`,
                    `Listener: ${hasListener ? '✓' : '✗'}`
                );
            });
        });
        
        // Time inputs
        ['timeStart', 'timeEnd'].forEach(name => {
            const input = elements[name];
            total++;
            
            if (!input) {
                console.warn(`❌ Input "${name}" non trouvé`);
                return;
            }
            
            const hasListener = this.hasEventListener(input, 'change');
            if (hasListener) working++;
            
            console.log(
                `${hasListener ? '✅' : '❌'} Time input "${name}":`,
                `Listener: ${hasListener ? '✓' : '✗'}`
            );
        });
        
        // Search input
        const search = elements.search;
        total++;
        
        if (search) {
            const hasListener = this.hasEventListener(search, 'input');
            if (hasListener) working++;
            
            console.log(
                `${hasListener ? '✅' : '❌'} Search input:`,
                `Listener: ${hasListener ? '✓' : '✗'}`
            );
        } else {
            console.warn('❌ Search input non trouvé');
        }
        
        // Clear button
        const clearBtn = elements.clearBtn;
        total++;
        
        if (clearBtn) {
            const hasListener = this.hasEventListener(clearBtn, 'click');
            if (hasListener) working++;
            
            console.log(
                `${hasListener ? '✅' : '❌'} Clear filters button:`,
                `Listener: ${hasListener ? '✓' : '✗'}`
            );
        } else {
            console.warn('❌ Clear filters button non trouvé');
        }
        
        console.groupEnd();
        
        return {
            total,
            working,
            elements: Object.keys(elements)
        };
    },
    
    /**
     * Vérifie le bouton d'export
     */
    checkExportButton() {
        console.group('💾 Bouton d\'export');
        
        const btn = document.getElementById('btn-export');
        const modal = document.getElementById('export-modal');
        const closeBtn = modal?.querySelector('.modal-close');
        const exportBtn = modal?.querySelector('.btn-primary');
        
        let working = 0;
        let total = 3; // btn, close, export
        
        if (btn && this.hasEventListener(btn, 'click')) {
            console.log('✅ Bouton d\'export: Listener présent');
            working++;
        } else {
            console.warn('❌ Bouton d\'export: Pas de listener');
        }
        
        if (modal) {
            console.log('✅ Modal d\'export: Trouvée');
        } else {
            console.warn('❌ Modal d\'export: Non trouvée');
        }
        
        if (closeBtn && this.hasEventListener(closeBtn, 'click')) {
            console.log('✅ Bouton fermer modal: Listener présent');
            working++;
        } else {
            console.warn('❌ Bouton fermer modal: Pas de listener');
        }
        
        if (exportBtn && this.hasEventListener(exportBtn, 'click')) {
            console.log('✅ Bouton export dans modal: Listener présent');
            working++;
        } else {
            console.warn('❌ Bouton export dans modal: Pas de listener');
        }
        
        console.groupEnd();
        
        return { total, working };
    },
    
    /**
     * Vérifie le bouton d'aide
     */
    checkHelpButton() {
        console.group('❓ Bouton d\'aide');
        
        const btn = document.querySelector('[aria-label="Aide"]');
        const modal = document.getElementById('help-modal');
        const closeBtn = modal?.querySelector('.modal-close');
        
        let working = 0;
        let total = 2; // btn, close
        
        if (btn && this.hasEventListener(btn, 'click')) {
            console.log('✅ Bouton d\'aide: Listener présent');
            working++;
        } else {
            console.warn('❌ Bouton d\'aide: Pas de listener');
        }
        
        if (modal) {
            console.log('✅ Modal d\'aide: Trouvée');
        } else {
            console.warn('❌ Modal d\'aide: Non trouvée');
        }
        
        if (closeBtn && this.hasEventListener(closeBtn, 'click')) {
            console.log('✅ Bouton fermer modal: Listener présent');
            working++;
        } else {
            console.warn('❌ Bouton fermer modal: Pas de listener');
        }
        
        console.groupEnd();
        
        return { total, working };
    },
    
    /**
     * Vérifie si un élément a un event listener
     * Note: Cette méthode est approximative car on ne peut pas directement
     * vérifier les listeners en JavaScript
     */
    hasEventListener(element, eventType) {
        // On teste en regardant si l'élément a des propriétés de listener
        // C'est une approximation, pas parfait mais utile
        
        if (!element) return false;
        
        // Vérifie onclick, onchange, etc.
        const onEventProp = 'on' + eventType;
        if (element[onEventProp]) return true;
        
        // Vérifie addEventListener via getEventListeners (Chrome DevTools only)
        if (typeof getEventListeners === 'function') {
            const listeners = getEventListeners(element);
            return listeners[eventType]?.length > 0;
        }
        
        // Fallback: assume listener exists if element has appropriate data attributes
        // or is part of initialized components
        return element.hasAttribute('data-initialized') ||
               element.closest('[data-initialized]') !== null;
    },
    
    /**
     * Test interactif d'un bouton
     */
    testButton(selector) {
        const element = document.querySelector(selector);
        
        if (!element) {
            console.error(`❌ Élément "${selector}" non trouvé`);
            return;
        }
        
        console.log(`🧪 Test du bouton: ${selector}`);
        
        // Simule un click
        try {
            element.click();
            console.log('✅ Click simulé avec succès');
        } catch (error) {
            console.error('❌ Erreur lors du click:', error);
        }
    }
};

// Export pour utilisation globale
if (typeof window !== 'undefined') {
    window.ButtonChecker = ButtonChecker;
    
    // Commande rapide dans la console
    console.log('💡 Utilisez ButtonChecker.checkAllButtons() pour vérifier tous les boutons');
    console.log('💡 Utilisez ButtonChecker.testButton(".btn") pour tester un bouton spécifique');
}
