/**
 * ui-controls.js - Gestion des interactions UI globales (événements, sidebars, thèmes)
 */

const THEME_STORAGE_KEY = 'pycalendar-theme';
const PALETTE_STORAGE_KEY = 'pycalendar-palette';

function logThemeDiagnostics(context = 'manual') {
    if (typeof window === 'undefined') return;
    const html = document.documentElement;
    const body = document.body;
    const agendaContainer = document.querySelector('.agenda-view-container');
    const colorClasses = agendaContainer
        ? Array.from(agendaContainer.classList).filter(cls => cls.startsWith('color-'))
        : [];

    console.groupCollapsed(`[Theme] Diagnostics :: ${context}`);
    console.info('html[data-theme]', html?.getAttribute('data-theme') || '(none)');
    console.info('body[data-theme]', body?.getAttribute('data-theme') || '(none)');
    console.info('data-palette', html?.getAttribute('data-palette') || 'purple');
    console.info('color-classes', colorClasses.length ? colorClasses : '(none)');
    console.groupEnd();
}

bootstrapAppearancePreferences();

function bootstrapAppearancePreferences() {
    if (typeof window === 'undefined') return;
    try {
        const savedTheme = localStorage.getItem(THEME_STORAGE_KEY);
        if (savedTheme) {
            applyThemeAttributes(savedTheme);
            console.info('[Theme] Bootstrap restore', savedTheme);
            logThemeDiagnostics('bootstrap-theme');
        }

        const savedPalette = localStorage.getItem(PALETTE_STORAGE_KEY);
        if (savedPalette && savedPalette !== 'purple') {
            document.documentElement.setAttribute('data-palette', savedPalette);
            console.info('[Palette] Bootstrap restore', savedPalette);
            logThemeDiagnostics('bootstrap-palette');
        }
    } catch (error) {
        console.warn('[Theme] Unable to bootstrap preferences', error);
    }
}

function setupEventListeners() {
    document.querySelectorAll('.view-btn').forEach(btn => {
        btn.addEventListener('click', () => switchView(btn.dataset.view));
    });

    const exportBtn = document.getElementById('btn-export-modifications');
    if (exportBtn) exportBtn.addEventListener('click', openExportModal);

    const resetBtn = document.getElementById('btn-reset-modifications');
    if (resetBtn) {
        resetBtn.addEventListener('click', () => {
            if (confirm('Voulez-vous vraiment réinitialiser toutes les modifications ?')) {
                window.modificationManager.clearAll();
                window.dataManager.revertAllModifications();
            }
        });
    }
    
    // Bouton calendrier des semaines
    const calendarBtn = document.getElementById('btn-calendar');
    if (calendarBtn) {
        calendarBtn.addEventListener('click', () => {
            if (typeof openCalendarModal === 'function') {
                openCalendarModal();
            }
        });
    }
    
    setupThemeControls();
    setupPaletteControls();
    setupAnimationControls();
    setupSidebarControls();
    setupSidebarResize();
}

function setupSidebarControls() {
    const btnCollapseLeft = document.getElementById('btn-collapse-left');
    const btnCollapseRight = document.getElementById('btn-collapse-right');
    const btnShowLeft = document.getElementById('btn-show-left');
    const btnShowRight = document.getElementById('btn-show-right');
    const sidebarLeft = document.querySelector('.sidebar-left');
    const sidebarRight = document.querySelector('.sidebar-right');
    
    function toggleSidebar(sidebar, btnCollapse, side) {
        if (!sidebar) return;
        const isCollapsed = sidebar.classList.contains('collapsed');
        if (isCollapsed) {
            sidebar.classList.remove('collapsed');
            if (btnCollapse) {
                btnCollapse.querySelector('span').textContent = side === 'left' ? '◀' : '▶';
                btnCollapse.setAttribute('title', 'Réduire');
            }
        } else {
            sidebar.classList.add('collapsed');
            if (btnCollapse) {
                btnCollapse.querySelector('span').textContent = side === 'left' ? '▶' : '◀';
                btnCollapse.setAttribute('title', 'Développer');
            }
        }
        localStorage.setItem(`sidebar-${side}-collapsed`, !isCollapsed);
        requestAnimationFrame(() => updateGridColumns());
    }

    if (btnCollapseLeft && sidebarLeft) {
        btnCollapseLeft.addEventListener('click', () => toggleSidebar(sidebarLeft, btnCollapseLeft, 'left'));
        if (localStorage.getItem('sidebar-left-collapsed') === 'true') {
            sidebarLeft.classList.add('collapsed');
            btnCollapseLeft.querySelector('span').textContent = '▶';
            btnCollapseLeft.setAttribute('title', 'Développer');
        }
    }

    if (btnShowLeft && sidebarLeft) {
        btnShowLeft.addEventListener('click', () => toggleSidebar(sidebarLeft, btnCollapseLeft, 'left'));
    }

    if (btnCollapseRight && sidebarRight) {
        btnCollapseRight.addEventListener('click', () => toggleSidebar(sidebarRight, btnCollapseRight, 'right'));
        if (localStorage.getItem('sidebar-right-collapsed') === 'true') {
            sidebarRight.classList.add('collapsed');
            btnCollapseRight.querySelector('span').textContent = '◀';
            btnCollapseRight.setAttribute('title', 'Développer');
        }
    }

    if (btnShowRight && sidebarRight) {
        btnShowRight.addEventListener('click', () => toggleSidebar(sidebarRight, btnCollapseRight, 'right'));
    }

    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 'b') {
            e.preventDefault();
            if (e.shiftKey) {
                toggleSidebar(sidebarRight, btnCollapseRight, 'right');
            } else {
                toggleSidebar(sidebarLeft, btnCollapseLeft, 'left');
            }
        }
    });
}

