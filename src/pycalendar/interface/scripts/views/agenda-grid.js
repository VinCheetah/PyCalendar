/**
 * AgendaGridView - Vue agenda avec axe temporel vertical et colonnes par gymnase
 * 
 * Architecture:
 * - Axe vertical: Horaires de 14h à 23h
 * - Colonnes horizontales: Une par gymnase (mode week) ou par journée (mode venue)
 * - Matchs positionnés absolument selon leur horaire
 * - Matchs simultanés placés côte à côte
 */
class AgendaGridView {
    // ═══════════════════════════════════════════════════════════════
    // CONSTANTES DE CONFIGURATION
    // ═══════════════════════════════════════════════════════════════
    static MIN_HOUR = 14;           // Heure de début de l'affichage
    static MAX_HOUR = 23;           // Heure de fin de l'affichage
    static PIXELS_PER_HOUR = 120;   // Hauteur en pixels pour 1 heure
    static MATCH_DURATION_HOURS = 2; // Durée d'affichage d'un match
    static TIME_COLUMN_WIDTH = 85;  // Largeur de la colonne des horaires
    static COLUMN_MIN_WIDTH = 200;  // Largeur minimale d'une colonne
    static COLUMN_MARGIN = 4;       // Marge entre les colonnes
    
    constructor(dataManager, container) {
        this.dataManager = dataManager;
        this.container = container;
        
        // Renderer pour les cartes de matchs
        this.cardRenderer = new MatchCardRenderer(dataManager);
        
        // Drag & drop
        this.dragDropManager = new DragDropManager(
            dataManager,
            window.modificationManager
        );
        this.dragDropManager.onModification = () => this.render();
        
        // Filtres actifs
        this.filters = {
            institution: '',
            pool: '',
            venue: '',
            team: '',
            gender: ''
        };
        
        // Mode d'affichage : 'week' (par journée) ou 'venue' (par gymnase)
        this.displayMode = 'week'; // Par défaut : navigation par journée
        
        // Mode de coloration des matchs
        this.colorCodingMode = 'none'; // Par défaut : pas de coloration
        
        // Affichage des créneaux libres
        this.showEmptySlots = false; // Par défaut : masqués
        
        // Navigation par journée (mode 'week')
        this.currentWeekIndex = 0;
        this.weeks = []; // Liste des journées disponibles
        
        // Navigation par gymnase (mode 'venue')
        this.currentVenueIndex = 0;
        this.venues = []; // Liste des gymnases disponibles
        
        // Date de début du championnat (J1 = jeudi 16 octobre 2025)
        this.championshipStartDate = new Date(2025, 9, 16); // Mois 9 = octobre (0-indexed)
        
        // Stockage des event listeners pour nettoyage
        this._eventListeners = [];
    }
    
    /**
     * Calcule la date du jeudi pour une journée donnée
     * @param {number} weekNumber - Numéro de la journée (J1, J2, etc.)
     * @returns {{date: Date, label: string}} - Date du jeudi et label formaté
     */
    getWeekDates(weekNumber) {
        // Calculer le jeudi de cette journée
        const matchDate = new Date(this.championshipStartDate);
        matchDate.setDate(matchDate.getDate() + (weekNumber - 1) * 7);
        
        return {
            date: matchDate,
            label: this.formatDate(matchDate)
        };
    }
    
    /**
     * Formate une date de manière concise
     * @param {Date} date - Date à formater
     * @returns {string} - Format "16 oct." ou "3 déc."
     */
    formatDate(date) {
        const months = ['janv.', 'févr.', 'mars', 'avr.', 'mai', 'juin',
                       'juil.', 'août', 'sept.', 'oct.', 'nov.', 'déc.'];
        
        const day = date.getDate();
        const month = months[date.getMonth()];
        
        return `${day} ${month}`;
    }
    
    /**
     * Retourne la configuration des options d'affichage pour le panneau latéral
     * @returns {Object} Configuration pour ViewOptionsManager
     */
    getDisplayOptions() {
        return {
            title: "Options d'affichage",
            options: [
                {
                    type: 'button-group',
                    id: 'agenda-navigation-mode',
                    label: 'Navigation par',
                    values: [
                        { value: 'week', text: '📅 Journée' },
                        { value: 'venue', text: '🏛️ Gymnase' }
                    ],
                    default: this.displayMode,
                    action: (value) => {
                        this.setDisplayMode(value);
                    }
                },
                {
                    type: 'button-group',
                    id: 'agenda-color-coding',
                    label: 'Coloration des matchs',
                    values: [
                        { value: 'none', text: '🎨 Aucune' },
                        { value: 'genre', text: '👥 Genre' },
                        { value: 'niveau', text: '🎯 Niveau (A1-A4)' },
                        { value: 'penalite', text: '⚠️ Pénalités' },
                        { value: 'statut', text: '✅ Statut' }
                    ],
                    default: this.colorCodingMode || 'none',
                    action: (value) => {
                        this.setColorCoding(value);
                    }
                },
                {
                    type: 'checkbox',
                    id: 'agenda-show-empty-slots',
                    label: 'Créneaux libres',
                    description: 'Afficher les créneaux horaires disponibles',
                    default: this.showEmptySlots,
                    action: (value) => {
                        this.setShowAvailableSlots(value);
                    }
                }
            ]
        };
    }
    
    /**
     * Change le mode de coloration des matchs
     * @param {string} mode - 'none', 'genre', 'niveau', 'penalite', ou 'statut'
     */
    setColorCoding(mode) {
        const validModes = ['none', 'genre', 'niveau', 'penalite', 'statut'];
        if (!validModes.includes(mode)) {
            console.warn(`Mode de coloration invalide: ${mode}`);
            return;
        }
        
        this.colorCodingMode = mode;
        
        // Appliquer les classes de coloration sur le container
        const container = document.querySelector('.agenda-view-container');
        if (container) {
            // Retirer toutes les classes de coloration
            container.classList.remove('color-none', 'color-genre', 'color-niveau', 'color-penalite', 'color-statut');
            // Ajouter la nouvelle classe
            container.classList.add(`color-${mode}`);
        }
        
        // Re-rendre la vue pour appliquer les changements
        this.render();
        
        // FORCER l'application des couleurs via JavaScript (fallback si CSS ne fonctionne pas)
        setTimeout(() => this.applyColorCoding(), 50);
    }
    
    /**
     * Applique les couleurs directement via JavaScript (fallback)
     */
    applyColorCoding() {
        if (!this.colorCodingMode || this.colorCodingMode === 'none') return;
        
        const cards = document.querySelectorAll('.match-card');
        
        cards.forEach(card => {
            let background = null;
            
            if (this.colorCodingMode === 'genre') {
                if (card.classList.contains('male') || card.classList.contains('match-male')) {
                    // Bleu dynamique avec reflets clairs
                    background = 'linear-gradient(135deg, #60a5fa 0%, #3b82f6 50%, #2563eb 100%)';
                } else if (card.classList.contains('female') || card.classList.contains('match-female')) {
                    // Rose vibrant avec reflets
                    background = 'linear-gradient(135deg, #f472b6 0%, #ec4899 50%, #db2777 100%)';
                } else if (card.classList.contains('mixed')) {
                    // Violet énergique
                    background = 'linear-gradient(135deg, #a78bfa 0%, #8b5cf6 50%, #7c3aed 100%)';
                }
            } else if (this.colorCodingMode === 'niveau') {
                const category = card.getAttribute('data-category');
                const categoryLower = category ? category.toLowerCase() : '';
                if (categoryLower === 'a1') {
                    // Violet royal premium (A1 = élite)
                    background = 'linear-gradient(135deg, #a855f7 0%, #9333ea 40%, #7c3aed 100%)';
                } else if (categoryLower === 'a2') {
                    // Bleu indigo profond
                    background = 'linear-gradient(135deg, #6366f1 0%, #4f46e5 50%, #4338ca 100%)';
                } else if (categoryLower === 'a3') {
                    // Bleu ciel dynamique
                    background = 'linear-gradient(135deg, #38bdf8 0%, #0ea5e9 50%, #0284c7 100%)';
                } else if (categoryLower === 'a4') {
                    // Teal aqua frais
                    background = 'linear-gradient(135deg, #2dd4bf 0%, #14b8a6 50%, #0d9488 100%)';
                }
            } else if (this.colorCodingMode === 'penalite') {
                const penalties = parseInt(card.getAttribute('data-penalties') || '0');
                if (penalties === 0) {
                    // Vert émeraude positif
                    background = 'linear-gradient(135deg, #34d399 0%, #10b981 50%, #059669 100%)';
                } else if (penalties <= 5) {
                    // Orange ambre attention
                    background = 'linear-gradient(135deg, #fbbf24 0%, #f59e0b 50%, #d97706 100%)';
                } else {
                    // Rouge corail alerte
                    background = 'linear-gradient(135deg, #f87171 0%, #ef4444 50%, #dc2626 100%)';
                }
            } else if (this.colorCodingMode === 'statut') {
                if (card.classList.contains('match-fixed')) {
                    // Violet améthyste (fixé)
                    background = 'linear-gradient(135deg, #a78bfa 0%, #8b5cf6 50%, #7c3aed 100%)';
                } else if (card.classList.contains('match-conflict-critical')) {
                    // Rouge rubis critique
                    background = 'linear-gradient(135deg, #f87171 0%, #ef4444 50%, #dc2626 100%)';
                } else if (card.classList.contains('match-conflict-warning')) {
                    // Orange topaze warning
                    background = 'linear-gradient(135deg, #fbbf24 0%, #f59e0b 50%, #d97706 100%)';
                } else {
                    // Bleu saphir flexible
                    background = 'linear-gradient(135deg, #60a5fa 0%, #3b82f6 50%, #2563eb 100%)';
                }
            }
            
            if (background) {
                card.style.background = background;
                card.style.color = 'white';
            }
        });
    }
    
