# Hotel Bar Inventory Forecasting & Par Level Recommendation System

A complete Python + Flask project based on the supplied reference workflow:

**load → validate → aggregate → EDA/ABC → forecast → par level → inventory simulation → dashboard**

## Project structure

```text
hotel-bar-inventory-system/
├── app.py                         # Flask web application
├── run.py                         # CLI pipeline
├── requirements.txt
├── README.md
├── data/
│   ├── raw/bar_inventory_data.csv
│   └── processed/
├── src/
│   ├── config.py
│   ├── data_loader.py
│   ├── preprocessing.py
│   ├── eda.py
│   ├── evaluation.py
│   ├── feature_engineering.py
│   ├── forecasting.py
│   ├── par_level.py
│   └── inventory_simulation.py
├── templates/index.html            # HTML only
├── static/css/style.css            # CSS only
├── static/js/app.js                # JavaScript only
├── notebooks/inventory_forecasting_solution.ipynb
└── reports/
```

## 1. Open in VS Code

Extract the ZIP and open the project folder in VS Code.

## 2. Create virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 3. Install packages

```powershell
python -m pip install -r requirements.txt
```

## 4. Run the command-line pipeline

```powershell
python run.py --demo
```

This creates the demo CSV and generates processed data, charts, ABC analysis, stockout audit, forecasts, par-level calculations, and model summary.

## 5. Run the web dashboard

```powershell
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

The dashboard can:

- Run the demo dataset
- Upload a CSV with the reference column structure
- Display total consumption and daily demand
- Show consumption trends
- Show weekday demand patterns
- Show ABC classification
- Compare Moving Average, Holt-Winters, and Random Forest
- Show forecast-informed par levels and safety stock
- Show historical simulation metrics

## Expected CSV columns

```text
Date Time Served
Bar Name
Brand Name
Opening Balance
Purchase
Consumed
Closing Balance
```

The loader also supports common aliases such as `Date`, `Bar`, `Brand`, `Consumption`, `Purchased`, etc.

## Important methodology

The reference workflow uses chronological validation for forecasting. The operational par-level example uses Holt-Winters with a two-day lead time and a 95% service-level z value of 1.645. Safety stock is based on recent demand variability.

## Notebook

The notebook is included for academic/project demonstration. The web dashboard is the user-facing application, while the `src/` modules contain the reusable analytics logic.
