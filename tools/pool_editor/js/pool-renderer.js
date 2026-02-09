/**
 * PyCalendar Pool Editor - Pool Renderer
 * Renders pools and teams to the DOM
 */

class PoolRenderer {
    constructor() {
        this.filters = {
            institution: 'all',
            time: 'all',
            level: 'all'
        };
        this.viewMode = 'pools'; // 'pools' or 'list'
    }
    
    /**
     * Set the view mode
     */
    setViewMode(mode) {
        this.viewMode = mode;
        this.updateViewVisibility();
        this.render();
    }
    
    /**
     * Update visibility of view containers
     */
    updateViewVisibility() {
        const poolsView = document.getElementById('unassigned-section');
        const feminineSection = document.getElementById('feminine-section');
        const masculineSection = document.getElementById('masculine-section');
        const listView = document.getElementById('list-view-container');
        
        if (this.viewMode === 'pools') {
            if (poolsView) poolsView.style.display = '';
            if (feminineSection) feminineSection.style.display = '';
            if (masculineSection) masculineSection.style.display = '';
            if (listView) listView.style.display = 'none';
        } else {
            if (poolsView) poolsView.style.display = 'none';
            if (feminineSection) feminineSection.style.display = 'none';
            if (masculineSection) masculineSection.style.display = 'none';
            if (listView) listView.style.display = '';
        }
    }
    
    /**
     * Set a filter
     */
    setFilter(filterName, value) {
        this.filters[filterName] = value;
        this.render();
    }
    
    /**
     * Clear all filters
     */
    clearFilters() {
        this.filters = {
            institution: 'all',
            time: 'all',
            level: 'all'
        };
        this.render();
    }
    
    /**
     * Initialize renderer
     */
    init() {
        dragDropManager.init();
    }
    
    /**
     * Render everything
     */
    render() {
        if (this.viewMode === 'pools') {
            this.renderUnassignedTeams();
            this.renderPools();
        } else {
            this.renderListView();
        }
        this.renderLegend();
        this.updateStats();
        statistics.update();
    }
    
    /**
     * Render unassigned teams
     */
    renderUnassignedTeams() {
        const unassigned = dataManager.getUnassignedTeams();
        const grouped = Utils.groupTeamsByGenderAndLevel(unassigned);
        
        // Reset drop zones
        dragDropManager.reset();
        
        Utils.GENDERS.forEach(gender => {
            Utils.LEVELS.forEach(level => {
                const container = document.querySelector(
                    `.teams-dropzone[data-gender="${gender}"][data-level="${level}"]`
                );
                
                if (!container) return;
                
                // Clear
                container.innerHTML = '';
                
                const teams = grouped[gender][level] || [];
                
                // Add empty class
                container.classList.toggle('empty', teams.length === 0);
                
                // Render teams
                teams.forEach(team => {
                    const card = this.createTeamCard(team, true);
                    container.appendChild(card);
                });
                
                // Make drop zone
                dragDropManager.makeDropZone(container, null, {
                    isUnassigned: true,
                    gender,
                    level
                });
            });
        });
        
        // Update count
        const countEl = document.getElementById('unassigned-count');
        if (countEl) {
            countEl.textContent = unassigned.length;
        }
    }
    
    /**
     * Render pools organized by gender and level
     */
    renderPools() {
        const pools = dataManager.getPools();
        
        // Organize pools by gender and level
        const organized = {};
        Utils.GENDERS.forEach(gender => {
            organized[gender] = {};
            Utils.LEVELS.forEach(level => {
                organized[gender][level] = [];
            });
        });
        
        pools.forEach(pool => {
            if (organized[pool.gender] && organized[pool.gender][pool.level]) {
                organized[pool.gender][pool.level].push(pool);
            }
        });
        
        // Render each column
        Utils.GENDERS.forEach(gender => {
            Utils.LEVELS.forEach(level => {
                const container = document.getElementById(`pools-${gender}-${level}`);
                if (!container) return;
                
                // Clear
                container.innerHTML = '';
                
                // Sort and render pools
                const levelPools = Utils.sortPools(organized[gender][level]);
                
                levelPools.forEach(pool => {
                    const poolCard = this.createPoolCard(pool);
                    container.appendChild(poolCard);
                });
                
                // Add "add pool" button
                const addBtn = Utils.createElement('button', {
                    className: 'add-pool-btn',
                    onClick: () => poolEditor.openModal(null, gender, level)
                }, ['➕ Ajouter une poule']);
                
                container.appendChild(addBtn);
            });
        });
        
        // Update counts
        const femPools = pools.filter(p => p.gender === 'F').length;
        const masPools = pools.filter(p => p.gender === 'M').length;
        
        document.getElementById('feminine-count').textContent = femPools;
        document.getElementById('masculine-count').textContent = masPools;
    }
    
