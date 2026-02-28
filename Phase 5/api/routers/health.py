"""
Health check endpoint for load balancers and monitoring.
"""
from fastapi import APIRouter

from api.config import API_VERSION, FEATURE_SCHEMA_PATH, RISK_MODEL_PATH, CLAIM_MODEL_PATH
from api.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Liveness/readiness: reports whether models and schema are loaded."""
    risk_loaded = RISK_MODEL_PATH.exists()
    claim_loaded = CLAIM_MODEL_PATH.exists()
    schema_loaded = FEATURE_SCHEMA_PATH.exists()
    status = "ok" if (risk_loaded and claim_loaded) else "degraded"
    return HealthResponse(
        status=status,
        version=API_VERSION,
        risk_model_loaded=risk_loaded,
        claim_model_loaded=claim_loaded,
        feature_schema_loaded=schema_loaded,
    )


@router.get("/live")
def live() -> dict:
    """Minimal liveness probe (no dependency checks)."""
    return {"status": "ok"}
