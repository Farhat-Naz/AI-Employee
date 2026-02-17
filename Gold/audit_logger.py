"""
audit_logger.py — Gold Tier Core Engine
----------------------------------------
Har action ko append-only audit log mein likhta hai.
Format: [timestamp] | [skill] | [action] | [result] | [duration_ms] | [task_id]

Usage:
    from audit_logger import AuditLogger
    log = AuditLogger()
    log.log("RalphLoop", "plan_task", "success", duration_ms=120, task_id="TASK-001")
"""

import os
from datetime import datetime


# ── Config ────────────────────────────────────────────────────────────────────

BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
AUDIT_LOG_DIR = os.path.join(BASE_DIR, "Audit_Logs")


# ── AuditLogger ───────────────────────────────────────────────────────────────

class AuditLogger:

    def __init__(self):
        os.makedirs(AUDIT_LOG_DIR, exist_ok=True)

    def _log_file(self) -> str:
        """Return today's log file path."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        return os.path.join(AUDIT_LOG_DIR, f"{date_str}_audit.log")

    def log(
        self,
        skill:       str,
        action:      str,
        result:      str,
        duration_ms: int  = 0,
        task_id:     str  = "-",
        detail:      str  = ""
    ) -> None:
        """Append one line to today's audit log."""
        ts      = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        detail_part = f" | {detail}" if detail else ""
        line    = (
            f"[{ts}] | {skill:<22} | {action:<28} | {result:<10} "
            f"| {duration_ms:>6}ms | {task_id}{detail_part}\n"
        )
        with open(self._log_file(), "a", encoding="utf-8") as f:
            f.write(line)
        print(f"[AUDIT] {line.strip()}")

    def log_start(self, skill: str, action: str, task_id: str = "-") -> datetime:
        """Log action start and return start time for duration calc."""
        self.log(skill, action, "STARTED", task_id=task_id)
        return datetime.now()

    def log_end(
        self,
        skill:      str,
        action:     str,
        start_time: datetime,
        result:     str = "success",
        task_id:    str = "-",
        detail:     str = ""
    ) -> None:
        """Log action completion with auto-calculated duration."""
        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        self.log(skill, action, result, duration_ms, task_id, detail)

    def log_error(
        self,
        skill:   str,
        action:  str,
        error:   str,
        task_id: str = "-"
    ) -> None:
        """Log an error."""
        self.log(skill, action, "ERROR", task_id=task_id, detail=str(error)[:120])

    def today_summary(self) -> dict:
        """Return count of actions, errors, retries from today's log."""
        log_file = self._log_file()
        summary  = {"total": 0, "errors": 0, "retries": 0, "needs_human": 0}

        if not os.path.exists(log_file):
            return summary

        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                summary["total"] += 1
                if "| ERROR" in line:
                    summary["errors"] += 1
                if "retry" in line.lower():
                    summary["retries"] += 1
                if "needs_human" in line.lower():
                    summary["needs_human"] += 1

        return summary
