"""
base_watcher.py — Abstract Base Watcher (Platinum Tier)
--------------------------------------------------------
All Platinum watchers (Gmail, File, WhatsApp, Filesystem) extend this.

Usage:
  from Shared.base_watcher import BaseWatcher

  class MyWatcher(BaseWatcher):
      def poll(self) -> list[dict]:   # fetch raw items
          ...
      def process(self, item: dict) -> None:   # handle one item
          ...
"""

import os
import sys
import time
from abc import ABC, abstractmethod
from datetime import datetime

# ── Paths ─────────────────────────────────────────────────────────────────────

PLATINUM_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PLATINUM_DIR)

from Shared.audit_logger import AuditLogger


# ── Base Watcher ──────────────────────────────────────────────────────────────

class BaseWatcher(ABC):
    """
    Template for all Platinum watchers.

    Subclasses must implement:
      - poll()    -> list[dict]    — fetch items from source
      - process() -> None          — handle a single item

    Optional overrides:
      - on_start()  — called once before loop
      - on_error()  — called on unhandled exception in loop body
    """

    def __init__(self, skill: str, poll_seconds: int = 5):
        self.skill        = skill
        self.poll_seconds = poll_seconds
        self.log          = AuditLogger()
        self._running     = False

    # ── Abstract interface ─────────────────────────────────────────────────────

    @abstractmethod
    def poll(self) -> list[dict]:
        """Fetch zero or more raw items from source. Must not raise."""
        ...

    @abstractmethod
    def process(self, item: dict) -> None:
        """Handle one raw item. Raise on unrecoverable error."""
        ...

    # ── Optional hooks ─────────────────────────────────────────────────────────

    def on_start(self) -> None:
        """Called once before the main loop starts."""
        pass

    def on_error(self, exc: Exception) -> None:
        """Called when process() raises. Default: log + continue."""
        self.log.log_error(self.skill, "process_item", str(exc))

    # ── Main loop ──────────────────────────────────────────────────────────────

    def run(self) -> None:
        """Start the polling loop. Blocks until KeyboardInterrupt."""
        self._running = True
        self.log.log(self.skill, "watcher_start", "success")
        print(f"[{self.skill}] Started — poll every {self.poll_seconds}s")

        self.on_start()

        while self._running:
            try:
                items = self.poll()
                for item in items:
                    try:
                        self.process(item)
                    except Exception as exc:
                        self.on_error(exc)

            except KeyboardInterrupt:
                print(f"\n[{self.skill}] Stopping...")
                self._running = False
                break
            except Exception as exc:
                self.log.log_error(self.skill, "poll_loop", str(exc))
                print(f"[{self.skill}] Poll error: {exc}")

            time.sleep(self.poll_seconds)

        self.log.log(self.skill, "watcher_stop", "success")
        print(f"[{self.skill}] Stopped.")

    def stop(self) -> None:
        """Signal the loop to stop after current iteration."""
        self._running = False
