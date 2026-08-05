import os, glob
import pandas as pd
from reportlab.lib.pagesizes import A4, portrait
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

# 1. Load & Categorize Data
path = '/root/MyProject/OfficeCLI/REKENING KORAN/MANDIRI'
files = [
    ('account_statement_1140016063946_01 January 2026-31 January 2026_20260805140110.xlsx', '2026-01', 'Januari 2026'),
    ('account_statement_1140016063946_01 February 2026-28 February 2026_20260805140325.xlsx', '2026-02', 'Februari 2026'),
    ('account_statement_1140016063946_01 March 2026-31 March 2026_20260805140420.xlsx', '2026-03', 'Maret 2026'),
    ('account_statement_1140016063946_01 April 2026-30 April 2026_20260805140524.xlsx', '2026-04', 'April 2026'),
    ('account_statement_1140016063946_01 May 2026-31 May 2026_20260805140642.xlsx', '2026-05', 'Mei 2026'),
    ('account_statement_1140016063946_01 June 2026-30 June 2026_20260805140816.xlsx', '2026-06', 'Juni 2026'),
    ('account_statement_1140016063946_01 July 2026-31 July 2026_20260805140941.xlsx', '2026-07', 'Juli 2026')
]

dfs = []
for fname, code_m, name_m in files:
    fpath = os.path.join(path, fname)
    df = pd.read_excel(fpath)
    df_valid = df[df['Date'].notna()].copy()
    df_valid['PERIODE_CODE'] = code_m
    df_valid['PERIODE_NAME'] = name_m
    dfs.append(df_valid)

df_all = pd.concat(dfs, ignore_index=True)
df_all['Debit'] = df_all['Debit'].astype(float).fillna(0.0)
df_all['Credit'] = df_all['Credit'].astype(float).fillna(0.0)

def categorize_mandiri(row):
    d = (str(row['Description']) + ' ' + str(row['Description.1'])).upper()
    deb = float(row['Debit'])
    kre = float(row['Credit'])
    
    if kre > 0:
        if 'BUNGA' in d:
            return 'Pendapatan Bunga Bank'
        elif 'MANAMBANG MUARA ENIM' in d:
            return 'Penerimaan Penjualan (PT Manambang Muara Enim)'
        elif 'AKR CORPORINDO' in d:
            return 'Penerimaan Penjualan (PT AKR Corporindo)'
        elif 'BIO NUSANTARA' in d:
            return 'Penerimaan Penjualan (PT Bio Nusantara)'
        elif 'SRI KARYA LINTASINDO' in d:
            return 'Penerimaan Penjualan (PT Sri Karya Lintasindo)'
        elif 'NOAHTU SHIPYARD' in d:
            return 'Penerimaan Penjualan / Refund (PT Noahtu Shipyard)'
        elif 'DUA PUTRA PERKASA' in d:
            return 'Penerimaan Penjualan (PT Dua Putra Perkasa Pratama)'
        elif 'HILMAWAN INDRA' in d:
            return 'Transfer Masuk Pihak Ketiga (Hilmawan Indra Waskita)'
        elif 'BURHAN' in d:
            return 'Transfer Masuk Internal (Burhan)'
        elif 'HIJAU SEJAHTERA BERSAMA' in d or 'BRINIDJA/PT HIJAU' in d or 'BNINIDJA/HIJAU' in d or 'CENAIDJA/HIJAU' in d:
            return 'Pemindahbukuan Rekening Internal (HSB)'
        elif 'PRMA CR TRANSF' in d:
            return 'Transfer Masuk Pihak Ketiga (PRMA/ATM)'
        else:
            return 'Transfer Masuk Lainnya'
    else:
        if 'AUTO COLL' in d:
            return 'Pembayaran Angsuran Pinjaman (Auto Coll)'
        elif 'AKR CORPORINDO' in d:
            return 'Pembayaran Pembelian (PT AKR Corporindo)'
        elif 'BURHAN' in d:
            return 'Transfer Keluar Internal (Burhan)'
        elif 'WIJI INDRAYANI' in d:
            return 'Transfer Keluar (Wiji Indrayani)'
        elif 'TARIK TUNAI' in d:
            return 'Penarikan Tunai Cek'
        elif 'NOAHTU SHIPYARD' in d:
            return 'Pembayaran Vendor (PT Noahtu Shipyard)'
        elif 'LAUTAN BERLIAN' in d:
            return 'Pembayaran Vendor (PT Lautan Berlian)'
        elif 'HIJAU SEJAHTERA BERSAMA' in d or 'BRINIDJA/PT HIJAU' in d or 'BNINIDJA/HIJAU' in d or 'CENAIDJA/HIJAU' in d:
            return 'Pemindahbukuan Rekening Internal (HSB)'
        elif 'BIAYA ADM' in d or 'BUKU CEK' in d or 'METERAI' in d:
            return 'Biaya Administrasi Bank & Buku Cek'
        elif deb == 2500:
            return 'Biaya Admin Transfer'
        elif 'PAJAK' in d:
            return 'Pajak Bunga Tabungan'
        else:
            return 'Pengeluaran Lainnya'