    /**
     * Create pool card
     */
    createPoolCard(pool) {
        // Always use getPoolTeams to have a single source of truth based on team.poule
        const teams = dataManager.getPoolTeams(pool.id);
        const isAR = pool.type === 'aller-retour';
        const matchCount = Utils.calculateMatches(teams.length, isAR);
        
        const card = Utils.createElement('div', {
            className: `pool-card ${pool.gender === 'F' ? 'feminine' : 'masculine'}`,
            dataPoolId: pool.id
        });
        
        // Check if pool is filtered
        if (this.isPoolFiltered(pool, teams)) {
            card.classList.add('filtered-out');
        }
        
        // Header
        const header = Utils.createElement('div', {
            className: 'pool-header',
            onClick: () => poolEditor.openModal(pool)
        });
        
        const poolName = Utils.createElement('div', { className: 'pool-name' }, [
            Utils.createElement('code', {}, [pool.name])
        ]);
        
        if (isAR) {
            poolName.appendChild(Utils.createElement('span', { className: 'type-badge' }, ['AR']));
        }
        
        const poolInfo = Utils.createElement('div', { className: 'pool-info' });
        poolInfo.appendChild(Utils.createElement('span', { className: 'pool-count' }, [`${teams.length} équipes`]));
        poolInfo.appendChild(Utils.createElement('span', { className: 'pool-matches' }, [`${matchCount} matchs`]));
        
        // Actions
        const actions = Utils.createElement('div', { className: 'pool-actions' });
        actions.appendChild(Utils.createElement('button', {
            title: 'Modifier',
            onClick: (e) => {
                e.stopPropagation();
                poolEditor.openModal(pool);
            }
        }, ['✏️']));
        actions.appendChild(Utils.createElement('button', {
            title: 'Supprimer',
            onClick: (e) => {
                e.stopPropagation();
                poolEditor.confirmDelete(pool);
            }
        }, ['🗑️']));
        
        header.appendChild(poolName);
        header.appendChild(poolInfo);
        header.appendChild(actions);
        card.appendChild(header);
        
        // Body (teams)
        const body = Utils.createElement('div', {
            className: 'pool-body',
            dataPoolId: pool.id
        });
        
        body.classList.toggle('empty', teams.length === 0);
        
        // Sort and render teams
        const sortedTeams = Utils.sortTeams(teams);
        sortedTeams.forEach(team => {
            const teamCard = this.createTeamCard(team);
            body.appendChild(teamCard);
        });
        
        // Make body a drop zone with pool info for level change detection
        dragDropManager.makeDropZone(body, pool.id, {
            isUnassigned: false,
            gender: pool.gender,
            level: pool.level
        });
        
        card.appendChild(body);
        
        // Stats footer
        if (teams.length >= 2) {
            const timeDistrib = Utils.calculateTimeDistribution(teams, isAR);
            const statsFooter = Utils.createElement('div', { className: 'pool-stats' });
            
            Utils.TIMES.forEach(time => {
                if (timeDistrib[time] > 0) {
                    statsFooter.appendChild(Utils.createElement('div', { className: 'pool-stat' }, [
                        Utils.createElement('span', { className: 'pool-stat-icon' }, [Utils.TIME_ICONS[time]]),
                        Utils.createElement('span', { className: 'pool-stat-value' }, [timeDistrib[time].toString()])
                    ]));
                }
            });
            
            if (statsFooter.children.length > 0) {
                card.appendChild(statsFooter);
            }
        }
        
        return card;
    }
    
