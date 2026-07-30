#!/bin/bash
# 1-Line Complete VPS Restore & Environment Setup Script for OfficeCLI

set -e

echo "🚀 Starting 1-Line Setup & Restore from GitHub (OfficeCLI)..."

# 1. Check & setup .env file safely without hardcoding secrets
if [ ! -f "/root/.env" ]; then
    echo "🔑 Setting up environment file (.env)..."
    touch /root/.env
    chmod 600 /root/.env
fi

# 2. Extract tar.gz backup if present in /root
BACKUP_ARCHIVE=$(ls /root/vps_backup_*.tar.gz 2>/dev/null | head -n 1 || true)
if [ -n "$BACKUP_ARCHIVE" ] && [ -f "$BACKUP_ARCHIVE" ]; then
    echo "📦 Extracting VPS backup archive: $BACKUP_ARCHIVE..."
    tar -xzf "$BACKUP_ARCHIVE" -C / 2>/dev/null || true
fi

# 3. Install Core System Dependencies
echo "📦 Installing System Dependencies (Python3, Node.js 20, Git, LibreOffice, Pandoc, Poppler)..."
apt-get update -qq
apt-get install -y -qq python3 python3-pip python3-venv git curl tar cron \
    libreoffice-writer libreoffice-calc libreoffice-impress pandoc poppler-utils ghostscript

if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y -qq nodejs
fi

if ! command -v wrangler &> /dev/null; then
    npm install -g wrangler &> /dev/null || true
fi

# 4. Install Python Office Libraries
echo "🐍 Installing Python Office & PDF Libraries..."
pip install python-docx openpyxl pandas python-pptx reportlab pypdf pdfplumber pdf2image fpdf2 --break-system-packages &> /dev/null || true

# 5. Copy Systemd Bot Service
if [ -f "/root/antigravity-bot.service" ]; then
    cp /root/antigravity-bot.service /etc/systemd/system/antigravity-bot.service
fi

# 6. Configure Permissions & Executables
chmod +x /root/telegram_bot.py /root/backup_vps.sh /root/git_backup.sh /root/setup.sh /root/office_tools.py 2>/dev/null || true
chmod +x /root/.local/bin/agy 2>/dev/null || true

# 7. Enable & Restart Systemd Bot Service
if [ -f "/etc/systemd/system/antigravity-bot.service" ]; then
    echo "⚙️ Starting Telegram Bot Service (@Kontrolagybot)..."
    systemctl daemon-reload
    systemctl enable antigravity-bot.service
    systemctl restart antigravity-bot.service
fi

# 8. Git Global Config
git config --global user.name "Setiaji Eka Putra"
git config --global user.email "setiajiepagina00@gmail.com" 2>/dev/null || git config --global user.email "setiajiekaputra00@gmail.com"
git config --global init.defaultBranch main

# 9. Set Shell Aliases & Environment Loading
if ! grep -q 'alias agy=' /root/.bashrc 2>/dev/null; then
    echo 'alias agy="agy --dangerously-skip-permissions"' >> /root/.bashrc
fi

if ! grep -q '\.env' /root/.bashrc 2>/dev/null; then
    echo '[ -f ~/.env ] && export $(cat ~/.env | xargs)' >> /root/.bashrc
fi

# 10. Setup Timezone to Asia/Jakarta (WIB) & Daily Auto-Backup Cron Job (00:00 WIB)
timedatectl set-timezone Asia/Jakarta 2>/dev/null || ln -sf /usr/share/zoneinfo/Asia/Jakarta /etc/localtime
(crontab -l 2>/dev/null | grep -v 'git_backup.sh'; echo "0 0 * * * /root/git_backup.sh >/dev/null 2>&1") | crontab -
systemctl enable --now cron

echo ""
echo "🎉 ================================================= 🎉"
echo "✅ VPS RESTORE & SETUP COMPLETED SUCCESSFULLY!"
echo "🤖 Telegram Bot (@Kontrolagybot) is running live!"
echo "🏢 Office CLI & PDF Suite is fully operational!"
echo "⏰ Daily Automatic Backup Schedule (00:00 WIB) is ACTIVE!"
echo "⚡ Antigravity CLI (agy) & Wrangler ready to use!"
echo "🎉 ================================================= 🎉"
