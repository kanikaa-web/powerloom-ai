"""
app.py
------
Main entry point for the Barkavi Textiles AI-Powered Smart Powerloom Prediction &
Production Planning System. Handles login, role-based access
(Admin/Manager/Employee seeded users), forgot password, and the home page
that links to the multi-page Streamlit app (see /pages).
"""

import os
import sys
import logging
import pandas as pd
import streamlit as st

sys.path.append(os.path.dirname(__file__))

from database.db import init_db, seed_default_data
from utils.auth import login_user, is_logged_in, reset_password, update_profile
from models.train_material_prediction import ensure_models_trained
from utils.branding import (BRAND_NAME, BRAND_TAGLINE, BRAND_SUBTITLE, BRAND_ADDRESS,
                            LOGO_MAIN, page_icon, apply_sidebar_logo)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title=f"{BRAND_NAME} | Powerloom AI System",
    page_icon=page_icon(),
    layout="wide",
    initial_sidebar_state="expanded",
)

from utils.ui import inject_css, hero, section, kpi_row, tile, sidebar_user, footer  # noqa: E402
from utils.data import load_dataset, stock_table, log_activity  # noqa: E402

inject_css()
apply_sidebar_logo()

# ---------- Initialize DB on first run ----------
init_db()
seed_default_data()

# ---------- Ensure ML models exist & match THIS machine's library versions ----------
if "models_ready" not in st.session_state:
    with st.spinner("First-time setup: preparing dataset and training ML models "
                    "(this happens once, may take 30-60 seconds)..."):
        ensure_models_trained()
    st.session_state["models_ready"] = True

LOGIN_CSS = """
<style>
.login-brand {
    border-radius: 24px; padding: 34px 32px; height: 100%; min-height: 520px; color: #fff;
    background: linear-gradient(150deg, #1A1446 0%, #3B2A8C 55%, #B07A1E 120%);
    box-shadow: 0 18px 44px rgba(26,20,70,.28); position: relative; overflow: hidden;
}
.login-brand::before { content:""; position:absolute; inset:0;
    background: repeating-linear-gradient(115deg, rgba(255,255,255,.04) 0 2px, transparent 2px 16px); }
.login-brand h2 { color:#fff; font-size:1.7rem; font-weight:800; margin:.4rem 0 .4rem 0; position:relative; }
.login-brand p { color:#E9E3FF; position:relative; }
.login-brand .feat { display:flex; gap:.7rem; align-items:center; margin:.65rem 0; position:relative; font-size:.95rem; }
.login-brand .feat span:first-child { width:34px; height:34px; border-radius:10px; display:flex; align-items:center;
    justify-content:center; background: rgba(245,213,140,.22); }
.login-brand .addr { font-size:.78rem; opacity:.8; margin-top:1.6rem; position:relative; }
.login-logo { background:#FDFDF5; border-radius:16px; padding:10px 14px; display:inline-block; position:relative; }
</style>
"""


def login_screen():
    st.markdown(LOGIN_CSS, unsafe_allow_html=True)
    st.write("")
    left, right = st.columns([1.15, 1], gap="large")

    with left:
        import base64
        logo_b64 = ""
        if os.path.exists(LOGO_MAIN):
            with open(LOGO_MAIN, "rb") as f:
                logo_b64 = base64.b64encode(f.read()).decode()
        logo_html = (f"<div class='login-logo'><img src='data:image/png;base64,{logo_b64}' style='height:70px'></div>"
                     if logo_b64 else f"<h2>{BRAND_NAME}</h2>")
        feats = [("🧪", "ML raw-material requirement prediction"),
                 ("📈", "30–90 day demand & stock-out forecasting"),
                 ("🚨", "Anomaly detection & smart alerts"),
                 ("🔧", "Machine health & predictive maintenance"),
                 ("🎛️", "What-If profit simulator"),
                 ("📄", "Branded PDF / Excel reports")]
        st.markdown(
            f"<div class='login-brand'>{logo_html}<h2>{BRAND_TAGLINE}</h2><p>{BRAND_SUBTITLE}</p>"
            + "".join(f"<div class='feat'><span>{i}</span><span>{t}</span></div>" for i, t in feats)
            + f"<div class='addr'>📍 {BRAND_ADDRESS}</div></div>",
            unsafe_allow_html=True)

    with right:
        st.markdown("<h2 style='margin-bottom:0'>Welcome back 👋</h2>"
                    "<p style='color:#6B6580'>Sign in to continue to your production workspace.</p>",
                    unsafe_allow_html=True)
        tab_login, tab_forgot = st.tabs(["🔐 Login", "❓ Forgot Password"])

        with tab_login:
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="e.g. admin")
                password = st.text_input("Password", type="password", placeholder="••••••••")
                submitted = st.form_submit_button("Login →", use_container_width=True)

                if submitted:
                    if not username or not password:
                        st.warning("Please enter both username and password.")
                    else:
                        user = login_user(username, password)
                        if user:
                            log_activity("Login", f"Role: {user['role']}", user=user["username"])
                            st.success(f"Welcome, {user['full_name']} ({user['role']})")
                            st.rerun()
                        else:
                            st.error("Invalid username or password.")

            with st.expander("Demo credentials"):
                st.code(
                    "Admin    -> admin / Admin@123\n"
                    "Manager  -> manager / Manager@123\n"
                    "Employee -> employee / Employee@123"
                )

        with tab_forgot:
            with st.form("forgot_form"):
                f_username = st.text_input("Username", key="forgot_username")
                new_pass = st.text_input("New Password", type="password")
                confirm_pass = st.text_input("Confirm New Password", type="password")
                reset_submitted = st.form_submit_button("Reset Password", use_container_width=True)

                if reset_submitted:
                    if new_pass != confirm_pass:
                        st.error("Passwords do not match.")
                    elif len(new_pass) < 6:
                        st.warning("Password should be at least 6 characters.")
                    else:
                        if reset_password(f_username, new_pass):
                            log_activity("Password reset", "", user=f_username)
                            st.success("Password reset successful. Please login.")
                        else:
                            st.error("Username not found.")
    footer()


