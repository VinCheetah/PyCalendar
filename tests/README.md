# Tests PyCalendar - Suite Complète CP-SAT

Cette suite de tests valide le comportement du solver CP-SAT dans différents scénarios.

## 🎯 Objectif

Cette suite de tests valide le comportement du solveur CP-SAT sur des **cas synthétiques simples** où la **solution optimale est connue à l'avance**.

## 📊 Résumé

**Total** : **43 tests** organisés en **5 fichiers**

- ✅ **41 passent** (95%)
- ⏭️ **2 skipped** (ententes fallback)

## 📁 Structure

```
tests/
├── conftest.py              # Fixtures pytest partagées (builders, configs)
├── test_cpsat_basic.py      # Tests de base (9 tests)
├── test_cpsat_penalties.py  # Tests des pénalités et préférences (11 tests)
├── test_cpsat_advanced.py   # Tests avancés avec choix forcés (10 tests)
├── test_cpsat_features.py   # Tests fonctionnalités avancées (8 tests) ✨ NOUVEAU
├── test_examples.py         # Exemples documentés (5 tests)
├── README.md                # Ce fichier
├── SUMMARY_v2.md            # Résumé détaillé v3
├── ANALYSE_CRITIQUE.md      # Analyse critique complète
└── EXTENSION_TESTS_FEATURES.md  # Documentation tests features ✨ NOUVEAU
```

## 🚀 Lancer les tests

### Tous les tests

```bash
pytest tests/ -v
```

### Un fichier spécifique

```bash
pytest tests/test_cpsat_basic.py -v
```

### Une classe de tests

```bash
pytest tests/test_cpsat_basic.py::TestBasicAssignment -v
```

### Un test particulier

```bash
pytest tests/test_cpsat_basic.py::TestBasicAssignment::test_single_match_single_slot -v
```

- ✅ **Matchs fixés** (2 tests)

  - Respect des matchs pré-planifiés### Avec sortie détaillée

  - Blocage de créneaux par matchs fixés

```bash

### 2️⃣ Tests de Pénalités (`test_cpsat_penalties.py`) - 11 testspytest tests/ -v -s  # -s affiche les print()

```

**Objectif** : Valider l'optimisation (pénalités, bonus, équilibrage)

### Avec coverage

- ✅ **Préférences horaires** (4 tests)

  - Choix de l'horaire exact préféré```bash

  - Tolérance horairepytest tests/ --cov=pycalendar.solvers --cov-report=html

  - Formule quadratique de distance```

  - Multiplicateurs avant/après

## 📋 Catégories de tests

- ✅ **Préférences gymnases** (2 tests)

  - Bonus gymnase favori### 1. Tests de base (`test_cpsat_basic.py`)

  - Bonus décroissant par rang

Tests d'affectation fondamentale sans pénalités :

- ✅ **Niveaux gymnases** (1 test)

  - Évitement gymnase bas niveau pour match haut niveau- ✅ Affectation simple (1 match → 1 créneau)

- ✅ Contraintes de capacité

- ✅ **Équilibrage progressif** (1 test)- ✅ Contraintes d'indisponibilité

  - Priorité aux équipes avec moins de matchs- ✅ Contraintes de non-simultanéité

- ✅ Respect des matchs fixés

- ✅ **Fonctions de calcul** (3 tests)

  - Tests unitaires des formules mathématiques**Principe** : Config minimale, désactiver toutes les pénalités, tester uniquement les contraintes dures.



### 3️⃣ Tests Avancés (`test_cpsat_advanced.py`) - 10 tests ✨ **NOUVEAU**### 2. Tests de pénalités (`test_cpsat_penalties.py`)



**Objectif** : Tests avec VRAIS choix difficiles et cas complexesTests des préférences et optimisation :



#### **Choix Forcés** (3 tests)- ✅ Pénalités horaires (préféré, tolérance, avant/après)

- ✅ **Pénalité force le choix** : 2 matchs, 1 créneau → CP-SAT choisit match avec moins de pénalité- ✅ Bonus gymnases préférés

- ✅ **Préférences gymnases antagonistes** : Match1 préfère Gym1, Match2 préfère Gym2 → Arbitrage optimal- ✅ Pénalités niveau gymnase

- ✅ **Équilibrage avec historique** : Équipe C a déjà 2 matchs → Défavorisée au profit de A et B- ✅ Bonus équilibrage progressif

- ✅ Tests unitaires des fonctions de calcul

#### **Cas Limites (Edge Cases)** (3 tests)

- ✅ **Conflit Horaire vs Gymnase** : Tester quel critère prime selon poids configurés**Principe** : Activer UNE pénalité à la fois, tester que le solveur choisit le bon créneau.

- ✅ **Espacement influence choix** : S1+S2 (consécutifs) vs S1+S4 (espacés) → Repos prioritaire

- ✅ **Compaction temporelle** : Préférer début de saison (S1 > S5 > S10)## 🏗️ Fixtures disponibles



#### **Tests Négatifs (Contraintes Dures)** (3 tests)### Configurations

- ✅ **Capacité JAMAIS dépassée** : 5 matchs, capacité=2 → Max 2 planifiés

- ✅ **Indisponibilité JAMAIS violée** : Équipe indispo S1, seul créneau S1 → Match non planifié- `minimal_config` : Config vide (toutes pénalités désactivées)

- ✅ **Non-simultanéité TOUJOURS respectée** : Équipe ne joue jamais 2x en même temps- `default_config` : Config par défaut du projet

- `volleyball_config` : Config volleyball réelle

#### **Arbitrages Complexes** (1 test)

- ✅ **Trade-off 3 critères** : Horaire vs Gymnase vs Espacement → Vérifier cohérence### Builders



### 4️⃣ Exemples Documentés (`test_examples.py`) - 5 tests- `equipe_builder` : Créer des équipes facilement

- `match_builder` : Créer des matchs

**Objectif** : Exemples pédagogiques pour comprendre le solver- `creneau_builder` : Créer des créneaux

- `gymnase_builder` : Créer des gymnases

- ✅ Contrainte de capacité

- ✅ Pénalité horaire### Helpers

- ✅ Bonus gymnase

- ✅ Équilibrage- `assert_match_assigned_to(match, creneau)` : Vérifie affectation

- ✅ Fonction de calcul- `assert_match_not_assigned(match)` : Vérifie non-affectation



## 🚀 Exécution## 📝 Écrire un nouveau test



```bash### Exemple de test simple