    /**
     * Create team card
     * Compact single-line display: Name + Time badge + Amenage indicator
     */
    createTeamCard(team, compact = false) {
        const instColor = Utils.getInstitutionColor(team.institution);
        
        const card = Utils.createElement('div', {
            className: 'team-card',
            dataTeamId: team.id
        });
        
        // Set institution color
        if (instColor) {
            card.style.setProperty('--institution-color', instColor);
            card.setAttribute('data-institution-color', 'true');
        }
        
        // Check if team has amenaged schedule - add visual indicator
        const hasAmenage = team.horaireAmenage && team.gymnasesAmenages && team.gymnasesAmenages.length > 0;
        if (hasAmenage) {
            card.classList.add('has-amenaged-schedule');
            card.setAttribute('title', `Horaire aménagé: ${team.horaireAmenage} sur ${team.gymnasesAmenages.join(', ')}`);
        }
        
        // Check if team is filtered - add dimmed class instead of filtered-out
        const isFiltered = this.isTeamFiltered(team);
        if (isFiltered) {
            card.classList.add('filtered-dimmed');
        } else if (this.hasActiveFilters()) {
            card.classList.add('filtered-highlight');
        }
        
        // Content - single line: name + time badge + amenage indicator
        const content = Utils.createElement('div', { className: 'team-content team-content-inline' });
        
        // Team name
        content.appendChild(Utils.createElement('span', { className: 'team-name' }, [team.nom]));
        
        // Time badge - always show inline
        const timeClass = `time-badge time-${team.horaire?.replace('H', '').replace(':', '')}`;
        content.appendChild(Utils.createElement('span', { className: timeClass }, [
            Utils.TIME_ICONS[team.horaire] || '',
            team.horaire || '14H'
        ]));
        
        // Amenaged schedule badge - signe visible et clair
        if (hasAmenage) {
            const amenageBadge = Utils.createElement('span', { 
                className: 'team-badge-amenage',
                title: `⏰ Horaire aménagé: peut jouer à ${team.horaireAmenage} sur ${team.gymnasesAmenages.join(', ')}`
            }, [`⏰ ${team.horaireAmenage}`]);
            content.appendChild(amenageBadge);
        }
        
        card.appendChild(content);
        
        // Actions (only visible on hover)
        const actions = Utils.createElement('div', { className: 'team-actions' });
        
        actions.appendChild(Utils.createElement('button', {
            title: 'Modifier',
            onClick: (e) => {
                e.stopPropagation();
                teamEditor.openModal(team);
            }
        }, ['✏️']));
        
        actions.appendChild(Utils.createElement('button', {
            className: 'btn-delete',
            title: 'Supprimer',
            onClick: (e) => {
                e.stopPropagation();
                teamEditor.confirmDelete(team);
            }
        }, ['🗑️']));
        
        card.appendChild(actions);
        
        // Make draggable
        dragDropManager.makeDraggable(card, team);
        
        // Double-click to edit
        card.addEventListener('dblclick', () => teamEditor.openModal(team));
        
        return card;
    }
    
    /**
     * Check if any filter is active
     */
    hasActiveFilters() {
        return this.filters.institution !== 'all' 
            || this.filters.time !== 'all' 
            || this.filters.level !== 'all';
    }
    
    /**
     * Render institution legend
     */
    renderLegend() {
        const panel = document.getElementById('legend-panel');
        if (!panel) return;
        
        const institutions = dataManager.getInstitutions();
        
        if (institutions.length === 0) {
            panel.innerHTML = '<p class="empty-message">Aucune institution</p>';
            return;
        }
        
        // Count teams per institution
        const counts = {};
        dataManager.getTeams().forEach(team => {
            if (team.institution) {
                counts[team.institution] = (counts[team.institution] || 0) + 1;
            }
        });
        
        // Sort by count
        institutions.sort((a, b) => (counts[b] || 0) - (counts[a] || 0));
        
        panel.innerHTML = '';
        
        institutions.forEach(inst => {
            const color = Utils.getInstitutionColor(inst);
            const isFiltered = this.filters.institution !== 'all' && this.filters.institution !== inst;
            
            const item = Utils.createElement('div', {
                className: `legend-item ${isFiltered ? 'filtered' : ''}`,
                onClick: () => this.toggleInstitutionFilter(inst)
            });
            
            item.appendChild(Utils.createElement('div', {
                className: 'legend-color',
                style: { backgroundColor: color }
            }));
            
            item.appendChild(Utils.createElement('span', { className: 'legend-name' }, [inst]));
            item.appendChild(Utils.createElement('span', { className: 'legend-count' }, [counts[inst]?.toString() || '0']));
            
            panel.appendChild(item);
        });
    }
    
