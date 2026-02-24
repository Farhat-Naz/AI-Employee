<!-- AGENT METADATA
  received_at : 2026-02-17 17:54:54
  source      : file_watcher (internal)
  risk_level  : high
  approval    : required
  retries     : 0
-->

# Task: TEST-HIGH-002

**Type:** Test
**Priority:** High

## Description

Production server pe deploy karna hai. Yeh task high-risk hai kyunki isme "deploy" aur "production" keywords hain.

## Steps

1. Deploy latest build to production
2. Verify deployment success

## Expected Result

- Task Awaiting_Approval mein route ho
- `risk_level: high` set ho
- `approval: required` ho
