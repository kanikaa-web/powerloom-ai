"""
Module 2 — Inventory Management.
Stock entry, stock history, low-stock alerts, inventory analytics.
"""

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

from utils.ui import setup_page, kpi_card, kpi_row, section, chart, alert_card, footer
from database.db import fetch_all, execute

setup_page("Inventory Management", "📦", "Stock levels, stock entry, movement history and reorder alerts", "Module 2")

stock_df = pd.DataFrame(fetch_all("SELECT * FROM stock"))

tab1, tab2, tab3 = st.tabs(["📋 Current Stock", "➕ Stock Entry / Update", "📜 Stock History"])

with tab1:
    low_n = int((stock_df["current_stock"] < stock_df["reorder_level"]).sum())
    kpi_row([
        dict(label="Materials tracked", value=len(stock_df), icon="📦", color="indigo"),
        dict(label="Below reorder", value=low_n, icon="⚠️", color="rose" if low_n else "emerald"),
        dict(label="Total stock (kg)", value=f"{stock_df.loc[stock_df['unit']=='kg','current_stock'].sum():,.0f}",
             icon="⚖️", color="teal"),
        dict(label="Movements logged", value=len(fetch_all("SELECT id FROM stock_history")), icon="📜", color="amber"),
    ])
    section("Current Stock Levels")
    st.dataframe(stock_df, use_container_width=True, hide_index=True)

    low_stock = stock_df[stock_df["current_stock"] < stock_df["reorder_level"]]
    if not low_stock.empty:
        st.error(f"⚠️ Low Stock Alert: {', '.join(low_stock['material_name'])}")
    else:
        st.success("✅ All materials are above reorder level.")

    fig = px.bar(stock_df, x="material_name", y=["current_stock", "safety_stock", "reorder_level"],
                 barmode="group", title="Inventory Levels by Material",
                 color_discrete_sequence=["#6366F1", "#F59E0B", "#F43F5E"])
    chart(fig)

with tab2:
    section("Material Entry / Stock Update")
    with st.form("stock_update_form"):
        material = st.selectbox("Material", stock_df["material_name"].tolist() if not stock_df.empty else [])
        change_type = st.radio("Type", ["IN (Purchase/Received)", "OUT (Consumption/Issue)"], horizontal=True)
        qty = st.number_input("Quantity", 0.0, 100000.0, 100.0)
        note = st.text_input("Note (optional)")
        submitted = st.form_submit_button("Update Stock", use_container_width=True)

        if submitted and material:
            delta = qty if change_type.startswith("IN") else -qty
            execute("UPDATE stock SET current_stock = current_stock + ?, last_updated = ? WHERE material_name = ?",
                    (delta, datetime.now().isoformat(), material))
            execute("""INSERT INTO stock_history (material_name, change_qty, change_type, note, performed_by)
                       VALUES (?,?,?,?,?)""",
                    (material, qty, "IN" if change_type.startswith("IN") else "OUT",
                     note, st.session_state.get("username", "system")))
            from utils.data import log_activity
            log_activity("Stock updated", f"{material} {'+' if delta >= 0 else ''}{delta}")
            st.success(f"Stock updated for {material}.")
            st.rerun()

with tab3:
    section("Stock Movement History")
    history_df = pd.DataFrame(fetch_all("SELECT * FROM stock_history ORDER BY timestamp DESC LIMIT 200"))
    if not history_df.empty:
        st.dataframe(history_df, use_container_width=True)
    else:
        st.info("No stock movements recorded yet.")

footer()
