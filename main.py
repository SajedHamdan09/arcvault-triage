import json
from classifier import classify_message
from enricher import enrich_message
from router import route_message
from escalation import check_escalation
from summarizer import generate_summary
from output_writer import save_record, clear_output, get_sheet, setup_sheet_headers

def load_inputs(filepath: str) -> list:
    with open(filepath, "r") as f:
        return json.load(f)

def process_message(message: dict, worksheet=None) -> dict:
    print(f"\n{'='*60}")
    print(f"Processing Message #{message['id']} | Source: {message['source']}")
    print(f"Message: {message['raw_message'][:80]}...")
    print(f"{'='*60}")

    raw = message["raw_message"]

    # Classification
    print("[Step 2] Classifying...")
    classification = classify_message(raw)
    print(f"  → Category: {classification['category']}")
    print(f"  → Priority: {classification['priority']}")
    print(f"  → Confidence: {classification['confidence_score']:.0%}")

    # Enrichment
    print("[Step 3] Enriching...")
    enrichment = enrich_message(raw)
    print(f"  → Core Issue: {enrichment['core_issue']}")
    print(f"  → Identifiers: {enrichment['identifiers']}")
    print(f"  → Urgency: {enrichment['urgency_signal']}")

    # Routing
    print("[Step 4] Routing...")
    routing = route_message(
        category=classification["category"],
        confidence_score=classification["confidence_score"]
    )
    print(f"  → Destination: {routing['destination_queue']}")
    print(f"  → Reason: {routing['routing_reason']}")

    # Escalation Check
    print("[Step 6] Checking escalation...")
    escalation = check_escalation(
        raw_message=raw,
        confidence_score=classification["confidence_score"],
        category=classification["category"]
    )
    if escalation["escalation_flag"]:
        print(f"  → ESCALATED: {escalation['escalation_reason']}")
        final_queue = escalation["destination_queue"]
    else:
        print(f"  → No escalation needed")
        final_queue = routing["destination_queue"]

    # Build full record
    combined_data = {
        "id": message["id"],
        "source": message["source"],
        "raw_message": raw,
        "category": classification["category"],
        "priority": classification["priority"],
        "confidence_score": classification["confidence_score"],
        "core_issue": enrichment["core_issue"],
        "identifiers": enrichment["identifiers"],
        "urgency_signal": enrichment["urgency_signal"],
        "destination_queue": final_queue,
        "escalation_flag": escalation["escalation_flag"],
        "escalation_reason": escalation["escalation_reason"]
    }

    # Generate summary
    print("[Step 5] Generating summary...")
    summary = generate_summary(combined_data)
    combined_data["summary"] = summary
    print(f"  → Summary: {summary[:100]}...")

    # Save output
    save_record(combined_data, worksheet=worksheet)

    return combined_data


def main():
    print("\n ArcVault Triage Pipeline Starting...")
    print("Loading sample inputs...")

    inputs = load_inputs("sample_inputs.json")
    print(f"Loaded {len(inputs)} messages.\n")

    clear_output()

    # Initialize Google Sheet
    print("[sheets] Connecting to Google Sheets...")
    try:
        worksheet = get_sheet()
        setup_sheet_headers(worksheet)
        print("[sheets] Connected successfully.\n")
    except Exception as e:
        print(f"[sheets] Could not connect to Google Sheets: {e}")
        print("[sheets] Continuing with JSON output only.\n")
        worksheet = None

    results = []
    for message in inputs:
        record = process_message(message, worksheet=worksheet)
        results.append(record)

    print(f"\n{'='*60}")
    print(f"Pipeline complete. {len(results)} messages processed.")
    print(f"Results saved to output/results.json")
    if worksheet:
        print(f"Results saved to Google Sheets.")
    print(f"{'='*60}\n")

    escalated = [r for r in results if r["escalation_flag"]]
    if escalated:
        print(f" {len(escalated)} message(s) flagged for escalation:")
        for r in escalated:
            print(f"   - Message #{r['id']}: {r['escalation_reason']}")
    else:
        print("No messages required escalation.")


if __name__ == "__main__":
    main()