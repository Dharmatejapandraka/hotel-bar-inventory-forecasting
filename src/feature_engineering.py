import pandas as pd


def add_time_features(daily: pd.DataFrame) -> pd.DataFrame:
    out = daily.copy().sort_values(
        ["Bar Name", "Brand Name", "Date"]
    ).reset_index(drop=True)

    group = out.groupby(["Bar Name", "Brand Name"])["Consumed (ml)"]

    out["lag_1"] = group.shift(1)
    out["lag_7"] = group.shift(7)
    out["lag_14"] = group.shift(14)

    out["rolling_mean_7"] = (
        group.shift(1).transform(lambda s: s.rolling(7, min_periods=3).mean())
    )
    out["rolling_std_7"] = (
        group.shift(1).transform(lambda s: s.rolling(7, min_periods=3).std())
    )

    out["dayofweek"] = out["Date"].dt.dayofweek
    out["is_weekend"] = out["dayofweek"].isin([4, 5, 6]).astype(int)

    return out


def make_supervised_series(series: pd.Series, lags=(1, 7, 14)) -> pd.DataFrame:
    data = pd.DataFrame({"y": series.astype(float).values})
    for lag in lags:
        data[f"lag_{lag}"] = data["y"].shift(lag)
    data["rolling_mean_7"] = data["y"].shift(1).rolling(7, min_periods=3).mean()
    data["rolling_std_7"] = data["y"].shift(1).rolling(7, min_periods=3).std()
    return data
