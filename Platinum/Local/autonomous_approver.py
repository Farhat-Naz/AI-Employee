"""
autonomous_approver.py — Platinum Tier Autonomous Approval System
------------------------------------------------------------------
Automatically approves low-risk tasks, routes high-risk to human.

Risk Levels:
- LOW: Auto-approve (read, fetch, query, search)
- MEDIUM: Configurable (update, modify, send to known contacts)
- HIGH: Always require human approval (delete, deploy, payment, post)

Usage:
    python autonomous_approver.py --watch     # Continuous monitoring
    python autonomous_approver.py --once      # Process once and exit
"""

import os
import sys
import time
import re
from pathlib import Path
from datetime import datetime
from typing import Tuple, Dict, List

# Add parent to path for shared utilities
sys.path.insert(0, str(Path(__file__).parent.parent / "Shared"))

try:
    from audit_logger import AuditLogger
    from retry_handler import retry_with_backoff
except ImportError:
    print("Warning: Could not import shared utilities")
    # Fallback implementations
    class AuditLogger:
        def log(self, *args, **kwargs): pass
    def retry_with_backoff(fn): return fn


# Configuration
VAULT_ROOT = Path(__file__).parent.parent.parent  # personalAI root
PLATINUM_ROOT = Path(__file__).parent.parent  # Platinum folder

PENDING_APPROVAL = PLATINUM_ROOT / "Pending_Approval"
NEEDS_ACTION = PLATINUM_ROOT / "Needs_Action"
FAILED = PLATINUM_ROOT / "Failed"
LOGS_DIR = PLATINUM_ROOT / "Logs"

# Risk classification keywords
HIGH_RISK_KEYWORDS = [
    "delete", "deploy", "production", "billing", "payment", "purchase",
    "cloud", "database", "drop", "remove", "terminate", "cancel"
]

MEDIUM_RISK_KEYWORDS = [
    "update", "modify", "push", "send", "email", "post", "publish",
    "edit", "change", "alter", "write"
]

LOW_RISK_KEYWORDS = [
    "read", "fetch", "query", "search", "get", "view", "list",
    "show", "display", "check", "verify", "test"
]

# Configurable: Auto-approve medium risk tasks from trusted sources
AUTO_APPROVE_MEDIUM = False  # Set to True for more automation
TRUSTED_SOURCES = ["internal", "system", "scheduled"]


# ── Risk Assessment ──────────────────────────────────────────────────────────

def assess_risk(content: str, metadata: Dict[str, str]) -> Tuple[str, float, List[str]]:
    """
    Assess risk level of a task.

    Returns:
        (risk_level: str, confidence: float, reasons: List[str])
    """
    content_lower = content.lower()
    reasons = []

    # Check for explicit risk level in metadata
    if 'risk_level' in metadata:
        explicit_risk = metadata['risk_level'].lower()
        if explicit_risk in ['high', 'medium', 'low']:
            reasons.append(f"Explicit risk level: {explicit_risk}")
            return explicit_risk, 1.0, reasons

    # Check for high-risk keywords
    high_risk_matches = [kw for kw in HIGH_RISK_KEYWORDS if kw in content_lower]
    if high_risk_matches:
        reasons.append(f"High-risk keywords: {', '.join(high_risk_matches)}")
        return "high", 0.9, reasons

    # Check for medium-risk keywords
    medium_risk_matches = [kw for kw in MEDIUM_RISK_KEYWORDS if kw in content_lower]
    if medium_risk_matches:
        reasons.append(f"Medium-risk keywords: {', '.join(medium_risk_matches)}")
        confidence = 0.7 if len(medium_risk_matches) > 2 else 0.6
        return "medium", confidence, reasons

    # Check for low-risk keywords
    low_risk_matches = [kw for kw in LOW_RISK_KEYWORDS if kw in content_lower]
    if low_risk_matches:
        reasons.append(f"Low-risk keywords: {', '.join(low_risk_matches)}")
        return "low", 0.8, reasons

    # Check task type in metadata
    task_type = metadata.get('type', '').lower()
    if task_type in ['read', 'query', 'fetch', 'search']:
        reasons.append(f"Safe task type: {task_type}")
        return "low", 0.7, reasons

    if task_type in ['email', 'post', 'social', 'linkedin', 'facebook']:
        reasons.append(f"Social/communication task type: {task_type}")
        return "high", 0.8, reasons  # Social posts always need approval

    # Default to medium risk if uncertain
    reasons.append("No clear risk indicators, defaulting to medium")
    return "medium", 0.5, reasons


