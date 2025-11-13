/**
 * ViewOptionsManager - Gère les options d'affichage dynamiques dans la barre latérale
 * 
 * Ce gestionnaire affiche les options spécifiques à chaque vue active
 * et gère les interactions utilisateur avec ces options.
 */

class ViewOptionsManager {
    constructor(container) {
        this.container = container;
        this.currentView = null;
        this.viewInstances = {};
    }

    /**
     * Enregistre une vue et son instance
     */
    registerView(viewName, viewInstance) {
        this.viewInstances[viewName] = viewInstance;
    }

    /**
     * Change la vue active et met à jour les options affichées
     */
    switchView(viewName) {
        this.currentView = viewName;
        this.render();
    }

    /**
     * Affiche les options pour la vue courante
     */
    render() {
        if (!this.container) return;

        const viewInstance = this.viewInstances[this.currentView];
        
        if (viewInstance && typeof viewInstance.getDisplayOptions === 'function') {
            const optionsConfig = viewInstance.getDisplayOptions();
            this.container.innerHTML = this._generateOptionsHTML(optionsConfig);
            this._attachEventListeners(optionsConfig);
        } else {
            this.container.innerHTML = '';
        }
    }

    /**
     * Génère le HTML des options
     */
    _generateOptionsHTML(config) {
        if (!config || !config.options || config.options.length === 0) {
            return '';
        }

        let html = `
            <div class="control-section view-options-section">
                <h3 class="control-section-title">${config.title || 'Options'}</h3>
                <div class="option-group">
        `;

        config.options.forEach(option => {
            switch (option.type) {
                case 'button-group':
                    html += this._generateButtonGroup(option);
                    break;
                case 'select':
                    html += this._generateSelect(option);
                    break;
                case 'checkbox':
                    html += this._generateCheckbox(option);
                    break;
            }
        });

        html += `
                </div>
            </div>
        `;

        return html;
    }

    /**
     * Génère un groupe de boutons
     */
    _generateButtonGroup(option) {
        let html = `
            <div class="option-item" style="margin-bottom: 1.5rem;">
                <label class="option-label-full" style="display: block; font-weight: 600; margin-bottom: 0.75rem; color: #1e293b; font-size: 0.875rem; text-transform: uppercase; letter-spacing: 0.5px;">${option.label}</label>
                <div class="display-format-buttons" style="display: flex; flex-direction: column; gap: 0.5rem;">
        `;

        option.values.forEach(value => {
            const isActive = value.value === option.default;
            const activeStyles = isActive 
                ? 'background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; font-weight: 600; box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);' 
                : 'background: white; color: #475569; border: 2px solid #e2e8f0;';
            
            html += `
                <button class="display-option-btn ${isActive ? 'active' : ''}" 
                        data-option-id="${option.id}" 
                        data-value="${value.value}"
                        style="padding: 0.75rem 1rem; border-radius: 8px; border: none; cursor: pointer; transition: all 0.2s ease; font-size: 0.875rem; text-align: left; ${activeStyles}">
                    ${value.text}
                </button>
            `;
        });

        html += `
                </div>
            </div>
        `;

        return html;
    }

    /**
     * Génère un sélecteur
     */
    _generateSelect(option) {
        let html = `
            <div class="option-item">
                <label class="option-label-full">${option.label}</label>
                <select class="form-select-sidebar" data-option-id="${option.id}">
        `;

        option.values.forEach(value => {
            const selected = value.value === option.default ? 'selected' : '';
            html += `<option value="${value.value}" ${selected}>${value.text}</option>`;
        });

        html += `
                </select>
            </div>
        `;

        return html;
    }

    /**
     * Génère une case à cocher
     */
    _generateCheckbox(option) {
        return `
            <label class="option-item">
                <input type="checkbox" 
                       data-option-id="${option.id}" 
                       ${option.default ? 'checked' : ''}>
                <span class="option-label">${option.label}</span>
            </label>
        `;
    }

    /**
     * Attache les écouteurs d'événements
     */
    _attachEventListeners(config) {
        if (!this.container) return;

        // Gestion des groupes de boutons
        const buttons = this.container.querySelectorAll('.display-option-btn');
        buttons.forEach(button => {
            button.addEventListener('click', (e) => {
                const optionId = e.currentTarget.dataset.optionId;
                const value = e.currentTarget.dataset.value;
                
                // Trouver l'option correspondante
                const option = config.options.find(opt => opt.id === optionId);
                if (option && option.action) {
                    option.action(value);
                    
                    // Mettre à jour l'état visuel des boutons avec styles inline
                    const groupButtons = this.container.querySelectorAll(`[data-option-id="${optionId}"]`);
                    groupButtons.forEach(btn => {
                        btn.classList.remove('active');
                        // Style inactif
                        btn.style.background = 'white';
                        btn.style.color = '#475569';
                        btn.style.border = '2px solid #e2e8f0';
                        btn.style.fontWeight = 'normal';
                        btn.style.boxShadow = 'none';
                    });
                    
                    e.currentTarget.classList.add('active');
                    // Style actif
                    e.currentTarget.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
                    e.currentTarget.style.color = 'white';
                    e.currentTarget.style.border = 'none';
                    e.currentTarget.style.fontWeight = '600';
                    e.currentTarget.style.boxShadow = '0 4px 12px rgba(102, 126, 234, 0.4)';
                }
            });
        });

        // Gestion des sélecteurs
        const selects = this.container.querySelectorAll('select[data-option-id]');
        selects.forEach(select => {
            select.addEventListener('change', (e) => {
                const optionId = e.currentTarget.dataset.optionId;
                const value = e.currentTarget.value;
                
                const option = config.options.find(opt => opt.id === optionId);
                if (option && option.action) {
                    option.action(value);
                }
            });
        });

        // Gestion des cases à cocher
        const checkboxes = this.container.querySelectorAll('input[type="checkbox"][data-option-id]');
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const optionId = e.currentTarget.dataset.optionId;
                const checked = e.currentTarget.checked;
                
                const option = config.options.find(opt => opt.id === optionId);
                if (option && option.action) {
                    option.action(checked);
                }
            });
        });
    }
}

// Export global
if (typeof window !== 'undefined') {
    window.ViewOptionsManager = ViewOptionsManager;
}
