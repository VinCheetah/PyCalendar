#!/usr/bin/env python3
"""
Script pour générer un HTML ultra-basique avec juste un tableau des matchs.
Pas de JavaScript complexe, pas de vue agenda, juste un tableau simple.
"""

import json
from pathlib import Path
from datetime import datetime

def load_solution():
    """Charge la solution depuis latest_volley.json."""
    solution_path = Path("solutions/latest_volley.json")
    with open(solution_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_basic_html_table(assignments, output_path):
    """Génère un HTML simple avec un tableau des matchs."""
    
    # Grouper par semaine
    by_week = {}
    for assignment in assignments:
        week = assignment["semaine"]
        if week not in by_week:
            by_week[week] = []
        by_week[week].append(assignment)
    
    # Trier chaque semaine par horaire
    for week in by_week:
        by_week[week].sort(key=lambda x: (x["horaire"], x["gymnase"]))
    
    # HTML de base
    html = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Calendrier Volleyball - Version Basique</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }
        
        h1 {
            color: #2c3e50;
            text-align: center;
            margin-bottom: 30px;
        }
        
        .week-section {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .week-header {
            background: #3498db;
            color: white;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .week-title {
            font-size: 20px;
            font-weight: bold;
        }
        
        .week-count {
            background: rgba(255,255,255,0.2);
            padding: 5px 15px;
            border-radius: 20px;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        
        th {
            background: #34495e;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }
        
        td {
            padding: 10px 12px;
            border-bottom: 1px solid #ecf0f1;
        }
        
        tr:hover {
            background: #f8f9fa;
        }
        
        .time {
            font-weight: 600;
            color: #3498db;
        }
        
        .venue {
            color: #27ae60;
            font-weight: 500;
        }
        
        .team {
            color: #2c3e50;
        }
        
        .genre-M {
            color: #3498db;
        }
        
        .genre-F {
            color: #e74c3c;
        }
        
        .fixed {
            background: #d5f4e6;
        }
        
        .badge {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
        }
        
        .badge-fixed {
            background: #27ae60;
            color: white;
        }
        
        .badge-M {
            background: #3498db;
            color: white;
        }
        
        .badge-F {
            background: #e74c3c;
            color: white;
        }
    </style>
</head>
<body>
    <h1>📅 Calendrier Volleyball 2024-2025</h1>
"""
    
    # Générer les sections par semaine
    for week in sorted(by_week.keys()):
        matches = by_week[week]
        html += f"""
    <div class="week-section">
        <div class="week-header">
            <div class="week-title">📅 Semaine {week}</div>
            <div class="week-count">{len(matches)} match{'s' if len(matches) > 1 else ''}</div>
        </div>
        <table>
            <thead>
                <tr>
                    <th>Horaire</th>
                    <th>Équipe 1</th>
                    <th>vs</th>
                    <th>Équipe 2</th>
                    <th>Gymnase</th>
                    <th>Genre</th>
                    <th>Statut</th>
                </tr>
            </thead>
            <tbody>
"""
        
        for match in matches:
            is_fixed = match.get("is_fixed", False)
            genre = match.get("equipe1_genre", "M")
            row_class = ' class="fixed"' if is_fixed else ''
            
            html += f"""
                <tr{row_class}>
                    <td class="time">{match['horaire']}</td>
                    <td class="team">{match['equipe1_nom']}</td>
                    <td style="text-align: center; color: #95a5a6;">⚔️</td>
                    <td class="team">{match['equipe2_nom']}</td>
                    <td class="venue">{match['gymnase']}</td>
                    <td><span class="badge badge-{genre}">{genre}</span></td>
                    <td>{'<span class="badge badge-fixed">Fixé</span>' if is_fixed else ''}</td>
                </tr>
"""
        
        html += """
            </tbody>
        </table>
    </div>
"""
    
    html += """
</body>
</html>
"""
    
    # Sauvegarder
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return output_path

def main():
    print("=" * 70)
    print("GÉNÉRATION HTML BASIQUE (Tableau simple - pas de JavaScript)")
    print("=" * 70)
    
    # Charger la solution
    print("\n[1/3] Chargement de la solution...")
    solution = load_solution()
    assignments = solution.get("assignments", [])
    print(f"   ✓ {len(assignments)} matchs chargés")
    
    # Générer le HTML
    print("\n[2/3] Génération du tableau HTML...")
    output_path = "data_volley/calendrier_volley_BASIC.html"
    result_path = generate_basic_html_table(assignments, output_path)
    
    # Statistiques
    file_size = Path(result_path).stat().st_size
    print(f"   ✓ HTML généré: {result_path}")
    print(f"   ✓ Taille: {file_size:,} octets ({file_size/1024:.1f} KB)")
    
    # Compter les semaines
    weeks = set(a["semaine"] for a in assignments)
    print(f"   ✓ {len(weeks)} semaines")
    
    # Instructions
    print("\n[3/3] Fichier généré:")
    print(f"   📄 {result_path}")
    print(f"   → Tableau HTML simple et lisible")
    print(f"   → Groupé par semaine")
    print(f"   → Trié par horaire et gymnase")
    print(f"   → SANS JavaScript complexe")
    print(f"   → SANS vue agenda/calendrier")
    
    print("\n" + "=" * 70)
    print("✓ GÉNÉRATION TERMINÉE")
    print("=" * 70)
    print("\n💡 Ouvrez ce fichier pour vérifier les données brutes des matchs")
    print("   Si les données sont correctes ici, le problème vient du JavaScript")

if __name__ == "__main__":
    main()
