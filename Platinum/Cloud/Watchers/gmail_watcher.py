"""
gmail_watcher.py — Gmail Watcher (Platinum Cloud)
--------------------------------------------------
Polls Gmail inbox every 60s for unread emails.
Converts each email -> task file in Platinum/Needs_Action/cloud/
Marks email as read after processing.

Extends BaseWatcher from Shared/.

Setup:
  1. Enable Gmail API in Google Cloud Console
  2. Download credentials.json -> this folder (never commit)
  3. First run: pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client
  4. First run will open browser for OAuth -> saves token.json (never commit)

Run:
  python Cloud/Watchers/gmail_watcher.py
"""

import os
import sys
import base64
import re
from datetime import datetime
from email import message_from_bytes

# ── Paths ─────────────────────────────────────────────────────────────────────

CLOUD_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLATINUM_DIR = os.path.dirname(CLOUD_DIR)
SHARED_DIR   = os.path.join(PLATINUM_DIR, "Shared")

sys.path.insert(0, PLATINUM_DIR)

from Shared.base_watcher import BaseWatcher
from Shared.retry_handler import with_retry

INBOX_DIR       = os.path.join(PLATINUM_DIR, "Needs_Action", "cloud")
CREDENTIALS_FILE = os.path.join(CLOUD_DIR, "credentials.json")   # NEVER commit
TOKEN_FILE       = os.path.join(CLOUD_DIR, "token.json")         # NEVER commit

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

POLL_SECONDS = 60
SKILL        = "GmailWatcher_Platinum"


# ── Auth ──────────────────────────────────────────────────────────────────────

def get_gmail_service():
    """Authenticate and return Gmail API service object."""
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError:
        print("[gmail_watcher] ERROR: pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client")
        raise SystemExit(1)

    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                print(f"[gmail_watcher] credentials.json not found at: {CREDENTIALS_FILE}")
                raise SystemExit(1)
            flow  = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


# ── GmailWatcher ──────────────────────────────────────────────────────────────

class GmailWatcher(BaseWatcher):

    def __init__(self):
        super().__init__(SKILL, poll_seconds=POLL_SECONDS)
        self.service = None

    def on_start(self) -> None:
        os.makedirs(INBOX_DIR, exist_ok=True)
        print(f"[{self.skill}] Authenticating with Gmail...")
        self.service = get_gmail_service()
        print(f"[{self.skill}] Gmail connected. Dropping tasks to: {INBOX_DIR}")

    @with_retry(max_attempts=3, delay=5.0, exceptions=(Exception,))
    def poll(self) -> list[dict]:
        """Fetch unread emails from INBOX."""
        result = self.service.users().messages().list(
            userId="me",
            labelIds=["INBOX", "UNREAD"],
            maxResults=10,
        ).execute()

        messages = result.get("messages", [])
        items    = []

        for msg_ref in messages:
            msg = self.service.users().messages().get(
                userId="me",
                id=msg_ref["id"],
                format="full",
            ).execute()
            items.append(msg)

        return items

    def process(self, item: dict) -> None:
        """Convert email to task file in Needs_Action/cloud/."""
        start = datetime.now()
        msg_id = item["id"]

        # Extract headers
        headers = {h["name"]: h["value"] for h in item.get("payload", {}).get("headers", [])}
        subject  = headers.get("Subject", "(no subject)")
        sender   = headers.get("From", "unknown")
        date_str = headers.get("Date", "")

        # Extract body text
        body = self._extract_body(item)

        # Build task filename
        ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
        slug     = re.sub(r"[^a-zA-Z0-9_-]", "_", subject)[:40].strip("_")
        filename = f"EMAIL_{ts}_{slug}.md"
        filepath = os.path.join(INBOX_DIR, filename)

        # Write task file
        content = f"""# Task: Email — {subject}

**Priority:** Medium
**Created:** {datetime.now().strftime("%Y-%m-%d")}
**Tier:** Platinum
**Source:** Gmail
**From:** {sender}
**Date:** {date_str}
**Gmail-ID:** {msg_id}

## Email Body

{body.strip() if body else "_[No text body]_"}

## Steps

- Step 1: Email read karo aur intent/request samjho
- Step 2: Draft reply banao (email_drafter chalao)
- Step 3: Draft Pending_Approval/cloud/ mein rakh do
- Step 4: Local approval ka wait karo
- Step 5: Approved? -> Local MCP se email send karo

## Acceptance Criteria

- [ ] Email ka intent identified
- [ ] Reply draft Pending_Approval/cloud/ mein
- [ ] Approval milne ke baad reply sent

## Notes

Auto-generated from Gmail via Platinum GmailWatcher.
Original sender: {sender}
"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        # Mark email as read
        self.service.users().messages().modify(
            userId="me",
            id=msg_id,
            body={"removeLabelIds": ["UNREAD"]},
        ).execute()

        duration_ms = int((datetime.now() - start).total_seconds() * 1000)
        print(f"[{datetime.now():%H:%M:%S}] EMAIL->TASK  {filename}")
        self.log.log(self.skill, "email_to_task", "success",
                     duration_ms=duration_ms,
                     task_id=filename,
                     detail=f"from={sender[:50]}")

    # ── Body extraction ───────────────────────────────────────────────────────

    def _extract_body(self, msg: dict) -> str:
        """Extract plain text body from Gmail message."""
        payload = msg.get("payload", {})
        return self._walk_parts(payload)

    def _walk_parts(self, payload: dict) -> str:
        mime_type = payload.get("mimeType", "")
        body_data = payload.get("body", {}).get("data", "")

        if mime_type == "text/plain" and body_data:
            return base64.urlsafe_b64decode(body_data).decode("utf-8", errors="replace")

        for part in payload.get("parts", []):
            result = self._walk_parts(part)
            if result:
                return result

        return ""


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    watcher = GmailWatcher()
    watcher.run()
