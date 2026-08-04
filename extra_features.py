import os
import re
import time
import subprocess
import urllib.request
import urllib.parse
import json
import threading
import qrcode
from io import BytesIO

# ============================================================
# FITUR CANGGIH TAMBAHAN UNTUK OfficeCLI Telegram Bot
# File: /root/extra_features.py
# ============================================================

# ---------- 1. QR CODE GENERATOR ----------
def generate_qr_code(text, output_path=None):
    """Generate QR Code dari teks/URL, return path file PNG"""
    try:
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(text)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        if output_path is None:
            safe = re.sub(r'[^a-zA-Z0-9]', '_', text[:20])
            output_path = f"/root/MyProject/downloads/qr_{safe}_{int(time.time())}.png"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img.save(output_path)
        return output_path
    except Exception as e:
        print(f"❌ QR Error: {e}")
        return None

# ---------- 2. URL SHORTENER (via TinyURL) ----------
def shorten_url(long_url):
    """Perkecil URL menggunakan TinyURL API"""
    try:
        api = f"http://tinyurl.com/api-create.php?url={urllib.parse.quote(long_url)}"
        with urllib.request.urlopen(api, timeout=10) as r:
            return r.read().decode()
    except Exception as e:
        return f"❌ Gagal shortening URL: {e}"

# ---------- 3. DOWNLOAD VIDEO/AUDIO dari YouTube/Medsos ----------
def download_media(url, audio_only=False, output_dir="/root/MyProject/downloads"):
    """Download video atau audio dari YouTube/Reel/TikTok via yt-dlp"""
    os.makedirs(output_dir, exist_ok=True)
    try:
        fmt = "bestaudio/best" if audio_only else "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
        ext = "mp3" if audio_only else "mp4"
        ts = int(time.time())
        out_tmpl = f"{output_dir}/media_{ts}.%(ext)s"

        cmd = ["yt-dlp", "--no-playlist", "-f", fmt, "-o", out_tmpl, url]
        if audio_only:
            cmd += ["--extract-audio", "--audio-format", "mp3"]

        res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        # Cari file hasil download
        for fname in os.listdir(output_dir):
            if fname.startswith(f"media_{ts}"):
                return os.path.join(output_dir, fname), None
        return None, res.stderr[-500:] if res.stderr else "Tidak ada output"
    except subprocess.TimeoutExpired:
        return None, "⏱️ Timeout: Video terlalu besar"
    except Exception as e:
        return None, str(e)

# ---------- 4. NETWORK / PING TOOL ----------
def ping_host(host, count=4):
    """Ping host dan return hasil ringkas"""
    try:
        res = subprocess.run(
            ["ping", "-c", str(count), "-W", "3", host],
            capture_output=True, text=True, timeout=20
        )
        output = res.stdout
        # Ekstrak statistik
        lines = [l for l in output.splitlines() if l.strip()]
        summary = "\n".join(lines[-4:]) if len(lines) >= 4 else output
        return f"📡 *Ping ke {host}*\n```\n{summary}\n```"
    except Exception as e:
        return f"❌ Ping error: {e}"

def check_port(host, port):
    """Cek apakah port terbuka di host tertentu"""
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, int(port)))
        sock.close()
        status = "🟢 OPEN" if result == 0 else "🔴 CLOSED"
        return f"🔌 Port *{port}* di `{host}`: {status}"
    except Exception as e:
        return f"❌ Error cek port: {e}"

def whois_ip(ip_or_domain):
    """Lookup informasi IP/domain via ip-api.com"""
    try:
        url = f"http://ip-api.com/json/{urllib.parse.quote(ip_or_domain)}?fields=status,country,regionName,city,isp,org,as,query"
        with urllib.request.urlopen(url, timeout=8) as r:
            data = json.loads(r.read())
        if data.get("status") == "success":
            return (
                f"🌍 *IP Info: {data['query']}*\n"
                f"├ Negara: {data.get('country','?')}\n"
                f"├ Region: {data.get('regionName','?')}\n"
                f"├ Kota: {data.get('city','?')}\n"
                f"├ ISP: {data.get('isp','?')}\n"
                f"└ AS: {data.get('as','?')}"
            )
        return f"❌ Tidak ada data untuk: {ip_or_domain}"
    except Exception as e:
        return f"❌ Whois error: {e}"

