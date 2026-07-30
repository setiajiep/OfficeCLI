#!/usr/bin/env python3
import os
import sys
import io
import time
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

    elif ext in [".pptx", ".ppt"]:
        try:
            import pptx
            prs = pptx.Presentation(file_path)
            slides_text = []
            for i, slide in enumerate(prs.slides, 1):
                slides_text.append(f"--- Slide {i} ---")
                for shape in slide.shapes:
                    if shape.has_text_frame:
                        for paragraph in shape.text_frame.paragraphs:
                            if paragraph.text.strip():
                                slides_text.append(paragraph.text.strip())
            return "\n".join(slides_text)
        except Exception as e:
            return f"Error extracting PowerPoint: {e}"

    elif ext in [".xlsx", ".xls", ".csv"]:
        try:
            import pandas as pd
            if ext == ".csv":
                df = pd.read_csv(file_path)
                return df.to_string()
            else:
                sheets_dict = pd.read_excel(file_path, sheet_name=None)
                out_str = []
                for sheet_name, df in sheets_dict.items():
                    out_str.append(f"--- Sheet: {sheet_name} ---")
                    out_str.append(df.to_string())
                return "\n\n".join(out_str)
        except Exception as e:
            return f"Error reading Spreadsheet: {e}"

    elif ext in [".txt", ".md", ".json", ".py", ".html", ".css", ".js", ".sh", ".yaml", ".yml"]:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception as e:
            return f"Error reading text file: {e}"

    return "Unsupported file format for text extraction."

def get_doc_info(file_path):
    """Retrieve summary metadata for documents and media"""
    if not os.path.exists(file_path):
        return {}
    
    ext = os.path.splitext(file_path)[1].lower()
    info = {"size_kb": os.path.getsize(file_path) / 1024}

    if ext == ".pdf":
        try:
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            info["pages"] = len(reader.pages)
        except Exception:
            pass
    elif ext in [".docx", ".doc"]:
        try:
            import docx
            doc = docx.Document(file_path)
            info["paragraphs"] = len(doc.paragraphs)
            info["tables"] = len(doc.tables)
        except Exception:
            pass
    elif ext in [".pptx", ".ppt"]:
        try:
            import pptx
            prs = pptx.Presentation(file_path)
            info["slides"] = len(prs.slides)
        except Exception:
            pass
    elif ext in [".xlsx", ".xls"]:
        try:
            import pandas as pd
            xl = pd.ExcelFile(file_path)
            info["sheets"] = xl.sheet_names
        except Exception:
            pass
    elif ext in [".png", ".jpg", ".jpeg", ".webp", ".bmp"]:
        try:
            from PIL import Image
            with Image.open(file_path) as img:
                info["dimensions"] = f"{img.width}x{img.height}"
                info["mode"] = img.mode
        except Exception:
            pass
    return info

def merge_pdfs(pdf_list, output_path=None):
    """Merge multiple PDF files into one single PDF document"""
    from pypdf import PdfWriter
    if not pdf_list:
        print("No input PDF files provided for merging.")
        return None

    valid_files = [f for f in pdf_list if os.path.exists(f) and f.lower().endswith(".pdf")]
    if not valid_files:
        print("No valid PDF files found in arguments.")
        return None

    if output_path is None:
        first_dir = os.path.dirname(os.path.abspath(valid_files[0]))
        output_path = os.path.join(first_dir, f"merged_{int(time.time())}.pdf")

    writer = PdfWriter()
    merged_count = 0
    for pdf in valid_files:
        try:
            writer.append(pdf)
            merged_count += 1
        except Exception as e:
            print(f"Error appending PDF '{pdf}': {e}")

    if merged_count == 0:
        return None

    with open(output_path, "wb") as f:
        writer.write(f)

    print(f"Successfully merged {merged_count} PDF files: {output_path}")
    return output_path

