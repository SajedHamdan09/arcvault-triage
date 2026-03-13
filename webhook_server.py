from fastapi import FastAPI
from pydantic import BaseModel
from contextlib import asynccontextmanager
from classifier import classify_message
from enricher import enrich_message
from router import route_message
from escalation import check_escalation
from summarizer import generate_summary
from output_writer import save_record, get_sheet, setup_sheet_headers
from datetime import datetime
import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()

worksheet = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global worksheet
    print("\nArcVault Triage Webhook Server Starting...")
    try:
        worksheet = get_sheet()
        setup_sheet_headers(worksheet)
        print(" Google Sheets connected.")
    except Exception as e:
        print(f" Google Sheets unavailable: {e}")
        worksheet = None
    yield


app = FastAPI(
    title="ArcVault Triage API",
    description="AI-powered intake and triage pipeline for inbound customer messages.",
    version="1.0.0",
    lifespan=lifespan
)


class InboundMessage(BaseModel):
    id: int
    source: str
    raw_message: str


class TriageResult(BaseModel):
    id: int
    source: str
    raw_message: str
    category: str
    priority: str
    confidence_score: float
    core_issue: str
    identifiers: list
    urgency_signal: str
    destination_queue: str
    escalation_flag: bool
    escalation_reason: str | None
    summary: str
    processed_at: str


@app.get("/")
def root():
    return {
        "service": "ArcVault Triage Pipeline",
        "status": "running",
        "version": "1.0.0",
        "endpoint": "POST /triage"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@app.post("/triage", response_model=TriageResult)
async def triage_message(message: InboundMessage):
    """
    Receives a raw inbound message and runs the full 6-step triage pipeline.
    Automatically classifies, enriches, routes, escalates, and saves the result.
    """
    print(f"\n{'='*60}")
    print(f" New message received | ID: {message.id} | Source: {message.source}")
    print(f"Message: {message.raw_message[:80]}...")
    print(f"{'='*60}")

    raw = message.raw_message

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

    # Escalation
    print("[Step 6] Checking escalation...")
    escalation = check_escalation(
        raw_message=raw,
        confidence_score=classification["confidence_score"],
        category=classification["category"]
    )
    if escalation["escalation_flag"]:
        print(f"  →  ESCALATED: {escalation['escalation_reason']}")
        final_queue = escalation["destination_queue"]
    else:
        print(f"  → No escalation needed")
        final_queue = routing["destination_queue"]

    # Build full record
    combined_data = {
        "id": message.id,
        "source": message.source,
        "raw_message": raw,
        "category": classification["category"],
        "priority": classification["priority"],
        "confidence_score": classification["confidence_score"],
        "core_issue": enrichment["core_issue"],
        "identifiers": enrichment["identifiers"],
        "urgency_signal": enrichment["urgency_signal"],
        "destination_queue": final_queue,
        "escalation_flag": escalation["escalation_flag"],
        "escalation_reason": escalation["escalation_reason"],
        "processed_at": datetime.utcnow().isoformat() + "Z"
    }

    # Summary + Output
    print("[Step 5] Generating summary and saving...")
    summary = generate_summary(combined_data)
    combined_data["summary"] = summary
    print(f"  → Summary: {summary[:100]}...")

    save_record(combined_data, worksheet=worksheet)
    print(f" Message #{message.id} fully processed.\n")

    return TriageResult(**combined_data)


if __name__ == "__main__":
    uvicorn.run("webhook_server:app", host="0.0.0.0", port=8000, reload=False)