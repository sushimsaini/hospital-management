-- Tables DDL Starts --


-- 1. Create Patients Table
CREATE TABLE patients (
    patient_id INTEGER PRIMARY KEY,
    age INTEGER NOT NULL,
    gender VARCHAR(10),
    city VARCHAR(100),
    insurance_provider VARCHAR(100),
    chronic_flag INTEGER, -- Using INTEGER to represent Boolean (0 or 1)
    registration_date DATE NOT NULL
);

-- 2. Create Visits Table
CREATE TABLE visits (
    visit_id INTEGER PRIMARY KEY,
    patient_id INTEGER NOT NULL,
    visit_date DATE NOT NULL,
    department VARCHAR(100),
    visit_type VARCHAR(50),
    length_of_stay_hours DECIMAL(10, 2),
    risk_score VARCHAR(20),
    doctor_id INTEGER,
    CONSTRAINT fk_patient
        FOREIGN KEY (patient_id) 
        REFERENCES patients(patient_id)
);

-- 3. Create Billing Table
CREATE TABLE billing (
    bill_id INTEGER PRIMARY KEY,
    visit_id INTEGER NOT NULL,
    billed_amount DECIMAL(15, 2),
    approved_amount DECIMAL(15, 2),
    claim_status VARCHAR(50),
    payment_days INTEGER,
    billing_date DATE,
    CONSTRAINT fk_visit
        FOREIGN KEY (visit_id) 
        REFERENCES visits(visit_id)
);

-- DDL Ends --

-- Index DDL starts --

-- Optimizes time-series analysis and date-based filtering
CREATE INDEX idx_visit_date ON visits(visit_date);

-- Optimizes departmental efficiency and volume reporting
CREATE INDEX idx_department ON visits(department);

-- Optimizes financial analysis by insurance provider
CREATE INDEX idx_insurance_provider ON patients(insurance_provider);

-- Optimizes revenue leakage analysis and claim status monitoring
CREATE INDEX idx_claim_status ON billing(claim_status);

-- Index DDL Ends --