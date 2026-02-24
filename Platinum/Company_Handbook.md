# Company Handbook — Platinum Tier

**Agent Tier:** Platinum — Cloud + Local Split
**Authority Level:** Very High — Draft-Only Cloud, Human-Approved Local Execution

---

## Core Rules

### Rule 1: Draft, Don't Send
Cloud agents create drafts only.
Local agents execute only after human approval.
No exceptions for email, social media, or payments.

### Rule 2: Claim Once, Process Once
Claim-by-move prevents duplicate processing.
If a file is already gone from Needs_Action/ — skip it. No errors.

### Rule 3: Dashboard Belongs to Local
Cloud writes to Signals/. Local merges to Dashboard.md.
Cloud never touches Dashboard.md directly.

### Rule 4: Secrets Stay Local
.env files, API tokens, OAuth credentials — never in git.
Copy manually between machines.

### Rule 5: Human is Final Authority
All financial actions: NEEDS_HUMAN — never auto-execute.
All social posts: require approval via approval_agent.py.
All email replies: require approval via approval_agent.py.

### Rule 6: Log Everything
Every action logged via AuditLogger.
Logs go to Platinum/Logs/YYYY-MM-DD_audit.log.
Logs are synced to GitHub (safe — no secrets in logs).

### Rule 7: Retry with Backoff
Transient failures: use with_retry(max_attempts=3, delay=2.0, backoff=2.0).
Permanent failures: log_error and move to Failed/.
Never retry more than 3 times without human review.

### Rule 8: Health Checks Every 5 Minutes
health_monitor.py verifies all processes running.
WhatsApp alert if critical failure detected.
Signals/ entry written for Dashboard.

---

## Task Priority System

| Priority | Response Time | Examples |
|----------|--------------|---------|
| URGENT   | < 15 min     | Production down, payment issue, security alert |
| HIGH     | < 2 hours    | Client complaint, billing inquiry, urgent email |
| MEDIUM   | < 24 hours   | General emails, social posts, reports |
| LOW      | < 72 hours   | Newsletters, optional updates, FYI messages |

---

## What Cloud Agents CAN Do

- Poll Gmail inbox and create task files
- Classify and route task files (claim-by-move)
- Generate email reply drafts
- Generate social media post drafts
- Monitor health of all processes
- Sync vault via git (pull/push)
- Write signal files to Signals/
- Write to Logs/

---

## What Cloud Agents CANNOT Do

- Send emails (Phase 2 — requires Local MCP approval)
- Post to social media (Phase 2 — requires Local MCP approval)
- Execute payments (NEVER — always NEEDS_HUMAN)
- Write to Dashboard.md (Local only)
- Access WhatsApp session (Local only)
- Make decisions without human input on high-risk actions

---

## What Local Agents CAN Do

- Monitor WhatsApp (Green API)
- Watch filesystem drop folder
- Display approval queue to human
- Execute approved actions (send email, post, etc.) — Phase 2
- Merge Cloud signals into Dashboard.md
- Restart crashed Local processes

---

## Escalation Path

```
Low risk task
  -> Cloud processes automatically
  -> Done/ (no human needed for low-risk non-email tasks)

Email or social task
  -> Cloud drafts
  -> Human approves via approval_agent.py
  -> Local executes (Phase 2)

High risk task (delete, payment, production)
  -> Routes to Pending_Approval/cloud/ with APPROVAL REQUIRED
  -> Human reviews carefully before approving

NEEDS_HUMAN tag
  -> Immediately paused — human must intervene
  -> Never auto-processed
```

---

## Memory Updates

Important decisions should be logged in:
- `Memory/decisions.md` — strategic decisions
- `Memory/notes.md` — operational notes

Format:
```
[YYYY-MM-DD] DECISION: What was decided and why
[YYYY-MM-DD] NOTE: Important operational observation
```
