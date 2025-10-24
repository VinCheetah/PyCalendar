# Importateur de Matchs Externes

## Description

Script pour importer des matchs depuis un fichier Excel externe (par exemple depuis LAURASU) dans la feuille `Matchs_Fixes` d'une configuration PyCalendar.

## Utilisation

### Commande de base

```bash
python importer_matchs_externes.py --config <config.yaml> --fichier-local <fichier.xlsx> --sport <SPORT> [OPTIONS]
```

### Paramètres requis

- `--config` : Fichier de configuration YAML (ex: `configs/config_volley.yaml`)
- `--fichier-local` ou `--url` : Source du fichier Excel
- `--sport` : Code du sport (VB pour volleyball, HB pour handball, BB pour basketball, etc.)

### Options de filtrage

- `--journee N` : Filtrer sur une journée spécifique
- `--date-limite DD/MM/YYYY` : Importer seulement les matchs avant cette date
- `--avec-score` : Importer uniquement les matchs avec score
- `--sans-score` : Importer uniquement les matchs sans score  
- `--tous` : Importer tous les matchs (défaut)

### Options d'exécution

- `--dry-run` : Mode simulation (affiche ce qui serait fait sans modifier)
- `--explorer` : Mode exploration (affiche la structure du fichier sans importer)

## Exemples

### Import depuis fichier local avec simulation

```bash
python importer_matchs_externes.py \
    --config configs/config_volley.yaml \
    --fichier-local ~/Downloads/J1.xlsx \
    --sport VB \
    --dry-run \
    --tous
```

### Import réel des matchs avec score

```bash
python importer_matchs_externes.py \
    --config configs/config_volley.yaml \
    --fichier-local ~/Downloads/J1.xlsx \
    --sport VB \
    --avec-score
```

### Import depuis URL SharePoint

```bash
python importer_matchs_externes.py \
    --config configs/config_volley.yaml \
    --url "https://ffsu.sharepoint.com/.../J1.xlsx" \
    --sport VB \
    --tous
```

### Explorer la structure du fichier

```bash
python importer_matchs_externes.py \
    --config configs/config_volley.yaml \
    --fichier-local ~/Downloads/J1.xlsx \
    --explorer
```

## Format du fichier source

Le script s'adapte automatiquement aux fichiers LAURASU avec :

- **Détection automatique** de la ligne d'en-têtes (cherche "Date" + "Sport")
- **Colonnes attendues** :
  - `Date` : Date du match (format date Excel)
  - `Sport` : Code du sport (VB, HB, BB, etc.)
  - `Equipe 1` et `Equipe 2` : Noms des équipes
  - `Hre Déb` : Horaire de début (format time)
  - `Lieu` : Gymnase
  - `Poule` : Code de la poule
  - `Résultats` : Score (format "X / Y")
  - `Commentaire` : Remarques éventuelles

## Format de sortie

Les matchs sont importés dans la feuille `Matchs_Fixes` avec :

- **Colonnes** : `Equipe_1`, `Equipe_2`, `Poule`, `Semaine`, `Horaire`, `Gymnase`, `Score`, `Type_Competition`, `Remarques`
- **Semaine** : Calculée automatiquement depuis la date (semaine 1 = premier lundi d'octobre 2025)
- **Type_Competition** : "Acad" par défaut
- **Remarques** : Préserve les commentaires + ajoute "Importé J1"

## Gestion des doublons

Le script détecte automatiquement les doublons basés sur :
- Équipes (même paire, peu importe l'ordre)
- Poule
- Semaine
- Horaire

Les doublons ne sont pas réimportés.

## Notes importantes

1. **Date de début de saison** : Semaine 1 commence le 16 octobre 2025 (configurable dans `convertir_vers_format_config()`)
2. **Normalisation des noms** : Les espaces superflus sont supprimés automatiquement
3. **Format horaire** : Converti de "HH:MM:SS" vers "HH:MM"
4. **Scores vides** : Les matchs sans score ont une cellule vide (pas "0 / 0")

## Troubleshooting

### Erreur "Aucun fichier Excel trouvé"
→ Vérifier que le YAML contient `fichiers.donnees` ou `fichier_excel`

### Erreur "Impossible de trouver les en-têtes"
→ Le fichier doit avoir une ligne avec "Date" et "Sport" côte à côte

### Aucun match importé
→ Vérifier le code sport (doit correspondre exactement, ex: VB pas Volley)
→ Vérifier les filtres (--avec-score peut exclure tous les matchs)

### Scores mal formatés
→ Le format attendu est "X / Y" avec espaces (ex: "3 / 0")
