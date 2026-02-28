import pandas as pd
import numpy as np
import os
from datetime import datetime
from scipy.stats import ks_2samp

class GovernanceEngine:
    def __init__(self, data_path='model_table.csv'):
        self.data_path = data_path
        self.reference_data = None
        self.current_data = None
        
    def prepare_data(self):
        """Loads data and simulates a reference (train) and current (prod) split."""
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Missing {self.data_path}. Ensure it is in the directory.")
        
        df = pd.read_csv(self.data_path)
        df['visit_date'] = pd.to_datetime(df['visit_date'])
        df = df.sort_values('visit_date')
        
        # Simulating Reference (first 80%) and Current (latest 20%)
        split_idx = int(len(df) * 0.8)
        self.reference_data = df.iloc[:split_idx]
        self.current_data = df.iloc[split_idx:]
        return True

    def run_drift_detection(self):
        """Performs K-S test on numerical features to detect distribution shifts."""
        metrics = []
        features_to_check = ['billed_amount', 'length_of_stay_hours', 'age', 'days_since_registration']
        
        for feature in features_to_check:
            stat, p_value = ks_2samp(self.reference_data[feature].dropna(), 
                                     self.current_data[feature].dropna())
            drift_status = "⚠️ ALERT" if p_value < 0.05 else "✅ STABLE"
            metrics.append({
                'Feature': feature,
                'Ref Mean': round(self.reference_data[feature].mean(), 2),
                'Curr Mean': round(self.current_data[feature].mean(), 2),
                'P-Value': round(p_value, 4),
                'Status': drift_status
            })
            
        return pd.DataFrame(metrics)

    def generate_drift_report(self, drift_df):
        """Generates the Drift Detection Report markdown file."""
        report_path = "drift_report.md"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        md_content = f"# Drift Detection Report\n"
        md_content += f"**Generated:** {timestamp}\n\n"
        md_content += "## 1. Feature Distribution Analysis (K-S Test)\n"
        md_content += "Comparing historical training data against recent production data.\n\n"
        md_content += drift_df.to_markdown(index=False)
        md_content += "\n\n## 2. Summary & Recommendations\n"
        
        if (drift_df['Status'] == "⚠️ ALERT").any():
            md_content += "- **Action Required:** Significant drift detected in billing or clinical distributions. Trigger model retraining.\n"
        else:
            md_content += "- **Status:** Data distributions remain within safe operational bounds.\n"
            
        with open(report_path, "w") as f:
            f.write(md_content)
        print(f"Generated: {report_path}")

    def generate_governance_doc(self):
        """Generates the Governance and Compliance document."""
        doc_path = "governance_policy.md"
        
        gov_content = """# Governance & Compliance Document
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
"""
        with open(doc_path, "w") as f:
            f.write(gov_content)
        print(f"Generated: {doc_path}")

if __name__ == "__main__":
    engine = GovernanceEngine()
    if engine.prepare_data():
        drift_results = engine.run_drift_detection()
        engine.generate_drift_report(drift_results)
        engine.generate_governance_doc()
        print("\nPhase 6 Compliance and Monitoring suite execution complete.")