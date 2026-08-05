import subprocess
import os

typst_gold = """
#set page(
  paper: "a4",
  margin: 0pt,
  fill: rgb("#070b19")
)

#set text(
  font: ("Nimbus Sans", "DejaVu Sans", "sans-serif")
)

// Background Gradient Layer
#place(top + left, dx: 0pt, dy: 0pt)[
  #rect(
    width: 100%,
    height: 100%,
    fill: gradient.radial(rgb("#172554"), rgb("#0b1329"), rgb("#030712"), radius: 85%, center: (50%, 45%))
  )
]

// Outer Gold Frame
#place(center + horizon)[
  #rect(
    width: 194mm,
    height: 281mm,
    stroke: 1.5pt + rgb("#d97706")
  )
]

// Inner Fine Frame
#place(center + horizon)[
  #rect(
    width: 188mm,
    height: 275mm,
    stroke: 0.5pt + rgb("#fbbf24").lighten(40%)
  )
]

// Corner Accents
#place(top + left, dx: 12mm, dy: 14mm)[#line(length: 15mm, stroke: 2pt + rgb("#f59e0b"))]
#place(top + left, dx: 12mm, dy: 14mm)[#line(angle: 90deg, length: 15mm, stroke: 2pt + rgb("#f59e0b"))]

#place(top + right, dx: -12mm, dy: 14mm)[#line(length: 15mm, stroke: 2pt + rgb("#f59e0b"))]
#place(top + right, dx: -12mm, dy: 14mm)[#line(angle: 90deg, length: 15mm, stroke: 2pt + rgb("#f59e0b"))]

#place(bottom + left, dx: 12mm, dy: -14mm)[#line(length: 15mm, stroke: 2pt + rgb("#f59e0b"))]
#place(bottom + left, dx: 12mm, dy: -14mm)[#line(angle: -90deg, length: 15mm, stroke: 2pt + rgb("#f59e0b"))]

#place(bottom + right, dx: -12mm, dy: -14mm)[#line(length: 15mm, stroke: 2pt + rgb("#f59e0b"))]
#place(bottom + right, dx: -12mm, dy: -14mm)[#line(angle: -90deg, length: 15mm, stroke: 2pt + rgb("#f59e0b"))]


#align(center + horizon)[
  #v(-1.5cm)
  
  // Top Emblem / Crest Badge
  #rect(
    fill: rgb("#1e293b").transparentize(30%),
    stroke: 0.8pt + rgb("#f59e0b"),
    radius: 20pt,
    inset: (x: 18pt, y: 8pt)
  )[
    #text(size: 11pt, tracking: 0.35em, fill: rgb("#fbbf24"), weight: "bold")[INTEGRITAS  #sym.bullet  KARAKTER  #sym.bullet  KEPERCAYAAN]
  ]

  #v(2.5cm)

  // Main Typography
  #text(size: 46pt, weight: "bold", tracking: 0.18em, fill: gradient.linear(rgb("#ffffff"), rgb("#f1f5f9"), angle: 90deg))[KEJUJURAN]
  
  #v(0.6cm)

  #text(size: 26pt, style: "italic", tracking: 0.15em, fill: rgb("#fbbf24"))[—  di atas  —]
  
  #v(0.6cm)

  #text(size: 50pt, weight: "extrabold", tracking: 0.22em, fill: gradient.linear(rgb("#f59e0b"), rgb("#d97706"), rgb("#b45309"), angle: 45deg))[SEGALANYA]

  #v(2.2cm)

  // Decorative Diamond Line
  #grid(
    columns: (1fr, auto, 1fr),
    align: horizon,
    line(length: 80%, stroke: 0.7pt + gradient.linear(rgb("#070b19"), rgb("#f59e0b"))),
    polygon(
      fill: rgb("#fbbf24"),
      (0pt, -4pt), (4pt, 0pt), (0pt, 4pt), (-4pt, 0pt)
    ),
    line(length: 80%, stroke: 0.7pt + gradient.linear(rgb("#f59e0b"), rgb("#070b19")))
  )

  #v(1.8cm)

  // Quote Section
  #block(width: 80%)[
    #set par(leading: 0.8em)
    #text(size: 13pt, style: "italic", fill: rgb("#e2e8f0"))[
      "Kejujuran adalah bab pertama dalam buku kebijaksanaan."
    ]
    #v(0.4cm)
    #text(size: 10pt, tracking: 0.2em, fill: rgb("#94a3b8"), weight: "bold")[— THOMAS JEFFERSON]
  ]

  #v(2.5cm)
  
  // Footer
  #text(size: 8.5pt, tracking: 0.4em, fill: rgb("#64748b"))[POSTER MOTIVASI & EDUKASI KARAKTER]
]
"""

