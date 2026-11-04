"""
Module 3 — Production Planning.
Forecasts daily/weekly/monthly production, efficiency, machine utilization,
and delay risk using trend-based estimation from historical data.
"""

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from utils.ui import setup_page, kpi_card, kpi_row, section, chart, alert_card, footer

setup_page("Production Planning", "🏭", "Output forecast, efficiency, delay risk and planning suggestions", "Module 3")

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "dataset", "powerloom_production_data.csv")
df = pd.read_csv(DATA_PATH, parse_dates=["Date"])

recent = df.sort_values("Date").tail(90)
avg_daily = recent["Actual_Production"].mean()
avg_efficiency = recent["Machine_Efficiency"].mean()

section("Production Forecast", "trend-based, from last 90 records")
delay_risk = "High" if avg_efficiency < 75 else ("Medium" if avg_efficiency < 88 else "Low")
risk_color = {"High": "🔴", "Medium": "🟠", "Low": "🟢"}[delay_risk]
kpi_row([
    dict(label="Predicted Daily", value=f"{avg_daily:,.0f}", icon="📅", color="indigo", sub="units / day"),
    dict(label="Predicted Weekly", value=f"{avg_daily*6:,.0f}", icon="🗓️", color="violet", sub="units / 6-day week"),
    dict(label="Predicted Monthly", value=f"{avg_daily*26:,.0f}", icon="📆", color="sky", sub="units / 26 days"),
    dict(label="Avg Efficiency", value=f"{avg_efficiency:.1f}%", icon="⚙️", color="teal"),
    dict(label="Delay Risk", value=f"{risk_color} {delay_risk}", icon="⏰",
         color={"High": "rose", "Medium": "amber", "Low": "emerald"}[delay_risk]),
])

section("AI Production Suggestions")

suggestions = []
if avg_efficiency < 80:
    suggestions.append("Machine efficiency trending low — schedule maintenance to avoid delays.")
if recent["Actual_Production"].std() > recent["Actual_Production"].mean() * 0.3:
    suggestions.append("Production output is highly variable — consider standardizing shift plans.")
target_gap = (recent["Production_Target"] - recent["Actual_Production"]).mean()
if target_gap > 50:
    suggestions.append(f"Average shortfall of {target_gap:.0f} units vs. target — consider adding a shift or overtime.")
if not suggestions:
    suggestions.append("Production is tracking well against targets. Maintain current planning.")

for s in suggestions:
    alert_card("Suggestion", s, "Info")

section("Production Efficiency Trend")
trend = df.groupby(df["Date"].dt.to_period("M")).agg(
    Production=("Actual_Production", "sum"),
    Efficiency=("Machine_Efficiency", "mean")
).reset_index()
trend["Date"] = trend["Date"].astype(str)

import plotly.graph_objects as go
fig = go.Figure()
fig.add_bar(x=trend["Date"], y=trend["Production"], name="Production",
            marker=dict(color=trend["Production"], colorscale=[[0, "#A5B4FC"], [1, "#4F46E5"]]))
fig.add_scatter(x=trend["Date"], y=trend["Efficiency"], name="Efficiency %", yaxis="y2",
                line=dict(color="#F43F5E", width=3, shape="spline"))
fig.update_layout(title="Monthly Production & Efficiency Trend",
                  yaxis2=dict(overlaying="y", side="right", showgrid=False, title="Efficiency %"))
c1, c2 = st.columns(2)
with c1, st.container(border=True):
    chart(fig, height=400)

fig2 = px.box(df, x="Machine_Type", y="Machine_Efficiency", title="Machine Utilization Distribution by Type",
              color="Machine_Type")
fig2.update_layout(showlegend=False)
with c2, st.container(border=True):
    chart(fig2, height=400)

footer()
