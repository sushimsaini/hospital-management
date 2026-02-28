# Drift Detection Report
**Generated:** 2026-02-27 23:44:22

## 1. Feature Distribution Analysis (K-S Test)
Comparing historical training data against recent production data.

| Feature                 |   Ref Mean |   Curr Mean |   P-Value | Status    |
|:------------------------|-----------:|------------:|----------:|:----------|
| billed_amount           |   20794.5  |    21175.7  |    0.0297 | ⚠️ ALERT  |
| length_of_stay_hours    |      19.58 |       19.43 |    0.362  | ✅ STABLE |
| age                     |      44.69 |       45.07 |    0.2547 | ✅ STABLE |
| days_since_registration |     -33.25 |      147.84 |    0      | ⚠️ ALERT  |

## 2. Summary & Recommendations
- **Action Required:** Significant drift detected in billing or clinical distributions. Trigger model retraining.
