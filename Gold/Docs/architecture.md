# System Architecture — AI Deployment Agent

**Version:** Gold Tier 1.0
**Date:** 2026-02-10

---

## Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Deployment Agent                       │
│                                                             │
│  ┌──────────┐    ┌──────────────┐    ┌───────────────────┐  │
│  │  Bronze  │───▶│    Silver    │───▶│       Gold        │  │
│  │  Layer   │    │    Layer     │    │      Layer        │  │
│  └──────────┘    └──────────────┘    └───────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Bronze Layer
- Inbox/Needs_Action/Done folder pipeline
- Manual task processing
- Dashboard updates

## Silver Layer
- file_watcher.py → auto-detects Inbox files
- gmail_watcher.py → converts emails to tasks
- Risk classification + metadata injection
- Approval routing → Awaiting_Approval/
- Retry logic → Failed/
- Memory persistence → Memory/

## Gold Layer
- **Ralph Wiggum Loop** → autonomous multi-step task completion
- **Odoo MCP Server** → accounting via JSON-RPC
- **Social MCP Server** → Facebook/Instagram/Twitter
- **Audit MCP Server** → comprehensive logging
- **CEO Briefing Generator** → weekly business reports

---

## Data Flow

```
External Signal (Email/File)
        │
        ▼
    Watchers/
    (classify + metadata)
        │
        ▼
    Inbox/
        │
        ▼
    Needs_Action/
        │
    ┌───┴────────────────────┐
    │                        │
approval:required          execute
    │                  (Ralph Wiggum Loop)
    ▼                        │
Awaiting_Approval/      ┌────┴─────┐
    │                   │          │
approved             Done/      Failed/
    │                   │
    └───────────────▶ Memory/
                        │
                     Dashboard/
                        │
                   CEO Briefing
```

---

## MCP Server Architecture

```
Agent Core
    │
    ├── MCP_Servers/odoo/odoo_mcp_server.py
    │       └── Odoo 19 (localhost:8069) via XML-RPC
    │
    ├── MCP_Servers/social/social_mcp_server.py
    │       ├── Facebook Graph API v19.0
    │       ├── Instagram Graph API v19.0
    │       └── Twitter API v2
    │
    └── MCP_Servers/audit/audit_mcp_server.py
            └── Audit_Logs/ (append-only)
```

---

## Ralph Wiggum Loop

```
task
  │
  ▼
PLAN (agent breaks task into steps)
  │
  ▼
ACT (execute step N)
  │
  ▼
OBSERVE (check result)
  │
  ├── success → next step → loop back to ACT
  ├── failure → retry (max 3) → replan → ACT
  ├── blocked → NEEDS_HUMAN → Awaiting_Approval
  └── complete → Done/ + Memory + Dashboard
```

---

## Security Model

| Action | Risk | Required |
|--------|------|----------|
| Read files | Low | None |
| Write task files | Low | None |
| Post social media | High | Approval |
| Odoo financial write | High | Approval |
| Send emails | High | Approval |
| Read Odoo data | Medium | Logged |
| Fetch social metrics | Low | Logged |
