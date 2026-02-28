"""
Risk model loader and predictor (Visit Risk Classification - Model A).
Loads pickle (.pkl) artifact and feature schema; runs prediction with logging.
Builds feature vector to match model's fit-time schema (feature_names_in_) when present.
"""
import logging
from pathlib import Path
from typing import Any, Optional

from api.config import FEATURE_SCHEMA_PATH, RISK_MODEL_PATH, RISK_MODEL_VERSION
from api.schemas import RiskPredictionRequest, RiskPredictionResponse, RiskScore
from api.services.prediction_logger import log_prediction

logger = logging.getLogger(__name__)

_risk_model = None
_feature_schema = None

# API request field name -> model fit-time name (when different)
_RISK_FIELD_TO_MODEL = {
    "avg_length_of_stay_patient": "avg_los_per_patient",
}


def _load_model():
    global _risk_model
    if _risk_model is not None:
        return _risk_model
    if not RISK_MODEL_PATH.exists():
        logger.warning("Risk model file not found at %s", RISK_MODEL_PATH)
        return None
    try:
        # Support both joblib and pickle: many sklearn/training flows save with joblib even as .pkl
        try:
            import joblib
            raw = joblib.load(RISK_MODEL_PATH)
        except Exception:
            import pickle
            with open(RISK_MODEL_PATH, "rb") as f:
                raw = pickle.load(f)
        # Unwrap if artifact is a dict (e.g. {"model": estimator, "encoder": ...})
        if isinstance(raw, dict) and "model" in raw:
            _risk_model = raw["model"]
            logger.info("Risk model loaded from %s (unwrapped from dict)", RISK_MODEL_PATH)
        else:
            _risk_model = raw
            logger.info("Risk model loaded from %s", RISK_MODEL_PATH)
        if not hasattr(_risk_model, "predict_proba"):
            logger.warning(
                "Risk model has no predict_proba; responses will have probabilities=null"
            )
        return _risk_model
    except Exception as e:
        logger.exception("Failed to load risk model: %s", e)
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


def _get_model_feature_names(model: Any) -> Optional[list[str]]:
    """Return the list of feature names the model was fit with, or None."""
    if hasattr(model, "feature_names_in_") and model.feature_names_in_ is not None:
        return list(model.feature_names_in_)
    # Pipeline: try last step (classifier) or pipeline itself
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


def _request_to_features(req: RiskPredictionRequest) -> dict[str, Any]:
    """Convert Pydantic request to feature dict for model (and logging)."""
    return req.model_dump(exclude_none=True, by_alias=False)


def _build_row_for_model_feature_names(
    feature_names: list[str], req: RiskPredictionRequest
) -> dict[str, Any]:
    """
    Build a single row dict with keys exactly feature_names, using request fields.
    Handles: direct numeric fields, API->model name mapping, one-hot columns (prefix_value).
    """
    raw = _request_to_features(req)
    row: dict[str, Any] = {}
    for name in feature_names:
        if name in row:
            continue
        # Mapped name (e.g. avg_los_per_patient <- avg_length_of_stay_patient)
        api_name = next(
            (k for k, v in _RISK_FIELD_TO_MODEL.items() if v == name), None
        )
        if api_name is not None and raw.get(api_name) is not None:
            row[name] = raw[api_name]
            continue
        if name in raw and raw.get(name) is not None:
            val = raw[name]
            # Model expects numeric X; skip string values (use one-hot or 0.0 fallback below).
            if isinstance(val, (int, float)) and not isinstance(val, bool):
                row[name] = val
                continue
            # else: val is str or other; don't set row[name] here, let one-hot or 0.0 handle it
        # One-hot style: "gender_F", "gender_M" -> use request "gender": "F" to set gender_F=1.0, gender_M=0.0.
        # We do not convert the string "F" to a float; we use it only to pick which one-hot column is 1.
        if "_" in name:
            parts = name.split("_", 1)
            prefix, rest = parts[0], parts[1]
            req_val = raw.get(prefix)
            if req_val is not None and isinstance(req_val, str):
                norm = lambda s: (s or "").replace("_", " ").lower()
                row[name] = 1.0 if norm(rest) == norm(req_val) else 0.0
                continue
        # Defaults for common extra training-only features
        if name == "age":
            row[name] = raw.get("age") if raw.get("age") is not None else 0.0
            continue
        if name == "chronic_flag":
            row[name] = raw.get("chronic_flag") if raw.get("chronic_flag") is not None else 0.0
            continue
        # Model expects numeric X; use 0.0 for any missing feature (no strings like "").
        row[name] = 0.0
    return row


def _predict_with_proba(model: Any, features: dict) -> tuple:
    """Run model predict; return class label and probabilities if available."""
    # Try predict_proba first (sklearn-style)
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
    # Model has predict but not predict_proba (e.g. some wrappers or dict-saved artifacts)
    pred = model.predict(features)
    label = str(pred[0]) if hasattr(pred, "__getitem__") else str(pred)
    return label, None


def predict_risk(req: RiskPredictionRequest, request_id: Optional[str] = None) -> RiskPredictionResponse:
    """
    Run risk classification and return response with model version.
    If model is not loaded, returns a fallback response and logs warning.
    """
    features = _request_to_features(req)
    model = _load_model()
    if model is None:
        # Fallback when model not deployed (e.g. dev without artifacts)
        log_prediction("risk_model", RISK_MODEL_VERSION, request_id, features, "Low", None)
        return RiskPredictionResponse(
            risk_score=RiskScore.LOW,
            probabilities=None,
            model_version=RISK_MODEL_VERSION,
            request_id=request_id,
        )
    import pandas as pd
    model_feature_names = _get_model_feature_names(model)
    if model_feature_names:
        # Build a row that exactly matches the model's fit-time feature names (order + one-hot, etc.)
        row = _build_row_for_model_feature_names(model_feature_names, req)
        # Use row[n] so string values (e.g. gender="F") are not replaced by 0.0
        ordered = [row[n] for n in model_feature_names]
        feature_vector = pd.DataFrame([ordered], columns=model_feature_names)
    else:
        # Fallback: use feature_schema or plain request dict
        schema = _load_feature_schema()
        risk_features = (schema or {}).get("risk", {}).get("features") if isinstance(schema, dict) else None
        if risk_features and isinstance(features, dict):
            ordered = [features.get(k) for k in risk_features]
            feature_vector = pd.DataFrame([ordered], columns=risk_features)
        else:
            feature_vector = pd.DataFrame([features]) if isinstance(features, dict) else pd.DataFrame([features])
    label, probs = _predict_with_proba(model, feature_vector)
    risk_score = _normalize_risk_score(label)
    log_prediction("risk_model", RISK_MODEL_VERSION, request_id, features, risk_score, probs)
    return RiskPredictionResponse(
        risk_score=risk_score,
        probabilities=probs,
        model_version=RISK_MODEL_VERSION,
        request_id=request_id,
    )


def _normalize_risk_score(label: str) -> RiskScore:
    """Map model output to RiskScore enum."""
    s = (label or "").strip().lower()
    if s in ("high", "2"):
        return RiskScore.HIGH
    if s in ("medium", "mid", "1"):
        return RiskScore.MEDIUM
    return RiskScore.LOW
