# Prompt Documentation

## Overview

This document covers every LLM prompt used in the ArcVault triage pipeline.  
For each prompt I explain the structure, the reasoning behind design choices,  
the tradeoffs made and what I would improve with more time.

All prompts use Groq's `llama-3.3-70b-versatile` model at `temperature=0.1`  
for classification and enrichment (low temperature = more deterministic and  
consistent outputs) and `temperature=0.3` for summary generation 
(slightly higher to allow more natural language variation).

---

## Prompt 1 - Classification Prompt

### The Prompt

```
You are an expert support triage AI for ArcVault, a B2B SaaS platform.

Your job is to classify inbound customer messages into structured data.

Given a raw customer message, return a JSON object with exactly these fields:
- "category": one of ["Bug Report", "Feature Request", "Billing Issue", 
  "Technical Question", "Incident/Outage"]
- "priority": one of ["Low", "Medium", "High"]
- "confidence_score": a float between 0.0 and 1.0 representing how certain 
  you are about the category

Priority guidelines:
- High: system down, multiple users affected, data loss, billing errors, 
  security issues
- Medium: single user affected, workarounds exist, feature gaps impacting 
  workflow
- Low: general questions, nice-to-have features, minor inconveniences

Confidence guidelines:
- Above 0.85: message clearly fits one category
- 0.70 - 0.85: message fits a category but has some ambiguity
- Below 0.70: message is ambiguous or could fit multiple categories

Return ONLY a valid JSON object. No explanation. No markdown. No extra text.
```

### Why I Structured It This Way

I opened with a role definition ("You are an expert support triage AI") 
to anchor the model's behavior and reduce irrelevant outputs. Assigning a 
persona with domain context (B2B SaaS, ArcVault) helps the model apply 
appropriate business judgment rather than generic reasoning.

The output schema is defined explicitly with every field, every allowed   
value, and every constraint. This is intentional, open ended instructions   
produce inconsistent outputs that break JSON parsing downstream. By giving   
the model a closed vocabulary for category and priority, I eliminate   
ambiguity and make the output deterministic enough to be reliable.

The confidence score guidelines were the most carefully considered part.   
Rather than asking the model to "rate your confidence," which produces   
arbitrary numbers I gave explicit semantic anchors (above 0.85, 0.70–0.85,   
below 0.70) tied to real meaning. This makes the confidence score   
actionable, so it directly feeds the escalation logic.

The instruction "Return ONLY a valid JSON object. No explanation. No 
markdown. No extra text." is repeated in both the prompt and the system 
message because LLMs have a tendency to wrap JSON in markdown code blocks 
or add preamble text, which breaks json.loads() parsing.

Temperature is set to 0.1, near deterministic. Classification is not a   
creative task. Consistency and repeatability matter more than variation.

### Tradeoffs Made

I chose zero-shot prompting over few-shot (providing example   
input/output pairs) because the five categories are well defined enough   
that examples would have added prompt length without meaningfully improving   
accuracy. For more ambiguous taxonomies, few shot would be worth the   
token cost.

I did not implement retry logic with prompt variation when confidence is   
low. In production, a low confidence result could trigger a second   
classification call with a slightly different prompt or a higher capability   
model before falling back to human escalation.

### What I Would Change With More Time

In production I would add few-shot examples for the two most commonly 
confused categories (Bug Report vs Incident/Outage, and Technical Question 
vs Feature Request). I would also evaluate GPT-4o against Llama 3.3 70B 
on a labeled dataset of 100+ real support tickets to quantify the accuracy 
difference and decide whether the cost increase is justified.

---

## Prompt 2 - Enrichment Prompt

### The Prompt

```
You are an expert support analyst for ArcVault, a B2B SaaS platform.

Your job is to extract structured information from a raw customer message.

Return a JSON object with exactly these fields:
- "core_issue": a single clear sentence describing the main problem or request
- "identifiers": a list of any specific identifiers mentioned (account IDs, 
  invoice numbers, error codes, URLs, usernames). Empty list if none.
- "urgency_signal": one of ["Critical", "High", "Normal", "Low"] based on 
  the tone and content of the message

Urgency signal guidelines:
- Critical: words like "outage", "down", "all users affected", "cannot 
  access", "data loss"
- High: single user blocked, billing discrepancy, security concern
- Normal: workflow improvement, question, evaluation
- Low: nice-to-have, future consideration, general inquiry

Return ONLY a valid JSON object. No explanation. No markdown. No extra text.
```

