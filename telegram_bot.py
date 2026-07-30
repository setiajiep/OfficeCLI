import os
import sys
import json
import time
import shutil
import urllib.request
import urllib.parse
import subprocess
import threading
import re
from datetime import datetime

TOKEN = "8555802988:AAFwf5YYGQzWRqxMf_YbCpZ19LLev92z6XE"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}/"
AGY_BIN = "/root/.local/bin/agy"
OFFICE_TOOLS = "/root/office_tools.py"

STATE_FILE = "/root/.antigravity_bot_state.json"
FILES_PER_PAGE = 8

# Path encoder to ensure Telegram 64-byte callback_data limit is never exceeded
PATH_MAP = {}
PATH_COUNTER = 0

def encode_path(path):
    global PATH_COUNTER
    abs_path = os.path.abspath(path)
    for k, v in PATH_MAP.items():
        if v == abs_path:
            return k
    PATH_COUNTER += 1
    key = f"p{PATH_COUNTER}"
    PATH_MAP[key] = abs_path
    return key

def decode_path(key):
    return PATH_MAP.get(key, "/root/MyProject")

encode_path("/root")
encode_path("/root/MyProject")

def clean_ai_output(text):
    if not text:
        return ""
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'`(.*?)`', r'\1', text)
    text = re.sub(r'^#{1,6}\s*(.*)$', r'📌 \1', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*[\*\-]\s+', '• ', text, flags=re.MULTILINE)
    return text.strip()

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"owner_id": None, "owner_username": None, "cwds": {}, "show_hidden": {}}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

STATE = load_state()

def get_user_cwd(user_id):
    str_id = str(user_id)
    default_dir = "/root/MyProject" if os.path.exists("/root/MyProject") else "/root"
    cwd = STATE.get("cwds", {}).get(str_id, default_dir)
    if not os.path.exists(cwd):
        cwd = default_dir
    return cwd

def set_user_cwd(user_id, new_cwd):
    str_id = str(user_id)
    if os.path.exists(new_cwd) and os.path.isdir(new_cwd):
        if "cwds" not in STATE:
            STATE["cwds"] = {}
        STATE["cwds"][str_id] = os.path.abspath(new_cwd)
        save_state(STATE)
        return True
    return False

def get_show_hidden(user_id):
    str_id = str(user_id)
    return STATE.get("show_hidden", {}).get(str_id, False)

def toggle_show_hidden(user_id):
    str_id = str(user_id)
    if "show_hidden" not in STATE:
        STATE["show_hidden"] = {}
    current = STATE["show_hidden"].get(str_id, False)
    STATE["show_hidden"][str_id] = not current
    save_state(STATE)
    return not current

def api_request(method, data=None):
    url = BASE_URL + method
    try:
        if data:
            encoded_data = json.dumps(data).encode("utf-8")
            req = urllib.request.Request(url, data=encoded_data, headers={"Content-Type": "application/json"})
        else:
            req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"API Error ({method}): {e}", file=sys.stderr)
        return None

def answer_callback_query(callback_query_id, text=None, show_alert=False):
    payload = {"callback_query_id": callback_query_id, "show_alert": show_alert}
    if text:
        payload["text"] = text
    api_request("answerCallbackQuery", payload)

def send_message(chat_id, text, reply_markup=None, parse_mode=None):
    if not text:
        text = "✅ Selesai."
    chunks = [text[i:i+3900] for i in range(0, len(text), 3900)]
    sent_msgs = []
    for idx, chunk in enumerate(chunks):
        payload = {"chat_id": chat_id, "text": chunk}
        if parse_mode:
            payload["parse_mode"] = parse_mode
        if idx == len(chunks) - 1 and reply_markup:
            payload["reply_markup"] = reply_markup
        
        res = api_request("sendMessage", payload)
        if not res or not res.get("ok"):
            payload.pop("parse_mode", None)
            res = api_request("sendMessage", payload)
            
        if res and res.get("ok"):
            sent_msgs.append(res["result"])
    return sent_msgs

def edit_message(chat_id, message_id, text, reply_markup=None, parse_mode=None):
    if not text:
        text = "✅ Selesai."
    payload = {"chat_id": chat_id, "message_id": message_id, "text": text[:3900]}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    if parse_mode:
        payload["parse_mode"] = parse_mode
    
    res = api_request("editMessageText", payload)
    
    if not res or not res.get("ok"):
        payload.pop("parse_mode", None)
        res = api_request("editMessageText", payload)

    if not res or not res.get("ok"):
        return send_message(chat_id, text, reply_markup=reply_markup)
    return res

