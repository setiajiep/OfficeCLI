#!/usr/bin/env python3
import os
import sys
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

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 office_tools.py <convert_pdf|extract_text> <file_path>")
        sys.exit(1)
        
    action = sys.argv[1]
    file_path = sys.argv[2] if len(sys.argv) > 2 else ""
    
    if action == "convert_pdf":
        out = convert_to_pdf(file_path)
        if out:
            print(out)
    elif action == "extract_text":
        print(extract_text(file_path))
