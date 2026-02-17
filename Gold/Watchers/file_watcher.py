"""
file_watcher.py — Internal Watcher (Gold Tier)
-----------------------------------------------
Silver file_watcher ka Gold upgrade:
  - Inbox monitor karta hai (every 5s)
  - Risk classify + metadata inject karta hai
  - High-risk -> Awaiting_Approval/
  - Low/Medium -> Needs_Action/ + Ralph Wiggum Loop auto-trigger

Run:
  python Gold/Watchers/file_watcher.py
"""

import os
import sys
import time
import subprocess
from datetime import datetime

# ── Paths ─────────────────────────────────────────────────────────────────────

GOLD_DIR         = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INBOX_DIR        = os.path.join(GOLD_DIR, "Inbox")
ACTION_DIR       = os.path.join(GOLD_DIR, "Needs_Action")
APPROVAL_DIR     = os.path.join(GOLD_DIR, "Awaiting_Approval")
RALPH_LOOP_PATH  = os.path.join(GOLD_DIR, "ralph_loop.py")

sys.path.insert(0, GOLD_DIR)
from audit_logger import AuditLogger

POLL_SECONDS = 5
SKILL        = "FileWatcher_Gold"

HIGH_RISK_KEYWORDS   = ["delete", "deploy", "production", "billing", "payment", "cloud"]
MEDIUM_RISK_KEYWORDS = ["update", "modify", "push", "send", "email"]


# ── Classification ────────────────────────────────────────────────────────────

def classify_risk(content: str) -> str:
    lower = content.lower()
    if any(kw in lower for kw in HIGH_RISK_KEYWORDS):
        return "high"
    if any(kw in lower for kw in MEDIUM_RISK_KEYWORDS):
        return "medium"
    return "low"


def needs_approval(content: str, risk: str) -> bool:
    return "approval: required" in content.lower() or risk == "high"


def inject_metadata(filepath: str) -> tuple[str, str, str]:
    """Read file, prepend Gold Tier metadata. Return (enriched_content, risk, approval)."""
    with open(filepath, "r", encoding="utf-8") as f:
        original = f.read()

    risk     = classify_risk(original)
    approval = "required" if needs_approval(original, risk) else "not_required"
    ts       = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    metadata = (
        f"<!-- AGENT METADATA\n"
        f"  received_at : {ts}\n"
        f"  source      : file_watcher (Gold)\n"
        f"  tier        : gold\n"
        f"  risk_level  : {risk}\n"
        f"  approval    : {approval}\n"
        f"  retries     : 0\n"
        f"-->\n\n"
    )
    return metadata + original, risk, approval


# ── Process one file ──────────────────────────────────────────────────────────

def process_file(filename: str, log: AuditLogger) -> None:
    src   = os.path.join(INBOX_DIR, filename)
    start = datetime.now()

    enriched, risk, approval = inject_metadata(src)

    if approval == "required":
        dst   = os.path.join(APPROVAL_DIR, filename)
        label = "Awaiting_Approval"
    else:
        dst   = os.path.join(ACTION_DIR, filename)
        label = "Needs_Action"

    with open(dst, "w", encoding="utf-8") as f:
        f.write(enriched)
    os.remove(src)

    duration_ms = int((datetime.now() - start).total_seconds() * 1000)
    print(f"[{datetime.now():%H:%M:%S}] MOVED  {filename}  ->  {label}/  [risk={risk}]")
    log.log(SKILL, "classify_and_route", label,
            duration_ms=duration_ms,
            task_id=filename,
            detail=f"risk={risk}")

    # Auto-trigger Ralph Wiggum Loop for non-approval tasks
    if approval != "required":
        print(f"[{datetime.now():%H:%M:%S}] TRIGGER  Ralph Loop for {filename}")
        log.log(SKILL, "trigger_ralph_loop", "started", task_id=filename)
        try:
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            result = subprocess.run(
                [sys.executable, RALPH_LOOP_PATH, dst],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=120,
                env=env
            )
            if result.returncode == 0:
                log.log(SKILL, "ralph_loop_done", "success", task_id=filename)
            else:
                log.log(SKILL, "ralph_loop_done", "failed",
                        task_id=filename,
                        detail=(result.stderr or "")[:100])
        except subprocess.TimeoutExpired:
            log.log_error(SKILL, "ralph_loop_done", "timeout", task_id=filename)
        except Exception as exc:
            log.log_error(SKILL, "ralph_loop_done", str(exc), task_id=filename)


# ── Main Loop ─────────────────────────────────────────────────────────────────

def watch() -> None:
    for d in [INBOX_DIR, ACTION_DIR, APPROVAL_DIR]:
        os.makedirs(d, exist_ok=True)

    log  = AuditLogger()
    seen: set[str] = set()

    print(f"[file_watcher:gold] Watching {INBOX_DIR} (every {POLL_SECONDS}s)")
    print(f"[file_watcher:gold] Ralph Loop auto-trigger: ON")
    log.log(SKILL, "watcher_start", "success")

    while True:
        try:
            files     = {f for f in os.listdir(INBOX_DIR)
                         if f.endswith(".md") and not f.startswith(".")}
            new_files = files - seen

            for filename in sorted(new_files):
                print(f"[{datetime.now():%H:%M:%S}] DETECTED  {filename}")
                process_file(filename, log)

            seen = files - new_files

        except Exception as exc:
            log.log_error(SKILL, "watch_loop", str(exc))
            print(f"[file_watcher:gold] ERROR: {exc}")

        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    watch()
