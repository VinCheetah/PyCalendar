# Documentation du Système de Contraintes PyCalendar

## Vue d'ensemble

PyCalendar utilise un système de contraintes sophistiqué pour planifier les matchs sportifs. Les contraintes sont divisées en deux catégories :

- **Contraintes DURES (hard)** : Doivent être respectées (poids élevés > 500)
- **Contraintes SOUPLES (soft)** : Préférences à optimiser (poids < 500)

## Architecture

### Deux Solveurs Complémentaires

1. **CP-SAT (OR-Tools)** : Solver optimal basé sur la programmation par contraintes
   - Garantit la solution optimale si trouvée dans le temps imparti
   - Plus lent mais plus précis
   - Fichier : `solvers/cpsat_solver.py`

2. **Greedy** : Solver heuristique rapide
   - Solution approximative mais calcul très rapide
   - Utilisé en fallback si CP-SAT échoue
   - Fichier : `solvers/greedy_solver.py`

**IMPORTANT** : Les deux solveurs utilisent **EXACTEMENT** la même logique de pénalités pour garantir la cohérence.

## Contraintes Dures (Hard Constraints)

### 1. TeamAvailabilityConstraint
**Fichier** : `constraints/team_constraints.py`
**Poids** : `poids_indisponibilite` (défaut: 1000.0)

Vérifie que les deux équipes sont disponibles pendant la semaine du match.

```python
if not match.equipe1.est_disponible(creneau.semaine):
    return False, self.weight
```

### 2. VenueCapacityConstraint
**Fichier** : `constraints/venue_constraints.py`
**Poids** : `poids_capacite_gymnase` (défaut: 500.0)

Vérifie que la capacité du gymnase n'est pas dépassée.

```python
if matchs_au_creneau >= gymnase.capacite:
    return False, self.weight
```

### 3. VenueAvailabilityConstraint
**Fichier** : `constraints/venue_constraints.py`
**Poids** : `poids_indisponibilite` (défaut: 1000.0)

Vérifie que le gymnase est disponible au créneau demandé.

### 4. TeamNotPlayingSimultaneouslyConstraint
**Fichier** : `constraints/team_constraints.py`
**Poids** : `poids_indisponibilite` (défaut: 1000.0)

Empêche une équipe de jouer plusieurs matchs en même temps.

**IMPORTANT** : Utilise `id_unique` pour distinguer les équipes de même nom mais de genre différent.

### 5. MaxMatchesPerWeekConstraint
**Fichier** : `constraints/team_constraints.py`
**Poids** : `poids_capacite_gymnase` (défaut: 500.0)
**Paramètre** : `max_matchs_par_equipe_par_semaine` (défaut: 1)

Limite le nombre de matchs qu'une équipe peut jouer par semaine.

**IMPORTANT** : Utilise également `id_unique`.

### 6. VenuePresenceObligationConstraint
**Fichier** : `constraints/venue_constraints.py`
**Poids** : `poids_indisponibilite` (défaut: 1000.0)

Si un gymnase a une obligation de présence pour une institution, au moins une des équipes du match doit appartenir à cette institution.

## Contraintes Souples (Soft Constraints)

### 1. MinSpacingConstraint ⭐ (Nouvelle version avec liste de pénalités)
**Fichier** : `constraints/schedule_constraints.py`
**Paramètre** : `penalites_espacement_repos` (liste de floats)
**Défaut** : `[100.0, 50.0, 10.0]`

Pénalise les matchs d'une même équipe en fonction du nombre de semaines de repos entre matchs consécutifs.

#### Logique de Calcul

Pour chaque équipe, la contrainte :
1. Identifie le match précédent le plus proche
2. Calcule le nombre de semaines de repos : `repos = |semaine_actuelle - semaine_precedente| - 1`
3. Applique la pénalité correspondante depuis la liste

#### Configuration de la Liste

```yaml
penalites_espacement_repos: [100.0, 50.0, 10.0]
```

