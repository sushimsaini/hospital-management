from .health import router as health_router
from .predictions import router as predictions_router

__all__ = ["health_router", "predictions_router"]
