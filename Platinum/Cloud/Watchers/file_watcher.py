"""
file_watcher.py — File Watcher (Platinum Cloud)
------------------------------------------------
Monitors Needs_Action/cloud/ for new .md task files.
Implements claim-by-move rule:
  Needs_Action/cloud/TASK.md  ->  In_Progress/cloud/TASK.md
Then auto-triggers email_drafter for email tasks.

Extends BaseWatcher from Shared/.

Run:
  python Cloud/Watchers/file_watcher.py
"""

import os
import sys
import re
import shutil
import subprocess
from datetime import datetime

CLOUD_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLATINUM_DIR = os.path.dirname(CLOUD_DIR)

sys.path.insert(0, PLATINUM_DIR)

from Shared.base_watcher import BaseWatcher

NEEDS_ACTION_DIR  = os.path.join(PLATINUM_DIR, "Needs_Action", "cloud")
IN_PROGRESS_DIR   = os.path.join(PLATINUM_DIR, "In_Progress", "cloud")
EMAIL_DRAFTER     = os.path.join(CLOUD_DIR, "email_drafter.py")
SIGNALS_DIR       = os.path.join(PLATINUM_DIR, "Signals")

POLL_SECONDS = 5
SKILL        = "FileWatcher_Platinum"


# ── Risk classification (same as Gold) ────────────────────────────────────────

HIGH_RISK_KEYWORDS   = ["delete", "deploy", "production", "billing", "payment", "cloud"]
MEDIUM_RISK_KEYWORDS = ["update", "modify", "push", "send", "email"]


def classify_risk(content: str) -> str:
    lower = content.lower()
    if any(kw in lower for kw in HIGH_RISK_KEYWORDS):
        return "high"
    if any(kw in lower for kw in MEDIUM_RISK_KEYWORDS):
        return "medium"
    return "low"


# ── FileWatcher ────────────────────────────────────────────────────────────────

class FileWatcher(BaseWatcher):

    def __init__(self):
        super().__init__(SKILL, poll_seconds=POLL_SECONDS)
        self._seen: set[str] = set()

    def on_start(self) -> None:
        for d in [NEEDS_ACTION_DIR, IN_PROGRESS_DIR, SIGNALS_DIR]:
            os.makedirs(d, exist_ok=True)
        print(f"[{self.skill}] Watching: {NEEDS_ACTION_DIR}")
        print(f"[{self.skill}] Claim-by-move -> {IN_PROGRESS_DIR}")

    def poll(self) -> list[dict]:
        """Detect new .md files in Needs_Action/cloud/."""
        files = {
            f for f in os.listdir(NEEDS_ACTION_DIR)
            if f.endswith(".md") and not f.startswith(".")
        }
        new_files       = files - self._seen
        self._seen      = files - new_files   # keep only files still present

        return [{"filename": f} for f in sorted(new_files)]

    def process(self, item: dict) -> None:
        """Claim file and dispatch to appropriate agent."""
        filename = item["filename"]
        src      = os.path.join(NEEDS_ACTION_DIR, filename)
        dst      = os.path.join(IN_PROGRESS_DIR, filename)

        if not os.path.exists(src):
            # Already claimed by another agent (race condition guard)
            return

        # -- Claim-by-move (atomic on most OS) --
        start = datetime.now()
        try:
            shutil.move(src, dst)
        except FileNotFoundError:
            # Lost race — another agent claimed first
            print(f"[{self.skill}] SKIP {filename} (claimed elsewhere)")
            return

        # Read content for classification
        with open(dst, "r", encoding="utf-8") as f:
            content = f.read()

        risk = classify_risk(content)

        duration_ms = int((datetime.now() - start).total_seconds() * 1000)
        print(f"[{datetime.now():%H:%M:%S}] CLAIMED  {filename}  [risk={risk}]")
        self.log.log(self.skill, "claim_task", "In_Progress/cloud",
                     duration_ms=duration_ms,
                     task_id=filename,
                     detail=f"risk={risk}")

        # -- Write signal for Dashboard --
        self._write_signal(filename, "claimed", risk)

        # -- Dispatch --
        if self._is_email_task(filename, content):
            self._trigger_email_drafter(dst, filename)
        else:
            print(f"[{self.skill}] NOTE: No auto-handler for {filename} — manual action needed")
            self.log.log(self.skill, "dispatch", "manual_needed", task_id=filename)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _is_email_task(self, filename: str, content: str) -> bool:
        return filename.startswith("EMAIL_") or "## Email Body" in content

    def _trigger_email_drafter(self, task_path: str, filename: str) -> None:
        print(f"[{datetime.now():%H:%M:%S}] TRIGGER  email_drafter for {filename}")
        self.log.log(self.skill, "trigger_email_drafter", "started", task_id=filename)
        try:
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            result = subprocess.run(
                [sys.executable, EMAIL_DRAFTER, task_path],
                capture_output=True, text=True,
                encoding="utf-8", errors="replace",
                timeout=120, env=env,
            )
            if result.returncode == 0:
                self.log.log(self.skill, "email_drafter_done", "success", task_id=filename)
            else:
                self.log.log_error(self.skill, "email_drafter_done",
                                   (result.stderr or "")[:100], task_id=filename)
        except subprocess.TimeoutExpired:
            self.log.log_error(self.skill, "email_drafter_done", "timeout", task_id=filename)
        except Exception as exc:
            self.log.log_error(self.skill, "email_drafter_done", str(exc), task_id=filename)

    def _write_signal(self, task_id: str, event: str, detail: str = "") -> None:
        """Write a signal file so Local can update Dashboard.md."""
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


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    watcher = FileWatcher()
    watcher.run()
