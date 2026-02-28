"""
Application configuration for the Hospital Prediction API.
Paths and model versions used for loading artifacts and logging.
"""
import os
from pathlib import Path

# Base paths (support running from project root or from api/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = Path(os.getenv("MODELS_DIR", str(PROJECT_ROOT / "models")))
ARTIFACTS_DIR = Path(os.getenv("ARTIFACTS_DIR", str(PROJECT_ROOT / "artifacts")))

# Model artifact filenames (from Phase 3)
RISK_MODEL_FILENAME = os.getenv("RISK_MODEL_FILENAME", "visit_risk_model.pkl")
CLAIM_MODEL_FILENAME = os.getenv("CLAIM_MODEL_FILENAME", "claim_outcome_model.pkl")
FEATURE_SCHEMA_FILENAME = os.getenv("FEATURE_SCHEMA_FILENAME", "feature_schema.json")

# Full paths
RISK_MODEL_PATH = MODELS_DIR / RISK_MODEL_FILENAME
CLAIM_MODEL_PATH = MODELS_DIR / CLAIM_MODEL_FILENAME
FEATURE_SCHEMA_PATH = ARTIFACTS_DIR / FEATURE_SCHEMA_FILENAME

# Model version for audit logging (set via env or default)
RISK_MODEL_VERSION = os.getenv("RISK_MODEL_VERSION", "1.0.0")
CLAIM_MODEL_VERSION = os.getenv("CLAIM_MODEL_VERSION", "1.0.0")

# API settings
API_TITLE = "Hospital Prediction API"
API_VERSION = "1.0.0"
LOG_PREDICTIONS = os.getenv("LOG_PREDICTIONS", "true").lower() == "true"
