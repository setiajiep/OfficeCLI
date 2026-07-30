import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Register LiberationSans fonts for crisp typography
font_dir = '/usr/share/fonts/truetype/liberation/'
if os.path.exists(os.path.join(font_dir, 'LiberationSans-Regular.ttf')):
    pdfmetrics.registerFont(TTFont('LiberationSans', os.path.join(font_dir, 'LiberationSans-Regular.ttf')))
    pdfmetrics.registerFont(TTFont('LiberationSans-Bold', os.path.join(font_dir, 'LiberationSans-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('LiberationSans-Italic', os.path.join(font_dir, 'LiberationSans-Italic.ttf')))
    pdfmetrics.registerFont(TTFont('LiberationSans-BoldItalic', os.path.join(font_dir, 'LiberationSans-BoldItalic.ttf')))
    FONT_NAME = 'LiberationSans'
    FONT_BOLD = 'LiberationSans-Bold'
else:
    FONT_NAME = 'Helvetica'
    FONT_BOLD = 'Helvetica-Bold'

class SinglePageCanvas(canvas.Canvas):
    """
    Canvas to draw decorative background header/footer bars and layout accents.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_decorations(self, page_count):
        self.saveState()
        width, height = A4
        
        # Premium Palette
        PRIMARY = colors.HexColor('#0D5C3A')   # Islamic Deep Emerald Green
        GOLD = colors.HexColor('#D4AF37')      # Accent Gold
        DARK_BAR = colors.HexColor('#083C25')

        # Top Header Accent Bar
        self.setFillColor(PRIMARY)
        self.rect(0, height - 10, width, 10, fill=1, stroke=0)
        self.setFillColor(GOLD)
        self.rect(0, height - 13, width, 3, fill=1, stroke=0)

        # Bottom Footer Accent Bar
        self.setFillColor(DARK_BAR)
        self.rect(0, 0, width, 18, fill=1, stroke=0)
        self.setFillColor(GOLD)
        self.rect(0, 18, width, 2, fill=1, stroke=0)

        # Footer Text
        self.setFont(FONT_NAME, 8)
        self.setFillColor(colors.white)
        self.drawString(32, 5, "Pondok Pesantren Wali Barokah • SOP & Petunjuk Teknis Penjemputan Santri")
        
        page_str = f"Dokumen Resmi | Halaman {self._pageNumber} dari {page_count}"
        self.drawRightString(width - 32, 5, page_str)

        self.restoreState()


def build_pdf(filename="Teknis_Penjemputan_Santri_PPWB.pdf"):
    pdf_path = filename
    
    # Custom margins for optimal single page A4 layout
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        leftMargin=32,
        rightMargin=32,
        topMargin=26,
        bottomMargin=28
    )

    width, height = A4
    content_width = width - 64

    styles = getSampleStyleSheet()

    # Color Scheme
    PRIMARY = colors.HexColor('#0D5C3A')       # Deep Emerald Green
    PRIMARY_TINT = colors.HexColor('#EBF4F0')  # Soft Green Tint
    GOLD = colors.HexColor('#C59B27')          # Gold Accent
    GOLD_LIGHT = colors.HexColor('#FFFDF2')    # Light Gold Callout
    DARK_TEXT = colors.HexColor('#1F2937')     # Dark Neutral
    MUTED_TEXT = colors.HexColor('#4B5563')    # Slate Gray
    BORDER_COLOR = colors.HexColor('#D1D5DB')  # Card Border
    CARD_BG = colors.HexColor('#FAFAFA')       # Card Fill

    # Paragraph Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName=FONT_BOLD,
        fontSize=13.5,
        leading=17.5,
        textColor=colors.white,
        alignment=1
    )

    header_tag_style = ParagraphStyle(
        'HeaderTag',
        parent=styles['Normal'],
        fontName=FONT_BOLD,
        fontSize=8.5,
        leading=11,
        textColor=GOLD,
        alignment=1
    )

    sec_title_style = ParagraphStyle(
        'SecTitle',
        parent=styles['Normal'],
        fontName=FONT_BOLD,
        fontSize=9.5,
        leading=13,
        textColor=PRIMARY
    )

    step_title_style = ParagraphStyle(
        'StepTitle',
        parent=styles['Normal'],
        fontName=FONT_BOLD,
        fontSize=10,
        leading=13,
        textColor=PRIMARY
    )

    step_body_style = ParagraphStyle(
        'StepBody',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=8.8,
        leading=12.2,
        textColor=DARK_TEXT
    )

    badge_style = ParagraphStyle(
        'BadgeText',
        parent=styles['Normal'],
        fontName=FONT_BOLD,
        fontSize=10,
        leading=12,
        textColor=colors.white,
        alignment=1
    )

    note_title_style = ParagraphStyle(
        'NoteTitle',
        parent=styles['Normal'],
        fontName=FONT_BOLD,
        fontSize=9.5,
        leading=12.5,
        textColor=colors.HexColor('#854D0E')
    )

    note_body_style = ParagraphStyle(
        'NoteBody',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=8.5,
        leading=11.8,
        textColor=colors.HexColor('#713F12')
    )

    story = []

    # 1. HEADER BANNER
    header_content = [
        [Paragraph("PONDOK PESANTREN WALI BAROKAH KEDIRI", header_tag_style)],
        [Spacer(1, 3)],
        [Paragraph("TEKNIS PENJEMPUTAN SANTRI YANG DIQODAR BELUM LULUS TES<br/><font size=10.5 color='#E2EFE9'>KEDIRI DAN KERTOSONO</font>", title_style)],
        [Spacer(1, 3)],
        [Paragraph("STANDAR OPERASIONAL PROSEDUR (SOP) RESMI PENJEMPUTAN", header_tag_style)]
    ]

    header_table = Table(header_content, colWidths=[content_width])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), PRIMARY),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 9),
        ('BOTTOMPADDING', (0,0), (-1,-1), 9),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
        ('LINEBELOW', (0,-1), (-1,-1), 2.5, GOLD),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 8))

    # Metadata Strip
    meta_data = [
        [
            Paragraph("<b>Target Utama:</b> Pengurus Pondok / Wali", ParagraphStyle('m1', parent=styles['Normal'], fontName=FONT_NAME, fontSize=8, textColor=MUTED_TEXT)),
            Paragraph("<b>Lokasi Utama:</b> Database Kediri", ParagraphStyle('m2', parent=styles['Normal'], fontName=FONT_NAME, fontSize=8, textColor=MUTED_TEXT, alignment=1)),
            Paragraph("<b>Unit Terkait:</b> Database, DMC, PASUS/Guru Putri, Pos Penjagaan", ParagraphStyle('m3', parent=styles['Normal'], fontName=FONT_NAME, fontSize=8, textColor=MUTED_TEXT, alignment=2))
        ]
    ]
    meta_table = Table(meta_data, colWidths=[content_width*0.3, content_width*0.3, content_width*0.4])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), PRIMARY_TINT),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#B8D8C9')),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # Section Title
    story.append(Paragraph("ALUR DAN PROSEDUR PENJEMPUTAN SANTRI:", sec_title_style))
    story.append(Spacer(1, 6))

    # 2. STEP CARDS (5 STEPS)
    steps = [
        (
            "1",
            "Kedatangan Pengurus & Konfirmasi Database",
            "Pengurus datang ke <b>Database Kediri</b> untuk mengambil surat keterangan tidak lulus tes, dan melakukan konfirmasi kepada petugas bahwa akan menjemput santri tes yang tidak lulus dari pondoknya."
        ),
        (
            "2",
            "Pemanggilan Santri oleh Petugas",
            "Petugas Database menghubungi <b>DMC</b> atau <b>PASUS / Guru Putri</b> yang bertugas untuk memanggilkan santri tersebut, agar santri segera melakukan persiapan kepulangan."
        ),
        (
            "3",
            "Prosedur Khusus (Pengurus Sudah Bertemu Santri)",
            "Apabila pengurus sebelum ke Database sudah bertemu terlebih dahulu dengan santrinya, maka membawa santrinya ke <b>Database Kediri</b> untuk konfirmasi penjemputan dan mengambil surat keterangan tidak lulus tes."
        ),
        (
            "4",
            "Pencatatan & Penandaan Data Santri",
            "Petugas Database memberi tanda / status verifikasi pada data santri yang telah resmi dijemput oleh pengurus."
        ),
        (
            "5",
            "Pemeriksaan Pos Penjagaan & Kepulangan",
            "Pengurus pulang dengan membawa santri tersebut. Di <b>Pos Penjagaan PPWB</b>, tunjukkan surat tanda tidak lulus tes sebagai <b>Surat Izin Resmi Keluar Komplek PPWB</b>."
        ),
    ]

    for num, stitle, sbody in steps:
        badge_p = Paragraph(num, badge_style)
        badge_table = Table([[badge_p]], colWidths=[24], rowHeights=[24])
        badge_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), PRIMARY),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 3),
        ]))

        step_content = [
            [Paragraph(f"LANGKAH {num} — {stitle.upper()}", step_title_style)],
            [Spacer(1, 2)],
            [Paragraph(sbody, step_body_style)]
        ]
        
        content_table = Table(step_content, colWidths=[content_width - 44])
        content_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ]))

        card_table = Table(
            [[badge_table, content_table]],
            colWidths=[34, content_width - 34]
        )
        card_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), CARD_BG),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 10),
            ('BOX', (0,0), (-1,-1), 0.5, BORDER_COLOR),
            ('LINELEFT', (0,0), (0,-1), 3, PRIMARY),
        ]))

        story.append(card_table)
        story.append(Spacer(1, 5.5))

    story.append(Spacer(1, 4))

    # 3. CATATAN PENTING
    note_content = [
        [Paragraph("<b>CATATAN PENTING & KETENTUAN KHUSUS POS PENJAGAAN:</b>", note_title_style)],
        [Spacer(1, 2)],
        [Paragraph("• <b>Surat Keterangan / Tanda Tidak Lulus Tes</b> wajib diambil di Database Kediri dan berfungsi resmi sebagai <b>Surat Izin Keluar Komplek PPWB</b> di Pos Penjagaan.<br/>"
                   "• Santri <b>wajib</b> dipanggil melalui jalur resmi (DMC / PASUS / Guru Putri) untuk menjaga ketertiban pondok.<br/>"
                   "• Pengurus dan wali santri dimohon mengikuti alur konfirmasi hingga selesai sebelum meninggalkan komplek PPWB.", note_body_style)]
    ]
    note_table = Table(note_content, colWidths=[content_width])
    note_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), GOLD_LIGHT),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ('BOX', (0,0), (-1,-1), 0.7, GOLD),
    ]))
    story.append(note_table)

    story.append(Spacer(1, 14))

    # 4. SIGNATURE SECTION
    sig_head_style = ParagraphStyle('sh', parent=styles['Normal'], fontName=FONT_BOLD, fontSize=8.5, leading=11, alignment=1, textColor=DARK_TEXT)
    sig_line_style = ParagraphStyle('sl', parent=styles['Normal'], fontName=FONT_NAME, fontSize=8.5, alignment=1, textColor=MUTED_TEXT)

    sig_data = [
        [
            Paragraph("Mengetahui,<br/><b>Petugas Database Kediri</b>", sig_head_style),
            Paragraph("Kediri, ....................................<br/><b>Petugas Lapangan / DMC</b>", sig_head_style),
            Paragraph("Konfirmasi Penjemputan,<br/><b>Pengurus / Penanggung Jawab</b>", sig_head_style)
        ],
        [
            Spacer(1, 28),
            Spacer(1, 28),
            Spacer(1, 28)
        ],
        [
            Paragraph("( ________________________ )", sig_line_style),
            Paragraph("( ________________________ )", sig_line_style),
            Paragraph("( ________________________ )", sig_line_style)
        ]
    ]

    sig_table = Table(sig_data, colWidths=[content_width/3.0]*3)
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    
    story.append(sig_table)

    # Build PDF with single page canvas
    doc.build(story, canvasmaker=SinglePageCanvas)
    print(f"PDF successfully generated: {pdf_path}")

if __name__ == "__main__":
    build_pdf()
