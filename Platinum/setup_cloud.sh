#!/bin/bash
# setup_cloud.sh — Oracle Free VM Bootstrap (Platinum Tier)
# ----------------------------------------------------------
# Run once on a fresh Oracle Cloud Ubuntu 22.04 VM.
# Sets up Python env, clones/updates vault, enables systemd services.
#
# Usage:
#   chmod +x setup_cloud.sh
#   ./setup_cloud.sh
#
# Prerequisites:
#   - Ubuntu 22.04 (Oracle Free Tier ARM or x86)
#   - SSH access as ubuntu user
#   - GitHub repo URL ready
#   - .env file ready (copy manually — never commit)

set -e

VAULT_DIR="/home/ubuntu/AI_Employee_Vault"
GITHUB_REPO="${GITHUB_REPO:-https://github.com/Farhat-Naz/AI-Employee.git}"
VENV_DIR="/home/ubuntu/venv"

echo "=============================================="
echo " Platinum Tier Cloud Setup"
echo " Vault: $VAULT_DIR"
echo " Repo:  $GITHUB_REPO"
echo "=============================================="

# ── 1. System packages ────────────────────────────────────────────────────────
echo ""
echo "[1/7] Installing system packages..."
sudo apt-get update -qq
sudo apt-get install -y -qq \
    python3 python3-pip python3-venv \
    git curl wget \
    build-essential libssl-dev

# ── 2. Python virtualenv ──────────────────────────────────────────────────────
echo ""
echo "[2/7] Creating Python virtualenv at $VENV_DIR..."
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

pip install --upgrade pip -q

# ── 3. Clone / pull vault ─────────────────────────────────────────────────────
echo ""
echo "[3/7] Cloning / updating vault from GitHub..."
if [ -d "$VAULT_DIR/.git" ]; then
    echo "  Repo exists — pulling latest..."
    git -C "$VAULT_DIR" pull --rebase origin main
else
    echo "  Cloning repo..."
    git clone "$GITHUB_REPO" "$VAULT_DIR"
fi

cd "$VAULT_DIR"

# ── 4. Copy .env (manual step) ────────────────────────────────────────────────
echo ""
echo "[4/7] Checking .env..."
if [ ! -f "$VAULT_DIR/.env" ]; then
    echo "  WARNING: .env not found!"
    echo "  Create it from Platinum/.env.example and fill in secrets:"
    echo "    cp Platinum/.env.example .env"
    echo "    nano .env"
    echo ""
    echo "  Then re-run this script or enable services manually."
fi

# ── 5. Install Python dependencies ────────────────────────────────────────────
echo ""
echo "[5/7] Installing Python dependencies..."
if [ -f "$VAULT_DIR/Platinum/requirements_cloud.txt" ]; then
    pip install -r "$VAULT_DIR/Platinum/requirements_cloud.txt" -q
else
    # Fallback: install known deps
    pip install \
        google-auth-oauthlib \
        google-auth-httplib2 \
        google-api-python-client \
        requests -q
fi
echo "  Done."

# ── 6. Install systemd services ───────────────────────────────────────────────
echo ""
echo "[6/7] Installing systemd services..."
SERVICES_DIR="$VAULT_DIR/Platinum/Cloud/Services"

for service_file in "$SERVICES_DIR"/*.service; do
    service_name=$(basename "$service_file")
    echo "  Installing $service_name..."
    sudo cp "$service_file" "/etc/systemd/system/$service_name"
done

sudo systemctl daemon-reload

# Enable and start orchestrator (it manages others)
if [ -f "/etc/systemd/system/orchestrator.service" ]; then
    sudo systemctl enable orchestrator.service
    sudo systemctl start orchestrator.service
    echo "  Orchestrator enabled and started."
else
    echo "  WARNING: orchestrator.service not found — enabling individual services..."
    for service_file in "$SERVICES_DIR"/*.service; do
        service_name=$(basename "$service_file")
        sudo systemctl enable "$service_name"
        sudo systemctl start "$service_name"
    done
fi

# ── 7. Verify ─────────────────────────────────────────────────────────────────
echo ""
echo "[7/7] Status check..."
echo ""
sudo systemctl status orchestrator.service --no-pager -l || true
echo ""
echo "=============================================="
echo " Platinum Cloud Setup Complete!"
echo "=============================================="
echo ""
echo "Useful commands:"
echo "  journalctl -u orchestrator.service -f    # live logs"
echo "  journalctl -u gmail-watcher.service -f"
echo "  systemctl status platinum-*.service"
echo "  systemctl restart orchestrator.service"
echo ""
echo "IMPORTANT: If .env was missing, add it now:"
echo "  nano $VAULT_DIR/.env"
echo "  sudo systemctl restart orchestrator.service"
