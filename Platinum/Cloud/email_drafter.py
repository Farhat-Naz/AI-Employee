"""
email_drafter.py — Email Drafter Agent (Platinum Cloud)
--------------------------------------------------------
Reads an email task file from In_Progress/cloud/
Creates a draft reply in Pending_Approval/cloud/
Human reviews on Local and approves/rejects.

DRAFT-ONLY rule: This agent NEVER sends emails directly.
Only Local (with human approval) sends.

Usage:
  python Cloud/email_drafter.py In_Progress/cloud/EMAIL_*.md
  # or triggered automatically by file_watcher.py
"""

import os
import sys
import re
from datetime import datetime

CLOUD_DIR    = os.path.dirname(os.path.abspath(__file__))
PLATINUM_DIR = os.path.dirname(CLOUD_DIR)

sys.path.insert(0, PLATINUM_DIR)

from Shared.audit_logger import AuditLogger

PENDING_DIR  = os.path.join(PLATINUM_DIR, "Pending_Approval", "cloud")
DONE_DIR     = os.path.join(PLATINUM_DIR, "Done")
FAILED_DIR   = os.path.join(PLATINUM_DIR, "Failed")
SIGNALS_DIR  = os.path.join(PLATINUM_DIR, "Signals")

SKILL = "EmailDrafter_Platinum"


# ── Draft creation ────────────────────────────────────────────────────────────

def extract_email_info(content: str) -> dict:
    """Parse task file for email metadata."""
    info = {}

    for key, pattern in [
        ("subject", r"\*\*.*?Subject.*?\*\*:?\s*(.+)"),
        ("from",    r"\*\*From:\*\*\s*(.+)"),
        ("date",    r"\*\*Date:\*\*\s*(.+)"),
        ("gmail_id", r"\*\*Gmail-ID:\*\*\s*(.+)"),
    ]:
        m = re.search(pattern, content, re.IGNORECASE)
        info[key] = m.group(1).strip() if m else ""

    # Extract email body
    body_match = re.search(r"## Email Body\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL)
    info["body"] = body_match.group(1).strip() if body_match else ""

    # Extract task title
    title_match = re.search(r"^#\s+Task:\s*(.+)", content, re.MULTILINE)
    info["title"] = title_match.group(1).strip() if title_match else "Email"

    return info


def generate_draft_reply(info: dict) -> str:
    """Generate a draft reply based on email content."""
    sender   = info.get("from", "")
    subject  = info.get("subject", "")
    body     = info.get("body", "")

    # Extract first name from sender
    name_match = re.match(r"([A-Za-z]+)", sender)
    first_name = name_match.group(1) if name_match else "Sir/Madam"

    # Simple intent detection
    body_lower = body.lower()

    if any(kw in body_lower for kw in ["invoice", "bill", "payment", "amount due"]):
        reply_body = (
            f"Dear {first_name},\n\n"
            f"Thank you for your message regarding the invoice/payment.\n\n"
            f"I have received your request and will review the details shortly. "
            f"I will get back to you with a full response within 24 hours.\n\n"
            f"Best regards,\n[YOUR NAME]"
        )
        category = "billing_inquiry"

    elif any(kw in body_lower for kw in ["meeting", "call", "schedule", "appointment"]):
        reply_body = (
            f"Dear {first_name},\n\n"
            f"Thank you for reaching out.\n\n"
            f"I would be happy to schedule a meeting. Please let me know your availability "
            f"and I will confirm a suitable time.\n\n"
            f"Best regards,\n[YOUR NAME]"
        )
        category = "meeting_request"

    elif any(kw in body_lower for kw in ["urgent", "asap", "immediately", "emergency"]):
        reply_body = (
            f"Dear {first_name},\n\n"
            f"Thank you for your urgent message. I have noted the priority.\n\n"
            f"I am reviewing this immediately and will respond with a full update very shortly.\n\n"
            f"Best regards,\n[YOUR NAME]"
        )
        category = "urgent"

    else:
        reply_body = (
            f"Dear {first_name},\n\n"
            f"Thank you for your email. I have received your message and will review it carefully.\n\n"
            f"I will get back to you with a detailed response within 24-48 hours.\n\n"
            f"Best regards,\n[YOUR NAME]"
        )
        category = "general"

    return reply_body, category


def create_approval_file(task_filepath: str, info: dict, draft: str, category: str, log: AuditLogger) -> str:
    """Create approval file in Pending_Approval/cloud/."""
    os.makedirs(PENDING_DIR, exist_ok=True)

    task_name = os.path.splitext(os.path.basename(task_filepath))[0]
    ts        = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename  = f"APPROVAL_{ts}_{task_name}.md"
    filepath  = os.path.join(PENDING_DIR, filename)

    content = f"""# APPROVAL REQUIRED: Email Reply Draft

**Created:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Original Task:** {task_name}
**From:** {info.get("from", "")}
**Subject:** {info.get("subject", "")}
**Category:** {category}
**Status:** PENDING_APPROVAL

---

## Original Email

{info.get("body", "_[no body]_")}

---

## Draft Reply

```
{draft}
```

---

## Approval Actions

**To APPROVE** (Local):
  Run: python Local/approval_agent.py
  Select this file and press A to approve

**To REJECT** (Local):
  Run: python Local/approval_agent.py
  Select this file and press R to reject with reason

**If approved:**
  -> Local MCP will send this reply via Gmail
  -> Task moved to Done/

**If rejected:**
  -> Task returned to Needs_Action/cloud/ for redraft

---

## Metadata

- gmail_id: {info.get("gmail_id", "")}
- task_file: {task_filepath}
- drafter: email_drafter.py (Platinum Cloud)
- approval: REQUIRED — do not send without approval
"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return filepath


def write_signal(task_id: str, approval_file: str) -> None:
    """Signal Local that a new approval is waiting."""
    os.makedirs(SIGNALS_DIR, exist_ok=True)
    ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
    sig_file = os.path.join(SIGNALS_DIR, f"SIGNAL_{ts}_approval_needed.md")
    content  = (
        f"signal: approval_needed\n"
        f"task_id: {task_id}\n"
        f"approval_file: {approval_file}\n"
        f"timestamp: {datetime.now().isoformat()}\n"
    )
    with open(sig_file, "w", encoding="utf-8") as f:
        f.write(content)


# ── Main ──────────────────────────────────────────────────────────────────────

def run(task_filepath: str) -> None:
    log   = AuditLogger()
    start = datetime.now()
    task  = os.path.basename(task_filepath)

    log.log(SKILL, "draft_start", "STARTED", task_id=task)
    print(f"[{SKILL}] Processing: {task}")

    if not os.path.exists(task_filepath):
        log.log_error(SKILL, "draft_start", f"File not found: {task_filepath}", task_id=task)
        print(f"[{SKILL}] ERROR: File not found: {task_filepath}")
        return

    with open(task_filepath, "r", encoding="utf-8") as f:
        content = f.read()

    info            = extract_email_info(content)
    draft, category = generate_draft_reply(info)

    approval_path = create_approval_file(task_filepath, info, draft, category, log)

    write_signal(task, approval_path)

    duration_ms = int((datetime.now() - start).total_seconds() * 1000)
    print(f"[{SKILL}] DRAFT CREATED -> {os.path.basename(approval_path)}")
    log.log(SKILL, "draft_created", "pending_approval",
            duration_ms=duration_ms,
            task_id=task,
            detail=f"category={category} approval={os.path.basename(approval_path)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <task_filepath>")
        sys.exit(1)
    run(sys.argv[1])
