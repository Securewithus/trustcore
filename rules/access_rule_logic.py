"""
Rule-based access anomaly logic for TrustCore's insider-threat module.
Each rule returns (penalty 0-1, reason string) or (0, None) if not triggered.
"""


def rule_off_hours_access(row):
    hour = int(row["login_hour"])
    if hour in [0, 1, 2, 3, 23]:
        return 0.35, f"Access occurred at an off-hours time ({hour}:00)"
    return 0, None


def rule_bulk_file_access(row):
    if row["usual_files_per_session"] <= 0:
        return 0, None
    ratio = row["files_accessed"] / row["usual_files_per_session"]
    if ratio > 4:
        return 0.4, f"Files accessed ({int(row['files_accessed'])}) is {ratio:.1f}x this user's usual session"
    return 0, None


def rule_new_device(row):
    if row["new_device"] == 1:
        return 0.15, "Access from a previously unseen device"
    return 0, None


def rule_failed_logins(row):
    attempts = int(row["failed_login_attempts"])
    if attempts >= 2:
        return 0.25, f"{attempts} failed login attempts before this session"
    return 0, None


ALL_ACCESS_RULES = [rule_off_hours_access, rule_bulk_file_access, rule_new_device, rule_failed_logins]


def evaluate_access_rules(row):
    total_penalty = 0.0
    reasons = []
    for rule_fn in ALL_ACCESS_RULES:
        penalty, reason = rule_fn(row)
        if reason:
            total_penalty += penalty
            reasons.append(reason)
    return min(total_penalty, 1.0), reasons