df_all['KATEGORI'] = df_all.apply(categorize_mandiri, axis=1)

# Format Currency Helper
def fmt(val):
    if abs(val) < 0.01:
        return "-"
    return f"Rp {val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# Setup PDF document
pdf_filename = os.path.join(path, "Rekap_Rekening_Koran_Mandiri_2026.pdf")
doc = SimpleDocTemplate(
    pdf_filename,
    pagesize=portrait(A4),
    leftMargin=36,
    rightMargin=36,
    topMargin=36,
    bottomMargin=36
)

styles = getSampleStyleSheet()

# Color Palette (Mandiri Corporate Theme)
PRIMARY_COLOR = colors.HexColor('#0F4C81') # Mandiri Deep Blue
SECONDARY_COLOR = colors.HexColor('#F59E0B') # Gold Accent
TEXT_DARK = colors.HexColor('#1E293B')
BG_LIGHT = colors.HexColor('#F8FAFC')
BORDER_COLOR = colors.HexColor('#CBD5E1')
GREEN_COLOR = colors.HexColor('#1E7E34')
RED_COLOR = colors.HexColor('#BD2130')

title_style = ParagraphStyle(
    'DocTitle',
    parent=styles['Normal'],
    fontName='Helvetica-Bold',
    fontSize=18,
    leading=22,
    textColor=PRIMARY_COLOR,
    alignment=0
)

subtitle_style = ParagraphStyle(
    'DocSubTitle',
    parent=styles['Normal'],
    fontName='Helvetica',
    fontSize=10,
    leading=14,
    textColor=colors.HexColor('#64748B'),
    alignment=0
)

h2_style = ParagraphStyle(
    'H2',
    parent=styles['Normal'],
    fontName='Helvetica-Bold',
    fontSize=12,
    leading=16,
    textColor=PRIMARY_COLOR,
    spaceBefore=12,
    spaceAfter=6
)

cell_style = ParagraphStyle('Cell', fontName='Helvetica', fontSize=8, leading=10, textColor=TEXT_DARK)
cell_bold = ParagraphStyle('CellBold', fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=TEXT_DARK)
cell_right = ParagraphStyle('CellRight', fontName='Helvetica', fontSize=8, leading=10, alignment=2, textColor=TEXT_DARK)
cell_right_bold = ParagraphStyle('CellRightBold', fontName='Helvetica-Bold', fontSize=8, leading=10, alignment=2, textColor=TEXT_DARK)
cell_header = ParagraphStyle('CellHeader', fontName='Helvetica-Bold', fontSize=8.5, leading=11, alignment=1, textColor=colors.white)

elements = []