def main_landing():
    sidebar_user()
    with st.sidebar:
        with st.expander("✏️ Edit Profile"):
            new_name = st.text_input("Full Name", value=st.session_state.get("full_name", ""))
            new_email = st.text_input("Email")
            if st.button("Update Profile"):
                update_profile(st.session_state["username"], new_name, new_email)
                st.session_state["full_name"] = new_name
                log_activity("Profile updated")
                st.success("Profile updated.")

    first = (st.session_state.get("full_name") or "").split(" ")[0]
    hero(f"Welcome, {first}" if first else f"Welcome to {BRAND_NAME}", "👋",
         f"{BRAND_TAGLINE} — choose a module below or from the sidebar.", BRAND_NAME)

    # ---------- quick stats ----------
    df = load_dataset()
    stock = stock_table()
    last30 = df[df["Date"] > df["Date"].max() - pd.Timedelta(days=30)]
    low = int((stock["current_stock"] <= stock["reorder_level"]).sum()) if not stock.empty else 0
    kpi_row([
        dict(label="Production (30d)", value=f"{int(last30['Actual_Production'].sum()):,}", icon="🏭", color="indigo",
             sub="units, latest 30 days of data"),
        dict(label="Avg Efficiency", value=f"{last30['Machine_Efficiency'].mean():.1f}%", icon="⚙️", color="teal"),
        dict(label="Avg Waste", value=f"{last30['Waste_Percentage'].mean():.1f}%", icon="♻️", color="amber"),
        dict(label="Low-stock Items", value=low, icon="📦", color="rose" if low else "emerald",
             sub="at or below reorder level"),
    ])

    section("Core Modules", "Prediction, planning and operations")
    core = [
        ("📊", "Dashboard", "KPIs, trends, stock levels and alerts at a glance", "indigo", "Overview"),
        ("🧪", "Material Prediction", "ML prediction of cotton, yarn, dye & more per order", "violet", "Module 1"),
        ("📦", "Inventory", "Stock entry, history and reorder alerts", "teal", "Module 2"),
        ("🏭", "Production Planning", "Output forecast, efficiency & delay risk", "sky", "Module 3"),
        ("💰", "Cost Prediction", "Full manufacturing cost & profit estimate", "amber", "Module 4"),
        ("♻️", "Wastage Prediction", "Waste %, cost and root-cause analysis", "emerald", "Module 5"),
        ("🚚", "Supplier Recommendation", "Top suppliers ranked on price, quality, speed", "orange", "Module 6"),
        ("⏱️", "Order Priority", "Auto-prioritise incoming orders", "rose", "Module 7"),
        ("🤖", "AI Insights", "Plain-English business insights", "gold", "Module 8"),
        ("📄", "Reports", "Branded PDF & Excel exports", "slate", "Module 9"),
        ("📈", "Analytics", "Deep-dive interactive analytics", "indigo", "Module 10"),
    ]
    _tiles(core)

    section("Advanced Intelligence", "New")
    adv = [
        ("🔮", "Demand Forecast", "30–90 day ML forecast with stock-out countdown", "violet", "AI"),
        ("🚨", "Anomaly Detection", "Isolation-Forest scan for unusual production", "rose", "AI"),
        ("🎛️", "What-If Simulator", "Test price, tariff & efficiency changes on profit", "amber", "Planning"),
        ("🔧", "Machine Health", "Health score & predictive maintenance", "teal", "Maintenance"),
        ("🔔", "Smart Alerts", "One prioritised list of everything that needs action", "orange", "Ops"),
        ("🛡️", "Admin Panel", "Users, data upload, model retraining, audit log", "slate", "Admin"),
    ]
    _tiles(adv)
    st.info("👈 Open any module from the sidebar.")
    footer()


def _tiles(items, per_row=4):
    for i in range(0, len(items), per_row):
        cols = st.columns(per_row)
        for c, (icon, title, desc, color, tag) in zip(cols, items[i:i + per_row]):
            with c:
                tile(icon, title, desc, color, tag)
        st.write("")


if __name__ == "__main__":
    if not is_logged_in():
        login_screen()
    else:
        main_landing()
