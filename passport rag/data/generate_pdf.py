"""
Generate CitizenDoc Regulatory & Compliance PDF using ReportLab.
Produces a 7-page official Citizen Documents, Passport Seva & Parivahan RTO Rulebook.
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """Adds professional running header and footer with page number 'Page X of 7'."""
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
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, total_pages):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#1E3A8A"))

        # Header
        self.drawString(54, 750, "CITIZENDOC: PASSPORT SEVA & PARIVAHAN RTO REGULATORY COMPLIANCE MANUAL")
        self.setFont("Helvetica", 7)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawRightString(558, 750, "GOVERNMENT OF INDIA (MEA & MoRTH STANDARDS)")
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.75)
        self.line(54, 742, 558, 742)

        # Footer
        self.line(54, 45, 558, 45)
        self.drawString(54, 32, "OFFICIAL CITIZEN ASSISTANT REFERENCE — VERIFIED REGULATORY CIRCULARS & NOTIFICATIONS")
        self.drawRightString(558, 32, f"Page {self._pageNumber} of {total_pages}")
        self.restoreState()


def build_pdf(txt_path: str, pdf_path: str):
    with open(txt_path, "r", encoding="utf-8") as f:
        text = f.read()

    pages_raw = text.split("--- [PAGE ")
    pages_data = []

    for item in pages_raw:
        item = item.strip()
        if not item:
            continue
        try:
            p_num = int(item.split("]")[0])
            p_body = item.split("---", 1)[1].strip()
            pages_data.append((p_num, p_body))
        except Exception:
            pass

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=64,
        bottomMargin=60
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "SectionTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=6
    )

    h2_style = ParagraphStyle(
        "SubSectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#1E3A8A"),
        spaceBefore=7,
        spaceAfter=4
    )

    body_style = ParagraphStyle(
        "CleanBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#334155"),
        spaceAfter=3
    )

    meta_style = ParagraphStyle(
        "MetaBox",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor("#0284C7")
    )

    story = []

    for idx, (p_num, p_body) in enumerate(pages_data):
        lines = p_body.splitlines()
        meta_lines = []
        content_lines = []

        for line in lines:
            line_str = line.strip()
            if line_str.startswith("Authority:") or line_str.startswith("Service Category:") or line_str.startswith("Rejection Risk Tier:"):
                meta_lines.append(line_str)
            else:
                content_lines.append(line)

        # Meta Table
        if meta_lines:
            meta_text = "<br/>".join([f"<b>{ml.split(':', 1)[0]}:</b> {ml.split(':', 1)[1].strip()}" for ml in meta_lines if ":" in ml])
            meta_p = Paragraph(meta_text, meta_style)
            meta_table = Table([[meta_p]], colWidths=[504])
            meta_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F0F9FF")),
                ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#BAE6FD")),
                ("PADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))

        for line in content_lines:
            line_clean = line.strip()
            if not line_clean:
                continue

            if line_clean.startswith("# SECTION"):
                heading_clean = line_clean.replace("#", "").strip()
                story.append(Paragraph(heading_clean, title_style))
                if meta_lines:
                    story.append(meta_table)
                    story.append(Spacer(1, 6))
            elif line_clean.startswith("###"):
                sub_clean = line_clean.replace("###", "").strip()
                story.append(Paragraph(sub_clean, h2_style))
            elif line_clean.startswith("- ") or line_clean.startswith("* ") or (len(line_clean) > 2 and line_clean[0].isdigit() and line_clean[1] in [".", ")"]):
                bullet_text = f"&bull; {line_clean.lstrip('- *0123456789.) ')}"
                story.append(Paragraph(bullet_text, body_style))
            else:
                story.append(Paragraph(line_clean, body_style))

        if idx < len(pages_data) - 1:
            story.append(PageBreak())

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated 7-page CitizenDoc PDF at: {pdf_path}")


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    txt_file = os.path.join(base_dir, "citizendoc_rules.txt")
    pdf_file = os.path.join(base_dir, "citizendoc_rules.pdf")
    build_pdf(txt_file, pdf_file)
