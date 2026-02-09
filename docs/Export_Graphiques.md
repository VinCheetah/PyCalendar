# 📊 Système d'Export des Graphiques - Guide Utilisateur

## 🎯 Aperçu

Ce notebook inclut un système automatique d'export qui sauvegarde **chaque graphique individuellement** au format PNG haute résolution, puis génère un **rapport PDF complet** regroupant tous les graphiques.

## 📁 Configuration de l'Export

Au début du notebook (cellule d'imports), vous trouverez la configuration `EXPORT_CONFIG` :

```python
EXPORT_CONFIG = {
    # Dossier principal d'export (modifiez ce nom selon vos besoins)
    'export_folder': 'exports',
    
    # Sous-dossier pour les figures individuelles
    'figures_subfolder': 'figures',
    
    # Préfixe pour les fichiers de rapport PDF
    'pdf_prefix': 'rapport_analyse_matchs',
    
    # Résolution des images (DPI)
    'dpi': 300,
    
    # Inclure un timestamp dans les noms de fichiers PDF
    'include_timestamp': True,
    
    # Format de numérotation des figures (ex: "01", "001", etc.)
    'number_format': '{:02d}',
}
```

### 🔧 Personnalisation

Pour changer le dossier d'export, modifiez simplement :
```python
EXPORT_CONFIG['export_folder'] = 'mes_resultats'
```

## 🎨 Comment ça fonctionne

### Sauvegarde Automatique - Export Individuel

Chaque graphique utilise `smart_show_individual("Nom_du_graphique")` au lieu de `plt.show()`.

Cette fonction :
1. **Extrait chaque sous-graphique** de la figure (subplots)
2. **Sauvegarde individuellement** chaque sous-graphique en PNG (300 DPI)
3. **Stocke les métadonnées** dans `EXPORTED_FIGURES` pour le PDF
4. **Affiche** la figure complète normalement

Exemple : une figure avec 4 subplots génère 4 fichiers PNG :
- `01_Forfaits_1.png` (subplot haut-gauche)
- `01_Forfaits_2.png` (subplot haut-droit)
- `01_Forfaits_3.png` (subplot bas-gauche)
- `01_Forfaits_4.png` (subplot bas-droit)

### Liste des Graphiques Exportés

Le notebook génère **11 sections de graphiques** (avec sous-graphiques individuels) :

| # | Section | Sous-graphiques |
|---|---------|-----------------|
| 01 | Matchs_par_semaine | 2 (distribution joués/non-joués) |
| 02 | Matchs_annules | 1 (analyse annulations) |
| 03 | Horaires_par_equipe | 2 (boxplot horaires) |
| 04 | Equipes_academiques | 4 (stats académiques) |
| 05 | Forfaits | 4 (par semaine/gymnase/horaire/poule) |
| 06 | Ententes | 4 (analyse ententes) |
| 07 | Matchs_aller_retour | 4 (paires et écarts) |
| 08 | Scores | 4 (distribution scores) |
| 09 | Poules | 4 (complétion poules) |
| 10 | Types_competition | 4 (CFE/CFU/etc.) |
| 11 | Tableau_de_bord | 1 (KPIs synthèse) |

**Total : ~34 fichiers PNG individuels**

## 📦 Structure des Fichiers Générés

```
exports/
├── figures/
│   ├── 01_Matchs_par_semaine_1.png      (subplot 1)
│   ├── 01_Matchs_par_semaine_2.png      (subplot 2)
│   ├── 02_Matchs_annules_1.png
│   ├── 03_Horaires_par_equipe_1.png
│   ├── 03_Horaires_par_equipe_2.png
│   ├── 04_Equipes_academiques_1.png
│   ├── 04_Equipes_academiques_2.png
│   ├── 04_Equipes_academiques_3.png
│   ├── 04_Equipes_academiques_4.png
│   ├── 05_Forfaits_1.png                (par semaine)
│   ├── 05_Forfaits_2.png                (par gymnase)
│   ├── 05_Forfaits_3.png                (par horaire)
│   ├── 05_Forfaits_4.png                (par poule)
│   ├── ... (autres sous-graphiques)
│   └── 11_Tableau_de_bord_1.png
└── rapport_analyse_matchs_2025-01-15_143000.pdf
```

## 🚀 Utilisation

### Exécution Standard

1. **Exécuter toutes les cellules** du notebook
2. Les graphiques sont automatiquement sauvegardés au fur et à mesure
3. Les 2 dernières cellules génèrent le résumé et le PDF

### Réinitialisation

Pour recommencer l'export (si vous réexécutez le notebook) :
```python
reset_export_counter()
```

### Vérification

Pour voir les figures déjà exportées :
```python
print(f"Figures exportées: {len(EXPORTED_FIGURES)}")
for name, info in EXPORTED_FIGURES.items():
    print(f"  - {name}: {info['path']}")
```

## ⚙️ Fonctions Disponibles

| Fonction | Description |
|----------|-------------|
| `smart_show(nom)` | Sauvegarde et affiche le graphique |
| `get_export_paths()` | Retourne les chemins d'export configurés |
| `reset_export_counter()` | Réinitialise le compteur pour recommencer |
| `get_all_exported_figures()` | Retourne le dictionnaire des figures |

## 📋 Notes Techniques

- **Format**: PNG avec fond blanc
- **Résolution**: 300 DPI (configurable)
- **PDF**: Pages A4 paysage avec page de titre
- **Métadonnées PDF**: Titre, auteur, date de création inclus
