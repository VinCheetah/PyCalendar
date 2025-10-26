# 📊 Analyse de Migration v1.0 → v2.0

## Vue d'ensemble

Ce document analyse les différences entre les formats v1.0 et v2.0 des solutions PyCalendar et documente les améliorations nécessaires.

---

## Format v1.0 (Actuel - `solutions/latest_volley.json`)

### Structure
```json
{
  "metadata": {
    "date": "ISO-8601",
    "solution_name": "volley",
    "config_name": "path/to/config.xlsx",
    "solver": "cpsat",
    "status": "FEASIBLE|OPTIMAL",
    "score": 1615395.0,
    "matchs_planifies": 243,
    "matchs_non_planifies": 23,
    "matchs_fixes": 81
  },
  "config_signature": { /* hash et structure */ },
  "assignments": [
    {
      "match_id": 0,
      "equipe1_nom": "LYON 1 (1)",
      "equipe1_genre": "M",
      "equipe1_id": "LYON 1 (1)|M",
      "equipe2_nom": "LYON 2 (1)",
      "equipe2_genre": "M",
      "equipe2_id": "LYON 2 (1)|M",
      "poule": "M_Pool_1",
      "semaine": 1,
      "horaire": "18h00",
      "gymnase": "Gymnase A",
      "is_fixed": false
    }
  ]
}
```

### ✅ Forces
- Compact et simple
- Contient les assignments essentiels
- Inclut signature de configuration pour warm-start

### ❌ Limitations
- **Pas d'entités séparées** : équipes, gymnases, poules mélangés dans assignments
- **Données manquantes** : horaires_preferes, semaines_indisponibles, capacités gymnases
- **Pas de slots** : impossible de savoir quels créneaux sont disponibles
- **Pas de statistiques** : calculs faits côté interface
- **Pas de pénalités** : impossible d'analyser la qualité des solutions

---

## Format v2.0 (Cible - `output/latest_volley_v2.json`)

### Structure complète

```json
{
  "version": "2.0",
  "generated_at": "ISO-8601",
  
  "metadata": {
    "solution_name": "volley",
    "solver": "cpsat",
    "status": "FEASIBLE",
    "score": 1615395.0,
    "execution_time_seconds": 45.2
  },
  
  "config": {
    "hash": "b6113cc31dc33f0df4533ccf66c81cd2",
    "nb_semaines": 14,
    "semaine_min": 1,
    "strategie": "cpsat",
    "temps_max_secondes": 300,
    "constraints": {
      "poids_indisponibilite": 1000,
      "poids_capacite_gymnase": 500,
      /* ... autres contraintes */
    }
  },
  
  "entities": {
    "equipes": [
      {
        "id": "LYON 1 (1)|M",
        "nom": "LYON 1 (1)",
        "nom_complet": "LYON 1 (1)",
        "institution": "LYON 1",
        "numero_equipe": "1",
        "genre": "M",
        "poule": "Excellence M",
        "horaires_preferes": ["18h00", "20h00"],
        "lieux_preferes": ["Gymnase A"],
        "semaines_indisponibles": {
          "3": ["18h00", "20h00"],
          "5": ["18h00"]
        }
      }
    ],
    "gymnases": [
      {
        "id": "Gymnase A",
        "nom": "Gymnase A",
        "capacite": 2,
        "horaires_disponibles": ["18h00", "20h00", "21h30"],
        "semaines_indisponibles": {
          "7": ["18h00"]
        },
        "capacite_reduite": {
          "5": {"18h00": 1}
        }
      }
    ],
    "poules": [
      {
        "id": "Excellence M",
        "nom": "Excellence M",
        "genre": "M",
        "niveau": "Excellence",
        "nb_equipes": 10,
        "equipes_ids": ["LYON 1 (1)|M", "LYON 2 (1)|M", ...],
        "nb_matchs_planifies": 45,
        "nb_matchs_non_planifies": 0
      }
    ]
  },
  
  "matches": {
    "scheduled": [
      {
        "match_id": "M_0001",
        "equipe1_id": "LYON 1 (1)|M",
        "equipe1_nom": "LYON 1 (1)",
        "equipe1_nom_complet": "LYON 1 (1)",
        "equipe1_institution": "LYON 1",
        "equipe1_genre": "M",
        "equipe1_horaires_preferes": ["18h00", "20h00"],
        "equipe2_id": "LYON 2 (1)|M",
        "equipe2_nom": "LYON 2 (1)",
        "equipe2_nom_complet": "LYON 2 (1)",
        "equipe2_institution": "LYON 2",
        "equipe2_genre": "M",
        "equipe2_horaires_preferes": ["18h00"],
        "poule": "Excellence M",
        "semaine": 1,
        "horaire": "18h00",
        "gymnase": "Gymnase A",
        "is_fixed": false,
        "is_entente": false,
        "is_external": false,
        "score": {
          "equipe1": null,
          "equipe2": null,
          "has_score": false
        },
        "penalties": {
          "total": 0.0,
          "horaire_prefere": 0.0,
          "espacement": 0.0,
          "indisponibilite": 0.0,
          "compaction": 0.0,
          "overlap": 0.0
        }
      }
    ],
    "unscheduled": [
      {
        "match_id": "M_0245",
        "equipe1_id": "LYON 3 (2)|F",
        "equipe2_id": "LYON 1 (5)|F",
        "poule": "N1 F",
        "reason": "Aucun créneau disponible",
        "constraints_violated": ["capacity", "availability"]
      }
    ]
  },
  
  "slots": {
    "available": [
      {
        "slot_id": "S_GymnaseA_1_18h00",
        "gymnase": "Gymnase A",
        "semaine": 1,
        "horaire": "18h00",
        "status": "libre"
      }
    ],
    "occupied": [
      {
        "slot_id": "S_GymnaseA_2_18h00",
        "gymnase": "Gymnase A",
        "semaine": 2,
        "horaire": "18h00",
        "status": "occupé",
        "match_id": "M_0001"
      }
    ]
  },
  
  "statistics": {
    "global": {
      "taux_planification": 91.3,
      "score_total": 1615395.0,
      "score_moyen_par_match": 6646.9,
      "nb_matchs_total": 266,
      "nb_matchs_planifies": 243,
      "nb_matchs_non_planifies": 23,
      "nb_matchs_fixes": 81,
      "nb_matchs_auto": 162
    },
    "par_semaine": {
      "1": {
        "nb_matchs": 20,
        "par_horaire": {
          "18h00": 10,
          "20h00": 10
        }
      }
    },
    "par_poule": {
      "Excellence M": {
        "nb_matchs_planifies": 45,
        "nb_matchs_non_planifies": 0,
        "taux_completion": 100.0
      }
    },
    "par_gymnase": {
      "Gymnase A": {
        "nb_matchs": 50,
        "capacite": 2,
        "taux_occupation": 89.3
      }
    },
    "par_equipe": {
      "LYON 1 (1)|M": {
        "nb_matchs_planifies": 9,
        "nb_matchs_non_planifies": 0,
        "horaires_repartition": {
          "18h00": 5,
          "20h00": 4
        }
      }
    }
  }
}
```

