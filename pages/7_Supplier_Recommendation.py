"""
Module 6 — Supplier Recommendation.
Recommends top 5 suppliers ranked by price, quality, delivery, rating, availability.
"""

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import plotly.express as px

from utils.ui import setup_page, kpi_card, kpi_row, section, chart, alert_card, footer
from utils.supplier_recommender import recommend_suppliers
from database.db import fetch_all

setup_page("Supplier Recommendation", "🚚", "Suppliers ranked on price, quality, delivery, rating and availability", "Module 6")

materials = sorted(set(r["material_supplied"] for r in fetch_all("SELECT DISTINCT material_supplied FROM suppliers")))
material_filter = st.selectbox("Filter by Material (optional)", ["All"] + materials)

top_n = st.slider("Number of top suppliers to show", 3, 10, 5)

result_df = recommend_suppliers(
    material_name=None if material_filter == "All" else material_filter,
    top_n=top_n
)

if result_df.empty:
    st.info("No suppliers found. Add suppliers in the database.")
else:
    best = result_df.iloc[0]
    kpi_row([
        dict(label="Top pick", value=best["name"], icon="🏆", color="gold", sub=f"score {best['final_score']}/100"),
        dict(label="Price", value=f"₹{best['price_per_unit']}", icon="💲", color="emerald", sub="per unit"),
        dict(label="Delivery", value=f"{best['avg_delivery_days']} days", icon="🚚", color="sky"),
        dict(label="Suppliers compared", value=len(result_df), icon="📋", color="indigo"),
    ])
    section(f"Top {top_n} Recommended Suppliers")
    st.dataframe(result_df, use_container_width=True)

    fig = px.bar(result_df, x="name", y="final_score", color="final_score",
                 title="Supplier Recommendation Score", color_continuous_scale=["#FDE68A", "#F59E0B", "#B07A1E"], text_auto=".1f")
    chart(fig)

    best = result_df.iloc[0]
    st.success(f"✅ Top pick: **{best['name']}** with a score of {best['final_score']}/100 "
               f"(₹{best['price_per_unit']}/unit, {best['avg_delivery_days']} day delivery)")

footer()
