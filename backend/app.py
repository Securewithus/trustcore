import os
import sys

import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS

# Let this file import from the model and rules folders
HERE = os.path.dirname(__file__)
sys.path.append(os.path.join(HERE, "..", "model"))
sys.path.append(os.path.join(HERE, "..", "rules"))

from score import score_transactions, train_model, ml_trust_component
from rule_logic import evaluate_rules

app = Flask(__name__)
CORS(app)  # lets a dashboard on another port call this API

# Load data, score everything, and train the model ONCE when the server starts
raw_df = pd.read_csv(os.path.join(HERE, "..", "data", "transactions.csv"))
scored_df = score_transactions(raw_df)
model, _, score_range = train_model(raw_df)


@app.route("/api/summary", methods=["GET"])
def summary():
    """Counts for the dashboard's top cards."""
    counts = scored_df["flag"].value_counts().to_dict()
    return jsonify({
        "total": len(scored_df),
        "high_risk": counts.get("high_risk", 0),
        "review": counts.get("review", 0),
        "trusted": counts.get("trusted", 0),
    })


@app.route("/api/transactions", methods=["GET"])
def transactions():
    """List scored transactions. Optional: ?flag=high_risk&limit=20"""
    limit = int(request.args.get("limit", 100))
    flag = request.args.get("flag")

    df = scored_df.sort_values("timestamp", ascending=False)
    if flag:
        df = df[df["flag"] == flag]

    cols = ["transaction_id", "user_id", "timestamp", "amount",
            "city", "trust_score", "flag", "explanation"]
    return jsonify(df[cols].head(limit).to_dict(orient="records"))


@app.route("/api/score", methods=["POST"])
def score_one():
    """Score ONE new transaction sent as JSON. This is the real-time part."""
    row = pd.Series(request.get_json())

    ratio = row["amount"] / max(row["user_avg_amount"], 1)
    unfamiliar = int(row["city"] != row["home_city"])

    features = pd.DataFrame([{
        "amount_ratio_to_avg": ratio,
        "hour_of_day": row["hour_of_day"],
        "txn_count_last_hour": row["txn_count_last_hour"],
        "is_unfamiliar_city": unfamiliar,
    }])

    ml_score = ml_trust_component(model, features, score_range)[0]
    penalty, reasons = evaluate_rules(row)

    trust_score = round((0.6 * ml_score + 0.4 * (1 - penalty)) * 100, 1)
    flag = "high_risk" if trust_score < 40 else ("review" if trust_score < 70 else "trusted")

    return jsonify({
        "trust_score": trust_score,
        "flag": flag,
        "explanation": "; ".join(reasons) if reasons else "No anomalies detected",
    })


if __name__ == "__main__":
    print(f"Loaded {len(scored_df)} transactions. API running on http://localhost:5000")
    app.run(debug=True, port=5000)