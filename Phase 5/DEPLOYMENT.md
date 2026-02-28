# Phase 5 – Deployment and Operations Guide

This guide covers running the **Hospital Prediction API** locally and with Docker, plus sample requests and responses for health checks and predictions.

---

## 1. Prerequisites

- **Python 3.10+** (for local run)
- **Docker** (optional, for containerized run)
- **Model artifacts from Phase 3** (optional): place `visit_risk_model.pkl` and `claim_outcome_model.pkl` in `models/` for real predictions. Without them, the API runs in fallback mode (default risk: Low, claim: Pending).

---

## 2. Running Locally

### 2.1 Create and activate a virtual environment

```bash
cd /path/to/Capstone
python3 -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
```

### 2.2 Install dependencies

```bash
pip install -r requirements.txt
```

### 2.3 Set Python path and start the server

From the **project root** (the folder containing `api/`, `models/`, `artifacts/`):

```bash
export PYTHONPATH=.   # Linux/macOS
# On Windows CMD: set PYTHONPATH=.
# On Windows PowerShell: $env:PYTHONPATH = "."

uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

- **API base URL:** `http://localhost:8000`
- **Interactive docs:** `http://localhost:8000/docs`
- **Health check:** `http://localhost:8000/health`

### 2.4 (Optional) Place model artifacts

Copy your Phase 3 outputs into the project:

- `models/visit_risk_model.pkl`
- `models/claim_outcome_model.pkl`
- `artifacts/feature_schema.json` (already provided; override if your Phase 3 schema differs)

Restart the server after adding or changing artifacts.

---

## 3. Running with Docker

### 3.1 Build the image

From the **project root**:

```bash
docker build -t hospital-prediction-api:latest .
```

### 3.2 Run the container

```bash
docker run -p 8000:8000 hospital-prediction-api:latest
```

- API: `http://localhost:8000`
- Docs: `http://localhost:8000/docs`

### 3.3 Mount models and artifacts (recommended)

If your models live on the host, mount them so the container uses the same files:

```bash
docker run -p 8000:8000 \
  -v "$(pwd)/models:/app/models" \
  -v "$(pwd)/artifacts:/app/artifacts" \
  hospital-prediction-api:latest
```

### 3.4 Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MODELS_DIR` | `/app/models` | Directory containing `.pkl` model files |
| `ARTIFACTS_DIR` | `/app/artifacts` | Directory containing `feature_schema.json` |
| `RISK_MODEL_FILENAME` | `visit_risk_model.pkl` | Risk model filename |
| `CLAIM_MODEL_FILENAME` | `claim_outcome_model.pkl` | Claim model filename |
| `FEATURE_SCHEMA_FILENAME` | `feature_schema.json` | Feature schema filename |
| `RISK_MODEL_VERSION` | `1.0.0` | Risk model version (for logging) |
| `CLAIM_MODEL_VERSION` | `1.0.0` | Claim model version (for logging) |
| `LOG_PREDICTIONS` | `true` | Set to `false` to disable prediction logging |

Example with custom paths and versions:

```bash
docker run -p 8000:8000 \
  -e RISK_MODEL_VERSION=1.1.0 \
  -e CLAIM_MODEL_VERSION=1.1.0 \
  -v "$(pwd)/models:/app/models" \
  -v "$(pwd)/artifacts:/app/artifacts" \
  hospital-prediction-api:latest
```

---

## 4. API Endpoints Summary

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Service info and links |
| GET | `/health` | Health check (models + schema loaded) |
| GET | `/live` | Simple liveness probe |
| POST | `/predict/risk` | Single visit risk prediction |
| POST | `/predict/claim` | Single claim outcome prediction |
| POST | `/predict/risk/batch` | Batch risk predictions (max 100) |
| POST | `/predict/claim/batch` | Batch claim predictions (max 100) |

---

## 5. Sample Request and Response

### 5.1 Health check

**Request**

```http
GET /health HTTP/1.1
Host: localhost:8000
```

**Response (200)**

```json
{
  "status": "ok",
  "version": "1.0.0",
  "risk_model_loaded": true,
  "claim_model_loaded": true,
  "feature_schema_loaded": true
}
```