Signification :
- **Index 0** (100.0) : Pénalité si 0 semaine de repos (matchs semaines consécutives)
- **Index 1** (50.0) : Pénalité si 1 semaine de repos (1 semaine d'écart)
- **Index 2** (10.0) : Pénalité si 2 semaines de repos
- **Index >= longueur** : Pénalité = 0 (espacement suffisant)

#### Exemples Concrets

Avec `penalites_espacement_repos: [100.0, 50.0, 10.0]` :

| Match précédent | Match actuel | Semaines de repos | Pénalité |
|-----------------|--------------|-------------------|----------|
| Semaine 3 | Semaine 4 | 0 (consécutif) | 100.0 ⚠️⚠️ |
| Semaine 3 | Semaine 5 | 1 | 50.0 ⚠️ |
| Semaine 3 | Semaine 6 | 2 | 10.0 |
| Semaine 3 | Semaine 7 | 3 | 0.0 ✅ |
| Semaine 3 | Semaine 10 | 6 | 0.0 ✅ |

#### Implémentation dans les Solveurs

✅ **Greedy** (`schedule_constraints.py` lignes 8-75) :
```python
def validate(self, match, creneau, solution_state):
    # Pour chaque équipe, trouver le match le plus récent
    if derniers_matchs_equipe:
        semaine_plus_proche = min(derniers_matchs_equipe, 
                                 key=lambda s: abs(s - creneau.semaine))
        weeks_rest = abs(creneau.semaine - semaine_plus_proche) - 1
        penalty += self._get_penalty_for_rest(weeks_rest)
```

✅ **CP-SAT** (`cpsat_solver.py` lignes 327-370) :
```python
# Pour chaque équipe et chaque paire de semaines
for semaine1 in range(1, nb_semaines + 1):
    for semaine2 in range(semaine1 + 1, nb_semaines + 1):
        weeks_rest = semaine2 - semaine1 - 1
        if weeks_rest < len(penalites_espacement_repos):
            penalty_value = penalites_espacement_repos[weeks_rest]
            # Créer variables pour détecter si équipe joue aux 2 semaines
            plays_both = model.NewBoolVar(...)
            objective_terms.append(-int(penalty_value) * plays_both)
```

#### Avantages du Nouveau Système

1. **Flexibilité** : Définissez précisément la pénalité pour chaque niveau d'espacement
2. **Progressivité** : Pénalités décroissantes pour encourager plus d'espacement
3. **Simplicité** : Une seule liste remplace deux paramètres (min_weeks + weight)
4. **Cohérence** : Même logique dans CP-SAT et Greedy
5. **Extensibilité** : Ajoutez autant de niveaux que nécessaire

#### Migration depuis l'Ancienne Version

**Ancienne configuration** :
```yaml
espacement_minimum_semaines: 1
poids_espacement_matchs: 100.0
```

**Équivalent nouvelle version** :
```yaml
penalites_espacement_repos: [100.0, 50.0]
```

**Pour une transition douce** :
```yaml
penalites_espacement_repos: [100.0, 0.0]  # Pénalise uniquement 0 repos
```

### 2. LoadBalancingConstraint
**Fichier** : `constraints/schedule_constraints.py`
**Poids** : `poids_equilibrage_charge` (défaut: 50.0)

Équilibre la charge de matchs entre les semaines et les gymnases.

```python
penalty = weight × |matchs_semaine - moyenne| × 0.5
penalty += weight × |matchs_gymnase - moyenne| × 0.5
```

### 3. PreferredTimeConstraint ⭐ (Sophistiquée)
**Fichier** : `constraints/schedule_constraints.py`
**Poids base** : `penalite_apres_horaire_min` (défaut: 10.0)

**LA PLUS COMPLEXE** : Système de tolérance avec multiplicateurs variables.

#### Logique de Tolérance

```
Fenêtre de tolérance (en minutes) : penalite_horaire_tolerance
│
├─ Si distance ≤ tolérance
│  └─> PAS de pénalité (match accepté dans la zone de tolérance)
│
└─ Si distance > tolérance
   └─> Pénalité sur (distance - tolérance)
```

#### Multiplicateurs Selon Position du Match

| Situation | Multiplicateur | Paramètre Config | Sévérité |
|-----------|----------------|------------------|----------|
| Match AVANT horaire des 2 équipes | 300x | `penalite_avant_horaire_min_deux` | ⚠️⚠️⚠️ Très grave |
| Match AVANT horaire d'1 équipe | 100x | `penalite_avant_horaire_min` | ⚠️⚠️ Grave |
| Match APRÈS horaire préféré | 10x | `penalite_apres_horaire_min` | ⚠️ Acceptable |

#### Formule Mathématique

```
pénalité = multiplicateur × ((distance_effective / diviseur)²)

où:
  distance_effective = max(0, distance_en_minutes - tolérance)
  diviseur = penalite_horaire_diviseur (normalisation)
```

#### Paramètres de Configuration

```yaml
penalite_apres_horaire_min: 10.0              # Multiplicateur de base (après)
penalite_avant_horaire_min: 100.0           # Multiplicateur 1 équipe avant
penalite_avant_horaire_min_deux: 300.0      # Multiplicateur 2 équipes avant
penalite_horaire_diviseur: 90.0             # Diviseur (60=heures, 90=plus doux)
penalite_horaire_tolerance: 30.0            # Tolérance en minutes
```

#### Exemples Concrets

**Avec tolérance=30 minutes, diviseur=90 :**

| Situation | Distance | Distance effective | Multiplicateur | Pénalité |
|-----------|----------|-------------------|----------------|----------|
| Match à +20min | 20 min | 0 (≤ 30) | - | 0.00 ✅ |
| Match à +45min | 45 min | 15 min | 10x | 0.28 |
| Match à -50min (1 équipe) | 50 min | 20 min | 100x | 4.94 ⚠️ |
| Match à -70min (2 équipes) | 70 min | 40 min | 300x | 59.26 ⚠️⚠️⚠️ |

#### Implémentation Identique

✅ **CP-SAT** (`cpsat_solver.py` ligne 48-155) :
```python
def _calculate_time_preference_penalty(self, match, creneau):
    # Pour chaque équipe
    distance_min = abs(horaire_match - horaire_prefere)
    if distance_min <= tolerance:
        continue  # Pas de pénalité
    
    distance_effective = distance_min - tolerance
    penalty += multiplicateur × ((distance_effective / diviseur)²)
```

✅ **Greedy** (`schedule_constraints.py` ligne 67-202) :
```python
def _calculate_penalty_for_equipe(self, equipe, creneau_horaire):
    distance_minutes = abs(horaire_match - horaire_pref)
    if distance_minutes <= self.tolerance:
        return 0.0, False  # Dans tolérance
    
    distance_effective = distance_minutes - self.tolerance
    # Multiplicateur déterminé dans validate()
    penalty = multiplicateur × ((distance_effective / divisor)²)
```

✅ **Validateur** (`solution_validator.py` ligne 360-435) :
```python
# Même calcul pour vérifier la solution
if distance_minutes <= tolerance:
    stats['nb_matchs_dans_tolerance'] += 1
else:
    distance_effective = distance_minutes - tolerance
    penalite = multiplicateur × ((distance_effective / diviseur)²)
```

### 4. PreferredVenueConstraint
**Fichier** : `constraints/schedule_constraints.py`
**Poids** : `poids_preference_lieu` (défaut: 10.0)

Préférence de gymnase pour les équipes (simple pénalité constante si non respectée).

## Validation de Solution

**Fichier** : `validation/solution_validator.py`

Le validateur vérifie chaque match assigné contre toutes les contraintes et calcule :

1. **Violations hard** : Nombre de contraintes dures violées
2. **Violations soft** : Nombre de contraintes souples non respectées
3. **Pénalité totale** : Somme pondérée des violations
4. **Statistiques détaillées** : 
   - Matchs respectant exactement les horaires préférés
   - Matchs dans la zone de tolérance
   - Taux de respect total (exact + tolérance)
   - Violations hors tolérance uniquement

### Rapport de Validation

Le rapport inclut une section spéciale pour les horaires préférés :

```
Horaires préférés:
  Matchs respectés exactement: 8/84 (9.5%)
  Matchs dans tolérance (±30min): 19/84 (22.6%)
  ✓ Taux de respect total: 27/84 (32.1%)
  Violations hors tolérance: 57/84
    - Avant horaire des 2 équipes: 0
    - Avant horaire d'1 équipe: 7
    - Après horaire préféré: 50
```

## Tests de Cohérence

**Fichier** : `test_comparaison_solvers.py`

Compare les performances de CP-SAT et Greedy :

```bash
python test_comparaison_solvers.py
```

Vérifie que les deux solveurs :
- Produisent des planifications valides
- Utilisent les mêmes calculs de pénalités
- Respectent la tolérance de la même manière

## Fichiers de Configuration

### CP-SAT : `data_hand/config_cpsat.yaml`
```yaml
penalite_avant_horaire_min: 100.0
penalite_avant_horaire_min_deux: 300.0
penalite_horaire_diviseur: 90.0
penalite_horaire_tolerance: 30.0
```

### Greedy : `data_hand/config.yaml`
```yaml
penalite_avant_horaire_min: 100.0
penalite_avant_horaire_min_deux: 300.0
penalite_horaire_diviseur: 90.0
penalite_horaire_tolerance: 30.0
```

## Évolution du Système

### Phase 1 : Système Simple
- Pénalité constante si horaire non respecté
- Pas de distinction avant/après
- Pas de tolérance

### Phase 2 : Multiplicateurs
- Ajout de `penalite_avant_horaire_min`
- Distinction avant (pénalisant) vs après (acceptable)

### Phase 3 : Multiplicateurs Avancés ⭐
- Ajout de `penalite_avant_horaire_min_deux`
- Distinction 2 équipes avant (très grave) vs 1 équipe (grave)

### Phase 4 : Distance Quadratique
- Ajout de `penalite_horaire_diviseur`
- Pénalité proportionnelle au carré de la distance
- Normalisation avec diviseur

### Phase 5 : Tolérance (ACTUELLE) ⭐⭐
- Ajout de `penalite_horaire_tolerance`
- Fenêtre d'acceptation sans pénalité
- Pénalité calculée uniquement sur distance excédentaire
- **Impact mesuré** : 9.5% → 32.1% de respect avec tolérance=30min

## Code Nettoyé et Cohérent

✅ **Tous les paramètres sont utilisés** dans les 3 composants :
- CP-SAT solver
- Greedy solver
- Solution validator

✅ **Formules identiques** partout :
```python
if distance <= tolerance:
    penalty = 0
else:
    penalty = multiplicateur × ((distance - tolerance) / diviseur)²
```

✅ **Documentation complète** :
- Docstrings détaillées avec exemples
- Commentaires inline expliquant la logique
- Paramètres YAML commentés

✅ **Pas de code obsolète** :
- Ancien paramètre `penalty_before_earliest` supprimé
- Anciennes formules de pénalité supprimées
- Tests cohérents avec la nouvelle implémentation

## Utilisation Recommandée

### Pour un dataset de taille moyenne (< 100 matchs)
```yaml
strategie: "cpsat"
cpsat:
  temps_max_secondes: 300
```

### Pour un grand dataset (> 200 matchs)
```yaml
strategie: "greedy"
fallback_greedy: true  # Utiliser Greedy si CP-SAT échoue
greedy:
  nb_essais: 10
```

### Réglage de la tolérance

- **tolérance = 0** : Strict, seules les correspondances exactes comptent
- **tolérance = 15-30** : Équilibré, accepte de légères variations (RECOMMANDÉ)
- **tolérance = 60+** : Souple, accepte des écarts d'1 heure ou plus

### Réglage du diviseur

- **diviseur = 60** : Pénalités plus fortes (1 heure = unité)
- **diviseur = 90** : Équilibré (1.5 heures = unité) (RECOMMANDÉ)
- **diviseur = 120** : Pénalités plus douces (2 heures = unité)

## Maintenance et Évolution

### Pour ajouter une nouvelle contrainte :

1. Créer une classe héritant de `Constraint` dans le fichier approprié
2. Implémenter `validate(match, creneau, solution_state) -> (bool, float)`
3. Ajouter à `ConstraintValidator` dans les deux solveurs
4. Ajouter les paramètres dans `Config` et les YAML
5. Documenter dans ce README

### Pour modifier une contrainte existante :

1. ⚠️ **IMPORTANT** : Modifier les 3 implémentations en parallèle :
   - CP-SAT solver
   - Greedy constraint
   - Solution validator
2. Tester avec `test_comparaison_solvers.py`
3. Vérifier la cohérence des pénalités calculées
4. Mettre à jour la documentation

## Auteurs et Historique

- **Auteur principal** : Vincent Gardies
- **Dernière mise à jour** : Décembre 2024
- **Version tolérance** : v5.0 (avec système de tolérance sophistiqué)
