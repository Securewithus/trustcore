import os
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

# Let this file import from the rules folder
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "rules"))
from rule_logic import evaluate_rules


def add_derived_features(df):
    """Turn raw columns into features that make anomalies easier to spot."""
    df = df.copy()
    df["amount_ratio_to_avg"] = df["amount"] / df["user_avg_amount"].replace(0, 1)
    df["is_unfamiliar_city"] = (df["city"] != df["home_city"]).astype(int)
    return df


def train_model(df):
    """Train the Isolation Forest and remember the score range it produced."""
    df = add_derived_features(df)
    features = df[["amount_ratio_to_avg", "hour_of_day",
                   "txn_count_last_hour", "is_unfamiliar_city"]]
    model = IsolationForest(contamination=0.05, random_state=42, n_estimators=200)
    model.fit(features)
    raw = model.decision_function(features)
    score_range = (raw.min(), raw.max())
    return model, features, score_range


def ml_trust_component(model, features, score_range):
    """Convert the model's raw output to 0-1, where 1 = most normal."""
    raw = model.decision_function(features)
    lo, hi = score_range
    return np.clip((raw - lo) / (hi - lo + 1e-9), 0, 1)


def score_transactions(df):
    """Full pipeline: ML score + rule penalty -> trust score, flag, explanation."""
    df = add_derived_features(df)
    model, features, score_range = train_model(df)
    ml_component = ml_trust_component(model, features, score_range)

    penalties, reasons = [], []
    for _, row in df.iterrows():
        penalty, why = evaluate_rules(row)
        penalties.append(penalty)
        reasons.append(why)
    penalties = np.array(penalties)

    # 60% ML signal, 40% rules
    hybrid = 0.6 * ml_component + 0.4 * (1 - penalties)
    df["trust_score"] = (hybrid * 100).round(1)
    df["flag"] = df["trust_score"].apply(
        lambda s: "high_risk" if s < 40 else ("review" if s < 70 else "trusted")
    )

    def explain(row_reasons, score):
        if row_reasons:
            return "; ".join(row_reasons)
        if score < 70:
            return "Statistical pattern deviates from this user's normal behavior"
        return "No anomalies detected"

    df["explanation"] = [explain(r, s) for r, s in zip(reasons, df["trust_score"])]
    return df


if __name__ == "__main__":
    here = os.path.dirname(__file__)
    df = pd.read_csv(os.path.join(here, "..", "data", "transactions.csv"))
    scored = score_transactions(df)

    print("\n--- Flag distribution ---")
    print(scored["flag"].value_counts())

    print("\n--- Sample high-risk transactions ---")
    print(scored[scored["flag"] == "high_risk"][
        ["transaction_id", "amount", "trust_score", "explanation"]
    ].head(5).to_string(index=False))

    caught = ((scored["flag"] == "high_risk") & (scored["is_fraud_actual"] == 1)).sum()
    total = scored["is_fraud_actual"].sum()
    print(f"\nCaught {caught}/{total} planted frauds as high_risk ({caught/total*100:.0f}%)")

    scored.to_csv(os.path.join(here, "..", "data", "scored_transactions.csv"), index=False)