def split_pdf(pdf_path, pages="1", output_path=None):
    """
    Extract specific page numbers or page ranges from a PDF.
    pages: string format e.g. "1-3, 5, 8"
    """
    from pypdf import PdfReader, PdfWriter
    if not os.path.exists(pdf_path):
        print(f"PDF file not found: {pdf_path}")
        return None

    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)
    selected_indices = set()

    for part in str(pages).split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            sp = part.split("-")
            try:
                s, e = int(sp[0]), int(sp[1])
                for p in range(max(1, s), min(total_pages, e) + 1):
                    selected_indices.add(p - 1)
            except ValueError:
                pass
        else:
            try:
                p = int(part)
                if 1 <= p <= total_pages:
                    selected_indices.add(p - 1)
            except ValueError:
                pass

    if not selected_indices:
        print("No valid page numbers selected for extraction.")
        return None

    writer = PdfWriter()
    for idx in sorted(selected_indices):
        writer.add_page(reader.pages[idx])

    if output_path is None:
        base, _ = os.path.splitext(pdf_path)
        output_path = f"{base}_pages_{pages.replace(' ', '')}.pdf"

    with open(output_path, "wb") as f:
        writer.write(f)

    print(f"Successfully extracted pages ({pages}) to PDF: {output_path}")
    return output_path

def stamp_image_on_pdf(pdf_path, img_path, output_path=None, page_num="-1", x=350, y=80, width=150, height=60, auto_nobg=True, rotation=0):
    """
    Stamp an image (signature, logo, watermark, stamp) onto PDF page(s).
    page_num: '-1' or 'last' for last page, 'all' for every page, or 1-based page number / list of numbers (e.g. '1', '1,2').
    x, y: coordinates from bottom-left corner in points or preset strings ('bottom-right', 'bottom-left', 'center', 'top-right').
    width, height: dimensions in points.
    auto_nobg: if True, removes white background from signature image before stamping.
    rotation: rotation angle in degrees.
    """
    from pypdf import PdfReader, PdfWriter
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader
    from PIL import Image

    if not os.path.exists(pdf_path):
        print(f"PDF file not found: {pdf_path}")
        return None
    if not os.path.exists(img_path):
        print(f"Image file not found: {img_path}")
        return None

    if output_path is None:
        base, _ = os.path.splitext(pdf_path)
        output_path = f"{base}_signed.pdf"

    # Pre-process image to remove white background if requested
    stamp_img_path = img_path
    if auto_nobg:
        try:
            with Image.open(img_path).convert("RGBA") as raw_img:
                import numpy as np
                data = np.array(raw_img)
                r, g, b, a = data[:,:,0], data[:,:,1], data[:,:,2], data[:,:,3]
                # Treat near-white pixels (RGB > 210) as transparent
                white_mask = (r > 210) & (g > 210) & (b > 210)
                data[:, :, 3][white_mask] = 0
                clean_img = Image.fromarray(data)
                
                temp_nobg = f"/tmp/stamp_temp_{int(time.time())}.png"
                clean_img.save(temp_nobg)
                stamp_img_path = temp_nobg
        except Exception as e:
            stamp_img_path = img_path

    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)

    # Determine targeted page indices (0-based)
    str_p = str(page_num).lower().strip()
    target_indices = []

    if str_p in ["-1", "last"]:
        target_indices = [total_pages - 1]
    elif str_p in ["all", "*"]:
        target_indices = list(range(total_pages))
    else:
        for part in str_p.split(","):
            part = part.strip()
            try:
                val = int(part)
                if val == -1:
                    target_indices.append(total_pages - 1)
                elif 1 <= val <= total_pages:
                    target_indices.append(val - 1)
            except ValueError:
                pass

    if not target_indices:
        target_indices = [total_pages - 1]

    writer = PdfWriter()
    img_reader = ImageReader(stamp_img_path)

    for i, page in enumerate(reader.pages):
        if i in target_indices:
            page_width = float(page.mediabox.width)
            page_height = float(page.mediabox.height)

            calc_x, calc_y = x, y
            if isinstance(calc_x, str):
                pos = calc_x.lower()
                if pos in ["bottom-right", "br"]:
                    calc_x = page_width - width - 50
                    calc_y = 50
                elif pos in ["bottom-left", "bl"]:
                    calc_x = 50
                    calc_y = 50
                elif pos in ["top-right", "tr"]:
                    calc_x = page_width - width - 50
                    calc_y = page_height - height - 50
                elif pos in ["top-left", "tl"]:
                    calc_x = 50
                    calc_y = page_height - height - 50
                elif pos in ["center", "c"]:
                    calc_x = (page_width - width) / 2
                    calc_y = (page_height - height) / 2
                else:
                    calc_x = page_width - width - 50
                    calc_y = 50

            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize=(page_width, page_height))
            
            if rotation != 0:
                can.saveState()
                can.translate(float(calc_x) + width/2, float(calc_y) + height/2)
                can.rotate(float(rotation))
                can.drawImage(img_reader, -width/2, -height/2, width=float(width), height=float(height), mask='auto')
                can.restoreState()
            else:
                can.drawImage(img_reader, float(calc_x), float(calc_y), width=float(width), height=float(height), mask='auto')
            
            can.save()
            packet.seek(0)

            overlay_pdf = PdfReader(packet)
            page.merge_page(overlay_pdf.pages[0])

        writer.add_page(page)

    with open(output_path, "wb") as f:
        writer.write(f)

    # Clean temporary background-removed file if created
    if stamp_img_path != img_path and os.path.exists(stamp_img_path):
        try:
            os.remove(stamp_img_path)
        except Exception:
            pass

    print(f"Successfully stamped image onto PDF: {output_path}")
    return output_path

