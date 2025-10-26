# 🔄 Guide de migration rapide - PyCalendar v2.0

## ✅ Restructuration terminée !

La réorganisation complète du projet a été effectuée avec succès le **26 octobre 2025**.

## 📊 Résumé des changements

### Fichiers déplacés
- ✅ **9 packages** déplacés vers `src/pycalendar/` 
- ✅ **7 scripts CLI** déplacés vers `src/pycalendar/cli/` et renommés
- ✅ **3 dossiers d'exemples** réorganisés dans `examples/`

### Fichiers créés
- ✅ `setup.py` - Configuration installation
- ✅ `pyproject.toml` - Configuration moderne Python
- ✅ `requirements-dev.txt` - Dépendances développement
- ✅ `src/pycalendar/__init__.py` - Exports publics
- ✅ `src/pycalendar/__main__.py` - Point d'entrée module
- ✅ `fix_imports.py` - Script correction imports (24 fichiers, 32 imports)

### Documentation
- ✅ `docs/ARCHITECTURE.md` - Architecture détaillée v2.0
- ✅ Ce fichier - Guide migration rapide

## 🚀 Comment utiliser la nouvelle structure

### 1. Installation en mode développement

```bash
# Dans le dossier PyCalendar
source .venv/bin/activate.fish  # ou .venv/bin/activate pour bash
pip install -e .
```

✅ **Fait !** Le package est maintenant installé et utilisable partout.

### 2. Utilisation

#### Option A : Via main.py (comme avant)
```bash
python main.py
python main.py configs/config_volley.yaml
```

#### Option B : Via module Python (nouveau)
```bash
python -m pycalendar
python -m pycalendar configs/config_volley.yaml
```

#### Option C : Via commandes CLI (nouveau)
```bash
pycalendar configs/config_volley.yaml
pycalendar-config examples/volleyball/config_volley.xlsx
pycalendar-validate solutions/latest_volley.json
pycalendar-interface
```

### 3. Imports Python

```python
# Nouvelle syntaxe (v2.0)
from pycalendar import Config, SchedulingPipeline
from pycalendar.core.models import Equipe, Gymnase, Match
from pycalendar.interface.core.generator import InterfaceGenerator

# Créer un pipeline
config = Config.from_yaml("configs/config_volley.yaml")
pipeline = SchedulingPipeline(config)
solution = pipeline.run()
```

## 📁 Correspondance ancienne → nouvelle structure

### Packages Python

| Ancien chemin | Nouveau chemin |
|---------------|----------------|
| `core/` | `src/pycalendar/core/` |
| `data/` | `src/pycalendar/data/` |
| `constraints/` | `src/pycalendar/constraints/` |
| `generators/` | `src/pycalendar/generators/` |
| `solvers/` | `src/pycalendar/solvers/` |
| `orchestrator/` | `src/pycalendar/orchestrator/` |
| `exporters/` | `src/pycalendar/exporters/` |
| `validation/` | `src/pycalendar/validation/` |
| `interface/` | `src/pycalendar/interface/` |

### Scripts CLI

| Ancien nom | Nouveau chemin | Commande CLI |
|------------|----------------|--------------|
| `actualiser_config.py` | `src/pycalendar/cli/config_tools.py` | `pycalendar-config` |
| `extract_poules.py` | `src/pycalendar/cli/pool_extractor.py` | `pycalendar-extract` |
| `generer_feuille_matchs.py` | `src/pycalendar/cli/match_sheet_generator.py` | `pycalendar-sheet` |
| `importer_matchs_externes.py` | `src/pycalendar/cli/external_importer.py` | `pycalendar-import` |
| `validate_solution.py` | `src/pycalendar/cli/solution_validator.py` | `pycalendar-validate` |
| `check_solution_quality.py` | `src/pycalendar/cli/quality_checker.py` | `pycalendar-check` |
| `regenerate_interface.py` | `src/pycalendar/cli/interface_regenerator.py` | `pycalendar-interface` |

### Exemples et données

| Ancien nom | Nouveau chemin |
|------------|----------------|
| `data_volley/` | `examples/volleyball/` |
| `data_hand/` | `examples/handball/` |
| `exemple/` | `examples/basic/` |

## 🔧 Maintenance

### Ajouter un nouveau module
1. Créer dans `src/pycalendar/mon_module/`
2. Utiliser imports : `from pycalendar.core import ...`
3. Si export public : ajouter à `src/pycalendar/__init__.py`

### Ajouter un outil CLI
1. Créer `src/pycalendar/cli/mon_outil.py`
2. Ajouter fonction `main()`
3. Enregistrer dans `setup.py` :
   ```python
   entry_points={
       "console_scripts": [
           "pycalendar-mon-outil=pycalendar.cli.mon_outil:main",
       ],
   }
   ```
4. Réinstaller : `pip install -e .`

### Lancer les tests (quand créés)
```bash
pytest
pytest --cov=pycalendar
```

## ⚠️ Points d'attention

### ✅ Ce qui fonctionne
- ✅ Installation package : `pip install -e .`
- ✅ Imports : `from pycalendar import ...`
- ✅ Main.py : `python main.py`
- ✅ Module : `python -m pycalendar`
- ✅ 24 fichiers avec imports corrigés automatiquement

### ⚡ À vérifier
- Scripts dans `scripts/` (apply_modifications.py, etc.) : imports à mettre à jour si nécessaire
- Configs YAML : chemins vers examples/ au lieu de data_volley/
- Scripts CLI : tester chaque commande individuellement

### 📝 À faire (optionnel)
- [ ] Créer `tests/` avec pytest
- [ ] Mettre à jour README.md avec nouvelle structure
- [ ] Ajouter badges (CI/CD, coverage)
- [ ] Documenter chaque commande CLI

## 🎓 Ressources

- `docs/ARCHITECTURE.md` - Documentation complète architecture
- `src/pycalendar/` - Code source commenté
- `interface/README.md` - Documentation interface web
- `README.md` - Guide utilisateur

## 💡 Conseils

1. **Toujours** activer l'environnement virtuel avant de travailler
2. **Tester** après chaque modification importante
3. **Documenter** les nouveaux modules
4. **Suivre** la structure existante pour la cohérence

## 🆘 En cas de problème

### Import error
```bash
# Réinstaller le package
pip install -e .
```

### Module not found
```bash
# Vérifier que src/ est dans PYTHONPATH
python -c "import sys; print('\n'.join(sys.path))"
```

### Tests des imports
```bash
python -c "from pycalendar import Config; print('✅ OK')"
```

---

**Félicitations !** 🎉 Votre projet suit maintenant les standards Python modernes !
