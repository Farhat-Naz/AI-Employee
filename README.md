# personalAI - Autonomous AI Agent System

**Version:** 1.0
**Date:** 2026-02-24
**Author:** Farhat Naz
**Status:** Production Ready

---

## 🎯 Overview

**personalAI** is a tiered AI autonomous agent system designed to progressively evolve from basic task automation to fully autonomous operation. Built with Python and file-system orchestration, it provides human-supervised AI assistance across multiple domains.

### Key Features

- 🔄 **Progressive Autonomy** - Four tiers from manual to fully autonomous
- 🛡️ **Human Oversight** - Smart approval workflows for high-risk operations
- 📊 **Full Audit Trail** - Every action logged with timestamps and results
- 🔗 **Multi-Platform Integration** - LinkedIn, Gmail, Odoo, Facebook, Instagram, Twitter
- 💾 **Memory System** - Persistent decision logging and learning
- 🔐 **Security First** - OAuth 2.0, risk classification, approval routing

---

## 🏗️ Architecture

### Tier System

The system is organized into four progressive capability tiers:

```
Bronze (Basic) → Silver (Semi-Autonomous) → Gold (Autonomous) → Platinum (Fully Autonomous)
```

---

## 🥉 Bronze Tier - Basic Agent

**Status:** ✅ Complete

### Features
- Manual task pipeline
- Folder-based workflow
- Basic file operations
- Simple task execution

### Structure
```
Bronze/
├── tasks/
├── completed/
└── README.md
```

### Use Cases
- Manual task tracking
- Simple file organization
- Learning the system basics

---

## 🥈 Silver Tier - Semi-Autonomous

**Status:** ✅ Complete

### Features
- **File Watcher** - Auto-detects tasks in Inbox/
- **Gmail Watcher** - Monitors Gmail for actionable emails
- **Approval Routing** - High-risk tasks → Awaiting_Approval/
- **Risk Classification** - Auto-classifies task risk levels
  - **High Risk:** delete, deploy, production, billing, payment, cloud
  - **Medium Risk:** update, modify, push, send, email
  - **Low Risk:** read, fetch, query, search
- **Memory Persistence** - Decisions and notes logged
- **Retry Logic** - Max 3 retries on failures
- **Metadata Enrichment** - Auto-adds timestamps, source, risk level

### Structure
```
Silver/
├── Agent_Skills.md          # Available capabilities
├── Company_Handbook.md      # Operating guidelines
├── Dashboard.md             # Status overview
├── Inbox/                   # Drop tasks here
├── Needs_Action/           # Ready to execute
├── Awaiting_Approval/      # High-risk pending approval
├── Done/                   # Completed tasks
├── Failed/                 # Failed tasks
├── Memory/
│   ├── decisions.md        # Decision log
│   └── notes.md           # Configuration notes
└── Watchers/
    ├── file_watcher.py    # Monitors Inbox/
    ├── gmail_watcher.py   # Monitors Gmail
    └── SETUP_GUIDE.md
```

### Workflow
```
Task created → Inbox/ → file_watcher detects →
Classifies risk → Routes to Needs_Action/ or Awaiting_Approval/ →
Human approves (if needed) → Execute → Done/ or Failed/ →
Log to Memory/decisions.md
```

### Setup
```bash
# Start file watcher
cd Silver/Watchers
python file_watcher.py

# Start Gmail watcher (requires credentials.json)
python gmail_watcher.py
```

---

## 🥇 Gold Tier - Autonomous Employee

**Status:** 🔄 In Progress

### Features
- **Multi-Platform Integration**
  - LinkedIn (posting, engagement)
  - Odoo 19+ (business accounting)
  - Facebook & Instagram (social media)
  - Twitter/X (microblogging)
- **Ralph Wiggum Loop** - Autonomous decision-making
  - PLAN → ACT → OBSERVE → REFLECT → PLAN
  - Max 10 iterations per task
  - Self-correction and replanning
- **CEO Briefing Generation** - Weekly consolidated reports
- **Full Audit Logging** - Timestamp, action, result, duration
- **Multi-Step Autonomous Tasks** - Complex workflows without human intervention

### Structure
```
Gold/
├── MCP_Servers/            # Model Context Protocol integrations
│   ├── odoo/
│   │   ├── odoo_mcp_server.py
│   │   └── odoo_config.json
│   ├── social/
│   │   ├── social_mcp_server.py
│   │   └── social_config.json
│   └── audit/
├── Integrations/
│   ├── linkedin/
│   │   ├── linkedin_client.py
│   │   ├── linkedin_post_handler.py
│   │   ├── get_linkedin_token.py
│   │   ├── linkedin_config.json
│   │   ├── QUICKSTART.md
│   │   ├── POSTING_WORKFLOW.md
│   │   └── examples/
│   ├── facebook_instagram/
│   ├── twitter/
│   └── odoo/
├── Audit_Logs/
│   └── YYYY-MM-DD_audit.log
└── Reports/
    └── CEO_Briefings/
```

