from pathlib import Path
import json
import numpy as np
import pandas as pd
from flask import Flask, jsonify, render_template, request

from src.config import Config
from src.data_loader import load_inventory_data
from src.preprocessing import validate_conservation, prepare_daily_consumption, save_processed
from src.eda import abc_categorization, identify_stockout_days
from src.forecasting import compare_models, forecast_next_days
from src.par_level import compute_par_level
from src.inventory_simulation import simulate_bar_inventory

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "raw" / "bar_inventory_data.csv"
PROCESSED_PATH = BASE_DIR / "data" / "processed" / "daily_bar_consumption.csv"
ABC_PATH = BASE_DIR / "reports" / "figures" / "abc_categorization.csv"
STOCKOUT_PATH = BASE_DIR / "reports" / "figures" / "historical_stockouts.csv"
SUMMARY_PATH = BASE_DIR / "reports" / "model_summary.csv"

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024


def create_demo_dataset(path: Path, days: int = 120):
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
                noise = rng.normal(0, base * 0.12)
                consumed = max(0.0, base * bar_factor * weekend_factor + noise)
                opening = previous[(bar, brand)]
                purchase = 4000.0 if opening - consumed < 1000 else 0.0
                closing = max(0.0, opening + purchase - consumed)
                rows.append({
                    "Date Time Served": date + pd.Timedelta(hours=18),
                    "Bar Name": bar,
                    "Brand Name": brand,
                    "Opening Balance": opening,
                    "Purchase": purchase,
                    "Consumed": consumed,
                    "Closing Balance": closing,
                })
                previous[(bar, brand)] = closing

    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False)


def run_analysis():
    cfg = Config(
        raw_data_path=DATA_PATH,
        processed_data_path=PROCESSED_PATH,
        figures_dir=BASE_DIR / "reports" / "figures",
        summary_path=SUMMARY_PATH,
    )
    cfg.figures_dir.mkdir(parents=True, exist_ok=True)
    PROCESSED_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)

    raw = load_inventory_data(DATA_PATH)
    validated = validate_conservation(raw)
    daily = prepare_daily_consumption(raw)
    save_processed(daily, PROCESSED_PATH)

    abc = abc_categorization(daily)
    abc.to_csv(ABC_PATH, index=False)
    stockouts = identify_stockout_days(validated)
    stockouts.to_csv(STOCKOUT_PATH, index=False)

    recommendation_rows = []
    model_rows = []
    for (bar, brand), group in daily.groupby(["Bar Name", "Brand Name"]):
        group = group.sort_values("Date")
        series = group["Consumed (ml)"].reset_index(drop=True)
        if len(series) < cfg.min_history_days:
            continue

        results, _, _ = compare_models(series)
        for _, row in results.iterrows():
            model_rows.append({
                "Bar Name": bar,
                "Brand Name": brand,
                "model": row["model"],
                "MAE": float(row["MAE"]),
                "RMSE": float(row["RMSE"]),
                "WAPE": float(row["WAPE"]),
            })

        forecast = forecast_next_days(series, cfg.lead_time_days, "Holt-Winters")
        std_daily = float(series.tail(28).std())
        if np.isnan(std_daily):
            std_daily = 0.0
        par = compute_par_level(
            float(np.mean(forecast)), std_daily,
            cfg.lead_time_days, cfg.service_level_z
        )
        sim = simulate_bar_inventory(
            series.values, par["par_level"], cfg.lead_time_days, par["par_level"]
        )
        abc_class = "-"
        match = abc[(abc["Bar Name"] == bar) & (abc["Brand Name"] == brand)]
        if not match.empty:
            abc_class = str(match.iloc[0]["ABC Class"])

        recommendation_rows.append({
            "Bar Name": bar,
            "Brand Name": brand,
            "ABC Class": abc_class,
            "Forecast Daily Demand": float(np.mean(forecast)),
            "Lead Time Demand": par["lead_time_demand"],
            "Safety Stock": par["safety_stock"],
            "Par Level": par["par_level"],
            "Stockout Days": sim["stockout_days"],
            "Lost Volume (ml)": sim["lost_volume_ml"],
            "Average Inventory (ml)": sim["average_inventory_ml"],
            "Turnover Ratio": sim["turnover_ratio"],
        })

    model_df = pd.DataFrame(model_rows)
    if not model_df.empty:
        model_df.to_csv(SUMMARY_PATH, index=False)

    rec_df = pd.DataFrame(recommendation_rows)
    return raw, validated, daily, abc, stockouts, model_df, rec_df


