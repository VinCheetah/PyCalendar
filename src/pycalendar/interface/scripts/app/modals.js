/**
 * modals.js - Gestion centralisée des modales et états d'erreur
 * 
 * Features:
 * - Ouverture/fermeture animée
 * - Focus trap pour accessibilité
 * - Fermeture via Escape
 * - Gestion des erreurs
 */

// ==================== FOCUS TRAP ==================== 

const FOCUSABLE_SELECTORS = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';

let lastFocusedElement = null;
let currentModal = null;

function trapFocus(modal) {
    if (!modal) return;
    
    const focusableElements = modal.querySelectorAll(FOCUSABLE_SELECTORS);
    const firstFocusable = focusableElements[0];
    const lastFocusable = focusableElements[focusableElements.length - 1];
    
    if (firstFocusable) {
        firstFocusable.focus();
    }
    
    modal.addEventListener('keydown', (e) => {
        if (e.key === 'Tab') {
            if (e.shiftKey) {
                if (document.activeElement === firstFocusable) {
                    e.preventDefault();
                    lastFocusable.focus();
                }
            } else {
                if (document.activeElement === lastFocusable) {
                    e.preventDefault();
                    firstFocusable.focus();
                }
            }
        }
    });
}

function handleModalKeydown(e) {
    if (e.key === 'Escape' && currentModal) {
        closeModal(currentModal);
    }
}

// ==================== MODAL OPEN/CLOSE ==================== 

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    
    lastFocusedElement = document.activeElement;
    currentModal = modal;
    
    modal.classList.remove('hidden');
    modal.setAttribute('aria-hidden', 'false');
    
    // Focus trap
    trapFocus(modal);
    
    // Keyboard events
    document.addEventListener('keydown', handleModalKeydown);
    
    // Prevent body scroll
    document.body.style.overflow = 'hidden';
    
    // Close on backdrop click
    const overlay = modal.querySelector('.modal-overlay') || modal;
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
            closeModal(modalId);
        }
    });
}

function closeModal(modalId) {
    const id = typeof modalId === 'string' ? modalId : modalId?.id;
    const modal = document.getElementById(id);
    if (!modal) return;
    
    modal.classList.add('hidden');
    modal.setAttribute('aria-hidden', 'true');
    
    // Restore focus
    if (lastFocusedElement) {
        lastFocusedElement.focus();
        lastFocusedElement = null;
    }
    
    currentModal = null;
    
    // Remove keyboard events
    document.removeEventListener('keydown', handleModalKeydown);
    
    // Restore body scroll
    document.body.style.overflow = '';
}

// ==================== EXPORT MODAL ==================== 

function openExportModal() {
    const modal = document.getElementById('modal-export');
    if (!modal) return;
    
    const count = window.modificationManager ? window.modificationManager.getModificationCount() : 0;
    const countElement = document.getElementById('export-count');
    if (countElement) {
        countElement.textContent = count;
    }
    
    const date = new Date().toISOString().split('T')[0];
    const filenameInput = document.getElementById('export-filename');
    if (filenameInput) {
        filenameInput.value = `pycalendar_modifications_${date}.json`;
    }
    
    openModal('modal-export');
}

function closeExportModal() {
    closeModal('modal-export');
}

function exportModifications() {
    if (!window.modificationManager) return;
    
    const filenameInput = document.getElementById('export-filename');
    const filename = filenameInput ? filenameInput.value : null;
    window.modificationManager.exportAndDownload(filename);
    closeExportModal();
}

// ==================== CALENDAR MODAL ==================== 

function openCalendarModal() {
    // Populate the calendar content
    populateCalendarContent();
    openModal('modal-calendar');
}

function closeCalendarModal() {
    closeModal('modal-calendar');
}

