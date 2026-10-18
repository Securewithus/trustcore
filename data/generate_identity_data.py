"""
Generates a simulated identity document dataset for TrustCore's
identity verification module. Mimics common document-fraud signals
without using any real personal data.
"""
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

random.seed(7)
np.random.seed(7)

N_DOCS = 800
FRAUD_RATE = 0.06

doc_types = ["Aadhaar", "PAN", "Passport", "Driving License", "Voter ID"]


def random_date(start_year, end_year):
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days))


rows = []
for i in range(N_DOCS):
    is_fraud = random.random() < FRAUD_RATE
    doc_type = random.choice(doc_types)
    issue_date = random_date(2015, 2024)

    if is_fraud:
        # Fraud patterns: expiry before issue, face mismatch, font/metadata inconsistency,
        # or a document number that fails a simple checksum-like rule
        fraud_pattern = random.choice(["expiry_before_issue", "face_mismatch", "font_inconsistency", "invalid_number_format"])
        expiry_date = issue_date - timedelta(days=random.randint(30, 400)) if fraud_pattern == "expiry_before_issue" else issue_date + timedelta(days=365 * random.randint(5, 10))
        face_match_score = round(np.random.uniform(0.2, 0.55), 2) if fraud_pattern == "face_mismatch" else round(np.random.uniform(0.85, 0.99), 2)
        font_consistency_score = round(np.random.uniform(0.2, 0.5), 2) if fraud_pattern == "font_inconsistency" else round(np.random.uniform(0.85, 1.0), 2)
        doc_number_valid = 0 if fraud_pattern == "invalid_number_format" else 1
    else:
        fraud_pattern = "none"
        expiry_date = issue_date + timedelta(days=365 * random.randint(5, 10))
        face_match_score = round(np.random.uniform(0.85, 0.99), 2)
        font_consistency_score = round(np.random.uniform(0.85, 1.0), 2)
        doc_number_valid = 1

    rows.append({
        "document_id": f"DOC{i:05d}",
        "doc_type": doc_type,
        "issue_date": issue_date.date().isoformat(),
        "expiry_date": expiry_date.date().isoformat(),
        "face_match_score": face_match_score,        # similarity between ID photo and live selfie
        "font_consistency_score": font_consistency_score,  # OCR/forensic font-uniformity signal
        "doc_number_valid": doc_number_valid,          # passes basic format/checksum validation
        "is_fraud_actual": int(is_fraud),
        "fraud_pattern_actual": fraud_pattern,
    })

df = pd.DataFrame(rows)
df.to_csv("identity_documents.csv", index=False)
print(f"Generated {len(df)} documents, {df['is_fraud_actual'].sum()} planted fraud cases")
print(df["fraud_pattern_actual"].value_counts())