def create_zip(target_path, output_zip=None):
    """Zip a file or entire folder into a .zip archive"""
    import zipfile
    if not os.path.exists(target_path):
        return None
    if output_zip is None:
        base = os.path.basename(os.path.abspath(target_path))
        parent = os.path.dirname(os.path.abspath(target_path))
        output_zip = os.path.join(parent, f"{base}.zip")

    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        if os.path.isdir(target_path):
            for root, dirs, files in os.walk(target_path):
                for file in files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, os.path.dirname(target_path))
                    zipf.write(full_path, rel_path)
        else:
            zipf.write(target_path, os.path.basename(target_path))

    print(f"Successfully created zip archive: {output_zip}")
    return output_zip

def extract_zip(zip_path, extract_dir=None):
    """Extract a .zip archive into target directory"""
    import zipfile
    if not os.path.exists(zip_path):
        return None
    if extract_dir is None:
        extract_dir = os.path.dirname(os.path.abspath(zip_path))

    with zipfile.ZipFile(zip_path, 'r') as zipf:
        zipf.extractall(extract_dir)

    print(f"Successfully extracted zip to: {extract_dir}")
    return extract_dir

def parse_float_arg(val, default):
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 office_tools.py <convert_pdf|extract_text|stamp_pdf|merge|split|info> <args...>")
        sys.exit(1)
        
    action = sys.argv[1]
    
    if action == "convert_pdf" and len(sys.argv) > 2:
        out = convert_to_pdf(sys.argv[2])
        if out:
            print(out)
    elif action == "extract_text" and len(sys.argv) > 2:
        print(extract_text(sys.argv[2]))
    elif action == "info" and len(sys.argv) > 2:
        print(get_doc_info(sys.argv[2]))
    elif action == "merge" and len(sys.argv) > 3:
        out_file = sys.argv[2] if sys.argv[2] != "-" else None
        pdf_inputs = sys.argv[3:]
        if not out_file and pdf_inputs:
            out = merge_pdfs(pdf_inputs)
        else:
            out = merge_pdfs(pdf_inputs, output_path=out_file)
        if out:
            print(out)
    elif action == "split" and len(sys.argv) > 3:
        pdf_file = sys.argv[2]
        pages_sel = sys.argv[3]
        out_file = sys.argv[4] if len(sys.argv) > 4 and sys.argv[4] != "-" else None
        out = split_pdf(pdf_file, pages=pages_sel, output_path=out_file)
        if out:
            print(out)
    elif action == "stamp_pdf" and len(sys.argv) > 3:
        pdf_path = sys.argv[2]
        img_path = sys.argv[3]
        output_path = sys.argv[4] if len(sys.argv) > 4 and sys.argv[4] != "-" else None
        
        page_num = sys.argv[5] if len(sys.argv) > 5 else "-1"

        arg6 = sys.argv[6] if len(sys.argv) > 6 else "bottom-right"
        try:
            x = float(arg6)
        except ValueError:
            x = arg6

        y = parse_float_arg(sys.argv[7] if len(sys.argv) > 7 else None, 80)
        width = parse_float_arg(sys.argv[8] if len(sys.argv) > 8 else None, 150)
        height = parse_float_arg(sys.argv[9] if len(sys.argv) > 9 else None, 60)

        out = stamp_image_on_pdf(pdf_path, img_path, output_path, page_num, x, y, width, height)
        if out:
            print(out)
    elif action == "zip" and len(sys.argv) > 2:
        out = create_zip(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
        if out:
            print(out)
    elif action == "unzip" and len(sys.argv) > 2:
        out = extract_zip(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
        if out:
            print(out)
