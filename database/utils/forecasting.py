"""
forecasting.py
--------------
ML demand forecasting on the daily production / consumption series.

Model: Gradient Boosting on calendar + lag features, forecast recursively
day-by-day. Accuracy is measured by a hold-out back-test on the most recent
days, and the confidence band comes from the back-test residuals.
"""

import numpy as np
import pandas as pd
import streamlit as st
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

LAGS = (1, 2, 7, 14, 28)


def _features(series: pd.Series, idx: pd.DatetimeIndex) -> pd.DataFrame:
    X = pd.DataFrame(index=idx)
    X["dow"] = idx.dayofweek
    X["month_sin"] = np.sin(2 * np.pi * idx.month / 12)
    X["month_cos"] = np.cos(2 * np.pi * idx.month / 12)
    X["doy_sin"] = np.sin(2 * np.pi * idx.dayofyear / 365.25)
    X["doy_cos"] = np.cos(2 * np.pi * idx.dayofyear / 365.25)
    for lag in LAGS:
        X[f"lag_{lag}"] = series.shift(lag).reindex(idx)
    X["roll_7"] = series.shift(1).rolling(7).mean().reindex(idx)
    X["roll_28"] = series.shift(1).rolling(28).mean().reindex(idx)
    return X


def _fit(series: pd.Series):
    X = _features(series, series.index).dropna()
    y = series.loc[X.index]
    model = GradientBoostingRegressor(n_estimators=250, max_depth=3, learning_rate=0.05,
                                      subsample=0.9, random_state=42)
    model.fit(X, y)
    return model


def _recursive(model, history: pd.Series, horizon: int) -> pd.Series:
    hist = history.copy()
    preds = []
    for _ in range(horizon):
        nxt = hist.index[-1] + pd.Timedelta(days=1)
        ext = pd.concat([hist, pd.Series([np.nan], index=[nxt])])
        X = _features(ext, pd.DatetimeIndex([nxt]))
        X = X.fillna(hist.tail(28).mean())
        val = max(0.0, float(model.predict(X)[0]))
        preds.append((nxt, val))
        hist = pd.concat([hist, pd.Series([val], index=[nxt])])
    return pd.Series([v for _, v in preds], index=[d for d, _ in preds])


@st.cache_data(show_spinner=False)
def forecast_series(values: tuple, start: str, horizon: int = 30, backtest_days: int = 60):
    """
    values/start: the daily series (passed as tuple for caching).
    Returns dict with forecast DataFrame (yhat, lower, upper), back-test frame and metrics.
    """
    idx = pd.date_range(start=start, periods=len(values), freq="D")
    series = pd.Series(values, index=idx, dtype=float)

    # ---- back-test on the last `backtest_days`
    train, test = series.iloc[:-backtest_days], series.iloc[-backtest_days:]
    bt_model = _fit(train)
    bt_pred = _recursive(bt_model, train, backtest_days)
    resid = test.values - bt_pred.values
    mae = mean_absolute_error(test.values, bt_pred.values)
    denom = np.where(test.values == 0, np.nan, test.values)
    mape = float(np.nanmean(np.abs(resid / denom)) * 100)
    sigma = float(np.std(resid))

    # ---- final model on all data
    model = _fit(series)
    fc = _recursive(model, series, horizon)
    steps = np.arange(1, horizon + 1)
    width = 1.28 * sigma * np.sqrt(1 + steps / horizon)  # ~80% band, widening with horizon
    fc_df = pd.DataFrame({"yhat": fc.values,
                          "lower": np.maximum(0, fc.values - width),
                          "upper": fc.values + width}, index=fc.index)

    backtest = pd.DataFrame({"actual": test.values, "predicted": bt_pred.values}, index=test.index)
    return {"forecast": fc_df, "backtest": backtest,
            "metrics": {"MAE": round(float(mae), 2), "MAPE": round(mape, 2),
                        "Accuracy": round(max(0.0, 100 - mape), 2)}}


def stockout_projection(current_stock: float, reorder_level: float, daily_forecast: pd.Series):
    """Days until stock crosses reorder level and zero, using cumulative forecast consumption."""
    remaining = current_stock - daily_forecast.cumsum()
    reorder_day = next((i + 1 for i, v in enumerate(remaining.values) if v <= reorder_level), None)
    stockout_day = next((i + 1 for i, v in enumerate(remaining.values) if v <= 0), None)
    return {"remaining": remaining, "reorder_in_days": reorder_day, "stockout_in_days": stockout_day}
