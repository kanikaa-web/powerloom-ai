"""
Advanced — Admin Panel (Admin role only).
User management, production-data upload with validation, one-click ML model
retraining, activity/audit log and database backup.
"""

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import shutil
import platform
from datetime import datetime
import pandas as pd
import plotly.express as px
import streamlit as st

from utils.ui import setup_page, kpi_row, section, chart, footer
from utils.auth import hash_password
from utils.data import DATA_PATH, load_dataset, clear_caches, log_activity
from database.db import fetch_all, fetch_one, execute, DB_PATH

setup_page("Admin Panel", "🛡️", "Users, data, model retraining, audit log and backups", "Advanced · Admin",
           roles=["Admin"])

users = pd.DataFrame(fetch_all("SELECT id, username, role, full_name, email, created_at FROM users"))
acts = pd.DataFrame(fetch_all("SELECT * FROM activity_log ORDER BY timestamp DESC LIMIT 2000"))
df = load_dataset()

kpi_row([
    dict(label="Users", value=len(users), icon="👥", color="indigo"),
    dict(label="Dataset records", value=f"{len(df):,}", icon="🗂️", color="teal",
         sub=f"{df['Date'].min():%b %Y} → {df['Date'].max():%b %Y}"),
    dict(label="Activity events", value=len(acts), icon="📝", color="amber"),
    dict(label="Database size", value=f"{os.path.getsize(DB_PATH)/1024:,.0f} KB", icon="💾", color="violet"),
])
st.write("")

tab_u, tab_d, tab_m, tab_a, tab_s = st.tabs(["👥 Users", "📤 Data Upload", "🤖 ML Models", "📝 Activity Log", "💾 Backup & System"])

# ---------------- Users ----------------
with tab_u:
    st.dataframe(users, use_container_width=True, hide_index=True)
    c1, c2 = st.columns(2)
    with c1, st.form("add_user", clear_on_submit=True):
        st.markdown("**➕ Add user**")
        u = st.text_input("Username")
        n = st.text_input("Full name")
        e = st.text_input("Email")
        r = st.selectbox("Role", ["Employee", "Manager", "Admin"])
        p = st.text_input("Password", type="password")
        if st.form_submit_button("Create user", use_container_width=True):
            if not u or len(p) < 6:
                st.error("Username required and password must be at least 6 characters.")
            elif fetch_one("SELECT id FROM users WHERE username = ?", (u,)):
                st.error("Username already exists.")
            else:
                execute("INSERT INTO users (username, password_hash, role, full_name, email) VALUES (?,?,?,?,?)",
                        (u, hash_password(p), r, n, e))
                log_activity("User created", f"{u} ({r})")
                st.success(f"User {u} created.")
                st.rerun()
    with c2, st.form("edit_user"):
        st.markdown("**✏️ Change role / reset password / delete**")
        target = st.selectbox("User", users["username"].tolist())
        new_role = st.selectbox("New role", ["(no change)", "Employee", "Manager", "Admin"])
        new_pw = st.text_input("New password (optional)", type="password")
        delete = st.checkbox("Delete this user")
        if st.form_submit_button("Apply", use_container_width=True):
            me = st.session_state.get("username")
            if delete:
                if target == me:
                    st.error("You cannot delete your own account.")
                else:
                    execute("DELETE FROM users WHERE username = ?", (target,))
                    log_activity("User deleted", target)
                    st.success(f"{target} deleted.")
                    st.rerun()
            else:
                if new_role != "(no change)":
                    if target == me and new_role != "Admin":
                        st.error("You cannot remove your own Admin role.")
                        st.stop()
                    execute("UPDATE users SET role = ? WHERE username = ?", (new_role, target))
                    log_activity("Role changed", f"{target} → {new_role}")
                if new_pw:
                    if len(new_pw) < 6:
                        st.error("Password must be at least 6 characters.")
                        st.stop()
                    execute("UPDATE users SET password_hash = ? WHERE username = ?", (hash_password(new_pw), target))
                    log_activity("Password reset by admin", target)
                st.success("Changes applied.")
                st.rerun()
    fig = px.pie(users, names="role", hole=0.55, title="Users by role")
    chart(fig, height=280)