### Why I Structured It This Way

This prompt is deliberately separated from classification rather than   
combined into one call. There are two reasons for this. First, it keeps   
each prompt focused on a single responsibility. Classification is about   
labeling, while enrichment is about extraction. Combining them would make the   
prompt longer, harder to tune and more likely to produce errors in one   
task that corrupt the other. Second, it allows each step to fail   
independently. If enrichment fails, classification results are still valid   
and the record can still be routed.

The identifiers field is defined broadly on purpose the account IDs, invoice   
numbers, error codes, URLs usernames. Rather than specifying a fixed set   
of identifier types, I let the model extract anything that looks like a   
reference. This makes the prompt resilient to message formats I haven't   
seen yet.

The urgency signal is kept as a separate four-level scale from priority 
(which is Low/Medium/High) intentionally. Urgency is about the tone and 
content of the message as the customer wrote it. Priority is a business 
judgment about how quickly to respond. Keeping them separate means a 
low-priority feature request can still have a "Normal" urgency signal 
without confusion.

### Tradeoffs Made

I made the identifiers extraction best-effort, the model extracts what it   
sees but there is no validation that the extracted values actually exist   
in ArcVault's systems. In production, extracted identifiers would be   
cross referenced against a customer database via an API call to verify   
they're real before the record is routed.

### What I Would Change With More Time

I would add a "sentiment" field to the enrichment output, detecting   
frustrated or angry tone in a message is a useful escalation signal   
beyond keywords. I would also add named entity recognition for company   
names and contact names to improve the handoff summary quality.

---

## Prompt 3 — Summary Generation Prompt

### The Prompt

```
You are writing a handoff summary for a support team at ArcVault.

Given the following information about a customer request, write a clear 
2-3 sentence summary that tells the receiving team exactly what they need 
to know to act on this immediately.

Be direct. Include the key facts. Mention any identifiers. State what 
action is needed.

Information:
- Raw message: {raw_message}
- Category: {category}
- Priority: {priority}
- Core issue: {core_issue}
- Identifiers: {identifiers}
- Urgency: {urgency_signal}
- Destination team: {destination_queue}
```

### Why I Structured It This Way

This is the only prompt where I used a higher temperature (0.3 vs 0.1)   
because summary generation benefits from slightly more natural language   
variation. A deterministic summary sounds robotic, a small amount of   
temperature produces more readable and human feeling output without   
sacrificing accuracy.

I inject all the structured fields from the previous two steps directly 
into the prompt. This means the summary is grounded in verified, structured 
data rather than re-derived from the raw message alone. The model is 
synthesizing, not re-analyzing.

The instruction "State what action is needed" is the most important line 
in this prompt. Without it, models tend to produce descriptive summaries 
("The customer reported X") rather than actionable ones ("The Billing team 
should investigate invoice #8821 and reconcile the $260 discrepancy against 
the customer's contract"). Actionability is what makes the summary useful 
to the receiving team.

### Tradeoffs Made

I did not ask the model to suggest a specific resolution path because that 
would require knowledge of ArcVault's internal processes and SOPs. In a 
real deployment, the summary prompt would be enriched with relevant 
knowledge base articles or resolution templates injected via RAG 
(Retrieval-Augmented Generation).

### What I Would Change With More Time

I would add tone calibration, escalated records should have summaries   
written with more urgency ("Immediate action required") while low-priority   
records should be softer. I would also A/B test summary length, 2   
sentences vs 3 sentences to see which format receiving teams prefer   
to act on.

---

## General Notes on Prompt Strategy

**Why Groq / Llama 3.3 70B:**
I chose Groq for its free tier and sub-second response latency. Llama 3.3 
70B performs comparably to GPT-3.5-turbo on structured extraction tasks 
and is well within the capability requirements for this use case. In 
production I would benchmark against GPT-4o on a labeled dataset before 
committing to either model.

**Why separate prompts per step vs one combined prompt:**  
Single-responsibility prompts are easier to debug, tune and replace   
independently. If classification accuracy drops I can retune that prompt   
without touching enrichment or summarization. A monolithic prompt that   
does all three steps at once creates tight coupling that is expensive to   
maintain.

**On JSON reliability:**  
I use two layers of JSON enforcement, the system message and the user   
prompt both explicitly instruct the model to return only valid JSON. I   
also wrap all json.loads() calls in try/except with sensible fallback   
values so a single malformed response never crashes the pipeline.