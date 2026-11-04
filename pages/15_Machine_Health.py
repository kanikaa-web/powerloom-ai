"""
Advanced — Machine Health & Predictive Maintenance.
Scores each machine type 0–100 from efficiency, trend, waste, target
achievement and stability; recommends service timing; logs maintenance.
"""

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from datetime import date, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.ui import setup_page, kpi_row, section, chart, gauge, alert_card, pill, footer, PALETTE
from utils.data import load_dataset, log_activity
from utils.machine_health import machine_health
from database.db import execute, fetch_all

setup_page("Machine Health", "🔧", "Health score, degradation trend and predictive maintenance per machine type",
           "Advanced · Maintenance")

df = load_dataset()
window = st.select_slider("Assessment window", [30, 60, 90, 180], value=90, format_func=lambda d: f"Last {d} days")
mh = machine_health(df, window)

kpi_row([
    dict(label="Fleet health", value=f"{mh['Health_Score'].mean():.0f}/100", icon="💚", color="emerald"),
    dict(label="Healthy", value=int((mh["Status"] == "Healthy").sum()), icon="🟢", color="teal",
         sub=f"of {len(mh)} machine types"),
    dict(label="Watch", value=int((mh["Status"] == "Watch").sum()), icon="🟡", color="amber"),
    dict(label="Critical", value=int((mh["Status"] == "Critical").sum()), icon="🔴", color="rose"),
])

section("Health score by machine type")
cols = st.columns(len(mh))
colors = {"Healthy": "#10B981", "Watch": "#F59E0B", "Critical": "#E11D48"}
for c, (_, r) in zip(cols, mh.sort_values("Machine_Type").iterrows()):
    with c, st.container(border=True):
        chart(gauge(r["Health_Score"], r["Machine_Type"], suffix="", color=colors[r["Status"]],
                    bands=[(0, .5, "#FEE2E2"), (.5, .7, "#FEF3C7"), (.7, 1, "#DCFCE7")]), height=200,
              key=f"g_{r['Machine_Type']}")
        sev = {"Healthy": "Low", "Watch": "Medium", "Critical": "Critical"}[r["Status"]]
        st.markdown(f"<div style='text-align:center'>{pill(r['Status'], sev)}<br>"
                    f"<span style='font-size:.8rem;color:#6B6580'>Service in ≤ {r['Next_Service_In_Days']} days · "
                    f"due {date.today() + timedelta(days=int(r['Next_Service_In_Days'])):%d %b}</span></div>",
                    unsafe_allow_html=True)

c1, c2 = st.columns(2)
with c1, st.container(border=True):
    end = df["Date"].max()
    w = df[df["Date"] > end - pd.Timedelta(days=365)]
    wk = w.groupby([pd.Grouper(key="Date", freq="W"), "Machine_Type"])["Machine_Efficiency"].mean().reset_index()
    wk["Smoothed"] = wk.groupby("Machine_Type")["Machine_Efficiency"].transform(lambda s: s.rolling(4, 1).mean())
    fig = px.line(wk, x="Date", y="Smoothed", color="Machine_Type", title="Weekly efficiency trend (4-wk smoothed, 1 yr)")
    fig.update_layout(yaxis_title="Efficiency %", xaxis_title="")
    chart(fig, height=380)
with c2, st.container(border=True):
    cats = ["Efficiency", "Low waste", "Target hit", "Stability", "Trend"]
    fig = go.Figure()
    for i, (_, r) in enumerate(mh.iterrows()):
        vals = [min(100, max(0, (r["Avg_Efficiency"] - 60) / 38 * 100)),
                min(100, max(0, (12 - r["Avg_Waste_%"]) / 10 * 100)),
                min(100, max(0, (r["Target_Achievement_%"] - 60) / 40 * 100)),
                min(100, max(0, (15 - r["Variability_%"]) / 15 * 100)),
                min(100, max(0, 50 + r["Weekly_Trend"] * 100))]
        fig.add_trace(go.Scatterpolar(r=vals + vals[:1], theta=cats + cats[:1], fill="toself", opacity=0.55,
                                      name=r["Machine_Type"], line=dict(color=PALETTE[i % len(PALETTE)])))
    fig.update_layout(title="Health factor radar (0–100)", polar=dict(radialaxis=dict(range=[0, 100], showticklabels=False)))
    chart(fig, height=380)

section("Maintenance recommendations")
for _, r in mh.iterrows():
    sev = {"Healthy": "Low", "Watch": "Medium", "Critical": "Critical"}[r["Status"]]
    alert_card(f"{r['Machine_Type']} — {r['Health_Score']}/100",
               r["Recommendation"], sev,
               f"Efficiency {r['Avg_Efficiency']}% ({r['Efficiency_Change']:+.2f} pts vs previous window) · "
               f"waste {r['Avg_Waste_%']}% · target {r['Target_Achievement_%']}% · variability {r['Variability_%']}%")

with st.expander("📋 Full health table"):
    st.dataframe(mh, use_container_width=True, hide_index=True)

section("Maintenance log", "record service work")
with st.form("maint_form", clear_on_submit=True):
    m1, m2, m3 = st.columns(3)
    mtype = m1.selectbox("Machine type", sorted(df["Machine_Type"].unique()))
    sdate = m2.date_input("Service date", date.today())
    hours = m3.number_input("Downtime (hours)", 0.0, 200.0, 2.0, 0.5)
    m4, m5 = st.columns([2, 1])
    work = m4.text_input("Work done", placeholder="e.g. Reed replaced, warp tension reset")
    cost = m5.number_input("Cost (₹)", 0.0, 1e7, 0.0, 100.0)
    if st.form_submit_button("➕ Add service record", use_container_width=True):
        execute("""INSERT INTO maintenance_log (machine_type, service_date, work_done, downtime_hours, cost, performed_by)
                   VALUES (?,?,?,?,?,?)""",
                (mtype, sdate.isoformat(), work, hours, cost, st.session_state.get("username", "system")))
        log_activity("Maintenance logged", f"{mtype}: {work}")
        st.success("Service record saved.")

ml = pd.DataFrame(fetch_all("SELECT * FROM maintenance_log ORDER BY service_date DESC"))
if ml.empty:
    st.info("No maintenance records yet.")
else:
    m1, m2 = st.columns([1.6, 1])
    m1.dataframe(ml.drop(columns=["id"]), use_container_width=True, hide_index=True)
    with m2:
        agg = ml.groupby("machine_type").agg(Downtime=("downtime_hours", "sum"), Cost=("cost", "sum")).reset_index()
        fig = px.bar(agg, x="machine_type", y="Downtime", color="machine_type", title="Downtime hours by machine")
        fig.update_layout(showlegend=False, xaxis_title="")
        chart(fig, height=300)

st.caption("The dataset records machine type, not individual loom IDs, so health is scored per machine type. "
           "Score = 40% efficiency + 20% trend + 20% waste + 10% target achievement + 10% stability.")
footer()
