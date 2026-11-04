"""
train_material_prediction.py
-----------------------------
Trains and compares multiple ML models to predict raw material
requirement (Cotton, Yarn, Polyester, Dye, Chemical, Packing).

Models compared:
    - Linear Regression
    - Random Forest
    - Decision Tree
    - Gradient Boosting
    - XGBoost

The best model per material (lowest RMSE) is saved to /saved_models/.
Also saves the fitted preprocessing encoders/scaler for reuse at inference time.

Run:
    python models/train_material_prediction.py
"""

import os
import logging
import joblib
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "dataset", "powerloom_production_data.csv")
SAVE_DIR = os.path.join(os.path.dirname(__file__), "..", "saved_models")
os.makedirs(SAVE_DIR, exist_ok=True)

FEATURES = [
    "Fabric_Type", "Fabric_GSM", "Fabric_Width", "Machine_Type",
    "Machine_Efficiency", "Production_Target", "Season", "Month", "Working_Days"
]

TARGETS = ["Cotton_Used", "Yarn_Used", "Polyester_Used",
           "Dye_Used", "Chemical_Used", "Packing_Material"]

MODELS = {
    "LinearRegression": LinearRegression(),
    "DecisionTree": DecisionTreeRegressor(max_depth=8, random_state=42),
    "RandomForest": RandomForestRegressor(n_estimators=200, max_depth=10, random_state=42, n_jobs=-1),
    "GradientBoosting": GradientBoostingRegressor(n_estimators=200, max_depth=4, random_state=42),
    "XGBoost": XGBRegressor(n_estimators=300, max_depth=5, learning_rate=0.08,
                             random_state=42, n_jobs=-1, verbosity=0),
}


def load_and_prepare_data():
    """Load dataset and encode categorical features."""
    df = pd.read_csv(DATA_PATH)

    encoders = {}
    for col in ["Fabric_Type", "Machine_Type", "Season"]:
        le = LabelEncoder()
        df[col + "_enc"] = le.fit_transform(df[col])
        encoders[col] = le

    feature_cols = ["Fabric_Type_enc", "Fabric_GSM", "Fabric_Width", "Machine_Type_enc",
                     "Machine_Efficiency", "Production_Target", "Season_enc", "Month", "Working_Days"]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df[feature_cols])

    joblib.dump(encoders, os.path.join(SAVE_DIR, "encoders.pkl"))
    joblib.dump(scaler, os.path.join(SAVE_DIR, "scaler.pkl"))
    joblib.dump(feature_cols, os.path.join(SAVE_DIR, "feature_cols.pkl"))

    return df, X_scaled


def train_for_target(df, X_scaled, target_col):
    """Train all candidate models for one target material and pick the best."""
    y = df[target_col].values
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

    results = []
    best_model, best_rmse, best_name = None, float("inf"), None

    for name, model in MODELS.items():
        try:
            model.fit(X_train, y_train)
            preds = model.predict(X_test)

            mae = mean_absolute_error(y_test, preds)
            rmse = np.sqrt(mean_squared_error(y_test, preds))
            r2 = r2_score(y_test, preds)

            cv_scores = cross_val_score(model, X_scaled, y, cv=5, scoring="r2")
            accuracy = round(max(0, r2) * 100, 2)

            results.append({
                "Model": name, "MAE": round(mae, 3), "RMSE": round(rmse, 3),
                "R2": round(r2, 4), "CV_R2_Mean": round(cv_scores.mean(), 4),
                "Accuracy_%": accuracy
            })

            if rmse < best_rmse:
                best_rmse, best_model, best_name = rmse, model, name

        except Exception as e:
            logger.error(f"Error training {name} for {target_col}: {e}")

    joblib.dump(best_model, os.path.join(SAVE_DIR, f"{target_col}_best_model.pkl"))
    results_df = pd.DataFrame(results).sort_values("RMSE")
    results_df.to_csv(os.path.join(SAVE_DIR, f"{target_col}_model_comparison.csv"), index=False)

    logger.info(f"[{target_col}] Best model: {best_name} (RMSE={best_rmse:.3f})")
    return results_df, best_name


def main():
    logger.info("Loading and preparing dataset...")
    df, X_scaled = load_and_prepare_data()

    summary = {}
    for target in TARGETS:
        logger.info(f"Training models for target: {target}")
        results_df, best_name = train_for_target(df, X_scaled, target)
        summary[target] = best_name
        print(f"\n=== {target} ===")
        print(results_df.to_string(index=False))

    print("\n=== BEST MODEL SUMMARY ===")
    for k, v in summary.items():
        print(f"{k}: {v}")

    joblib.dump(summary, os.path.join(SAVE_DIR, "best_model_summary.pkl"))
    logger.info("Training complete. Models saved to /saved_models/")


def ensure_models_trained():
    """
    Ensures a dataset and trained models exist, matching the numpy/sklearn/xgboost
    versions actually installed in THIS environment. This avoids cross-machine
    pickle/BitGenerator incompatibilities entirely, since models are always
    trained locally on first run rather than shipped pre-baked.

    Called automatically from app.py at startup.
    """
    summary_path = os.path.join(SAVE_DIR, "best_model_summary.pkl")

    if not os.path.exists(DATA_PATH):
        logger.info("Dataset not found. Generating dataset...")
        import subprocess, sys as _sys
        gen_script = os.path.join(os.path.dirname(__file__), "..", "dataset", "generate_dataset.py")
        subprocess.run([_sys.executable, gen_script], check=True, cwd=os.path.dirname(gen_script))

    if not os.path.exists(summary_path):
        logger.info("Trained models not found for this environment. Training now "
                     "(one-time setup, may take a minute)...")
        main()
        logger.info("Model training complete.")
    else:
        # Sanity check: try loading one artifact; if it fails (e.g. version
        # mismatch from a copied/shared saved_models folder), retrain fresh.
        try:
            joblib.load(summary_path)
        except Exception as e:
            logger.warning(f"Existing model artifacts are incompatible with this "
                            f"environment ({e}). Retraining from scratch...")
            for f in os.listdir(SAVE_DIR):
                try:
                    os.remove(os.path.join(SAVE_DIR, f))
                except OSError:
                    pass
            main()


if __name__ == "__main__":
    main()
