"""
PyCalendar - Sports Scheduling System
Main entry point

Usage:
    python main.py [config.yaml]
    
Examples:
    python main.py                              # Utilise configs/default.yaml
    python main.py configs/config_volley.yaml   # Configuration volleyball
    python main.py configs/config_hand.yaml     # Configuration handball

Le système génère automatiquement :
    - Solution JSON dans solutions/
    - Fichier Excel dans data_*/
    - Interface HTML interactive
    - Validation automatique
"""

import sys
from pathlib import Path

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from pycalendar.core.config import Config
from pycalendar.orchestrator.pipeline import SchedulingPipeline


def print_usage():
    """Affiche les instructions d'utilisation."""
    print("\n📖 Usage:")
    print("  python main.py [config.yaml]")
    print("\n📝 Exemples:")
    print("  python main.py                              # Config par défaut")
    print("  python main.py configs/config_volley.yaml   # Volleyball")
    print("  python main.py configs/config_hand.yaml     # Handball")
    print("\n📁 Configurations disponibles:")
    configs_dir = Path("configs")
    if configs_dir.exists():
        for config_file in sorted(configs_dir.glob("*.yaml")):
            print(f"  • {config_file}")


def main():
    """Point d'entrée principal."""
    
    # Déterminer le fichier de configuration
    config_file = "configs/default.yaml"
    
    if len(sys.argv) > 1:
        config_file = sys.argv[1]
    
    # Vérifier l'existence du fichier
    if not Path(config_file).exists():
        print(f"\n❌ Fichier de configuration introuvable: {config_file}")
        print_usage()
        return 1
    
    # Note: La bannière est maintenant affichée par le pipeline
    print(f"\n📄 Configuration: {config_file}")
    
    try:
        # Charger la configuration
        config = Config.from_yaml(config_file)
        
        # Créer et exécuter le pipeline
        pipeline = SchedulingPipeline(config)
        solution = pipeline.run()
        
        # Afficher le résultat
        print("\n" + "="*70)
        if solution and solution.est_complete():
            print("✅ PLANIFICATION COMPLÈTE RÉUSSIE!")
            print(f"   • {len(solution.matchs_planifies)} matchs planifiés")
            print(f"   • Taux de planification: {solution.taux_planification():.1f}%")
            print("\n📂 Fichiers générés:")
            print(f"   • Solution JSON: solutions/latest_{config.cpsat_warm_start_file}.json")
            print(f"   • Fichier Excel: {config.fichier_sortie}")
            print(f"   • Interface HTML: {config.fichier_sortie.replace('.xlsx', '.html')}")
            print("\n💡 Pour régénérer uniquement l'interface:")
            print(f"   python regenerate_interface.py")
            print("="*70 + "\n")
            return 0
            
        elif solution:
            print("⚠️  PLANIFICATION PARTIELLE")
            print(f"   • {len(solution.matchs_planifies)} matchs planifiés")
            print(f"   • {len(solution.matchs_non_planifies)} matchs non planifiés")
            print(f"   • Taux de planification: {solution.taux_planification():.1f}%")
            print("\n💡 Conseils:")
            print("   • Augmentez le temps de résolution CP-SAT")
            print("   • Ajustez les contraintes dans le fichier de configuration")
            print("   • Vérifiez les créneaux disponibles")
            print("="*70 + "\n")
            return 0
            
        else:
            print("❌ LA PLANIFICATION A ÉCHOUÉ")
            print("\n💡 Vérifications suggérées:")
            print("   • Fichier de données Excel correct?")
            print("   • Nombre de créneaux suffisant?")
            print("   • Contraintes trop restrictives?")
            print("="*70 + "\n")
            return 1
            
    except FileNotFoundError as e:
        print(f"\n❌ Fichier manquant: {e}")
        print("💡 Vérifiez que le fichier de données Excel existe")
        return 1
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        print("\n💡 Utilisez --verbose pour plus de détails")
        return 1


if __name__ == "__main__":
    sys.exit(main())
