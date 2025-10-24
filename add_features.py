#!/usr/bin/env python3
"""
Ajoute les nouvelles fonctionnalités au calendrier existant:
- Détection de conflits (bordures rouges)
- Auto-résolution (suggestions intelligentes)  
- Historique (undo/redo)
"""

from pathlib import Path

def load_file(filepath):
    """Charge le contenu d'un fichier"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def add_new_features():
    """Ajoute les nouvelles fonctionnalités au calendrier"""
    
    # Chemins
    base_html = Path('data_volley/calendrier_volley.html')
    output_html = Path('data_volley/calendrier_volley_enhanced.html')
    components_dir = Path('visualization/components')
    
    # Charger le HTML existant
    print('📂 Chargement du calendrier existant...')
    html_content = load_file(base_html)
    
    # Charger les nouveaux composants JS
    print('📦 Chargement des nouveaux composants...')
    conflict_detector_js = load_file(components_dir / 'conflict-detector.js')
    auto_resolver_js = load_file(components_dir / 'auto-resolver.js')
    history_manager_js = load_file(components_dir / 'history-manager.js')
    panels_ui_js = load_file(components_dir / 'panels-ui.js')
    
    # Trouver la position d'insertion (juste avant la classe PyCalendarApp)
    insert_marker = '// ==================== INITIALISATION ===================='
    
    if insert_marker not in html_content:
        print('❌ Marqueur d\'insertion non trouvé')
        return False
    
    # Créer le bloc de nouveaux scripts
    new_scripts = f'''
    <script>
// ==================== CONFLICT DETECTOR ====================
{conflict_detector_js}
    </script>
    
    <script>
// ==================== AUTO-RESOLVER ====================
{auto_resolver_js}
    </script>
    
    <script>
// ==================== HISTORY MANAGER ====================
{history_manager_js}
    </script>
    
    <script>
// ==================== PANELS UI ====================
{panels_ui_js}
    </script>
    
    <script>
    '''
    
    # Insérer les nouveaux scripts
    html_content = html_content.replace(
        f'    <script>\n    {insert_marker}',
        new_scripts + insert_marker
    )
    
    # Ajouter les boutons toggle des panels (avant </div> de fermeture de app-container)
    panel_buttons = '''
        
        <!-- ==================== PANEL TOGGLES ==================== -->
        <button class="panel-toggle history" onclick="window.historyPanel?.toggle()">
            📜 Historique
        </button>
        <button class="panel-toggle conflicts" onclick="window.conflictPanel?.toggle()">
            ⚠️ Conflits <span class="badge" id="conflictBadge">0</span>
        </button>
        <button class="panel-toggle resolver" onclick="window.resolverPanel?.toggle()">
            🤖 Auto-Résolution
        </button>
    </div>'''
    
    # Remplacer la fermeture de app-container
    html_content = html_content.replace('    </div>\n    \n    <!-- ==================== EDIT CONTROLS', panel_buttons + '\n    \n    <!-- ==================== EDIT CONTROLS')
    
    # Modifier la classe PyCalendarApp pour initialiser les nouveaux systèmes
    
    # 1. Ajouter les managers dans le constructor
    old_constructor = '''            constructor() {
                this.filterManager = new FilterManager();
                this.calendarGridView = new CalendarGridView();
                this.currentTab = 'grid';
            }'''
    
    new_constructor = '''            constructor() {
                this.filterManager = new FilterManager();
                this.calendarGridView = new CalendarGridView();
                this.currentTab = 'grid';
                
                // Initialize new systems
                this.conflictDetector = new ConflictDetector();
                this.autoResolver = new AutoResolver(this.conflictDetector);
                this.historyManager = new HistoryManager();
            }'''
    
    html_content = html_content.replace(old_constructor, new_constructor)
    
    # 2. Ajouter initializePanels() après init()
    init_panels_method = '''
            
            initializePanels() {
                // Create UI panels
                window.conflictPanel = new ConflictPanel(this.conflictDetector);
                window.historyPanel = new HistoryPanel(this.historyManager);
                window.resolverPanel = new ResolverPanel(this.autoResolver);
                
                // Expose managers globally
                window.conflictDetector = this.conflictDetector;
                window.autoResolver = this.autoResolver;
                window.historyManager = this.historyManager;
                
                // Initial conflict detection
                this.updateConflicts();
                
                console.log('✅ Panels initialized');
            }
            
            setupDragAndDropHistory() {
                // Override the saveModification function to track history
                if (window.editModal) {
                    const originalSaveModification = window.editModal.saveModification.bind(window.editModal);
                    
                    window.editModal.saveModification = (modification) => {
                        // Save modification as usual
                        originalSaveModification(modification);
                        
                        // Track in history
                        window.historyManager.pushAction({
                            type: 'move',
                            description: `Déplacé match vers ${modification.new.venue} à ${modification.new.time}`,
                            data: {
                                matchId: modification.match_id,
                                from: modification.original,
                                to: modification.new
                            }
                        });
                        
                        // Update conflicts after modification
                        setTimeout(() => this.updateConflicts(), 300);
                    };
                }
            }
            
            updateConflicts() {
                if (!window.conflictPanel) return;
                
                // Detect conflicts
                window.conflictPanel.update(matchsData);
                
                // Add badges to match cards
                window.conflictPanel.addConflictBadges(matchsData);
                
                // Update conflict count badge
                const stats = this.conflictDetector.getConflictStats();
                const badge = document.getElementById('conflictBadge');
                if (badge) {
                    badge.textContent = stats.critical;
                    badge.style.display = stats.critical > 0 ? 'inline-block' : 'none';
                }
                
                // Update resolver suggestions
                if (window.resolverPanel) {
                    window.resolverPanel.update(matchsData, availableSlotsData);
                }
            }'''
    
    # Trouver où insérer (après la méthode reloadAndRender)
    reload_method_end = '''                // Re-render current view
                this.render(this.filterManager.filters, this.filterManager.preferences);
            }'''
    
    html_content = html_content.replace(
        reload_method_end,
        reload_method_end + init_panels_method
    )
    
    # 3. Appeler initializePanels() et setupDragAndDropHistory() dans init()
    old_init_end = '''                // Initial render
                this.render(this.filterManager.filters, this.filterManager.preferences);
                
                console.log('✅ Initialisation terminée');
            }'''
    
    new_init_end = '''                // Initial render
                this.render(this.filterManager.filters, this.filterManager.preferences);
                
                // Initialize UI panels
                this.initializePanels();
                
                // Setup drag-and-drop history tracking
                this.setupDragAndDropHistory();
                
                console.log('✅ Initialisation terminée');
            }'''
    
    html_content = html_content.replace(old_init_end, new_init_end)
    
    # 4. Mettre à jour reloadAndRender pour détecter les conflits
    old_reload_end = '''                // Re-render current view
                this.render(this.filterManager.filters, this.filterManager.preferences);
            }'''
    
    new_reload_end = '''                // Re-render current view
                this.render(this.filterManager.filters, this.filterManager.preferences);
                
                // Update conflicts after reload
                setTimeout(() => this.updateConflicts(), 200);
            }'''
    
    # Cette modification cible spécifiquement reloadAndRender
    # Chercher le contexte unique de reloadAndRender
    reload_context = '''                }
                
                // Re-render current view
                this.render(this.filterManager.filters, this.filterManager.preferences);
            }
            
            init() {'''
    
    new_reload_context = '''                }
                
                // Re-render current view
                this.render(this.filterManager.filters, this.filterManager.preferences);
                
                // Update conflicts after reload
                setTimeout(() => this.updateConflicts(), 200);
            }
            
            init() {'''
    
    html_content = html_content.replace(reload_context, new_reload_context)
    
    # Sauvegarder
    print(f'💾 Sauvegarde dans {output_html}...')
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print()
    print('=' * 60)
    print('✅ ✅ ✅ CALENDRIER AMÉLIORÉ CRÉÉ ✅ ✅ ✅')
    print('=' * 60)
    print()
    print(f'📁 Fichier: {output_html}')
    print()
    print('🎉 Nouvelles fonctionnalités ajoutées:')
    print('   ⚠️  Détection de conflits avec bordures rouges')
    print('   🤖 Suggestions intelligentes d\'auto-résolution')
    print('   📜 Historique avec undo/redo (Ctrl+Z / Ctrl+Shift+Z)')
    print()
    print('🚀 Ouvrez le calendrier dans votre navigateur:')
    print(f'   http://localhost:8894/{output_html.name}')
    print()
    
    return True

if __name__ == '__main__':
    add_new_features()
