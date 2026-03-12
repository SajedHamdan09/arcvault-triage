import json
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

CLASSIFICATION_PROMPT = """You are an expert support triage AI for ArcVault, a B2B SaaS platform.

Your job is to classify inbound customer messages into structured data.

Given a raw customer message, return a JSON object with exactly these fields:
- "category": one of ["Bug Report", "Feature Request", "Billing Issue", "Technical Question", "Incident/Outage"]
- "priority": one of ["Low", "Medium", "High"]
- "confidence_score": a float between 0.0 and 1.0 representing how certain you are about the category

Priority guidelines:
- High: system down, multiple users affected, data loss, billing errors, security issues
- Medium: single user affected, workarounds exist, feature gaps impacting workflow
- Low: general questions, nice-to-have features, minor inconveniences

Confidence guidelines:
- Above 0.85: message clearly fits one category
- 0.70 - 0.85: message fits a category but has some ambiguity
- Below 0.70: message is ambiguous or could fit multiple categories

Return ONLY a valid JSON object. No explanation. No markdown. No extra text.

Example output:
{"category": "Bug Report", "priority": "High", "confidence_score": 0.95}

Message to classify:
"""

def classify_message(raw_message: str) -> dict:
    """
    Sends a message to Groq LLM for classification.
    Returns a dict with category, priority, and confidence_score.
    """
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a precise classification AI. You always return valid JSON only, with no extra text or markdown."
                },
                {
                    "role": "user",
                    "content": CLASSIFICATION_PROMPT + raw_message
                }
            ],
            temperature=0.1,
            max_tokens=150
        )

        raw_output = response.choices[0].message.content.strip()
        result = json.loads(raw_output)

        # Validate required fields exist
        assert "category" in result
        assert "priority" in result
        assert "confidence_score" in result

        return result

    except json.JSONDecodeError:
        print(f"[classifier] Failed to parse JSON. Raw output: {raw_output}")
        return {
            "category": "Unknown",
            "priority": "Medium",
            "confidence_score": 0.0
        }
    except Exception as e:
        print(f"[classifier] Error: {e}")
        return {
            "category": "Unknown",
            "priority": "Medium",
            "confidence_score": 0.0
        }