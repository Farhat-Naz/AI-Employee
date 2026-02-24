"""
health_monitor.py — Health Monitor (Platinum Cloud)
----------------------------------------------------
Runs every 5 minutes on Oracle VM. Checks:
  1. Required processes (gmail_watcher, file_watcher, sync_agent) running?
  2. Disk space > 20% free?
  3. Audit log written in last 10 minutes?
  4. Pending_Approval tasks older than 24h? (alert)
  5. Failed/ tasks? (alert)

Writes health signal -> Signals/ for Local Dashboard.
Optionally sends WhatsApp alert via Green API if critical.

Run:
  python Cloud/health_monitor.py          # single check
  python Cloud/health_monitor.py --loop   # continuous (every 5 min)
"""

import os
import sys
import json
import time
import shutil
import subprocess
from datetime import datetime, timedelta

CLOUD_DIR    = os.path.dirname(os.path.abspath(__file__))
PLATINUM_DIR = os.path.dirname(CLOUD_DIR)

sys.path.insert(0, PLATINUM_DIR)

from Shared.audit_logger import AuditLogger

SIGNALS_DIR     = os.path.join(PLATINUM_DIR, "Signals")
LOGS_DIR        = os.path.join(PLATINUM_DIR, "Logs")
PENDING_DIR     = os.path.join(PLATINUM_DIR, "Pending_Approval", "cloud")
FAILED_DIR      = os.path.join(PLATINUM_DIR, "Failed")

CHECK_INTERVAL  = 300   # 5 minutes
MIN_DISK_PCT    = 20
LOG_STALE_MINS  = 10
PENDING_WARN_H  = 24    # warn if approval pending > 24 hours

SKILL = "HealthMonitor_Platinum"

# Optional WhatsApp alert (Green API) — set in .env
WA_INSTANCE = os.environ.get("WA_INSTANCE_ID", "")
WA_TOKEN    = os.environ.get("WA_API_TOKEN", "")
WA_ALERT_TO = os.environ.get("WA_ALERT_NUMBER", "")   # e.g. 923142062716


# ── Checks ────────────────────────────────────────────────────────────────────

def check_disk() -> dict:
    """Check disk free space on Platinum dir partition."""
    try:
        total, used, free = shutil.disk_usage(PLATINUM_DIR)
        pct_free = (free / total) * 100
        return {
            "name":   "disk",
            "ok":     pct_free >= MIN_DISK_PCT,
            "detail": f"{pct_free:.1f}% free ({free // (1024**3)}GB)"
        }
    except Exception as exc:
        return {"name": "disk", "ok": False, "detail": str(exc)}


def check_audit_log_recency() -> dict:
    """Check that audit log has been written in last LOG_STALE_MINS minutes."""
    log_file = os.path.join(LOGS_DIR, f"{datetime.now().strftime('%Y-%m-%d')}_audit.log")
    if not os.path.exists(log_file):
        return {"name": "audit_log", "ok": False, "detail": "log file missing"}
    mtime    = os.path.getmtime(log_file)
    age_mins = (time.time() - mtime) / 60
    return {
        "name":   "audit_log",
        "ok":     age_mins <= LOG_STALE_MINS,
        "detail": f"last write {age_mins:.1f}min ago"
    }


def check_pending_age() -> dict:
    """Check for approval tasks older than PENDING_WARN_H hours."""
    if not os.path.exists(PENDING_DIR):
        return {"name": "pending_age", "ok": True, "detail": "no pending dir"}

    now   = datetime.now()
    stale = []
    for f in os.listdir(PENDING_DIR):
        if not f.endswith(".md"):
            continue
        path  = os.path.join(PENDING_DIR, f)
        age_h = (now - datetime.fromtimestamp(os.path.getmtime(path))).total_seconds() / 3600
        if age_h > PENDING_WARN_H:
            stale.append(f"{f} ({age_h:.0f}h)")

    return {
        "name":   "pending_age",
        "ok":     len(stale) == 0,
        "detail": f"{len(stale)} stale approvals: {stale[:3]}" if stale else "all fresh"
    }


