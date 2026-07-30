#!/bin/bash
# VPS 1-Line Restore Script
# Usage: bash restore.sh <path_to_backup.tar.gz>

set -e

BACKUP_FILE="$1"

if [ -z "$BACKUP_FILE" ]; then
    # Look for any vps_backup tarball in current directory or /tmp
    BACKUP_FILE=$(find . /tmp /root -name "vps_backup_*.tar.gz" 2>/dev/null | head -n 1)
fi

if [ -z "$BACKUP_FILE" ] || [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Error: Backup file not found!"
    echo "Usage: bash restore.sh <path_to_vps_backup.tar.gz>"
    exit 1
fi

echo "🚀 Starting 1-Line VPS Restore from: $BACKUP_FILE"

# 1. Install Essential Dependencies
echo "📦 Installing system dependencies (Python3, Node.js, Git, Curl)..."
apt-get update -qq
apt-get install -y -qq python3 python3-pip python3-venv git curl tar

if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y -qq nodejs
fi

if ! command -v wrangler &> /dev/null; then
    npm install -g wrangler &> /dev/null || true
fi

# 2. Extract Backup Archive to /root
echo "📂 Restoring files and configurations..."
tar -xzf "$BACKUP_FILE" -C /root

# 3. Restore Permissions & Executables
chmod +x /root/telegram_bot.py /root/backup_vps.sh /root/restore.sh 2>/dev/null || true
chmod +x /root/.local/bin/agy 2>/dev/null || true

# 4. Setup Systemd Service
if [ -f "/etc/systemd/system/antigravity-bot.service" ]; then
    echo "⚙️ Configuring systemd service..."
    systemctl daemon-reload
    systemctl enable antigravity-bot.service
    systemctl restart antigravity-bot.service
fi

# 5. Environment & Bashrc Refresh
echo 'alias agy="agy --dangerously-skip-permissions"' >> /root/.bashrc 2>/dev/null || true

echo ""
echo "🎉 ================================================= 🎉"
echo "✅ VPS RESTORE COMPLETED SUCCESSFULLY!"
echo "🤖 Telegram Bot (@Kontrolagybot) is running & active!"
echo "⚡ Antigravity CLI (agy) is configured and ready!"
echo "🎉 ================================================= 🎉"
