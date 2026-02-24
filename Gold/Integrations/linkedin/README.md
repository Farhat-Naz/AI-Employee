# LinkedIn Integration — Gold/Platinum Tier

**Version:** 1.0
**Date:** 2026-02-24

---

## Overview

The LinkedIn integration allows your AI agent to:
- ✅ Post text updates to LinkedIn
- ✅ Share articles with commentary
- ✅ Fetch engagement summaries (with limitations)
- ✅ Validate access tokens
- ✅ Full audit logging

**API:** LinkedIn API v2
**Authentication:** OAuth 2.0
**Scope:** Personal profile posting

---

## Setup Guide

### Step 1: Create LinkedIn App

1. Go to [LinkedIn Developers](https://developers.linkedin.com)
2. Click **"Create app"**
3. Fill in basic information:
   - **App name:** Your AI Agent
   - **LinkedIn Page:** Associate with your personal profile or company page
   - **App logo:** Upload a logo (optional but recommended)
   - **Legal agreement:** Accept terms

### Step 2: Add Required Products

Your app needs these products:

1. **Sign In with LinkedIn using OpenID Connect**
   - Click "Request access" for this product
   - Usually auto-approved

2. **Share on LinkedIn**
   - Click "Request access" for this product
   - Requires verification (may take 24-48 hours)
   - You'll need to explain your use case

### Step 3: Configure OAuth Settings

1. Go to **"Auth"** tab in your app
2. Under **"OAuth 2.0 settings"**:
   - Add **Redirect URL:** `http://localhost:8000/callback`
   - Copy your **Client ID**
   - Copy your **Client Secret**

3. Under **"OAuth 2.0 scopes"**, ensure these are enabled:
   - `openid` (read basic profile)
   - `profile` (read full profile)
   - `w_member_social` (create, modify, delete posts)
   - `email` (read email address)

### Step 4: Generate Access Token

Run the OAuth helper script:

```bash
cd Gold/Integrations/linkedin
python get_linkedin_token.py
```

Follow the prompts:
1. Enter your **Client ID**
2. Enter your **Client Secret**
3. Enter **Redirect URI** (or press Enter for default)
4. Browser will open → authorize the app
5. Script will automatically capture the token

This creates `linkedin_config.json` with your credentials.

### Step 5: Test Connection

```bash
python linkedin_client.py
```

Or test in Python:

```python
from linkedin_client import validate_access_token, post_update

# Test connection
if validate_access_token():
    print("✓ LinkedIn connected!")

    # Post a test update (requires approval in production)
    result = post_update("Hello from my AI agent! 🤖")
    print(f"Posted: {result}")
```

---

## Usage Examples

### Post a Text Update

```python
from linkedin_client import post_update

result = post_update(
    text="Just shipped a new feature! 🚀 #coding #AI",
    visibility="PUBLIC"  # or "CONNECTIONS"
)
print(f"Post ID: {result['id']}")
```

**Character limit:** 3000 characters

### Share an Article

```python
from linkedin_client import post_article_share

result = post_article_share(
    article_url="https://example.com/blog/my-article",
    comment="Check out this great article about AI automation!"
)
print(f"Post ID: {result['id']}")
```

**Comment limit:** 1300 characters

### Get User Profile

```python
from linkedin_client import get_user_profile

profile = get_user_profile()
print(f"Name: {profile['localizedFirstName']} {profile['localizedLastName']}")
print(f"ID: {profile['id']}")
```

### Get Engagement Summary

```python
from linkedin_client import get_engagement_summary

summary = get_engagement_summary(days=7)
print(f"Posts last 7 days: {summary['post_count']}")
print(f"Note: {summary['note']}")
```

**Note:** LinkedIn's free API has limited analytics access. For comprehensive metrics, you need LinkedIn Marketing API or Analytics Finder API.

---

## Configuration File

`linkedin_config.json` structure:

```json
{
  "access_token": "AQV...(long token)...xyz",
  "client_id": "86xxxxxxxxxxxxx",
  "client_secret": "Wm7xxxxxxxxxxxxx",
  "redirect_uri": "http://localhost:8000/callback",
  "api_version": "v2",
  "expires_in": 5184000,
  "note": "Token expires after specified time. Re-run get_linkedin_token.py to refresh."
}
```

**⚠️ NEVER commit this file to Git!**

---

## Access Token Expiration

LinkedIn access tokens expire after **60 days** (5,184,000 seconds).

When expired, you'll get:
```
401 Unauthorized: The token used in the request has expired
```

**Solution:** Re-run the OAuth helper:
```bash
python get_linkedin_token.py
```

---

## API Limitations

### Free API Limitations:
- ✅ Post updates (personal profile)
- ✅ Share articles
- ✅ Basic profile info
- ❌ Limited analytics (requires Marketing API)
- ❌ No post scheduling
- ❌ No company page posting (requires separate permissions)

### Rate Limits:
- **Posting:** ~100 posts per day (soft limit)
- **API calls:** Throttled per app (varies)
- If exceeded: `429 Too Many Requests`

---

## Guardrails & Approval Flow

In production, all LinkedIn posts require approval:

```python
# Pseudo-code for agent flow
def agent_post_to_linkedin(content):
    # 1. Agent drafts post
    draft = {
        "text": content,
        "platform": "linkedin",
        "action": "post_update"
    }

    # 2. Request approval
    approval_file = f"Platinum/Vault/Pending_Approval/linkedin_post_{timestamp}.json"
    save_approval_request(approval_file, draft)

    # 3. Wait for human approval
    if wait_for_approval(approval_file):
        # 4. Execute post
        result = post_update(content)
        log_audit("linkedin_post", "approved_and_posted", result['id'])
    else:
        log_audit("linkedin_post", "rejected", "")
```

---

## Audit Logging

All actions are logged to `Gold/Audit_Logs/YYYY-MM-DD_audit.log`:

```
[2026-02-24 14:32:15] [linkedin_client] [post_update] [post_id=urn:li:share:123456] [1234ms]
[2026-02-24 14:35:22] [linkedin_client] [get_user_profile] [user_id=abc123] [456ms]
[2026-02-24 14:40:01] [linkedin_client] [get_engagement_summary] [7 posts analyzed] [2341ms]
```

---

## Troubleshooting

### Error: "The token used in the request has expired"
**Solution:** Run `python get_linkedin_token.py` to refresh token

### Error: "Insufficient permissions for this operation"
**Solution:** Verify "Share on LinkedIn" product is approved in your app

### Error: "Invalid redirect URI"
**Solution:** Ensure `http://localhost:8000/callback` is added in app settings

### Posts not appearing?
- Check if post is visible on your profile (may be privacy settings)
- LinkedIn may shadow-ban automated posts if detected as spam
- Ensure you're not hitting rate limits (max ~100/day)

### Analytics not working?
- Free API has limited analytics
- Consider upgrading to LinkedIn Marketing API for full metrics
- Current implementation provides basic post count only

---

## Integration Checklist

- [ ] LinkedIn app created at developers.linkedin.com
- [ ] "Share on LinkedIn" product approved
- [ ] OAuth credentials obtained (Client ID + Secret)
- [ ] `get_linkedin_token.py` executed successfully
- [ ] `linkedin_config.json` created and populated
- [ ] Test post successful: `post_update("Test")`
- [ ] Access token validated: `validate_access_token()`
- [ ] Added to `.gitignore`: `linkedin_config.json`
- [ ] Approval flow configured (for production use)
- [ ] Audit logging verified

---

## Security Notes

1. **Never commit** `linkedin_config.json` to version control
2. **Restrict access** to config file (contains sensitive tokens)
3. **Rotate tokens** regularly (every 30-60 days)
4. **Monitor usage** via audit logs
5. **Require approval** for all posts in production
6. **Rate limit** posting (max 10-20 per day recommended)

---

## Next Steps

1. ✅ LinkedIn integration complete
2. Add LinkedIn to MCP server (optional)
3. Integrate with CEO Briefing reports
4. Set up scheduled posting workflow
5. Monitor engagement metrics
6. Test approval flow end-to-end

---

## Resources

- [LinkedIn API Documentation](https://learn.microsoft.com/en-us/linkedin/)
- [Share on LinkedIn API](https://learn.microsoft.com/en-us/linkedin/consumer/integrations/self-serve/share-on-linkedin)
- [OAuth 2.0 Flow](https://learn.microsoft.com/en-us/linkedin/shared/authentication/authentication)
- [API Rate Limits](https://learn.microsoft.com/en-us/linkedin/shared/api-guide/concepts/rate-limits)

---

**Status:** ✅ Ready for Gold/Platinum Tier
**Tested:** 2026-02-24
**Maintainer:** AI Agent Team
