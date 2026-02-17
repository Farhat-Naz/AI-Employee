"""
file_watcher.py — Internal Watcher (Silver Tier)
-------------------------------------------------
Monitors the /Inbox folder for new .md task files.
When a file appears, enriches it with metadata and
moves it to /Needs_Action for the agent to process.

Skill: Scan Inbox (Bronze) + Task Classification (Silver)
"""

import os
import time
import shutil
from datetime import datetime

# ── Configuration ────────────────────────────────────────────────────────────
BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INBOX_DIR    = os.path.join(BASE_DIR, "Inbox")
ACTION_DIR   = os.path.join(BASE_DIR, "Needs_Action")
POLL_SECONDS = 5          # how often to check Inbox

# Keywords used to auto-classify risk level
HIGH_RISK_KEYWORDS   = ["delete", "deploy", "production", "billing", "payment", "cloud"]
MEDIUM_RISK_KEYWORDS = ["update", "modify", "push", "send", "email"]


# ── Helpers ───────────────────────────────────────────────────────────────────

def classify_risk(content: str) -> str:
    """Return 'high', 'medium', or 'low' based on task content."""
    lower = content.lower()
    if any(kw in lower for kw in HIGH_RISK_KEYWORDS):
        return "high"
    if any(kw in lower for kw in MEDIUM_RISK_KEYWORDS):
        return "medium"
    return "low"


def needs_approval(content: str, risk: str) -> bool:
    """Return True if task should be routed to Awaiting_Approval."""
    return "approval: required" in content.lower() or risk == "high"


def inject_metadata(filepath: str) -> str:
    """Read file, prepend Silver Tier metadata block, return enriched content."""
    with open(filepath, "r", encoding="utf-8") as f:
        original = f.read()

    risk      = classify_risk(original)
    approval  = "required" if needs_approval(original, risk) else "not_required"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    metadata_block = (
        f"<!-- AGENT METADATA\n"
        f"  received_at : {timestamp}\n"
        f"  source      : file_watcher (internal)\n"
        f"  risk_level  : {risk}\n"
        f"  approval    : {approval}\n"
        f"  retries     : 0\n"
        f"-->\n\n"
    )
    return metadata_block + original


def move_to_needs_action(filename: str) -> None:
    src  = os.path.join(INBOX_DIR, filename)
    dst  = os.path.join(ACTION_DIR, filename)

    enriched = inject_metadata(src)

    with open(dst, "w", encoding="utf-8") as f:
        f.write(enriched)

    os.remove(src)
    print(f"[{datetime.now():%H:%M:%S}] MOVED  {filename}  →  Needs_Action/")


# ── Main loop ─────────────────────────────────────────────────────────────────

def watch() -> None:
    print(f"[file_watcher] Watching  {INBOX_DIR}  (every {POLL_SECONDS}s)")
    seen: set[str] = set()

    while True:
        try:
            files = {
                f for f in os.listdir(INBOX_DIR)
                if f.endswith(".md") and not f.startswith(".")
            }
            new_files = files - seen

            for filename in sorted(new_files):
                print(f"[{datetime.now():%H:%M:%S}] DETECTED  {filename}")
                move_to_needs_action(filename)

            seen = files - new_files   # keep only files still in Inbox

        except Exception as exc:
            print(f"[file_watcher] ERROR: {exc}")

        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    os.makedirs(INBOX_DIR,  exist_ok=True)
    os.makedirs(ACTION_DIR, exist_ok=True)
    watch()
