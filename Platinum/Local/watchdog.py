"""
watchdog.py — Process Watchdog (Platinum Local)
------------------------------------------------
Runs on Windows PC. Monitors Local processes:
  - Local/Watchers/whatsapp_watcher.py
  - Local/Watchers/filesystem_watcher.py

Auto-restarts any crashed process.
Also periodically merges Signals/ into Dashboard.md

Run:
  python Local/watchdog.py
"""

import os
import sys
import subprocess
import time
import re
from datetime import datetime

LOCAL_DIR    = os.path.dirname(os.path.abspath(__file__))
PLATINUM_DIR = os.path.dirname(LOCAL_DIR)

sys.path.insert(0, PLATINUM_DIR)

from Shared.audit_logger import AuditLogger

SIGNALS_DIR    = os.path.join(PLATINUM_DIR, "Signals")
DASHBOARD_FILE = os.path.join(PLATINUM_DIR, "Dashboard.md")
LOGS_DIR       = os.path.join(PLATINUM_DIR, "Logs")

SKILL          = "Watchdog_Platinum"
POLL_INTERVAL  = 10    # seconds between liveness checks
RESTART_DELAY  = 5     # seconds before restarting crashed process
SIGNAL_MERGE_INTERVAL = 60   # merge signals every 60s

SERVICES = [
    ("whatsapp_watcher",   os.path.join(LOCAL_DIR, "Watchers", "whatsapp_watcher.py"),   []),
    ("filesystem_watcher", os.path.join(LOCAL_DIR, "Watchers", "filesystem_watcher.py"), []),
]


# ── Managed process ───────────────────────────────────────────────────────────

class ManagedProcess:
    def __init__(self, name: str, script: str, args: list[str]):
        self.name     = name
        self.script   = script
        self.args     = args
        self.proc     = None
        self.restarts = 0

    def start(self) -> None:
        if not os.path.exists(self.script):
            print(f"[Watchdog] SKIP {self.name} — script not found")
            return

        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"

        log_path = os.path.join(LOGS_DIR, f"{self.name}.log")
        log_file = open(log_path, "a", encoding="utf-8")

        self.proc = subprocess.Popen(
            [sys.executable, self.script] + self.args,
            stdout=log_file,
            stderr=log_file,
            env=env,
        )
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] STARTED  {self.name}  (PID {self.proc.pid})")

    def is_alive(self) -> bool:
        return self.proc is not None and self.proc.poll() is None

    def stop(self) -> None:
        if self.proc and self.is_alive():
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        print(f"[Watchdog] STOPPED  {self.name}")


# ── Signal merge -> Dashboard ─────────────────────────────────────────────────

def parse_signal(filepath: str) -> dict:
    """Parse a Signals/SIGNAL_*.md file into a dict."""
    data = {}
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if ": " in line:
                k, v = line.split(": ", 1)
                data[k] = v
    return data


def merge_signals_to_dashboard(log: AuditLogger) -> int:
    """
    Read all Signals/ files, update Dashboard.md, delete processed signals.
    Returns number of signals processed.
    """
    if not os.path.exists(SIGNALS_DIR):
        return 0

    signals = [
        f for f in os.listdir(SIGNALS_DIR)
        if f.startswith("SIGNAL_") and f.endswith(".md")
    ]

    if not signals:
        return 0

    # Read existing dashboard
    if os.path.exists(DASHBOARD_FILE):
        with open(DASHBOARD_FILE, "r", encoding="utf-8") as f:
            dashboard = f.read()
    else:
        dashboard = "# Platinum Dashboard\n\n"

    entries = []
    for sig_file in sorted(signals):
        sig_path = os.path.join(SIGNALS_DIR, sig_file)
        data     = parse_signal(sig_path)
        event    = data.get("signal", "unknown")
        task_id  = data.get("task_id", "-")
        detail   = data.get("detail", "")
        ts       = data.get("timestamp", datetime.now().isoformat())[:19]
        entries.append(f"| {ts} | {event} | {task_id} | {detail} |")

    if entries:
        # Append to Activity Log section in dashboard
        activity_block = "\n".join(entries)
        if "## Activity Log" in dashboard:
            dashboard = dashboard.replace(
                "## Activity Log",
                f"## Activity Log\n\n{activity_block}",
                1
            )
        else:
            dashboard += f"\n\n## Activity Log\n\n{activity_block}\n"

        with open(DASHBOARD_FILE, "w", encoding="utf-8") as f:
            f.write(dashboard)

    # Delete processed signals
    for sig_file in signals:
        try:
            os.remove(os.path.join(SIGNALS_DIR, sig_file))
        except FileNotFoundError:
            pass

    log.log(SKILL, "signal_merge", "success", detail=f"{len(signals)} signals merged")
    return len(signals)


# ── Main ──────────────────────────────────────────────────────────────────────

def run() -> None:
    os.makedirs(LOGS_DIR, exist_ok=True)
    log      = AuditLogger()
    services = [ManagedProcess(n, s, a) for n, s, a in SERVICES]

    print(f"[Watchdog] Starting {len(services)} Local services...")
    log.log(SKILL, "watchdog_start", "success")

    for svc in services:
        svc.start()

    last_signal_merge = 0.0

    try:
        while True:
            time.sleep(POLL_INTERVAL)

            # Check and restart crashed processes
            for svc in services:
                if not os.path.exists(svc.script):
                    continue
                if not svc.is_alive():
                    svc.restarts += 1
                    ts = datetime.now().strftime("%H:%M:%S")
                    print(f"[{ts}] CRASHED  {svc.name}  (restart #{svc.restarts} in {RESTART_DELAY}s)")
                    log.log(SKILL, f"crash_{svc.name}", "restarting",
                            detail=f"restart #{svc.restarts}")
                    time.sleep(RESTART_DELAY)
                    svc.start()

            # Merge signals periodically
            now = time.time()
            if now - last_signal_merge >= SIGNAL_MERGE_INTERVAL:
                count = merge_signals_to_dashboard(log)
                if count > 0:
                    print(f"[{datetime.now():%H:%M:%S}] MERGED  {count} signals -> Dashboard.md")
                last_signal_merge = now

    except KeyboardInterrupt:
        print("\n[Watchdog] Shutting down...")
        for svc in services:
            svc.stop()
        log.log(SKILL, "watchdog_stop", "success")


if __name__ == "__main__":
    run()
