"""
Dashboard page — colourful executive overview: filters, KPI cards with
period-over-period change, gauges, stock levels, trends, mix and alerts.
"""

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.ui import (setup_page, money, kpi_row, section, chart, gauge, progress_bar, alert_card,
                      footer, PALETTE, GOLD_SCALE)
from utils.data import load_dataset, stock_table, orders_table, MATERIAL_COLUMNS
from utils.alerts import build_alerts

setup_page("Production Dashboard", "📊", "Live overview of production, efficiency, stock, cost and profit")

df_all = load_dataset()
min_d, max_d = df_all["Date"].min().date(), df_all["Date"].max().date()

# ---------------- Filters ----------------
with st.expander("🎚️ Filters", expanded=False):
    f1, f2, f3 = st.columns([1.4, 1, 1])
    default_start = max(min_d, (pd.Timestamp(max_d) - pd.DateOffset(months=12)).date())
    date_range = f1.date_input("Date range", (default_start, max_d), min_value=min_d, max_value=max_d)
    fabrics = f2.multiselect("Fabric type", sorted(df_all["Fabric_Type"].unique()))
    machines = f3.multiselect("Machine type", sorted(df_all["Machine_Type"].unique()))

if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
else:
    start, end = pd.Timestamp(default_start), pd.Timestamp(max_d)

base = df_all.copy()
if fabrics:
    base = base[base["Fabric_Type"].isin(fabrics)]
if machines:
    base = base[base["Machine_Type"].isin(machines)]

df = base[(base["Date"] >= start) & (base["Date"] <= end)]
span = end - start
prev = base[(base["Date"] >= start - span - pd.Timedelta(days=1)) & (base["Date"] < start)]

if df.empty:
    st.warning("No records for the selected filters.")
    st.stop()

st.caption(f"Showing **{start:%d %b %Y} → {end:%d %b %Y}** · {len(df):,} orders · "
           f"compared with the previous {span.days + 1} days")


def pct(cur, old):
    return None if not old else (cur - old) / abs(old) * 100


prod, prod_p = df["Actual_Production"].sum(), prev["Actual_Production"].sum()
ach = prod / df["Production_Target"].sum() * 100
ach_p = prod_p / prev["Production_Target"].sum() * 100 if len(prev) else None
eff, eff_p = df["Machine_Efficiency"].mean(), prev["Machine_Efficiency"].mean() if len(prev) else None
waste, waste_p = df["Waste_Percentage"].mean(), prev["Waste_Percentage"].mean() if len(prev) else None
cost, cost_p = df["Total_Cost"].sum(), prev["Total_Cost"].sum()
profit, profit_p = df["Profit"].sum(), prev["Profit"].sum()
orders_n, orders_p = df["Order_ID"].nunique(), prev["Order_ID"].nunique()

stock = stock_table()
low = int((stock["current_stock"] <= stock["reorder_level"]).sum()) if not stock.empty else 0
orders_db = orders_table()
pending = int((orders_db["status"].fillna("Pending") == "Pending").sum()) if not orders_db.empty else 0

kpi_row([
    dict(label="Total Production", value=f"{prod:,.0f}", icon="🏭", color="indigo", delta=pct(prod, prod_p), sub="units"),
    dict(label="Target Achievement", value=f"{ach:.1f}%", icon="🎯", color="violet",
         delta=None if ach_p is None else ach - ach_p, sub="actual vs target (Δ in pts)"),
    dict(label="Machine Efficiency", value=f"{eff:.1f}%", icon="⚙️", color="teal",
         delta=None if eff_p is None else eff - eff_p, sub="average (Δ in pts)"),
    dict(label="Avg Waste", value=f"{waste:.2f}%", icon="♻️", color="amber",
         delta=None if waste_p is None else waste - waste_p, delta_good_when_up=False, sub="lower is better"),
])
st.write("")
kpi_row([
    dict(label="Orders", value=f"{orders_n:,}", icon="🧾", color="sky", delta=pct(orders_n, orders_p),
         sub=f"{pending} pending in order book"),
    dict(label="Total Cost", value=money(cost), icon="💸", color="orange", delta=pct(cost, cost_p),
         delta_good_when_up=False, sub="material + production + power + labour + transport"),
    dict(label="Net Profit", value=money(profit), icon="💰", color="emerald" if profit >= 0 else "rose",
         delta=pct(profit, profit_p), sub="as recorded in dataset"),
    dict(label="Low-stock Items", value=low, icon="📦", color="rose" if low else "emerald",
         sub=f"of {len(stock)} materials at/below reorder"),
])

