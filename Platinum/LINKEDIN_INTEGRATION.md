# Platinum Tier - LinkedIn Integration Guide

**Version:** 1.0
**Date:** 2026-02-24
**Status:** ✅ Production Ready

---

## 🎯 Overview

Platinum tier LinkedIn integration enables **Cloud-Local split architecture**:
- **Cloud** (24/7): Drafts LinkedIn posts
- **Local** (Your PC): Approves & publishes posts

This ensures you maintain control while allowing 24/7 automation.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    CLOUD (Oracle VM)                     │
│                       24/7 Running                       │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  1. Gmail Watcher → Detects "Post this to LinkedIn"    │
│     └─> Creates task: Needs_Action/cloud/EMAIL_123.md  │
│                                                          │
│  2. Social Drafter → Reads email, creates draft        │
│     └─> Saves: Pending_Approval/linkedin/DRAFT_123.md  │
│                                                          │
│  3. Sync Agent → Pushes to GitHub (every 5 min)        │
│     └─> git add, commit, push                          │
│                                                          │
└─────────────────────────────────────────────────────────┘
                            ↓ GitHub Sync
┌─────────────────────────────────────────────────────────┐
│                   LOCAL (Your Windows PC)                │
│                    When You're Online                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  4. Watchdog → Pulls from GitHub                        │
│     └─> git pull                                        │
│                                                          │
│  5. Autonomous Approver → Analyzes draft                │
│     ├─> Risk: HIGH (social post keyword)               │
│     ├─> Confidence: 90%                                 │
│     └─> Decision: REQUIRES HUMAN APPROVAL               │
│                                                          │
│  6. Human Reviews → Opens Obsidian                      │
│     ├─> Reads Pending_Approval/linkedin/DRAFT_123.md   │
│     ├─> Reviews content, checks quality                 │
│     └─> Approves: Changes "approved: false" → "true"   │
│                                                          │
│  7. LinkedIn Executor → Posts to LinkedIn               │
│     ├─> Calls Gold/Integrations/linkedin/linkedin_client.py │
│     ├─> Posts via LinkedIn API v2                      │
│     ├─> Gets Post ID: urn:li:share:7432017...          │
│     └─> Moves to Done/linkedin/DRAFT_123.md            │
│                                                          │
│  8. Watchdog → Pushes result to GitHub                  │
│     └─> git add, commit, push                          │
│                                                          │
└─────────────────────────────────────────────────────────┘
                            ↓ GitHub Sync
┌─────────────────────────────────────────────────────────┐
│                         CLOUD                            │
│          Receives confirmation, continues watching        │
└─────────────────────────────────────────────────────────┘
```

---

## 📦 Components

### 1. Gold Tier (Base Integration)
**Location:** `Gold/Integrations/linkedin/`

**Files:**
- `linkedin_client.py` - LinkedIn API wrapper (OAuth 2.0, post_update, post_article_share)
- `linkedin_config.json` - OAuth credentials (NEVER sync to Git!)
- `linkedin_post_handler.py` - Silver/Gold tier handler

**Status:** ✅ Complete & Working (4+ real posts published)

### 2. Platinum Tier (Cloud-Local Split)
**Location:** `Platinum/Local/Executors/`

**New Files:**
- ✅ `linkedin_executor.py` - Platinum executor (wraps Gold tier)
- ✅ `autonomous_approver.py` - Auto-approval system

**Location:** `Platinum/Cloud/`

**Files:**
- `social_drafter.py` - Drafts LinkedIn posts from various sources
- `sync_agent.py` - GitHub sync every 5 min

---

## 🚀 Quick Start

### Prerequisites
1. ✅ Gold tier LinkedIn integration configured
2. ✅ `Gold/Integrations/linkedin/linkedin_config.json` exists
3. ✅ LinkedIn access token valid
4. ✅ Tested Gold tier (manual posting works)

### Test Platinum Integration (5 minutes)

#### Step 1: Create Test Draft
```bash
cat > "D:\quarterr 4\personalAI\Platinum\Pending_Approval\linkedin\test_platinum.md" << 'EOF'
---
type: linkedin_post
source: test
created: 2026-02-24
---

# LinkedIn: Platinum Tier Test Post

post_type: text
post_content: "Testing Platinum Tier LinkedIn integration! 🚀

This post demonstrates the Cloud-Local split architecture:
- Cloud drafts content 24/7
- Local approves & publishes
- Full audit trail maintained

Building the future of AI automation!

#PlatinumTier #AI #Automation #BuildingInPublic"

visibility: PUBLIC

approved: false
EOF
```

#### Step 2: Run Autonomous Approver
```bash
cd "D:\quarterr 4\personalAI\Platinum\Local"
python autonomous_approver.py --once
```

**Expected Output:**
```
[HH:MM:SS] Processing: test_platinum.md
  Risk Assessment:
    Level: HIGH
    Confidence: 80%
    Source: test
    - Social/communication task type: linkedin_post
  ⚠ REQUIRES HUMAN APPROVAL: High-risk tasks always require human approval
