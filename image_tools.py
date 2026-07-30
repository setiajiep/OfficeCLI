#!/usr/bin/env python3
import os
import sys
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps, ImageDraw, ImageFont

def resize_image(img_path, width=None, height=None, output_path=None):
    if not os.path.exists(img_path):
        return None
    if output_path is None:
        base, ext = os.path.splitext(img_path)
        output_path = f"{base}_resized{ext}"

    with Image.open(img_path) as img:
        orig_w, orig_h = img.size
        if width and not height:
            height = int(orig_h * (width / orig_w))
        elif height and not width:
            width = int(orig_w * (height / orig_h))
        elif not width and not height:
            width, height = orig_w, orig_h

        resized = img.resize((int(width), int(height)), Image.Resampling.LANCZOS)
        resized.save(output_path)
        print(f"Successfully resized image: {output_path}")
        return output_path

def rotate_image(img_path, angle=90, output_path=None):
    if not os.path.exists(img_path):
        return None
    if output_path is None:
        base, ext = os.path.splitext(img_path)
        output_path = f"{base}_rotated{ext}"

    with Image.open(img_path) as img:
        rotated = img.rotate(-float(angle), expand=True)
        rotated.save(output_path)
        print(f"Successfully rotated image ({angle}°): {output_path}")
        return output_path

def flip_image(img_path, direction='horizontal', output_path=None):
    if not os.path.exists(img_path):
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
        print(f"Successfully flipped image ({direction}): {output_path}")
        return output_path

def crop_image(img_path, left=None, top=None, right=None, bottom=None, auto=False, output_path=None):
    """
    Crop an image using bounding box or auto-crop whitespace/transparent edges.
    """
    if not os.path.exists(img_path):
        return None
    if output_path is None:
        base, ext = os.path.splitext(img_path)
        output_path = f"{base}_cropped{ext}"

    with Image.open(img_path) as img:
        w, h = img.size
        if auto:
            # Auto-crop non-empty bounding box
            if img.mode == 'RGBA':
                bbox = img.getbbox()
            else:
                gray = img.convert('L')
                inverted = ImageOps.invert(gray)
                bbox = inverted.getbbox()
            if bbox:
                cropped = img.crop(bbox)
            else:
                cropped = img
        else:
            l = int(left) if left is not None else 0
            t = int(top) if top is not None else 0
            r = int(right) if right is not None else w
            b = int(bottom) if bottom is not None else h
            cropped = img.crop((l, t, r, b))

        cropped.save(output_path)
        print(f"Successfully cropped image: {output_path}")
        return output_path

def apply_filter(img_path, filter_type='grayscale', output_path=None):
    if not os.path.exists(img_path):
        return None
    if output_path is None:
        base, ext = os.path.splitext(img_path)
        output_path = f"{base}_{filter_type}{ext}"

    with Image.open(img_path) as img:
        ftype = filter_type.lower()
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
                print(f"Successfully applied vintage filter: {output_path}")
                return output_path
            res = img
        elif ftype == 'sketch':
            img_cv = cv2.imread(img_path)
            if img_cv is not None:
                gray, sketch = cv2.pencilSketch(img_cv, sigma_s=60, sigma_r=0.07, shade_factor=0.05)
                cv2.imwrite(output_path, sketch)
                print(f"Successfully applied sketch filter: {output_path}")
                return output_path
            res = img
        else:
            res = img

        res.save(output_path)
        print(f"Successfully applied {filter_type} filter: {output_path}")
        return output_path

def adjust_image(img_path, brightness=1.0, contrast=1.0, saturation=1.0, sharpness=1.0, output_path=None):
    if not os.path.exists(img_path):
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
        print(f"Successfully adjusted image: {output_path}")
        return output_path

def add_watermark(img_path, text, position='bottom-right', font_size=36, color="white", alpha=200, diagonal=False, output_path=None):
    """
    Add text watermark with custom positioning, font size, color, alpha transparency, or diagonal angle.
    """
    if not os.path.exists(img_path):
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
            # Create a larger transparent canvas for angled watermark text
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
            else: # bottom-right
                x = w - text_w - 30
                y = h - text_h - 30

            draw.rectangle([x - 10, y - 5, x + text_w + 10, y + text_h + 5], fill=(0, 0, 0, int(alpha * 0.5)))
            draw.text((x, y), text, font=font, fill=text_fill)

            out_img = Image.alpha_composite(base_img, txt_img)

        if output_path.lower().endswith(('.jpg', '.jpeg')):
            out_img = out_img.convert("RGB")
        out_img.save(output_path)
        print(f"Successfully added watermark: {output_path}")
        return output_path

