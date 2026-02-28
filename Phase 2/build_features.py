import pandas as pd
import numpy as np

def load_and_merge_data(patients_path, visits_path, billing_path):
    """Loads CSVs and merges them into a single analytical base table."""
    patients = pd.read_csv(patients_path)
    visits = pd.read_csv(visits_path)
    billing = pd.read_csv(billing_path)

    # Convert date columns to datetime objects
    patients['registration_date'] = pd.to_datetime(patients['registration_date'])
    visits['visit_date'] = pd.to_datetime(visits['visit_date'])
    billing['billing_date'] = pd.to_datetime(billing['billing_date'])

    # Merge: Patients -> Visits -> Billing
    df = pd.merge(visits, patients, on='patient_id', how='left')
    df = pd.merge(df, billing, on='visit_id', how='left')
    
    return df

def engineer_features(df):
    """Applies business logic to create predictive features."""
    
    # 1. Patient Frequency: How many times has this patient visited the hospital?
    df['patient_visit_count'] = df.groupby('patient_id')['visit_id'].transform('count')

    # 2. Patient History: Average Length of Stay (LoS) for this patient across all visits
    df['avg_los_per_patient'] = df.groupby('patient_id')['length_of_stay_hours'].transform('mean')

    # 3. Provider Reliability: Rejection Rate for each insurance provider
    # Logic: (Count of Rejected Claims / Total Claims) per provider
    rejection_rates = df.groupby('insurance_provider')['claim_status'].apply(
        lambda x: (x == 'Rejected').mean()
    ).reset_index()
    rejection_rates.columns = ['insurance_provider', 'provider_rejection_rate']
    df = pd.merge(df, rejection_rates, on='insurance_provider', how='left')

    # 4. Loyalty/Tenure: Days since the patient first registered at the hospital
    df['days_since_registration'] = (df['visit_date'] - df['registration_date']).dt.days

    # 5. Time-based Features (Seasonality/Peak Times)
    df['visit_month'] = df['visit_date'].dt.month
    df['visit_day_of_week'] = df['visit_date'].dt.dayofweek
    
    return df

def handle_missing_and_clean(df):
    """Final cleaning before saving the modeling table."""
    # Fill missing approved amounts with 0 for rejected/pending claims
    df['approved_amount'] = df['approved_amount'].fillna(0)
    
    # Fill missing payment_days with a flag or mean (here using median)
    df['payment_days'] = df['payment_days'].fillna(df['payment_days'].median())
    
    return df

def main():
    print("Starting Feature Engineering Pipeline...")
    
    # Load
    df = load_and_merge_data('patients.csv', 'visits.csv', 'billing.csv')
    
    # Transform
    df = engineer_features(df)
    
    # Clean
    df = handle_missing_and_clean(df)
    
    # Export
    output_path = 'model_table.csv'
    df.to_csv(output_path, index=False)
    
    print(f"Success! Modeling dataset saved to: {output_path}")
    print(f"Features created: {len(df.columns)} total columns.")

if __name__ == "__main__":
    main()