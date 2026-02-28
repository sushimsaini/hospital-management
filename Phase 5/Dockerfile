# Phase 5 - Hospital Prediction API
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application and artifacts
COPY api ./api
COPY artifacts ./artifacts
COPY models ./models

ENV PYTHONPATH=/app
ENV MODELS_DIR=/app/models
ENV ARTIFACTS_DIR=/app/artifacts

EXPOSE 8000

# Run with uvicorn; use 1 worker for simplicity (scale via replicas)
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