typst_light = """
#set page(
  paper: "a4",
  margin: 0pt,
  fill: rgb("#fafafa")
)

#set text(
  font: ("Nimbus Sans", "DejaVu Sans", "sans-serif")
)

// Background Clean Gradient
#place(top + left, dx: 0pt, dy: 0pt)[
  #rect(
    width: 100%,
    height: 100%,
    fill: gradient.linear(rgb("#ffffff"), rgb("#f1f5f9"), angle: 180deg)
  )
]

// Frame
#place(center + horizon)[
  #rect(
    width: 192mm,
    height: 279mm,
    stroke: 2pt + rgb("#0f172a")
  )
]

#place(center + horizon)[
  #rect(
    width: 186mm,
    height: 273mm,
    stroke: 0.5pt + rgb("#94a3b8")
  )
]

#align(center + horizon)[
  #v(-1cm)
  
  #text(size: 12pt, tracking: 0.4em, fill: rgb("#475569"), weight: "bold")[NILAI UTAMA INTEGRITAS]

  #v(1.8cm)

  // Minimal Shield Symbol in Typst Shapes
  #place(center)[
    #v(-1.2cm)
    #polygon(
      fill: rgb("#0f172a").transparentize(92%),
      stroke: 1.5pt + rgb("#0f172a"),
      (0pt, -20pt), (20pt, -10pt), (20pt, 10pt), (0pt, 25pt), (-20pt, 10pt), (-20pt, -10pt)
    )
  ]

  #v(1.5cm)

  #text(size: 44pt, weight: "bold", tracking: 0.15em, fill: rgb("#0f172a"))[KEJUJURAN]
  
  #v(0.6cm)

  #text(size: 24pt, style: "italic", tracking: 0.12em, fill: rgb("#2563eb"))[di atas]
  
  #v(0.6cm)

  #text(size: 48pt, weight: "extrabold", tracking: 0.18em, fill: rgb("#1e3a8a"))[SEGALANYA]

  #v(2.5cm)

  #line(length: 40mm, stroke: 1.5pt + rgb("#2563eb"))

  #v(1.8cm)

  #block(width: 78%)[
    #set par(leading: 0.8em)
    #text(size: 12.5pt, style: "italic", fill: rgb("#334155"))[
      "Tidak ada warisan yang lebih kaya dan berharga daripada kejujuran."
    ]
    #v(0.4cm)
    #text(size: 9.5pt, tracking: 0.25em, fill: rgb("#64748b"), weight: "bold")[— WILLIAM SHAKESPEARE]
  ]

  #v(3cm)
  
  #text(size: 8pt, tracking: 0.35em, fill: rgb("#94a3b8"))[BUILDING INTEGRITY • INSPIRING TRUST]
]
"""

