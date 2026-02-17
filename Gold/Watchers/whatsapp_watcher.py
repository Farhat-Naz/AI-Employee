"""
whatsapp_watcher.py — External Watcher (Gold Tier)
---------------------------------------------------
Silver tier watcher ka Gold upgrade:
  - Drops tasks into Gold/Inbox/
  - Every action logged via AuditLogger
  - Config shared with Silver/Watchers/whatsapp_config.json

Run:
  python Gold/Watchers/whatsapp_watcher.py
"""

import os
import json
import time
import re
import sys
from datetime import datetime

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("[whatsapp_watcher:gold] WARNING: pip install requests")

# ── Paths ─────────────────────────────────────────────────────────────────────

GOLD_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INBOX_DIR   = os.path.join(GOLD_DIR, "Inbox")

# Config shared from Silver tier
SILVER_DIR  = os.path.join(os.path.dirname(GOLD_DIR), "Silver")
CONFIG_FILE = os.path.join(SILVER_DIR, "Watchers", "whatsapp_config.json")

# Audit logger from Gold/
sys.path.insert(0, GOLD_DIR)
from audit_logger import AuditLogger

POLL_SECONDS = 5
SKILL        = "WA_Watcher_Gold"


# ── Config ────────────────────────────────────────────────────────────────────

def load_config() -> dict:
    if not os.path.exists(CONFIG_FILE):
        print(f"[whatsapp_watcher:gold] Config not found: {CONFIG_FILE}")
        raise SystemExit(1)
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    missing = [k for k in ["instance_id", "api_token"] if not cfg.get(k)]
    if missing:
        print(f"[whatsapp_watcher:gold] Missing config keys: {missing}")
        raise SystemExit(1)
    return cfg


# ── Green API ─────────────────────────────────────────────────────────────────

def receive_notification(base_url: str, api_token: str) -> dict | None:
    url = f"{base_url}/receiveNotification/{api_token}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data if data else None
    except requests.exceptions.RequestException as e:
        print(f"[whatsapp_watcher:gold] Poll error: {e}")
        return None


def delete_notification(base_url: str, api_token: str, receipt_id: int) -> None:
    url = f"{base_url}/deleteNotification/{api_token}/{receipt_id}"
    try:
        requests.delete(url, timeout=10)
    except requests.exceptions.RequestException as e:
        print(f"[whatsapp_watcher:gold] Delete error: {e}")


# ── Message Parsing ───────────────────────────────────────────────────────────

def extract_text(notification: dict) -> str | None:
    body         = notification.get("body", {})
    webhook_type = body.get("typeWebhook", "")
    if webhook_type != "incomingMessageReceived":
        return None
    msg_data = body.get("messageData", {})
    msg_type = msg_data.get("typeMessage", "")
    if msg_type == "textMessage":
        return msg_data.get("textMessageData", {}).get("textMessage", "")
    elif msg_type == "extendedTextMessage":
        return msg_data.get("extendedTextMessageData", {}).get("text", "")
    return None


def get_sender(notification: dict) -> tuple[str, str]:
    sender_data = notification.get("body", {}).get("senderData", {})
    chat_id     = sender_data.get("chatId", "unknown")
    name        = sender_data.get("senderName", chat_id)
    phone       = chat_id.replace("@c.us", "").replace("@g.us", "")
    return phone, name


def is_allowed_sender(phone: str, allowed_numbers: list[str]) -> bool:
    if not allowed_numbers:
        return True
    digits = re.sub(r"\D", "", phone)
    for num in allowed_numbers:
        if digits.endswith(re.sub(r"\D", "", num)):
            return True
    return False


# ── Message -> Task ───────────────────────────────────────────────────────────

def message_to_task(text: str, phone: str, name: str) -> tuple[str, str]:
    ts       = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    slug     = re.sub(r"[^a-zA-Z0-9_-]", "_", name)[:30].strip("_")
    filename = f"WA_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{slug}.md"

    content = f"""# Task: WhatsApp from {name}

**Priority:** Medium
**Created:** {datetime.now().strftime("%Y-%m-%d")}
**Tier:** Gold
**Source:** WhatsApp — {name} (+{phone})
**Received At:** {ts}

## Message

{text.strip()}

## Steps

- Step 1: Message ko review karo aur intent samjho
- Step 2: Action plan banao based on request
- Step 3: Task execute karo ya approval route karo
- Step 4: Reply/confirmation update karo in Done/

## Acceptance Criteria

- [ ] Request of {name} addressed
- [ ] Reply sent if needed: +{phone}

## Notes

Auto-generated from WhatsApp via Green API (Gold Tier).
Sender: {name} | Phone: +{phone}
"""
    return filename, content


# ── Main Loop ─────────────────────────────────────────────────────────────────

def watch() -> None:
    if not REQUESTS_AVAILABLE:
        print("[whatsapp_watcher:gold] Cannot start — pip install requests")
        return

    log             = AuditLogger()
    cfg             = load_config()
    instance_id     = cfg["instance_id"]
    api_token       = cfg["api_token"]
    allowed_numbers = cfg.get("allowed_numbers", [])
    base_url        = f"https://api.green-api.com/waInstance{instance_id}"

    os.makedirs(INBOX_DIR, exist_ok=True)

    print(f"[whatsapp_watcher:gold] Starting — instance: {instance_id}")
    print(f"[whatsapp_watcher:gold] Dropping tasks into: {INBOX_DIR}")
    if allowed_numbers:
        print(f"[whatsapp_watcher:gold] Allowed: {allowed_numbers}")

    log.log(SKILL, "watcher_start", "success", detail=f"instance={instance_id}")

    while True:
        notification = receive_notification(base_url, api_token)

        if notification is None:
            time.sleep(POLL_SECONDS)
            continue

        receipt_id = notification.get("receiptId")
        start_time = datetime.now()

        try:
            text = extract_text(notification)

            if text is None:
                log.log(SKILL, "skip_non_text", "skipped")
            else:
                phone, name = get_sender(notification)

                if not is_allowed_sender(phone, allowed_numbers):
                    print(f"[{datetime.now():%H:%M:%S}] IGNORED  +{phone} (not allowed)")
                    log.log(SKILL, "msg_ignored", "filtered", detail=f"+{phone}")
                else:
                    filename, content = message_to_task(text, phone, name)
                    dest = os.path.join(INBOX_DIR, filename)

                    with open(dest, "w", encoding="utf-8") as f:
                        f.write(content)

                    duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                    print(f"[{datetime.now():%H:%M:%S}] WA->TASK  {filename}  (from {name})")
                    log.log(SKILL, "msg_to_task", "success",
                            duration_ms=duration_ms,
                            detail=f"from={name}(+{phone}) file={filename}")

        except Exception as exc:
            log.log_error(SKILL, "process_notification", str(exc))
            print(f"[whatsapp_watcher:gold] ERROR: {exc}")

        finally:
            if receipt_id is not None:
                delete_notification(base_url, api_token, receipt_id)


if __name__ == "__main__":
    watch()
