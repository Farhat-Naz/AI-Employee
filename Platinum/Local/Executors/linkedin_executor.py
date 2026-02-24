"""
linkedin_executor.py — Platinum Tier LinkedIn Executor
-------------------------------------------------------
Executes approved LinkedIn posts using Gold tier integration.

Flow:
1. Reads approved posts from Pending_Approval/linkedin/
2. Calls Gold/Integrations/linkedin/linkedin_client.py
3. Posts to LinkedIn
4. Moves to Done/linkedin/
5. Logs to audit trail

Usage:
    python linkedin_executor.py --watch     # Continuous monitoring
    python linkedin_executor.py --once      # Process once and exit
"""

import os
import sys
import time
import re
from pathlib import Path
from datetime import datetime

# Add Gold tier LinkedIn integration to path
PLATINUM_ROOT = Path(__file__).parent.parent.parent
GOLD_LINKEDIN = PLATINUM_ROOT.parent / "Gold" / "Integrations" / "linkedin"
sys.path.insert(0, str(GOLD_LINKEDIN))

# Add Platinum shared utilities
SHARED_DIR = PLATINUM_ROOT / "Shared"
sys.path.insert(0, str(SHARED_DIR))

try:
    from linkedin_client import post_update, post_article_share, validate_access_token
    LINKEDIN_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import LinkedIn client: {e}")
    print(f"Make sure Gold/Integrations/linkedin/ exists")
    LINKEDIN_AVAILABLE = False

try:
    from audit_logger import AuditLogger
except ImportError:
    class AuditLogger:
        def log(self, *args, **kwargs): pass


# Configuration
PENDING_APPROVAL = PLATINUM_ROOT / "Pending_Approval" / "linkedin"
DONE = PLATINUM_ROOT / "Done" / "linkedin"
FAILED = PLATINUM_ROOT / "Failed" / "linkedin"
LOGS_DIR = PLATINUM_ROOT / "Logs"

POLL_INTERVAL = 30  # seconds


# ── File Parsing ─────────────────────────────────────────────────────────────

def parse_linkedin_post(content: str) -> dict:
    """Extract LinkedIn post details from file content."""
    linkedin_data = {}

    # Extract post_type
    type_match = re.search(r'post_type\s*:\s*(\w+)', content, re.IGNORECASE)
    if type_match:
        linkedin_data['post_type'] = type_match.group(1).strip()

    # Extract post_content
    content_match = re.search(
        r'post_content\s*:\s*["\']?(.*?)["\']?(?=\n\s*(?:visibility|approved|---|$))',
        content,
        re.DOTALL | re.IGNORECASE
    )
    if content_match:
        post_content = content_match.group(1).strip()
        # Remove quotes if present
        post_content = re.sub(r'^["\']|["\']$', '', post_content)
        linkedin_data['post_content'] = post_content

    # Extract article_url
    url_match = re.search(r'article_url\s*:\s*(https?://\S+)', content, re.IGNORECASE)
    if url_match:
        linkedin_data['article_url'] = url_match.group(1).strip()

    # Extract visibility
    vis_match = re.search(r'visibility\s*:\s*(\w+)', content, re.IGNORECASE)
    if vis_match:
        linkedin_data['visibility'] = vis_match.group(1).strip().upper()
    else:
        linkedin_data['visibility'] = 'PUBLIC'

    return linkedin_data


def is_approved(content: str) -> bool:
    """Check if post is approved."""
    # Check for approved:true or autonomous_approval:true
    if re.search(r'approved\s*:\s*true', content, re.IGNORECASE):
        return True
    if re.search(r'autonomous_approval\s*:\s*true', content, re.IGNORECASE):
        return True
    return False


# ── LinkedIn Posting ─────────────────────────────────────────────────────────

