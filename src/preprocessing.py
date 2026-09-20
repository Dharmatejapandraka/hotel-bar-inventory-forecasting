import numpy as np
import pandas as pd


def validate_conservation(df: pd.DataFrame, tolerance: float = 1e-6) -> pd.DataFrame:
    out = df.copy()
    out["expected_closing"] = (
        out["Opening Balance"] + out["Purchase"] - out["Consumed"]
    )
    out["conservation_difference"] = (
        out["Closing Balance"] - out["expected_closing"]
    )
    out["conservation_ok"] = (
        out["conservation_difference"].abs() <= tolerance
    )
    return out


def prepare_daily_consumption(df: pd.DataFrame) -> pd.DataFrame:
    work = df.copy()
    work["Date"] = work["Date Time Served"].dt.floor("D")

    daily = (
        work.groupby(["Date", "Bar Name", "Brand Name"], as_index=False)["Consumed"]
        .sum()
        .rename(columns={"Consumed": "Consumed (ml)"})
    )

    if daily.empty:
        return daily

    dates = pd.date_range(
        daily["Date"].min(),
        daily["Date"].max(),
        freq="D"
    )
    bars = daily["Bar Name"].dropna().unique()
    brands = daily["Brand Name"].dropna().unique()

    full_index = pd.MultiIndex.from_product(
        [dates, bars, brands],
        names=["Date", "Bar Name", "Brand Name"]
    )

    daily = (
        daily.set_index(["Date", "Bar Name", "Brand Name"])
        .reindex(full_index, fill_value=0.0)
        .reset_index()
    )

    daily["Consumed (ml)"] = daily["Consumed (ml)"].clip(lower=0)
    return daily.sort_values(
        ["Bar Name", "Brand Name", "Date"]
    ).reset_index(drop=True)


def save_processed(daily: pd.DataFrame, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    daily.to_csv(path, index=False)
