# Project Report: Hospital Operations & Revenue Risk Intelligence Platform

## Executive Summary
This project outlines the development of an end-to-end analytics and machine learning ecosystem designed for modern healthcare environments. The platform addresses clinical bottlenecks by predicting patient risk levels and mitigates financial losses by forecasting insurance claim rejections. By integrating disparate data sources, the system provides a unified interface for operational efficiency and revenue stability.

---

## Phase 1: Data Integration & Structural Foundation
**Objective:** Create a unified master dataset from siloed relational tables.

- **Core Tables:** `patients.csv` (Demographics), `visits.csv` (Clinical encounters), and `billing.csv` (Financial records).
- **Key Operations:** Implementing robust joins using `visit_id` and `patient_id` to ensure a one-to-one relationship between clinical visits and their financial outcomes.
- **Result:** A comprehensive data warehouse structure capable of supporting both clinical and financial longitudinal analysis.

---

## Phase 2: Exploratory Data Analysis (EDA) & Data Quality
**Objective:** Profile the data to ensure reliability and uncover operational trends.

- **Data Cleansing:**
    - Addressed "pre-registration visits" by capping tenure features at zero.
    - Standardized date formats to ISO 8601.
    - Performed median imputation for missing payment cycles.
- **Key Findings:**
    - **Departmental Risk:** Cardiology and ICU were identified as high-intensity zones with the highest average length of stay.
    - **Insurance Volatility:** Specific payers demonstrated significantly higher rejection rates, identifying them as high-priority for pre-submission audits.
- **Deliverable:** `Data_Quality_Report.md`

---

## Phase 3: Predictive Modeling
**Objective:** Build high-performance classifiers for real-time decision support.

- **Model A (Visit Risk):** A Random Forest Classifier that categorizes incoming visits into High, Medium, or Low risk.
    - **Primary Features:** Chronic flag, age, and previous visit frequency.
- **Model B (Claim Outcome):** A Random Forest Classifier that predicts if a claim will be Paid, Pending, or Rejected.
    - **Primary Features:** Billed amount, insurance provider history, and provider rejection rates.
- **Temporal Integrity:** Applied an 80/20 Time-Based Split to prevent "look-ahead" bias, ensuring the models are tested on the most recent chronological data.

---

## Phase 4: Evaluation & Explainability
**Objective:** Quantify model impact and ensure clinical transparency.

- **Metrics:** Utilized Precision-Recall curves and F1-scores to optimize for "High Risk" identification, ensuring critical clinical cases are not overlooked.
- **Explainability:** Developed Feature Importance summaries to provide clinicians with the "Why" behind AI predictions (e.g., identifying that 'Length of Stay' is the leading driver of clinical risk).
- **Fairness:** Performed accuracy audits across Gender and City demographics to ensure equitable model performance.
- **Deliverables:** `Risk_Model_Evaluation.md`, `Claim_Model_Evaluation.md`, and `Explainability_Summary.md`.

---

## Phase 5: Deployment & Integration
**Objective:** Deploy models as production-ready microservices.

- **Architecture:** Developed a FastAPI interface that allows hospital EHR (Electronic Health Record) systems to send patient data and receive instant risk scores.
- **Functionality:** Built endpoints for single-visit inference and batch processing, allowing the hospital to scale the tool across multiple departments.

---

## Phase 6: Monitoring, Drift Detection, & Governance
**Objective:** Ensure the system remains safe, accurate, and compliant over time.

- **Data Validation:** Implemented "Safety Gates" to block invalid data entries (e.g., negative billing amounts or impossible age ranges).
- **Drift Tracking:** Utilized the Kolmogorov-Smirnov (K-S) test to detect shifts in patient demographics or insurance behaviors that might require model retraining.
- **Governance:** Established formal policies for HIPAA-aligned data privacy and a human-in-the-loop protocol for high-risk clinical escalations.
- **Deliverables:** `drift_report.md` and `governance.md`.

---

## Final Outcome & Business Value
The platform transitions the hospital from a reactive stance to a proactive strategy.

- **Operational Value:** Optimizes ICU/ER staffing by forecasting high-risk arrivals.
- **Financial Value:** Protects revenue by identifying likely rejections before the claim is submitted to the payer.
- **Compliance Value:** Provides a fully auditable trail of AI-assisted decisions, meeting healthcare regulatory standards.
