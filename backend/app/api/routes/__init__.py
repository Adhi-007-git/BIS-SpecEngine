"""
API Routes Package.
"""
from backend.app.api.routes import (
    search,
    upload,
    recommendations,
    standards,
    evidence,
    graph,
    review,
    standards_management
)

__all__ = [
    "search",
    "upload",
    "recommendations",
    "standards",
    "evidence",
    "graph",
    "review",
    "standards_management"
]
