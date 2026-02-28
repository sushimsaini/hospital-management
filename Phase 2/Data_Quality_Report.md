# Phase 2: Data Quality & Reliability Report
**Generated on:** 2026-02-27 12:11:09

## 1. Executive Summary
Total Records Analyzed: **25,000**
This report evaluates the completeness and validity of the hospital datasets.

## 2. Missing Value Analysis (Completeness)
| Field | Null Count | % Missing | Status |
| :--- | :--- | :--- | :--- |
| approved_amount | 1,318 | 5.27% | ⚠️ WARNING |
| payment_days | 790 | 3.16% | ⚠️ WARNING |
| length_of_stay_hours | 0 | 0.00% | ✅ OK |

## 3. Outlier Detection (Validity)
| Metric | Outlier Count | Lower Bound | Upper Bound |
| :--- | :--- | :--- | :--- |
| billed_amount | 373 | -13,640.97 | 53,621.49 |
| payment_days | 509 | -5.50 | 30.50 |
| length_of_stay_hours | 256 | -16.07 | 53.34 |

## 4. Operational Distributions
- **High Volume Department:** General
- **Primary Insurance Provider:** MediCareX