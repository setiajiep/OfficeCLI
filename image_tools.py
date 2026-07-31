#!/usr/bin/env python3
"""
OfficeCLI - Complete Photo & Image Suite for Python
Handles image resizing, rotation, flipping, cropping, filters, adjustments, watermarks,
format conversions, automatic background removal, compression, OCR text extraction,
QR code generation, graphic card/banner creation, and document scanner filter.
Integrates with Telegram for optional instant file delivery.
"""

import os
import sys
import cv2
import numpy as np
import time
from PIL import Image, ImageEnhance, ImageFilter, ImageOps, ImageDraw, ImageFont
from telegram_utils import prompt_send_to_telegram, send_file_to_telegram

def resize_image(img_path, width=None, height=None, output_path=None):
    """Resize image to specified width/height while maintaining aspect ratio if only one dimension given"""
    if not os.path.exists(img_path):
        print(f"❌ File gambar tidak ditemukan: {img_path}")
        return None
    if output_path is None:
        base, ext = os.path.splitext(img_path)
        output_path = f"{base}_resized{ext}"

    with Image.open(img_path) as img:
        orig_w, orig_h = img.size
        if width and not height:
            height = int(orig_h * (float(width) / orig_w))
        elif height and not width:
            width = int(orig_w * (float(height) / orig_h))
        elif not width and not height:
            width, height = orig_w, orig_h

        resized = img.resize((int(width), int(height)), Image.Resampling.LANCZOS)
        resized.save(output_path)
        print(f"✅ Gambar berhasil diubah ukuran ({width}x{height}): {output_path}")
        return output_path

def rotate_image(img_path, angle=90, output_path=None):
    """Rotate image by specified angle in degrees"""
    if not os.path.exists(img_path):
        print(f"❌ File gambar tidak ditemukan: {img_path}")
        return None
    if output_path is None:
        base, ext = os.path.splitext(img_path)
        output_path = f"{base}_rotated{ext}"

    with Image.open(img_path) as img:
        rotated = img.rotate(-float(angle), expand=True)
        rotated.save(output_path)
        print(f"✅ Gambar berhasil diputar ({angle}°): {output_path}")
        return output_path

def flip_image(img_path, direction='horizontal', output_path=None):
    """Flip image horizontally or vertically"""
    if not os.path.exists(img_path):
        print(f"❌ File gambar tidak ditemukan: {img_path}")
        return None
    if output_path is None:
        base, ext = os.path.splitext(img_path)
        output_path = f"{base}_flipped{ext}"

    with Image.open(img_path) as img:
        if direction.lower() in ['horizontal', 'h', 'left-right']:
            flipped = ImageOps.mirror(img)
        else:
            flipped = ImageOps.flip(img)
        flipped.save(output_path)
        print(f"✅ Gambar berhasil dibalik ({direction}): {output_path}")
        return output_path

def crop_image(img_path, left=None, top=None, right=None, bottom=None, auto=False, output_path=None):
    """Crop an image using bounding box or auto-crop whitespace/transparent edges"""
    if not os.path.exists(img_path):
        print(f"❌ File gambar tidak ditemukan: {img_path}")
        return None
    if output_path is None:
        base, ext = os.path.splitext(img_path)
        output_path = f"{base}_cropped{ext}"

    with Image.open(img_path) as img:
        w, h = img.size
        if auto:
            if img.mode == 'RGBA':
                bbox = img.getbbox()
            else:
                gray = img.convert('L')
                inverted = ImageOps.invert(gray)
                bbox = inverted.getbbox()
            cropped = img.crop(bbox) if bbox else img
        else:
            l = int(left) if left is not None else 0
            t = int(top) if top is not None else 0
            r = int(right) if right is not None else w
            b = int(bottom) if bottom is not None else h
            cropped = img.crop((l, t, r, b))

        cropped.save(output_path)
        print(f"✅ Gambar berhasil dipotong: {output_path}")
        return output_path