# Document Header Banner
elements.append(Paragraph("LAPORAN REKAPITULASI REKENING KORAN BANK MANDIRI", title_style))
elements.append(Paragraph("PT HIJAU SEJAHTERA BERSAMA | No. Rekening: <b>1140016063946</b> | Periode: Januari - Juli 2026", subtitle_style))
elements.append(Spacer(1, 10))

# KPI Cards Block Table
tot_cred = df_all['Credit'].sum()
tot_deb = df_all['Debit'].sum()
net_cf = tot_cred - tot_deb

kpi_data = [
    [
        Paragraph("<font size=7 color='#64748B'><b>TOTAL TRANSAKSI</b></font><br/><font size=12 color='#0F4C81'><b>214 Items</b></font>", ParagraphStyle('KPI', alignment=1)),
        Paragraph(f"<font size=7 color='#64748B'><b>TOTAL UANG MASUK (KREDIT)</b></font><br/><font size=11 color='#1E7E34'><b>{fmt(tot_cred)}</b></font>", ParagraphStyle('KPI', alignment=1)),
        Paragraph(f"<font size=7 color='#64748B'><b>TOTAL UANG KELUAR (DEBET)</b></font><br/><font size=11 color='#BD2130'><b>{fmt(tot_deb)}</b></font>", ParagraphStyle('KPI', alignment=1)),
        Paragraph(f"<font size=7 color='#64748B'><b>NET CASH FLOW (SURPLUS)</b></font><br/><font size=11 color='#0F4C81'><b>{fmt(net_cf)}</b></font>", ParagraphStyle('KPI', alignment=1)),
    ]
]
kpi_table = Table(kpi_data, colWidths=[1.3*inch, 2.5*inch, 2.5*inch, 2.2*inch])
kpi_table.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,-1), BG_LIGHT),
    ('BOX', (0,0), (-1,-1), 1, BORDER_COLOR),
    ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
    ('TOPPADDING', (0,0), (-1,-1), 8),
    ('BOTTOMPADDING', (0,0), (-1,-1), 8),
]))
elements.append(kpi_table)
elements.append(Spacer(1, 15))

# 1. Ringkasan Arus Kas Bulanan
elements.append(Paragraph("1. Ringkasan Arus Kas Bulanan (Januari - Juli 2026)", h2_style))

headers_m = ['Periode', 'Total Masuk / Kredit (Rp)', 'Total Keluar / Debet (Rp)', 'Net Cash Flow (Rp)', 'Tx']
table_data_m = [[Paragraph(h, cell_header) for h in headers_m]]

for fname, code_m, name_m in files:
    df_m = df_all[df_all['PERIODE_CODE'] == code_m]
    c_sum = df_m['Credit'].sum()
    d_sum = df_m['Debit'].sum()
    n_flow = c_sum - d_sum
    cnt = len(df_m)
    
    table_data_m.append([
        Paragraph(name_m, cell_style),
        Paragraph(fmt(c_sum), cell_right),
        Paragraph(fmt(d_sum), cell_right),
        Paragraph(fmt(n_flow), cell_right_bold),
        Paragraph(str(cnt), ParagraphStyle('C', parent=cell_style, alignment=1))
    ])

# Total row
table_data_m.append([
    Paragraph("<b>TOTAL</b>", cell_bold),
    Paragraph(fmt(tot_cred), cell_right_bold),
    Paragraph(fmt(tot_deb), cell_right_bold),
    Paragraph(fmt(net_cf), cell_right_bold),
    Paragraph(f"<b>{len(df_all)}</b>", ParagraphStyle('CB', parent=cell_bold, alignment=1))
])

t_m = Table(table_data_m, colWidths=[1.5*inch, 2.2*inch, 2.2*inch, 2.1*inch, 0.6*inch])
t_m.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), PRIMARY_COLOR),
    ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
    ('ROWBACKGROUNDS', (0,1), (-1,-2), [colors.white, BG_LIGHT]),
    ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#D0E1F9')),
    ('TOPPADDING', (0,0), (-1,-1), 4),
    ('BOTTOMPADDING', (0,0), (-1,-1), 4),
]))
elements.append(t_m)
elements.append(Spacer(1, 15))

