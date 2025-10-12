"""Open the calendar visualization in the default browser."""

import webbrowser
import sys
from pathlib import Path


def open_visualization(html_file: str = "exemple/calendrier.html"):
    """Open the HTML visualization in the default browser."""
    
    html_path = Path(html_file)
    
    if not html_path.exists():
        print(f"❌ Fichier introuvable: {html_file}")
        print("Assurez-vous d'avoir exécuté 'python3 main.py' d'abord")
        return False
    
    absolute_path = html_path.absolute()
    url = f"file://{absolute_path}"
    
    print(f"🌐 Ouverture du calendrier dans le navigateur...")
    print(f"   {url}")
    
    webbrowser.open(url)
    print("✅ Calendrier ouvert !")
    
    return True


if __name__ == "__main__":
    html_file = sys.argv[1] if len(sys.argv) > 1 else "exemple/calendrier.html"
    open_visualization(html_file)
