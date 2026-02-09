#!/usr/bin/env python3
"""Debug indispos application."""
import sys
sys.path.insert(0, "src")
from pycalendar.core.config import Config
from pycalendar.core.calendar_manager import CalendarConfig, CalendarManager
from pycalendar.data.data_source import DataSource

config = Config.from_yaml("configs/config_volleyP2.yaml")
cal_cfg = CalendarConfig(
    date_debut=config.calendrier_date_debut,
    jour_match=config.calendrier_jour_match,
    semaines_banalisees=config.calendrier_semaines_banalisees,
)
cal_mgr = CalendarManager(cal_cfg)
datasource = DataSource("data/volleyball/config_volleyP2.xlsx", calendar_manager=cal_mgr)
gymnases = datasource.charger_gymnases()

# Vérifier LYON 2 HC qui a des indispos
lyon = [g for g in gymnases if g.nom == "LYON 2 HC"][0]
print(f"LYON 2 HC - Capacité: {lyon.capacite}")
print(f"LYON 2 HC - Horaires: {lyon.horaires_disponibles}")
print(f"LYON 2 HC - Semaines indispos: {lyon.semaines_indisponibles}")
print(f"LYON 2 HC - Capacités réduites: {lyon.capacite_reduite}")

# Tester quelques créneaux
print("\nTesting availability:")
print("S1 14:00:", lyon.get_capacite_disponible(1, "14:00"))
print("S1 18:00:", lyon.get_capacite_disponible(1, "18:00"))
print("S2 14:00:", lyon.get_capacite_disponible(2, "14:00"))
print("S2 18:00:", lyon.get_capacite_disponible(2, "18:00"))
