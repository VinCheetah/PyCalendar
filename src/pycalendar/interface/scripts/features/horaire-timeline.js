/**
 * Extension de EnhancedFilterSystem pour la timeline horaire interactive
 */

// Ajouter les méthodes à la classe EnhancedFilterSystem
(function() {
    if (typeof EnhancedFilterSystem === 'undefined') {
        console.error('❌ EnhancedFilterSystem doit être chargé avant horaire-timeline.js');
        return;
    }

    /**
     * Initialise la timeline interactive pour le filtre horaire
     */
    EnhancedFilterSystem.prototype.initHoraireTimeline = function() {
        if (!this.availableHoraires || this.availableHoraires.length === 0) {
            console.warn('⏰ Aucun horaire disponible pour la timeline');
            return;
        }
        
        // Limites min/max
        this.minMinutes = this.availableHoraires[0].minutes;
        this.maxMinutes = this.availableHoraires[this.availableHoraires.length - 1].minutes;
        
        // État initial: tout sélectionné
        this.horaireStart = this.minMinutes;
        this.horaireEnd = this.maxMinutes;
        
        // Créer les graduations
        const ticksContainer = document.getElementById('horaire-ticks');
        if (ticksContainer) {
            ticksContainer.innerHTML = '';
            // Afficher quelques horaires clés (début, milieu, fin)
            const tickIndices = [0, Math.floor(this.availableHoraires.length / 2), this.availableHoraires.length - 1];
            tickIndices.forEach(i => {
                const tick = document.createElement('span');
                tick.textContent = this.availableHoraires[i].time;
                tick.style.fontWeight = '600';
                ticksContainer.appendChild(tick);
            });
        }
        
        // Configurer les curseurs
        this.setupTimelineDragHandlers();
        
        // Mettre à jour l'affichage initial
        this.updateHoraireDisplay();
        
        console.log('⏰ Timeline horaire initialisée:', {
            min: this.availableHoraires[0].time,
            max: this.availableHoraires[this.availableHoraires.length - 1].time,
            count: this.availableHoraires.length
        });
    };

    /**
     * Configure les gestionnaires de drag pour les curseurs de la timeline
     */
    EnhancedFilterSystem.prototype.setupTimelineDragHandlers = function() {
        const cursorStart = document.getElementById('horaire-cursor-start');
        const cursorEnd = document.getElementById('horaire-cursor-end');
        const container = document.getElementById('horaire-timeline-container');
        const resetBtn = document.getElementById('horaire-reset');
        
        if (!cursorStart || !cursorEnd || !container) return;
        
        let draggedCursor = null;
        const self = this;
        
        const startDrag = (e, cursor) => {
            e.preventDefault();
            draggedCursor = cursor;
            cursor.style.cursor = 'grabbing';
            cursor.style.transform = 'translate(-50%, -50%) scale(1.2)';
            cursor.style.boxShadow = cursor.dataset.type === 'start' 
                ? '0 4px 12px rgba(59, 130, 246, 0.8)' 
                : '0 4px 12px rgba(239, 68, 68, 0.8)';
        };
        
        const doDrag = (e) => {
            if (!draggedCursor) return;
            
            const rect = container.getBoundingClientRect();
            const x = (e.type.includes('mouse') ? e.clientX : e.touches[0].clientX) - rect.left;
            const percent = Math.max(0, Math.min(100, (x / rect.width) * 100));
            
            // Convertir le pourcentage en minutes
            const minutes = self.minMinutes + (percent / 100) * (self.maxMinutes - self.minMinutes);
            
            // Trouver l'horaire le plus proche
            const closest = self.availableHoraires.reduce((prev, curr) => 
                Math.abs(curr.minutes - minutes) < Math.abs(prev.minutes - minutes) ? curr : prev
            );
            
            if (draggedCursor.dataset.type === 'start') {
                // Ne pas dépasser le curseur de fin
                if (closest.minutes <= self.horaireEnd) {
                    self.horaireStart = closest.minutes;
                }
            } else {
                // Ne pas descendre sous le curseur de début
                if (closest.minutes >= self.horaireStart) {
                    self.horaireEnd = closest.minutes;
                }
            }
            
            self.updateHoraireDisplay();
            self.apply();
        };
        
        const stopDrag = () => {
            if (draggedCursor) {
                draggedCursor.style.cursor = 'grab';
                draggedCursor.style.transform = 'translate(-50%, -50%) scale(1)';
                draggedCursor.style.boxShadow = draggedCursor.dataset.type === 'start'
                    ? '0 2px 8px rgba(59, 130, 246, 0.5)'
                    : '0 2px 8px rgba(239, 68, 68, 0.5)';
                draggedCursor = null;
            }
        };
        
        // Events pour le curseur de début
        cursorStart.addEventListener('mousedown', (e) => startDrag(e, cursorStart));
        cursorStart.addEventListener('touchstart', (e) => startDrag(e, cursorStart), { passive: false });
        
        // Events pour le curseur de fin
        cursorEnd.addEventListener('mousedown', (e) => startDrag(e, cursorEnd));
        cursorEnd.addEventListener('touchstart', (e) => startDrag(e, cursorEnd), { passive: false });
        
        // Events globaux pour le drag
        document.addEventListener('mousemove', doDrag);
        document.addEventListener('touchmove', doDrag, { passive: false });
        document.addEventListener('mouseup', stopDrag);
        document.addEventListener('touchend', stopDrag);
        
        // Bouton reset
        if (resetBtn) {
            resetBtn.addEventListener('click', () => {
                self.horaireStart = self.minMinutes;
                self.horaireEnd = self.maxMinutes;
                self.updateHoraireDisplay();
                self.apply();
            });
        }
    };

    /**
     * Met à jour l'affichage visuel de la timeline
     */
    EnhancedFilterSystem.prototype.updateHoraireDisplay = function() {
        if (!this.availableHoraires || this.availableHoraires.length === 0) return;
        
        // Convertir les minutes en pourcentages
        const startPercent = ((this.horaireStart - this.minMinutes) / (this.maxMinutes - this.minMinutes)) * 100;
        const endPercent = ((this.horaireEnd - this.minMinutes) / (this.maxMinutes - this.minMinutes)) * 100;
        
        // Trouver les horaires correspondants
        const startTime = this.availableHoraires.find(h => h.minutes === this.horaireStart)?.time || '--:--';
        const endTime = this.availableHoraires.find(h => h.minutes === this.horaireEnd)?.time || '--:--';
        
        // Mettre à jour les labels
        const startLabel = document.getElementById('horaire-start-label');
        const endLabel = document.getElementById('horaire-end-label');
        if (startLabel) startLabel.innerHTML = `<strong>Début:</strong> ${startTime}`;
        if (endLabel) endLabel.innerHTML = `<strong>Fin:</strong> ${endTime}`;
        
        // Mettre à jour les positions des curseurs
        const cursorStart = document.getElementById('horaire-cursor-start');
        const cursorEnd = document.getElementById('horaire-cursor-end');
        if (cursorStart) cursorStart.style.left = `${startPercent}%`;
        if (cursorEnd) cursorEnd.style.left = `${endPercent}%`;
        
        // Mettre à jour la zone active
        const activeRange = document.getElementById('horaire-active-range');
        if (activeRange) {
            activeRange.style.left = `${startPercent}%`;
            activeRange.style.width = `${endPercent - startPercent}%`;
        }
        
        // Mettre à jour les filtres - TOUJOURS actifs (même avec plage complète)
        this.filters.horaireStart = startTime;
        this.filters.horaireEnd = endTime;
        
        console.log('⏰ Timeline mise à jour:', {
            startTime,
            endTime,
            isFullRange: this.horaireStart === this.minMinutes && this.horaireEnd === this.maxMinutes
        });
    };

    console.log('⏰ Extension horaire-timeline.js chargée');
})();
