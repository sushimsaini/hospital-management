#!/usr/bin/env python3
"""
Inspect the visit_risk_model.pkl artifact: type, predict/predict_proba, classes_.
Run from project root: python scripts/inspect_risk_model.py
"""
import sys
from pathlib import Path

# Allow importing api.config from project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from api.config import RISK_MODEL_PATH


def main():
    if not RISK_MODEL_PATH.exists():
        print(f"File not found: {RISK_MODEL_PATH}")
        return 1
    # Try joblib first (common for sklearn models); fall back to pickle for .pkl from pickle.dump()
    try:
        import joblib
        obj = joblib.load(RISK_MODEL_PATH)
        print("(loaded with joblib)")
    except Exception:
        import pickle
        with open(RISK_MODEL_PATH, "rb") as f:
            obj = pickle.load(f)
        print("(loaded with pickle)")
    print(f"Path: {RISK_MODEL_PATH}")
    print(f"Type: {type(obj).__module__}.{type(obj).__name__}")
    if isinstance(obj, dict):
        print(f"Keys: {list(obj.keys())}")
        if "model" in obj:
            m = obj["model"]
            print(f"  obj['model'] type: {type(m).__module__}.{type(m).__name__}")
            print(f"  has predict: {hasattr(m, 'predict')}")
            print(f"  has predict_proba: {hasattr(m, 'predict_proba')}")
            if hasattr(m, "classes_"):
                print(f"  classes_: {getattr(m, 'classes_', None)}")
    else:
        print(f"has predict: {hasattr(obj, 'predict')}")
        print(f"has predict_proba: {hasattr(obj, 'predict_proba')}")
        if hasattr(obj, "classes_"):
            print(f"classes_: {getattr(obj, 'classes_', None)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
