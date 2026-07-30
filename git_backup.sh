#!/bin/bash

# Load environment file if present
[ -f /root/.env ] && export $(grep -v '^#' /root/.env | xargs) 2>/dev/null

# Configuration
KONTROL_BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-8555802988:AAFwf5YYGQzWRqxMf_YbCpZ19LLev92z6XE}"
TELEGRAM_USER_ID="${TELEGRAM_OWNER_ID:-508687457}"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

# Ensure service file is up-to-date in git repo
cp /etc/systemd/system/antigravity-bot.service /root/antigravity-bot.service 2>/dev/null || true

echo "📦 Performing Git Backup to GitHub (OfficeCLI)..."

cd /root
git add . 2>/dev/null || true
git commit -m "VPS Backup: $TIMESTAMP" 2>/dev/null || true

PUSH_OUT=$(git push origin main 2>&1)
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    MSG="📦 *VPS BACKUP SUCCESSFUL!*
━━━━━━━━━━━━━━━━━━━━━
🕒 *Waktu:* \`$TIMESTAMP\`
🔗 *GitHub Repo:* [setiajiep/OfficeCLI](https://github.com/setiajiep/OfficeCLI)
🤖 *Bot Controller:* @Kontrolagybot

⚡ *1-BARIS PERINTAH RESTORE DI VPS BARU:*
\`git clone https://github.com/setiajiep/OfficeCLI.git /root && bash /root/setup.sh\`"
else
    MSG="⚠️ *GIT BACKUP ERROR*
━━━━━━━━━━━━━━━━━━━━━
🕒 *Waktu:* \`$TIMESTAMP\`
❌ *Detail Error:*
\`\`\`
$PUSH_OUT
\`\`\`"
fi

curl -s -F "chat_id=${TELEGRAM_USER_ID}" \
     -F "text=${MSG}" \
     -F "parse_mode=Markdown" \
     "https://api.telegram.org/bot${KONTROL_BOT_TOKEN}/sendMessage" > /dev/null
