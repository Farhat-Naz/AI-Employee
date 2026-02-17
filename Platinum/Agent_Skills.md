# Agent Skills — Platinum Tier

**Updated:** 2026-02-17
**Tier:** Platinum — Cloud + Local Split

Includes all Bronze + Silver + Gold skills, plus new Platinum-exclusive skills.

---

## Bronze Skills (inherited)
- Task file creation (Markdown format)
- Basic folder routing (Inbox, Done, Failed)
- Manual priority assignment

## Silver Skills (inherited)
- Risk classification (HIGH/MEDIUM/LOW keywords)
- Approval routing (Awaiting_Approval/ vs Needs_Action/)
- WhatsApp intake (Green API, allowed_numbers filter)
- Git-based vault sync

## Gold Skills (inherited)
- Audit logging (AuditLogger, pipe-delimited logs)
- PLAN/ACT/OBSERVE/REFLECT loop (Ralph Wiggum Loop)
- Metadata injection (risk_level, approval, retries)
- Auto-trigger subprocess agents
- Subprocess encoding safety (PYTHONIOENCODING=utf-8)

---

## Platinum Skills (NEW)

### Cloud Skills

#### GmailWatcher_Platinum
- Polls Gmail API every 60s for UNREAD INBOX messages
- Extracts subject, sender, body (handles multipart MIME)
- Creates EMAIL_*.md in Needs_Action/cloud/
- Marks email as read after task creation
- Retries: 3 attempts with 5s delay
- Module: `Cloud/Watchers/gmail_watcher.py`

#### FileWatcher_Platinum (Cloud)
- Polls Needs_Action/cloud/ every 5s
- Claim-by-move: Needs_Action/cloud/ -> In_Progress/cloud/
- Race condition safe (FileNotFoundError -> skip)
- Dispatches EMAIL_ tasks to email_drafter.py
- Writes Signals/ entry for Dashboard
- Module: `Cloud/Watchers/file_watcher.py`

#### EmailDrafter_Platinum
- Reads In_Progress/cloud/EMAIL_*.md
- Intent detection: billing, meeting, urgent, general
- Generates appropriate draft reply template
- Creates APPROVAL_*.md in Pending_Approval/cloud/
- Writes Signals/ for approval notification
- Module: `Cloud/email_drafter.py`

#### SocialDrafter_Platinum
- Reads social task files from In_Progress/cloud/
- Supports: Twitter (280 char), Facebook, Instagram, LinkedIn
- Tone detection: casual, professional, formal
- Creates APPROVAL_*.md in Pending_Approval/cloud/
- Module: `Cloud/social_drafter.py`

#### HealthMonitor_Platinum
- Checks every 5 minutes (--loop mode):
  - Disk space > 20% free
  - Audit log written in last 10 minutes
  - No approvals older than 24 hours
  - No tasks in Failed/ (alerts)
  - All required processes running (Linux)
- Sends WhatsApp alert via Green API if critical
- Writes Signals/SIGNAL_*_health.md
- Module: `Cloud/health_monitor.py`

#### SyncAgent_Platinum
- git pull (--rebase origin main) every 5 minutes
- git add Platinum/ && git commit && git push if changes exist
- Retries: 3 attempts, 10s delay, exponential backoff
- Skips push if nothing changed
- Module: `Cloud/sync_agent.py`

#### Orchestrator_Platinum
- Starts Cloud subprocesses (gmail_watcher, file_watcher, sync_agent, health_monitor)
- Monitors liveness every 5s
- Auto-restarts crashed processes (10s delay)
- Logs all process events to Logs/orchestrator.log
- Graceful shutdown on SIGINT/SIGTERM
- Module: `Cloud/orchestrator.py`

---

### Local Skills

#### WA_Watcher_Platinum
- Polls Green API every 5s (same as Silver/Gold)
- Allowed numbers filter (from Silver config)
- Creates WA_*.md in Needs_Action/local/
- Extends BaseWatcher
- Module: `Local/Watchers/whatsapp_watcher.py`

#### FilesystemWatcher_Platinum
- Polls ~/Desktop/AI_Drop/ every 5s
- Accepted types: .pdf, .docx, .txt, .md, .xlsx, .csv, .png, .jpg, etc.
- Moves file to Memory/attachments/
- Creates DROP_*.md in Needs_Action/local/
- Extends BaseWatcher
- Module: `Local/Watchers/filesystem_watcher.py`

#### ApprovalAgent_Platinum
- Interactive terminal: lists Pending_Approval/cloud/ files
- Shows age of pending approvals
- View (V), Approve (A), Reject (R), Skip (S), Quit (Q)
- Approve -> Done/ + MCP trigger (Phase 2)
- Reject -> Failed/REJECTED_*.md with reason
- Writes Signals/ for both approve/reject
- Module: `Local/approval_agent.py`

#### Watchdog_Platinum
- Starts Local subprocesses (whatsapp_watcher, filesystem_watcher)
- Monitors liveness every 10s, restarts if crashed
- Merges Signals/ -> Dashboard.md every 60s
- Signal merger: single-writer rule for Dashboard
- Module: `Local/watchdog.py`

---

## Shared Utilities

#### BaseWatcher
- Abstract base class for all Platinum watchers
- poll() -> list[dict], process(item) -> None
- on_start(), on_error() hooks
- Built-in AuditLogger integration
- Module: `Shared/base_watcher.py`

#### with_retry
- Decorator for transient failure resilience
- max_attempts=3, delay=2.0, backoff=2.0 (default)
- Configurable exception types
- retry_call() for non-decorator use
- Module: `Shared/retry_handler.py`

#### AuditLogger (Platinum)
- Writes to Platinum/Logs/YYYY-MM-DD_audit.log
- Pipe-delimited format (compatible with Gold)
- Methods: log, log_start, log_end, log_error, today_summary
- Module: `Shared/audit_logger.py`