def execute_linkedin_post(linkedin_data: dict, task_name: str) -> tuple:
    """
    Execute LinkedIn post.

    Returns:
        (success: bool, message: str, post_id: str)
    """
    if not LINKEDIN_AVAILABLE:
        return False, "LinkedIn client not available", None

    try:
        post_type = linkedin_data.get('post_type', 'text').lower()
        visibility = linkedin_data.get('visibility', 'PUBLIC')

        if post_type == 'text':
            # Post text update
            post_content = linkedin_data.get('post_content')
            if not post_content:
                return False, "post_content is required for text posts", None

            print(f"  Posting text update...")
            print(f"  Content length: {len(post_content)} chars")
            print(f"  Visibility: {visibility}")

            result = post_update(post_content, visibility)
            post_id = result.get('id', 'unknown')

            return True, f"Text post published successfully", post_id

        elif post_type == 'article':
            # Share article
            article_url = linkedin_data.get('article_url')
            if not article_url:
                return False, "article_url is required for article shares", None

            comment = linkedin_data.get('post_content', '')

            print(f"  Sharing article: {article_url}")
            print(f"  Comment length: {len(comment)} chars")

            result = post_article_share(article_url, comment)
            post_id = result.get('id', 'unknown')

            return True, f"Article shared successfully", post_id

        else:
            return False, f"Unknown post_type: {post_type}", None

    except Exception as e:
        return False, f"Error posting to LinkedIn: {str(e)}", None


# ── Task Processing ──────────────────────────────────────────────────────────

def append_execution_result(content: str, success: bool, message: str, post_id: str = None) -> str:
    """Append execution result to file content."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    result_block = f"""

