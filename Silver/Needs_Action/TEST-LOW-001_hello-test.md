<!-- AGENT METADATA
  received_at : 2026-02-17 17:54:20
  source      : file_watcher (internal)
  risk_level  : low
  approval    : not_required
  retries     : 0
-->

# Task: TEST-LOW-001

**Type:** Test
**Priority:** Low

## Description

Yeh ek simple test task hai jo Silver tier ka low-risk flow test karta hai.

## Steps

1. Is task ko Inbox se Needs_Action mein move karo
2. Metadata inject karo (risk_level: low)
3. Confirm karo ke task classify hua

## Expected Result

- Task Needs_Action mein move ho jaye
- Metadata block prepend ho jaye with `risk_level: low`
- `approval: not_required` ho
