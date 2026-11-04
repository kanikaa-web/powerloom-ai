"""
anomaly.py
----------
Production anomaly detection with Isolation Forest.
Each flagged record also gets a plain-English reason: the features that
deviate most (largest |z-score|) from normal behaviour.
"""

import numpy as np
import pandas as pd
import streamlit as st
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

FEATURES = {
    "Machine_Efficiency": "machine efficiency",
    "Waste_Percentage": "waste %",
    "Shortfall_Pct": "shortfall vs target",
    "Cost_Per_Unit": "raw-material cost per unit",
    "Delivery_Days": "delivery days",
}


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["Shortfall_Pct"] = (out["Production_Target"] - out["Actual_Production"]) / out["Production_Target"] * 100
    out["Cost_Per_Unit"] = out["Raw_Material_Cost"] / out["Actual_Production"].replace(0, np.nan)
    return out


@st.cache_data(show_spinner=False)
def detect_anomalies(df: pd.DataFrame, contamination: float = 0.03) -> pd.DataFrame:
    data = add_features(df).dropna(subset=list(FEATURES))
    X = data[list(FEATURES)].values
    scaler = StandardScaler().fit(X)
    Z = scaler.transform(X)

    model = IsolationForest(n_estimators=300, contamination=contamination, random_state=42)
    model.fit(Z)
    data["Anomaly_Score"] = -model.score_samples(Z)            # higher = more unusual
    data["Is_Anomaly"] = model.predict(Z) == -1

    reasons = []
    for row in Z:
        top = np.argsort(-np.abs(row))[:2]
        parts = []
        for i in top:
            name = list(FEATURES.values())[i]
            parts.append(f"{'very high' if row[i] > 0 else 'very low'} {name} ({row[i]:+.1f}σ)")
        reasons.append("; ".join(parts))
    data["Reason"] = reasons

    s = data["Anomaly_Score"]
    data["Severity"] = pd.cut(s.rank(pct=True), bins=[0, 0.97, 0.99, 0.997, 1.0],
                              labels=["Low", "Medium", "High", "Critical"], include_lowest=True).astype(str)
    data.loc[~data["Is_Anomaly"], "Severity"] = "Normal"
    return data
