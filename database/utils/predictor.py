"""
predictor.py
------------
Loads trained models/encoders/scaler and runs raw material predictions.
"""

import os
import joblib
import logging
import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SAVE_DIR = os.path.join(os.path.dirname(__file__), "..", "saved_models")

TARGETS = ["Cotton_Used", "Yarn_Used", "Polyester_Used",
           "Dye_Used", "Chemical_Used", "Packing_Material"]

MATERIAL_UNIT_COST = {
    "Cotton_Used": 165, "Yarn_Used": 210, "Polyester_Used": 130,
    "Dye_Used": 320, "Chemical_Used": 180, "Packing_Material": 15
}


def _load_artifacts():
    try:
        encoders = joblib.load(os.path.join(SAVE_DIR, "encoders.pkl"))
        scaler = joblib.load(os.path.join(SAVE_DIR, "scaler.pkl"))
        feature_cols = joblib.load(os.path.join(SAVE_DIR, "feature_cols.pkl"))
        models = {t: joblib.load(os.path.join(SAVE_DIR, f"{t}_best_model.pkl")) for t in TARGETS}
        return encoders, scaler, feature_cols, models
    except FileNotFoundError as e:
        logger.error(f"Model artifacts not found. Run training first. {e}")
        raise
    except Exception as e:
        # Covers numpy/sklearn/xgboost version-mismatch errors (e.g. BitGenerator
        # pickle errors) that can occur if saved_models/ was copied from a
        # different machine/environment. Retrain locally and retry once.
        logger.warning(f"Model artifacts incompatible with this environment ({e}). "
                        "Retraining locally...")
        from models.train_material_prediction import ensure_models_trained
        import shutil
        if os.path.exists(SAVE_DIR):
            shutil.rmtree(SAVE_DIR)
        os.makedirs(SAVE_DIR, exist_ok=True)
        ensure_models_trained()

        encoders = joblib.load(os.path.join(SAVE_DIR, "encoders.pkl"))
        scaler = joblib.load(os.path.join(SAVE_DIR, "scaler.pkl"))
        feature_cols = joblib.load(os.path.join(SAVE_DIR, "feature_cols.pkl"))
        models = {t: joblib.load(os.path.join(SAVE_DIR, f"{t}_best_model.pkl")) for t in TARGETS}
        return encoders, scaler, feature_cols, models


def predict_material_requirement(fabric_type, fabric_gsm, fabric_width, machine_type,
                                   machine_efficiency, production_target, season,
                                   month, working_days, waste_buffer_pct=8):
    """
    Predict required quantities of each raw material for a given production plan.

    Returns a dict with predicted quantities, safety stock, expected waste,
    reorder quantity, and estimated cost per material + total.
    """
    encoders, scaler, feature_cols, models = _load_artifacts()

    try:
        fabric_enc = encoders["Fabric_Type"].transform([fabric_type])[0]
    except ValueError:
        fabric_enc = 0
    try:
        machine_enc = encoders["Machine_Type"].transform([machine_type])[0]
    except ValueError:
        machine_enc = 0
    try:
        season_enc = encoders["Season"].transform([season])[0]
    except ValueError:
        season_enc = 0

    row = pd.DataFrame([{
        "Fabric_Type_enc": fabric_enc,
        "Fabric_GSM": fabric_gsm,
        "Fabric_Width": fabric_width,
        "Machine_Type_enc": machine_enc,
        "Machine_Efficiency": machine_efficiency,
        "Production_Target": production_target,
        "Season_enc": season_enc,
        "Month": month,
        "Working_Days": working_days,
    }])[feature_cols]

    X_scaled = scaler.transform(row)

    results = {}
    total_cost = 0
    for target in TARGETS:
        pred = max(0, float(models[target].predict(X_scaled)[0]))
        safety_stock = pred * 0.15
        expected_waste = pred * (waste_buffer_pct / 100)
        reorder_qty = pred + safety_stock + expected_waste
        cost = reorder_qty * MATERIAL_UNIT_COST[target]
        total_cost += cost

        results[target.replace("_Used", "").replace("_Material", "")] = {
            "predicted_qty": round(pred, 2),
            "safety_stock": round(safety_stock, 2),
            "expected_waste": round(expected_waste, 2),
            "reorder_qty": round(reorder_qty, 2),
            "estimated_cost": round(cost, 2),
        }

    results["_total_estimated_cost"] = round(total_cost, 2)
    return results


def get_model_comparison(target_col):
    """Return the saved model comparison table for a given material target."""
    path = os.path.join(SAVE_DIR, f"{target_col}_model_comparison.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame()


def get_best_model_summary():
    path = os.path.join(SAVE_DIR, "best_model_summary.pkl")
    if os.path.exists(path):
        return joblib.load(path)
    return {}