    /**
     * Update global stats
     */
    updateStats() {
        const teams = dataManager.getTeams();
        const pools = dataManager.getPools();
        
        document.getElementById('stat-teams').textContent = teams.length;
        document.getElementById('stat-pools').textContent = pools.length;
        document.getElementById('stat-female').textContent = teams.filter(t => t.genre === 'F').length;
        document.getElementById('stat-male').textContent = teams.filter(t => t.genre === 'M').length;
        
        // Total matches - update both possible IDs
        let totalMatches = 0;
        pools.forEach(pool => {
            const poolTeams = dataManager.getPoolTeams(pool.id);
            const isAR = pool.type === 'aller-retour';
            totalMatches += Utils.calculateMatches(poolTeams.length, isAR);
        });
        
        // Try both possible element IDs
        const matchesEl = document.getElementById('stat-total-matches') || document.getElementById('stat-matches');
        if (matchesEl) matchesEl.textContent = totalMatches;
        
        // Update change indicator
        const changeCount = dataManager.getChangeCount();
        const indicator = document.getElementById('unsaved-indicator');
        if (indicator) {
            indicator.style.display = changeCount > 0 ? 'flex' : 'none';
            document.getElementById('stat-changes').textContent = changeCount;
        }
    }
    
    // ==================== Filtering ====================
    
    /**
     * Set filter
     */
    setFilter(type, value) {
        this.filters[type] = value;
        this.render();
    }
    
    /**
     * Toggle institution filter from legend
     */
    toggleInstitutionFilter(institution) {
        if (this.filters.institution === institution) {
            this.filters.institution = 'all';
            document.getElementById('filter-institution').value = 'all';
        } else {
            this.filters.institution = institution;
            // Update dropdown if value exists
            const select = document.getElementById('filter-institution');
            if ([...select.options].some(o => o.value === institution)) {
                select.value = institution;
            }
        }
        this.render();
    }
    
    /**
     * Clear all filters
     */
    clearFilters() {
        this.filters = {
            institution: 'all',
            time: 'all',
            level: 'all'
        };
        
        document.getElementById('filter-institution').value = 'all';
        document.getElementById('filter-time').value = 'all';
        document.getElementById('filter-level').value = 'all';
        
        this.render();
    }
    
    /**
     * Check if team is filtered out
     */
    isTeamFiltered(team) {
        if (this.filters.institution !== 'all' && team.institution !== this.filters.institution) {
            return true;
        }
        if (this.filters.time !== 'all' && team.horaire !== this.filters.time) {
            return true;
        }
        if (this.filters.level !== 'all' && team.niveau !== this.filters.level) {
            return true;
        }
        return false;
    }
    
    /**
     * Check if pool is filtered out (all teams filtered)
     */
    isPoolFiltered(pool, teams) {
        if (this.filters.level !== 'all' && pool.level !== this.filters.level) {
            return true;
        }
        if (!teams || teams.length === 0) return false;
        return teams.every(team => this.isTeamFiltered(team));
    }
    
    /**
     * Populate institution filter dropdown
     */
    populateInstitutionFilter() {
        const select = document.getElementById('filter-institution');
        if (!select) return;
        
        // Clear all except first
        while (select.children.length > 1) {
            select.removeChild(select.lastChild);
        }
        
        const institutions = dataManager.getInstitutions();
        institutions.forEach(inst => {
            select.appendChild(Utils.createElement('option', { value: inst }, [inst]));
        });
    }
    
