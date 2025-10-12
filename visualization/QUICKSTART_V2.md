# 🚀 PyCalendar Pro V2 - Guide de Démarrage Rapide

## ⚡ Démarrage en 3 étapes

### 1. Générer le calendrier

```bash
cd /home/vincheetah/Documents/Travail/FFSU/PyCalendar
python3 main.py data_volley/config.yaml
```

### 2. Ouvrir l'interface V2

Le fichier `*_v2.html` est généré automatiquement :

```bash
# Avec votre navigateur par défaut
xdg-open results/calendrier_v2.html

# Ou spécifiquement Firefox/Chrome
firefox results/calendrier_v2.html
google-chrome results/calendrier_v2.html
```

### 3. Explorer les fonctionnalités

## 🎯 Fonctionnalités Principales

### 🔍 Contrôle de Zoom
En haut des contrôles, utilisez les boutons **−** **+** **⟲** pour :
- **−** Réduire à 75% (compact)
- **+** Agrandir à 125% (large)
- **⟲** Réinitialiser à 100%

### 📊 Vue Planning Moderne (Nouvel onglet !)

Cliquez sur l'onglet **"📊 Planning Moderne"** puis choisissez :

#### 🌐 Vue Totale
- Voir toutes les semaines d'un coup d'œil
- Résumé par gymnase
- Parfait pour une vue d'ensemble

#### 📅 Vue Journée ⭐
1. Sélectionnez une **semaine** dans les filtres
2. Voyez le planning détaillé avec :
   - Horaires en vertical (échelle proportionnelle)
   - Gymnases en colonnes
   - Matchs positionnés sur leurs horaires
   - Créneaux libres visibles (si activé)

#### 👥 Vue Équipe
1. Sélectionnez une **équipe** dans les filtres
2. Voyez tous ses matchs

#### 🏢 Vue Gymnase
1. Sélectionnez un **gymnase** dans les filtres
2. Voyez son planning complet

### ⚙️ Options d'Affichage

En bas des contrôles, activez/désactivez :

- **⏰ Horaires préférés** : Voir les préférences horaires des équipes
- **🏛️ Institutions** : Afficher les noms d'institutions
- **⚧️ Badges genre** : Afficher M/F sur les cartes
- **📅 Créneaux libres** : Voir les créneaux non utilisés (en hachuré dans le planning)

💾 **Les préférences sont sauvegardées automatiquement !**

### 🔎 Filtres Intelligents

Combinez les filtres pour affiner :
- **Genre** : Masculin / Féminin / Tous (boutons visuels)
- **Institution** : Choisir un établissement
- **Équipe** : Sélection d'équipe (s'adapte à l'institution/genre)
- **Poule** : Filtrer par poule
- **Gymnase** : Focus sur un gymnase
- **Semaine** : Voir une semaine spécifique

## 🎨 Scénarios d'Utilisation

### Je veux voir le planning d'une journée spécifique

1. Onglet **📊 Planning Moderne**
2. Cliquer sur **📅 Vue Journée**
3. Filtre **Semaine** → Sélectionner la semaine voulue
4. ✅ Vous voyez le planning détaillé avec horaires !

### Je veux vérifier les matchs d'une équipe

1. Filtre **Équipe** → Sélectionner l'équipe
2. Onglet **📅 Calendrier** pour voir par semaine
3. Ou onglet **📊 Planning Moderne** → **👥 Vue Équipe**
4. ✅ Tous les matchs de l'équipe sont mis en évidence !

### Je veux voir l'utilisation d'un gymnase

1. Filtre **Gymnase** → Sélectionner le gymnase
2. Onglet **📊 Planning Moderne** → **🏢 Vue Gymnase**
3. ✅ Vous voyez le planning complet du gymnase par semaine !

### Je veux une vue compacte pour tout voir

1. Cliquer sur **−** pour passer en mode compact (75%)
2. Onglet **📅 Calendrier**
3. ✅ Plus de matchs visibles à l'écran !

### Je veux voir les créneaux encore disponibles

1. Activer le toggle **📅 Créneaux libres**
2. Onglet **📊 Planning Moderne** → **📅 Vue Journée**
3. Sélectionner une semaine
4. ✅ Les créneaux libres apparaissent en hachuré !

## 💡 Astuces

### Navigation Rapide
- **Onglets** : Changer de vue
- **🔄 Réinitialiser** : Effacer tous les filtres
- **Shift + Molette** : Zoom navigateur (si nécessaire)

### Informations au Survol
- Survolez les cartes pour voir les détails
- Tooltips sur les créneaux libres
- Info-bulles sur les contrôles

### Statistiques en Temps Réel
En haut, vous voyez :
- Matchs planifiés
- Matchs non planifiés
- Nombre de semaines
- Nombre de poules
- Nombre de gymnases
- **Créneaux libres** 🆕

### Barre d'Info Contextuelle
Quand vous filtrez par Institution ou Équipe, une barre bleue apparaît avec :
- Nombre de matchs planifiés
- Nombre de matchs non planifiés
- Semaines utilisées
- Gymnases utilisés

## 🐛 Résolution de Problèmes

### L'interface ne charge pas
- Vérifiez que le fichier `*_v2.html` existe
- Ouvrez la console du navigateur (F12)
- Rafraîchissez la page (Ctrl+R)

### Les créneaux libres ne s'affichent pas
- Assurez-vous que le toggle **📅 Créneaux libres** est activé
- Allez dans l'onglet **📊 Planning Moderne**
- Sélectionnez **📅 Vue Journée**
- Choisissez une semaine

### La vue planning est vide
- Pour **📅 Vue Journée** : Sélectionnez une semaine dans les filtres
- Pour **👥 Vue Équipe** : Sélectionnez une équipe dans les filtres
- Pour **🏢 Vue Gymnase** : Sélectionnez un gymnase dans les filtres

### Les filtres ne fonctionnent pas
- Cliquez sur **🔄 Réinitialiser** pour repartir de zéro
- Vérifiez que vous êtes dans le bon onglet
- Actualisez la page si nécessaire

## 📱 Sur Mobile/Tablette

L'interface est responsive :
- Les grilles s'adaptent
- Navigation tactile optimisée
- Menus déroulants accessibles
- Pas de perte de fonctionnalité

## 🎓 Prochaines Étapes

Une fois familiarisé avec l'interface :
1. Explorez les différentes combinaisons de filtres
2. Testez tous les modes de la vue planning
3. Personnalisez les options d'affichage
4. Comparez avec les versions classique et premium

## 📚 Documentation Complète

Pour aller plus loin :
- `README_V2.md` - Architecture et détails techniques
- `SUMMARY_V2.md` - Résumé complet des améliorations
- Code source commenté dans `components/`

---

**Besoin d'aide ?** Consultez la documentation ou inspectez le code source bien commenté !

🏐 **PyCalendar Pro V2** - Visualisation de calendrier sportif moderne et intuitive ✨
