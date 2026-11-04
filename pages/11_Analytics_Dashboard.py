"""
Module 10 — Analytics Dashboard.
Interactive Plotly charts: pie, bar, line, scatter, heatmap, monthly/yearly trends.
"""

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd
import plotly.express as px

from utils.ui import setup_page, kpi_card, kpi_row, section, chart, alert_card, footer

setup_page("Analytics", "📈", "Interactive deep-dive into production, materials, suppliers and costs", "Module 10")

from utils.data import load_dataset

df = load_dataset()
years = sorted(df["Year"].unique())
sel = st.multiselect("Years", years, default=years)
if sel:
    df = df[df["Year"].isin(sel)]

c1, c2 = st.columns(2)
with c1, st.container(border=True):
    fig1 = px.pie(df, names="Fabric_Type", title="Orders by Fabric Type", hole=0.55)
    fig1.update_traces(textinfo="percent+label", marker=dict(line=dict(color="#FBF8F2", width=3)))
    fig1.update_layout(showlegend=False)
    chart(fig1, height=380)
with c2, st.container(border=True):
    sp = df.groupby("Supplier")["Raw_Material_Cost"].sum().reset_index().sort_values("Raw_Material_Cost")
    fig2 = px.bar(sp, x="Raw_Material_Cost", y="Supplier", orientation="h", color="Supplier",
                  title="Raw Material Spend by Supplier (₹)")
    fig2.update_layout(showlegend=False, yaxis_title="")
    chart(fig2, height=380)

c3, c4 = st.columns(2)
with c3, st.container(border=True):
    yearly = df.groupby(["Year", "Fabric_Type"])["Actual_Production"].sum().reset_index()
    fig3 = px.bar(yearly, x="Year", y="Actual_Production", color="Fabric_Type", title="Yearly Production by Fabric")
    chart(fig3, height=380)
with c4, st.container(border=True):
    fig4 = px.scatter(df.sample(min(800, len(df)), random_state=1), x="Machine_Efficiency", y="Waste_Percentage",
                      color="Machine_Type", trendline=None, opacity=0.7, title="Efficiency vs Wastage")
    chart(fig4, height=380)

c5, c6 = st.columns(2)
with c5, st.container(border=True):
    fs = df.pivot_table(index="Fabric_Type", columns="Season", values="Actual_Production", aggfunc="sum")
    fig = px.imshow(fs, color_continuous_scale=["#FFF7E6", "#D4A445", "#7C3AED"], text_auto=".2s",
                    aspect="auto", title="Production: fabric × season")
    chart(fig, height=380)
with c6, st.container(border=True):
    fig = px.box(df, x="Supplier", y="Delivery_Days", color="Supplier", title="Delivery days by supplier")
    fig.update_layout(showlegend=False, xaxis_title="")
    chart(fig, height=380)

section("Correlation Heatmap")
numeric_cols = ["Fabric_GSM", "Machine_Efficiency", "Actual_Production", "Cotton_Used",
                "Yarn_Used", "Raw_Material_Cost", "Profit", "Waste_Percentage"]
corr = df[numeric_cols].corr()
with st.container(border=True):
    fig5 = px.imshow(corr, text_auto=".2f", color_continuous_scale=["#4F46E5", "#FFFFFF", "#B07A1E"],
                     zmin=-1, zmax=1, title="Feature Correlation Heatmap")
    chart(fig5, height=480)

section("Monthly Consumption Trend")
monthly = df.groupby(df["Date"].dt.to_period("M"))[["Cotton_Used", "Yarn_Used", "Polyester_Used",
                                                     "Dye_Used", "Chemical_Used"]].sum()
monthly.index = monthly.index.to_timestamp()
with st.container(border=True):
    fig6 = px.area(monthly, x=monthly.index, y=monthly.columns, title="Monthly Material Consumption Trend")
    fig6.update_layout(xaxis_title="", yaxis_title="kg / litre")
    chart(fig6, height=400)

footer()
