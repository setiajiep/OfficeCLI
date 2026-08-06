#!/bin/bash

# Load environment file if present
[ -f /root/.env ] && set -a && . /root/.env && set +a 2>/dev/null

# Configuration
KONTROL_BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-}"
DEFAULT_USER_ID="${TELEGRAM_OWNER_ID:-}"
TARGET_CHAT_ID="${1:-$DEFAULT_USER_ID}"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
DATE_STAMP=$(date +"%Y%m%d_%H%M%S")

# Ensure service file is up-to-date in git repo
cp /etc/systemd/system/antigravity-bot.service /root/antigravity-bot.service 2>/dev/null || true

echo "📦 Performing Git Backup to GitHub (OfficeCLI)..."

cd /root
git add . 2>/dev/null || true
git commit -m "VPS Backup: $TIMESTAMP" 2>/dev/null || true

PUSH_OUT=$(git push origin main 2>&1)
EXIT_CODE=$?

# Create Zip Archive of project and configuration files
BACKUP_ZIP="/tmp/vps_backup_${DATE_STAMP}.zip"
echo "🤐 Creating Backup Zip file..."
zip -r "$BACKUP_ZIP" /root/MyProject /root/*.py /root/*.sh /root/*.md /root/*.json /root/.env /root/antigravity-bot.service -x "*.git*" "*__pycache__*" "*.cache*" 2>/dev/null || true

if [ -z "$KONTROL_BOT_TOKEN" ] || [ -z "$TARGET_CHAT_ID" ]; then
    echo "⚠️ TELEGRAM_BOT_TOKEN or TELEGRAM_OWNER_ID not configured in /root/.env! Skipping Telegram notification."
    rm -f "$BACKUP_ZIP"
    exit 0
fi

if [ $EXIT_CODE -eq 0 ]; then
    MSG="📦 *VPS BACKUP SUCCESSFUL!*
━━━━━━━━━━━━━━━━━━━━━
🕒 *Waktu:* \`$TIMESTAMP\`
🔗 *GitHub Repo:* [setiajiep/OfficeCLI](https://github.com/setiajiep/OfficeCLI)
🤖 *Bot Controller Active*

⚡ *1-BARIS PERINTAH RESTORE DI VPS BARU:*
\`git clone https://github.com/setiajiep/OfficeCLI.git /root && bash /root/setup.sh\`"
else
    MSG="⚠️ *GIT BACKUP NOTICE*
━━━━━━━━━━━━━━━━━━━━━
🕒 *Waktu:* \`$TIMESTAMP\`
ℹ️ *Status Git:* \`$PUSH_OUT\`

📂 *File Zip Backup Tetap Dikirim Langsung ke Telegram Below.*"
fi

# Send Text Status Message
curl -s -F "chat_id=${TARGET_CHAT_ID}" \
     -F "text=${MSG}" \
     -F "parse_mode=Markdown" \
     "https://api.telegram.org/bot${KONTROL_BOT_TOKEN}/sendMessage" > /dev/null

# Send Backup Zip File to Telegram Document
if [ -f "$BACKUP_ZIP" ]; then
    echo "📤 Sending Zip Backup file to Telegram..."
    curl -s -F "chat_id=${TARGET_CHAT_ID}" \
         -F "document=@${BACKUP_ZIP}" \
         -F "caption=📦 File Backup VPS ($TIMESTAMP)" \
         "https://api.telegram.org/bot${KONTROL_BOT_TOKEN}/sendDocument" > /dev/null
    rm -f "$BACKUP_ZIP"
fi