def apply_filter(img_path, filter_type='grayscale', output_path=None):
    """Apply photo filter (grayscale, sepia, blur, sharpen, contour, invert, vintage, sketch, doc_scan)"""
    if not os.path.exists(img_path):
        print(f"❌ File gambar tidak ditemukan: {img_path}")
        return None
    if output_path is None:
        base, ext = os.path.splitext(img_path)
        output_path = f"{base}_{filter_type}{ext}"

    ftype = filter_type.lower()
    if ftype in ['doc_scan', 'scan', 'scanner']:
        return doc_scanner_effect(img_path, output_path=output_path)

    with Image.open(img_path) as img:
        if ftype in ['grayscale', 'gray', 'bw']:
            res = img.convert('L')
        elif ftype == 'sepia':
            gray = img.convert('L')
            res = ImageOps.colorize(gray, '#704214', '#C0A080')
        elif ftype == 'blur':
            res = img.filter(ImageFilter.BLUR)
        elif ftype == 'sharpen':
            res = img.filter(ImageFilter.SHARPEN)
        elif ftype == 'contour':
            res = img.filter(ImageFilter.CONTOUR)
        elif ftype == 'invert':
            if img.mode == 'RGBA':
                r, g, b, a = img.split()
                rgb = Image.merge('RGB', (r, g, b))
                inv = ImageOps.invert(rgb)
                r, g, b = inv.split()
                res = Image.merge('RGBA', (r, g, b, a))
            else:
                res = ImageOps.invert(img.convert('RGB'))
        elif ftype == 'vintage':
            img_cv = cv2.imread(img_path)
            if img_cv is not None:
                b, g, r = cv2.split(img_cv)
                r = cv2.add(r, 30)
                b = cv2.subtract(b, 20)
                vintage_cv = cv2.merge((b, g, r))
                cv2.imwrite(output_path, vintage_cv)
                print(f"✅ Filter vintage berhasil diterapkan: {output_path}")
                return output_path
            res = img
        elif ftype == 'sketch':
            img_cv = cv2.imread(img_path)
            if img_cv is not None:
                gray, sketch = cv2.pencilSketch(img_cv, sigma_s=60, sigma_r=0.07, shade_factor=0.05)
                cv2.imwrite(output_path, sketch)
                print(f"✅ Filter sketch berhasil diterapkan: {output_path}")
                return output_path
            res = img
        else:
            res = img

        res.save(output_path)
        print(f"✅ Filter {filter_type} berhasil diterapkan: {output_path}")
        return output_path

def adjust_image(img_path, brightness=1.0, contrast=1.0, saturation=1.0, sharpness=1.0, output_path=None):
    """Adjust brightness, contrast, saturation, and sharpness"""
    if not os.path.exists(img_path):
        print(f"❌ File gambar tidak ditemukan: {img_path}")
        return None
    if output_path is None:
        base, ext = os.path.splitext(img_path)
        output_path = f"{base}_adjusted{ext}"

    with Image.open(img_path) as img:
        res = img
        if float(brightness) != 1.0:
            res = ImageEnhance.Brightness(res).enhance(float(brightness))
        if float(contrast) != 1.0:
            res = ImageEnhance.Contrast(res).enhance(float(contrast))
        if float(saturation) != 1.0:
            res = ImageEnhance.Color(res).enhance(float(saturation))
        if float(sharpness) != 1.0:
            res = ImageEnhance.Sharpness(res).enhance(float(sharpness))

        res.save(output_path)
        print(f"✅ Penyesuaian gambar berhasil: {output_path}")
        return output_path

