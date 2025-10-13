#!/usr/bin/env fish

# PyCalendar V2 - End-to-End Test Script
# =========================================
# Tests the complete workflow: Backend API → Frontend UI → Solver Integration
# 
# Requirements:
# - Python 3.12+ with uvicorn, fastapi, sqlalchemy
# - Node.js 18+ with npm
# - Port 8000 (backend) and 5173 (frontend) available
#
# Usage:
#   chmod +x test_e2e.fish
#   ./test_e2e.fish

set -g RED '\033[0;31m'
set -g GREEN '\033[0;32m'
set -g YELLOW '\033[1;33m'
set -g BLUE '\033[0;34m'
set -g NC '\033[0m' # No Color

# Configuration
set -g BACKEND_PORT 8000
set -g FRONTEND_PORT 5173
set -g PROJECT_ROOT (pwd)
set -g BACKEND_PID ""
set -g FRONTEND_PID ""

# Fonctions utilitaires
function log_info
    echo -e "$BLUE[INFO]$NC $argv"
end

function log_success
    echo -e "$GREEN[✓]$NC $argv"
end

function log_error
    echo -e "$RED[✗]$NC $argv"
end

function log_warning
    echo -e "$YELLOW[!]$NC $argv"
end

function cleanup
    log_info "Nettoyage des processus..."
    
    if test -n "$BACKEND_PID"
        kill $BACKEND_PID 2>/dev/null
        log_info "Backend arrêté (PID: $BACKEND_PID)"
    end
    
    if test -n "$FRONTEND_PID"
        kill $FRONTEND_PID 2>/dev/null
        log_info "Frontend arrêté (PID: $FRONTEND_PID)"
    end
    
    # Kill any remaining processes on ports
    lsof -ti:$BACKEND_PORT | xargs kill -9 2>/dev/null
    lsof -ti:$FRONTEND_PORT | xargs kill -9 2>/dev/null
    
    log_success "Nettoyage terminé"
end

# Trap pour cleanup sur exit
trap cleanup EXIT INT TERM

# ============================================================
# 1. VÉRIFICATIONS PRÉLIMINAIRES
# ============================================================

log_info "=== Phase 1: Vérifications préliminaires ==="

# Vérifier Python
if not command -v python3 &>/dev/null
    log_error "Python 3 n'est pas installé"
    exit 1
end
log_success "Python: "(python3 --version)

# Vérifier Node.js
if not command -v node &>/dev/null
    log_error "Node.js n'est pas installé"
    exit 1
end
log_success "Node.js: "(node --version)

# Vérifier npm
if not command -v npm &>/dev/null
    log_error "npm n'est pas installé"
    exit 1
end
log_success "npm: "(npm --version)

# Vérifier que les ports sont libres
if lsof -Pi :$BACKEND_PORT -sTCP:LISTEN -t >/dev/null
    log_error "Port $BACKEND_PORT déjà utilisé. Arrêtez le processus d'abord."
    exit 1
end
log_success "Port $BACKEND_PORT disponible"

if lsof -Pi :$FRONTEND_PORT -sTCP:LISTEN -t >/dev/null
    log_error "Port $FRONTEND_PORT déjà utilisé. Arrêtez le processus d'abord."
    exit 1
end
log_success "Port $FRONTEND_PORT disponible"

# ============================================================
# 2. DÉMARRAGE BACKEND
# ============================================================

log_info "=== Phase 2: Démarrage du backend ==="

# Vérifier que le dossier backend existe
if not test -d backend
    log_error "Dossier backend/ introuvable"
    exit 1
end

# Démarrer le backend en arrière-plan
log_info "Démarrage de l'API FastAPI sur le port $BACKEND_PORT..."
set -gx PYTHONPATH $PROJECT_ROOT
python3 -m uvicorn backend.api.main:app --port $BACKEND_PORT --log-level warning >/tmp/pycalendar_backend.log 2>&1 &
set -g BACKEND_PID $last_pid

log_info "Backend PID: $BACKEND_PID"

# Attendre que le backend soit prêt (max 30 secondes)
set -l max_attempts 30
set -l attempt 0

while test $attempt -lt $max_attempts
    if curl -s http://localhost:$BACKEND_PORT/health >/dev/null 2>&1
        log_success "Backend démarré et prêt (/health répond)"
        break
    end
    
    set attempt (math $attempt + 1)
    sleep 1
    
    if test $attempt -eq $max_attempts
        log_error "Timeout: le backend n'a pas démarré dans les 30 secondes"
        log_info "Logs du backend:"
        cat /tmp/pycalendar_backend.log
        exit 1
    end
end

# ============================================================
# 3. TESTS API BACKEND
# ============================================================

log_info "=== Phase 3: Tests de l'API backend ==="