def should_auto_approve(risk_level: str, confidence: float, source: str) -> Tuple[bool, str]:
    """
    Determine if task should be auto-approved.

    Returns:
        (should_approve: bool, reason: str)
    """
    # Never auto-approve high risk
    if risk_level == "high":
        return False, "High-risk tasks always require human approval"

    # Auto-approve low risk with high confidence
    if risk_level == "low" and confidence >= 0.7:
        return True, f"Low-risk task with {confidence:.0%} confidence"

    # Conditionally auto-approve medium risk
    if risk_level == "medium":
        if AUTO_APPROVE_MEDIUM and source in TRUSTED_SOURCES:
            return True, f"Medium-risk from trusted source: {source}"
        return False, "Medium-risk tasks require approval (configurable)"

    return False, f"Risk level '{risk_level}' with {confidence:.0%} confidence requires review"


# ── File Processing ──────────────────────────────────────────────────────────

def parse_metadata(content: str) -> Dict[str, str]:
    """Extract metadata from task file."""
    metadata = {}

    # Parse HTML comment metadata
    meta_match = re.search(r'<!-- AGENT METADATA\s+(.*?)\s+-->', content, re.DOTALL)
    if meta_match:
        meta_text = meta_match.group(1)
        for line in meta_text.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                metadata[key.strip()] = value.strip()

    # Parse YAML frontmatter
    yaml_match = re.search(r'^---\s+(.*?)\s+---', content, re.DOTALL | re.MULTILINE)
    if yaml_match:
        yaml_text = yaml_match.group(1)
        for line in yaml_text.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                metadata[key.strip()] = value.strip()

    return metadata


def process_approval_request(task_file: Path, audit_logger: AuditLogger) -> bool:
    """
    Process a single approval request.

    Returns:
        True if processed successfully, False otherwise
    """
    print(f"\n[{datetime.now():%H:%M:%S}] Processing: {task_file.name}")

    try:
        # Read task file
        content = task_file.read_text(encoding='utf-8')
        metadata = parse_metadata(content)

        # Assess risk
        risk_level, confidence, reasons = assess_risk(content, metadata)
        source = metadata.get('source', 'unknown')

        print(f"  Risk Assessment:")
        print(f"    Level: {risk_level.upper()}")
        print(f"    Confidence: {confidence:.0%}")
        print(f"    Source: {source}")
        for reason in reasons:
            print(f"    - {reason}")

        # Decide approval
        should_approve, approval_reason = should_auto_approve(risk_level, confidence, source)

        if should_approve:
            print(f"  ✓ AUTO-APPROVED: {approval_reason}")

            # Update file with approval
            updated_content = content
            if 'approved: false' in content:
                updated_content = content.replace('approved: false', 'approved: true')
            elif 'approval    : required' in content:
                updated_content = content.replace(
                    'approval    : required',
                    'approval    : auto_approved'
                )
            else:
                # Add approval marker
                updated_content = f"{content}\n\napproved: true\nautonomous_approval: true\n"

            # Append approval log
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            approval_log = f"""

---
## Autonomous Approval
**Timestamp:** {timestamp}
**Risk Level:** {risk_level}
**Confidence:** {confidence:.0%}
**Decision:** AUTO-APPROVED
**Reason:** {approval_reason}
**Reasons:** {'; '.join(reasons)}
"""
            updated_content += approval_log

            # Move to Needs_Action with approval
            dest_file = NEEDS_ACTION / task_file.name
            dest_file.write_text(updated_content, encoding='utf-8')
            task_file.unlink()

            audit_logger.log(
                "autonomous_approver",
                f"auto_approved: {task_file.name}",
                {"risk": risk_level, "confidence": confidence}
            )
            return True

        else:
            print(f"  ⚠ REQUIRES HUMAN APPROVAL: {approval_reason}")

            # Update metadata to show pending human review
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            review_note = f"""

---
## Autonomous Review
**Timestamp:** {timestamp}
**Risk Level:** {risk_level}
**Confidence:** {confidence:.0%}
**Decision:** REQUIRES HUMAN APPROVAL
**Reason:** {approval_reason}
**Assessment:** {'; '.join(reasons)}

**Action Required:** Human must review and approve this task.
"""
            updated_content = content + review_note
            task_file.write_text(updated_content, encoding='utf-8')

            audit_logger.log(
                "autonomous_approver",
                f"requires_human: {task_file.name}",
                {"risk": risk_level, "confidence": confidence}
            )
            return False

    except Exception as e:
        error_msg = f"Error processing {task_file.name}: {str(e)}"
        print(f"  ✗ {error_msg}")

        # Move to Failed
        if task_file.exists():
            failed_file = FAILED / task_file.name
            failed_content = task_file.read_text(encoding='utf-8')
            failed_content += f"\n\n---\n## Processing Error\n{error_msg}\n"
            failed_file.write_text(failed_content, encoding='utf-8')
            task_file.unlink()

        audit_logger.log("autonomous_approver", f"error: {task_file.name}", {"error": str(e)})
        return False