def add_watermark(img_path, text, position='bottom-right', font_size=36, color="white", alpha=200, diagonal=False, output_path=None):
    """Add text watermark with custom positioning, font size, color, alpha transparency, or diagonal angle"""
    if not os.path.exists(img_path):
        print(f"❌ File gambar tidak ditemukan: {img_path}")
        return None
    if output_path is None:
        base, ext = os.path.splitext(img_path)
        output_path = f"{base}_watermarked{ext}"

    COLOR_MAP = {
        "white": (255, 255, 255),
        "black": (0, 0, 0),
        "red": (230, 50, 50),
        "blue": (50, 120, 240),
        "green": (50, 200, 80),
        "yellow": (240, 200, 40),
        "gold": (220, 175, 40)
    }
    rgb_color = COLOR_MAP.get(str(color).lower(), (255, 255, 255))
    text_fill = (*rgb_color, int(alpha))

    with Image.open(img_path).convert("RGBA") as base_img:
        w, h = base_img.size

        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(font_size))
        except Exception:
            font = ImageFont.load_default()

        if diagonal or str(position).lower() == 'diagonal':
            txt_layer = Image.new("RGBA", (w * 2, h * 2), (255, 255, 255, 0))
            draw = ImageDraw.Draw(txt_layer)
            
            bbox = draw.textbbox((0, 0), text, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]

            cx = w - text_w / 2
            cy = h - text_h / 2
            draw.rectangle([cx - 15, cy - 8, cx + text_w + 15, cy + text_h + 8], fill=(0, 0, 0, int(alpha * 0.4)))
            draw.text((cx, cy), text, font=font, fill=text_fill)

            rotated_layer = txt_layer.rotate(35, resample=Image.Resampling.BICUBIC, center=(w, h))
            crop_box = (w // 2, h // 2, w // 2 + w, h // 2 + h)
            out_layer = rotated_layer.crop(crop_box)
            out_img = Image.alpha_composite(base_img, out_layer)
        else:
            txt_img = Image.new("RGBA", base_img.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(txt_img)
            
            bbox = draw.textbbox((0, 0), text, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]

            pos = str(position).lower()
            if pos == 'center':
                x = (w - text_w) / 2
                y = (h - text_h) / 2
            elif pos == 'bottom-left':
                x = 30
                y = h - text_h - 30
            elif pos == 'top-right':
                x = w - text_w - 30
                y = 30
            elif pos == 'top-left':
                x = 30
                y = 30
            else:
                x = w - text_w - 30
                y = h - text_h - 30

            draw.rectangle([x - 10, y - 5, x + text_w + 10, y + text_h + 5], fill=(0, 0, 0, int(alpha * 0.5)))
            draw.text((x, y), text, font=font, fill=text_fill)
            out_img = Image.alpha_composite(base_img, txt_img)

        if output_path.lower().endswith(('.jpg', '.jpeg')):
            out_img = out_img.convert("RGB")
        out_img.save(output_path)
        print(f"✅ Watermark berhasil ditambahkan: {output_path}")
        return output_path

def convert_format(img_path, target_ext="png", output_path=None):
    """Convert image to JPG, PNG, WEBP, BMP, PDF, etc."""
    if not os.path.exists(img_path):
        print(f"❌ File gambar tidak ditemukan: {img_path}")
        return None
    target_ext = target_ext.lstrip('.').lower()
    if output_path is None:
        base, _ = os.path.splitext(img_path)
        output_path = f"{base}.{target_ext}"

    with Image.open(img_path) as img:
        if target_ext in ['jpg', 'jpeg'] and img.mode in ['RGBA', 'LA', 'P']:
            img = img.convert('RGB')
        elif target_ext == 'pdf' and img.mode != 'RGB':
            img = img.convert('RGB')
        img.save(output_path)
        print(f"✅ Format gambar berhasil dikonversi ke .{target_ext}: {output_path}")
        return output_path

def remove_bg(img_path, output_path=None, threshold=210):
    """Automatic background removal for document / signature images"""
    if not os.path.exists(img_path):
        print(f"❌ File gambar tidak ditemukan: {img_path}")
        return None
    if output_path is None:
        base, _ = os.path.splitext(img_path)
        output_path = f"{base}_nobg.png"

    img_cv = cv2.imread(img_path)
    if img_cv is None:
        return None

    b_channel, g_channel, r_channel = cv2.split(img_cv)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    _, alpha = cv2.threshold(gray, int(threshold), 255, cv2.THRESH_BINARY_INV)
    alpha = cv2.GaussianBlur(alpha, (3, 3), 0)

    rgba = cv2.merge((b_channel, g_channel, r_channel, alpha))
    cv2.imwrite(output_path, rgba)
    print(f"✅ Latar belakang putih berhasil dihapus: {output_path}")
    return output_path

def compress_image(img_path, quality=75, output_path=None):
    """Compress image file size while preserving visual quality"""
    if not os.path.exists(img_path):
        print(f"❌ File gambar tidak ditemukan: {img_path}")
        return None
    if output_path is None:
        base, ext = os.path.splitext(img_path)
        output_path = f"{base}_compressed{ext}"

    with Image.open(img_path) as img:
        if img.mode in ['RGBA', 'LA', 'P'] and output_path.lower().endswith(('.jpg', '.jpeg')):
            img = img.convert('RGB')
        img.save(output_path, optimize=True, quality=int(quality))
        print(f"✅ Gambar berhasil dikompres (Kualitas={quality}%): {output_path}")
        return output_path

def ocr_image(img_path, lang='ind+eng'):
    """Optical Character Recognition (OCR) to extract text from images/photos"""
    if not os.path.exists(img_path):
        return "❌ File gambar tidak ditemukan."
    try:
        import pytesseract
        with Image.open(img_path) as img:
            text = pytesseract.image_to_string(img, lang=lang)
            return text.strip() or "Tidak ada teks yang terdeteksi pada gambar."
    except Exception as e:
        return f"Error OCR: {e}"

def get_image_info(img_path):
    """Get metadata and dimensions of an image"""
    if not os.path.exists(img_path):
        return {}
    try:
        with Image.open(img_path) as img:
            size_kb = os.path.getsize(img_path) / 1024
            return {
                "format": img.format,
                "mode": img.mode,
                "width": img.width,
                "height": img.height,
                "dimensions": f"{img.width}x{img.height}",
                "size_kb": round(size_kb, 2)
            }
    except Exception as e:
        return {"error": str(e)}

# ---------------------------------------------------------
# Image Generation & Special Upgrades
# ---------------------------------------------------------

def create_image(output_path=None, width=1080, height=1080, bg_color="#1E3C72", text="Gambar Baru", font_size=54, text_color="white"):
    """Create a new custom banner, graphics canvas, or card image"""
    if output_path is None:
        output_path = f"/root/Gambar_{int(time.time())}.png"

    width, height = int(width), int(height)
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(font_size))
    except Exception:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    tx = (width - tw) / 2
    ty = (height - th) / 2

    # Draw centered text with subtle shadow
    draw.text((tx + 3, ty + 3), text, font=font, fill=(0, 0, 0, 150))
    draw.text((tx, ty), text, font=font, fill=text_color)

    img.save(output_path)
    print(f"✅ Gambar baru berhasil dibuat: {output_path}")
    return output_path

def create_qr(text="https://github.com/setiajiep/OfficeCLI", output_path=None, size=10):
    """Generate a high-quality QR Code image"""
    import qrcode

    if output_path is None:
        output_path = f"/root/QRCode_{int(time.time())}.png"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=int(size),
        border=4,
    )
    qr.add_data(text)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#1E3C72", back_color="white")
    img.save(output_path)
    print(f"✅ QR Code berhasil dibuat: {output_path}")
    return output_path

