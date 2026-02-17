"""
Bronze Tier Agent Skills
========================
4 core skills for AI Employee Bronze Tier workflow.

Workflow: /Inbox → /Needs_Action → /Done
"""

import os
import shutil
from datetime import datetime
from pathlib import Path

# --- Vault root (relative to this file) ---
VAULT_ROOT   = Path(__file__).parent.parent          # Bronze/
INBOX        = VAULT_ROOT / "Inbox"
NEEDS_ACTION = VAULT_ROOT / "Needs_Action"
DONE         = VAULT_ROOT / "Done"
DASHBOARD    = VAULT_ROOT / "Dashboard.md"


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def _classify(content: str) -> str:
    """Simple keyword-based task classifier."""
    content_lower = content.lower()
    if any(kw in content_lower for kw in ["bug", "error", "crash", "urgent", "critical"]):
        return "bug_fix"
    if any(kw in content_lower for kw in ["setup", "install", "configure", "deploy"]):
        return "setup"
    if any(kw in content_lower for kw in ["report", "summary", "review", "audit"]):
        return "report"
    if any(kw in content_lower for kw in ["research", "explore", "investigate"]):
        return "research"
    return "general"


def _priority(content: str, task_type: str) -> str:
    """Assign priority based on content signals and task type."""
    content_lower = content.lower()
    if any(kw in content_lower for kw in ["urgent", "critical", "asap", "immediately"]):
        return "High"
    if task_type in ("bug_fix", "setup"):
        return "Medium"
    return "Low"


# ---------------------------------------------------------------------------
# Skill 1: triage_item
# ---------------------------------------------------------------------------

def triage_item(file_path: str) -> dict:
    """
    Analyze a new file from /Inbox, classify it, tag priority,
    move it to /Needs_Action, and update Dashboard.

    Args:
        file_path: Full path to a file inside /Inbox

    Returns:
        dict with keys: success, new_path, task_type, priority, message
    """
    src = Path(file_path)

    if not src.exists():
        return {"success": False, "message": f"File not found: {src}"}

    if INBOX not in src.parents and src.parent != INBOX:
        return {"success": False, "message": f"File is not inside /Inbox: {src}"}

    content = _read(src)

    task_type = _classify(content)
    priority  = _priority(content, task_type)
    now       = _now()

    # Inject triage metadata block at top of file
    triage_block = (
        f"\n\n---\n"
        f"## Triage Metadata\n"
        f"- **Task Type:** {task_type}\n"
        f"- **Priority:** {priority}\n"
        f"- **Triaged At:** {now}\n"
        f"- **Status:** Needs Action\n"
    )

    updated_content = content + triage_block
    dest = NEEDS_ACTION / src.name

    NEEDS_ACTION.mkdir(exist_ok=True)
    _write(dest, updated_content)
    src.unlink()

    # Update dashboard
    update_dashboard()

    log_entry = f"[{now}] triage_item: {src.name} → /Needs_Action | type={task_type} | priority={priority}"
    _append_dashboard_log(log_entry)

    return {
        "success":   True,
        "new_path":  str(dest),
        "task_type": task_type,
        "priority":  priority,
        "message":   f"Triaged '{src.name}' as {task_type} ({priority}) → Needs_Action",
    }


# ---------------------------------------------------------------------------
# Skill 2: summarize_item
# ---------------------------------------------------------------------------

