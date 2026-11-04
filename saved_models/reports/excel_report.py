"""
excel_report.py
-----------------
Generates formatted Excel reports (inventory, production, prediction,
analytics) using OpenPyXL, with styled headers and auto-sized columns.
"""

import logging
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

from utils.branding import BRAND_NAME, BRAND_TAGLINE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_excel_report(output_path: str, sheets: dict):
    """
    sheets: dict of {sheet_name: pandas.DataFrame}
    """
    try:
        wb = Workbook()
        wb.remove(wb.active)  # remove default sheet

        header_fill = PatternFill(start_color="0B3D91", end_color="0B3D91", fill_type="solid")
        header_font = Font(color="FFFFFF", bold=True)

        for sheet_name, df in sheets.items():
            ws = wb.create_sheet(title=sheet_name[:31])
            ws.append(list(df.columns))

            for cell in ws[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center")

            for row in df.itertuples(index=False):
                ws.append(list(row))

            for i, col in enumerate(df.columns, 1):
                max_len = max(df[col].astype(str).map(len).max() if len(df) else 0, len(str(col)))
                ws.column_dimensions[get_column_letter(i)].width = min(max_len + 4, 40)

        wb.properties.creator = BRAND_NAME
        wb.properties.company = BRAND_NAME
        wb.properties.title = f"{BRAND_NAME} - {BRAND_TAGLINE}"
        wb.save(output_path)
        logger.info(f"Excel report generated at {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Error generating Excel report: {e}")
        raise