typst_vibrant = """
#set page(
  paper: "a4",
  margin: 0pt,
  fill: rgb("#042f2e")
)

#set text(
  font: ("Nimbus Sans", "DejaVu Sans", "sans-serif")
)

// Background Gradient
#place(top + left, dx: 0pt, dy: 0pt)[
  #rect(
    width: 100%,
    height: 100%,
    fill: gradient.linear(rgb("#064e3b"), rgb("#0f172a"), rgb("#0284c7"), angle: 135deg)
  )
]

// Geometric Lines Accents
#place(top + left, dx: 20mm, dy: 30mm)[
  #circle(radius: 60mm, fill: rgb("#38bdf8").transparentize(90%))
]

#place(bottom + right, dx: -10mm, dy: -10mm)[
  #circle(radius: 80mm, fill: rgb("#34d399").transparentize(92%))
]

#place(center + horizon)[
  #rect(
    width: 190mm,
    height: 277mm,
    stroke: 1pt + rgb("#38bdf8").transparentize(50%),
    radius: 8pt
  )
]

#align(center + horizon)[
  #v(-1cm)
  
  #rect(
    fill: rgb("#0f172a").transparentize(40%),
    stroke: 1pt + rgb("#34d399"),
    radius: 4pt,
    inset: (x: 16pt, y: 7pt)
  )[
    #text(size: 11pt, tracking: 0.3em, fill: rgb("#34d399"), weight: "bold")[PRINSIP KEPEMIMPINAN & KARAKTER]
  ]

  #v(2.5cm)

  #text(size: 48pt, weight: "extrabold", tracking: 0.16em, fill: rgb("#ffffff"))[KEJUJURAN]
  
  #v(0.6cm)

  #text(size: 26pt, style: "italic", tracking: 0.2em, fill: rgb("#38bdf8"))[—  DI ATAS  —]
  
  #v(0.6cm)

  #text(size: 52pt, weight: "black", tracking: 0.2em, fill: gradient.linear(rgb("#34d399"), rgb("#a7f3d0"), angle: 45deg))[SEGALANYA]

  #v(2.5cm)

  #rect(
    width: 75%,
    fill: rgb("#0f172a").transparentize(50%),
    stroke: 0.5pt + rgb("#94a3b8").transparentize(50%),
    inset: 14pt,
    radius: 6pt
  )[
    #set par(leading: 0.8em)
    #text(size: 12pt, fill: rgb("#f1f5f9"))[
      Kejujuran adalah pondasi utama dalam membangun kepercayaan, integritas, dan martabat diri.
    ]
  ]

  #v(3cm)
  
  #text(size: 8.5pt, tracking: 0.4em, fill: rgb("#94a3b8"))[EDUKASI INTEGRITAS & MORAL]
]
"""

os.makedirs('/root/MyProject/OfficeCLI', exist_ok=True)
files = {
    'Poster_Kejujuran_Dark_Gold.typ': typst_gold,
    'Poster_Kejujuran_Minimalist_Light.typ': typst_light,
    'Poster_Kejujuran_Vibrant_Modern.typ': typst_vibrant
}

for filename, content in files.items():
    typ_path = os.path.join('/root/MyProject/OfficeCLI', filename)
    pdf_path = typ_path.replace('.typ', '.pdf')
    png_prefix = typ_path.replace('.typ', '_preview')
    
    with open(typ_path, 'w') as f:
        f.write(content)
        
    subprocess.run(['typst', 'compile', typ_path, pdf_path], check=True)
    subprocess.run(['pdftoppm', '-png', '-r', '150', pdf_path, png_prefix], check=True)
    print(f"Generated {pdf_path} and preview {png_prefix}-1.png")

# Also create a copy of the primary poster as `Poster_Kejujuran_di_Atas_Segalanya.pdf`
primary_pdf = '/root/MyProject/OfficeCLI/Poster_Kejujuran_di_Atas_Segalanya.pdf'
subprocess.run(['cp', '/root/MyProject/OfficeCLI/Poster_Kejujuran_Dark_Gold.pdf', primary_pdf])
subprocess.run(['pdftoppm', '-png', '-r', '150', primary_pdf, '/root/MyProject/OfficeCLI/Poster_Kejujuran_di_Atas_Segalanya_preview'])

print("All poster PDFs generated successfully!")
