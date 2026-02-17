# Company Handbook — Silver Tier Extension

**Version:** 2.0 (Silver)
**Last Updated:** 2026-02-10
**Extends:** Bronze/Company_Handbook.md (all Bronze rules remain in force)

---

## 1. Silver Tier Additions

All Bronze Tier rules apply. This document adds Silver-specific rules only.

---

## 2. Folder Structure (Silver)

```
Silver/
├── Agent_Skills.md         # Bronze + Silver skills
├── Company_Handbook.md     # This file
├── Dashboard.md            # Silver live status board
├── Inbox/                  # Incoming files (monitored by file_watcher.py)
├── Needs_Action/           # Classified tasks ready to execute
├── Awaiting_Approval/      # High-risk tasks pending human sign-off
├── Memory/
│   ├── decisions.md        # Auto-appended after every task
│   └── notes.md            # Agent config & learned patterns
├── Done/                   # Completed tasks
├── Failed/                 # Tasks that exhausted retries
└── Watchers/
    ├── file_watcher.py     # Internal watcher (Inbox → Needs_Action)
    └── gmail_watcher.py    # External watcher (Gmail → Inbox)
```

---

## 3. Task Lifecycle (Silver)

```
Inbox
  ↓  [file_watcher.py: classify + inject metadata]
Needs_Action
  ↓
  ├─ approval: required OR risk: high → Awaiting_Approval (wait for human)
  │                                          ↓ approved
  └─────────────────────────────────── Needs_Action
                                             ↓ execute
                                        Done   or   retry (max 3)
                                                        ↓ still failing
                                                     Failed
```

---

## 4. Risk Classification Rules

| Risk Level | Keywords | Action |
|------------|----------|--------|
| high | delete, deploy, production, billing, payment, cloud | Route to Awaiting_Approval |
| medium | update, modify, push, send, email | Execute with extra logging |
| low | (none of the above) | Execute normally |

---

## 5. Approval Rules

A task MUST go to `Awaiting_Approval/` if:
- Metadata contains `approval: required`
- Risk level is `high`

A task in `Awaiting_Approval/` MUST NOT be executed until:
- A human adds `approved: true` to the task metadata

---

## 6. Retry Policy

- Maximum **3 retries** per task
- Each failure appends a `## Failure Log` entry to the task file
- After 3 failures: move to `Failed/`, add `status: failed` to metadata
- Failed tasks require human review before re-queuing

---

## 7. Memory Policy

After every completed task, the agent MUST:
1. Append a row to `Memory/decisions.md` with date, task ID, and lesson learned
2. Update `Memory/notes.md` if any configuration or pattern changed

Memory files are NEVER deleted — only appended.

---

## 8. Watcher Configuration

### file_watcher.py (Internal)
- Polls `Silver/Inbox/` every 5 seconds
- Injects metadata and moves files to `Needs_Action/`
- Run: `python Silver/Watchers/file_watcher.py`

### gmail_watcher.py (External)
- Polls Gmail every 60 seconds for unread messages matching `label:ai-tasks`
- Converts emails to task `.md` files, drops into `Silver/Inbox/`
- Requires: `credentials.json` in `Watchers/` (from Google Cloud Console)
- Run: `python Silver/Watchers/gmail_watcher.py`

---

## 9. Guardrails (Silver)

The agent MUST NOT perform these without explicit approval:
- Create or destroy cloud resources
- Send emails or messages
- Execute billing or payment actions
- Push code to remote repositories

---

## 10. Promotion to Gold Tier

Silver Tier is considered stable when:
- Approval flow is tested and working
- Retry logic handles failures gracefully
- Memory is being persisted across sessions
- At least one external watcher is receiving live signals

Only after a stable Silver Tier → Gold Tier (multi-agent, autonomous deployment).

---

## Summary

| Tier | Milestone |
|------|-----------|
| Bronze | Agent exists |
| Silver | Agent is useful & trustworthy |
| Gold | Agent is autonomous |
