"""
Rule-based identity document verification logic for TrustCore.
Each rule returns (penalty 0-1, reason string) or (0, None) if not triggered.
"""
from datetime import date


def rule_expiry_before_issue(row):
    issue = date.fromisoformat(row["issue_date"])
    expiry = date.fromisoformat(row["expiry_date"])
    if expiry <= issue:
        return 0.6, "Expiry date precedes or matches issue date"
    return 0, None


def rule_face_mismatch(row):
    score = row["face_match_score"]
    if score < 0.6:
        return 0.5, f"Face match score is low ({score})"
    elif score < 0.75:
        return 0.25, f"Face match score is borderline ({score})"
    return 0, None


def rule_font_inconsistency(row):
    score = row["font_consistency_score"]
    if score < 0.6:
        return 0.4, f"Document font/formatting inconsistency detected (score {score})"
    return 0, None


def rule_invalid_doc_number(row):
    if row["doc_number_valid"] == 0:
        return 0.5, "Document number fails format/checksum validation"
    return 0, None


ALL_IDENTITY_RULES = [rule_expiry_before_issue, rule_face_mismatch, rule_font_inconsistency, rule_invalid_doc_number]


def evaluate_identity_rules(row):
    total_penalty = 0.0
    reasons = []
    for rule_fn in ALL_IDENTITY_RULES:
        penalty, reason = rule_fn(row)
        if reason:
            total_penalty += penalty
            reasons.append(reason)
    return min(total_penalty, 1.0), reasons
