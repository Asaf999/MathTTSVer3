"""API routers for MathTTS v3."""

from .expressions import router as expression_router
from .patterns import router as pattern_router
from .voices import router as voice_router
from .health import router as health_router
from .auth import router as auth_router

__all__ = [
    "expression_router",
    "pattern_router", 
    "voice_router",
    "health_router",
    "auth_router"
]