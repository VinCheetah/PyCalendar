# 🎨 PyCalendar Display Options - Quick Reference

## 🎯 Pools View (16 Options)

| Option | Type | Values | Default |
|--------|------|--------|---------|
| **Format** | Buttons | Cartes / Compact / Liste | Cartes |
| **Coloration** | Select | 7 schemes | Par statut |
| **Taille** | Select | xs / sm / md / lg / xl | md |
| **Densité info** | Select | Minimale / Normale / Détaillée / Verbose | Normale |
| **Liste équipes** | Checkbox | On/Off | Off |
| **Préférences** | Checkbox | On/Off | Off |
| **Séparateurs niveau** | Checkbox | On/Off | On |
| **Statistiques** | Checkbox | On/Off | On |
| **Horaires détaillés** | Checkbox | On/Off | On |
| **Gymnases** | Checkbox | On/Off | On |
| **Grouper par jour** | Checkbox | On/Off | Off |
| **Animations** | Checkbox | On/Off | On |
| **Conflits** | Checkbox | On/Off | Off |
| **Auto-expand** | Checkbox | On/Off | Off |

## 📅 Agenda View (17 Options)

| Option | Type | Values | Default |
|--------|------|--------|---------|
| **Afficher par** | Buttons | Gymnase / Semaine | Gymnase |
| **Coloration** | Select | 7 schemes | Par gymnase |
| **Taille** | Select | xs / sm / md / lg / xl | md |
| **Densité grille** | Select | 15min / 30min / 1h | 30min |
| **Format heure** | Buttons | 24h / 12h | 24h |
| **Créneaux libres** | Checkbox | On/Off | On |
| **Gymnases** | Checkbox | On/Off | On |
| **Horaires** | Checkbox | On/Off | On |
| **Poules** | Checkbox | On/Off | On |
| **Équipes** | Checkbox | On/Off | On |
| **Week-ends** | Checkbox | On/Off | On |
| **Conflits** | Checkbox | On/Off | Off |
| **Mode compact** | Checkbox | On/Off | Off |
| **Animations** | Checkbox | On/Off | On |
| **Lignes grille** | Checkbox | On/Off | On |

## 🎨 Color Schemes (7 Available)

1. **Aucune** - No special coloring
2. **Par statut** - 🟢 Scheduled / 🟠 Unscheduled / 🔴 Conflict
3. **Par gymnase** - Unique color per venue
4. **Par semaine** - Gradient across weeks
5. **Par jour** - Different color per day
6. **Par genre** - 🩷 Female / 💙 Male
7. **Par conflits** - 🔴 Highlights conflicts

## 📏 Card Sizes (5 Available)

| Size | Height | Font | Use Case |
|------|--------|------|----------|
| **xs** | 40px | 0.7rem | Maximum density |
| **sm** | 50px | 0.8rem | Compact view |
| **md** | 70px | 0.9rem | **Default** - Balanced |
| **lg** | 90px | 1.0rem | Comfortable reading |
| **xl** | 110px | 1.1rem | Maximum detail |

## 💡 Quick Presets

### 🔍 **Analysis Mode**
- Format: Cartes
- Taille: lg
- Densité: Très détaillée
- Conflits: ✓
- Statistiques: ✓

### 📊 **Overview Mode**
- Format: Compact
- Taille: sm
- Densité: Minimale
- Animations: ✗
- Mode compact: ✓

### 🎯 **Planning Mode**
- Afficher par: Gymnase
- Créneaux libres: ✓
- Densité grille: Compacte (15min)
- Coloration: Par statut
- Conflits: ✓

### 🎬 **Presentation Mode**
- Taille: lg
- Coloration: Par genre
- Animations: ✓
- Statistiques: ✓
- Grille: ✓

## 🔧 Tips & Tricks

### Performance
- Disable animations on slower machines
- Use compact mode for large datasets
- Choose 1h grid density for overview

### Visibility
- Use "by-conflict" coloring to spot issues
- Enable grid lines for better alignment
- Highlight weekends for better context

### Workflow
- Auto-expand pools when reviewing all
- Group by day to see distribution
- Show available slots when planning

### Presentation
- Use large cards for demos
- Enable all statistics for completeness
- Choose gender coloring for clarity

## 📱 Persistence

✅ All settings auto-saved to browser  
✅ Restored on next visit  
✅ Per-view (Pools vs Agenda)  
✅ No manual save needed  

## 🚀 Access Options

Options appear in **left sidebar** when:
- ✓ Pools view is active → Pools options
- ✓ Agenda view is active → Agenda options
- ✓ Automatically switches with view

## 📖 Full Documentation

See **`DISPLAY_OPTIONS_GUIDE.md`** for:
- Detailed descriptions
- Usage scenarios
- Troubleshooting
- Advanced tips
