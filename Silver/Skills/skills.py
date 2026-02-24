"""
Silver Tier Agent Skills
========================
6 core skills — Bronze se zyada powerful.

New in Silver:
  - Risk classification (low / medium / high)
  - Approval routing (high risk → Awaiting_Approval)
  - Retry logic (3 retries → Failed)
  - Memory system (lessons → Memory/decisions.md)

Workflow:
  /Inbox → triage → /Needs_Action or /Awaiting_Approval
  /Needs_Action → complete → /Done + Memory update
  /Needs_Action → fail (3x retry) → /Failed
"""

import re
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Vault paths
# ---------------------------------------------------------------------------

VAULT_ROOT        = Path(__file__).parent.parent          # Silver/
INBOX             = VAULT_ROOT / "Inbox"
NEEDS_ACTION      = VAULT_ROOT / "Needs_Action"
AWAITING_APPROVAL = VAULT_ROOT / "Awaiting_Approval"
DONE              = VAULT_ROOT / "Done"
FAILED            = VAULT_ROOT / "Failed"
MEMORY_DIR        = VAULT_ROOT / "Memory"
DECISIONS_FILE    = MEMORY_DIR / "decisions.md"
NOTES_FILE        = MEMORY_DIR / "notes.md"
DASHBOARD         = VAULT_ROOT / "Dashboard.md"

# Risk keywords
HIGH_RISK   = ["delete", "deploy", "production", "billing", "payment", "cloud",
               "remove", "drop", "truncate", "shutdown", "terminate"]
