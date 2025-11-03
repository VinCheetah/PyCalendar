# 🎯 Vue Poules - Guide de Démarrage Rapide

## Comment accéder à la vue Poules

1. **Ouvrez le fichier** `new_calendar.html` dans votre navigateur
2. **Cliquez sur le bouton "Poules"** dans la barre latérale gauche (icône 🎯)
3. **Explorez les poules** organisées par genre et niveau

## Principales fonctionnalités

### 📊 Voir les statistiques globales
Les cartes en haut affichent :
- Nombre de poules
- Total d'équipes
- Total de matchs
- Matchs planifiés vs non planifiés

### 👥 Organiser par genre
Les poules sont automatiquement séparées en deux colonnes :
- **Colonne gauche** : Poules féminines (♀️) en rose
- **Colonne droite** : Poules masculines (♂️) en bleu

### 🔍 Développer une poule
1. **Cliquez sur l'en-tête** d'une poule
2. Le bouton ▶ se transforme en ▼
3. Le contenu se déploie avec animation

### 📋 Consulter le classement
Dans chaque poule développée :
- **Tableau de classement** avec positions, victoires, défaites, points
- **Podium visuel** : Or 🥇, Argent 🥈, Bronze 🥉
- **Tri automatique** par points

### ⚽ Explorer les matchs
Trois onglets disponibles :
1. **À venir** : Matchs futurs planifiés
2. **Joués** : Matchs passés avec scores
3. **Tous** : Vue complète

### 🎨 Personnaliser l'affichage
- **Thème clair** : ☀️ en haut à droite
- **Thème sombre** : 🌙 en haut à droite  
- **Thème France** : 🇫🇷 en haut à droite (recommandé!)

### 📱 Utiliser sur mobile
L'interface s'adapte automatiquement :
- Les colonnes passent en liste verticale
- Les statistiques s'empilent
- Les matchs s'affichent en liste simple

## Interactions rapides

| Action | Résultat |
|--------|----------|
| **Clic sur en-tête de poule** | Développe/réduit la poule |
| **Clic sur onglet match** | Change la vue des matchs |
| **Double-clic sur match** | Ouvre l'édition (si disponible) |
| **Survol carte** | Effet d'élévation et brillance |

## Informations affichées

### Par poule
- Nom et niveau
- Genre (♀️/♂️)
- Nombre d'équipes
- Nombre de matchs
- Statistiques détaillées

### Par match
- Date et horaire 🕒
- Équipes (noms complets)
- Score (si joué)
- Gymnase 📍
- Statut (Joué/À venir)
- Pénalités (avec code couleur)

### Par équipe (dans classement)
- Position (#)
- Nom
- Matchs joués (J)
- Victoires (G)
- Nuls (N)
- Défaites (P)
- Points (Pts)

## Filtres disponibles

Utilisez la barre latérale de filtres pour :
- **Genre** : Afficher uniquement F ou M
- **Poule spécifique** : Isoler une poule
- **Autres filtres** : Selon configuration

## Astuces

💡 **Pour imprimer** : Utilisez Ctrl+P (les styles d'impression sont optimisés)

💡 **Pour partager** : Le fichier HTML est autonome, envoyez-le directement

💡 **Pour analyser** : Les statistiques sont calculées en temps réel

💡 **Pour comparer** : Ouvrez plusieurs poules simultanément

💡 **Performance** : Les animations utilisent le GPU pour une fluidité maximale

## Problèmes courants

### Les poules ne s'affichent pas
- Vérifiez que le fichier JSON contient des poules
- Rechargez la page (F5)
- Consultez la console (F12)

### Les animations sont saccadées
- Fermez les onglets inutilisés
- Désactivez les extensions de navigateur
- Utilisez un navigateur moderne (Chrome, Firefox, Edge)

### Le design ne s'affiche pas correctement
- Vérifiez que le CSS est chargé (F12 > Network)
- Essayez un autre navigateur
- Videz le cache (Ctrl+Shift+R)

## Support

Pour plus d'informations :
- 📖 Consultez `POOLS_VIEW_IMPROVEMENTS.md` pour la documentation complète
- 🐛 Rapportez les bugs sur GitHub
- 💬 Posez vos questions dans les issues

---

**Bon usage de la vue Poules ! 🎉**
