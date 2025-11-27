# 📊 PenaltyCalculator - Documentation Complète

**Module** : `pycalendar.core.penalty_calculator`  
**Version** : 2.0 (Mise à jour 21 novembre 2025)  
**Objectif** : Calculer rétrospectivement toutes les pénalités d'un match planifié

---

## 🎯 Vue d'Ensemble

Le `PenaltyCalculator` calcule **toutes** les pénalités et contraintes présentes dans le solveur CP-SAT, permettant :

1. **Analyse de qualité** - Identifier les matchs avec pénalités élevées
2. **Filtrage de qualité** - Rejeter les affectations au-dessus d'un seuil
3. **Debugging** - Comprendre pourquoi un match est pénalisé
4. **Validation** - Vérifier que le solveur applique correctement les pénalités

---

## 📋 Pénalités Calculées (10 catégories)

### 1. **Horaires Préférés** (`horaire_prefere`)

**Objectif** : Pénaliser les matchs planifiés loin des horaires préférés des équipes

**Formule** :
```python
diff_minutes = abs(horaire_creneau - horaire_prefere) - tolerance
if diff_minutes > 0:
    penalite = (diff_minutes / diviseur) * poids
    # poids = penalite_avant_horaire_min (avant) ou penalite_apres_horaire_min (après)
```

**Paramètres config** :
- `penalite_avant_horaire_min` : Poids si avant horaire préféré
- `penalite_apres_horaire_min` : Poids si après horaire préféré
- `penalite_horaire_tolerance` : Minutes de tolérance (pas de pénalité)
- `penalite_horaire_diviseur` : Diviseur pour normaliser (généralement 60)

**Exemple** :
```python
# Horaire préféré: 18:00, planifié à 20:00
# diff = 120 min - 0 tolérance = 120 min
# penalite = (120 / 60) * 100 = 200
```

**Note** : Pénalité calculée **pour chaque équipe** du match

---

### 2. **Préférences Gymnases** (`gymnase_prefere`)

**Objectif** : Système de bonus inversé - pénalité de base moins les bonus

**Formule** :
```python
base_penalty = 2 * max(bonus_preferences_gymnases)
penalite = base_penalty

# Pour chaque équipe:
for rang, gymnase in enumerate(equipe.lieux_preferes):
    if gymnase == creneau.gymnase:
        penalite -= bonus_preferences_gymnases[rang]
        break
```

**Paramètres config** :
- `bonus_preferences_gymnases` : Liste de bonus par rang [bonus_rank1, bonus_rank2, ...]

**Exemple** :
```python
# bonus_preferences_gymnases = [500, 300, 100]
# base_penalty = 2 * 500 = 1000
# Équipe1 : Gym3 est rang 0 → pénalité -= 500 → 500
# Équipe2 : Gym3 est rang 2 → pénalité -= 100 → 400
# TOTAL = 500 + 400 = 900
```

---

### 3. **Niveau Gymnase** (`niveau_gymnase`)

**Objectif** : Pénaliser matchs haut niveau dans gymnases bas niveau (et vice versa)

**Formule** :
```python
niveau_match = A1=0, A2=1, A3=2, A4=3  # Extrait de la poule
niveau_gymnase = "haut" ou "bas"

if niveau_gymnase == "haut":
    penalite = penalite_niveau_gymnases_haut[niveau_match]
elif niveau_gymnase == "bas":
    penalite = penalite_niveau_gymnases_bas[niveau_match]
```

**Paramètres config** :
- `penalite_niveau_gymnases_haut` : Liste [A1, A2, A3, A4] pour gymnases "haut"
- `penalite_niveau_gymnases_bas` : Liste [A1, A2, A3, A4] pour gymnases "bas"

**Exemple** :
```python
# penalite_niveau_gymnases_bas = [8, 4, 2, 1]
# Match A1 (niveau_match=0) sur gymnase "bas" → pénalité = 8
# Match A4 (niveau_match=3) sur gymnase "bas" → pénalité = 1
```

**Note** : Valeurs positives = pénalité, valeurs négatives = bonus

---

### 4. **Espacement Repos** (`espacement`)

**Objectif** : Pénaliser matchs trop rapprochés pour une même équipe

**Formule** :
```python
for chaque autre match de l'équipe:
    semaine_diff = abs(semaine_match - semaine_autre)
    if semaine_diff < len(penalites_espacement_repos):
        penalite += penalites_espacement_repos[semaine_diff]
```

**Paramètres config** :
- `penalites_espacement_repos` : Liste [diff_0, diff_1, diff_2, ...]

**Exemple** :
```python
# penalites_espacement_repos = [5000, 2000, 1000, 500, 0]
# Match A en S1, Match B en S2 → diff = 1 → pénalité = 2000
# Match A en S1, Match C en S5 → diff = 4 → pénalité = 0
```

**Note** : Calculé **pour chaque équipe** du match

---

### 5. **Compaction Temporelle** (`compaction`)

