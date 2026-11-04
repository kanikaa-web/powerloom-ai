"""
Module 9 — Reports.
Generates PDF/Excel reports for prediction, inventory, production, and analytics.
"""

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd

from utils.ui import setup_page, kpi_card, kpi_row, section, chart, alert_card, footer
from database.db import fetch_all
from reports.pdf_report import generate_pdf_report
from reports.excel_report import generate_excel_report

setup_page("Reports", "📄", "Branded PDF and Excel reports", "Module 9")

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

report_type = st.selectbox("Select Report Type", [
    "Inventory Report", "Production Report", "Analytics Report", "Dashboard Summary Report"
])
report_format = st.radio("Format", ["PDF", "Excel"], horizontal=True)

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "dataset", "powerloom_production_data.csv")
df = pd.read_csv(DATA_PATH, parse_dates=["Date"])

if st.button("📥 Generate Report", use_container_width=True):
    stock_df = pd.DataFrame(fetch_all("SELECT * FROM stock"))
    orders_df = pd.DataFrame(fetch_all("SELECT * FROM orders"))

    if report_type == "Inventory Report":
        data_df = stock_df
    elif report_type == "Production Report":
        data_df = df[["Date", "Fabric_Type", "Machine_Type", "Production_Target",
                       "Actual_Production", "Machine_Efficiency"]].tail(200)
    elif report_type == "Analytics Report":
        data_df = df.groupby(df["Date"].dt.to_period("M")).agg(
            Production=("Actual_Production", "sum"), Profit=("Profit", "sum"),
            Avg_Waste=("Waste_Percentage", "mean")).reset_index()
        data_df["Date"] = data_df["Date"].astype(str)
    else:
        data_df = df.tail(50)[["Date", "Order_ID", "Customer", "Actual_Production", "Profit"]]

    if report_format == "PDF":
        out_path = os.path.join(OUTPUT_DIR, f"{report_type.replace(' ', '_')}.pdf")
        sections = [{
            "type": "table", "heading": report_type,
            "headers": list(data_df.columns), "rows": data_df.astype(str).values.tolist()[:40]
        }]
        generate_pdf_report(out_path, report_type, sections, st.session_state.get("username", "system"))
    else:
        out_path = os.path.join(OUTPUT_DIR, f"{report_type.replace(' ', '_')}.xlsx")
        generate_excel_report(out_path, {report_type[:28]: data_df})

    with open(out_path, "rb") as f:
        st.download_button(f"⬇️ Download {report_type} ({report_format})", f,
                            file_name=os.path.basename(out_path), use_container_width=True)
    st.success("Report generated successfully!")

footer()
