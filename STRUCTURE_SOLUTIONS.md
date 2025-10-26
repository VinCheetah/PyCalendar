# Structure des Solutions - PyCalendar

## 📁 Organisation des Dossiers

Depuis la mise à jour du système, les solutions sont organisées dans des sous-dossiers distincts selon leur format :

```
solutions/
├── v1.0/                          # Solutions au format v1.0 (legacy)
│   ├── latest_volley.json        # Dernière solution v1.0
│   └── solution_volley_*.json    # Solutions horodatées
│
└── v2.0/                          # Solutions au format v2.0 (enrichi)
    ├── latest_volley.json        # Dernière solution v2.0
    └── solution_volley_*.json    # Solutions horodatées
```

## 🎯 Formats de Solutions

### Format v1.0 (Legacy)
- **Taille**: ~50-80 KB
- **Contenu**: Assignments simples (équipes, créneaux, poules)
- **Usage**: Format de base, compatible avec anciennes versions
- **Emplacement**: `solutions/v1.0/`

### Format v2.0 (Enrichi)
- **Taille**: ~300-400 KB
- **Contenu**: 
  - Entités complètes (équipes, gymnases, poules)
  - Matchs enrichis avec toutes les métadonnées
  - Slots (disponibles et occupés)
  - Statistiques détaillées
- **Usage**: Format pour l'interface web moderne
- **Emplacement**: `solutions/v2.0/`

## 🚀 Utilisation

### 1. Générer une Solution

```bash
# Le format est configuré dans le fichier YAML
python main.py configs/config_volley.yaml
```

Le paramètre `solution_format` dans votre configuration détermine le format :

```yaml
# Dans configs/config_volley.yaml
fichiers:
  solution_format: "v2.0"  # ou "v1.0"
```

**Par défaut** : Si `solution_format` n'est pas spécifié, le format `v2.0` est utilisé.

### 2. Régénérer l'Interface HTML

```bash
# Utilise automatiquement solutions/v2.0/latest_volley.json
python regenerate_interface.py --solution latest_volley.json --output calendrier.html

# Ou spécifier un fichier spécifique
python regenerate_interface.py --solution solution_volley_2025-10-24_192158.json
```

Le script cherche automatiquement dans cet ordre :
1. `solutions/v2.0/` (priorité)
2. `solutions/v1.0/`
3. `solutions/` (ancien emplacement)

### 3. Ouvrir l'Interface

```bash
python open_calendar.py calendrier.html
```

## ⚙️ Configuration

### Changer le Format de Sauvegarde

Modifiez votre fichier de configuration YAML :

```yaml
# configs/config_volley.yaml
fichiers:
  donnees: "data_volley/config_volley.xlsx"
  sortie: "data_volley/calendrier_volley.xlsx"
  solution_format: "v2.0"  # Choix: "v1.0" ou "v2.0"
```

### Comportements selon le Format

| Format | Sauvegarde v1.0 | Sauvegarde v2.0 | Emplacement |
|--------|----------------|----------------|-------------|
| `v1.0` | ✅ Oui | ❌ Non | `solutions/v1.0/` |
| `v2.0` | ✅ Oui (backup) | ✅ Oui | `solutions/v1.0/` + `solutions/v2.0/` |

**Note** : En mode `v2.0`, les deux formats sont sauvegardés :
- Format v1.0 dans `solutions/v1.0/` (pour compatibilité)
- Format v2.0 dans `solutions/v2.0/` (pour l'interface)

## 🔄 Migration

### Fichiers Existants

Si vous avez des anciens fichiers dans `solutions/`, vous pouvez :

1. **Les laisser en place** : Ils continueront à fonctionner
2. **Les déplacer manuellement** :
   ```bash
   mv solutions/latest_volley.json solutions/v1.0/
   ```
3. **Régénérer** : Exécutez simplement `main.py` pour créer de nouvelles solutions

### Conversion v1.0 → v2.0

Si vous avez un ancien fichier v1.0 et voulez le convertir :

```bash
python scripts/convert_solution_to_v2.py solutions/v1.0/ma_solution.json
```

## 📊 Détection Intelligente des Poules

Le convertisseur v1.0 → v2.0 détecte automatiquement les poules :

- **Si poules présentes** dans v1.0 → ✅ Utilise les vraies poules (ex: VBFA4PA)
- **Si poules absentes** → ⚠️ Détection automatique par clustering (ex: M_Pool_1)

Pour garantir les vraies poules, assurez-vous que le champ `poule` est bien sauvegardé dans le format v1.0.

## 🛠️ Dépannage

### Problème : "Poules inventées (M_Pool_1) au lieu des vraies"

**Cause** : Le fichier v1.0 source ne contient pas le champ `poule`

**Solution** : Régénérez la solution avec une version récente qui sauvegarde les poules :
```bash
python main.py configs/config_volley.yaml
```

### Problème : "Solution introuvable"

**Vérifiez** :
1. Le fichier existe bien dans `solutions/v1.0/` ou `solutions/v2.0/`
2. Vous utilisez le bon nom de fichier
3. Utilisez `ls solutions/v2.0/` pour voir les fichiers disponibles

### Problème : "Noms d'équipes mal gérés"

**Cause probable** : Utilisation d'un ancien fichier sans poules

**Solution** :
```bash
# 1. Vérifier quel fichier est utilisé
python regenerate_interface.py --solution latest_volley.json

# 2. Forcer l'utilisation du nouveau fichier v2.0
python scripts/regenerate_interface.py solutions/v2.0/latest_volley.json -o calendrier.html
```

## 📝 Fichiers Clés

| Fichier | Rôle |
|---------|------|
| `core/solution_store.py` | Gestion de la sauvegarde (v1.0 et v2.0) |
| `scripts/convert_solution_to_v2.py` | Conversion v1.0 → v2.0 |
| `regenerate_interface.py` | Wrapper simplifié pour régénérer l'interface |
| `scripts/regenerate_interface.py` | Générateur d'interface (v2.0 → HTML) |
| `scripts/auto_generate_interface.py` | Pipeline complet (v1.0 → v2.0 → HTML) |

## 💡 Bonnes Pratiques

1. **Toujours utiliser `v2.0`** pour de nouvelles solutions (plus complet)
2. **Ne pas supprimer `v1.0`** : Il sert de backup et de format de base
3. **Vérifier les poules** : Après génération, vérifiez que les vraies poules apparaissent
4. **Utiliser les fichiers `latest_*`** : Plus facile que de chercher le dernier horodaté

## 🔗 Voir Aussi

- `FORMAT_SOLUTION.md` : Documentation détaillée des formats v1.0 vs v2.0
- `POULES_EXPLICATION.md` : Système de détection des poules
- `README.md` : Documentation générale du projet
