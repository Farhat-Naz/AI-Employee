"""
filesystem_watcher.py — Filesystem Drop-Folder Watcher (Platinum Local)
------------------------------------------------------------------------
Monitors a local drop folder for new files (PDF, images, docs, etc.)
Converts each file into a task in Platinum/Needs_Action/local/

Drop folder: ~/Desktop/AI_Drop/   (or set DROP_FOLDER in .env)

Extends BaseWatcher from Shared/.

Run:
  python Local/Watchers/filesystem_watcher.py
"""

import os
import sys
import shutil
import mimetypes
from datetime import datetime

LOCAL_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLATINUM_DIR = os.path.dirname(LOCAL_DIR)

sys.path.insert(0, PLATINUM_DIR)

from Shared.base_watcher import BaseWatcher

# ── Paths ─────────────────────────────────────────────────────────────────────

INBOX_DIR   = os.path.join(PLATINUM_DIR, "Needs_Action", "local")
ATTACH_DIR  = os.path.join(PLATINUM_DIR, "Memory", "attachments")

# Drop folder: Desktop/AI_Drop/ by default
DROP_FOLDER = os.environ.get(
    "DROP_FOLDER",
    os.path.join(os.path.expanduser("~"), "Desktop", "AI_Drop")
)

POLL_SECONDS = 5
SKILL        = "FilesystemWatcher_Platinum"

# File types to process
ALLOWED_EXTENSIONS = {
    ".pdf", ".docx", ".doc", ".txt", ".md",
    ".xlsx", ".csv", ".png", ".jpg", ".jpeg",
    ".zip", ".json", ".xml",
}


# ── FilesystemWatcher ─────────────────────────────────────────────────────────

class FilesystemWatcher(BaseWatcher):

    def __init__(self):
        super().__init__(SKILL, poll_seconds=POLL_SECONDS)
        self._seen: set[str] = set()

    def on_start(self) -> None:
        os.makedirs(DROP_FOLDER, exist_ok=True)
        os.makedirs(INBOX_DIR, exist_ok=True)
        os.makedirs(ATTACH_DIR, exist_ok=True)
        print(f"[{self.skill}] Watching drop folder: {DROP_FOLDER}")
        print(f"[{self.skill}] Tasks -> {INBOX_DIR}")

    def poll(self) -> list[dict]:
        """Detect new files in drop folder."""
        try:
            files = {
                f for f in os.listdir(DROP_FOLDER)
                if not f.startswith(".")
                and os.path.isfile(os.path.join(DROP_FOLDER, f))
                and os.path.splitext(f)[1].lower() in ALLOWED_EXTENSIONS
            }
        except FileNotFoundError:
            return []

        new_files  = files - self._seen
        self._seen = files

        return [{"filename": f} for f in sorted(new_files)]

    def process(self, item: dict) -> None:
        """Convert dropped file to a task."""
        filename = item["filename"]
        src      = os.path.join(DROP_FOLDER, filename)

        if not os.path.exists(src):
            return

        start    = datetime.now()
        ext      = os.path.splitext(filename)[1].lower()
        mime     = mimetypes.guess_type(filename)[0] or "unknown"
        size_kb  = os.path.getsize(src) // 1024

        # Move file to Memory/attachments/
        attach_dest = os.path.join(ATTACH_DIR, filename)
        if os.path.exists(attach_dest):
            attach_dest = os.path.join(ATTACH_DIR, f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}")
        shutil.move(src, attach_dest)

        # Create task file
        ts           = datetime.now().strftime("%Y%m%d_%H%M%S")
        task_slug    = os.path.splitext(filename)[0].replace(" ", "_")[:40]
        task_name    = f"DROP_{ts}_{task_slug}.md"
        task_path    = os.path.join(INBOX_DIR, task_name)

        content = f"""# Task: File Drop — {filename}

**Priority:** Medium
**Created:** {datetime.now().strftime("%Y-%m-%d")}
**Tier:** Platinum
**Source:** Filesystem Drop ({DROP_FOLDER})
**File:** {filename}
**Type:** {mime} ({ext})
**Size:** {size_kb} KB
**Stored At:** Memory/attachments/{os.path.basename(attach_dest)}

## Steps

- Step 1: File ka type aur content review karo
- Step 2: Intent/action decide karo (process, archive, respond?)
- Step 3: Relevant agent trigger karo (email_drafter, social_drafter, etc.)
- Step 4: Done/ mein complete karo

## Acceptance Criteria

- [ ] File reviewed and intent identified
- [ ] Appropriate action taken
- [ ] File archived in Memory/attachments/

## Notes

Auto-generated from filesystem drop via Platinum Local Watcher.
Original file moved to: Memory/attachments/{os.path.basename(attach_dest)}
"""
        with open(task_path, "w", encoding="utf-8") as f:
            f.write(content)

        duration_ms = int((datetime.now() - start).total_seconds() * 1000)
        print(f"[{datetime.now():%H:%M:%S}] FILE->TASK  {task_name}  ({size_kb}KB)")
        self.log.log(self.skill, "file_to_task", "success",
                     duration_ms=duration_ms,
                     task_id=task_name,
                     detail=f"file={filename} size={size_kb}KB")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    watcher = FilesystemWatcher()
    watcher.run()
