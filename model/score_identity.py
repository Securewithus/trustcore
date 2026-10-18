"""
TrustCore identity verification scoring engine.
Same hybrid approach as the transaction engine: Isolation Forest anomaly
detection + explicit rule logic, producing an explainable 0-100 trust score.
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import sys
import os
from datetime import date

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "rules"))
from identity_rule_logic import evaluate_identity_rules

FEATURE_COLS = ["face_match_score", "font_consistency_score", "doc_number_valid", "validity_days"]


def add_derived_features(df):
    df = df.copy()
    issue = pd.to_datetime(df["issue_date"])
    expiry = pd.to_datetime(df["expiry_date"])
    df["validity_days"] = (expiry - issue).dt.days  # negative = red flag, handled by rules too
    return df


def train_model(df):
    df = add_derived_features(df)
    features = df[FEATURE_COLS]
    model = IsolationForest(contamination=0.06, random_state=42, n_estimators=200)
    model.fit(features)
    raw_scores = model.decision_function(features)
    score_range = (raw_scores.min(), raw_scores.max())
    return model, features, score_range


def ml_trust_component(model, features, score_range):
    raw_scores = model.decision_function(features)
    lo, hi = score_range
    normalized = (raw_scores - lo) / (hi - lo + 1e-9)
    return np.clip(normalized, 0, 1)


def score_documents(df):
    df = add_derived_features(df)
    model, features, score_range = train_model(df)
    ml_component = ml_trust_component(model, features, score_range)

    rule_penalties = []
    rule_reasons = []
    for _, row in df.iterrows():
        penalty, reasons = evaluate_identity_rules(row)
        rule_penalties.append(penalty)
        rule_reasons.append(reasons)
    rule_penalties = np.array(rule_penalties)

    hybrid = 0.5 * ml_component + 0.5 * (1 - rule_penalties)
    trust_score = (hybrid * 100).round(1)

    df["trust_score"] = trust_score
    df["rule_reasons"] = rule_reasons
    df["flag"] = df["trust_score"].apply(
        lambda s: "high_risk" if s < 40 else ("review" if s < 70 else "trusted")
    )
    df["explanation"] = df["rule_reasons"].apply(
        lambda r: "; ".join(r) if r else "No document anomalies detected"
    )
    return df


if __name__ == "__main__":
    df = pd.read_csv(os.path.join(os.path.dirname(__file__), "..", "data", "identity_documents.csv"))
    scored = score_documents(df)

    print("\n--- Score distribution ---")
    print(scored["flag"].value_counts())

    print("\n--- Sample high-risk documents ---")
    print(scored[scored["flag"] == "high_risk"][
        ["document_id", "doc_type", "trust_score", "explanation", "is_fraud_actual"]
    ].head(10).to_string(index=False))

    caught = scored[(scored["flag"] == "high_risk") & (scored["is_fraud_actual"] == 1)].shape[0]
    total_fraud = scored["is_fraud_actual"].sum()
    print(f"\nCaught {caught}/{total_fraud} planted fraud documents as high_risk ({caught/total_fraud*100:.0f}%)")

    scored.to_csv(os.path.join(os.path.dirname(__file__), "..", "data", "scored_identity_documents.csv"), index=False)
    print("Saved scored_identity_documents.csv")