# ---------- 5. REMINDER / ALARM ----------
_reminders = {}

def set_reminder(chat_id, send_fn, seconds, message):
    """Set alarm/reminder yang akan kirim pesan setelah N detik"""
    def _fire():
        time.sleep(seconds)
        send_fn(chat_id, f"⏰ *REMINDER!*\n\n{message}")
    t = threading.Thread(target=_fire, daemon=True)
    t.start()
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    dur_str = f"{mins} menit {secs} detik" if mins > 0 else f"{secs} detik"
    return f"✅ Reminder diset! Saya akan ingatkan dalam *{dur_str}*:\n_{message}_"

def parse_reminder_duration(text):
    """Parse durasi seperti '5m', '30s', '2h', '1j', '10menit' -> detik"""
    text = text.lower().strip()
    total = 0
    patterns = [
        (r'(\d+)\s*(?:jam|hours?|h)', 3600),
        (r'(\d+)\s*(?:menit|minutes?|min|m)', 60),
        (r'(\d+)\s*(?:detik|seconds?|sec|s)', 1),
    ]
    for pattern, mult in patterns:
        m = re.search(pattern, text)
        if m:
            total += int(m.group(1)) * mult
    return total if total > 0 else None

# ---------- 6. KALKULATOR CANGGIH ----------
def smart_calc(expr):
    """Kalkulator ekspresi matematika yang aman"""
    import math
    allowed = {
        'abs': abs, 'round': round, 'min': min, 'max': max,
        'pow': pow, 'sum': sum,
        'sqrt': math.sqrt, 'log': math.log, 'log10': math.log10,
        'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
        'pi': math.pi, 'e': math.e, 'ceil': math.ceil, 'floor': math.floor,
    }
    try:
        clean = re.sub(r'[^\d\s\+\-\*\/\(\)\.\,\%\^a-zA-Z_]', '', expr)
        clean = clean.replace('^', '**').replace(',', '.')
        result = eval(clean, {"__builtins__": {}}, allowed)
        return f"🧮 `{expr}` = *{result}*"
    except Exception as e:
        return f"❌ Kalkulator error: {e}"

# ---------- 7. TEXT TOOLS ----------
def count_words(text):
    """Hitung kata, karakter, dan kalimat dari teks"""
    words = len(text.split())
    chars = len(text)
    chars_no_space = len(text.replace(' ', ''))
    sentences = len(re.split(r'[.!?]+', text))
    lines = len(text.splitlines())
    return (
        f"📝 *Statistik Teks:*\n"
        f"├ Kata: *{words}*\n"
        f"├ Karakter: *{chars}* (tanpa spasi: {chars_no_space})\n"
        f"├ Kalimat: *{sentences}*\n"
        f"└ Baris: *{lines}*"
    )

def base64_encode(text):
    import base64
    return base64.b64encode(text.encode()).decode()

def base64_decode(text):
    import base64
    try:
        return base64.b64decode(text.encode()).decode()
    except Exception as e:
        return f"❌ Base64 decode error: {e}"

# ---------- 8. CUACA (wttr.in) ----------
def get_weather(city):
    """Ambil info cuaca kota via wttr.in"""
    try:
        url = f"https://wttr.in/{urllib.parse.quote(city)}?format=4"
        req = urllib.request.Request(url, headers={"User-Agent": "curl/7.68.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            result = r.read().decode('utf-8').strip()
        return f"🌤️ *Cuaca di {city}:*\n`{result}`"
    except Exception as e:
        return f"❌ Gagal ambil cuaca: {e}"

# ---------- 9. SPEEDTEST / BANDWIDTH CHECK ----------
def check_bandwidth():
    """Test download speed server via wget"""
    try:
        start = time.time()
        url = "http://speedtest.tele2.net/1MB.zip"
        req = urllib.request.Request(url, headers={"User-Agent": "curl/7.68.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = r.read()
        elapsed = time.time() - start
        size_mb = len(data) / (1024 * 1024)
        speed = size_mb / elapsed * 8  # Mbps
        return (
            f"🚀 *Bandwidth Test:*\n"
            f"├ Download: *{speed:.1f} Mbps*\n"
            f"├ Ukuran: {size_mb:.2f} MB\n"
            f"└ Waktu: {elapsed:.2f}s"
        )
    except Exception as e:
        return f"❌ Bandwidth test error: {e}"

