"""
approval_agent.py — Approval Agent (Platinum Local)
----------------------------------------------------
Runs on your Windows PC.
Lists all pending approvals in Pending_Approval/cloud/
Human reviews each draft and approves or rejects.

For email approvals: MCP / Gmail API sends the reply.
For social approvals: MCP / social API posts the content.

Run:
  python Local/approval_agent.py         # interactive mode
  python Local/approval_agent.py --list  # just list pending, no interaction
"""

import os
import sys
import shutil
import re
from datetime import datetime

LOCAL_DIR    = os.path.dirname(os.path.abspath(__file__))
PLATINUM_DIR = os.path.dirname(LOCAL_DIR)

sys.path.insert(0, PLATINUM_DIR)

from Shared.audit_logger import AuditLogger

PENDING_CLOUD_DIR = os.path.join(PLATINUM_DIR, "Pending_Approval", "cloud")
PENDING_LOCAL_DIR = os.path.join(PLATINUM_DIR, "Pending_Approval", "local")
DONE_DIR          = os.path.join(PLATINUM_DIR, "Done")
FAILED_DIR        = os.path.join(PLATINUM_DIR, "Failed")
SIGNALS_DIR       = os.path.join(PLATINUM_DIR, "Signals")
MCP_CONFIG        = os.path.join(LOCAL_DIR, "MCP", "mcp_config.json")

SKILL = "ApprovalAgent_Platinum"


# ── List pending ──────────────────────────────────────────────────────────────

def list_pending(directory: str) -> list[str]:
    if not os.path.exists(directory):
        return []
    return sorted([
        f for f in os.listdir(directory)
        if f.endswith(".md") and not f.startswith(".")
    ])


def show_file(filepath: str) -> None:
    """Print the content of an approval file to terminal."""
    print("\n" + "=" * 70)
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    print(content)
    print("=" * 70)


# ── Actions ───────────────────────────────────────────────────────────────────

def approve(filepath: str, log: AuditLogger) -> None:
    """Move approved file to Done/ and trigger send (via MCP)."""
    filename = os.path.basename(filepath)
    dst      = os.path.join(DONE_DIR, filename)
    os.makedirs(DONE_DIR, exist_ok=True)

    shutil.move(filepath, dst)

    # Detect type from filename/content and trigger MCP action
    _trigger_mcp_send(dst, filename, log)

    log.log(SKILL, "approved", "success", task_id=filename)
    print(f"\n[APPROVED] {filename}")
    print(f"  -> Moved to Done/")
    _write_signal(filename, "approved")


def reject(filepath: str, reason: str, log: AuditLogger) -> None:
    """Move rejected file to Failed/ with rejection reason appended."""
    filename = os.path.basename(filepath)

    # Append rejection note to file
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(f"\n\n---\n\n## REJECTED\n\n**Reason:** {reason}\n**Rejected at:** {datetime.now().isoformat()}\n")

    dst = os.path.join(FAILED_DIR, f"REJECTED_{filename}")
    os.makedirs(FAILED_DIR, exist_ok=True)
    shutil.move(filepath, dst)

    log.log(SKILL, "rejected", "failed", task_id=filename, detail=reason[:60])
    print(f"\n[REJECTED] {filename}")
    print(f"  -> Moved to Failed/REJECTED_{filename}")
    _write_signal(filename, "rejected", reason)


def _trigger_mcp_send(filepath: str, filename: str, log: AuditLogger) -> None:
    """
    Placeholder: trigger MCP action for approved draft.
    In Phase 2: call Gmail API to send reply, or social API to post.
    """
    # Detect type
    if "EMAIL" in filename or "email" in filename.lower():
        print(f"  [MCP] Email send queued — implement Gmail MCP in Phase 2")
        log.log(SKILL, "mcp_trigger", "queued", task_id=filename, detail="email_send_pending_mcp")
    elif "SOCIAL" in filename or any(p in filename.lower() for p in ["twitter", "instagram", "facebook"]):
        print(f"  [MCP] Social post queued — implement Social MCP in Phase 2")
        log.log(SKILL, "mcp_trigger", "queued", task_id=filename, detail="social_post_pending_mcp")
    else:
        print(f"  [MCP] Action queued — unknown type")
        log.log(SKILL, "mcp_trigger", "queued", task_id=filename, detail="unknown_type")


def _write_signal(task_id: str, event: str, detail: str = "") -> None:
    os.makedirs(SIGNALS_DIR, exist_ok=True)
    ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
    sig_file = os.path.join(SIGNALS_DIR, f"SIGNAL_{ts}_{event}.md")
    content  = (
        f"signal: {event}\n"
        f"task_id: {task_id}\n"
        f"detail: {detail}\n"
        f"timestamp: {datetime.now().isoformat()}\n"
    )
    with open(sig_file, "w", encoding="utf-8") as f:
        f.write(content)


# ── Interactive mode ──────────────────────────────────────────────────────────

def interactive(log: AuditLogger) -> None:
    """Interactive approval loop."""
    pending = list_pending(PENDING_CLOUD_DIR)

    if not pending:
        print("[approval_agent] No pending approvals in Pending_Approval/cloud/")
        return

    print(f"\n[approval_agent] {len(pending)} pending approval(s):")
    for i, f in enumerate(pending, 1):
        path  = os.path.join(PENDING_CLOUD_DIR, f)
        age_h = (datetime.now() - datetime.fromtimestamp(os.path.getmtime(path))).total_seconds() / 3600
        print(f"  {i}. {f}  ({age_h:.1f}h old)")

    print()

    for i, filename in enumerate(pending, 1):
        filepath = os.path.join(PENDING_CLOUD_DIR, filename)

        print(f"\n--- [{i}/{len(pending)}] {filename} ---")
        print("Press:")
        print("  V = View full file")
        print("  A = Approve (trigger send)")
        print("  R = Reject (with reason)")
        print("  S = Skip (decide later)")
        print("  Q = Quit")

        while True:
            try:
                choice = input("\nAction [V/A/R/S/Q]: ").strip().upper()
            except (EOFError, KeyboardInterrupt):
                print("\n[approval_agent] Exiting.")
                return

            if choice == "V":
                show_file(filepath)

            elif choice == "A":
                approve(filepath, log)
                break

            elif choice == "R":
                try:
                    reason = input("Rejection reason: ").strip()
                except (EOFError, KeyboardInterrupt):
                    reason = "no reason given"
                reject(filepath, reason, log)
                break

            elif choice == "S":
                print(f"[approval_agent] Skipped {filename}")
                log.log(SKILL, "skipped", "skipped", task_id=filename)
                break

            elif choice == "Q":
                print("[approval_agent] Exiting.")
                return

            else:
                print("  Invalid choice. Use V / A / R / S / Q")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    log = AuditLogger()

    if "--list" in sys.argv:
        pending = list_pending(PENDING_CLOUD_DIR)
        print(f"Pending approvals ({len(pending)}):")
        for f in pending:
            print(f"  {f}")
    else:
        interactive(log)
