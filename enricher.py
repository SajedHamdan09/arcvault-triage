import json
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

ENRICHMENT_PROMPT = """You are an expert support analyst for ArcVault, a B2B SaaS platform.

Your job is to extract structured information from a raw customer message.

Return a JSON object with exactly these fields:
- "core_issue": a single clear sentence describing the main problem or request
- "identifiers": a list of any specific identifiers mentioned (account IDs, invoice numbers, error codes, URLs, usernames). Empty list if none.
- "urgency_signal": one of ["Critical", "High", "Normal", "Low"] based on the tone and content of the message

Urgency signal guidelines:
- Critical: words like "outage", "down", "all users affected", "cannot access", "data loss"
- High: single user blocked, billing discrepancy, security concern
- Normal: workflow improvement, question, evaluation
- Low: nice-to-have, future consideration, general inquiry

Return ONLY a valid JSON object. No explanation. No markdown. No extra text.

Example output:
{"core_issue": "User cannot log in due to a 403 error after a platform update.", "identifiers": ["arcvault.io/user/jsmith", "403"], "urgency_signal": "High"}

Message to analyze:
"""

def enrich_message(raw_message: str) -> dict:
    """
    Sends a message to Groq LLM for enrichment.
    Returns a dict with core_issue, identifiers, and urgency_signal.
    """
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a precise extraction AI. You always return valid JSON only, with no extra text or markdown."
                },
                {
                    "role": "user",
                    "content": ENRICHMENT_PROMPT + raw_message
                }
            ],
            temperature=0.1,
            max_tokens=300
        )

        raw_output = response.choices[0].message.content.strip()
        result = json.loads(raw_output)

        assert "core_issue" in result
        assert "identifiers" in result
        assert "urgency_signal" in result

        return result

    except json.JSONDecodeError:
        print(f"[enricher] Failed to parse JSON. Raw output: {raw_output}")
        return {
            "core_issue": "Unable to extract core issue.",
            "identifiers": [],
            "urgency_signal": "Normal"
        }
    except Exception as e:
        print(f"[enricher] Error: {e}")
        return {
            "core_issue": "Unable to extract core issue.",
            "identifiers": [],
            "urgency_signal": "Normal"
        }