ESCALATION_KEYWORDS = [
    "outage",
    "down for all users",
    "multiple users affected",
    "all users",
    "data loss",
    "cannot access",
    "billing error",
    "security breach",
    "unauthorized"
]

BILLING_ESCALATION_THRESHOLD = 500  # dollars
CONFIDENCE_ESCALATION_THRESHOLD = 0.70

def check_escalation(raw_message: str, confidence_score: float, category: str) -> dict:
    """
    Determines if a record should be flagged for human escalation.
    Returns escalation status and the reason if flagged.
    """
    reasons = []

    # Low confidence
    if confidence_score < CONFIDENCE_ESCALATION_THRESHOLD:
        reasons.append(f"Confidence score {confidence_score:.0%} is below threshold")

    # Escalation keywords in message
    message_lower = raw_message.lower()
    for keyword in ESCALATION_KEYWORDS:
        if keyword in message_lower:
            reasons.append(f"Escalation keyword detected: '{keyword}'")
            break

    # Billing discrepancy over $500
    if category == "Billing Issue":
        import re
        amounts = re.findall(r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)', raw_message)
        for amount_str in amounts:
            amount = float(amount_str.replace(",", ""))
            if amount > BILLING_ESCALATION_THRESHOLD:
                reasons.append(f"Billing amount ${amount:,.0f} exceeds escalation threshold")
                break

    if reasons:
        return {
            "escalation_flag": True,
            "escalation_reason": "; ".join(reasons),
            "destination_queue": "Escalation"
        }

    return {
        "escalation_flag": False,
        "escalation_reason": None,
        "destination_queue": None
    }