# PyCalendar Pro V2 - Interface de Visualisation Modulaire

## 📋 Vue d'ensemble

La nouvelle interface V2 de PyCalendar Pro propose une architecture modulaire professionnelle avec des fonctionnalités avancées de visualisation et de filtrage.

## 🏗️ Architecture

### Structure des fichiers

```
visualization/
├── components/                      # Composants JavaScript/CSS modulaires
│   ├── styles.css                  # Styles CSS avec variables pour zoom
│   ├── utils.js                    # Fonctions utilitaires
│   ├── filters.js                  # Gestion des filtres et préférences
│   ├── match-card.js               # Composants de rendu des matchs
│   ├── calendar-view.js            # Vues cartes (semaine, poule, gymnase)
│   └── planning-view.js            # Nouvelle vue planning moderne
├── templates/
│   └── main.html                   # Template HTML principal
├── html_visualizer_v2.py           # Builder Python
├── html_visualizer_pro.py          # Ancienne version (conservée)
└── html_visualizer.py              # Version classique (conservée)
```

## ✨ Nouvelles fonctionnalités

### 1. Contrôle de zoom dynamique
- **3 tailles** : Compact (75%), Normal (100%), Large (125%)
- Boutons +/- et réinitialisation
- Variables CSS pour ajustement fluide
- Persistance dans localStorage

### 2. Vue Planning Moderne 🎯

Une nouvelle vue révolutionnaire avec :

#### **4 modes de visualisation** :

##### 🌐 Vue Totale
- Aperçu de toutes les semaines
- Résumé par gymnase
- Limite à 4 semaines pour éviter surcharge

##### 📅 Vue Journée
- Planning détaillé d'une semaine
- Colonnes par gymnase
- Axe vertical des horaires proportionnel
- Affichage des créneaux libres (si activé)
- Matchs positionnés sur l'échelle horaire

##### 👥 Vue Équipe
- Focus sur une équipe spécifique
- Tous ses matchs affichés
- Nécessite sélection d'équipe via filtre

##### 🏢 Vue Gymnase
- Focus sur un gymnase spécifique
- Planning vertical par semaine
- Affichage des créneaux disponibles
- Nécessite sélection de gymnase via filtre

### 3. Options d'affichage avancées

Toggles pour contrôler :
- ⏰ **Horaires préférés** : Affiche les préférences horaires des équipes
- 🏛️ **Institutions** : Affiche/masque les noms d'institutions
- ⚧️ **Badges genre** : Affiche/masque les badges M/F
- 📅 **Créneaux libres** : Affiche les créneaux non utilisés dans le planning

Toutes les préférences sont sauvegardées en localStorage.

### 4. Créneaux disponibles

- Calcul automatique des créneaux non utilisés
- Affichage dans la vue planning (motif hachuré)
- Compteur dans le header
- Tooltips informatifs

### 5. Onglets améliorés

- 📅 **Calendrier** : Vue par semaines (existante améliorée)
- 📊 **Planning Moderne** : Nouvelle vue planning (🆕)
- 🎯 **Par Poule** : Groupement par poule
- 🏢 **Par Gymnase** : Groupement par gymnase
- ⚠️ **Non Planifiés** : Matchs non planifiés

## 🎨 Design

### Palette de couleurs
- Variables CSS personnalisables
- Mode cohérent avec thème gradient
- Couleurs distinctes par genre/catégorie
- États hover et focus soignés

### Animations
- Transitions fluides entre états
- FadeIn pour changements de contenu
- Hover effects sur cartes
- Tooltips animés

### Responsive
- Grilles adaptatives
- Breakpoints mobile
- Débordement géré
- Touch-friendly

## 🔧 Utilisation

### Génération automatique

La nouvelle interface V2 est générée automatiquement lors de l'exécution du pipeline :

```bash
python main.py data/config.yaml
```

Trois fichiers HTML sont créés :
- `calendrier.html` - Version classique
- `calendrier_premium.html` - Version premium
- `calendrier_v2.html` - **Nouvelle interface V2** ✨

### Filtres disponibles

1. **Genre** : Masculin / Féminin / Tous
2. **Institution** : Filtrage par établissement
3. **Équipe** : Sélection d'équipe (dépend institution/genre)
4. **Poule** : Filtrage par poule
5. **Gymnase** : Sélection de gymnase
6. **Semaine** : Sélection de semaine

Les filtres se combinent intelligemment.

### Navigation

1. **Sélectionner un onglet** pour changer de vue
2. **Utiliser les filtres** pour affiner l'affichage
3. **Ajuster le zoom** selon vos besoins
4. **Activer/désactiver les options** d'affichage
5. **Dans Planning Moderne**, choisir le mode de vue

## 🚀 Avantages de l'architecture modulaire

### Maintenabilité
- Code séparé par responsabilité
- Composants réutilisables
- Facile à débugger

### Extensibilité
- Ajout facile de nouveaux modes de vue
- Nouveaux filtres simples à implémenter
- Styles personnalisables via variables CSS

### Performance
- Chargement optimisé
- Rendu à la demande
- Pas de framework lourd

### Qualité
- Code propre et commenté
- Architecture professionnelle
- Patterns modernes

## 📝 Personnalisation

### Modifier les styles

Éditer `components/styles.css` et ajuster les variables CSS :

```css
:root {
    --primary: #4F46E5;
    --card-scale: 1;
    /* etc. */
}
```

### Ajouter un mode de vue

1. Créer la fonction dans `planning-view.js`
2. Ajouter le bouton dans le template
3. Mettre à jour le switch dans `render()`

### Nouveaux filtres

1. Ajouter dans `FilterManager` (filters.js)
2. Ajouter l'élément UI dans le template
3. Implémenter la logique de filtrage

## 🐛 Debug

Console du navigateur affiche :
- Logs d'initialisation
- Nombre de matchs chargés
- Erreurs éventuelles

## 📊 Métriques

L'interface affiche en temps réel :
- Nombre de matchs planifiés/non planifiés
- Nombre de semaines
- Nombre de poules
- Nombre de gymnases
- **Nombre de créneaux libres** 🆕

## 🎯 Points clés

1. **Modulaire** : Code séparé en composants logiques
2. **Performant** : Rendu optimisé, pas de surcharge
3. **Intuitif** : Interface moderne et claire
4. **Flexible** : Multiples vues et filtres
5. **Persistant** : Préférences sauvegardées
6. **Responsive** : Adapté mobile/desktop

## 🔄 Migration depuis ancienne version

L'ancienne version reste disponible. La V2 est générée en parallèle avec le suffixe `_v2.html`.

Aucune modification des données d'entrée nécessaire. Tout est rétrocompatible.

## 📞 Support

Pour toute question ou amélioration, référez-vous au code source bien commenté dans chaque module.

---

**PyCalendar Pro V2** - Interface de planification sportive de nouvelle génération 🏐✨
