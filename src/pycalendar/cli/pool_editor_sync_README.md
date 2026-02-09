# Pool Editor Synchronization Module

Module de synchronisation entre l'éditeur de poules (Pool Editor) et les fichiers de configuration Excel.

## 📁 Structure

```
src/pycalendar/cli/
└── pool_editor_sync.py    # Module principal de synchronisation

scripts/
└── update_teams_from_pool_editor.py    # Script CLI interactif

docs/
└── GUIDE_POOL_EDITOR_SYNC.md    # Guide d'utilisation complet
```

## 🎯 Fonctionnalités

- ✅ **Import JSON** : Charge les équipes depuis un export JSON du Pool Editor
- ✅ **Synchronisation intelligente** : Compare et détermine les actions nécessaires
- ✅ **Préservation des données** : Les colonnes supplémentaires (contacts, etc.) sont conservées
- ✅ **Modes flexibles** : Update (par défaut) ou Sync (avec suppression)
- ✅ **Sauvegarde automatique** : Crée une backup avant modification
- ✅ **Mode interactif** : Prévisualisation des changements avec confirmation
- ✅ **Rapports détaillés** : Statistiques complètes des modifications

## 🚀 Utilisation rapide

### En ligne de commande

```bash
# Mise à jour simple (recommandé)
python scripts/update_teams_from_pool_editor.py poules_export.json --config configs/config_volley.yaml

# Mode interactif
python scripts/update_teams_from_pool_editor.py poules_export.json --config configs/config_volley.yaml -i

# Synchronisation complète
python scripts/update_teams_from_pool_editor.py poules_export.json --config configs/config_volley.yaml --sync
```

### En Python

```python
from pycalendar.cli.pool_editor_sync import synchroniser_equipes_depuis_json, afficher_rapport

# Synchroniser
stats = synchroniser_equipes_depuis_json(
    json_path="poules_export.json",
    excel_path="data/volleyball/config_volley.xlsx",
    mode='update',  # ou 'sync'
    backup=True
)

# Afficher le rapport
afficher_rapport(stats)
```

## 📊 Format des données

### Format JSON (exporté par le Pool Editor)

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
    }
  ],
  "pools": [...],
  "settings": {...}
}
```

### Format Excel (feuille Equipes)

| Equipe | Niveau_Equipe | Genre_Equipe | Poule | Horaire_Prefere | Responsable_Nom | Responsable_Email | Responsable_Telephone |
|--------|---------------|--------------|-------|-----------------|-----------------|-------------------|----------------------|
| LYON 1 (1) | A1 | F | VBFA1PA | 14:00 | MARTIN Jean | jean@univ.fr | 0601020304 |

**Colonnes synchronisées** : Equipe, Niveau_Equipe, Genre_Equipe, Poule, Horaire_Prefere  
**Colonnes préservées** : Responsable_*, et toutes autres colonnes personnalisées

## 🔄 Modes de synchronisation

### Mode UPDATE (défaut)

```python
mode='update'
```

- Ajoute les nouvelles équipes
- Met à jour les équipes existantes
- **Conserve** les équipes absentes du JSON

**→ Utiliser pour** : Mises à jour partielles, ajout d'équipes

### Mode SYNC

```python
mode='sync'
```

- Ajoute les nouvelles équipes
- Met à jour les équipes existantes
- **Supprime** les équipes absentes du JSON

**→ Utiliser pour** : Synchronisation complète, réorganisation totale

## 📝 API Reference

### `synchroniser_equipes_depuis_json()`

```python
def synchroniser_equipes_depuis_json(
    json_path: str,
    excel_path: str,
    sheet_name: str = 'Equipes',
    backup: bool = True,
    mode: str = 'update'
) -> Dict[str, any]:
```

**Paramètres** :
- `json_path` : Chemin vers le fichier JSON exporté
- `excel_path` : Chemin vers le fichier Excel de configuration
- `sheet_name` : Nom de la feuille à synchroniser (défaut: 'Equipes')
- `backup` : Si True, crée une sauvegarde avant modification
- `mode` : 'update' ou 'sync'

**Retourne** : Dictionnaire avec les statistiques
```python
{
    'ajoutees': 5,
    'modifiees': 12,
    'supprimees': 0,
    'conservees': 45,
    'backup_path': 'config_volley.backup_20260107_201530.xlsx'
}
```

**Lève** : `PoolEditorSyncError` en cas d'erreur

### Classes utilitaires

#### `EquipeData`

Représente les données d'une équipe.

```python
class EquipeData:
    def __init__(self, nom: str, niveau: str, genre: str, 
                 poule: Optional[str], horaire: Optional[str], 
                 institution: str)
