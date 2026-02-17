# Company Handbook — AI Deployment Division

**Version:** 1.0
**Last Updated:** 2026-02-10

---

## 1. Mission
Deploy, monitor, and maintain AI systems reliably, securely, and in alignment with company standards.

---

## 2. Core Principles

| # | Principle | Description |
|---|-----------|-------------|
| 1 | Plan First | Always create or update `Plan.md` before performing any work |
| 2 | Transparency | All actions and decisions must be logged in `Dashboard.md` |
| 3 | Traceability | Every completed task must be moved to the `Done/` folder |
| 4 | Security | Never expose credentials, API keys, or PII in any file |
| 5 | Minimal Footprint | Only create files that are necessary for the task at hand |

---

## 3. Folder Structure

```
personalAI/
├── Company_Handbook.md     # This file — rules and standards
├── Plan.md                 # Current session plan (always updated first)
├── Dashboard.md            # Live status board
├── Needs_Action/           # Incoming tasks awaiting action
│   └── <task-name>.md
└── Done/                   # Completed task files
    └── <task-name>.md
```

---

## 4. Task Lifecycle

1. A task file is placed in `Needs_Action/`
2. The assistant reads `Plan.md` and `Company_Handbook.md`
3. The task is read and executed
4. The task file is moved to `Done/` with a completion note appended
5. `Dashboard.md` is updated to reflect the change

---

## 5. Task File Format

Each task file in `Needs_Action/` should follow this template:

```markdown
# Task: <Title>
**Priority:** High | Medium | Low
**Created:** YYYY-MM-DD
**Owner:** <name or team>

## Description
<What needs to be done>

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Notes
<Any additional context>
```

---

## 6. Dashboard Update Format

After completing work, `Dashboard.md` must reflect:
- Total tasks pending
- Total tasks completed today
- Any blockers
- Last updated timestamp

---

## 7. Escalation Policy

- If a task is ambiguous, add a `BLOCKED` note in the task file and flag it in the Dashboard
- If a task requires credentials or external system access not available, mark as `NEEDS_HUMAN`
- Never guess or fabricate information — ask or block

---

## 8. Prohibited Actions

- Do NOT delete files — move them or archive them
- Do NOT modify task files in `Needs_Action/` — only read and move
- Do NOT commit or push code without explicit instruction
- Do NOT expose sensitive data in any output or file

---

*This handbook is the source of truth for all AI Deployment Assistant behavior.*
