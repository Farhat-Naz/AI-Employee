"""
sync_agent.py — Git Sync Agent (Platinum Cloud)
------------------------------------------------
Runs on Oracle VM every 5 minutes.
Phase 1 bridge between Cloud and Local:
  - git pull  (get Local approvals + config)
  - git add . (stage new Cloud drafts, signals, logs)
  - git commit + push (send drafts to Local)

Skips push if nothing changed.
Logs every action via AuditLogger.

Run:
  python Cloud/sync_agent.py          # single sync
  python Cloud/sync_agent.py --loop   # continuous (every 5 min)
"""

import os
import sys
import subprocess
import time
from datetime import datetime

CLOUD_DIR    = os.path.dirname(os.path.abspath(__file__))
PLATINUM_DIR = os.path.dirname(CLOUD_DIR)
VAULT_ROOT   = os.path.dirname(PLATINUM_DIR)

sys.path.insert(0, PLATINUM_DIR)

from Shared.audit_logger import AuditLogger
from Shared.retry_handler import with_retry

SKILL          = "SyncAgent_Platinum"
SYNC_INTERVAL  = 300   # 5 minutes

# Commit author shown in git log
GIT_AUTHOR_NAME  = os.environ.get("GIT_AUTHOR_NAME",  "Platinum Cloud Agent")
GIT_AUTHOR_EMAIL = os.environ.get("GIT_AUTHOR_EMAIL", "cloud@ai-employee.local")


# ── Git helpers ───────────────────────────────────────────────────────────────

def _run_git(args: list[str], cwd: str) -> tuple[int, str, str]:
    """Run a git command, return (returncode, stdout, stderr)."""
    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"]     = GIT_AUTHOR_NAME
    env["GIT_AUTHOR_EMAIL"]    = GIT_AUTHOR_EMAIL
    env["GIT_COMMITTER_NAME"]  = GIT_AUTHOR_NAME
    env["GIT_COMMITTER_EMAIL"] = GIT_AUTHOR_EMAIL

    result = subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
        env=env,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


@with_retry(max_attempts=3, delay=10.0, exceptions=(subprocess.SubprocessError, OSError))
def git_pull(cwd: str) -> str:
    code, out, err = _run_git(["pull", "--rebase", "origin", "main"], cwd)
    if code != 0 and "nothing to commit" not in err:
        raise subprocess.SubprocessError(f"git pull failed: {err}")
    return out or "already up to date"


def git_has_changes(cwd: str) -> bool:
    code, out, _ = _run_git(["status", "--porcelain"], cwd)
    return bool(out.strip())


@with_retry(max_attempts=3, delay=10.0, exceptions=(subprocess.SubprocessError, OSError))
def git_push(cwd: str) -> str:
    # Stage all Platinum changes
    _run_git(["add", "Platinum/"], cwd)

    ts      = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"[cloud-sync] auto-sync {ts}"
    code, out, err = _run_git(["commit", "-m", message], cwd)

    if code != 0:
        if "nothing to commit" in out or "nothing to commit" in err:
            return "nothing to commit"
        raise subprocess.SubprocessError(f"git commit failed: {err}")

    code, out, err = _run_git(["push", "origin", "main"], cwd)
    if code != 0:
        raise subprocess.SubprocessError(f"git push failed: {err}")

    return out or "pushed"


# ── Sync cycle ────────────────────────────────────────────────────────────────

def sync_once(log: AuditLogger) -> None:
    ts    = datetime.now().strftime("%H:%M:%S")
    start = datetime.now()

    print(f"[{ts}] SYNC START")

    # 1. Pull latest from Local
    try:
        pull_result = git_pull(VAULT_ROOT)
        print(f"[{ts}] PULL: {pull_result}")
        log.log(SKILL, "git_pull", "success", detail=pull_result[:60])
    except Exception as exc:
        print(f"[{ts}] PULL ERROR: {exc}")
        log.log_error(SKILL, "git_pull", str(exc))
        return   # don't push if pull failed (risk of conflict)

    # 2. Check if we have anything new to push
    if not git_has_changes(VAULT_ROOT):
        print(f"[{ts}] SYNC: nothing to push")
        log.log(SKILL, "git_push", "skipped", detail="no changes")
        return

    # 3. Push new Cloud output
    try:
        push_result = git_push(VAULT_ROOT)
        duration_ms = int((datetime.now() - start).total_seconds() * 1000)
        print(f"[{ts}] PUSH: {push_result}")
        log.log(SKILL, "git_push", "success", duration_ms=duration_ms, detail=push_result[:60])
    except Exception as exc:
        print(f"[{ts}] PUSH ERROR: {exc}")
        log.log_error(SKILL, "git_push", str(exc))


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    loop = "--loop" in sys.argv
    log  = AuditLogger()

    if loop:
        print(f"[{SKILL}] Starting loop — sync every {SYNC_INTERVAL}s")
        log.log(SKILL, "sync_start", "success", detail=f"interval={SYNC_INTERVAL}s")
        while True:
            try:
                sync_once(log)
            except Exception as exc:
                log.log_error(SKILL, "sync_loop", str(exc))
                print(f"[{SKILL}] ERROR: {exc}")
            time.sleep(SYNC_INTERVAL)
    else:
        sync_once(log)
