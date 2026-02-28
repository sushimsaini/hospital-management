"""
Hospital Prediction API - Phase 5.
FastAPI service for visit risk and claim outcome predictions.
"""
import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import API_TITLE, API_VERSION
from api.routers import health_router, predictions_router

# Configure logging so prediction_log entries are visible
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    stream=sys.stdout,
)

app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description="Real-time predictions for visit risk and claim outcome (Phase 5).",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(predictions_router)


@app.get("/")
def root() -> dict:
    """Root redirect to docs."""
    return {
        "service": API_TITLE,
        "version": API_VERSION,
        "docs": "/docs",
        "health": "/health",
        "predict_risk": "POST /predict/risk",
        "predict_claim": "POST /predict/claim",
    }
