"""
Bronze Tier — Inbox Watcher
============================
Watches /Inbox for new .md files and automatically calls triage_item.
Runs as a background process.

Usage:
    python watcher.py

Requirements:
    pip install watchdog
"""

import time
import logging
from pathlib import Path

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileMovedEvent
except ImportError:
    raise SystemExit(
        "watchdog is not installed.\n"
        "Run:  pip install watchdog\n"
    )

from skills import triage_item, update_dashboard

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

VAULT_ROOT = Path(__file__).parent.parent      # Bronze/
INBOX      = VAULT_ROOT / "Inbox"

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("watcher")


# ---------------------------------------------------------------------------
# Event Handler
# ---------------------------------------------------------------------------

class InboxHandler(FileSystemEventHandler):
    """Reacts to new files dropped in /Inbox."""

    def _process(self, path: Path) -> None:
        """Common processing for any new .md file in Inbox."""
        if path.suffix.lower() != ".md":
            log.info("Ignored non-md file: %s", path.name)
            return

        if path.name.startswith(".") or path.name.startswith("~"):
            return

        if not path.exists():
            return

        log.info("New file detected in Inbox: %s", path.name)
        time.sleep(0.5)

        result = triage_item(str(path))

        if result["success"]:
            log.info(
                "Triaged '%s' — type=%s | priority=%s",
                path.name,
                result["task_type"],
                result["priority"],
            )
        else:
            log.error("Triage failed for '%s': %s", path.name, result["message"])

    def on_created(self, event: FileCreatedEvent) -> None:
        if event.is_directory:
            return
        self._process(Path(event.src_path))

    def on_moved(self, event: FileMovedEvent) -> None:
        """Catch files renamed into Inbox (e.g. Obsidian temp → final file)."""
        if event.is_directory:
            return
        dest = Path(event.dest_path)
        if dest.parent == INBOX:
            self._process(dest)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    INBOX.mkdir(exist_ok=True)

    log.info("Bronze Tier Watcher started.")
    log.info("Watching: %s", INBOX)

    # Sync dashboard on startup
    update_dashboard()
    log.info("Dashboard synced on startup.")

    handler  = InboxHandler()
    observer = Observer()
    observer.schedule(handler, str(INBOX), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(2)
    except KeyboardInterrupt:
        log.info("Watcher stopped by user.")
    finally:
        observer.stop()
        observer.join()


if __name__ == "__main__":
    main()