```

#### `PoolEditorSyncError`

Exception levée lors d'erreurs de synchronisation.

### Fonctions auxiliaires

#### `charger_equipes_depuis_json()`

```python
def charger_equipes_depuis_json(json_path: Path) -> List[EquipeData]
```

Charge les équipes depuis un fichier JSON.

#### `charger_equipes_depuis_excel()`

```python
def charger_equipes_depuis_excel(excel_path: Path, 
                                  sheet_name: str = 'Equipes') -> pd.DataFrame
```

Charge la feuille Equipes depuis Excel.

#### `comparer_equipes()`

```python
def comparer_equipes(
    equipes_json: List[EquipeData],
    df_excel: pd.DataFrame
) -> Tuple[List[EquipeData], List[str], List[Tuple[str, EquipeData]]]
```

Compare les équipes et retourne (à_ajouter, à_supprimer, à_modifier).

#### `afficher_rapport()`

```python
def afficher_rapport(stats: Dict[str, any])
```

Affiche un rapport formaté des modifications.

## 🧪 Tests

### Test unitaire du module

```python
from pycalendar.cli.pool_editor_sync import *

# Charger un JSON
equipes = charger_equipes_depuis_json(Path("test.json"))
print(f"{len(equipes)} équipes chargées")

# Charger un Excel
df = charger_equipes_depuis_excel(Path("config.xlsx"))
print(f"{len(df)} équipes existantes")

# Comparer
a_ajouter, a_supprimer, a_modifier = comparer_equipes(equipes, df)
print(f"Ajouts: {len(a_ajouter)}, Suppressions: {len(a_supprimer)}, Modifications: {len(a_modifier)}")
```

### Test du script complet

```bash
# Créer un JSON de test
cat > test_export.json << EOF
{
  "teams": [
    {"nom": "TEST (1)", "genre": "F", "niveau": "A1", "horaire": "14H", 
     "institution": "TEST", "poule": "VBFA1PA"}
  ],
  "pools": [],
  "settings": {}
}
EOF

# Tester en mode interactif
python scripts/update_teams_from_pool_editor.py test_export.json --excel config_test.xlsx -i
```

## ⚠️ Erreurs courantes

### `PoolEditorSyncError: Fichier JSON invalide`

**Cause** : JSON mal formaté ou corrompu

**Solution** : Vérifiez le JSON avec un validateur, ré-exportez depuis le Pool Editor

### `PoolEditorSyncError: Feuille 'Equipes' introuvable`

**Cause** : Nom de feuille incorrect

**Solution** : Utilisez `--sheet <nom>` pour spécifier le bon nom

### `PoolEditorSyncError: Colonnes manquantes`

**Cause** : Feuille Excel incomplète

**Solution** : La feuille doit contenir : Equipe, Niveau_Equipe, Genre_Equipe, Poule, Horaire_Prefere

## 📚 Documentation

- **Guide complet** : [docs/GUIDE_POOL_EDITOR_SYNC.md](../../docs/GUIDE_POOL_EDITOR_SYNC.md)
- **Pool Editor** : [tools/pool_editor/README.md](../../tools/pool_editor/README.md)
- **Guide général** : [GUIDE_UTILISATION.md](../../GUIDE_UTILISATION.md)

## 🔧 Développement

### Ajouter une nouvelle colonne synchronisée

1. Modifiez `EquipeData.__init__()` pour ajouter l'attribut
2. Mettez à jour `EquipeData.to_dict()` pour inclure la colonne
3. Ajoutez la colonne dans `colonnes_requises` de `synchroniser_equipes_depuis_json()`

### Ajouter un nouveau format d'export

1. Créez une fonction `charger_equipes_depuis_<format>()`
2. Retournez une `List[EquipeData]`
3. Utilisez avec `comparer_equipes()` et `synchroniser_equipes_depuis_json()`

## 📝 Licence

Fait partie du projet PyCalendar - FFSU

---

**Version** : 1.0  
**Auteur** : PyCalendar Team  
**Date** : Janvier 2026