# Test 1: Health check
log_info "Test 1/4: Health check..."
set -l health_response (curl -s http://localhost:$BACKEND_PORT/health)
if test $status -eq 0
    log_success "✓ Health check OK: $health_response"
else
    log_error "✗ Health check échoué"
    exit 1
end

# Test 2: Liste des projets
log_info "Test 2/4: GET /projects..."
set -l projects_response (curl -s http://localhost:$BACKEND_PORT/projects)
if test $status -eq 0
    log_success "✓ GET /projects OK"
    echo "  Response: $projects_response" | head -c 100
    echo "..."
else
    log_error "✗ GET /projects échoué"
    exit 1
end

# Test 3: Créer un projet de test
log_info "Test 3/4: POST /projects (création projet test)..."
set -l create_response (curl -s -X POST http://localhost:$BACKEND_PORT/projects \
    -H "Content-Type: application/json" \
    -d '{"nom": "Test E2E", "description": "Projet de test automatisé"}')

if test $status -eq 0
    log_success "✓ POST /projects OK"
    set -g TEST_PROJECT_ID (echo $create_response | grep -o '"id":[0-9]*' | grep -o '[0-9]*')
    log_info "  Project ID créé: $TEST_PROJECT_ID"
else
    log_error "✗ POST /projects échoué"
    exit 1
end

# Test 4: Résolution du projet (Greedy)
if test -n "$TEST_PROJECT_ID"
    log_info "Test 4/4: POST /projects/$TEST_PROJECT_ID/solve (Greedy)..."
    set -l solve_response (curl -s -X POST http://localhost:$BACKEND_PORT/projects/$TEST_PROJECT_ID/solve \
        -H "Content-Type: application/json" \
        -d '{"strategy": "greedy"}')
    
    if test $status -eq 0
        log_success "✓ POST /solve OK"
        echo "  Response: $solve_response" | head -c 150
        echo "..."
    else
        log_error "✗ POST /solve échoué"
        exit 1
    end
end

# ============================================================
# 4. DÉMARRAGE FRONTEND
# ============================================================

log_info "=== Phase 4: Démarrage du frontend ==="

# Vérifier que le dossier frontend existe
if not test -d frontend
    log_error "Dossier frontend/ introuvable"
    exit 1
end

# Installer les dépendances si nécessaire
if not test -d frontend/node_modules
    log_info "Installation des dépendances npm..."
    cd frontend
    npm install --silent
    cd ..
    log_success "Dépendances installées"
end

# Démarrer le frontend en arrière-plan
log_info "Démarrage du frontend Vite sur le port $FRONTEND_PORT..."
cd frontend
npm run dev -- --port $FRONTEND_PORT >/tmp/pycalendar_frontend.log 2>&1 &
set -g FRONTEND_PID $last_pid
cd ..

log_info "Frontend PID: $FRONTEND_PID"

# Attendre que le frontend soit prêt (max 30 secondes)
set attempt 0
while test $attempt -lt $max_attempts
    if curl -s http://localhost:$FRONTEND_PORT >/dev/null 2>&1
        log_success "Frontend démarré et prêt"
        break
    end
    
    set attempt (math $attempt + 1)
    sleep 1
    
    if test $attempt -eq $max_attempts
        log_error "Timeout: le frontend n'a pas démarré dans les 30 secondes"
        log_info "Logs du frontend:"
        cat /tmp/pycalendar_frontend.log
        exit 1
    end
end

# ============================================================
# 5. TESTS MANUELS INTERACTIFS
# ============================================================

log_info "=== Phase 5: Tests manuels ==="

log_success "✅ Backend et Frontend sont opérationnels!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "$GREEN Environnement de test prêt! $NC"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "$BLUE Backend API:$NC    http://localhost:$BACKEND_PORT"
echo -e "$BLUE API Docs:$NC      http://localhost:$BACKEND_PORT/docs"
echo -e "$BLUE Frontend UI:$NC   http://localhost:$FRONTEND_PORT"
echo ""
echo -e "$YELLOW Tests à effectuer manuellement:$NC"
echo "  1. Ouvrir http://localhost:$FRONTEND_PORT dans un navigateur"
echo "  2. Sélectionner le projet 'Test E2E' (ID: $TEST_PROJECT_ID)"
echo "  3. Cliquer sur 'Résoudre (Greedy)' ou 'Résoudre (CP-SAT)'"
echo "  4. Vérifier que:"
echo "     - Un toast de chargement s'affiche"
echo "     - Un overlay avec spinner apparaît"
echo "     - Un toast de succès apparaît avec les métriques"
echo "     - Le calendrier se met à jour automatiquement"
echo ""
echo -e "$YELLOW Pour arrêter les services:$NC"
echo "  Appuyez sur Ctrl+C"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Attendre que l'utilisateur appuie sur Ctrl+C
read -P "Appuyez sur Entrée pour arrêter les services..."

# Le cleanup sera appelé automatiquement via le trap EXIT
