# 🚀 Guide de Performance du Solver CP-SAT

Ce document décrit les contraintes les plus coûteuses en calcul et comment les optimiser.

## 📊 Analyse des Contraintes par Coût Computationnel

### 🔴 Contraintes CRITIQUES (Impact Majeur)

| Contrainte | Complexité | Variables Auxiliaires | Impact Estimé |
|------------|------------|----------------------|---------------|
| **Équilibrage avec ententes** | O(E × S × N) | ~2,500+ | ⭐⭐⭐⭐⭐ |
| **Coach Overlap** | O(C × M² × J²) | ~100,000+ | ⭐⭐⭐⭐⭐ |
| **Espacement Repos** | O(E × S²) | ~25,000 | ⭐⭐⭐⭐ |
| **Aller-Retour Espacement** | O(P × J²) | ~millions potentiels | ⭐⭐⭐⭐ |

*Légende: E=équipes, S=semaines/seuils, N=ententes, C=coachs, M=matchs, J=créneaux, P=paires*

### 🟠 Contraintes ÉLEVÉES (Impact Modéré)

| Contrainte | Complexité | Variables Auxiliaires | Impact Estimé |
|------------|------------|----------------------|---------------|
| **Overlap Institution** | O(paires × moments) | ~1,000-10,000 | ⭐⭐⭐ |
| **Compaction Temporelle** | O(M × J) | 0 (termes linéaires) | ⭐⭐ |

### 🟢 Contraintes LÉGÈRES (Impact Faible)

| Contrainte | Complexité | Variables Auxiliaires | Impact Estimé |
|------------|------------|----------------------|---------------|
| Préférences horaires | O(M × J) | 0 | ⭐ |
| Préférences gymnases | O(M × J) | 0 | ⭐ |
| Niveaux gymnases | O(M × J) | 0 | ⭐ |

---

## ⚡ Mode Fast et Options de Performance

### Activer le Mode Fast

Le mode fast désactive automatiquement les contraintes les plus coûteuses :

```yaml
cpsat:
  mode_fast: true  # Active toutes les optimisations
```

**Effet du mode fast:**
- ✅ Espacement repos: désactivé ou simplifié
- ✅ Aller-retour espacement: désactivé ou simplifié  
- ✅ Équilibrage: mode simplifié sans ententes fines
- ⚠️ Qualité de solution potentiellement réduite

### Contrôle Fin des Contraintes

Pour un contrôle plus précis, utilisez les flags individuels :

```yaml
cpsat:
  # Désactiver entièrement des contraintes coûteuses
  enable_espacement_repos: false  # Désactive complètement
  enable_aller_retour_espacement: false  # Désactive complètement
  
  # OU utiliser les modes simplifiés (moins coûteux, qualité préservée)
  espacement_repos_simplifie: true  # O(semaines) au lieu de O(semaines²)
  aller_retour_simplifie: true  # O(semaines²) au lieu de O(créneaux²)

contraintes:
  equilibrage_mode_simplifie: true  # O(seuils) au lieu de O(seuils × ententes)
```

---

## 📈 Comparaison des Modes

### Espacement Repos

| Mode | Complexité | Ce qui est pénalisé |
|------|------------|---------------------|
| **Complet** | O(E × S²) | Toutes les paires de semaines |
| **Simplifié** | O(E × S) | Seulement semaines consécutives |
| **Désactivé** | O(1) | Rien |

**Recommandation:** Mode simplifié préserve 80% de la qualité avec 90% de réduction du temps.

### Aller-Retour Espacement

| Mode | Complexité | Ce qui est pénalisé |
|------|------------|---------------------|
| **Complet** | O(P × J²) | Chaque paire (créneau aller, créneau retour) |
| **Simplifié** | O(P × S²) | Chaque paire (semaine aller, semaine retour) |
| **Désactivé** | O(1) | Rien |

**Recommandation:** Mode simplifié donne les mêmes résultats pratiques (l'espacement se mesure en semaines, pas en créneaux).

### Équilibrage

| Mode | Complexité | Gestion des ententes |
|------|------------|---------------------|
| **Complet** | O(E × S × N) | Fine (bonus différent par nb d'ententes) |
| **Simplifié** | O(E × S) | Approximative (bonus moyen) |
| **Désactivé** | O(1) | Aucune (bonus fixe par match) |

**Recommandation:** Mode simplifié si peu d'ententes dans le calendrier.

---

## 🎯 Configurations Recommandées

### Pour Tests Rapides (< 30 secondes)

```yaml
cpsat:
  temps_max_secondes: 30
  mode_fast: true
  use_prefilter: true
```

### Pour Production (Qualité Maximale)

```yaml
cpsat:
  temps_max_secondes: 300  # 5 minutes
  mode_fast: false
  use_prefilter: true
  num_search_workers: 8
```

### Pour Gros Problèmes (> 300 matchs)

```yaml
cpsat:
  temps_max_secondes: 600  # 10 minutes
  use_prefilter: true
  espacement_repos_simplifie: true
  aller_retour_simplifie: true

contraintes:
  equilibrage_mode_simplifie: true
  coach_overlap_actif: false  # Très coûteux
```

---

## 🔧 Autres Optimisations

### Préfiltrage (Toujours Recommandé)

```yaml
cpsat:
  use_prefilter: true  # Réduit les variables de 30-60%
```

Le préfiltrage élimine les combinaisons match-créneau impossibles AVANT la création du modèle :
- Équipes indisponibles
- Gymnases fermés
- Capacité dépassée
- Horaire avant interdit

### Parallélisation

```yaml
cpsat:
  num_search_workers: 8  # Nombre de threads (défaut: 8)
```

Augmentez sur machines puissantes, réduisez si mémoire limitée.

### Arrêt Anticipé

```yaml
cpsat:
  relative_gap_limit: 0.01  # Arrête si solution à 1% de l'optimal
  absolute_gap_limit: 1000  # Arrête si écart absolu < 1000
```

Utile pour avoir une "bonne" solution rapidement sans attendre l'optimal.

---

## 📉 Mesurer l'Impact

Activez la progression pour voir les statistiques :

```yaml
cpsat:
  afficher_progression: true
```

Vous verrez :
- Nombre de combinaisons initiales/filtrées
- Nombre de variables auxiliaires créées
- Temps par phase

---

## 🧪 Profils de Benchmark

### Profil "Minimal" (Debug)
```yaml
cpsat:
  temps_max_secondes: 10
  mode_fast: true
contraintes:
  equilibrage_actif: false
  overlap_institution_actif: false
  coach_overlap_actif: false
```

### Profil "Équilibré"
```yaml
cpsat:
  temps_max_secondes: 120
  espacement_repos_simplifie: true
  aller_retour_simplifie: true
```

### Profil "Qualité Maximale"
```yaml
cpsat:
  temps_max_secondes: 600
  mode_fast: false
  # Toutes les contraintes actives par défaut
```
