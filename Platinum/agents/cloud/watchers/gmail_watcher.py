"""
Gmail Watcher — Cloud Agent
Monitors Gmail for unread/important emails.
Writes each email as a .md file into Vault/Needs_Action/cloud/
"""

import os
import base64
import json
from pathlib import Path
from datetime import datetime

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from base_watcher import BaseWatcher

# Only read access needed — we never send from Cloud
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly',
          'https://www.googleapis.com/auth/gmail.modify']

PROCESSED_IDS_FILE = Path(__file__).parent / '.processed_ids.json'


class GmailWatcher(BaseWatcher):
    def __init__(self, vault_path: str, credentials_path: str):
        super().__init__(vault_path, check_interval=120)  # check every 2 min
        self.credentials_path = Path(credentials_path)
        self.token_path = self.credentials_path.parent / 'token.json'
        self.service = self._authenticate()
        self.processed_ids = self._load_processed_ids()

    # ------------------------------------------------------------------ auth
    def _authenticate(self):
        creds = None

        if self.token_path.exists():
            creds = Credentials.from_authorized_user_file(str(self.token_path), SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path), SCOPES)
                creds = flow.run_local_server(port=0)
            self.token_path.write_text(creds.to_json())
            self.logger.info(f'Token saved to {self.token_path}')

        return build('gmail', 'v1', credentials=creds)

    # ------------------------------------------------- processed IDs (cache)
    def _load_processed_ids(self) -> set:
        if PROCESSED_IDS_FILE.exists():
            return set(json.loads(PROCESSED_IDS_FILE.read_text()))
        return set()

    def _save_processed_ids(self):
        PROCESSED_IDS_FILE.write_text(json.dumps(list(self.processed_ids)))

    # ----------------------------------------------- BaseWatcher interface
    def check_for_updates(self) -> list:
        results = self.service.users().messages().list(
            userId='me',
            q='is:unread is:important',
            maxResults=10
        ).execute()

        messages = results.get('messages', [])
        new = [m for m in messages if m['id'] not in self.processed_ids]
        self.logger.info(f'Found {len(new)} new important emails')
        return new

    def create_action_file(self, message: dict) -> Path:
        msg = self.service.users().messages().get(
            userId='me',
            id=message['id'],
            format='full'
        ).execute()

        headers = {h['name']: h['value'] for h in msg['payload']['headers']}
        sender  = headers.get('From', 'Unknown')
        subject = headers.get('Subject', '(No Subject)')
        date    = headers.get('Date', datetime.now().isoformat())
        snippet = msg.get('snippet', '')

        # Safe filename
        safe_id = message['id'][:12]
        filename = f'EMAIL_{safe_id}.md'
        filepath = self.needs_action / filename

        content = f"""---
type: email
id: {message['id']}
from: {sender}
subject: {subject}
received: {date}
created: {datetime.now().isoformat()}
priority: high
status: needs_action
agent_owner: cloud
---

## From
{sender}

## Subject
{subject}

## Preview
{snippet}

## Suggested Actions
- [ ] Draft reply
- [ ] Move to /Pending_Approval/cloud/ after drafting
- [ ] Local Agent to review and send

---
*Created by Cloud Gmail Watcher*
"""
        filepath.write_text(content, encoding='utf-8')

        # Mark as processed so we don't re-create
        self.processed_ids.add(message['id'])
        self._save_processed_ids()

        return filepath


# ------------------------------------------------------------------ entrypoint
if __name__ == '__main__':
    VAULT_PATH = os.getenv('VAULT_PATH', r'D:\quarterr 4\personalAI\Platinum\Vault')
    CREDS_PATH = os.getenv('GMAIL_CREDENTIALS', r'D:\quarterr 4\personalAI\Platinum\credentials.json')

    watcher = GmailWatcher(vault_path=VAULT_PATH, credentials_path=CREDS_PATH)
    watcher.run()
