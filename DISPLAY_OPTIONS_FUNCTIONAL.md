# Options d'Affichage PyCalendar - Fonctionnelles et Testées

## 🎯 Vue Poules - 5 Options Fonctionnelles

### 1. 📐 Format d'affichage
**Type:** Boutons radio (3 choix)  
**Options:** Cartes / Compact / Liste  
**Par défaut:** Cartes  

**Ce que ça fait:**
- **Cartes**: Affichage riche avec toutes les informations dans des cartes développables
- **Compact**: Vue condensée pour voir plus de poules en un coup d'œil
- **Liste**: Format tableau simple avec colonnes (nom, niveau, équipes, matchs)

**Fonctionnement:** Change complètement la méthode de rendu des poules (`_generatePoolCard`, `_generatePoolCompact`, `_generatePoolListRow`)

---

### 2. 👥 Afficher liste des équipes
**Type:** Case à cocher  
**Par défaut:** Désactivé  

**Ce que ça fait:**
- Active/désactive l'affichage de la liste complète des équipes dans chaque poule développée
- Utile pour voir rapidement toutes les équipes participantes sans chercher dans les matchs

**Fonctionnement:** Contrôle l'appel à `_generateTeamsList()` dans le contenu développé

---

### 3. ⭐ Afficher préférences équipes
**Type:** Case à cocher  
**Par défaut:** Désactivé  

**Ce que ça fait:**
- Affiche les horaires préférés, lieux préférés et semaines d'indisponibilité de chaque équipe
- Visible uniquement quand la liste des équipes est activée

**Fonctionnement:** Ajoute la section `.team-item-details` avec les préférences dans `_generateTeamsList()`

---

### 4. 📊 Séparateurs de niveau
**Type:** Case à cocher  
**Par défaut:** Activé  

**Ce que ça fait:**
- Ajoute des séparateurs visuels entre les différents niveaux de compétition (Excellence, Régional, etc.)
- Améliore la lisibilité en organisant visuellement les poules

**Fonctionnement:** Contrôle l'affichage des `.level-separator` dans `_generateGenderSection()`

---

### 5. 📖 Tout développer
**Type:** Case à cocher  
**Par défaut:** Désactivé  

**Ce que ça fait:**
- **Activé**: Développe automatiquement toutes les poules pour voir leur contenu
- **Désactivé**: Réduit toutes les poules (clic manuel pour développer)

**Fonctionnement:** Manipule le Set `this.expandedPools` pour ajouter/retirer tous les IDs de poules

---

## 📅 Vue Agenda - 2 Options Fonctionnelles

### 1. 📊 Organiser par
**Type:** Boutons radio (2 choix)  
**Options:** Gymnase / Semaine  
**Par défaut:** Gymnase  

**Ce que ça fait:**
- **Gymnase**: Une colonne par gymnase, voir l'occupation de chaque lieu
- **Semaine**: Une colonne par semaine, voir la progression temporelle

**Fonctionnement:** Change le mode du `viewManager` qui calcule les colonnes différemment

---

### 2. 🆓 Afficher créneaux libres
**Type:** Case à cocher  
**Par défaut:** Activé  

**Ce que ça fait:**
- Affiche les créneaux horaires disponibles dans chaque gymnase
- Aide à identifier où on peut ajouter de nouveaux matchs

**Fonctionnement:** Le `availableSlotsManager` calcule les créneaux libres et les affiche dans la grille

---

## ✅ Pourquoi Ces Options ?

### Vue Poules
1. **Format** - Change réellement la présentation visuelle (3 rendus différents)
2. **Liste équipes** - Information pertinente souvent nécessaire
3. **Préférences** - Données utiles pour la planification
4. **Séparateurs niveau** - Améliore significativement la lisibilité
5. **Tout développer** - Gain de temps pour voir tous les détails

### Vue Agenda
1. **Organiser par** - Deux façons fondamentalement différentes de voir le planning
2. **Créneaux libres** - Essentiel pour la planification de nouveaux matchs

---