    /**
     * Render list view - teams organized by gender/level, sorted by time then institution
     */
    renderListView() {
        const teams = dataManager.getTeams();
        
        // Group teams by gender and level
        const grouped = {};
        Utils.GENDERS.forEach(gender => {
            grouped[gender] = {};
            Utils.LEVELS.forEach(level => {
                grouped[gender][level] = [];
            });
        });
        
        teams.forEach(team => {
            const gender = team.genre || 'M';
            const level = team.niveau || 'A1';
            if (grouped[gender] && grouped[gender][level]) {
                grouped[gender][level].push(team);
            }
        });
        
        // Render each section
        let feminineTotal = 0;
        let masculineTotal = 0;
        
        Utils.GENDERS.forEach(gender => {
            Utils.LEVELS.forEach(level => {
                const container = document.getElementById(`list-${gender}-${level}`);
                if (!container) return;
                
                // Clear
                container.innerHTML = '';
                
                // Sort teams by time (order: 14H, 16H, 18H, 20H), then by institution
                const timeOrder = { '14H': 0, '16H': 1, '18H': 2, '20H': 3 };
                const levelTeams = grouped[gender][level].sort((a, b) => {
                    const timeA = timeOrder[a.horaire] ?? 0;
                    const timeB = timeOrder[b.horaire] ?? 0;
                    if (timeA !== timeB) return timeA - timeB;
                    return (a.institution || '').localeCompare(b.institution || '');
                });
                
                // Render teams
                levelTeams.forEach(team => {
                    const card = this.createListTeamCard(team);
                    container.appendChild(card);
                });
                
                // Update count in title
                const countSpan = container.closest('.list-level-section')?.querySelector('.list-level-count');
                if (countSpan) {
                    countSpan.textContent = `(${levelTeams.length} équipes)`;
                }
                
                if (gender === 'F') feminineTotal += levelTeams.length;
                else masculineTotal += levelTeams.length;
            });
        });
        
        // Update section counts
        const femCount = document.getElementById('feminine-list-count');
        const masCount = document.getElementById('masculine-list-count');
        if (femCount) femCount.textContent = feminineTotal;
        if (masCount) masCount.textContent = masculineTotal;
    }
    
    /**
     * Create a team card for list view
     */
    createListTeamCard(team) {
        const instColor = Utils.getInstitutionColor(team.institution);
        const pool = team.poule ? dataManager.getPool(team.poule) : null;
        
        const card = Utils.createElement('div', {
            className: 'list-team-card',
            dataTeamId: team.id
        });
        
        // Set institution color
        if (instColor) {
            card.style.setProperty('--institution-color', instColor);
            card.setAttribute('data-institution-color', 'true');
        }
        
        // Check if team is filtered
        const isFiltered = this.isTeamFiltered(team);
        if (isFiltered) {
            card.classList.add('filtered-dimmed');
        } else if (this.hasActiveFilters()) {
            card.classList.add('filtered-highlight');
        }
        
        // Time badge
        const timeClass = `list-team-time time-${team.horaire?.replace('H', '')}`;
        card.appendChild(Utils.createElement('span', { className: timeClass }, [
            Utils.TIME_ICONS[team.horaire] || '',
            ' ',
            team.horaire || '14H'
        ]));
        
        // Team name
        card.appendChild(Utils.createElement('span', { className: 'list-team-name' }, [team.nom]));
        
        // Institution badge (if different from name)
        if (team.institution && team.institution !== team.nom) {
            card.appendChild(Utils.createElement('span', { className: 'list-team-institution' }, [team.institution]));
        }
        
        // Pool badge
        if (pool) {
            card.appendChild(Utils.createElement('span', { className: 'list-team-pool' }, [pool.name]));
        } else {
            card.appendChild(Utils.createElement('span', { className: 'list-team-pool unassigned' }, ['Non assignée']));
        }
        
        // Actions
        const actions = Utils.createElement('div', { className: 'list-team-actions' });
        
        actions.appendChild(Utils.createElement('button', {
            title: 'Modifier',
            onClick: (e) => {
                e.stopPropagation();
                teamEditor.openModal(team);
            }
        }, ['✏️']));
        
        actions.appendChild(Utils.createElement('button', {
            className: 'btn-delete',
            title: 'Supprimer',
            onClick: (e) => {
                e.stopPropagation();
                teamEditor.confirmDelete(team);
            }
        }, ['🗑️']));
        
        card.appendChild(actions);
        
        // Double-click to edit
        card.addEventListener('dblclick', () => teamEditor.openModal(team));
        
        return card;
    }
}

// Create global instance
window.poolRenderer = new PoolRenderer();
