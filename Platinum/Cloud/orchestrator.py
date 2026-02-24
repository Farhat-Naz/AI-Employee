"""
orchestrator.py — Cloud Orchestrator (Platinum Cloud)
------------------------------------------------------
Starts and monitors all Cloud processes on Oracle VM:
  1. gmail_watcher.py
  2. Cloud/Watchers/file_watcher.py
  3. sync_agent.py --loop
  4. health_monitor.py --loop

Auto-restarts any crashed process after RESTART_DELAY seconds.
All output logged to Platinum/Logs/orchestrator.log

Run:
  python Cloud/orchestrator.py

Stop:
  Ctrl+C (sends SIGTERM to all children)
"""

import os
import sys
import subprocess
import signal
import time
from datetime import datetime

CLOUD_DIR    = os.path.dirname(os.path.abspath(__file__))
PLATINUM_DIR = os.path.dirname(CLOUD_DIR)
LOGS_DIR     = os.path.join(PLATINUM_DIR, "Logs")

sys.path.insert(0, PLATINUM_DIR)

from Shared.audit_logger import AuditLogger

SKILL          = "Orchestrator_Platinum"
RESTART_DELAY  = 10   # seconds before restarting a crashed process
POLL_INTERVAL  = 5    # seconds between liveness checks

# Processes to manage: (name, script_path, extra_args)
SERVICES = [
    ("gmail_watcher",  os.path.join(CLOUD_DIR, "Watchers", "gmail_watcher.py"),  []),
    ("file_watcher",   os.path.join(CLOUD_DIR, "Watchers", "file_watcher.py"),   []),
    ("sync_agent",     os.path.join(CLOUD_DIR, "sync_agent.py"),                  ["--loop"]),
    ("health_monitor", os.path.join(CLOUD_DIR, "health_monitor.py"),              ["--loop"]),
]


class ManagedProcess:
    def __init__(self, name: str, script: str, args: list[str]):
        self.name   = name
        self.script = script
        self.args   = args
        self.proc: subprocess.Popen | None = None
        self.restarts = 0

    def start(self) -> None:
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"

        log_file = open(
            os.path.join(LOGS_DIR, f"{self.name}.log"), "a", encoding="utf-8"
        )

        self.proc = subprocess.Popen(
            [sys.executable, self.script] + self.args,
            stdout=log_file,
            stderr=log_file,
            env=env,
        )
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] STARTED  {self.name}  (PID {self.proc.pid})")

    def is_alive(self) -> bool:
        if self.proc is None:
            return False
        return self.proc.poll() is None

    def stop(self) -> None:
        if self.proc and self.is_alive():
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] STOPPED  {self.name}")


# ── Orchestrator ──────────────────────────────────────────────────────────────

def run() -> None:
    os.makedirs(LOGS_DIR, exist_ok=True)
    log      = AuditLogger()
    services = [ManagedProcess(n, s, a) for n, s, a in SERVICES]

    # Handle Ctrl+C / SIGTERM gracefully
    def shutdown(sig, frame):
        print("\n[Orchestrator] Shutting down...")
        for svc in services:
            svc.stop()
        log.log(SKILL, "orchestrator_stop", "success")
        sys.exit(0)

    signal.signal(signal.SIGINT,  shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # Initial start
    print(f"[Orchestrator] Platinum Cloud starting {len(services)} services...")
    log.log(SKILL, "orchestrator_start", "success", detail=f"{len(services)} services")

    for svc in services:
        if os.path.exists(svc.script):
            svc.start()
            log.log(SKILL, f"start_{svc.name}", "success")
        else:
            print(f"[Orchestrator] WARNING: {svc.script} not found — skipping {svc.name}")
            log.log(SKILL, f"start_{svc.name}", "skipped", detail="script not found")

    # Monitor loop
    while True:
        time.sleep(POLL_INTERVAL)

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
                log.log(SKILL, f"restart_{svc.name}", "success",
                        detail=f"restart #{svc.restarts}")


if __name__ == "__main__":
    run()
