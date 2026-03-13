import json
import os
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()

OUTPUT_FILE = "output/results.json"
SHEET_ID = os.environ.get("GOOGLE_SHEET_ID")
CREDENTIALS_FILE = "google_credentials.json"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

SHEET_HEADERS = [
    "ID",
    "Source",
    "Raw Message",
    "Category",
    "Priority",
    "Confidence Score",
    "Core Issue",
    "Identifiers",
    "Urgency Signal",
    "Destination Queue",
    "Escalation Flag",
    "Escalation Reason",
    "Summary",
    "Processed At"
]


def get_sheet():
    """
    Authenticates and returns the first worksheet of the target Google Sheet.
    """
    creds = Credentials.from_service_account_file(
        CREDENTIALS_FILE,
        scopes=SCOPES
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID)
    return sheet.sheet1


def setup_sheet_headers(worksheet):
    """
    Clears the sheet and adds headers on the first row.
    """
    worksheet.clear()
    worksheet.append_row(SHEET_HEADERS)

    worksheet.format("A1:N1", {
        "textFormat": {"bold": True},
        "backgroundColor": {
            "red": 0.2,
            "green": 0.4,
            "blue": 0.8
        }
    })
    print("[output_writer] Google Sheet headers set up.")


def record_to_sheet_row(record: dict) -> list:
    """
    Converts a record dict to a flat list matching the sheet headers order.
    """
    return [
        record.get("id", ""),
        record.get("source", ""),
        record.get("raw_message", ""),
        record.get("category", ""),
        record.get("priority", ""),
        f"{record.get('confidence_score', 0):.0%}",
        record.get("core_issue", ""),
        ", ".join(record.get("identifiers", [])) or "None",
        record.get("urgency_signal", ""),
        record.get("destination_queue", ""),
        "YES" if record.get("escalation_flag") else "No",
        record.get("escalation_reason") or "—",
        record.get("summary", ""),
        record.get("processed_at", "")
    ]


def save_record_to_json(record: dict):
    """
    Appends a single processed record to the output JSON file.
    """
    os.makedirs("output", exist_ok=True)

    existing_records = []
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r") as f:
            try:
                existing_records = json.load(f)
            except json.JSONDecodeError:
                existing_records = []

    record["processed_at"] = datetime.utcnow().isoformat() + "Z"
    existing_records.append(record)

    with open(OUTPUT_FILE, "w") as f:
        json.dump(existing_records, f, indent=2)

    print(f"[output_writer] Record #{record.get('id')} saved to JSON.")


def save_record(record: dict, worksheet=None):
    """
    Saves a record to both JSON and Google Sheets.
    """
    # Add timestamp if not already set
    if "processed_at" not in record:
        record["processed_at"] = datetime.utcnow().isoformat() + "Z"

    # Save to JSON
    save_record_to_json(record)

    # Save to Google Sheets
    if worksheet:
        try:
            row = record_to_sheet_row(record)
            worksheet.append_row(row)
            print(f"[output_writer] Record #{record.get('id')} saved to Google Sheets.")
        except Exception as e:
            print(f"[output_writer] Google Sheets error: {e}")


def clear_output():
    """
    Clears the JSON output file before a fresh run.
    """
    os.makedirs("output", exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump([], f)
    print("[output_writer] Output file cleared for fresh run.")