# 2. Rekapitulasi Kategori Transaksi
elements.append(Paragraph("2. Rekapitulasi Kategori Transaksi", h2_style))

categories_list = [
    ('Penerimaan Penjualan (PT Manambang Muara Enim)', 'Uang Masuk'),
    ('Penerimaan Penjualan (PT Bio Nusantara)', 'Uang Masuk'),
    ('Penerimaan Penjualan (PT Sri Karya Lintasindo)', 'Uang Masuk'),
    ('Penerimaan Penjualan / Refund (PT Noahtu Shipyard)', 'Uang Masuk'),
    ('Penerimaan Penjualan (PT Dua Putra Perkasa Pratama)', 'Uang Masuk'),
    ('Penerimaan Penjualan (PT AKR Corporindo)', 'Uang Masuk'),
    ('Transfer Masuk Internal (Burhan)', 'Uang Masuk'),
    ('Transfer Masuk Pihak Ketiga (Hilmawan Indra Waskita)', 'Uang Masuk'),
    ('Transfer Masuk Pihak Ketiga (PRMA/ATM)', 'Uang Masuk'),
    ('Pendapatan Bunga Bank', 'Uang Masuk'),
    ('Transfer Keluar Internal (Burhan)', 'Uang Keluar'),
    ('Penarikan Tunai Cek', 'Uang Keluar'),
    ('Pemindahbukuan Rekening Internal (HSB)', 'Net'),
    ('Transfer Keluar (Wiji Indrayani)', 'Uang Keluar'),
    ('Pembayaran Pembelian (PT AKR Corporindo)', 'Uang Keluar'),
    ('Pembayaran Angsuran Pinjaman (Auto Coll)', 'Uang Keluar'),
    ('Pembayaran Vendor (PT Lautan Berlian)', 'Uang Keluar'),
    ('Biaya Administrasi Bank & Buku Cek', 'Uang Keluar'),
    ('Biaya Admin Transfer', 'Uang Keluar'),
    ('Pajak Bunga Tabungan', 'Uang Keluar')
]

headers_cat = ['No', 'Kategori Transaksi', 'Tipe', 'Debet / Keluar (Rp)', 'Kredit / Masuk (Rp)', 'Net Impact (Rp)', 'Tx', '% Total']
table_data_cat = [[Paragraph(h, cell_header) for h in headers_cat]]

tot_mutasi_all = tot_cred + tot_deb

for idx, (cat_name, cat_type) in enumerate(categories_list, 1):
    df_c = df_all[df_all['KATEGORI'] == cat_name]
    d_val = df_c['Debit'].sum()
    c_val = df_c['Credit'].sum()
    n_val = c_val - d_val
    cnt = len(df_c)
    pct = ((d_val + c_val) / tot_mutasi_all) * 100

    table_data_cat.append([
        Paragraph(str(idx), ParagraphStyle('C', parent=cell_style, alignment=1)),
        Paragraph(cat_name, cell_style),
        Paragraph(cat_type, ParagraphStyle('C', parent=cell_style, alignment=1)),
        Paragraph(fmt(d_val), cell_right),
        Paragraph(fmt(c_val), cell_right),
        Paragraph(fmt(n_val), cell_right_bold),
        Paragraph(str(cnt), ParagraphStyle('C', parent=cell_style, alignment=1)),
        Paragraph(f"{pct:.2f}%", cell_right)
    ])

table_data_cat.append([
    Paragraph("", cell_bold),
    Paragraph("<b>TOTAL KATEGORI</b>", cell_bold),
    Paragraph("-", ParagraphStyle('C', parent=cell_bold, alignment=1)),
    Paragraph(fmt(tot_deb), cell_right_bold),
    Paragraph(fmt(tot_cred), cell_right_bold),
    Paragraph(fmt(net_cf), cell_right_bold),
    Paragraph(f"<b>{len(df_all)}</b>", ParagraphStyle('CB', parent=cell_bold, alignment=1)),
    Paragraph("<b>100.00%</b>", cell_right_bold)
])

