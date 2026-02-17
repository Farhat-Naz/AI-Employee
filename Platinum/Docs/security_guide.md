# Platinum Tier — Security Guide

## Golden Rule

**Secrets never go to GitHub. Ever.**

---

## What Is a Secret?

| File/Value | Classification | Where to Store |
|-----------|---------------|----------------|
| `.env` | SECRET | Local PC + Cloud VM only |
| `credentials.json` (Gmail OAuth) | SECRET | Cloud VM only |
| `token.json` (Gmail OAuth) | SECRET | Cloud VM only |
| `whatsapp_config.json` | SECRET | Local PC only (Silver shared) |
| `*.pem` / `*.key` (SSH) | SECRET | Your machine only |
| API keys / tokens | SECRET | `.env` only |
| Banking credentials | SECRET | NEVER digital — paper only |
| Task content (Markdown) | OK to sync | GitHub (private repo) |
| Python code | OK to sync | GitHub |
| Dashboard.md | OK to sync | GitHub |
| Audit logs | OK to sync | GitHub |

---

## .gitignore — Required Entries

Check that your vault root `.gitignore` contains ALL of these:

```gitignore
# Secrets — NEVER COMMIT
.env
*.env
.env.*
credentials.json
token.json
whatsapp_config.json
client_secret*.json
*.pem
*.key
*.token
banking_creds/
payment_creds/

# WhatsApp session
Local/MCP/wa_session/
*.session

# Google OAuth
Cloud/credentials.json
Cloud/token.json

# Python cache
__pycache__/
*.pyc
*.pyo
.venv/
venv/

# Obsidian workspace (local only)
.obsidian/workspace.json
.obsidian/workspace-mobile.json
```

---

## .env File Template

See `Platinum/.env.example` for the full template.

Never commit `.env`. Copy it manually to each machine:

```bash
# Local PC
C:\Users\aasif\Documents\AI_Employee_Vault\.env

# Oracle VM
/home/ubuntu/AI_Employee_Vault/.env
```

---

## SSH Security (Oracle VM)

1. Use key-based auth only — password auth disabled by default on Oracle
2. Keep your `.key` file private (chmod 400)
3. Never share your SSH private key
4. Use a passphrase on the SSH key for extra safety
5. Consider fail2ban (auto-installed on Ubuntu 22.04):
   ```bash
   sudo apt install fail2ban
   sudo systemctl enable fail2ban
   ```

---

## API Token Security

### Green API (WhatsApp)
- Token in `whatsapp_config.json` — excluded from git
- If token leaks: regenerate at green-api.com immediately
- Restrict `allowed_numbers` in config to trusted numbers only

### Gmail OAuth
- `credentials.json` + `token.json` on Cloud VM only
- If token is compromised: revoke at myaccount.google.com/security

### Future: Facebook / Twitter / LinkedIn
- Store in `.env` only — never hardcode in Python files
- Use read-only scopes where possible during testing
- Use page tokens (not personal account tokens)

---

## GitHub Repo Security

1. Keep repo **Private** (currently: https://github.com/Farhat-Naz/AI-Employee)
2. Use **branch protection** on main if collaborating
3. Enable **GitHub secret scanning** (Settings > Security > Secret scanning)
4. Regularly audit `.gitignore` when adding new integrations

### Check for accidental commits
```bash
# Scan git history for potential secrets
git log --all --full-diff -p | grep -i "password\|token\|secret\|api_key" | head -50
```

If found, secrets in history must be rotated immediately and history cleaned with:
```bash
# Nuclear option — rewrite history
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch PATH_TO_SECRET_FILE' \
  --prune-empty --tag-name-filter cat -- --all
```

---

## Data Classification

| Data Type | Risk | Action |
|-----------|------|--------|
| Customer names / emails | Medium | OK in tasks — don't over-retain |
| Phone numbers | Medium | Remove from Done/ after 30 days |
| Payment/billing info | HIGH | NEVER store in vault — route to NEEDS_HUMAN |
| Medical/legal documents | HIGH | NEVER in cloud — local only, encrypted |
| Login credentials | CRITICAL | NEVER in vault — use credential manager |

---

## Incident Response

If credentials are exposed to GitHub:

1. **Immediately** revoke/regenerate the exposed credential
2. Check GitHub repo for the commit: `git log --all -S "exposed_string"`
3. Delete the file from git history (filter-branch or BFG Repo Cleaner)
4. Force push cleaned history to GitHub
5. Audit who had access to the repo during exposure window
6. Log the incident in `Memory/decisions.md`
