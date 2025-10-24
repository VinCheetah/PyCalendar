/**
 * formatters.js - Utilitaires de formatage
 * 
 * Fonctions pour formater les dates, heures, textes, etc.
 * Exposé globalement via window.Formatters
 */

window.Formatters = {
    /**
     * Formate une date au format français
     */
    formatDate(date, format = 'short') {
        if (!date) return '-';
        
        const d = typeof date === 'string' ? new Date(date) : date;
        
        const options = {
            short: { day: '2-digit', month: '2-digit', year: 'numeric' },
            long: { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' },
            full: { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit' }
        };
        
        return new Intl.DateTimeFormat('fr-FR', options[format] || options.short).format(d);
    },

    /**
     * Formate une heure
     */
    formatTime(time) {
        if (!time) return '-';
        
        if (/^\d{2}:\d{2}$/.test(time)) {
            return time;
        }
        
        if (/^\d{2}:\d{2}:\d{2}$/.test(time)) {
            return time.substring(0, 5);
        }
        
        return time;
    },

    /**
     * Formate un jour de semaine
     */
    formatDay(day) {
        if (!day) return '-';
        
        return day.charAt(0).toUpperCase() + day.slice(1).toLowerCase();
    },

    /**
     * Formate un nom d'équipe
     */
    formatTeamName(name, maxLength = 30) {
        if (!name) return '-';
        
        if (name.length <= maxLength) {
            return name;
        }
        
        return name.substring(0, maxLength - 3) + '...';
    },

    /**
     * Formate un genre
     */
    formatGender(gender) {
        if (!gender) return '-';
        
        const g = gender.toUpperCase();
        
        if (g === 'M' || g.startsWith('MASC')) {
            return 'Masculin';
        }
        
        if (g === 'F' || g.startsWith('FÉM') || g.startsWith('FEM')) {
            return 'Féminin';
        }
        
        return gender;
    },

    /**
     * Formate un genre en version courte
     */
    formatGenderShort(gender) {
        if (!gender) return '-';
        
        const g = gender.toUpperCase();
        
        if (g === 'M' || g.startsWith('MASC')) {
            return 'M';
        }
        
        if (g === 'F' || g.startsWith('FÉM') || g.startsWith('FEM')) {
            return 'F';
        }
        
        return gender.charAt(0).toUpperCase();
    },

    /**
     * Formate un numéro de semaine
     */
    formatWeek(week) {
        if (week === null || week === undefined) return 'Non planifié';
        
        return `Semaine ${week}`;
    },

    /**
     * Formate un score de pénalités
     */
    formatPenalties(penalties, showPlus = false) {
        if (penalties === null || penalties === undefined || penalties === 0) {
            return '0';
        }
        
        const formatted = penalties.toFixed(1);
        
        if (penalties > 0 && showPlus) {
            return '+' + formatted;
        }
        
        return formatted;
    },

    /**
     * Formate un nombre avec séparateur de milliers
     */
    formatNumber(num) {
        if (num === null || num === undefined) return '0';
        
        return new Intl.NumberFormat('fr-FR').format(num);
    },

    /**
     * Formate une taille de fichier
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },

    /**
     * Formate un pourcentage
     */
    formatPercentage(value, isDecimal = true) {
        if (value === null || value === undefined) return '0%';
        
        const percent = isDecimal ? value * 100 : value;
        
        return `${percent.toFixed(1)}%`;
    },

    /**
     * Formate une durée en minutes
     */
    formatDuration(minutes) {
        if (!minutes) return '0min';
        
        const hours = Math.floor(minutes / 60);
        const mins = minutes % 60;
        
        if (hours === 0) {
            return `${mins}min`;
        }
        
        if (mins === 0) {
            return `${hours}h`;
        }
        
        return `${hours}h${mins.toString().padStart(2, '0')}`;
    },

    /**
     * Capitalise la première lettre
     */
    capitalize(str) {
        if (!str) return '';
        
        return str.charAt(0).toUpperCase() + str.slice(1);
    },

    /**
     * Tronque un texte
     */
    truncate(text, maxLength) {
        if (!text || text.length <= maxLength) {
            return text;
        }
        
        return text.substring(0, maxLength - 3) + '...';
    },

    /**
     * Pluralise un mot
     */
    pluralize(count, singular, plural = null) {
        if (count <= 1) {
            return `${count} ${singular}`;
        }
        
        const pluralForm = plural || (singular + 's');
        return `${count} ${pluralForm}`;
    }
};