def doc_scanner_effect(img_path, output_path=None):
    """Clean document photo scanner effect (b&w high contrast adaptive thresholding)"""
    if not os.path.exists(img_path):
        print(f"❌ File gambar tidak ditemukan: {img_path}")
        return None
    if output_path is None:
        base, ext = os.path.splitext(img_path)
        output_path = f"{base}_scanned{ext}"

    img_cv = cv2.imread(img_path)
    if img_cv is None:
        return None

    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    scanned = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, 10)
    cv2.imwrite(output_path, scanned)
    print(f"✅ Efek Scanner dokumen berhasil diterapkan: {output_path}")
    return output_path

# ---------------------------------------------------------
# CLI Main Function
# ---------------------------------------------------------

if __name__ == "__main__":
    args = sys.argv[1:]
    send_tg = False

    # Check for --send-telegram or -t flag
    if "--send-telegram" in args:
        send_tg = True
        args.remove("--send-telegram")
    elif "-t" in args:
        send_tg = True
        args.remove("-t")

    if not args:
        print("""
🖼️ OfficeCLI - Suite Editing & Pembuat Gambar
Usage: python3 image_tools.py <action> [args...] [--send-telegram / -t]

Tindakan yang tersedia:
  • resize <img_path> [width] [height]  - Ubah ukuran gambar
  • rotate <img_path> [angle]           - Putar gambar (derajat)
  • flip <img_path> [h|v]               - Balik horizontal/vertikal
  • crop <img_path> [auto|l t r b]      - Potong bagian gambar
  • filter <img_path> [grayscale|sepia|blur|sharpen|vintage|sketch|doc_scan]
  • adjust <img_path> [bright] [contrast] [sat] [sharp]
  • watermark <img_path> <text> [pos] [color] [diag]
  • convert <img_path> <target_ext>     - Ubah format (png, jpg, webp, pdf)
  • nobg <img_path> [threshold]         - Hapus background putih (TTD/Logo)
  • compress <img_path> [quality]       - Kompres ukuran file (75%)
  • create_image [out] [width] [height] [bg_color] [text] - Buat gambar baru
  • create_qr <text_or_url> [out]       - Buat gambar QR Code
  • scanner <img_path> [out]            - Filter scanner dokumen (B&W)
  • ocr <img_path>                      - Ekstrak teks dari foto (OCR)
  • info <img_path>                     - Info dimensi & ukuran file

Setiap pembuatan/perubahan gambar akan menanyakan konfirmasi pengiriman ke Telegram.
Gunakan flag --send-telegram atau -t untuk pengiriman otomatis.
""")
        sys.exit(0)

    action = args[0]
    img_path = args[1] if len(args) > 1 else ""
    result_file = None

    if action == "resize" and len(args) > 1:
        w = args[2] if len(args) > 2 else None
        h = args[3] if len(args) > 3 else None
        result_file = resize_image(img_path, width=int(w) if w else None, height=int(h) if h else None)
    elif action == "rotate" and len(args) > 1:
        angle = float(args[2]) if len(args) > 2 else 90
        result_file = rotate_image(img_path, angle=angle)
    elif action == "flip" and len(args) > 1:
        d = args[2] if len(args) > 2 else "horizontal"
        result_file = flip_image(img_path, direction=d)
    elif action == "crop" and len(args) > 1:
        if len(args) > 2 and args[2] == "auto":
            result_file = crop_image(img_path, auto=True)
        elif len(args) >= 6:
            result_file = crop_image(img_path, left=args[2], top=args[3], right=args[4], bottom=args[5])
    elif action == "filter" and len(args) > 1:
        ft = args[2] if len(args) > 2 else "grayscale"
        result_file = apply_filter(img_path, filter_type=ft)
    elif action == "scanner" and len(args) > 1:
        result_file = doc_scanner_effect(img_path, output_path=args[2] if len(args) > 2 else None)
    elif action == "adjust" and len(args) > 1:
        br = float(args[2]) if len(args) > 2 else 1.0
        co = float(args[3]) if len(args) > 3 else 1.0
        sa = float(args[4]) if len(args) > 4 else 1.0
        sh = float(args[5]) if len(args) > 5 else 1.0
        result_file = adjust_image(img_path, brightness=br, contrast=co, saturation=sa, sharpness=sh)
    elif action == "watermark" and len(args) > 1:
        txt = args[2] if len(args) > 2 else "WATERMARK"
        pos = args[3] if len(args) > 3 else "bottom-right"
        col = args[4] if len(args) > 4 else "white"
        diag = True if pos == "diagonal" or (len(args) > 5 and args[5] == "true") else False
        result_file = add_watermark(img_path, txt, position=pos, color=col, diagonal=diag)
    elif action == "convert" and len(args) > 1:
        target_ext = args[2] if len(args) > 2 else "png"
        result_file = convert_format(img_path, target_ext=target_ext)
    elif action == "nobg" and len(args) > 1:
        th = args[2] if len(args) > 2 else 210
        result_file = remove_bg(img_path, threshold=th)
    elif action == "compress" and len(args) > 1:
        q = args[2] if len(args) > 2 else 75
        result_file = compress_image(img_path, quality=q)
    elif action == "create_image":
        out = args[1] if len(args) > 1 and args[1] != "-" else None
        w = args[2] if len(args) > 2 else 1080
        h = args[3] if len(args) > 3 else 1080
        bg = args[4] if len(args) > 4 else "#1E3C72"
        txt = args[5] if len(args) > 5 else "Gambar Baru"
        result_file = create_image(output_path=out, width=w, height=h, bg_color=bg, text=txt)
    elif action == "create_qr" and len(args) > 1:
        txt = args[1]
        out = args[2] if len(args) > 2 else None
        result_file = create_qr(text=txt, output_path=out)
    elif action == "ocr" and len(args) > 1:
        print(ocr_image(img_path))
    elif action == "info" and len(args) > 1:
        import json
        print(json.dumps(get_image_info(img_path), indent=2))

    # Prompt user or send to Telegram if a result file was generated
    if result_file and os.path.exists(result_file):
        prompt_send_to_telegram(result_file, force_send=send_tg)
