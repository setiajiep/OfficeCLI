#!/bin/bash
# One-Click Disaster Recovery Script for MyProject

echo "========================================="
echo "   Disaster Recovery: Restoring VPS      "
echo "========================================="

# 1. Install dependencies
echo "1. Installing basic dependencies (git, curl, tar, rclone)..."
sudo apt-get update -qq && sudo apt-get install -y -qq git curl tar rclone nodejs npm python3 > /dev/null

# 2. Setup rclone configuration
echo "2. Setting up Google Drive authentication..."
mkdir -p ~/.config/rclone /home/ubuntu/.config/rclone
if [ ! -f ~/.config/rclone/rclone.conf ]; then
    if [ -n "$RCLONE_TOKEN" ]; then
        cat << EOF > ~/.config/rclone/rclone.conf
[gdrive]
type = drive
scope = drive
token = $RCLONE_TOKEN
EOF
    else
        echo "WARNING: ~/.config/rclone/rclone.conf not found."
        echo "Please ensure rclone is configured or set RCLONE_TOKEN."
    fi
fi
cp ~/.config/rclone/rclone.conf /home/ubuntu/.config/rclone/rclone.conf 2>/dev/null || true

# 3. Find latest backup from Google Drive
echo "3. Searching latest backup archive in Google Drive..."
LATEST_BACKUP=$(rclone lsf gdrive:Backup_Server_MyProject --files-only | sort -r | head -n 1)

if [ -z "$LATEST_BACKUP" ]; then
    echo "ERROR: No backup archive found in gdrive:Backup_Server_MyProject!"
    exit 1
fi

echo "Found latest backup: $LATEST_BACKUP"
echo "4. Downloading backup file..."
rclone copy "gdrive:Backup_Server_MyProject/$LATEST_BACKUP" /tmp/ --tpslimit 10

# 4. Extract archive
echo "5. Extracting projects and data..."
tar -xzf "/tmp/$LATEST_BACKUP" -C /

# 5. Fix symlinks and permissions
mkdir -p /home/ubuntu
ln -sfn /root/MyProject /home/ubuntu/MyProject 2>/dev/null
rm -f "/tmp/$LATEST_BACKUP"

# 6. Re-enable Cron
echo "6. Restoring automated daily cron job..."
(crontab -l 2>/dev/null | grep -v 'run_all_backups.sh'; echo "0 2 * * * /bin/bash /root/run_all_backups.sh > /root/backup.log 2>&1") | crontab -

echo "========================================="
echo "  SUCCESS! RESTORE COMPLETED IN MINUTES. "
echo "  All projects restored at: /root/MyProject"
echo "========================================="
