"""
Prediction logging for audit and governance.
Logs timestamp, model version, input feature hash, and prediction outcome.
"""
import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from api.config import LOG_PREDICTIONS

logger = logging.getLogger(__name__)


def _feature_hash(features: dict) -> str:
    """Compute a stable hash of the input features for idempotency/audit."""
    # Sort keys for deterministic hash
    canonical = json.dumps(features, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


def log_prediction(
    model_name: str,
    model_version: str,
    request_id: Optional[str],
    features: dict,
    prediction: Any,
    probabilities: Optional[dict] = None,
) -> None:
    """
    Log a prediction event for monitoring and governance.
    Only logs if LOG_PREDICTIONS is true.
    """
    if not LOG_PREDICTIONS:
        return
    try:
        input_hash = _feature_hash(features)
        ts = datetime.now(timezone.utc).isoformat()
        payload = {
            "timestamp": ts,
            "model_name": model_name,
            "model_version": model_version,
            "request_id": request_id,
            "input_feature_hash": input_hash,
            "prediction": str(prediction),
            "probabilities": probabilities,
        }
        logger.info("prediction_log", extra=payload)
    except Exception as e:
        logger.warning("prediction_log_failed", extra={"error": str(e)})
