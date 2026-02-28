"""
Request and response schemas for the Hospital Prediction API.
Validates inputs and structures outputs for risk and claim prediction endpoints.
"""
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# --- Enums aligned with Phase 3 targets ---
class RiskScore(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class ClaimStatus(str, Enum):
    PAID = "Paid"
    PENDING = "Pending"
    REJECTED = "Rejected"


# --- Risk prediction (Visit Risk Classification) ---
class RiskPredictionRequest(BaseModel):
    """Features required for visit risk classification (Model A)."""

    department: str = Field(..., description="Department code or name")
    visit_type: str = Field(..., description="Type of visit (e.g., Inpatient, Outpatient)")
    length_of_stay_hours: Optional[float] = Field(None, description="Length of stay in hours")
    city: Optional[str] = Field(None, description="Patient city")
    gender: Optional[str] = Field(None, description="Patient gender")
    insurance_provider: Optional[str] = Field(None, description="Insurance provider name")
    doctor_id: Optional[str] = Field(None, description="Attending doctor identifier")
    # Optional engineered/context features
    visit_frequency: Optional[float] = Field(None, description="Patient visit frequency")
    avg_length_of_stay_patient: Optional[float] = Field(None, description="Patient avg LOS")
    # Optional fields used by some trained models (e.g. align with fit-time schema)
    age: Optional[float] = Field(None, description="Patient age (used if model was trained with age)")
    chronic_flag: Optional[float] = Field(None, description="Chronic condition flag 0/1 (used if model was trained with it)")

    model_config = {"extra": "allow"}  # Allow extra fields for flexibility


class RiskPredictionResponse(BaseModel):
    """Response for visit risk prediction."""

    risk_score: RiskScore = Field(..., description="Predicted risk: Low, Medium, or High")
    probabilities: Optional[dict[str, float]] = Field(
        None, description="Class probabilities if model supports it"
    )
    model_version: str = Field(..., description="Model version used for prediction")
    request_id: Optional[str] = Field(None, description="Client-provided request id for tracing")


# --- Claim prediction (Claim Outcome Classification) ---
class ClaimPredictionRequest(BaseModel):
    """Features required for claim outcome classification (Model B)."""

    department: str = Field(..., description="Department code or name")
    billed_amount: float = Field(..., ge=0, description="Billed amount")
    approved_amount: Optional[float] = Field(None, ge=0, description="Approved amount if known")
    insurance_provider: str = Field(..., description="Insurance provider name")
    payment_days: Optional[float] = Field(None, ge=0, description="Payment delay in days")
    visit_type: Optional[str] = Field(None, description="Type of visit")
    length_of_stay_hours: Optional[float] = Field(None, ge=0, description="Length of stay in hours")
    city: Optional[str] = Field(None, description="Patient city")
    gender: Optional[str] = Field(None, description="Patient gender")
    # Optional engineered features
    revenue_realization_ratio: Optional[float] = Field(
        None, ge=0, le=1, description="approved_amount / billed_amount"
    )
    provider_rejection_rate: Optional[float] = Field(
        None, ge=0, le=1, description="Historical rejection rate for provider"
    )
    age: Optional[float] = Field(None, description="Patient age (used if model was trained with age)")
    chronic_flag: Optional[float] = Field(None, description="Chronic condition flag 0/1 (used if model was trained with it)")

    model_config = {"extra": "allow"}


class ClaimPredictionResponse(BaseModel):
    """Response for claim outcome prediction."""

    claim_status: ClaimStatus = Field(
        ..., description="Predicted status: Paid, Pending, or Rejected"
    )
    probabilities: Optional[dict[str, float]] = Field(
        None, description="Class probabilities if model supports it"
    )
    model_version: str = Field(..., description="Model version used for prediction")
    request_id: Optional[str] = Field(None, description="Client-provided request id for tracing")


# --- Batch (optional, for multiple predictions) ---
class RiskPredictionBatchRequest(BaseModel):
    """Batch of risk prediction requests."""

    requests: list[RiskPredictionRequest] = Field(..., max_length=100)
    request_id: Optional[str] = None


class RiskPredictionBatchResponse(BaseModel):
    """Batch of risk predictions."""

    predictions: list[RiskPredictionResponse]
    model_version: str
    request_id: Optional[str] = None


class ClaimPredictionBatchRequest(BaseModel):
    """Batch of claim prediction requests."""

    requests: list[ClaimPredictionRequest] = Field(..., max_length=100)
    request_id: Optional[str] = None


class ClaimPredictionBatchResponse(BaseModel):
    """Batch of claim predictions."""

    predictions: list[ClaimPredictionResponse]
    model_version: str
    request_id: Optional[str] = None


# --- Health ---
class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="ok or degraded")
    version: str = Field(..., description="API version")
    risk_model_loaded: bool = Field(..., description="Whether risk model is loaded")
    claim_model_loaded: bool = Field(..., description="Whether claim model is loaded")
    feature_schema_loaded: bool = Field(..., description="Whether feature schema is loaded")
