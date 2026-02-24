# Platinum Tier Specification

**Version:** 1.0
**Created:** 2026-02-17
**Status:** Implementation Phase 1 — Git Sync + Approval Loop

---

## Purpose

Platinum is the cloud-split tier of the AI Employee. It separates the work into:

- **Cloud** (Oracle Free VM, 24/7): Watches, drafts, syncs — never sleeps
- **Local** (Windows PC): Approves, executes final actions, manages WhatsApp

The key insight: Cloud does the grunt work, Local has final authority.

---

## Tier Progression

| Tier | Location | Trust | Capability |
|------|----------|-------|-----------|
| Bronze | Local | Low | Manual task list, basic structure |
| Silver | Local | Medium | Auto-classification, WhatsApp intake |
| Gold | Local | High | Audit logging, Ralph Wiggum loop, autonomous processing |
| **Platinum** | **Cloud + Local** | **Very High** | **24/7 email/social watching, draft → approve → execute** |

---

## Design Principles

### 1. Cloud is draft-only
Cloud agents (email_drafter, social_drafter) create drafts only.
They NEVER send emails or post to social media directly.
All final actions require human approval on Local.

### 2. Claim-by-move (no database needed)
```
Needs_Action/cloud/TASK.md
    -> shutil.move() ->
In_Progress/cloud/TASK.md   (atomic, no lock files needed)
```
If another agent already moved it: FileNotFoundError -> skip silently.

### 3. Single-writer Dashboard
Cloud never writes Dashboard.md (risk of git conflict).
Cloud writes small Signals/SIGNAL_*.md files.
Local watchdog merges signals -> Dashboard.md.

### 4. Git as Phase 1 message bus
- Cloud pushes drafts and signals via `sync_agent.py` (every 5 min)
- Local pulls, reviews, approves, pushes results back
- Phase 2: Replace git with direct API calls or message queue

### 5. Secrets never in git
.env, credentials.json, token.json — manual copy to each machine.
GitHub repo stays clean and potentially public-safe.

---

## Minimum Demo Gate

**Email arrives when you're asleep:**
1. Gmail Watcher captures it -> Needs_Action/cloud/
2. File Watcher claims it -> email_drafter runs
3. Draft created in Pending_Approval/cloud/
4. sync_agent pushes to GitHub
5. Next morning: you open Obsidian, see "1 approval pending"
6. Run: `python Local/approval_agent.py`
7. Read draft, press A to approve
8. Email sent (Phase 2: via MCP), task -> Done/

**This flow works even if your PC was off overnight.**

---

## Phase 1 Scope (Current)

- [x] Folder structure + .keep files
- [x] Shared utilities (BaseWatcher, retry_handler, AuditLogger)
- [x] Cloud watchers (Gmail, File)
- [x] Cloud agents (email_drafter, social_drafter, health_monitor, sync_agent, orchestrator)
- [x] Local agents (approval_agent, watchdog, whatsapp_watcher, filesystem_watcher)
- [x] Systemd services + setup_cloud.sh
- [x] Docs (architecture, oracle_setup, deployment, security)
- [ ] Oracle VM deployed (manual step)
- [ ] Gmail OAuth authorized on VM
- [ ] First end-to-end email demo

## Phase 2 Scope (Future)

- [ ] MCP Gmail send (Local actually sends approved reply)
- [ ] MCP Social post (Local posts approved social content)
- [ ] Odoo integration (link from Gold/MCP_Servers/odoo/)
- [ ] WhatsApp reply via Green API (from approved draft)
- [ ] CEO Briefing generation (weekly summary)
- [ ] A2A agent messaging (Cloud <-> Local direct)
- [ ] Payment/billing handler (route to human, NEVER auto-execute)

---

## Security Summary

- **Never sync**: .env, credentials.json, token.json, whatsapp_config.json
- **Never auto-pay**: All financial actions require human approval
- **Never auto-post**: All social posts require human approval
- **Never auto-send**: All emails require human approval (Platinum)
- See: `Docs/security_guide.md`

---

## Files Overview

```
Platinum/
├── Platinum_Tier_Spec.md     <- This file
├── Company_Handbook.md       <- Rules for AI agents
├── Agent_Skills.md           <- All skills registered
├── Dashboard.md              <- Live status (Local writes, Obsidian view)
│
├── Shared/                   <- Used by both Cloud and Local
│   ├── base_watcher.py       <- ABC for all watchers
│   ├── retry_handler.py      <- Exponential backoff decorator
│   └── audit_logger.py       <- Append-only log -> Logs/
│
├── Cloud/                    <- Runs on Oracle VM 24/7
│   ├── orchestrator.py       <- Starts + monitors all cloud processes
│   ├── gmail_watcher.py      <- Gmail API -> Needs_Action/cloud/
│   ├── file_watcher.py       <- Claim-by-move + dispatch
│   ├── email_drafter.py      <- Draft reply -> Pending_Approval/cloud/
│   ├── social_drafter.py     <- Draft post -> Pending_Approval/cloud/
│   ├── health_monitor.py     <- Checks + WA alert -> Signals/
│   ├── sync_agent.py         <- git pull/push every 5 min
│   └── Services/             <- systemd unit files
│
├── Local/                    <- Runs on Windows PC
│   ├── watchdog.py           <- Starts local processes + signal merge
│   ├── approval_agent.py     <- Interactive approve/reject terminal
│   ├── Watchers/
│   │   ├── whatsapp_watcher.py  <- Green API -> Needs_Action/local/
│   │   └── filesystem_watcher.py <- Drop folder -> Needs_Action/local/
│   └── MCP/
│       └── mcp_config.json   <- Phase 2 integration config
│
└── Docs/                     <- Reference
    ├── architecture.md
    ├── oracle_cloud_setup.md
    ├── deployment_guide.md
    └── security_guide.md
```
