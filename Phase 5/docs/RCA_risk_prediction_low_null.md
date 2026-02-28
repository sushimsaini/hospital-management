# RCA: Risk prediction returns "Low" with `probabilities: null`

## Symptom

For a valid request to `POST /predict/risk` (e.g. the sample in DEPLOYMENT.md), the API returns:

```json
{
  "risk_score": "Low",
  "probabilities": null,
  "model_version": "1.0.0",
  "request_id": "req-abc-001"
}
```

instead of an example with a non-Low score and probabilities populated.

---

## Root cause analysis

The same response can be produced by **three different causes**. Use the checks below to identify which one applies.

### 1. Fallback mode (model not loaded)

**Cause:** The risk model is never loaded, so the API returns the hard-coded fallback: `risk_score: "Low"`, `probabilities: null`.

This happens when:

- **File not found:** `visit_risk_model.pkl` is missing from `models/` or `MODELS_DIR` points elsewhere (e.g. wrong working directory when starting the server).
- **Load failure:** `pickle.load()` raises (e.g. missing class at unpickle time, Python version mismatch, corrupted file). The exception is logged and the in-memory model stays `None`, so every request gets the fallback.

**Check:**

- Call `GET /health`. If `risk_model_loaded` is `false`, the service considers the risk model file missing (it only checks **file existence**, not successful load).
- Inspect server logs when the first risk prediction runs. Look for:
  - `"Risk model file not found at ..."`
  - `"Failed to load risk model: ..."` (with stack trace).

**Note:** Health currently reports `risk_model_loaded=true` only if the file exists. If the file exists but unpickling fails on first use, health can still be “ok” while predictions use fallback.

---

### 2. Loaded artifact has no `predict_proba`

**Cause:** The object loaded from `visit_risk_model.pkl` has `.predict()` but not `.predict_proba()`. The code then returns the real prediction label and `probabilities: null`.

Common cases:

- Artifact is a **dict** (e.g. `{"model": <estimator>, "encoder": ...}`). The API calls `model.predict()` / `model.predict_proba()` on the dict, which doesn’t have those methods; if there’s a wrapper that only implements `predict`, you get a label and null probs.
- Artifact is a **custom wrapper** or an estimator that doesn’t support `predict_proba` (e.g. certain ensembles or external libs).
- Artifact is a **Pipeline** whose last step doesn’t expose `predict_proba`.

**Check:**

- Run the inspection script (see below) to see the type of the pickled object and whether it has `predict_proba`.
- In code, after load, the service uses `hasattr(model, "predict_proba")`; if that’s `False`, probabilities stay `null`.

---

### 3. Feature mismatch or model behavior

**Cause:** The model is loaded and has `predict_proba`, but:

- **Feature mismatch:** Training used different columns, order, or preprocessing (e.g. one-hot encoding, scaling). The API sends raw request features; if the saved model is a **bare estimator** expecting already-transformed features, predictions can be wrong or unstable. If it’s a **full Pipeline** (e.g. ColumnTransformer + classifier) fitted on the same schema, this is less likely.
- **Model actually predicts Low:** For the given input, the model’s decision is “Low” risk. The DEPLOYMENT.md example (High with probabilities) is **illustrative**; real output depends on the trained model and data.

**Check:**

- Confirm how Phase 3 saved the model (bare estimator vs Pipeline, which columns, which encoding). Align API feature building and schema with that.
- Run the same request through your training/eval script and compare with the API.

---

## How to inspect the pickled risk model

Run from project root (with the same venv as the API):

```bash
cd /Users/Sushim_Saini/Documents/Capstone
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
python scripts/inspect_risk_model.py
```

This script prints the type of the loaded object, whether it has `predict` / `predict_proba`, and (if applicable) `classes_`, so you can confirm cause (1) vs (2) vs (3).

---

## Summary

| Observation              | Likely cause                                      |
|--------------------------|---------------------------------------------------|
| `risk_model_loaded: false` or load errors in logs | Fallback: model not loaded (cause 1)             |
| `risk_model_loaded: true`, no errors, still null probs | Artifact has no `predict_proba` (cause 2)        |
| Probs non-null but score always Low for this input    | Feature mismatch or model behavior (cause 3)    |

The DEPLOYMENT.md sample response is an example only; the actual response is determined by whether the model loads, the artifact’s interface, and the trained model’s behavior on the given features.
