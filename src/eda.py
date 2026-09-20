from pathlib import Path
import matplotlib
matplotlib.use("Agg")  # Non-GUI backend for reliable VS Code/terminal execution
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd


def ensure_dir(path):
    Path(path).mkdir(parents=True, exist_ok=True)


def plot_top_items(daily, output_dir, top_n=10):
    ensure_dir(output_dir)
    totals = (
        daily.groupby(["Bar Name", "Brand Name"])["Consumed (ml)"]
        .sum()
        .sort_values(ascending=False)
        .head(top_n)
    )

    plt.figure(figsize=(11, 6))
    totals.sort_values().plot(kind="barh")
    plt.title("Top bar-brand combinations by consumption")
    plt.xlabel("Consumed (ml)")
    plt.tight_layout()
    path = Path(output_dir) / "top_items.png"
    plt.savefig(path, dpi=150)
    plt.close()
    return path


def plot_weekday_pattern(daily, output_dir):
    ensure_dir(output_dir)
    work = daily.copy()
    work["Day"] = work["Date"].dt.day_name()
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    summary = work.groupby("Day")["Consumed (ml)"].mean().reindex(order)

    plt.figure(figsize=(10, 5))
    summary.plot(kind="bar")
    plt.title("Average daily consumption by day of week")
    plt.ylabel("Average consumption (ml)")
    plt.xticks(rotation=30)
    plt.tight_layout()
    path = Path(output_dir) / "weekday_pattern.png"
    plt.savefig(path, dpi=150)
    plt.close()
    return path


def plot_demand_series(daily, output_dir, bar_name, brand_name):
    ensure_dir(output_dir)
    series = daily[
        (daily["Bar Name"] == bar_name) &
        (daily["Brand Name"] == brand_name)
    ].sort_values("Date")

    if series.empty:
        return None

    plt.figure(figsize=(12, 5))
    plt.plot(series["Date"], series["Consumed (ml)"])
    plt.title(f"Daily demand — {bar_name} / {brand_name}")
    plt.xlabel("Date")
    plt.ylabel("Consumed (ml)")
    plt.tight_layout()

    safe_bar = str(bar_name).replace("/", "_")
    safe_brand = str(brand_name).replace("/", "_")
    path = Path(output_dir) / f"demand_{safe_bar}_{safe_brand}.png"
    plt.savefig(path, dpi=150)
    plt.close()
    return path


def abc_categorization(daily):
    totals = (
        daily.groupby(["Bar Name", "Brand Name"])["Consumed (ml)"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    if totals.empty:
        return totals

    totals["share"] = totals["Consumed (ml)"] / totals["Consumed (ml)"].sum()
    totals["cumulative_share"] = totals["share"].cumsum()

    def category(x):
        if x <= 0.80:
            return "A"
        if x <= 0.95:
            return "B"
        return "C"

    totals["ABC Class"] = totals["cumulative_share"].apply(category)
    return totals


def identify_stockout_days(raw_validated):
    if raw_validated.empty:
        return raw_validated.copy()

    return raw_validated[
        (raw_validated["Closing Balance"] <= 0) &
        (raw_validated["Consumed"] > 0)
    ].copy()
