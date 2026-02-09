/**
 * sport-utils.js - Utilitaires pour la gestion multi-sport
 * 
 * Fournit des fonctions pour:
 * - Récupérer les informations du sport depuis les données
 * - Obtenir l'emoji approprié
 * - Formater les affichages selon le sport
 */

class SportUtils {
    constructor() {
        this.sportData = null;
        this.defaultSport = {
            type: 'volleyball',
            prefix: 'VB',
            name: 'Volleyball',
            name_short: 'Volley',
            emoji: '🏐',
            duree_match_minutes: 90,
            score_format: 'points',
            niveaux: ['A1', 'A2', 'A3', 'A4'],
            genres: ['M', 'F']
        };
    }

    /**
     * Initialise les données de sport depuis le DataManager
     */
    init(dataManager) {
        if (!dataManager) {
            console.warn('⚠️ SportUtils: DataManager non fourni, utilisation des valeurs par défaut');
            this.sportData = this.defaultSport;
            return;
        }

        const data = dataManager.getData();
        this.sportData = data.sport || this.defaultSport;
        
        console.log('🎯 SportUtils initialisé:', {
            type: this.sportData.type,
            name: this.sportData.name,
            emoji: this.sportData.emoji,
            prefix: this.sportData.prefix
        });
    }

    /**
     * Obtient l'emoji du sport actuel
     */
    getEmoji() {
        return this.sportData?.emoji || this.defaultSport.emoji;
    }

    /**
     * Obtient le nom du sport
     */
    getName(short = false) {
        if (short) {
            return this.sportData?.name_short || this.sportData?.name || this.defaultSport.name_short;
        }
        return this.sportData?.name || this.defaultSport.name;
    }

    /**
     * Obtient le préfixe du sport (ex: VB, HB, BB)
     */
    getPrefix() {
        return this.sportData?.prefix || this.defaultSport.prefix;
    }

    /**
     * Obtient le type du sport
     */
    getType() {
        return this.sportData?.type || this.defaultSport.type;
    }

    /**
     * Obtient la durée d'un match
     */
    getMatchDuration() {
        return this.sportData?.duree_match_minutes || this.defaultSport.duree_match_minutes;
    }

    /**
     * Obtient le format de score (points ou sets)
     */
    getScoreFormat() {
        return this.sportData?.score_format || this.defaultSport.score_format;
    }

    /**
     * Obtient les niveaux disponibles
     */
    getNiveaux() {
        return this.sportData?.niveaux || this.defaultSport.niveaux;
    }

    /**
     * Obtient les genres disponibles
     */
    getGenres() {
        return this.sportData?.genres || this.defaultSport.genres;
    }

    /**
     * Vérifie si un code de poule correspond au sport actuel
     */
    isCurrentSport(pouleCode) {
        if (!pouleCode || typeof pouleCode !== 'string' || pouleCode.length < 2) {
            return false;
        }
        const prefix = pouleCode.substring(0, 2).toUpperCase();
        return prefix === this.getPrefix();
    }

    /**
     * Extrait le sport depuis un code de poule (ex: "VBFA1PA" -> "VB")
     */
    extractSportFromPoule(pouleCode) {
        if (!pouleCode || typeof pouleCode !== 'string' || pouleCode.length < 2) {
            return this.getPrefix();
        }
        return pouleCode.substring(0, 2).toUpperCase();
    }

    /**
     * Formate le titre de la page avec l'emoji du sport
     */
    updatePageTitle() {
        const emoji = this.getEmoji();
        const name = this.getName();
        document.title = `${emoji} PyCalendar FFSU - ${name}`;
    }

    /**
     * Obtient toutes les données du sport
     */
    getSportData() {
        return this.sportData || this.defaultSport;
    }
}

// Créer une instance globale
window.sportUtils = new SportUtils();
