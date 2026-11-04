"""
Module 5 — Material Wastage Prediction.
Predicts waste %, quantity, cost, and generates root-cause + AI recommendations.
"""

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import plotly.graph_objects as go

from utils.ui import setup_page, kpi_card, kpi_row, section, chart, alert_card, footer
from utils.wastage_predictor import predict_wastage

setup_page("Wastage Prediction", "♻️", "Expected waste %, quantity, cost and root-cause analysis", "Module 5")

with st.form("wastage_form"):
    c1, c2 = st.columns(2)
    with c1:
        machine_efficiency = st.slider("Machine Efficiency (%)", 50, 100, 85)
        fabric_gsm = st.number_input("Fabric GSM", 80, 400, 180)
    with c2:
        machine_type = st.selectbox("Machine Type", ["Sulzer", "Airjet", "Rapier", "Waterjet", "Shuttle"])
        production_qty = st.number_input("Production Quantity", 100, 10000, 1200)

    material_cost = st.number_input("Material Unit Cost (₹/kg)", 50.0, 500.0, 165.0)
    submitted = st.form_submit_button("♻️ Predict Wastage", use_container_width=True)

if submitted:
    result = predict_wastage(machine_efficiency, fabric_gsm, machine_type, production_qty, material_cost)

    kpi_row([
        dict(label="Expected Waste", value=f"{result['expected_waste_pct']}%", icon="♻️", color="amber"),
        dict(label="Waste Quantity", value=f"{result['waste_quantity']} kg", icon="⚖️", color="orange"),
        dict(label="Waste Cost", value=f"₹{result['waste_cost']:,.0f}", icon="💸", color="rose"),
    ])

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=result["expected_waste_pct"],
        title={"text": "Wastage Gauge (%)"},
        gauge={"axis": {"range": [0, 15]},
               "bar": {"color": "#B07A1E", "thickness": 0.28},
               "steps": [{"range": [0, 6], "color": "#D5F5E3"},
                         {"range": [6, 10], "color": "#FCF3CF"},
                         {"range": [10, 15], "color": "#FADBD8"}]}
    ))
    chart(fig)

    c1, c2 = st.columns(2)
    with c1:
        section("Root Cause Analysis")
        for cause in result["root_causes"]:
            alert_card("Root cause", cause, "Medium")
    with c2:
        section("AI Recommendations")
        for rec in result["recommendations"]:
            alert_card("Recommendation", rec, "Low")

footer()