def send_document(chat_id, file_path, caption=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendDocument"
    if not os.path.exists(file_path):
        send_message(chat_id, f"❌ File {file_path} tidak ditemukan.")
        return
    try:
        cmd = ["curl", "-s", "-F", f"chat_id={chat_id}", "-F", f"document=@{file_path}"]
        if caption:
            cmd.extend(["-F", f"caption={caption}"])
        cmd.append(url)
        subprocess.run(cmd, check=True)
    except Exception as e:
        send_message(chat_id, f"❌ Gagal mengirim document: {e}")

SYSTEM_FILES = ["telegram_bot.py", "office_tools.py", "setup.sh", "backup_vps.sh", "git_backup.sh", "restore.sh", "antigravity-bot.service"]

def render_file_manager(user_id, current_dir, page=1, notice=None):
    current_dir = os.path.abspath(current_dir)
    if not os.path.exists(current_dir):
        current_dir = "/root/MyProject" if os.path.exists("/root/MyProject") else "/root"

    dir_key = encode_path(current_dir)
    show_hidden = get_show_hidden(user_id)

    rel_path = current_dir.replace("/root", "~")
    text = f"🏢 OFFICE CLI & PROJECT MANAGER\n"
    text += f"━━━━━━━━━━━━━━━━━━━━━\n"
    text += f"📍 Path: {rel_path}\n"
    if notice:
        text += f"\n{notice}\n"
    text += "━━━━━━━━━━━━━━━━━━━━━\n\n"

    folders = []
    files = []
    try:
        raw_items = os.listdir(current_dir)
        for name in raw_items:
            if not show_hidden:
                if name.startswith(".") or name in ["__pycache__"]:
                    continue
                if current_dir == "/root" and name in SYSTEM_FILES:
                    continue

            full_p = os.path.join(current_dir, name)
            try:
                if os.path.isdir(full_p):
                    folders.append(name)
                else:
                    files.append(name)
            except Exception:
                files.append(name)
        
        folders.sort(key=lambda x: x.lower())
        files.sort(key=lambda x: x.lower())
    except Exception as e:
        text += f"❌ Error membaca folder: {e}\n"

    total_files = len(files)
    total_pages = max(1, (total_files + FILES_PER_PAGE - 1) // FILES_PER_PAGE)
    page = max(1, min(page, total_pages))

    start_idx = (page - 1) * FILES_PER_PAGE
    end_idx = start_idx + FILES_PER_PAGE
    page_files = files[start_idx:end_idx]

    text += f"📁 Folder ({len(folders)}):\n"
    if folders:
        for f_name in folders[:15]:
            text += f"• 📁 {f_name}\n"
        if len(folders) > 15:
            text += f"  ...dan {len(folders)-15} folder lainnya.\n"
    else:
        text += "_Tidak ada folder_\n"

    text += f"\n📄 Dokumen & File ({total_files}) - Halaman {page}/{total_pages}:\n"
    if page_files:
        for fl_name in page_files:
            ext = os.path.splitext(fl_name)[1].lower()
            icon = "📄"
            if ext == ".pdf": icon = "📕"
            elif ext in [".docx", ".doc"]: icon = "📘"
            elif ext in [".xlsx", ".xls", ".csv"]: icon = "📊"
            elif ext in [".pptx", ".ppt"]: icon = "📙"
            elif ext in [".png", ".jpg", ".jpeg"]: icon = "🖼️"

            try:
                sz = os.path.getsize(os.path.join(current_dir, fl_name)) / 1024
                sz_str = f"{sz:.1f}KB"
            except Exception:
                sz_str = ""
            text += f"• {icon} {fl_name} ({sz_str})\n"
    else:
        text += "_Tidak ada file_\n"

    inline_keyboard = []

    parent_dir = os.path.dirname(current_dir)
    parent_key = encode_path(parent_dir)
    nav_buttons = []
    if parent_dir != current_dir and current_dir != "/root":
        nav_buttons.append({"text": "⬆️ Ke Folder Atas", "callback_data": f"fm_cd:{parent_key}:1"})
    nav_buttons.append({"text": "🔄 Refresh", "callback_data": f"fm_cd:{dir_key}:{page}"})
    inline_keyboard.append(nav_buttons)

    myproject_key = encode_path("/root/MyProject")
    toggle_hidden_text = "🙈 Sembunyikan System" if show_hidden else "👁️ Lihat File System"
    
    inline_keyboard.append([
        {"text": "➕ Folder Baru", "callback_data": "fm_action:create_folder_prompt"},
        {"text": "📝 File Baru", "callback_data": "fm_action:create_file_prompt"}
    ])
    inline_keyboard.append([
        {"text": "📂 MyProject Home", "callback_data": f"fm_cd:{myproject_key}:1"},
        {"text": "📦 Backup VPS", "callback_data": "fm_action:do_backup"}
    ])
    inline_keyboard.append([
        {"text": toggle_hidden_text, "callback_data": "fm_action:toggle_hidden"}
    ])

    row = []
    for item in folders[:10]:
        full_path = os.path.join(current_dir, item)
        f_key = encode_path(full_path)
        btn_text = f"📁 {item[:16]}"
        row.append({"text": btn_text, "callback_data": f"fm_folder:{f_key}"})
        if len(row) == 2:
            inline_keyboard.append(row)
            row = []
    if row:
        inline_keyboard.append(row)

    file_row = []
    for item in page_files:
        full_path = os.path.join(current_dir, item)
        fl_key = encode_path(full_path)
        ext = os.path.splitext(item)[1].lower()
        icon = "📄"
        if ext == ".pdf": icon = "📕"
        elif ext in [".docx", ".doc"]: icon = "📘"
        elif ext in [".xlsx", ".xls", ".csv"]: icon = "📊"
        elif ext in [".pptx", ".ppt"]: icon = "📙"
        elif ext in [".png", ".jpg", ".jpeg"]: icon = "🖼️"

        btn_text = f"{icon} {item[:16]}"
        file_row.append({"text": btn_text, "callback_data": f"fm_file:{fl_key}"})
        if len(file_row) == 2:
            inline_keyboard.append(file_row)
            file_row = []
    if file_row:
        inline_keyboard.append(file_row)

    if total_pages > 1:
        pag_row = []
        if page > 1:
            pag_row.append({"text": "◀️ Prev", "callback_data": f"fm_cd:{dir_key}:{page-1}"})
        pag_row.append({"text": f"📄 {page}/{total_pages}", "callback_data": "fm_action:noop"})
        if page < total_pages:
            pag_row.append({"text": "Next ▶️", "callback_data": f"fm_cd:{dir_key}:{page+1}"})
        inline_keyboard.append(pag_row)

    text += "\n💡 Tip: Upload dokumen Word/Excel/PDF/Gambar Tanda Tangan dengan caption instruksi!"

    reply_markup = {"inline_keyboard": inline_keyboard}
    return text, reply_markup

def execute_antigravity(prompt, chat_id, status_msg_id, work_dir):
    try:
        before_files = {}
        if os.path.exists(work_dir):
            try:
                for fname in os.listdir(work_dir):
                    fpath = os.path.join(work_dir, fname)
                    if os.path.isfile(fpath):
                        before_files[fname] = os.path.getmtime(fpath)
            except Exception:
                pass

        cmd = [
            AGY_BIN,
            "--add-dir", work_dir,
            "--prompt", prompt,
            "--dangerously-skip-permissions"
        ]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=work_dir
        )
        
        output, _ = process.communicate(timeout=300)
        output = output.strip() if output else "✅ Perintah selesai dijalankan."

        clean_out = clean_ai_output(output)

        rel_dir = work_dir.replace("/root", "~")
        result_header = f"🤖 OFFICE AI EXECUTION\n📍 Path: {rel_dir}\n💬 Prompt: {prompt}\n━━━━━━━━━━━━━━━━━━━━━\n\n"
        full_output = result_header + clean_out
        
        edit_message(chat_id, status_msg_id, full_output)

        after_files = {}
        if os.path.exists(work_dir):
            try:
                for fname in os.listdir(work_dir):
                    fpath = os.path.join(work_dir, fname)
                    if os.path.isfile(fpath):
                        after_files[fname] = os.path.getmtime(fpath)
            except Exception:
                pass

        sent_files = set()
        target_exts = [".pdf", ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".csv", ".png", ".jpg"]
        for fname, mtime in after_files.items():
            ext = os.path.splitext(fname)[1].lower()
            if ext in target_exts:
                if fname not in before_files or mtime > (before_files[fname] + 0.01):
                    full_fpath = os.path.join(work_dir, fname)
                    if full_fpath not in sent_files:
                        sent_files.add(full_fpath)
                        send_document(chat_id, full_fpath, caption=f"📄 Hasil Dokumen: {fname}")

    except subprocess.TimeoutExpired:
        process.kill()
        edit_message(chat_id, status_msg_id, "⚠️ Perintah mengalami timeout (melebihi 5 menit).")
    except Exception as e:
        edit_message(chat_id, status_msg_id, f"❌ Terjadi kesalahan saat menjalankan perintah: {str(e)}")

def process_callback_query(cq):
    cq_id = cq["id"]
    chat_id = cq["message"]["chat"]["id"]
    message_id = cq["message"]["message_id"]
    user_id = cq["from"]["id"]
    data = cq.get("data", "")

    owner_id = STATE.get("owner_id")
    if owner_id and user_id != owner_id:
        answer_callback_query(cq_id, "⛔ Akses ditolak.")
        return

    current_cwd = get_user_cwd(user_id)

    if data.startswith("fm_cd:"):
        parts = data.split("fm_cd:", 1)[1].split(":")
        target_key = parts[0]
        page = int(parts[1]) if len(parts) > 1 else 1

        target_dir = decode_path(target_key)
        if set_user_cwd(user_id, target_dir):
            new_cwd = get_user_cwd(user_id)
            text, reply_markup = render_file_manager(user_id, new_cwd, page=page)
            answer_callback_query(cq_id, f"📂 {os.path.basename(new_cwd) or new_cwd} (Hal {page})")
            edit_message(chat_id, message_id, text, reply_markup=reply_markup)
        else:
            answer_callback_query(cq_id, f"❌ Directory tidak ditemukan: {target_dir}", show_alert=True)

    elif data.startswith("fm_folder:"):
        f_key = data.split("fm_folder:", 1)[1]
        folder_path = decode_path(f_key)
        folder_name = os.path.basename(folder_path)
        target_key = encode_path(folder_path)
        parent_key = encode_path(current_cwd)

        answer_callback_query(cq_id, f"📁 {folder_name}")
        
        text = f"📁 FOLDER OPTIONS: {folder_name}\n"
        text += f"━━━━━━━━━━━━━━━━━━━━━\n"
        text += f"📍 Path: {folder_path}\n\n"
        
        btn = {"inline_keyboard": [
            [{"text": "📂 Masuk ke Folder Ini", "callback_data": f"fm_cd:{target_key}:1"}],
            [{"text": "🗑️ Hapus Folder Ini", "callback_data": f"fm_rm_confirm:{target_key}"}],
            [{"text": "🔙 Kembali", "callback_data": f"fm_cd:{parent_key}:1"}]
        ]}
        edit_message(chat_id, message_id, text, reply_markup=btn)

    elif data.startswith("fm_file:"):
        fl_key = data.split("fm_file:", 1)[1]
        file_path = decode_path(fl_key)
        file_name = os.path.basename(file_path)
        ext = os.path.splitext(file_name)[1].lower()
        parent_key = encode_path(current_cwd)

        answer_callback_query(cq_id, f"📄 {file_name}")
        if os.path.exists(file_path) and os.path.isfile(file_path):
            stat = os.stat(file_path)
            size_kb = stat.st_size / 1024
            mtime = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            
            text = f"📄 OFFICE DOKUMEN: {file_name}\n"
            text += f"━━━━━━━━━━━━━━━━━━━━━\n"
            text += f"📌 Nama: {file_name}\n"
            text += f"📍 Path: {file_path}\n"
            text += f"📊 Ukuran: {size_kb:.2f} KB\n"
            text += f"🕒 Modifikasi: {mtime}\n\n"
            
            try:
                res = subprocess.run(["python3", OFFICE_TOOLS, "extract_text", file_path], capture_output=True, text=True)
                snippet = res.stdout[:1200] if res.stdout else "Gagal mengekstrak teks."
                snippet_clean = clean_ai_output(snippet)
                text += f"📝 Pratinjau Isi Teks:\n{snippet_clean}"
            except Exception as e:
                text += f"⚠️ Tidak dapat membaca isi file: {e}"

            btn_list = []
            if ext == ".pdf":
                btn_list.append([{"text": "✍️ Tempel Tanda Tangan / Gambar", "callback_data": f"fm_stamp_prompt:{fl_key}"}])
            if ext in [".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt", ".txt", ".md", ".html"]:
                btn_list.append([{"text": "📕 Convert ke PDF", "callback_data": f"fm_convert_pdf:{fl_key}"}])
            btn_list.append([{"text": "🔍 Extract Text", "callback_data": f"fm_extract_text:{fl_key}"}])
            btn_list.append([{"text": "📥 Download File", "callback_data": f"fm_dl:{fl_key}"}])
            btn_list.append([{"text": "🗑️ Hapus File Ini", "callback_data": f"fm_rm_confirm:{fl_key}"}])
            btn_list.append([{"text": "🔙 Kembali ke File Manager", "callback_data": f"fm_cd:{parent_key}:1"}])

            btn = {"inline_keyboard": btn_list}
            edit_message(chat_id, message_id, text, reply_markup=btn)

    elif data.startswith("fm_stamp_prompt:"):
        fl_key = data.split("fm_stamp_prompt:", 1)[1]
        file_path = decode_path(fl_key)
        file_name = os.path.basename(file_path)
        answer_callback_query(cq_id, "✍️ Tempel Tanda Tangan")
        force_reply = {"force_reply": True, "selective": True}
        send_message(chat_id, f"✍️ TEMPEL TANDA TANGAN / STEMPEL PADA PDF\n\nUpload gambar tanda tangan (PNG/JPG) atau ketik nama file gambar tanda tangan yang ada di `{current_cwd}` untuk ditempelkan pada `{file_name}`:", reply_markup=force_reply)

    elif data.startswith("fm_convert_pdf:"):
        fl_key = data.split("fm_convert_pdf:", 1)[1]
        file_path = decode_path(fl_key)
        answer_callback_query(cq_id, "📕 Mengkonversi ke PDF...")
        send_message(chat_id, f"📕 Mengkonversi {os.path.basename(file_path)} ke PDF...")
        try:
            res = subprocess.run(["python3", OFFICE_TOOLS, "convert_pdf", file_path], capture_output=True, text=True)
            out_pdf = res.stdout.strip()
            if out_pdf and os.path.exists(out_pdf):
                send_document(chat_id, out_pdf, caption=f"📕 Hasil Konversi PDF: {os.path.basename(out_pdf)}")
            else:
                send_message(chat_id, f"❌ Konversi PDF gagal: {res.stderr}")
        except Exception as e:
            send_message(chat_id, f"❌ Error konversi: {e}")

    elif data.startswith("fm_extract_text:"):
        fl_key = data.split("fm_extract_text:", 1)[1]
        file_path = decode_path(fl_key)
        answer_callback_query(cq_id, "🔍 Mengekstrak Teks...")
        try:
            res = subprocess.run(["python3", OFFICE_TOOLS, "extract_text", file_path], capture_output=True, text=True)
            extracted = res.stdout or "Tidak ada teks yang dapat diekstrak."
            extracted_clean = clean_ai_output(extracted)
            send_message(chat_id, f"🔍 HASIL EKSTRAKSI TEKS ({os.path.basename(file_path)}):\n━━━━━━━━━━━━━━━━━━━━━\n{extracted_clean[:3800]}")
        except Exception as e:
            send_message(chat_id, f"❌ Error ekstraksi: {e}")

    elif data.startswith("fm_dl:"):
        fl_key = data.split("fm_dl:", 1)[1]
        file_path = decode_path(fl_key)
        answer_callback_query(cq_id, "📥 Mengirim file...")
        send_document(chat_id, file_path, caption=f"📄 {os.path.basename(file_path)}")

    elif data.startswith("fm_rm_confirm:"):
        item_key = data.split("fm_rm_confirm:", 1)[1]
        target_path = decode_path(item_key)
        name = os.path.basename(target_path)
        is_dir = os.path.isdir(target_path)
        item_type = "Folder" if is_dir else "File"
        parent_key = encode_path(current_cwd)

        answer_callback_query(cq_id, "⚠️ Konfirmasi Hapus", show_alert=True)
        text = f"⚠️ KONFIRMASI HAPUS {item_type.upper()}\n"
        text += f"Apakah kamu yakin ingin menghapus {item_type} ini secara permanen?\n\n"
        text += f"📌 Nama: {name}\n"
        text += f"📍 Path: {target_path}"
        
        btn = {"inline_keyboard": [
            [{"text": f"🔥 YA, Hapus {item_type}", "callback_data": f"fm_rm_do:{item_key}"}],
            [{"text": "❌ Batal", "callback_data": f"fm_cd:{parent_key}:1"}]
        ]}
        edit_message(chat_id, message_id, text, reply_markup=btn)

    elif data.startswith("fm_rm_do:"):
        item_key = data.split("fm_rm_do:", 1)[1]
        target_path = decode_path(item_key)
        name = os.path.basename(target_path)
        notice = ""
        try:
            if os.path.isdir(target_path):
                shutil.rmtree(target_path)
            elif os.path.exists(target_path):
                os.remove(target_path)
            notice = f"🔥 Item {name} telah dihapus."
            answer_callback_query(cq_id, f"✅ {name} dihapus!", show_alert=True)
        except Exception as e:
            notice = f"❌ Gagal menghapus: {e}"
            answer_callback_query(cq_id, f"❌ Gagal menghapus: {e}", show_alert=True)
        
        msg_text, reply_markup = render_file_manager(user_id, current_cwd, page=1, notice=notice)
        edit_message(chat_id, message_id, msg_text, reply_markup=reply_markup)

    elif data.startswith("fm_action:"):
        action = data.split("fm_action:", 1)[1]
        if action == "noop":
            answer_callback_query(cq_id)
        elif action == "toggle_hidden":
            new_state = toggle_show_hidden(user_id)
            state_str = "ditampilkan" if new_state else "disembunyikan"
            answer_callback_query(cq_id, f"👁️ File System {state_str}!")
            msg_text, reply_markup = render_file_manager(user_id, current_cwd, page=1)
            edit_message(chat_id, message_id, text, reply_markup=reply_markup)
        elif action == "do_backup":
            answer_callback_query(cq_id, "📦 Mengirim Backup VPS...")
            send_message(chat_id, "📦 Sedang membuat file backup VPS dan mengirim ke Telegram...")
            subprocess.Popen(["/root/backup_vps.sh"], cwd="/root")
        elif action == "create_folder_prompt":
            answer_callback_query(cq_id, "Ketik nama folder baru...")
            force_reply = {"force_reply": True, "selective": True}
            send_message(chat_id, f"📁 BUAT FOLDER BARU\n\nKetik nama folder baru yang ingin dibuat di {current_cwd}:", reply_markup=force_reply)
        elif action == "create_file_prompt":
            answer_callback_query(cq_id, "Ketik nama file baru...")
            force_reply = {"force_reply": True, "selective": True}
            send_message(chat_id, f"📝 BUAT FILE BARU\n\nKetik nama file baru yang ingin dibuat di {current_cwd} (misal: laporan.docx atau data.xlsx):", reply_markup=force_reply)

def process_update(update):
    if "callback_query" in update:
        process_callback_query(update["callback_query"])
        return

    message = update.get("message")
    if not message:
        return

    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    username = message["from"].get("username", "Unknown")

    owner_id = STATE.get("owner_id")

    if owner_id is None:
        STATE["owner_id"] = user_id
        STATE["owner_username"] = username
        save_state(STATE)
        owner_id = user_id
        send_message(
            chat_id,
            f"🔐 Bot Registered!\nUser {user_id} (@{username}) terdaftar sebagai owner."
        )

    if user_id != owner_id:
        send_message(chat_id, f"⛔ Maaf, kamu tidak memiliki akses. (ID: {user_id})")
        return

    current_cwd = get_user_cwd(user_id)

    # Check for ForceReply (Interactive Folder/File creation or PDF Stamping)
    reply_to = message.get("reply_to_message")
    if reply_to and "text" in reply_to:
        reply_text = reply_to["text"]
        user_input_name = message.get("text", "").strip()

        if "BUAT FOLDER BARU" in reply_text and user_input_name:
            new_folder_path = os.path.join(current_cwd, user_input_name)
            try:
                os.makedirs(new_folder_path, exist_ok=True)
                set_user_cwd(user_id, new_folder_path)
                msg_text, reply_markup = render_file_manager(user_id, new_folder_path, page=1, notice=f"✅ Folder {user_input_name} berhasil dibuat!")
                send_message(chat_id, msg_text, reply_markup=reply_markup)
            except Exception as e:
                send_message(chat_id, f"❌ Gagal membuat folder: {e}")
            return

        if "BUAT FILE BARU" in reply_text and user_input_name:
            new_file_path = os.path.join(current_cwd, user_input_name)
            try:
                with open(new_file_path, "a") as f:
                    pass
                msg_text, reply_markup = render_file_manager(user_id, current_cwd, page=1, notice=f"✅ File {user_input_name} berhasil dibuat!")
                send_message(chat_id, msg_text, reply_markup=reply_markup)
            except Exception as e:
                send_message(chat_id, f"❌ Gagal membuat file: {e}")
            return

        if "TEMPEL TANDA TANGAN" in reply_text:
            # Extract PDF name from prompt message
            match = re.search(r'pada `(.*?)`:', reply_text)
            pdf_filename = match.group(1) if match else None
            if pdf_filename:
                pdf_path = os.path.join(current_cwd, pdf_filename)
                img_path = os.path.join(current_cwd, user_input_name) if not user_input_name.startswith("/") else user_input_name
                
                # Check if photo was uploaded in reply
                if "photo" in message:
                    photo = message["photo"][-1]
                    img_path = os.path.join(current_cwd, "signature_temp.png")
                    res = api_request("getFile", {"file_id": photo["file_id"]})
                    if res and res.get("ok"):
                        urllib.request.urlretrieve(f"https://api.telegram.org/file/bot{TOKEN}/{res['result']['file_path']}", img_path)

                if os.path.exists(pdf_path) and os.path.exists(img_path):
                    send_message(chat_id, f"✍️ Menempelkan tanda tangan `{os.path.basename(img_path)}` ke `{pdf_filename}`...")
                    try:
                        res = subprocess.run(["python3", OFFICE_TOOLS, "stamp_pdf", pdf_path, img_path], capture_output=True, text=True)
                        out_pdf = res.stdout.strip()
                        if out_pdf and os.path.exists(out_pdf):
                            send_document(chat_id, out_pdf, caption=f"✍️ Dokumen PDF Ter-Tanda Tangan: {os.path.basename(out_pdf)}")
                        else:
                            send_message(chat_id, f"❌ Gagal menempelkan tanda tangan: {res.stderr}")
                    except Exception as e:
                        send_message(chat_id, f"❌ Error penempelan tanda tangan: {e}")
                else:
                    send_message(chat_id, f"❌ Gambar tanda tangan `{user_input_name}` tidak ditemukan di `{current_cwd}`.")
            return

    # Handle Photo/Image Uploads
    if "photo" in message:
        photo = message["photo"][-1]
        file_id = photo["file_id"]
        caption_text = message.get("caption", "").strip()
        img_filename = f"image_{int(time.time())}.png"
        target_path = os.path.join(current_cwd, img_filename)

        res = api_request("getFile", {"file_id": file_id})
        if res and res.get("ok"):
            file_rel_path = res["result"]["file_path"]
            dl_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_rel_path}"
            try:
                urllib.request.urlretrieve(dl_url, target_path)

                if caption_text:
                    full_prompt = f"Gambar '{img_filename}' telah diupload ke direktori '{current_cwd}'. Instruksi pengguna: {caption_text}. Silakan olah gambar atau tempelkan gambar ini ke PDF sesuai instruksi."
                    res_msg = send_message(chat_id, f"🤖 Antigravity memproses gambar {img_filename}...\n💬 Instruksi: {caption_text}")
                    if res_msg and len(res_msg) > 0:
                        status_msg_id = res_msg[0]["message_id"]
                        t = threading.Thread(target=execute_antigravity, args=(full_prompt, chat_id, status_msg_id, current_cwd))
                        t.start()
                    return

                send_message(chat_id, f"🖼️ GAMBAR DITERIMA: `{img_filename}`\n📍 Saved to: `{target_path}`\n\n💡 Tip: Kamu bisa upload gambar tanda tangan/logo dan minta AI tempelkan ke file PDF pilihanmu!")
            except Exception as e:
                send_message(chat_id, f"❌ Gagal mengunduh gambar: {e}")
        return

    # Handle Document Uploads (with optional Caption Instruction!)
    if "document" in message:
        doc = message["document"]
        file_id = doc["file_id"]
        file_name = doc.get("file_name", "uploaded_file")
        caption_text = message.get("caption", "").strip()
        target_path = os.path.join(current_cwd, file_name)
        ext = os.path.splitext(file_name)[1].lower()

        res = api_request("getFile", {"file_id": file_id})
        if res and res.get("ok"):
            file_rel_path = res["result"]["file_path"]
            dl_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_rel_path}"
            try:
                urllib.request.urlretrieve(dl_url, target_path)

                if caption_text:
                    full_prompt = f"File '{file_name}' telah diupload ke direktori '{current_cwd}'. Instruksi pengguna: {caption_text}. Silakan edit atau proses file '{file_name}' sesuai instruksi tersebut."
                    res_msg = send_message(chat_id, f"🤖 Antigravity mengedit file {file_name} sesuai instruksi...\n💬 Instruksi: {caption_text}")
                    if res_msg and len(res_msg) > 0:
                        status_msg_id = res_msg[0]["message_id"]
                        t = threading.Thread(target=execute_antigravity, args=(full_prompt, chat_id, status_msg_id, current_cwd))
                        t.start()
                    return

                fl_key = encode_path(target_path)
                btn_list = []
                if ext == ".pdf":
                    btn_list.append([{"text": "✍️ Tempel Tanda Tangan / Stempel", "callback_data": f"fm_stamp_prompt:{fl_key}"}])
                if ext in [".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt", ".txt", ".md", ".csv"]:
                    btn_list.append([{"text": "📕 Convert ke PDF", "callback_data": f"fm_convert_pdf:{fl_key}"}])
                btn_list.append([{"text": "🔍 Extract Text / Data", "callback_data": f"fm_extract_text:{fl_key}"}])
                parent_key = encode_path(current_cwd)
                btn_list.append([{"text": "🔙 Buka di File Manager", "callback_data": f"fm_cd:{parent_key}:1"}])

                reply_markup = {"inline_keyboard": btn_list}
                send_message(chat_id, f"📥 DOKUMEN DITERIMA: {file_name}\n📍 Saved to: {target_path}\n\n💡 Tip: Kamu bisa upload dokumen sambil memberikan instruksi di Caption, atau kirim chat perintah setelah ini untuk mengedit file {file_name}.", reply_markup=reply_markup)
            except Exception as e:
                send_message(chat_id, f"❌ Gagal mengunduh file: {e}")
        return

    if "text" not in message:
        return

    text = message["text"].strip()

    if text in ["/start", "/fm", "/ls", "/browse"]:
        msg_text, reply_markup = render_file_manager(user_id, current_cwd, page=1)
        send_message(chat_id, msg_text, reply_markup=reply_markup)
        return

    if text in ["/backup", "/backupvps"]:
        send_message(chat_id, "📦 Sedang membuat file backup VPS dan mengirim ke Telegram...")
        subprocess.Popen(["/root/backup_vps.sh"], cwd="/root")
        return

    if text.startswith("/cd "):
        target_dir = text[4:].strip()
        if not target_dir.startswith("/"):
            target_dir = os.path.join(current_cwd, target_dir)
        if set_user_cwd(user_id, target_dir):
            new_cwd = get_user_cwd(user_id)
            msg_text, reply_markup = render_file_manager(user_id, new_cwd, page=1)
            send_message(chat_id, msg_text, reply_markup=reply_markup)
        else:
            send_message(chat_id, f"❌ Directory tidak ditemukan: {target_dir}")
        return

    if text == "/pwd":
        send_message(chat_id, f"📍 Current Working Directory: {current_cwd}")
        return

    # /mkdir <folder_name>
    if text.startswith("/mkdir "):
        folder_name = text[7:].strip()
        new_path = os.path.join(current_cwd, folder_name)
        try:
            os.makedirs(new_path, exist_ok=True)
            set_user_cwd(user_id, new_path)
            msg_text, reply_markup = render_file_manager(user_id, new_path, page=1, notice=f"✅ Folder {folder_name} berhasil dibuat!")
            send_message(chat_id, msg_text, reply_markup=reply_markup)
        except Exception as e:
            send_message(chat_id, f"❌ Gagal membuat folder: {e}")
        return

    # /touch <file_name>
    if text.startswith("/touch "):
        file_name = text[7:].strip()
        new_path = os.path.join(current_cwd, file_name)
        try:
            with open(new_path, "a") as f:
                pass
            msg_text, reply_markup = render_file_manager(user_id, current_cwd, page=1, notice=f"✅ File {file_name} berhasil dibuat!")
            send_message(chat_id, msg_text, reply_markup=reply_markup)
        except Exception as e:
            send_message(chat_id, f"❌ Gagal membuat file: {e}")
        return

    # /rm <item_name>
    if text.startswith("/rm "):
        item_name = text[4:].strip()
        target_path = os.path.join(current_cwd, item_name) if not item_name.startswith("/") else item_name
        try:
            if os.path.isdir(target_path):
                shutil.rmtree(target_path)
                notice = f"🔥 Folder {item_name} berhasil dihapus!"
            elif os.path.exists(target_path):
                os.remove(target_path)
                notice = f"🔥 File {item_name} berhasil dihapus!"
            else:
                notice = f"❌ {item_name} tidak ditemukan."
            msg_text, reply_markup = render_file_manager(user_id, current_cwd, page=1, notice=notice)
            send_message(chat_id, msg_text, reply_markup=reply_markup)
        except Exception as e:
            send_message(chat_id, f"❌ Gagal menghapus: {e}")
        return

    # /rename <old_name> <new_name>
    if text.startswith("/rename "):
        parts = text[8:].strip().split()
        if len(parts) >= 2:
            old_name, new_name = parts[0], parts[1]
            old_path = os.path.join(current_cwd, old_name) if not old_name.startswith("/") else old_name
            new_path = os.path.join(current_cwd, new_name) if not new_name.startswith("/") else new_name
            try:
                os.rename(old_path, new_path)
                msg_text, reply_markup = render_file_manager(user_id, current_cwd, page=1, notice=f"✏️ Renamed {old_name} ➔ {new_name}")
                send_message(chat_id, msg_text, reply_markup=reply_markup)
            except Exception as e:
                send_message(chat_id, f"❌ Gagal rename: {e}")
        else:
            send_message(chat_id, "ℹ️ Format: /rename nama_lama nama_baru")
        return

    # /download <file_name>
    if text.startswith("/download "):
        file_name = text[10:].strip()
        target_file = os.path.join(current_cwd, file_name) if not file_name.startswith("/") else file_name
        send_document(chat_id, target_file, caption=f"📄 {os.path.basename(target_file)}")
        return

    # /exec <bash_command>
    if text.startswith("/exec "):
        cmd_str = text[6:].strip()
        try:
            res = subprocess.run(cmd_str, shell=True, capture_output=True, text=True, cwd=current_cwd, timeout=60)
            out = res.stdout or res.stderr or "✅ Perintah selesai (tanpa output)."
            out_clean = clean_ai_output(out)
            send_message(chat_id, f"💻 BASH EXECUTION:\n{cmd_str}\n━━━━━━━━━━━━━━━━━━━━━\n{out_clean[:3800]}")
        except Exception as e:
            send_message(chat_id, f"❌ Exec error: {e}")
        return

    # Regular prompt -> Run AGY with PDF Stamping & Office capabilities!
    res_msg = send_message(chat_id, f"🤖 Antigravity memproses perintah...\n📍 cwd: {current_cwd}")
    if res_msg and len(res_msg) > 0:
        status_msg_id = res_msg[0]["message_id"]
        t = threading.Thread(target=execute_antigravity, args=(text, chat_id, status_msg_id, current_cwd))
        t.start()

def main():
    print("🚀 Antigravity Telegram Office CLI & Agent Active...")
    print("Bot Username: @Kontrolagybot")

    offset = 0
    while True:
        try:
            updates = api_request("getUpdates", {"offset": offset, "timeout": 30})
            if updates and updates.get("ok"):
                for update in updates.get("result", []):
                    offset = update["update_id"] + 1
                    process_update(update)
        except Exception as e:
            print(f"Polling loop error: {e}", file=sys.stderr)
            time.sleep(3)

if __name__ == "__main__":
    main()
