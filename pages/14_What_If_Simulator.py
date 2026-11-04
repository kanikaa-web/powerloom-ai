"""
Advanced — What-If Profit Simulator.
Move price, tariff, labour, efficiency, waste and selling-price levers and
see the monthly profit impact, a waterfall bridge, break-even price and a
sensitivity (tornado) chart. Scenarios can be saved and compared.
"""

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.ui import setup_page, kpi_row, section, chart, footer, money
from utils.data import load_dataset, log_activity
from utils.scenario import monthly_baseline, simulate, sensitivity

setup_page("What-If Simulator", "🎛️", "Test price, tariff, efficiency and waste changes on monthly profit",
           "Advanced · Planning")

df = load_dataset()
months = st.select_slider("Baseline = average month over the last", [3, 6, 12, 24], value=12,
                          format_func=lambda m: f"{m} months")
base = monthly_baseline(df, months)

left, right = st.columns([1, 2.1], gap="large")
with left, st.container(border=True):
    st.markdown("#### 🎚️ Levers")
    presets = {
        "Custom": {},
        "📈 Cotton price spike (+15%)": dict(raw_price=15),
        "⚡ EB tariff hike (+20%)": dict(electricity=20),
        "🔧 After maintenance (+4 eff, −1 waste)": dict(efficiency=4, waste=1.0),
        "💹 Price revision (+10%)": dict(selling_price=10),
    }
    preset = st.selectbox("Quick scenario", list(presets))
    p = presets[preset]
    raw = st.slider("Raw material price change (%)", -30, 50, p.get("raw_price", 0))
    elec = st.slider("Electricity tariff change (%)", -30, 50, p.get("electricity", 0))
    lab = st.slider("Labour cost change (%)", -30, 50, p.get("labour", 0))
    trans = st.slider("Transport cost change (%)", -30, 50, p.get("transport", 0))
    eff = st.slider("Machine efficiency change (points)", -15.0, 15.0, float(p.get("efficiency", 0)), 0.5)
    waste = st.slider("Waste reduction (points)", -3.0, 4.0, float(p.get("waste", 0.0)), 0.25,
                      help=f"Baseline waste is {base['waste_pct']:.2f}%")
    price = st.slider("Selling price change (%)", -20, 100, p.get("selling_price", 0))

b = simulate(base)
s = simulate(base, raw, elec, lab, trans, eff, waste, price)

with right:
    d_profit = s["profit"] - b["profit"]
    kpi_row([
        dict(label="Scenario profit / month", value=money(s['profit']), icon="💰",
             color="emerald" if s["profit"] >= 0 else "rose", sub=f"baseline {money(b['profit'])}"),
        dict(label="Profit change", value=("+" if d_profit > 0 else "") + money(d_profit), icon="📊",
             color="emerald" if d_profit >= 0 else "rose", sub="vs baseline month"),
        dict(label="Break-even price", value=f"₹{s['breakeven_price']:,.2f}", icon="⚖️", color="violet",
             sub=f"per unit · selling at ₹{s['price_per_unit']:,.2f}"),
    ], cols=3)
    st.write("")
    kpi_row([
        dict(label="Production / month", value=f"{s['production']:,.0f}", icon="🏭", color="indigo",
             delta=(s["production"] - b["production"]) / b["production"] * 100),
        dict(label="Revenue / month", value=money(s['revenue']), icon="🧾", color="sky",
             delta=(s["revenue"] - b["revenue"]) / b["revenue"] * 100 if b["revenue"] else None),
        dict(label="Cost / month", value=money(s['total_cost']), icon="💸", color="orange",
             delta=(s["total_cost"] - b["total_cost"]) / b["total_cost"] * 100, delta_good_when_up=False),
    ], cols=3)

    with st.container(border=True):
        steps = [("Revenue", s["revenue"] - b["revenue"]),
                 ("Raw material", -(s["raw"] - b["raw"])),
                 ("Production", -(s["prod_cost"] - b["prod_cost"])),
                 ("Electricity", -(s["electricity"] - b["electricity"])),
                 ("Labour", -(s["labour"] - b["labour"])),
                 ("Transport", -(s["transport"] - b["transport"]))]
        fig = go.Figure(go.Waterfall(
            x=["Baseline profit"] + [n for n, _ in steps] + ["Scenario profit"],
            measure=["absolute"] + ["relative"] * len(steps) + ["total"],
            y=[b["profit"]] + [v for _, v in steps] + [0],
            increasing=dict(marker=dict(color="#10B981")), decreasing=dict(marker=dict(color="#F43F5E")),
            totals=dict(marker=dict(color="#6366F1")), connector=dict(line=dict(color="#CBD5E1"))))
        fig.update_layout(title="Profit bridge: baseline → scenario (₹ / month)", showlegend=False)
        chart(fig, height=360)

