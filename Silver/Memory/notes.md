# Memory — General Notes

> Auto-maintained by the AI Deployment Assistant (Silver Tier: Memory Append skill)

---

## Agent Configuration

- **Tier:** Silver
- **Watchers Active:** file_watcher.py, gmail_watcher.py
- **Max Retries:** 3
- **Approval Required For:** cloud resource creation, email sending, billing actions

---

## Known Patterns

- Tasks with `approval: required` in metadata → route to Awaiting_Approval/
- Tasks that fail 3 times → move to Failed/ with failure log
- All task completions → append to Memory/decisions.md

---

## Notes

_Agent notes will be appended here during operation._
