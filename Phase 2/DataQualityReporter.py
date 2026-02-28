import pandas as pd
import numpy as np
from datetime import datetime

class DataQualityReporter:
    def __init__(self, patients_path, visits_path, billing_path):
        """Initializes the reporter by loading and merging datasets."""
        self.patients = pd.read_csv(patients_path)
        self.visits = pd.read_csv(visits_path)
        self.billing = pd.read_csv(billing_path)
        
        # Merge logic following the project schema
        self.df = self.visits.merge(self.patients, on='patient_id', how='left')
        self.df = self.df.merge(self.billing, on='visit_id', how='left')
        
        self.report_content = []

    def _get_outlier_count(self, series):
        """Helper to calculate outliers using the IQR method."""
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR
        return ((series < lower) | (series > upper)).sum(), lower, upper

    def generate_report(self, output_file="Data_Quality_Report.md"):
        """Compiles the statistical findings into a Markdown file."""
        
        # 1. Header
        self.report_content.append("# Phase 2: Data Quality & Reliability Report")
        self.report_content.append(f"**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # 2. Executive Summary
        self.report_content.append("## 1. Executive Summary")
        self.report_content.append(f"Total Records Analyzed: **{len(self.df):,}**")
        self.report_content.append("This report evaluates the completeness and validity of the hospital datasets.")

        # 3. Completeness Analysis
        self.report_content.append("\n## 2. Missing Value Analysis (Completeness)")
        self.report_content.append("| Field | Null Count | % Missing | Status |")
        self.report_content.append("| :--- | :--- | :--- | :--- |")
        
        for col in ['approved_amount', 'payment_days', 'length_of_stay_hours']:
            nulls = self.df[col].isnull().sum()
            pct = (nulls / len(self.df)) * 100
            status = "✅ OK" if pct < 1 else "⚠️ WARNING"
            self.report_content.append(f"| {col} | {nulls:,} | {pct:.2f}% | {status} |")

        # 4. Outlier Analysis
        self.report_content.append("\n## 3. Outlier Detection (Validity)")
        self.report_content.append("| Metric | Outlier Count | Lower Bound | Upper Bound |")
        self.report_content.append("| :--- | :--- | :--- | :--- |")
        
        for col in ['billed_amount', 'payment_days', 'length_of_stay_hours']:
            count, lb, ub = self._get_outlier_count(self.df[col].dropna())
            self.report_content.append(f"| {col} | {count:,} | {lb:,.2f} | {ub:,.2f} |")

        # 5. Distribution Analysis (Brief)
        self.report_content.append("\n## 4. Operational Distributions")
        top_dept = self.df['department'].value_counts().idxmax()
        top_provider = self.df['insurance_provider'].value_counts().idxmax()
        self.report_content.append(f"- **High Volume Department:** {top_dept}")
        self.report_content.append(f"- **Primary Insurance Provider:** {top_provider}")

        # Write to file
        with open(output_file, "w") as f:
            f.write("\n".join(self.report_content))
        
        print(f"✅ Report successfully generated: {output_file}")

# --- Execution ---
if __name__ == "__main__":
    # Ensure your CSV files are in the same folder
    reporter = DataQualityReporter('patients.csv', 'visits.csv', 'billing.csv')
    reporter.generate_report("Data_Quality_Report.md")