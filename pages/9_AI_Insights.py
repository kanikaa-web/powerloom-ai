"""
Module 8 — AI Insights.
Generates intelligent, plain-English business insights from live data.
"""

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd

from utils.ui import setup_page, kpi_card, kpi_row, section, chart, alert_card, footer
from utils.insights_generator import generate_insights
from database.db import fetch_all

setup_page("AI Business Insights", "🤖", "Plain-English insights generated from live stock and production data", "Module 8")

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "dataset", "powerloom_production_data.csv")
df = pd.read_csv(DATA_PATH, parse_dates=["Date"])
recent = df.sort_values("Date").tail(60)

stock_df = pd.DataFrame(fetch_all("SELECT * FROM stock"))

avg_daily_consumption = {
    "Cotton": recent["Cotton_Used"].mean(),
    "Yarn": recent["Yarn_Used"].mean(),
    "Polyester": recent["Polyester_Used"].mean(),
    "Dye": recent["Dye_Used"].mean(),
    "Chemical": recent["Chemical_Used"].mean(),
    "Packing Material": recent["Packing_Material"].mean(),
}

machine_efficiency = round(recent["Machine_Efficiency"].mean(), 1)
half = len(recent) // 2
profit_trend_pct = round(((recent["Profit"].tail(half).mean() - recent["Profit"].head(half).mean()) /
                           abs(recent["Profit"].head(half).mean() + 1e-6)) * 100, 1)
waste_pct = round(recent["Waste_Percentage"].mean(), 1)

kpi_row([
    dict(label="Avg Machine Efficiency", value=f"{machine_efficiency}%", icon="⚙️", color="teal", sub="last 60 records"),
    dict(label="Profit Trend", value=f"{profit_trend_pct}%", icon="📈",
         color="emerald" if profit_trend_pct >= 0 else "rose", sub="2nd half vs 1st half of window"),
    dict(label="Avg Wastage", value=f"{waste_pct}%", icon="♻️", color="amber"),
], cols=3)

st.button("🔄 Refresh Insights", use_container_width=True)
insights = generate_insights(stock_df, avg_daily_consumption, machine_efficiency, profit_trend_pct, waste_pct)

section("Key Insights")
for i, insight in enumerate(insights):
    alert_card(f"Insight {i + 1}", insight, ["Info", "Low", "Medium"][i % 3])

footer()
