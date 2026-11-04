"""
Module 1 — Raw Material Requirement Prediction.
Compares ML models and predicts material needs for a production plan.
"""

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd
import plotly.express as px

from utils.ui import setup_page, kpi_card, kpi_row, section, chart, alert_card, footer
from utils.predictor import predict_material_requirement, get_model_comparison, get_best_model_summary

setup_page("Raw Material Prediction", "🧪", "ML prediction of cotton, yarn, polyester, dye, chemical & packing needs", "Module 1")

with st.form("prediction_form"):
    c1, c2, c3 = st.columns(3)
    with c1:
        fabric_type = st.selectbox("Fabric Type", ["Cotton", "Poly-Cotton", "Polyester", "Denim", "Terry", "Voile", "Canvas"])
        fabric_gsm = st.number_input("Fabric GSM", 80, 400, 180)
        fabric_width = st.number_input("Fabric Width (inches)", 40.0, 100.0, 60.0)
    with c2:
        machine_type = st.selectbox("Machine Type", ["Sulzer", "Airjet", "Rapier", "Waterjet", "Shuttle"])
        machine_efficiency = st.slider("Machine Efficiency (%)", 50, 100, 85)
        production_qty = st.number_input("Production Quantity (units)", 100, 10000, 1200)
    with c3:
        season = st.selectbox("Season", ["Summer", "Monsoon", "Winter", "Spring"])
        month = st.selectbox("Month", list(range(1, 13)), index=5)
        working_days = st.number_input("Working Days", 15, 31, 26)

    submitted = st.form_submit_button("🔮 Predict Requirement", use_container_width=True)

if submitted:
    with st.spinner("Running prediction models..."):
        try:
            results = predict_material_requirement(
                fabric_type, fabric_gsm, fabric_width, machine_type,
                machine_efficiency, production_qty, season, month, working_days
            )
        except FileNotFoundError:
            st.error("Trained models not found. Please run `python models/train_material_prediction.py` first.")
            st.stop()

    st.success("Prediction complete!")
    total_cost = results.pop("_total_estimated_cost")

    rows = []
    for material, vals in results.items():
        rows.append({"Material": material, **vals})
    result_df = pd.DataFrame(rows)

    section("Predicted Requirement Summary")
    st.dataframe(result_df, use_container_width=True)
    kpi_row([
        dict(label="Total material cost", value=f"₹{total_cost:,.0f}", icon="💰", color="gold"),
        dict(label="Production qty", value=f"{production_qty:,}", icon="🏭", color="indigo", sub=f"{fabric_type} · {machine_type}"),
        dict(label="Materials predicted", value=len(result_df), icon="🧪", color="violet"),
    ], cols=3)

    fig = px.bar(result_df, x="Material", y="reorder_qty", title="Recommended Reorder Quantity by Material",
                 color="Material", text_auto=".0f")
    fig.update_layout(showlegend=False)
    chart(fig)
section("Model Comparison & Accuracy")
summary = get_best_model_summary()

target_display = st.selectbox("Select Material to View Model Comparison",
                               ["Cotton_Used", "Yarn_Used", "Polyester_Used",
                                "Dye_Used", "Chemical_Used", "Packing_Material"])

comp_df = get_model_comparison(target_display)
if not comp_df.empty:
    st.dataframe(comp_df, use_container_width=True)
    best = summary.get(target_display, "N/A")
    st.success(f"✅ Best performing model for {target_display}: **{best}**")

    fig2 = px.bar(comp_df, x="Model", y="Accuracy_%", title=f"Model Accuracy Comparison — {target_display}",
                  color="Model")
    chart(fig2)
else:
    st.info("Run the training script to generate model comparison data.")

footer()
