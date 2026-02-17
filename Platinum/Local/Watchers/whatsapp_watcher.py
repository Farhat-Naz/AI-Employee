"""
whatsapp_watcher.py — WhatsApp Watcher (Platinum Local)
--------------------------------------------------------
Polls Green API every 5s for incoming WhatsApp messages.
Converts messages to task files in Platinum/Needs_Action/local/
Uses same Green API instance as Silver/Gold (shared config).

Config: read from Silver/Watchers/whatsapp_config.json
  (or set WA_INSTANCE_ID + WA_API_TOKEN in .env)

Extends BaseWatcher from Shared/.

Run:
  python Local/Watchers/whatsapp_watcher.py
"""

import os
import sys
import re
import json
from datetime import datetime

LOCAL_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLATINUM_DIR = os.path.dirname(LOCAL_DIR)
VAULT_ROOT   = os.path.dirname(PLATINUM_DIR)

sys.path.insert(0, PLATINUM_DIR)

from Shared.base_watcher import BaseWatcher

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("[wa_watcher:platinum] WARNING: pip install requests")

# ── Paths ─────────────────────────────────────────────────────────────────────

INBOX_DIR = os.path.join(PLATINUM_DIR, "Needs_Action", "local")

# Config: try Silver config first, then .env, then fail
SILVER_CONFIG = os.path.join(VAULT_ROOT, "Silver", "Watchers", "whatsapp_config.json")

POLL_SECONDS = 5
SKILL        = "WA_Watcher_Platinum"


# ── Config ────────────────────────────────────────────────────────────────────

def load_config() -> dict:
    # Option 1: Silver shared config
    if os.path.exists(SILVER_CONFIG):
        with open(SILVER_CONFIG, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        print(f"[{SKILL}] Config loaded from Silver")
        return cfg

    # Option 2: environment variables
    instance_id = os.environ.get("WA_INSTANCE_ID", "")
    api_token   = os.environ.get("WA_API_TOKEN", "")
    allowed     = os.environ.get("WA_ALLOWED_NUMBERS", "")

    if instance_id and api_token:
        print(f"[{SKILL}] Config loaded from environment")
        return {
            "instance_id":     instance_id,
            "api_token":       api_token,
            "allowed_numbers": [n.strip() for n in allowed.split(",") if n.strip()],
        }

    print(f"[{SKILL}] ERROR: No config found.")
    print(f"  Option 1: Copy Silver/Watchers/whatsapp_config.json (already done if Silver working)")
    print(f"  Option 2: Set WA_INSTANCE_ID + WA_API_TOKEN in .env")
    raise SystemExit(1)


# ── WhatsApp Watcher ──────────────────────────────────────────────────────────

class WhatsAppWatcher(BaseWatcher):

    def __init__(self):
        super().__init__(SKILL, poll_seconds=POLL_SECONDS)

        if not REQUESTS_AVAILABLE:
            print(f"[{SKILL}] Cannot start — pip install requests")
            raise SystemExit(1)

        cfg                  = load_config()
        self.instance_id     = cfg["instance_id"]
        self.api_token       = cfg["api_token"]
        self.allowed_numbers = cfg.get("allowed_numbers", [])
        self.base_url        = f"https://api.green-api.com/waInstance{self.instance_id}"

    def on_start(self) -> None:
        os.makedirs(INBOX_DIR, exist_ok=True)
        print(f"[{self.skill}] Instance: {self.instance_id}")
        print(f"[{self.skill}] Dropping tasks to: {INBOX_DIR}")
        if self.allowed_numbers:
            print(f"[{self.skill}] Allowed numbers: {self.allowed_numbers}")

    def poll(self) -> list[dict]:
        """Poll one notification from Green API."""
        url = f"{self.base_url}/receiveNotification/{self.api_token}"
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            return [data] if data else []
        except requests.exceptions.RequestException as e:
            print(f"[{self.skill}] Poll error: {e}")
            return []

    def process(self, item: dict) -> None:
        """Handle one WhatsApp notification."""
        receipt_id = item.get("receiptId")
        start      = datetime.now()

        try:
            text = self._extract_text(item)
            if text is None:
                self.log.log(self.skill, "skip_non_text", "skipped")
                return

            phone, name = self._get_sender(item)

            if not self._is_allowed(phone):
                print(f"[{datetime.now():%H:%M:%S}] IGNORED  +{phone} (not allowed)")
                self.log.log(self.skill, "msg_ignored", "filtered", detail=f"+{phone}")
                return

            filename, content = self._message_to_task(text, phone, name)
            dest = os.path.join(INBOX_DIR, filename)

            with open(dest, "w", encoding="utf-8") as f:
                f.write(content)

            duration_ms = int((datetime.now() - start).total_seconds() * 1000)
            print(f"[{datetime.now():%H:%M:%S}] WA->TASK  {filename}  (from {name})")
            self.log.log(self.skill, "msg_to_task", "success",
                         duration_ms=duration_ms,
                         detail=f"from={name}(+{phone})")

        finally:
            if receipt_id is not None:
                self._delete(receipt_id)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _extract_text(self, notification: dict) -> str | None:
        body         = notification.get("body", {})
        webhook_type = body.get("typeWebhook", "")
        if webhook_type != "incomingMessageReceived":
            return None
        msg_data = body.get("messageData", {})
        msg_type = msg_data.get("typeMessage", "")
        if msg_type == "textMessage":
            return msg_data.get("textMessageData", {}).get("textMessage", "")
        if msg_type == "extendedTextMessage":
            return msg_data.get("extendedTextMessageData", {}).get("text", "")
        return None

    def _get_sender(self, notification: dict) -> tuple[str, str]:
        sender_data = notification.get("body", {}).get("senderData", {})
        chat_id     = sender_data.get("chatId", "unknown")
        name        = sender_data.get("senderName", chat_id)
        phone       = chat_id.replace("@c.us", "").replace("@g.us", "")
        return phone, name

    def _is_allowed(self, phone: str) -> bool:
        if not self.allowed_numbers:
            return True
        digits = re.sub(r"\D", "", phone)
        for num in self.allowed_numbers:
            if digits.endswith(re.sub(r"\D", "", num)):
                return True
        return False

    def _delete(self, receipt_id: int) -> None:
        url = f"{self.base_url}/deleteNotification/{self.api_token}/{receipt_id}"
        try:
            requests.delete(url, timeout=10)
        except requests.exceptions.RequestException:
            pass

    def _message_to_task(self, text: str, phone: str, name: str) -> tuple[str, str]:
        ts       = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        slug     = re.sub(r"[^a-zA-Z0-9_-]", "_", name)[:30].strip("_")
        filename = f"WA_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{slug}.md"

        content = f"""# Task: WhatsApp from {name}

**Priority:** Medium
**Created:** {datetime.now().strftime("%Y-%m-%d")}
**Tier:** Platinum
**Source:** WhatsApp — {name} (+{phone})
**Received At:** {ts}

## Message

{text.strip()}

## Steps

- Step 1: Message ko review karo aur intent samjho
- Step 2: Response plan banao
- Step 3: Approval route karo if needed (Pending_Approval/local/)
- Step 4: Reply/confirmation update karo in Done/

## Acceptance Criteria

- [ ] Request of {name} addressed
- [ ] Reply sent if needed: +{phone}

## Notes

Auto-generated from WhatsApp via Green API (Platinum Local).
Sender: {name} | Phone: +{phone}
"""
        return filename, content


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    watcher = WhatsAppWatcher()
    watcher.run()
