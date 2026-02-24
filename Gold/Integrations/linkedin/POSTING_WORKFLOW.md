# LinkedIn Posting Workflow with Human Approval

**Version:** 1.0
**Date:** 2026-02-24
**Tier:** Gold/Platinum

---

## Overview

This workflow enables your AI agent to post to LinkedIn with **mandatory human approval**. Every post is reviewed before going live, ensuring quality control and brand safety.

### Flow Diagram

```
┌─────────────┐
│   Create    │  1. Create .md task file with LinkedIn post request
│  Task File  │     (Use examples as templates)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Inbox/    │  2. Drop file in Silver/Inbox/
└──────┬──────┘
       │
       ▼
┌─────────────┐
│file_watcher │  3. Auto-detects file, adds metadata
│    .py      │     Classifies as high-risk (social media)
└──────┬──────┘     Sets approval:required
       │
       ▼
┌─────────────┐
│Needs_Action/│  4. File moved here with metadata
└──────┬──────┘     Status: Awaiting approval
       │
       ▼
┌─────────────┐
│   HUMAN     │  5. You review the post content
│  REVIEWS    │     Check quality, accuracy, tone
└──────┬──────┘     Decision: Approve or reject
       │
       ├─── APPROVE ──────────────────────┐
       │                                   │
       │  Add line: approved:true          │
       │                                   ▼
       │                          ┌─────────────┐
       │                          │  linkedin_  │  6. Handler detects
       │                          │   post_     │     approval, executes
       │                          │ handler.py  │     LinkedIn API call
       │                          └──────┬──────┘
       │                                 │
       │                                 ▼
       │                          ┌─────────────┐
       │                          │  LinkedIn   │  7. Post goes live
       │                          │     API     │
       │                          └──────┬──────┘
       │                                 │
       │                                 ▼
       │                          ┌─────────────┐
       │                          │   Done/     │  8. Task moved to Done/
       │                          │  +Memory    │     Result logged
       │                          └─────────────┘
       │
       └─── REJECT ───────────────────────┐
                                          │
         Delete file or move to Failed/   │
                                          ▼
                                  ┌─────────────┐
                                  │   Failed/   │  No post created
                                  └─────────────┘
```

---

## Step-by-Step Guide

### Prerequisites

1. ✅ LinkedIn integration configured (`linkedin_config.json` exists)
2. ✅ Access token validated (run `python linkedin_client.py` to test)
3. ✅ File watcher running: `python Silver/Watchers/file_watcher.py`
4. ✅ LinkedIn post handler ready: `linkedin_post_handler.py`

---

### Step 1: Create Post Request

Use one of the example templates in `Gold/Integrations/linkedin/examples/`:

**Option A: Text Post**
```markdown
# LinkedIn: My Post Title

post_type: text
post_content: "Your post content here with hashtags #AI #Tech"
visibility: PUBLIC

approved: false
```

**Option B: Article Share**
```markdown
# LinkedIn: Share Article

post_type: article
article_url: https://example.com/article
post_content: "Your commentary about the article"
visibility: PUBLIC

approved: false
```

**Key Fields:**
- `post_type`: `text` or `article`
- `post_content`: Your post text (max 3000 chars for text, 1300 for article commentary)
- `article_url`: Required for article shares
- `visibility`: `PUBLIC` (everyone) or `CONNECTIONS` (network only)
- `approved`: Must be `false` initially

---

### Step 2: Submit for Processing

Drop your `.md` file in:
```
Silver/Inbox/
```

Example:
```bash
# Copy example to Inbox
cp Gold/Integrations/linkedin/examples/example_text_post.md Silver/Inbox/my_linkedin_post.md
```

---

### Step 3: Auto-Processing (file_watcher)

**What happens automatically:**

1. File watcher detects new file in `Inbox/`
2. Adds metadata:
   ```html
   <!-- AGENT METADATA
     received_at : 2026-02-24 14:30:00
     source      : file_watcher (internal)
     risk_level  : high
     approval    : required
     retries     : 0
   -->
   ```
3. Moves file to `Needs_Action/`

**Why high risk?**
Social media posts are auto-classified as high-risk because they're public-facing and can impact your brand.

---

### Step 4: Human Review & Approval

Navigate to:
```
Silver/Needs_Action/
```

Open your task file and review:

1. **Content Quality**
   - Is the text clear and error-free?
   - Are hashtags appropriate?
   - Is the tone professional?

2. **Factual Accuracy**
   - Are claims accurate?
   - Are links correct?
   - Is timing appropriate?

3. **Brand Safety**
   - Does it align with your personal brand?
   - Is it appropriate for your network?
   - Any controversial content?

**To Approve:**

Add this line anywhere in the file:
```
approved: true
```

Or update the existing line:
```
approved: false  →  approved: true
```

