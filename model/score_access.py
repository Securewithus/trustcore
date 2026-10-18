"""
TrustCore access anomaly scoring engine.
Same hybrid ML + rules pattern as the transaction and identity engines,
applied to employee access logs for insider-threat detection.
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "rules"))
from access_rule_logic import evaluate_access_rules

FEATURE_COLS = ["login_hour", "files_ratio", "new_device", "failed_login_attempts"]


def add_derived_features(df):
    df = df.copy()
    df["files_ratio"] = df["files_accessed"] / df["usual_files_per_session"].replace(0, 1)
    return df


def train_model(df):
    df = add_derived_features(df)
    features = df[FEATURE_COLS]
    model = IsolationForest(contamination=0.05, random_state=42, n_estimators=200)
    model.fit(features)
    raw_scores = model.decision_function(features)
    score_range = (raw_scores.min(), raw_scores.max())
    return model, features, score_range


def ml_trust_component(model, features, score_range):
    raw_scores = model.decision_function(features)
    lo, hi = score_range
    normalized = (raw_scores - lo) / (hi - lo + 1e-9)
    return np.clip(normalized, 0, 1)


def score_access_events(df):
    df = add_derived_features(df)
    model, features, score_range = train_model(df)
    ml_component = ml_trust_component(model, features, score_range)

    rule_penalties = []
    rule_reasons = []
    for _, row in df.iterrows():
        penalty, reasons = evaluate_access_rules(row)
        rule_penalties.append(penalty)
        rule_reasons.append(reasons)
    rule_penalties = np.array(rule_penalties)

    hybrid = 0.6 * ml_component + 0.4 * (1 - rule_penalties)
    trust_score = (hybrid * 100).round(1)

    df["trust_score"] = trust_score
    df["rule_reasons"] = rule_reasons
    df["flag"] = df["trust_score"].apply(
        lambda s: "high_risk" if s < 40 else ("review" if s < 70 else "trusted")
    )
    df["explanation"] = df["rule_reasons"].apply(
        lambda r: "; ".join(r) if r else "No access anomalies detected"
    )
    return df


if __name__ == "__main__":
    df = pd.read_csv(os.path.join(os.path.dirname(__file__), "..", "data", "access_logs.csv"))
    scored = score_access_events(df)

    print("\n--- Score distribution ---")
    print(scored["flag"].value_counts())

    print("\n--- Sample high-risk access events ---")
    print(scored[scored["flag"] == "high_risk"][
        ["event_id", "employee_id", "trust_score", "explanation", "is_anomaly_actual"]
    ].head(10).to_string(index=False))

    caught = scored[(scored["flag"] == "high_risk") & (scored["is_anomaly_actual"] == 1)].shape[0]
    total = scored["is_anomaly_actual"].sum()
    print(f"\nCaught {caught}/{total} planted anomalies as high_risk ({caught/total*100:.0f}%)")

    scored.to_csv(os.path.join(os.path.dirname(__file__), "..", "data", "scored_access_logs.csv"), index=False)
    print("Saved scored_access_logs.csv")
