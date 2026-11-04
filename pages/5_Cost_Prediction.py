"""
Module 4 — Cost Prediction.
Predicts raw material, production, labour, electricity, transport cost,
total manufacturing cost, expected profit, and profit margin.
"""

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd
import plotly.express as px

from utils.ui import setup_page, kpi_card, kpi_row, section, chart, alert_card, footer
from utils.cost_calculator import calculate_costs
from utils.predictor import predict_material_requirement

setup_page("Cost Prediction", "💰", "Full manufacturing cost, expected profit and margin for a production plan", "Module 4")

with st.form("cost_form"):
    c1, c2, c3 = st.columns(3)
    with c1:
        fabric_type = st.selectbox("Fabric Type", ["Cotton", "Poly-Cotton", "Polyester", "Denim", "Terry", "Voile", "Canvas"])
        fabric_gsm = st.number_input("Fabric GSM", 80, 400, 180)
        fabric_width = st.number_input("Fabric Width", 40.0, 100.0, 60.0)
    with c2:
        machine_type = st.selectbox("Machine Type", ["Sulzer", "Airjet", "Rapier", "Waterjet", "Shuttle"])
        machine_efficiency = st.slider("Machine Efficiency (%)", 50, 100, 85)
        production_qty = st.number_input("Production Quantity", 100, 10000, 1200)
    with c3:
        season = st.selectbox("Season", ["Summer", "Monsoon", "Winter", "Spring"])
        month = st.selectbox("Month", list(range(1, 13)), index=5)
        working_days = st.number_input("Working Days", 15, 31, 26)

    distance_factor = st.slider("Transport Distance Factor (1 = local, 2 = far)", 0.5, 3.0, 1.0)
    submitted = st.form_submit_button("💵 Predict Costs", use_container_width=True)

if submitted:
    with st.spinner("Calculating cost projection..."):
        try:
            material_results = predict_material_requirement(
                fabric_type, fabric_gsm, fabric_width, machine_type,
                machine_efficiency, production_qty, season, month, working_days
            )
            raw_material_cost = material_results.pop("_total_estimated_cost")
        except FileNotFoundError:
            st.error("Trained models not found. Please run the training script first.")
            st.stop()

        costs = calculate_costs(raw_material_cost, production_qty, working_days, distance_factor)

    st.success("Cost prediction complete!")

    labels = [("raw_material_cost", "🧵", "violet"), ("production_cost", "🏭", "indigo"),
              ("electricity_cost", "⚡", "amber"), ("labour_cost", "👷", "sky"),
              ("transport_cost", "🚚", "orange"), ("total_manufacturing_cost", "💸", "rose")]
    kpi_row([dict(label=k.replace("_", " ").title(), value=f"₹{costs[k]:,.0f}", icon=i, color=c)
             for k, i, c in labels], cols=3)
    st.write("")
    kpi_row([
        dict(label="Expected Profit", value=f"₹{costs['expected_profit']:,.0f}", icon="💰",
             color="emerald" if costs["expected_profit"] >= 0 else "rose"),
        dict(label="Profit Margin", value=f"{costs['profit_margin_pct']}%", icon="📊", color="teal"),
    ], cols=2)

    chart_df = pd.DataFrame({
        "Component": ["Raw Material", "Production", "Electricity", "Labour", "Transport"],
        "Cost": [costs["raw_material_cost"], costs["production_cost"], costs["electricity_cost"],
                 costs["labour_cost"], costs["transport_cost"]]
    })
    c1, c2 = st.columns(2)
    with c1, st.container(border=True):
        fig = px.pie(chart_df, names="Component", values="Cost", title="Cost Breakdown", hole=0.55)
        fig.update_traces(textinfo="percent+label", marker=dict(line=dict(color="#FBF8F2", width=3)))
        chart(fig, height=380)
    with c2, st.container(border=True):
        fig = px.bar(chart_df.sort_values("Cost"), x="Cost", y="Component", orientation="h", color="Component",
                     title="Cost by component (₹)", text_auto=",.0f")
        fig.update_layout(showlegend=False, yaxis_title="")
        chart(fig, height=380)

footer()
