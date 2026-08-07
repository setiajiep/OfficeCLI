#!/bin/bash
# Real-time File Watcher & Auto-Sync to Google Drive

WATCH_DIR="/root/MyProject"
LOG_FILE="/var/log/gdrive_autosync.log"

echo "=== [$(date)] Starting Real-time Google Drive Auto-Sync Daemon ===" >> "$LOG_FILE"

# Initial sync on daemon startup
/root/sync_gdrive.sh >> "$LOG_FILE" 2>&1

# Watch directory for changes, excluding noise
inotifywait -m -r -e create,modify,delete,move \
    --exclude '(node_modules|\.git|\.wrangler|\.turbo|DawnCache|GPUCache|\.tmp)' \
    "$WATCH_DIR" | while read -r directory events filename; do
        echo "[$(date)] Change detected: $directory$filename ($events)" >> "$LOG_FILE"
        # Debounce: wait 5 seconds after file modification finishes
        sleep 5
        /root/sync_gdrive.sh >> "$LOG_FILE" 2>&1
    done
