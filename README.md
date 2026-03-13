# ArcVault Triage Pipeline

An AI-powered intake and triage pipeline that automatically classifies,
enriches, routes, and escalates inbound customer support messages for
ArcVault, a fictional B2B SaaS company.

Built as part of the Valsoft / Aspire Software AI Engineer technical
assessment — March 2026.

---

## What It Does

Inbound customer messages arrive unstructured from email, web forms,
and support portals. This pipeline processes each message through six
sequential steps and produces a fully structured, routed, and
human-readable record — automatically.

| Step | Module | Description |
|------|--------|-------------|
| 1 | `main.py` | Ingests raw messages from `sample_inputs.json` |
| 2 | `classifier.py` | LLM classifies category, priority, confidence score |
| 3 | `enricher.py` | LLM extracts core issue, identifiers, urgency signal |
| 4 | `router.py` | Deterministic routing table maps category to queue |
| 5 | `output_writer.py` | Writes structured JSON + Google Sheets record |
| 6 | `escalation.py` | Rule engine flags records for human review |

---

## Results

All five sample inputs processed correctly. Output visible here:
📊 [Google Sheets — Live Results](https://docs.google.com/spreadsheets/d/1c5i1MLkNqxcsIj7Jla71nymdMdE8UyI_84PDdg1F5wQ/edit?usp=sharing)

| # | Category | Priority | Confidence | Queue | Escalated |
|---|----------|----------|------------|-------|-----------|
| 1 | Bug Report | High | 92% | Engineering | No |
| 2 | Feature Request | Medium | 80% | Product | No |
| 3 | Billing Issue | High | 92% | Billing | YES |
| 4 | Technical Question | Low | 80% | IT/Security | No |
| 5 | Incident/Outage | High | 95% | Engineering | YES |

Messages #3 and #5 correctly triggered escalation:
- **#3** — Billing amount $1,240 exceeds the $500 escalation threshold
- **#5** — Keyword "multiple users affected" detected in raw message

---

## Stack

| Component | Tool | Reason |
|-----------|------|--------|
| Language | Python 3.12 | Backend role — code ownership over visual builders |
| LLM | Groq / Llama 3.3 70B | Free tier, sub-second latency, strong structured output |
| Output | Google Sheets + JSON | Visual for reviewers, file for submission |
| Editor | Cursor | AI-augmented development workflow |

---

## Project Structure
```
arcvault-triage/
├── main.py               # Orchestrator — runs the full pipeline
├── classifier.py         # LLM classification (category, priority, confidence)
├── enricher.py           # LLM enrichment (core issue, identifiers, urgency)
├── router.py             # Deterministic routing table
├── escalation.py         # Rule-based escalation engine
├── summarizer.py         # LLM handoff summary generation
├── output_writer.py      # JSON + Google Sheets writer
├── sample_inputs.json    # 5 synthetic test messages
├── output/
│   └── results.json      # Full structured output for all 5 messages
├── PROMPTS.md            # Prompt documentation with reasoning
├── ARCHITECTURE.md       # System design write-up
└── requirements.txt      # Python dependencies
```

---

## Setup & Run

**1. Clone the repo**
```bash
git clone https://github.com/SajedHamdan09/arcvault-triage.git
cd arcvault-triage
```

**2. Create and activate virtual environment**
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Set up environment variables**

Create a `.env` file in the project root:
```
GROQ_API_KEY=your_groq_api_key_here
GOOGLE_SHEET_ID=your_google_sheet_id_here
```

**5. Add Google credentials**

Place your `google_credentials.json` service account file in the
project root. See the Architecture write-up for setup details.

**6. Run the pipeline**
```bash
python main.py
```

---

## AI Tools Used

This project was built using **Claude** (reasoning, architecture, and
prompt design) and **Cursor** (code generation and iteration). Every
AI-generated output was reviewed, tested, and adjusted — the prompts
went through multiple iterations to achieve consistent JSON output,
and the escalation thresholds were deliberately chosen based on the
assessment specification rather than accepted as-is from AI suggestions.

---

## Deliverables

| Deliverable | Location |
|-------------|----------|
| Working pipeline | This repository |
| Structured output (JSON) | `output/results.json` |
| Structured output (Sheets) | [Google Sheets link](https://docs.google.com/spreadsheets/d/1c5i1MLkNqxcsIj7Jla71nymdMdE8UyI_84PDdg1F5wQ/edit?usp=sharing) |
| Prompt documentation | `PROMPTS.md` |
| Architecture write-up | `ARCHITECTURE.md` / `ARCHITECTURE.docx` |
| Demo recording | [Loom link](YOUR_LOOM_LINK_HERE) |