def summarize_item(file_path: str) -> dict:
    """
    Generate a 3–5 line summary for a task file and append it
    under an '## AI Summary' section.

    Args:
        file_path: Full path to the task file (any folder)

    Returns:
        dict with keys: success, summary, message
    """
    src = Path(file_path)

    if not src.exists():
        return {"success": False, "message": f"File not found: {src}"}

    content = _read(src)

    if "## AI Summary" in content:
        return {"success": False, "message": "Summary already exists in this file."}

    # Build summary from first meaningful lines (skip blank/metadata lines)
    lines = [l.strip() for l in content.splitlines() if l.strip() and not l.startswith("#")]
    body_lines = [l for l in lines if not l.startswith("-") or len(l) > 5][:8]

    task_type = _classify(content)
    priority_tag = ""
    if "Priority:** High" in content:
        priority_tag = " — HIGH PRIORITY"
    elif "Priority:** Medium" in content:
        priority_tag = " — Medium Priority"

    summary_lines = [
        f"- Task file: `{src.name}`{priority_tag}",
        f"- Task category: {task_type}",
        f"- Key content: {body_lines[0][:120] if body_lines else 'No content found'}",
        f"- Requires follow-up: {'Yes' if task_type in ('bug_fix', 'research') else 'No'}",
        f"- Summarized at: {_now()}",
    ]

    summary_block = "\n\n---\n## AI Summary\n" + "\n".join(summary_lines) + "\n"
    _write(src, content + summary_block)

    return {
        "success": True,
        "summary": "\n".join(summary_lines),
        "message": f"Summary appended to '{src.name}'",
    }


# ---------------------------------------------------------------------------
# Skill 3: complete_item
# ---------------------------------------------------------------------------

def complete_item(file_path: str) -> dict:
    """
    Mark a task as completed: append timestamp, move to /Done,
    update Dashboard.

    Args:
        file_path: Full path to a file inside /Needs_Action

    Returns:
        dict with keys: success, done_path, message
    """
    src = Path(file_path)

    if not src.exists():
        return {"success": False, "message": f"File not found: {src}"}

    if src.parent != NEEDS_ACTION:
        return {"success": False, "message": f"File is not inside /Needs_Action: {src}"}

    now = _now()
    content = _read(src)

    completion_block = (
        f"\n\n---\n"
        f"## Completion\n"
        f"- **Completed At:** {now}\n"
        f"- **Status:** Done\n"
    )

    updated_content = content + completion_block
    dest = DONE / src.name

    DONE.mkdir(exist_ok=True)
    _write(dest, updated_content)
    src.unlink()

    update_dashboard()

    log_entry = f"[{now}] complete_item: {src.name} → /Done"
    _append_dashboard_log(log_entry)

    return {
        "success":  True,
        "done_path": str(dest),
        "message":  f"'{src.name}' completed and moved to /Done",
    }


# ---------------------------------------------------------------------------
# Skill 4: update_dashboard
# ---------------------------------------------------------------------------

