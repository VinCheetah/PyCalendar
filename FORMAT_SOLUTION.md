# Formats de Solution PyCalendar

## Vue d'ensemble

PyCalendar supporte deux formats de sauvegarde de solutions :

- **v1.0** (Legacy) : Format simple avec assignments uniquement
- **v2.0** (Recommandé) : Format enrichi avec entités, poules, statistiques

## Configuration du format

Dans votre fichier YAML de configuration (`configs/config_volley.yaml`, etc.) :

```yaml
fichiers:
  donnees: "data_volley/config_volley.xlsx"
  sortie: "data_volley/calendrier_volley.xlsx"
  solution_format: "v2.0"  # v2.0 (défaut) ou v1.0
```

## Format v2.0 (Recommandé)

**Utilisation** : Interface web, analyse avancée, visualisation

**Avantages** :
- ✅ Poules automatiquement détectées et préservées (VBFA1PA, VBMA2PB, etc.)
- ✅ Informations complètes sur les équipes (institution, genre, préférences)
- ✅ Statistiques de la solution (taux de planification, pénalités)
- ✅ Slots disponibles et occupés
- ✅ Prêt pour l'interface HTML (pas de conversion nécessaire)

**Fichiers générés** :
```
solutions/
├── latest_volley_v2.json          # Dernière solution v2.0
├── solution_volley_v2_2025-10-24_193045.json  # Timestampé
├── latest_volley.json              # Format v1.0 (aussi généré)
└── solution_volley_2025-10-24_193045.json     # v1.0 timestampé
```

**Structure** :
```json
{
  "version": "2.0",
  "generated_at": "2025-10-24T19:30:45",
  "metadata": {...},
  "config": {...},
  "entities": {
    "equipes": [...],    // 132 équipes avec poules
    "gymnases": [...],   // 9 gymnases
    "poules": [...]      // 30 poules (VBFA1PA, etc.)
  },
  "matches": {
    "scheduled": [...],   // 243 matchs enrichis
    "unscheduled": []
  },
  "slots": {
    "available": [...],   // 665 créneaux libres
    "occupied": [...]     // 243 créneaux occupés
  },
  "statistics": {...}
}
```

**Workflow** :
```bash
# 1. Générer la solution (format v2.0 par défaut)
python main.py configs/config_volley.yaml

# 2. L'interface est générée automatiquement
#    Ouvrir solutions/latest_volley_v2.json dans l'interface
```

## Format v1.0 (Legacy)

**Utilisation** : Rétrocompatibilité, export simple

**Avantages** :
- ✅ Format compact
- ✅ Compatible avec anciennes versions
- ✅ Facile à parser

**Fichiers générés** :
```
solutions/
├── latest_volley.json
└── solution_volley_2025-10-24_193045.json
```

**Structure** :
```json
{
  "metadata": {...},
  "config_signature": {...},
  "assignments": [
    {
      "match_id": 0,
      "equipe1_nom": "LYON 1 (1)",
      "equipe1_genre": "F",
      "equipe1_id": "LYON 1 (1)|F",
      "equipe2_nom": "INSA (2)",
      "equipe2_genre": "F",
      "equipe2_id": "INSA (2)|F",
      "poule": "VBFA1PA",  // ✅ Maintenant inclus !
      "semaine": 1,
      "horaire": "14:00",
      "gymnase": "ECL",
      "is_fixed": false
    }
  ]
}
```

**Workflow** :
```bash
# 1. Configurer pour v1.0
#    Dans config_volley.yaml: solution_format: "v1.0"

# 2. Générer la solution
python main.py configs/config_volley.yaml

# 3. Convertir manuellement vers v2.0 (si besoin)
python scripts/convert_solution_to_v2.py solutions/latest_volley.json
```

## Migration v1.0 → v2.0

### Option 1 : Passer au format v2.0 par défaut

Dans votre config YAML :
```yaml
fichiers:
  solution_format: "v2.0"  # Changez de "v1.0" à "v2.0"
```

Puis relancez `python main.py` → génère directement v2.0

### Option 2 : Convertir une ancienne solution

```bash
# Convertir latest_volley.json → latest_volley_v2.json
python scripts/convert_solution_to_v2.py solutions/latest_volley.json

# Le script détecte automatiquement si les poules sont présentes
# Si oui → utilise les vraies poules (VBFA1PA, etc.)
# Si non → clustering automatique (F_Pool_1, etc.)
```

## Détails techniques

### Poules dans v2.0

Le format v2.0 **préserve les vraies poules** depuis le fichier Excel :

**Avec poule dans le JSON v1.0** (main.py avec solution_format: "v2.0") :
```
✅ Poules trouvées dans les données
→ VBFA1PA, VBFA1PB, VBMA1PA, ... (30 poules)
```

**Sans poule dans le JSON v1.0** (ancien format) :
```
⚠️ Poules manquantes → Détection automatique par clustering
→ F_Pool_1, F_Pool_2, M_Pool_1, ... (8 poules détectées)
```

### Modification du code

Le changement s'est fait dans `core/solution_store.py` :

```python
# Nouvelle méthode save_solution_v2()
# 1. Sauvegarde d'abord au format v1.0 (avec poule)
# 2. Puis convertit automatiquement vers v2.0
# 3. Génère les deux versions (v1.0 + v2.0)
```

Et dans `orchestrator/pipeline.py` :

```python
# Détection du format depuis la config
format_version = self.config.solution_format  # "v1.0" ou "v2.0"

if format_version == 'v2.0':
    store.save_solution_v2(...)  # Format enrichi
else:
    store.save_solution(...)      # Format legacy
```

## Recommandations

✅ **Utiliser v2.0 par défaut** : Meilleure pour l'interface et l'analyse  
✅ **Les deux formats sont générés** : Vous avez toujours le v1.0 en backup  
✅ **Les poules sont préservées** : Plus besoin de conversion manuelle  
⚠️ **v1.0 uniquement si besoin de rétrocompatibilité**

## Questions fréquentes

**Q: Est-ce que je perds quelque chose en passant à v2.0 ?**  
R: Non, le format v1.0 est aussi généré automatiquement.

**Q: Comment revenir au format v1.0 ?**  
R: Changez `solution_format: "v1.0"` dans votre config YAML.

**Q: Les anciennes solutions v1.0 fonctionnent-elles encore ?**  
R: Oui, utilisez `scripts/convert_solution_to_v2.py` pour les convertir.

**Q: Quelle est la taille des fichiers ?**  
R: v1.0 ≈ 50 KB, v2.0 ≈ 380 KB (plus de détails mais toujours rapide).

## Support

Pour toute question : voir le fichier principal `README.md`
