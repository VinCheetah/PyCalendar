# 📋 Guide d'utilisation des scripts de génération d'interface

## 🎯 Script principal : `regenerate_interface.py`

Le script **à la racine** détecte automatiquement le format de votre solution et choisit le bon workflow.

### ✅ Utilisation simple

```bash
# Génération depuis latest_volley.json (format par défaut)
python regenerate_interface.py

# Génération depuis une solution spécifique
python regenerate_interface.py --solution ma_solution.json --output mon_calendrier.html

# Depuis une solution v2.0 (déjà convertie)
python regenerate_interface.py --solution latest_volley_v2.json --output calendrier.html
```

### 📊 Formats supportés

#### Format v1.0 (ancien format)
```json
{
  "assignments": [...],
  "config_signature": "volley",
  "metadata": {...}
}
```

#### Format v2.0 (nouveau format)
```json
{
  "version": "2.0",
  "entities": {...},
  "matches": {...},
  "slots": [...],
  "statistics": {...}
}
```

## 🔧 Scripts disponibles

### 1. `regenerate_interface.py` (racine) ⭐ **RECOMMANDÉ**
```bash
python regenerate_interface.py --solution SOLUTION --output OUTPUT
```
- ✅ Détection automatique du format (v1.0 ou v2.0)
- ✅ Conversion automatique si nécessaire
- ✅ Génération de l'interface HTML
- ✅ Syntaxe simple et cohérente

### 2. `scripts/convert_solution_to_v2.py`
```bash
python scripts/convert_solution_to_v2.py solutions/latest_volley.json -o solutions/latest_volley_v2.json
```
- Convertit une solution v1.0 → v2.0
- Utile si vous voulez garder le fichier v2.0 pour inspection

### 3. `scripts/regenerate_interface.py`
```bash
python scripts/regenerate_interface.py solutions/latest_volley_v2.json -o calendrier.html
```
- Génère l'interface depuis une solution **v2.0 uniquement**
- Plus rapide si vous avez déjà un fichier v2.0

### 4. `scripts/auto_generate_interface.py`
```bash
python scripts/auto_generate_interface.py solutions/latest_volley.json -o output
```
- Pipeline complet : conversion v1.0 → v2.0 → HTML
- Crée un répertoire de sortie avec les deux fichiers

## 📝 Exemples pratiques

### Workflow quotidien (recommandé)
```bash
# Après avoir généré une nouvelle solution
python regenerate_interface.py --solution latest_volley.json --output calendrier.html

# Ouvrir dans le navigateur
firefox calendrier.html
```

### Workflow avancé (conservation des fichiers v2.0)
```bash
# 1. Convertir v1.0 → v2.0 (garder pour inspection)
python scripts/convert_solution_to_v2.py solutions/latest_volley.json -o solutions/latest_volley_v2.json

# 2. Générer l'interface depuis v2.0
python scripts/regenerate_interface.py solutions/latest_volley_v2.json -o calendrier.html
```

### Génération en batch
```bash
# Pour toutes les solutions dans le répertoire
for solution in solutions/*.json; do
    name=$(basename "$solution" .json)
    python regenerate_interface.py --solution "$solution" --output "calendrier_${name}.html"
done
```

## ✨ Résumé

| Script | Format accepté | Sortie | Quand l'utiliser |
|--------|----------------|--------|------------------|
| `regenerate_interface.py` | v1.0 ou v2.0 | HTML | **Usage quotidien** ⭐ |
| `scripts/convert_solution_to_v2.py` | v1.0 | v2.0 JSON | Conversion pour inspection |
| `scripts/regenerate_interface.py` | v2.0 | HTML | Si v2.0 déjà disponible |
| `scripts/auto_generate_interface.py` | v1.0 | v2.0 + HTML | Pipeline complet |

## 🎨 Fichier généré : `calendrier.html`

Le fichier HTML généré contient :
- ✅ **560 KB** - Un seul fichier, tout embarqué
- ✅ **0 export/import** - Pas d'erreurs JavaScript
- ✅ **3 vues** - Agenda, Poules, Cartes
- ✅ **Filtres** - Genre, institution, gymnase, semaine
- ✅ **Édition** - Modal pour modifier les matchs
- ✅ **Export** - Sauvegarde des modifications en JSON

## 🚨 Résolution de problèmes

### Erreur : "Solution introuvable"
```bash
# Vérifiez que le fichier existe
ls solutions/latest_volley.json

# Ou utilisez le chemin complet
python regenerate_interface.py --solution /chemin/complet/vers/solution.json
```

### Erreur : "ConfigManager.__init__() missing argument"
❌ N'utilisez pas l'ancien script cassé `regenerate_interface.py.broken`
✅ Utilisez le nouveau `regenerate_interface.py` (ce fichier a été corrigé)

### Le HTML ne charge pas dans le navigateur
```bash
# Vérifiez qu'il n'y a pas d'export/import
grep -c "export function\|export class" calendrier.html
# Doit afficher : 0

# Régénérez si nécessaire
python regenerate_interface.py
```