**To Reject:**

Either:
- Delete the file
- Move to `Silver/Failed/`
- Leave `approved: false` (handler will skip it)

---

### Step 5: Execute Post

**Option A: Manual Execution**

Run once to process all approved posts:
```bash
cd Gold/Integrations/linkedin
python linkedin_post_handler.py --once
```

**Option B: Watch Mode (Recommended)**

Continuously monitor for approved posts:
```bash
cd Gold/Integrations/linkedin
python linkedin_post_handler.py --watch
```

Leave this running in the background. It checks every 10 seconds.

---

### Step 6: Verify Execution

**Check Done/ folder:**
```
Silver/Done/my_linkedin_post.md
```

The file will include execution results:
```markdown
---
## Execution Result
**Timestamp:** 2026-02-24 14:35:12
**Status:** SUCCESS: ✓ Text post created successfully. Post ID: urn:li:share:123456789
```

**Check Memory:**
```
Silver/Memory/decisions.md
```

Includes:
```markdown
## my_linkedin_post.md
**Date:** 2026-02-24 14:35:12
**Result:** SUCCESS: ✓ Text post created successfully. Post ID: urn:li:share:123456789
```

**Check Audit Log:**
```
Gold/Audit_Logs/2026-02-24_audit.log
```

Includes:
```
[2026-02-24 14:35:12] [linkedin_post_handler] [posted: my_linkedin_post.md] [0ms]
[2026-02-24 14:35:12] [linkedin_client] [post_update] [post_id=urn:li:share:123456789] [1234ms]
```

**Check LinkedIn:**

Your post should be live on your LinkedIn profile!

---

## Common Use Cases

### 1. Daily Motivation Post

```markdown
# LinkedIn: Monday Motivation

post_type: text
post_content: "Start your week strong! 💪 #MondayMotivation"
visibility: PUBLIC
approved: false
```

### 2. Share Blog Article

```markdown
# LinkedIn: Share My Blog Post

post_type: article
article_url: https://myblog.com/ai-automation
post_content: "Just published my thoughts on AI automation in 2026"
visibility: PUBLIC
approved: false
```

### 3. Announce New Project

```markdown
# LinkedIn: Product Launch

post_type: text
post_content: "Excited to announce the launch of [Product]! 🚀

After 6 months of development, we're finally ready to share this with the world.

Check it out: https://myproduct.com

#ProductLaunch #AI #Innovation"
visibility: PUBLIC
approved: false
```

### 4. Share Industry News

```markdown
# LinkedIn: Industry Insight

post_type: article
article_url: https://news.com/ai-breakthrough
post_content: "This changes everything. The implications for our industry are massive.

What's your take? 👇"
visibility: CONNECTIONS
approved: false
```

---

## Automation Ideas

### Scheduled Posts

Create multiple posts in advance, approve in batch:

```bash
# Create posts for the week
Silver/Inbox/
├── monday_motivation.md        (approved: false)
├── tuesday_tech_tip.md         (approved: false)
├── wednesday_case_study.md     (approved: false)
├── thursday_thought.md         (approved: false)
└── friday_reflection.md        (approved: false)
```

Review all at once on Sunday, approve by adding `approved:true` to each.

Run handler in watch mode—posts execute automatically when approved.

---

### AI-Generated Posts

Have your AI agent draft posts based on:
- Recent blog articles
- Company updates
- Industry news
- Personal achievements

Agent creates `.md` files in Inbox with draft content.
You review and approve before posting.

**Example workflow:**
1. AI monitors your blog RSS feed
2. Detects new article published
3. Generates LinkedIn post draft
4. Saves to `Inbox/share_article_[title].md`
5. You review and approve
6. Handler posts to LinkedIn

---

### Cross-Platform Posting

Extend this workflow to other platforms:
- Twitter/X post handler
- Facebook post handler
- Instagram post handler

Same approval flow, different API integrations.

---

## Troubleshooting

### "Post not appearing on LinkedIn"

**Check:**
1. ✅ Is `approved:true` in the file?
2. ✅ Is handler running (`--watch` mode)?
3. ✅ Check `Done/` for success message
4. ✅ Check `Failed/` for error message
5. ✅ Verify LinkedIn access token is valid

**Test connection:**
```bash
cd Gold/Integrations/linkedin
python -c "from linkedin_client import validate_access_token; print(validate_access_token())"
```

---

### "Task moved to Failed/"

**Common errors:**

1. **"post_content is required"**
   - Fix: Add `post_content: "Your text"` to task file

2. **"Token expired"**
   - Fix: Run `python get_linkedin_token.py` to refresh

3. **"Post too long"**
   - Fix: Reduce text to under 3000 chars (text) or 1300 chars (article comment)

4. **"article_url is required"**
   - Fix: Add `article_url: https://...` for article posts

