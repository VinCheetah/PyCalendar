#!/usr/bin/env python3
"""
Exemple simple d'utilisation de l'interface PyCalendar
"""

from pathlib import Path
import json
from interface.core.generator import InterfaceGenerator

# Chemins
SOLUTIONS_DIR = Path(__file__).parent / "solutions"
OUTPUT_FILE = Path(__file__).parent / "calendrier_exemple.html"

# Charger une solution
solution_file = SOLUTIONS_DIR / "latest_volley.json"

if not solution_file.exists():
    print(f"❌ Solution introuvable: {solution_file}")
    print("Exécutez d'abord: python main.py --config configs/config_volley.yaml")
    exit(1)

# Lire le JSON
with open(solution_file, 'r', encoding='utf-8') as f:
    solution_data = json.load(f)

print(f"✅ Solution chargée: {solution_file.name}")
print(f"   Matchs planifiés: {len(solution_data.get('assignments', []))}")

# Générer l'interface
generator = InterfaceGenerator()

html_path = generator.generate(
    solution=solution_data,
    output_path=OUTPUT_FILE,
    config=None,  # Config optionnelle
    solution_name="latest_volley"
)

print(f"\n✅ Interface générée: {html_path}")
print(f"📦 Taille: {Path(html_path).stat().st_size / 1024:.1f} KB")
print(f"\n🌐 Ouvrez {OUTPUT_FILE.name} dans votre navigateur!")