## 🚫 Options Retirées (et Pourquoi)

### Supprimées car non fonctionnelles sans implémentation supplémentaire:

1. **Coloration des matchs** - Nécessiterait d'ajouter des attributs `data-*` et du CSS dynamique
2. **Taille des cartes** - Nécessiterait un système de classes CSS variables
3. **Densité d'information** - Nécessiterait plusieurs niveaux de rendu conditionnel
4. **Grouper par jour** - Nécessiterait une refonte du rendu des matchs
5. **Animations** - Déjà gérées globalement, pas spécifique à la vue
6. **Conflits** - Nécessiterait un système de détection de conflits
7. **Format d'heure** - Nécessiterait un formateur d'heure
8. **Grid density** - Nécessiterait de modifier le SlotManager
9. **Afficher gymnases/horaires/poules** - Trop granulaire, surcharge l'interface

---

## 💡 Comment Ça Marche

### Mécanisme de Sauvegarde
```javascript
// Les options sont stockées dans this.displayOptions
this.displayOptions = {
    format: 'cards',
    showTeams: false,
    showPreferences: false,
    showLevelSeparators: true,
    autoExpand: false
};
```

### Mécanisme de Changement
```javascript
// Chaque option a une action qui modifie displayOptions et re-render
action: (checked) => {
    this.displayOptions.showTeams = checked;
    this.render(); // Redessine toute la vue
}
```

### Mécanisme de Rendu Conditionnel
```javascript
// Dans le code de génération HTML
if (this.displayOptions.showTeams) {
    html += this._generateTeamsList(pool, data);
}
```

---

## 🎨 Impact Visuel de Chaque Option

### Format: Cartes
```
┌─────────────────────────────┐
│ Poule A - Féminin          │
│ Excellence - 6 équipes      │
│ [Développer ▶]             │
└─────────────────────────────┘
```

### Format: Compact
```
Poule A - Excellence | 👥 6 | ⚽ 15 | [▶]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Format: Liste
```
┌──────────┬──────────┬────────┬─────────┐
│ Nom      │ Niveau   │ Équipes│ Matchs  │
├──────────┼──────────┼────────┼─────────┤
│ Poule A  │ Excel.   │ 6      │ 15      │
└──────────┴──────────┴────────┴─────────┘
```

### Avec Liste Équipes
```
┌─────────────────────────────┐
│ 👥 Équipes (6)             │
│ • INSA Lyon                │
│ • Université Paris         │
│ • ...                      │
└─────────────────────────────┘
```

### Avec Préférences
```
🏐 INSA Lyon
  🕐 Horaires: 14h-18h
  📍 Lieux: Gymnase A, B
  ❌ Indisponible: Semaines 3, 7
```

---

## 🧪 Tests Effectués

✅ Changement de format (Cartes → Compact → Liste) - **Fonctionne**  
✅ Toggle liste équipes - **Fonctionne**  
✅ Toggle préférences (avec équipes activé) - **Fonctionne**  
✅ Toggle séparateurs niveau - **Fonctionne**  
✅ Tout développer/réduire - **Fonctionne**  
✅ Agenda: Gymnase ↔ Semaine - **Fonctionne**  
✅ Agenda: Créneaux libres - **Fonctionne**  

---

## 🚀 Utilisation

1. **Ouvrir** `new_calendar.html`
2. **Sélectionner** une vue (Poules ou Agenda)
3. **Les options** apparaissent automatiquement dans le panneau gauche
4. **Cliquer** pour activer/désactiver
5. **Changements** appliqués instantanément

---

## 📝 Note Importante

Ces options ont été **réduites mais testées** pour garantir qu'elles fonctionnent vraiment. Chaque option :
- ✅ Modifie réellement l'affichage
- ✅ A un code d'implémentation complet
- ✅ Est utile pour les utilisateurs
- ✅ Ne crée pas d'erreurs console
- ✅ Est intuitive et claire

**Moins d'options, mais toutes fonctionnelles = Meilleure expérience utilisateur** 🎯
