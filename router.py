# maps category to destination queue
ROUTING_TABLE = {
    "Bug Report":         "Engineering",
    "Feature Request":    "Product",
    "Billing Issue":      "Billing",
    "Technical Question": "IT/Security",
    "Incident/Outage":    "Engineering",
    "Unknown":            "Escalation"
}

CONFIDENCE_THRESHOLD = 0.70

def route_message(category: str, confidence_score: float) -> dict:
    """
    Determines the destination queue based on category and confidence.
    Falls back to Escalation queue if confidence is too low.
    """
    if confidence_score < CONFIDENCE_THRESHOLD:
        return {
            "destination_queue": "Escalation",
            "routing_reason": f"Low confidence score ({confidence_score:.0%}) — routed to human review"
        }

    destination = ROUTING_TABLE.get(category, "Escalation")

    return {
        "destination_queue": destination,
        "routing_reason": f"Category '{category}' mapped to {destination} queue"
    }