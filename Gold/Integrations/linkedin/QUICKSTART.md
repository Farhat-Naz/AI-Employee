# LinkedIn Posting Quick Start Guide

**Goal:** Post to LinkedIn with human approval in 5 minutes

---

## Prerequisites Check

Run these commands to verify setup:

```bash
# 1. Check if LinkedIn is configured
ls Gold/Integrations/linkedin/linkedin_config.json

# 2. Test LinkedIn connection
cd Gold/Integrations/linkedin
python -c "from linkedin_client import validate_access_token; print('✓ Connected!' if validate_access_token() else '❌ Failed')"
```

**If connection fails:** Run `python get_linkedin_token.py` to configure LinkedIn first.

---

## Quick Start (3 Steps)

### Step 1: Start the Watchers

Open **2 terminal windows**:

**Terminal 1 — File Watcher:**
```bash
cd Silver/Watchers
python file_watcher.py
```

**Terminal 2 — LinkedIn Handler:**
```bash
cd Gold/Integrations/linkedin
python linkedin_post_handler.py --watch
```

Keep both running.

---

### Step 2: Create a Post

Copy example to Inbox:

```bash
# Copy the simple example
cp Gold/Integrations/linkedin/examples/example_simple_post.md Silver/Inbox/my_first_post.md

# Or create your own
cat > Silver/Inbox/my_post.md << 'EOF'
# LinkedIn: Test Post

post_type: text
post_content: "Testing my new AI-powered LinkedIn posting system! 🚀 #AI #Automation"
visibility: PUBLIC
approved: false
EOF
```

**What happens automatically:**
1. File watcher detects file in Inbox
2. Adds metadata (sets `approval:required`)
3. Moves to `Needs_Action/`

---

### Step 3: Approve & Post

**Open the file:**
```bash
# Find your file
ls Silver/Needs_Action/

# Edit it
nano Silver/Needs_Action/my_post.md
# (or use VS Code, any text editor)
```

**Approve by changing:**
```markdown
approved: false
```
to:
```markdown
approved: true
```

**Save and close.**

**What happens automatically:**
1. LinkedIn handler detects approval
2. Posts to LinkedIn via API
3. Moves file to `Done/` with results
4. Logs to Memory and Audit Logs

**Check LinkedIn:** Your post should be live! 🎉

---

## Verify Success

```bash
# Check Done folder
ls Silver/Done/

# View result
cat Silver/Done/my_post.md
# Should show: "SUCCESS: ✓ Text post created successfully"

# Check audit log
tail Gold/Audit_Logs/$(date +%Y-%m-%d)_audit.log

# Check memory
tail Silver/Memory/decisions.md
```

---

## Common Post Templates

### 1. Simple Text Post

```markdown
# LinkedIn: Update

post_type: text
post_content: "Your message here #hashtag"
visibility: PUBLIC
approved: false
```

### 2. Share Article

```markdown
# LinkedIn: Share Article

post_type: article
article_url: https://example.com/article
post_content: "Check out this article!"
visibility: PUBLIC
approved: false
```

### 3. Network-Only Post

```markdown
# LinkedIn: Team Update

post_type: text
post_content: "Internal update for my network"
visibility: CONNECTIONS
approved: false
```

---

## Workflow Summary

```
You create .md → Drop in Inbox/ → file_watcher adds metadata
→ Moves to Needs_Action/ → You approve (approved:true)
→ linkedin_handler posts → Moves to Done/ → SUCCESS!
```

---

## Troubleshooting

### Post not appearing?

1. Check if file is still in `Needs_Action/` (forgot to approve?)
2. Check `Failed/` folder for errors
3. Verify both watchers are running
4. Test connection: `python linkedin_client.py`

### Error: "Token expired"

```bash
cd Gold/Integrations/linkedin
python get_linkedin_token.py
# Follow OAuth flow to refresh token
```

### File stuck in Needs_Action?

Make sure you added: `approved: true` (not `approved: false`)

---

## Next Steps

1. ✅ **Read full workflow:** [POSTING_WORKFLOW.md](./POSTING_WORKFLOW.md)
2. ✅ **Browse examples:** [examples/](./examples/)
3. ✅ **Set up automation:** Schedule posts in advance
4. ✅ **Monitor logs:** Check audit logs daily

---

## Key Reminders

- ✅ **Always require approval** for social posts (never auto-approve)
- ✅ **Keep watchers running** in background for continuous monitoring
- ✅ **Review content carefully** before approving (it's going live!)
- ✅ **Check Done/ and Failed/** folders to track results
- ✅ **Limit to 3-5 posts/day** (LinkedIn best practice)

---

**Happy posting! 🚀**

For detailed documentation, see [POSTING_WORKFLOW.md](./POSTING_WORKFLOW.md)