---

### "File stuck in Needs_Action/"

**Reasons:**
- `approved: false` (waiting for your approval)
- Handler not running (start with `--watch` mode)
- File doesn't match LinkedIn post pattern (missing `post_type` or `linkedin` keyword)

**Fix:**
1. Verify `approved: true` is in file
2. Start handler: `python linkedin_post_handler.py --watch`
3. Check logs for errors

---

### "Multiple posts at once"

If you approved several posts and they all execute:
- This is expected behavior
- Handler processes all approved tasks
- Posts are created in sequence
- Each gets logged separately

To control timing:
- Approve one at a time
- Use `--once` mode instead of `--watch`
- Delete unapproved files until you're ready

---

## Security Best Practices

### 1. Never Auto-Approve

Always require human approval for social media posts:
```python
# ❌ NEVER DO THIS
if is_linkedin_post_task(content):
    auto_approve()  # DANGEROUS!

# ✅ ALWAYS DO THIS
if is_linkedin_post_task(content):
    require_human_approval()
```

### 2. Content Review Checklist

Before approving any post, verify:
- [ ] No personal/sensitive information
- [ ] No confidential business data
- [ ] No inflammatory or controversial content
- [ ] Links are correct and safe
- [ ] Hashtags are appropriate
- [ ] Grammar and spelling are correct
- [ ] Tone matches your brand

### 3. Rate Limiting

LinkedIn soft limit: ~100 posts/day

Recommended max: 3-5 posts/day for personal profiles

Space out posts by at least 2-3 hours.

### 4. Access Token Security

**Protect your token:**
- ✅ Never commit `linkedin_config.json` to Git
- ✅ Restrict file permissions: `chmod 600 linkedin_config.json`
- ✅ Rotate token every 30 days
- ✅ Monitor audit logs for suspicious activity

**Token in `.gitignore`:**
```gitignore
# LinkedIn credentials
Gold/Integrations/linkedin/linkedin_config.json
**/linkedin_config.json
```

### 5. Audit Everything

Every action is logged to:
```
Gold/Audit_Logs/YYYY-MM-DD_audit.log
```

Review logs weekly to detect:
- Unauthorized posting attempts
- Failed authentication
- Unusual activity patterns

---

## Performance & Monitoring

### Metrics to Track

**In Memory/decisions.md:**
- Total posts created
- Success vs. failure rate
- Average approval time

**In Audit Logs:**
- API response times
- Error frequency
- Token expiration events

### Optimization Tips

1. **Batch Approval**
   - Review multiple posts at once
   - Approve in batch on Sundays

2. **Template Library**
   - Create reusable post templates
   - Saves time on formatting

3. **Content Calendar**
   - Plan posts 1-2 weeks ahead
   - Pre-create task files
   - Approve in batches

---

## Advanced Configuration

### Custom Visibility Rules

Edit `linkedin_post_handler.py` to add custom logic:

```python
def determine_visibility(content: str) -> str:
    """Auto-determine visibility based on content."""
    if "hiring" in content.lower() or "job" in content.lower():
        return "PUBLIC"  # Job posts should be public
    elif "team" in content.lower():
        return "CONNECTIONS"  # Team updates for network only
    else:
        return "PUBLIC"  # Default
```

### Post Scheduling

Add scheduling metadata:

```markdown
post_type: text
post_content: "My scheduled post"
visibility: PUBLIC
schedule_time: 2026-02-25 09:00:00
approved: true
```

Update handler to respect `schedule_time` field.

---

## Integration with Other Tools

### CEO Briefing

Add LinkedIn stats to weekly briefing:

```markdown
## LinkedIn Activity This Week
- Posts created: 5
- Engagement: [requires Analytics API]
- Top performing post: [link]
```

### Odoo Integration

Log successful posts to Odoo for marketing tracking:

```python
from odoo_client import create_record

def log_to_odoo(post_id, content):
    create_record('marketing.post', {
        'name': f'LinkedIn Post {post_id}',
        'content': content,
        'platform': 'linkedin',
        'date': datetime.now()
    })
```

---

## Next Steps

1. ✅ **Test the workflow** with an example post
2. ✅ **Set up watch mode** for continuous monitoring
3. ✅ **Create post templates** for common use cases
4. ✅ **Build content calendar** for the week/month
5. ✅ **Monitor audit logs** daily for issues
6. ✅ **Refine approval process** based on usage

---

## Resources

- [LinkedIn Client Documentation](./README.md)
- [LinkedIn API Docs](https://learn.microsoft.com/en-us/linkedin/)
- [Example Posts](./examples/)
- [File Watcher Setup](../../Silver/Watchers/SETUP_GUIDE.md)

---

**Status:** ✅ Production Ready
**Last Updated:** 2026-02-24
**Maintainer:** AI Agent Team
