"""
PyCalendar - Sports Scheduling System
Main entry point
"""

import sys
from pathlib import Path
from core.config import Config
from orchestrator.pipeline import SchedulingPipeline


def main():
    """Main entry point."""
    
    config_file = "configs/default.yaml"
    
    if len(sys.argv) > 1:
        config_file = sys.argv[1]
    
    if not Path(config_file).exists():
        print(f"❌ Fichier de configuration introuvable: {config_file}")
        print(f"Utilisation: python main.py [config.yaml]")
        return 1
    
    try:
        config = Config.from_yaml(config_file)
        pipeline = SchedulingPipeline(config)
        solution = pipeline.run()
        
        if solution and solution.est_complete():
            print("\n✅ Planification complète réussie!")
            return 0
        elif solution:
            print(f"\n⚠️  Planification partielle: {solution.taux_planification():.1f}%")
            return 0
        else:
            print("\n❌ La planification a échoué")
            return 1
            
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
