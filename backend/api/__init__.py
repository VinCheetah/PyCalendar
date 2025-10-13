"""
FastAPI backend package for PyCalendar V2.

This package contains the REST API implementation with:
- main: FastAPI application with CORS middleware
- routes: API endpoints for all entities (matches, projects, teams, venues)
"""

from backend.api.main import app

__all__ = ["app"]