### LinkedIn Integration

**Features:**
- Post text updates (max 3000 chars)
- Share articles with commentary (max 1300 chars)
- Human approval workflow
- Full audit trail
- Visibility control (PUBLIC/CONNECTIONS)

**Workflow:**
```
1. Create .md task in Inbox/
2. file_watcher moves to Needs_Action/ (approval:required)
3. Human reviews and approves (approved:true)
4. linkedin_post_handler detects approval
5. Posts to LinkedIn via API
6. Moves to Done/ with results
7. Logs to Audit and Memory
```

**Setup:**
```bash
# 1. Configure LinkedIn OAuth
cd Gold/Integrations/linkedin
python get_linkedin_token.py

# 2. Start post handler (watch mode)
python linkedin_post_handler.py --watch

# Or process once
python linkedin_post_handler.py --once
```

**Quick Start:**
```bash
# Create a post
cat > Silver/Inbox/my_post.md << 'EOF'
# LinkedIn Post

post_type: text
post_content: "Your message here #hashtag"
visibility: PUBLIC
approved: false
EOF

# Approve it
# Edit Silver/Needs_Action/my_post.md
# Change: approved: false → approved: true

# Post it
cd Gold/Integrations/linkedin
python linkedin_post_handler.py --once
```

See [LinkedIn Integration Guide](Gold/Integrations/linkedin/POSTING_WORKFLOW.md) for details.

### Audit Logging

Every action is logged:
```
[YYYY-MM-DD HH:MM:SS] [component] [action] [result] [duration_ms]
```

Example:
```
[2026-02-24 15:12:47] [linkedin_client] [post_update] [post_id=urn:li:share:7432004555049115652] [2901ms]
```

---

## 💎 Platinum Tier - Fully Autonomous

**Status:** 🚀 Started (Partial Implementation)

### Features (Planned/In Progress)
- **Zero Human-in-Loop** - Self-authorized low-risk actions
- **Cloud-Local Hybrid** - Distributed agent operation
- **Advanced Planning** - Multi-step autonomous planning
- **Self-Healing** - Automatic error recovery and alternative approaches
- **Scheduled Operations** - Time-based task execution
- **Agent Collaboration** - Multiple agents working together

### Structure
```
Platinum/
├── agents/
│   └── cloud/
│       └── watchers/
│           ├── base_watcher.py
│           ├── gmail_watcher.py
│           └── requirements.txt
├── Vault/                  # Cloud executive dashboard
│   ├── Dashboard.md
│   ├── Needs_Action/cloud/
│   ├── Pending_Approval/cloud/
│   ├── Logs/
│   └── Plans/
└── credentials.json        # Google OAuth
```

### Risk-Based Autonomy

| Risk Level | Approval Required | Auto-Execute |
|------------|------------------|--------------|
| Low        | ❌ No            | ✅ Yes       |
| Medium     | ⚠️ Optional      | ⚠️ Configurable |
| High       | ✅ Required      | ❌ No        |

---

## 🛠️ Tech Stack

### Core Technologies
- **Language:** Python 3.14+
- **Architecture:** File-system orchestration, MCP servers
- **Storage:** Markdown files (no traditional database)
- **Authentication:** OAuth 2.0 (Google, LinkedIn)

### API Integrations
- **LinkedIn API v2** - Social media posting
- **Google Gmail API** - Email monitoring
- **Odoo 19+ JSON-RPC** - Business accounting
- **Facebook/Instagram Graph API** - Social media
- **Twitter/X API v2** - Microblogging

### Python Dependencies
```
google-auth==2.29.0
google-auth-oauthlib==1.2.0
google-auth-httplib2==0.2.0
google-api-python-client==2.130.0
requests==2.31.0
```

---

## 📦 Installation

### Prerequisites
- Python 3.14+
- Git
- OAuth credentials for integrated services

### Setup
```bash
# 1. Clone repository
git clone <repository-url>
cd personalAI

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure integrations
cd Gold/Integrations/linkedin
python get_linkedin_token.py

# 4. Start watchers
cd ../../Silver/Watchers
python file_watcher.py &
python gmail_watcher.py &

# 5. Start handlers
cd ../../Gold/Integrations/linkedin
python linkedin_post_handler.py --watch &
```

---

## 🚀 Quick Start

### 1. Create Your First Task

```bash
cat > Silver/Inbox/hello.md << 'EOF'
# Task: Hello World

Test task to verify the system.

## Acceptance Criteria
- [ ] File moves to Needs_Action/
- [ ] Task executes successfully
- [ ] Result logged to Memory/
EOF
```

