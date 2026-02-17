"""
audit_logger.py — Enhanced Audit Logger (Platinum Tier)
--------------------------------------------------------
Upgraded from Gold AuditLogger:
  - Writes to Platinum/Logs/YYYY-MM-DD_audit.log
  - Pipe-delimited format (compatible with Gold logs)
  - today_summary() for Dashboard/health checks
  - Works from both Cloud and Local (path-agnostic)

Usage:
  from Shared.audit_logger import AuditLogger
  log = AuditLogger()
  log.log("MySkill", "do_thing", "success", duration_ms=42, task_id="TASK-001")
"""

import os
from datetime import datetime


# ── Paths ─────────────────────────────────────────────────────────────────────

PLATINUM_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR     = os.path.join(PLATINUM_DIR, "Logs")


# ── AuditLogger ───────────────────────────────────────────────────────────────

class AuditLogger:
    """
    Append-only audit logger for Platinum tier.

    Log format (pipe-delimited):
      [YYYY-MM-DD HH:MM:SS] | skill | action | result | duration_ms | task_id | detail
    """

    def __init__(self, logs_dir: str = LOGS_DIR):
        self.logs_dir = logs_dir
        os.makedirs(self.logs_dir, exist_ok=True)

    # ── Core log ──────────────────────────────────────────────────────────────

    def log(
        self,
        skill: str,
        action: str,
        result: str,
        duration_ms: int = 0,
        task_id: str = "-",
        detail: str = "",
    ) -> None:
        ts   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = (
            f"[{ts}] | {skill:<22} | {action:<28} | {result:<10} | "
            f"{duration_ms:>6}ms | {task_id} | {detail}\n"
        )
        log_file = os.path.join(self.logs_dir, f"{datetime.now().strftime('%Y-%m-%d')}_audit.log")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(line)

    # ── Convenience wrappers ──────────────────────────────────────────────────

    def log_start(self, skill: str, action: str, task_id: str = "-") -> datetime:
        """Log action start and return start time for duration calculation."""
        self.log(skill, action, "STARTED", task_id=task_id)
        return datetime.now()

    def log_end(
        self,
        skill: str,
        action: str,
        start_time: datetime,
        result: str = "success",
        task_id: str = "-",
        detail: str = "",
    ) -> None:
        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        self.log(skill, action, result, duration_ms=duration_ms, task_id=task_id, detail=detail)

    def log_error(self, skill: str, action: str, error: str, task_id: str = "-") -> None:
        self.log(skill, action, "ERROR", task_id=task_id, detail=error[:120])

    # ── Summary ───────────────────────────────────────────────────────────────

    def today_summary(self) -> dict:
        """
        Read today's log file and return summary counts.
        Returns: {total, errors, retries, needs_human}
        """
        log_file = os.path.join(self.logs_dir, f"{datetime.now().strftime('%Y-%m-%d')}_audit.log")
        summary  = {"total": 0, "errors": 0, "retries": 0, "needs_human": 0}

        if not os.path.exists(log_file):
            return summary

        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                summary["total"] += 1
                if "ERROR" in line:
                    summary["errors"] += 1
                if "retry" in line.lower():
                    summary["retries"] += 1
                if "NEEDS_HUMAN" in line:
                    summary["needs_human"] += 1

        return summary
