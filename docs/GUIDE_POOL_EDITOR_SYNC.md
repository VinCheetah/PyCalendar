# Guide d'actualisation depuis le Pool Editor

Ce guide explique comment synchroniser la feuille Equipes d'un fichier Excel de configuration avec les données exportées depuis l'éditeur de poules (Pool Editor).

## Vue d'ensemble

L'éditeur de poules (`tools/pool_editor/`) permet de gérer visuellement les équipes et leurs assignations aux poules. Une fois le travail terminé, vous pouvez exporter les données au format JSON et les importer dans votre configuration Excel.

### Flux de travail

```
Pool Editor (interface web)
    ↓ Export JSON
Fichier poules_export.json
    ↓ Synchronisation
Fichier config_volley.xlsx (feuille Equipes)
```

## 📋 Prérequis

1. Un fichier JSON exporté depuis le Pool Editor
2. Un fichier de configuration Excel avec une feuille "Equipes"
3. Python 3.8+ avec les dépendances installées

## 🚀 Utilisation

### Commande de base

```bash
python scripts/update_teams_from_pool_editor.py <fichier_json> --config <config_yaml>
```

### Exemples

#### 1. Mise à jour simple (mode recommandé)

Ajoute et modifie les équipes sans supprimer celles absentes du JSON :

```bash
python scripts/update_teams_from_pool_editor.py poules_export.json --config configs/config_volley.yaml
```

#### 2. Synchronisation complète avec suppression

Synchronise complètement : ajoute, modifie ET supprime les équipes absentes du JSON :

```bash
python scripts/update_teams_from_pool_editor.py poules_export.json --config configs/config_volley.yaml --sync
```

⚠️ **Attention** : Le mode `--sync` supprime les équipes qui ne sont pas dans le JSON !

#### 3. Mode interactif avec prévisualisation

Affiche un aperçu des modifications avant de les appliquer :

```bash
python scripts/update_teams_from_pool_editor.py poules_export.json --config configs/config_volley.yaml --interactive
```

Exemple de sortie :
```
======================================================================
🚀 PRÉVISUALISATION DES MODIFICATIONS
======================================================================
ℹ️  
➕ 2 équipes seront AJOUTÉES:
   • PARIS SCIENCES (1) [F] A2 → VBFA2PA
   • SORBONNE (1) [M] A1 → Non assignée
ℹ️  
✏️  3 équipes seront MODIFIÉES:
   • LYON 1 (2) → A1 [M] VBMA1PA
   • LYON 2 (1) → A2 [F] VBFA2PB
   • CENTRALE (1) → A1 [M] VBMA1PA
ℹ️  
ℹ️  45 équipes absentes du JSON seront CONSERVÉES

❓ Appliquer ces modifications ? [o/N] :
```

#### 4. Utilisation avec chemin Excel direct

Si vous ne voulez pas utiliser un fichier YAML :

```bash
python scripts/update_teams_from_pool_editor.py poules_export.json --excel data/volleyball/config_volley.xlsx
```

#### 5. Sans sauvegarde (déconseillé)

```bash
python scripts/update_teams_from_pool_editor.py poules_export.json --config configs/config_volley.yaml --no-backup
```

## 📊 Options