def convert_format(img_path, target_ext="png", output_path=None):
    if not os.path.exists(img_path):
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
        print(f"Successfully converted format to {target_ext}: {output_path}")
        return output_path

def remove_bg(img_path, output_path=None, threshold=210):
    """Automatic background removal with edge smoothing for document / signature images"""
    if not os.path.exists(img_path):
        return None
    if output_path is None:
        base, _ = os.path.splitext(img_path)
        output_path = f"{base}_nobg.png"

    img_cv = cv2.imread(img_path)
    if img_cv is None:
        return None

    # Convert to RGBA
    b_channel, g_channel, r_channel = cv2.split(img_cv)
    
    # Detect light background with inverse thresholding
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    _, alpha = cv2.threshold(gray, int(threshold), 255, cv2.THRESH_BINARY_INV)

    # Apply light Gaussian blur on alpha mask for smooth edges
    alpha = cv2.GaussianBlur(alpha, (3, 3), 0)

    rgba = cv2.merge((b_channel, g_channel, r_channel, alpha))
    cv2.imwrite(output_path, rgba)
    print(f"Successfully removed white background: {output_path}")
    return output_path

def compress_image(img_path, quality=75, output_path=None):
    """Compress image size while preserving visual quality"""
    if not os.path.exists(img_path):
        return None
    if output_path is None:
        base, ext = os.path.splitext(img_path)
        output_path = f"{base}_compressed{ext}"

    with Image.open(img_path) as img:
        if img.mode in ['RGBA', 'LA', 'P'] and output_path.lower().endswith(('.jpg', '.jpeg')):
            img = img.convert('RGB')
        img.save(output_path, optimize=True, quality=int(quality))
        print(f"Successfully compressed image (quality={quality}): {output_path}")
        return output_path

def ocr_image(img_path, lang='ind+eng'):
    """Optical Character Recognition (OCR) to extract text from images/photos"""
    if not os.path.exists(img_path):
        return "File gambar tidak ditemukan."
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
                "size_kb": size_kb
            }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 image_tools.py <resize|rotate|flip|crop|filter|adjust|watermark|convert|nobg|compress|info> <img_path> [args...]")
        sys.exit(1)

    action = sys.argv[1]
    img_path = sys.argv[2] if len(sys.argv) > 2 else ""

    if action == "resize" and len(sys.argv) > 3:
        w = sys.argv[3] if len(sys.argv) > 3 else None
        h = sys.argv[4] if len(sys.argv) > 4 else None
        resize_image(img_path, width=int(w) if w else None, height=int(h) if h else None)
    elif action == "rotate" and len(sys.argv) > 3:
        rotate_image(img_path, angle=float(sys.argv[3]))
    elif action == "flip":
        d = sys.argv[3] if len(sys.argv) > 3 else "horizontal"
        flip_image(img_path, direction=d)
    elif action == "crop":
        if len(sys.argv) > 3 and sys.argv[3] == "auto":
            crop_image(img_path, auto=True)
        elif len(sys.argv) >= 7:
            crop_image(img_path, left=sys.argv[3], top=sys.argv[4], right=sys.argv[5], bottom=sys.argv[6])
    elif action == "filter" and len(sys.argv) > 3:
        apply_filter(img_path, filter_type=sys.argv[3])
    elif action == "adjust":
        br = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
        co = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
        sa = float(sys.argv[5]) if len(sys.argv) > 5 else 1.0
        sh = float(sys.argv[6]) if len(sys.argv) > 6 else 1.0
        adjust_image(img_path, brightness=br, contrast=co, saturation=sa, sharpness=sh)
    elif action == "watermark" and len(sys.argv) > 3:
        txt = sys.argv[3]
        pos = sys.argv[4] if len(sys.argv) > 4 else "bottom-right"
        col = sys.argv[5] if len(sys.argv) > 5 else "white"
        diag = True if pos == "diagonal" or (len(sys.argv) > 6 and sys.argv[6] == "true") else False
        add_watermark(img_path, txt, position=pos, color=col, diagonal=diag)
    elif action == "convert" and len(sys.argv) > 3:
        convert_format(img_path, target_ext=sys.argv[3])
    elif action == "nobg":
        th = sys.argv[3] if len(sys.argv) > 3 else 210
        remove_bg(img_path, threshold=th)
    elif action == "compress":
        q = sys.argv[3] if len(sys.argv) > 3 else 75
        compress_image(img_path, quality=q)
    elif action == "ocr":
        print(ocr_image(img_path))
    elif action == "info":
        print(get_image_info(img_path))
