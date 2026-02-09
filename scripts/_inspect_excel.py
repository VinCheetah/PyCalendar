#!/usr/bin/env python3
"""Debug script to inspect Excel structure and indispos."""

import pandas as pd
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

excel_file = PROJECT_ROOT / "data/volleyball/config_volleyP2.xlsx"

print("=== Gymnases ===")
try:
    df_gyms = pd.read_excel(excel_file, sheet_name="Gymnases")
    print(df_gyms[['Gymnase', 'Capacite', 'Creneaux']].to_string())
except Exception as e:
    print(f"Error: {e}")

print("\n=== Indispos_Gymnases ===")
try:
    df_indispos = pd.read_excel(excel_file, sheet_name="Indispos_Gymnases")
    if len(df_indispos) == 0:
        print("Aucune indisponibilité trouvée")
    else:
        print(df_indispos.to_string())
except Exception as e:
    print(f"Error: {e}")
