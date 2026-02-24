"""
social_drafter.py — Social Media Drafter Agent (Platinum Cloud)
----------------------------------------------------------------
Reads a social task file from In_Progress/cloud/
Creates a draft post in Pending_Approval/cloud/
Supports: Facebook, Instagram, Twitter/X, LinkedIn

DRAFT-ONLY rule: This agent NEVER posts directly.
Only Local (with human approval) posts.

Usage:
  python Cloud/social_drafter.py In_Progress/cloud/SOCIAL_*.md
"""

import os
import sys
import re
from datetime import datetime

CLOUD_DIR    = os.path.dirname(os.path.abspath(__file__))
PLATINUM_DIR = os.path.dirname(CLOUD_DIR)

sys.path.insert(0, PLATINUM_DIR)

from Shared.audit_logger import AuditLogger

PENDING_DIR = os.path.join(PLATINUM_DIR, "Pending_Approval", "cloud")
SIGNALS_DIR = os.path.join(PLATINUM_DIR, "Signals")

SKILL = "SocialDrafter_Platinum"

# Platform character limits
CHAR_LIMITS = {
    "twitter":   280,
    "facebook":  2000,
    "instagram": 2200,
    "linkedin":  3000,
}


# ── Draft generation ──────────────────────────────────────────────────────────

def extract_social_info(content: str) -> dict:
    """Parse task file for social post metadata."""
    info = {}

    for key, pattern in [
        ("platform",  r"\*\*Platform:\*\*\s*(.+)"),
        ("tone",      r"\*\*Tone:\*\*\s*(.+)"),
        ("topic",     r"\*\*Topic:\*\*\s*(.+)"),
        ("hashtags",  r"\*\*Hashtags:\*\*\s*(.+)"),
    ]:
        m = re.search(pattern, content, re.IGNORECASE)
        info[key] = m.group(1).strip() if m else ""

    # Extract request/brief
    brief_match = re.search(r"## Brief\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL)
    if not brief_match:
        brief_match = re.search(r"## Message\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL)
    info["brief"] = brief_match.group(1).strip() if brief_match else ""

    # Detect platform from content if not explicit
    if not info["platform"]:
        lower = content.lower()
        for p in ["twitter", "instagram", "facebook", "linkedin"]:
            if p in lower:
                info["platform"] = p
                break
        if not info["platform"]:
            info["platform"] = "all"   # multi-platform

    return info


def generate_draft_post(info: dict) -> dict:
    """Generate draft post(s) for requested platform(s)."""
    platform = info.get("platform", "all").lower()
    brief    = info.get("brief", "")
    tone     = info.get("tone", "professional").lower()
    hashtags = info.get("hashtags", "")

    # Base content from brief
    base = brief if brief else "New update from our team. Stay tuned for more!"

    # Tone adjustments
    if "casual" in tone or "friendly" in tone:
        opener = "Hey everyone! "
        closer = " Let us know what you think!"
    elif "formal" in tone or "professional" in tone:
        opener = "We are pleased to announce: "
        closer = " Thank you for your continued support."
    else:
        opener = ""
        closer = ""

    full_text = f"{opener}{base}{closer}"

    # Hashtag block
    ht_block = f"\n\n{hashtags}" if hashtags else ""

    drafts = {}

    if platform in ("twitter", "all"):
        tweet = full_text
        if len(tweet) > 260:
            tweet = tweet[:257] + "..."
        drafts["twitter"] = f"{tweet}{ht_block}"[:280]

    if platform in ("facebook", "all"):
        drafts["facebook"] = f"{full_text}{ht_block}"

    if platform in ("instagram", "all"):
        drafts["instagram"] = f"{full_text}{ht_block}"

    if platform in ("linkedin", "all"):
        drafts["linkedin"] = (
            f"{full_text}\n\n"
            f"---\n"
            f"Follow us for more updates.{ht_block}"
        )

    return drafts


def create_approval_file(task_filepath: str, info: dict, drafts: dict, log: AuditLogger) -> str:
    """Create approval file in Pending_Approval/cloud/."""
    os.makedirs(PENDING_DIR, exist_ok=True)

    task_name = os.path.splitext(os.path.basename(task_filepath))[0]
    ts        = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename  = f"APPROVAL_{ts}_{task_name}.md"
    filepath  = os.path.join(PENDING_DIR, filename)

    platform_section = ""
    for platform, text in drafts.items():
        limit = CHAR_LIMITS.get(platform, 9999)
        platform_section += f"""
### {platform.title()} ({len(text)}/{limit} chars)

```
{text}
```
"""

    content = f"""# APPROVAL REQUIRED: Social Post Draft

**Created:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Original Task:** {task_name}
**Platform:** {info.get("platform", "")}
**Tone:** {info.get("tone", "")}
**Status:** PENDING_APPROVAL

---

## Original Brief

{info.get("brief", "_[no brief]_")}

---

## Draft Posts
{platform_section}
---

## Approval Actions

**To APPROVE** (Local):
  Run: python Local/approval_agent.py
  Select this file and press A to approve

**To REJECT** (Local):
  Select this file and press R with edit notes

**If approved:**
  -> Local MCP posts to selected platform(s)
  -> Task moved to Done/

---

## Metadata

- drafter: social_drafter.py (Platinum Cloud)
- approval: REQUIRED — do not post without approval
"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return filepath


def write_signal(task_id: str, approval_file: str) -> None:
    os.makedirs(SIGNALS_DIR, exist_ok=True)
    ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
    sig_file = os.path.join(SIGNALS_DIR, f"SIGNAL_{ts}_social_approval.md")
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
        return

    with open(task_filepath, "r", encoding="utf-8") as f:
        content = f.read()

    info   = extract_social_info(content)
    drafts = generate_draft_post(info)

    approval_path = create_approval_file(task_filepath, info, drafts, log)
    write_signal(task, approval_path)

    duration_ms = int((datetime.now() - start).total_seconds() * 1000)
    platforms   = list(drafts.keys())
    print(f"[{SKILL}] DRAFT CREATED -> {os.path.basename(approval_path)}  [{', '.join(platforms)}]")
    log.log(SKILL, "draft_created", "pending_approval",
            duration_ms=duration_ms, task_id=task,
            detail=f"platforms={platforms}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <task_filepath>")
        sys.exit(1)
    run(sys.argv[1])
