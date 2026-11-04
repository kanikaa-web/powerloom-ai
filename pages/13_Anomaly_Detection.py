"""
Advanced — Production Anomaly Detection (Isolation Forest).
Flags unusual orders (efficiency, waste, shortfall, cost/unit, delivery) and
explains why each one is unusual.
"""

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.ui import setup_page, kpi_row, section, chart, alert_card, footer
from utils.data import load_dataset, log_activity
from utils.anomaly import detect_anomalies, FEATURES

setup_page("Anomaly Detection", "🚨", "Isolation-Forest scan that flags unusual production records and explains why",
           "Advanced · AI")

df = load_dataset()
c1, c2, c3 = st.columns([1, 1, 1.4])
sensitivity = c1.select_slider("Sensitivity", ["Low", "Medium", "High"], value="Medium")
contamination = {"Low": 0.015, "Medium": 0.03, "High": 0.06}[sensitivity]
window = c2.selectbox("Period", ["Last 90 days", "Last 180 days", "Last 365 days", "All data"], index=1)
machines = c3.multiselect("Machine type", sorted(df["Machine_Type"].unique()))

with st.spinner("Scanning records..."):
    res = detect_anomalies(df, contamination)

days = {"Last 90 days": 90, "Last 180 days": 180, "Last 365 days": 365}.get(window)
view = res if days is None else res[res["Date"] > res["Date"].max() - pd.Timedelta(days=days)]
if machines:
    view = view[view["Machine_Type"].isin(machines)]
anom = view[view["Is_Anomaly"]].sort_values("Anomaly_Score", ascending=False)

loss = (anom["Shortfall_Pct"].clip(lower=0) / 100 * anom["Production_Target"]).sum()
kpi_row([
    dict(label="Records scanned", value=f"{len(view):,}", icon="🔎", color="indigo"),
    dict(label="Anomalies found", value=f"{len(anom):,}", icon="🚨", color="rose",
         sub=f"{len(anom) / max(len(view), 1) * 100:.1f}% of records"),
    dict(label="Critical / High", value=int(anom["Severity"].isin(["Critical", "High"]).sum()), icon="🔥",
         color="orange"),
    dict(label="Units lost in anomalies", value=f"{loss:,.0f}", icon="📉", color="amber",
         sub="shortfall vs target on flagged orders"),
])

section("Where the anomalies are")
with st.container(border=True):
    plot = view.assign(Status=view["Severity"].where(view["Is_Anomaly"], "Normal"))
    fig = px.scatter(plot, x="Date", y="Machine_Efficiency", color="Status", size="Anomaly_Score",
                     size_max=16, hover_data=["Order_ID", "Machine_Type", "Fabric_Type", "Waste_Percentage", "Reason"],
                     color_discrete_map={"Normal": "rgba(148,163,184,0.35)", "Low": "#FBBF24", "Medium": "#F97316",
                                         "High": "#E11D48", "Critical": "#7C3AED"},
                     category_orders={"Status": ["Normal", "Low", "Medium", "High", "Critical"]},
                     title="Efficiency timeline — coloured points are anomalies")
    chart(fig, height=420)

c4, c5 = st.columns(2)
with c4, st.container(border=True):
    fig = px.scatter(plot, x="Machine_Efficiency", y="Waste_Percentage", color="Status",
                     color_discrete_map={"Normal": "rgba(148,163,184,0.35)", "Low": "#FBBF24", "Medium": "#F97316",
                                         "High": "#E11D48", "Critical": "#7C3AED"},
                     title="Efficiency vs waste")
    chart(fig, height=360)
with c5, st.container(border=True):
    if len(anom):
        by = anom.groupby(["Machine_Type", "Severity"]).size().reset_index(name="Count")
        fig = px.bar(by, x="Machine_Type", y="Count", color="Severity", title="Anomalies by machine type",
                     color_discrete_map={"Low": "#FBBF24", "Medium": "#F97316", "High": "#E11D48", "Critical": "#7C3AED"})
        chart(fig, height=360)
    else:
        st.success("No anomalies in this selection 🎉")

section("Top unusual records", "with explanation")
for _, r in anom.head(5).iterrows():
    alert_card(f"{r['Order_ID']} · {r['Machine_Type']} · {r['Fabric_Type']}",
               f"{r['Reason']}. Efficiency {r['Machine_Efficiency']:.1f}%, waste {r['Waste_Percentage']:.1f}%, "
               f"produced {r['Actual_Production']:,} of {r['Production_Target']:,} target.",
               r["Severity"], f"{r['Date']:%d %b %Y} · supplier {r['Supplier']} · score {r['Anomaly_Score']:.3f}")

cols = ["Date", "Order_ID", "Customer", "Machine_Type", "Fabric_Type", "Severity", "Anomaly_Score",
        *FEATURES.keys(), "Reason"]
table = anom[cols].copy()
table["Date"] = table["Date"].dt.date
st.dataframe(table.round(2), use_container_width=True, hide_index=True)
st.download_button("⬇️ Download anomaly list (CSV)", table.to_csv(index=False).encode(),
                   "barkavi_anomalies.csv", "text/csv", use_container_width=True,
                   on_click=lambda: log_activity("Downloaded anomaly list", f"{len(table)} rows"))
st.caption("Model: Isolation Forest (300 trees) on standardised efficiency, waste %, shortfall %, cost per unit and "
           "delivery days. Reason = the two features furthest from normal (σ = standard deviations).")
footer()
