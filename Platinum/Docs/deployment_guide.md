# Platinum Tier — Deployment Guide

## Prerequisites

- Oracle Cloud VM running (see oracle_cloud_setup.md)
- GitHub repo: https://github.com/Farhat-Naz/AI-Employee
- Local PC: Python 3.10+, Git installed
- WhatsApp Green API instance (already working from Silver)

---

## Architecture Summary

```
Local PC (Windows)          GitHub             Oracle Cloud VM
     |                         |                      |
     |-- git push -------->    |<-- git pull ---------|
     |                         |                      |
     |-- approval_agent.py     |    orchestrator.py   |
     |-- watchdog.py           |    gmail_watcher.py  |
     |-- whatsapp_watcher.py   |    file_watcher.py   |
     |-- filesystem_watcher.py |    email_drafter.py  |
                               |    sync_agent.py     |
                               |    health_monitor.py |
```

---

## Local Setup (Windows PC)

### 1. Install requirements
```bash
cd C:\Users\aasif\Documents\AI_Employee_Vault
pip install -r Platinum/requirements_local.txt
```

### 2. Start Local watchdog
```bash
python Platinum/Local/watchdog.py
```

This starts:
- `whatsapp_watcher.py` (Green API)
- `filesystem_watcher.py` (~/Desktop/AI_Drop/)
- Signal merge loop (Signals/ -> Dashboard.md)

### 3. Run approval agent (when prompted)
```bash
python Platinum/Local/approval_agent.py
```
Or just check `Platinum/Pending_Approval/cloud/` in Obsidian.

---

## Cloud Setup (Oracle VM)

### First-time setup
```bash
ssh ubuntu@<VM_IP>
cd /home/ubuntu/AI_Employee_Vault
./Platinum/setup_cloud.sh
```

### Everyday operations

```bash
# Check all services running
sudo systemctl status orchestrator.service

# View live logs
journalctl -u orchestrator.service -f

# Manual sync (if sync_agent missed)
cd /home/ubuntu/AI_Employee_Vault
source /home/ubuntu/venv/bin/activate
python Platinum/Cloud/sync_agent.py

# Manual health check
python Platinum/Cloud/health_monitor.py
```

---

## Sync Flow

### Cloud -> Local (automatic, every 5 min)
```
Cloud creates draft in Pending_Approval/cloud/
  -> sync_agent git push
  -> Local git pull (manual or auto)
  -> watchdog sees Signals/ -> Dashboard updated
  -> Human sees badge in Obsidian
```

### Local -> Cloud (after approval)
```
Human approves via approval_agent.py
  -> Done/ file created locally
  -> git push
  -> Cloud sync_agent git pull
  -> Cloud sees task completed
```

### Manual sync (both sides)
```bash
# Local
git -C "C:\Users\aasif\Documents\AI_Employee_Vault" pull origin main
git -C "C:\Users\aasif\Documents\AI_Employee_Vault" push origin main

# Cloud
git -C /home/ubuntu/AI_Employee_Vault pull origin main
```

---

## Updating Code

### Deploy new code to Cloud
```bash
# On Local — edit code, commit, push
git add Platinum/
git commit -m "update: description"
git push origin main

# Cloud picks it up automatically via sync_agent
# Or manually:
ssh ubuntu@<VM_IP>
git -C /home/ubuntu/AI_Employee_Vault pull origin main
sudo systemctl restart orchestrator.service
```

---

## Troubleshooting

### gmail_watcher not working
```bash
# Check logs
journalctl -u gmail-watcher.service -20

# Re-authorize OAuth (if token expired)
systemctl stop gmail-watcher.service
source /home/ubuntu/venv/bin/activate
python Platinum/Cloud/Watchers/gmail_watcher.py
# Authorize in browser -> token.json refreshed
systemctl start gmail-watcher.service
```

### sync_agent push failing
```bash
# Check git status
git -C /home/ubuntu/AI_Employee_Vault status

# Reset if stuck
git -C /home/ubuntu/AI_Employee_Vault fetch origin
git -C /home/ubuntu/AI_Employee_Vault reset --hard origin/main
```

### WhatsApp not receiving
```bash
# Check Green API settings
# Must have: incomingWebhook: "yes"
# Use setSettings API to fix (see Silver WHATSAPP_SETUP.md)
```

### Disk full
```bash
df -h /home/ubuntu/AI_Employee_Vault
# Clean old logs
find /home/ubuntu/AI_Employee_Vault/Platinum/Logs -name "*.log" -mtime +30 -delete
```

---

## Daily Checklist

- [ ] Obsidian open — check Dashboard.md
- [ ] Any pending in `Pending_Approval/cloud/`?
- [ ] Any failed tasks in `Failed/`?
- [ ] WhatsApp watcher running?
- [ ] Cloud health: `journalctl -u orchestrator.service -n 20`
