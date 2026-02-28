"""
Prediction endpoints for risk and claim models.
"""
from typing import Optional

from fastapi import APIRouter, Header

from api.schemas import (
    ClaimPredictionBatchRequest,
    ClaimPredictionBatchResponse,
    ClaimPredictionRequest,
    ClaimPredictionResponse,
    RiskPredictionBatchRequest,
    RiskPredictionBatchResponse,
    RiskPredictionRequest,
    RiskPredictionResponse,
)
from api.services import predict_claim, predict_risk

router = APIRouter(prefix="/predict", tags=["predictions"])


def _request_id(x_request_id: Optional[str] = Header(None, alias="X-Request-ID")) -> Optional[str]:
    return x_request_id


@router.post("/risk", response_model=RiskPredictionResponse)
def predict_visit_risk(
    body: RiskPredictionRequest,
    x_request_id: Optional[str] = Header(None, alias="X-Request-ID"),
) -> RiskPredictionResponse:
    """
    Predict visit risk (Low / Medium / High) for a single visit.
    Uses Model A from Phase 3.
    """
    return predict_risk(body, request_id=x_request_id)


@router.post("/claim", response_model=ClaimPredictionResponse)
def predict_claim_outcome(
    body: ClaimPredictionRequest,
    x_request_id: Optional[str] = Header(None, alias="X-Request-ID"),
) -> ClaimPredictionResponse:
    """
    Predict claim outcome (Paid / Pending / Rejected) for a single claim.
    Uses Model B from Phase 3.
    """
    return predict_claim(body, request_id=x_request_id)


@router.post("/risk/batch", response_model=RiskPredictionBatchResponse)
def predict_visit_risk_batch(
    body: RiskPredictionBatchRequest,
    x_request_id: Optional[str] = Header(None, alias="X-Request-ID"),
) -> RiskPredictionBatchResponse:
    """Batch risk predictions (max 100 per request)."""
    from api.config import RISK_MODEL_VERSION
    predictions = [predict_risk(r, request_id=body.request_id or x_request_id) for r in body.requests]
    return RiskPredictionBatchResponse(
        predictions=predictions,
        model_version=RISK_MODEL_VERSION,
        request_id=body.request_id or x_request_id,
    )


@router.post("/claim/batch", response_model=ClaimPredictionBatchResponse)
def predict_claim_outcome_batch(
    body: ClaimPredictionBatchRequest,
    x_request_id: Optional[str] = Header(None, alias="X-Request-ID"),
) -> ClaimPredictionBatchResponse:
    """Batch claim predictions (max 100 per request)."""
    from api.config import CLAIM_MODEL_VERSION
    predictions = [
        predict_claim(r, request_id=body.request_id or x_request_id) for r in body.requests
    ]
    return ClaimPredictionBatchResponse(
        predictions=predictions,
        model_version=CLAIM_MODEL_VERSION,
        request_id=body.request_id or x_request_id,
    )
