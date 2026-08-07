#!/bin/bash
# Master Backup Script: Both Archive (.tar.gz) and Live Sync to Google Drive

echo "========================================="
echo "Starting Master Backup & Sync $(date)"
echo "========================================="

# 1. Run Archive Backup (.tar.gz)
echo "--- Step 1: Running Archive Backup ---"
/bin/bash /root/backup_gdrive.sh

# Sleep 15 seconds to allow API quota to cool down
sleep 15

# 2. Run Direct Folder Sync (Unzipped)
echo "--- Step 2: Running Live Folder Sync ---"
/bin/bash /root/sync_gdrive.sh

echo "========================================="
echo "Master Backup & Sync Completed Successfully!"
echo "========================================="