def safe_records(df):
    if df is None or df.empty:
        return []
    clean = df.copy()
    clean = clean.replace({np.nan: None, np.inf: None, -np.inf: None})
    return json.loads(clean.to_json(orient="records", date_format="iso"))


@app.route("/")
def dashboard():
    return render_template("index.html")


@app.route("/api/dashboard")
def dashboard_api():
    try:
        raw, validated, daily, abc, stockouts, model_df, rec_df = run_analysis()
    except FileNotFoundError:
        return jsonify({"error": "Dataset not found. Use Run Demo Dataset or upload a CSV."}), 404

    weekday = daily.assign(Day=daily["Date"].dt.day_name()).groupby("Day")["Consumed (ml)"].mean()
    weekday = weekday.reindex(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])

    trend = daily.groupby("Date", as_index=False)["Consumed (ml)"].sum()
    cards = {
        "rows": int(len(raw)),
        "total_consumed": float(raw["Consumed"].sum()),
        "avg_daily_consumption": float(daily.groupby("Date")["Consumed (ml)"].sum().mean()),
        "stockout_rows": int(len(stockouts)),
        "bar_brand_count": int(daily[["Bar Name", "Brand Name"]].drop_duplicates().shape[0]),
    }
    return jsonify({
        "cards": cards,
        "abc": safe_records(abc),
        "recommendations": safe_records(rec_df),
        "models": safe_records(model_df),
        "trend": safe_records(trend),
        "weekday": {k: (None if pd.isna(v) else float(v)) for k, v in weekday.items()},
        "generated": pd.Timestamp.now().isoformat(),
    })


@app.route("/api/trend")
def trend_api():
    try:
        # Do NOT run the complete forecasting pipeline here.
        # The processed daily data is already generated by run_analysis().
        if not PROCESSED_PATH.exists():
            run_analysis()

        daily = pd.read_csv(
            PROCESSED_PATH,
            parse_dates=["Date"]
        )

    except FileNotFoundError:
        return jsonify({"error": "Dataset not found."}), 404

    except Exception as exc:
        return jsonify({"error": str(exc)}), 500

    bar = request.args.get("bar")
    brand = request.args.get("brand")

    data = daily.copy()

    if bar:
        data = data[data["Bar Name"].astype(str) == bar]

    if brand:
        data = data[data["Brand Name"].astype(str) == brand]

    data = (
        data.groupby("Date", as_index=False)["Consumed (ml)"]
        .sum()
        .sort_values("Date")
    )

    return jsonify(safe_records(data))


@app.route("/api/run-demo", methods=["POST"])
def run_demo():
    create_demo_dataset(DATA_PATH)
    run_analysis()
    return jsonify({"message": "Demo dataset generated and analysis completed."})


@app.route("/api/upload", methods=["POST"])
def upload_csv():
    uploaded = request.files.get("file")
    if uploaded is None or uploaded.filename == "":
        return jsonify({"error": "Please choose a CSV file."}), 400
    if not uploaded.filename.lower().endswith(".csv"):
        return jsonify({"error": "Only CSV files are supported."}), 400
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    uploaded.save(DATA_PATH)
    try:
        run_analysis()
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify({"message": "CSV uploaded and analysis completed."})


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