function setupSidebarResize() {
    const resizeHandleLeft = document.getElementById('resize-handle-left');
    const resizeHandleRight = document.getElementById('resize-handle-right');
    const sidebarLeft = document.querySelector('.sidebar-left');
    const sidebarRight = document.querySelector('.sidebar-right');
    
    const MIN_WIDTH = 250;
    const MAX_WIDTH = 600;
    const DEFAULT_LEFT_WIDTH = 280;
    const DEFAULT_RIGHT_WIDTH = 320;
    
    let isResizing = false;
    let currentSidebar = null;
    let currentHandle = null;
    let startX = 0;
    let startWidth = 0;
    let pendingAnimationFrame = null;

    function scheduleGridUpdate() {
        if (pendingAnimationFrame) return;
        pendingAnimationFrame = requestAnimationFrame(() => {
            updateGridColumns();
            pendingAnimationFrame = null;
        });
    }
    
    function updateGridColumns() {
        const mainLayout = document.querySelector('.main-layout');
        if (!mainLayout) return;
        
        const leftWidth = sidebarLeft && !sidebarLeft.classList.contains('collapsed') 
            ? (sidebarLeft.offsetWidth || DEFAULT_LEFT_WIDTH) + 'px'
            : '0px';
        const rightWidth = sidebarRight && !sidebarRight.classList.contains('collapsed') 
            ? (sidebarRight.offsetWidth || DEFAULT_RIGHT_WIDTH) + 'px'
            : '0px';
        
        const leftHandle = leftWidth !== '0px' ? '4px' : '0px';
        const rightHandle = rightWidth !== '0px' ? '4px' : '0px';
        
        mainLayout.style.gridTemplateColumns = `${leftWidth} ${leftHandle} 1fr ${rightHandle} ${rightWidth}`;
    }
    
    window.updateGridColumns = updateGridColumns;
    
    function restoreSidebarWidths() {
        const savedLeftWidth = localStorage.getItem('sidebar-left-width');
        const savedRightWidth = localStorage.getItem('sidebar-right-width');
        
        if (sidebarLeft && savedLeftWidth) {
            const width = parseInt(savedLeftWidth, 10);
            if (width >= MIN_WIDTH && width <= MAX_WIDTH) {
                sidebarLeft.style.width = width + 'px';
            }
        }
        
        if (sidebarRight && savedRightWidth) {
            const width = parseInt(savedRightWidth, 10);
            if (width >= MIN_WIDTH && width <= MAX_WIDTH) {
                sidebarRight.style.width = width + 'px';
            }
        }
        updateGridColumns();
    }
    
    restoreSidebarWidths();
    
    function setupDoubleClickReset(handle, sidebar, defaultWidth) {
        if (!handle || !sidebar) return;
        handle.addEventListener('dblclick', () => {
            sidebar.style.width = defaultWidth + 'px';
            const side = sidebar.classList.contains('sidebar-left') ? 'left' : 'right';
            localStorage.setItem(`sidebar-${side}-width`, defaultWidth);
            updateGridColumns();
            handle.style.transform = 'scaleX(2)';
            setTimeout(() => {
                handle.style.transform = '';
            }, 200);
        });
    }
    
    setupDoubleClickReset(resizeHandleLeft, sidebarLeft, DEFAULT_LEFT_WIDTH);
    setupDoubleClickReset(resizeHandleRight, sidebarRight, DEFAULT_RIGHT_WIDTH);
    
    function startResize(e, handle, sidebar) {
        if (!sidebar || sidebar.classList.contains('collapsed')) return;
        isResizing = true;
        currentHandle = handle;
        currentSidebar = sidebar;
        startX = e.clientX;
        startWidth = sidebar.offsetWidth;
        if (handle) handle.classList.add('resizing');
        document.body.classList.add('resizing');
        e.preventDefault();
    }
    
    function stopResize() {
        if (!isResizing) return;
        isResizing = false;
        if (currentHandle) currentHandle.classList.remove('resizing');
        document.body.classList.remove('resizing');
        if (currentSidebar) {
            const side = currentSidebar.classList.contains('sidebar-left') ? 'left' : 'right';
            localStorage.setItem(`sidebar-${side}-width`, currentSidebar.offsetWidth);
        }
        currentHandle = null;
        currentSidebar = null;
    }
    
    function resize(e) {
        if (!isResizing || !currentSidebar) return;
        const isLeft = currentSidebar.classList.contains('sidebar-left');
        const delta = isLeft ? (e.clientX - startX) : (startX - e.clientX);
        const newWidth = Math.max(MIN_WIDTH, Math.min(MAX_WIDTH, startWidth + delta));
        currentSidebar.style.width = newWidth + 'px';
        scheduleGridUpdate();
    }
    
    if (resizeHandleLeft && sidebarLeft) {
        resizeHandleLeft.addEventListener('mousedown', (e) => startResize(e, resizeHandleLeft, sidebarLeft));
    }
    
    if (resizeHandleRight && sidebarRight) {
        resizeHandleRight.addEventListener('mousedown', (e) => startResize(e, resizeHandleRight, sidebarRight));
    }
    
    document.addEventListener('mousemove', resize);
    document.addEventListener('mouseup', stopResize);
    window.addEventListener('resize', () => scheduleGridUpdate());
    setTimeout(() => updateGridColumns(), 100);
}

