"""
FastAPI routers for the scheduling application.

This package contains modular router definitions for different API features.
"""

from .schedule import router as schedule_router

__all__ = ["schedule_router"]
