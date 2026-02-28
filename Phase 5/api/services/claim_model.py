"""
Claim model loader and predictor (Claim Outcome Classification - Model B).
Loads pickle (.pkl) artifact; runs prediction with logging.
Builds feature vector to match model's fit-time schema (feature_names_in_) when present.
"""
import logging
from typing import Any, Optional

from api.config import CLAIM_MODEL_PATH, CLAIM_MODEL_VERSION, FEATURE_SCHEMA_PATH
from api.schemas import ClaimPredictionRequest, ClaimPredictionResponse, ClaimStatus
from api.services.prediction_logger import log_prediction

logger = logging.getLogger(__name__)

_claim_model = None
_feature_schema = None


def _load_model():
    global _claim_model
    if _claim_model is not None:
        return _claim_model
    if not CLAIM_MODEL_PATH.exists():
        logger.warning("Claim model file not found at %s", CLAIM_MODEL_PATH)
        return None
    try:
        try:
            import joblib
            raw = joblib.load(CLAIM_MODEL_PATH)
        except Exception:
            import pickle
            with open(CLAIM_MODEL_PATH, "rb") as f:
                raw = pickle.load(f)
        if isinstance(raw, dict) and "model" in raw:
            _claim_model = raw["model"]
            logger.info("Claim model loaded from %s (unwrapped from dict)", CLAIM_MODEL_PATH)
        else:
            _claim_model = raw
            logger.info("Claim model loaded from %s", CLAIM_MODEL_PATH)
        if not hasattr(_claim_model, "predict_proba"):
            logger.warning(
                "Claim model has no predict_proba; responses will have probabilities=null"
            )
        return _claim_model
    except Exception as e:
        logger.exception("Failed to load claim model: %s", e)
        return None


def _get_model_feature_names(model: Any) -> Optional[list[str]]:
    """Return the list of feature names the model was fit with, or None."""
    if hasattr(model, "feature_names_in_") and model.feature_names_in_ is not None:
        return list(model.feature_names_in_)
    if hasattr(model, "steps") and model.steps:
        last = model.steps[-1][1]
        if hasattr(last, "feature_names_in_") and last.feature_names_in_ is not None:
            return list(last.feature_names_in_)
    if hasattr(model, "named_steps"):
        for name in reversed(list(model.named_steps.keys())):
            step = model.named_steps[name]
            if hasattr(step, "feature_names_in_") and step.feature_names_in_ is not None:
                return list(step.feature_names_in_)
    return None


def _load_feature_schema() -> Optional[dict]:
    global _feature_schema
    if _feature_schema is not None:
        return _feature_schema
    if not FEATURE_SCHEMA_PATH.exists():
        return None
    try:
        import json
        with open(FEATURE_SCHEMA_PATH) as f:
            _feature_schema = json.load(f)
        return _feature_schema
    except Exception as e:
        logger.warning("Could not load feature schema: %s", e)
        return None


def _request_to_features(req: ClaimPredictionRequest) -> dict[str, Any]:
    return req.model_dump(exclude_none=True, by_alias=False)


def _build_row_for_claim_model_feature_names(
    feature_names: list[str], req: ClaimPredictionRequest
) -> dict[str, Any]:
    """
    Build a single row dict with keys exactly feature_names, using request fields.
    Handles: numeric fields, one-hot columns (prefix_value), age/chronic_flag defaults.
    Model expects numeric X only (no strings).
    """
    raw = _request_to_features(req)
    row: dict[str, Any] = {}
    for name in feature_names:
        if name in row:
            continue
        if name in raw and raw.get(name) is not None:
            val = raw[name]
            if isinstance(val, (int, float)) and not isinstance(val, bool):
                row[name] = val
                continue
        if "_" in name:
            parts = name.split("_", 1)
            prefix, rest = parts[0], parts[1]
            req_val = raw.get(prefix)
            if req_val is not None and isinstance(req_val, str):
                norm = lambda s: (s or "").replace("_", " ").lower()
                row[name] = 1.0 if norm(rest) == norm(req_val) else 0.0
                continue
        if name == "age":
            row[name] = raw.get("age") if raw.get("age") is not None else 0.0
            continue
        if name == "chronic_flag":
            row[name] = raw.get("chronic_flag") if raw.get("chronic_flag") is not None else 0.0
            continue
        row[name] = 0.0
    return row


def _predict_with_proba(model: Any, features: dict) -> tuple:
    if hasattr(model, "predict_proba"):
        probs = model.predict_proba(features)
        if hasattr(model, "classes_"):
            classes = list(model.classes_)
            proba_dict = {str(c): float(p) for c, p in zip(classes, probs[0])}
        else:
            proba_dict = None
        pred = model.predict(features)
        label = str(pred[0]) if hasattr(pred, "__getitem__") else str(pred)
        return label, proba_dict
    pred = model.predict(features)
    label = str(pred[0]) if hasattr(pred, "__getitem__") else str(pred)
    return label, None


def predict_claim(
    req: ClaimPredictionRequest, request_id: Optional[str] = None
) -> ClaimPredictionResponse:
    """
    Run claim outcome classification and return response.
    If model is not loaded, returns fallback Pending with model version.
    """
    features = _request_to_features(req)
    model = _load_model()
    if model is None:
        log_prediction("claim_model", CLAIM_MODEL_VERSION, request_id, features, "Pending", None)
        return ClaimPredictionResponse(
            claim_status=ClaimStatus.PENDING,
            probabilities=None,
            model_version=CLAIM_MODEL_VERSION,
            request_id=request_id,
        )
    import pandas as pd
    model_feature_names = _get_model_feature_names(model)
    if model_feature_names:
        row = _build_row_for_claim_model_feature_names(model_feature_names, req)
        ordered = [row[n] for n in model_feature_names]
        feature_vector = pd.DataFrame([ordered], columns=model_feature_names)
    else:
        schema = _load_feature_schema()
        claim_features = (schema or {}).get("claim", {}).get("features") if isinstance(schema, dict) else None
        if claim_features and isinstance(features, dict):
            ordered = [features.get(k) for k in claim_features]
            feature_vector = pd.DataFrame([ordered], columns=claim_features)
        else:
            feature_vector = pd.DataFrame([features]) if isinstance(features, dict) else pd.DataFrame([features])
    label, probs = _predict_with_proba(model, feature_vector)
    claim_status = _normalize_claim_status(label)
    log_prediction("claim_model", CLAIM_MODEL_VERSION, request_id, features, claim_status, probs)
    return ClaimPredictionResponse(
        claim_status=claim_status,
        probabilities=probs,
        model_version=CLAIM_MODEL_VERSION,
        request_id=request_id,
    )


def _normalize_claim_status(label: str) -> ClaimStatus:
    s = (label or "").strip().lower()
    if s in ("rejected", "reject"):
        return ClaimStatus.REJECTED
    if s in ("paid", "accept"):
        return ClaimStatus.PAID
    return ClaimStatus.PENDING
