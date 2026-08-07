#!/bin/bash
# Backup Script for MyProject to Google Drive via rclone

DATE=$(date +%Y-%m-%d_%H%M%S)
BACKUP_DIR="/tmp/backup_work"
ARCHIVE_NAME="MyProject_backup_${DATE}.tar.gz"
REMOTE_FOLDER="gdrive:Backup_Server_MyProject"

mkdir -p "$BACKUP_DIR"

echo "=== Starting Backup: $DATE ==="

# 1. Compress /root/MyProject excluding node_modules and cache folders
tar --exclude='node_modules' \
    --exclude='.wrangler' \
    --exclude='.turbo' \
    --exclude='DawnCache' \
    --exclude='GPUCache' \
    -czf "$BACKUP_DIR/$ARCHIVE_NAME" \
    /root/MyProject \
    /home/ubuntu/MyProject 2>/dev/null

echo "Archive created: $BACKUP_DIR/$ARCHIVE_NAME"
ls -lh "$BACKUP_DIR/$ARCHIVE_NAME"

# 2. Upload to Google Drive
echo "Uploading to Google Drive ($REMOTE_FOLDER)..."
rclone copy "$BACKUP_DIR/$ARCHIVE_NAME" "$REMOTE_FOLDER/" --tpslimit 5 --retries 5

if [ $? -eq 0 ]; then
    echo "SUCCESS: Upload completed."
    rm -f "$BACKUP_DIR/$ARCHIVE_NAME"
else
    echo "ERROR: Upload failed!"
    exit 1
fi

# 3. Clean up backups older than 14 days on Google Drive
echo "Cleaning up backups older than 14 days on Google Drive..."
rclone delete "$REMOTE_FOLDER" --min-age 14d 2>/dev/null

echo "=== Backup Finished Successfully: $DATE ==="
