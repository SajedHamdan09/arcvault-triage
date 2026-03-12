import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

SUMMARY_PROMPT = """You are writing a handoff summary for a support team at ArcVault, a B2B SaaS platform.

Given the following information about a customer request, write a clear 2-3 sentence summary 
that tells the receiving team exactly what they need to know to act on this immediately.

Be direct. Include the key facts. Mention any identifiers. State what action is needed.

Information:
- Raw message: {raw_message}
- Category: {category}
- Priority: {priority}
- Core issue: {core_issue}
- Identifiers: {identifiers}
- Urgency: {urgency_signal}
- Destination team: {destination_queue}

Write only the summary paragraph. No labels. No JSON. Just the 2-3 sentences.
"""

def generate_summary(data: dict) -> str:
    """
    Generates a human-readable handoff summary for the receiving team.
    """
    try:
        prompt = SUMMARY_PROMPT.format(
            raw_message=data.get("raw_message", ""),
            category=data.get("category", ""),
            priority=data.get("priority", ""),
            core_issue=data.get("core_issue", ""),
            identifiers=", ".join(data.get("identifiers", [])) or "None",
            urgency_signal=data.get("urgency_signal", ""),
            destination_queue=data.get("destination_queue", "")
        )

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=200
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"[summarizer] Error: {e}")
        return "Summary generation failed. Please review the raw message directly."