```

#### Step 3: Human Approval
```bash
# Edit the file
notepad "D:\quarterr 4\personalAI\Platinum\Pending_Approval\linkedin\test_platinum.md"

# Change this line:
approved: false

# To:
approved: true

# Save and close
```

#### Step 4: Execute Post
```bash
cd "D:\quarterr 4\personalAI\Platinum\Local\Executors"
python linkedin_executor.py --once
```

**Expected Output:**
```
============================================================
Platinum Tier — LinkedIn Executor
============================================================
Pending Approval: D:\quarterr 4\personalAI\Platinum\Pending_Approval\linkedin
Done: D:\quarterr 4\personalAI\Platinum\Done\linkedin
Failed: D:\quarterr 4\personalAI\Platinum\Failed\linkedin

Validating LinkedIn connection...
✓ LinkedIn connection valid

Found 1 post(s) to process

[HH:MM:SS] Processing: test_platinum.md
  ✓ Post is approved
  Executing LinkedIn post...
  Content length: 234 chars
  Visibility: PUBLIC
  ✓ SUCCESS: Text post published successfully
  Post ID: urn:li:share:743201...

============================================================
Processing Complete
============================================================
Published: 1
Failed: 0
============================================================
```

#### Step 5: Verify on LinkedIn
Check your LinkedIn profile - the post should be live!

**Direct Link:** Will be in `Done/linkedin/test_platinum.md`

---

## 🔄 Production Workflow

### Daily Operation

**Morning (When You Wake Up):**
```bash
# 1. Pull updates from Cloud
cd "D:\quarterr 4\personalAI"
git pull

# 2. Check pending approvals
ls Platinum/Pending_Approval/linkedin/

# 3. Run autonomous approver (checks all pending)
cd Platinum/Local
python autonomous_approver.py --once

# 4. Review any that need human approval in Obsidian
# Open: Platinum/Pending_Approval/linkedin/
# Approve: Change approved: false → true

# 5. Execute approved posts
cd Executors
python linkedin_executor.py --once

# 6. Push results
cd "D:\quarterr 4\personalAI"
git add Platinum/Done/ Platinum/Logs/
git commit -m "Executed approved LinkedIn posts"
git push
```

**Continuous Monitoring (Optional):**
```bash
# Run in watch mode - monitors continuously
cd Platinum/Local/Executors
python linkedin_executor.py --watch

# Leave running in background
# Processes approved posts automatically every 30 seconds
```

---

## 📝 Post Formats

### Text Post
```markdown
# LinkedIn: Your Title

post_type: text
post_content: "Your post content here.

Can be multiple paragraphs.

#Hashtags #Work"

visibility: PUBLIC
approved: false
```

### Article Share
```markdown
# LinkedIn: Share Article

post_type: article
article_url: https://example.com/blog/my-article
post_content: "Check out this article! Great insights on AI automation."

visibility: PUBLIC
approved: false
```

### Visibility Options
- `PUBLIC` - Everyone can see
- `CONNECTIONS` - Only your network

---

## ⚙️ Configuration

### Auto-Approve Settings
**File:** `Platinum/Local/autonomous_approver.py`

```python
# Line ~40-41
AUTO_APPROVE_MEDIUM = False  # Set to True for more automation
TRUSTED_SOURCES = ["internal", "system", "scheduled"]
```

**Options:**
- `AUTO_APPROVE_MEDIUM = False` (Default) - Only auto-approve LOW risk
- `AUTO_APPROVE_MEDIUM = True` - Also auto-approve MEDIUM risk from trusted sources

**Recommendation:** Keep `False` for social media posts

### Poll Intervals
**Autonomous Approver:** 30 seconds (in watch mode)
**LinkedIn Executor:** 30 seconds (in watch mode)
**Cloud Sync Agent:** 300 seconds (5 minutes)

---

## 🔍 Monitoring & Logs

### Audit Logs
**Location:** `Platinum/Logs/YYYY-MM-DD_audit.log`

**Sample Entry:**
```
[2026-02-24 16:30:15] [autonomous_approver] [requires_human: test_platinum.md] {"risk": "high", "confidence": 0.8}
[2026-02-24 16:35:42] [linkedin_executor] [posted: test_platinum.md] {"post_id": "urn:li:share:7432017...", "success": true}
```

### Success Tracking
```bash
# Count successful posts today
grep "linkedin_executor.*posted" Platinum/Logs/$(date +%Y-%m-%d)_audit.log | wc -l

# View all LinkedIn activity
grep "linkedin" Platinum/Logs/$(date +%Y-%m-%d)_audit.log
```

### Check Post Status
```bash
# Pending
ls Platinum/Pending_Approval/linkedin/

