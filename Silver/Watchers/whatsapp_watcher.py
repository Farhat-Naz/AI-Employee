"""
whatsapp_watcher.py — External Watcher (Silver Tier)
-----------------------------------------------------
Polls a Green API instance for incoming WhatsApp messages.
Converts each message into a structured task file and drops
it into /Inbox for file_watcher.py to pick up and classify.

Skill: External Watcher — WhatsApp (Silver Tier)

Prerequisites:
  pip install requests

Setup:
  1. Green API pe account banao: https://console.green-api.com
  2. Naya instance create karo, WhatsApp scan karo
  3. Instance ID aur API Token copy karo
  4. whatsapp_config.json mein paste karo
  5. python Silver/Watchers/whatsapp_watcher.py

Green API Docs: https://green-api.com/en/docs/api/receiving/
"""

import os
import json
import time
import re
from datetime import datetime

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("[whatsapp_watcher] WARNING: requests library not installed.")
    print("  Run: pip install requests")


# ── Configuration ─────────────────────────────────────────────────────────────

BASE_DIR      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INBOX_DIR     = os.path.join(BASE_DIR, "Inbox")
WATCHER_DIR   = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE   = os.path.join(WATCHER_DIR, "whatsapp_config.json")

POLL_SECONDS  = 5   # Green API short-poll interval (recommended: 5s)


# ── Load Config ───────────────────────────────────────────────────────────────

def load_config() -> dict:
    """Load whatsapp_config.json and validate required keys."""
    if not os.path.exists(CONFIG_FILE):
        print(f"[whatsapp_watcher] ERROR: Config file not found: {CONFIG_FILE}")
        print("  Copy whatsapp_config.json.example and fill in your credentials.")
        raise SystemExit(1)

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    required = ["instance_id", "api_token"]
    missing  = [k for k in required if not cfg.get(k)]
    if missing:
        print(f"[whatsapp_watcher] ERROR: Missing config keys: {missing}")
        raise SystemExit(1)

    return cfg


# ── Green API Helpers ─────────────────────────────────────────────────────────

def get_base_url(instance_id: str) -> str:
    return f"https://api.green-api.com/waInstance{instance_id}"


def receive_notification(base_url: str, api_token: str) -> dict | None:
    """
    Poll Green API for one pending notification.
    Returns the notification dict or None if queue is empty.
    """
    url = f"{base_url}/receiveNotification/{api_token}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data if data else None
    except requests.exceptions.RequestException as e:
        print(f"[whatsapp_watcher] Poll error: {e}")
        return None


def delete_notification(base_url: str, api_token: str, receipt_id: int) -> None:
    """Remove a processed notification from Green API queue."""
    url = f"{base_url}/deleteNotification/{api_token}/{receipt_id}"
    try:
        requests.delete(url, timeout=10)
    except requests.exceptions.RequestException as e:
        print(f"[whatsapp_watcher] Delete error (receiptId={receipt_id}): {e}")


# ── Message Parsing ───────────────────────────────────────────────────────────

def extract_text(notification: dict) -> str | None:
    """
    Extract plain text from a Green API notification body.
    Returns None if message type is not text.
    """
    body = notification.get("body", {})
    webhook_type = body.get("typeWebhook", "")

    if webhook_type != "incomingMessageReceived":
        return None  # ignore receipts, outgoing, etc.

    msg_data = body.get("messageData", {})
    msg_type = msg_data.get("typeMessage", "")

    if msg_type == "textMessage":
        return msg_data.get("textMessageData", {}).get("textMessage", "")
    elif msg_type == "extendedTextMessage":
        return msg_data.get("extendedTextMessageData", {}).get("text", "")

    return None  # image, audio, sticker, etc. — skip


def get_sender(notification: dict) -> tuple[str, str]:
    """Return (phone_number, display_name) of the message sender."""
    sender_data = notification.get("body", {}).get("senderData", {})
    chat_id     = sender_data.get("chatId", "unknown")           # e.g. "923001234567@c.us"
    name        = sender_data.get("senderName", chat_id)
    # Strip the @c.us suffix to get the raw phone number
    phone = chat_id.replace("@c.us", "").replace("@g.us", "")
    return phone, name


def is_allowed_sender(phone: str, allowed_numbers: list[str]) -> bool:
    """
    Return True if allowed_numbers is empty (accept all)
    OR phone is in the allowed list.
    Strip non-digits for comparison.
    """
    if not allowed_numbers:
        return True
    digits = re.sub(r"\D", "", phone)
    for num in allowed_numbers:
        if digits.endswith(re.sub(r"\D", "", num)):
            return True
    return False


# ── WhatsApp Message → Task File ──────────────────────────────────────────────

def safe_filename(sender_name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]", "_", sender_name)[:30].strip("_")
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"WA_{ts}_{slug}.md"


def message_to_task(text: str, phone: str, name: str) -> tuple[str, str]:
    """Return (filename, markdown_content) for the task file."""
    ts       = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filename = safe_filename(name)

    content = f"""# Task: WhatsApp Message from {name}

**Priority:** Medium
**Created:** {datetime.now().strftime("%Y-%m-%d")}
**Owner:** WhatsApp Watcher (external)
**Source:** WhatsApp — {name} ({phone})
**Received At:** {ts}

## Message

{text.strip()}

## Acceptance Criteria

- [ ] Review and action the request from {name}
- [ ] Reply on WhatsApp if needed: +{phone}

## Notes

Auto-generated from WhatsApp via Green API.
Sender: {name} | Phone: +{phone}
"""
    return filename, content


# ── Main Loop ─────────────────────────────────────────────────────────────────

def watch() -> None:
    if not REQUESTS_AVAILABLE:
        print("[whatsapp_watcher] Cannot start — install: pip install requests")
        return

    cfg             = load_config()
    instance_id     = cfg["instance_id"]
    api_token       = cfg["api_token"]
    allowed_numbers = cfg.get("allowed_numbers", [])   # empty = accept all

    base_url = get_base_url(instance_id)
    os.makedirs(INBOX_DIR, exist_ok=True)

    print(f"[whatsapp_watcher] Starting — instance: {instance_id}  (every {POLL_SECONDS}s)")
    if allowed_numbers:
        print(f"[whatsapp_watcher] Filtering — only from: {allowed_numbers}")
    else:
        print("[whatsapp_watcher] No filter — accepting messages from all numbers")

    while True:
        notification = receive_notification(base_url, api_token)

        if notification is None:
            # Queue empty — wait and poll again
            time.sleep(POLL_SECONDS)
            continue

        receipt_id = notification.get("receiptId")

        try:
            text = extract_text(notification)

            if text is None:
                # Not a text message (image, receipt, etc.) — delete and skip
                pass
            else:
                phone, name = get_sender(notification)

                if not is_allowed_sender(phone, allowed_numbers):
                    print(f"[{datetime.now():%H:%M:%S}] IGNORED  msg from {phone} (not in allowed list)")
                else:
                    filename, content = message_to_task(text, phone, name)
                    dest = os.path.join(INBOX_DIR, filename)

                    with open(dest, "w", encoding="utf-8") as f:
                        f.write(content)

                    print(f"[{datetime.now():%H:%M:%S}] WA→TASK  {filename}  (from {name} / +{phone})")

        except Exception as exc:
            print(f"[whatsapp_watcher] ERROR processing notification: {exc}")

        finally:
            # Always delete the notification to dequeue it
            if receipt_id is not None:
                delete_notification(base_url, api_token, receipt_id)

        # Green API: no sleep between polls when queue has items
        # (loop immediately to drain the queue)


if __name__ == "__main__":
    watch()
