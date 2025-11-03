# Dev Tools - Outils de Développement

Ce dossier contient des outils de diagnostic et de débogage pour le développement de l'interface PyCalendar.

## 📁 Contenu

### button-checker.js

**Utilité**: Outil de diagnostic pour vérifier le bon fonctionnement de tous les boutons de l'interface.

**Fonctionnalités**:
- ✅ Vérifie les boutons de thème (clair/sombre/france)
- ✅ Vérifie les boutons de sport (volleyball, handball, etc.)
- ✅ Vérifie les boutons de vue (agenda, poules, cartes)
- ✅ Vérifie les boutons de sidebar (collapse/expand)
- ✅ Vérifie les boutons d'action (export, reset, print)
- ✅ Vérifie les éléments de filtre (radios, checkboxes, selects)
- ✅ Vérifie les boutons d'export et d'aide
- ✅ Génère un rapport détaillé avec statistiques

**Utilisation**:

1. Ouvrir la console du navigateur (F12)
2. Charger le script dans la console:
   ```javascript
   // Copier-coller le contenu de button-checker.js dans la console
   ```
3. Exécuter la vérification:
   ```javascript
   ButtonChecker.checkAllButtons();
   ```

**Sortie Exemple**:
```
🔍 Vérification des boutons
  🎨 Boutons de thème
    ✅ Thème "light": Listener: ✓, Accessible: ✓
    ✅ Thème "dark": Listener: ✓, Accessible: ✓
    ✅ Thème "tricolore": Listener: ✓, Accessible: ✓
  ...
  
📊 Résumé: 42/45 boutons fonctionnels
⚠️  3 bouton(s) nécessite(nt) une correction
```

**Quand l'utiliser**:
- Après modifications du HTML ou du JavaScript
- Lors de l'ajout de nouveaux boutons
- Pour diagnostiquer des problèmes d'interaction
- Pendant le développement de nouvelles fonctionnalités

**Note**: Cet outil n'est PAS chargé dans l'interface générée (non présent dans generator.py). C'est un outil de développement manuel à utiliser uniquement en dev.

## 🔧 Ajouter d'autres outils

Pour ajouter de nouveaux outils de diagnostic, suivre ce modèle:

1. Créer un fichier `.js` dans ce dossier
2. Documenter son usage dans ce README
3. Ne PAS l'ajouter à `generator.py` (outils dev seulement)
4. Utiliser un namespace pour éviter les conflits (ex: `MyToolName = {}`)

## 📝 Bonnes Pratiques

- ✅ Les outils dev ne doivent JAMAIS être inclus dans la production
- ✅ Documenter chaque outil dans ce README
- ✅ Utiliser des namespaces pour éviter les conflits globaux
- ✅ Inclure des exemples d'utilisation
- ✅ Ajouter des emojis et du formatage pour les outputs console