# ---------------- Alerts strip ----------------
section("Needs attention", "top alerts right now")
alerts = build_alerts()
for a in alerts[:3]:
    alert_card(a["title"], a["body"], a["severity"], f"{a['category']} · {a['action']}")
if len(alerts) > 3:
    st.caption(f"+ {len(alerts) - 3} more on the 🔔 Smart Alerts page")

# ---------------- Production trend + gauges ----------------
section("Production performance")
c1, c2 = st.columns([2.2, 1])
with c1, st.container(border=True):
    m = df.groupby(df["Date"].dt.to_period("M")).agg(
        Actual=("Actual_Production", "sum"), Target=("Production_Target", "sum"),
        Efficiency=("Machine_Efficiency", "mean")).reset_index()
    m["Date"] = m["Date"].dt.to_timestamp()
    fig = go.Figure()
    fig.add_bar(x=m["Date"], y=m["Target"], name="Target", marker_color="rgba(176,122,30,0.28)")
    fig.add_bar(x=m["Date"], y=m["Actual"], name="Actual",
                marker=dict(color=m["Actual"], colorscale=[[0, "#A5B4FC"], [1, "#4F46E5"]]))
    fig.add_scatter(x=m["Date"], y=m["Efficiency"], name="Efficiency %", yaxis="y2", mode="lines+markers",
                    line=dict(color="#F43F5E", width=3, shape="spline"), marker=dict(size=7))
    fig.update_layout(title="Monthly production vs target", barmode="overlay", bargap=0.25,
                      yaxis=dict(title="Units"),
                      yaxis2=dict(title="Efficiency %", overlaying="y", side="right", showgrid=False))
    chart(fig, height=380)
with c2, st.container(border=True):
    chart(gauge(round(ach, 1), "Target achievement", max_value=120,
                bands=[(0, .625, "#FEE2E2"), (.625, .75, "#FEF3C7"), (.75, 1, "#DCFCE7")], color="#7C3AED"),
          height=190)
    chart(gauge(round(eff, 1), "Machine efficiency", color="#0D9488",
                bands=[(0, .75, "#FEE2E2"), (.75, .85, "#FEF3C7"), (.85, 1, "#DCFCE7")]), height=190)

# ---------------- Stock + material mix ----------------
section("Inventory & materials")
c3, c4 = st.columns([1, 1.3])
with c3, st.container(border=True):
    st.markdown("**📦 Live stock levels** · bar = stock vs 3× reorder level")
    for _, r in stock.iterrows():
        cap = max(r["reorder_level"] * 3, r["current_stock"])
        status = "🔴" if r["current_stock"] <= r["safety_stock"] else ("🟠" if r["current_stock"] <= r["reorder_level"] else "🟢")
        progress_bar(f"{status} {r['material_name']}", r["current_stock"], cap,
                     f"{r['current_stock']:,.0f} {r['unit']} · reorder {r['reorder_level']:,.0f}")
with c4, st.container(border=True):
    cons = pd.DataFrame({"Material": list(MATERIAL_COLUMNS),
                         "Used": [df[c].sum() for c in MATERIAL_COLUMNS.values()]})
    fig = px.pie(cons, names="Material", values="Used", hole=0.58, title="Material consumption mix")
    fig.update_traces(textposition="outside", textinfo="percent+label",
                      marker=dict(line=dict(color="#FBF8F2", width=3)))
    fig.update_layout(showlegend=False, annotations=[dict(text=f"<b>{cons['Used'].sum()/1000:,.0f} t</b><br>total",
                                                          showarrow=False, font_size=16)])
    chart(fig, height=380)

