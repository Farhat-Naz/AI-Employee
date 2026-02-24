# 🧠 Agent Skills (Bronze Tier)

## Skill: Scan Inbox
**Trigger:** New file in /Inbox
**Action:** Move to /Needs_Action with metadata

---

## Skill: Process Task
**Trigger:** File appears in /Needs_Action
**Action:**
- Read task
- Create Plan.md
- Execute steps
- Move task to /Done

---

## Skill: Update Dashboard
**Trigger:** Task completed
**Action:** Log task in Dashboard.md

---

## Skill: Self-Audit
**Trigger:** On startup
**Action:** Verify folder structure & rules
