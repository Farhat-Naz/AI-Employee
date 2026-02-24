# Company Handbook — Gold Tier

**Version:** 3.0 (Gold)
**Date:** 2026-02-10
**Extends:** Bronze + Silver handbooks

---

## 1. Gold Tier Purpose

Gold Tier agent is an **Autonomous Employee**:
- Works across Personal and Business domains
- Integrates with Odoo (accounting), Facebook, Instagram, Twitter
- Generates weekly CEO briefings
- Completes multi-step tasks without human intervention (Ralph Wiggum Loop)

---

## 2. All Bronze + Silver Rules Apply

Do not repeat them here. Refer to:
- `Bronze/Company_Handbook.md`
- `Silver/Company_Handbook.md`

---

## 3. Integration Setup Checklist

### Odoo 19+
- [ ] Install Odoo Community locally (port 8069)
- [ ] Create database
- [ ] Enable API Key: Settings > Technical > API Keys
- [ ] Fill `MCP_Servers/odoo/odoo_config.json`
- [ ] Test: `python MCP_Servers/odoo/odoo_mcp_server.py`

### Facebook / Instagram
- [ ] Create Facebook Developer App (developers.facebook.com)
- [ ] Add Facebook Login + Instagram Graph API products
- [ ] Generate long-lived Page Access Token
- [ ] Fill `Integrations/facebook_instagram/fb_ig_config.json`
- [ ] Test: `python Integrations/facebook_instagram/fb_ig_client.py`

### Twitter / X
- [ ] Create Twitter Developer account (developer.twitter.com)
- [ ] Create Project + App
- [ ] Enable Read + Write permissions
- [ ] Generate all 4 keys + Bearer Token
- [ ] Fill `Integrations/twitter/twitter_config.json`
- [ ] Test: `python Integrations/twitter/twitter_client.py`

### LinkedIn
- [ ] Create LinkedIn app (developers.linkedin.com)
- [ ] Request "Share on LinkedIn" product access
- [ ] Add OAuth redirect: http://localhost:8000/callback
- [ ] Run: `python Integrations/linkedin/get_linkedin_token.py`
- [ ] Follow OAuth flow to generate access token
- [ ] Test: `python Integrations/linkedin/linkedin_client.py`

---

## 4. Ralph Wiggum Loop Rules

- Max **10 iterations** per task
- Every iteration must be logged to `Audit_Logs/`
- On iteration 10 with no completion → mark `NEEDS_HUMAN`
- Replanning allowed (agent may revise its own plan mid-loop)

---

## 5. Audit Logging Rules

- **Every** skill execution must write to `Audit_Logs/YYYY-MM-DD_audit.log`
- Format: `[timestamp] [skill] [action] [result] [duration_ms]`
- Logs are **never deleted**
- Weekly log summary included in CEO Briefing

---

## 6. CEO Briefing Rules

- Generated every **Monday 09:00** or on-demand
- Saved to: `Reports/CEO_Briefings/YYYY-WXX_ceo_briefing.md`
- Must include: Business ops, Accounting snapshot, Social performance, Pending decisions, Recommendations
- Requires at least Odoo OR Social integration to be active

---

## 7. Social Media Guardrails

| Platform  | Post | Read | Approval Required |
|-----------|------|------|-------------------|
| Facebook  | Yes  | Yes  | Always            |
| Instagram | Yes  | Yes  | Always            |
| Twitter/X | Yes  | Yes  | Always            |
| LinkedIn  | Yes  | Yes  | Always            |

---

## 8. Odoo Guardrails

| Action | Approval Required |
|--------|-------------------|
| Read data (invoices, partners) | No |
| Create draft invoice | Yes |
| Post (confirm) invoice | Yes |
| Journal entry | Yes |
| Delete any record | Never — escalate to human |

---

## 9. Config Files — Never Commit

These files contain secrets. Never share or commit:
- `MCP_Servers/odoo/odoo_config.json`
- `Integrations/facebook_instagram/fb_ig_config.json`
- `Integrations/twitter/twitter_config.json`
- `Integrations/linkedin/linkedin_config.json`
- `Silver/Watchers/credentials.json`
- `Silver/Watchers/token.json`

---

## 10. Promotion to Platinum

Gold → Platinum when:
- All social integrations (Facebook + Instagram + Twitter + LinkedIn) active and tested
- Odoo integration working
- 4+ weeks of stable autonomous operation
- At least 4 CEO Briefings generated
- Zero unrecovered failures in last 2 weeks
