#!/usr/bin/env fish
# Script pour exécuter les tests PyCalendar avec couverture de code
# Usage: ./scripts/run_tests.sh [OPTIONS]
# Options: --unit, --api, --integration, --coverage, --html, --verbose

set SCRIPT_DIR (dirname (status -f))
set PROJECT_ROOT (cd "$SCRIPT_DIR/.." && pwd)
set PYTHON "$PROJECT_ROOT/.venv/bin/python"

# Couleurs
set GREEN \x1b[32m
set BLUE \x1b[34m
set YELLOW \x1b[33m
set RED \x1b[31m
set RESET \x1b[0m

# Configuration par défaut
set test_args "-v"
set coverage_args "--cov=backend --cov-report=term-missing"
set html_report false
set run_type "all"

# Parser les arguments
for arg in $argv
    switch $arg
        case --unit
            set run_type "unit"
            set test_args "$test_args -m unit"
        case --api
            set run_type "api"
            set test_args "$test_args -m api"
        case --integration
            set run_type "integration"
            set test_args "$test_args -m integration"
        case --coverage --cov
            set coverage_args "--cov=backend --cov-report=term-missing --cov-report=html"
            set html_report true
        case --html
            set html_report true
            set coverage_args "$coverage_args --cov-report=html"
        case --verbose -v
            set test_args "$test_args -vv"
        case --help -h
            echo "Usage: ./scripts/run_tests.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --unit         Exécuter uniquement les tests unitaires"
            echo "  --api          Exécuter uniquement les tests API"
            echo "  --integration  Exécuter uniquement les tests d'intégration"
            echo "  --coverage     Générer rapport de couverture HTML"
            echo "  --html         Générer rapport HTML"
            echo "  --verbose      Mode verbeux"
            echo "  --help         Afficher cette aide"
            echo ""
            echo "Exemples:"
            echo "  ./scripts/run_tests.sh                    # Tous les tests"
            echo "  ./scripts/run_tests.sh --unit --coverage  # Tests unitaires avec couverture"
            echo "  ./scripts/run_tests.sh --api --html       # Tests API avec rapport HTML"
            exit 0
    end
end

# Banner
echo ""
echo "$BLUE━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$RESET"
echo "$BLUE                      🧪 PyCalendar Test Suite 🧪                                $RESET"
echo "$BLUE━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$RESET"
echo ""

# Vérifier environnement Python
if not test -f "$PYTHON"
    echo "$RED✗ Erreur: Python non trouvé à $PYTHON$RESET"
    echo "  → Créer venv: python3 -m venv .venv"
    exit 1
end

# Vérifier pytest
if not $PYTHON -c "import pytest" 2>/dev/null
    echo "$YELLOW⚠ pytest non installé. Installation...$RESET"
    $PYTHON -m pip install -q pytest pytest-cov
end

# Afficher configuration
echo "$BLUE📋 Configuration:$RESET"
echo "  Type de tests : $run_type"
echo "  Python        : $PYTHON"
echo "  Arguments     : $test_args $coverage_args"
echo ""

# Exécuter tests
echo "$BLUE🚀 Exécution des tests...$RESET"
echo ""

cd "$PROJECT_ROOT"

if test $run_type = "all"
    set cmd "$PYTHON -m pytest tests/ $test_args $coverage_args"
else
    set cmd "$PYTHON -m pytest tests/ $test_args $coverage_args"
end

eval $cmd
set exit_code $status

# Résultats
echo ""
if test $exit_code -eq 0
    echo "$GREEN━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$RESET"
    echo "$GREEN                        ✅ TOUS LES TESTS PASSÉS ✅                              $RESET"
    echo "$GREEN━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$RESET"
    
    if test "$html_report" = "true"
        echo ""
        echo "$BLUE📊 Rapport de couverture HTML généré:$RESET"
        echo "  → file://$PROJECT_ROOT/htmlcov/index.html"
    end
else
    echo "$RED━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$RESET"
    echo "$RED                        ❌ ÉCHEC DES TESTS ❌                                    $RESET"
    echo "$RED━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$RESET"
end

echo ""
exit $exit_code