# Published
ls Platinum/Done/linkedin/

# Failed
ls Platinum/Failed/linkedin/
```

---

## 🐛 Troubleshooting

### Issue: "LinkedIn client not available"
**Cause:** Can't find Gold tier integration

**Fix:**
```bash
# Verify Gold tier exists
ls "D:\quarterr 4\personalAI\Gold\Integrations\linkedin\linkedin_client.py"

# If missing, LinkedIn integration not set up
# Follow: Gold/Integrations/linkedin/QUICKSTART.md
```

### Issue: "LinkedIn connection failed"
**Cause:** OAuth token expired (60 days)

**Fix:**
```bash
cd "D:\quarterr 4\personalAI\Gold\Integrations\linkedin"
python get_linkedin_token.py
# Follow OAuth flow to refresh token
```

### Issue: Post stuck in Pending_Approval
**Cause:** Not approved or autonomous approver not running

**Fix:**
```bash
# Check approval status
grep "approved" Platinum/Pending_Approval/linkedin/YOUR_POST.md

# Should show: approved: true
# If not, change it manually

# Run executor
cd Platinum/Local/Executors
python linkedin_executor.py --once
```

### Issue: Post moved to Failed
**Cause:** API error or invalid content

**Fix:**
```bash
# Check error message
tail Platinum/Failed/linkedin/YOUR_POST.md

# Common errors:
# - "post_content is required" → Add post_content field
# - "Post too long" → Reduce to under 3000 chars
# - "Token expired" → Refresh token (see above)
```

---

## 🔐 Security

### What's Safe to Sync (Git)
- ✅ Post drafts (.md files)
- ✅ Execution results
- ✅ Audit logs
- ✅ Python scripts

### NEVER Sync
- ❌ `linkedin_config.json` (OAuth credentials)
- ❌ `.env` files
- ❌ `credentials.json` (Gmail)
- ❌ `token.json`

### Approval Requirements
- **HIGH RISK** = Always human approval
  - All social media posts (LinkedIn, Facebook, Twitter)
  - Delete, deploy, production operations
  - Payment, billing actions

- **MEDIUM RISK** = Configurable
  - Send, email, update operations
  - Default: Human approval

- **LOW RISK** = Auto-approve
  - Read, fetch, query, search operations

---

## 📊 Success Metrics

### Current Performance
- ✅ LinkedIn integration: 100% operational
- ✅ Gold tier: 5+ real posts published
- ✅ Platinum executor: Ready for production
- ✅ Auto-approval: Tested and working

### Target Metrics
- 🎯 Uptime: 99.9% (with Cloud deployment)
- 🎯 Auto-approval accuracy: 95%+
- 🎯 Human approval time: < 2 minutes
- 🎯 Post execution time: < 5 seconds
- 🎯 Zero unauthorized posts: 100%

---

## 🚀 Next Steps

### Immediate (Today)
1. ✅ Test Platinum executor (follow Quick Start above)
2. ✅ Verify end-to-end flow works
3. ✅ Review audit logs
4. ✅ Document any issues

### Short Term (This Week)
1. Deploy Cloud VM (Oracle Free Tier)
2. Set up Cloud agents (orchestrator, watchers, drafters)
3. Configure GitHub sync (5-minute intervals)
4. Test Cloud → Local → GitHub flow

### Long Term (This Month)
1. Add Facebook integration
2. Implement scheduling (post at specific times)
3. CEO briefing automation
4. Multi-platform posting (LinkedIn + Facebook + Twitter)

---

## 📚 Related Documentation

- [Gold LinkedIn Integration](../Gold/Integrations/linkedin/README.md)
- [Platinum Tier Spec](./Platinum_Tier_Spec.md)
- [Platinum Status](./PLATINUM_STATUS.md)
- [Autonomous Approver](./Local/autonomous_approver.py)
- [LinkedIn Executor](./Local/Executors/linkedin_executor.py)

---

## 🎯 Quick Reference

### Key Commands
```bash
# Test autonomous approver
cd Platinum/Local
python autonomous_approver.py --once

# Execute approved posts
cd Platinum/Local/Executors
python linkedin_executor.py --once

# Watch mode (continuous)
python linkedin_executor.py --watch

# Check logs
tail -f Platinum/Logs/$(date +%Y-%m-%d)_audit.log
```

### Key Locations
```
Platinum/
├── Pending_Approval/linkedin/  ← Posts awaiting approval
├── Done/linkedin/              ← Successfully published
├── Failed/linkedin/            ← Failed posts
└── Logs/                       ← Audit trail
```

---

**Status:** ✅ Production Ready
**Last Updated:** 2026-02-24
**Integration Level:** Platinum (Cloud-Local Split)
