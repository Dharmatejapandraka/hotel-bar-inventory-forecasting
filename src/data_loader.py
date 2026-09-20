from pathlib import Path
import pandas as pd


ALIASES = {
    "Date Time Served": [
        "Date Time Served", "Datetime", "Date", "DateTime", "Timestamp"
    ],
    "Bar Name": ["Bar Name", "Bar", "Bar_Name"],
    "Brand Name": ["Brand Name", "Brand", "Brand_Name", "Item", "Item Name"],
    "Opening Balance": ["Opening Balance", "Opening Balance (ml)", "Opening"],
    "Purchase": ["Purchase", "Purchase (ml)", "Purchased"],
    "Consumed": ["Consumed", "Consumed (ml)", "Consumption", "Consumption (ml)"],
    "Closing Balance": ["Closing Balance", "Closing Balance (ml)", "Closing"],
}


def _find_column(columns, candidates):
    normalized = {str(c).strip().lower(): c for c in columns}
    for candidate in candidates:
        key = candidate.strip().lower()
        if key in normalized:
            return normalized[key]
    return None


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename = {}
    for target, candidates in ALIASES.items():
        found = _find_column(df.columns, candidates)
        if found is not None:
            rename[found] = target

    out = df.rename(columns=rename).copy()

    missing = [
        c for c in ALIASES
        if c not in out.columns and c not in {"Opening Balance", "Purchase", "Closing Balance"}
    ]
    if missing:
        raise ValueError(
            "Missing required columns: "
            + ", ".join(missing)
            + ". Required core columns are Date Time Served, Bar Name, Brand Name and Consumed."
        )

    for col in ["Opening Balance", "Purchase", "Consumed", "Closing Balance"]:
        if col not in out.columns:
            out[col] = 0.0

    return out


def load_inventory_data(path) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {path}. Put your CSV at data/raw/bar_inventory_data.csv "
            "or run `python run.py --demo`."
        )

    df = pd.read_csv(path)
    df = normalize_columns(df)

    df["Date Time Served"] = pd.to_datetime(df["Date Time Served"], errors="coerce")
    if df["Date Time Served"].isna().any():
        bad = int(df["Date Time Served"].isna().sum())
        raise ValueError(f"{bad} rows have invalid Date Time Served values.")

    for col in ["Opening Balance", "Purchase", "Consumed", "Closing Balance"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    df["Bar Name"] = df["Bar Name"].astype(str).str.strip()
    df["Brand Name"] = df["Brand Name"].astype(str).str.strip()

    return df.sort_values("Date Time Served").reset_index(drop=True)
