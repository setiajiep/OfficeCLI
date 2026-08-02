# Panduan Lengkap Tool CLI PDF & Office

Dokumen ini berisi daftar alat CLI (Command Line Interface) PDF dan Office paling canggih yang telah berhasil diinstal di sistem beserta contoh penggunaannya.

---

## 1. Tool CLI PDF Canggih

### 🛠️ **pdfcpu** (Pengolahan PDF Berkecepatan Tinggi)
Tool serbaguna berbasis Go untuk manipulasi PDF lengkap.
- **Merge PDF**: `pdfcpu merge output.pdf file1.pdf file2.pdf`
- **Split PDF**: `pdfcpu split input.pdf out_dir/`
- **Ekstrak Halaman**: `pdfcpu extract -mode page input.pdf out_dir/`
- **Tambah Watermark**: `pdfcpu watermark add -mode text "CONFIDENTIAL" "" input.pdf output.pdf`
- **Proteksi Password**: `pdfcpu encrypt -userw user123 -ownerw admin123 input.pdf output.pdf`
- **Optimize / Compress**: `pdfcpu optimize input.pdf output.pdf`
- **Buat Booklet / N-Up**: `pdfcpu nup output.pdf 2 input.pdf`

---

### 🛠️ **pdftk** (PDF Toolkit)
Tool standar industri untuk manipulasi file PDF.
- **Gabung File**: `pdftk file1.pdf file2.pdf cat output gabungan.pdf`
- **Pisah Halaman Tertentu**: `pdftk input.pdf cat 1-5 8 10-end output hasil.pdf`
- **Putar Halaman (Rotate)**: `pdftk input.pdf cat 1east 2-end output rotated.pdf`
- **Isi Form PDF**: `pdftk form.pdf fill_form data.fdf output filled.pdf`
- **Stempel / Background**: `pdftk doc.pdf stamp watermark.pdf output stamped.pdf`

---

### 🛠️ **qpdf** (Analisis & Transformasi Struktural PDF)
Tool terbaik untuk enkripsi, dekripsi, perbaikan file rusak, dan optimasi web (linearization).
- **Dekripsi PDF (Hapus Password)**: `qpdf --password=SECRET --decrypt input.pdf output.pdf`
- **Optimasi Web (Linearize)**: `qpdf --linearize input.pdf web_optimized.pdf`
- **Perbaiki PDF Rusak**: `qpdf --qdf input_corrupt.pdf fixed.pdf`
- **Enkripsi AES-256**: `qpdf --encrypt userpass ownerpass 256 -- input.pdf encrypted.pdf`

---

### 🛠️ **ocrmypdf** (OCR Scanner PDF)
Menambahkan lapisan teks hasil OCR pada PDF berupa hasil scan/foto gambar agar dapat di-search dan di-copy text-nya. Menyiapkan bahasa Indonesia (`ind`) dan Inggris (`eng`).
- **Jalankan OCR (Bahasa Indonesia & Inggris)**: `ocrmypdf -l ind+eng scanned.pdf output_searchable.pdf`
- **OCR + Deskew (Luruskan Halaman Miring)**: `ocrmypdf --deskew --clean scanned.pdf output.pdf`

---

### 🛠️ **pdf2docx** (Konversi PDF ke Word)
Tool CLI Python untuk mengonversi PDF langsung menjadi dokumen Word (`.docx`) dengan mempertahankan format layout, tabel, dan gambar.
- **Konversi PDF ke DOCX**: `pdf2docx convert document.pdf document.docx`

---

### 🛠️ **Poppler-Utils** (Paket Ekstraksi & Konversi PDF)
Kumpulan utility sangat cepat untuk ekstraksi teks, gambar, dan konversi ke format gambar:
- **Konversi Halaman PDF ke Gambar (PNG/JPEG)**: `pdftoppm -png -r 150 document.pdf page`
- **Konversi PDF ke SVG/Vector**: `pdftocairo -svg document.pdf output.svg`
- **Ekstrak Seluruh Teks**: `pdftotext document.pdf text_output.txt`
- **Ekstrak Semua Gambar Dalam PDF**: `pdfimages -png document.pdf img_prefix`
- **Lihat Metadata PDF**: `pdfinfo document.pdf`
- **Gabung PDF Ringkas**: `pdfunite file1.pdf file2.pdf output.pdf`
- **Pisah Tiap Halaman PDF**: `pdfseparate input.pdf page_%d.pdf`