# ---------------- Data upload ----------------
with tab_d:
    required = list(pd.read_csv(DATA_PATH, nrows=0).columns)
    st.markdown(f"Upload new production records as **CSV** with the same **{len(required)} columns** as the current dataset.")
    with st.expander("Required columns"):
        st.code(", ".join(required))
    st.download_button("⬇️ Download CSV template", pd.DataFrame(columns=required).to_csv(index=False).encode(),
                       "barkavi_production_template.csv", "text/csv")
    up = st.file_uploader("Upload CSV", type=["csv"])
    if up is not None:
        try:
            new = pd.read_csv(up)
        except Exception as ex:
            st.error(f"Could not read file: {ex}")
            st.stop()
        missing = [c for c in required if c not in new.columns]
        if missing:
            st.error(f"Missing columns: {', '.join(missing)}")
        else:
            new = new[required]
            bad_dates = pd.to_datetime(new["Date"], errors="coerce").isna().sum()
            st.success(f"✅ {len(new):,} rows, all required columns present. Invalid dates: {bad_dates}.")
            st.dataframe(new.head(20), use_container_width=True, hide_index=True)
            mode = st.radio("Import mode", ["Append to existing data", "Replace existing data"], horizontal=True)
            retrain = st.checkbox("Retrain ML models after import", value=True)
            if st.button("🚀 Import data", use_container_width=True):
                backup = DATA_PATH.replace(".csv", f"_backup_{datetime.now():%Y%m%d_%H%M%S}.csv")
                shutil.copy(DATA_PATH, backup)
                old = pd.read_csv(DATA_PATH)
                out = pd.concat([old, new], ignore_index=True).drop_duplicates(subset=["Order_ID"], keep="last") \
                    if mode.startswith("Append") else new
                out.to_csv(DATA_PATH, index=False)
                clear_caches()
                log_activity("Dataset imported", f"{mode}: {len(new)} rows (backup {os.path.basename(backup)})")
                st.success(f"Dataset now has {len(out):,} rows. Backup saved as {os.path.basename(backup)}.")
                if retrain:
                    with st.spinner("Retraining models..."):
                        from models.train_material_prediction import main as train_main
                        train_main()
                    log_activity("Models retrained", "after data import")
                    st.success("Models retrained on the new data.")

# ---------------- Models ----------------
with tab_m:
    from models.train_material_prediction import SAVE_DIR
    rows = []
    for f in sorted(os.listdir(SAVE_DIR)):
        if f.endswith("_model_comparison.csv"):
            comp = pd.read_csv(os.path.join(SAVE_DIR, f))
            target = f.replace("_model_comparison.csv", "")
            sort_col = "RMSE" if "RMSE" in comp.columns else comp.columns[-1]
            best = comp.sort_values(sort_col).iloc[0].to_dict()
            best["Target"] = target
            rows.append(best)
    if rows:
        mt = pd.DataFrame(rows)
        mt = mt[["Target"] + [c for c in mt.columns if c != "Target"]]
        st.markdown("**Best model per material** (from the last training run)")
        st.dataframe(mt, use_container_width=True, hide_index=True)
        if "Accuracy_%" in mt.columns:
            fig = px.bar(mt, x="Target", y="Accuracy_%", color="Model" if "Model" in mt.columns else None,
                         title="Best-model accuracy by material", text_auto=".1f")
            chart(fig, height=330)
        mtime = max(os.path.getmtime(os.path.join(SAVE_DIR, f)) for f in os.listdir(SAVE_DIR))
        st.caption(f"Last trained: {datetime.fromtimestamp(mtime):%d %b %Y %H:%M}")
    if st.button("🔁 Retrain all models now", use_container_width=True):
        with st.spinner("Training 5 algorithms × 6 materials... (about a minute)"):
            from models.train_material_prediction import main as train_main
            train_main()
        clear_caches()
        log_activity("Models retrained", "manual")
        st.success("Retraining complete.")
        st.rerun()

# ---------------- Activity ----------------
with tab_a:
    if acts.empty:
        st.info("No activity recorded yet.")
    else:
        acts["timestamp"] = pd.to_datetime(acts["timestamp"])
        f1, f2 = st.columns(2)
        fu = f1.multiselect("User", sorted(acts["username"].dropna().unique()))
        fa = f2.multiselect("Action", sorted(acts["action"].dropna().unique()))
        v = acts
        if fu:
            v = v[v["username"].isin(fu)]
        if fa:
            v = v[v["action"].isin(fa)]
        c1, c2 = st.columns([1.6, 1])
        c1.dataframe(v.drop(columns=["id"]), use_container_width=True, hide_index=True, height=380)
        with c2:
            fig = px.bar(v.groupby("action").size().reset_index(name="Events").sort_values("Events"),
                         x="Events", y="action", orientation="h", title="Events by action")
            fig.update_layout(yaxis_title="")
            chart(fig, height=380)
        st.download_button("⬇️ Export audit log", v.to_csv(index=False).encode(), "barkavi_audit_log.csv", "text/csv")

# ---------------- Backup ----------------
with tab_s:
    with open(DB_PATH, "rb") as fh:
        st.download_button("💾 Download database backup (.db)", fh.read(),
                           f"barkavi_powerloom_{datetime.now():%Y%m%d}.db", use_container_width=True,
                           on_click=lambda: log_activity("Database backup downloaded"))
    with open(DATA_PATH, "rb") as fh:
        st.download_button("🗂️ Download production dataset (.csv)", fh.read(), "barkavi_production_data.csv",
                           use_container_width=True)
    import sklearn, numpy
    info = {"Python": platform.python_version(), "Streamlit": st.__version__, "pandas": pd.__version__,
            "numpy": numpy.__version__, "scikit-learn": sklearn.__version__, "OS": platform.platform()}
    counts = {t: fetch_one(f"SELECT COUNT(*) AS c FROM {t}")["c"] for t in
              ["users", "stock", "stock_history", "suppliers", "orders", "activity_log", "maintenance_log"]}
    c1, c2 = st.columns(2)
    c1.markdown("**System**")
    c1.dataframe(pd.DataFrame(info.items(), columns=["Component", "Version"]), hide_index=True, use_container_width=True)
    c2.markdown("**Database tables**")
    c2.dataframe(pd.DataFrame(counts.items(), columns=["Table", "Rows"]), hide_index=True, use_container_width=True)
footer()