t_cat = Table(table_data_cat, colWidths=[0.3*inch, 2.5*inch, 0.7*inch, 1.4*inch, 1.4*inch, 1.4*inch, 0.4*inch, 0.6*inch])
t_cat.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), PRIMARY_COLOR),
    ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
    ('ROWBACKGROUNDS', (0,1), (-1,-2), [colors.white, BG_LIGHT]),
    ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#D0E1F9')),
    ('TOPPADDING', (0,0), (-1,-1), 3),
    ('BOTTOMPADDING', (0,0), (-1,-1), 3),
]))
elements.append(t_cat)

elements.append(PageBreak())

# 3. Top Transaksi Penerimaan Penjualan & Transfer Utama
elements.append(Paragraph("3. Top 15 Transaksi Penerimaan Terbesar", h2_style))

top_cr = df_all.sort_values(by='Credit', ascending=False).head(15)

headers_top = ['No', 'Tanggal', 'Kategori / Pelanggan', 'Deskripsi Transaction', 'Nominal Kredit (Rp)']
t_top_cr_data = [[Paragraph(h, cell_header) for h in headers_top]]

for idx, (_, r) in enumerate(top_cr.iterrows(), 1):
    desc = f"{r['Description']} {r['Description.1']}".strip()
    t_top_cr_data.append([
        Paragraph(str(idx), ParagraphStyle('C', parent=cell_style, alignment=1)),
        Paragraph(str(r['Date']), ParagraphStyle('C', parent=cell_style, alignment=1)),
        Paragraph(str(r['KATEGORI']), cell_bold),
        Paragraph(desc[:55], cell_style),
        Paragraph(fmt(r['Credit']), ParagraphStyle('CR', parent=cell_right_bold, textColor=GREEN_COLOR))
    ])

t_top_cr = Table(t_top_cr_data, colWidths=[0.4*inch, 0.9*inch, 2.3*inch, 3.2*inch, 1.8*inch])
t_top_cr.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), PRIMARY_COLOR),
    ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_LIGHT]),
    ('TOPPADDING', (0,0), (-1,-1), 3.5),
    ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
]))
elements.append(t_top_cr)
elements.append(Spacer(1, 15))

# 4. Top Transaksi Pengeluaran Terbesar
elements.append(Paragraph("4. Top 15 Transaksi Pengeluaran Terbesar", h2_style))

top_db = df_all.sort_values(by='Debit', ascending=False).head(15)

headers_top_db = ['No', 'Tanggal', 'Kategori Pengeluaran', 'Deskripsi Transaction', 'Nominal Debet (Rp)']
t_top_db_data = [[Paragraph(h, cell_header) for h in headers_top_db]]

for idx, (_, r) in enumerate(top_db.iterrows(), 1):
    desc = f"{r['Description']} {r['Description.1']}".strip()
    t_top_db_data.append([
        Paragraph(str(idx), ParagraphStyle('C', parent=cell_style, alignment=1)),
        Paragraph(str(r['Date']), ParagraphStyle('C', parent=cell_style, alignment=1)),
        Paragraph(str(r['KATEGORI']), cell_bold),
        Paragraph(desc[:55], cell_style),
        Paragraph(fmt(r['Debit']), ParagraphStyle('DB', parent=cell_right_bold, textColor=RED_COLOR))
    ])

t_top_db = Table(t_top_db_data, colWidths=[0.4*inch, 0.9*inch, 2.3*inch, 3.2*inch, 1.8*inch])
t_top_db.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), PRIMARY_COLOR),
    ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_LIGHT]),
    ('TOPPADDING', (0,0), (-1,-1), 3.5),
    ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
]))
elements.append(t_top_db)

# Build Document
doc.build(elements)
print(f"Successfully generated {pdf_filename}")