MEDIUM_RISK = ["update", "modify", "push", "send", "email", "upload", "change"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def _count_md(folder: Path) -> int:
    if not folder.exists():
        return 0
    return sum(1 for f in folder.iterdir() if f.suffix == ".md" and f.name != ".keep")


def _classify_risk(content: str) -> str:
    lower = content.lower()
    if any(kw in lower for kw in HIGH_RISK):
        return "high"
    if any(kw in lower for kw in MEDIUM_RISK):
        return "medium"
    return "low"


def _get_retry_count(content: str) -> int:
    for line in content.splitlines():
        if "retries:" in line.lower():
            try:
                return int(line.split(":")[-1].strip().rstrip("*").lstrip("*").strip())
            except ValueError:
                pass
    return 0


def _replace_section(text: str, header: str, new_section: str) -> str:
    start = text.find(header)
    if start == -1:
        return text + "\n---\n\n" + new_section
    next_h = text.find("\n## ", start + len(header))
    if next_h == -1:
        return text[:start] + new_section
    return text[:start] + new_section + "\n---\n\n" + text[next_h + 1:]


def _append_log(entry: str) -> None:
    if not DASHBOARD.exists():
        return
    raw = _read(DASHBOARD)
    if "```" in raw:
        idx = raw.rfind("```")
        raw = raw[:idx] + entry + "\n" + raw[idx:]
    else:
        raw += f"\n{entry}\n"
    _write(DASHBOARD, raw)


# ---------------------------------------------------------------------------
# Skill 1: triage_item
# ---------------------------------------------------------------------------

def triage_item(file_path: str) -> dict:
    """
    Analyze Inbox file — classify risk, assign priority.
    High risk → Awaiting_Approval.
    Others → Needs_Action.
    """
    src = Path(file_path)
    if not src.exists():
        return {"success": False, "message": f"File not found: {src}"}

    content = _read(src)
    risk    = _classify_risk(content)
    now     = _now()

    metadata_block = (
        f"\n\n---\n"
        f"## Agent Metadata\n"
        f"- **Received At:** {now}\n"
        f"- **Risk Level:** {risk}\n"
        f"- **Retries:** 0\n"
        f"- **Source:** file_watcher (internal)\n"
    )

    updated = content + metadata_block

    if risk == "high":
        dest   = AWAITING_APPROVAL / src.name
        status = "awaiting_approval"
        AWAITING_APPROVAL.mkdir(exist_ok=True)
        updated += f"- **Status:** Awaiting Approval\n"
    else:
        dest   = NEEDS_ACTION / src.name
        status = "needs_action"
        NEEDS_ACTION.mkdir(exist_ok=True)
        updated += f"- **Status:** Needs Action\n"

    _write(dest, updated)
    src.unlink()
    update_dashboard()
    _append_log(f"[{now}] triage_item: {src.name} → risk={risk} → /{status}")

    return {
        "success":    True,
        "new_path":   str(dest),
        "risk":       risk,
        "status":     status,
        "message":    f"Triaged '{src.name}' | risk={risk} → {status}",
    }


# ---------------------------------------------------------------------------
# Skill 2: route_approval
# ---------------------------------------------------------------------------

def route_approval(file_path: str) -> dict:
    """
    Manually route a task to Awaiting_Approval.
    Use when human review is needed.
    """
    src = Path(file_path)
    if not src.exists():
        return {"success": False, "message": f"File not found: {src}"}

    now     = _read(src)
    content = _read(src)
    now     = _now()

    content += f"\n- **Routed For Approval:** {now}\n- **Status:** Awaiting Approval\n"
    dest = AWAITING_APPROVAL / src.name
    AWAITING_APPROVAL.mkdir(exist_ok=True)
    _write(dest, content)
    src.unlink()

    update_dashboard()
    _append_log(f"[{now}] route_approval: {src.name} → /Awaiting_Approval")

    return {"success": True, "message": f"'{src.name}' routed to Awaiting_Approval"}


# ---------------------------------------------------------------------------
# Skill 3: complete_item
# ---------------------------------------------------------------------------

def complete_item(file_path: str, lesson: str = "") -> dict:
    """
    Mark task done → move to /Done → append lesson to Memory.

    Args:
        file_path: Path to file in /Needs_Action or /Awaiting_Approval
        lesson:    Optional lesson/decision to save in Memory
    """
    src = Path(file_path)
    if not src.exists():
        return {"success": False, "message": f"File not found: {src}"}

    if src.parent not in (NEEDS_ACTION, AWAITING_APPROVAL):
        return {"success": False, "message": "File must be in Needs_Action or Awaiting_Approval"}

    now     = _now()
    content = _read(src)

    content += (
        f"\n\n---\n"
        f"## Completion\n"
        f"- **Completed At:** {now}\n"
        f"- **Status:** Done\n"
    )

    dest = DONE / src.name
    DONE.mkdir(exist_ok=True)
    _write(dest, content)
    src.unlink()

    # Memory append
    if lesson:
        memory_append(src.name, lesson)
    else:
        memory_append(src.name, f"Task '{src.name}' completed successfully.")

    update_dashboard()
    _append_log(f"[{now}] complete_item: {src.name} → /Done")

    return {"success": True, "done_path": str(dest), "message": f"'{src.name}' completed"}


# ---------------------------------------------------------------------------
# Skill 4: fail_item
# ---------------------------------------------------------------------------

def fail_item(file_path: str, reason: str = "Unknown failure") -> dict:
    """
    Move a task to /Failed after exhausting retries.

    Args:
        file_path: Path to file in /Needs_Action
        reason:    Why the task failed
    """
    src = Path(file_path)
    if not src.exists():
        return {"success": False, "message": f"File not found: {src}"}

    now     = _now()
    content = _read(src)

    content += (
        f"\n\n---\n"
        f"## Failure\n"
        f"- **Failed At:** {now}\n"
        f"- **Reason:** {reason}\n"
        f"- **Status:** Failed\n"
    )

    dest = FAILED / src.name
    FAILED.mkdir(exist_ok=True)
    _write(dest, content)
    src.unlink()

    update_dashboard()
    _append_log(f"[{now}] fail_item: {src.name} → /Failed | reason={reason}")

    return {"success": True, "failed_path": str(dest), "message": f"'{src.name}' moved to Failed"}


# ---------------------------------------------------------------------------
# Skill 5: retry_item
# ---------------------------------------------------------------------------

def retry_item(file_path: str, reason: str = "") -> dict:
    """
    Increment retry counter. After 3 retries → call fail_item.

    Args:
        file_path: Path to file in /Needs_Action
        reason:    Why this retry is happening
    """
    src = Path(file_path)
    if not src.exists():
        return {"success": False, "message": f"File not found: {src}"}

    now     = _now()
    content = _read(src)
    retries = _get_retry_count(content) + 1

    # Update retry count in metadata
    content = re.sub(
        r"(\*\*Retries:\*\* )\d+",
        f"\\g<1>{retries}",
        content
    )

    if retries >= 3:
        _write(src, content)
        return fail_item(file_path, reason=f"Max retries (3) reached. Last: {reason}")

    content += f"\n- **Retry {retries} At:** {now} — {reason}\n"
    _write(src, content)

    _append_log(f"[{now}] retry_item: {src.name} | attempt={retries}/3")

    return {
        "success": True,
        "retries": retries,
        "message": f"Retry {retries}/3 for '{src.name}'",
    }


# ---------------------------------------------------------------------------
# Skill 6: memory_append
# ---------------------------------------------------------------------------

def memory_append(task_name: str, lesson: str) -> dict:
    """
    Append a lesson/decision to Memory/decisions.md.

    Args:
        task_name: Name of the completed task
        lesson:    What was learned or decided
    """
    MEMORY_DIR.mkdir(exist_ok=True)
    now = _now()

    # decisions.md
    if not DECISIONS_FILE.exists():
        _write(DECISIONS_FILE, "# Decisions & Lessons\n\n| Date | Task | Lesson |\n|------|------|--------|\n")

    row = f"| {now} | {task_name} | {lesson} |\n"

    content = _read(DECISIONS_FILE)
    _write(DECISIONS_FILE, content + row)

    return {"success": True, "message": f"Memory updated: {lesson[:60]}"}


# ---------------------------------------------------------------------------
# Skill 7: update_dashboard
# ---------------------------------------------------------------------------

def update_dashboard() -> dict:
    """Sync Silver Dashboard.md with real vault state."""
    if not DASHBOARD.exists():
        return {"success": False, "message": "Dashboard.md not found"}

    now    = _now()
    raw    = _read(DASHBOARD)

    inbox_c    = _count_md(INBOX)
    action_c   = _count_md(NEEDS_ACTION)
    approval_c = _count_md(AWAITING_APPROVAL)
    done_c     = _count_md(DONE)
    failed_c   = _count_md(FAILED)

    # Task Summary
    new_summary = (
        "## Task Summary\n\n"
        "| Metric | Count |\n"
        "|--------|-------|\n"
        f"| Inbox | {inbox_c} |\n"
        f"| Pending (Needs_Action) | {action_c} |\n"
        f"| Awaiting Approval | {approval_c} |\n"
        f"| Completed (Done) | {done_c} |\n"
        f"| Failed | {failed_c} |\n"
        f"\n_Last synced: {now}_\n"
    )

    # Pending Approvals
    approvals = list(AWAITING_APPROVAL.glob("*.md")) if AWAITING_APPROVAL.exists() else []
    if approvals:
        rows = "\n".join(f"| {f.name} | Pending |" for f in approvals)
        new_approvals = (
            "## Pending Approvals\n\n"
            "| File | Status |\n"
            "|------|--------|\n"
            f"{rows}\n"
        )
    else:
        new_approvals = "## Pending Approvals\n\n_No tasks awaiting approval._\n"

    # Failed Tasks
    fails = list(FAILED.glob("*.md")) if FAILED.exists() else []
    if fails:
        rows_f = "\n".join(f"| {f.name} |" for f in fails)
        new_failed = (
            "## Failed Tasks\n\n"
            "| File |\n"
            "|------|\n"
            f"{rows_f}\n"
        )
    else:
        new_failed = "## Failed Tasks\n\n_No failed tasks._\n"

    # Completed Today
    done_files = sorted(DONE.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True) if DONE.exists() else []
    if done_files:
        rows_d = []
        for f in done_files:
            content = _read(f)
            completed_at = "—"
            for line in content.splitlines():
                if "Completed At:" in line:
                    completed_at = line.split("Completed At:")[-1].strip().lstrip("*").rstrip("*").strip()
                    break
            rows_d.append(f"| {f.name} | {completed_at} |")
        new_completed = (
            "## Completed Today\n\n"
            "| File | Completed At |\n"
            "|------|--------------|\n"
            + "\n".join(rows_d) + "\n"
        )
    else:
        new_completed = "## Completed Today\n\n_No tasks completed yet._\n"

    # Memory Updates (last 3 rows from decisions.md)
    if DECISIONS_FILE.exists():
        lines = [l for l in _read(DECISIONS_FILE).splitlines() if l.startswith("|") and "Date" not in l and "---" not in l]
        last3 = lines[-3:] if len(lines) >= 3 else lines
        if last3:
            new_memory = (
                "## Memory Updates\n\n"
                "| Date | Task | Lesson |\n"
                "|------|------|--------|\n"
                + "\n".join(last3) + "\n"
            )
        else:
            new_memory = "## Memory Updates\n\n_No memory entries yet._\n"
    else:
        new_memory = "## Memory Updates\n\n_No memory entries yet._\n"

    raw = _replace_section(raw, "## Task Summary",      new_summary)
    raw = _replace_section(raw, "## Pending Approvals", new_approvals)
    raw = _replace_section(raw, "## Failed Tasks",      new_failed)
    raw = _replace_section(raw, "## Completed Today",   new_completed)
    raw = _replace_section(raw, "## Memory Updates",    new_memory)

    _write(DASHBOARD, raw)

    return {
        "success":   True,
        "inbox":     inbox_c,
        "action":    action_c,
        "approval":  approval_c,
        "done":      done_c,
        "failed":    failed_c,
        "message":   "Silver Dashboard updated",
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")

    usage = "python skills.py <triage|complete|fail|retry|memory|dashboard> [file_path] [extra]"
    commands = {
        "triage":    lambda a: triage_item(a[0]) if a else {"error": "file_path required"},
        "complete":  lambda a: complete_item(a[0], a[1] if len(a) > 1 else ""),
        "fail":      lambda a: fail_item(a[0], a[1] if len(a) > 1 else "Manual fail"),
        "retry":     lambda a: retry_item(a[0], a[1] if len(a) > 1 else ""),
        "memory":    lambda a: memory_append(a[0], a[1]) if len(a) >= 2 else {"error": "task_name and lesson required"},
        "dashboard": lambda a: update_dashboard(),
        "approve":   lambda a: route_approval(a[0]) if a else {"error": "file_path required"},
    }

    if len(sys.argv) < 2 or sys.argv[1] not in commands:
        print(usage)
        sys.exit(1)

    result = commands[sys.argv[1]](sys.argv[2:])
    print(result)