    /**
     * Change le mode d'affichage
     * @param {string} mode - 'week' pour navigation par journée, 'venue' pour navigation par gymnase
     */
    setDisplayMode(mode) {
        if (mode !== 'week' && mode !== 'venue') {
            console.warn(`Mode d'affichage invalide: ${mode}`);
            return;
        }
        
        this.displayMode = mode;
        
        // Réinitialiser l'index de navigation
        if (mode === 'week') {
            this.currentWeekIndex = 0;
        } else {
            this.currentVenueIndex = 0;
        }
        
        // Re-rendre la vue
        this.render();
    }
    
    /**
     * Active/désactive l'affichage des créneaux libres
     * @param {boolean} show - true pour afficher, false pour masquer
     */
    setShowAvailableSlots(show) {
        this.showEmptySlots = show;
        console.log(`🔄 Créneaux libres: ${show ? 'AFFICHÉS' : 'MASQUÉS'}`);
        this.render();
    }
    
    /**
     * Alias pour compatibilité
     */
    toggleEmptySlots(show) {
        this.setShowAvailableSlots(show);
    }
    
    /**
     * Initialise la vue
     */
    init() {
        this.render();
    }
    
    /**
     * Filtre les matchs selon les critères actifs
     */
    filterMatches(matches) {
        let filtered = [...matches];
        
        if (this.filters.gender) {
            filtered = filtered.filter(m => {
                const genre = m.equipe1_genre || m.equipe2_genre;
                return genre === this.filters.gender;
            });
        }
        
        if (this.filters.institution) {
            filtered = filtered.filter(m => 
                m.equipe1_institution === this.filters.institution || 
                m.equipe2_institution === this.filters.institution
            );
        }
        
        if (this.filters.pool) {
            filtered = filtered.filter(m => m.poule === this.filters.pool);
        }
        
        if (this.filters.venue) {
            filtered = filtered.filter(m => m.gymnase === this.filters.venue);
        }
        
        // Filtre par équipe - support des IDs multiples (groupe M+F)
        if (this.filters.equipe) {
            const equipeIds = this.filters.equipe.split(',');
            filtered = filtered.filter(m => {
                const equipe1Id = m.equipe1_id || m.equipes?.[0];
                const equipe2Id = m.equipe2_id || m.equipes?.[1];
                return equipeIds.includes(equipe1Id) || equipeIds.includes(equipe2Id);
            });
        }
        
        // Filtre par équipe (recherche texte - ancienne méthode)
        if (this.filters.team) {
            filtered = filtered.filter(m =>
                m.equipe1_nom.toLowerCase().includes(this.filters.team.toLowerCase()) ||
                m.equipe2_nom.toLowerCase().includes(this.filters.team.toLowerCase())
            );
        }
        
        return filtered;
    }
    
    /**
     * Organise les matchs par semaine
     */
    organizeMatchesByWeek(matches) {
        const weekMap = new Map();
        
        matches.forEach(match => {
            // Utiliser le champ 'semaine' directement
            const weekNumber = match.semaine;
            if (!weekNumber) return;
            
            const weekKey = `W${String(weekNumber).padStart(2, '0')}`;
            
            if (!weekMap.has(weekKey)) {
                weekMap.set(weekKey, {
                    key: weekKey,
                    weekNumber: weekNumber,
                    matches: []
                });
            }
            
            weekMap.get(weekKey).matches.push(match);
        });
        
        // Convertir en tableau et trier par numéro de semaine
        const weeks = Array.from(weekMap.values()).sort((a, b) => 
            a.weekNumber - b.weekNumber
        );
        
        return weeks;
    }
    
    /**
     * Organise les matchs par gymnase
     * @param {Array} matches - Liste des matchs
     * @returns {Array} Tableau d'objets {venueId, venueName, displayName, matches[]}
     */
    organizeMatchesByVenue(matches) {
        const venueMap = new Map();
        const data = this.dataManager.getData();
        const venuesData = data?.entities?.venues || {};
        
        matches.forEach(match => {
            const venueId = match.gymnase;
            if (!venueId) return;
            
            if (!venueMap.has(venueId)) {
                // Récupérer le nom formaté depuis les données
                const venueInfo = venuesData[venueId];
                const displayName = venueInfo?.nom || venueId;
                
                venueMap.set(venueId, {
                    venueId: venueId,
                    venueName: venueId, // ID brut (pour compatibilité)
                    displayName: displayName, // Nom formaté
                    matches: []
                });
            }
            
            venueMap.get(venueId).matches.push(match);
        });
        
        // Convertir en tableau et trier par nom d'affichage
        const venues = Array.from(venueMap.values()).sort((a, b) => 
            a.displayName.localeCompare(b.displayName)
        );
        
        return venues;
    }
    
    /**
     * Calcule le numéro de semaine ISO 8601
     */
    getWeekNumber(date) {
        const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
        const dayNum = d.getUTCDay() || 7;
        d.setUTCDate(d.getUTCDate() + 4 - dayNum);
        const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
        return Math.ceil((((d - yearStart) / 86400000) + 1) / 7);
    }
    
    /**
     * Retourne le lundi de la semaine
     */
    getWeekStartDate(date) {
        const d = new Date(date);
        const day = d.getDay();
        const diff = d.getDate() - day + (day === 0 ? -6 : 1);
        return new Date(d.setDate(diff));
    }
    
    /**
     * Formate le label d'une journée avec la date
     * @param {Object} week - Objet semaine avec weekNumber et matches
     * @returns {string} - Format "J2 (23 oct.)"
     */
    formatWeekLabel(week) {
        const weekDates = this.getWeekDates(week.weekNumber);
        return `J${week.weekNumber} (${weekDates.label})`;
    }

    /**
     * Rend la vue agenda complète
     */
    render() {
        try {
            const data = this.dataManager.getData();
            
            if (!data || !data.matches) {
                console.error('❌ [AgendaGrid] Aucune donnée disponible');
                this.container.innerHTML = '<div class="empty-state">Aucune donnée disponible</div>';
                return;
            }
            
            const allMatches = data.matches.scheduled || [];
            
            const filteredMatches = this.filterMatches(allMatches);
            
            if (filteredMatches.length === 0) {
                this.container.innerHTML = '<div class="empty-state">Aucun match ne correspond aux filtres sélectionnés</div>';
                return;
            }
            
            // ═══════════════════════════════════════════════════════════════
            // DUAL MODE LOGIC: Organiser selon le mode d'affichage
            // ═══════════════════════════════════════════════════════════════
            let matchesToDisplay = [];
            
            if (this.displayMode === 'week') {
                // MODE JOURNÉE: Organiser par semaine, naviguer entre J1, J2, J4...
                this.weeks = this.organizeMatchesByWeek(filteredMatches);
                
                if (this.weeks.length === 0) {
                    this.container.innerHTML = '<div class="empty-state">Aucun match trouvé</div>';
                    return;
                }
                
                // Valider l'index de journée
                if (this.currentWeekIndex >= this.weeks.length) {
                    this.currentWeekIndex = this.weeks.length - 1;
                }
                if (this.currentWeekIndex < 0) {
                    this.currentWeekIndex = 0;
                }
                
                const currentWeek = this.weeks[this.currentWeekIndex];
                matchesToDisplay = currentWeek.matches;
                console.log('🔍 [AgendaGrid] Journée courante:', currentWeek.key, 'matchs:', matchesToDisplay.length);
                
            } else if (this.displayMode === 'venue') {
                // MODE GYMNASE: Organiser par gymnase, naviguer entre BESSON, LAENNEC...
                this.venues = this.organizeMatchesByVenue(filteredMatches);
                console.log('🔍 [AgendaGrid] Mode Gymnase - Nombre de gymnases:', this.venues.length);
                
                if (this.venues.length === 0) {
                    this.container.innerHTML = '<div class="empty-state">Aucun match trouvé</div>';
                    return;
                }
                
                // Valider l'index de gymnase
                if (this.currentVenueIndex >= this.venues.length) {
                    this.currentVenueIndex = this.venues.length - 1;
                }
                if (this.currentVenueIndex < 0) {
                    this.currentVenueIndex = 0;
                }
                
                const currentVenue = this.venues[this.currentVenueIndex];
                matchesToDisplay = currentVenue.matches;
                console.log('🔍 [AgendaGrid] Gymnase courant:', currentVenue.displayName || currentVenue.venueName, 'matchs:', matchesToDisplay.length);
            }
            
            // ═══════════════════════════════════════════════════════════════
            // GÉNÉRATION DU HTML (commun aux deux modes)
            // ═══════════════════════════════════════════════════════════════
            const html = this.generateAgendaView(matchesToDisplay, data);
            
            this.container.innerHTML = html;
            
            // Initialiser le drag & drop
            this.dragDropManager.initializeDragDrop(this.container);
            
            // Attacher les événements
            this.attachEvents();
            
            // Synchroniser le scroll horizontal des en-têtes avec les colonnes
            this.syncHeaderScroll();
            
            // Réappliquer les couleurs si un mode de coloration est actif
            if (this.colorCodingMode && this.colorCodingMode !== 'none') {
                setTimeout(() => this.applyColorCoding(), 50);
            }
            
            console.log('✅ [AgendaGrid] render() terminé avec succès');
            
        } catch (error) {
            console.error('❌ [AgendaGrid] Erreur dans render():', error);
            this.container.innerHTML = `
                <div class="error-state">
                    <h3>⚠️ Erreur d'affichage</h3>
                    <p>${error.message}</p>
                    <pre>${error.stack}</pre>
                    <button onclick="location.reload()">Recharger la page</button>
                </div>
            `;
        }
    }


