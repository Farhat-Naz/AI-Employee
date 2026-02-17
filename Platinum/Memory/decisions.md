# Platinum Memory — Decisions

## 2026-02-17

**DECISION:** Platinum tier architecture chosen — Cloud + Local split
- Cloud: Oracle Free VM (ARM Ubuntu 22.04, 1 OCPU + 6 GB free)
- Local: Windows PC (Obsidian + approval agent)
- Sync: Git via GitHub private repo (Phase 1)

**DECISION:** Green API for WhatsApp (not Playwright)
- Reason: Already working from Silver/Gold tiers
- Playwright requires Chrome + session — not suitable for headless cloud
- Green API polling works on both Cloud and Local

**DECISION:** Git as Phase 1 message bus (no Redis/Kafka needed)
- Reason: Simple, free, already set up, Obsidian-compatible
- Limitation: 5-minute sync latency acceptable for approval workflow
- Phase 2: Direct API if real-time needed

**DECISION:** Claim-by-move (shutil.move) for task claiming — no lock files
- Reason: Atomic rename on most filesystems
- FileNotFoundError on race = silent skip (correct behavior)

**DECISION:** Single-writer rule for Dashboard.md
- Cloud writes Signals/SIGNAL_*.md
- Local watchdog.py merges signals -> Dashboard.md
- Prevents git conflicts on shared file

**DECISION:** Draft-only Cloud agents
- email_drafter and social_drafter never send/post
- Human must approve via Local approval_agent.py
- Aligns with "human in the loop" principle
