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
        this.colorCodingMode = 'mixte'; // Par défaut : coloration mixte (genre + niveau)
        
        // Affichage des créneaux libres
        this.showEmptySlots = false; // Par défaut : masqués
        // Affichage des badges de pénalités
        this.showPenalties = false;
        
        // Navigation par journée (mode 'week')
        this.currentWeekIndex = 0;
        this.weeks = []; // Liste des journées disponibles
        
        // Navigation par gymnase (mode 'venue')
        this.currentVenueIndex = 0;
        this.venues = []; // Liste des gymnases disponibles
        
        // Date de début du championnat - sera initialisée depuis les données de config
        // Valeur par défaut si non spécifiée dans config
        this.championshipStartDate = this._initChampionshipStartDate();
        
        // Stockage des event listeners pour nettoyage
        this._eventListeners = [];

        // Contexte spécifique au mode entente (stats + listes)
        this.ententeContext = null;
    }
    
    /**
     * Initialise la date de début du championnat depuis les données de configuration
     * @returns {Date} Date de début du championnat
     */
    _initChampionshipStartDate() {
        // Essayer de récupérer la date depuis les données de configuration
        const data = this.dataManager?.getData?.();
        const dateDebut = data?.config?.calendrier?.date_debut;
        
        if (dateDebut) {
            // Format attendu: "YYYY-MM-DD"
            const [year, month, day] = dateDebut.split('-').map(Number);
            console.log(`📅 Date de début chargée depuis config: ${dateDebut}`);
            return new Date(year, month - 1, day); // month - 1 car les mois JS sont 0-indexed
        }
        
        // Valeur par défaut si non spécifiée
        console.warn('⚠️ Date de début non trouvée dans config, utilisation de la valeur par défaut');
        return new Date(2025, 9, 16); // 16 octobre 2025
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
                        { value: 'mixte', text: '✨ Mixte' },
                        { value: 'genre', text: '👥 Genre' },
                        { value: 'niveau', text: '🎯 Niveau' },
                        { value: 'penalite', text: '⚠️ Pénalités' },
                        { value: 'statut', text: '✅ Statut' },
                        { value: 'none', text: '⚫ Neutre' }
                    ],
                    default: this.colorCodingMode || 'mixte',
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
                },
                {
                    type: 'checkbox',
                    id: 'agenda-show-penalties',
                    label: 'Badges pénalités',
                    description: 'Afficher les badges indiquant le total de pénalités',
                    default: this.showPenalties,
                    action: (value) => {
                        this.setShowPenalties(value);
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
        const validModes = ['none', 'genre', 'niveau', 'penalite', 'statut', 'mixte'];
        if (!validModes.includes(mode)) {
            console.warn(`Mode de coloration invalide: ${mode}`);
            return;
        }
        
        this.colorCodingMode = mode;
        
        // Appliquer les classes de coloration sur le container
        const container = document.querySelector('.agenda-view-container');
        if (container) {
            // Retirer toutes les classes de coloration
            container.classList.remove('color-none', 'color-genre', 'color-niveau', 'color-penalite', 'color-statut', 'color-mixte');
            // Ajouter la nouvelle classe
            container.classList.add(`color-${mode}`);
        }
        
        // Re-rendre la vue pour appliquer les changements
        this.render();

        if (window.logThemeDiagnostics) {
            window.logThemeDiagnostics(`color-coding:${mode}`);
        } else {
            console.info('[ColorCoding] Applied', mode);
        }
    }
    
    /**
     * Change le mode d'affichage
     * @param {string} mode - 'week' pour navigation par journée, 'venue' pour navigation par gymnase
     */
    setDisplayMode(mode) {
        const validModes = ['week', 'venue', 'entente'];
        if (!validModes.includes(mode)) {
            console.warn(`Mode d'affichage invalide: ${mode}`);
            return;
        }
        
        this.displayMode = mode;
        
        // Réinitialiser l'index de navigation
        if (mode === 'week') {
            this.currentWeekIndex = 0;
        } else if (mode === 'venue') {
            this.currentVenueIndex = 0;
        } else if (mode === 'entente') {
            this.currentWeekIndex = 0;
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

    setShowPenalties(show) {
        this.showPenalties = Boolean(show);
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
        
        // Filtre par genre - utiliser m.genre en priorité (déterminé par le serveur)
        if (this.filters.gender) {
            filtered = filtered.filter(m => {
                const genre = m.genre || m.equipe1_genre || m.equipe2_genre;
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
            const searchTerm = this.filters.team.toLowerCase();
            filtered = filtered.filter(m => {
                const equipe1 = (m.equipe1_nom || m.equipe1_nom_complet || '').toLowerCase();
                const equipe2 = (m.equipe2_nom || m.equipe2_nom_complet || '').toLowerCase();
                return (equipe1 && equipe1.includes(searchTerm)) || (equipe2 && equipe2.includes(searchTerm));
            });
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

    countUniqueVenues(matches = []) {
        const uniqueVenues = new Set();
        matches.forEach(match => {
            const venueId = match?.gymnase || match?.gymnase_id;
            if (venueId) {
                uniqueVenues.add(venueId);
            }
        });
        return uniqueVenues.size;
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
            
            // Rafraîchir la date de début du championnat depuis les données
            this.championshipStartDate = this._initChampionshipStartDate();
            
            const isEntenteMode = this.displayMode === 'entente';
            const filtersActive = Object.values(this.filters || {}).some(Boolean);

            let matchesSource = data.matches.scheduled || [];
            let filteredPendingEntentes = [];

            if (isEntenteMode) {
                const ententeMatches = this.collectEntenteMatches(data);
                const scheduledEntentes = ententeMatches.filter(match => this.hasEntenteSlot(match));
                const pendingEntentes = ententeMatches.filter(match => !this.hasEntenteSlot(match));

                this.ententeContext = {
                    total: ententeMatches.length,
                    scheduledCount: scheduledEntentes.length,
                    pendingCount: pendingEntentes.length,
                    scheduledMatches: scheduledEntentes,
                    pendingMatches: pendingEntentes
                };

                matchesSource = scheduledEntentes;
                filteredPendingEntentes = this.filterMatches(pendingEntentes || []);
            } else {
                this.ententeContext = null;
            }
            
            const filteredMatches = this.filterMatches(matchesSource);

            if (filteredMatches.length === 0) {
                if (isEntenteMode) {
                    this.renderEntenteFallbackView(filteredMatches, filteredPendingEntentes, filtersActive);
                } else {
                    this.container.innerHTML = '<div class="empty-state">Aucun match ne correspond aux filtres sélectionnés</div>';
                }
                return;
            }
            
            // ═══════════════════════════════════════════════════════════════
            // DUAL MODE LOGIC: Organiser selon le mode d'affichage
            // ═══════════════════════════════════════════════════════════════
            let matchesToDisplay = [];
            
            if (this.displayMode === 'week' || isEntenteMode) {
                // MODE JOURNÉE: Organiser par semaine, naviguer entre J1, J2, J4...
                this.weeks = this.organizeMatchesByWeek(filteredMatches);
                
                if (this.weeks.length === 0) {
                    if (isEntenteMode) {
                        this.renderEntenteFallbackView(filteredMatches, filteredPendingEntentes, filtersActive);
                    } else {
                        this.container.innerHTML = '<div class="empty-state">Aucun match trouvé</div>';
                    }
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
                console.log(`🔍 [AgendaGrid] ${isEntenteMode ? 'Mode Entente' : 'Mode Journée'} - ${currentWeek.key} matchs:`, matchesToDisplay.length);
                
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
            const ententePanelContent = isEntenteMode
                ? this.buildEntentePanelContent(
                    filteredMatches,
                    filteredPendingEntentes,
                    this.ententeContext
                )
                : '';

            const ententePanelSection = ententePanelContent
                ? `<section class="agenda-entente-mode entente-followup">${ententePanelContent}</section>`
                : '';
            
            const html = this.generateAgendaView(matchesToDisplay, data, {
                ententeMode: isEntenteMode,
                ententePanel: ententePanelSection
            });
            
            this.container.innerHTML = html;
            
            // Initialiser le drag & drop
            this.dragDropManager.initializeDragDrop(this.container);
            
            // Attacher les événements
            this.attachEvents();
            
            // Synchroniser le scroll horizontal des en-têtes avec les colonnes
            this.syncHeaderScroll();
            
            // Log du mode de coloration actif (le style est désormais géré côté CSS)
            if (this.colorCodingMode && this.colorCodingMode !== 'none') {
                console.debug('[ColorCoding] Active during render', this.colorCodingMode);
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
    generateAgendaView(matches, data, options = {}) {
        // Utiliser les constantes de classe
        const minHour = AgendaGridView.MIN_HOUR;
        const maxHour = AgendaGridView.MAX_HOUR;
        const pixelsPerHour = AgendaGridView.PIXELS_PER_HOUR;
        const matchDuration = AgendaGridView.MATCH_DURATION_HOURS;
        const matchDisplayHeight = AgendaGridView.MATCH_DURATION_HOURS;
        const totalHeight = (maxHour - minHour) * pixelsPerHour;
        const { ententeMode = false, ententePanel = '' } = options;
        const isWeekLikeMode = this.displayMode === 'week' || ententeMode;
        
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
        
        if (isWeekLikeMode) {
            // MODE JOURNÉE: Colonnes = Gymnases
            // Récupérer le numéro de semaine courante pour filtrer les créneaux libres
            const currentWeekNumber = this.weeks?.[this.currentWeekIndex]?.weekNumber || null;
            
            // Inclure les gymnases avec créneaux libres si l'option est activée
            venues = this.getVenuesWithCapacity(matches, data, this.showEmptySlots, currentWeekNumber);
            matchesByVenue = this.groupMatchesByVenue(matches);
            
            // Calculer le nombre maximum de slots nécessaires par gymnase
            // Si showEmptySlots, inclure les créneaux disponibles dans le calcul
            if (this.showEmptySlots) {
                venueMaxSimultaneous = this.calculateMaxSlotsWithAvailable(matchesByVenue, currentWeekNumber);
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
        const penaltyClass = this.showPenalties ? ' show-penalties' : '';
        
        // Générer les en-têtes de colonnes séparément
        let headersHTML = '';
        if (isWeekLikeMode) {
            headersHTML = venues.map(venue => {
                const widthInfo = columnWidths.get(venue.id) || { width: this.columnMinWidth, widthPerSlot: 200 };
                const maxSim = venueMaxSimultaneous.get(venue.id) || 1;
                return `
                    <div class="venue-header-cell agenda-header-card" style="width: ${widthInfo.width}px;">
                        <div class="venue-name">${venue.name}</div>
                        <div class="venue-info">
                            <span class="venue-capacity">⚡ Capacité: ${venue.capacity}</span>
                            <span class="venue-matches">📊 ${(matchesByVenue.get(venue.id) || []).length} matchs</span>
                            ${maxSim > 1 ? `<span class="venue-simultaneous">🔀 Max: ${maxSim}</span>` : ''}
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
                    <div class="week-header-cell agenda-header-card" style="width: ${widthInfo.width}px;">
                        <div class="week-name">${weekLabel}</div>
                        <div class="week-info">
                            <span class="week-matches">📊 ${(matchesByWeek.get(week.weekNumber) || []).length} matchs</span>
                            ${maxSim > 1 ? `<span class="week-simultaneous">🔀 Max: ${maxSim}</span>` : ''}
                        </div>
                    </div>
                `;
            }).join('');
        }
        
        return `
            <div class="agenda-view-container${colorClass}${penaltyClass}">
                <!-- Barre de navigation en haut (non-scrollable) -->
                ${this.generateNavigationBar(matches, venues, data)}
                
                <!-- Rangée des en-têtes de colonnes (au-dessus de la grille) -->
                <div class="agenda-headers-row">
                    <!-- Espace pour la colonne des horaires -->
                    <div class="agenda-header-spacer" style="width: ${AgendaGridView.TIME_COLUMN_WIDTH}px; margin-right: ${AgendaGridView.COLUMN_MARGIN}px;"></div>
                    <!-- Container scrollable pour les en-têtes -->
                    <div class="agenda-headers-scroll">
                        <div class="agenda-headers-track">
                            ${headersHTML}
                        </div>
                    </div>
                </div>
                
                <!-- Zone de contenu (scrollable verticalement uniquement) -->
                <div class="agenda-scroll-wrapper">
                    <div class="agenda-grid-container">
                        <!-- Colonne des horaires (fixée à gauche) -->
                        <div class="time-column-fixed" style="width: ${AgendaGridView.TIME_COLUMN_WIDTH}px; margin-right: ${AgendaGridView.COLUMN_MARGIN}px;">
                            ${this.generateTimeScale(minHour, maxHour, pixelsPerHour, totalHeight)}
                        </div>
                        
                        <!-- Colonnes dynamiques selon le mode -->
                        <div class="${containerClass}">
                            ${columnsHTML}
                        </div>
                    </div>
                </div>
                ${ententePanel || ''}
            </div>
        `;
    }

    /**
     * Récupère tous les gymnases avec leurs capacités
     * Si includeAvailableSlots est true, inclut aussi les gymnases ayant des créneaux libres
     * @param {Array} matches - Liste des matchs
     * @param {Object} data - Données complètes
     * @param {boolean} includeAvailableSlots - Inclure les gymnases avec créneaux libres
     * @param {number|null} currentWeek - Numéro de semaine pour filtrer (null = toutes semaines)
     */
    getVenuesWithCapacity(matches, data, includeAvailableSlots = false, currentWeek = null) {
        const venueMap = new Map();
        const venues = data.entities?.venues || {};
        
        // Récupérer les IDs de gymnases depuis les matchs de cette semaine
        const venuesWithMatches = new Set();
        matches.forEach(match => {
            if (match.gymnase) {
                venuesWithMatches.add(match.gymnase);
            }
        });
        
        // Si on affiche les créneaux libres, récupérer les gymnases ayant des créneaux libres
        const venuesWithSlots = new Set();
        if (includeAvailableSlots && data.slots?.available) {
            data.slots.available.forEach(slot => {
                // Filtrer par semaine courante si spécifiée
                if (currentWeek !== null && slot.semaine !== currentWeek) return;
                if (slot.gymnase) {
                    venuesWithSlots.add(slot.gymnase);
                }
            });
        }
        
        // Combiner les deux ensembles
        const allVenueIds = new Set([...venuesWithMatches, ...venuesWithSlots]);
        
        // Ajouter uniquement les gymnases pertinents depuis les entités
        Object.entries(venues).forEach(([id, venueData]) => {
            // Si on n'a ni matchs ni créneaux libres, ne pas inclure ce gymnase
            if (!allVenueIds.has(id)) return;
            
            venueMap.set(id, {
                id: id,
                name: venueData.nom || id,
                capacity: venueData.capacite || 1
            });
        });
        
        // Ajouter les gymnases des matchs qui ne sont pas dans les entités
        matches.forEach(match => {
            const venueId = match.gymnase;
            if (venueId && !venueMap.has(venueId)) {
                venueMap.set(venueId, {
                    id: venueId,
                    name: venueId,
                    capacity: 1
                });
            }
        });
        
        // Ajouter les gymnases des slots libres qui ne sont pas dans les entités
        if (includeAvailableSlots && data.slots?.available) {
            data.slots.available.forEach(slot => {
                if (currentWeek !== null && slot.semaine !== currentWeek) return;
                const venueId = slot.gymnase;
                if (venueId && !venueMap.has(venueId)) {
                    venueMap.set(venueId, {
                        id: venueId,
                        name: venueId,
                        capacity: 1
                    });
                }
            });
        }
        
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
     * @param {Map} matchesByVenue - Map des matchs par gymnase
     * @param {number|null} currentWeek - Numéro de semaine pour filtrer (passé en paramètre)
     */
    calculateMaxSlotsWithAvailable(matchesByVenue, currentWeek = null) {
        const maxSlots = new Map();
        const data = this.dataManager?.getData();
        
        if (!data || !data.slots || !data.slots.available) {
            // Pas de données de slots, revenir au calcul basique
            return this.calculateMaxSimultaneousMatches(matchesByVenue);
        }
        
        // Récupérer tous les gymnases qui ont des créneaux libres cette semaine
        const allVenuesWithSlots = new Set();
        data.slots.available.forEach(slot => {
            if (currentWeek !== null && slot.semaine !== currentWeek) return;
            allVenuesWithSlots.add(slot.gymnase);
        });
        
        // Calculer pour tous les gymnases (ceux avec matchs + ceux avec slots libres seulement)
        const allVenueIds = new Set([...matchesByVenue.keys(), ...allVenuesWithSlots]);
        
        allVenueIds.forEach(venueId => {
            const matches = matchesByVenue.get(venueId) || [];
            let max = 0;
            
            // Filtrer les slots disponibles pour ce gymnase et la semaine courante
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
            
            // Si pas d'horaires, maximum = 0
            if (allTimes.size === 0) {
                maxSlots.set(venueId, 0);
                return;
            }
            
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
            
            maxSlots.set(venueId, Math.max(1, max));
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
                  style="width: ${columnWidth}px; margin-right: ${AgendaGridView.COLUMN_MARGIN}px;">
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
                <div class="column-body" style="height: ${totalHeight}px;">
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
                 style="width: ${columnWidth}px; margin-right: ${AgendaGridView.COLUMN_MARGIN}px;">
                
                <!-- Corps avec les matchs et créneaux libres (sans en-tête) -->
                <div class="week-body" style="height: ${totalHeight}px;">
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
        const isEntenteMode = this.displayMode === 'entente';
        let totalVenues = venues.length;
        let totalMatches = matches.length;
        
        if (isEntenteMode) {
            totalVenues = this.countUniqueVenues(this.ententeContext?.scheduledMatches || []);
            totalMatches = this.ententeContext?.scheduledCount || 0;
        }
        
        let navigationContent = '';
        
        if (this.displayMode === 'week' || isEntenteMode) {
            const currentWeek = this.weeks[this.currentWeekIndex];
            if (currentWeek) {
                const weekLabel = this.formatWeekLabel(currentWeek);
                const weekDates = this.getWeekDates(currentWeek.weekNumber);
                const fullDate = weekDates.date.toLocaleDateString('fr-FR', {
                    weekday: 'long',
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                });
                const prevDisabled = this.currentWeekIndex === 0;
                const nextDisabled = this.currentWeekIndex === this.weeks.length - 1;
                const weekIndicator = `${this.currentWeekIndex + 1}/${this.weeks.length}`;
                
                let subtitle = fullDate;
                let titleIcon = '';
                if (isEntenteMode) {
                    const stats = this.ententeContext || { total: 0, scheduledCount: 0, pendingCount: 0 };
                    const ratio = stats.total ? Math.round((stats.scheduledCount / stats.total) * 100) : 0;
                    const progressText = stats.total
                        ? `${stats.scheduledCount}/${stats.total} planifiées • ${ratio}%`
                        : 'Aucune entente planifiée';
                    subtitle = `${fullDate} • ${progressText}`;
                    titleIcon = '<span class="nav-item-icon">🤝</span>';
                }
                
                navigationContent = `
                    <button id="prev-week" class="nav-button nav-prev" ${prevDisabled ? 'disabled' : ''} title="Journée précédente">
                        <span class="nav-button-icon">◀</span>
                    </button>
                    
                    <div class="nav-current-item">
                        <div class="nav-item-main">
                            ${titleIcon}
                            <span class="nav-item-label">${weekLabel}</span>
                            <span class="nav-item-indicator">${weekIndicator}</span>
                        </div>
                        <div class="nav-item-subtitle" title="${fullDate}">
                            ${subtitle}
                        </div>
                    </div>
                    
                    <button id="next-week" class="nav-button nav-next" ${nextDisabled ? 'disabled' : ''} title="Journée suivante">
                        <span class="nav-button-icon">▶</span>
                    </button>
                `;
            }
        } else if (this.displayMode === 'venue') {
            const currentVenue = this.venues[this.currentVenueIndex];
            const venueName = currentVenue.displayName || currentVenue.venueName;
            const prevDisabled = this.currentVenueIndex === 0;
            const nextDisabled = this.currentVenueIndex === this.venues.length - 1;
            const venueIndicator = `${this.currentVenueIndex + 1}/${this.venues.length}`;
            const uniqueWeeks = new Set(currentVenue.matches.map(m => m.semaine));
            const weekCount = uniqueWeeks.size;
            
            navigationContent = `
                <button id="prev-venue" class="nav-button nav-prev" ${prevDisabled ? 'disabled' : ''} title="Gymnase précédent">
                    <span class="nav-button-icon">◀</span>
                </button>
                
                <div class="nav-current-item">
                    <div class="nav-item-main">
                        <span class="nav-item-icon">🏛️</span>
                        <span class="nav-item-label">${venueName}</span>
                        <span class="nav-item-indicator">${venueIndicator}</span>
                    </div>
                    <div class="nav-item-subtitle">
                        ${totalMatches} match${totalMatches > 1 ? 's' : ''} • ${weekCount} journée${weekCount > 1 ? 's' : ''}
                    </div>
                </div>
                
                <button id="next-venue" class="nav-button nav-next" ${nextDisabled ? 'disabled' : ''} title="Gymnase suivant">
                    <span class="nav-button-icon">▶</span>
                </button>
            `;
        }
        
        const pendingInfo = isEntenteMode ? `
            <div class="nav-info-group nav-info-warning">
                <span class="nav-icon">⌛</span>
                <span class="nav-label">À organiser</span>
                <span class="nav-value">${this.ententeContext?.pendingCount || 0}</span>
            </div>
        ` : '';
        
        return `
            <div class="agenda-navigation-bar">
                <!-- Section gauche: Informations générales -->
                <div class="nav-section nav-left">
                    <div class="nav-info-group">
                        <span class="nav-icon">🏟️</span>
                        <span class="nav-label">Gymnases</span>
                        <span class="nav-value">${totalVenues}</span>
                    </div>
                    <div class="nav-info-group">
                        <span class="nav-icon">🎯</span>
                        <span class="nav-label">Matchs</span>
                        <span class="nav-value">${totalMatches}</span>
                    </div>
                    ${pendingInfo}
                </div>
                
                <!-- Section centrale: Navigation dynamique selon le mode -->
                <div class="nav-section nav-center">
                    ${navigationContent}
                </div>
                
                <!-- Section droite: Informations horaires -->
                <div class="nav-section nav-right">
                    <div class="nav-info-group">
                        <span class="nav-icon">🕒</span>
                        <span class="nav-label">Horaires</span>
                        <span class="nav-value">14h - 23h</span>
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
                  style="width: ${columnWidth}px;">
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
                <div class="venue-body" style="height: ${totalHeight}px;">
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
                 style="width: ${columnWidth}px; margin-right: ${AgendaGridView.COLUMN_MARGIN}px;">
                
                <!-- Corps avec les matchs et créneaux libres (sans en-tête) -->
                <div class="venue-body" style="height: ${totalHeight}px;">
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
     * Agrège tous les matchs marqués comme ententes (planifiés ou non)
     */
    collectEntenteMatches(data) {
        const aggregated = [];
        const seen = new Set();
        const sources = [
            ...(data?.matches?.scheduled || []),
            ...(data?.matches?.unscheduled || []),
            ...(data?.matches?.fixed || [])
        ];
        
        sources.forEach(match => {
            if (!this.isEntenteMatch(match)) return;
            const key = match.match_id || `${match.equipe1_id || match.equipe1_nom}-${match.equipe2_id || match.equipe2_nom}-${match.semaine || 'NA'}`;
            if (seen.has(key)) return;
            seen.add(key);
            aggregated.push(match);
        });
        
        return aggregated;
    }

    /**
     * Détermine si un match est une entente
     */
    isEntenteMatch(match) {
        if (!match) return false;
        return Boolean(
            match.is_entente ||
            match.entente_status ||
            (match.penalties && match.penalties.entente !== undefined)
        );
    }

    /**
     * Vérifie si une entente est planifiée (créneau confirmé)
     * Utilise le nouveau système EntenteStatus: scheduled ou played = planifié
     */
    isEntentePlanned(match) {
        if (!this.isEntenteMatch(match)) return false;
        if (match.entente_status) {
            const status = match.entente_status.toLowerCase();
            return status === 'scheduled' || status === 'played';
        }
        return Boolean(match.semaine && match.gymnase && match.horaire);
    }

    hasEntenteSlot(match) {
        if (!match) return false;
        return Boolean(
            match.semaine &&
            match.horaire &&
            (match.gymnase || match.gymnase_id || match.venue || match.venue_id)
        );
    }

    /**
     * Catégorise les ententes selon leur statut EntenteStatus
     * @param {Array} matches - Liste des matchs entente
     * @returns {Object} Objet avec les matchs catégorisés par statut
     */
    categorizeEntentesByStatus(matches) {
        const categories = {
            played: [],      // Ententes jouées (score enregistré)
            scheduled: [],   // Ententes planifiées (créneau confirmé)
            confirmed: [],   // Ententes confirmées (accord des équipes)
            suggested: [],   // Ententes suggérées (proposition système)
            unknown: []      // Sans statut clair
        };

        matches.forEach(match => {
            const status = (match.entente_status || '').toLowerCase();
            switch (status) {
                case 'played':
                    categories.played.push(match);
                    break;
                case 'scheduled':
                    categories.scheduled.push(match);
                    break;
                case 'confirmed':
                    categories.confirmed.push(match);
                    break;
                case 'suggested':
                    categories.suggested.push(match);
                    break;
                default:
                    // Fallback basé sur la présence de créneau
                    if (this.hasEntenteSlot(match)) {
                        categories.scheduled.push(match);
                    } else {
                        categories.suggested.push(match);
                    }
                    break;
            }
        });

        return categories;
    }

    /**
     * Génère la configuration d'affichage pour chaque catégorie d'entente
     */
    getEntenteStatusConfig() {
        return {
            played: {
                title: 'Jouées',
                subtitle: 'Matchs terminés avec score enregistré',
                icon: '✅',
                color: '#27AE60',
                bgColor: 'rgba(39, 174, 96, 0.1)',
                borderColor: 'rgba(39, 174, 96, 0.3)',
                emptyMessage: 'Aucune entente jouée pour le moment',
                emptyIcon: '🏆'
            },
            scheduled: {
                title: 'Planifiées',
                subtitle: 'Créneaux confirmés dans le calendrier',
                icon: '📅',
                color: '#3498DB',
                bgColor: 'rgba(52, 152, 219, 0.1)',
                borderColor: 'rgba(52, 152, 219, 0.3)',
                emptyMessage: 'Aucune entente n\'a encore de créneau',
                emptyIcon: '📅'
            },
            confirmed: {
                title: 'Confirmées',
                subtitle: 'Accord des équipes obtenu',
                icon: '🤝',
                color: '#9B59B6',
                bgColor: 'rgba(155, 89, 182, 0.1)',
                borderColor: 'rgba(155, 89, 182, 0.3)',
                emptyMessage: 'Aucune entente en attente de planification',
                emptyIcon: '🤝'
            },
            suggested: {
                title: 'Suggérées',
                subtitle: 'Propositions à valider par les équipes',
                icon: '💡',
                color: '#F39C12',
                bgColor: 'rgba(243, 156, 18, 0.1)',
                borderColor: 'rgba(243, 156, 18, 0.3)',
                emptyMessage: 'Aucune suggestion d\'entente',
                emptyIcon: '💡'
            }
        };
    }

    renderEntenteFallbackView(plannedMatches, pendingMatches, filtersActive) {
        const stats = this.ententeContext || { total: 0, scheduledCount: 0, pendingCount: 0 };
        const panelContent = this.buildEntentePanelContent(plannedMatches, pendingMatches, stats);
        let message;
        if (stats.scheduledCount === 0) {
            message = stats.pendingCount > 0
                ? "Aucun match d'entente n'a encore reçu de créneau confirmé."
                : "Aucune entente enregistrée pour le moment.";
        } else if (filtersActive) {
            message = "Aucun match d'entente planifié ne correspond aux filtres sélectionnés.";
        } else {
            message = "Aucun match d'entente planifié à afficher pour cette sélection.";
        }
        
        const penaltyClass = this.showPenalties ? ' show-penalties' : '';
        this.container.innerHTML = `
            <div class="agenda-view-container agenda-entente-mode entente-fallback${penaltyClass}">
                <div class="empty-state">${message}</div>
                ${panelContent ? `<section class="agenda-entente-mode entente-followup">${panelContent}</section>` : ''}
            </div>
        `;
    }

    buildEntentePanelContent(plannedMatches, pendingMatches, stats = null) {
        // Utiliser le nouveau système de catégorisation si disponible
        const allMatches = [...plannedMatches, ...pendingMatches];
        const categories = this.categorizeEntentesByStatus(allMatches);
        const statusConfig = this.getEntenteStatusConfig();
        
        const plannedCount = stats?.scheduledCount ?? plannedMatches.length;
        const pendingCount = stats?.pendingCount ?? pendingMatches.length;
        const totalCount = stats?.total ?? (plannedCount + pendingCount);
        
        if (!totalCount && plannedMatches.length === 0 && pendingMatches.length === 0) {
            return '';
        }
        
        const plannedFilteredLabel = plannedCount !== plannedMatches.length
            ? `${plannedMatches.length}/${plannedCount} visibles`
            : '';
        const pendingFilteredLabel = pendingCount !== pendingMatches.length
            ? `${pendingMatches.length}/${pendingCount} visibles`
            : '';
        
        const pendingEmptyMessage = pendingCount > 0 && pendingMatches.length === 0
            ? 'Les filtres actifs masquent ces ententes.'
            : undefined;
        const plannedEmptyMessage = plannedCount > 0 && plannedMatches.length === 0
            ? 'Les filtres actifs masquent ces ententes planifiées.'
            : undefined;
        
        // Générer le contenu avec le nouveau système de catégories
        return `
            ${this.generateEntenteSummaryBarEnhanced(categories, totalCount)}
            <div class="entente-columns entente-columns-enhanced">
                ${this.generateEntenteColumnEnhanced('suggested', categories.suggested, statusConfig.suggested)}
                ${this.generateEntenteColumnEnhanced('confirmed', categories.confirmed, statusConfig.confirmed)}
                ${this.generateEntenteColumnEnhanced('scheduled', categories.scheduled, statusConfig.scheduled)}
                ${this.generateEntenteColumnEnhanced('played', categories.played, statusConfig.played)}
            </div>
        `;
    }

    /**
     * Génère la barre de résumé améliorée avec les 4 catégories
     */
    generateEntenteSummaryBarEnhanced(categories, total) {
        const statusConfig = this.getEntenteStatusConfig();
        const finalized = categories.scheduled.length + categories.played.length;
        const ratio = total ? Math.round((finalized / total) * 100) : 0;
        
        return `
            <div class="entente-summary-bar entente-summary-enhanced">
                <div class="entente-summary-card total">
                    <div>
                        <div class="entente-summary-label">Total ententes</div>
                        <div class="entente-summary-value">${total}</div>
                    </div>
                    <span class="entente-summary-icon">🤝</span>
                </div>
                <div class="entente-summary-card suggested" style="border-left: 3px solid ${statusConfig.suggested.color};">
                    <div>
                        <div class="entente-summary-label">${statusConfig.suggested.title}</div>
                        <div class="entente-summary-value">${categories.suggested.length}</div>
                    </div>
                    <span class="entente-summary-icon">${statusConfig.suggested.icon}</span>
                </div>
                <div class="entente-summary-card confirmed" style="border-left: 3px solid ${statusConfig.confirmed.color};">
                    <div>
                        <div class="entente-summary-label">${statusConfig.confirmed.title}</div>
                        <div class="entente-summary-value">${categories.confirmed.length}</div>
                    </div>
                    <span class="entente-summary-icon">${statusConfig.confirmed.icon}</span>
                </div>
                <div class="entente-summary-card scheduled" style="border-left: 3px solid ${statusConfig.scheduled.color};">
                    <div>
                        <div class="entente-summary-label">${statusConfig.scheduled.title}</div>
                        <div class="entente-summary-value">${categories.scheduled.length}</div>
                    </div>
                    <span class="entente-summary-icon">${statusConfig.scheduled.icon}</span>
                </div>
                <div class="entente-summary-card played" style="border-left: 3px solid ${statusConfig.played.color};">
                    <div>
                        <div class="entente-summary-label">${statusConfig.played.title}</div>
                        <div class="entente-summary-value">${categories.played.length}</div>
                    </div>
                    <span class="entente-summary-icon">${statusConfig.played.icon}</span>
                </div>
                <div class="entente-summary-card ratio">
                    <div>
                        <div class="entente-summary-label">Avancement</div>
                        <div class="entente-summary-value">${ratio}%</div>
                    </div>
                    <span class="entente-summary-icon">📈</span>
                </div>
            </div>
        `;
    }

    /**
     * Génère une colonne de catégorie d'entente avec la configuration de statut
     */
    generateEntenteColumnEnhanced(statusKey, matches, config) {
        const count = matches.length;
        const cards = count > 0
            ? matches.map((match, index) => `
                    <div class="entente-card-wrapper">
                        ${this.cardRenderer.renderMatchCard(match, false, index, false, null)}
                    </div>
                `).join('')
            : `
                <div class="entente-empty-state">
                    <div class="entente-empty-icon">${config.emptyIcon}</div>
                    <div>${config.emptyMessage}</div>
                </div>
            `;
        
        return `
            <section class="entente-column entente-${statusKey}" style="border-top: 3px solid ${config.color}; background: ${config.bgColor};">
                <header class="entente-column-header" style="border-bottom: 1px solid ${config.borderColor};">
                    <div>
                        <div class="entente-column-title" style="color: ${config.color};">
                            ${config.icon} ${config.title}
                        </div>
                        <div class="entente-column-subtitle">${config.subtitle}</div>
                    </div>
                    <span class="entente-count" style="background: ${config.color}; color: white;">${count}</span>
                </header>
                <div class="entente-column-body">
                    ${cards}
                </div>
            </section>
        `;
    }

    /**
     * @deprecated Utilisez generateEntenteSummaryBarEnhanced à la place
     */
    generateEntenteSummaryBar(total, planned, pending) {
        const ratio = total ? Math.round((planned / total) * 100) : 0;
        return `
            <div class="entente-summary-bar">
                <div class="entente-summary-card">
                    <div>
                        <div class="entente-summary-label">Ententes totales</div>
                        <div class="entente-summary-value">${total}</div>
                    </div>
                    <span class="entente-summary-icon">🤝</span>
                </div>
                <div class="entente-summary-card pending">
                    <div>
                        <div class="entente-summary-label">À organiser</div>
                        <div class="entente-summary-value">${pending}</div>
                    </div>
                    <span class="entente-summary-icon">⌛</span>
                </div>
                <div class="entente-summary-card planned">
                    <div>
                        <div class="entente-summary-label">Planifiées</div>
                        <div class="entente-summary-value">${planned}</div>
                    </div>
                    <span class="entente-summary-icon">✅</span>
                </div>
                <div class="entente-summary-card ratio">
                    <div>
                        <div class="entente-summary-label">Avancement</div>
                        <div class="entente-summary-value">${ratio}%</div>
                    </div>
                    <span class="entente-summary-icon">📈</span>
                </div>
            </div>
        `;
    }

    /**
     * @deprecated Utilisez generateEntenteColumnEnhanced à la place
     */
    generateEntenteColumn(title, matches, variant, options = {}) {
        const count = typeof options.countOverride === 'number' ? options.countOverride : matches.length;
        const baseSubtitle = options.subtitle || (variant === 'pending'
            ? 'Créneaux à définir avec les capitaines'
            : 'Créneaux confirmés pour les ententes');
        const subtitleExtra = options.subtitleExtra ? ` • ${options.subtitleExtra}` : '';
        const subtitle = `${baseSubtitle}${subtitleExtra}`;
        const emptyMessage = options.emptyMessage || (variant === 'pending'
            ? 'Toutes les ententes sont déjà engagées'
            : 'Aucune entente confirmée pour l\'instant');
        const emptyIcon = variant === 'pending' ? '🙌' : '🎯';
        const cards = count
            ? matches.map((match, index) => `
                    <div class="entente-card-wrapper">
                        ${this.cardRenderer.renderMatchCard(match, false, index, false, null)}
                    </div>
                `).join('')
            : `
                <div class="entente-empty-state">
                    <div class="entente-empty-icon">${emptyIcon}</div>
                    <div>${emptyMessage}</div>
                </div>
            `;
        
        return `
            <section class="entente-column entente-${variant}">
                <header class="entente-column-header">
                    <div>
                        <div class="entente-column-title">${title}</div>
                        <div class="entente-column-subtitle">${subtitle}</div>
                    </div>
                    <span class="entente-count">${count}</span>
                </header>
                <div class="entente-column-body">
                    ${cards}
                </div>
            </section>
        `;
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
        
        if (this.displayMode === 'week' || this.displayMode === 'entente') {
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
     * Définit les filtres depuis le panneau latéral (compatible avec EnhancedFilterSystem)
     */
    setFilters(filters) {
        this.filters = { ...this.filters, ...filters };
        this.render();
    }
    
    /**
     * Met à jour les filtres depuis le panneau latéral (alias pour setFilters)
     */
    updateFilters(filters) {
        this.setFilters(filters);
    }
}

// Export global
window.AgendaGridView = AgendaGridView;