function populateCalendarContent() {
    const container = document.getElementById('calendar-weeks-content');
    if (!container || !window.dataManager) return;
    
    const weeks = window.dataManager.getAllWeeksWithDates();
    const config = window.dataManager.getConfig();
    const semainesBanalisees = config?.calendrier?.semaines_banalisees || [];
    
    let html = `
        <div class="calendar-weeks-grid">
            <div class="calendar-header-row">
                <div class="calendar-header-cell">Semaine</div>
                <div class="calendar-header-cell">Date (jeudi)</div>
                <div class="calendar-header-cell">Statut</div>
            </div>
    `;
    
    weeks.forEach(w => {
        const isBanalisee = semainesBanalisees.includes(w.week);
        const statusClass = isBanalisee ? 'calendar-week-banalisee' : 'calendar-week-active';
        const statusText = isBanalisee ? '🚫 Banalisée' : '✅ Active';
        const statusBadge = isBanalisee 
            ? '<span class="calendar-badge calendar-badge-banalisee">Pas de matchs</span>'
            : '<span class="calendar-badge calendar-badge-active">Matchs programmés</span>';
        
        html += `
            <div class="calendar-week-row ${statusClass}">
                <div class="calendar-week-number">
                    <span class="week-number-badge">S${w.week}</span>
                </div>
                <div class="calendar-week-date">
                    <span class="week-date-full">${w.dateFormatted}</span>
                </div>
                <div class="calendar-week-status">
                    ${statusBadge}
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    
    // Add legend
    html += `
        <div class="calendar-legend">
            <div class="legend-item">
                <span class="calendar-badge calendar-badge-active">Matchs programmés</span>
                <span class="legend-text">Semaine de compétition</span>
            </div>
            <div class="legend-item">
                <span class="calendar-badge calendar-badge-banalisee">Pas de matchs</span>
                <span class="legend-text">Semaine banalisée (vacances, examens...)</span>
            </div>
        </div>
    `;
    
    container.innerHTML = html;
}

// ==================== ERROR STATE ==================== 

function showError(message) {
    const container = document.querySelector('.app-container') || document.body;
    container.innerHTML = `
        <div class="error-state" role="alert" aria-live="assertive">
            <div class="error-icon" aria-hidden="true">❌</div>
            <h3 class="error-title">Erreur critique</h3>
            <p class="error-message">${message}</p>
            <p class="error-hint">Veuillez vérifier la console pour plus de détails.</p>
            <button class="btn btn-primary" onclick="location.reload()">
                🔄 Recharger la page
            </button>
        </div>
    `;
    console.error('PyCalendar Error:', message);
}

// ==================== TOAST NOTIFICATIONS ==================== 

function showToast(message, type = 'info', duration = 4000) {
    const container = document.getElementById('toast-container') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.setAttribute('role', 'status');
    toast.setAttribute('aria-live', 'polite');
    
    const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
    };
    
    toast.innerHTML = `
        <span class="toast-icon" aria-hidden="true">${icons[type] || icons.info}</span>
        <span class="toast-message">${message}</span>
        <button class="toast-close" aria-label="Fermer" onclick="this.parentElement.remove()">×</button>
    `;
    
    container.appendChild(toast);
    
    // Trigger animation
    requestAnimationFrame(() => {
        toast.classList.add('toast-visible');
    });
    
    // Auto-remove
    if (duration > 0) {
        setTimeout(() => {
            toast.classList.remove('toast-visible');
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }
    
    return toast;
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    container.setAttribute('aria-label', 'Notifications');
    document.body.appendChild(container);
    return container;
}

// ==================== GLOBAL EXPORTS ==================== 

if (typeof window !== 'undefined') {
    window.openModal = openModal;
    window.closeModal = closeModal;
    window.openExportModal = openExportModal;
    window.closeExportModal = closeExportModal;
    window.exportModifications = exportModifications;
    window.openCalendarModal = openCalendarModal;
    window.closeCalendarModal = closeCalendarModal;
    window.showError = showError;
    window.showToast = showToast;
}
