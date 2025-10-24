#!/usr/bin/env python3
"""
Script pour ajouter du code de débogage JavaScript dans le HTML
afin de voir exactement ce qui se passe avec le positionnement des matchs.
"""

import json
from pathlib import Path

def inject_debug_code():
    """Injecte du code de débogage dans le HTML."""
    
    html_path = Path("data_volley/calendrier_volley.html")
    
    # Lire le HTML
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Code de débogage à injecter
    debug_code = """
        // ==================== CODE DE DÉBOGAGE ====================
        console.log('%c🔍 DÉBOGAGE DU POSITIONNEMENT DES MATCHS', 'font-size: 16px; font-weight: bold; color: #3498db');
        
        // Attendre que tout soit chargé
        setTimeout(() => {
            console.log('%c📊 INFORMATIONS GÉNÉRALES', 'font-size: 14px; font-weight: bold; color: #27ae60');
            
            // 1. Vérifier les données brutes
            console.log('Nombre de matchs:', rawMatchsData ? rawMatchsData.length : 0);
            if (rawMatchsData && rawMatchsData.length > 0) {
                console.log('Premier match:', rawMatchsData[0]);
                console.log('Dernier match:', rawMatchsData[rawMatchsData.length - 1]);
            }
            
            // 2. Vérifier la grille
            const grid = document.querySelector('.calendar-grid-view');
            if (grid && grid.__calendarGridView) {
                const view = grid.__calendarGridView;
                console.log('\\n%c⏰ PLAGE HORAIRE DE LA GRILLE', 'font-size: 14px; font-weight: bold; color: #e74c3c');
                console.log('startHour:', view.startHour, '(' + view.startHour + ':00)');
                console.log('endHour:', view.endHour, '(' + view.endHour + ':00)');
                console.log('gridStartMinutes:', view.startHour * 60);
                console.log('gridEndMinutes:', view.endHour * 60);
                console.log('matchDuration:', view.matchDuration, 'minutes');
                console.log('timeSlotMinutes:', view.timeSlotMinutes, 'minutes');
                
                // 3. Vérifier le calcul de hauteur
                const slotHeight = view.getSlotHeight();
                console.log('\\n%c📏 DIMENSIONS', 'font-size: 14px; font-weight: bold; color: #9b59b6');
                console.log('slotHeight:', slotHeight, 'px (pour', view.timeSlotMinutes, 'min)');
                console.log('pixelsPerMinute:', slotHeight / view.timeSlotMinutes);
                console.log('windowHeight:', window.innerHeight, 'px');
                
                // 4. Analyser les matchs affichés
                const matchBlocks = document.querySelectorAll('.match-block');
                console.log('\\n%c🎯 MATCHS AFFICHÉS', 'font-size: 14px; font-weight: bold; color: #f39c12');
                console.log('Nombre de blocs DOM:', matchBlocks.length);
                
                if (matchBlocks.length > 0) {
                    const firstBlock = matchBlocks[0];
                    const topValue = firstBlock.style.top;
                    const heightValue = firstBlock.style.height;
                    console.log('Premier bloc:');
                    console.log('  - top:', topValue);
                    console.log('  - height:', heightValue);
                    console.log('  - data-match:', firstBlock.getAttribute('data-match'));
                    
                    // Calculer la position théorique
                    const matchData = JSON.parse(firstBlock.getAttribute('data-match') || '{}');
                    if (matchData.horaire) {
                        const [h, m] = matchData.horaire.split(':').map(Number);
                        const matchMinutes = h * 60 + m;
                        const gridStartMinutes = view.startHour * 60;
                        const offsetMinutes = matchMinutes - gridStartMinutes;
                        const pixelsPerMinute = slotHeight / view.timeSlotMinutes;
                        const theoreticalTop = offsetMinutes * pixelsPerMinute;
                        const theoreticalHeight = view.matchDuration * pixelsPerMinute;
                        
                        console.log('  - horaire:', matchData.horaire);
                        console.log('  - matchMinutes:', matchMinutes);
                        console.log('  - offsetMinutes:', offsetMinutes);
                        console.log('  - THÉORIQUE top:', theoreticalTop, 'px');
                        console.log('  - THÉORIQUE height:', theoreticalHeight, 'px');
                        console.log('  - RÉEL top:', topValue);
                        console.log('  - RÉEL height:', heightValue);
                        
                        if (parseFloat(topValue) !== theoreticalTop) {
                            console.error('⚠️ PROBLÈME: Le top réel ne correspond pas au top théorique!');
                        }
                    }
                }
                
                // 5. Analyser les horaires de tous les matchs
                console.log('\\n%c🕐 ANALYSE DES HORAIRES', 'font-size: 14px; font-weight: bold; color: #16a085');
                const allHoraires = rawMatchsData.map(m => m.horaire).filter(h => h);
                const uniqueHoraires = [...new Set(allHoraires)].sort();
                console.log('Horaires uniques:', uniqueHoraires);
                
                const times = uniqueHoraires.map(h => {
                    const [hours, minutes] = h.split(':').map(Number);
                    const totalMinutes = hours * 60 + minutes;
                    return { horaire: h, minutes: totalMinutes };
                });
                console.log('En minutes:', times);
                
                const minTime = Math.min(...times.map(t => t.minutes));
                const maxTime = Math.max(...times.map(t => t.minutes));
                console.log('Plage:', Math.floor(minTime/60) + ':' + (minTime%60).toString().padStart(2,'0'), 
                           '→', Math.floor(maxTime/60) + ':' + (maxTime%60).toString().padStart(2,'0'));
                
            } else {
                console.error('❌ Impossible de trouver l\'instance CalendarGridView!');
            }
            
            console.log('\\n%c✅ FIN DU DÉBOGAGE', 'font-size: 16px; font-weight: bold; color: #3498db');
            console.log('Ouvrez cet onglet dans les outils de développement pour voir les détails');
            
        }, 1000);
"""
    
    # Trouver où injecter (juste avant </body>)
    injection_point = html_content.rfind('</body>')
    if injection_point == -1:
        print("❌ Impossible de trouver </body> dans le HTML")
        return False
    
    # Injecter
    new_html = (
        html_content[:injection_point] +
        '    <script>\n' +
        debug_code +
        '    </script>\n' +
        html_content[injection_point:]
    )
    
    # Sauvegarder
    output_path = Path("data_volley/calendrier_volley_DEBUG.html")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(new_html)
    
    file_size = output_path.stat().st_size
    print("=" * 70)
    print("HTML DE DÉBOGAGE GÉNÉRÉ")
    print("=" * 70)
    print(f"\n📄 Fichier: {output_path}")
    print(f"📊 Taille: {file_size:,} octets ({file_size/1024:.1f} KB)")
    print("\n🔍 INSTRUCTIONS:")
    print("   1. Ouvrez le fichier dans votre navigateur")
    print("   2. Ouvrez la console développeur (F12)")
    print("   3. Regardez les informations de débogage affichées")
    print("   4. Vérifiez si:")
    print("      - startHour et endHour sont corrects")
    print("      - Le top THÉORIQUE correspond au top RÉEL")
    print("      - Les horaires des matchs sont bien parsés")
    print("\n💡 Rapportez-moi les valeurs affichées dans la console!")
    print("=" * 70)
    
    return True

if __name__ == "__main__":
    inject_debug_code()
