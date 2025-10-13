"""
Pydantic Schemas for Solver API

These schemas handle validation and serialization for solver-related API operations.
They define request/response formats for project resolution endpoints.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


class SolveRequest(BaseModel):
    """
    Request schema for solving a project.
    
    Allows specifying which solver strategy to use.
    Currently supports 'cpsat' (optimal) and 'greedy' (heuristic).
    """
    strategy: str = Field(
        default="greedy",
        description="Solver strategy: 'cpsat' for optimal solution, 'greedy' for fast heuristic"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "strategy": "greedy"
            }
        }
    )


class SolveResponse(BaseModel):
    """
    Response schema for solver execution results.
    
    Contains detailed metrics about the resolution process:
    - Match counts (total, fixed, planned, updated)
    - Execution time
    - Solver strategy used
    - Solution quality score
    """
    project_id: int = Field(description="ID of the resolved project")
    strategy: str = Field(description="Solver strategy used (cpsat/greedy)")
    
    # Match statistics
    nb_matchs_total: int = Field(description="Total number of matches in project")
    nb_matchs_fixes: int = Field(description="Number of fixed matches (not modified)")
    nb_matchs_planifies: int = Field(description="Number of successfully planned matches")
    nb_matchs_updated: int = Field(description="Number of matches updated by solver")
    
    # Performance metrics
    execution_time: float = Field(description="Execution time in seconds")
    solution_score: Optional[float] = Field(
        default=None,
        description="Solution quality score (lower is better)"
    )
    
    # Errors/warnings
    erreurs: Optional[List[str]] = Field(
        default=None,
        description="List of errors or warnings during resolution"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "project_id": 1,
                "strategy": "greedy",
                "nb_matchs_total": 100,
                "nb_matchs_fixes": 15,
                "nb_matchs_planifies": 98,
                "nb_matchs_updated": 83,
                "execution_time": 2.45,
                "solution_score": 145.3,
                "erreurs": None
            }
        }
    )