### 2. Watch It Process

The file watcher will:
1. Detect the file in Inbox/
2. Add metadata (timestamp, risk level, approval status)
3. Move to Needs_Action/
4. Execute the task
5. Move to Done/
6. Log to Memory/decisions.md

### 3. Post to LinkedIn

```bash
cat > Silver/Inbox/linkedin_post.md << 'EOF'
# LinkedIn Post

post_type: text
post_content: "My first AI-automated LinkedIn post! #AI"
visibility: PUBLIC
approved: false
EOF

# Wait for file_watcher to move it to Needs_Action/
# Edit the file and change: approved: false → approved: true
# Run handler: python Gold/Integrations/linkedin/linkedin_post_handler.py --once
```

---

## 📊 Project Status

| Component | Status | Completion |
|-----------|--------|------------|
| Bronze Tier | ✅ Complete | 100% |
| Silver Tier | ✅ Complete | 100% |
| File Watcher | ✅ Complete | 100% |
| Gmail Watcher | ✅ Complete | 100% |
| Memory System | ✅ Complete | 100% |
| Gold Tier | 🔄 In Progress | 60% |
| LinkedIn Integration | ✅ Complete | 100% |
| Odoo Integration | 🔄 Partial | 40% |
| Social Media Integration | 🔄 Planned | 20% |
| Audit Logging | ✅ Complete | 100% |
| Platinum Tier | 🚀 Started | 30% |
| Cloud-Local Hybrid | 🚀 Started | 20% |
| Self-Healing | 📝 Planned | 0% |

---

## 🔒 Security

### Guardrails
- ✅ **Risk Classification** - All tasks auto-classified
- ✅ **Approval Workflows** - High-risk requires human approval
- ✅ **Audit Logging** - Full trail of all actions
- ✅ **OAuth 2.0** - Secure API authentication
- ✅ **Rate Limiting** - Prevents API abuse
- ✅ **Token Rotation** - Regular credential refresh

### Best Practices
- Never auto-approve high-risk tasks
- Review audit logs weekly
- Rotate tokens every 30-60 days
- Keep credentials in `.gitignore`
- Monitor Failed/ folder for issues
- Back up Memory/ regularly

---

## 📝 Task File Format

All tasks use Markdown with optional YAML frontmatter:

```markdown
---
priority: high
deadline: 2026-02-25
tags: [linkedin, social-media]
---

# Task: Post Weekly Update

## Description
Create and post weekly update to LinkedIn.

## Details
post_type: text
post_content: "Weekly update content here"
visibility: PUBLIC

## Approval
approved: false
```

---

## 🤝 Contributing

This is a personal project, but feedback and suggestions are welcome!

### Areas for Improvement
- [ ] Complete Odoo integration
- [ ] Add Facebook/Instagram posting
- [ ] Implement Twitter/X integration
- [ ] Build self-healing error recovery
- [ ] Create web dashboard
- [ ] Add voice interface
- [ ] Mobile app companion

---

## 📚 Documentation

- [Home](Home.md) - Navigation hub
- [Plan](Plan.md) - Session planning
- [Silver Dashboard](Silver/Dashboard.md) - Current status
- [Agent Skills](Silver/Agent_Skills.md) - Available capabilities
- [Company Handbook](Silver/Company_Handbook.md) - Operating guidelines
- [LinkedIn Integration](Gold/Integrations/linkedin/README.md)
- [LinkedIn Posting Workflow](Gold/Integrations/linkedin/POSTING_WORKFLOW.md)
- [LinkedIn Quick Start](Gold/Integrations/linkedin/QUICKSTART.md)

---

## 📧 Contact

**Author:** Farhat Naz
**Email:** faronaz786@gmail.com
**LinkedIn:** [linkedin.com/in/farhat-naz](https://www.linkedin.com/in/farhat-naz/)

---

## 📄 License

Private project - All rights reserved

---

## 🎯 Roadmap

### Q1 2026
- ✅ Complete Silver Tier
- ✅ LinkedIn integration
- 🔄 Odoo integration
- 🔄 CEO briefing system

### Q2 2026
- Social media integration (Facebook, Instagram, Twitter)
- Advanced planning system
- Multi-agent collaboration

### Q3 2026
- Platinum tier completion
- Self-healing mechanisms
- Cloud-local hybrid operation

### Q4 2026
- Web dashboard
- Mobile app
- Voice interface

---

## 🙏 Acknowledgments

Built with:
- Python 3.14
- LinkedIn API v2
- Google APIs
- Odoo JSON-RPC
- MCP (Model Context Protocol)

---

**Last Updated:** 2026-02-24
**Version:** 1.0
**Status:** Production Ready (Tiers: Bronze ✅, Silver ✅, Gold 🔄, Platinum 🚀)