# Tous les tests

pytest tests/ -v```python

def test_my_feature(minimal_config, match_builder, creneau_builder, gymnase_builder):

# Par fichier    """

pytest tests/test_cpsat_basic.py -v    Description du cas de test.

pytest tests/test_cpsat_penalties.py -v    

pytest tests/test_cpsat_advanced.py -v        # ✨ Nouveaux tests    Solution optimale attendue : ...

pytest tests/test_examples.py -v    """

    # Setup : créer les données

# Par classe    match = match_builder.create()

pytest tests/test_cpsat_advanced.py::TestForcedChoices -v    creneau = creneau_builder.create()

    gymnases = gymnase_builder.create_dict(["Gym1"])

# Test spécifique    

pytest tests/test_cpsat_advanced.py::TestForcedChoices::test_penalty_forces_choice_between_matches -v    # Résolution

    solver = CPSATSolver(minimal_config)

# Avec script    solution = solver.solve([match], [creneau], gymnases)

./run_tests.sh    

```    # Vérifications

    assert solution.est_complete()

## ✨ Nouveautés (21 nov 2025)    assert_match_assigned_to(match, creneau)

```

### **Corrections Critiques**

### Bonnes pratiques

1. ✅ **Format indisponibilités** : `{1}` → `{1: {"18:00", "20:00"}}`

2. ✅ **Matchs fixés** : Ajout des `metadata` obligatoires1. **Un test = Un comportement** : Ne testez qu'une chose à la fois

3. ✅ **Niveaux gymnases** : Harmonisation `"haut"/"bas"` partout dans le code source2. **Solution connue** : Toujours savoir quelle est la solution optimale attendue

3. **Données minimales** : Utilisez le moins de données possible pour isoler le test

### **10 Nouveaux Tests Avancés**4. **Config minimale** : Désactivez tout sauf ce que vous testez

5. **Docstring claire** : Expliquez la solution optimale attendue

- **Choix forcés** : Tests où CP-SAT DOIT choisir entre options (pas de solution évidente)

- **Edge cases** : Conflits d'intérêts, espacement, compaction## 🔍 Stratégie de test

- **Tests négatifs** : Vérifier que contraintes dures ne sont JAMAIS violées

- **Arbitrages complexes** : Trade-offs multi-critères### Niveau 1 : Fonctions de calcul (isolées)



### **Amélioration Qualité**Tester les fonctions `_calculate_*` directement, sans lancer CP-SAT.



- **Avant** : 25 tests, 22 passaient (88%), certains trop faciles```python

- **Après** : 35 tests, 35 passent (100%), tests robustes et exigeantsdef test_penalty_formula():

    solver = CPSATSolver(config)

## 📖 Documentation    penalty = solver._calculate_time_preference_penalty(match, creneau)

    assert penalty == expected_value

- **README.md** (ce fichier) : Vue d'ensemble et guide d'utilisation```

- **SUMMARY.md** : Résumé détaillé de tous les tests

- **ANALYSE_CRITIQUE.md** : Analyse approfondie de la qualité des tests**Avantages** : Rapide, déterministe, facile à débugger.



## 🏗️ Architecture### Niveau 2 : Comportement CP-SAT (intégration)



### Fixtures Réutilisables (`conftest.py`)Tester que CP-SAT fait le bon choix entre plusieurs options.



```python```python

- minimal_config: Config minimale (pénalités désactivées)def test_cpsat_chooses_best_slot():

- equipe_builder: Créer équipes facilement    solution = solver.solve([match], [slot_good, slot_bad], gymnases)

- match_builder: Créer matchs facilement    assert_match_assigned_to(match, slot_good)

- creneau_builder: Créer créneaux facilement```

