#!/usr/bin/env python3
import os
import sys
import io
import subprocess

def convert_to_pdf(input_path, output_dir=None):
    if not os.path.exists(input_path):
        print(f"File not found: {input_path}")
        return None
    
    if output_dir is None:
        output_dir = os.path.dirname(os.path.abspath(input_path))
        
    cmd = ["soffice", "--headless", "--convert-to", "pdf", input_path, "--outdir", output_dir]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        filename = os.path.splitext(os.path.basename(input_path))[0] + ".pdf"
        out_pdf = os.path.join(output_dir, filename)
        if os.path.exists(out_pdf):
            print(f"Successfully converted to PDF: {out_pdf}")
            return out_pdf
    except Exception as e:
        print(f"Conversion failed: {e}")
    return None

def extract_text(file_path):
    if not os.path.exists(file_path):
        return ""
    
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == ".pdf":
        try:
            import pdfplumber
            text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text += (page.extract_text() or "") + "\n"
            return text.strip()
        except Exception:
            try:
                res = subprocess.run(["pdftotext", file_path, "-"], capture_output=True, text=True)
                return res.stdout.strip()
            except Exception as e:
                return f"Error extracting PDF: {e}"

    elif ext in [".docx", ".doc"]:
        try:
            import docx
            doc = docx.Document(file_path)
            return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        except Exception as e:
            return f"Error extracting DOCX: {e}"

    elif ext in [".xlsx", ".xls", ".csv"]:
        try:
            import pandas as pd
            if ext == ".csv":
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            return df.to_string()
        except Exception as e:
            return f"Error reading Spreadsheet: {e}"

    elif ext in [".txt", ".md", ".json", ".py", ".html", ".css", ".js"]:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception as e:
            return f"Error reading text file: {e}"

    return "Unsupported file format for text extraction."

def stamp_image_on_pdf(pdf_path, img_path, output_path=None, page_num=-1, x=350, y=80, width=150, height=60):
    """
    Stamp an image (signature, logo, watermark, stamp) onto a PDF page.
    page_num: -1 for last page, or 1-based page number (e.g. 1 for page 1).
    x, y: coordinates from bottom-left corner in points (1 inch = 72 pt).
    width, height: image dimensions in points.
    """
    from pypdf import PdfReader, PdfWriter
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader

    if not os.path.exists(pdf_path):
        print(f"PDF file not found: {pdf_path}")
        return None
    if not os.path.exists(img_path):
        print(f"Image file not found: {img_path}")
        return None

    if output_path is None:
        base, ext = os.path.splitext(pdf_path)
        output_path = f"{base}_signed.pdf"

    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)

    if page_num == -1 or page_num > total_pages:
        target_page_idx = total_pages - 1
    else:
        target_page_idx = max(0, page_num - 1)

    target_page = reader.pages[target_page_idx]
    page_width = float(target_page.mediabox.width)
    page_height = float(target_page.mediabox.height)

    # Position presets: 'bottom-right' (default), 'bottom-left', 'center'
    if isinstance(x, str):
        pos = x.lower()
        if pos == "bottom-right":
            x = page_width - width - 50
            y = 50
        elif pos == "bottom-left":
            x = 50
            y = 50
        elif pos == "center":
            x = (page_width - width) / 2
            y = (page_height - height) / 2
        else:
            x = page_width - width - 50
            y = 50

    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=(page_width, page_height))
    
    img = ImageReader(img_path)
    can.drawImage(img, float(x), float(y), width=float(width), height=float(height), mask='auto')
    can.save()

    packet.seek(0)
    overlay_pdf = PdfReader(packet)
    overlay_page = overlay_pdf.pages[0]

    # Merge overlay image onto the target page
    target_page.merge_page(overlay_page)

    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    with open(output_path, "wb") as f:
        writer.write(f)

    print(f"Successfully stamped signature/image onto PDF: {output_path}")
    return output_path

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 office_tools.py <convert_pdf|extract_text|stamp_pdf> <args...>")
        sys.exit(1)
        
    action = sys.argv[1]
    
    if action == "convert_pdf" and len(sys.argv) > 2:
        out = convert_to_pdf(sys.argv[2])
        if out:
            print(out)
    elif action == "extract_text" and len(sys.argv) > 2:
        print(extract_text(sys.argv[2]))
    elif action == "stamp_pdf" and len(sys.argv) > 3:
        pdf_path = sys.argv[2]
        img_path = sys.argv[3]
        output_path = sys.argv[4] if len(sys.argv) > 4 and sys.argv[4] != "-" else None
        page_num = int(sys.argv[5]) if len(sys.argv) > 5 else -1
        x = float(sys.argv[6]) if len(sys.argv) > 6 and sys.argv[6].replace('.','',1).isdigit() else (sys.argv[6] if len(sys.argv) > 6 else "bottom-right")
        y = float(sys.argv[7]) if len(sys.argv) > 7 and sys.argv[7].replace('.','',1).isdigit() else 80
        width = float(sys.argv[8]) if len(sys.argv) > 8 else 150
        height = float(sys.argv[9]) if len(sys.argv) > 9 else 60

        out = stamp_image_on_pdf(pdf_path, img_path, output_path, page_num, x, y, width, height)
        if out:
            print(out)
