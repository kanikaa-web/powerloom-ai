"""
pdf_report.py
--------------
Generates professional PDF reports (prediction, inventory, production,
analytics, dashboard summary) using ReportLab.
"""

import os
import logging
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                 Paragraph, Spacer, Image)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from utils.branding import BRAND_NAME, BRAND_TAGLINE, LOGO_BANNER

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

STYLES = getSampleStyleSheet()
TITLE_STYLE = ParagraphStyle("TitleStyle", parent=STYLES["Title"], textColor=colors.HexColor("#0B3D91"))
HEADER_STYLE = ParagraphStyle("HeaderStyle", parent=STYLES["Heading2"], textColor=colors.HexColor("#1B4F72"))


def generate_pdf_report(output_path: str, report_title: str, sections: list, generated_by: str = "System"):
    """
    sections: list of dicts, each either:
        {"type": "text", "content": "..."}
        {"type": "table", "headers": [...], "rows": [[...], ...]}
    """
    try:
        doc = SimpleDocTemplate(output_path, pagesize=A4,
                                 topMargin=1.5 * cm, bottomMargin=1.5 * cm,
                                 title=report_title, author=BRAND_NAME)
        story = []

        # ---- Barkavi Textiles letterhead ----
        if os.path.exists(LOGO_BANNER):
            banner_w = A4[0] - 4 * cm
            story.append(Image(LOGO_BANNER, width=banner_w, height=banner_w * 337 / 1024))
            story.append(Spacer(1, 0.3 * cm))
        else:
            story.append(Paragraph(BRAND_NAME, TITLE_STYLE))
        story.append(Paragraph(BRAND_TAGLINE, TITLE_STYLE))
        story.append(Paragraph(report_title, HEADER_STYLE))
        story.append(Paragraph(
            f"{BRAND_NAME} | Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')} | By: {generated_by}",
            STYLES["Normal"]))
        story.append(Spacer(1, 0.6 * cm))

        for section in sections:
            if section["type"] == "text":
                story.append(Paragraph(section.get("heading", ""), HEADER_STYLE))
                story.append(Paragraph(section["content"], STYLES["Normal"]))
                story.append(Spacer(1, 0.4 * cm))

            elif section["type"] == "table":
                story.append(Paragraph(section.get("heading", ""), HEADER_STYLE))
                data = [section["headers"]] + section["rows"]
                table = Table(data, hAlign="LEFT")
                table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0B3D91")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F4F7")]),
                    ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                ]))
                story.append(table)
                story.append(Spacer(1, 0.5 * cm))

        doc.build(story)
        logger.info(f"PDF report generated at {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Error generating PDF report: {e}")
        raise