- gymnase_builder: Créer gymnases facilement

```**Avantages** : Teste le système complet, détecte les bugs d'intégration.



### Assertions Helper### Niveau 3 : Validation de solution (non-régression)



```pythonCharger une vraie solution et vérifier qu'elle reste valide.

def assert_match_assigned_to(match, creneau):

    """Vérifie qu'un match est assigné au créneau attendu."""```python

    def test_solution_still_valid():

def assert_match_not_assigned(match):    solution = load_solution("solutions/volley_2025.json")

    """Vérifie qu'un match n'est PAS assigné."""    violations = validate(solution)

```    assert len(violations) == 0

```

## 🎓 Principes de Test

**Avantages** : Protège contre les régressions sur données réelles.

### ✅ Bons Tests

## 🐛 Débugger un test qui échoue

1. **Synthétiques** : Cas minimaux où la solution optimale est connue

2. **Isolés** : Un test = un comportement testé### Activer les logs

3. **Reproductibles** : Résultats déterministes

4. **Documentés** : Docstring explique solution attendue```bash

5. **Difficiles** : Forcent le solver à faire de vrais choix ✨ **NOUVEAU**pytest tests/test_cpsat_basic.py::test_my_test -v -s --log-cli-level=DEBUG

```

### ❌ Tests à Éviter

### Utiliser le debugger

1. ❌ Tests avec une seule solution évidente (trop faciles)

2. ❌ Tests sans vérification de la solution optimale```python

3. ❌ Tests dépendants d'autres testsimport pytest

4. ❌ Tests avec paramètres mal configurés (pénalités écrasées par bonus)

def test_my_test():

## 📈 Couverture    # ...

    pytest.set_trace()  # Point d'arrêt

**Contraintes dures** : ✅ 100%    # ...

- Capacité gymnases```

- Disponibilité équipes

- Non-simultanéité### Afficher la solution

- Matchs fixés

```python

**Optimisation (soft constraints)** : ✅ 100%def test_my_test():

- Pénalités horaires    solution = solver.solve(...)

- Bonus gymnases    print(f"Matchs planifiés: {len(solution.matchs_planifies)}")

- Niveaux gymnases    for match in solution.matchs_planifies:

- Équilibrage progressif        print(f"  {match.equipe1.nom} vs {match.equipe2.nom} → {match.creneau}")

- Espacement repos ✨ **NOUVEAU**```

- Compaction temporelle ✨ **NOUVEAU**

## 📊 Coverage

**Scénarios complexes** : ✅ **NOUVEAU**

- Choix forcésGénérer un rapport de couverture :

- Conflits d'intérêts

- Arbitrages multi-critères```bash

- Tests négatifs (contraintes jamais violées)pytest tests/ --cov=pycalendar.solvers --cov-report=html

open htmlcov/index.html

## 🔧 Maintenance```



Pour ajouter un nouveau test :## 🎯 TODO



1. Choisir le fichier approprié (basic/penalties/advanced/examples)Tests à ajouter :

2. Utiliser les builders (`equipe_builder`, etc.)

3. Configurer `minimal_config` avec pénalités nécessaires- [ ] Pénalités espacement repos

4. Documenter la solution optimale attendue- [ ] Pénalités compaction temporelle

5. **IMPORTANT** : Forcer un choix réel si test de pénalités ✨ **NOUVEAU**- [ ] Contraintes overlap institution

   - 2 matchs + 1 créneau pour tester optimisation- [ ] Contraintes ententes

   - Pénalités significatives (≥ 100) si bonus de planification actif- [ ] Contraintes aller-retour

- [ ] Contraintes temporelles souples

## 📝 Notes Techniques- [ ] Système de guidance qualité

- [ ] Warm start

### ⚠️ Problème Résolu : Pénalités Écrasées- [ ] Tests de performance (grands datasets)



**Avant** : Les tests de pénalités passaient pour la MAUVAISE raison## 📚 Ressources

- Bonus de planification : 10^10

- Pénalités horaires : ~100-1000- [Pytest documentation](https://docs.pytest.org/)

- Différence : 0.00001% (négligeable pour CP-SAT)- [CP-SAT documentation](https://developers.google.com/optimization/cp/cp_solver)

- [Guide des structures de données](../docs/GUIDE_STRUCTURES_DONNEES.md)

**Solution** : Tests avancés forcent des CHOIX réels
- 2 matchs, 1 créneau → CP-SAT doit choisir lequel planifier
- Pénalités différentes → Choix basé sur optimisation
- Vérification que le bon match est choisi

## 🎯 TODO Futurs Tests

Idées pour étendre la couverture :

- [ ] Tests d'overlaps institution (contraintes souples)
- [ ] Tests aller-retour (espacement matchs même équipes)
- [ ] Tests avec ententes (fallback)
- [ ] Tests de warm start (solutions précédentes)
- [ ] Tests de qualité match (filtrage post-résolution)
- [ ] Tests de performance (temps de résolution)

---

**Dernière mise à jour** : 21 novembre 2025  
**Version** : 2.0 (35 tests, 100% succès)
