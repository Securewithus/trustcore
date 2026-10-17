import pandas as pd
from rule_logic import evaluate_rules

# A clearly suspicious transaction
suspicious = pd.Series({
    "amount": 15000, "user_avg_amount": 500,
    "hour_of_day": 2, "city": "Kolkata", "home_city": "Lucknow",
    "txn_count_last_hour": 6
})

# A clearly normal transaction
normal = pd.Series({
    "amount": 480, "user_avg_amount": 450,
    "hour_of_day": 14, "city": "Pune", "home_city": "Pune",
    "txn_count_last_hour": 0
})

for name, txn in [("SUSPICIOUS", suspicious), ("NORMAL", normal)]:
    penalty, reasons = evaluate_rules(txn)
    print(f"\n{name}")
    print("Penalty:", penalty)
    print("Reasons:", reasons)