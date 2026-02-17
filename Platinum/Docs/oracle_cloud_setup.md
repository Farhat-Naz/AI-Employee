# Oracle Cloud Free Tier — Setup Guide

## Goal

Set up a free 24/7 Ubuntu VM on Oracle Cloud to run the Platinum Cloud agents.

---

## Step 1: Create Oracle Account

1. Go to https://cloud.oracle.com
2. Click **Start for Free**
3. Sign up with your email (credit card required for verification — not charged)
4. Choose your **Home Region** (pick closest to you — cannot change later)
   - Recommended: `ap-mumbai-1` (Mumbai) for Pakistan users

---

## Step 2: Create Free VM Instance

1. Login → **Compute** → **Instances** → **Create Instance**

2. **Name:** `platinum-ai-employee`

3. **Image:** Ubuntu 22.04 (Canonical)

4. **Shape:** Click **Change Shape**
   - Select: **Ampere** (ARM) → **VM.Standard.A1.Flex**
   - OCPUs: **1** (free tier allows up to 4 total)
   - RAM: **6 GB** (free tier allows up to 24 GB total)

5. **Networking:**
   - Create new VCN (default settings OK)
   - Subnet: public subnet
   - Public IP: **Assign automatically**

6. **SSH Keys:**
   - Generate keypair → download `ssh-key-XXXX.key`
   - Keep this file — it's your only access to the VM

7. Click **Create**

8. Wait ~2 minutes → Status: **Running**

9. Copy the **Public IP Address**

---

## Step 3: Connect to VM

```bash
# On your local machine (Windows: use Git Bash or WSL)
chmod 400 ~/Downloads/ssh-key-XXXX.key
ssh -i ~/Downloads/ssh-key-XXXX.key ubuntu@<YOUR_VM_IP>
```

---

## Step 4: Open Firewall (Security List)

By default, only port 22 (SSH) is open.

1. Oracle Console → **Networking** → **Virtual Cloud Networks**
2. Click your VCN → **Security Lists** → **Default Security List**
3. Add Ingress Rules if needed (for health check endpoints etc.)
   - For now: no extra ports needed — agents work outbound only

---

## Step 5: Run Setup Script

```bash
# On the Oracle VM:
cd /home/ubuntu

# Clone vault
git clone https://github.com/Farhat-Naz/AI-Employee.git AI_Employee_Vault
cd AI_Employee_Vault

# Copy your .env (see Platinum/.env.example — fill in secrets first)
# From local machine:
# scp -i ~/ssh-key.key .env ubuntu@<VM_IP>:/home/ubuntu/AI_Employee_Vault/.env

# Run setup
chmod +x Platinum/setup_cloud.sh
./Platinum/setup_cloud.sh
```

---

## Step 6: Set Up Gmail API (for gmail_watcher)

1. Go to https://console.cloud.google.com
2. Create new project → **AI Employee**
3. Enable **Gmail API**: APIs & Services → Enable APIs → search Gmail API
4. Create credentials:
   - APIs & Services → Credentials → Create Credentials → **OAuth 2.0 Client ID**
   - Application type: **Desktop App**
   - Download → `credentials.json`
5. Copy to VM:
   ```bash
   scp -i ssh-key.key credentials.json ubuntu@<VM_IP>:/home/ubuntu/AI_Employee_Vault/Platinum/Cloud/credentials.json
   ```
6. First-time OAuth (on VM with port forwarding):
   ```bash
   # From local machine — forward port 8080 from VM
   ssh -i ssh-key.key -L 8080:localhost:8080 ubuntu@<VM_IP>

   # On VM
   cd /home/ubuntu/AI_Employee_Vault
   source /home/ubuntu/venv/bin/activate
   python Platinum/Cloud/Watchers/gmail_watcher.py
   # Opens browser on your local machine via port forward
   # Authorize → token.json saved on VM
   ```

---

## Step 7: Configure .env

```bash
nano /home/ubuntu/AI_Employee_Vault/.env
```

Fill in from `.env.example`:
```
WA_INSTANCE_ID=7103518775
WA_API_TOKEN=bbaa819148a54e3abd37d96f69fe9172459d4c45038046f3ba
WA_ALERT_NUMBER=923142062716
GIT_AUTHOR_NAME=Platinum Cloud
GIT_AUTHOR_EMAIL=cloud@ai-employee.local
```

---

## Step 8: Start Services

```bash
# Restart orchestrator to pick up .env
sudo systemctl restart orchestrator.service

# Check status
sudo systemctl status orchestrator.service

# Live logs
journalctl -u orchestrator.service -f
```

---

## Monitoring

```bash
# All platinum logs
tail -f /home/ubuntu/AI_Employee_Vault/Platinum/Logs/orchestrator.log

# Per-service
journalctl -u gmail-watcher.service -f
journalctl -u health-monitor.service -f

# Health check (manual)
cd /home/ubuntu/AI_Employee_Vault
source /home/ubuntu/venv/bin/activate
python Platinum/Cloud/health_monitor.py
```

---

## Keeping VM Updated

```bash
# Update vault from GitHub (sync_agent does this automatically)
git -C /home/ubuntu/AI_Employee_Vault pull origin main

# Update system packages (monthly)
sudo apt-get update && sudo apt-get upgrade -y
```

---

## Cost

Oracle Free Tier (Always Free):
- 2 AMD x86 micro instances OR
- Up to 4 Ampere ARM OCPUs + 24 GB RAM (shared)
- 2 Block Volumes (200 GB total)
- 10 GB Object Storage

**Our setup uses: 1 OCPU + 6 GB RAM = completely free**
