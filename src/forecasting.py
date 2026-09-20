import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from .evaluation import evaluate_forecast
from .feature_engineering import make_supervised_series


def temporal_split(series, test_fraction=0.20):
    n = len(series)
    split = max(1, int(n * (1 - test_fraction)))
    return series.iloc[:split], series.iloc[split:]


def rolling_mean_forecast(train, horizon, window=7):
    if len(train) == 0:
        return np.zeros(horizon)
    value = float(train.tail(window).mean())
    return np.repeat(max(0.0, value), horizon)


def holt_winters_forecast(train, horizon):
    train = pd.Series(train).astype(float)
    if len(train) < 14 or train.nunique() <= 1:
        return rolling_mean_forecast(train, horizon, 7)

    try:
        model = ExponentialSmoothing(
            train,
            trend="add",
            seasonal="add",
            seasonal_periods=7,
            initialization_method="estimated",
        )
        fitted = model.fit(optimized=True)
        pred = fitted.forecast(horizon)
        return np.maximum(np.asarray(pred, dtype=float), 0.0)
    except Exception:
        return rolling_mean_forecast(train, horizon, 7)


def random_forest_forecast(train, horizon, random_state=42):
    train = pd.Series(train).astype(float).reset_index(drop=True)
    supervised = make_supervised_series(train).dropna()

    if len(supervised) < 20:
        return rolling_mean_forecast(train, horizon, 7)

    feature_cols = [c for c in supervised.columns if c != "y"]
    model = RandomForestRegressor(
        n_estimators=250,
        max_depth=10,
        random_state=random_state,
        n_jobs=-1,
    )
    model.fit(supervised[feature_cols], supervised["y"])

    history = list(train.values)
    predictions = []

    for _ in range(horizon):
        lag_1 = history[-1]
        lag_7 = history[-7] if len(history) >= 7 else np.mean(history)
        lag_14 = history[-14] if len(history) >= 14 else np.mean(history)
        recent = np.asarray(history[-7:], dtype=float)

        row = {
            "lag_1": lag_1,
            "lag_7": lag_7,
            "lag_14": lag_14,
            "rolling_mean_7": recent.mean(),
            "rolling_std_7": recent.std(ddof=1) if len(recent) > 1 else 0.0,
        }

        pred = float(model.predict(pd.DataFrame([row])[feature_cols])[0])
        pred = max(0.0, pred)
        predictions.append(pred)
        history.append(pred)

    return np.asarray(predictions)


def compare_models(series, test_fraction=0.20):
    series = pd.Series(series).astype(float).reset_index(drop=True)
    train, test = temporal_split(series, test_fraction)

    if len(test) == 0:
        raise ValueError("Not enough data for a temporal test split.")

    horizon = len(test)
    results = []

    baseline = rolling_mean_forecast(train, horizon, 7)
    results.append({
        "model": "7-day moving average",
        **evaluate_forecast(test, baseline)
    })

    hw = holt_winters_forecast(train, horizon)
    results.append({
        "model": "Holt-Winters",
        **evaluate_forecast(test, hw)
    })

    rf = random_forest_forecast(train, horizon)
    results.append({
        "model": "Random Forest",
        **evaluate_forecast(test, rf)
    })

    return pd.DataFrame(results), train, test


def forecast_next_days(series, horizon=7, model_name="Holt-Winters"):
    series = pd.Series(series).astype(float).reset_index(drop=True)

    if model_name == "7-day moving average":
        return rolling_mean_forecast(series, horizon, 7)
    if model_name == "Random Forest":
        return random_forest_forecast(series, horizon)
    return holt_winters_forecast(series, horizon)
