#!/usr/bin/env python3
"""
Telegram Utility Helper for OfficeCLI Suite
Allows sending documents, photos, and files directly to Telegram,
and prompts the user in CLI interactive mode after file generation.
"""

import os
import sys
import json
import requests

DEFAULT_BOT_TOKEN = "8555802988:AAFwf5YYGQzWRqxMf_YbCpZ19LLev92z6XE"
DEFAULT_OWNER_ID = 508687457
OWNER_FILE = "/root/.antigravity_bot_owner.json"

def get_telegram_config():
    """Retrieve Bot Token and Target Chat/Owner ID from env or config files."""
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        token = DEFAULT_BOT_TOKEN

    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip() or os.getenv("TELEGRAM_OWNER_ID", "").strip()
    if not chat_id and os.path.exists(OWNER_FILE):
        try:
            with open(OWNER_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                chat_id = data.get("user_id")
        except Exception:
            pass

    if not chat_id:
        chat_id = DEFAULT_OWNER_ID

    return token, str(chat_id)

def send_file_to_telegram(file_path, caption=None, chat_id=None):
    """
    Send a document or image file to Telegram via Bot API.
    Returns (success: bool, message: str)
    """
    if not os.path.exists(file_path):
        return False, f"File tidak ditemukan: {file_path}"

    token, default_chat_id = get_telegram_config()
    target_chat_id = str(chat_id) if chat_id else default_chat_id

    if not token:
        return False, "Telegram Bot Token tidak dikonfigurasi."

    ext = os.path.splitext(file_path)[1].lower()
    filename = os.path.basename(file_path)
    if caption is None:
        caption = f"📄 *File:* `{filename}`"

    # Decide whether to send as Photo or Document
    if ext in ['.png', '.jpg', '.jpeg', '.webp'] and os.path.getsize(file_path) < 10 * 1024 * 1024:
        endpoint = f"https://api.telegram.org/bot{token}/sendPhoto"
        file_field = "photo"
    else:
        endpoint = f"https://api.telegram.org/bot{token}/sendDocument"
        file_field = "document"

    try:
        with open(file_path, 'rb') as f:
            files = {file_field: (filename, f)}
            data = {
                "chat_id": target_chat_id,
                "caption": caption,
                "parse_mode": "Markdown"
            }
            resp = requests.post(endpoint, data=data, files=files, timeout=30)
            result = resp.json()
            if result.get("ok"):
                return True, f"✅ Berhasil mengirim file '{filename}' ke Telegram (Chat ID: {target_chat_id})."
            else:
                # Fallback sendDocument if sendPhoto failed
                if file_field == "photo":
                    f.seek(0)
                    endpoint = f"https://api.telegram.org/bot{token}/sendDocument"
                    files = {"document": (filename, f)}
                    resp = requests.post(endpoint, data=data, files=files, timeout=30)
                    result = resp.json()
                    if result.get("ok"):
                        return True, f"✅ Berhasil mengirim file '{filename}' ke Telegram."
                
                err_msg = result.get("description", "Unknown error")
                return False, f"❌ Gagal mengirim ke Telegram: {err_msg}"
    except Exception as e:
        return False, f"❌ Error koneksi Telegram: {e}"

def prompt_send_to_telegram(file_path, caption=None, chat_id=None, force_send=False):
    """
    After creating/editing a document or image:
    1. If force_send is True, send immediately.
    2. If running interactively in terminal (TTY), ask:
       "Mau dikirim ke Telegram nggak dokumen/gambarnya? (y/n): "
    """
    if not os.path.exists(file_path):
        return False

    filename = os.path.basename(file_path)

    if force_send:
        print(f"\n🚀 Mengirim '{filename}' ke Telegram...")
        success, msg = send_file_to_telegram(file_path, caption=caption, chat_id=chat_id)
        print(msg)
        return success

    # Check if CLI is in interactive mode (TTY)
    if sys.stdin and sys.stdin.isatty():
        try:
            print("\n" + "═" * 55)
            ans = input(f"✈️  File '{filename}' selesai dibuat.\n❓ Mau dikirim ke Telegram nggak? (y/N): ").strip().lower()
            print("═" * 55)
            if ans in ['y', 'ya', 'yes', '1']:
                print(f"📤 Mengirim '{filename}' ke Telegram...")
                success, msg = send_file_to_telegram(file_path, caption=caption, chat_id=chat_id)
                print(msg)
                return success
            else:
                print("ℹ️ File disimpan lokal. Tidak dikirim ke Telegram.")
                return False
        except (KeyboardInterrupt, EOFError):
            print("\nℹ️ Batal kirim ke Telegram.")
            return False
    else:
        print(f"\n💡 File '{filename}' tersimpan. [Gunakan flag --send-telegram / -t untuk otomatis kirim ke Telegram]")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        fp = sys.argv[1]
        cap = sys.argv[2] if len(sys.argv) > 2 else None
        prompt_send_to_telegram(fp, caption=cap, force_send=True)
    else:
        print("Usage: python3 telegram_utils.py <file_path> [caption]")
