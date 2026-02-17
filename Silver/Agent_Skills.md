# 🧠 Agent Skills

---

## 🥉 Bronze Tier Skills

### Skill: Scan Inbox
**Trigger:** New file in /Inbox
**Action:** Move to /Needs_Action with metadata

---

### Skill: Process Task
**Trigger:** File appears in /Needs_Action
**Action:**
- Read task
- Create Plan.md
- Execute steps
- Move task to /Done

---

### Skill: Update Dashboard
**Trigger:** Task completed
**Action:** Log task in Dashboard.md

---

### Skill: Self-Audit
**Trigger:** On startup
**Action:** Verify folder structure & rules

---

## 🥈 Silver Tier Skills

### Skill: Task Classification
**Trigger:** Task enters Inbox
**Action:**
- Assess risk level: `low` / `medium` / `high`
- Assign priority
- Inject metadata block into task file
- Handled by: `Watchers/file_watcher.py`

---

### Skill: Approval Required
**Trigger:** Task metadata contains `approval: required` OR risk = `high`
**Action:**
- Do NOT execute task
- Move task to `/Awaiting_Approval`
- Mark as `approval_pending` in Dashboard

---

### Skill: Retry On Failure
**Trigger:** Task execution failure
**Action:**
- Log failure reason in task file
- Increment retry counter
- Retry up to **3 times**
- After 3 failures → move to `/Failed`

---

### Skill: Memory Append
**Trigger:** Task completion
**Action:**
- Extract lesson / decision from completed task
- Append row to `/Memory/decisions.md`
- Update `/Memory/notes.md` if config changed

---

### Skill: External Watcher — Gmail
**Trigger:** Unread Gmail message matching configured query
**Action:**
- Convert email → structured task `.md` file
- Drop into `/Inbox`
- Mark email as read
- Handled by: `Watchers/gmail_watcher.py`

---

### Skill: External Watcher — File System
**Trigger:** New `.md` file appears in `/Inbox`
**Action:**
- Classify risk level
- Inject metadata
- Move to `/Needs_Action`
- Handled by: `Watchers/file_watcher.py`

---

### Skill: External Watcher — WhatsApp
**Trigger:** Incoming WhatsApp message from allowed number
**Action:**
- Poll Green API instance for new messages (every 5s)
- Filter by allowed_numbers (configured in whatsapp_config.json)
- Convert message → structured task `.md` file
- Drop into `/Inbox`
- Delete notification from Green API queue
- Handled by: `Watchers/whatsapp_watcher.py`
