"""
generate_dataset.py
--------------------
Generates a realistic synthetic dataset for the Powerloom Industry
Raw Material Prediction & Production Planning System.

Run:
    python dataset/generate_dataset.py

Output:
    dataset/powerloom_production_data.csv  (5000+ rows)
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random

np.random.seed(42)
random.seed(42)

N_RECORDS = 5200

FABRIC_TYPES = ["Cotton", "Poly-Cotton", "Polyester", "Denim", "Terry", "Voile", "Canvas"]
MACHINE_TYPES = ["Sulzer", "Airjet", "Rapier", "Waterjet", "Shuttle"]
SUPPLIERS = ["ShreeTex Suppliers", "Om Sai Yarns", "Balaji Cotton Mills",
             "Vardhman Fibers", "Nandi Dye Chem", "SriKrishna Traders"]
SEASONS = ["Summer", "Monsoon", "Winter", "Spring"]
PRIORITIES = ["High", "Medium", "Low"]
CUSTOMERS = [f"Customer_{i}" for i in range(1, 121)]

def month_to_season(month):
    if month in [3, 4, 5]:
        return "Summer"
    elif month in [6, 7, 8, 9]:
        return "Monsoon"
    elif month in [10, 11]:
        return "Spring"
    else:
        return "Winter"

def working_days_in_month(year, month):
    # Approx: powerloom units run 6 days/week, ~1 holiday extra per month
    import calendar
    days_in_month = calendar.monthrange(year, month)[1]
    sundays = sum(1 for d in range(1, days_in_month + 1)
                  if datetime(year, month, d).weekday() == 6)
    return days_in_month - sundays - random.randint(0, 2)

rows = []
start_date = datetime(2021, 1, 1)

# running stock trackers (simulate real depletion/replenishment)
current_stock = {"Cotton": 5000, "Yarn": 4000, "Polyester": 3000,
                  "Dye": 800, "Chemical": 500, "Packing": 1200}
safety_stock = {"Cotton": 800, "Yarn": 600, "Polyester": 500,
                "Dye": 150, "Chemical": 100, "Packing": 200}
reorder_level = {k: v * 1.3 for k, v in safety_stock.items()}

for i in range(N_RECORDS):
    date = start_date + timedelta(days=int(i * (1460 / N_RECORDS)))  # spread over ~4 years
    year, month = date.year, date.month
    season = month_to_season(month)
    working_days = working_days_in_month(year, month)

    fabric_type = random.choice(FABRIC_TYPES)
    fabric_gsm = int(np.clip(np.random.normal(180, 40), 80, 400))
    fabric_width = round(random.choice([44, 58, 63, 72, 96]), 1)
    machine_type = random.choice(MACHINE_TYPES)
    machine_efficiency = round(np.clip(np.random.normal(85, 7), 55, 99), 1)

    # Seasonal demand multiplier
    season_mult = {"Summer": 1.15, "Monsoon": 0.9, "Winter": 1.05, "Spring": 1.0}[season]

    production_target = int(np.clip(np.random.normal(1200, 300) * season_mult, 300, 3000))
    actual_production = int(production_target * (machine_efficiency / 100) *
                             np.random.uniform(0.92, 1.02))

    # Material consumption depends on GSM, width, production qty
    base_factor = (fabric_gsm / 180) * (fabric_width / 60) * (actual_production / 1000)

    cotton_used = round(max(0, np.random.normal(350, 60) * base_factor *
                             (1.3 if "Cotton" in fabric_type else 0.4)), 2)
    yarn_used = round(max(0, np.random.normal(300, 50) * base_factor), 2)
    polyester_used = round(max(0, np.random.normal(150, 40) * base_factor *
                                (1.4 if "Poly" in fabric_type else 0.3)), 2)
    dye_used = round(max(0, np.random.normal(40, 10) * base_factor), 2)
    chemical_used = round(max(0, np.random.normal(20, 6) * base_factor), 2)
    packing_material = round(max(0, actual_production * np.random.uniform(0.08, 0.12)), 2)

    waste_percentage = round(np.clip(np.random.normal(6, 2) -
                                      (machine_efficiency - 85) * 0.05, 1, 15), 2)

    # Costs (INR)
    raw_material_cost = round(cotton_used * 165 + yarn_used * 210 +
                               polyester_used * 130 + dye_used * 320 +
                               chemical_used * 180, 2)
    production_cost = round(actual_production * np.random.uniform(8, 12), 2)
    electricity_cost = round(actual_production * np.random.uniform(2.5, 4.2), 2)
    labour_cost = round(working_days * np.random.uniform(900, 1400), 2)
    transport_cost = round(np.random.uniform(1500, 6000), 2)

    total_cost = raw_material_cost + production_cost + electricity_cost + labour_cost + transport_cost
    revenue = round(actual_production * np.random.uniform(28, 40), 2)
    profit = round(revenue - total_cost, 2)

    supplier = random.choice(SUPPLIERS)
    delivery_days = random.randint(2, 12)
    order_priority = random.choices(PRIORITIES, weights=[0.25, 0.5, 0.25])[0]

    # Update simulated stock
    consumption = {"Cotton": cotton_used, "Yarn": yarn_used, "Polyester": polyester_used,
                   "Dye": dye_used, "Chemical": chemical_used, "Packing": packing_material}
    for k in current_stock:
        current_stock[k] -= consumption[k]
        if current_stock[k] < reorder_level[k]:
            current_stock[k] += np.random.uniform(500, 1500)  # replenishment
        current_stock[k] = max(current_stock[k], 0)

    row = {
        "Date": date.strftime("%Y-%m-%d"),
        "Order_ID": f"ORD{10000 + i}",
        "Customer": random.choice(CUSTOMERS),
        "Fabric_Type": fabric_type,
        "Fabric_GSM": fabric_gsm,
        "Fabric_Width": fabric_width,
        "Machine_Type": machine_type,
        "Machine_Efficiency": machine_efficiency,
        "Production_Target": production_target,
        "Actual_Production": actual_production,
        "Cotton_Used": cotton_used,
        "Yarn_Used": yarn_used,
        "Polyester_Used": polyester_used,
        "Dye_Used": dye_used,
        "Chemical_Used": chemical_used,
        "Packing_Material": packing_material,
        "Raw_Material_Cost": raw_material_cost,
        "Production_Cost": production_cost,
        "Electricity_Cost": electricity_cost,
        "Labour_Cost": labour_cost,
        "Transport_Cost": transport_cost,
        "Profit": profit,
        "Waste_Percentage": waste_percentage,
        "Supplier": supplier,
        "Delivery_Days": delivery_days,
        "Order_Priority": order_priority,
        "Season": season,
        "Month": month,
        "Working_Days": working_days,
        "Current_Stock_Cotton": round(current_stock["Cotton"], 2),
        "Remaining_Stock_Cotton": round(current_stock["Cotton"] - cotton_used, 2),
        "Safety_Stock_Cotton": safety_stock["Cotton"],
        "Reorder_Level_Cotton": round(reorder_level["Cotton"], 2),
    }
    rows.append(row)

df = pd.DataFrame(rows)
df.to_csv("dataset/powerloom_production_data.csv", index=False)
print(f"Dataset generated: {len(df)} records -> dataset/powerloom_production_data.csv")
print(df.head())
