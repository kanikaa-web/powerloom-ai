"""
scenario.py
-----------
What-If profit simulator. Baseline = average month over the selected
history window (from the dataset). Each lever adjusts one driver and the
new monthly profit is recomputed so you can see the impact of every change.
"""

import pandas as pd

LEVERS = {
    "raw_price": "Raw material price",
    "electricity": "Electricity tariff",
    "labour": "Labour cost",
    "transport": "Transport cost",
    "efficiency": "Machine efficiency",
    "waste": "Waste reduction",
    "selling_price": "Selling price",
}


def monthly_baseline(df: pd.DataFrame, months: int = 12) -> dict:
    m = df.groupby(df["Date"].dt.to_period("M")).agg(
        production=("Actual_Production", "sum"),
        raw=("Raw_Material_Cost", "sum"),
        prod_cost=("Production_Cost", "sum"),
        electricity=("Electricity_Cost", "sum"),
        labour=("Labour_Cost", "sum"),
        transport=("Transport_Cost", "sum"),
        revenue=("Revenue", "sum"),
        waste_pct=("Waste_Percentage", "mean"),
        efficiency=("Machine_Efficiency", "mean"),
    ).tail(months)
    base = m.mean().to_dict()
    base["price_per_unit"] = base["revenue"] / base["production"] if base["production"] else 0
    base["months"] = len(m)
    return base


def simulate(base: dict, raw_price=0.0, electricity=0.0, labour=0.0, transport=0.0,
             efficiency=0.0, waste=0.0, selling_price=0.0) -> dict:
    """
    All inputs are % changes except:
      efficiency -> change in efficiency points (e.g. +3 = 3 percentage points)
      waste      -> waste reduction in percentage points (e.g. 1 = waste 6% -> 5%)
    """
    prod_factor = 1 + efficiency / max(base["efficiency"], 1)
    production = base["production"] * prod_factor

    # material needed scales with output; waste reduction saves material
    # material bought = good fabric / (1 - waste); lower waste => less material for same output
    new_waste = min(max(base["waste_pct"] - waste, 0.0), 50.0)
    waste_factor = (1 - base["waste_pct"] / 100) / (1 - new_waste / 100)
    raw = base["raw"] * prod_factor * (1 + raw_price / 100) * waste_factor
    prod_cost = base["prod_cost"] * prod_factor
    elec = base["electricity"] * prod_factor * (1 + electricity / 100)
    lab = base["labour"] * (1 + labour / 100)                  # labour ~ fixed per month
    trans = base["transport"] * prod_factor * (1 + transport / 100)
    price = base["price_per_unit"] * (1 + selling_price / 100)
    revenue = production * price
    total_cost = raw + prod_cost + elec + lab + trans
    profit = revenue - total_cost
    breakeven_price = total_cost / production if production else 0
    return {"production": production, "revenue": revenue, "raw": raw, "prod_cost": prod_cost,
            "electricity": elec, "labour": lab, "transport": trans, "total_cost": total_cost,
            "profit": profit, "margin_pct": (profit / revenue * 100) if revenue else 0,
            "price_per_unit": price, "breakeven_price": breakeven_price}


def sensitivity(base: dict, step: float = 10.0) -> pd.DataFrame:
    """Profit impact of moving each lever by ±step (% or points)."""
    ref = simulate(base)["profit"]
    rows = []
    spec = {"raw_price": step, "electricity": step, "labour": step, "transport": step,
            "efficiency": step / 2, "waste": 1.0, "selling_price": step}
    for key, mv in spec.items():
        up = simulate(base, **{key: mv})["profit"] - ref
        down = simulate(base, **{key: -mv if key != "waste" else -1.0})["profit"] - ref
        rows.append({"Lever": LEVERS[key], "Increase": up, "Decrease": down,
                     "Range": abs(up - down)})
    return pd.DataFrame(rows).sort_values("Range")
