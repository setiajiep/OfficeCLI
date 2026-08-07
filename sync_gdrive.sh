#!/bin/bash
# Direct Folder Sync Script for MyProject to Google Drive

echo "=== Starting Direct Folder Sync to Google Drive ==="

rclone sync /root/MyProject gdrive:MyProject_LiveSync \
    --exclude "node_modules/**" \
    --exclude ".wrangler/**" \
    --exclude ".turbo/**" \
    --exclude "DawnCache/**" \
    --exclude "GPUCache/**" \
    --tpslimit 10 --retries 3

if [ $? -eq 0 ]; then
    echo "SUCCESS: Direct folder sync completed to 'MyProject_LiveSync'."
else
    echo "ERROR: Sync failed!"
    exit 1
fi