**Objectif** : Prioriser les matchs en début de calendrier

**Formule** :
```python
if semaine <= len(compaction_penalites_par_semaine):
    penalite = compaction_penalites_par_semaine[semaine - 1]
else:
    penalite = compaction_penalites_par_semaine[-1]
```

**Paramètres config** :
- `compaction_temporelle_actif` : Activer/désactiver
- `compaction_penalites_par_semaine` : Liste [S1, S2, S3, ...]

**Exemple** :
```python
# compaction_penalites_par_semaine = [0, 10, 20, 30, 40]
# Match en S1 → pénalité = 0
# Match en S5 → pénalité = 40
```

---

### 6. **Overlap Institution** (`overlap`)

**Objectif** : Éviter que deux matchs de même institution jouent simultanément

**Formule** :
```python
for chaque autre match au même moment (semaine, horaire):
    institutions_match = {equipe1.institution, equipe2.institution}
    institutions_autre = {autre_eq1.institution, autre_eq2.institution}
    
    if institutions_match & institutions_autre:  # Intersection non vide
        penalite += overlap_institution_poids
```

**Paramètres config** :
- `overlap_institution_actif` : Activer/désactiver
- `overlap_institution_poids` : Poids de la pénalité (recommandé > 10^11)

**Exemple** :
```python
# overlap_institution_poids = 100000000000
# Match LYON 1 vs AUTRE à S1 18:00 Gym1
# Match LYON 1 vs AUTRE2 à S1 18:00 Gym2
# → Même institution (LYON 1) en simultané → pénalité = 100 milliards
```

---

### 7. **Aller-Retour Espacement** (`aller_retour`) ✨ NOUVEAU

**Objectif** : Espacer les matchs aller et retour

**Formule** :
```python
# Trouver le match retour (équipes inversées, même poule)
semaine_diff = abs(semaine_aller - semaine_retour)

if semaine_diff == 0:
    penalite = aller_retour_penalite_meme_semaine
elif semaine_diff == 1:
    penalite = aller_retour_penalite_consecutives
```

**Paramètres config** :
- `aller_retour_espacement_actif` : Activer/désactiver
- `aller_retour_min_semaines` : Espacement minimum recommandé
- `aller_retour_penalite_meme_semaine` : Pénalité si même semaine
- `aller_retour_penalite_consecutives` : Pénalité si semaines consécutives

**Exemple** :
```python
# aller_retour_penalite_meme_semaine = 5000
# aller_retour_penalite_consecutives = 2000
# Aller S1, Retour S1 → pénalité = 5000
# Aller S1, Retour S2 → pénalité = 2000
# Aller S1, Retour S4 → pénalité = 0 (OK)
```

---

### 8. **Contrainte Temporelle** (`contrainte_temporelle`) ✨ NOUVEAU

**Objectif** : Pénaliser matchs hors de la fenêtre temporelle autorisée (soft)

**Formule** :
```python
if contrainte exists and not contrainte.est_respectee(semaine):
    penalite = contrainte_temporelle_penalite
```

**Paramètres config** :
- `contrainte_temporelle_actif` : Activer/désactiver
- `contrainte_temporelle_dure` : Si True, contrainte dure (interdiction), sinon soft
- `contrainte_temporelle_penalite` : Poids de la pénalité

**Exemple** :
```python
# Match doit être en S1-S5, planifié en S7
# → pénalité = contrainte_temporelle_penalite
```

**Note** : Nécessite que la contrainte soit dans `match.metadata['contrainte_temporelle']`

---

### 9. **Guidance Qualité** (`guidance_qualite`) ✨ NOUVEAU

**Objectif** : Grosse pénalité dissuasive pour créneaux intrinsèquement mauvais

**Formule** :
```python
estimation = horaire_prefere + gymnase_prefere + niveau_gymnase
seuil = qualite_match_seuil * 0.5

if estimation > seuil:
    penalite = 100000  # Grosse pénalité dissuasive
```

**Paramètres config** :
- `qualite_match_actif` : Activer/désactiver le filtrage qualité
- `qualite_match_guidance_cpsat` : Activer la guidance dans CP-SAT
- `qualite_match_seuil` : Seuil qualité (50% utilisé pour estimation)

**Exemple** :
```python
# qualite_match_seuil = 100
# estimation = 30 (horaire) + 40 (gymnase) + 20 (niveau) = 90
# seuil_estimation = 100 * 0.5 = 50
# 90 > 50 → pénalité = 100000
```

---

## 🔧 Utilisation

### Calcul Simple

```python
from pycalendar.core.penalty_calculator import PenaltyCalculator

calculator = PenaltyCalculator(config, all_matches, niveaux_gymnases)
penalties = calculator.calculate_match_penalties(match)

print(f"Total: {penalties['total']}")
print(f"Horaire: {penalties['horaire_prefere']}")
print(f"Gymnase: {penalties['gymnase_prefere']}")
```

