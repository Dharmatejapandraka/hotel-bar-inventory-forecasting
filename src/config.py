from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    raw_data_path: Path = Path("data/raw/bar_inventory_data.csv")
    processed_data_path: Path = Path("data/processed/daily_bar_consumption.csv")
    figures_dir: Path = Path("reports/figures")
    summary_path: Path = Path("reports/model_summary.csv")

    lead_time_days: int = 2
    service_level_z: float = 1.645  # 95% service level
    initial_stock_multiplier: float = 1.0
    min_history_days: int = 21

    @property
    def required_columns(self):
        return [
            "Date Time Served",
            "Bar Name",
            "Brand Name",
            "Opening Balance",
            "Purchase",
            "Consumed",
            "Closing Balance",
        ]