function setupThemeControls() {
    const themeButtons = document.querySelectorAll('.theme-btn');
    if (!themeButtons.length) {
        console.warn('[Theme] No theme buttons found in DOM');
        return;
    }
    themeButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const theme = btn.dataset.theme;
            if (!theme) return;
            setTheme(theme);
            themeButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        });
    });
}

function setupPaletteControls() {
    const paletteButtons = document.querySelectorAll('.palette-btn');
    paletteButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const palette = btn.dataset.palette;
            if (!palette) return;
            setPalette(palette);
            paletteButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        });
    });
}

function setPalette(palette) {
    const html = document.documentElement;
    if (palette === 'purple') {
        html.removeAttribute('data-palette');
    } else {
        html.setAttribute('data-palette', palette);
    }
    localStorage.setItem(PALETTE_STORAGE_KEY, palette);
    console.info('[Palette] Applied', palette || 'purple');
    logThemeDiagnostics('palette-change');
}

function loadSavedPalette() {
    const savedPalette = localStorage.getItem(PALETTE_STORAGE_KEY) || 'purple';
    setPalette(savedPalette);
    const activeBtn = document.querySelector(`.palette-btn[data-palette="${savedPalette}"]`);
    if (activeBtn) {
        document.querySelectorAll('.palette-btn').forEach(btn => btn.classList.remove('active'));
        activeBtn.classList.add('active');
    }
}

function setupAnimationControls() {
    const animCheckbox = document.getElementById('opt-animations');
    if (!animCheckbox) return;
    animCheckbox.addEventListener('change', () => {
        const level = animCheckbox.checked ? 1 : 0;
        setAnimationLevel(level);
    });
    const savedLevel = localStorage.getItem('pycalendar-animation-level') || '1';
    setAnimationLevel(parseInt(savedLevel, 10));
    animCheckbox.checked = savedLevel !== '0';
}

function setAnimationLevel(level) {
    const html = document.documentElement;
    html.setAttribute('data-animation-level', level.toString());
    localStorage.setItem('pycalendar-animation-level', level.toString());
}

function loadSavedTheme() {
    const savedTheme = localStorage.getItem(THEME_STORAGE_KEY) || 'light';
    setTheme(savedTheme);
    const activeBtn = document.querySelector(`.theme-btn[data-theme="${savedTheme}"]`);
    if (activeBtn) {
        document.querySelectorAll('.theme-btn').forEach(btn => btn.classList.remove('active'));
        activeBtn.classList.add('active');
    }
}

function setTheme(theme) {
    const targetTheme = theme || 'light';
    const state = applyThemeAttributes(targetTheme);
    localStorage.setItem(THEME_STORAGE_KEY, targetTheme);
    console.info('[Theme] Applied', targetTheme, state);
    logThemeDiagnostics('theme-change');
    if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('pycalendar:theme-change', { detail: { theme: targetTheme } }));
    }
}

function applyThemeAttributes(theme) {
    const targets = [document.documentElement, document.body].filter(Boolean);
    targets.forEach(el => el.setAttribute('data-theme', theme));
    return {
        html: document.documentElement?.getAttribute('data-theme'),
        body: document.body?.getAttribute('data-theme') || null
    };
}

const PyCalendarUI = {
    logThemeDiagnostics,
    setupEventListeners,
    setupSidebarControls,
    setupSidebarResize,
    setupThemeControls,
    setupPaletteControls,
    setupAnimationControls,
    loadSavedTheme,
    loadSavedPalette,
    setTheme,
    setPalette,
};

if (typeof window !== 'undefined') {
    window.PyCalendarUI = PyCalendarUI;
    window.logThemeDiagnostics = logThemeDiagnostics;
}
