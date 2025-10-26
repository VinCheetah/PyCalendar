# 📁 Interface PyCalendar - Architecture Modulaire

## 🎯 Vue d'ensemble

Ce dossier contient la nouvelle interface HTML modulaire pour PyCalendar, conçue pour être **maintenable**, **extensible** et **performante**.

### Principes de conception

1. **Modularité** : Code organisé en modules indépendants et réutilisables
2. **Séparation des responsabilités** : Backend (Python) pour les données, Frontend (HTML/CSS/JS) pour l'affichage
3. **Auto-suffisant** : L'HTML généré est autonome (pas de dépendances externes)
4. **Exportable** : Système d'export/import JSON pour les modifications
5. **Qualité** : Code commenté, nommage clair, structure logique

---

## 📂 Structure des dossiers

```
interface/
├── core/                           # Backend Python
│   ├── data_formatter.py           # Transformation Solution → JSON v2.0
│   └── generator.py                # Assemblage HTML final
│
├── assets/                         # Ressources statiques
│   └── styles/                     # CSS modulaire
│       ├── 00-variables.css        # Variables CSS (couleurs, espacements)
│       ├── 01-reset.css            # Reset navigateur
│       ├── 02-base.css             # Typographie et utilitaires
│       ├── 03-layout.css           # Grilles et mise en page
│       ├── components/             # Styles des composants
│       │   ├── match-card.css      # Cartes de match
│       │   ├── filters.css         # Panneaux de filtres
│       │   └── modals.css          # Fenêtres modales
│       └── themes/                 # Thèmes visuels
│           └── default-light.css   # Thème par défaut
│
├── scripts/                        # JavaScript modulaire
│   ├── core/                       # Gestion de données
│   │   └── data-manager.js         # Gestionnaire central de données
│   ├── data/                       # Stockage et modifications
│   │   └── modification-manager.js # Export/Import JSON, undo/redo
│   ├── views/                      # Vues de l'interface
│   │   ├── agenda-view.js          # Vue Agenda (priorité 1)
│   │   ├── pools-view.js           # Vue Poules (priorité 2)
│   │   └── cards-view.js           # Vue Cartes (priorité 3)
│   ├── components/                 # Composants réutilisables
│   │   ├── match-card.js           # Composant carte de match
│   │   ├── filter-panel.js         # Panneau de filtres
│   │   └── edit-modal.js           # Fenêtre d'édition
│   └── utils/                      # Utilitaires
│       ├── formatters.js           # Formatage de dates, heures, etc.
│       └── validators.js           # Validation de données
│
├── templates/                      # Templates HTML
│   └── index.html                  # Template principal
│
└── data/                           # Schémas et documentation
    └── schemas/                    # Schémas JSON
        ├── solution_schema.json    # Format de données v2.0
        └── modification_schema.json # Format d'export
```

---

## 🔄 Flux de travail

### 1. Génération de l'interface

```bash
# Générer l'interface depuis une solution
python regenerate_interface.py

# Depuis une solution spécifique
python regenerate_interface.py --solution solution_volley_2025-10-13

# Avec nom de fichier personnalisé
python regenerate_interface.py --output mon_calendrier.html
```

**Processus interne :**
1. `data_formatter.py` transforme la Solution Python en JSON v2.0 enrichi
2. `generator.py` charge le template HTML
3. Combine tous les CSS dans l'ordre (variables → reset → base → layout → composants → thème)
4. Combine tous les JS (core → data → views → components → utils)
5. Injecte le JSON de la solution
6. Produit un fichier HTML autonome

### 2. Utilisation de l'interface

