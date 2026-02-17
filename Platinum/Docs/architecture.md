# Platinum Tier — Architecture

## Overview

Platinum tier splits the AI Employee into two execution zones:

```
+─────────────────────────────────────────────────────────────────+
│  CLOUD (Oracle Free VM — 24/7)       LOCAL (Windows PC)         │
│                                                                  │
│  gmail_watcher ─────────────────►  Needs_Action/cloud/          │
│  whatsapp (via Green API) ──────►  Needs_Action/local/  ◄──── (Local WA watcher)
│                                                                  │
│  file_watcher (Cloud)                                            │
│    Needs_Action/cloud/ ─► In_Progress/cloud/                    │
│    (claim-by-move)                                               │
│                                                                  │
│  email_drafter ────────────────►  Pending_Approval/cloud/       │
│  social_drafter ───────────────►  Pending_Approval/cloud/       │
│                                                                  │
│  sync_agent (git push) ────────►  GitHub ◄──── git pull (Local) │
│                                                                  │
│  health_monitor ───────────────►  Signals/                      │
│                                      │                           │
│                         watchdog.py ─► Dashboard.md (merge)     │
│                                                                  │
│                         approval_agent.py                        │
│                           Pending_Approval/cloud/ ─► A / R      │
│                           Approved ─► Done/ + MCP send          │
│                           Rejected ─► Failed/                   │
+─────────────────────────────────────────────────────────────────+
```

---

## Full Demo Flow: Email → Approved Reply

```
1.  Email arrives in Gmail inbox (Cloud always-on)
    └─► gmail_watcher.py polls Gmail API (60s interval)
    └─► Creates: Needs_Action/cloud/EMAIL_YYYYMMDD_subject.md

2.  file_watcher.py (Cloud) detects new file
    └─► Claim-by-move: Needs_Action/cloud/ → In_Progress/cloud/
    └─► Detects EMAIL_ prefix → triggers email_drafter.py

3.  email_drafter.py reads In_Progress/cloud/EMAIL_*.md
    └─► Generates draft reply (intent detection)
    └─► Creates: Pending_Approval/cloud/APPROVAL_*.md
    └─► Writes: Signals/SIGNAL_*_approval_needed.md

4.  sync_agent.py (every 5 min)
    └─► git add Platinum/ && git commit && git push

5.  Local: git pull (auto or manual)
    └─► watchdog.py sees new Signals/ → merges to Dashboard.md
    └─► Human sees approval badge in Dashboard.md (Obsidian)

6.  Human runs: python Local/approval_agent.py
    └─► Lists APPROVAL_*.md files
    └─► Views draft, presses A (approve) or R (reject)

7a. APPROVED:
    └─► Moved to Done/
    └─► MCP Gmail send triggered (Phase 2)
    └─► Signal written → Dashboard updated
    └─► git push → Cloud sees completion

7b. REJECTED:
    └─► Moved to Failed/REJECTED_*.md with reason
    └─► Signal written
    └─► Cloud can redraft if needed
```

---

## Folder Responsibilities

| Folder | Owner | Purpose |
|--------|-------|---------|
| `Needs_Action/cloud/` | Cloud | Tasks Cloud must handle |
| `Needs_Action/local/` | Local | Tasks Local must handle |
| `In_Progress/cloud/` | Cloud | Claimed tasks (cloud) |
| `In_Progress/local/` | Local | Claimed tasks (local) |
| `Pending_Approval/cloud/` | Cloud writes / Local reads | Drafts waiting for human |
| `Pending_Approval/local/` | Local | Local items pending approval |
| `Done/` | Both | Completed tasks |
| `Failed/` | Both | Failed/rejected tasks |
| `Signals/` | Cloud writes / Local reads | Cloud → Dashboard events |
| `Briefings/` | Cloud | CEO briefings (future) |
| `Logs/` | Both | Audit logs |
| `Memory/` | Both | Long-term memory |

---

## Key Rules

### 1. Claim-by-move (no locks needed)
```python
shutil.move(src_needs_action, dst_in_progress)  # atomic rename
# If FileNotFoundError: another agent claimed it — skip silently
```

### 2. Single-writer: Dashboard.md
- Cloud NEVER writes Dashboard.md directly
- Cloud writes small signal files to Signals/
- Local watchdog.py reads Signals/ and merges → Dashboard.md
- This prevents git conflicts on Dashboard.md

### 3. Secrets never sync (.gitignore)
```
.env
credentials.json
token.json
whatsapp_config.json
*.pem / *.key / *.token
```

### 4. Draft-only (Cloud)
- Cloud creates drafts only
- Cloud never sends emails or posts socially
- Only Local (with human approval) triggers final actions

---

## Process Map

```
Cloud VM:
  orchestrator.py
    ├── gmail_watcher.py     (60s poll)
    ├── file_watcher.py      (5s poll, claim-by-move)
    ├── sync_agent.py --loop (5min git pull/push)
    └── health_monitor.py --loop (5min checks)

Local PC:
  watchdog.py
    ├── whatsapp_watcher.py  (5s poll, Green API)
    ├── filesystem_watcher.py (5s poll, ~/Desktop/AI_Drop/)
    └── [signal merge to Dashboard every 60s]

  approval_agent.py  ← run manually when Dashboard shows pending
```

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Cloud VM | Oracle Cloud Free Tier (ARM Ubuntu 22.04) |
| Process manager | systemd + Python subprocess orchestrator |
| Gmail | Gmail API (google-api-python-client) |
| WhatsApp | Green API (polling, no Playwright) |
| Sync | Git (GitHub private repo) |
| Task format | Markdown (.md) |
| Vault GUI | Obsidian |
| Logging | Custom AuditLogger (pipe-delimited) |
| Retry | Custom with_retry decorator (exponential backoff) |
| MCP | Phase 2 (Odoo, Gmail send, social post) |
