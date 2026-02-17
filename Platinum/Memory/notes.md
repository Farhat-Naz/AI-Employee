# Platinum Memory — Operational Notes

## 2026-02-17

**NOTE:** Oracle Free Tier ARM VM (Ampere) is always-free, not time-limited
- Unlike x86 trial VMs, ARM instances are permanently free
- Limit: 4 OCPUs + 24 GB RAM total (can use across 1-4 instances)
- We use: 1 OCPU + 6 GB (well within limits)

**NOTE:** Gmail OAuth token.json never expires unless revoked
- Refresh token is included — auto-refreshes access token
- Only need re-auth if: revoked at myaccount.google.com, or app deleted

**NOTE:** Green API free tier limits
- 500 messages/month incoming on free plan
- Upgrade if WhatsApp volume increases significantly

**NOTE:** sync_agent commits may appear noisy in git log
- Each 5-min cycle creates a commit if there are changes
- To view meaningful commits only: `git log --no-merges --all --author="Human"`
- Agent commits tagged with "[cloud-sync]" prefix

**NOTE:** Obsidian on Windows auto-opens .md files from Pending_Approval/
- Create an Obsidian "Dataview" query to show pending approvals badge:
  ```dataview
  LIST
  FROM "Platinum/Pending_Approval/cloud"
  WHERE file.name != ".keep"
  SORT file.mtime desc
  ```
