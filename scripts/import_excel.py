#!/usr/bin/env python3
"""
Script d'import d'un projet depuis config YAML + Excel.

Charge les données depuis les fichiers de configuration et les importe dans la DB.
Utilise le service de synchronisation (SyncService) créé en Tâche 1.6.
"""

import sys
from pathlib import Path
import argparse

# Ajouter répertoire racine au sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.database.engine import SessionLocal, DATABASE_PATH
from backend.services.sync_service import SyncService


def main():
    # Parser arguments
    parser = argparse.ArgumentParser(
        description="Importer un projet depuis config YAML + Excel",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  # Import avec nom auto-généré
  python scripts/import_excel.py configs/config_volley.yaml
  
  # Import avec nom personnalisé
  python scripts/import_excel.py configs/config_volley.yaml "Championnat Volley 2025"
  
  # Import sans validation Excel (déconseillé)
  python scripts/import_excel.py configs/config_volley.yaml --no-validate
        """
    )
    
    parser.add_argument(
        "config_path",
        help="Chemin vers le fichier YAML de configuration"
    )
    parser.add_argument(
        "project_name",
        nargs="?",
        default=None,
        help="Nom du projet (optionnel, généré automatiquement si absent)"
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Désactiver la validation Excel (actualiser_config.py)"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Afficher plus de détails"
    )
    
    args = parser.parse_args()
    
    # Vérifier que DB existe
    if not DATABASE_PATH.exists():
        print("❌ Base de données non trouvée!")
        print(f"   Exécutez d'abord : python scripts/init_db.py")
        sys.exit(1)
    
    # Vérifier que fichier YAML existe
    yaml_path = Path(args.config_path)
    if not yaml_path.exists():
        print(f"❌ Fichier YAML non trouvé : {yaml_path}")
        sys.exit(1)
    
    # Afficher header
    print("=" * 70)
    print("Import d'un projet dans PyCalendar")
    print("=" * 70)
    print(f"\n📄 Configuration YAML : {yaml_path}")
    
    # Import
    db = SessionLocal()
    service = SyncService(db)
    
    try:
        # Importer via service (Tâche 1.6)
        validate_excel = not args.no_validate
        
        if args.verbose:
            print(f"🔍 Validation Excel : {'Activée' if validate_excel else 'Désactivée'}")
        
        print(f"\n🚀 Démarrage de l'import...\n")
        
        project = service.import_from_excel(
            yaml_path=str(yaml_path),
            project_name=args.project_name,
            validate_excel=validate_excel
        )
        
        # Afficher statistiques
        print(f"\n{'=' * 70}")
        print(f"✅ Import terminé avec succès!")
        print(f"{'=' * 70}")
        print(f"\n📊 Statistiques du projet :")
        print(f"   ID         : {project.id}")
        print(f"   Nom        : {project.nom}")
        print(f"   Sport      : {project.sport}")
        print(f"   Semaines   : {project.nb_semaines}")
        print(f"   Semaine min: {project.semaine_min}")
        print(f"\n📈 Données importées :")
        print(f"   Équipes    : {len(project.teams)}")
        print(f"   Gymnases   : {len(project.venues)}")
        print(f"   Matchs     : {len(project.matches)}")
        
        # Détails matchs
        nb_planifies = sum(1 for m in project.matches if m.semaine is not None)
        nb_fixes = sum(1 for m in project.matches if m.est_fixe)
        print(f"\n🎯 État des matchs :")
        print(f"   Planifiés  : {nb_planifies}")
        print(f"   Fixés      : {nb_fixes}")
        print(f"   À planifier: {len(project.matches) - nb_planifies}")
        
        # Fichiers config
        if project.config_data:
            print(f"\n📁 Fichiers de configuration :")
            print(f"   YAML  : {project.config_yaml_path}")
            if 'excel_path' in project.config_data:
                print(f"   Excel : {project.config_data['excel_path']}")
        
        print(f"\n💡 Prochaines étapes :")
        print(f"   1. Démarrer l'API : python run_api.py")
        print(f"   2. Ou : uvicorn backend.api.main:app --reload")
        print(f"   3. Accéder à la documentation : http://localhost:8000/docs")
        
    except FileNotFoundError as e:
        print(f"\n❌ Fichier non trouvé : {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"\n❌ Erreur de validation : {e}")
        print(f"\n💡 Suggestions :")
        print(f"   1. Exécutez : python actualiser_config.py <fichier_excel>")
        print(f"   2. Corrigez les erreurs détectées")
        print(f"   3. Relancez cet import")
        print(f"   OU")
        print(f"   4. Ajoutez --no-validate pour ignorer la validation (déconseillé)")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur lors de l'import : {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
