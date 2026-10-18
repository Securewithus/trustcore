"""
Generates a simulated employee access log dataset for TrustCore's
access anomaly detection module (insider threat use case).
"""
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

random.seed(21)
np.random.seed(21)

N_EMPLOYEES = 25
N_EVENTS = 1200
ANOMALY_RATE = 0.05

employees = [f"emp_{i:03d}" for i in range(N_EMPLOYEES)]
emp_profiles = {
    e: {
        "usual_login_hour": np.random.randint(8, 10),
        "usual_logout_hour": np.random.randint(17, 19),
        "usual_files_per_session": np.random.randint(3, 15),
        "role": random.choice(["engineer", "finance", "hr", "support", "admin"]),
    }
    for e in employees
}

rows = []
start_date = datetime(2026, 1, 1)

for i in range(N_EVENTS):
    emp = random.choice(employees)
    profile = emp_profiles[emp]
    is_anomaly = random.random() < ANOMALY_RATE
    ts = start_date + timedelta(minutes=random.randint(0, 60 * 24 * 60))

    if is_anomaly:
        login_hour = random.choice([0, 1, 2, 3, 23])  # off-hours access
        files_accessed = np.random.randint(30, 80)  # bulk access spike
        new_device = 1
        failed_login_attempts = np.random.randint(2, 6)
    else:
        login_hour = np.random.randint(profile["usual_login_hour"], profile["usual_logout_hour"])
        files_accessed = max(1, int(np.random.normal(profile["usual_files_per_session"], 3)))
        new_device = 0
        failed_login_attempts = 0

    ts = ts.replace(hour=login_hour % 24)

    rows.append({
        "event_id": f"EVT{i:05d}",
        "employee_id": emp,
        "role": profile["role"],
        "timestamp": ts.isoformat(),
        "login_hour": login_hour % 24,
        "files_accessed": files_accessed,
        "usual_files_per_session": profile["usual_files_per_session"],
        "new_device": new_device,
        "failed_login_attempts": failed_login_attempts,
        "is_anomaly_actual": int(is_anomaly),
    })

df = pd.DataFrame(rows).sort_values("timestamp").reset_index(drop=True)
df.to_csv("access_logs.csv", index=False)
print(f"Generated {len(df)} access events, {df['is_anomaly_actual'].sum()} planted anomalies")