| Option | Description |
|--------|-------------|
| `--config <yaml>` | Fichier de configuration YAML (contient le chemin vers l'Excel) |
| `--excel <xlsx>` | Chemin direct vers le fichier Excel (alternative à `--config`) |
| `--sheet <nom>` | Nom de la feuille à synchroniser (défaut: `Equipes`) |
| `--update` | Mode mise à jour (ajoute, modifie, conserve) **[DÉFAUT]** |
| `--sync` | Mode synchronisation complète (ajoute, modifie, supprime) |
| `--interactive`, `-i` | Mode interactif avec prévisualisation |
| `--no-backup` | Ne pas créer de sauvegarde avant modification |
| `--verbose`, `-v` | Mode verbeux pour le débogage |

## 🔄 Modes de synchronisation

### Mode UPDATE (défaut)

```bash
python scripts/update_teams_from_pool_editor.py export.json --config configs/config_volley.yaml --update
```

**Actions** :
- ✅ Ajoute les nouvelles équipes du JSON
- ✅ Met à jour les équipes existantes (Genre, Niveau, Poule, Horaire)
- ✅ **Conserve** les équipes absentes du JSON

**Utiliser quand** : Vous voulez ajouter/modifier des équipes sans risquer de supprimer des données.

### Mode SYNC (synchronisation complète)

```bash
python scripts/update_teams_from_pool_editor.py export.json --config configs/config_volley.yaml --sync
```

**Actions** :
- ✅ Ajoute les nouvelles équipes du JSON
- ✅ Met à jour les équipes existantes
- ⚠️ **Supprime** les équipes absentes du JSON

**Utiliser quand** : Vous voulez que l'Excel reflète exactement le contenu du JSON.

## 📝 Format du JSON

Le fichier JSON exporté par le Pool Editor doit avoir la structure suivante :

```json
{
  "teams": [
    {
      "nom": "LYON 1 (1)",
      "genre": "F",
      "niveau": "A1",
      "horaire": "14H",
      "institution": "LYON 1",
      "poule": "VBFA1PA"
    },
    {
      "nom": "PARIS SCIENCES (1)",
      "genre": "M",
      "niveau": "A2",
      "horaire": "16H",
      "institution": "PARIS SCIENCES",
      "poule": null
    }
  ],
  "pools": [...],
  "settings": {...},
  "exportDate": "2026-01-07T20:00:00.000Z"
}
```

### Champs synchronisés

Les champs suivants sont synchronisés depuis le JSON vers l'Excel :

| Champ JSON | Colonne Excel | Description |
|------------|---------------|-------------|
| `nom` | `Equipe` | Nom de l'équipe (ex: "LYON 1 (1)") |
| `genre` | `Genre_Equipe` | Genre (F, M, X) |
| `niveau` | `Niveau_Equipe` | Niveau (A1, A2, A3, A4) |
| `poule` | `Poule` | Code de la poule (ex: "VBFA1PA") |
| `horaire` | `Horaire_Prefere` | Horaire préféré (14H → 14:00) |

### Données préservées

Les colonnes suivantes dans l'Excel sont **préservées** lors de la synchronisation :

- `Responsable_Nom`
- `Responsable_Email`
- `Responsable_Telephone`
- Toutes autres colonnes personnalisées

⚠️ Ces données ne sont **jamais** écrasées par le script.

## 💾 Sauvegarde automatique

Par défaut, une sauvegarde est créée avant toute modification :

```
config_volley.xlsx
config_volley.backup_20260107_201530.xlsx  ← Sauvegarde
```

Format : `{nom_fichier}.backup_{YYYYMMDD_HHMMSS}.xlsx`

Pour désactiver la sauvegarde (déconseillé) :
```bash
python scripts/update_teams_from_pool_editor.py export.json --config configs/config_volley.yaml --no-backup
```

## 📊 Rapport de synchronisation

Après exécution, un rapport détaillé est affiché :

```
======================================================================
📊 RAPPORT DE SYNCHRONISATION
======================================================================
✅ Équipes ajoutées     : 5
✏️  Équipes modifiées    : 12
🗑️  Équipes supprimées  : 0
ℹ️  Équipes conservées   : 45 (absentes du JSON)

💾 Sauvegarde créée: config_volley.backup_20260107_201530.xlsx
======================================================================
```

## ⚠️ Cas d'usage et précautions

### Cas 1 : Création initiale des poules

Vous venez de créer toutes vos poules dans le Pool Editor pour la première fois.

**Recommandation** : Mode `--update`

```bash
python scripts/update_teams_from_pool_editor.py poules_initial.json --config configs/config_volley.yaml
```

✅ Ajoute toutes les équipes sans supprimer les données existantes.

### Cas 2 : Modification de quelques poules

Vous avez modifié l'assignation de quelques équipes dans le Pool Editor.

**Recommandation** : Mode `--update` + `--interactive`

```bash
python scripts/update_teams_from_pool_editor.py poules_modif.json --config configs/config_volley.yaml -i
```

✅ Prévisualise les changements avant de les appliquer.

### Cas 3 : Réorganisation complète

Vous avez complètement réorganisé toutes les poules dans le Pool Editor et voulez synchroniser exactement.

**Recommandation** : Mode `--sync` + `--interactive`

```bash
python scripts/update_teams_from_pool_editor.py poules_final.json --config configs/config_volley.yaml --sync -i
```

⚠️ **Attention** : Vérifie bien la prévisualisation avant de confirmer !

### Cas 4 : Export partiel

Vous avez exporté seulement quelques poules depuis le Pool Editor (ex: féminines uniquement).

**Recommandation** : Mode `--update` obligatoire

```bash
python scripts/update_teams_from_pool_editor.py poules_feminines.json --config configs/config_volley.yaml --update
```

✅ Les équipes non présentes dans le JSON (masculines) seront conservées.

## 🔧 Dépannage

### Erreur : "Fichier JSON invalide"

**Cause** : Le fichier JSON est mal formaté ou corrompu.

**Solution** :
1. Vérifiez que le JSON est valide avec un validateur en ligne
2. Ré-exportez depuis le Pool Editor

### Erreur : "Feuille 'Equipes' introuvable"

**Cause** : Le fichier Excel n'a pas de feuille nommée "Equipes".

**Solution** :
- Vérifiez le nom de la feuille dans l'Excel
- Utilisez `--sheet <nom>` pour spécifier un autre nom

### Erreur : "Colonnes manquantes dans la feuille"

**Cause** : La feuille Equipes n'a pas les colonnes requises.

**Solution** : La feuille doit avoir au minimum :
- `Equipe`
- `Niveau_Equipe`
- `Genre_Equipe`
- `Poule`
- `Horaire_Prefere`

### Les modifications ne sont pas appliquées

**Cause** : Mode interactif avec réponse "Non".

**Solution** : Répondez "o" ou "oui" à la confirmation.

## 📚 Voir aussi

- [GUIDE_UTILISATION.md](GUIDE_UTILISATION.md) - Guide général du projet
- [GUIDE_CONFIGURATION_CENTRALE.md](GUIDE_CONFIGURATION_CENTRALE.md) - Configuration Excel
- [Pool Editor](tools/pool_editor/README.md) - Documentation de l'éditeur de poules

## 💡 Bonnes pratiques

1. **Toujours utiliser le mode interactif** la première fois :
   ```bash
   python scripts/update_teams_from_pool_editor.py export.json --config configs/config_volley.yaml -i
   ```

2. **Vérifier la sauvegarde** est créée avant de modifier l'Excel

3. **Utiliser le mode `--update` par défaut** sauf si vous êtes sûr de vouloir supprimer des équipes

4. **Faire un export complet** depuis le Pool Editor pour éviter les données manquantes

5. **Tester sur une copie** du fichier Excel avant de modifier l'original :
   ```bash
   cp data/volleyball/config_volley.xlsx data/volleyball/config_volley_test.xlsx
   python scripts/update_teams_from_pool_editor.py export.json --excel data/volleyball/config_volley_test.xlsx -i
   ```

## 🎯 Workflow complet recommandé

1. **Ouvrir le Pool Editor** : `tools/pool_editor/index.html`

2. **Importer les données** existantes (YAML + Excel)

3. **Modifier les poules** selon vos besoins

4. **Exporter au format JSON** : bouton "💾 Exporter"

5. **Prévisualiser les changements** :
   ```bash
   python scripts/update_teams_from_pool_editor.py poules_export.json --config configs/config_volley.yaml -i
   ```

6. **Confirmer et appliquer** si tout est correct

7. **Vérifier le fichier Excel** mis à jour

8. **Tester la génération** du calendrier :
   ```bash
   python main.py configs/config_volley.yaml
   ```

---

**Auteur** : PyCalendar Team  
**Version** : 1.0  
**Date** : Janvier 2026