If one or both models are missing, `status` is `"degraded"` and the corresponding `*_loaded` flags are `false`.

---

### 5.2 Visit risk prediction (Model A)

**Request**

```http
POST /predict/risk HTTP/1.1
Host: localhost:8000
Content-Type: application/json
X-Request-ID: req-abc-001

{
  "department": "Cardiology",
  "visit_type": "Inpatient",
  "length_of_stay_hours": 72.5,
  "city": "Boston",
  "gender": "F",
  "insurance_provider": "Blue Cross",
  "visit_frequency": 2.0,
  "avg_length_of_stay_patient": 48.0
}
```

**Response (200)**

```json
{
  "risk_score": "High",
  "probabilities": {
    "Low": 0.1,
    "Medium": 0.25,
    "High": 0.65
  },
  "model_version": "1.0.0",
  "request_id": "req-abc-001"
}
```

`risk_score` is one of: `"Low"`, `"Medium"`, `"High"`. `probabilities` may be `null` if the model does not expose them. The example above is illustrative; actual scores and probabilities depend on your trained model and input. If you get `"Low"` with `probabilities: null`, see `docs/RCA_risk_prediction_low_null.md` for root cause analysis.

---

### 5.3 Claim outcome prediction (Model B)

**Request**

```http
POST /predict/claim HTTP/1.1
Host: localhost:8000
Content-Type: application/json
X-Request-ID: req-claim-002

{
  "department": "Emergency",
  "billed_amount": 5000.0,
  "approved_amount": 4200.0,
  "insurance_provider": "Aetna",
  "payment_days": 45.0,
  "visit_type": "Emergency",
  "length_of_stay_hours": 8.0,
  "city": "Chicago",
  "revenue_realization_ratio": 0.84,
  "provider_rejection_rate": 0.12
}
```

**Response (200)**

```json
{
  "claim_status": "Paid",
  "probabilities": {
    "Paid": 0.78,
    "Pending": 0.15,
    "Rejected": 0.07
  },
  "model_version": "1.0.0",
  "request_id": "req-claim-002"
}
```

`claim_status` is one of: `"Paid"`, `"Pending"`, `"Rejected"`.

---

### 5.4 Validation errors (422)

Invalid payloads (e.g. missing required fields or wrong types) return **422 Unprocessable Entity** with a Pydantic error body, for example:

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "department"],
      "msg": "Field required"
    }
  ]
}
```

---

## 6. Prediction Logging (Audit and Governance)

When `LOG_PREDICTIONS=true` (default), each prediction is logged with:

- **timestamp** (UTC ISO)
- **model_name** (`risk_model` or `claim_model`)
- **model_version**
- **request_id** (from header or body if provided)
- **input_feature_hash** (SHA-256 of canonicalized input, first 16 chars)
- **prediction** (class label)
- **probabilities** (if available)

Logs go to stdout in the configured format (e.g. `%(message)s` and `extra`). For production, configure your logging stack to capture stdout and optionally forward to a central store for audit and monitoring.

---

## 7. Operations Runbook (Summary)

| Task | Action |
|------|--------|
| **Deploy new model** | Replace `visit_risk_model.pkl` or `claim_outcome_model.pkl` in `models/`, update `RISK_MODEL_VERSION` / `CLAIM_MODEL_VERSION` if desired, restart API. |
| **Update feature schema** | Replace `artifacts/feature_schema.json`, restart API. |
| **Disable prediction logging** | Set `LOG_PREDICTIONS=false`. |
| **Scale** | Run multiple containers (e.g. behind a load balancer); use `/health` for readiness and `/live` for liveness. |
| **Troubleshoot** | Check `/health` for model/schema load status; inspect logs for `prediction_log` and stack traces. |

---

## 8. Quick reference

**Local (from project root):**

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=.
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**Docker:**

```bash
docker build -t hospital-prediction-api:latest .
docker run -p 8000:8000 -v "$(pwd)/models:/app/models" -v "$(pwd)/artifacts:/app/artifacts" hospital-prediction-api:latest
```

Then open **http://localhost:8000/docs** for interactive requests.
