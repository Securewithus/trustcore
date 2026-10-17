import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

random.seed(42)
np.random.seed(42)

N_USERS = 40
N_TRANSACTIONS = 2000
FRAUD_RATE = 0.05  # about 5% of transactions will be fraud

users = [f"user_{i:03d}" for i in range(N_USERS)]

# Each user gets a "normal" profile: usual spend, usual hours, home city
user_profiles = {
    u: {
        "avg_amount": np.random.uniform(100, 2000),
        "usual_hour_start": np.random.randint(7, 11),
        "usual_hour_end": np.random.randint(18, 22),
        "home_city": random.choice(["Lucknow", "Delhi", "Mumbai", "Bengaluru", "Pune"]),
    }
    for u in users
}
cities = ["Lucknow", "Delhi", "Mumbai", "Bengaluru", "Pune", "Kolkata", "Jaipur", "Chennai"]

rows = []
start_date = datetime(2026, 1, 1)

for i in range(N_TRANSACTIONS):
    user = random.choice(users)
    profile = user_profiles[user]
    is_fraud = random.random() < FRAUD_RATE
    ts = start_date + timedelta(minutes=random.randint(0, 60 * 24 * 60))

    if is_fraud:
        # Suspicious pattern: huge amount, odd hour, unfamiliar city, burst of transactions
        amount = round(profile["avg_amount"] * np.random.uniform(5, 15), 2)
        hour = random.choice([1, 2, 3, 4])
        city = random.choice([c for c in cities if c != profile["home_city"]])
        txn_count_last_hour = np.random.randint(4, 10)
    else:
        # Normal behavior, close to the user's usual profile
        amount = round(max(10, np.random.normal(profile["avg_amount"], profile["avg_amount"] * 0.2)), 2)
        hour = np.random.randint(profile["usual_hour_start"], profile["usual_hour_end"])
        city = profile["home_city"]
        txn_count_last_hour = np.random.randint(0, 2)

    ts = ts.replace(hour=hour % 24)

    rows.append({
        "transaction_id": f"TXN{i:05d}",
        "user_id": user,
        "timestamp": ts.isoformat(),
        "amount": amount,
        "user_avg_amount": round(profile["avg_amount"], 2),
        "hour_of_day": hour % 24,
        "city": city,
        "home_city": profile["home_city"],
        "txn_count_last_hour": txn_count_last_hour,
        "is_fraud_actual": int(is_fraud),  # ground truth, only for our own testing
    })

df = pd.DataFrame(rows).sort_values("timestamp").reset_index(drop=True)
df.to_csv("transactions.csv", index=False)
print(f"Generated {len(df)} transactions, {df['is_fraud_actual'].sum()} planted anomalies")