#!/usr/bin/env python3
"""Generate the non-image scRNA-seq marker cheat sheet lead magnet."""
from fpdf import FPDF
from pathlib import Path

OUT = Path(__file__).resolve().parent / "files" / "scRNA_seq_Marker_Cheat_Sheet.pdf"

class CheatSheetPDF(FPDF):
    def header(self):
        self.set_fill_color(15, 23, 42)
        self.rect(0, 0, 216, 23, "F")
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 13)
        self.set_xy(14, 6)
        self.cell(0, 6, "THE OMICS HUB", ln=1)
        self.set_font("Helvetica", "", 8.5)
        self.set_xy(14, 13)
        self.cell(0, 4, "Practical bioinformatics education and reproducible analysis", ln=1)
        self.ln(11)

    def footer(self):
        self.set_y(-12)
        self.set_draw_color(226, 232, 240)
        self.line(14, self.get_y() - 2, 202, self.get_y() - 2)
        self.set_text_color(100, 116, 139)
        self.set_font("Helvetica", "", 7.5)
        self.cell(150, 5, "Educational reference only. Validate annotations with tissue, species, state, and study context.", align="L")
        self.cell(0, 5, f"Page {self.page_no()}/{{nb}}", align="R")


def title(pdf, text, subtitle):
    pdf.set_text_color(15, 23, 42)
    pdf.set_font("Helvetica", "B", 20)
    pdf.multi_cell(0, 9, text)
    pdf.set_text_color(71, 85, 105)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5, subtitle)
    pdf.ln(4)


def section(pdf, heading, body):
    pdf.set_fill_color(239, 246, 255)
    pdf.set_text_color(30, 64, 175)
    pdf.set_font("Helvetica", "B", 10.5)
    pdf.cell(0, 6.5, heading, fill=True, ln=1)
    pdf.set_text_color(51, 65, 85)
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(0, 4.6, body)
    pdf.ln(3)


def marker_table(pdf, rows):
    left = 63
    right = 125
    pdf.set_fill_color(30, 64, 175)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.cell(left, 6, "Cell population", border=0, fill=True)
    pdf.cell(right, 6, "Representative markers", border=0, fill=True, ln=1)
    fill = False
    for cell_type, markers in rows:
        pdf.set_fill_color(248, 250, 252) if fill else pdf.set_fill_color(255, 255, 255)
        pdf.set_text_color(15, 23, 42)
        pdf.set_font("Helvetica", "B", 8.3)
        pdf.cell(left, 5, cell_type, border=1, fill=True)
        pdf.set_font("Helvetica", "", 8.3)
        pdf.cell(right, 5, markers, border=1, fill=True, ln=1)
        fill = not fill
    pdf.ln(3)


def main():
    pdf = CheatSheetPDF("P", "mm", "Letter")
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.set_title("scRNA-seq Marker Genes Cheat Sheet | The Omics Hub")
    pdf.set_author("Nasir Mahmood Abbasi, PhD")
    pdf.set_subject("Educational quick reference for context-aware scRNA-seq cell-type annotation")
    pdf.set_keywords("single-cell RNA-seq, marker genes, cell annotation, bioinformatics")
    pdf.alias_nb_pages()
    pdf.add_page()

    title(pdf, "scRNA-seq Marker Genes Cheat Sheet", "A context-aware quick reference for initial cell-type annotation. Compiled by Nasir Mahmood Abbasi, PhD.")
    section(pdf, "Use this guide correctly", "Marker genes are supporting evidence, not labels by themselves. Confirm annotations using multiple positive and negative markers, cluster-level differential expression, tissue and species context, cell state, sample metadata, and-where available-reference mapping or orthogonal assays. Do not use this sheet for clinical diagnosis or clinical decision-making.")
    section(pdf, "Common immune populations", "These marker sets are representative examples for common human immune contexts. Expression can vary by tissue, activation, disease, dissociation protocol, and sequencing depth.")
    marker_table(pdf, [
        ("T cells (general)", "CD3D, CD3E, CD3G, TRBC1/TRBC2"),
        ("CD4+ T cells", "IL7R, LTB, CCR7, MALAT1; confirm with CD4 where detected"),
        ("CD8+ / cytotoxic T cells", "CD8A, CD8B, NKG7, CCL5, GZMK/GZMB depending on state"),
        ("NK cells", "NKG7, GNLY, KLRD1, PRF1, FCGR3A"),
        ("B cells", "MS4A1, CD79A, CD79B, CD74, HLA-DRA"),
        ("Plasma cells", "JCHAIN, MZB1, XBP1, SDC1, immunoglobulin genes"),
        ("CD14+ monocytes", "LYZ, S100A8, S100A9, CTSD, FCN1"),
        ("FCGR3A+ monocytes", "FCGR3A, LST1, MS4A7, IFITM3, LILRB1"),
        ("Macrophages", "C1QC, APOC1, LGMN, CD68, CD163; context dependent"),
        ("Conventional dendritic cells", "CLEC10A, FCER1A, CD1C; cDC1 may express CLEC9A"),
        ("Plasmacytoid dendritic cells", "GZMB, IRF7, IL3RA, TCF4, SERPINF1; use a panel and context"),
    ])

    pdf.add_page()
    title(pdf, "Stromal, vascular, and epithelial context", "Use broad lineage markers as a starting point, then examine tissue-specific programs and technical artifacts.")
    marker_table(pdf, [
        ("Endothelial cells", "PECAM1, VWF, KDR, EMCN; assess vessel subtype markers in context"),
        ("Fibroblasts", "COL1A1, COL1A2, DCN, LUM, COL3A1; state programs can vary strongly"),
        ("Epithelial cells", "EPCAM, KRT8, KRT18, KRT19; use tissue-specific epithelial markers"),
        ("Cycling cells", "MKI67, TOP2A, HMGB2; treat as a state overlay, not a lineage"),
        ("Stressed / dissociation response", "FOS, JUN, HSP genes, DDIT4; assess technical context before labeling"),
        ("Doublet warning", "Coexpression of incompatible lineage programs; inspect UMI counts, doublet scores, and cluster context"),
    ])
    section(pdf, "Annotation checklist", "1. Inspect cluster markers and the full expression pattern, not one gene.  2. Check tissue, species, condition, and expected lineage composition.  3. Compare multiple reference sources or classifiers.  4. Record a confidence level and competing hypotheses.  5. Validate important labels with additional markers, spatial context, protein data, or orthogonal experiments when possible.")
    section(pdf, "Further resources", "Single Cell Best Practices: sc-best-practices.org. CellMarker: bio-bigdata.hrbmu.edu.cn/CellMarker. PanglaoDB: panglaodb.se. Scanpy and Seurat documentation provide workflow-specific annotation examples. Always record the database/version and access date used for a research analysis.")
    pdf.set_text_color(37, 99, 235)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 5, "More tutorials and practical workflows: theomicshub.com", ln=1)
    pdf.output(str(OUT))
    print(f"Wrote {OUT}")

if __name__ == "__main__":
    main()
