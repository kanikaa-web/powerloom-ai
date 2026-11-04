"""
data.py
-------
Shared, cached data access for all pages + activity (audit) logging.
The cache key includes the dataset file's modified time, so when an Admin
uploads new data the whole app refreshes automatically.
"""

import os
import logging
import pandas as pd
import streamlit as st

from database.db import fetch_all, execute

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "dataset", "powerloom_production_data.csv")

MATERIAL_COLUMNS = {
    "Cotton": "Cotton_Used",
    "Yarn": "Yarn_Used",
    "Polyester": "Polyester_Used",
    "Dye": "Dye_Used",
    "Chemical": "Chemical_Used",
    "Packing Material": "Packing_Material",
}
COST_COLUMNS = ["Raw_Material_Cost", "Production_Cost", "Electricity_Cost", "Labour_Cost", "Transport_Cost"]


def _mtime(path):
    try:
        return os.path.getmtime(path)
    except OSError:
        return 0


@st.cache_data(show_spinner=False)
def _load(path, mtime):
    df = pd.read_csv(path, parse_dates=["Date"])
    df = df.sort_values("Date").reset_index(drop=True)
    df["Year"] = df["Date"].dt.year
    df["Total_Cost"] = df[COST_COLUMNS].sum(axis=1)
    df["Revenue"] = df["Profit"] + df["Total_Cost"]
    df["Target_Achievement"] = (df["Actual_Production"] / df["Production_Target"].replace(0, pd.NA) * 100).astype(float)
    return df


def load_dataset() -> pd.DataFrame:
    return _load(DATA_PATH, _mtime(DATA_PATH)).copy()


def daily_series(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate the order-level dataset to one row per calendar day."""
    agg = {c: "sum" for c in ["Actual_Production", "Production_Target", *MATERIAL_COLUMNS.values(),
                              *COST_COLUMNS, "Profit", "Revenue"]}
    agg["Machine_Efficiency"] = "mean"
    agg["Waste_Percentage"] = "mean"
    daily = df.groupby(df["Date"].dt.normalize()).agg(agg)
    daily["Orders"] = df.groupby(df["Date"].dt.normalize())["Order_ID"].count()
    daily = daily.asfreq("D")
    sums = [c for c, how in agg.items() if how == "sum"] + ["Orders"]
    daily[sums] = daily[sums].fillna(0)
    daily[["Machine_Efficiency", "Waste_Percentage"]] = daily[["Machine_Efficiency", "Waste_Percentage"]].ffill()
    daily.index.name = "Date"
    return daily


def stock_table() -> pd.DataFrame:
    return pd.DataFrame(fetch_all("SELECT * FROM stock"))


def orders_table() -> pd.DataFrame:
    return pd.DataFrame(fetch_all("SELECT * FROM orders ORDER BY created_at DESC"))


def clear_caches():
    st.cache_data.clear()


# ------------------------------------------------------------------ activity log
def log_activity(action: str, details: str = "", user: str = None):
    try:
        execute("INSERT INTO activity_log (username, action, details) VALUES (?,?,?)",
                (user or st.session_state.get("username", "system"), action, details[:500]))
    except Exception as e:  # logging must never break a page
        logger.warning(f"Activity log failed: {e}")
