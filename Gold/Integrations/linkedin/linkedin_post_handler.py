"""
linkedin_post_handler.py — LinkedIn Post Handler with Approval Flow
--------------------------------------------------------------------
Processes LinkedIn posting requests from task files with human approval.

Workflow:
1. Task created in Inbox/ with linkedin posting request
2. file_watcher moves to Needs_Action/ with approval:required metadata
3. Human reviews in Needs_Action/ and approves by adding "approved:true"
4. This script monitors Needs_Action/ for approved LinkedIn posts
5. Executes post and moves task to Done/

Usage:
    python linkedin_post_handler.py --watch     # Run in watch mode (recommended)
    python linkedin_post_handler.py --once      # Process once and exit
"""

import os
import sys

# Fix Windows console encoding issues
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, errors='replace')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, errors='replace')
import time
import json
import re
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

try:
    from linkedin_client import post_update, post_article_share, validate_access_token, audit
except ImportError as e:
    print(f"[ERROR] Could not import linkedin_client: {e}")
    print("Make sure linkedin_client.py is in the same directory")
    sys.exit(1)

# ── Configuration ────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent.parent.parent  # Navigate to personalAI root
NEEDS_ACTION_DIR = BASE_DIR / "Silver" / "Needs_Action"
DONE_DIR = BASE_DIR / "Silver" / "Done"
FAILED_DIR = BASE_DIR / "Silver" / "Failed"
MEMORY_DIR = BASE_DIR / "Silver" / "Memory"

POLL_SECONDS = 10  # How often to check for approved LinkedIn posts


# ── Metadata Parsing ─────────────────────────────────────────────────────────

def parse_metadata(content: str) -> dict:
    """Extract metadata from task file."""
    metadata = {}

    # Parse HTML comment metadata
    metadata_match = re.search(r'<!-- AGENT METADATA\s+(.*?)\s+-->', content, re.DOTALL)
    if metadata_match:
        metadata_text = metadata_match.group(1)
        for line in metadata_text.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                metadata[key.strip()] = value.strip()

    # Parse YAML frontmatter if present
    yaml_match = re.search(r'^---\s+(.*?)\s+---', content, re.DOTALL | re.MULTILINE)
    if yaml_match:
        yaml_text = yaml_match.group(1)
        for line in yaml_text.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                metadata[key.strip()] = value.strip()

    return metadata