---
## Execution Result (Platinum Executor)
**Timestamp:** {timestamp}
**Success:** {success}
**Message:** {message}
"""
    if post_id:
        result_block += f"**Post ID:** {post_id}\n"
        result_block += f"**Direct Link:** https://www.linkedin.com/feed/update/{post_id}/\n"

    return content + result_block


def process_approved_post(post_file: Path, audit_logger: AuditLogger) -> bool:
    """
    Process a single approved LinkedIn post.

    Returns:
        True if processed successfully, False otherwise
    """
    print(f"\n[{datetime.now():%H:%M:%S}] Processing: {post_file.name}")

    try:
        # Read post file
        content = post_file.read_text(encoding='utf-8')

        # Check if approved
        if not is_approved(content):
            print(f"  ⚠ Not approved, skipping")
            return False

        print(f"  ✓ Post is approved")

        # Parse LinkedIn post data
        linkedin_data = parse_linkedin_post(content)

        if not linkedin_data.get('post_content'):
            print(f"  ✗ No post content found")
            error_content = append_execution_result(
                content, False, "No post content found"
            )
            failed_file = FAILED / post_file.name
            FAILED.mkdir(parents=True, exist_ok=True)
            failed_file.write_text(error_content, encoding='utf-8')
            post_file.unlink()
            return False

        # Execute post
        print(f"  Executing LinkedIn post...")
        success, message, post_id = execute_linkedin_post(linkedin_data, post_file.name)

        # Update content with result
        result_content = append_execution_result(content, success, message, post_id)

        if success:
            print(f"  ✓ SUCCESS: {message}")
            if post_id:
                print(f"  Post ID: {post_id}")

            # Move to Done
            DONE.mkdir(parents=True, exist_ok=True)
            done_file = DONE / post_file.name
            done_file.write_text(result_content, encoding='utf-8')
            post_file.unlink()

            audit_logger.log(
                "linkedin_executor",
                f"posted: {post_file.name}",
                {"post_id": post_id, "success": True}
            )
            return True

        else:
            print(f"  ✗ FAILED: {message}")

            # Move to Failed
            FAILED.mkdir(parents=True, exist_ok=True)
            failed_file = FAILED / post_file.name
            failed_file.write_text(result_content, encoding='utf-8')
            post_file.unlink()

            audit_logger.log(
                "linkedin_executor",
                f"failed: {post_file.name}",
                {"error": message, "success": False}
            )
            return False

    except Exception as e:
        error_msg = f"Exception processing {post_file.name}: {str(e)}"
        print(f"  ✗ {error_msg}")

        try:
            error_content = append_execution_result(
                post_file.read_text(encoding='utf-8'), False, error_msg
            )
            FAILED.mkdir(parents=True, exist_ok=True)
            failed_file = FAILED / post_file.name
            failed_file.write_text(error_content, encoding='utf-8')
            post_file.unlink()
        except:
            pass

        audit_logger.log(
            "linkedin_executor",
            f"exception: {post_file.name}",
            {"error": str(e), "success": False}
        )
        return False


# ── Main Loop ────────────────────────────────────────────────────────────────

def process_once(audit_logger: AuditLogger):
    """Process all approved LinkedIn posts once."""
    print(f"\n{'='*60}")
    print("Platinum Tier — LinkedIn Executor")
    print(f"{'='*60}")
    print(f"Pending Approval: {PENDING_APPROVAL}")
    print(f"Done: {DONE}")
    print(f"Failed: {FAILED}")

    if not LINKEDIN_AVAILABLE:
        print("\n✗ LinkedIn client not available")
        print("Make sure Gold/Integrations/linkedin/ is set up")
        return

    # Validate LinkedIn connection
    print("\nValidating LinkedIn connection...")
    try:
        if validate_access_token():
            print("✓ LinkedIn connection valid")
        else:
            print("✗ LinkedIn connection failed")
            return
    except Exception as e:
        print(f"✗ Error validating connection: {e}")
        return

    # Create directories
    PENDING_APPROVAL.mkdir(parents=True, exist_ok=True)
    DONE.mkdir(parents=True, exist_ok=True)
    FAILED.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # Find approved posts
    post_files = list(PENDING_APPROVAL.glob("*.md"))

    if not post_files:
        print("\nNo approved posts found")
        return

    print(f"\nFound {len(post_files)} post(s) to process\n")

    success_count = 0
    failed_count = 0

    for post_file in sorted(post_files):
        result = process_approved_post(post_file, audit_logger)
        if result:
            success_count += 1
        else:
            failed_count += 1

    print(f"\n{'='*60}")
    print("Processing Complete")
    print(f"{'='*60}")
    print(f"Published: {success_count}")
    print(f"Failed: {failed_count}")
    print(f"{'='*60}\n")


def watch_mode(audit_logger: AuditLogger):
    """Continuously monitor for approved LinkedIn posts."""
    print(f"\n{'='*60}")
    print("Platinum Tier — LinkedIn Executor (Watch Mode)")
    print(f"{'='*60}")
    print(f"Monitoring: {PENDING_APPROVAL}")
    print(f"Poll interval: {POLL_INTERVAL} seconds")

    if not LINKEDIN_AVAILABLE:
        print("\n✗ LinkedIn client not available")
        print("Make sure Gold/Integrations/linkedin/ is set up")
        return

    # Validate connection once at start
    print("\nValidating LinkedIn connection...")
    try:
        if validate_access_token():
            print("✓ LinkedIn connection valid")
        else:
            print("✗ LinkedIn connection failed - check your token")
            return
    except Exception as e:
        print(f"✗ Error validating connection: {e}")
        return

    print(f"\nWatching for approved LinkedIn posts... (Ctrl+C to stop)")
    print(f"{'='*60}\n")

    try:
        while True:
            post_files = list(PENDING_APPROVAL.glob("*.md"))

            if post_files:
                print(f"\n[{datetime.now():%H:%M:%S}] Found {len(post_files)} post(s)")
                for post_file in sorted(post_files):
                    process_approved_post(post_file, audit_logger)

            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        print("\n\nStopping LinkedIn executor...")
        print("Goodbye!")


# ── CLI Entry Point ──────────────────────────────────────────────────────────

def main():
    """Main entry point."""
    # Initialize audit logger
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    audit_logger = AuditLogger(str(LOGS_DIR))

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python linkedin_executor.py --watch    # Run in watch mode")
        print("  python linkedin_executor.py --once     # Process once and exit")
        sys.exit(1)

    mode = sys.argv[1]

    if mode == "--watch":
        watch_mode(audit_logger)
    elif mode == "--once":
        process_once(audit_logger)
    else:
        print(f"Unknown mode: {mode}")
        print("Use --watch or --once")
        sys.exit(1)


if __name__ == "__main__":
    main()
