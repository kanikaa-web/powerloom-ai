"""
machine_health.py
-----------------
Machine health scoring & predictive-maintenance signals per machine type.

The dataset records machine TYPE (Sulzer, Airjet, Rapier, Waterjet, Shuttle),
not individual loom IDs, so health is scored per machine type from:
  - recent efficiency level           (40%)
  - efficiency trend (slope)          (20%)
  - waste %                           (20%)
  - target achievement                (10%)
  - output stability (low variation)  (10%)
"""

import numpy as np
import pandas as pd


def _slope(y: pd.Series) -> float:
    if len(y) < 3:
        return 0.0
    x = np.arange(len(y))
    return float(np.polyfit(x, y.values, 1)[0])


def machine_health(df: pd.DataFrame, recent_days: int = 90) -> pd.DataFrame:
    end = df["Date"].max()
    recent = df[df["Date"] > end - pd.Timedelta(days=recent_days)]
    prior = df[(df["Date"] <= end - pd.Timedelta(days=recent_days)) &
               (df["Date"] > end - pd.Timedelta(days=2 * recent_days))]
    rows = []
    for mtype, g in recent.groupby("Machine_Type"):
        weekly = g.groupby(g["Date"].dt.to_period("W"))["Machine_Efficiency"].mean()
        p = prior[prior["Machine_Type"] == mtype]
        eff = g["Machine_Efficiency"].mean()
        eff_prev = p["Machine_Efficiency"].mean() if len(p) else eff
        waste = g["Waste_Percentage"].mean()
        achieve = (g["Actual_Production"].sum() / g["Production_Target"].sum()) * 100
        cv = g["Machine_Efficiency"].std() / eff * 100 if eff else 0
        slope = _slope(weekly)

        s_eff = np.clip((eff - 60) / (98 - 60), 0, 1)
        s_trend = np.clip(0.5 + slope / 1.0, 0, 1)
        s_waste = np.clip((12 - waste) / (12 - 2), 0, 1)
        s_ach = np.clip((achieve - 60) / (100 - 60), 0, 1)
        s_stab = np.clip((15 - cv) / 15, 0, 1)
        score = 100 * (0.4 * s_eff + 0.2 * s_trend + 0.2 * s_waste + 0.1 * s_ach + 0.1 * s_stab)

        status = "Healthy" if score >= 70 else ("Watch" if score >= 50 else "Critical")
        if status == "Critical":
            days = 3
        elif status == "Watch":
            days = 10
        else:
            days = 30
        rows.append({
            "Machine_Type": mtype, "Health_Score": round(float(score), 1), "Status": status,
            "Avg_Efficiency": round(eff, 1), "Efficiency_Change": round(eff - eff_prev, 2),
            "Weekly_Trend": round(slope, 3), "Avg_Waste_%": round(waste, 2),
            "Target_Achievement_%": round(achieve, 1), "Variability_%": round(cv, 1),
            "Orders": len(g), "Next_Service_In_Days": days,
            "Recommendation": _recommend(eff, slope, waste, achieve, cv),
        })
    return pd.DataFrame(rows).sort_values("Health_Score")


def _recommend(eff, slope, waste, achieve, cv):
    tips = []
    if eff < 80:
        tips.append("Efficiency below 80% — inspect heald frames, reed and warp tension.")
    if slope < -0.05:
        tips.append("Efficiency trending down week-on-week — schedule preventive maintenance.")
    if waste > 7:
        tips.append("High waste — check weft insertion settings and yarn quality.")
    if achieve < 85:
        tips.append("Missing production targets — review shift loading and breakdown logs.")
    if cv > 8:
        tips.append("Unstable output — standardise machine settings across shifts.")
    return " ".join(tips) or "Running well — continue routine lubrication and cleaning schedule."
