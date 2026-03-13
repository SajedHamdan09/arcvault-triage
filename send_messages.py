import httpx
import json
import time

WEBHOOK_URL = "http://localhost:8000/triage"

messages = [
    {
        "id": 1,
        "source": "Email",
        "raw_message": "Hi, I tried logging in this morning and keep getting a 403 error. My account is arcvault.io/user/jsmith. This started after your update last Tuesday."
    },
    {
        "id": 2,
        "source": "Web Form",
        "raw_message": "We'd love to see a bulk export feature for our audit logs. We're a compliance-heavy org and this would save us hours every month."
    },
    {
        "id": 3,
        "source": "Support Portal",
        "raw_message": "Invoice #8821 shows a charge of $1,240 but our contract rate is $980/month. Can someone look into this?"
    },
    {
        "id": 4,
        "source": "Email",
        "raw_message": "I'm not sure if this is the right place to ask, but is there a way to set up SSO with Okta? We're evaluating switching our auth provider."
    },
    {
        "id": 5,
        "source": "Web Form",
        "raw_message": "Your dashboard stopped loading for us around 2pm EST. Checked our end — it's definitely on yours. Multiple users affected."
    }
]

def send_all():
    print("\n🚀 Sending all 5 messages to ArcVault Triage Webhook...\n")
    results = []

    for msg in messages:
        print(f"📨 Sending Message #{msg['id']} ({msg['source']})...")
        try:
            response = httpx.post(WEBHOOK_URL, json=msg, timeout=60)
            result = response.json()
            results.append(result)
            print(f"  ✅ Category: {result['category']}")
            print(f"  ✅ Priority: {result['priority']}")
            print(f"  ✅ Queue: {result['destination_queue']}")
            print(f"  ✅ Escalated: {'YES 🚨' if result['escalation_flag'] else 'No'}")
            print()
            time.sleep(1)  # Small delay between messages
        except Exception as e:
            print(f"  ❌ Error: {e}\n")

    print("="*60)
    print(f"✅ All {len(results)} messages processed successfully.")
    escalated = [r for r in results if r['escalation_flag']]
    if escalated:
        print(f"🚨 {len(escalated)} message(s) escalated:")
        for r in escalated:
            print(f"   - Message #{r['id']}: {r['escalation_reason']}")

if __name__ == "__main__":
    send_all()