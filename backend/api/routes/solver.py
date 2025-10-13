"""
Routes API pour la résolution de projets via le solveur.

Ce module expose les endpoints pour déclencher la résolution d'un projet,
en utilisant le SolverService qui orchestre l'ensemble du processus.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import time

from backend.database.engine import get_db
from backend.database import models
from backend.schemas import solver as schemas
from backend.services.solver_service import SolverService, SolverError

router = APIRouter()


@router.post("/{project_id}/solve", response_model=schemas.SolveResponse, tags=["Solver"])
def solve_project(
    project_id: int,
    request: schemas.SolveRequest,
    db: Session = Depends(get_db)
):
    """
    Résout le calendrier d'un projet avec la stratégie choisie.
    
    ## Workflow
    
    1. **Chargement** : Récupère projet, matchs, équipes, gymnases depuis DB
    2. **Filtrage** : Identifie matchs fixes (est_fixe=True ou semaine < semaine_minimum)
    3. **Conversion** : Convertit modèles DB → modèles Core (dataclasses)
    4. **Résolution** : Exécute solveur (CPSATSolver ou GreedySolver)
    5. **Validation** : Vérifie contraintes (matchs fixes, conflits équipes/gymnases)
    6. **Persistance** : Met à jour matchs modifiables dans DB
    7. **Retour** : Résumé avec métriques de résolution
    
    ## Stratégies disponibles
    
    - **cpsat** : Solveur CP-SAT (Google OR-Tools) pour solution optimale
    - **greedy** : Algorithme heuristique glouton rapide
    
    ## Contraintes respectées
    
    - ✅ Matchs fixes non modifiés (est_fixe=True)
    - ✅ Matchs avant semaine_minimum non modifiés  
    - ✅ Respect des indisponibilités (équipes, gymnases, institutions)
    - ✅ Équilibre domicile/extérieur
    - ✅ Temps de repos entre matchs
    - ✅ Capacité des gymnases
    
    ## Exemples
    
    ```bash
    # Résolution avec stratégie greedy (par défaut)
    curl -X POST http://localhost:8000/projects/1/solve \\
      -H "Content-Type: application/json" \\
      -d '{"strategy": "greedy"}'
    
    # Résolution avec stratégie cpsat (optimal)
    curl -X POST http://localhost:8000/projects/1/solve \\
      -H "Content-Type: application/json" \\
      -d '{"strategy": "cpsat"}'
    ```
    
    ## Réponse
    
    Retourne un résumé de résolution avec :
    - Stratégie utilisée
    - Nombre de matchs total, fixes, planifiés, modifiés
    - Temps d'exécution
    - Score de la solution (si disponible)
    - Erreurs éventuelles
    
    ## Gestion des erreurs
    
    - **404** : Projet non trouvé
    - **400** : Stratégie invalide ou erreur de résolution (aucune solution, timeout)
    - **500** : Erreur serveur inattendue
    """
    
    # Vérifier que le projet existe
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Projet {project_id} non trouvé"
        )
    
    # Valider la stratégie
    valid_strategies = ["cpsat", "greedy"]
    if request.strategy not in valid_strategies:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stratégie invalide: '{request.strategy}'. Utiliser: {', '.join(valid_strategies)}"
        )
    
    # Mesurer le temps d'exécution
    start_time = time.time()
    
    try:
        # Instancier le service et résoudre
        service = SolverService(db)
        result = service.solve_project(project_id, strategy=request.strategy)
        
        # Calculer le temps d'exécution
        execution_time = time.time() - start_time
        
        # Construire la réponse
        return schemas.SolveResponse(
            project_id=result['project_id'],
            strategy=result['strategy'],
            nb_matchs_total=result['nb_matchs_total'],
            nb_matchs_fixes=result['nb_matchs_fixes'],
            nb_matchs_planifies=result['nb_matchs_planifies'],
            nb_matchs_updated=result['nb_matchs_updated'],
            execution_time=round(execution_time, 2),
            solution_score=result.get('solution_score'),
            erreurs=None
        )
    
    except SolverError as e:
        # Erreur métier du solveur (aucune solution trouvée, contraintes impossibles, etc.)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erreur lors de la résolution : {str(e)}"
        )
    
    except Exception as e:
        # Erreur inattendue
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur serveur : {str(e)}"
        )