def update_dashboard() -> dict:
    """
    Synchronize Dashboard.md with current vault folder counts
    and list top-5 priority tasks from /Needs_Action.

    Returns:
        dict with keys: success, inbox, needs_action, done, message
    """
    inbox_files        = _count_md(INBOX)
    needs_action_files = _count_md(NEEDS_ACTION)
    done_files         = _count_md(DONE)
    top5               = _top5_tasks()
    now                = _now()

    if not DASHBOARD.exists():
        return {"success": False, "message": "Dashboard.md not found"}

    raw = _read(DASHBOARD)

    # Replace Task Summary table block
    new_summary = (
        "## Task Summary\n\n"
        "| Metric | Count |\n"
        "|--------|-------|\n"
        f"| Inbox | {inbox_files} |\n"
        f"| Pending (Needs_Action) | {needs_action_files} |\n"
        f"| Completed (Done) | {done_files} |\n"
        f"\n_Last synced: {now}_\n"
    )

    # Replace Completed Today block
    completed = _completed_list()
    if completed:
        rows = "\n".join(f"| {n} | {d} |" for n, d in completed)
        new_completed = (
            "## Completed Today\n\n"
            "| File | Completed At |\n"
            "|------|--------------|\n"
            f"{rows}\n"
        )
    else:
        new_completed = "## Completed Today\n\n_No completed tasks yet._\n"

    # Replace Pending Tasks block
    pending = _pending_list()
    if pending:
        rows_p = "\n".join(f"| {n} | {p} |" for n, p in pending)
        new_pending = (
            "## Pending Tasks\n\n"
            "| File | Priority |\n"
            "|------|----------|\n"
            f"{rows_p}\n"
        )
    else:
        new_pending = "## Pending Tasks\n\n_No tasks pending._\n"

    # Replace Top Priority block
    top5_lines = "\n".join(f"- {t}" for t in top5) if top5 else "_No pending tasks._"
    new_top5 = f"## Top Priority Tasks\n\n{top5_lines}\n"

    # Apply all replacements
    raw = _replace_section(raw, "## Task Summary",    new_summary)
    raw = _replace_section(raw, "## Completed Today", new_completed)
    raw = _replace_section(raw, "## Pending Tasks",   new_pending)
    raw = _replace_section(raw, "## Top Priority Tasks", new_top5)

    _write(DASHBOARD, raw)

    return {
        "success":      True,
        "inbox":        inbox_files,
        "needs_action": needs_action_files,
        "done":         done_files,
        "message":      "Dashboard updated",
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _count_md(folder: Path) -> int:
    if not folder.exists():
        return 0
    return sum(1 for f in folder.iterdir() if f.suffix == ".md" and f.name != ".keep")


def _completed_list() -> list:
    """Return (filename, completed_at) for all files in /Done."""
    if not DONE.exists():
        return []
    results = []
    for f in sorted(DONE.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True):
        content = _read(f)
        completed_at = "—"
        for line in content.splitlines():
            if "Completed At:" in line:
                completed_at = line.split("Completed At:")[-1].strip().lstrip("*").rstrip("*").strip()
                break
        results.append((f.name, completed_at))
    return results


def _pending_list() -> list:
    """Return (filename, priority) for all files in /Needs_Action."""
    if not NEEDS_ACTION.exists():
        return []
    results = []
    for f in NEEDS_ACTION.glob("*.md"):
        content = _read(f)
        if "Priority:** High" in content:
            pri = "High"
        elif "Priority:** Medium" in content:
            pri = "Medium"
        else:
            pri = "Low"
        results.append((f.name, pri))
    results.sort(key=lambda x: {"High": 0, "Medium": 1, "Low": 2}[x[1]])
    return results


def _top5_tasks() -> list:
    """Return top-5 task file names from /Needs_Action sorted by priority."""
    if not NEEDS_ACTION.exists():
        return []

    tasks = []
    for f in NEEDS_ACTION.glob("*.md"):
        content = _read(f)
        if "Priority:** High" in content:
            pri = 0
        elif "Priority:** Medium" in content:
            pri = 1
        else:
            pri = 2
        tasks.append((pri, f.name))

    tasks.sort()
    return [name for _, name in tasks[:5]]


def _append_dashboard_log(entry: str) -> None:
    if not DASHBOARD.exists():
        return
    raw = _read(DASHBOARD)
    # Find Activity Log code block and insert before closing ```
    if "```" in raw:
        idx = raw.rfind("```")
        raw = raw[:idx] + entry + "\n" + raw[idx:]
    else:
        raw += f"\n{entry}\n"
    _write(DASHBOARD, raw)


def _replace_section(text: str, header: str, new_section: str) -> str:
    """
    Replace everything from `header` to the next `## ` heading (or end)
    with `new_section`.
    """
    start = text.find(header)
    if start == -1:
        # Section doesn't exist yet — append it
        return text + "\n---\n\n" + new_section
    # Find next heading after start
    next_h = text.find("\n## ", start + len(header))
    if next_h == -1:
        return text[:start] + new_section
    return text[:start] + new_section + "\n---\n\n" + text[next_h + 1:]


# ---------------------------------------------------------------------------
# CLI entry point (for manual testing)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")

    commands = {
        "triage":    triage_item,
        "summarize": summarize_item,
        "complete":  complete_item,
        "dashboard": lambda _: update_dashboard(),
    }

    if len(sys.argv) < 2 or sys.argv[1] not in commands:
        print("Usage: python skills.py <triage|summarize|complete|dashboard> [file_path]")
        sys.exit(1)

    cmd  = sys.argv[1]
    path = sys.argv[2] if len(sys.argv) > 2 else ""
    result = commands[cmd](path)
    print(result)