def parse_linkedin_request(content: str) -> dict:
    """
    Extract LinkedIn posting details from task content.

    Supported formats:
    - post_type: text | article
    - post_content: "Your post text here"
    - article_url: https://example.com/article (for article shares)
    - visibility: PUBLIC | CONNECTIONS
    """
    linkedin_data = {}

    # Look for LinkedIn-specific fields in the content
    patterns = {
        'post_type': r'post_type\s*:\s*(\w+)',
        'post_content': r'post_content\s*:\s*["\']?(.*?)["\']?(?:\n|$)',
        'article_url': r'article_url\s*:\s*(https?://\S+)',
        'visibility': r'visibility\s*:\s*(\w+)',
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            linkedin_data[key] = match.group(1).strip()

    # Default values
    linkedin_data.setdefault('post_type', 'text')
    linkedin_data.setdefault('visibility', 'PUBLIC')

    return linkedin_data


def is_linkedin_post_task(content: str) -> bool:
    """Check if task is a LinkedIn posting request."""
    lower_content = content.lower()
    return any([
        'linkedin' in lower_content and 'post' in lower_content,
        'post_type:' in lower_content,
        'linkedin_post' in lower_content
    ])


def is_approved(metadata: dict, content: str) -> bool:
    """Check if task has been approved by human."""
    # Check metadata approval field
    if metadata.get('approval') == 'approved' or metadata.get('approved') == 'true':
        return True

    # Check for approved:true in content
    if re.search(r'approved\s*:\s*true', content, re.IGNORECASE):
        return True

    return False


# ── Post Execution ───────────────────────────────────────────────────────────

def execute_linkedin_post(linkedin_data: dict, task_name: str) -> tuple[bool, str]:
    """
    Execute the LinkedIn post.

    Returns:
        (success: bool, message: str)
    """
    try:
        post_type = linkedin_data.get('post_type', 'text').lower()

        if post_type == 'text':
            # Post text update
            post_content = linkedin_data.get('post_content')
            if not post_content:
                return False, "Error: post_content is required for text posts"

            visibility = linkedin_data.get('visibility', 'PUBLIC').upper()
            result = post_update(post_content, visibility)
            post_id = result.get('id', 'unknown')

            return True, f"[SUCCESS] Text post created successfully. Post ID: {post_id}"

        elif post_type == 'article':
            # Share article
            article_url = linkedin_data.get('article_url')
            if not article_url:
                return False, "Error: article_url is required for article shares"

            comment = linkedin_data.get('post_content', '')
            result = post_article_share(article_url, comment)
            post_id = result.get('id', 'unknown')

            return True, f"[SUCCESS] Article shared successfully. Post ID: {post_id}"

        else:
            return False, f"Error: Unknown post_type '{post_type}'. Use 'text' or 'article'"

    except Exception as e:
        return False, f"Error posting to LinkedIn: {str(e)}"


# ── Task Management ──────────────────────────────────────────────────────────

def append_to_memory(task_name: str, result: str) -> None:
    """Append task result to Memory/decisions.md."""
    memory_file = MEMORY_DIR / "decisions.md"
    memory_file.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"\n## {task_name}\n**Date:** {timestamp}\n**Result:** {result}\n\n"

    with open(memory_file, 'a', encoding='utf-8') as f:
        f.write(entry)


def move_task(task_file: Path, destination_dir: Path, result_message: str) -> None:
    """Move task file to destination and append result."""
    destination_dir.mkdir(parents=True, exist_ok=True)

    # Read original content
    with open(task_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Append result
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    result_block = f"\n\n---\n## Execution Result\n**Timestamp:** {timestamp}\n**Status:** {result_message}\n"
    updated_content = content + result_block

    # Write to destination
    dest_file = destination_dir / task_file.name
    with open(dest_file, 'w', encoding='utf-8') as f:
        f.write(updated_content)

    # Remove original
    task_file.unlink()

    # Log to memory
    append_to_memory(task_file.name, result_message)


def process_task(task_file: Path) -> None:
    """Process a single LinkedIn posting task."""
    print(f"\n[{datetime.now():%H:%M:%S}] Processing: {task_file.name}")

    try:
        # Read task file
        with open(task_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if it's a LinkedIn post
        if not is_linkedin_post_task(content):
            print(f"  → Not a LinkedIn post task, skipping")
            return

        # Parse metadata
        metadata = parse_metadata(content)

        # Check approval
        if not is_approved(metadata, content):
            print(f"  → Awaiting approval (approval:required in metadata)")
            return

        print(f"  [APPROVED] Task approved by human")

        # Parse LinkedIn request
        linkedin_data = parse_linkedin_request(content)
        print(f"  → Post type: {linkedin_data.get('post_type')}")
        print(f"  → Visibility: {linkedin_data.get('visibility')}")

        # Execute post
        success, message = execute_linkedin_post(linkedin_data, task_file.name)

        if success:
            print(f"  {message}")
            move_task(task_file, DONE_DIR, f"SUCCESS: {message}")
            audit("linkedin_post_handler", f"posted: {task_file.name}", 0)
        else:
            print(f"  [FAILED] {message}")
            move_task(task_file, FAILED_DIR, f"FAILED: {message}")
            audit("linkedin_post_handler", f"failed: {task_file.name} - {message}", 0)

    except Exception as e:
        error_msg = f"Exception while processing {task_file.name}: {str(e)}"
        print(f"  [ERROR] {error_msg}")
        move_task(task_file, FAILED_DIR, f"EXCEPTION: {error_msg}")
        audit("linkedin_post_handler", f"exception: {task_file.name}", 0)


# ── Main Loop ────────────────────────────────────────────────────────────────

def process_once() -> None:
    """Process all approved LinkedIn tasks once."""
    print(f"\n{'='*60}")
    print("LinkedIn Post Handler — Processing Once")
    print(f"{'='*60}")
    print(f"Needs Action: {NEEDS_ACTION_DIR}")
    print(f"Done: {DONE_DIR}")
    print(f"Failed: {FAILED_DIR}")

    # Validate LinkedIn connection
    print("\nValidating LinkedIn connection...")
    if not validate_access_token():
        print("[FAILED] LinkedIn connection failed. Check your access token.")
        sys.exit(1)
    print("[OK] LinkedIn connection validated")

    # Process tasks
    if not NEEDS_ACTION_DIR.exists():
        print(f"\n[ERROR] Directory not found: {NEEDS_ACTION_DIR}")
        return

    task_files = list(NEEDS_ACTION_DIR.glob("*.md"))

    if not task_files:
        print("\nNo tasks found in Needs_Action/")
        return

    print(f"\nFound {len(task_files)} task(s) to check")

    for task_file in sorted(task_files):
        process_task(task_file)

    print(f"\n{'='*60}")
    print("Processing complete")
    print(f"{'='*60}\n")


def watch_mode() -> None:
    """Continuously monitor for approved LinkedIn tasks."""
    print(f"\n{'='*60}")
    print("LinkedIn Post Handler — Watch Mode")
    print(f"{'='*60}")
    print(f"Needs Action: {NEEDS_ACTION_DIR}")
    print(f"Done: {DONE_DIR}")
    print(f"Failed: {FAILED_DIR}")
    print(f"Poll interval: {POLL_SECONDS} seconds")

    # Validate LinkedIn connection
    print("\nValidating LinkedIn connection...")
    if not validate_access_token():
        print("[FAILED] LinkedIn connection failed. Check your access token.")
        sys.exit(1)
    print("[OK] LinkedIn connection validated")

    print(f"\n{'='*60}")
    print("Watching for approved LinkedIn posts... (Ctrl+C to stop)")
    print(f"{'='*60}\n")

    try:
        while True:
            if not NEEDS_ACTION_DIR.exists():
                print(f"[ERROR] Directory not found: {NEEDS_ACTION_DIR}")
                time.sleep(POLL_SECONDS)
                continue

            task_files = list(NEEDS_ACTION_DIR.glob("*.md"))

            for task_file in sorted(task_files):
                process_task(task_file)

            time.sleep(POLL_SECONDS)

    except KeyboardInterrupt:
        print("\n\nStopping LinkedIn post handler...")
        print("Goodbye!")


# ── CLI Entry Point ──────────────────────────────────────────────────────────

def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python linkedin_post_handler.py --watch    # Run in watch mode")
        print("  python linkedin_post_handler.py --once     # Process once and exit")
        sys.exit(1)

    mode = sys.argv[1]

    if mode == "--watch":
        watch_mode()
    elif mode == "--once":
        process_once()
    else:
        print(f"Unknown mode: {mode}")
        print("Use --watch or --once")
        sys.exit(1)


if __name__ == "__main__":
    main()
