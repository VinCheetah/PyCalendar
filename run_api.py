#!/usr/bin/env python3
"""
Script de lancement de l'API PyCalendar V2.

Usage:
    python run_api.py              # Mode dev (hot-reload) sur port 8000
    python run_api.py --port 8080  # Mode dev sur port 8080
    python run_api.py --prod       # Mode production
"""

import sys
import os
from pathlib import Path

# Ajouter le répertoire racine au PYTHONPATH
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    import uvicorn
    
    # Parser arguments simples
    port = 8000
    reload = True
    
    for i, arg in enumerate(sys.argv[1:]):
        if arg == "--port" and i + 1 < len(sys.argv) - 1:
            port = int(sys.argv[i + 2])
        elif arg == "--prod":
            reload = False
    
    # Configuration
    config = {
        "app": "backend.api.main:app",
        "host": "127.0.0.1" if reload else "0.0.0.0",
        "port": port,
        "reload": reload,
        "log_level": "info"
    }
    
    print("=" * 60)
    print(f"🚀 Démarrage API PyCalendar V2")
    print("=" * 60)
    print(f"Mode: {'Développement (hot-reload)' if reload else 'Production'}")
    print(f"URL: http://{config['host']}:{port}")
    print(f"Docs: http://{config['host']}:{port}/docs")
    print("=" * 60)
    print()
    
    # Lancer uvicorn
    uvicorn.run(**config)
