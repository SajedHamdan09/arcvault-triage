# ArcVault Triage Pipeline

Sajed Hamdan | AI Engineer Assessment | Valsoft / Aspire Software | March 2026

---

## 1. System Design

The pipeline is a six step Python application with a FastAPI webhook
server as its ingestion layer. Each pipeline step lives in its own
module, so any component can be tuned or replaced without touching the
others. State is held in memory as a single dictionary per message that
accumulates fields as it moves through the pipeline.

The entry point is webhook_server.py, a FastAPI server that listens on
port 8000 for inbound POST requests at the /triage endpoint. Each
request carries a raw customer message with its source channel (Email,
Web Form or Support Portal). The moment a request arrives the server
automatically triggers the full pipeline for that message, no manual
intervention required.

The flow is as follows: the webhook receives the raw message (Step 1,
Ingestion) and calls classifier.py which sends it to the Groq LLM
returning category, priority and confidence score (Step 2). It then
calls enricher.py for a second LLM call extracting the core issue,
identifiers and urgency signal (Step 3). The result passes to router.py
for deterministic queue assignment (Step 4), then to escalation.py
which checks three rules and overrides the queue if needed (Step 6).
Finally, summarizer.py generates a human readable handoff summary and
output_writer.py persists the complete record to both a local JSON file
and a Google Sheet simultaneously (Step 5).

For demonstration purposes, send_messages.py simulates the inbound
traffic, it sends all five synthetic messages as sequential POST
requests to the webhook exactly as a real email provider or web form
integration would. In production this script is replaced by live
integrations with Gmail, web form providers or support portal APIs.

---

## 2. Routing Logic

Routing is a pure lookup table in router.py, no LLM involved. The five
categories map are as follows: Bug Report and Incident/Outage route to
Engineering, Feature Request routes to Product, Billing Issue routes to
Billing and Technical Question routes to IT/Security. Any Unclassified
result routes directly to Escalation.

Routing is intentionally deterministic rather than LLM-driven because
routing decisions must be auditable. A manager should always be able to
point to the exact rule that sends a ticket to a particular queue. The
routing table is also trivially extensible adding a new category is a
single line change.

One rule sits on top of the table, if the model's confidence score falls
below 70%, the category assignment is ignored and the message routes to
Escalation regardless. An uncertain classification should never reach a
team queue automatically, the cost of a wrong routing decision exceeds
the cost of a human review.

---

## 3. Escalation Logic

Escalation fires if any one of three rules is met:

- **Confidence below 70%:** the model is uncertain and human judgment
  is required before routing.
- **Escalation keywords:** outage, down for all users, multiple users
  affected, data loss, cannot access, security breach. Any of these in
  the raw message triggers immediate escalation. Keyword matching is
  intentionally broad. A false positive costs a human five minutes, a
  false negative on a live outage costs the business far more.
- **Billing amount above $500:** extracted via regex from Billing Issue
  messages. Financial discrepancies of this size carry legal and
  contractual implications requiring human review before any automated
  action.

In the test run: Message #3 (invoice discrepancy of $1,240) and Message
#5 (dashboard outage, multiple users) both correctly triggered
escalation. Messages #1, #2 and #4 correctly did not.

Escalation uses a rule engine rather than an LLM because escalation
decisions must be transparent and auditable. Every escalation can be
traced to the exact rule that fired, something LLM-based escalation
cannot guarantee.

---

## 4. What I Would Do Differently at Production Scale

- **Reliability:** add exponential backoff with three retries on LLM
  calls, a dead letter queue for messages that exhaust retries and
  structured logging with a per message correlation ID. Replace print
  statements with a proper logging framework. The FastAPI server would
  be containerized with Docker and deployed behind a load balancer.
- **Cost:** at 10,000 tickets per day, three LLM calls per message adds
  up significantly. I would merge classification and enrichment into a
  single call with a combined JSON schema (saving ~33% of API calls) and
  introduce a tiered model strategy, Llama 3.1 8B for high confidence
  obvious cases, 70B reserved for ambiguous or escalated records. This
  could reduce costs by 60-70% with minimal accuracy impact.
- **Latency:** classification and enrichment are fully independent and
  could run in parallel using FastAPI's async capabilities and
  asyncio.gather(). This would cut per message latency nearly in half.
  The summary call depends on both and correctly runs last.
- **Prompt versioning:** move prompts out of Python files into a
  versioned config store so they can be updated, rolled back and tested
  without a code deployment.
- **Model drift monitoring:** log every classification result and run
  weekly accuracy checks against a labeled validation set to detect
  provider-side model drift before it impacts routing quality.

---

## 5. Phase 2, With One More Week

- **Live channel integrations:** connect the FastAPI webhook directly to
  Gmail (via Gmail API), web form providers and support portal APIs.
  Replacing send_messages.py with real event sources. The webhook server
  is already production ready for this.
- **Customer context via RAG:** look up the sender's account tier and
  ticket history before classification using any identifier extracted
  from the message. A Platinum customer's bug report warrants different
  routing and priority than a free tier inquiry.
- **Human feedback loop:** add a verdict column to the Google Sheet.
  When agents resolve tickets, they mark whether the classification was
  correct. Feed verified labels back as few shot examples into the prompt
  overtime, creating a self-improving classifier.
- **Escalation notifications:** push an immediate Slack or email alert
  to the on call team when a record is escalated, with the summary and a
  direct Sheet link. Currently escalated records sit passively, while in
  production the system should reach out proactively.
- **Metrics dashboard:** a read layer on the output Sheet showing volume
  by category, average confidence over time, escalation rate and queue
  backlog per team. Giving managers visibility without touching raw data.