#!/usr/bin/env python3
import os
import sys
import json
import time
import re
import subprocess

def normalize_url(url):
    if not url:
        return ""
    url = url.strip()
    # Normalize YouTube Shorts and short links
    shorts_match = re.search(r'(?:youtube\.com/shorts/|youtu\.be/)([a-zA-Z0-9_-]{11})', url)
    if shorts_match:
        video_id = shorts_match.group(1)
        return f"https://www.youtube.com/watch?v={video_id}"
    return url

def get_media_info(url):
    """Retrieve metadata for video/audio URL using yt-dlp"""
    clean_url = normalize_url(url)
    cmd = [
        "yt-dlp",
        "--dump-json",
        "--no-playlist",
        "--skip-download",
        "--extractor-args", "youtube:player_client=android_vr,web,ios",
        clean_url
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
        if res.returncode == 0 and res.stdout.strip():
            info = json.loads(res.stdout.strip())
            return {
                "title": info.get("title", "Media Video"),
                "uploader": info.get("uploader") or info.get("channel") or "Unknown",
                "duration": info.get("duration", 0),
                "thumbnail": info.get("thumbnail"),
                "view_count": info.get("view_count", 0),
                "ext": info.get("ext", "mp4")
            }
    except Exception as e:
        print(f"Error fetching info: {e}", file=sys.stderr)
    return None

def download_video(url, quality="best", output_dir="/tmp"):
    """Download video with selected quality format and YouTube Shorts fallback support"""
    os.makedirs(output_dir, exist_ok=True)
    clean_url = normalize_url(url)
    out_template = os.path.join(output_dir, f"video_{int(time.time())}_%(title).50s.%(ext)s")
    
    fmt = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/b/best/bestvideo+bestaudio"
    if quality == "720p":
        fmt = "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/b/best"
    elif quality == "480p":
        fmt = "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/b/best"
    elif quality == "360p":
        fmt = "bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360][ext=mp4]/b/best"

    cmd = [
        "yt-dlp",
        "-f", fmt,
        "--merge-output-format", "mp4",
        "--no-playlist",
        "--extractor-args", "youtube:player_client=android_vr,web,ios",
        "-o", out_template,
        clean_url
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        # Find the downloaded file
        for f in os.listdir(output_dir):
            if f.startswith("video_") and (f.endswith(".mp4") or f.endswith(".mkv") or f.endswith(".webm")):
                full_p = os.path.join(output_dir, f)
                if os.path.getmtime(full_p) > (time.time() - 310):
                    print(f"Downloaded video: {full_p}", file=sys.stderr)
                    return full_p
    except Exception as e:
        print(f"Video download failed: {e}", file=sys.stderr)
    return None

def download_audio(url, audio_format="mp3", output_dir="/tmp"):
    """Extract audio MP3/M4A from video URL"""
    os.makedirs(output_dir, exist_ok=True)
    clean_url = normalize_url(url)
    out_template = os.path.join(output_dir, f"audio_{int(time.time())}_%(title).50s.%(ext)s")

    cmd = [
        "yt-dlp",
        "-x",
        "--audio-format", audio_format,
        "--audio-quality", "0",
        "--no-playlist",
        "--extractor-args", "youtube:player_client=android_vr,web,ios",
        "-o", out_template,
        clean_url
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        target_ext = f".{audio_format}"
        for f in os.listdir(output_dir):
            if f.startswith("audio_") and (f.endswith(target_ext) or f.endswith(".mp3") or f.endswith(".m4a")):
                full_p = os.path.join(output_dir, f)
                if os.path.getmtime(full_p) > (time.time() - 310):
                    print(f"Downloaded audio: {full_p}", file=sys.stderr)
                    return full_p
    except Exception as e:
        print(f"Audio download failed: {e}", file=sys.stderr)
    return None

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 media_downloader.py <info|video|audio> <url> [quality/format]")
        sys.exit(1)

    action = sys.argv[1]
    url = sys.argv[2]
    opt = sys.argv[3] if len(sys.argv) > 3 else "best"

    if action == "info":
        info = get_media_info(url)
        print(json.dumps(info) if info else "{}")
    elif action == "video":
        out = download_video(url, quality=opt)
        if out: print(out)
    elif action == "audio":
        out = download_audio(url, audio_format=opt)
        if out: print(out)
