import os
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pdf2image import convert_from_path

# Register TTF fonts
pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
pdfmetrics.registerFont(TTFont('DejaVuSans', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('LiberationSans-Bold', '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'))

def draw_lock_icon(c, x, y, scale=1.0, body_color='#DC2626', shackle_color='#FFFFFF'):
    c.saveState()
    c.translate(x, y)
    c.scale(scale, scale)

    # Lock Shackle (top arc)
    c.setStrokeColor(colors.HexColor(shackle_color))
    c.setLineWidth(4)
    c.setFillColor(colors.transparent)
    c.arc(-10, 0, 10, 24, 0, 180)

    # Lock Body
    c.setFillColor(colors.HexColor(body_color))
    c.setStrokeColor(colors.HexColor(shackle_color))
    c.setLineWidth(2)
    c.roundRect(-16, -24, 32, 25, 4, fill=1, stroke=1)

    # Keyhole
    c.setFillColor(colors.HexColor(shackle_color))
    c.circle(0, -9, 3, fill=1, stroke=0)
    
    path = c.beginPath()
    path.moveTo(-2, -10)
    path.lineTo(2, -10)
    path.lineTo(3, -18)
    path.lineTo(-3, -18)
    path.close()
    c.drawPath(path, fill=1, stroke=0)

    c.restoreState()

def draw_warning_icon(c, x, y, scale=1.0):
    c.saveState()
    c.translate(x, y)
    c.scale(scale, scale)

    # Yellow/Gold Warning Triangle
    c.setFillColor(colors.HexColor('#F59E0B'))
    c.setStrokeColor(colors.HexColor('#FFFFFF'))
    c.setLineWidth(2)

    path = c.beginPath()
    path.moveTo(0, 20)
    path.lineTo(22, -16)
    path.lineTo(-22, -16)
    path.close()
    c.drawPath(path, fill=1, stroke=1)

    # Exclamation point
    c.setFillColor(colors.HexColor('#78350F'))
    c.roundRect(-2, -3, 4, 14, 1.5, fill=1, stroke=0)
    c.circle(0, -10, 2, fill=1, stroke=0)

    c.restoreState()


# DESIGN 1: Bold High-Visibility Red & Navy (Modern Door Notice)
def draw_design_1(c, w, h):
    # Background
    c.setFillColor(colors.HexColor('#FFFFFF'))
    c.rect(0, 0, w, h, fill=1, stroke=0)

    # Outer border
    margin = 22
    c.setStrokeColor(colors.HexColor('#DC2626'))
    c.setLineWidth(6)
    c.roundRect(margin, margin, w - 2*margin, h - 2*margin, 14, fill=0, stroke=1)

    c.setStrokeColor(colors.HexColor('#0F172A'))
    c.setLineWidth(2)
    c.roundRect(margin + 6, margin + 6, w - 2*(margin + 6), h - 2*(margin + 6), 10, fill=0, stroke=1)

    # Top Red Header Banner
    banner_h = 95
    banner_y = h - margin - 20 - banner_h
    banner_w = w - 2*(margin + 20)
    banner_x = margin + 20

    c.setFillColor(colors.HexColor('#DC2626'))
    c.roundRect(banner_x, banner_y, banner_w, banner_h, 8, fill=1, stroke=0)

    # Icons on Header
    draw_lock_icon(c, banner_x + 60, banner_y + 48, scale=1.2, body_color='#0F172A', shackle_color='#FFFFFF')
    draw_lock_icon(c, banner_x + banner_w - 60, banner_y + 48, scale=1.2, body_color='#0F172A', shackle_color='#FFFFFF')

    # Header Text
    c.setFillColor(colors.white)
    c.setFont('DejaVuSans-Bold', 36)
    c.drawCentredString(w / 2.0, banner_y + 32, "PEMBERITAHUAN KHUSUS")

    # Main Body Text - Well spaced vertically
    y_curr = banner_y - 75
    
    # Line 1
    c.setFillColor(colors.HexColor('#0F172A'))
    c.setFont('DejaVuSans-Bold', 36)
    c.drawCentredString(w / 2.0, y_curr, "SELAIN GURU DILARANG MASUK,")

    # Line 2
    y_curr -= 65
    c.setFont('DejaVuSans-Bold', 32)
    c.setFillColor(colors.HexColor('#334155'))
    c.drawCentredString(w / 2.0, y_curr, "DAN SETELAH PINTU DIBUKA")

    # Line 3
    y_curr -= 70
    c.setFont('DejaVuSans-Bold', 36)
    c.setFillColor(colors.HexColor('#DC2626'))
    c.drawCentredString(w / 2.0, y_curr, "AMAL SHOLIH DIKUNCI KEMBALI !")

    # Divider line
    y_curr -= 45
    c.setStrokeColor(colors.HexColor('#CBD5E1'))
    c.setLineWidth(2.5)
    c.line(w/2 - 280, y_curr, w/2 + 280, y_curr)

    # Footer Card
    footer_w = 680
    footer_h = 80
    footer_x = (w - footer_w) / 2.0
    footer_y = margin + 30

    c.setFillColor(colors.HexColor('#047857')) # Emerald Green
    c.roundRect(footer_x, footer_y, footer_w, footer_h, 10, fill=1, stroke=0)

    # Inner Gold Border
    c.setStrokeColor(colors.HexColor('#F59E0B'))
    c.setLineWidth(2)
    c.roundRect(footer_x + 4, footer_y + 4, footer_w - 8, footer_h - 8, 7, fill=0, stroke=1)

    c.setFillColor(colors.white)
    c.setFont('DejaVuSans-Bold', 28)
    c.drawCentredString(w / 2.0, footer_y + 26, "Alhamdulillah jaza kumullohu khoiro")


# DESIGN 2: Islamic Green & Gold (Classic Pesantren / TPQ Style)
def draw_design_2(c, w, h):
    # Background: Soft Warm Off-White
    c.setFillColor(colors.HexColor('#FFFBEB'))
    c.rect(0, 0, w, h, fill=1, stroke=0)

    margin = 22
    # Outer double border (Green & Gold)
    c.setStrokeColor(colors.HexColor('#065F46'))
    c.setLineWidth(6)
    c.roundRect(margin, margin, w - 2*margin, h - 2*margin, 14, fill=0, stroke=1)

    c.setStrokeColor(colors.HexColor('#D97706'))
    c.setLineWidth(2)
    c.roundRect(margin + 6, margin + 6, w - 2*(margin + 6), h - 2*(margin + 6), 10, fill=0, stroke=1)

    # Top Green Header Banner
    banner_h = 95
    banner_y = h - margin - 20 - banner_h
    banner_w = w - 2*(margin + 20)
    banner_x = margin + 20

    c.setFillColor(colors.HexColor('#065F46'))
    c.roundRect(banner_x, banner_y, banner_w, banner_h, 10, fill=1, stroke=0)

    # Gold accent line on header
    c.setStrokeColor(colors.HexColor('#F59E0B'))
    c.setLineWidth(2)
    c.roundRect(banner_x + 5, banner_y + 5, banner_w - 10, banner_h - 10, 7, fill=0, stroke=1)

    # Warning Icons on sides
    draw_warning_icon(c, banner_x + 55, banner_y + 48, scale=1.2)
    draw_warning_icon(c, banner_x + banner_w - 55, banner_y + 48, scale=1.2)

    # Header Text
    c.setFillColor(colors.HexColor('#FEF3C7'))
    c.setFont('DejaVuSans-Bold', 36)
    c.drawCentredString(w / 2.0, banner_y + 32, "PERHATIAN BERSAMA")

    # Content
    y_curr = banner_y - 75

    c.setFillColor(colors.HexColor('#064E3B'))
    c.setFont('DejaVuSans-Bold', 36)
    c.drawCentredString(w / 2.0, y_curr, "Selain Guru Dilarang Masuk,")

    y_curr -= 65
    c.setFont('DejaVuSans-Bold', 32)
    c.setFillColor(colors.HexColor('#1E293B'))
    c.drawCentredString(w / 2.0, y_curr, "dan Setelah Pintu Dibuka")

    y_curr -= 70
    c.setFont('DejaVuSans-Bold', 38)
    c.setFillColor(colors.HexColor('#B91C1C'))
    c.drawCentredString(w / 2.0, y_curr, "Amal Sholih Dikunci Kembali")

    # Divider
    y_curr -= 45
    c.setStrokeColor(colors.HexColor('#D97706'))
    c.setLineWidth(2.5)
    c.line(w/2 - 260, y_curr, w/2 + 260, y_curr)

    # Footer Card
    footer_w = 680
    footer_h = 80
    footer_x = (w - footer_w) / 2.0
    footer_y = margin + 30

    c.setFillColor(colors.HexColor('#047857'))
    c.roundRect(footer_x, footer_y, footer_w, footer_h, 10, fill=1, stroke=0)

    c.setStrokeColor(colors.HexColor('#F59E0B'))
    c.setLineWidth(2)
    c.roundRect(footer_x + 4, footer_y + 4, footer_w - 8, footer_h - 8, 7, fill=0, stroke=1)

    c.setFillColor(colors.white)
    c.setFont('DejaVuSans-Bold', 28)
    c.drawCentredString(w / 2.0, footer_y + 26, "Alhamdulillah jaza kumullohu khoiro")


# DESIGN 3: User Exact Text Formatting (Pintu & Amal Solih Notice)
def draw_design_3(c, w, h):
    # Pure Clean White
    c.setFillColor(colors.HexColor('#FFFFFF'))
    c.rect(0, 0, w, h, fill=1, stroke=0)

    margin = 22
    # Frame
    c.setStrokeColor(colors.HexColor('#1E293B'))
    c.setLineWidth(5)
    c.roundRect(margin, margin, w - 2*margin, h - 2*margin, 12, fill=0, stroke=1)

    c.setStrokeColor(colors.HexColor('#DC2626'))
    c.setLineWidth(2)
    c.roundRect(margin + 5, margin + 5, w - 2*(margin + 5), h - 2*(margin + 5), 9, fill=0, stroke=1)

    # Top Header Box
    banner_h = 95
    banner_y = h - margin - 20 - banner_h
    banner_w = w - 2*(margin + 20)
    banner_x = margin + 20

    c.setFillColor(colors.HexColor('#1E293B'))
    c.roundRect(banner_x, banner_y, banner_w, banner_h, 8, fill=1, stroke=0)

    draw_lock_icon(c, banner_x + 60, banner_y + 48, scale=1.2, body_color='#DC2626', shackle_color='#FFFFFF')
    draw_lock_icon(c, banner_x + banner_w - 60, banner_y + 48, scale=1.2, body_color='#DC2626', shackle_color='#FFFFFF')

    c.setFillColor(colors.white)
    c.setFont('DejaVuSans-Bold', 36)
    c.drawCentredString(w / 2.0, banner_y + 32, "PERHATIAN !")

    # Body with Exact Input Text
    y_curr = banner_y - 75

    c.setFillColor(colors.HexColor('#DC2626'))
    c.setFont('DejaVuSans-Bold', 36)
    c.drawCentredString(w / 2.0, y_curr, "Selain Guru Dilarang Masuk,")

    y_curr -= 65
    c.setFillColor(colors.HexColor('#0F172A'))
    c.setFont('DejaVuSans-Bold', 32)
    c.drawCentredString(w / 2.0, y_curr, "dan Setelah Pintu Dibuka")

    y_curr -= 70
    c.setFillColor(colors.HexColor('#047857'))
    c.setFont('DejaVuSans-Bold', 38)
    c.drawCentredString(w / 2.0, y_curr, "Amal Sholih Dikunci Kembali")

    # Divider line
    y_curr -= 45
    c.setStrokeColor(colors.HexColor('#94A3B8'))
    c.setLineWidth(2)
    c.line(w/2 - 260, y_curr, w/2 + 260, y_curr)

    # Bottom Prayer Banner
    footer_w = 680
    footer_h = 80
    footer_x = (w - footer_w) / 2.0
    footer_y = margin + 30

    c.setFillColor(colors.HexColor('#DC2626'))
    c.roundRect(footer_x, footer_y, footer_w, footer_h, 8, fill=1, stroke=0)

    c.setFillColor(colors.white)
    c.setFont('DejaVuSans-Bold', 28)
    c.drawCentredString(w / 2.0, footer_y + 26, "Alhamdulillah jaza kumullohu khoiro")


def generate_all():
    w, h = landscape(A4)

    # 1. Individual files
    d1_path = "/root/MyProject/OfficeCLI/Pemberitahuan_Desain1_Merah.pdf"
    c1 = canvas.Canvas(d1_path, pagesize=(w, h))
    draw_design_1(c1, w, h)
    c1.showPage()
    c1.save()

    d2_path = "/root/MyProject/OfficeCLI/Pemberitahuan_Desain2_Hijau.pdf"
    c2 = canvas.Canvas(d2_path, pagesize=(w, h))
    draw_design_2(c2, w, h)
    c2.showPage()
    c2.save()

    d3_path = "/root/MyProject/OfficeCLI/Pemberitahuan_Desain3_InputUser.pdf"
    c3 = canvas.Canvas(d3_path, pagesize=(w, h))
    draw_design_3(c3, w, h)
    c3.showPage()
    c3.save()

    # 2. Combined PDF with all 3 pages
    combined_path = "/root/MyProject/OfficeCLI/Pemberitahuan_Pintu_A4_Landscape.pdf"
    cc = canvas.Canvas(combined_path, pagesize=(w, h))
    draw_design_1(cc, w, h)
    cc.showPage()
    draw_design_2(cc, w, h)
    cc.showPage()
    draw_design_3(cc, w, h)
    cc.showPage()
    cc.save()

    # Convert to PNG for visual inspection
    imgs = convert_from_path(combined_path)
    for idx, img in enumerate(imgs):
        img.save(f"/root/MyProject/OfficeCLI/preview_desain_{idx+1}.png", "PNG")
    print("All designs created successfully.")

if __name__ == '__main__':
    generate_all()
