"""HTML calendar visualizer."""

import json
from pathlib import Path
from typing import Dict, List
from core.models import Solution, Match
from collections import defaultdict


class HTMLVisualizer:
    """Generate interactive HTML visualization of the calendar."""
    
    TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PyCalendar - Visualisation</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }
        
        .stats {
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-top: 20px;
            flex-wrap: wrap;
        }
        
        .stat-card {
            background: rgba(255,255,255,0.2);
            padding: 15px 30px;
            border-radius: 10px;
            backdrop-filter: blur(10px);
        }
        
        .stat-value {
            font-size: 2em;
            font-weight: bold;
        }
        
        .stat-label {
            font-size: 0.9em;
            opacity: 0.9;
            margin-top: 5px;
        }
        
        .controls {
            padding: 20px 30px;
            background: #f8f9fa;
            border-bottom: 2px solid #e9ecef;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            align-items: center;
        }
        
        .control-group {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .control-group label {
            font-weight: 600;
            color: #495057;
        }
        
        select, input {
            padding: 8px 15px;
            border: 2px solid #dee2e6;
            border-radius: 8px;
            font-size: 14px;
            transition: all 0.3s;
        }
        
        select:hover, input:hover {
            border-color: #667eea;
        }
        
        select:focus, input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        button {
            padding: 8px 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        
        button:active {
            transform: translateY(0);
        }
        
        .content {
            padding: 30px;
        }
        
        .view-tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            border-bottom: 2px solid #e9ecef;
        }
        
        .tab {
            padding: 12px 25px;
            cursor: pointer;
            border: none;
            background: transparent;
            color: #6c757d;
            font-weight: 600;
            border-bottom: 3px solid transparent;
            transition: all 0.3s;
        }
        
        .tab:hover {
            color: #667eea;
        }
        
        .tab.active {
            color: #667eea;
            border-bottom-color: #667eea;
        }
        
        .view-content {
            display: none;
        }
        
        .view-content.active {
            display: block;
        }
        
        .week-container {
            margin-bottom: 30px;
        }
        
        .week-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            border-radius: 10px 10px 0 0;
            font-size: 1.3em;
            font-weight: bold;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .week-info {
            font-size: 0.8em;
            opacity: 0.9;
        }
        
        .matches-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 15px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 0 0 10px 10px;
        }
        
        .match-card {
            background: white;
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
            border-left: 4px solid #667eea;
        }
        
        .match-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 5px 20px rgba(0,0,0,0.15);
        }
        
        .match-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            padding-bottom: 10px;
            border-bottom: 1px solid #e9ecef;
        }
        
        .match-poule {
            background: #667eea;
            color: white;
            padding: 4px 10px;
            border-radius: 15px;
            font-size: 0.85em;
            font-weight: 600;
        }
        
        .match-time {
            color: #6c757d;
            font-size: 0.9em;
            font-weight: 600;
        }
        
        .match-teams {
            font-size: 1.1em;
            margin: 10px 0;
            text-align: center;
        }
        
        .team {
            font-weight: 600;
            color: #495057;
            transition: all 0.3s;
        }
        
        .team.highlighted {
            color: #667eea;
            background: rgba(102, 126, 234, 0.1);
            padding: 4px 8px;
            border-radius: 5px;
            font-weight: 700;
        }
        
        .vs {
            color: #667eea;
            font-weight: bold;
            margin: 0 10px;
        }
        
        .match-venue {
            text-align: center;
            color: #6c757d;
            font-size: 0.9em;
            margin-top: 10px;
        }
        
        .venue-icon {
            margin-right: 5px;
        }
        
        .timeline-container {
            position: relative;
            padding: 20px 0;
        }
        
        .timeline-week {
            margin-bottom: 40px;
            position: relative;
            padding-left: 120px;
        }
        
        .timeline-marker {
            position: absolute;
            left: 0;
            top: 0;
            width: 100px;
            height: 100px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-direction: column;
            color: white;
            font-weight: bold;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }
        
        .timeline-week-num {
            font-size: 2em;
        }
        
        .timeline-week-label {
            font-size: 0.7em;
            opacity: 0.9;
        }
        
        .timeline-content {
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            border-left: 4px solid #667eea;
        }
        
        .timeline-matches {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 10px;
            margin-top: 10px;
        }
        
        .timeline-match {
            padding: 10px;
            background: #f8f9fa;
            border-radius: 8px;
            font-size: 0.9em;
        }
        
        .venue-section {
            margin-bottom: 30px;
        }
        
        .venue-header {
            background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
            color: white;
            padding: 15px 20px;
            border-radius: 10px 10px 0 0;
            font-size: 1.2em;
            font-weight: bold;
        }
        
        .venue-schedule {
            background: white;
            border-radius: 0 0 10px 10px;
            overflow: hidden;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        
        .time-slot {
            display: flex;
            border-bottom: 1px solid #e9ecef;
        }
        
        .time-slot:last-child {
            border-bottom: none;
        }
        
        .time-label {
            width: 120px;
            padding: 15px;
            background: #f8f9fa;
            font-weight: 600;
            color: #495057;
            display: flex;
            align-items: center;
            border-right: 2px solid #e9ecef;
        }
        
        .time-matches {
            flex: 1;
            padding: 15px;
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }
        
        .mini-match {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 8px 15px;
            border-radius: 8px;
            font-size: 0.85em;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        
        .empty-slot {
            color: #adb5bd;
            font-style: italic;
        }
        
        .pool-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
            gap: 20px;
        }
        
        .pool-card {
            background: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        
        .pool-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            font-size: 1.3em;
            font-weight: bold;
            text-align: center;
        }
        
        .pool-matches {
            padding: 20px;
        }
        
        .pool-match {
            padding: 12px;
            margin-bottom: 10px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 3px solid #667eea;
        }
        
        .pool-match:last-child {
            margin-bottom: 0;
        }
        
        .no-matches {
            text-align: center;
            padding: 60px 20px;
            color: #6c757d;
            font-size: 1.2em;
        }
        
        .no-matches-icon {
            font-size: 3em;
            margin-bottom: 15px;
        }
        
        .filter-info {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 15px;
            display: none;
        }
        
        .filter-info.active {
            display: block;
        }
        
        .filter-info h3 {
            margin-bottom: 10px;
            font-size: 1.5em;
        }
        
        .filter-stats {
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            margin-top: 15px;
        }
        
        .filter-stat {
            background: rgba(255, 255, 255, 0.2);
            padding: 10px 20px;
            border-radius: 8px;
            backdrop-filter: blur(10px);
        }
        
        .filter-stat-value {
            font-size: 1.8em;
            font-weight: bold;
        }
        
        .filter-stat-label {
            font-size: 0.85em;
            opacity: 0.9;
        }
        
        @media (max-width: 768px) {
            .matches-grid {
                grid-template-columns: 1fr;
            }
            
            .pool-grid {
                grid-template-columns: 1fr;
            }
            
            .timeline-week {
                padding-left: 80px;
            }
            
            .timeline-marker {
                width: 60px;
                height: 60px;
            }
            
            .timeline-week-num {
                font-size: 1.5em;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🏐 PyCalendar - Calendrier Sportif</h1>
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-value" id="totalMatches">0</div>
                    <div class="stat-label">Matchs planifiés</div>
                </div>
                <div class="stat-card" style="border-left-color: #ff6b6b;">
                    <div class="stat-value" id="totalUnscheduled">0</div>
                    <div class="stat-label">Non planifiés</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="totalWeeks">0</div>
                    <div class="stat-label">Semaines</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="totalPools">0</div>
                    <div class="stat-label">Poules</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="totalVenues">0</div>
                    <div class="stat-label">Gymnases</div>
                </div>
            </div>
        </header>
        
        <div class="controls">
            <div class="control-group">
                <label>🏛️ Institution:</label>
                <select id="filterInstitution">
                    <option value="">Toutes les institutions</option>
                </select>
            </div>
            <div class="control-group">
                <label>👥 Équipe:</label>
                <select id="filterTeam">
                    <option value="">Toutes les équipes</option>
                </select>
            </div>
            <div class="control-group">
                <label>🎯 Poule:</label>
                <select id="filterPool">
                    <option value="">Toutes les poules</option>
                </select>
            </div>
            <div class="control-group">
                <label>🏢 Gymnase:</label>
                <select id="filterVenue">
                    <option value="">Tous les gymnases</option>
                </select>
            </div>
            <div class="control-group">
                <label>📅 Semaine:</label>
                <select id="filterWeek">
                    <option value="">Toutes les semaines</option>
                </select>
            </div>
            <button onclick="resetFilters()">🔄 Réinitialiser</button>
        </div>
        
        <div class="content">
            <div id="filterInfo" class="filter-info"></div>
            
            <div class="view-tabs">
                <button class="tab active" onclick="switchView('calendar')">📅 Calendrier</button>
                <button class="tab" onclick="switchView('timeline')">📊 Timeline</button>
                <button class="tab" onclick="switchView('venues')">🏢 Par Gymnase</button>
                <button class="tab" onclick="switchView('pools')">🎯 Par Poule</button>
                <button class="tab" onclick="switchView('unscheduled')">⚠️ Non Planifiés</button>
            </div>
            
            <div id="calendarView" class="view-content active"></div>
            <div id="timelineView" class="view-content"></div>
            <div id="venuesView" class="view-content"></div>
            <div id="poolsView" class="view-content"></div>
            <div id="unscheduledView" class="view-content"></div>
        </div>
    </div>
    
    <script>
        const matchsData = {{MATCHES_DATA}};
        const unscheduledData = {{UNSCHEDULED_DATA}};
        let currentFilters = { institution: '', team: '', pool: '', venue: '', week: '' };
        
        function initializeData() {
            const stats = calculateStats(matchsData);
            document.getElementById('totalMatches').textContent = stats.totalMatches;
            document.getElementById('totalUnscheduled').textContent = unscheduledData.length;
            document.getElementById('totalWeeks').textContent = stats.totalWeeks;
            document.getElementById('totalPools').textContent = stats.totalPools;
            document.getElementById('totalVenues').textContent = stats.totalVenues;
            
            populateFilters(stats);
            renderAllViews();
        }
        
        function calculateStats(matches) {
            const weeks = new Set();
            const pools = new Set();
            const venues = new Set();
            const institutions = new Set();
            const teams = new Set();
            
            matches.forEach(match => {
                weeks.add(match.semaine);
                pools.add(match.poule);
                venues.add(match.gymnase);
                institutions.add(match.institution1);
                institutions.add(match.institution2);
                teams.add(match.equipe1);
                teams.add(match.equipe2);
            });
            
            return {
                totalMatches: matches.length,
                totalWeeks: weeks.size,
                totalPools: pools.size,
                totalVenues: venues.size,
                weeks: Array.from(weeks).sort((a, b) => a - b),
                pools: Array.from(pools).sort(),
                venues: Array.from(venues).sort(),
                institutions: Array.from(institutions).sort(),
                teams: Array.from(teams).sort()
            };
        }
        
        function populateFilters(stats) {
            const institutionSelect = document.getElementById('filterInstitution');
            stats.institutions.forEach(institution => {
                const option = document.createElement('option');
                option.value = institution;
                option.textContent = institution;
                institutionSelect.appendChild(option);
            });
            
            const teamSelect = document.getElementById('filterTeam');
            stats.teams.forEach(team => {
                const option = document.createElement('option');
                option.value = team;
                option.textContent = team;
                teamSelect.appendChild(option);
            });
            
            const poolSelect = document.getElementById('filterPool');
            stats.pools.forEach(pool => {
                const option = document.createElement('option');
                option.value = pool;
                option.textContent = `Poule ${pool}`;
                poolSelect.appendChild(option);
            });
            
            const venueSelect = document.getElementById('filterVenue');
            stats.venues.forEach(venue => {
                const option = document.createElement('option');
                option.value = venue;
                option.textContent = venue;
                venueSelect.appendChild(option);
            });
            
            const weekSelect = document.getElementById('filterWeek');
            stats.weeks.forEach(week => {
                const option = document.createElement('option');
                option.value = week;
                option.textContent = `Semaine ${week}`;
                weekSelect.appendChild(option);
            });
            
            institutionSelect.addEventListener('change', (e) => {
                currentFilters.institution = e.target.value;
                updateTeamFilter(stats);
                renderAllViews();
            });
            
            teamSelect.addEventListener('change', (e) => {
                currentFilters.team = e.target.value;
                renderAllViews();
            });
            
            poolSelect.addEventListener('change', (e) => {
                currentFilters.pool = e.target.value;
                renderAllViews();
            });
            
            venueSelect.addEventListener('change', (e) => {
                currentFilters.venue = e.target.value;
                renderAllViews();
            });
            
            weekSelect.addEventListener('change', (e) => {
                currentFilters.week = e.target.value;
                renderAllViews();
            });
        }
        
        function updateTeamFilter(stats) {
            const teamSelect = document.getElementById('filterTeam');
            const selectedTeam = currentFilters.team;
            
            // Clear team filter
            teamSelect.innerHTML = '<option value="">Toutes les équipes</option>';
            
            // Filter teams by institution if one is selected
            let filteredTeams = stats.teams;
            if (currentFilters.institution) {
                filteredTeams = matchsData
                    .filter(m => m.institution1 === currentFilters.institution || m.institution2 === currentFilters.institution)
                    .flatMap(m => [m.equipe1, m.equipe2])
                    .filter((team, index, self) => self.indexOf(team) === index && 
                            team.startsWith(currentFilters.institution))
                    .sort();
            }
            
            filteredTeams.forEach(team => {
                const option = document.createElement('option');
                option.value = team;
                option.textContent = team;
                if (team === selectedTeam) option.selected = true;
                teamSelect.appendChild(option);
            });
            
            // Reset team filter if it's not in the new list
            if (currentFilters.team && !filteredTeams.includes(currentFilters.team)) {
                currentFilters.team = '';
            }
        }
        
        function filterMatches(matches) {
            return matches.filter(match => {
                if (currentFilters.institution && 
                    match.institution1 !== currentFilters.institution && 
                    match.institution2 !== currentFilters.institution) return false;
                if (currentFilters.team && 
                    match.equipe1 !== currentFilters.team && 
                    match.equipe2 !== currentFilters.team) return false;
                if (currentFilters.pool && match.poule !== currentFilters.pool) return false;
                if (currentFilters.venue && match.gymnase !== currentFilters.venue) return false;
                if (currentFilters.week && match.semaine != currentFilters.week) return false;
                return true;
            });
        }
        
        function renderAllViews() {
            const filtered = filterMatches(matchsData);
            updateFilterInfo(filtered);
            renderCalendarView(filtered);
            renderTimelineView(filtered);
            renderVenuesView(filtered);
            renderPoolsView(filtered);
            renderUnscheduledView();
        }
        
        function updateFilterInfo(matches) {
            const filterInfo = document.getElementById('filterInfo');
            
            if (!currentFilters.institution && !currentFilters.team) {
                filterInfo.classList.remove('active');
                return;
            }
            
            filterInfo.classList.add('active');
            
            let title = '';
            if (currentFilters.team) {
                title = `👥 Équipe: ${currentFilters.team}`;
            } else if (currentFilters.institution) {
                title = `🏛️ Institution: ${currentFilters.institution}`;
            }
            
            // Calculate stats for the filtered selection
            const weeks = new Set(matches.map(m => m.semaine));
            const venues = new Set(matches.map(m => m.gymnase));
            const opponents = new Set();
            matches.forEach(m => {
                if (currentFilters.team) {
                    if (m.equipe1 === currentFilters.team) opponents.add(m.equipe2);
                    if (m.equipe2 === currentFilters.team) opponents.add(m.equipe1);
                } else if (currentFilters.institution) {
                    if (m.institution1 === currentFilters.institution) opponents.add(m.equipe2);
                    if (m.institution2 === currentFilters.institution) opponents.add(m.equipe1);
                }
            });
            
            filterInfo.innerHTML = `
                <h3>${title}</h3>
                <div class="filter-stats">
                    <div class="filter-stat">
                        <div class="filter-stat-value">${matches.length}</div>
                        <div class="filter-stat-label">Matchs</div>
                    </div>
                    <div class="filter-stat">
                        <div class="filter-stat-value">${weeks.size}</div>
                        <div class="filter-stat-label">Semaines</div>
                    </div>
                    <div class="filter-stat">
                        <div class="filter-stat-value">${venues.size}</div>
                        <div class="filter-stat-label">Gymnases</div>
                    </div>
                    <div class="filter-stat">
                        <div class="filter-stat-value">${opponents.size}</div>
                        <div class="filter-stat-label">Adversaires</div>
                    </div>
                </div>
            `;
        }
        
        function renderCalendarView(matches) {
            const container = document.getElementById('calendarView');
            if (matches.length === 0) {
                container.innerHTML = '<div class="no-matches"><div class="no-matches-icon">🔍</div>Aucun match trouvé</div>';
                return;
            }
            
            const byWeek = {};
            matches.forEach(match => {
                if (!byWeek[match.semaine]) byWeek[match.semaine] = [];
                byWeek[match.semaine].push(match);
            });
            
            let html = '';
            Object.keys(byWeek).sort((a, b) => a - b).forEach(week => {
                const weekMatches = byWeek[week];
                html += `
                    <div class="week-container">
                        <div class="week-header">
                            <span>Semaine ${week}</span>
                            <span class="week-info">${weekMatches.length} match${weekMatches.length > 1 ? 's' : ''}</span>
                        </div>
                        <div class="matches-grid">
                            ${weekMatches.map(match => {
                                const team1Class = shouldHighlight(match.equipe1, match.institution1) ? 'team highlighted' : 'team';
                                const team2Class = shouldHighlight(match.equipe2, match.institution2) ? 'team highlighted' : 'team';
                                return `
                                    <div class="match-card">
                                        <div class="match-header">
                                            <span class="match-poule">Poule ${match.poule}</span>
                                            <span class="match-time">⏰ ${match.horaire}</span>
                                        </div>
                                        <div class="match-teams">
                                            <span class="${team1Class}">${match.equipe1}</span>
                                            <span class="vs">VS</span>
                                            <span class="${team2Class}">${match.equipe2}</span>
                                        </div>
                                        <div class="match-venue">
                                            <span class="venue-icon">🏢</span>${match.gymnase}
                                        </div>
                                    </div>
                                `;
                            }).join('')}
                        </div>
                    </div>
                `;
            });
            
            container.innerHTML = html;
        }
        
        function shouldHighlight(team, institution) {
            if (currentFilters.team && team === currentFilters.team) return true;
            if (currentFilters.institution && !currentFilters.team && institution === currentFilters.institution) return true;
            return false;
        }
        
        function renderTimelineView(matches) {
            const container = document.getElementById('timelineView');
            if (matches.length === 0) {
                container.innerHTML = '<div class="no-matches"><div class="no-matches-icon">🔍</div>Aucun match trouvé</div>';
                return;
            }
            
            const byWeek = {};
            matches.forEach(match => {
                if (!byWeek[match.semaine]) byWeek[match.semaine] = [];
                byWeek[match.semaine].push(match);
            });
            
            let html = '<div class="timeline-container">';
            Object.keys(byWeek).sort((a, b) => a - b).forEach(week => {
                const weekMatches = byWeek[week];
                html += `
                    <div class="timeline-week">
                        <div class="timeline-marker">
                            <div class="timeline-week-num">${week}</div>
                            <div class="timeline-week-label">SEMAINE</div>
                        </div>
                        <div class="timeline-content">
                            <strong>${weekMatches.length} match${weekMatches.length > 1 ? 's' : ''} programmé${weekMatches.length > 1 ? 's' : ''}</strong>
                            <div class="timeline-matches">
                                ${weekMatches.map(match => `
                                    <div class="timeline-match">
                                        <strong>Poule ${match.poule}</strong><br>
                                        ${match.equipe1} vs ${match.equipe2}<br>
                                        <small>⏰ ${match.horaire} | 🏢 ${match.gymnase}</small>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    </div>
                `;
            });
            html += '</div>';
            
            container.innerHTML = html;
        }
        
        function renderVenuesView(matches) {
            const container = document.getElementById('venuesView');
            if (matches.length === 0) {
                container.innerHTML = '<div class="no-matches"><div class="no-matches-icon">🔍</div>Aucun match trouvé</div>';
                return;
            }
            
            const byVenue = {};
            matches.forEach(match => {
                if (!byVenue[match.gymnase]) byVenue[match.gymnase] = {};
                if (!byVenue[match.gymnase][match.horaire]) byVenue[match.gymnase][match.horaire] = [];
                byVenue[match.gymnase][match.horaire].push(match);
            });
            
            let html = '';
            Object.keys(byVenue).sort().forEach(venue => {
                html += `
                    <div class="venue-section">
                        <div class="venue-header">🏢 ${venue}</div>
                        <div class="venue-schedule">
                            ${Object.keys(byVenue[venue]).sort().map(horaire => {
                                const horMatches = byVenue[venue][horaire];
                                return `
                                    <div class="time-slot">
                                        <div class="time-label">⏰ ${horaire}</div>
                                        <div class="time-matches">
                                            ${horMatches.map(match => `
                                                <div class="mini-match">
                                                    <strong>S${match.semaine}</strong> - Poule ${match.poule}<br>
                                                    ${match.equipe1} vs ${match.equipe2}
                                                </div>
                                            `).join('')}
                                        </div>
                                    </div>
                                `;
                            }).join('')}
                        </div>
                    </div>
                `;
            });
            
            container.innerHTML = html;
        }
        
        function renderPoolsView(matches) {
            const container = document.getElementById('poolsView');
            if (matches.length === 0) {
                container.innerHTML = '<div class="no-matches"><div class="no-matches-icon">🔍</div>Aucun match trouvé</div>';
                return;
            }
            
            const byPool = {};
            matches.forEach(match => {
                if (!byPool[match.poule]) byPool[match.poule] = [];
                byPool[match.poule].push(match);
            });
            
            let html = '<div class="pool-grid">';
            Object.keys(byPool).sort().forEach(pool => {
                const poolMatches = byPool[pool];
                html += `
                    <div class="pool-card">
                        <div class="pool-header">Poule ${pool}</div>
                        <div class="pool-matches">
                            ${poolMatches.map(match => `
                                <div class="pool-match">
                                    <strong>${match.equipe1} vs ${match.equipe2}</strong><br>
                                    <small>📅 Semaine ${match.semaine} | ⏰ ${match.horaire} | 🏢 ${match.gymnase}</small>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
            });
            html += '</div>';
            
            container.innerHTML = html;
        }
        
        function switchView(viewName) {
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.view-content').forEach(content => content.classList.remove('active'));
            
            event.target.classList.add('active');
            document.getElementById(viewName + 'View').classList.add('active');
        }
        
        function resetFilters() {
            currentFilters = { institution: '', team: '', pool: '', venue: '', week: '' };
            document.getElementById('filterInstitution').value = '';
            document.getElementById('filterTeam').value = '';
            document.getElementById('filterPool').value = '';
            document.getElementById('filterVenue').value = '';
            document.getElementById('filterWeek').value = '';
            
            // Repopulate team filter with all teams
            const stats = calculateStats(matchsData);
            const teamSelect = document.getElementById('filterTeam');
            teamSelect.innerHTML = '<option value="">Toutes les équipes</option>';
            stats.teams.forEach(team => {
                const option = document.createElement('option');
                option.value = team;
                option.textContent = team;
                teamSelect.appendChild(option);
            });
            
            renderAllViews();
        }
        
        function renderUnscheduledView() {
            const container = document.getElementById('unscheduledView');
            
            if (unscheduledData.length === 0) {
                container.innerHTML = `
                    <div style="text-align: center; padding: 60px 20px; color: #4caf50;">
                        <div style="font-size: 80px; margin-bottom: 20px;">✅</div>
                        <h2 style="font-size: 28px; margin-bottom: 10px;">Tous les matchs ont été planifiés !</h2>
                        <p style="font-size: 18px; opacity: 0.8;">Aucun match non planifié</p>
                    </div>
                `;
                return;
            }
            
            // Group unscheduled matches by pool
            const byPool = {};
            unscheduledData.forEach(match => {
                if (!byPool[match.poule]) {
                    byPool[match.poule] = [];
                }
                byPool[match.poule].push(match);
            });
            
            let html = '<div class="pool-grid">';
            
            Object.keys(byPool).sort().forEach(poolName => {
                const poolMatches = byPool[poolName];
                html += `
                    <div class="pool-card" style="border-left: 4px solid #ff6b6b;">
                        <div class="pool-header" style="background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);">
                            ⚠️ Poule ${poolName} <span class="pool-count">${poolMatches.length} match(s) non planifié(s)</span>
                        </div>
                        <div class="pool-matches">
                `;
                
                poolMatches.forEach(match => {
                    html += `
                        <div class="pool-match" style="border-left-color: #ff6b6b;">
                            <div class="match-teams">
                                <strong>${match.equipe1}</strong> vs <strong>${match.equipe2}</strong>
                            </div>
                            <div class="match-institutions">
                                ${match.institution1} • ${match.institution2}
                            </div>
                            <div style="margin-top: 8px; color: #ff6b6b; font-weight: 600;">
                                ❌ Match non planifié
                            </div>
                        </div>
                    `;
                });
                
                html += `
                        </div>
                    </div>
                `;
            });
            
            html += '</div>';
            container.innerHTML = html;
        }
        
        initializeData();
    </script>
</body>
</html>"""
    
    @staticmethod
    def generate(solution: Solution, output_path: str):
        """Generate interactive HTML visualization."""
        
        matches_data = []
        for match in solution.matchs_planifies:
            if match.creneau:
                matches_data.append({
                    'equipe1': match.equipe1.nom_complet,
                    'equipe2': match.equipe2.nom_complet,
                    'institution1': match.equipe1.institution,
                    'institution2': match.equipe2.institution,
                    'poule': match.poule,
                    'semaine': match.creneau.semaine,
                    'horaire': match.creneau.horaire,
                    'gymnase': match.creneau.gymnase
                })
        
        # Ajouter les matchs non planifiés
        unscheduled_data = []
        for match in solution.matchs_non_planifies:
            unscheduled_data.append({
                'equipe1': match.equipe1.nom_complet,
                'equipe2': match.equipe2.nom_complet,
                'institution1': match.equipe1.institution,
                'institution2': match.equipe2.institution,
                'poule': match.poule
            })
        
        html_content = HTMLVisualizer.TEMPLATE.replace(
            '{{MATCHES_DATA}}',
            json.dumps(matches_data, ensure_ascii=False)
        ).replace(
            '{{UNSCHEDULED_DATA}}',
            json.dumps(unscheduled_data, ensure_ascii=False)
        )
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✓ Visualisation HTML générée: {output_path}")
        return str(output_file.absolute())
