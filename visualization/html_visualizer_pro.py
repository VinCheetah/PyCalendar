"""HTML calendar visualizer - VERSION PROFESSIONNELLE avec qualité supérieure."""

import json
from pathlib import Path
from typing import Dict, List
from core.models import Solution, Match
from collections import defaultdict


class HTMLVisualizerPro:
    """Génère une visualisation HTML professionnelle ultra-intuitive."""
    
    TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PyCalendar Pro - Calendrier Sportif</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        :root {
            --primary: #4F46E5;
            --primary-hover: #4338CA;
            --secondary: #10B981;
            --danger: #EF4444;
            --warning: #F59E0B;
            --dark: #1F2937;
            --gray: #6B7280;
            --light: #F9FAFB;
            --border: #E5E7EB;
            
            /* Couleurs Genre */
            --male: #3B82F6;
            --female: #EC4899;
            
            /* Couleurs Catégories */
            --cat-a1: #8B5CF6;
            --cat-a2: #6366F1;
            --cat-a3: #3B82F6;
            --cat-a4: #14B8A6;
            
            --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
            --shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
            --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 2rem;
            color: var(--dark);
            line-height: 1.6;
        }
        
        .app-container {
            max-width: 1600px;
            margin: 0 auto;
            background: white;
            border-radius: 24px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
            overflow: hidden;
        }
        
        /* HEADER */
        .header {
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-hover) 100%);
            color: white;
            padding: 2.5rem;
        }
        
        .header-title {
            font-size: 2.5rem;
            font-weight: 800;
            margin-bottom: 0.5rem;
        }
        
        .header-subtitle {
            font-size: 1.125rem;
            opacity: 0.95;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin-top: 2rem;
        }
        
        .stat-card {
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 12px;
            padding: 1.25rem;
            transition: all 0.3s;
        }
        
        .stat-card:hover {
            background: rgba(255, 255, 255, 0.25);
            transform: translateY(-2px);
        }
        
        .stat-value {
            font-size: 2.25rem;
            font-weight: 800;
            line-height: 1;
        }
        
        .stat-label {
            font-size: 0.875rem;
            opacity: 0.9;
            margin-top: 0.5rem;
            font-weight: 500;
        }
        
        .legend-section {
            margin-top: 2rem;
            padding-top: 1.5rem;
            border-top: 1px solid rgba(255, 255, 255, 0.2);
            display: flex;
            flex-wrap: wrap;
            gap: 2rem;
        }
        
        .legend-group {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }
        
        .legend-title {
            font-weight: 600;
            font-size: 0.875rem;
        }
        
        .legend-items {
            display: flex;
            gap: 0.75rem;
        }
        
        .legend-item {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.875rem;
        }
        
        .legend-badge {
            width: 20px;
            height: 20px;
            border-radius: 4px;
            border: 2px solid rgba(255, 255, 255, 0.5);
        }
        
        /* CONTROLS */
        .controls-section {
            padding: 1.5rem 2.5rem;
            background: var(--light);
            border-bottom: 1px solid var(--border);
        }
        
        .controls-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1.25rem;
            align-items: end;
        }
        
        .control-item {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            min-width: 0; /* Permet le shrink */
        }
        
        .control-item.full-width {
            grid-column: 1 / -1;
        }
        
        .control-label {
            font-weight: 600;
            font-size: 0.875rem;
            color: var(--dark);
        }
        
        select {
            padding: 0.625rem 1rem;
            border: 2px solid var(--border);
            border-radius: 8px;
            font-size: 0.9375rem;
            font-weight: 500;
            background: white;
            color: var(--dark);
            transition: all 0.2s;
            cursor: pointer;
        }
        
        select:hover {
            border-color: var(--primary);
        }
        
        select:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
        }
        
        .btn-reset {
            padding: 0.625rem 1.5rem;
            background: var(--primary);
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            font-size: 0.9375rem;
            cursor: pointer;
            transition: all 0.3s;
            align-self: flex-end;
        }
        
        .btn-reset:hover {
            background: var(--primary-hover);
            transform: translateY(-1px);
            box-shadow: var(--shadow);
        }
        
        /* GENDER FILTER */
        .gender-filter {
            display: flex;
            gap: 0.5rem;
            width: 100%;
        }
        
        .gender-btn {
            flex: 1;
            padding: 0.625rem 0.75rem;
            background: white;
            color: var(--gray);
            border: 2px solid var(--border);
            border-radius: 8px;
            font-weight: 600;
            font-size: 0.8125rem;
            cursor: pointer;
            transition: all 0.2s;
            text-align: center;
            white-space: nowrap;
            min-width: 0;
        }
        
        .gender-btn:hover {
            border-color: var(--primary);
            color: var(--primary);
        }
        
        .gender-btn.active {
            background: var(--primary);
            border-color: var(--primary);
            color: white;
        }
        
        .gender-btn.male.active {
            background: var(--male);
            border-color: var(--male);
        }
        
        .gender-btn.female.active {
            background: var(--female);
            border-color: var(--female);
        }
        
        /* TOGGLE PREFERENCES */
        .toggle-container {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.625rem 1rem;
            background: white;
            border: 2px solid var(--border);
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .toggle-container:hover {
            border-color: var(--primary);
        }
        
        .toggle-switch {
            position: relative;
            width: 44px;
            height: 24px;
            background: var(--border);
            border-radius: 12px;
            transition: background 0.3s;
        }
        
        .toggle-switch::after {
            content: '';
            position: absolute;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: white;
            top: 2px;
            left: 2px;
            transition: transform 0.3s;
        }
        
        .toggle-container.active .toggle-switch {
            background: var(--primary);
        }
        
        .toggle-container.active .toggle-switch::after {
            transform: translateX(20px);
        }
        
        .toggle-label {
            font-weight: 600;
            font-size: 0.875rem;
            color: var(--dark);
            user-select: none;
        }
        
        /* HORAIRES PREFERES - Symétrie gauche/droite */
        .horaires-preferes {
            display: inline-block;
            padding: 0.125rem 0.5rem;
            background: rgba(79, 70, 229, 0.1);
            color: var(--primary);
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 500;
            opacity: 0;
            transition: opacity 0.3s;
            white-space: nowrap;
        }
        
        /* Horaire de l'équipe 1 (à gauche) : marge à droite */
        .team:first-of-type .horaires-preferes {
            margin-right: 0.5rem;
        }
        
        /* Horaire de l'équipe 2 (à droite) : marge à gauche */
        .team:last-of-type .horaires-preferes {
            margin-left: 0.5rem;
        }
        
        .show-preferences .horaires-preferes {
            opacity: 1;
        }
        
        .horaires-preferes.no-preferences {
            background: rgba(107, 114, 128, 0.08);
            color: var(--gray);
            font-style: italic;
        }
        
        /* GENRE BADGE */
        .genre-badge {
            display: inline-block;
            margin-left: 0.375rem;
            padding: 0.125rem 0.375rem;
            border-radius: 3px;
            font-size: 0.625rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .genre-badge.male {
            background: rgba(59, 130, 246, 0.15);
            color: var(--male);
        }
        
        .genre-badge.female {
            background: rgba(236, 72, 153, 0.15);
            color: var(--female);
        }
        
        /* FILTER INFO */
        .filter-info {
            margin: 2rem 2.5rem;
            padding: 1.5rem;
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-hover) 100%);
            color: white;
            border-radius: 12px;
            display: none;
        }
        
        .filter-info.active {
            display: block;
        }
        
        .filter-info-title {
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        
        .filter-info-subtitle {
            opacity: 0.9;
            margin-bottom: 1rem;
        }
        
        .filter-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
            gap: 1rem;
        }
        
        .filter-stat {
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 8px;
            padding: 1rem;
            text-align: center;
        }
        
        .filter-stat-value {
            font-size: 1.75rem;
            font-weight: 800;
        }
        
        .filter-stat-label {
            font-size: 0.75rem;
            opacity: 0.9;
            margin-top: 0.25rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        /* CONTENT */
        .content-section {
            padding: 2.5rem;
        }
        
        /* TABS */
        .tabs-nav {
            display: flex;
            gap: 0.5rem;
            margin-bottom: 2rem;
            border-bottom: 2px solid var(--border);
            padding-bottom: 0;
            overflow-x: auto;
        }
        
        .tab-btn {
            padding: 1rem 1.5rem;
            background: transparent;
            border: none;
            color: var(--gray);
            font-weight: 600;
            font-size: 0.9375rem;
            cursor: pointer;
            border-bottom: 3px solid transparent;
            transition: all 0.2s;
            white-space: nowrap;
            margin-bottom: -2px;
        }
        
        .tab-btn:hover {
            color: var(--primary);
            background: var(--light);
        }
        
        .tab-btn.active {
            color: var(--primary);
            border-bottom-color: var(--primary);
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
            animation: fadeIn 0.3s ease-in;
        }
        
        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        /* MATCHES */
        .week-section {
            margin-bottom: 2.5rem;
        }
        
        .week-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1.25rem 1.5rem;
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-hover) 100%);
            color: white;
            border-radius: 12px 12px 0 0;
            font-weight: 700;
        }
        
        .week-title {
            font-size: 1.375rem;
        }
        
        .week-count {
            font-size: 0.9375rem;
            opacity: 0.9;
        }
        
        .matches-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
            gap: 1.25rem;
            padding: 1.5rem;
            background: var(--light);
            border-radius: 0 0 12px 12px;
        }
        
        .match-card {
            background: white;
            border-radius: 12px;
            padding: 1.25rem;
            box-shadow: var(--shadow);
            transition: all 0.3s;
            border-left: 4px solid var(--primary);
            position: relative;
        }
        
        .match-card:hover {
            transform: translateY(-4px);
            box-shadow: var(--shadow-lg);
        }
        
        .match-card.male {
            border-left-color: var(--male);
        }
        
        .match-card.female {
            border-left-color: var(--female);
        }
        
        .match-card.unscheduled {
            border-left-color: var(--danger);
            opacity: 0.85;
        }
        
        .match-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
            padding-bottom: 0.75rem;
            border-bottom: 1px solid var(--border);
        }
        
        .match-badges {
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
        }
        
        .badge {
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .badge-poule {
            background: var(--primary);
            color: white;
        }
        
        .badge-gender-male {
            background: var(--male);
            color: white;
        }
        
        .badge-gender-female {
            background: var(--female);
            color: white;
        }
        
        .badge-cat-a1 {
            background: var(--cat-a1);
            color: white;
        }
        
        .badge-cat-a2 {
            background: var(--cat-a2);
            color: white;
        }
        
        .badge-cat-a3 {
            background: var(--cat-a3);
            color: white;
        }
        
        .badge-cat-a4 {
            background: var(--cat-a4);
            color: white;
        }
        
        .badge-unscheduled {
            background: var(--danger);
            color: white;
        }
        
        .match-time {
            color: var(--gray);
            font-size: 0.875rem;
            font-weight: 600;
        }
        
        .match-teams {
            font-size: 1.125rem;
            margin: 1rem 0;
            text-align: center;
            line-height: 1.8;
        }
        
        .team {
            font-weight: 600;
            color: var(--dark);
        }
        
        .team.highlighted {
            color: var(--primary);
            background: rgba(79, 70, 229, 0.1);
            padding: 0.375rem 0.75rem;
            border-radius: 6px;
            font-weight: 700;
        }
        
        .vs {
            color: var(--primary);
            font-weight: 800;
            margin: 0 0.75rem;
            font-size: 0.875rem;
        }
        
        .match-venue {
            text-align: center;
            color: var(--gray);
            font-size: 0.875rem;
            margin-top: 0.75rem;
            padding-top: 0.75rem;
            border-top: 1px solid var(--border);
            font-weight: 500;
        }
        
        .match-institutions {
            text-align: center;
            color: #9CA3AF;
            font-size: 0.75rem;
            margin-top: 0.5rem;
        }
        
        .unscheduled-alert {
            background: linear-gradient(135deg, var(--danger) 0%, #DC2626 100%);
            color: white;
            padding: 0.75rem 1rem;
            border-radius: 8px;
            margin-top: 0.75rem;
            font-weight: 600;
            font-size: 0.875rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        /* EMPTY STATE */
        .empty-state {
            text-align: center;
            padding: 4rem 2rem;
            color: var(--gray);
        }
        
        .empty-icon {
            font-size: 4rem;
            margin-bottom: 1rem;
        }
        
        .empty-title {
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            color: var(--dark);
        }
        
        .empty-text {
            font-size: 1rem;
        }
        
        .success-state {
            text-align: center;
            padding: 4rem 2rem;
            color: var(--secondary);
        }
        
        .success-icon {
            font-size: 5rem;
            margin-bottom: 1.5rem;
        }
        
        .success-title {
            font-size: 2rem;
            font-weight: 800;
            margin-bottom: 0.75rem;
        }
        
        .success-text {
            font-size: 1.125rem;
            opacity: 0.9;
        }
        
        /* RESPONSIVE */
        @media (max-width: 768px) {
            body {
                padding: 1rem;
            }
            
            .header {
                padding: 1.5rem;
            }
            
            .header-title {
                font-size: 1.75rem;
            }
            
            .controls-section {
                padding: 1rem;
            }
            
            .content-section {
                padding: 1.5rem;
            }
            
            .matches-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="app-container">
        <!-- HEADER -->
        <header class="header">
            <h1 class="header-title">🏐 PyCalendar Pro</h1>
            <p class="header-subtitle">Système de planification sportive intelligente</p>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value" id="totalMatches">0</div>
                    <div class="stat-label">Matchs planifiés</div>
                </div>
                <div class="stat-card">
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
            
            <div class="legend-section">
                <div class="legend-group">
                    <span class="legend-title">Genre :</span>
                    <div class="legend-items">
                        <div class="legend-item">
                            <span class="legend-badge" style="background: var(--male);"></span>
                            <span>Garçons</span>
                        </div>
                        <div class="legend-item">
                            <span class="legend-badge" style="background: var(--female);"></span>
                            <span>Filles</span>
                        </div>
                    </div>
                </div>
                <div class="legend-group">
                    <span class="legend-title">Catégories :</span>
                    <div class="legend-items">
                        <div class="legend-item">
                            <span class="legend-badge" style="background: var(--cat-a1);"></span>
                            <span>A1</span>
                        </div>
                        <div class="legend-item">
                            <span class="legend-badge" style="background: var(--cat-a2);"></span>
                            <span>A2</span>
                        </div>
                        <div class="legend-item">
                            <span class="legend-badge" style="background: var(--cat-a3);"></span>
                            <span>A3</span>
                        </div>
                        <div class="legend-item">
                            <span class="legend-badge" style="background: var(--cat-a4);"></span>
                            <span>A4</span>
                        </div>
                    </div>
                </div>
            </div>
        </header>
        
        <!-- CONTROLS -->
        <section class="controls-section">
            <div class="controls-grid">
                <div class="control-item">
                    <label class="control-label">⚧️ Genre</label>
                    <div class="gender-filter">
                        <button class="gender-btn active" data-gender="" onclick="setGenderFilter('')">Tous</button>
                        <button class="gender-btn male" data-gender="M" onclick="setGenderFilter('M')">♂ Masculin</button>
                        <button class="gender-btn female" data-gender="F" onclick="setGenderFilter('F')">♀ Féminin</button>
                    </div>
                </div>
                <div class="control-item">
                    <label class="control-label" for="filterInstitution">🏛️ Institution</label>
                    <select id="filterInstitution">
                        <option value="">Toutes les institutions</option>
                    </select>
                </div>
                <div class="control-item">
                    <label class="control-label" for="filterTeam">👥 Équipe</label>
                    <select id="filterTeam">
                        <option value="">Toutes les équipes</option>
                    </select>
                </div>
                <div class="control-item">
                    <label class="control-label" for="filterPool">🎯 Poule</label>
                    <select id="filterPool">
                        <option value="">Toutes les poules</option>
                    </select>
                </div>
                <div class="control-item">
                    <label class="control-label" for="filterVenue">🏢 Gymnase</label>
                    <select id="filterVenue">
                        <option value="">Tous les gymnases</option>
                    </select>
                </div>
                <div class="control-item">
                    <label class="control-label" for="filterWeek">📅 Semaine</label>
                    <select id="filterWeek">
                        <option value="">Toutes les semaines</option>
                    </select>
                </div>
                <div class="control-item">
                    <label class="control-label">⏰ Horaires préférés</label>
                    <div class="toggle-container" id="togglePreferences" onclick="togglePreferences()">
                        <div class="toggle-switch"></div>
                        <span class="toggle-label">Afficher</span>
                    </div>
                </div>
                <div class="control-item">
                    <button class="btn-reset" onclick="resetFilters()">🔄 Réinitialiser</button>
                </div>
            </div>
        </section>
        
        <!-- FILTER INFO -->
        <div id="filterInfo" class="filter-info"></div>
        
        <!-- CONTENT -->
        <main class="content-section">
            <!-- TABS -->
            <nav class="tabs-nav">
                <button class="tab-btn active" data-tab="calendar">📅 Calendrier</button>
                <button class="tab-btn" data-tab="pools">🎯 Par Poule</button>
                <button class="tab-btn" data-tab="venues">🏢 Par Gymnase</button>
                <button class="tab-btn" data-tab="unscheduled" id="unscheduledTab">⚠️ Non Planifiés</button>
            </nav>
            
            <!-- TAB CONTENTS -->
            <div id="calendarContent" class="tab-content active"></div>
            <div id="poolsContent" class="tab-content"></div>
            <div id="venuesContent" class="tab-content"></div>
            <div id="unscheduledContent" class="tab-content"></div>
        </main>
    </div>
    
    <script>
        // DONNÉES
        const matchsData = {{MATCHES_DATA}};
        const unscheduledData = {{UNSCHEDULED_DATA}};
        
        // STATE
        let filters = {
            gender: '',
            institution: '',
            team: '',
            pool: '',
            venue: '',
            week: ''
        };
        
        let showPreferences = false;
        
        // UTILITAIRES
        function getGender(poolName) {
            return (poolName.includes('HBF') || poolName.includes('F')) ? 'female' : 'male';
        }
        
        function getCategory(poolName) {
            if (poolName.includes('A1') || poolName.includes('1P')) return 'a1';
            if (poolName.includes('A2') || poolName.includes('2P')) return 'a2';
            if (poolName.includes('A3') || poolName.includes('3P')) return 'a3';
            if (poolName.includes('A4') || poolName.includes('4P')) return 'a4';
            return 'a1';
        }
        
        function shouldHighlight(team, institution) {
            if (filters.team && team === filters.team) return true;
            if (filters.institution && !filters.team && institution === filters.institution) return true;
            return false;
        }
        
        // CALCUL DES STATS
        function calculateStats(matches) {
            const stats = {
                weeks: new Set(),
                pools: new Set(),
                venues: new Set(),
                institutions: new Set(),
                teams: new Set()
            };
            
            matches.forEach(m => {
                stats.weeks.add(m.semaine);
                stats.pools.add(m.poule);
                stats.venues.add(m.gymnase);
                stats.institutions.add(m.institution1);
                stats.institutions.add(m.institution2);
                stats.teams.add(m.equipe1);
                stats.teams.add(m.equipe2);
            });
            
            return {
                totalMatches: matches.length,
                totalWeeks: stats.weeks.size,
                totalPools: stats.pools.size,
                totalVenues: stats.venues.size,
                weeks: Array.from(stats.weeks).sort((a, b) => a - b),
                pools: Array.from(stats.pools).sort(),
                venues: Array.from(stats.venues).sort(),
                institutions: Array.from(stats.institutions).sort(),
                teams: Array.from(stats.teams).sort()
            };
        }
        
        // FILTRAGE
        function filterMatches(matches) {
            return matches.filter(m => {
                if (filters.gender && m.equipe1_genre !== filters.gender && m.equipe2_genre !== filters.gender) return false;
                if (filters.institution && m.institution1 !== filters.institution && m.institution2 !== filters.institution) return false;
                if (filters.team && m.equipe1 !== filters.team && m.equipe2 !== filters.team) return false;
                if (filters.pool && m.poule !== filters.pool) return false;
                if (filters.venue && m.gymnase !== filters.venue) return false;
                if (filters.week && m.semaine != filters.week) return false;
                return true;
            });
        }
        
        function filterUnscheduled(matches) {
            return matches.filter(m => {
                if (filters.gender && m.equipe1_genre !== filters.gender && m.equipe2_genre !== filters.gender) return false;
                if (filters.institution && m.institution1 !== filters.institution && m.institution2 !== filters.institution) return false;
                if (filters.team && m.equipe1 !== filters.team && m.equipe2 !== filters.team) return false;
                if (filters.pool && m.poule !== filters.pool) return false;
                return true;
            });
        }
        
        // RENDU: CARTE DE MATCH
        function renderMatchCard(match, isUnscheduled = false) {
            const gender = getGender(match.poule);
            const category = getCategory(match.poule);
            const team1Class = shouldHighlight(match.equipe1, match.institution1) ? 'team highlighted' : 'team';
            const team2Class = shouldHighlight(match.equipe2, match.institution2) ? 'team highlighted' : 'team';
            
            // Horaires préférés avec symétrie : horaire1 équipe1 VS équipe2 horaire2
            const formatHorairesLeft = (horaires) => {
                if (!horaires || horaires.length === 0) {
                    return `<span class="horaires-preferes no-preferences" title="Aucun horaire préféré défini">⏰ −</span>`;
                }
                const horaireStr = horaires[0];
                return `<span class="horaires-preferes" title="Horaire préféré: ${horaireStr}">⏰ ${horaireStr}</span>`;
            };
            
            const formatHorairesRight = (horaires) => {
                if (!horaires || horaires.length === 0) {
                    return `<span class="horaires-preferes no-preferences" title="Aucun horaire préféré défini">⏰ −</span>`;
                }
                const horaireStr = horaires[0];
                return `<span class="horaires-preferes" title="Horaire préféré: ${horaireStr}">${horaireStr} ⏰</span>`;
            };
            
            return `
                <div class="match-card ${gender} ${isUnscheduled ? 'unscheduled' : ''}">
                    <div class="match-header">
                        <div class="match-badges">
                            <span class="badge badge-poule">${match.poule}</span>
                            <span class="badge badge-gender-${gender}">${gender === 'male' ? 'M' : 'F'}</span>
                            <span class="badge badge-cat-${category}">${category.toUpperCase()}</span>
                            ${isUnscheduled ? '<span class="badge badge-unscheduled">Non planifié</span>' : ''}
                        </div>
                        ${!isUnscheduled ? `<div class="match-time">⏰ ${match.horaire}</div>` : ''}
                    </div>
                    <div class="match-teams">
                        <span class="${team1Class}">
                            ${formatHorairesLeft(match.equipe1_horaires_preferes)} ${match.equipe1}
                        </span>
                        <span class="vs">VS</span>
                        <span class="${team2Class}">
                            ${match.equipe2} ${formatHorairesRight(match.equipe2_horaires_preferes)}
                        </span>
                    </div>
                    <div class="match-institutions">${match.institution1} • ${match.institution2}</div>
                    ${!isUnscheduled ? `
                        <div class="match-venue">🏢 ${match.gymnase}</div>
                    ` : `
                        <div class="unscheduled-alert">❌ Match non planifié</div>
                    `}
                </div>
            `;
        }
        
        // RENDU: VUE CALENDRIER
        function renderCalendar(matches) {
            const container = document.getElementById('calendarContent');
            
            if (matches.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-icon">🔍</div>
                        <h3 class="empty-title">Aucun match trouvé</h3>
                        <p class="empty-text">Essayez de modifier vos filtres</p>
                    </div>
                `;
                return;
            }
            
            // Grouper par semaine
            const byWeek = {};
            matches.forEach(m => {
                if (!byWeek[m.semaine]) byWeek[m.semaine] = [];
                byWeek[m.semaine].push(m);
            });
            
            let html = '';
            Object.keys(byWeek).sort((a, b) => a - b).forEach(week => {
                const weekMatches = byWeek[week];
                html += `
                    <section class="week-section">
                        <div class="week-header">
                            <div class="week-title">📅 Semaine ${week}</div>
                            <div class="week-count">${weekMatches.length} match${weekMatches.length > 1 ? 's' : ''}</div>
                        </div>
                        <div class="matches-grid">
                            ${weekMatches.map(m => renderMatchCard(m, false)).join('')}
                        </div>
                    </section>
                `;
            });
            
            container.innerHTML = html;
        }
        
        // RENDU: VUE PAR POULE
        function renderPools(matches) {
            const container = document.getElementById('poolsContent');
            
            if (matches.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-icon">🔍</div>
                        <h3 class="empty-title">Aucun match trouvé</h3>
                        <p class="empty-text">Essayez de modifier vos filtres</p>
                    </div>
                `;
                return;
            }
            
            // Grouper par poule
            const byPool = {};
            matches.forEach(m => {
                if (!byPool[m.poule]) byPool[m.poule] = [];
                byPool[m.poule].push(m);
            });
            
            let html = '';
            Object.keys(byPool).sort().forEach(pool => {
                const poolMatches = byPool[pool];
                html += `
                    <section class="week-section">
                        <div class="week-header">
                            <div class="week-title">🎯 ${pool}</div>
                            <div class="week-count">${poolMatches.length} match${poolMatches.length > 1 ? 's' : ''}</div>
                        </div>
                        <div class="matches-grid">
                            ${poolMatches.map(m => renderMatchCard(m, false)).join('')}
                        </div>
                    </section>
                `;
            });
            
            container.innerHTML = html;
        }
        
        // RENDU: VUE PAR GYMNASE
        function renderVenues(matches) {
            const container = document.getElementById('venuesContent');
            
            if (matches.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-icon">🔍</div>
                        <h3 class="empty-title">Aucun match trouvé</h3>
                        <p class="empty-text">Essayez de modifier vos filtres</p>
                    </div>
                `;
                return;
            }
            
            // Grouper par gymnase
            const byVenue = {};
            matches.forEach(m => {
                if (!byVenue[m.gymnase]) byVenue[m.gymnase] = [];
                byVenue[m.gymnase].push(m);
            });
            
            let html = '';
            Object.keys(byVenue).sort().forEach(venue => {
                const venueMatches = byVenue[venue];
                html += `
                    <section class="week-section">
                        <div class="week-header">
                            <div class="week-title">🏢 ${venue}</div>
                            <div class="week-count">${venueMatches.length} match${venueMatches.length > 1 ? 's' : ''}</div>
                        </div>
                        <div class="matches-grid">
                            ${venueMatches.map(m => renderMatchCard(m, false)).join('')}
                        </div>
                    </section>
                `;
            });
            
            container.innerHTML = html;
        }
        
        // RENDU: VUE MATCHS NON PLANIFIÉS
        function renderUnscheduled(matches) {
            const container = document.getElementById('unscheduledContent');
            
            if (matches.length === 0) {
                container.innerHTML = `
                    <div class="success-state">
                        <div class="success-icon">✅</div>
                        <h2 class="success-title">Tous les matchs sont planifiés !</h2>
                        <p class="success-text">Aucun match non planifié</p>
                    </div>
                `;
                return;
            }
            
            // Grouper par poule
            const byPool = {};
            matches.forEach(m => {
                if (!byPool[m.poule]) byPool[m.poule] = [];
                byPool[m.poule].push(m);
            });
            
            let html = '';
            Object.keys(byPool).sort().forEach(pool => {
                const poolMatches = byPool[pool];
                html += `
                    <section class="week-section">
                        <div class="week-header" style="background: linear-gradient(135deg, var(--danger) 0%, #DC2626 100%);">
                            <div class="week-title">⚠️ ${pool}</div>
                            <div class="week-count">${poolMatches.length} non planifié${poolMatches.length > 1 ? 's' : ''}</div>
                        </div>
                        <div class="matches-grid">
                            ${poolMatches.map(m => renderMatchCard(m, true)).join('')}
                        </div>
                    </section>
                `;
            });
            
            container.innerHTML = html;
        }
        
        // MISE À JOUR DES INFOS DE FILTRE
        function updateFilterInfo(matches, unscheduled) {
            const container = document.getElementById('filterInfo');
            
            if (!filters.institution && !filters.team) {
                container.classList.remove('active');
                return;
            }
            
            container.classList.add('active');
            
            const title = filters.team ? `👥 ${filters.team}` : `🏛️ ${filters.institution}`;
            const subtitle = filters.team ? "Détails de l'équipe" : "Détails de l'institution";
            
            const weeks = new Set(matches.map(m => m.semaine));
            const venues = new Set(matches.map(m => m.gymnase));
            
            container.innerHTML = `
                <div class="filter-info-title">${title}</div>
                <div class="filter-info-subtitle">${subtitle}</div>
                <div class="filter-stats">
                    <div class="filter-stat">
                        <div class="filter-stat-value">${matches.length}</div>
                        <div class="filter-stat-label">Planifiés</div>
                    </div>
                    <div class="filter-stat">
                        <div class="filter-stat-value">${unscheduled.length}</div>
                        <div class="filter-stat-label">Non planifiés</div>
                    </div>
                    <div class="filter-stat">
                        <div class="filter-stat-value">${weeks.size}</div>
                        <div class="filter-stat-label">Semaines</div>
                    </div>
                    <div class="filter-stat">
                        <div class="filter-stat-value">${venues.size}</div>
                        <div class="filter-stat-label">Gymnases</div>
                    </div>
                </div>
            `;
        }
        
        // RENDU GLOBAL
        function renderAll() {
            const filtered = filterMatches(matchsData);
            const unscheduledFiltered = filterUnscheduled(unscheduledData);
            
            updateFilterInfo(filtered, unscheduledFiltered);
            renderCalendar(filtered);
            renderPools(filtered);
            renderVenues(filtered);
            renderUnscheduled(unscheduledFiltered);
        }
        
        // POPULATE FILTERS
        function populateFilters(stats) {
            // Institution
            const instSelect = document.getElementById('filterInstitution');
            stats.institutions.forEach(inst => {
                const opt = document.createElement('option');
                opt.value = inst;
                opt.textContent = inst;
                instSelect.appendChild(opt);
            });
            instSelect.addEventListener('change', (e) => {
                filters.institution = e.target.value;
                updateTeamFilter(stats);
                renderAll();
            });
            
            // Team
            const teamSelect = document.getElementById('filterTeam');
            stats.teams.forEach(team => {
                const opt = document.createElement('option');
                opt.value = team;
                opt.textContent = team;
                teamSelect.appendChild(opt);
            });
            teamSelect.addEventListener('change', (e) => {
                filters.team = e.target.value;
                renderAll();
            });
            
            // Pool
            const poolSelect = document.getElementById('filterPool');
            stats.pools.forEach(pool => {
                const opt = document.createElement('option');
                opt.value = pool;
                opt.textContent = pool;
                poolSelect.appendChild(opt);
            });
            poolSelect.addEventListener('change', (e) => {
                filters.pool = e.target.value;
                renderAll();
            });
            
            // Venue
            const venueSelect = document.getElementById('filterVenue');
            stats.venues.forEach(venue => {
                const opt = document.createElement('option');
                opt.value = venue;
                opt.textContent = venue;
                venueSelect.appendChild(opt);
            });
            venueSelect.addEventListener('change', (e) => {
                filters.venue = e.target.value;
                renderAll();
            });
            
            // Week
            const weekSelect = document.getElementById('filterWeek');
            stats.weeks.forEach(week => {
                const opt = document.createElement('option');
                opt.value = week;
                opt.textContent = `Semaine ${week}`;
                weekSelect.appendChild(opt);
            });
            weekSelect.addEventListener('change', (e) => {
                filters.week = e.target.value;
                renderAll();
            });
        }
        
        function updateTeamFilter(stats) {
            const teamSelect = document.getElementById('filterTeam');
            const selectedTeam = filters.team;
            
            teamSelect.innerHTML = '<option value="">Toutes les équipes</option>';
            
            // Créer une map des équipes avec leurs genres
            const teamGenreMap = new Map();
            matchsData.forEach(m => {
                if (!teamGenreMap.has(m.equipe1)) teamGenreMap.set(m.equipe1, new Set());
                if (!teamGenreMap.has(m.equipe2)) teamGenreMap.set(m.equipe2, new Set());
                teamGenreMap.get(m.equipe1).add(m.equipe1_genre);
                teamGenreMap.get(m.equipe2).add(m.equipe2_genre);
            });
            
            // Filtrer les équipes selon institution et genre
            let teams = stats.teams;
            if (filters.institution) {
                const instTeams = new Set();
                matchsData.forEach(m => {
                    if (m.institution1 === filters.institution) instTeams.add(m.equipe1);
                    if (m.institution2 === filters.institution) instTeams.add(m.equipe2);
                });
                teams = Array.from(instTeams).sort();
            }
            
            // Si filtre par genre, filtrer encore
            if (filters.gender) {
                const genderTeams = new Set();
                matchsData.forEach(m => {
                    if (m.equipe1_genre === filters.gender) genderTeams.add(m.equipe1);
                    if (m.equipe2_genre === filters.gender) genderTeams.add(m.equipe2);
                });
                teams = teams.filter(t => genderTeams.has(t));
            }
            
            teams.forEach(team => {
                const opt = document.createElement('option');
                opt.value = team;
                
                // Afficher le genre si les deux existent
                const genres = teamGenreMap.get(team);
                if (genres && genres.size > 1) {
                    // Afficher avec symboles de genre
                    const genreSymbols = Array.from(genres).map(g => g === 'M' ? '♂M' : '♀F').join(' / ');
                    opt.textContent = `${team} (${genreSymbols})`;
                } else {
                    opt.textContent = team;
                }
                
                if (team === selectedTeam) opt.selected = true;
                teamSelect.appendChild(opt);
            });
            
            if (filters.team && !teams.includes(filters.team)) {
                filters.team = '';
            }
        }
        
        // GENRE FILTER
        function setGenderFilter(gender) {
            filters.gender = gender;
            
            // Update UI
            document.querySelectorAll('.gender-btn').forEach(btn => {
                btn.classList.remove('active');
                if (btn.dataset.gender === gender) {
                    btn.classList.add('active');
                }
            });
            
            // Update team filter and render
            const stats = calculateStats(matchsData);
            updateTeamFilter(stats);
            renderAll();
        }
        
        // TOGGLE PREFERENCES
        function togglePreferences() {
            showPreferences = !showPreferences;
            const container = document.getElementById('togglePreferences');
            const appContainer = document.querySelector('.app-container');
            
            if (showPreferences) {
                container.classList.add('active');
                appContainer.classList.add('show-preferences');
            } else {
                container.classList.remove('active');
                appContainer.classList.remove('show-preferences');
            }
        }
        
        // RESET FILTERS
        function resetFilters() {
            filters = { gender: '', institution: '', team: '', pool: '', venue: '', week: '' };
            
            // Reset gender buttons
            document.querySelectorAll('.gender-btn').forEach(btn => {
                btn.classList.remove('active');
                if (btn.dataset.gender === '') {
                    btn.classList.add('active');
                }
            });
            
            document.getElementById('filterInstitution').value = '';
            document.getElementById('filterTeam').value = '';
            document.getElementById('filterPool').value = '';
            document.getElementById('filterVenue').value = '';
            document.getElementById('filterWeek').value = '';
            
            const stats = calculateStats(matchsData);
            updateTeamFilter(stats);
            renderAll();
        }
        
        // GESTION DES TABS
        function setupTabs() {
            const tabs = document.querySelectorAll('.tab-btn');
            tabs.forEach(tab => {
                tab.addEventListener('click', () => {
                    // Remove active
                    tabs.forEach(t => t.classList.remove('active'));
                    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                    
                    // Add active
                    tab.classList.add('active');
                    const contentId = tab.dataset.tab + 'Content';
                    document.getElementById(contentId).classList.add('active');
                });
            });
        }
        
        // INITIALISATION
        function init() {
            console.log('🚀 Initialisation PyCalendar Pro');
            console.log('  Matchs planifiés:', matchsData.length);
            console.log('  Matchs non planifiés:', unscheduledData.length);
            
            const stats = calculateStats(matchsData);
            
            // Update header stats
            document.getElementById('totalMatches').textContent = stats.totalMatches;
            document.getElementById('totalUnscheduled').textContent = unscheduledData.length;
            document.getElementById('totalWeeks').textContent = stats.totalWeeks;
            document.getElementById('totalPools').textContent = stats.totalPools;
            document.getElementById('totalVenues').textContent = stats.totalVenues;
            
            // Update unscheduled tab
            if (unscheduledData.length > 0) {
                document.getElementById('unscheduledTab').textContent = `⚠️ Non Planifiés (${unscheduledData.length})`;
            }
            
            // Setup
            populateFilters(stats);
            setupTabs();
            renderAll();
            
            console.log('✅ Initialisation terminée');
        }
        
        // LANCEMENT
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', init);
        } else {
            init();
        }
    </script>
</body>
</html>"""
    
    @staticmethod
    def generate(solution: Solution, output_path: str):
        """Génère la visualisation HTML professionnelle."""
        
        # Matches planifiés
        matches_data = []
        for match in solution.matchs_planifies:
            if match.creneau:
                matches_data.append({
                    'equipe1': match.equipe1.nom,
                    'equipe2': match.equipe2.nom,
                    'equipe1_genre': match.equipe1.genre,
                    'equipe2_genre': match.equipe2.genre,
                    'equipe1_horaires_preferes': match.equipe1.horaires_preferes if match.equipe1.horaires_preferes else [],
                    'equipe2_horaires_preferes': match.equipe2.horaires_preferes if match.equipe2.horaires_preferes else [],
                    'institution1': match.equipe1.institution,
                    'institution2': match.equipe2.institution,
                    'poule': match.poule,
                    'semaine': match.creneau.semaine,
                    'horaire': match.creneau.horaire,
                    'gymnase': match.creneau.gymnase
                })
        
        # Matches non planifiés
        unscheduled_data = []
        for match in solution.matchs_non_planifies:
            unscheduled_data.append({
                'equipe1': match.equipe1.nom,
                'equipe2': match.equipe2.nom,
                'equipe1_genre': match.equipe1.genre,
                'equipe2_genre': match.equipe2.genre,
                'equipe1_horaires_preferes': match.equipe1.horaires_preferes if match.equipe1.horaires_preferes else [],
                'equipe2_horaires_preferes': match.equipe2.horaires_preferes if match.equipe2.horaires_preferes else [],
                'institution1': match.equipe1.institution,
                'institution2': match.equipe2.institution,
                'poule': match.poule
            })
        
        # Generate HTML
        html_content = HTMLVisualizerPro.TEMPLATE.replace(
            '{{MATCHES_DATA}}',
            json.dumps(matches_data, ensure_ascii=False, indent=2)
        ).replace(
            '{{UNSCHEDULED_DATA}}',
            json.dumps(unscheduled_data, ensure_ascii=False, indent=2)
        )
        
        # Write file
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✓ Visualisation HTML Pro générée: {output_path}")
        return str(output_file.absolute())