# ── Main Loop ────────────────────────────────────────────────────────────────

def process_once(audit_logger: AuditLogger):
    """Process all pending approvals once."""
    print(f"\n{'='*60}")
    print("Platinum Tier — Autonomous Approver")
    print(f"{'='*60}")
    print(f"Pending Approval: {PENDING_APPROVAL}")
    print(f"Auto-Approve Medium Risk: {AUTO_APPROVE_MEDIUM}")

    # Create directories if needed
    PENDING_APPROVAL.mkdir(parents=True, exist_ok=True)
    NEEDS_ACTION.mkdir(parents=True, exist_ok=True)
    FAILED.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # Find pending approval tasks
    task_files = list(PENDING_APPROVAL.glob("*.md"))

    if not task_files:
        print("\nNo tasks pending approval")
        return

    print(f"\nFound {len(task_files)} task(s) pending approval\n")

    approved_count = 0
    requires_human_count = 0

    for task_file in sorted(task_files):
        result = process_approval_request(task_file, audit_logger)
        if result:
            approved_count += 1
        else:
            requires_human_count += 1

    print(f"\n{'='*60}")
    print(f"Processing Complete")
    print(f"{'='*60}")
    print(f"Auto-Approved: {approved_count}")
    print(f"Requires Human: {requires_human_count}")
    print(f"{'='*60}\n")


def watch_mode(audit_logger: AuditLogger):
    """Continuously monitor for approval requests."""
    print(f"\n{'='*60}")
    print("Platinum Tier — Autonomous Approver (Watch Mode)")
    print(f"{'='*60}")
    print(f"Monitoring: {PENDING_APPROVAL}")
    print(f"Poll interval: 30 seconds")
    print(f"Auto-Approve Medium Risk: {AUTO_APPROVE_MEDIUM}")
    print(f"\nPress Ctrl+C to stop")
    print(f"{'='*60}\n")

    try:
        while True:
            task_files = list(PENDING_APPROVAL.glob("*.md"))
            if task_files:
                print(f"\n[{datetime.now():%H:%M:%S}] Found {len(task_files)} pending task(s)")
                for task_file in sorted(task_files):
                    process_approval_request(task_file, audit_logger)

            time.sleep(30)

    except KeyboardInterrupt:
        print("\n\nStopping autonomous approver...")
        print("Goodbye!")


# ── CLI Entry Point ──────────────────────────────────────────────────────────

def main():
    """Main entry point."""
    # Initialize audit logger
    audit_logger = AuditLogger(str(LOGS_DIR))

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python autonomous_approver.py --watch    # Run in watch mode")
        print("  python autonomous_approver.py --once     # Process once and exit")
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
