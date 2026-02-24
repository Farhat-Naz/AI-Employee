# 🧠 Agent Skills

---

## 🥉 Bronze Tier Skills

### Skill: Scan Inbox
**Trigger:** New file in /Inbox
**Action:** Move to /Needs_Action with metadata

### Skill: Process Task
**Trigger:** File in /Needs_Action
**Action:** Read → Plan → Execute → Move to /Done

### Skill: Update Dashboard
**Trigger:** Task completed
**Action:** Log task in Dashboard.md

### Skill: Self-Audit
**Trigger:** On startup
**Action:** Verify folder structure & rules

---

## 🥈 Silver Tier Skills

### Skill: Task Classification
**Trigger:** Task enters Inbox
**Action:** Assess risk, assign priority, inject metadata
**Handler:** Watchers/file_watcher.py

### Skill: Approval Required
**Trigger:** `approval: required` OR risk = high
**Action:** Route to /Awaiting_Approval

### Skill: Retry On Failure
**Trigger:** Task execution failure
**Action:** Log → retry (max 3) → move to /Failed

### Skill: Memory Append
**Trigger:** Task completion
**Action:** Append to Memory/decisions.md + notes.md

### Skill: External Watcher — Gmail
**Trigger:** Unread Gmail matching query
**Action:** Convert email → task → drop in /Inbox
**Handler:** Watchers/gmail_watcher.py

### Skill: External Watcher — File System
**Trigger:** New .md in /Inbox
**Action:** Classify → inject metadata → move to /Needs_Action
**Handler:** Watchers/file_watcher.py

---

## 🥇 Gold Tier Skills

### Skill: Ralph Wiggum Loop
**Trigger:** Multi-step task in /Needs_Action
**Action:**
- PLAN → ACT → OBSERVE → REFLECT → repeat
- Max 10 iterations
- Every iteration logged to Audit_Logs/
- On completion → /Done
- On block → NEEDS_HUMAN
**Handler:** MCP_Servers/odoo/odoo_mcp_server.py (or relevant MCP)

---

### Skill: Odoo Accounting Integration
**Trigger:** Task with `integration: odoo` metadata
**Action:**
- Connect to Odoo 19+ via JSON-RPC
- Supported actions: create_invoice, get_partner, journal_entry, balance_report
- All actions require approval if financial write
**Handler:** MCP_Servers/odoo/odoo_mcp_server.py
**Config:** MCP_Servers/odoo/odoo_config.json

---

### Skill: Facebook/Instagram Post
**Trigger:** Task with `integration: facebook` or `integration: instagram`
**Action:**
- Post message to Facebook Page or Instagram
- Fetch engagement summary (reach, likes, comments)
- Log to Audit_Logs/
- Requires approval always
**Handler:** Integrations/facebook_instagram/fb_ig_client.py
**Config:** Integrations/facebook_instagram/fb_ig_config.json

---

### Skill: Twitter/X Post
**Trigger:** Task with `integration: twitter`
**Action:**
- Post tweet
- Fetch mention + engagement summary (impressions, engagements)
- Log to Audit_Logs/
- Requires approval always
**Handler:** Integrations/twitter/twitter_client.py
**Config:** Integrations/twitter/twitter_config.json

---

### Skill: Weekly CEO Briefing
**Trigger:** Every Monday 09:00 OR task `type: ceo_briefing`
**Action:**
- Pull data from Odoo + Social + Task history
- Generate Reports/CEO_Briefings/YYYY-WXX_ceo_briefing.md
- Log to Audit_Logs/
- Update Dashboard
**Handler:** Gold-tier briefing generator

---

### Skill: Comprehensive Audit Logger
**Trigger:** Every skill execution (start + end)
**Action:**
- Write to Audit_Logs/YYYY-MM-DD_audit.log
- Format: `[timestamp] [skill] [action] [result] [duration_ms]`
- Never deletes logs — append only

---

### Skill: Error Recovery
**Trigger:** Any skill failure
**Action:**
- Log error with full traceback
- Retry up to 3 times with backoff
- On 3rd failure: graceful degradation
  - Mark task NEEDS_HUMAN
  - Update Dashboard with blocker
  - Append to Memory/notes.md

---

### Skill: Social Media Summary
**Trigger:** Task `type: social_summary` OR weekly schedule
**Action:**
- Pull last 7 days stats from Facebook, Instagram, Twitter
- Generate summary report
- Feed into CEO Briefing

---

### Skill: Architecture Documentation
**Trigger:** On significant system change
**Action:**
- Update Docs/architecture.md
- Append to Docs/lessons_learned.md
