import os
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing, Rect, String, Group, Path, Polygon, Circle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pdf2image import convert_from_path

# Register TTF fonts
pdfmetrics.registerFont(TTFont('LiberationSans-Bold', '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'))
pdfmetrics.registerFont(TTFont('LiberationSans-Regular', '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf'))
pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))

def draw_pdf(filename):
    # A4 Landscape: 841.89 x 595.27 pt
    w, h = landscape(A4)
    c = canvas.Canvas(filename, pagesize=(w, h))

    # Background color: Soft off-white / light cream for professional print
    c.setFillColor(colors.HexColor('#F8FAFC'))
    c.rect(0, 0, w, h, fill=1, stroke=0)

    # Outer border / Frame
    margin = 25
    c.setStrokeColor(colors.HexColor('#1E293B'))
    c.setLineWidth(4)
    c.roundRect(margin, margin, w - 2*margin, h - 2*margin, 16, fill=0, stroke=1)

    c.setStrokeColor(colors.HexColor('#DC2626'))
    c.setLineWidth(1.5)
    c.roundRect(margin + 5, margin + 5, w - 2*(margin + 5), h - 2*(margin + 5), 12, fill=0, stroke=1)

    # Top Header Banner
    header_h = 85
    header_y = h - margin - 15 - header_h
    header_w = w - 2*(margin + 15)
    header_x = margin + 15

    c.setFillColor(colors.HexColor('#DC2626')) # Red warning header
    c.roundRect(header_x, header_y, header_w, header_h, 10, fill=1, stroke=0)

    # Header text
    c.setFillColor(colors.white)
    c.setFont('DejaVuSans-Bold', 36)
    c.drawCentredString(w / 2.0, header_y + 26, "PEMBERITAHUAN KHUSUS")

    # Main Notice Box / Text
    # Line 1: Selain Guru Dilarang Masuk,
    # Line 2: dan Setelah Pintu Dibuka
    # Line 3: Amal Sholih Dikunci Kembali

    c.setFillColor(colors.HexColor('#0F172A'))
    c.setFont('DejaVuSans-Bold', 36)
    c.drawCentredString(w / 2.0, header_y - 65, "SELAIN GURU DILARANG MASUK")

    c.setFont('DejaVuSans-Bold', 30)
    c.setFillColor(colors.HexColor('#334155'))
    c.drawCentredString(w / 2.0, header_y - 120, "DAN SETELAH PINTU DIBUKA")

    c.setFont('DejaVuSans-Bold', 36)
    c.setFillColor(colors.HexColor('#B91C1C')) # High emphasis red text
    c.drawCentredString(w / 2.0, header_y - 175, "AMAL SHOLIH DIKUNCI KEMBALI !")

    # Decorative separator line
    c.setStrokeColor(colors.HexColor('#CBD5E1'))
    c.setLineWidth(2)
    c.line(w/2 - 250, header_y - 210, w/2 + 250, header_y - 210)

    # Footer Prayer Card (Alhamdulillah jaza kumullohu khoiro)
    footer_w = 640
    footer_h = 75
    footer_x = (w - footer_w) / 2.0
    footer_y = margin + 25

    c.setFillColor(colors.HexColor('#047857')) # Islamic Green
    c.roundRect(footer_x, footer_y, footer_w, footer_h, 12, fill=1, stroke=0)

    # Subtle inner gold border for footer card
    c.setStrokeColor(colors.HexColor('#F59E0B'))
    c.setLineWidth(2)
    c.roundRect(footer_x + 4, footer_y + 4, footer_w - 8, footer_h - 8, 8, fill=0, stroke=1)

    c.setFillColor(colors.white)
    c.setFont('DejaVuSans-Bold', 26)
    c.drawCentredString(w / 2.0, footer_y + 24, "Alhamdulillah jaza kumullohu khoiro")

    c.showPage()
    c.save()

if __name__ == '__main__':
    pdf_path = "/root/MyProject/OfficeCLI/Pemberitahuan_A4_Landscape.pdf"
    draw_pdf(pdf_path)
    images = convert_from_path(pdf_path)
    images[0].save("/root/MyProject/OfficeCLI/preview_v1.png", "PNG")
    print("PDF generated successfully.")