c1, c2 = st.columns(2)
with c1, st.container(border=True):
    sens = sensitivity(base)
    fig = go.Figure()
    fig.add_bar(y=sens["Lever"], x=sens["Decrease"], orientation="h", name="Lever ↓", marker_color="#F59E0B")
    fig.add_bar(y=sens["Lever"], x=sens["Increase"], orientation="h", name="Lever ↑", marker_color="#6366F1")
    fig.update_layout(barmode="overlay", title="Sensitivity: profit change for ±10% (eff ±5 pts, waste ±1 pt)",
                      xaxis_title="₹ / month")
    chart(fig, height=380)
with c2, st.container(border=True):
    comp = pd.DataFrame({"Component": ["Raw material", "Production", "Electricity", "Labour", "Transport"],
                         "Baseline": [b["raw"], b["prod_cost"], b["electricity"], b["labour"], b["transport"]],
                         "Scenario": [s["raw"], s["prod_cost"], s["electricity"], s["labour"], s["transport"]]})
    fig = go.Figure()
    fig.add_bar(x=comp["Component"], y=comp["Baseline"], name="Baseline", marker_color="#C7D2FE")
    fig.add_bar(x=comp["Component"], y=comp["Scenario"], name="Scenario", marker_color="#B07A1E")
    fig.update_layout(barmode="group", title="Monthly cost by component (₹)")
    chart(fig, height=380)

# ---------------- Save & compare ----------------
section("Saved scenarios", "compare up to any number side by side")
st.session_state.setdefault("scenarios", [])
n1, n2 = st.columns([3, 1])
name = n1.text_input("Scenario name", value=preset if preset != "Custom" else "My scenario",
                     label_visibility="collapsed")
if n2.button("💾 Save scenario", use_container_width=True):
    st.session_state["scenarios"].append({
        "Scenario": name, "Raw %": raw, "Power %": elec, "Labour %": lab, "Transport %": trans,
        "Eff pts": eff, "Waste pts": waste, "Price %": price,
        "Profit (₹L/month)": round(s["profit"] / 1e5, 2), "Break-even ₹/unit": round(s["breakeven_price"], 2)})
    log_activity("Saved what-if scenario", name)
if st.session_state["scenarios"]:
    sc = pd.DataFrame(st.session_state["scenarios"])
    st.dataframe(sc, use_container_width=True, hide_index=True)
    fig = go.Figure(go.Bar(x=sc["Scenario"], y=sc["Profit (₹L/month)"],
                           marker_color=["#10B981" if v >= 0 else "#F43F5E" for v in sc["Profit (₹L/month)"]]))
    fig.update_layout(title="Profit per scenario (₹ lakh / month)")
    chart(fig, height=300)
    if st.button("🗑️ Clear saved scenarios"):
        st.session_state["scenarios"] = []
        st.rerun()

st.caption(f"Baseline uses the average of the last {base['months']} months in the dataset. Revenue per unit "
           f"(₹{base['price_per_unit']:,.2f}) is derived from recorded profit + recorded costs. Labour is treated as a "
           "fixed monthly cost; other costs scale with output.")
footer()