def check_failed_tasks() -> dict:
    """Check if Failed/ has any files."""
    if not os.path.exists(FAILED_DIR):
        return {"name": "failed", "ok": True, "detail": "no failed dir"}
    files = [f for f in os.listdir(FAILED_DIR) if f.endswith(".md")]
    return {
        "name":   "failed",
        "ok":     len(files) == 0,
        "detail": f"{len(files)} failed tasks" if files else "none"
    }


def check_processes(required: list[str]) -> dict:
    """Check if required process names appear in running process list."""
    try:
        result = subprocess.run(
            ["ps", "aux"], capture_output=True, text=True, timeout=10
        )
        running = result.stdout
    except FileNotFoundError:
        # Windows fallback (for local testing)
        result  = subprocess.run(
            ["tasklist"], capture_output=True, text=True, timeout=10
        )
        running = result.stdout

    missing = [p for p in required if p not in running]
    return {
        "name":   "processes",
        "ok":     len(missing) == 0,
        "detail": f"missing: {missing}" if missing else "all running"
    }


# ── Signal + Alert ────────────────────────────────────────────────────────────

def write_health_signal(checks: list[dict], overall: str) -> None:
    os.makedirs(SIGNALS_DIR, exist_ok=True)
    ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
    sig_file = os.path.join(SIGNALS_DIR, f"SIGNAL_{ts}_health.md")

    lines = [
        f"signal: health_check\n",
        f"timestamp: {datetime.now().isoformat()}\n",
        f"overall: {overall}\n",
    ]
    for c in checks:
        lines.append(f"check.{c['name']}: {'OK' if c['ok'] else 'FAIL'} — {c['detail']}\n")

    with open(sig_file, "w", encoding="utf-8") as f:
        f.writelines(lines)


def send_wa_alert(message: str) -> None:
    """Send WhatsApp alert via Green API (optional)."""
    if not all([WA_INSTANCE, WA_TOKEN, WA_ALERT_TO]):
        return
    try:
        import requests
        url     = f"https://api.green-api.com/waInstance{WA_INSTANCE}/sendMessage/{WA_TOKEN}"
        payload = {"chatId": f"{WA_ALERT_TO}@c.us", "message": message}
        requests.post(url, json=payload, timeout=10)
    except Exception:
        pass   # alert failure should not crash monitor


# ── Run checks ────────────────────────────────────────────────────────────────

def run_checks() -> None:
    log = AuditLogger()
    ts  = datetime.now().strftime("%H:%M:%S")

    checks = [
        check_disk(),
        check_audit_log_recency(),
        check_pending_age(),
        check_failed_tasks(),
    ]

    # Process check only on Linux (cloud)
    if sys.platform.startswith("linux"):
        checks.append(check_processes(["gmail_watcher", "file_watcher", "sync_agent"]))

    failed  = [c for c in checks if not c["ok"]]
    overall = "HEALTHY" if not failed else "DEGRADED"

    print(f"[{ts}] Health: {overall}")
    for c in checks:
        status = "OK  " if c["ok"] else "FAIL"
        print(f"  [{status}] {c['name']:<20} {c['detail']}")

    write_health_signal(checks, overall)

    for c in checks:
        log.log(SKILL, f"check_{c['name']}", "ok" if c["ok"] else "fail",
                detail=c["detail"])

    if failed:
        alert_msg = (
            f"[Platinum HealthMonitor] {overall}\n"
            + "\n".join(f"FAIL: {c['name']} — {c['detail']}" for c in failed)
        )
        send_wa_alert(alert_msg)

    log.log(SKILL, "health_check", overall, detail=f"{len(failed)} failures")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    loop = "--loop" in sys.argv

    if loop:
        print(f"[{SKILL}] Starting loop — check every {CHECK_INTERVAL}s")
        while True:
            try:
                run_checks()
            except Exception as exc:
                print(f"[{SKILL}] ERROR: {exc}")
            time.sleep(CHECK_INTERVAL)
    else:
        run_checks()
