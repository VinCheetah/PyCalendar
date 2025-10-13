"""
API Routes package for PyCalendar V2.

This package contains all the FastAPI routers for the REST API:
- matches: Match CRUD + fix/unfix/move operations
- projects: Project CRUD + statistics
- teams: Team CRUD
- venues: Venue/Gymnasium CRUD
"""

from backend.api.routes import matches, projects, teams, venues

__all__ = ["matches", "projects", "teams", "venues"]
