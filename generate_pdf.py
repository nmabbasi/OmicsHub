import os
import subprocess
import sys

def install_and_import(package):
    try:
        import reportlab
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

install_and_import('reportlab')

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors

os.makedirs('files', exist_ok=True)
pdf_path = 'files/scRNA_seq_Marker_Cheat_Sheet.pdf'

c = canvas.Canvas(pdf_path, pagesize=letter)
width, height = letter

# Title
c.setFont("Helvetica-Bold", 24)
c.setFillColor(colors.HexColor("#1E3A8A"))
c.drawString(50, height - 80, "scRNA-seq Marker Genes Cheat Sheet")

# Subtitle
c.setFont("Helvetica", 14)
c.setFillColor(colors.HexColor("#4B5563"))
c.drawString(50, height - 110, "A quick-reference guide for identifying major cell types")

# Author
c.setFont("Helvetica-Oblique", 12)
c.drawString(50, height - 130, "Compiled by Nasir Mahmood Abbasi, PhD | The Omics Hub")

# Table Headers
c.setFont("Helvetica-Bold", 12)
c.setFillColor(colors.black)
c.drawString(50, height - 170, "Cell Type")
c.drawString(250, height - 170, "Canonical Markers")

c.line(50, height - 180, width - 50, height - 180)

# Data
data = [
    ("T Cells (General)", "CD3D, CD3E, CD3G"),
    ("CD4+ T Cells", "CD4, IL7R"),
    ("CD8+ T Cells", "CD8A, CD8B"),
    ("B Cells", "CD79A, CD79B, MS4A1 (CD20)"),
    ("Plasma Cells", "IGJ, MZB1, SDC1 (CD138)"),
    ("NK Cells", "GNLY, NKG7, NCAM1 (CD56)"),
    ("Monocytes (CD14+)", "CD14, LYZ, S100A9"),
    ("Monocytes (FCGR3A+)", "FCGR3A (CD16), MS4A7"),
    ("Macrophages", "CD68, MACRO, CD163"),
    ("Dendritic Cells (pDC)", "LILRA4, IL3RA, CLEC4C"),
    ("Dendritic Cells (cDC)", "CLEC9A, CLEC10A, HLA-DPA1"),
    ("Endothelial Cells", "PECAM1 (CD31), VWF"),
    ("Fibroblasts", "COL1A1, DCN, PDGFRA"),
    ("Epithelial Cells", "EPCAM, KRT8, KRT18"),
]

c.setFont("Helvetica", 11)
y_pos = height - 210
for cell, markers in data:
    c.drawString(50, y_pos, cell)
    c.drawString(250, y_pos, markers)
    y_pos -= 25

c.line(50, y_pos, width - 50, y_pos)

# Footer
c.setFont("Helvetica", 10)
c.setFillColor(colors.gray)
c.drawString(50, 50, "Visit https://theomicshub.com for more tutorials and consulting services.")

c.save()
print(f"Generated {pdf_path} successfully!")
