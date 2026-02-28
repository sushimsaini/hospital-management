# Governance & Compliance Document
**Status:** Active | **System:** Hospital Revenue Risk Platform

## 1. Automated Validation Checks
The system implements real-time validation for every incoming record:
- **Null Check:** Critical fields (Age, Billed Amount, Chronic Flag) must not be empty.
- **Range Check:** Age must be [0-120]. Billed Amount must be > 0.
- **Logic Check:** Length of Stay cannot be negative.

## 2. Model Audit & Traceability
- **Audit Logging:** Every prediction is timestamped and logged in `hospital_ai_audit.log`.
- **Version Control:** Current production model: `v1.0.0_RandomForest`.
- **Model Card:** Documentation of training data and feature schema is stored in Phase 4 artifacts.

## 3. Retraining Strategy & Assumptions
- **Assumption:** Insurance provider rejection logic is based on the previous 12 months.
- **Scheduled Retraining:** Every 6 months.
- **Immediate Retraining:** Triggered if P-Value of `billed_amount` drift drops below 0.05 for 7 consecutive days.

## 4. Compliance & Ethics
- **Anonymization:** No Patient Names, IDs, or SSNs are processed by the modeling layer.
- **Fairness:** Accuracy is monitored across Gender and City demographics to ensure equitable clinical risk assessment.
