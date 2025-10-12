#!/usr/bin/env bash
# Script de lancement du simulateur de pénalités

echo "🎲 Lancement du Simulateur de Pénalités Horaires..."
echo ""

# Vérifier si on est dans le bon répertoire
if [ ! -f "app_penalty_simulator.py" ]; then
    echo "❌ Erreur : Fichier app_penalty_simulator.py non trouvé"
    echo "   Assurez-vous d'être dans le répertoire PyCalendar"
    exit 1
fi

# Vérifier si streamlit est installé
if ! command -v streamlit &> /dev/null; then
    echo "⚠️  Streamlit n'est pas installé"
    echo "   Installation en cours..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ Erreur lors de l'installation des dépendances"
        exit 1
    fi
    echo "✅ Dépendances installées"
    echo ""
fi

echo "🎲 Ouverture du simulateur dans votre navigateur..."
echo "   URL : http://localhost:8501"
echo ""
echo "💡 Pour arrêter l'application : Ctrl+C"
echo ""

# Lancer streamlit
streamlit run app_penalty_simulator.py