---

## Données manquantes dans DataFormatter actuel

### ❌ Problèmes identifiés

1. **Entités incomplètes**
   - `horaires_preferes` : vide (doit venir de Config)
   - `lieux_preferes` : vide (doit venir de Config)
   - `semaines_indisponibles` : vide (doit venir de Config)
   - Gymnases : capacités, horaires_disponibles, capacite_reduite manquants

2. **Matches incomplets**
   - `priorite` : manquant dans le schema
   - `is_entente` : non calculé correctement
   - `penalties` : TODO - pas calculées

3. **Slots**
   - Logique correcte mais dépend de `creneaux_disponibles` passé en paramètre
   - Besoin de tous les créneaux (pas juste ceux utilisés)

4. **Statistics**
   - `taux_occupation` gymnases : placeholder 0.0
   - Manque de stats par institution
   - Manque de détection de conflits

---

## Plan d'amélioration

### Phase 1 : Enrichissement des entités ✅
- [x] Passer les objets Equipe complets à DataFormatter
- [x] Passer les objets Gymnase complets
- [x] Extraire horaires_preferes, semaines_indisponibles depuis Equipe
- [x] Extraire capacite, horaires_disponibles depuis Gymnase

### Phase 2 : Calcul des créneaux complets ✅
- [x] Générer TOUS les créneaux possibles (pas juste disponibles)
- [x] Calculer available = tous - occupés
- [x] Calculer occupied depuis matchs_planifies

### Phase 3 : Infrastructure pénalités 🔄
- [ ] Créer PenaltyCalculator avec méthodes séparées par type
- [ ] Documenter chaque type de pénalité
- [ ] Ajouter TODOs clairs pour implémentation future
- [ ] Retourner structure complète même avec valeurs 0.0

### Phase 4 : Statistics complètes 🔄
- [ ] Calculer taux_occupation réel des gymnases
- [ ] Ajouter stats par institution
- [ ] Détecter overlaps et conflits
- [ ] Ajouter métriques de qualité

### Phase 5 : Validation 🔄
- [ ] Installer jsonschema
- [ ] Créer validateur avec rapports détaillés
- [ ] Intégrer dans pipeline de sauvegarde
- [ ] Tests automatiques

### Phase 6 : Intégration pipeline 🔄
- [ ] Modifier solution_store.save_solution_v2 pour utiliser DataFormatter
- [ ] Supprimer appel à convert_solution_to_v2.py
- [ ] Nettoyer le code legacy
- [ ] Mettre à jour documentation

---

## Bénéfices attendus

✅ **Génération directe** : Plus de conversion intermédiaire  
✅ **Données complètes** : Toutes les infos nécessaires à l'interface  
✅ **Maintenabilité** : Code centralisé dans DataFormatter  
✅ **Validation** : Garantie de conformité au schema  
✅ **Extensibilité** : Facile d'ajouter nouvelles stats/pénalités  

---

**Date de création** : 2025-10-26  
**Status** : 🚧 En cours de migration
