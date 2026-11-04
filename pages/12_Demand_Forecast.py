"""
Advanced — Demand Forecast & Stock-out Countdown.
ML (Gradient Boosting, recursive) forecast of daily production and material
consumption with back-tested accuracy, confidence band, and projected
reorder / stock-out day for every material in live stock.
"""

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from datetime import date, timedelta
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.ui import setup_page, kpi_row, kpi_card, section, chart, alert_card, footer
from utils.data import load_dataset, daily_series, stock_table, MATERIAL_COLUMNS, log_activity
from utils.forecasting import forecast_series, stockout_projection

setup_page("Demand Forecast", "🔮", "ML forecast of production & material consumption with stock-out countdown",
           "Advanced · AI")

df = load_dataset()
daily = daily_series(df)

TARGETS = {"Production (units)": "Actual_Production", "Orders (count)": "Orders",
           **{f"{k} consumption": v for k, v in MATERIAL_COLUMNS.items()}}

c1, c2, c3 = st.columns([1.4, 1, 1])
target_label = c1.selectbox("What to forecast", list(TARGETS))
horizon = c2.select_slider("Horizon (days)", [14, 30, 60, 90], value=30)
history_days = c3.select_slider("History shown (days)", [60, 90, 180, 365], value=90)
col = TARGETS[target_label]

series = daily[col]
with st.spinner("Training forecast model & back-testing..."):
    res = forecast_series(tuple(series.values.round(4)), str(series.index[0].date()), horizon)
fc, bt, met = res["forecast"], res["backtest"], res["metrics"]

recent_avg = series.tail(28).mean()
fc_avg = fc["yhat"].mean()
kpi_row([
    dict(label=f"Forecast total ({horizon}d)", value=f"{fc['yhat'].sum():,.0f}", icon="📦", color="violet"),
    dict(label="Forecast daily avg", value=f"{fc_avg:,.1f}", icon="📅", color="indigo",
         delta=(fc_avg - recent_avg) / recent_avg * 100 if recent_avg else None, sub="vs last 28 days"),
    dict(label="Back-test accuracy", value=f"{met['Accuracy']:.1f}%", icon="🎯", color="emerald",
         sub=f"100 − MAPE on last 60 days"),
    dict(label="Back-test MAE", value=f"{met['MAE']:,.1f}", icon="📏", color="amber", sub="avg absolute error / day"),
])

section("Forecast", f"{target_label} · next {horizon} days after the last recorded date")
with st.container(border=True):
    hist = series.tail(history_days)
    fig = go.Figure()
    fig.add_scatter(x=hist.index, y=hist.values, name="Actual", mode="lines",
                    line=dict(color="#6366F1", width=2))
    fig.add_scatter(x=hist.index, y=hist.rolling(7).mean(), name="7-day avg", mode="lines",
                    line=dict(color="#B07A1E", width=2, dash="dot"))
    fig.add_scatter(x=list(fc.index) + list(fc.index[::-1]), y=list(fc["upper"]) + list(fc["lower"][::-1]),
                    fill="toself", fillcolor="rgba(244,63,94,0.14)", line=dict(width=0),
                    name="~80% band", hoverinfo="skip")
    fig.add_scatter(x=fc.index, y=fc["yhat"], name="Forecast", mode="lines+markers",
                    line=dict(color="#F43F5E", width=3), marker=dict(size=5))
    fig.add_vline(x=series.index[-1], line_dash="dash", line_color="#94A3B8")
    fig.update_layout(title=f"{target_label}: history & forecast", hovermode="x unified")
    chart(fig, height=430)

c4, c5 = st.columns(2)
with c4, st.container(border=True):
    fig = go.Figure()
    fig.add_scatter(x=bt.index, y=bt["actual"], name="Actual", line=dict(color="#6366F1"))
    fig.add_scatter(x=bt.index, y=bt["predicted"], name="Model", line=dict(color="#F59E0B", width=3))
    fig.update_layout(title="Back-test: model vs actual (last 60 days, unseen)")
    chart(fig, height=330)
with c5, st.container(border=True):
    wk = fc["yhat"].groupby(pd.Grouper(freq="W")).sum()
    fig = go.Figure(go.Bar(x=[f"Wk of {d:%d %b}" for d in wk.index], y=wk.values,
                           marker=dict(color=wk.values, colorscale=[[0, "#FDE68A"], [1, "#D97706"]])))
    fig.update_layout(title="Forecast by week")
    chart(fig, height=330)

# ---------------- Stock-out countdown ----------------
section("Stock-out countdown", "live stock ÷ forecast daily consumption")
stock = stock_table()
rows = []
with st.spinner("Forecasting every material..."):
    for _, r in stock.iterrows():
        mcol = MATERIAL_COLUMNS.get(r["material_name"])
        if not mcol:
            continue
        s = daily[mcol]
        f = forecast_series(tuple(s.values.round(4)), str(s.index[0].date()), 90)["forecast"]["yhat"]
        p = stockout_projection(float(r["current_stock"]), float(r["reorder_level"]), f)
        rows.append({"Material": r["material_name"], "Unit": r["unit"], "Current stock": r["current_stock"],
                     "Reorder level": r["reorder_level"], "Forecast use / day": round(f.head(30).mean(), 1),
                     "Reorder in (days)": p["reorder_in_days"], "Stock-out in (days)": p["stockout_in_days"],
                     "Need for 30 days": round(f.head(30).sum(), 0),
                     "Suggested order qty": round(max(0, f.head(30).sum() + r["reorder_level"] - r["current_stock"]), 0)})
so = pd.DataFrame(rows)

today = date.today()
cols = st.columns(len(so) if len(so) else 1)
for c, (_, r) in zip(cols, so.iterrows()):
    d = r["Stock-out in (days)"]
    with c:
        color = "rose" if d is not None and d <= 7 else ("amber" if d is not None and d <= 21 else "emerald")
        kpi_card(r["Material"], f"{d} days" if d is not None else "90+ days", "⏳", color,
                 sub=(f"≈ {today + timedelta(days=int(d)):%d %b}" if d is not None else "beyond horizon"))

st.write("")
with st.container(border=True):
    fig = go.Figure()
    for i, (_, r) in enumerate(so.iterrows()):
        fig.add_bar(name=r["Material"], x=[r["Material"]],
                    y=[r["Stock-out in (days)"] if pd.notna(r["Stock-out in (days)"]) else 90])
    fig.add_hline(y=7, line_dash="dash", line_color="#E11D48", annotation_text="7-day danger line")
    fig.update_layout(title="Days of stock remaining (capped at 90)", showlegend=False, yaxis_title="Days")
    chart(fig, height=330)

st.dataframe(so, use_container_width=True, hide_index=True)
st.download_button("⬇️ Download purchase plan (CSV)", so.to_csv(index=False).encode(),
                   "barkavi_purchase_plan.csv", "text/csv", use_container_width=True,
                   on_click=lambda: log_activity("Downloaded purchase plan"))

urgent = so[so["Stock-out in (days)"].notna() & (so["Stock-out in (days)"] <= 7)]
for _, r in urgent.iterrows():
    alert_card(f"{r['Material']} runs out in {r['Stock-out in (days)']} days",
               f"Order about {r['Suggested order qty']:,.0f} {r['Unit']} to cover the next 30 days plus reorder buffer.",
               "Critical" if r["Stock-out in (days)"] <= 3 else "High")

st.caption("Stock-out days are counted from today using live stock from the database and the ML forecast of daily "
           "consumption learned from the production dataset.")
footer()