1. Ouvrir le fichier HTML généré dans un navigateur
2. Filtrer les matchs (genre, institution, poule, etc.)
3. Basculer entre les vues (Agenda, Poules, Cartes, etc.)
4. Éditer les matchs (drag & drop, modal d'édition)
5. Exporter les modifications en JSON

### 3. Application des modifications

```bash
# Appliquer les modifications exportées
python interface/scripts/apply_modifications_interface.py modifications_2025-10-24.json

# Sur une solution spécifique
python interface/scripts/apply_modifications_interface.py mods.json --solution latest_volley

# Avec nom de sortie personnalisé
python interface/scripts/apply_modifications_interface.py mods.json --output solution_modifiee
```

**Processus interne :**
1. Charge le fichier de modifications JSON
2. Charge la solution source
3. Applique chaque modification (semaine, horaire, gymnase)
4. Sauvegarde une nouvelle solution avec métadonnées de modification
5. Propose de régénérer l'interface HTML

---

## 📊 Format de données v2.0

L'interface utilise un format JSON enrichi qui contient :

### Structure globale

```json
{
  "version": "2.0",
  "metadata": {
    "generation_date": "2025-01-24T15:30:00",
    "solution_name": "latest_volley",
    "config_signature": "config_volley"
  },
  "entities": { ... },
  "matches": { ... },
  "slots": { ... },
  "statistics": { ... }
}
```

### Entities (Entités du système)

- **equipes** : Liste des équipes avec `id`, `nom`, `institution`, `genre`, `poule`
- **gymnases** : Liste des gymnases avec `id`, `nom`, `capacite`, `institution`
- **poules** : Liste des poules avec `id`, `nom`, `niveau`, `genre`, `nb_equipes`

### Matches (Matchs)

- **scheduled** : Matchs planifiés avec `semaine`, `horaire`, `gymnase`, `penalties`
- **unscheduled** : Matchs non planifiés avec raisons

### Slots (Créneaux)

- **available** : Créneaux disponibles
- **occupied** : Créneaux occupés avec références aux matchs

### Statistics (Statistiques pré-calculées)

- Par semaine : nombre de matchs, utilisation des gymnases
- Par poule : nombre de matchs, répartition
- Par gymnase : taux d'occupation, matchs hébergés
- Par équipe : matchs à domicile/extérieur, répartition horaire

---

## 🎨 Architecture CSS

### Ordre de chargement (important !)

1. **00-variables.css** : Définition des variables CSS
2. **01-reset.css** : Normalisation navigateur
3. **02-base.css** : Typographie de base
4. **03-layout.css** : Système de grille et mise en page
5. **components/*.css** : Styles des composants
6. **themes/*.css** : Thème visuel

### Variables clés

```css
/* Couleurs principales */
--primary: #0055A4;
--danger: #EF4444;
--success: #10B981;
--warning: #F59E0B;

/* Couleurs de genre */
--male: #3B82F6;
--female: #EC4899;

/* Espacement */
--spacing-xs: 0.25rem;
--spacing-sm: 0.5rem;
--spacing-md: 1rem;
--spacing-lg: 1.5rem;
--spacing-xl: 2rem;
```

### Modes de coloration des cartes

- **Genre** : Bleu (M) / Rose (F)
- **Niveau** : Dégradé selon le niveau de la poule
- **Institution** : Couleur par institution

---

## 🧩 Architecture JavaScript

### DataManager (core/data-manager.js)

Gestionnaire central de données avec :
- **Indexes Map** : Accès O(1) aux matchs par ID, semaine, poule, gymnase
- **Observer Pattern** : Notification des changements aux vues
- **CRUD Operations** : Create, Read, Update, Delete des matchs
- **State Synchronization** : Cohérence entre les vues

```javascript
// Exemple d'utilisation
window.dataManager.subscribe('matches', (matches) => {
    // Mise à jour de la vue
});

const match = window.dataManager.getMatchById('match_123');
window.dataManager.updateMatch('match_123', { semaine: 2, horaire: '18:00' });
```

### ModificationManager (data/modification-manager.js)

Gestion des modifications avec :
- **Tracking** : Enregistrement de toutes les modifications
- **Undo/Redo** : Historique des actions
- **Export JSON** : Export conforme au schéma
- **Persistence** : Sauvegarde locale (localStorage)

```javascript
// Ajout d'une modification
window.modificationManager.addModification('match_123', originalSlot, newSlot);

// Export
const json = window.modificationManager.exportToJSON();
window.modificationManager.exportAndDownload('mes_modifications.json');

// Undo/Redo
window.modificationManager.undo();
window.modificationManager.redo();
```

---

## 🚀 Développement

### Ajouter une nouvelle vue

1. Créer `interface/scripts/views/ma-vue.js`
2. Implémenter les méthodes : `init()`, `render()`, `update()`, `destroy()`
3. S'abonner aux événements du DataManager
4. Ajouter le script dans `generator.py` → `_load_all_js()`
5. Ajouter un onglet dans `templates/index.html`

### Ajouter un composant

1. Créer `interface/scripts/components/mon-composant.js`
2. Créer `interface/assets/styles/components/mon-composant.css`
3. Ajouter les fichiers dans `generator.py`
4. Utiliser le composant dans les vues

### Ajouter un thème

1. Créer `interface/assets/styles/themes/mon-theme.css`
2. Définir les variables CSS override
3. Charger conditionnellement dans `generator.py`

---

## 📝 TODO / Améliorations futures

### ✅ Complété

- [x] Architecture modulaire (27 dossiers)
- [x] Format de données v2.0 avec JSON schemas
- [x] CSS modulaire (10 fichiers ciblés vs 6222 lignes monolithiques)
- [x] DataManager avec indexes et observer pattern
- [x] ModificationManager avec export/import JSON
- [x] InterfaceGenerator pour assemblage HTML
- [x] Template HTML avec placeholders
- [x] Scripts d'entrée (regenerate_interface.py, apply_modifications_interface.py)
- [x] Vue Agenda (calendrier par semaine)
- [x] Vue Poules (classements et matchs par poule)
- [x] Vue Cartes (grille de cartes filtrables)
- [x] Utilitaires (formatters.js, validators.js)
- [x] Système de filtrage multi-critères
- [x] Styles CSS pour les 3 vues prioritaires

### Priorité 1 - Composants essentiels
- [ ] match-card.js - Composant carte réutilisable
- [ ] filter-panel.js - Gestionnaire de filtres avancés
- [ ] edit-modal.js - Fenêtre d'édition de match avec validation

### Priorité 2 - Fonctionnalités
- [ ] Drag & Drop pour déplacer les matchs entre créneaux
- [ ] Vue Pénalités détaillée avec graphiques
- [ ] Vue Statistiques complète avec tableaux de bord
- [ ] Vue Non Planifiés avec suggestions de créneaux
- [ ] Validation en temps réel des contraintes

### Priorité 3 - Optimisations
- [ ] Virtualisation pour grandes listes (>500 matchs)
- [ ] Cache des vues rendues
- [ ] Lazy loading des composants
- [ ] Service Worker pour usage offline
- [ ] Compression des données

### Priorité 4 - Accessibilité & UX
- [ ] Support clavier complet (navigation, édition)
- [ ] ARIA labels pour accessibilité
- [ ] Mode sombre / thème personnalisable
- [ ] Responsive mobile amélioré
- [ ] Internationalisation (i18n)

---

## 🐛 Dépannage

### L'HTML généré ne s'affiche pas correctement

- Vérifier que tous les CSS sont chargés dans le bon ordre
- Ouvrir la console navigateur pour voir les erreurs JS
- Vérifier que le JSON de données est valide

### Les modifications ne sont pas sauvegardées

- Vérifier que localStorage est activé dans le navigateur
- Vérifier la quota localStorage (limite ~5-10 MB)
- Exporter régulièrement en JSON pour ne pas perdre de données

### L'export JSON échoue

- Vérifier le schéma dans `data/schemas/modification_schema.json`
- Vérifier la console pour les erreurs de validation
- S'assurer que tous les champs requis sont présents

---

## 📚 Ressources

- **Schémas JSON** : `interface/data/schemas/`
- **Documentation API** : Commentaires dans les fichiers sources
- **Exemples** : Voir `solutions/latest_volley.json` pour un exemple de données

---

## 🤝 Contribution

Pour contribuer à l'interface :

1. Respecter l'architecture modulaire
2. Commenter le code en français
3. Suivre les conventions de nommage (camelCase JS, kebab-case CSS)
4. Tester dans plusieurs navigateurs
5. Documenter les nouveaux composants dans ce README

---

**Dernière mise à jour** : 2025-01-24  
**Version** : 2.0  
**Auteur** : PyCalendar Team
