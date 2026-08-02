#!/bin/bash
# ==============================================================================
# 1-LINE COMPLETE VPS SETUP & RESTORE SCRIPT (OfficeCLI & PDF Suite)
# ==============================================================================
# Cara Pakai di VPS Baru:
#   git clone https://github.com/setiajiep/OfficeCLI.git /root && bash /root/setup.sh
# Atau dengan Token Telegram Custom:
#   TELEGRAM_BOT_TOKEN="BOT_TOKEN_ANDA" TELEGRAM_OWNER_ID="ID_TELEGRAM_ANDA" bash /root/setup.sh
# ==============================================================================

set -e

echo "🚀 Starting Complete VPS Setup & Restore (OfficeCLI & PDF Suite)..."

# 0. Auto-clone repository if files are missing in /root
if [ ! -f "/root/telegram_bot.py" ]; then
    echo "📥 Repository files not found in /root. Cloning from GitHub..."
    apt-get update -qq && apt-get install -y -qq git
    git clone https://github.com/setiajiep/OfficeCLI.git /tmp/officecli_repo
    cp -rn /tmp/officecli_repo/* /tmp/officecli_repo/.* /root/ 2>/dev/null || true
    rm -rf /tmp/officecli_repo
fi

# 1. Setup Timezone to Asia/Jakarta (WIB)
echo "🌐 Setting timezone to Asia/Jakarta (WIB)..."
timedatectl set-timezone Asia/Jakarta 2>/dev/null || ln -sf /usr/share/zoneinfo/Asia/Jakarta /etc/localtime

# 2. Setup Environment (.env) File
echo "🔑 Checking Environment File (.env)..."
if [ ! -f "/root/.env" ]; then
    if [ -f "/root/.env.example" ]; then
        cp /root/.env.example /root/.env
    else
        touch /root/.env
    fi
    chmod 600 /root/.env
fi

# Update TOKEN or OWNER if passed explicitly via environment variables
if [ -n "$TELEGRAM_BOT_TOKEN" ]; then
    if grep -q "^TELEGRAM_BOT_TOKEN=" /root/.env; then
        sed -i "s|^TELEGRAM_BOT_TOKEN=.*|TELEGRAM_BOT_TOKEN=\"$TELEGRAM_BOT_TOKEN\"|" /root/.env
    else
        echo "TELEGRAM_BOT_TOKEN=\"$TELEGRAM_BOT_TOKEN\"" >> /root/.env
    fi
fi

if [ -n "$TELEGRAM_OWNER_ID" ]; then
    if grep -q "^TELEGRAM_OWNER_ID=" /root/.env; then
        sed -i "s|^TELEGRAM_OWNER_ID=.*|TELEGRAM_OWNER_ID=\"$TELEGRAM_OWNER_ID\"|" /root/.env
    else
        echo "TELEGRAM_OWNER_ID=\"$TELEGRAM_OWNER_ID\"" >> /root/.env
    fi
fi

# Load environment
[ -f /root/.env ] && export $(grep -v '^#' /root/.env | xargs) 2>/dev/null

# 3. Update APT Package Index & Install Full System Dependencies
echo "📦 Updating APT package index and installing Office & PDF CLI suite..."
apt-get update -qq

apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    tar \
    zip \
    unzip \
    cron \
    poppler-utils \
    qpdf \
    pdftk-java \
    img2pdf \
    ocrmypdf \
    tesseract-ocr \
    tesseract-ocr-ind \
    tesseract-ocr-eng \
    docx2txt \
    odt2txt \
    xlsx2csv \
    catdoc \
    ffmpeg \
    imagemagick \
    ghostscript \
    pandoc \
    libreoffice-writer \
    libreoffice-calc \
    libreoffice-impress \
    libreoffice-draw

# 4. Install Node.js (v20) if not present
if ! command -v node &> /dev/null; then
    echo "🟢 Installing Node.js (v20)..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &>/dev/null
    apt-get install -y -qq nodejs
fi

# 5. Install Typst CLI (Typesetting System)
if ! command -v typst &> /dev/null; then
    echo "⚡ Installing Typst CLI..."
    curl -fsSL https://github.com/typst/typst/releases/download/v0.11.1/typst-x86_64-unknown-linux-musl.tar.xz | tar -xJ -C /tmp
    cp /tmp/typst-x86_64-unknown-linux-musl/typst /usr/local/bin/
    chmod +x /usr/local/bin/typst
fi

# 6. Install pdfcpu CLI (Go PDF Processor)
if ! command -v pdfcpu &> /dev/null; then
    echo "⚡ Installing pdfcpu CLI..."
    curl -fsSL https://github.com/pdfcpu/pdfcpu/releases/download/v0.13.0/pdfcpu_0.13.0_Linux_x86_64.tar.xz | tar -xJ -C /tmp
    cp /tmp/pdfcpu_0.13.0_Linux_x86_64/pdfcpu /usr/local/bin/
    chmod +x /usr/local/bin/pdfcpu
fi

# 7. Install Python PDF & Office CLI Libraries
echo "🐍 Installing Python PDF & Office Libraries..."
pip install --break-system-packages \
    pdf2docx \
    pypdf \
    pdfplumber \
    pymupdf \
    csvkit \
    openpyxl \
    python-docx \
    python-pptx \
    reportlab \
    pandas \
    fpdf2 \
    qrcode[pil] \
    pytesseract \
    SpeechRecognition \
    matplotlib \
    psutil &>/dev/null || true

# 8. Configure Executable Permissions
chmod +x /root/telegram_bot.py \
         /root/backup_vps.sh \
         /root/git_backup.sh \
         /root/setup.sh \
         /root/office_tools.py \
         /root/image_tools.py \
         /root/telegram_utils.py 2>/dev/null || true

# 9. Configure Git Global User
git config --global user.name "Setiaji Eka Putra"
git config --global user.email "setiajiekaputra00@gmail.com"
git config --global init.defaultBranch main

# 10. Configure Systemd Service for Telegram Bot
if [ -f "/root/antigravity-bot.service" ]; then
    echo "⚙️ Setting up systemd service (antigravity-bot.service)..."
    cp /root/antigravity-bot.service /etc/systemd/system/antigravity-bot.service
    systemctl daemon-reload
    systemctl enable antigravity-bot.service
    systemctl restart antigravity-bot.service 2>/dev/null || true
fi

# 11. Configure Daily Auto-Backup Cron Job (00:00 WIB)
echo "⏰ Setting up daily cron job (00:00 WIB)..."
(crontab -l 2>/dev/null | grep -v 'git_backup.sh'; echo "0 0 * * * /root/git_backup.sh >/dev/null 2>&1") | crontab -
systemctl enable --now cron &>/dev/null || true

# 12. Set Shell Aliases & Environment Autoload
if ! grep -q 'alias agy=' /root/.bashrc 2>/dev/null; then
    echo 'alias agy="agy --dangerously-skip-permissions"' >> /root/.bashrc
fi

if ! grep -q '\.env' /root/.bashrc 2>/dev/null; then
    echo '[ -f ~/.env ] && export $(cat ~/.env | xargs)' >> /root/.bashrc
fi

echo ""
echo "🎉 ================================================= 🎉"
echo "✅ VPS SETUP & RESTORE COMPLETED SUCCESSFULLY!"
echo "🏢 Office CLI, PDF Suite, Typst & pdfcpu installed!"
echo "⏰ Daily Backup Cron Job (00:00 WIB) is ACTIVE!"
echo "🔗 GitHub Sync: https://github.com/setiajiep/OfficeCLI"
echo "💡 Masukkan Token Telegram di /root/.env jika belum ada."
echo "🎉 ================================================= 🎉"
