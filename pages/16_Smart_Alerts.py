"""
Advanced — Smart Alerts Center.
One prioritised list of everything that needs action across inventory,
machines, quality, production, finance and orders — plus order status updates.
"""

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.ui import setup_page, kpi_row, section, chart, alert_card, footer
from utils.alerts import build_alerts
from utils.data import orders_table, log_activity
from database.db import execute

setup_page("Smart Alerts", "🔔", "Prioritised, actionable alerts from inventory, machines, quality, production and orders",
           "Advanced · Operations")

with st.expander("⚙️ Alert thresholds"):
    t1, t2 = st.columns(2)
    cover = t1.slider("Warn when stock covers fewer than (days)", 3, 30, 7)
    waste = t2.slider("Warn when average waste exceeds (%)", 3.0, 12.0, 7.0, 0.5)

alerts = build_alerts(cover, waste)
adf = pd.DataFrame(alerts)
count = adf["severity"].value_counts()

kpi_row([
    dict(label="Total alerts", value=len(adf), icon="🔔", color="indigo"),
    dict(label="Critical", value=int(count.get("Critical", 0)), icon="🔴", color="rose"),
    dict(label="High", value=int(count.get("High", 0)), icon="🟠", color="orange"),
    dict(label="Medium / Low", value=int(count.get("Medium", 0) + count.get("Low", 0)), icon="🟡", color="amber"),
])

c1, c2 = st.columns([2, 1])
with c1:
    section("Alert feed")
    cats = st.multiselect("Category", sorted(adf["category"].unique()), default=sorted(adf["category"].unique()))
    sevs = st.multiselect("Severity", ["Critical", "High", "Medium", "Low", "Info"],
                          default=["Critical", "High", "Medium", "Low", "Info"])
    shown = adf[adf["category"].isin(cats) & adf["severity"].isin(sevs)]
    for _, a in shown.iterrows():
        alert_card(a["title"], a["body"], a["severity"], f"{a['category']} · ➜ {a['action']}" if a["action"] else a["category"])
    if shown.empty:
        st.success("Nothing matches these filters.")
with c2:
    section("Breakdown")
    with st.container(border=True):
        g = adf.groupby(["category", "severity"]).size().reset_index(name="Alerts")
        fig = px.sunburst(g, path=["category", "severity"], values="Alerts", color="severity",
                          color_discrete_map={"Critical": "#E11D48", "High": "#F97316", "Medium": "#FBBF24",
                                              "Low": "#10B981", "Info": "#6366F1", "(?)": "#EDE9FE"})
        chart(fig, height=360)
    st.download_button("⬇️ Export alerts (CSV)", adf.to_csv(index=False).encode(), "barkavi_alerts.csv",
                       "text/csv", use_container_width=True)

# ---------------- Order status board ----------------
section("Order status board", "update orders to clear order alerts")
orders = orders_table()
if orders.empty:
    st.info("No orders yet — add orders on the Order Priority page.")
else:
    orders["status"] = orders["status"].fillna("Pending")
    edit = orders[["order_id", "customer", "fabric_type", "quantity", "delivery_date", "priority", "status"]]
    edited = st.data_editor(
        edit, hide_index=True, use_container_width=True, disabled=["order_id", "customer", "fabric_type",
                                                                   "quantity", "delivery_date", "priority"],
        column_config={"status": st.column_config.SelectboxColumn(
            "Status", options=["Pending", "In Production", "Dispatched", "Completed"], required=True)},
        key="order_board")
    if st.button("💾 Save status changes", use_container_width=True):
        changed = edited[edited["status"] != edit["status"]]
        for _, r in changed.iterrows():
            execute("UPDATE orders SET status = ? WHERE order_id = ?", (r["status"], r["order_id"]))
            log_activity("Order status changed", f"{r['order_id']} → {r['status']}")
        st.success(f"{len(changed)} order(s) updated.")
        st.rerun()
footer()
