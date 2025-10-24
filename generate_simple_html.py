#!/usr/bin/env python3
"""
Script pour générer un HTML simplifié avec l'ancien format des matchs.
Pas de scores, pas de métadonnées complexes - juste les matchs basiques.
"""

import json
from pathlib import Path
from datetime import datetime

def load_solution():
    """Charge la solution depuis latest_volley.json."""
    solution_path = Path("solutions/latest_volley.json")
    with open(solution_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def simplify_match_data(assignments):
    """Convertit les assignments en format simple (comme l'ancien format)."""
    simple_matches = []
    
    for i, assignment in enumerate(assignments, 1):
        # Format simple mais compatible avec le code JavaScript
        # Les clés DOIVENT correspondre à celles attendues par le code JS
        simple_match = {
            "match_id": assignment.get("match_id", i-1),  # ID du match (commence à 0)
            "equipe1": assignment["equipe1_nom"],
            "equipe2": assignment["equipe2_nom"],
            "equipe1_genre": assignment.get("equipe1_genre", "M"),
            "equipe2_genre": assignment.get("equipe2_genre", "M"),
            "horaire": assignment["horaire"],  # CLEF ATTENDUE: horaire (pas heure!)
            "gymnase": assignment["gymnase"],
            "semaine": assignment["semaine"],
            "poule": assignment.get("poule", "Inconnu"),
            "genre": assignment.get("equipe1_genre", "M"),
            "is_fixed": assignment.get("is_fixed", False),
            # PAS de score, status, ou autres métadonnées complexes
        }
        simple_matches.append(simple_match)
    
    return simple_matches

def generate_simple_html(simple_matches, output_path):
    """Génère un HTML avec le format simplifié."""
    
    # Charger le template HTML
    template_path = Path("visualization/templates/main.html")
    with open(template_path, 'r', encoding='utf-8') as f:
        html_template = f.read()
    
    # Charger les composants (CSS + JS)
    components_dir = Path("visualization/components")
    
    # CSS
    css_path = components_dir / "styles.css"
    with open(css_path, 'r', encoding='utf-8') as f:
        css_content = f.read()
    css_html = f'<style>\n{css_content}\n</style>'
    
    # JavaScript modules (dans le bon ordre)
    js_modules = [
        'utils.js',
        'data-manager.js',
        'penalty-calculator.js',
        'match-card.js',
        'calendar-view.js',
        'calendar-grid-view.js',
        'penalties-view.js',
        'filters.js',
        'slot-manager.js',
        'edit-modal.js',
        'conflict-detector.js',
        'auto-resolver.js',
        'history-manager.js',
        'panels-ui.js'
    ]
    
    js_html = ''
    for module in js_modules:
        module_path = components_dir / module
        if module_path.exists():
            with open(module_path, 'r', encoding='utf-8') as f:
                js_content = f.read()
            js_html += f'<script>\n{js_content}\n</script>\n'
    
    # Remplacer les placeholders
    html_content = html_template.replace('<!-- STYLES_PLACEHOLDER -->', css_html)
    html_content = html_content.replace('<!-- SCRIPTS_PLACEHOLDER -->', js_html)
    
    # Injecter les données SIMPLIFIÉES
    html_content = html_content.replace(
        '{{MATCHES_DATA}}',
        json.dumps(simple_matches, ensure_ascii=False, indent=2)
    )
    
    # Données vides pour unscheduled et slots (pas besoin pour ce test)
    html_content = html_content.replace(
        '{{UNSCHEDULED_DATA}}',
        json.dumps([], ensure_ascii=False)
    )
    html_content = html_content.replace(
        '{{AVAILABLE_SLOTS_DATA}}',
        json.dumps([], ensure_ascii=False)
    )
    
    # Configuration des pénalités (valeurs par défaut pour le test)
    penalty_config = {
        'weight': 10.0,
        'penaltyBeforeOne': 100.0,
        'penaltyBeforeBoth': 300.0,
        'divisor': 60.0,
        'tolerance': 0.0
    }
    html_content = html_content.replace(
        '{{PENALTY_CONFIG}}',
        json.dumps(penalty_config, ensure_ascii=False)
    )
    
    # Sauvegarder
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return output_path

def main():
    print("=" * 70)
    print("GÉNÉRATION HTML SIMPLIFIÉ (Format ancien - sans scores)")
    print("=" * 70)
    
    # Charger la solution
    print("\n[1/4] Chargement de la solution...")
    solution = load_solution()
    assignments = solution.get("assignments", [])
    print(f"   ✓ {len(assignments)} matchs chargés")
    
    # Simplifier les données
    print("\n[2/4] Simplification des données (format ancien)...")
    simple_matches = simplify_match_data(assignments)
    print(f"   ✓ {len(simple_matches)} matchs simplifiés")
    print(f"   ✓ Format: match_id, equipe1, equipe2, horaire, gymnase, semaine, genre")
    print(f"   ✓ SANS: scores, status, penalties, metadata complexes")
    
    # Générer le HTML
    print("\n[3/4] Génération du HTML simplifié...")
    output_path = "data_volley/calendrier_volley_SIMPLE.html"
    result_path = generate_simple_html(simple_matches, output_path)
    
    # Statistiques
    file_size = Path(result_path).stat().st_size
    print(f"   ✓ HTML généré: {result_path}")
    print(f"   ✓ Taille: {file_size:,} octets ({file_size/1024:.1f} KB)")
    
    # Instructions
    print("\n[4/4] Test à effectuer:")
    print(f"   1. Ouvrez: {result_path}")
    print(f"   2. Vérifiez si les matchs sont bien positionnés")
    print(f"   3. Vérifiez si l'alignement est correct")
    print(f"   4. Comparez avec calendrier_volley.html (version avec scores)")
    
    print("\n" + "=" * 70)
    print("✓ GÉNÉRATION TERMINÉE")
    print("=" * 70)
    
    # Afficher un exemple de match simplifié
    print("\nExemple de match simplifié (format JSON):")
    print(json.dumps(simple_matches[0], ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
