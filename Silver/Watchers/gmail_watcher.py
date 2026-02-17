"""
gmail_watcher.py — External Watcher (Silver Tier)
--------------------------------------------------
Polls a Gmail inbox for unread messages matching a
configured label/query. Converts each email into a
structured task file and drops it into /Inbox for
file_watcher.py to pick up and classify.

Skill: External Watcher (Silver Tier)

Prerequisites:
  pip install google-auth google-auth-oauthlib google-api-python-client

Setup:
  1. Go to Google Cloud Console → enable Gmail API
  2. Download credentials.json → place next to this file
  3. On first run, browser will open for OAuth consent
  4. Token is saved to token.json for subsequent runs
"""

import os
import base64
import time
import re
from datetime import datetime
from email import message_from_bytes

# Google API client — install via: pip install google-api-python-client google-auth-oauthlib
try:
    from googleapiclient.discovery import build
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    print("[gmail_watcher] WARNING: Google libraries not installed.")
    print("  Run: pip install google-api-python-client google-auth-oauthlib")


# ── Configuration ─────────────────────────────────────────────────────────────
BASE_DIR       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INBOX_DIR      = os.path.join(BASE_DIR, "Inbox")
WATCHER_DIR    = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS    = os.path.join(WATCHER_DIR, "credentials.json")
TOKEN_FILE     = os.path.join(WATCHER_DIR, "token.json")

GMAIL_SCOPES   = ["https://www.googleapis.com/auth/gmail.modify"]
GMAIL_QUERY    = "is:unread label:ai-tasks"   # change to your label/query
POLL_SECONDS   = 60                            # check every 60 seconds


# ── Auth ──────────────────────────────────────────────────────────────────────

def get_gmail_service():
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, GMAIL_SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS, GMAIL_SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


# ── Email → Task conversion ───────────────────────────────────────────────────

def safe_filename(subject: str) -> str:
    """Convert email subject to a safe filename."""
    slug = re.sub(r"[^a-zA-Z0-9_-]", "_", subject)[:50].strip("_")
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"GMAIL_{ts}_{slug}.md"


def extract_body(payload: dict) -> str:
    """Recursively extract plain-text body from Gmail payload."""
    if payload.get("mimeType") == "text/plain":
        data = payload.get("body", {}).get("data", "")
        return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

    for part in payload.get("parts", []):
        result = extract_body(part)
        if result:
            return result
    return "(no plain text body)"


def email_to_task(msg_data: dict) -> tuple[str, str]:
    """Return (filename, markdown_content) for the task file."""
    headers = {h["name"]: h["value"] for h in msg_data["payload"]["headers"]}
    subject = headers.get("Subject", "No Subject")
    sender  = headers.get("From", "Unknown")
    date    = headers.get("Date", "Unknown")
    body    = extract_body(msg_data["payload"])

    content = f"""# Task: {subject}
**Priority:** Medium
**Created:** {datetime.now().strftime("%Y-%m-%d")}
**Owner:** Gmail Watcher (external)
**Source:** {sender}
**Email Date:** {date}

## Description
{body.strip()}

## Acceptance Criteria
- [ ] Review and action the request from {sender}

## Notes
Auto-generated from Gmail. Original subject: "{subject}"
"""
    return safe_filename(subject), content


# ── Main loop ─────────────────────────────────────────────────────────────────

def mark_read(service, msg_id: str) -> None:
    service.users().messages().modify(
        userId="me",
        id=msg_id,
        body={"removeLabelIds": ["UNREAD"]}
    ).execute()


def watch() -> None:
    if not GOOGLE_AVAILABLE:
        print("[gmail_watcher] Cannot start — install required libraries first.")
        return

    if not os.path.exists(CREDENTIALS):
        print(f"[gmail_watcher] credentials.json not found at {CREDENTIALS}")
        print("  Download from Google Cloud Console and place next to this script.")
        return

    print(f"[gmail_watcher] Starting — query: '{GMAIL_QUERY}'  (every {POLL_SECONDS}s)")
    service = get_gmail_service()
    os.makedirs(INBOX_DIR, exist_ok=True)

    while True:
        try:
            results  = service.users().messages().list(
                userId="me", q=GMAIL_QUERY
            ).execute()
            messages = results.get("messages", [])

            for msg_ref in messages:
                msg_id   = msg_ref["id"]
                msg_data = service.users().messages().get(
                    userId="me", id=msg_id, format="full"
                ).execute()

                filename, content = email_to_task(msg_data)
                dest = os.path.join(INBOX_DIR, filename)

                with open(dest, "w", encoding="utf-8") as f:
                    f.write(content)

                mark_read(service, msg_id)
                print(f"[{datetime.now():%H:%M:%S}] EMAIL→TASK  {filename}")

        except Exception as exc:
            print(f"[gmail_watcher] ERROR: {exc}")

        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    watch()
