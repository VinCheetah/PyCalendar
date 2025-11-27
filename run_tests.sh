#!/bin/bash
# Script de lancement rapide des tests PyCalendar

set -e  # Arrêt si erreur

echo "========================================="
echo "🧪 PyCalendar - Tests CP-SAT"
echo "========================================="
echo ""

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Fonction d'aide
show_help() {
    echo "Usage: ./run_tests.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  all             Lance tous les tests (défaut)"
    echo "  basic           Tests de base (contraintes)"
    echo "  penalties       Tests de pénalités"
    echo "  examples        Exemples guidés"
    echo "  quick           Tests rapides uniquement"
    echo "  coverage        Tests avec rapport de coverage"
    echo "  failed          Relance uniquement les tests échoués"
    echo "  debug [test]    Debug un test spécifique avec output"
    echo "  -h, --help      Affiche cette aide"
    echo ""
    echo "Exemples:"
    echo "  ./run_tests.sh                    # Tous les tests"
    echo "  ./run_tests.sh basic              # Tests de base"
    echo "  ./run_tests.sh coverage           # Avec coverage"
    echo "  ./run_tests.sh debug test_my_test # Debug un test"
}

# Si aucun argument ou 'all'
if [ $# -eq 0 ] || [ "$1" == "all" ]; then
    echo -e "${GREEN}📦 Lance tous les tests...${NC}"
    pytest tests/ -v
    
elif [ "$1" == "basic" ]; then
    echo -e "${GREEN}📦 Lance les tests de base...${NC}"
    pytest tests/test_cpsat_basic.py -v
    
elif [ "$1" == "penalties" ]; then
    echo -e "${GREEN}📦 Lance les tests de pénalités...${NC}"
    pytest tests/test_cpsat_penalties.py -v
    
elif [ "$1" == "examples" ]; then
    echo -e "${GREEN}📦 Lance les exemples guidés...${NC}"
    pytest tests/test_examples.py -v
    
elif [ "$1" == "quick" ]; then
    echo -e "${GREEN}⚡ Lance les tests rapides...${NC}"
    pytest tests/ -v -x  # Arrêt au premier échec
    
elif [ "$1" == "coverage" ]; then
    echo -e "${GREEN}📊 Génère le rapport de coverage...${NC}"
    pytest tests/ --cov=pycalendar.solvers --cov-report=html --cov-report=term
    echo ""
    echo -e "${YELLOW}📂 Rapport HTML généré dans: htmlcov/index.html${NC}"
    echo "   Ouvrir avec: open htmlcov/index.html"
    
elif [ "$1" == "failed" ]; then
    echo -e "${YELLOW}🔄 Relance les tests échoués...${NC}"
    pytest --lf -v
    
elif [ "$1" == "debug" ]; then
    if [ -z "$2" ]; then
        echo "❌ Erreur: Spécifiez le nom du test à débugger"
        echo "   Exemple: ./run_tests.sh debug test_single_match"
        exit 1
    fi
    echo -e "${YELLOW}🐛 Debug du test: $2${NC}"
    pytest tests/ -v -s -k "$2"
    
elif [ "$1" == "-h" ] || [ "$1" == "--help" ]; then
    show_help
    
else
    echo "❌ Option inconnue: $1"
    echo ""
    show_help
    exit 1
fi

echo ""
echo "========================================="
echo "✅ Terminé !"
echo "========================================="
