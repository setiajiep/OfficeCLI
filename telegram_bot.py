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
import psutil
import speech_recognition as sr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def load_env_file():
    env_path = "/root/.env"
    if os.path.exists(env_path):
        try:
            with open(env_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        v = v.strip("\"'")
                        os.environ[k.strip()] = v
        except Exception:
            pass

load_env_file()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN_HERE")
BASE_URL = f"https://api.telegram.org/bot{TOKEN}/"
AGY_BIN = "/root/.local/bin/agy"
OFFICE_TOOLS = "/root/office_tools.py"
IMAGE_TOOLS = "/root/image_tools.py"

STATE_FILE = "/root/.antigravity_bot_state.json"
FILES_PER_PAGE = 8
HTTP_PORT = 8080
DOWNLOADS_DIR = "/root/MyProject/downloads"
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

def get_public_ip():
    try:
        req = urllib.request.Request("https://ifconfig.me", headers={'User-Agent': 'curl/7.68.0'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.read().decode('utf-8').strip()
    except Exception:
        try:
            req = urllib.request.Request("https://api.ipify.org", headers={'User-Agent': 'curl/7.68.0'})
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.read().decode('utf-8').strip()
        except Exception:
            return "188.166.228.142"

VPS_IP = get_public_ip()

def start_http_server():
    from http.server import HTTPServer, SimpleHTTPRequestHandler
    class QuietHTTPHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=DOWNLOADS_DIR, **kwargs)
        def log_message(self, format, *args):
            pass

    try:
        server = HTTPServer(('0.0.0.0', HTTP_PORT), QuietHTTPHandler)
        print(f"🌐 HTTP File Server active on http://{VPS_IP}:{HTTP_PORT}")
        server.serve_forever()
    except Exception as e:
        print(f"HTTP Server error: {e}", file=sys.stderr)

def cleanup_old_downloads():
    while True:
        try:
            now = time.time()
            if os.path.exists(DOWNLOADS_DIR):
                for f in os.listdir(DOWNLOADS_DIR):
                    fpath = os.path.join(DOWNLOADS_DIR, f)
                    if os.path.isfile(fpath):
                        if (now - os.path.getmtime(fpath)) > 86400:
                            os.remove(fpath)
        except Exception:
            pass
        time.sleep(3600)

def create_download_link(file_path):
    os.makedirs(DOWNLOADS_DIR, exist_ok=True)
    filename = os.path.basename(file_path)
    dest_path = os.path.join(DOWNLOADS_DIR, filename)
    if file_path != dest_path and os.path.exists(file_path):
        shutil.copy2(file_path, dest_path)
    
    encoded_name = urllib.parse.quote(filename)
    link = f"http://{VPS_IP}:{HTTP_PORT}/{encoded_name}"
    return link, dest_path

# Path encoder to ensure Telegram 64-byte callback_data limit is never exceeded
PATH_MAP = {}
PATH_COUNTER = 0

def encode_path(path):
    global PATH_COUNTER, PATH_MAP
    abs_path = os.path.abspath(path)
    for k, v in PATH_MAP.items():
        if v == abs_path:
            return k
    if len(PATH_MAP) > 3000:
        PATH_MAP = {"p1": "/root", "p2": "/root/MyProject"}
        PATH_COUNTER = 2
        if abs_path == "/root":
            return "p1"
        if abs_path == "/root/MyProject":
            return "p2"
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

def get_session_mode(user_id):
    str_id = str(user_id)
    return STATE.get("session_modes", {}).get(str_id, "continue")

def toggle_session_mode(user_id):
    str_id = str(user_id)
    if "session_modes" not in STATE:
        STATE["session_modes"] = {}
    current = STATE["session_modes"].get(str_id, "continue")
    new_mode = "new" if current == "continue" else "continue"
    STATE["session_modes"][str_id] = new_mode
    save_state(STATE)
    return new_mode

def set_user_session_id(user_id, session_id):
    str_id = str(user_id)
    if "session_modes" not in STATE:
        STATE["session_modes"] = {}
    STATE["session_modes"][str_id] = session_id
    save_state(STATE)

def clean_transcript_text(text):
    if not text:
        return ""
    text = re.sub(r'<ADDITIONAL_METADATA>.*?</ADDITIONAL_METADATA>', '', text, flags=re.DOTALL)
    text = re.sub(r'<SYSTEM_MESSAGE>.*?</SYSTEM_MESSAGE>', '', text, flags=re.DOTALL)
    text = re.sub(r'<USER_SETTINGS_CHANGE>.*?</USER_SETTINGS_CHANGE>', '', text, flags=re.DOTALL)
    text = re.sub(r'</?[a-zA-Z_0-9]+[^>]*>', '', text)
    text = re.sub(r'[\r\n]+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def get_recent_sessions(limit=50):
    brain_dir = "/root/.gemini/antigravity-cli/brain"
    sessions = []
    if not os.path.exists(brain_dir):
        return []
    try:
        entries = []
        for cid in os.listdir(brain_dir):
            cpath = os.path.join(brain_dir, cid)
            if os.path.isdir(cpath) and len(cid) > 25:
                mtime = os.path.getmtime(cpath)
                entries.append((cid, mtime, cpath))
        entries.sort(key=lambda x: x[1], reverse=True)
        
        for cid, mtime, cpath in entries[:limit]:
            topic = "Sesi Obrolan Tanpa Judul"
            msg_count = 0
            transcript_file = os.path.join(cpath, ".system_generated", "logs", "transcript.jsonl")
            if os.path.exists(transcript_file):
                try:
                    with open(transcript_file, "r") as f:
                        for line in f:
                            if '"USER_INPUT"' in line:
                                msg_count += 1
                                if topic == "Sesi Obrolan Tanpa Judul":
                                    data = json.loads(line)
                                    content = data.get("content", "")
                                    if content:
                                        cleaned = clean_transcript_text(content)
                                        if cleaned:
                                            topic = cleaned[:85]
                except Exception:
                    pass
            date_str = datetime.fromtimestamp(mtime).strftime("%d/%m %H:%M")
            sessions.append({
                "id": cid,
                "date": date_str,
                "topic": topic,
                "msg_count": msg_count if msg_count > 0 else 1
            })
    except Exception as e:
        print(f"Error fetching sessions: {e}")
    return sessions

SESSIONS_PER_PAGE = 5

def render_session_picker(page=1):
    all_sessions = get_recent_sessions(limit=50)
    if not all_sessions:
        return "📜 Belum ada riwayat sesi percakapan yang tersimpan.", {"inline_keyboard": []}

    total_sessions = len(all_sessions)
    total_pages = max(1, (total_sessions + SESSIONS_PER_PAGE - 1) // SESSIONS_PER_PAGE)
    page = max(1, min(page, total_pages))

    start_idx = (page - 1) * SESSIONS_PER_PAGE
    end_idx = start_idx + SESSIONS_PER_PAGE
    page_sessions = all_sessions[start_idx:end_idx]

    text = f"📜 *DAFTAR SESI PERCAKAPAN RIWAYAT*\n"
    text += f"━━━━━━━━━━━━━━━━━━━━━\n"
    text += f"📊 Total: {total_sessions} Sesi | Halaman {page}/{total_pages}\n\n"

    btns = []
    for idx, s in enumerate(page_sessions, start=start_idx + 1):
        text += f"*{idx}. 🕒 {s['date']}* ({s['msg_count']} pesan)\n"
        text += f"   💬 `\"{s['topic']}\"`\n"
        text += f"   🆔 ID: `{s['id'][:13]}...`\n\n"
        
        btn_label = f"🔖 {idx}. {s['topic'][:25]}... ({s['date']})"
        btns.append([{"text": btn_label, "callback_data": f"fm_action:pick_session:{s['id']}"}])

    if total_pages > 1:
        pag_row = []
        if page > 1:
            pag_row.append({"text": "◀️ Prev", "callback_data": f"fm_action:list_sessions:{page-1}"})
        pag_row.append({"text": f"📄 {page}/{total_pages}", "callback_data": "fm_action:noop"})
        if page < total_pages:
            pag_row.append({"text": "Next ▶️", "callback_data": f"fm_action:list_sessions:{page+1}"})
        btns.append(pag_row)

    btns.append([
        {"text": "💬 Sesi Lanjut Default", "callback_data": "fm_action:pick_session:continue"},
        {"text": "🆕 Sesi Baru", "callback_data": "fm_action:pick_session:new"}
    ])

    reply_markup = {"inline_keyboard": btns}
    return text, reply_markup

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
    if not os.path.exists(file_path):
        send_message(chat_id, f"❌ File {file_path} tidak ditemukan.")
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendDocument"
    filename = os.path.basename(file_path)
    
    # Native Python Multipart Request
    try:
        boundary = '----WebKitFormBoundary' + hex(int(time.time() * 1000))[2:]
        body = bytearray()
        
        # chat_id field
        body.extend(f'--{boundary}\r\n'.encode('utf-8'))
        body.extend(f'Content-Disposition: form-data; name="chat_id"\r\n\r\n{chat_id}\r\n'.encode('utf-8'))
        
        # caption field
        if caption:
            body.extend(f'--{boundary}\r\n'.encode('utf-8'))
            body.extend(f'Content-Disposition: form-data; name="caption"\r\n\r\n{caption}\r\n'.encode('utf-8'))
            
        # document field
        body.extend(f'--{boundary}\r\n'.encode('utf-8'))
        body.extend(f'Content-Disposition: form-data; name="document"; filename="{filename}"\r\n'.encode('utf-8'))
        body.extend(b'Content-Type: application/octet-stream\r\n\r\n')
        with open(file_path, 'rb') as f:
            body.extend(f.read())
        body.extend(b'\r\n')
        body.extend(f'--{boundary}--\r\n'.encode('utf-8'))
        
        req = urllib.request.Request(url, data=bytes(body), headers={'Content-Type': f'multipart/form-data; boundary={boundary}'})
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        print(f"Native multipart upload failed ({e}), trying fallback curl...", file=sys.stderr)
        try:
            cmd = ["curl", "-s", "-F", f"chat_id={chat_id}", "-F", f"document=@{file_path}"]
            if caption:
                cmd.extend(["-F", f"caption={caption}"])
            cmd.append(url)
            subprocess.run(cmd, check=True)
        except Exception as ex:
            send_message(chat_id, f"❌ Gagal mengirim document: {ex}")

def send_photo(chat_id, photo_path, caption=None):
    if not os.path.exists(photo_path):
        send_message(chat_id, f"❌ File photo {photo_path} tidak ditemukan.")
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    filename = os.path.basename(photo_path)
    try:
        boundary = '----WebKitFormBoundary' + hex(int(time.time() * 1000))[2:]
        body = bytearray()
        
        body.extend(f'--{boundary}\r\n'.encode('utf-8'))
        body.extend(f'Content-Disposition: form-data; name="chat_id"\r\n\r\n{chat_id}\r\n'.encode('utf-8'))
        
        if caption:
            body.extend(f'--{boundary}\r\n'.encode('utf-8'))
            body.extend(f'Content-Disposition: form-data; name="caption"\r\n\r\n{caption}\r\n'.encode('utf-8'))
            
        body.extend(f'--{boundary}\r\n'.encode('utf-8'))
        body.extend(f'Content-Disposition: form-data; name="photo"; filename="{filename}"\r\n'.encode('utf-8'))
        body.extend(b'Content-Type: image/png\r\n\r\n')
        with open(photo_path, 'rb') as f:
            body.extend(f.read())
        body.extend(b'\r\n')
        body.extend(f'--{boundary}--\r\n'.encode('utf-8'))
        
        req = urllib.request.Request(url, data=bytes(body), headers={'Content-Type': f'multipart/form-data; boundary={boundary}'})
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        print(f"Native photo upload failed ({e}), fallback to curl...", file=sys.stderr)
        try:
            cmd = ["curl", "-s", "-F", f"chat_id={chat_id}", "-F", f"photo=@{photo_path}"]
            if caption:
                cmd.extend(["-F", f"caption={caption}"])
            cmd.append(url)
            subprocess.run(cmd, check=True)
        except Exception as ex:
            send_message(chat_id, f"❌ Gagal mengirim foto: {ex}")

def send_video(chat_id, video_path, caption=None):
    if not os.path.exists(video_path):
        send_message(chat_id, f"❌ File video {video_path} tidak ditemukan.")
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendVideo"
    filename = os.path.basename(video_path)
    try:
        boundary = '----WebKitFormBoundary' + hex(int(time.time() * 1000))[2:]
        body = bytearray()
        body.extend(f'--{boundary}\r\n'.encode('utf-8'))
        body.extend(f'Content-Disposition: form-data; name="chat_id"\r\n\r\n{chat_id}\r\n'.encode('utf-8'))
        if caption:
            body.extend(f'--{boundary}\r\n'.encode('utf-8'))
            body.extend(f'Content-Disposition: form-data; name="caption"\r\n\r\n{caption}\r\n'.encode('utf-8'))
        body.extend(f'--{boundary}\r\n'.encode('utf-8'))
        body.extend(f'Content-Disposition: form-data; name="video"; filename="{filename}"\r\n'.encode('utf-8'))
        body.extend(b'Content-Type: video/mp4\r\n\r\n')
        with open(video_path, 'rb') as f:
            body.extend(f.read())
        body.extend(b'\r\n')
        body.extend(f'--{boundary}--\r\n'.encode('utf-8'))
        
        req = urllib.request.Request(url, data=bytes(body), headers={'Content-Type': f'multipart/form-data; boundary={boundary}'})
        with urllib.request.urlopen(req, timeout=300) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        print(f"Native video upload failed ({e}), fallback to send_document...", file=sys.stderr)
        return send_document(chat_id, video_path, caption=caption)

def send_audio(chat_id, audio_path, caption=None):
    if not os.path.exists(audio_path):
        send_message(chat_id, f"❌ File audio {audio_path} tidak ditemukan.")
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendAudio"
    filename = os.path.basename(audio_path)
    try:
        boundary = '----WebKitFormBoundary' + hex(int(time.time() * 1000))[2:]
        body = bytearray()
        body.extend(f'--{boundary}\r\n'.encode('utf-8'))
        body.extend(f'Content-Disposition: form-data; name="chat_id"\r\n\r\n{chat_id}\r\n'.encode('utf-8'))
        if caption:
            body.extend(f'--{boundary}\r\n'.encode('utf-8'))
            body.extend(f'Content-Disposition: form-data; name="caption"\r\n\r\n{caption}\r\n'.encode('utf-8'))
        body.extend(f'--{boundary}\r\n'.encode('utf-8'))
        body.extend(f'Content-Disposition: form-data; name="audio"; filename="{filename}"\r\n'.encode('utf-8'))
        body.extend(b'Content-Type: audio/mpeg\r\n\r\n')
        with open(audio_path, 'rb') as f:
            body.extend(f.read())
        body.extend(b'\r\n')
        body.extend(f'--{boundary}--\r\n'.encode('utf-8'))
        
        req = urllib.request.Request(url, data=bytes(body), headers={'Content-Type': f'multipart/form-data; boundary={boundary}'})
        with urllib.request.urlopen(req, timeout=300) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        print(f"Native audio upload failed ({e}), fallback to send_document...", file=sys.stderr)
        return send_document(chat_id, audio_path, caption=caption)

def generate_system_chart():
    try:
        plt.style.use('dark_background')
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5), dpi=150)
        fig.patch.set_facecolor('#0f172a')
        
        mem = psutil.virtual_memory()
        used_gb = mem.used / (1024**3)
        free_gb = mem.available / (1024**3)
        
        ax1.set_facecolor('#0f172a')
        ax1.pie(
            [used_gb, free_gb],
            labels=['Used RAM', 'Free RAM'],
            colors=['#ff4757', '#2ed573'],
            autopct='%1.1f%%',
            startangle=140,
            textprops=dict(color="w", weight="bold")
        )
        ax1.set_title(f"RAM Usage ({mem.used/(1024**2):.0f}MB / {mem.total/(1024**2):.0f}MB)", color="cyan", fontsize=12, fontweight='bold')
        
        disk = psutil.disk_usage('/root')
        d_used = disk.used / (1024**3)
        d_free = disk.free / (1024**3)
        
        ax2.set_facecolor('#0f172a')
        bars = ax2.bar(['Used GB', 'Free GB'], [d_used, d_free], color=['#ffa500', '#1e90ff'], width=0.5)
        ax2.set_ylabel("Gigabytes (GB)", color="w")
        ax2.set_title(f"Disk Storage ({disk.total/(1024**3):.1f} GB Total)", color="#00f2fe", fontsize=12, fontweight='bold')
        ax2.tick_params(colors='w')
        
        for bar in bars:
            yval = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2.0, yval / 2, f"{yval:.1f} GB", ha='center', va='center', color='white', fontweight='bold')
            
        plt.tight_layout()
        chart_path = "/tmp/vps_system_chart.png"
        plt.savefig(chart_path, facecolor=fig.get_facecolor(), edgecolor='none')
        plt.close()
        return chart_path
    except Exception as e:
        print(f"Chart generation error: {e}")
        return None

def get_top_processes(limit=8):
    try:
        procs = []
        for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'username']):
            try:
                info = p.info
                mem_mb = info['memory_info'].rss / (1024 * 1024) if info['memory_info'] else 0
                procs.append({
                    'pid': info['pid'],
                    'name': info['name'] or 'unknown',
                    'cpu': info['cpu_percent'] or 0.0,
                    'mem_mb': mem_mb,
                    'user': info['username'] or 'root'
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        procs.sort(key=lambda x: x['mem_mb'], reverse=True)
        return procs[:limit]
    except Exception as e:
        print(f"Top procs error: {e}")
        return []

def transcribe_voice_note(ogg_path):
    try:
        wav_path = ogg_path.replace(".ogg", ".wav")
        subprocess.run(["ffmpeg", "-y", "-i", ogg_path, "-ar", "16000", "-ac", "1", wav_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        
        r = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio = r.record(source)
            
        try:
            text = r.recognize_google(audio, language="id-ID")
        except Exception:
            text = r.recognize_google(audio, language="en-US")
            
        if os.path.exists(wav_path):
            os.remove(wav_path)
            
        return text.strip()
    except Exception as e:
        print(f"Voice STT Error: {e}")
        return None

def read_web_page(url):
    try:
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url
            
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            
        title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
        title = title_match.group(1).strip() if title_match else url
        
        body = re.sub(r'<(script|style|svg|header|footer|nav)[^>]*>.*?</\1>', '', html, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'<[^>]+>', ' ', body)
        text = re.sub(r'\s+', ' ', text).strip()
        
        return f"🌐 *{clean_ai_output(title)}*\n📍 URL: {url}\n━━━━━━━━━━━━━━━━━━━━━\n{clean_ai_output(text[:3500])}"
    except Exception as e:
        return f"❌ Gagal membaca URL {url}: {e}"

def get_services_status():
    services = ["antigravity-bot", "nginx", "docker", "ssh", "cron"]
    status_list = []
    for s in services:
        try:
            res = subprocess.run(["systemctl", "is-active", s], capture_output=True, text=True)
            state = res.stdout.strip()
            icon = "🟢 Active" if state == "active" else "🔴 Inactive"
            status_list.append({"name": s, "state": state, "icon": icon})
        except Exception:
            pass
    return status_list

SYSTEM_FILES = ["telegram_bot.py", "office_tools.py", "image_tools.py", "setup.sh", "backup_vps.sh", "git_backup.sh", "restore.sh", "antigravity-bot.service"]

def get_disk_free_gb(path="/root"):
    try:
        total, used, free = shutil.disk_usage(path)
        return free / (1024 ** 3)
    except Exception:
        return 0.0

def get_system_status():
    """Retrieve detailed real-time VPS metrics"""
    status = {}
    try:
        # Disk usage
        total, used, free = shutil.disk_usage("/root")
        status["disk_total_gb"] = total / (1024 ** 3)
        status["disk_used_gb"] = used / (1024 ** 3)
        status["disk_free_gb"] = free / (1024 ** 3)
        status["disk_percent"] = (used / total) * 100

        # Memory usage
        with open("/proc/meminfo", "r") as f:
            meminfo = f.read()
        mem_total = 0
        mem_available = 0
        for line in meminfo.splitlines():
            if line.startswith("MemTotal:"):
                mem_total = int(line.split()[1]) / 1024
            elif line.startswith("MemAvailable:"):
                mem_available = int(line.split()[1]) / 1024
        mem_used = mem_total - mem_available
        status["mem_total_mb"] = mem_total
        status["mem_used_mb"] = mem_used
        status["mem_percent"] = (mem_used / mem_total) * 100 if mem_total else 0.0

        # Uptime
        with open("/proc/uptime", "r") as f:
            uptime_seconds = float(f.readline().split()[0])
            hours, remainder = divmod(int(uptime_seconds), 3600)
            minutes, seconds = divmod(remainder, 60)
            days, hours = divmod(hours, 24)
            status["uptime"] = f"{days}d {hours}h {minutes}m"

        # CPU Load
        load1, load5, load15 = os.getloadavg()
        status["cpu_load"] = f"{load1:.2f}, {load5:.2f}, {load15:.2f}"

    except Exception as e:
        status["error"] = str(e)
    return status

def render_file_manager(user_id, current_dir, page=1, notice=None):
    current_dir = os.path.abspath(current_dir)
    if not os.path.exists(current_dir):
        current_dir = "/root/MyProject" if os.path.exists("/root/MyProject") else "/root"

    dir_key = encode_path(current_dir)
    show_hidden = get_show_hidden(user_id)
    free_gb = get_disk_free_gb(current_dir)

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
        if notice:
            notice += f"\n❌ Error membaca folder: {e}"
        else:
            notice = f"❌ Error membaca folder: {e}"

    total_files = len(files)
    total_pages = max(1, (total_files + FILES_PER_PAGE - 1) // FILES_PER_PAGE)
    page = max(1, min(page, total_pages))

    start_idx = (page - 1) * FILES_PER_PAGE
    end_idx = start_idx + FILES_PER_PAGE
    page_files = files[start_idx:end_idx]

    rel_path = current_dir.replace("/root", "~")
    text = f"🏢 OFFICE CLI & PHOTO SUITE MANAGER\n"
    text += f"━━━━━━━━━━━━━━━━━━━━━\n"
    text += f"📍 Path: {rel_path}\n"
    text += f"💾 Free Space: {free_gb:.1f} GB\n"
    text += f"📊 Total: {len(folders)} Folder | {total_files} File"
    if total_pages > 1:
        text += f" (Hal {page}/{total_pages})"
    text += "\n"
    if notice:
        text += f"\n{notice}\n"
    text += "━━━━━━━━━━━━━━━━━━━━━\n"


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
        {"text": "📝 File Baru", "callback_data": "fm_action:create_file_prompt"},
        {"text": "📦 Zip Folder Ini", "callback_data": "fm_action:zip_cwd"}
    ])
    inline_keyboard.append([
        {"text": "📂 MyProject", "callback_data": f"fm_cd:{myproject_key}:1"},
        {"text": "📊 Status VPS", "callback_data": "fm_action:view_status"},
        {"text": "📈 Chart VPS", "callback_data": "fm_action:view_chart"},
        {"text": "⚡ Processes", "callback_data": "fm_action:view_procs"}
    ])
    session_mode = get_session_mode(user_id)
    if session_mode == "continue":
        session_text = "💬 Sesi: Lanjut"
    elif session_mode == "new":
        session_text = "🆕 Sesi: Baru"
    else:
        session_text = f"🔖 Sesi: {session_mode[:8]}"

    inline_keyboard.append([
        {"text": "📦 Backup VPS", "callback_data": "fm_action:do_backup"},
        {"text": session_text, "callback_data": "fm_action:toggle_session_mode"},
        {"text": "📜 Pilih Sesi", "callback_data": "fm_action:list_sessions"}
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
        if ext == ".pdf" or item.lower().startswith("doc-"): icon = "📕"
        elif ext in [".docx", ".doc"]: icon = "📘"
        elif ext in [".pptx", ".ppt"]: icon = "📙"
        elif ext in [".xlsx", ".xls", ".csv"]: icon = "📊"
        elif ext in [".png", ".jpg", ".jpeg", ".webp", ".bmp"]: icon = "🖼️"

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

    text += "\n💡 Tip: Upload Foto / Dokumen dengan caption instruksi edit!"

    reply_markup = {"inline_keyboard": inline_keyboard}
    return text, reply_markup

def execute_antigravity(prompt, chat_id, status_msg_id, work_dir, session_mode="continue"):
    start_time = time.time()
    try:
        before_files = {}
        if os.path.exists(work_dir):
            try:
                for root_path, dirs, files in os.walk(work_dir):
                    for fname in files:
                        full_p = os.path.join(root_path, fname)
                        try:
                            before_files[full_p] = os.path.getmtime(full_p)
                        except Exception:
                            pass
            except Exception:
                pass

        cmd = [
            AGY_BIN,
            "--add-dir", work_dir
        ]
        if session_mode == "continue":
            cmd.append("--continue")
        elif session_mode and session_mode != "new":
            cmd.extend(["--conversation", str(session_mode)])

        cmd.extend([
            "--prompt", prompt,
            "--dangerously-skip-permissions"
        ])
        
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
        result_header = f"🤖 OFFICE & PHOTO AI EXECUTION\n📍 Path: {rel_dir}\n💬 Prompt: {prompt}\n━━━━━━━━━━━━━━━━━━━━━\n\n"
        full_output = result_header + clean_out
        
        edit_message(chat_id, status_msg_id, full_output)

        sent_files = set()
        new_pdf_files = []
        new_doc_files = []
        new_img_files = []

        # 1. Recursive scan for newly created/modified files in work_dir (including all subfolders)
        if os.path.exists(work_dir):
            try:
                for root_path, dirs, files in os.walk(work_dir):
                    for fname in files:
                        if fname in SYSTEM_FILES or fname.startswith("."):
                            continue
                        full_fpath = os.path.join(root_path, fname)
                        if os.path.isfile(full_fpath):
                            mtime = os.path.getmtime(full_fpath)
                            if full_fpath not in before_files or mtime > (before_files.get(full_fpath, 0) + 0.01):
                                ext = os.path.splitext(fname)[1].lower()
                                if ext == ".pdf":
                                    new_pdf_files.append(full_fpath)
                                elif ext in [".docx", ".xlsx", ".pptx", ".zip"]:
                                    new_doc_files.append(full_fpath)
                                elif ext in [".png", ".jpg", ".jpeg", ".webp", ".bmp"]:
                                    new_img_files.append(full_fpath)
            except Exception:
                pass

        # 2. Extract files mentioned directly in AGY output text
        raw_paths = re.findall(r'(?:file://)?(/root/[^\s\)\"\'>]+|[a-zA-Z0-9_\-\./]+\.(?:pdf|docx|xlsx|pptx|png|jpg|jpeg|webp|md))', output)
        for p in raw_paths:
            clean_p = p.replace("file://", "").rstrip(".,;:)")
            target_f = clean_p if clean_p.startswith("/") else os.path.join(work_dir, clean_p)
            if os.path.exists(target_f) and os.path.isfile(target_f):
                ext = os.path.splitext(target_f)[1].lower()
                if ext == ".pdf" and target_f not in new_pdf_files:
                    new_pdf_files.append(target_f)
                elif ext in [".docx", ".xlsx", ".pptx", ".zip"] and target_f not in new_doc_files:
                    new_doc_files.append(target_f)
                elif ext in [".png", ".jpg", ".jpeg", ".webp", ".bmp"] and target_f not in new_img_files:
                    new_img_files.append(target_f)

        # 3. Check brain artifact directory for newly created photos & documents
        brain_dir = "/root/.gemini/antigravity-cli/brain"
        if os.path.exists(brain_dir):
            try:
                for root_path, dirs, files in os.walk(brain_dir):
                    for fname in files:
                        ext = os.path.splitext(fname)[1].lower()
                        if ext in ['.png', '.jpg', '.jpeg', '.webp', '.pdf', '.docx', '.xlsx', '.pptx']:
                            full_p = os.path.join(root_path, fname)
                            try:
                                if os.path.getmtime(full_p) >= (start_time - 10):
                                    if ext == ".pdf" and full_p not in new_pdf_files:
                                        new_pdf_files.append(full_p)
                                    elif ext in [".docx", ".xlsx", ".pptx", ".zip"] and full_p not in new_doc_files:
                                        new_doc_files.append(full_p)
                                    elif ext in [".png", ".jpg", ".jpeg", ".webp", ".bmp"] and full_p not in new_img_files:
                                        new_img_files.append(full_p)
                            except Exception:
                                pass
            except Exception:
                pass

        # --- SMART FILE DELIVERY LOGIC ---
        # Priority 1: Send all PDF documents first
        for pdf_f in new_pdf_files:
            if pdf_f not in sent_files and os.path.basename(pdf_f) not in SYSTEM_FILES:
                sent_files.add(pdf_f)
                send_document(chat_id, pdf_f, caption=f"📕 Hasil PDF: {os.path.basename(pdf_f)}")

        # Priority 2: Send Office Documents
        for doc_f in new_doc_files:
            if doc_f not in sent_files and os.path.basename(doc_f) not in SYSTEM_FILES:
                sent_files.add(doc_f)
                send_document(chat_id, doc_f, caption=f"📄 Hasil Dokumen: {os.path.basename(doc_f)}")

        # Priority 3: Send Images (Filter out PDF page previews if PDFs were created)
        has_pdfs = len(new_pdf_files) > 0
        filtered_imgs = []
        for img_f in new_img_files:
            bname = os.path.basename(img_f).lower()
            if has_pdfs and (bname.startswith("preview_") or bname.startswith("page_") or "page_img" in img_f or "_preview" in bname):
                continue
            filtered_imgs.append(img_f)

        if filtered_imgs:
            if len(filtered_imgs) > 5 and not has_pdfs:
                try:
                    from office_tools import create_zip
                    zip_out = os.path.join(work_dir, f"hasil_gambar_{int(time.time())}.zip")
                    create_zip(work_dir, zip_out)
                    if os.path.exists(zip_out):
                        send_document(chat_id, zip_out, caption=f"📦 Total {len(filtered_imgs)} foto dipack ke ZIP: {os.path.basename(zip_out)}")
                        sent_files.add(zip_out)
                except Exception:
                    pass

            for img_f in filtered_imgs[:5]:
                if img_f not in sent_files and os.path.basename(img_f) not in SYSTEM_FILES:
                    sent_files.add(img_f)
                    send_photo(chat_id, img_f, caption=f"📸 Hasil Foto: {os.path.basename(img_f)}")

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

    if data == "menu_ask_agy":
        answer_callback_query(cq_id, "🤖 Silakan ketik pesan/prompt Anda!")
        send_message(chat_id, "🤖 *ANTIGRAVITY AI (AGY)*\n━━━━━━━━━━━━━━━━━━━━━\nKetik pesan/instruksi atau kirim Voice Note kapan saja untuk diproses oleh AGY AI!", parse_mode="Markdown")
        return

    if data == "menu_sys_status":
        answer_callback_query(cq_id, "📊 Loading status...")
        st = get_system_status()
        status_text = (
            "📊 *REAL-TIME VPS SYSTEM DASHBOARD*\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"⏱️ *Uptime:* `{st.get('uptime', 'N/A')}`\n"
            f"⚡ *CPU Load:* `{st.get('cpu_load', 'N/A')}`\n"
            f"🧠 *RAM Used:* `{st.get('mem_used_mb', 0):.1f} MB / {st.get('mem_total_mb', 0):.1f} MB ({st.get('mem_percent', 0):.1f}%)`\n"
            f"💾 *Disk Free:* `{st.get('disk_free_gb', 0):.2f} GB / {st.get('disk_total_gb', 0):.2f} GB ({st.get('disk_percent', 0):.1f}% used)`\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "🤖 *Bot Service:* Running & Active\n"
            "⚡ *AI Engine:* Antigravity CLI Active"
        )
        send_message(chat_id, status_text, parse_mode="Markdown")
        return

    if data == "menu_backup":
        answer_callback_query(cq_id, "📦 Triggering backup...")
        send_message(chat_id, "📦 Sedang membuat file backup VPS dan mengirim ke Telegram...")
        subprocess.Popen(["/root/backup_vps.sh"], cwd="/root")
        return

    if data == "menu_help":
        answer_callback_query(cq_id, "❓ Panduan AGY AI")
        help_txt = (
            "🤖 *ANTIGRAVITY AI (AGY) TELEGRAM CONTROLLER*\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "💬 *INTERAKSI DENGAN AGY AI:*\n"
            "• Kirim pesan teks secara bebas -> Diproses otomatis oleh Antigravity AI (`agy`).\n"
            "• Kirim *Voice Note* -> Otomatis ditranskrip & dieksekusi oleh AGY AI.\n\n"
            "💻 *PERINTAH BASH & SYSTEM:*\n"
            "• `/exec <command>` : Eksekusi perintah bash langsung di VPS.\n"
            "• `/status` : Dashboard status RAM, CPU, dan Storage Disk VPS.\n"
            "• `/chart` : Grafik real-time pemakaian sistem VPS.\n"
            "• `/top` : Process manager dengan fitur terminate PID.\n"
            "• `/services` : Status layanan systemd.\n"
            "• `/web <url>` : Scrape dan baca isi halaman web.\n\n"
            "📂 *FILE MANAGER & DIREKTORI:*\n"
            "• `/fm` : Buka File Manager interaktif.\n"
            "• `/cd <path>` : Pindah direktori kerja.\n"
            "• `/pwd` : Tampilkan direktori saat ini.\n"
            "• `/mkdir <nama>` | `/rm <nama>` | `/rename <lama> <baru>`\n"
            "• `/download <file>` : Unduh file langsung dari VPS.\n\n"
            "📦 *BACKUP & UTILITY:*\n"
            "• `/backup` : Trigger backup otomatis ke GitHub & Telegram.\n"
            "• `/menu` : Munculkan kembali tombol keyboard menu utama."
        )
        send_message(chat_id, help_txt, parse_mode="Markdown")
        return

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
            [{"text": "📕 Convert Folder Ini ke PDF", "callback_data": f"fm_folder_to_pdf:{target_key}"}],
            [{"text": "📦 Zip Folder Ini", "callback_data": f"fm_action:zip_item:{target_key}"}],
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
            
            is_image = ext in [".png", ".jpg", ".jpeg", ".webp", ".bmp"]
            header_title = "🖼️ PHOTO / GAMBAR EDITOR" if is_image else "📄 OFFICE DOKUMEN"

            text = f"{header_title}: {file_name}\n"
            text += f"━━━━━━━━━━━━━━━━━━━━━\n"
            text += f"📌 Nama: {file_name}\n"
            text += f"📍 Path: {file_path}\n"
            text += f"📊 Ukuran: {size_kb:.2f} KB\n"
            text += f"🕒 Modifikasi: {mtime}\n\n"
            
            if is_image:
                try:
                    from PIL import Image
                    with Image.open(file_path) as img:
                        text += f"📐 Resolusi: {img.width}x{img.height} | Mode: {img.mode}\n"
                except Exception:
                    pass

            btn_list = []
            if is_image:
                btn_list.append([
                    {"text": "🔄 Rotate 90°", "callback_data": f"img_action:rotate:{fl_key}"},
                    {"text": "🪞 Flip Horiz", "callback_data": f"img_action:flip:{fl_key}"},
                    {"text": "✂️ Auto-Crop Border", "callback_data": f"img_action:autocrop:{fl_key}"}
                ])
                btn_list.append([
                    {"text": "🎨 Grayscale", "callback_data": f"img_action:filter_grayscale:{fl_key}"},
                    {"text": "📜 Sepia", "callback_data": f"img_action:filter_sepia:{fl_key}"},
                    {"text": "🎞️ Vintage", "callback_data": f"img_action:filter_vintage:{fl_key}"}
                ])
                btn_list.append([
                    {"text": "🏷️ Watermark Bottom", "callback_data": f"img_action:wm_prompt:{fl_key}"},
                    {"text": "🏷️ Watermark Diagonal", "callback_data": f"img_action:wm_diag_prompt:{fl_key}"}
                ])
                btn_list.append([
                    {"text": "📸 Pas Foto Merah 3x4", "callback_data": f"img_action:pasfoto_red_3x4:{fl_key}"},
                    {"text": "📸 Pas Foto Biru 3x4", "callback_data": f"img_action:pasfoto_blue_3x4:{fl_key}"}
                ])
                btn_list.append([
                    {"text": "✂️ Hapus Background", "callback_data": f"img_action:nobg:{fl_key}"},
                    {"text": "⚡ Kompres Foto", "callback_data": f"img_action:compress:{fl_key}"}
                ])
                btn_list.append([
                    {"text": "🔄 Convert ke PNG", "callback_data": f"img_action:conv_png:{fl_key}"},
                    {"text": "📕 Convert ke PDF", "callback_data": f"img_action:conv_pdf:{fl_key}"}
                ])
                btn_list.append([
                    {"text": "🔍 OCR Teks Gambar", "callback_data": f"img_action:ocr:{fl_key}"}
                ])
            else:
                if ext == ".pdf" or file_name.lower().startswith("doc-"):
                    btn_list.append([
                        {"text": "✍️ Tempel Tanda Tangan / Stempel", "callback_data": f"fm_stamp_prompt:{fl_key}"},
                        {"text": "✂️ Extract Halaman PDF", "callback_data": f"fm_split_pdf_prompt:{fl_key}"}
                    ])
                    btn_list.append([
                        {"text": "🔒 Protect Password PDF", "callback_data": f"fm_action:protect_pdf:{fl_key}"},
                        {"text": "⚡ Kompres Ukuran PDF", "callback_data": f"fm_action:compress_pdf:{fl_key}"}
                    ])

                if ext in [".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt", ".txt", ".md", ".html"]:
                    btn_list.append([{"text": "📕 Convert ke PDF", "callback_data": f"fm_convert_pdf:{fl_key}"}])
                if ext == ".zip":
                    btn_list.append([{"text": "📂 Extract File ZIP", "callback_data": f"fm_action:unzip:{fl_key}"}])
                
                btn_list.append([
                    {"text": "🔍 Extract Text", "callback_data": f"fm_extract_text:{fl_key}"},
                    {"text": "🤖 AI Summarize", "callback_data": f"fm_action:ai_summary:{fl_key}"}
                ])
                btn_list.append([{"text": "📦 Compress ke ZIP", "callback_data": f"fm_action:zip_item:{fl_key}"}])

            btn_list.append([
                {"text": "📥 Download Telegram", "callback_data": f"fm_dl:{fl_key}"},
                {"text": "🔗 Link Download HTTP", "callback_data": f"fm_link:{fl_key}"}
            ])
            btn_list.append([{"text": "🗑️ Hapus File Ini", "callback_data": f"fm_rm_confirm:{fl_key}"}])
            btn_list.append([{"text": "🔙 Kembali ke Manager", "callback_data": f"fm_cd:{parent_key}:1"}])

            btn = {"inline_keyboard": btn_list}
            edit_message(chat_id, message_id, text, reply_markup=btn)

    elif data.startswith("img_action:"):
        parts = data.split("img_action:", 1)[1].split(":")
        sub_action = parts[0]
        fl_key = parts[1]
        file_path = decode_path(fl_key)
        file_name = os.path.basename(file_path)

        if sub_action == "ocr":
            answer_callback_query(cq_id, "🔍 Membaca Teks (OCR)...")
            try:
                res = subprocess.run(["python3", IMAGE_TOOLS, "ocr", file_path], capture_output=True, text=True)
                extracted_ocr = res.stdout.strip() if res.stdout else "Tidak ada teks yang terdeteksi."
                send_message(chat_id, f"🔍 HASIL OCR TEKS GAMBAR ({file_name}):\n━━━━━━━━━━━━━━━━━━━━━\n{clean_ai_output(extracted_ocr)[:3800]}")
            except Exception as e:
                send_message(chat_id, f"❌ Gagal OCR: {e}")

        elif sub_action == "rotate":
            answer_callback_query(cq_id, "🔄 Memutar gambar 90°...")
            try:
                res = subprocess.run(["python3", IMAGE_TOOLS, "rotate", file_path, "90"], capture_output=True, text=True)
                out_path = res.stdout.strip().split()[-1] if res.stdout else file_path
                send_document(chat_id, out_path, caption=f"🔄 Hasil Rotate 90°: {os.path.basename(out_path)}")
            except Exception as e:
                send_message(chat_id, f"❌ Gagal rotate: {e}")

        elif sub_action == "flip":
            answer_callback_query(cq_id, "🪞 Flip Horizontal...")
            try:
                res = subprocess.run(["python3", IMAGE_TOOLS, "flip", file_path, "horizontal"], capture_output=True, text=True)
                out_path = res.stdout.strip().split()[-1] if res.stdout else file_path
                send_document(chat_id, out_path, caption=f"🪞 Hasil Flip: {os.path.basename(out_path)}")
            except Exception as e:
                send_message(chat_id, f"❌ Gagal flip: {e}")

        elif sub_action == "autocrop":
            answer_callback_query(cq_id, "✂️ Auto-Crop Edge...")
            try:
                res = subprocess.run(["python3", IMAGE_TOOLS, "crop", file_path, "auto"], capture_output=True, text=True)
                out_path = res.stdout.strip().split()[-1] if res.stdout else file_path
                send_document(chat_id, out_path, caption=f"✂️ Hasil Auto-Crop: {os.path.basename(out_path)}")
            except Exception as e:
                send_message(chat_id, f"❌ Gagal auto-crop: {e}")

        elif sub_action.startswith("filter_"):
            ftype = sub_action.split("filter_", 1)[1]
            answer_callback_query(cq_id, f"🎨 Aplikasi Filter {ftype}...")
            try:
                res = subprocess.run(["python3", IMAGE_TOOLS, "filter", file_path, ftype], capture_output=True, text=True)
                out_path = res.stdout.strip().split()[-1] if res.stdout else file_path
                send_document(chat_id, out_path, caption=f"🎨 Filter {ftype.title()}: {os.path.basename(out_path)}")
            except Exception as e:
                send_message(chat_id, f"❌ Gagal filter: {e}")

        elif sub_action == "nobg":
            answer_callback_query(cq_id, "✂️ Menghapus Background...")
            send_message(chat_id, f"✂️ Menghapus background putih pada `{file_name}`...")
            try:
                res = subprocess.run(["python3", IMAGE_TOOLS, "nobg", file_path], capture_output=True, text=True)
                out_path = res.stdout.strip().split()[-1] if res.stdout else file_path
                send_document(chat_id, out_path, caption=f"✂️ Hasil Tanpa Background: {os.path.basename(out_path)}")
            except Exception as e:
                send_message(chat_id, f"❌ Gagal hapus background: {e}")

        elif sub_action == "conv_png":
            answer_callback_query(cq_id, "🔄 Convert ke PNG...")
            try:
                res = subprocess.run(["python3", IMAGE_TOOLS, "convert", file_path, "png"], capture_output=True, text=True)
                out_path = res.stdout.strip().split()[-1] if res.stdout else file_path
                send_document(chat_id, out_path, caption=f"🔄 Hasil PNG: {os.path.basename(out_path)}")
            except Exception as e:
                send_message(chat_id, f"❌ Gagal convert PNG: {e}")

        elif sub_action == "conv_pdf":
            answer_callback_query(cq_id, "📕 Convert Gambar ke PDF...")
            try:
                res = subprocess.run(["python3", IMAGE_TOOLS, "convert", file_path, "pdf"], capture_output=True, text=True)
                out_path = res.stdout.strip().split()[-1] if res.stdout else file_path
                send_document(chat_id, out_path, caption=f"📕 Hasil Gambar ke PDF: {os.path.basename(out_path)}")
            except Exception as e:
                send_message(chat_id, f"❌ Gagal convert PDF: {e}")

        elif sub_action == "compress":
            answer_callback_query(cq_id, "⚡ Kompres Foto...")
            try:
                res = subprocess.run(["python3", IMAGE_TOOLS, "compress", file_path, "75"], capture_output=True, text=True)
                out_path = res.stdout.strip().split()[-1] if res.stdout else file_path
                send_document(chat_id, out_path, caption=f"⚡ Hasil Kompresi Foto: {os.path.basename(out_path)}")
            except Exception as e:
                send_message(chat_id, f"❌ Gagal kompres foto: {e}")

        elif sub_action.startswith("pasfoto_"):
            parts = sub_action.split("_")
            bg_col = parts[1]
            sz = parts[2]
            answer_callback_query(cq_id, f"📸 Pas Foto ({sz}, {bg_col.title()})...")
            send_message(chat_id, f"📸 Membuat Pas Foto Formal ({sz}, BG {bg_col.title()}) dari `{file_name}`...")
            try:
                res = subprocess.run(["python3", IMAGE_TOOLS, "pas_foto", file_path, sz, bg_col], capture_output=True, text=True)
                out_path = res.stdout.strip().split()[-1] if res.stdout else file_path
                send_document(chat_id, out_path, caption=f"📸 Hasil Pas Foto Formal ({sz.upper()}, BG {bg_col.title()}): {os.path.basename(out_path)}")
            except Exception as e:
                send_message(chat_id, f"❌ Gagal membuat pas foto: {e}")


        elif sub_action == "wm_prompt":
            answer_callback_query(cq_id, "🏷️ Watermark Text")
            force_reply = {"force_reply": True, "selective": True}
            send_message(chat_id, f"🏷️ TAMBAHKAN WATERMARK TEKS\n\nKetik teks watermark yang ingin ditambahkan pada `{file_name}`:", reply_markup=force_reply)

        elif sub_action == "wm_diag_prompt":
            answer_callback_query(cq_id, "🏷️ Watermark Diagonal")
            force_reply = {"force_reply": True, "selective": True}
            send_message(chat_id, f"🏷️ TAMBAHKAN WATERMARK DIAGONAL\n\nKetik teks watermark diagonal yang ingin ditambahkan pada `{file_name}`:", reply_markup=force_reply)

    elif data.startswith("fm_split_pdf_prompt:"):
        fl_key = data.split("fm_split_pdf_prompt:", 1)[1]
        file_path = decode_path(fl_key)
        file_name = os.path.basename(file_path)
        answer_callback_query(cq_id, "✂️ Split PDF")
        force_reply = {"force_reply": True, "selective": True}
        send_message(chat_id, f"✂️ EXTRACT / SPLIT HALAMAN PDF\n\nKetik nomor halaman yang ingin diekstrak dari `{file_name}` (contoh: `1-3` atau `1,5,8`):", reply_markup=force_reply)

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

    elif data.startswith("fm_folder_to_pdf:"):
        f_key = data.split("fm_folder_to_pdf:", 1)[1]
        folder_path = decode_path(f_key)
        folder_name = os.path.basename(folder_path.rstrip('/\\'))
        answer_callback_query(cq_id, f"📕 Mengonversi Folder '{folder_name}' ke PDF...")
        send_message(chat_id, f"📕 Menggabungkan gambar di folder `{folder_name}` menjadi 1 file PDF...")
        try:
            res = subprocess.run(["python3", OFFICE_TOOLS, "folder_to_pdf", folder_path], capture_output=True, text=True)
            out_pdf = os.path.join(folder_path, f"{folder_name}.pdf")
            if not os.path.exists(out_pdf):
                lines = res.stdout.strip().splitlines() if res.stdout else []
                for line in reversed(lines):
                    if line.startswith("✅") and ".pdf" in line:
                        out_pdf = line.split(":")[-1].strip()
                        break
            if os.path.exists(out_pdf):
                send_document(chat_id, out_pdf, caption=f"📕 Hasil PDF dari Folder '{folder_name}': {os.path.basename(out_pdf)}")
            else:
                send_message(chat_id, f"❌ Konversi PDF folder gagal: {res.stderr or res.stdout}")
        except Exception as e:
            send_message(chat_id, f"❌ Error konversi folder PDF: {e}")

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

    elif data.startswith("fm_link:"):
        fl_key = data.split("fm_link:", 1)[1]
        file_path = decode_path(fl_key)
        answer_callback_query(cq_id, "🔗 Membuat Link Download...")
        link, dest_file = create_download_link(file_path)
        msg = (
            f"🔗 *LINK DOWNLOAD HTTP LANGSUNG*\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📌 *File:* `{os.path.basename(file_path)}`\n"
            f"🔗 *Link Download:* \n{link}\n\n"
            f"📍 *Path VPS:* `{dest_file}`\n"
            f"⏱️ *Masa Aktif Link:* 24 Jam\n\n"
            f"💡 Tap link di atas untuk mengunduh langsung dari HP / Browser Anda!"
        )
        send_message(chat_id, msg, parse_mode="Markdown")

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

    elif data.startswith("proc_kill:"):
        pid_str = data.split("proc_kill:", 1)[1]
        try:
            pid = int(pid_str)
            p = psutil.Process(pid)
            p_name = p.name()
            p.terminate()
            answer_callback_query(cq_id, f"🔥 Process PID {pid} ({p_name}) di-terminate!", show_alert=True)
            send_message(chat_id, f"🔥 Process PID `{pid}` ({p_name}) berhasil di-terminate.")
        except Exception as e:
            answer_callback_query(cq_id, f"❌ Gagal kill PID {pid_str}: {e}", show_alert=True)

    elif data.startswith("fm_action:"):
        action = data.split("fm_action:", 1)[1]
        if action == "noop":
            answer_callback_query(cq_id)
        elif action == "view_status":
            answer_callback_query(cq_id, "📊 Memuat Status VPS...")
            st = get_system_status()
            status_text = (
                "📊 *REAL-TIME VPS SYSTEM STATUS*\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                f"⏱️ *Uptime:* `{st.get('uptime', 'N/A')}`\n"
                f"⚡ *CPU Load:* `{st.get('cpu_load', 'N/A')}`\n"
                f"🧠 *RAM Used:* `{st.get('mem_used_mb', 0):.1f} MB / {st.get('mem_total_mb', 0):.1f} MB ({st.get('mem_percent', 0):.1f}%)`\n"
                f"💾 *Disk Free:* `{st.get('disk_free_gb', 0):.2f} GB / {st.get('disk_total_gb', 0):.2f} GB ({st.get('disk_percent', 0):.1f}% used)`\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "🤖 *Bot Controller:* Active (@Kontrolagybot)"
            )
            send_message(chat_id, status_text, parse_mode="Markdown")
        elif action == "view_chart":
            answer_callback_query(cq_id, "📈 Membuat Chart Analytics VPS...")
            chart_file = generate_system_chart()
            if chart_file and os.path.exists(chart_file):
                send_photo(chat_id, chart_file, caption="📈 *DYNAMIC VPS ANALYTICS DASHBOARD*\nReal-time RAM Usage & Disk Allocation")
            else:
                send_message(chat_id, "❌ Gagal membuat chart visual.")

        elif action == "view_procs":
            answer_callback_query(cq_id, "⚡ Memuat Process Manager...")
            procs = get_top_processes(limit=8)
            msg = "⚡ *PROCESS MANAGER (TOP MEMORY & CPU)*\n━━━━━━━━━━━━━━━━━━━━━\n"
            btn_rows = []
            for p in procs:
                msg += f"• `PID {p['pid']}`: *{p['name']}* | RAM: `{p['mem_mb']:.1f}MB` | CPU: `{p['cpu']:.1f}%`\n"
                btn_rows.append([{"text": f"⚡ Kill PID {p['pid']} ({p['name'][:12]})", "callback_data": f"proc_kill:{p['pid']}"}])
            
            btn_rows.append([{"text": "🔄 Refresh Processes", "callback_data": "fm_action:view_procs"}])
            send_message(chat_id, msg, reply_markup={"inline_keyboard": btn_rows}, parse_mode="Markdown")

        elif action.startswith("ai_summary:"):
            fl_key = action.split("ai_summary:", 1)[1]
            file_path = decode_path(fl_key)
            file_name = os.path.basename(file_path)
            answer_callback_query(cq_id, "🤖 Menyiapkan AI Summary...")
            try:
                res = subprocess.run(["python3", OFFICE_TOOLS, "extract_text", file_path], capture_output=True, text=True)
                doc_text = res.stdout or ""
                if not doc_text.strip():
                    send_message(chat_id, f"❌ Dokumen `{file_name}` kosong atau teks tidak terbaca.")
                    return

                prompt = f"Tolong ringkas dokumen '{file_name}' ini secara eksekutif, sertakan poin-poin utama dan data penting.\n\nISITEKS DOKUMEN:\n{doc_text[:6000]}"
                res_msg = send_message(chat_id, f"🤖 Antigravity menganalisa & meringkas `{file_name}`...")
                if res_msg and len(res_msg) > 0:
                    status_msg_id = res_msg[0]["message_id"]
                    t = threading.Thread(target=execute_antigravity, args=(prompt, chat_id, status_msg_id, current_cwd))
                    t.start()
            except Exception as e:
                send_message(chat_id, f"❌ Gagal AI Summary: {e}")

        elif action == "zip_cwd":
            answer_callback_query(cq_id, "📦 Membuat file ZIP folder...")
            send_message(chat_id, f"📦 Mengompres folder `{os.path.basename(current_cwd)}` ke ZIP...")
            try:
                res = subprocess.run(["python3", OFFICE_TOOLS, "zip", current_cwd], capture_output=True, text=True)
                out_zip = res.stdout.strip()
                if out_zip and os.path.exists(out_zip):
                    send_document(chat_id, out_zip, caption=f"📦 Hasil Zip Archive: {os.path.basename(out_zip)}")
                else:
                    send_message(chat_id, f"❌ Gagal zip folder: {res.stderr}")
            except Exception as e:
                send_message(chat_id, f"❌ Error zip: {e}")

        elif action.startswith("zip_item:"):
            fl_key = action.split("zip_item:", 1)[1]
            target_path = decode_path(fl_key)
            answer_callback_query(cq_id, "📦 Mengompres ke ZIP...")
            try:
                res = subprocess.run(["python3", OFFICE_TOOLS, "zip", target_path], capture_output=True, text=True)
                out_zip = res.stdout.strip()
                if out_zip and os.path.exists(out_zip):
                    send_document(chat_id, out_zip, caption=f"📦 Hasil Zip Archive: {os.path.basename(out_zip)}")
                else:
                    send_message(chat_id, f"❌ Gagal zip: {res.stderr}")
            except Exception as e:
                send_message(chat_id, f"❌ Error zip: {e}")

        elif action.startswith("compress_pdf:"):
            fl_key = action.split("compress_pdf:", 1)[1]
            pdf_path = decode_path(fl_key)
            answer_callback_query(cq_id, "⚡ Mengompres PDF...")
            send_message(chat_id, f"⚡ Mengompres file PDF `{os.path.basename(pdf_path)}`...")
            try:
                res = subprocess.run(["python3", OFFICE_TOOLS, "compress_pdf", pdf_path], capture_output=True, text=True)
                out_pdf = res.stdout.strip().split()[-1] if res.stdout else pdf_path
                send_document(chat_id, out_pdf, caption=f"⚡ Hasil Kompresi PDF: {os.path.basename(out_pdf)}")
            except Exception as e:
                send_message(chat_id, f"❌ Gagal mengompres PDF: {e}")

        elif action.startswith("protect_pdf:"):
            fl_key = action.split("protect_pdf:", 1)[1]
            pdf_path = decode_path(fl_key)
            answer_callback_query(cq_id, "🔒 Melindungi PDF...")
            send_message(chat_id, f"🔒 Menambahkan kata sandi pada `{os.path.basename(pdf_path)}`...")
            try:
                res = subprocess.run(["python3", OFFICE_TOOLS, "protect_pdf", pdf_path, "123456"], capture_output=True, text=True)
                out_pdf = res.stdout.strip().split()[-1] if res.stdout else pdf_path
                send_document(chat_id, out_pdf, caption=f"🔒 Hasil Protect PDF (Password: 123456): {os.path.basename(out_pdf)}")
            except Exception as e:
                send_message(chat_id, f"❌ Gagal protect PDF: {e}")

        elif action.startswith("unzip:"):
            fl_key = action.split("unzip:", 1)[1]
            zip_path = decode_path(fl_key)
            answer_callback_query(cq_id, "📂 Mengekstrak ZIP...")
            send_message(chat_id, f"📂 Mengekstrak `{os.path.basename(zip_path)}` ke `{current_cwd}`...")
            try:
                res = subprocess.run(["python3", OFFICE_TOOLS, "unzip", zip_path, current_cwd], capture_output=True, text=True)
                msg_text, reply_markup = render_file_manager(user_id, current_cwd, page=1, notice=f"✅ ZIP {os.path.basename(zip_path)} berhasil diekstrak!")
                send_message(chat_id, msg_text, reply_markup=reply_markup)
            except Exception as e:
                send_message(chat_id, f"❌ Error unzip: {e}")


        elif action == "list_sessions" or action.startswith("list_sessions:"):
            page = 1
            if ":" in action:
                try:
                    page = int(action.split("list_sessions:", 1)[1])
                except Exception:
                    page = 1
            answer_callback_query(cq_id, f"📜 Memuat Sesi Hal {page}...")
            msg_text, reply_markup = render_session_picker(page=page)
            edit_message(chat_id, message_id, msg_text, reply_markup=reply_markup, parse_mode="Markdown")

        elif action.startswith("pick_session:"):
            cid = action.split("pick_session:", 1)[1]
            set_user_session_id(user_id, cid)
            label = "💬 Sesi Lanjut Default" if cid == "continue" else ("🆕 Sesi Baru" if cid == "new" else f"🔖 Sesi ({cid[:8]}...)")
            answer_callback_query(cq_id, f"✅ Mode Sesi Diaktifkan: {label}")
            msg_text, reply_markup = render_file_manager(user_id, current_cwd, page=1, notice=f"✅ Mode Sesi Diaktifkan: {label}")
            edit_message(chat_id, message_id, msg_text, reply_markup=reply_markup)

        elif action == "toggle_hidden":
            new_state = toggle_show_hidden(user_id)
            state_str = "ditampilkan" if new_state else "disembunyikan"
            answer_callback_query(cq_id, f"👁️ File System {state_str}!")
            msg_text, reply_markup = render_file_manager(user_id, current_cwd, page=1)
            edit_message(chat_id, message_id, msg_text, reply_markup=reply_markup)
        elif action == "toggle_session_mode":
            new_mode = toggle_session_mode(user_id)
            mode_label = "💬 Sesi Lanjut" if new_mode == "continue" else "🆕 Sesi Baru"
            answer_callback_query(cq_id, f"⚙️ Mode diubah ke: {mode_label}!")
            msg_text, reply_markup = render_file_manager(user_id, current_cwd, page=1)
            edit_message(chat_id, message_id, msg_text, reply_markup=reply_markup)
        elif action == "do_backup":
            answer_callback_query(cq_id, "📦 Mengirim Backup VPS...")
            send_message(chat_id, "📦 Sedang membuat file backup VPS dan mengirim ke Telegram...")
            subprocess.Popen(["/root/backup_vps.sh", str(chat_id)], cwd="/root")
        elif action == "create_folder_prompt":
            answer_callback_query(cq_id, "Ketik nama folder baru...")
            force_reply = {"force_reply": True, "selective": True}
            send_message(chat_id, f"📁 BUAT FOLDER BARU\n\nKetik nama folder baru yang ingin dibuat di {current_cwd}:", reply_markup=force_reply)

    elif data == "create_doc_menu":
        answer_callback_query(cq_id, "📝 Menu Pembuat Dokumen")
        text = "📝 *MENU PEMBUAT DOKUMEN OFFICE*\n━━━━━━━━━━━━━━━━━━━━━\nPilih jenis dokumen yang ingin Anda buat:"
        btn = {"inline_keyboard": [
            [{"text": "📘 Word (.docx)", "callback_data": "create_doc_type:docx"}],
            [{"text": "📊 Excel (.xlsx)", "callback_data": "create_doc_type:xlsx"}],
            [{"text": "📕 PDF Document", "callback_data": "create_doc_type:pdf"}],
            [{"text": "📙 PowerPoint (.pptx)", "callback_data": "create_doc_type:pptx"}]
        ]}
        edit_message(chat_id, message_id, text, reply_markup=btn, parse_mode="Markdown")

    elif data == "create_img_menu":
        answer_callback_query(cq_id, "🖼️ Menu Pembuat Gambar")
        text = "🖼️ *MENU PEMBUAT GAMBAR & QR*\n━━━━━━━━━━━━━━━━━━━━━\nPilih jenis gambar yang ingin Anda buat:"
        btn = {"inline_keyboard": [
            [{"text": "🎨 Kartu / Banner Gambar", "callback_data": "create_img_type:banner"}],
            [{"text": "📱 QR Code Generator", "callback_data": "create_img_type:qr"}]
        ]}
        edit_message(chat_id, message_id, text, reply_markup=btn, parse_mode="Markdown")

    elif data.startswith("create_doc_type:"):
        dtype = data.split("create_doc_type:", 1)[1]
        answer_callback_query(cq_id, f"Membuat {dtype.upper()}...")
        force_reply = {"force_reply": True, "selective": True}
        send_message(chat_id, f"📝 BUAT DOKUMEN {dtype.upper()}\n\nKetik Judul atau Topik dokumen yang ingin dibuat:", reply_markup=force_reply)

    elif data.startswith("create_img_type:"):
        itype = data.split("create_img_type:", 1)[1]
        answer_callback_query(cq_id, f"Membuat {itype.upper()}...")
        force_reply = {"force_reply": True, "selective": True}
        if itype == "qr":
            send_message(chat_id, "📱 BUAT GAMBAR QR CODE\n\nKetik URL atau Teks yang ingin dijadikan QR Code:", reply_markup=force_reply)
        else:
            send_message(chat_id, "🎨 BUAT KARTU / BANNER GAMBAR\n\nKetik Teks Utama untuk banner gambar:", reply_markup=force_reply)

    elif data.startswith("send_file_tg:"):
        fl_key = data.split("send_file_tg:", 1)[1]
        file_path = decode_path(fl_key)
        if os.path.exists(file_path):
            answer_callback_query(cq_id, "📤 Mengirim ke Telegram...")
            send_document(chat_id, file_path, caption=f"📄 File Hasil: {os.path.basename(file_path)}")
        else:
            answer_callback_query(cq_id, "❌ File tidak ditemukan", show_alert=True)

def setup_bot_commands():
    commands = [
        {"command": "start", "description": "🚀 Dashboard & Menu Utama AGY"},
        {"command": "menu", "description": "📱 Tampilkan Tombol Menu Keyboard"},
        {"command": "sessions", "description": "📜 Pilih & Riwayat Sesi Percakapan"},
        {"command": "continue", "description": "💬 Aktifkan Mode Sesi Lanjut"},
        {"command": "new", "description": "🆕 Aktifkan Mode Sesi Baru"},
        {"command": "fm", "description": "📂 File Manager Interaktif"},
        {"command": "exec", "description": "💻 Eksekusi Perintah Bash VPS"},
        {"command": "status", "description": "📊 Status Resources VPS (RAM/CPU/Disk)"},
        {"command": "chart", "description": "📈 Grafik Real-time Analytics VPS"},
        {"command": "top", "description": "⚡ Process Manager & PID Monitor"},
        {"command": "services", "description": "🛠️ Status Systemd Services"},
        {"command": "web", "description": "🌐 Scraper & Reader Halaman Web"},
        {"command": "backup", "description": "📦 Backup VPS ke GitHub & Telegram"},
        {"command": "closemenu", "description": "🙈 Sembunyikan Tombol Menu Keyboard"},
        {"command": "help", "description": "❓ Panduan & Cara Penggunaan AGY"}
    ]
    api_request("setMyCommands", {"commands": commands})

def get_main_menu_keyboard():
    return {
        "keyboard": [
            [{"text": "🤖 Tanya AGY AI"}, {"text": "📂 File Manager"}],
            [{"text": "📜 Pilih Sesi"}, {"text": "💬 Sesi Lanjut / Baru"}],
            [{"text": "📊 Status VPS"}, {"text": "📈 Chart VPS"}],
            [{"text": "⚡ Top Processes"}, {"text": "🛠️ Services"}],
            [{"text": "💻 Exec Bash"}, {"text": "📦 Backup VPS"}],
            [{"text": "🌐 Web Reader"}, {"text": "❓ Bantuan"}],
            [{"text": "🙈 Sembunyikan Menu"}]
        ],
        "resize_keyboard": True,
        "is_persistent": True
    }



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

    # Check for ForceReply (Interactive Folder/File creation, Watermarking, PDF Stamping, or PDF Splitting)
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

        if "BUAT DOKUMEN DOCX" in reply_text and user_input_name:
            out_file = os.path.join(current_cwd, f"Dokumen_{int(time.time())}.docx")
            send_message(chat_id, f"📝 Membuat Dokumen Word `{os.path.basename(out_file)}`...")
            try:
                res = subprocess.run(["python3", OFFICE_TOOLS, "create_docx", out_file, user_input_name], capture_output=True, text=True)
                if os.path.exists(out_file):
                    fl_key = encode_path(out_file)
                    btn = {"inline_keyboard": [
                        [{"text": "📤 Ya, Kirim File ke Telegram Chat", "callback_data": f"send_file_tg:{fl_key}"}],
                        [{"text": "📂 Simpan di Server VPS", "callback_data": f"fm_file:{fl_key}"}]
                    ]}
                    send_message(chat_id, f"✅ Dokumen Word `{os.path.basename(out_file)}` selesai dibuat!\n\n❓ Mau dikirim ke Telegram nggak dokumennya?", reply_markup=btn)
            except Exception as e:
                send_message(chat_id, f"❌ Gagal membuat dokumen Word: {e}")
            return

        if "BUAT DOKUMEN XLSX" in reply_text and user_input_name:
            out_file = os.path.join(current_cwd, f"Spreadsheet_{int(time.time())}.xlsx")
            send_message(chat_id, f"📊 Membuat Spreadsheet Excel `{os.path.basename(out_file)}`...")
            try:
                res = subprocess.run(["python3", OFFICE_TOOLS, "create_excel", out_file, user_input_name], capture_output=True, text=True)
                if os.path.exists(out_file):
                    fl_key = encode_path(out_file)
                    btn = {"inline_keyboard": [
                        [{"text": "📤 Ya, Kirim File ke Telegram Chat", "callback_data": f"send_file_tg:{fl_key}"}],
                        [{"text": "📂 Simpan di Server VPS", "callback_data": f"fm_file:{fl_key}"}]
                    ]}
                    send_message(chat_id, f"✅ Spreadsheet Excel `{os.path.basename(out_file)}` selesai dibuat!\n\n❓ Mau dikirim ke Telegram nggak dokumennya?", reply_markup=btn)
            except Exception as e:
                send_message(chat_id, f"❌ Gagal membuat Excel: {e}")
            return

        if "BUAT DOKUMEN PDF" in reply_text and user_input_name:
            out_file = os.path.join(current_cwd, f"Laporan_{int(time.time())}.pdf")
            send_message(chat_id, f"📕 Membuat Dokumen PDF `{os.path.basename(out_file)}`...")
            try:
                res = subprocess.run(["python3", OFFICE_TOOLS, "create_pdf", out_file, user_input_name], capture_output=True, text=True)
                if os.path.exists(out_file):
                    fl_key = encode_path(out_file)
                    btn = {"inline_keyboard": [
                        [{"text": "📤 Ya, Kirim File ke Telegram Chat", "callback_data": f"send_file_tg:{fl_key}"}],
                        [{"text": "📂 Simpan di Server VPS", "callback_data": f"fm_file:{fl_key}"}]
                    ]}
                    send_message(chat_id, f"✅ Dokumen PDF `{os.path.basename(out_file)}` selesai dibuat!\n\n❓ Mau dikirim ke Telegram nggak dokumennya?", reply_markup=btn)
            except Exception as e:
                send_message(chat_id, f"❌ Gagal membuat PDF: {e}")
            return

        if "BUAT PRESENTASI PPTX" in reply_text and user_input_name:
            out_file = os.path.join(current_cwd, f"Presentasi_{int(time.time())}.pptx")
            send_message(chat_id, f"📙 Membuat Presentasi PowerPoint `{os.path.basename(out_file)}`...")
            try:
                res = subprocess.run(["python3", OFFICE_TOOLS, "create_pptx", out_file, user_input_name], capture_output=True, text=True)
                if os.path.exists(out_file):
                    fl_key = encode_path(out_file)
                    btn = {"inline_keyboard": [
                        [{"text": "📤 Ya, Kirim File ke Telegram Chat", "callback_data": f"send_file_tg:{fl_key}"}],
                        [{"text": "📂 Simpan di Server VPS", "callback_data": f"fm_file:{fl_key}"}]
                    ]}
                    send_message(chat_id, f"✅ Presentasi PPTX `{os.path.basename(out_file)}` selesai dibuat!\n\n❓ Mau dikirim ke Telegram nggak dokumennya?", reply_markup=btn)
            except Exception as e:
                send_message(chat_id, f"❌ Gagal membuat PPTX: {e}")
            return

        if "BUAT KARTU / BANNER GAMBAR" in reply_text and user_input_name:
            out_file = os.path.join(current_cwd, f"Gambar_{int(time.time())}.png")
            send_message(chat_id, f"🎨 Membuat Gambar Banner `{os.path.basename(out_file)}`...")
            try:
                res = subprocess.run(["python3", IMAGE_TOOLS, "create_image", out_file, "1080", "1080", "#1E3C72", user_input_name], capture_output=True, text=True)
                if os.path.exists(out_file):
                    fl_key = encode_path(out_file)
                    btn = {"inline_keyboard": [
                        [{"text": "📤 Ya, Kirim Gambar ke Telegram Chat", "callback_data": f"send_file_tg:{fl_key}"}],
                        [{"text": "📂 Simpan di Server VPS", "callback_data": f"fm_file:{fl_key}"}]
                    ]}
                    send_message(chat_id, f"✅ Gambar Banner `{os.path.basename(out_file)}` selesai dibuat!\n\n❓ Mau dikirim ke Telegram nggak gambarnya?", reply_markup=btn)
            except Exception as e:
                send_message(chat_id, f"❌ Gagal membuat gambar: {e}")
            return

        if "BUAT GAMBAR QR CODE" in reply_text and user_input_name:
            out_file = os.path.join(current_cwd, f"QRCode_{int(time.time())}.png")
            send_message(chat_id, f"📱 Membuat Gambar QR Code `{os.path.basename(out_file)}`...")
            try:
                res = subprocess.run(["python3", IMAGE_TOOLS, "create_qr", user_input_name, out_file], capture_output=True, text=True)
                if os.path.exists(out_file):
                    fl_key = encode_path(out_file)
                    btn = {"inline_keyboard": [
                        [{"text": "📤 Ya, Kirim QR Code ke Telegram Chat", "callback_data": f"send_file_tg:{fl_key}"}],
                        [{"text": "📂 Simpan di Server VPS", "callback_data": f"fm_file:{fl_key}"}]
                    ]}
                    send_message(chat_id, f"✅ Gambar QR Code `{os.path.basename(out_file)}` selesai dibuat!\n\n❓ Mau dikirim ke Telegram nggak gambarnya?", reply_markup=btn)
            except Exception as e:
                send_message(chat_id, f"❌ Gagal membuat QR Code: {e}")
            return


        if "TAMBAHKAN WATERMARK TEKS" in reply_text and user_input_name:
            match = re.search(r'pada `(.*?)`:', reply_text)
            img_filename = match.group(1) if match else None
            if img_filename:
                img_path = os.path.join(current_cwd, img_filename)
                if os.path.exists(img_path):
                    send_message(chat_id, f"🏷️ Menambahkan watermark `{user_input_name}` pada `{img_filename}`...")
                    try:
                        res = subprocess.run(["python3", IMAGE_TOOLS, "watermark", img_path, user_input_name], capture_output=True, text=True)
                        out_img = res.stdout.strip().split()[-1] if res.stdout else img_path
                        send_document(chat_id, out_img, caption=f"🏷️ Hasil Watermark: {os.path.basename(out_img)}")
                    except Exception as e:
                        send_message(chat_id, f"❌ Gagal watermark: {e}")
            return

        if "TAMBAHKAN WATERMARK DIAGONAL" in reply_text and user_input_name:
            match = re.search(r'pada `(.*?)`:', reply_text)
            img_filename = match.group(1) if match else None
            if img_filename:
                img_path = os.path.join(current_cwd, img_filename)
                if os.path.exists(img_path):
                    send_message(chat_id, f"🏷️ Menambahkan watermark diagonal `{user_input_name}` pada `{img_filename}`...")
                    try:
                        res = subprocess.run(["python3", IMAGE_TOOLS, "watermark", img_path, user_input_name, "diagonal", "white", "true"], capture_output=True, text=True)
                        out_img = res.stdout.strip().split()[-1] if res.stdout else img_path
                        send_document(chat_id, out_img, caption=f"🏷️ Hasil Watermark Diagonal: {os.path.basename(out_img)}")
                    except Exception as e:
                        send_message(chat_id, f"❌ Gagal watermark diagonal: {e}")
            return

        if "EXTRACT / SPLIT HALAMAN PDF" in reply_text and user_input_name:
            match = re.search(r'dari `(.*?)`', reply_text)
            pdf_filename = match.group(1) if match else None
            if pdf_filename:
                pdf_path = os.path.join(current_cwd, pdf_filename)
                if os.path.exists(pdf_path):
                    send_message(chat_id, f"✂️ Mengekstrak halaman `{user_input_name}` dari `{pdf_filename}`...")
                    try:
                        res = subprocess.run(["python3", OFFICE_TOOLS, "split", pdf_path, user_input_name], capture_output=True, text=True)
                        out_pdf = res.stdout.strip().split()[-1] if res.stdout else pdf_path
                        send_document(chat_id, out_pdf, caption=f"✂️ Hasil Ekstraksi Halaman PDF: {os.path.basename(out_pdf)}")
                    except Exception as e:
                        send_message(chat_id, f"❌ Gagal split PDF: {e}")
            return

        if "TEMPEL TANDA TANGAN" in reply_text:
            match = re.search(r'pada `(.*?)`:', reply_text)
            pdf_filename = match.group(1) if match else None
            if pdf_filename:
                pdf_path = os.path.join(current_cwd, pdf_filename)
                img_path = os.path.join(current_cwd, user_input_name) if not user_input_name.startswith("/") else user_input_name
                
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

    # Handle Voice Note / Voice Commands
    if "voice" in message or "audio" in message:
        voice_obj = message.get("voice") or message.get("audio")
        file_id = voice_obj["file_id"]
        ogg_path = f"/tmp/voice_{int(time.time())}.ogg"
        res = api_request("getFile", {"file_id": file_id})
        if res and res.get("ok"):
            file_rel_path = res["result"]["file_path"]
            dl_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_rel_path}"
            try:
                urllib.request.urlretrieve(dl_url, ogg_path)
                send_message(chat_id, "🎙️ Memproses pesan suara & transkrip ke teks...")
                voice_text = transcribe_voice_note(ogg_path)
                if voice_text:
                    full_prompt = f"{voice_text}"
                    res_msg = send_message(chat_id, f"🎙️ *PERINTAH SUARA TERDETEKSI:*\n`\"{voice_text}\"`\n\n🤖 Antigravity AI mengeksekusi instruksi...", parse_mode="Markdown")
                    if res_msg and len(res_msg) > 0:
                        status_msg_id = res_msg[0]["message_id"]
                        t = threading.Thread(target=execute_antigravity, args=(full_prompt, chat_id, status_msg_id, current_cwd))
                        t.start()
                else:
                    send_message(chat_id, "⚠️ Gagal mengonversi pesan suara menjadi teks.")
            except Exception as e:
                send_message(chat_id, f"❌ Error voice processing: {e}")
            finally:
                if os.path.exists(ogg_path):
                    os.remove(ogg_path)
        return

    # Handle Photo/Image Uploads (with optional Caption Instruction!)
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
                    full_prompt = f"Gambar '{img_filename}' telah diupload ke direktori '{current_cwd}'. Instruksi pengguna: {caption_text}. Silakan olah/edit gambar ini sesuai instruksi."
                    res_msg = send_message(chat_id, f"🤖 Antigravity memproses & mengedit foto {img_filename}...\n💬 Instruksi: {caption_text}")
                    if res_msg and len(res_msg) > 0:
                        status_msg_id = res_msg[0]["message_id"]
                        t = threading.Thread(target=execute_antigravity, args=(full_prompt, chat_id, status_msg_id, current_cwd))
                        t.start()
                    return

                fl_key = encode_path(target_path)
                btn_list = [
                    [
                        {"text": "🔄 Rotate 90°", "callback_data": f"img_action:rotate:{fl_key}"},
                        {"text": "🪞 Flip Horiz", "callback_data": f"img_action:flip:{fl_key}"},
                        {"text": "✂️ Auto-Crop", "callback_data": f"img_action:autocrop:{fl_key}"}
                    ],
                    [
                        {"text": "🎨 Grayscale", "callback_data": f"img_action:filter_grayscale:{fl_key}"},
                        {"text": "📜 Sepia", "callback_data": f"img_action:filter_sepia:{fl_key}"},
                        {"text": "🎞️ Vintage", "callback_data": f"img_action:filter_vintage:{fl_key}"}
                    ],
                    [
                        {"text": "🏷️ Watermark Bottom", "callback_data": f"img_action:wm_prompt:{fl_key}"},
                        {"text": "🏷️ Watermark Diagonal", "callback_data": f"img_action:wm_diag_prompt:{fl_key}"}
                    ],
                    [
                        {"text": "✂️ Hapus Background", "callback_data": f"img_action:nobg:{fl_key}"},
                        {"text": "⚡ Kompres Foto", "callback_data": f"img_action:compress:{fl_key}"}
                    ],
                    [
                        {"text": "🔄 Convert ke PNG", "callback_data": f"img_action:conv_png:{fl_key}"},
                        {"text": "📕 Convert ke PDF", "callback_data": f"img_action:conv_pdf:{fl_key}"}
                    ]
                ]
                reply_markup = {"inline_keyboard": btn_list}
                send_message(chat_id, f"🖼️ FOTO DITERIMA: `{img_filename}`\n📍 Saved to: `{target_path}`\n\n💡 Tip: Pilih aksi editor foto di bawah ini, atau beri instruksi di caption saat upload foto!", reply_markup=reply_markup)
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
                if ext in [".png", ".jpg", ".jpeg", ".webp", ".bmp"]:
                    btn_list = [
                        [
                            {"text": "🔄 Rotate 90°", "callback_data": f"img_action:rotate:{fl_key}"},
                            {"text": "🪞 Flip Horiz", "callback_data": f"img_action:flip:{fl_key}"},
                            {"text": "✂️ Auto-Crop", "callback_data": f"img_action:autocrop:{fl_key}"}
                        ],
                        [
                            {"text": "🎨 Grayscale", "callback_data": f"img_action:filter_grayscale:{fl_key}"},
                            {"text": "📜 Sepia", "callback_data": f"img_action:filter_sepia:{fl_key}"},
                            {"text": "🎞️ Vintage", "callback_data": f"img_action:filter_vintage:{fl_key}"}
                        ],
                        [
                            {"text": "🏷️ Watermark Bottom", "callback_data": f"img_action:wm_prompt:{fl_key}"},
                            {"text": "🏷️ Watermark Diagonal", "callback_data": f"img_action:wm_diag_prompt:{fl_key}"}
                        ],
                        [
                            {"text": "✂️ Hapus Background", "callback_data": f"img_action:nobg:{fl_key}"},
                            {"text": "⚡ Kompres Foto", "callback_data": f"img_action:compress:{fl_key}"}
                        ]
                    ]
                else:
                    if ext == ".pdf" or file_name.lower().startswith("doc-"):
                        btn_list.append([
                            {"text": "✍️ Tempel Tanda Tangan / Stempel", "callback_data": f"fm_stamp_prompt:{fl_key}"},
                            {"text": "✂️ Extract Halaman PDF", "callback_data": f"fm_split_pdf_prompt:{fl_key}"}
                        ])
                    if ext in [".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt", ".txt", ".md", ".html"]:
                        btn_list.append([{"text": "📕 Convert ke PDF", "callback_data": f"fm_convert_pdf:{fl_key}"}])
                    btn_list.append([{"text": "🔍 Extract Text / Data", "callback_data": f"fm_extract_text:{fl_key}"}])

                parent_key = encode_path(current_cwd)
                btn_list.append([{"text": "🔙 Buka di File Manager", "callback_data": f"fm_cd:{parent_key}:1"}])

                reply_markup = {"inline_keyboard": btn_list}
                send_message(chat_id, f"📥 DOKUMEN DITERIMA: {file_name}\n📍 Saved to: {target_path}\n\n💡 Tip: Kamu bisa upload dokumen/foto sambil memberikan instruksi di Caption!", reply_markup=reply_markup)
            except Exception as e:
                send_message(chat_id, f"❌ Gagal mengunduh file: {e}")
        return

    if "text" not in message:
        return

    text = message["text"].strip()

    if text in ["/start", "/menu", "📱 Tombol Menu"]:
        st = get_system_status()
        disk_free = st.get('disk_free_gb', 0)
        ram_used = st.get('mem_used_mb', 0)
        ram_pct = st.get('mem_percent', 0)
        
        menu_text = (
            "🤖 *GOOGLE ANTIGRAVITY (AGY) AI DASHBOARD*\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "🟢 *System Status:* `Online & Operational`\n"
            f"🧠 *RAM Used:* `{ram_used:.1f} MB ({ram_pct:.1f}%)` | 💾 *Free Disk:* `{disk_free:.1f} GB`\n"
            "⚡ *AI Engine:* `Google Antigravity (agy v1.1.9)`\n"
            f"📍 *Current Path:* `{current_cwd}`\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📱 *PILIH MENU CEPAT:* Tap tombol keyboard di bawah atau langsung kirim pesan ke bot!\n\n"
            "💡 *Cara Interaksi dengan AGY:*\n"
            "• *Teks Prompt* -> Tulis pesan apa saja, AGY AI akan langsung mengeksekusi!\n"
            "• *Voice Note* -> Ucapan suara dikonversi otomatis menjadi prompt AGY AI!\n"
            "• *Perintah Bash* -> Gunakan `/exec <command>` untuk jalankan bash command."
        )
        inline_dash = {"inline_keyboard": [
            [{"text": "🤖 Tanya AGY AI", "callback_data": "menu_ask_agy"}, {"text": "📂 Buka File Manager", "callback_data": "fm_cd:L3Jvb3Q=:1"}],
            [{"text": "📊 Status System VPS", "callback_data": "menu_sys_status"}, {"text": "⚡ Process Top", "callback_data": "fm_action:view_procs"}],
            [{"text": "📦 Backup VPS", "callback_data": "menu_backup"}, {"text": "❓ Panduan & Bantuan", "callback_data": "menu_help"}]
        ]}
        send_message(chat_id, menu_text, reply_markup=get_main_menu_keyboard(), parse_mode="Markdown")
        send_message(chat_id, "⚡ *MENU PINTASAN AKSI INLINE:*", reply_markup=inline_dash, parse_mode="Markdown")
        return

    if text in ["/closemenu", "/hidemenu", "/close", "🙈 Sembunyikan Menu"]:
        send_message(
            chat_id,
            "🙈 Tombol menu keyboard disembunyikan.\n\n💡 Ketik `/menu` kapan saja untuk memunculkan kembali tombol menu.",
            reply_markup={"remove_keyboard": True},
            parse_mode="Markdown"
        )
        return

    if text.lower() in ["fm", "/fm", "ls", "/ls", "browse", "/browse"] or text == "📂 File Manager":
        msg_text, reply_markup = render_file_manager(user_id, current_cwd, page=1)
        send_message(chat_id, msg_text, reply_markup=reply_markup)
        return

    if text in ["📜 Pilih Sesi", "📜 List Sesi"]:
        msg_text, reply_markup = render_session_picker(page=1)
        send_message(chat_id, msg_text, reply_markup=reply_markup, parse_mode="Markdown")
        return

    if text in ["💬 Sesi Lanjut / Baru", "💬 Mode Sesi"]:
        new_mode = toggle_session_mode(user_id)
        mode_label = "💬 Mode Sesi Lanjut (Chat Berlanjut)" if new_mode == "continue" else "🆕 Mode Sesi Baru (Chat Baru)"
        send_message(chat_id, f"⚙️ *MODE SESI DIUBAH*\n━━━━━━━━━━━━━━━━━━━━━\n{mode_label}", parse_mode="Markdown")
        return

    if text in ["🤖 Tanya AGY AI", "/ask", "/agy"]:
        send_message(
            chat_id,
            "🤖 *TANYA ANTIGRAVITY AI (AGY)*\n━━━━━━━━━━━━━━━━━━━━━\n"
            "Silakan ketik instruksi atau prompt Anda secara langsung di chat ini, atau kirim *Voice Note*!\n\n"
            "AGY AI akan merespons dan mengeksekusi tugas Anda secara otomatis di VPS.",
            parse_mode="Markdown"
        )
        return

    if text in ["💻 Exec Bash", "💻 Run Bash", "/exec_help"]:
        send_message(
            chat_id,
            "💻 *EKSEKUSI PERINTAH BASH*\n━━━━━━━━━━━━━━━━━━━━━\n"
            "Ketik perintah terminal dengan format:\n`/exec <perintah>`\n\n"
            "Contoh:\n• `/exec ls -la`\n• `/exec df -h`\n• `/exec uptime`",
            parse_mode="Markdown"
        )
        return

    if text in ["/status", "/sys", "/vps", "📊 Status VPS"]:
        st = get_system_status()
        status_text = (
            "📊 *REAL-TIME VPS SYSTEM DASHBOARD*\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"⏱️ *Uptime:* `{st.get('uptime', 'N/A')}`\n"
            f"⚡ *CPU Load:* `{st.get('cpu_load', 'N/A')}`\n"
            f"🧠 *RAM Used:* `{st.get('mem_used_mb', 0):.1f} MB / {st.get('mem_total_mb', 0):.1f} MB ({st.get('mem_percent', 0):.1f}%)`\n"
            f"💾 *Disk Free:* `{st.get('disk_free_gb', 0):.2f} GB / {st.get('disk_total_gb', 0):.2f} GB ({st.get('disk_percent', 0):.1f}% used)`\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "🤖 *Bot Service:* Running & Active\n"
            "⚡ *AI Engine:* Antigravity CLI Active"
        )
        send_message(chat_id, status_text, parse_mode="Markdown")
        return

    if text in ["/chart", "/syschart", "📈 Chart VPS"]:
        send_message(chat_id, "📈 Sedang membuat chart analytics VPS...")
        chart_file = generate_system_chart()
        if chart_file and os.path.exists(chart_file):
            send_photo(chat_id, chart_file, caption="📈 *DYNAMIC VPS ANALYTICS DASHBOARD*\nReal-time RAM Usage & Disk Allocation")
        else:
            send_message(chat_id, "❌ Gagal membuat chart visual.")
        return

    if text in ["/top", "/ps", "/procs", "⚡ Top Processes"]:
        procs = get_top_processes(limit=8)
        msg = "⚡ *PROCESS MANAGER (TOP MEMORY & CPU)*\n━━━━━━━━━━━━━━━━━━━━━\n"
        btn_rows = []
        for p in procs:
            msg += f"• `PID {p['pid']}`: *{p['name']}* | RAM: `{p['mem_mb']:.1f}MB` | CPU: `{p['cpu']:.1f}%`\n"
            btn_rows.append([{"text": f"⚡ Kill PID {p['pid']} ({p['name'][:12]})", "callback_data": f"proc_kill:{p['pid']}"}])
        
        btn_rows.append([{"text": "🔄 Refresh Processes", "callback_data": "fm_action:view_procs"}])
        send_message(chat_id, msg, reply_markup={"inline_keyboard": btn_rows}, parse_mode="Markdown")
        return

    if text in ["/services", "/service", "🛠️ Services"]:
        svcs = get_services_status()
        msg = "🛠️ *SYSTEM SERVICES STATUS*\n━━━━━━━━━━━━━━━━━━━━━\n"
        for s in svcs:
            msg += f"• *{s['name']}*: {s['icon']} (`{s['state']}`)\n"
        send_message(chat_id, msg, parse_mode="Markdown")
        return

    if text in ["/backup", "/backupvps", "📦 Backup VPS"]:
        send_message(chat_id, "📦 Sedang membuat file backup VPS dan mengirim ke Telegram...")
        subprocess.Popen(["/root/backup_vps.sh"], cwd="/root")
        return

    if text == "🌐 Web Reader":
        send_message(chat_id, "🌐 *PEMBACA HALAMAN WEB*\n\nSilakan ketik URL yang ingin dibaca dengan format:\n`/web https://google.com`", parse_mode="Markdown")
        return

    if text.startswith("/web "):
        url = text[5:].strip()
        send_message(chat_id, f"🌐 Membaca halaman web `{url}`...")
        res = read_web_page(url)
        send_message(chat_id, res, parse_mode="Markdown")
        return

    if text in ["/help", "/bantuan", "❓ Bantuan"]:
        help_txt = (
            "🤖 *ANTIGRAVITY AI (AGY) TELEGRAM CONTROLLER*\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "💬 *INTERAKSI DENGAN AGY AI:*\n"
            "• Kirim pesan teks secara bebas -> Diproses otomatis oleh Antigravity AI (`agy`).\n"
            "• Kirim *Voice Note* -> Otomatis ditranskrip & dieksekusi oleh AGY AI.\n\n"
            "💻 *PERINTAH BASH & SYSTEM:*\n"
            "• `/exec <command>` : Eksekusi perintah bash langsung di VPS.\n"
            "• `/status` : Dashboard status RAM, CPU, dan Storage Disk VPS.\n"
            "• `/chart` : Grafik real-time pemakaian sistem VPS.\n"
            "• `/top` : Process manager dengan fitur terminate PID.\n"
            "• `/services` : Status layanan systemd.\n"
            "• `/web <url>` : Scrape dan baca isi halaman web.\n\n"
            "📂 *FILE MANAGER & DIREKTORI:*\n"
            "• `/fm` : Buka File Manager interaktif.\n"
            "• `/cd <path>` : Pindah direktori kerja.\n"
            "• `/pwd` : Tampilkan direktori saat ini.\n"
            "• `/mkdir <nama>` | `/rm <nama>` | `/rename <lama> <baru>`\n"
            "• `/download <file>` : Unduh file langsung dari VPS.\n\n"
            "📦 *BACKUP & UTILITY:*\n"
            "• `/backup` : Trigger backup otomatis ke GitHub & Telegram.\n"
            "• `/menu` : Munculkan kembali tombol keyboard menu utama."
        )
        send_message(chat_id, help_txt, parse_mode="Markdown")
        return

    if text in ["/backup", "/backupvps"]:
        send_message(chat_id, "📦 Sedang membuat file backup VPS dan mengirim ke Telegram...")
        subprocess.Popen(["/root/backup_vps.sh"], cwd="/root")
        return

    if text.startswith("/merge "):
        parts = text[7:].strip().split()
        if len(parts) >= 2:
            out_file = parts[0] if parts[0].endswith(".pdf") else f"{parts[0]}.pdf"
            pdf_files = parts[1:]
            pdf_paths = [os.path.join(current_cwd, p) if not p.startswith("/") else p for p in pdf_files]
            out_path = os.path.join(current_cwd, out_file)
            send_message(chat_id, f"📚 Menggabungkan {len(pdf_paths)} PDF ke `{out_file}`...")
            try:
                res = subprocess.run(["python3", OFFICE_TOOLS, "merge", out_path] + pdf_paths, capture_output=True, text=True)
                merged = res.stdout.strip()
                if merged and os.path.exists(merged):
                    send_document(chat_id, merged, caption=f"📚 Hasil Penggabungan PDF: {os.path.basename(merged)}")
                else:
                    send_message(chat_id, f"❌ Gagal menggabungkan PDF: {res.stderr}")
            except Exception as e:
                send_message(chat_id, f"❌ Error merge: {e}")
        else:
            send_message(chat_id, "ℹ️ Format: `/merge output.pdf file1.pdf file2.pdf`", parse_mode="Markdown")
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

    # /sessions or /listsessions -> Show interactive list of past sessions
    if text.startswith("/sessions") or text.startswith("/listsessions") or text.startswith("/history"):
        page = 1
        parts = text.strip().split()
        if len(parts) >= 2 and parts[1].isdigit():
            page = int(parts[1])
        msg_text, reply_markup = render_session_picker(page=page)
        send_message(chat_id, msg_text, reply_markup=reply_markup, parse_mode="Markdown")
        return

    # /new or /newsession or /reset -> Switch to new session mode
    if text in ["/new", "/newsession", "/resetsession", "/reset"]:
        if "session_modes" not in STATE:
            STATE["session_modes"] = {}
        STATE["session_modes"][str(user_id)] = "new"
        save_state(STATE)
        send_message(chat_id, "🆕 *MODE SESI BARU AKTIF!*\n━━━━━━━━━━━━━━━━━━━━━\nSetiap perintah baru tidak akan menyambung riwayat obrolan sebelumnya.\n\n💡 *Tip*: Ketik /continue untuk mengaktifkan kembali mode percakapan berlanjut.", parse_mode="Markdown")
        return

    # /continue or /continuesession -> Switch to continuous session mode
    if text in ["/continue", "/continuesession"]:
        if "session_modes" not in STATE:
            STATE["session_modes"] = {}
        STATE["session_modes"][str(user_id)] = "continue"
        save_state(STATE)
        send_message(chat_id, "💬 *MODE SESI LANJUT AKTIF!*\n━━━━━━━━━━━━━━━━━━━━━\nPerintah baru akan otomatis menyambung memori dan percakapan sebelumnya.\n\n💡 *Tip*: Ketik /new untuk mulai sesi baru.", parse_mode="Markdown")
        return

    # Regular prompt -> Run AGY with Photo Editor & Office capabilities!
    session_mode = get_session_mode(user_id)
    if session_mode == "continue":
        session_label = "💬 (Sesi Lanjut)"
    elif session_mode == "new":
        session_label = "🆕 (Sesi Baru)"
    else:
        session_label = f"🔖 (Sesi {session_mode[:8]})"

    res_msg = send_message(chat_id, f"🤖 Antigravity memproses perintah {session_label}...\n📍 cwd: {current_cwd}")
    if res_msg and len(res_msg) > 0:
        status_msg_id = res_msg[0]["message_id"]
        t = threading.Thread(target=execute_antigravity, args=(text, chat_id, status_msg_id, current_cwd, session_mode))
        t.start()

def main():
    print("🚀 Antigravity Telegram Office & Photo Editor Active...")
    print("Bot Username: @Kontrolagybot")

    setup_bot_commands()

    t_http = threading.Thread(target=start_http_server, daemon=True)
    t_http.start()

    t_clean = threading.Thread(target=cleanup_old_downloads, daemon=True)
    t_clean.start()

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