---

### 🛠️ **img2pdf** & **Ghostscript (gs)**
- **Convert Banyak Gambar ke 1 PDF (Lossless)**: `img2pdf *.jpg -o photo_album.pdf`
- **Kompresi PDF dengan Ghostscript**:
  `gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/ebook -dNOPAUSE -dQUIET -dBATCH -sOutputFile=compressed.pdf input.pdf`

---

### 🛠️ **Typst** (Typesetting Modern)
Alternatif LaTeX modern yang sangat cepat untuk membuat dokumen PDF berkualitas tinggi dari file teks/markup.
- **Kompilasi Dokumen Typst ke PDF**: `typst compile document.typ document.pdf`
- **Live Preview Document**: `typst watch document.typ`

---

## 2. Tool CLI Office (Word, Excel, PowerPoint)

### 📊 **LibreOffice / soffice** (Konverter Document Serbaguna Headless)
Mendukung konversi antar format Office (.docx, .xlsx, .pptx, .odt, .ods, .pdf, .html, .csv, dll) tanpa GUI.
- **Konversi DOCX / XLSX / PPTX ke PDF**:
  `libreoffice --headless --convert-to pdf document.docx`
- **Konversi DOCX ke HTML**:
  `libreoffice --headless --convert-to html document.docx`
- **Konversi ODT ke DOCX**:
  `libreoffice --headless --convert-to docx document.odt`

---

### 📊 **Pandoc** (Swiss-Army Knife Konversi Dokumen)
Konversi antar berbagai format mark-up dan dokumen (.md, .docx, .pdf, .html, .epub, .tex, dll).
- **Markdown ke DOCX**: `pandoc input.md -o output.docx`
- **DOCX ke Markdown**: `pandoc input.docx -o output.md`
- **Markdown ke PDF**: `pandoc input.md -o output.pdf`
- **HTML ke DOCX**: `pandoc index.html -o document.docx`

---

### 📊 **csvkit** (Olah Excel & CSV via CLI)
Toolkit super canggih untuk memproses file CSV dan Excel (.xlsx/.xls) langsung dari terminal.
- **Konversi Excel (.xlsx) ke CSV**: `in2csv sales.xlsx > sales.csv`
- **Lihat CSV dengan Tampilan Tabel Rapi**: `csvlook sales.csv | head -n 20`
- **Statistik & Analisis Ringkas Data CSV**: `csvstat sales.csv`
- **Query SQL langsung pada File CSV**: `csvsql --query "SELECT * FROM sales WHERE total > 100" sales.csv`

---

### 📊 **Utility Ekstraksi Ringkas**
- **docx2txt**: `docx2txt document.docx text.txt` (Ekstrak teks dari file Word)
- **xlsx2csv**: `xlsx2csv spreadsheet.xlsx spreadsheet.csv` (Konversi XLSX ke CSV)
- **odt2txt**: `odt2txt document.odt` (Ekstrak teks dari file ODT)

---

## 3. Python Automation Libraries (Terinstal)
Sudah terpasang library Python berikut untuk kebutuhan scripting & otomasi kustom:
- `pymupdf` (`fitz`) - manipulasi & rendering PDF super cepat
- `pdfplumber` - ekstraksi tabel & posisi elemen PDF
- `pypdf` - manipulasi dokumen PDF via Python
- `python-docx` - membuat & mengedit dokumen Word (`.docx`)
- `openpyxl` - membuat & mengedit spreadsheet Excel (`.xlsx`)
- `python-pptx` - membuat & mengedit slide PowerPoint (`.pptx`)
- `reportlab` - pegenrasian file PDF secara programatis
