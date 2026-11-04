"""
supplier_recommender.py
-------------------------
Scores and ranks suppliers using a weighted multi-criteria formula
based on price, quality, delivery time, rating, and availability.
"""

import logging
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WEIGHTS = {"price": 0.25, "quality": 0.30, "delivery": 0.20, "rating": 0.20, "availability": 0.05}


def _normalize(series, lower_is_better=False):
    if series.max() == series.min():
        return series.apply(lambda x: 1.0)
    norm = (series - series.min()) / (series.max() - series.min())
    return 1 - norm if lower_is_better else norm


def recommend_suppliers(material_name: str = None, top_n: int = 5):
    """
    Fetch suppliers (optionally filtered by material) from the DB,
    score them, and return the top N ranked recommendations.
    """
    from database.db import fetch_all

    query = "SELECT * FROM suppliers"
    params = ()
    if material_name:
        query += " WHERE material_supplied = ?"
        params = (material_name,)

    rows = fetch_all(query, params)
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df["availability_score"] = df["availability"].map({"Available": 1.0, "Limited": 0.5, "Unavailable": 0.0}).fillna(0.5)

    df["price_score"] = _normalize(df["price_per_unit"], lower_is_better=True)
    df["quality_score"] = _normalize(df["quality_rating"])
    df["delivery_score"] = _normalize(df["avg_delivery_days"], lower_is_better=True)
    df["rating_score"] = _normalize(df["rating"])

    df["final_score"] = (
        df["price_score"] * WEIGHTS["price"] +
        df["quality_score"] * WEIGHTS["quality"] +
        df["delivery_score"] * WEIGHTS["delivery"] +
        df["rating_score"] * WEIGHTS["rating"] +
        df["availability_score"] * WEIGHTS["availability"]
    ) * 100

    df["final_score"] = df["final_score"].round(2)
    result = df.sort_values("final_score", ascending=False).head(top_n)
    return result[["name", "material_supplied", "price_per_unit", "quality_rating",
                   "avg_delivery_days", "rating", "availability", "final_score"]]
