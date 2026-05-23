from app.routes.auth import router as auth_router
from app.routes.conflict_check import router as conflict_router
from app.routes.gap_analysis import router as gap_router
from app.routes.general import router as general_router
from app.routes.policy_guidance import router as policy_router
from app.routes.query import router as query_router
from app.routes.regulation import router as regulation_router

__all__ = [
    "auth_router",
    "conflict_router",
    "gap_router",
    "general_router",
    "policy_router",
    "query_router",
    "regulation_router",
]
