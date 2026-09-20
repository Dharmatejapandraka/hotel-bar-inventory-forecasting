import argparse
from pathlib import Path
import numpy as np
import pandas as pd

from src.config import Config
from src.data_loader import load_inventory_data
from src.preprocessing import validate_conservation, prepare_daily_consumption, save_processed
from src.eda import plot_top_items, plot_weekday_pattern, plot_demand_series, abc_categorization, identify_stockout_days
from src.forecasting import compare_models, forecast_next_days
from src.par_level import compute_par_level
from src.inventory_simulation import simulate_bar_inventory


def create_demo_dataset(path, days=120):
    rng = np.random.default_rng(42)
    dates = pd.date_range("2026-01-01", periods=days, freq="D")
    bars = ["Main Bar", "Pool Bar"]
    brands = ["Brand A", "Brand B", "Brand C"]
    rows = []
    previous = {(bar, brand): 5000.0 for bar in bars for brand in brands}
    for date in dates:
        for bar in bars:
            for brand in brands:
                base = {"Brand A": 2200, "Brand B": 1300, "Brand C": 600}[brand]
                bar_factor = 1.15 if bar == "Main Bar" else 0.75
                weekend_factor = 1.35 if date.dayofweek in [4, 5] else 1.0
                consumed = max(0.0, base * bar_factor * weekend_factor + rng.normal(0, base * 0.12))
                opening = previous[(bar, brand)]
                purchase = 4000.0 if opening - consumed < 1000 else 0.0
                closing = max(0.0, opening + purchase - consumed)
                rows.append({"Date Time Served": date + pd.Timedelta(hours=18), "Bar Name": bar, "Brand Name": brand, "Opening Balance": opening, "Purchase": purchase, "Consumed": consumed, "Closing Balance": closing})
                previous[(bar, brand)] = closing
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False)


def main():
    parser = argparse.ArgumentParser(description="Hotel Bar Inventory Forecasting pipeline")
    parser.add_argument("--demo", action="store_true", help="Generate demo data and run the complete pipeline")
    args = parser.parse_args()
    cfg = Config()
    cfg.figures_dir.mkdir(parents=True, exist_ok=True)
    cfg.processed_data_path.parent.mkdir(parents=True, exist_ok=True)
    cfg.summary_path.parent.mkdir(parents=True, exist_ok=True)
    if args.demo:
        create_demo_dataset(cfg.raw_data_path)
        print(f"Demo dataset created at {cfg.raw_data_path}")
    raw = load_inventory_data(cfg.raw_data_path)
    validated = validate_conservation(raw)
    print(f"Rows loaded: {len(raw):,}")
    print(f"Conservation check pass rate: {validated['conservation_ok'].mean() * 100:.2f}%")
    daily = prepare_daily_consumption(raw)
    save_processed(daily, cfg.processed_data_path)
    print(f"Daily data saved: {cfg.processed_data_path}")
    plot_top_items(daily, cfg.figures_dir)
    plot_weekday_pattern(daily, cfg.figures_dir)
    abc_categorization(daily).to_csv(cfg.figures_dir / "abc_categorization.csv", index=False)
    identify_stockout_days(validated).to_csv(cfg.figures_dir / "historical_stockouts.csv", index=False)
    all_results = []
    for (bar, brand), group in daily.groupby(["Bar Name", "Brand Name"]):
        series = group.sort_values("Date")["Consumed (ml)"].reset_index(drop=True)
        if len(series) < cfg.min_history_days:
            continue
        plot_demand_series(daily, cfg.figures_dir, bar, brand)
        results, _, _ = compare_models(series)
        results.insert(0, "Bar Name", bar)
        results.insert(1, "Brand Name", brand)
        forecast = forecast_next_days(series, cfg.lead_time_days, "Holt-Winters")
        std_daily = float(series.tail(28).std())
        if np.isnan(std_daily): std_daily = 0.0
        par = compute_par_level(float(np.mean(forecast)), std_daily, cfg.lead_time_days, cfg.service_level_z)
        sim = simulate_bar_inventory(series.values, par["par_level"], cfg.lead_time_days, par["par_level"])
        results["par_level_ml"] = par["par_level"]
        all_results.append(results)
        print(f"{bar} / {brand}: Par={par['par_level']:.0f} ml, Safety={par['safety_stock']:.0f} ml, Sim stockout days={sim['stockout_days']}")
    if all_results:
        pd.concat(all_results, ignore_index=True).to_csv(cfg.summary_path, index=False)
        print(f"Model summary saved: {cfg.summary_path}")
    print("\nPipeline completed.")


if __name__ == "__main__":
    main()