# ---------------- Mix: fabric / machine ----------------
section("Product & machine mix")
c5, c6 = st.columns(2)
with c5, st.container(border=True):
    tree = df.groupby(["Fabric_Type", "Machine_Type"], as_index=False)["Actual_Production"].sum()
    fig = px.sunburst(tree, path=["Fabric_Type", "Machine_Type"], values="Actual_Production",
                      title="Production by fabric → machine", color="Fabric_Type")
    chart(fig, height=420)
with c6, st.container(border=True):
    mp = df.groupby("Machine_Type").agg(Efficiency=("Machine_Efficiency", "mean"),
                                        Waste=("Waste_Percentage", "mean"),
                                        Production=("Actual_Production", "sum")).reset_index()
    fig = px.scatter(mp, x="Efficiency", y="Waste", size="Production", color="Machine_Type",
                     size_max=60, text="Machine_Type", title="Machine efficiency vs waste (bubble = output)")
    fig.update_traces(textposition="top center")
    fig.update_layout(showlegend=False, xaxis_title="Avg efficiency %", yaxis_title="Avg waste %")
    chart(fig, height=420)

# ---------------- Finance + heatmap ----------------
section("Cost, profit & patterns")
c7, c8 = st.columns(2)
with c7, st.container(border=True):
    cm = df.groupby(df["Date"].dt.to_period("M"))[
        ["Raw_Material_Cost", "Labour_Cost", "Production_Cost", "Electricity_Cost", "Transport_Cost"]].sum()
    cm.index = cm.index.to_timestamp()
    cm.columns = ["Raw material", "Labour", "Production", "Electricity", "Transport"]
    fig = px.area(cm, x=cm.index, y=cm.columns, title="Monthly cost structure (₹)")
    fig.update_layout(xaxis_title="", yaxis_title="₹")
    chart(fig, height=380)
with c8, st.container(border=True):
    hm = df.assign(Weekday=df["Date"].dt.day_name().str[:3], Month=df["Date"].dt.month_name().str[:3])
    pivot = hm.pivot_table(index="Weekday", columns="Month", values="Actual_Production", aggfunc="mean")
    pivot = pivot.reindex(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]).dropna(how="all")
    months = [mn for mn in ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
              if mn in pivot.columns]
    fig = px.imshow(pivot[months], color_continuous_scale=GOLD_SCALE, aspect="auto",
                    title="Avg output per order: weekday × month", text_auto=".0f")
    chart(fig, height=380)

# ---------------- Top customers + suppliers ----------------
c9, c10 = st.columns(2)
with c9, st.container(border=True):
    top = df.groupby("Customer")["Actual_Production"].sum().nlargest(10).sort_values().reset_index()
    fig = px.bar(top, x="Actual_Production", y="Customer", orientation="h", title="Top 10 customers by volume",
                 color="Actual_Production", color_continuous_scale=["#C7D2FE", "#4F46E5"])
    fig.update_layout(coloraxis_showscale=False, yaxis_title="", xaxis_title="Units")
    chart(fig, height=400)
with c10, st.container(border=True):
    sp = df.groupby("Supplier").agg(Spend=("Raw_Material_Cost", "sum"), Delivery=("Delivery_Days", "mean")).reset_index()
    fig = px.bar(sp.sort_values("Spend"), x="Spend", y="Supplier", orientation="h", color="Delivery",
                 color_continuous_scale=["#10B981", "#FBBF24", "#F43F5E"],
                 title="Supplier spend (colour = avg delivery days)")
    fig.update_layout(yaxis_title="", xaxis_title="₹")
    chart(fig, height=400)

footer()