### Annotation de Solution

```python
from pycalendar.core.penalty_calculator import annotate_solution_with_penalties

# Ajoute penalties dans match.metadata['penalties'] pour tous les matchs
annotate_solution_with_penalties(solution, config, niveaux_gymnases)

# Accès aux pénalités
for match in solution.matchs_planifies:
    total = match.metadata['penalties']['total']
    print(f"{match.nom}: {total}")
```

---

## 📊 Équivalence avec CP-SAT

Le `PenaltyCalculator` reproduit **exactement** les pénalités du solveur CP-SAT :

| Catégorie | CP-SAT (lignes) | PenaltyCalculator |
|-----------|-----------------|-------------------|
| Horaires préférés | 1205-1230 | `_calculate_preferred_time_penalty` |
| Préférences gymnases | 813-838 | `_calculate_gym_preference_penalty` |
| Niveau gymnase | 840-873 | `_calculate_gym_level_penalty` |
| Espacement repos | 876-928 | `_calculate_spacing_penalty` |
| Compaction temporelle | 930-946 | `_calculate_compaction_penalty` |
| Overlap institution | 948-1015 | `_calculate_overlap_penalty` |
| Aller-retour | 1017-1057 | `_calculate_aller_retour_penalty` |
| Contrainte temporelle | 800-810 | `_calculate_contrainte_temporelle_penalty` |
| Guidance qualité | 1062-1131 | `_calculate_guidance_qualite_penalty` |

---

## ⚙️ Paramètres Config Requis

```python
# Horaires
config.penalite_avant_horaire_min
config.penalite_apres_horaire_min
config.penalite_horaire_tolerance
config.penalite_horaire_diviseur

# Gymnases
config.bonus_preferences_gymnases
config.penalite_niveau_gymnases_haut
config.penalite_niveau_gymnases_bas

# Espacement/Compaction
config.penalites_espacement_repos
config.compaction_temporelle_actif
config.compaction_penalites_par_semaine

# Overlap
config.overlap_institution_actif
config.overlap_institution_poids

# Aller-retour
config.aller_retour_espacement_actif
config.aller_retour_min_semaines
config.aller_retour_penalite_meme_semaine
config.aller_retour_penalite_consecutives

# Contrainte temporelle
config.contrainte_temporelle_actif
config.contrainte_temporelle_dure
config.contrainte_temporelle_penalite

# Guidance qualité
config.qualite_match_actif
config.qualite_match_guidance_cpsat
config.qualite_match_seuil
```

---

## ✅ Tests de Validation

Le module est testé dans `test_penalty_calculator.py` :

```bash
$ PYTHONPATH=src python test_penalty_calculator.py

✅ Test 1 : PenaltyCalculator basique
✅ Test 2 : PenaltyCalculator avec niveaux de gymnase
✅ Test 3 : Annotation d'une solution

🎉 Tous les tests passent !
```

---

## 🚀 Nouveautés v2.0

1. ✨ **Aller-retour espacement** - Pénaliser aller/retour trop rapprochés
2. ✨ **Contrainte temporelle** - Pénalité soft pour fenêtres temporelles
3. ✨ **Guidance qualité** - Dissuasion forte pour créneaux mauvais
4. 📊 **Documentation complète** - Ce fichier
5. ✅ **100% couverture** - Toutes les pénalités CP-SAT implémentées

---

## 📝 Notes Importantes

### Contraintes Dures vs Soft

Certaines contraintes CP-SAT sont **dures** (interdiction) et n'apparaissent pas dans le PenaltyCalculator :

- **Capacité gymnases** - Impossible de planifier > capacité
- **Indisponibilités équipes** - Match impossible si équipe indisponible
- **Non-simultanéité** - Équipe ne peut jouer 2x en même temps
- **Matchs fixés** - Créneaux imposés non modifiables
- **Obligations présence** - Gymnase réservé à institution
- **Max matchs/semaine** - Limite dure par équipe

Ces contraintes sont **respectées** par le solveur (solution infaisable sinon).

### Bonus Progressif (Équilibrage)

Le système de bonus progressif pour l'équilibrage max-min n'est **pas** calculé rétrospectivement car il dépend de l'ordre de planification global, pas du match individuel.

**Formule CP-SAT** :
```python
bonus(n) = bonus_base × (facteur_decroissance ^ n)
# n = nombre de matchs déjà planifiés pour l'équipe
```

Impossible à recalculer sans connaître l'ordre exact de planification.

---

## 🔗 Références

- **Code source** : `src/pycalendar/core/penalty_calculator.py`
- **Solveur CP-SAT** : `src/pycalendar/solvers/cpsat_solver.py`
- **Tests** : `test_penalty_calculator.py`
- **Configuration** : `src/pycalendar/core/config.py`

---

**Version** : 2.0  
**Date** : 21 novembre 2025  
**Auteur** : PyCalendar Team  
**Status** : ✅ Production Ready
