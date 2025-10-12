# Guide de Contribution - PyCalendar

Merci de votre intérêt pour PyCalendar ! 🎉

## 🚀 Démarrage pour les Contributeurs

### 1. Fork et Clone

```bash
git clone https://github.com/VOTRE_USERNAME/PyCalendar.git
cd PyCalendar
```

### 2. Créer un environnement virtuel

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

### 3. Créer une branche

```bash
git checkout -b feature/ma-nouvelle-fonctionnalite
```

## 📁 Structure du Projet

```
PyCalendar/
├── core/               # Composants centraux
│   ├── config.py       # Gestion de la configuration
│   ├── config_manager.py  # Gestion des fichiers Excel
│   └── utils.py        # Utilitaires
├── data/               # Chargement des données
│   ├── data_loader.py  # Chargement depuis Excel
│   └── data_source.py  # Interface de données
├── generators/         # Génération de matchs
│   └── multi_pool_generator.py
├── constraints/        # Système de contraintes
│   ├── constraint_manager.py
│   └── types/          # Types de contraintes
├── solvers/            # Algorithmes d'optimisation
│   ├── cpsat_solver.py    # OR-Tools CP-SAT
│   └── greedy_solver.py   # Algorithme glouton
├── exporters/          # Export des résultats
│   └── excel_exporter.py
├── visualization/      # Visualisation web
│   └── html_generator.py
├── orchestrator/       # Orchestration globale
│   └── pipeline.py
├── validation/         # Validation des solutions
│   └── solution_validator.py
└── configs/            # Configurations par défaut
    └── default.yaml
```

## 🎯 Domaines de Contribution

### 🐛 Corrections de Bugs
- Consultez les [Issues](../../issues) étiquetées `bug`
- Ajoutez des tests pour reproduire le bug
- Proposez une correction avec Pull Request

### ✨ Nouvelles Fonctionnalités
- Consultez les [Issues](../../issues) étiquetées `enhancement`
- Discutez de votre idée dans une issue avant de coder
- Suivez l'architecture existante

### 📚 Documentation
- Améliorez les README
- Ajoutez des exemples
- Corrigez les fautes de frappe

### 🧪 Tests
- Ajoutez des tests unitaires
- Améliorez la couverture de code
- Testez sur différents scénarios

## 📝 Standards de Code

### Style Python
- Suivez [PEP 8](https://pep8.org/)
- Utilisez des noms de variables explicites
- Commentez les parties complexes
- Type hints encouragés

### Documentation
- Docstrings pour toutes les fonctions/classes
- Format Google Style

```python
def ma_fonction(param1: str, param2: int) -> bool:
    """
    Description courte de la fonction.
    
    Args:
        param1: Description du paramètre 1
        param2: Description du paramètre 2
        
    Returns:
        Description du retour
        
    Raises:
        ValueError: Quand param2 est négatif
    """
    pass
```

### Messages de Commit
Format conventionnel :

```
type(scope): description courte

Description détaillée si nécessaire

Closes #123
```

**Types** :
- `feat`: Nouvelle fonctionnalité
- `fix`: Correction de bug
- `docs`: Documentation
- `style`: Formatage, point-virgule manquant, etc.
- `refactor`: Refactoring de code
- `test`: Ajout/modification de tests
- `chore`: Tâches de maintenance

**Exemples** :
```
feat(constraints): ajout contrainte min matchs par semaine
fix(cpsat): correction warm start avec variables booléennes
docs(readme): ajout section installation
```

## 🔄 Processus de Pull Request

1. **Mettez à jour votre branche**
   ```bash
   git checkout main
   git pull origin main
   git checkout votre-branche
   git rebase main
   ```

2. **Testez localement**
   ```bash
   python main.py exemple/config.yaml
   ```

3. **Commitez vos changements**
   ```bash
   git add .
   git commit -m "feat(scope): description"
   ```

4. **Poussez vers votre fork**
   ```bash
   git push origin votre-branche
   ```

5. **Créez une Pull Request**
   - Titre clair et descriptif
   - Description détaillée des changements
   - Référencez les issues liées
   - Ajoutez des captures d'écran si pertinent

## 🧪 Tests

### Exécuter les tests
```bash
# Tests unitaires (si disponibles)
python -m pytest tests/

# Test manuel avec exemple
python main.py exemple/config.yaml
```

### Ajouter un test
Créez un fichier dans `tests/` :

```python
import unittest
from core.config import Config

class TestConfig(unittest.TestCase):
    def test_chargement_config(self):
        config = Config("exemple/config.yaml")
        self.assertIsNotNone(config)
```

## 📋 Checklist avant Pull Request

- [ ] Le code suit PEP 8
- [ ] Docstrings ajoutés/mis à jour
- [ ] Tests ajoutés si nouvelle fonctionnalité
- [ ] Documentation mise à jour
- [ ] Les tests passent localement
- [ ] Commit messages suivent la convention
- [ ] Branche à jour avec `main`

## ❓ Questions ?

- Ouvrez une [Discussion](../../discussions)
- Consultez la [Documentation](README.md)
- Contactez les mainteneurs

## 📜 Licence

En contribuant, vous acceptez que vos contributions soient sous la même licence que le projet.

---

**Merci de contribuer à PyCalendar !** 🙏