    /**
     * Génère la vue agenda complète avec axe temporel et colonnes de gymnases
     */
    generateAgendaView(matches, data) {
        // Utiliser les constantes de classe
        const minHour = AgendaGridView.MIN_HOUR;
        const maxHour = AgendaGridView.MAX_HOUR;
        const pixelsPerHour = AgendaGridView.PIXELS_PER_HOUR;
        const matchDuration = AgendaGridView.MATCH_DURATION_HOURS;
        const matchDisplayHeight = AgendaGridView.MATCH_DURATION_HOURS;
        const totalHeight = (maxHour - minHour) * pixelsPerHour;
        
        // ═══════════════════════════════════════════════════════════════
        // DUAL MODE: Générer les colonnes selon le mode d'affichage
        // ═══════════════════════════════════════════════════════════════
        let columnsHTML = '';
        let venues = [];
        let containerClass = '';
        
        // Déclarer les variables qui seront utilisées pour les en-têtes
        let columnWidths;
        let venueMaxSimultaneous;
        let matchesByVenue;
        let weekMaxSimultaneous;
        let matchesByWeek;
        
        if (this.displayMode === 'week') {
            // MODE JOURNÉE: Colonnes = Gymnases
            venues = this.getVenuesWithCapacity(matches, data);
            matchesByVenue = this.groupMatchesByVenue(matches);
            
            // Calculer le nombre maximum de slots nécessaires par gymnase
            // Si showEmptySlots, inclure les créneaux disponibles dans le calcul
            if (this.showEmptySlots) {
                venueMaxSimultaneous = this.calculateMaxSlotsWithAvailable(matchesByVenue);
            } else {
                venueMaxSimultaneous = this.calculateMaxSimultaneousMatches(matchesByVenue);
            }
            
            // Utiliser les largeurs calculées directement
            const effectiveWidths = new Map();
            venues.forEach(venue => {
                effectiveWidths.set(venue.id, venueMaxSimultaneous.get(venue.id) || 1);
            });
            
            // Calculer les largeurs proportionnelles pour chaque gymnase
            columnWidths = this.calculateColumnWidths(effectiveWidths);
            
            console.log('🔍 [AgendaGrid] Mode Journée - Gymnases:', venues.length);
            
            columnsHTML = venues.map(venue => {
                const widthInfo = columnWidths.get(venue.id) || { width: this.columnMinWidth, widthPerSlot: 200 };
                return this.generateVenueColumnWithWidth(
                    venue, 
                    matchesByVenue.get(venue.id) || [], 
                    venueMaxSimultaneous.get(venue.id) || 1,
                    widthInfo.width,
                    widthInfo.widthPerSlot,
                    minHour,
                    maxHour,  // AJOUT: Passer maxHour pour les créneaux libres
                    pixelsPerHour,
                    matchDisplayHeight,
                    totalHeight,
                    this.showEmptySlots  // NOUVEAU: Passer l'option créneaux libres
                );
            }).join('');
            
            containerClass = 'venues-container';
            
        } else if (this.displayMode === 'venue') {
            // MODE GYMNASE: Colonnes = Journées
            const weeks = this.getWeeksFromMatches(matches);
            matchesByWeek = this.groupMatchesByWeek(matches);
            weekMaxSimultaneous = this.calculateMaxSimultaneousMatchesByWeek(matchesByWeek);
            
            // Calculer les largeurs proportionnelles pour chaque journée
            columnWidths = this.calculateColumnWidths(weekMaxSimultaneous);
            
            console.log('🔍 [AgendaGrid] Mode Gymnase - Journées:', weeks.length);
            
            // Récupérer l'ID du gymnase courant pour filtrer les créneaux libres
            const currentVenueId = this.venues[this.currentVenueIndex]?.venueId;
            
            columnsHTML = weeks.map(week => {
                const widthInfo = columnWidths.get(week.weekNumber) || { width: AgendaGridView.COLUMN_MIN_WIDTH, widthPerSlot: 200 };
                return this.generateWeekColumnWithWidth(
                    week,
                    matchesByWeek.get(week.weekNumber) || [],
                    weekMaxSimultaneous.get(week.weekNumber) || 1,
                    widthInfo.width,
                    widthInfo.widthPerSlot,
                    minHour,
                    maxHour,
                    pixelsPerHour,
                    matchDisplayHeight,
                    totalHeight,
                    this.showEmptySlots,  // Activer les créneaux libres si demandé
                    currentVenueId       // ID du gymnase pour filtrer les créneaux
                );
            }).join('');
            
            containerClass = 'weeks-container';
        }
        
        // ═══════════════════════════════════════════════════════════════
        // Structure HTML commune
        // ═══════════════════════════════════════════════════════════════
        
        // Conserver la classe de coloration si elle est définie
        const colorClass = this.colorCodingMode && this.colorCodingMode !== 'none' ? ` color-${this.colorCodingMode}` : '';
        
        // Générer les en-têtes de colonnes séparément
        let headersHTML = '';
        if (this.displayMode === 'week') {
            headersHTML = venues.map(venue => {
                const widthInfo = columnWidths.get(venue.id) || { width: this.columnMinWidth, widthPerSlot: 200 };
                const maxSim = venueMaxSimultaneous.get(venue.id) || 1;
                return `
                    <div class="venue-header-cell" style="width: ${widthInfo.width}px; flex-shrink: 0; padding: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; display: flex; flex-direction: column; border-radius: 8px 8px 0 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-right: 4px;">
                        <div class="venue-name" style="font-size: 1.2rem; font-weight: 800; text-transform: uppercase; letter-spacing: 1.5px; text-shadow: 0 2px 4px rgba(0,0,0,0.3); background: rgba(0, 0, 0, 0.15); padding: 0.8rem 1rem; border-bottom: 2px solid rgba(255, 255, 255, 0.15); text-align: center;">${venue.name}</div>
                        <div class="venue-info" style="display: flex; gap: 0.75rem; font-size: 0.8rem; font-weight: 600; padding: 0.6rem 1rem; justify-content: center; flex-wrap: wrap;">
                            <span class="venue-capacity" style="display: flex; align-items: center; gap: 0.3rem; background: rgba(255, 255, 255, 0.25); padding: 0.3rem 0.7rem; border-radius: 12px; font-size: 0.75rem; white-space: nowrap;">⚡ Capacité: ${venue.capacity}</span>
                            <span class="venue-matches" style="display: flex; align-items: center; gap: 0.3rem; background: rgba(255, 255, 255, 0.25); padding: 0.3rem 0.7rem; border-radius: 12px; font-size: 0.75rem; white-space: nowrap;">📊 ${(matchesByVenue.get(venue.id) || []).length} matchs</span>
                            ${maxSim > 1 ? `<span class="venue-simultaneous" style="display: flex; align-items: center; gap: 0.3rem; background: rgba(255, 215, 0, 0.4); padding: 0.3rem 0.7rem; border-radius: 12px; font-size: 0.75rem; white-space: nowrap; font-weight: 700;">🔀 Max: ${maxSim}</span>` : ''}
                        </div>
                    </div>
                `;
            }).join('');
        } else {
            // Mode venue (journées)
            const weeks = this.getWeeksFromMatches(matches);
            const matchesByWeek = this.groupMatchesByWeek(matches);
            headersHTML = weeks.map(week => {
                const widthInfo = columnWidths.get(week.weekNumber) || { width: this.columnMinWidth, widthPerSlot: 200 };
                const weekLabel = this.formatWeekLabel(week);
                const maxSim = weekMaxSimultaneous.get(week.weekNumber) || 1;
                return `
                    <div class="week-header-cell" style="width: ${widthInfo.width}px; flex-shrink: 0; padding: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; display: flex; flex-direction: column; border-radius: 8px 8px 0 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-right: 4px;">
                        <div class="week-name" style="font-size: 1.2rem; font-weight: 800; text-transform: uppercase; letter-spacing: 1.5px; text-shadow: 0 2px 4px rgba(0,0,0,0.3); background: rgba(0, 0, 0, 0.15); padding: 0.8rem 1rem; border-bottom: 2px solid rgba(255, 255, 255, 0.15); text-align: center;">${weekLabel}</div>
                        <div class="week-info" style="display: flex; gap: 0.75rem; font-size: 0.8rem; font-weight: 600; padding: 0.6rem 1rem; justify-content: center; flex-wrap: wrap;">
                            <span class="week-matches" style="display: flex; align-items: center; gap: 0.3rem; background: rgba(255, 255, 255, 0.25); padding: 0.3rem 0.7rem; border-radius: 12px; font-size: 0.75rem; white-space: nowrap;">📊 ${(matchesByWeek.get(week.weekNumber) || []).length} matchs</span>
                            ${maxSim > 1 ? `<span class="week-simultaneous" style="display: flex; align-items: center; gap: 0.3rem; background: rgba(255, 215, 0, 0.4); padding: 0.3rem 0.7rem; border-radius: 12px; font-size: 0.75rem; white-space: nowrap; font-weight: 700;">🔀 Max: ${maxSim}</span>` : ''}
                        </div>
                    </div>
                `;
            }).join('');
        }
        
        return `
            <div class="agenda-view-container${colorClass}">
                <!-- Barre de navigation en haut (non-scrollable) -->
                ${this.generateNavigationBar(matches, venues, data)}
                
                <!-- Rangée des en-têtes de colonnes (au-dessus de la grille) -->
                <div class="agenda-headers-row" style="display: flex; flex-direction: row; background: #fafbfc; padding: 0.5rem 0.5rem 0 0.5rem; overflow: hidden;">
                    <!-- Espace pour la colonne des horaires -->
                    <div style="width: ${AgendaGridView.TIME_COLUMN_WIDTH}px; flex-shrink: 0; margin-right: ${AgendaGridView.COLUMN_MARGIN}px;"></div>
                    <!-- Container scrollable pour les en-têtes -->
                    <div class="agenda-headers-scroll" style="overflow-x: auto; overflow-y: hidden; flex: 1;">
                        <style>
                            .agenda-headers-scroll::-webkit-scrollbar {
                                display: none;
                            }
                            .agenda-headers-scroll {
                                -ms-overflow-style: none;
                                scrollbar-width: none;
                            }
                        </style>
                        <div style="display: flex; flex-direction: row; flex-wrap: nowrap; gap: 0;">
                            ${headersHTML}
                        </div>
                    </div>
                </div>
                
                <!-- Zone de contenu (scrollable verticalement uniquement) -->
                <div class="agenda-scroll-wrapper">
                    <div class="agenda-grid-container" style="display:flex; flex-direction:row; background:#fafbfc; padding:0.5rem;">
                        <!-- Colonne des horaires (fixée à gauche) -->
                        <div class="time-column-fixed" style="width: ${AgendaGridView.TIME_COLUMN_WIDTH}px; flex-shrink: 0; background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-right: 3px solid #667eea; box-shadow: 2px 0 8px rgba(0,0,0,0.06); margin-right: ${AgendaGridView.COLUMN_MARGIN}px; position: sticky; left: 0; z-index: 10;">
                            ${this.generateTimeScale(minHour, maxHour, pixelsPerHour, totalHeight)}
                        </div>
                        
                        <!-- Colonnes dynamiques selon le mode -->
                        <div class="${containerClass}" style="display:flex; flex-direction:row; flex-wrap:nowrap; overflow-x:auto; background:#ffffff; padding:0.25rem; gap:0;">
                            ${columnsHTML}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Récupère tous les gymnases avec leurs capacités
     */
    getVenuesWithCapacity(matches, data) {
        const venueMap = new Map();
        const venues = data.entities?.venues || {};
        
        // D'abord, ajouter tous les gymnases depuis les entités
        Object.entries(venues).forEach(([id, venueData]) => {
            venueMap.set(id, {
                id: id,
                name: venueData.nom || id,
                capacity: venueData.capacite || 1
            });
        });
        
        // Ensuite, vérifier les matchs pour s'assurer qu'on n'a pas oublié de gymnases
        matches.forEach(match => {
            const venueId = match.gymnase; // Utiliser 'gymnase' au lieu de 'gymnase_id'
            if (venueId && !venueMap.has(venueId)) {
                venueMap.set(venueId, {
                    id: venueId,
                    name: venueId,
                    capacity: 1
                });
            }
        });
        
        return Array.from(venueMap.values()).sort((a, b) => a.name.localeCompare(b.name));
    }

    /**
     * Groupe les matchs par gymnase
     */
    groupMatchesByVenue(matches) {
        const grouped = new Map();
        
        matches.forEach(match => {
            const venueId = match.gymnase; // Utiliser 'gymnase' au lieu de 'gymnase_id'
            if (!venueId) return;
            
            if (!grouped.has(venueId)) {
                grouped.set(venueId, []);
            }
            grouped.get(venueId).push(match);
        });
        
        return grouped;
    }

    /**
     * Calcule le nombre maximum de colonnes nécessaires pour chaque groupe
     * en utilisant l'algorithme de slot assignment pour gérer tous les chevauchements.
     * 
     * Contrairement à l'ancien calculateMaxSimultaneous (sweep line), cette méthode calcule
     * le nombre MINIMUM de colonnes nécessaires pour afficher tous les matchs sans
     * chevauchement visuel, même pour des chevauchements partiels.
     * 
     * Exemple :
     * - Match A : 14h-16h
     * - Match B : 15h-17h  
     * - Match C : 16h-18h
     * → Nécessite 3 colonnes (A, B, C ne peuvent pas partager la même position)
     * 
     * @param {Map} matchesByGroup - Map(groupId -> matches[])
     * @returns {Map} Map(groupId -> nombre de colonnes nécessaires)
     */
    calculateMaxSimultaneous(matchesByGroup) {
        const maxColumns = new Map();
        
        matchesByGroup.forEach((matches, groupId) => {
            if (matches.length === 0) {
                maxColumns.set(groupId, 0);
                return;
            }
            
            // Utiliser la logique d'assignMatchSlots pour calculer les slots
            const slots = this.assignMatchSlots(matches);
            
            // Le nombre de colonnes nécessaires = max(slot) + 1
            let maxSlot = 0;
            slots.forEach(slot => {
                maxSlot = Math.max(maxSlot, slot);
            });
            
            const columnsNeeded = maxSlot + 1;
            maxColumns.set(groupId, columnsNeeded);
            
            console.log(`📊 [calculateMaxSimultaneous] Groupe ${groupId}: ${matches.length} matchs, ${columnsNeeded} colonnes nécessaires`);
        });
        
        return maxColumns;
    }

    /**
     * Calcule le nombre maximum de matchs simultanés dans chaque gymnase
     * @deprecated Utiliser calculateMaxSimultaneous à la place
     */
    calculateMaxSimultaneousMatches(matchesByVenue) {
        return this.calculateMaxSimultaneous(matchesByVenue);
    }

    /**
     * Calcule le nombre maximum de matchs simultanés dans chaque journée
     * @deprecated Utiliser calculateMaxSimultaneous à la place
     */
    calculateMaxSimultaneousMatchesByWeek(matchesByWeek) {
        return this.calculateMaxSimultaneous(matchesByWeek);
    }

    /**
     * Calcule le nombre maximum de slots nécessaires (matchs + créneaux libres) par gymnase
     * Prend en compte à la fois les matchs planifiés ET les créneaux disponibles
     */
    calculateMaxSlotsWithAvailable(matchesByVenue) {
        const maxSlots = new Map();
        const data = this.dataManager?.getData();
        
        if (!data || !data.slots || !data.slots.available) {
            // Pas de données de slots, revenir au calcul basique
            return this.calculateMaxSimultaneousMatches(matchesByVenue);
        }
        
        matchesByVenue.forEach((matches, venueId) => {
            let max = 1;
            
            // Filtrer les slots disponibles pour ce gymnase et la semaine courante
            const currentWeek = this.displayMode === 'week' && this.weeks && this.weeks[this.currentWeekIndex] 
                ? this.weeks[this.currentWeekIndex].weekNumber 
                : null;
            
            const venueSlots = data.slots.available.filter(slot => {
                if (slot.gymnase !== venueId) return false;
                if (currentWeek !== null && slot.semaine !== currentWeek) return false;
                return true;
            });
            
            // Grouper les slots par horaire
            const slotsByTime = {};
            venueSlots.forEach(slot => {
                const time = this.parseTime(slot.horaire);
                if (!time) return;
                if (!slotsByTime[time]) slotsByTime[time] = [];
                slotsByTime[time].push(slot);
            });
            
            // Pour chaque créneau horaire, calculer matchs + slots disponibles
            const allTimes = new Set();
            
            // Ajouter les horaires des matchs
            matches.forEach(match => {
                const time = this.parseTime(match.horaire);
                if (time) allTimes.add(time);
            });
            
            // Ajouter les horaires des slots
            Object.keys(slotsByTime).forEach(time => {
                allTimes.add(parseFloat(time));
            });
            
            // Pour chaque horaire, compter matchs + slots
            allTimes.forEach(time => {
                const slotStart = time;
                const slotEnd = time + 2;
                
                // Compter les matchs qui se chevauchent
                const overlappingMatches = matches.filter(match => {
                    const matchTime = this.parseTime(match.horaire);
                    if (!matchTime) return false;
                    const matchEnd = matchTime + 2;
                    return !(matchEnd <= slotStart || matchTime >= slotEnd);
                });
                
                // Ajouter le nombre de slots disponibles à cette heure
                const availableSlots = slotsByTime[time] ? slotsByTime[time].length : 0;
                
                const total = overlappingMatches.length + availableSlots;
                max = Math.max(max, total);
            });
            
            maxSlots.set(venueId, max);
        });
        
        return maxSlots;
    }

    /**
     * Parse une heure au format "HH:MM" en nombre décimal
     */
    parseTime(timeStr) {
        if (!timeStr) return null;
        const [hours, minutes] = timeStr.split(':').map(Number);
        if (isNaN(hours) || isNaN(minutes)) return null;
        return hours + minutes / 60;
    }

    /**
     * Calcule les largeurs de colonnes de manière proportionnelle
     * 
     * @param {Map} maxSimultaneousMap - Map(id -> nombre max de matchs simultanés)
     * @returns {Map} Map(id -> {width: number, widthPerSlot: number})
     */
    calculateColumnWidths(maxSimultaneousMap) {
        const minColumnWidth = AgendaGridView.COLUMN_MIN_WIDTH;
        const padding = 8; // Réduit de 16 à 8 pour moins d'espace blanc
        const widths = new Map();
        
        // Pour chaque colonne, calculer la largeur par slot en fonction du nombre de matchs simultanés
        maxSimultaneousMap.forEach((maxSimultaneous, id) => {
            let widthPerSlot;
            
            // Adapter la largeur par slot selon le nombre de matchs simultanés
            // Plus il y a de matchs simultanés, plus on réduit la largeur par slot
            if (maxSimultaneous <= 1) {
                widthPerSlot = 250; // Largeur généreuse pour 1 seul match
            } else if (maxSimultaneous <= 3) {
                widthPerSlot = 230; // Largeur confortable
            } else if (maxSimultaneous <= 6) {
                widthPerSlot = 200; // Largeur normale
            } else if (maxSimultaneous <= 10) {
                widthPerSlot = 170; // Réduction légère
            } else if (maxSimultaneous <= 15) {
                widthPerSlot = 150; // Réduction moyenne
            } else {
                widthPerSlot = 130; // Réduction importante
            }
            
            // Calculer la largeur totale de la colonne
            let columnWidth = (maxSimultaneous * widthPerSlot) + padding;
            
            // Appliquer le minimum
            columnWidth = Math.max(columnWidth, minColumnWidth);
            
            widths.set(id, {
                width: columnWidth,
                widthPerSlot: widthPerSlot
            });
            
            console.log(`📏 [Column ${id}] maxSimultaneous: ${maxSimultaneous}, widthPerSlot: ${widthPerSlot}px, columnWidth: ${columnWidth}px`);
        });
        
        return widths;
    }

    /**
     * ═══════════════════════════════════════════════════════════════
     * MÉTHODES POUR MODE GYMNASE (colonnes = journées)
     * ═══════════════════════════════════════════════════════════════
     */

    /**
     * Récupère toutes les journées présentes dans les matchs
     */
    getWeeksFromMatches(matches) {
        const weekSet = new Set();
        matches.forEach(match => {
            if (match.semaine) {
                weekSet.add(match.semaine);
            }
        });
        
        const weeks = Array.from(weekSet).sort((a, b) => a - b).map(weekNum => ({
            weekNumber: weekNum,
            label: this.formatWeekLabel({ weekNumber: weekNum })
        }));
        
        return weeks;
    }

    /**
     * Groupe les matchs par journée (semaine)
     */
    groupMatchesByWeek(matches) {
        const grouped = new Map();
        
        matches.forEach(match => {
            const weekNum = match.semaine;
            if (!weekNum) return;
            
            if (!grouped.has(weekNum)) {
                grouped.set(weekNum, []);
            }
            grouped.get(weekNum).push(match);
        });
        
        return grouped;
    }

    /**
     * Génère une colonne pour une journée (mode gymnase)
     * @deprecated Cette méthode n'est plus utilisée, utiliser generateWeekColumnWithWidth
     */
    generateWeekColumn(week, matches, maxSimultaneous, minHour, pixelsPerHour, matchDuration, totalHeight) {
        // Largeur adaptative basée sur le nombre max de matchs simultanés
        let widthPerSlot;
        if (maxSimultaneous <= 3) {
            widthPerSlot = 230;
        } else if (maxSimultaneous <= 6) {
            widthPerSlot = 200;
        } else if (maxSimultaneous <= 10) {
            widthPerSlot = 170;
        } else if (maxSimultaneous <= 15) {
            widthPerSlot = 150;
        } else {
            widthPerSlot = 130;
        }
        
        const padding = 4;
        const columnWidth = Math.max(AgendaGridView.COLUMN_MIN_WIDTH, (maxSimultaneous * widthPerSlot) + padding);
        const weekDates = this.getWeekDates(week.weekNumber);
        
        console.log(`🔍 [Week ${week.weekNumber}] maxSimultaneous: ${maxSimultaneous}, widthPerSlot: ${widthPerSlot}px, columnWidth: ${columnWidth}px`);
        
        return `
            <div class="week-column" 
                 data-week="${week.weekNumber}"
                 data-max-simultaneous="${maxSimultaneous}"
                 style="width: ${columnWidth}px; flex-shrink: 0; margin-right: ${AgendaGridView.COLUMN_MARGIN}px;">
                <!-- En-tête de la journée -->
                <div class="column-header week-header">
                    <div class="column-title">${week.label}</div>
                    <div class="column-subtitle">${weekDates.label}</div>
                    <div class="column-stats">
                        <span>📊 ${matches.length} match${matches.length > 1 ? 's' : ''}</span>
                        ${maxSimultaneous > 1 ? `<span>🔀 Max: ${maxSimultaneous}</span>` : ''}
                    </div>
                </div>
                
                <!-- Corps avec les matchs -->
                <div class="column-body" style="height: ${totalHeight}px; position: relative;">
                    ${this.generateWeekMatches(matches, minHour, pixelsPerHour, matchDuration, maxSimultaneous, widthPerSlot)}
                </div>
            </div>
        `;
    }

    /**
     * Génère une colonne pour une journée avec largeur personnalisée (mode gymnase)
     */
    generateWeekColumnWithWidth(week, matches, maxSimultaneous, columnWidth, widthPerSlot, minHour, maxHour, pixelsPerHour, matchDuration, totalHeight, showEmptySlots = false, venueId = null) {
        const weekDates = this.getWeekDates(week.weekNumber);
        
        console.log(`🔍 [Week ${week.weekNumber}] maxSimultaneous: ${maxSimultaneous}, widthPerSlot: ${widthPerSlot}px, columnWidth: ${columnWidth}px, showEmptySlots: ${showEmptySlots}`);
        
        // Générer les créneaux libres si demandé (en mode venue avec venueId fourni)
        let emptySlotsHTML = '';
        if (showEmptySlots && venueId) {
            emptySlotsHTML = this.generateEmptySlotsForWeek(matches, venueId, week.weekNumber, minHour, maxHour, pixelsPerHour, widthPerSlot);
        }
        
        return `
            <div class="week-column" 
                 data-week="${week.weekNumber}"
                 data-max-simultaneous="${maxSimultaneous}"
                 style="width: ${columnWidth}px; flex-shrink: 0; background: linear-gradient(180deg, #ffffff 0%, #f8f9fa 100%); border-right: 2px solid #e9ecef; margin-right: ${AgendaGridView.COLUMN_MARGIN}px; border-radius: 0 0 8px 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
                
                <!-- Corps avec les matchs et créneaux libres (sans en-tête) -->
                <div class="week-body" style="height: ${totalHeight}px; position: relative; background-image: repeating-linear-gradient(to bottom, transparent 0, transparent 119px, rgba(102, 126, 234, 0.08) 119px, rgba(102, 126, 234, 0.08) 120px);">
                    ${emptySlotsHTML}
                    ${this.generateWeekMatches(matches, minHour, pixelsPerHour, matchDuration, maxSimultaneous, widthPerSlot)}
                </div>
            </div>
        `;
    }

    /**
     * Génère les matchs d'une journée avec positionnement absolu
     */
    generateWeekMatches(matches, minHour, pixelsPerHour, matchDuration, maxSimultaneous, widthPerSlot) {
        if (!matches || matches.length === 0) return '';
        
        // Trier les matchs par horaire
        const sortedMatches = matches.slice().sort((a, b) => {
            const timeA = this.parseTime(a.horaire) || 0;
            const timeB = this.parseTime(b.horaire) || 0;
            return timeA - timeB;
        });
        
        // Assigner un slot horizontal à chaque match
        const matchSlots = this.assignMatchSlots(sortedMatches);
        
        let html = '';
        sortedMatches.forEach((match, index) => {
            const time = this.parseTime(match.horaire);
            if (!time) return;
            
            // Position verticale basée sur l'horaire
            const top = (time - minHour) * pixelsPerHour;
            const height = matchDuration * pixelsPerHour; // Hauteur complète sans marge
            
            // Position horizontale basée sur le slot
            const slot = matchSlots.get(match.match_id) || 0;
            const left = slot * widthPerSlot + 2;
            const width = widthPerSlot - 4;
            
            html += `
                <div class="match-wrapper" style="
                    position: absolute;
                    top: ${top}px;
                    left: ${left}px;
                    width: ${width}px;
                    height: ${height}px;
                ">
                    ${this.cardRenderer.renderMatchCard(match, false, index, true, null)}
                </div>
            `;
        });
        
        return html;
    }

    /**
     * Positionne les matchs dans une colonne (gestion des chevauchements)
     */
    /**
     * ═══════════════════════════════════════════════════════════════
     * FIN MÉTHODES MODE GYMNASE
     * ═══════════════════════════════════════════════════════════════
     */

    /**
     * ÉTAPE 1: Génère la barre de navigation en haut (non-scrollable)
     * Structure propre avec 3 sections : info gauche, navigation centrale, stats droite
     */
    generateNavigationBar(matches, venues, data) {
        const totalVenues = venues.length;
        const totalMatches = matches.length;
        
        // ═══════════════════════════════════════════════════════════════
        // DUAL MODE: Informations de navigation selon le mode
        // ═══════════════════════════════════════════════════════════════
        let navigationContent = '';
        
        if (this.displayMode === 'week') {
            // MODE JOURNÉE: Naviguer entre J1, J2, J4...
            const currentWeek = this.weeks[this.currentWeekIndex];
            const weekLabel = this.formatWeekLabel(currentWeek);
            const weekDates = this.getWeekDates(currentWeek.weekNumber);
            
            const fullDate = weekDates.date.toLocaleDateString('fr-FR', { 
                weekday: 'long', 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
            });
            
            const prevDisabled = this.currentWeekIndex === 0 ? 'disabled' : '';
            const nextDisabled = this.currentWeekIndex === this.weeks.length - 1 ? 'disabled' : '';
            const weekIndicator = `${this.currentWeekIndex + 1}/${this.weeks.length}`;
            
            const btnStyle = "padding: 0.75rem 1.25rem; background: linear-gradient(135deg, #667eea, #764ba2); color: white; border: none; border-radius: 12px; cursor: pointer; font-weight: 700; box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3); transition: all 0.2s ease;";
            const btnDisabledStyle = "padding: 0.75rem 1.25rem; background: linear-gradient(135deg, #adb5bd, #868e96); color: white; border: none; border-radius: 12px; cursor: not-allowed; font-weight: 700; box-shadow: none; opacity: 0.3;";
            
            navigationContent = `
                <button id="prev-week" class="nav-button nav-prev" ${prevDisabled} title="Journée précédente" style="${prevDisabled ? btnDisabledStyle : btnStyle}">
                    <span class="nav-button-icon" style="font-size: 1.25rem; font-weight: 900;">◀</span>
                </button>
                
                <div class="nav-current-item" style="display: flex; flex-direction: column; align-items: center; gap: 0.5rem; min-width: 350px; padding: 0.75rem 1.5rem; background: white; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08);">
                    <div class="nav-item-main" style="display: flex; align-items: center; gap: 1rem;">
                        <span class="nav-item-label" style="font-size: 1.5rem; font-weight: 900; color: #667eea; letter-spacing: 1px;">${weekLabel}</span>
                        <span class="nav-item-indicator" style="padding: 0.25rem 0.75rem; background: linear-gradient(135deg, #f8f9fa, #e9ecef); border-radius: 20px; font-size: 0.85rem; font-weight: 600; color: #495057;">${weekIndicator}</span>
                    </div>
                    <div class="nav-item-subtitle" title="${fullDate}" style="font-size: 0.9rem; color: #6c757d; font-weight: 600;">
                        ${fullDate}
                    </div>
                </div>
                
                <button id="next-week" class="nav-button nav-next" ${nextDisabled} title="Journée suivante" style="${nextDisabled ? btnDisabledStyle : btnStyle}">
                    <span class="nav-button-icon" style="font-size: 1.25rem; font-weight: 900;">▶</span>
                </button>
            `;
            
        } else if (this.displayMode === 'venue') {
            // MODE GYMNASE: Naviguer entre BESSON, LAENNEC, DESCARTES...
            const currentVenue = this.venues[this.currentVenueIndex];
            const venueName = currentVenue.displayName || currentVenue.venueName;
            
            const prevDisabled = this.currentVenueIndex === 0 ? 'disabled' : '';
            const nextDisabled = this.currentVenueIndex === this.venues.length - 1 ? 'disabled' : '';
            const venueIndicator = `${this.currentVenueIndex + 1}/${this.venues.length}`;
            
            // Compter le nombre de journées différentes dans ce gymnase
            const uniqueWeeks = new Set(currentVenue.matches.map(m => m.semaine));
            const weekCount = uniqueWeeks.size;
            
            const btnStyle = "padding: 0.75rem 1.25rem; background: linear-gradient(135deg, #667eea, #764ba2); color: white; border: none; border-radius: 12px; cursor: pointer; font-weight: 700; box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3); transition: all 0.2s ease;";
            const btnDisabledStyle = "padding: 0.75rem 1.25rem; background: linear-gradient(135deg, #adb5bd, #868e96); color: white; border: none; border-radius: 12px; cursor: not-allowed; font-weight: 700; box-shadow: none; opacity: 0.3;";
            
            navigationContent = `
                <button id="prev-venue" class="nav-button nav-prev" ${prevDisabled} title="Gymnase précédent" style="${prevDisabled ? btnDisabledStyle : btnStyle}">
                    <span class="nav-button-icon" style="font-size: 1.25rem; font-weight: 900;">◀</span>
                </button>
                
                <div class="nav-current-item" style="display: flex; flex-direction: column; align-items: center; gap: 0.5rem; min-width: 350px; padding: 0.75rem 1.5rem; background: white; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08);">
                    <div class="nav-item-main" style="display: flex; align-items: center; gap: 1rem;">
                        <span class="nav-item-icon" style="font-size: 1.5rem;">🏛️</span>
                        <span class="nav-item-label" style="font-size: 1.5rem; font-weight: 900; color: #667eea; letter-spacing: 1px;">${venueName}</span>
                        <span class="nav-item-indicator" style="padding: 0.25rem 0.75rem; background: linear-gradient(135deg, #f8f9fa, #e9ecef); border-radius: 20px; font-size: 0.85rem; font-weight: 600; color: #495057;">${venueIndicator}</span>
                    </div>
                    <div class="nav-item-subtitle" style="font-size: 0.9rem; color: #6c757d; font-weight: 600;">
                        ${totalMatches} match${totalMatches > 1 ? 's' : ''} • ${weekCount} journée${weekCount > 1 ? 's' : ''}
                    </div>
                </div>
                
                <button id="next-venue" class="nav-button nav-next" ${nextDisabled} title="Gymnase suivant" style="${nextDisabled ? btnDisabledStyle : btnStyle}">
                    <span class="nav-button-icon" style="font-size: 1.25rem; font-weight: 900;">▶</span>
                </button>
            `;
        }
        
        return `
            <div class="agenda-navigation-bar" style="display: flex; justify-content: space-between; align-items: center; padding: 1rem 1.5rem; background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%); border-bottom: 3px solid #667eea; box-shadow: 0 4px 12px rgba(0,0,0,0.08); flex-shrink: 0; gap: 2rem; z-index: 100;">
                <!-- Section gauche: Informations générales -->
                <div class="nav-section nav-left" style="display: flex; align-items: center; gap: 1rem; min-width: 250px;">
                    <div class="nav-info-group" style="display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 1rem; background: rgba(102, 126, 234, 0.05); border-radius: 8px; transition: all 0.2s ease;">
                        <span class="nav-icon" style="font-size: 1.25rem;">🏟️</span>
                        <span class="nav-label" style="font-size: 0.85rem; color: #6c757d; font-weight: 600;">Gymnases</span>
                        <span class="nav-value" style="font-size: 1rem; font-weight: 700; color: #667eea;">${totalVenues}</span>
                    </div>
                    <div class="nav-info-group" style="display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 1rem; background: rgba(102, 126, 234, 0.05); border-radius: 8px; transition: all 0.2s ease;">
                        <span class="nav-icon" style="font-size: 1.25rem;">🎯</span>
                        <span class="nav-label" style="font-size: 0.85rem; color: #6c757d; font-weight: 600;">Matchs</span>
                        <span class="nav-value" style="font-size: 1rem; font-weight: 700; color: #667eea;">${totalMatches}</span>
                    </div>
                </div>
                
                <!-- Section centrale: Navigation dynamique selon le mode -->
                <div class="nav-section nav-center" style="display: flex; align-items: center; gap: 1rem; flex: 1; justify-content: center; min-width: 500px;">
                    ${navigationContent}
                </div>
                
                <!-- Section droite: Informations horaires -->
                <div class="nav-section nav-right" style="display: flex; align-items: center; gap: 1rem; min-width: 250px; justify-content: flex-end;">
                    <div class="nav-info-group" style="display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 1rem; background: rgba(102, 126, 234, 0.05); border-radius: 8px; transition: all 0.2s ease;">
                        <span class="nav-icon" style="font-size: 1.25rem;">🕒</span>
                        <span class="nav-label" style="font-size: 0.85rem; color: #6c757d; font-weight: 600;">Horaires</span>
                        <span class="nav-value" style="font-size: 1rem; font-weight: 700; color: #667eea;">14h - 23h</span>
                    </div>
                </div>
            </div>
        `;
    }
    
    /**
     * Génère l'échelle des horaires
     */
    generateTimeScale(minHour, maxHour, pixelsPerHour, totalHeight) {
        let html = '<div class="time-scale" style="height: ' + totalHeight + 'px; position: relative;">';
        
        for (let hour = minHour; hour <= maxHour; hour++) {
            const top = (hour - minHour) * pixelsPerHour;
            html += `
                <div class="time-marker" style="position: absolute; top: ${top}px; width: 100%;">
                    <span class="time-label">${hour}:00</span>
                    <div class="time-line"></div>
                </div>
            `;
        }
        
        html += '</div>';
        return html;
    }
    
    /**
     * Génère une colonne pour un gymnase
     */
    generateVenueColumn(venue, matches, maxSimultaneous, minHour, pixelsPerHour, matchDuration, totalHeight) {
        // Largeur adaptative avec réduction progressive si trop de matchs simultanés
        let widthPerSlot;
        if (maxSimultaneous <= 3) {
            widthPerSlot = 230; // Largeur normale
        } else if (maxSimultaneous <= 6) {
            widthPerSlot = 200; // Réduction légère
        } else if (maxSimultaneous <= 10) {
            widthPerSlot = 170; // Réduction moyenne
        } else if (maxSimultaneous <= 15) {
            widthPerSlot = 150; // Réduction importante
        } else {
            widthPerSlot = 130; // Réduction maximale pour beaucoup de matchs
        }
        
        const padding = 16; // Padding total de la colonne
        const columnWidth = (maxSimultaneous * widthPerSlot) + padding;
        
        console.log(`🔍 [Venue ${venue.name}] maxSimultaneous: ${maxSimultaneous}, widthPerSlot: ${widthPerSlot}px, columnWidth: ${columnWidth}px`);
        
        return `
            <div class="venue-column" 
                 data-venue-id="${venue.id}"
                 data-capacity="${venue.capacity}"
                 data-max-simultaneous="${maxSimultaneous}"
                 style="width: ${columnWidth}px; flex-shrink: 0;">
                <!-- En-tête du gymnase -->
                <div class="venue-header">
                    <div class="venue-name">${venue.name}</div>
                    <div class="venue-info">
                        <span class="venue-capacity">⚡ Capacité: ${venue.capacity}</span>
                        <span class="venue-matches">📊 ${matches.length} matchs</span>
                        ${maxSimultaneous > 1 ? `<span class="venue-simultaneous">🔀 Max: ${maxSimultaneous}</span>` : ''}
                    </div>
                </div>
                
                <!-- Corps avec les matchs -->
                <div class="venue-body" style="height: ${totalHeight}px; position: relative;">
                    ${this.generateVenueMatches(matches, minHour, pixelsPerHour, matchDuration, maxSimultaneous, widthPerSlot)}
                </div>
            </div>
        `;
    }
    
    /**
     * Génère une colonne pour un gymnase avec largeur personnalisée
     */
    generateVenueColumnWithWidth(venue, matches, maxSimultaneous, columnWidth, widthPerSlot, minHour, maxHour, pixelsPerHour, matchDuration, totalHeight, showEmptySlots = false) {
        console.log(`🔍 [Venue ${venue.name}] maxSimultaneous: ${maxSimultaneous}, widthPerSlot: ${widthPerSlot}px, columnWidth: ${columnWidth}px, showEmptySlots: ${showEmptySlots}`);
        
        return `
            <div class="venue-column" 
                 data-venue-id="${venue.id}"
                 data-capacity="${venue.capacity}"
                 data-max-simultaneous="${maxSimultaneous}"
                 style="width: ${columnWidth}px; flex-shrink: 0; background: linear-gradient(180deg, #ffffff 0%, #f8f9fa 100%); border-right: 2px solid #e9ecef; margin-right: 4px; border-radius: 0 0 8px 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
                
                <!-- Corps avec les matchs et créneaux libres (sans en-tête) -->
                <div class="venue-body" style="height: ${totalHeight}px; position: relative; background-image: repeating-linear-gradient(to bottom, transparent 0, transparent 119px, rgba(102, 126, 234, 0.08) 119px, rgba(102, 126, 234, 0.08) 120px);">
                    ${showEmptySlots ? this.generateEmptySlots(matches, venue, minHour, maxHour, pixelsPerHour, widthPerSlot) : ''}
                    ${this.generateVenueMatches(matches, minHour, pixelsPerHour, matchDuration, maxSimultaneous, widthPerSlot)}
                </div>
            </div>
        `;
    }
    
    /**
     * Génère les créneaux libres pour un gymnase à partir des données slots.available
     * Utilise les données réelles du JSON au lieu de calculer
     */
    generateEmptySlots(matches, venue, minHour, maxHour, pixelsPerHour, widthPerSlot) {
        // Récupérer les slots disponibles depuis les données
        const data = this.dataManager?.getData();
        if (!data || !data.slots || !data.slots.available) {
            console.warn('⚠️ Aucune donnée de slots disponibles');
            return '';
        }
        
        // Filtrer les slots pour ce gymnase et cette semaine courante
        const currentWeek = this.displayMode === 'week' && this.weeks && this.weeks[this.currentWeekIndex] 
            ? this.weeks[this.currentWeekIndex].weekNumber 
            : null;
        
        const venueSlots = data.slots.available.filter(slot => {
            if (slot.gymnase !== venue.id) return false;
            // Si on est en mode journée, filtrer par semaine courante
            if (currentWeek !== null && slot.semaine !== currentWeek) return false;
            return true;
        });
        
        if (venueSlots.length === 0) {
            return '';
        }
        
        console.log(`🟢 ${venueSlots.length} créneaux libres pour ${venue.name}`);
        
        let html = '';
        const slotDuration = 2; // Durée d'un créneau en heures
        
        // Grouper les slots par horaire pour gérer la capacité multiple
        const slotsByTime = {};
        venueSlots.forEach(slot => {
            const time = this.parseTime(slot.horaire);
            if (!time || time < minHour || time >= maxHour) return;
            
            if (!slotsByTime[time]) {
                slotsByTime[time] = [];
            }
            slotsByTime[time].push(slot);
        });
        
        // Pour chaque horaire avec des slots libres
        Object.entries(slotsByTime).forEach(([timeStr, slots]) => {
            const time = parseFloat(timeStr);
            const slotStart = time;
            const slotEnd = time + slotDuration;
            
            // Position verticale
            const top = (slotStart - minHour) * pixelsPerHour;
            const height = slotDuration * pixelsPerHour - 10;
            
            // Compter combien de matchs occupent déjà ce créneau
            const overlappingMatches = matches.filter(match => {
                const matchTime = this.parseTime(match.horaire);
                if (!matchTime) return false;
                
                const matchEnd = matchTime + slotDuration;
                // Chevauchement si : !(fin1 <= début2 || début1 >= fin2)
                return !(matchEnd <= slotStart || matchTime >= slotEnd);
            });
            
            const occupiedSlots = overlappingMatches.length;
            
            // Afficher chaque slot libre
            slots.forEach((slot, index) => {
                const slotIndex = occupiedSlots + index;
                const left = slotIndex * widthPerSlot + 2;
                const width = widthPerSlot - 4;
                
                html += `
                    <div class="empty-slot" data-slot-id="${slot.slot_id}" style="
                        position: absolute;
                        top: ${top}px;
                        left: ${left}px;
                        width: ${width}px;
                        height: ${height}px;
                        background: linear-gradient(135deg, 
                            rgba(34, 197, 94, 0.08) 0%, 
                            rgba(34, 197, 94, 0.04) 100%);
                        border: 2px dashed rgba(34, 197, 94, 0.3);
                        border-radius: 8px;
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        justify-content: center;
                        font-size: 0.75rem;
                        color: rgba(34, 197, 94, 0.7);
                        font-weight: 600;
                        text-align: center;
                        padding: 0.5rem;
                        cursor: default;
                        transition: all 0.2s ease;
                        z-index: 1;
                    " onmouseover="this.style.background='linear-gradient(135deg, rgba(34, 197, 94, 0.15) 0%, rgba(34, 197, 94, 0.08) 100%)'; this.style.borderColor='rgba(34, 197, 94, 0.5)'; this.style.transform='scale(1.02)'; this.style.zIndex='3';" onmouseout="this.style.background='linear-gradient(135deg, rgba(34, 197, 94, 0.08) 0%, rgba(34, 197, 94, 0.04) 100%)'; this.style.borderColor='rgba(34, 197, 94, 0.3)'; this.style.transform='scale(1)'; this.style.zIndex='1';">
                        <div style="font-size: 1.5rem; margin-bottom: 0.25rem;">✓</div>
                        <div style="font-weight: 700; font-size: 0.8rem;">Disponible</div>
                        <div style="font-size: 0.7rem; opacity: 0.8; margin-top: 0.25rem;">${this.formatTimeRange(slotStart, slotEnd)}</div>
                    </div>
                `;
            });
        });
        
        return html;
    }
    
    /**
     * Génère les créneaux libres pour une journée spécifique en mode venue
     * @param {Array} matches - Matchs déjà planifiés dans cette journée
     * @param {string} venueId - ID du gymnase
     * @param {number} weekNumber - Numéro de la journée
     * @param {number} minHour - Heure minimale
     * @param {number} maxHour - Heure maximale
     * @param {number} pixelsPerHour - Pixels par heure
     * @param {number} widthPerSlot - Largeur d'un slot
     */
    generateEmptySlotsForWeek(matches, venueId, weekNumber, minHour, maxHour, pixelsPerHour, widthPerSlot) {
        const data = this.dataManager?.getData();
        if (!data || !data.slots || !data.slots.available) {
            console.warn('⚠️ Aucune donnée de slots disponibles');
            return '';
        }
        
        // Filtrer les slots pour ce gymnase ET cette journée
        const slots = data.slots.available.filter(slot => {
            return slot.gymnase === venueId && slot.semaine === weekNumber;
        });
        
        if (slots.length === 0) {
            return '';
        }
        
        console.log(`🟢 ${slots.length} créneaux libres pour ${venueId} en J${weekNumber}`);
        
        let html = '';
        const slotDuration = AgendaGridView.MATCH_DURATION_HOURS;
        
        // Grouper les slots par horaire
        const slotsByTime = {};
        slots.forEach(slot => {
            const time = this.parseTime(slot.horaire);
            if (!time || time < minHour || time >= maxHour) return;
            
            if (!slotsByTime[time]) {
                slotsByTime[time] = [];
            }
            slotsByTime[time].push(slot);
        });
        
        // Pour chaque horaire avec des slots libres
        Object.entries(slotsByTime).forEach(([timeStr, timeSlots]) => {
            const time = parseFloat(timeStr);
            const slotStart = time;
            const slotEnd = time + slotDuration;
            
            // Position verticale
            const top = (slotStart - minHour) * pixelsPerHour;
            const height = slotDuration * pixelsPerHour;
            
            // Compter combien de slots libres on peut afficher
            // (limité par le nombre de matchs simultanés pour ne pas déborder)
            timeSlots.forEach((slot, index) => {
                const left = index * widthPerSlot + 2;
                const width = widthPerSlot - 4;
                
                html += `
                    <div class="empty-slot" style="
                        position: absolute;
                        top: ${top}px;
                        left: ${left}px;
                        width: ${width}px;
                        height: ${height}px;
                        background: linear-gradient(135deg, rgba(34, 197, 94, 0.1), rgba(22, 163, 74, 0.15));
                        border: 2px dashed rgba(34, 197, 94, 0.4);
                        border-radius: 8px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        flex-direction: column;
                        gap: 0.25rem;
                        padding: 0.5rem;
                        pointer-events: none;
                        z-index: 1;
                    ">
                        <div style="font-weight: 700; font-size: 0.8rem; color: rgba(22, 101, 52, 0.9);">Disponible</div>
                        <div style="font-size: 0.7rem; opacity: 0.8; margin-top: 0.25rem; color: rgba(22, 101, 52, 0.8);">${this.formatTimeRange(slotStart, slotEnd)}</div>
                    </div>
                `;
            });
        });
        
        return html;
    }
    
    /**
     * Formate une plage horaire
     */
    formatTimeRange(startHour, endHour) {
        const format = (h) => `${h}h${h === Math.floor(h) ? '00' : '30'}`;
        return `${format(startHour)} - ${format(endHour)}`;
    }
    
    /**
     * Génère les matchs d'un gymnase avec positionnement absolu
     */
    generateVenueMatches(matches, minHour, pixelsPerHour, matchDuration, maxSimultaneous, widthPerSlot) {
        if (!matches || matches.length === 0) return '';
        
        // Trier les matchs par horaire
        const sortedMatches = matches.slice().sort((a, b) => {
            const timeA = this.parseTime(a.horaire) || 0;
            const timeB = this.parseTime(b.horaire) || 0;
            return timeA - timeB;
        });
        
        // Assigner un slot horizontal à chaque match
        const matchSlots = this.assignMatchSlots(sortedMatches);
        
        let html = '';
        sortedMatches.forEach((match, index) => {
            const time = this.parseTime(match.horaire);
            if (!time) return;
            
            // Position verticale basée sur l'horaire
            const top = (time - minHour) * pixelsPerHour;
            const height = matchDuration * pixelsPerHour; // Hauteur complète sans marge
            
            // Position horizontale basée sur le slot
            const slot = matchSlots.get(match.match_id) || 0;
            const left = slot * widthPerSlot + 2;
            const width = widthPerSlot - 4;
            
            html += `
                <div class="match-wrapper" style="
                    position: absolute;
                    top: ${top}px;
                    left: ${left}px;
                    width: ${width}px;
                    height: ${height}px;
                ">
                    ${this.cardRenderer.renderMatchCard(match, false, index, true, null)}
                </div>
            `;
        });
        
        return html;
    }
    
    /**
     * Assigne un slot horizontal à chaque match pour éviter les chevauchements visuels
     */
    assignMatchSlots(matches) {
        const slots = new Map();
        
        // Récupérer la durée du match depuis la config (en minutes)
        const matchDurationMinutes = this.dataManager.data?.config?.duree_match_minutes || 90;
        const MATCH_DURATION = matchDurationMinutes / 60; // Conversion en heures
        
        // Grouper les matchs qui se chevauchent
        const overlappingGroups = [];
        
        matches.forEach(match => {
            const startTime = this.parseTime(match.horaire);
            if (!startTime) return;
            
            const endTime = startTime + MATCH_DURATION;
            
            // Chercher un groupe existant qui chevauche ce match
            let foundGroup = false;
            
            for (let group of overlappingGroups) {
                // Vérifier si ce match chevauche avec au moins un match du groupe
                const overlaps = group.matches.some(m => {
                    const mStart = this.parseTime(m.horaire);
                    const mEnd = mStart + MATCH_DURATION;
                    // Chevauchement si : !(fin1 <= début2 || début1 >= fin2)
                    return !(endTime <= mStart || startTime >= mEnd);
                });
                
                if (overlaps) {
                    group.matches.push(match);
                    foundGroup = true;
                    break;
                }
            }
            
            // Si aucun groupe ne convient, créer un nouveau groupe
            if (!foundGroup) {
                overlappingGroups.push({
                    matches: [match]
                });
            }
        });
        
        // Pour chaque groupe, assigner des slots en fonction de l'horaire
        overlappingGroups.forEach(group => {
            // Trier les matchs du groupe par horaire
            const sortedGroupMatches = group.matches.sort((a, b) => {
                const timeA = this.parseTime(a.horaire) || 0;
                const timeB = this.parseTime(b.horaire) || 0;
                return timeA - timeB;
            });
            
            // Assigner les slots séquentiellement
            const usedSlots = []; // [{slot: number, endTime: number}]
            
            sortedGroupMatches.forEach(match => {
                const startTime = this.parseTime(match.horaire);
                const endTime = startTime + MATCH_DURATION;
                
                // Nettoyer les slots qui ont expiré avant ce match
                const activeSlots = usedSlots.filter(s => s.endTime > startTime);
                
                // Trouver le premier slot disponible
                let slot = 0;
                while (activeSlots.some(s => s.slot === slot)) {
                    slot++;
                }
                
                // Assigner ce slot
                slots.set(match.match_id, slot);
                activeSlots.push({ slot, endTime });
                
                // Mettre à jour usedSlots
                usedSlots.length = 0;
                usedSlots.push(...activeSlots);
            });
        });
        
        return slots;
    }
    
    /**
     * Attache les événements aux éléments de la vue
     */
    /**
     * Attache les événements de la vue (navigation, clics)
     * Les listeners sont nettoyés à chaque render pour éviter les fuites mémoire
     */
    attachEvents() {
        // Note: Les listeners sont automatiquement supprimés quand container.innerHTML est modifié
        // Pas besoin de nettoyage manuel car render() remplace le HTML complet
        
        // ═══════════════════════════════════════════════════════════════
        // DUAL MODE: Navigation selon le mode d'affichage
        // ═══════════════════════════════════════════════════════════════
        
        if (this.displayMode === 'week') {
            // MODE JOURNÉE: Navigation entre J1, J2, J4...
            const prevBtn = this.container.querySelector('#prev-week');
            const nextBtn = this.container.querySelector('#next-week');
            
            if (prevBtn) {
                prevBtn.addEventListener('click', () => {
                    if (this.currentWeekIndex > 0) {
                        this.currentWeekIndex--;
                        console.log(`🔍 [AgendaGrid] Navigation: Journée précédente (index: ${this.currentWeekIndex})`);
                        this.render();
                    }
                });
            }
            
            if (nextBtn) {
                nextBtn.addEventListener('click', () => {
                    if (this.currentWeekIndex < this.weeks.length - 1) {
                        this.currentWeekIndex++;
                        console.log(`🔍 [AgendaGrid] Navigation: Journée suivante (index: ${this.currentWeekIndex})`);
                        this.render();
                    }
                });
            }
            
        } else if (this.displayMode === 'venue') {
            // MODE GYMNASE: Navigation entre BESSON, LAENNEC, DESCARTES...
            const prevBtn = this.container.querySelector('#prev-venue');
            const nextBtn = this.container.querySelector('#next-venue');
            
            if (prevBtn) {
                prevBtn.addEventListener('click', () => {
                    if (this.currentVenueIndex > 0) {
                        this.currentVenueIndex--;
                        console.log(`🔍 [AgendaGrid] Navigation: Gymnase précédent (index: ${this.currentVenueIndex})`);
                        this.render();
                    }
                });
            }
            
            if (nextBtn) {
                nextBtn.addEventListener('click', () => {
                    if (this.currentVenueIndex < this.venues.length - 1) {
                        this.currentVenueIndex++;
                        console.log(`🔍 [AgendaGrid] Navigation: Gymnase suivant (index: ${this.currentVenueIndex})`);
                        this.render();
                    }
                });
            }
        }
        
        // ═══════════════════════════════════════════════════════════════
        // Événements communs aux deux modes
        // ═══════════════════════════════════════════════════════════════
        
        // Clic sur les cartes de match
        this.container.querySelectorAll('[data-match-id]').forEach(card => {
            card.addEventListener('click', (e) => {
                // Ne pas ouvrir si on commence un drag
                if (e.target.closest('.match-card').classList.contains('dragging')) {
                    return;
                }
                
                const matchId = card.dataset.matchId;
                const match = this.dataManager.getMatch(matchId);
                if (match && window.editModal) {
                    window.editModal.open(match);
                }
            });
        });
    }
    
    /**
     * Synchronise le scroll horizontal des en-têtes avec les colonnes
     */
    syncHeaderScroll() {
        const headersScroll = this.container.querySelector('.agenda-headers-scroll');
        const columnsContainer = this.container.querySelector('.venues-container, .weeks-container');
        
        if (!headersScroll || !columnsContainer) {
            console.warn('⚠️ Impossible de synchroniser le scroll: éléments introuvables');
            return;
        }
        
        // Supprimer les anciens listeners s'ils existent
        if (this._scrollSyncHandler) {
            columnsContainer.removeEventListener('scroll', this._scrollSyncHandler);
        }
        
        // Créer le handler de synchronisation
        this._scrollSyncHandler = () => {
            headersScroll.scrollLeft = columnsContainer.scrollLeft;
        };
        
        // Attacher le listener
        columnsContainer.addEventListener('scroll', this._scrollSyncHandler);
        
        console.log('✅ Synchronisation du scroll horizontal activée');
    }
    
    /**
     * Met à jour les filtres depuis le panneau latéral
     */
    updateFilters(filters) {
        this.filters = { ...this.filters, ...filters };
        this.render();
    }
}

// Export global
window.AgendaGridView = AgendaGridView;
