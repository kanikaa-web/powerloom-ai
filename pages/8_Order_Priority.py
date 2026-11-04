"""
Module 7 — Order Priority Prediction.
Predicts order priority (High/Medium/Low) and stores the order.
"""

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd
from datetime import date

from utils.ui import setup_page, kpi_card, kpi_row, section, chart, alert_card, footer
from utils.priority_predictor import predict_order_priority
from database.db import fetch_all, execute

setup_page("Order Priority", "⏱️", "Automatic High / Medium / Low priority for incoming orders", "Module 7")

with st.form("priority_form"):
    c1, c2 = st.columns(2)
    with c1:
        order_id = st.text_input("Order ID", value=f"ORD{pd.Timestamp.now().strftime('%y%m%d%H%M')}")
        customer = st.text_input("Customer Name")
        fabric_type = st.selectbox("Fabric Type", ["Cotton", "Poly-Cotton", "Polyester", "Denim", "Terry"])
        order_size = st.number_input("Order Size (units)", 50, 20000, 1000)
    with c2:
        delivery_date = st.date_input("Delivery Date", min_value=date.today())
        customer_priority = st.selectbox("Customer Type", ["VIP", "Regular", "New"])
        machine_availability = st.slider("Current Machine Availability (%)", 0, 100, 60)

    submitted = st.form_submit_button("⏱️ Predict Priority", use_container_width=True)

if submitted:
    result = predict_order_priority(delivery_date.strftime("%Y-%m-%d"), order_size,
                                     customer_priority, machine_availability)

    color = {"High": "🔴", "Medium": "🟠", "Low": "🟢"}[result["priority"]]
    kpi_row([
        dict(label="Predicted priority", value=f"{color} {result['priority']}", icon="⏱️",
             color={"High": "rose", "Medium": "amber", "Low": "emerald"}[result["priority"]],
             sub=f"score {result['score']}/100"),
        dict(label="Urgency", value=result["breakdown"]["urgency_score"], icon="⏰", color="violet"),
        dict(label="Order size", value=result["breakdown"]["size_score"], icon="📦", color="indigo"),
        dict(label="Customer", value=result["breakdown"]["customer_score"], icon="🤝", color="sky"),
        dict(label="Machine", value=result["breakdown"]["machine_score"], icon="⚙️", color="teal"),
    ])

    execute("""INSERT OR REPLACE INTO orders (order_id, customer, fabric_type, quantity, delivery_date, priority)
               VALUES (?,?,?,?,?,?)""",
            (order_id, customer, fabric_type, order_size, delivery_date.strftime("%Y-%m-%d"), result["priority"]))
    from utils.data import log_activity
    log_activity("Order saved", f"{order_id} ({result['priority']})")
    st.success(f"Order {order_id} saved with priority: {result['priority']}")
section("Existing Orders")
orders_df = pd.DataFrame(fetch_all("SELECT * FROM orders ORDER BY created_at DESC LIMIT 100"))
if not orders_df.empty:
    st.dataframe(orders_df, use_container_width=True)
else:
    st.info("No orders recorded yet.")

footer()
