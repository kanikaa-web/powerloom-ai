"""
alerts.py
---------
Smart Alerts engine — scans live stock, orders, machine health, anomalies
and production KPIs and returns a prioritised list of actionable alerts.
"""

from datetime import date
import pandas as pd

from utils.data import load_dataset, daily_series, stock_table, orders_table, MATERIAL_COLUMNS
from utils.machine_health import machine_health
from utils.anomaly import detect_anomalies

ORDER = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3, "Info": 4}


def build_alerts(cover_days_threshold: int = 7, waste_threshold: float = 7.0) -> list:
    alerts = []
    df = load_dataset()
    daily = daily_series(df)
    last28 = daily.tail(28)

    # ---------- Inventory ----------
    stock = stock_table()
    for _, r in stock.iterrows():
        name, cur = r["material_name"], float(r["current_stock"])
        col = MATERIAL_COLUMNS.get(name)
        use = float(last28[col].mean()) if col in last28 else 0
        cover = cur / use if use > 0 else None
        if cur <= r["safety_stock"]:
            alerts.append(dict(category="Inventory", severity="Critical",
                               title=f"{name} below safety stock",
                               body=f"Only {cur:,.0f} {r['unit']} left (safety stock {r['safety_stock']:,.0f}). Reorder immediately.",
                               action="Raise purchase order now"))
        elif cur <= r["reorder_level"]:
            alerts.append(dict(category="Inventory", severity="High",
                               title=f"{name} at reorder level",
                               body=f"{cur:,.0f} {r['unit']} in stock vs reorder level {r['reorder_level']:,.0f}.",
                               action="Place reorder with top-ranked supplier"))
        if cover is not None and cover < cover_days_threshold:
            alerts.append(dict(category="Inventory", severity="High" if cover < 3 else "Medium",
                               title=f"{name}: {cover:.1f} days of cover",
                               body=f"At the recent usage of {use:,.0f} {r['unit']}/day (last 28 days), stock runs out in about {cover:.1f} days.",
                               action="Check Demand Forecast page for exact stock-out date"))

    # ---------- Machines ----------
    mh = machine_health(df)
    for _, r in mh.iterrows():
        if r["Status"] != "Healthy":
            alerts.append(dict(category="Machines", severity="Critical" if r["Status"] == "Critical" else "Medium",
                               title=f"{r['Machine_Type']} looms — health {r['Health_Score']}/100 ({r['Status']})",
                               body=r["Recommendation"],
                               action=f"Service within {r['Next_Service_In_Days']} days"))

    # ---------- Anomalies (last 30 days of data) ----------
    an = detect_anomalies(df)
    recent = an[(an["Is_Anomaly"]) & (an["Date"] > an["Date"].max() - pd.Timedelta(days=30))]
    if len(recent):
        worst = recent.sort_values("Anomaly_Score", ascending=False).iloc[0]
        sev = "High" if (recent["Severity"].isin(["High", "Critical"])).any() else "Medium"
        alerts.append(dict(category="Quality", severity=sev,
                           title=f"{len(recent)} unusual production records in the last 30 days",
                           body=f"Most unusual: {worst['Order_ID']} ({worst['Machine_Type']}, {worst['Date']:%d %b %Y}) — {worst['Reason']}.",
                           action="Review on Anomaly Detection page"))

    # ---------- Production KPIs ----------
    last30 = df[df["Date"] > df["Date"].max() - pd.Timedelta(days=30)]
    waste = last30["Waste_Percentage"].mean()
    if waste > waste_threshold:
        alerts.append(dict(category="Production", severity="Medium",
                           title=f"Average waste {waste:.1f}% (last 30 days)",
                           body=f"Above the {waste_threshold:.0f}% threshold. Check wastage drivers by machine type.",
                           action="Open Wastage Prediction"))
    ach = last30["Actual_Production"].sum() / last30["Production_Target"].sum() * 100
    if ach < 85:
        alerts.append(dict(category="Production", severity="High" if ach < 75 else "Medium",
                           title=f"Target achievement {ach:.1f}% (last 30 days)",
                           body="Actual production is well below plan. Consider extra shifts or rebalancing looms.",
                           action="Open Production Planning"))
    neg = (last30["Profit"] < 0).mean() * 100
    if neg > 50:
        alerts.append(dict(category="Finance", severity="High",
                           title=f"{neg:.0f}% of recent orders show a loss",
                           body="Recorded costs exceed recorded revenue for most recent orders. Review pricing in the What-If Simulator.",
                           action="Open What-If Simulator"))

    # ---------- Orders ----------
    orders = orders_table()
    if not orders.empty:
        orders["delivery_date"] = pd.to_datetime(orders["delivery_date"], errors="coerce")
        open_orders = orders[orders["status"].fillna("Pending") != "Completed"]
        today = pd.Timestamp(date.today())
        overdue = open_orders[open_orders["delivery_date"] < today]
        due_soon = open_orders[(open_orders["delivery_date"] >= today) &
                               (open_orders["delivery_date"] <= today + pd.Timedelta(days=3))]
        if len(overdue):
            alerts.append(dict(category="Orders", severity="Critical",
                               title=f"{len(overdue)} order(s) overdue",
                               body="Overdue: " + ", ".join(overdue["order_id"].astype(str).head(5)),
                               action="Update status / expedite dispatch"))
        if len(due_soon):
            alerts.append(dict(category="Orders", severity="High",
                               title=f"{len(due_soon)} order(s) due within 3 days",
                               body="Due soon: " + ", ".join(due_soon["order_id"].astype(str).head(5)),
                               action="Prioritise on looms"))

    if not alerts:
        alerts.append(dict(category="System", severity="Info", title="All clear",
                           body="No issues detected across inventory, machines, quality, production and orders.",
                           action=""))
    return sorted(alerts, key=lambda a: ORDER.get(a["severity"], 9))
