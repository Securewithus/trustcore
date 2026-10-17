def rule_amount_spike(row):
    """Transaction far larger than the user's usual amount."""
    if row["user_avg_amount"] <= 0:
        return 0, None
    ratio = row["amount"] / row["user_avg_amount"]
    if ratio > 5:
        return 0.5, f"Amount is {ratio:.1f}x the user's typical transaction"
    elif ratio > 3:
        return 0.25, f"Amount is {ratio:.1f}x higher than usual"
    return 0, None


def rule_odd_hour(row):
    """Transaction during unusual hours (1-4 AM)."""
    if row["hour_of_day"] in [1, 2, 3, 4]:
        return 0.3, f"Transaction occurred at an unusual hour ({row['hour_of_day']}:00)"
    return 0, None


def rule_unfamiliar_location(row):
    """Transaction from a city different from the user's home city."""
    if row["city"] != row["home_city"]:
        return 0.25, f"Transaction location ({row['city']}) differs from home city ({row['home_city']})"
    return 0, None


def rule_rapid_frequency(row):
    """Many transactions in a short window, a possible fraud burst."""
    if row["txn_count_last_hour"] >= 4:
        return 0.35, f"{row['txn_count_last_hour']} transactions by this user in the last hour"
    return 0, None


ALL_RULES = [rule_amount_spike, rule_odd_hour, rule_unfamiliar_location, rule_rapid_frequency]


def evaluate_rules(row):
    """
    Runs every rule on one transaction.
    Returns (total penalty capped at 1.0, list of triggered reasons).
    """
    total_penalty = 0.0
    reasons = []
    for rule_fn in ALL_RULES:
        penalty, reason = rule_fn(row)
        if reason:
            total_penalty += penalty
            reasons.append(reason)
    return min(total_penalty, 1.0), reasons